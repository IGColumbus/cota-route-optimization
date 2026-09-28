#!/usr/bin/env python3
"""Experiment 5 -- the MODELED operating-resource envelope.  SUPERSEDES the
treatment object in `src/cota_opt/exp5_resource.py` for production use.

WHY A NEW OBJECT, AND WHY THE OLD ONE IS KEPT
---------------------------------------------
`exp5_resource.ResourceEnvelope` defines its second resource as BLOCK-DERIVED
physical fleet per period (135/187/173/197/178/149, integral, floored). That is
internally consistent for a physical-fleet experiment, and it is preserved as
historical code, unmodified. It is not the resource the optimizer enforces.

What EXP4N's production loop actually constrains is `frequency._feasible`:

    fit.revenue_veh_hours  <= budget.vh_cap()        (hours)
    fit.peak_by_period[p]  <= budget.peak_cap(p)     (six periods)

where `fit.peak_by_period` is the CYCLE-OVER-HEADWAY concurrency proxy, summed
per period. EXP4N's common vector for that proxy is read from
`outputs/exp4_normalized/COMMON_RESOURCE_ENVELOPE.json`. Wiring the
block-derived fleet counts into `ResourceBudget.peak_vehicles_by_period` would
administer a physical-vehicle number to a function that measures concurrency --
the D5-C boundary `EXPERIMENT5_PREMISE_AUDIT.md` warned about. No conversion
between the two is attempted here, and the 1.307 interlining ratio is not an
exchange rate.

So Experiment 5 is re-stated as a MODELED OPERATING-RESOURCE FRONTIER over the
two quantities the solver enforces:

    hours   scheduled weekday revenue vehicle-hours       (continuous)
    peak    solver_peak_concurrency_proxy, six periods     (continuous)

The peak axis is proxy units. It is never "fleet", never "buses", and nothing
in this module converts it into either.

SCALING RULE
------------
    hours_cap(m)      = base_hours * m          exact float multiplication
    peak_cap_p(m)     = base_peak_p * m         exact, per period, NO flooring

The old `floor` rule applied to a count of physical vehicles. A continuous
proxy has no integer quantum, so flooring would change the treatment for no
reason. At m = 1.0 the multiplication is the identity in IEEE-754, which is
asserted: the 100/100 cell IS the EXP4N envelope, bit for bit.

This module lives in `scripts/`, not `src/cota_opt`, for the reason
`envelope_fingerprint.py` does: EXP4N pinned `src_cota_opt_content_digest =
add5d0002d29aa49`, and keeping the evaluation path byte-identical means every
Experiment 5 cell is scored by EXP4N's own certification code -- provable by
digest equality, not merely claimed.
"""
from __future__ import annotations

import json
import math
import struct
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from envelope_fingerprint import (_legacy_rounded_digest,  # noqa: E402
                                  envelope_fingerprint_inputs,
                                  exact_fingerprint, exact_fingerprint_full)

PERIODS: tuple[str, ...] = ("early", "am_peak", "midday", "pm_peak",
                            "evening", "owl")

#: The preregistered levels, UNCHANGED from `exp5_resource.LEVELS`. They were
#: committed before EXP4N existed, so they were not chosen after seeing its
#: winner. Relative to the EXP4N common envelope.
LEVELS: tuple[float, ...] = (0.75, 0.90, 1.00, 1.10, 1.25, 1.50)

HOURS_SEMANTICS = "scheduled_weekday_revenue_vehicle_hours"
PEAK_SEMANTICS = "solver_peak_concurrency_proxy"
PEAK_INSTRUMENT = ("frequency.FrequencyModel.peak_vehicles = cycle/headway, "
                   "cycle = 2*runtime*(1+layover), summed per period; the "
                   "quantity frequency._feasible compares against "
                   "ResourceBudget.peak_vehicles_by_period")
SCALING_RULE = "continuous_exact_multiplication_no_rounding"

BASE_ARTIFACT = "outputs/exp4_normalized/COMMON_RESOURCE_ENVELOPE.json"
CONTRACT_ARTIFACT = "outputs/exp4_normalized/EXP4N_PRODUCTION_CONTRACT.json"
FINGERPRINT_ARTIFACT = "outputs/ENVELOPE_FINGERPRINT_V1.json"

#: Words that may never label the peak axis. Asserted on every payload.
FORBIDDEN_PEAK_WORDS = ("fleet", "bus", "buses", "vehicle count",
                        "physical vehicles")

ARM_JOINT = "A_joint"
ARM_HOURS = "B_hours_only"
ARM_PEAK = "C_peak_proxy_only"


class ModelResourceError(ValueError):
    """An envelope that cannot mean what it says."""


def _bits(x: float) -> int:
    return struct.unpack(">Q", struct.pack(">d", float(x)))[0]


@dataclass(frozen=True)
class ModelResourceEnvelope:
    """Hours cap + six-period solver peak-proxy caps. Both continuous."""

    hours_cap: float
    peak_proxy_caps: Mapping[str, float]
    hours_multiplier: float
    peak_multiplier: float
    source_artifact: str = BASE_ARTIFACT
    source_label: str = "reference_network_baseline_peak_by_period"
    base_envelope_digest: str = ""          # historical rounded, of the BASE
    base_exact_fingerprint: str = ""        # exact IEEE-754, of the BASE
    tolerance: float = 0.0
    hours_semantics: str = HOURS_SEMANTICS
    peak_semantics: str = PEAK_SEMANTICS
    scaling_rule: str = SCALING_RULE

    def __post_init__(self) -> None:
        if set(self.peak_proxy_caps) != set(PERIODS):
            raise ModelResourceError(
                f"peak proxy caps must cover exactly the six periods "
                f"{PERIODS}; got {sorted(self.peak_proxy_caps)}")
        for p, v in self.peak_proxy_caps.items():
            if not (isinstance(v, float) and math.isfinite(v) and v > 0):
                raise ModelResourceError(f"peak proxy cap {p}={v!r} must be a "
                                         f"positive finite float")
        if not (math.isfinite(self.hours_cap) and self.hours_cap > 0):
            raise ModelResourceError(f"hours cap {self.hours_cap!r}")
        if self.tolerance != 0.0:
            raise ModelResourceError("budget tolerance must stay 0.0, as in "
                                     "EXP4N")
        if self.peak_semantics != PEAK_SEMANTICS:
            raise ModelResourceError(
                f"peak semantics {self.peak_semantics!r} is not "
                f"{PEAK_SEMANTICS!r}. The enforced quantity is a concurrency "
                f"proxy; it is not fleet.")
        if self.scaling_rule != SCALING_RULE:
            raise ModelResourceError(f"scaling rule {self.scaling_rule!r}")
        for m in (self.hours_multiplier, self.peak_multiplier):
            if not (math.isfinite(m) and m > 0):
                raise ModelResourceError(f"multiplier {m!r}")

    # -- identity -------------------------------------------------------------
    def _fp_inputs(self) -> dict:
        return envelope_fingerprint_inputs(
            {p: float(self.peak_proxy_caps[p]) for p in PERIODS},
            float(self.hours_cap), float(self.tolerance), self.source_label)

    @property
    def exact_fingerprint(self) -> str:
        """Exact IEEE-754 fingerprint of THIS cell's enforced caps."""
        return exact_fingerprint(self._fp_inputs())

    @property
    def exact_fingerprint_full(self) -> str:
        return exact_fingerprint_full(self._fp_inputs())

    @property
    def rounded_envelope_digest(self) -> str:
        """The historical round(x, 9) digest algorithm, for continuity only.
        Necessary, not sufficient (docs/ENVELOPE_DIGEST_INSUFFICIENCY.md)."""
        return _legacy_rounded_digest(
            {p: float(self.peak_proxy_caps[p]) for p in PERIODS},
            float(self.hours_cap), float(self.tolerance), self.source_label)

    def dominates(self, other: "ModelResourceEnvelope") -> bool:
        """Every cap here is >= other's, compared on the exact floats."""
        if self.hours_cap < other.hours_cap:
            return False
        return all(self.peak_proxy_caps[p] >= other.peak_proxy_caps[p]
                   for p in PERIODS)

    # -- the only bridge into the optimizer -----------------------------------
    def to_constraints(self, config_constraints: dict) -> dict:
        """The constraints dict EXP4N's launcher builds, with these caps.

        Mirrors `scripts/exp4n_launch.build_constraints` field for field:
        hours overridden, `peak_fleet_by_period` an explicit dict (so
        `exp2.py:326` takes it verbatim), tolerance 0.0. The key name
        `peak_fleet_by_period` is the CONFIG's name for the budget slot; what
        is placed in it is the concurrency proxy, and the payload says so.
        """
        c = config_constraints
        assert c["resource"]["peak_fleet_by_period"] == "baseline", (
            "the config sentinel changed; the launcher, not the config, must "
            "supply the peak vector")
        tol = float(c["resource"].get("budget_tolerance", 0.0))
        assert tol == 0.0, f"budget_tolerance is {tol}, must remain 0.0"
        cons = {**c, "resource": {
            **c["resource"],
            "weekday_revenue_vehicle_hours": float(self.hours_cap),
            "peak_fleet_by_period": {p: float(self.peak_proxy_caps[p])
                                     for p in PERIODS},
        }}
        r = cons["resource"]
        assert isinstance(r["peak_fleet_by_period"], dict)
        assert set(r["peak_fleet_by_period"]) == set(PERIODS)
        assert float(r.get("budget_tolerance", 0.0)) == 0.0
        return cons

    def payload(self) -> dict:
        p = {
            "hours_cap": repr(float(self.hours_cap)),
            "peak_proxy_caps": {q: repr(float(self.peak_proxy_caps[q]))
                                for q in PERIODS},
            "hours_multiplier": self.hours_multiplier,
            "peak_multiplier": self.peak_multiplier,
            "hours_semantics": self.hours_semantics,
            "peak_semantics": self.peak_semantics,
            "peak_instrument": PEAK_INSTRUMENT,
            "peak_units": "proxy units (cycle-over-headway concurrency), NOT "
                          "physical vehicles",
            "scaling_rule": self.scaling_rule,
            "tolerance": self.tolerance,
            "source_artifact": self.source_artifact,
            "base_rounded_envelope_digest": self.base_envelope_digest,
            "base_exact_fingerprint": self.base_exact_fingerprint,
            "cell_rounded_envelope_digest": self.rounded_envelope_digest,
            "cell_exact_fingerprint": self.exact_fingerprint,
            "cell_exact_fingerprint_full": self.exact_fingerprint_full,
        }
        _assert_no_fleet_language(p)
        return p


def _assert_no_fleet_language(payload: dict) -> None:
    """The peak axis is labelled as a proxy, never as fleet or buses.

    `peak_semantics` may contain none of the forbidden words. `peak_units`
    must declare proxy units and may mention physical vehicles only to deny
    them."""
    sem = str(payload.get("peak_semantics", "")).lower()
    if any(w in sem for w in FORBIDDEN_PEAK_WORDS):
        raise ModelResourceError(f"peak semantics uses fleet language: {sem!r}")
    units = str(payload.get("peak_units", "")).lower()
    if not units.startswith("proxy units"):
        raise ModelResourceError(f"peak units must declare proxy units: {units!r}")
    if any(w in units for w in ("fleet", "bus")):
        raise ModelResourceError(f"peak units use fleet language: {units!r}")


def load_base(root: Path | None = None) -> ModelResourceEnvelope:
    """The 100/100 envelope, read from the frozen artifact and cross-checked.

    Three independent assertions, all against artifacts, none against text
    typed here: the peak/hours floats equal the IEEE-754 bit patterns recorded
    in the EXP4N production contract; the exact fingerprint equals the one in
    ENVELOPE_FINGERPRINT_V1.json; the historical rounded digest equals the one
    the envelope artifact carries.
    """
    root = Path(root) if root else ROOT
    env = json.loads((root / BASE_ARTIFACT).read_text())
    con = json.loads((root / CONTRACT_ARTIFACT).read_text())
    fpa = json.loads((root / FINGERPRINT_ARTIFACT).read_text())
    peak = {p: float(env["peak_fleet_by_period"][p]) for p in PERIODS}
    hours = float(env["weekday_revenue_vehicle_hours"])
    tol = float(env["budget_tolerance"])

    ex = con["exact_peak_envelope_used_by_this_run"]
    for p in PERIODS:
        if _bits(peak[p]) != int(ex["values"][p]["int_bits"]):
            raise ModelResourceError(f"{p}: artifact float does not match the "
                                     f"EXP4N contract's recorded bit pattern")
    if _bits(hours) != int(ex["hours_cap"]["int_bits"]):
        raise ModelResourceError("hours cap bits differ from the EXP4N contract")

    base = ModelResourceEnvelope(
        hours_cap=hours, peak_proxy_caps=peak, hours_multiplier=1.0,
        peak_multiplier=1.0, source_label=str(env["source"]),
        base_envelope_digest=str(env["envelope_digest"]),
        base_exact_fingerprint=str(fpa["exact_envelope_fingerprint"]),
        tolerance=tol)
    if base.exact_fingerprint != fpa["exact_envelope_fingerprint"]:
        raise ModelResourceError(
            f"base exact fingerprint {base.exact_fingerprint} != artifact "
            f"{fpa['exact_envelope_fingerprint']}")
    if base.rounded_envelope_digest != env["envelope_digest"]:
        raise ModelResourceError(
            f"base rounded digest {base.rounded_envelope_digest} != artifact "
            f"{env['envelope_digest']}")
    return base


def scale(base: ModelResourceEnvelope, hours_m: float,
          peak_m: float) -> ModelResourceEnvelope:
    """Continuous exact scaling from the BASE only (never chained)."""
    if base.hours_multiplier != 1.0 or base.peak_multiplier != 1.0:
        raise ModelResourceError("scale() applies to the base envelope only; "
                                 "chaining would compound multipliers silently")
    out = ModelResourceEnvelope(
        hours_cap=base.hours_cap * hours_m,
        peak_proxy_caps={p: base.peak_proxy_caps[p] * peak_m for p in PERIODS},
        hours_multiplier=float(hours_m), peak_multiplier=float(peak_m),
        source_artifact=base.source_artifact, source_label=base.source_label,
        base_envelope_digest=base.base_envelope_digest,
        base_exact_fingerprint=base.base_exact_fingerprint,
        tolerance=base.tolerance)
    if hours_m == 1.0 and peak_m == 1.0:
        assert out.exact_fingerprint == base.exact_fingerprint
    return out


def cell_id(hours_m: float, peak_m: float) -> str:
    h, p = round(hours_m * 100), round(peak_m * 100)
    if h == p:
        return f"J{h:03d}"
    if p == 100:
        return f"H{h:03d}"
    if h == 100:
        return f"P{p:03d}"
    raise ModelResourceError(f"({hours_m}, {peak_m}) is not a cell of the "
                             f"preregistered three-arm design")


@dataclass(frozen=True)
class Cell:
    id: str
    arm: str
    envelope: ModelResourceEnvelope

    def payload(self) -> dict:
        return {"cell_id": self.id, "arm": self.arm, **self.envelope.payload()}


def grid(base: ModelResourceEnvelope,
         levels: tuple[float, ...] = LEVELS) -> list[Cell]:
    """16 unique cells: Arm A joint (6), Arm B hours-only (5), Arm C
    peak-proxy-only (5). The shared 100/100 cell is Arm A's J100."""
    cells = [Cell(cell_id(m, m), ARM_JOINT, scale(base, m, m)) for m in levels]
    cells += [Cell(cell_id(m, 1.0), ARM_HOURS, scale(base, m, 1.0))
              for m in levels if m != 1.0]
    cells += [Cell(cell_id(1.0, m), ARM_PEAK, scale(base, 1.0, m))
              for m in levels if m != 1.0]
    ids = [c.id for c in cells]
    fps = [c.envelope.exact_fingerprint for c in cells]
    if len(set(ids)) != len(ids) or len(set(fps)) != len(fps):
        raise ModelResourceError("duplicate treatment identity in the grid")
    return cells


def nested_pairs(cells: list[Cell]) -> list[tuple[Cell, Cell]]:
    """(looser, tighter) pairs where every cap of `looser` >= `tighter`'s."""
    out = []
    for a in cells:
        for b in cells:
            if a.id != b.id and a.envelope.dominates(b.envelope):
                out.append((a, b))
    return out


RETIRED = {
    "module": "src/cota_opt/exp5_resource.py",
    "status": "SUPERSEDED FOR PRODUCTION; preserved unmodified as history",
    "why": ("its second resource is block-derived physical fleet "
            "(135/187/173/197/178/149, integral, floored), which the "
            "production optimizer does not enforce; frequency._feasible "
            "constrains the cycle-over-headway peak proxy. The object was "
            "internally consistent for a physical-fleet experiment and does "
            "not match the resource the solver constrains."),
    "superseded_design": ("September 23 Exp 5 plan: six peak cells, one "
                          "predicted-null hours cell (Arm B), and 30/35/40% "
                          "hours service cuts (Arm C)"),
    "why_design_superseded": (
        "built on the premise that hours are slack (~36-37% used), measured "
        "on the LEGACY endogenous-cap Exp 4 plans. Under EXP4N's common "
        "envelope every certified plan uses 99.92-100.00% of the hours cap "
        "and N4 uses 2517.0171064814813 of 2517.1833333333334. The hours-null "
        "and deep-cut logic describe an operating point that no longer "
        "exists."),
}
