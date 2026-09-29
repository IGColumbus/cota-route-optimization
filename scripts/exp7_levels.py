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
# Consumed when the HARNESS is built (RAPTOR footpaths, zone access), not by
# build_setup, so a harness VIEW cannot reach them: refused, fail-closed.
HARNESS_BUILD_KEYS = ("path_assignment.walk_radius_m",
                      "path_assignment.access_radius_m")
OD_KINDS = ("scale", "wider_top_k", "periods_tilt", "noncommute_blend")


@dataclass(frozen=True)
class SensitivityLevel:
    name: str
    dimension: str
    lam: float = 2.0
    waiting_model: str = "same_route"
    overrides: tuple = ()          # ((dotted_key, value), ...)
    od: tuple = ()                 # ((kind, params-json), ...) applied in order
    rationale: str = ""

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

    def payload(self) -> dict:
        return {"name": self.name, "dimension": self.dimension,
                "lam": self.lam, "waiting_model": self.waiting_model,
                "overrides": [list(x) for x in self.overrides],
                "od": [[k, json.loads(p)] for k, p in self.od],
                "rationale": self.rationale}

    @property
    def digest(self) -> str:
        sys.path.insert(0, str(ROOT / "src"))
        from cota_opt.firewall.core import digest
        return digest(self.payload())

    @property
    def is_base(self) -> bool:
        return (self.lam == 2.0 and self.waiting_model == "same_route"
                and not self.overrides and not self.od)

    @property
    def changes_pathsets(self) -> bool:
        """Anything that changes the OD table, the waiting model or the path
        enumeration changes what `build_setup` enumerates."""
        return bool(self.od) or self.waiting_model != "same_route" or any(
            k.startswith("path_assignment.") for k, _ in self.overrides)


def level(name, dimension, *, lam=2.0, waiting_model="same_route",
          overrides=None, od=None, rationale="") -> SensitivityLevel:
    return SensitivityLevel(
        name=name, dimension=dimension, lam=float(lam),
        waiting_model=waiting_model,
        overrides=tuple(sorted((k, v) for k, v in (overrides or {}).items())),
        od=tuple((k, json.dumps(p, sort_keys=True)) for k, p in (od or [])),
        rationale=rationale)


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
    if kind == "noncommute_blend":
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
        return R.blend(od, nc, float(p["share_b"]))
    raise ValueError(kind)


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
                 od=[(k, v) for k, v in p["od"]], rationale=p.get("rationale", ""))


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
