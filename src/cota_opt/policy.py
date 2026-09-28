"""Experiment 6 policy constraints -- enforced on the production feasibility path.

A policy constraint here is not a label. `PolicySpec` is a frozen, digested
description; `compile()` binds it to one setup's route-period keys, baseline
headways, route stop sets and projected stop coordinates, and the compiled
object is attached to that setup's model. From then on:

* `PathBasedModel.evaluate_array` stamps every `FitnessVector` with
  `policy_violation` -- a non-negative count of how far the plan is outside the
  policy (0 = inside);
* `frequency._feasible` refuses any fitness with `policy_violation > 0`, so the
  Gen1 greedy/exchange search, the Gen2 exact block solves, explicit-anchor
  admission and every D35 reach test all decide policy with the SAME predicate
  that decides the resource envelope;
* `filter_ladders` additionally removes rungs no feasible plan could use (OFF
  on a must-stay-on route-period, headways above an R1 cap). That is an
  efficiency, never the enforcement: a one-rung `ladder_override` that bypasses
  the filter is still refused by `_feasible`.

With no policy attached nothing here runs: `policy_violation` defaults to 0.0
and every pre-Experiment-6 path is unchanged.

Regimes implemented (see EXPERIMENT6_CONSTRAINT_CATALOG.md for sources and
classification -- none is an adopted COTA standard):

  R1 max_headway      every baseline-served route-period stays ON with headway
                      <= max(H, its baseline headway)
  R2 max_off_share    at most floor(share * |B|) baseline-served route-periods
                      OFF, B = route-periods with finite baseline headway
  R3 span             each route's first and last baseline-served periods stay ON
  R4 max_lost_share   at most floor(share * |S|) baseline-served stop-periods
                      lose all service, S = (stop, period) pairs served in the
                      baseline plan
  R6 area_radius_m    every baseline-served stop-period stays within
                      `area_radius_m` (straight line, projected CRS) of a stop
                      served in that period
"""
from __future__ import annotations

import math
from dataclasses import asdict, dataclass

import numpy as np

PERIOD_ORDER = ("early", "am_peak", "midday", "pm_peak", "evening", "owl")
_EPS = 1e-9


@dataclass(frozen=True)
class PolicySpec:
    cell: str
    max_headway: float | None = None
    max_off_share: float | None = None
    span: bool = False
    max_lost_share: float | None = None
    area_radius_m: float | None = None
    catalog_digest: str = ""

    def payload(self) -> dict:
        return asdict(self)

    @property
    def digest(self) -> str:
        from .firewall.core import digest
        return digest(self.payload())

    @property
    def is_empty(self) -> bool:
        return (self.max_headway is None and self.max_off_share is None
                and not self.span and self.max_lost_share is None
                and self.area_radius_m is None)

    def at_least_as_tight_as(self, other: "PolicySpec") -> bool:
        """Every constraint of `other` is implied by self's, parameter-wise.

        Parameter-wise implication on the SAME network and envelope:
        R1 smaller H is tighter; R2/R4 smaller share is tighter; R3 True is
        tighter than False; R6 smaller radius is tighter. A constraint absent
        in self is looser than any present in other. R1 present (any H) implies
        R2 with share 0 (no baseline-served route-period may be OFF) and hence
        every R2 share. R4 with share 0 implies R6 at any radius (a stop that
        keeps service is at distance 0 from a served stop).
        """
        o = other
        if o.max_headway is not None:
            if self.max_headway is None or self.max_headway > o.max_headway:
                return False
        if o.max_off_share is not None:
            ok = (self.max_headway is not None or
                  (self.max_off_share is not None and
                   self.max_off_share <= o.max_off_share))
            if not ok:
                return False
        if o.span and not (self.span or self.max_headway is not None
                           or self.max_off_share == 0.0):
            return False
        if o.max_lost_share is not None:
            ok = (self.max_headway is not None or self.max_off_share == 0.0 or
                  (self.max_lost_share is not None and
                   self.max_lost_share <= o.max_lost_share))
            if not ok:
                return False
        if o.area_radius_m is not None:
            ok = (self.max_headway is not None or self.max_off_share == 0.0 or
                  self.max_lost_share == 0.0 or
                  (self.area_radius_m is not None and
                   self.area_radius_m <= o.area_radius_m))
            if not ok:
                return False
        return True

    def compile(self, keys, baseline_headways: dict, route_stops: dict,
                stop_xy: dict) -> "CompiledPolicy":
        return CompiledPolicy(self, list(keys), baseline_headways,
                              route_stops, stop_xy)


class CompiledPolicy:
    def __init__(self, spec: PolicySpec, keys, base: dict, route_stops: dict,
                 stop_xy: dict):
        self.spec = spec
        self.keys = keys
        n = len(keys)
        pos = {k: i for i, k in enumerate(keys)}
        b = np.array([float(base[k]) for k in keys])
        self.base = b
        self.B = np.flatnonzero(np.isfinite(b))
        # R1 caps
        self.r1_cap = np.full(n, np.inf)
        if spec.max_headway is not None:
            self.r1_cap[self.B] = np.maximum(float(spec.max_headway), b[self.B])
        # R2
        self.r2_allowed = (None if spec.max_off_share is None else
                           int(math.floor(spec.max_off_share * len(self.B)
                                          + _EPS)))
        # R3 span keys
        span = []
        if spec.span:
            routes = sorted({k[0] for k in keys})
            for r in routes:
                served = [p for p in PERIOD_ORDER
                          if (r, p) in pos and math.isfinite(base[(r, p)])]
                if served:
                    for p in {served[0], served[-1]}:
                        span.append(pos[(r, p)])
        self.span_idx = np.array(sorted(span), dtype=np.int64)
        # stop-period incidence (R4/R6)
        self.n_sp = 0
        self.r4_allowed = None
        self._r4 = self._r6 = None
        need_sp = spec.max_lost_share is not None or spec.area_radius_m is not None
        if need_sp:
            keys_by_period: dict[str, list] = {}
            for k in keys:
                keys_by_period.setdefault(k[1], []).append(k)
            sp = []            # (stop, period) served in baseline
            for p, ks in sorted(keys_by_period.items()):
                stops = set()
                for k in ks:
                    if math.isfinite(base[k]):
                        stops |= set(route_stops.get(k[0], ()))
                for s in sorted(stops):
                    sp.append((s, p))
            self.stop_periods = sp
            self.n_sp = len(sp)
            if spec.max_lost_share is not None:
                self.r4_allowed = int(math.floor(spec.max_lost_share * self.n_sp
                                                 + _EPS))
                self._r4 = self._incidence(sp, keys_by_period, route_stops,
                                           pos, None, stop_xy)
            if spec.area_radius_m is not None:
                self._r6 = self._incidence(sp, keys_by_period, route_stops,
                                           pos, float(spec.area_radius_m),
                                           stop_xy)

    @staticmethod
    def _incidence(sp, keys_by_period, route_stops, pos, radius, stop_xy):
        """For each stop-period, the key indices whose ON status covers it."""
        if radius is not None:
            from scipy.spatial import cKDTree
            ids = sorted(s for s in stop_xy)
            xy = np.array([stop_xy[s] for s in ids], dtype=float)
            tree = cKDTree(xy)
            idx_of = {s: i for i, s in enumerate(ids)}
        flat, offs = [], []
        route_by_stop_period: dict = {}
        for p, ks in keys_by_period.items():
            for k in ks:
                for s in route_stops.get(k[0], ()):
                    route_by_stop_period.setdefault((s, p), []).append(pos[k])
        for s, p in sp:
            if radius is None:
                cov = route_by_stop_period.get((s, p), [])
            else:
                if s not in idx_of:
                    raise ValueError(f"stop {s} has no projected coordinate; "
                                     f"R6 cannot be evaluated for it")
                near = tree.query_ball_point(xy[idx_of[s]], r=radius)
                cov = set()
                for j in near:
                    cov.update(route_by_stop_period.get((ids[j], p), []))
                cov = sorted(cov)
            if not cov:
                raise ValueError(f"stop-period {(s, p)} has no covering key")
            offs.append(len(flat))
            flat.extend(sorted(set(cov)))
        return np.array(flat, dtype=np.int64), np.array(offs, dtype=np.int64)

    # -- measurement -----------------------------------------------------
    def measure(self, h: np.ndarray) -> dict:
        on = np.isfinite(h)
        out = {"n_baseline_served_rp": int(len(self.B)),
               "n_off_baseline_served": int((~on[self.B]).sum()),
               "n_baseline_stop_periods": int(self.n_sp)}
        if self.spec.max_headway is not None:
            out["r1_over_cap"] = int((h[self.B] > self.r1_cap[self.B]
                                      * (1 + _EPS)).sum())
        if len(self.span_idx):
            out["r3_span_off"] = int((~on[self.span_idx]).sum())
        if self._r4 is not None:
            f, o = self._r4
            cov = np.maximum.reduceat(on[f].astype(np.int8), o)
            out["r4_lost_stop_periods"] = int(self.n_sp - cov.sum())
        if self._r6 is not None:
            f, o = self._r6
            cov = np.maximum.reduceat(on[f].astype(np.int8), o)
            out["r6_uncovered_stop_periods"] = int(self.n_sp - cov.sum())
        return out

    def violation(self, h: np.ndarray) -> float:
        m = self.measure(h)
        v = 0
        v += m.get("r1_over_cap", 0)
        if self.r2_allowed is not None:
            v += max(0, m["n_off_baseline_served"] - self.r2_allowed)
        v += m.get("r3_span_off", 0)
        if self.r4_allowed is not None:
            v += max(0, m["r4_lost_stop_periods"] - self.r4_allowed)
        v += m.get("r6_uncovered_stop_periods", 0)
        return float(v)

    # -- efficiency: rungs no feasible plan can use ----------------------
    def filter_ladders(self, ladders: dict) -> dict:
        must_on = set(int(i) for i in self.span_idx)
        if self.spec.max_headway is not None or self.r2_allowed == 0:
            must_on |= set(int(i) for i in self.B)
        out = dict(ladders)
        for i, k in enumerate(self.keys):
            lad = list(ladders[k])
            if i in must_on:
                lad = [v for v in lad if math.isfinite(v)]
            if self.spec.max_headway is not None and i in set(self.B.tolist()):
                lad = [v for v in lad if v <= self.r1_cap[i] * (1 + _EPS)]
            if not lad:
                raise ValueError(f"policy {self.spec.cell} leaves {k} no rung")
            out[k] = lad
        return out

    # -- a policy-feasible minimum-service start --------------------------
    def minimum_start(self, L: np.ndarray, L_len: np.ndarray,
                      idx: np.ndarray) -> np.ndarray:
        """From minimum service, switch OFF route-periods back ON (at their
        worst finite rung) until the policy holds. Deterministic: each step
        takes the candidate that most reduces the violation, ties broken by key
        order. Monotone constraints only, so the loop always terminates."""
        n = len(idx)
        idx = idx.copy()
        h = L[np.arange(n), idx].copy()
        v = self.violation(h)
        while v > 0:
            best = None
            for i in self.B.tolist():
                if math.isfinite(h[i]):
                    continue
                finite = [j for j in range(L_len[i]) if math.isfinite(L[i, j])]
                if not finite:
                    continue
                j = max(finite)
                old = h[i]
                h[i] = L[i, j]
                nv = self.violation(h)
                h[i] = old
                if best is None or nv < best[0]:
                    best = (nv, i, j)
            if best is None or best[0] >= v:
                raise ValueError(f"policy {self.spec.cell}: no single "
                                 f"activation reduces the violation ({v})")
            _, i, j = best
            idx[i] = j
            h[i] = L[i, j]
            v = best[0]
        return idx
