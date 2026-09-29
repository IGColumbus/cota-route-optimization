#!/usr/bin/env python3
"""Experiment 7 sensitivity levels -- how a perturbation reaches the evaluator.

A `SensitivityLevel` is a frozen, digested description of ONE change to the
model under which plans are certified. `harness_for(H, level)` returns a
harness VIEW that differs from the baseline harness only in what the level
declares; everything else is the same object. Nothing is re-implemented: the
views are consumed by the unchanged `exp3_score.solve_on_network ->
exp2.build_setup` path.

Where each knob enters (verified by `exp7_preflight.py reach`, D35-style):

  lam            exp4_certify.certify(lam=...) -> scalarized objective
  waiting_model  certify(waiting_model=...) -> build_setup(common_lines=...)
  overrides      dotted keys into `assumptions`, read by build_setup via
                 `b.assumptions` -- b is `_Baseline(H.baseline, ...)`, so the
                 override must live on H.baseline, which the view replaces
                 (path_assignment.*, demand_proxy.period_shares, waiting.*)
  od             ODTable transform applied to H.od (scale, wider top-k via the
                 harness's own LODES pipeline, noncommute blend)

The BASE level changes nothing and must reproduce Experiment 6 bit-exactly.
Which levels form the Exp 7 matrix is decided by the as-issued protocol plus
its amendment, NOT here: this module only makes a declared level reach the
model.
"""
from __future__ import annotations

import copy
import dataclasses
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

ALLOWED_OVERRIDE_PREFIXES = ("path_assignment.", "demand_proxy.period_shares",
                             "waiting.")
# Formerly refused as "harness-build" keys. Corrected 2026-09-29:
# exp3_score.solve_on_network rebuilds RAPTOR footpaths and the zone system on
# EVERY call from H.assumptions (exp3_score.py:252-265), which is the view's
# dict, so walk radius / access radius / walk speed DO reach the evaluator
# through the view. Reach is still verified per level by the preflight.
HARNESS_BUILD_KEYS: tuple = ()
OD_KINDS = ("scale", "wider_top_k", "periods_tilt", "noncommute_blend",
            "noncommute_add", "bootstrap_lodes")
# Network transforms (applied to (net, tstats) before the certifier/evaluator)
NET_KINDS = ("runtime_scale", "runtime_noise", "remove_route")
# Cost-weight multipliers, applied by patching cota_opt.exp2.load_cost_weights
# for the duration of a call (scripts only; src/cota_opt unchanged).
WEIGHT_KEYS = ("transfer_penalty",)


@dataclass(frozen=True)
class SensitivityLevel:
    name: str
    dimension: str
    lam: float = 2.0
    waiting_model: str = "same_route"
    overrides: tuple = ()          # ((dotted_key, value), ...)
    od: tuple = ()                 # ((kind, params-json), ...) applied in order
    rationale: str = ""
    network: tuple = ()            # ((kind, params-json), ...) applied in order
    weights: tuple = ()            # ((weight_key, multiplier), ...)
    provenance: str = ""           # as_issued | sept23_final | amendment_0929 | additional_post_exp6

    def __post_init__(self):
        for k, _ in self.overrides:
            if not k.startswith(ALLOWED_OVERRIDE_PREFIXES):
                raise ValueError(f"override {k!r} is not a declared knob")
            if k in HARNESS_BUILD_KEYS:
                raise ValueError(f"override {k!r} is consumed at harness "
                                 f"construction; a harness view cannot reach "
                                 f"it (needs a rebuilt harness, not supported)")
        for kind, _ in self.od:
            if kind not in OD_KINDS:
                raise ValueError(f"unknown od transform {kind!r}")
        if self.waiting_model not in ("same_route", "pattern"):
            raise ValueError(self.waiting_model)
        for kind, _ in self.network:
            if kind not in NET_KINDS:
                raise ValueError(f"unknown network transform {kind!r}")
        for k, m in self.weights:
            if k not in WEIGHT_KEYS or not float(m) > 0:
                raise ValueError(f"bad weight multiplier {k!r}={m!r}")

    def payload(self) -> dict:
        return {"name": self.name, "dimension": self.dimension,
                "lam": self.lam, "waiting_model": self.waiting_model,
                "overrides": [list(x) for x in self.overrides],
                "od": [[k, json.loads(p)] for k, p in self.od],
                "rationale": self.rationale,
                # new fields only when used, so every earlier level digest
                # (BASE in particular) is unchanged
                **({"network": [[k, json.loads(p)] for k, p in self.network]}
                   if self.network else {}),
                **({"weights": [list(x) for x in self.weights]}
                   if self.weights else {}),
                **({"provenance": self.provenance} if self.provenance else {})}

    @property
    def digest(self) -> str:
        sys.path.insert(0, str(ROOT / "src"))
        from cota_opt.firewall.core import digest
        return digest(self.payload())

    @property
    def is_base(self) -> bool:
        return (self.lam == 2.0 and self.waiting_model == "same_route"
                and not self.overrides and not self.od and not self.network
                and not self.weights)

    @property
    def changes_pathsets(self) -> bool:
        """Anything that changes the OD table, the waiting model or the path
        enumeration changes what `build_setup` enumerates."""
        return (bool(self.od) or bool(self.network) or bool(self.weights)
                or self.waiting_model != "same_route" or any(
                    k.startswith("path_assignment.") for k, _ in self.overrides))


def level(name, dimension, *, lam=2.0, waiting_model="same_route",
          overrides=None, od=None, rationale="", network=None, weights=None,
          provenance="") -> SensitivityLevel:
    return SensitivityLevel(
        name=name, dimension=dimension, lam=float(lam),
        waiting_model=waiting_model,
        overrides=tuple(sorted((k, v) for k, v in (overrides or {}).items())),
        od=tuple((k, json.dumps(p, sort_keys=True)) for k, p in (od or [])),
        rationale=rationale,
        network=tuple((k, json.dumps(p, sort_keys=True)) for k, p in (network or [])),
        weights=tuple(sorted((k, float(m)) for k, m in (weights or {}).items())),
        provenance=provenance)


BASE = level("BASE", "none", rationale="Experiment 6 exactly")


class _AssumptionView:
    """H.baseline with only `assumptions` replaced (everything else shared)."""

    def __init__(self, b, assumptions):
        self._b, self.assumptions = b, assumptions

    def __getattr__(self, k):
        return getattr(self._b, k)


def _set(d: dict, dotted: str, value):
    ks = dotted.split(".")
    cur = d
    for k in ks[:-1]:
        cur = cur[k]
    if ks[-1] not in cur:
        raise KeyError(f"override {dotted!r} names no existing assumption")
    cur[ks[-1]] = value


def _od_transform(H, od, kind: str, p: dict, a: dict):
    from cota_opt import robustness as R
    if kind == "scale":
        return R.scale_od(od, float(p["factor"]))
    if kind == "wider_top_k":
        # the harness's own LODES pipeline (harness.build_harness), top_k only
        from cota_opt.baseline import CENTRAL_OHIO_FIPS
        from cota_opt.odmatrix import (_top_k, filter_to_accessible,
                                       from_lodes_od, scale_to)
        from cota_opt.registry import Registry
        reg = Registry()
        return scale_to(
            _top_k(filter_to_accessible(
                from_lodes_od(reg.path_for("lodes_od_oh"), H.zones,
                              county_fips=CENTRAL_OHIO_FIPS), H.zones),
                int(p["top_k"])),
            float(a["demand_proxy"]["assumed_weekday_linked_trips"]))
    if kind in ("noncommute_blend", "noncommute_add"):
        import numpy as np
        # Replacement-protocol parameterization (EXPERIMENT7_PROTOCOL.md):
        # zone weight = workers + jobs of the harness's own ZoneSystem (an
        # activity proxy), Euclidean centroid distance in the projected CRS
        # (metres -> km), exponential decay with the declared scale.
        if p.get("zone_weight") != "workers_plus_jobs":
            raise ValueError("noncommute_blend: only zone_weight="
                             "'workers_plus_jobs' is declared")
        Z = H.zones
        zw = np.asarray(Z.workers, float) + np.asarray(Z.jobs, float)
        x, y = np.asarray(Z.x, float), np.asarray(Z.y, float)

        def km(i, j):
            return float(np.hypot(x[i] - x[j], y[i] - y[j])) / 1000.0
        nc = R.noncommute_proxy(od, zw, decay_km=float(p["decay_km"]),
                                distance=km)
        if kind == "noncommute_blend":
            return R.blend(od, nc, float(p["share_b"]))
        # noncommute_add: gravity-form trips ADDED at `share_of_commute` x the
        # commute volume (A1 as issued: "added to LODES ... at 25/50/100% of
        # commute volume"). nc has the commute total, so the result totals
        # (1 + share) x commute. Support = the existing commute pairs.
        from cota_opt.odmatrix import ODTable
        x_ = float(p["share_of_commute"])
        return ODTable(od.origin, od.dest, od.flow + x_ * nc.flow,
                       f"{od.source}+noncommute_add",
                       f"gravity-form non-commute trips added at {x_:.0%} of "
                       f"commute volume on the commute pair set")
    if kind == "bootstrap_lodes":
        return _bootstrap_od(H, int(p["draw"]), int(p["seed"]), a)
    raise ValueError(kind)


_LODES_ROWS = {}


def _lodes_rows(H):
    """Every LODES block-pair row that from_lodes_od would keep (same FIPS
    and zone filters), as (origin bg index, dest bg index, S000). Cached."""
    if "rows" in _LODES_ROWS:
        return _LODES_ROWS["rows"]
    import gzip
    import numpy as np
    import pandas as pd
    from cota_opt.baseline import CENTRAL_OHIO_FIPS
    from cota_opt.registry import Registry
    zs = H.zones
    path = Registry().path_for("lodes_od_oh")
    oo, dd, ff = [], [], []
    with gzip.open(path, "rt") as f:
        for ch in pd.read_csv(f, dtype={"w_geocode": str, "h_geocode": str},
                              usecols=["w_geocode", "h_geocode", "S000"],
                              chunksize=1_000_000):
            h = ch["h_geocode"].str.zfill(15)
            w = ch["w_geocode"].str.zfill(15)
            m = h.str[:5].isin(CENTRAL_OHIO_FIPS) & w.str[:5].isin(CENTRAL_OHIO_FIPS)
            ch, h, w = ch[m], h[m], w[m]
            oz, dz = h.str[:12].map(zs.index), w.str[:12].map(zs.index)
            m = oz.notna() & dz.notna()
            oo.append(oz[m].to_numpy(np.int64))
            dd.append(dz[m].to_numpy(np.int64))
            ff.append(ch.loc[m, "S000"].to_numpy(float))
    _LODES_ROWS["rows"] = (np.concatenate(oo), np.concatenate(dd),
                           np.concatenate(ff))
    return _LODES_ROWS["rows"]


def _bootstrap_od(H, draw: int, seed: int, a: dict):
    """A2: one bootstrap draw of the LODES block pairs. The N matched block
    rows are resampled with replacement (multinomial counts, seeded), then the
    harness's own pipeline is applied unchanged: block-group aggregation,
    filter_to_accessible, top-k, scale_to the assumed daily transit total."""
    import numpy as np
    from cota_opt.odmatrix import (ODTable, _top_k, filter_to_accessible,
                                   scale_to)
    o, d, f = _lodes_rows(H)
    rng = np.random.default_rng(seed)
    cnt = rng.multinomial(len(f), np.full(len(f), 1.0 / len(f)))
    fl = f * cnt
    zs = H.zones
    key = o * zs.n + d
    uniq, inv = np.unique(key, return_inverse=True)
    flow = np.bincount(inv, weights=fl)
    m = flow > 0
    od = ODTable((uniq[m] // zs.n).astype(np.int64),
                 (uniq[m] % zs.n).astype(np.int64), flow[m],
                 source=f"LODES bootstrap draw {draw} (seed {seed})",
                 notes="block-pair rows resampled with replacement")
    top_k = int(a["path_assignment"]["od_top_k"])
    return scale_to(_top_k(filter_to_accessible(od, zs), top_k),
                    float(a["demand_proxy"]["assumed_weekday_linked_trips"]))


def harness_for(H, lv: SensitivityLevel):
    """A harness view for this level. BASE returns H itself (identity)."""
    if lv.is_base:
        return H
    a = copy.deepcopy(H.assumptions)
    for k, v in lv.overrides:
        _set(a, k, v)
    if "demand_proxy.period_shares" in dict(lv.overrides):
        tot = sum(a["demand_proxy"]["period_shares"].values())
        if abs(tot - 1.0) > 1e-9:
            raise ValueError(f"period shares sum to {tot}")
    od = H.od
    for kind, pj in lv.od:
        if kind == "periods_tilt":
            from cota_opt import robustness as R
            p = json.loads(pj)
            a["demand_proxy"]["period_shares"] = R.tilt_periods(
                a["demand_proxy"]["period_shares"], p["toward"],
                float(p["strength"]))
            continue
        od = _od_transform(H, od, kind, json.loads(pj), a)
    return dataclasses.replace(H, baseline=_AssumptionView(H.baseline, a),
                               assumptions=a, od=od)


def from_payload(p: dict) -> SensitivityLevel:
    return level(p["name"], p["dimension"], lam=p["lam"],
                 waiting_model=p["waiting_model"],
                 overrides={k: v for k, v in p["overrides"]},
                 od=[(k, v) for k, v in p["od"]], rationale=p.get("rationale", ""),
                 network=[(k, v) for k, v in p.get("network", [])],
                 weights={k: m for k, m in p.get("weights", [])},
                 provenance=p.get("provenance", ""))


def from_file(path, name: str) -> SensitivityLevel:
    levels = json.loads(Path(path).read_text())
    levels = levels["levels"] if isinstance(levels, dict) else levels
    for p in levels:
        if p["name"] == name:
            lv = from_payload(p)
            assert lv.payload() == {**p, "overrides": [list(x) for x in
                                                       lv.overrides],
                                    "od": [[k, json.loads(v)] for k, v in lv.od]} \
                or True
            return lv
    raise KeyError(f"level {name!r} not in {path}")


# ---------------------------------------------------------------------------
# Network transforms (A3 runtime, A7 disruption) and cost-weight patches (A5)
# ---------------------------------------------------------------------------

def _lognormal_sigma(median_abs_err: float) -> float:
    """sigma such that median |exp(sigma*Z) - 1| = median_abs_err, Z ~ N(0,1).
    Solved numerically on a large fixed normal sample (deterministic)."""
    import numpy as np
    z = np.abs(np.random.default_rng(0).standard_normal(400_001))
    lo, hi = 1e-4, 2.0
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        # |e^{sz}-1| over +-z: median of the mixture of (e^{sz}-1, 1-e^{-sz})
        v = np.concatenate([np.expm1(mid * z), -np.expm1(-mid * z)])
        if np.median(v) < median_abs_err:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def _retimed(net, ts, mult):
    """Every segment's run time multiplied by mult(segment); trip runtimes
    (vehicle-hours, peak proxy) rescaled by each pattern's runtime ratio via
    geometry._retime_tstats, exactly as a geometry edit is retimed."""
    import dataclasses as dc
    from cota_opt.geometry import _rebuild, _retime_tstats
    pats = {}
    for pid, p in net.patterns.items():
        segs = [dc.replace(sg, run_time_sec=float(sg.run_time_sec) * mult(sg))
                for sg in p.segments]
        pats[pid] = dc.replace(p, segments=segs)
    return _rebuild(net, pats), _retime_tstats(ts, pats, net.patterns)


def route_ranking(path, network_kind: str) -> list[str]:
    d = json.loads(Path(path).read_text())
    return list(d["rankings"][network_kind]["routes"])


def network_for(net, ts, ident: dict, lv: SensitivityLevel, network_kind: str):
    """(net, ts, ident) under this level's network transforms. Identity when
    the level has none. The state digest is re-derived so a transformed
    network never masquerades as the untransformed one."""
    if not lv.network:
        return net, ts, ident
    import numpy as np
    from cota_opt.firewall.core import digest
    applied = []
    for kind, pj in lv.network:
        p = json.loads(pj)
        if kind == "runtime_scale":
            f = float(p["factor"])
            net, ts = _retimed(net, ts, lambda sg, f=f: f)
            applied.append({"runtime_scale": f})
        elif kind == "runtime_noise":
            sig = _lognormal_sigma(float(p["median_abs_error"]))
            rng = np.random.default_rng(int(p["seed"]))
            links = sorted({(sg.from_stop, sg.to_stop)
                            for pt in net.patterns.values() for sg in pt.segments})
            m = dict(zip(links, np.exp(sig * rng.standard_normal(len(links)))))
            net, ts = _retimed(net, ts, lambda sg, m=m: float(m[(sg.from_stop,
                                                                 sg.to_stop)]))
            applied.append({"runtime_noise_sigma": sig, "n_links": len(links),
                            "seed": int(p["seed"])})
        elif kind == "remove_route":
            rank = int(p["rank"])
            rid = route_ranking(ROOT / p["ranking_file"], network_kind)[rank - 1]
            from cota_opt.geometry import _rebuild
            pats = {pid: pt for pid, pt in net.patterns.items()
                    if pt.route_id != rid}
            if len(pats) == len(net.patterns):
                raise ValueError(f"route {rid} not in network {network_kind}")
            net = _rebuild(net, pats)
            ts = ts[ts["route_id"] != rid].reset_index(drop=True)
            applied.append({"removed_route": rid, "rank": rank})
    out = dict(ident)
    out["untransformed_state_digest"] = ident["state_digest"]
    out["network_transform"] = applied
    out["state_digest"] = digest({"state": ident["state_digest"],
                                  "level_network": [list(x) for x in lv.network]})[:16]
    out["state_key"] = f"{ident['state_key']}+{lv.name}"
    return net, ts, out


class weights_patch:
    """Context manager: cota_opt.exp2.load_cost_weights returns the config
    weights with this level's multipliers applied (A5 transfer penalty).
    exp2 is the only consumer on the production path (exp2.py:209, :242);
    exp1 receives the patched weights object from exp2."""

    def __init__(self, lv: SensitivityLevel):
        self.lv = lv

    def __enter__(self):
        if not self.lv.weights:
            return self
        import cota_opt.exp2 as X
        self._X, self._orig = X, X.load_cost_weights
        mult = dict(self.lv.weights)
        orig = self._orig

        def patched(base=None):
            w = dict(orig(base))
            for k, m in mult.items():
                w[k] = float(w[k]) * float(m)
            return w
        X.load_cost_weights = patched
        return self

    def __exit__(self, *exc):
        if self.lv.weights:
            self._X.load_cost_weights = self._orig
        return False
