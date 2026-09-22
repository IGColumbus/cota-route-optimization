#!/usr/bin/env python3
"""Resolve the EXP4N common resource envelope ONCE and freeze it with a digest.

This is the whole repair. In the legacy run the peak arm's `"baseline"`
sentinel was resolved inside `exp2.build_setup` against whatever network it was
handed — which, for a candidate, is that candidate's own geometry. Here the
sentinel is resolved a single time, against the REFERENCE network, before any
candidate exists, and written to an artifact. The launcher then passes the
resolved vector explicitly, so `exp2.py:324` never runs for a candidate and
`exp2.py:326` takes the dict verbatim instead.

That is exactly how the hours arm has always worked (`exp4_launch.py` overrides
`weekday_revenue_vehicle_hours` from `CANONICAL_ENVELOPE.json`). The peak arm
simply never got the same treatment.

`src/cota_opt` is NOT modified. Nothing about the demand model, the objective,
the exact evaluator, convergence, ladders, geometries, the hours cap, the peak
USAGE calculation, tolerance or the search neighbourhood changes.
"""
from __future__ import annotations
import json, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src")); sys.path.insert(0, str(ROOT / "scripts"))
OUT = ROOT / "outputs" / "exp4_normalized"
PERIODS = ("early", "am_peak", "midday", "pm_peak", "evening", "owl")

# Read off judge.budget live during the 2026-09-21 diagnostic and reproduced by
# the audit; the freeze below must agree with these to 4dp or it is a different
# envelope than the one the audit pilot validated.
AUDIT_REFERENCE = {
    "early": 85.2821, "am_peak": 162.0094, "midday": 159.1728,
    "pm_peak": 176.4931, "evening": 140.1946, "owl": 35.5574,
}


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    from cota_opt.configs import load_constraints, load_cost_weights
    from cota_opt.cost import CostWeights
    from cota_opt.exp1 import build_setup as exp1_setup
    from cota_opt.firewall.core import digest
    from exp4_c10_fixtures import _boot

    env = json.loads((ROOT / "outputs" / "CANONICAL_ENVELOPE.json").read_text())
    VH_CAP = float(env["weekday_revenue_vehicle_hours"])
    _c = load_constraints()
    if _c["resource"]["peak_fleet_by_period"] != "baseline":
        print("FATAL: the config sentinel is not 'baseline'; this script's "
              "premise no longer holds."); return 2
    TOL = float(_c["resource"].get("budget_tolerance", 0.0))
    if TOL != 0.0:
        print(f"FATAL: budget_tolerance is {TOL}, expected 0.0"); return 2

    cons = {**_c, "resource": {**_c["resource"],
                               "weekday_revenue_vehicle_hours": VH_CAP}}
    w = CostWeights.from_config(load_cost_weights())
    st = _boot(); H = st["H"]

    # Resolve the sentinel ONCE, against the reference network, exactly as
    # exp2.build_setup would: services from exp1, baseline plan evaluated,
    # peak_by_period taken off that fitness. `PathBasedModel` inherits the
    # resource physics unchanged (exp2.py:53), so this is the same quantity
    # candidate usage is measured in.
    e1 = exp1_setup(H.baseline, constraints=cons, weights=w)
    fit = e1.model.evaluate(e1.baseline_plan)
    peak = {p: float(fit.peak_by_period[p]) for p in PERIODS}

    worst = max(abs(peak[p] - AUDIT_REFERENCE[p]) for p in PERIODS)
    if worst > 5e-5:
        print(f"FATAL: frozen envelope disagrees with the audit-validated "
              f"reference by {worst:.3e}; this is not the envelope the pilot "
              f"was run against."); return 2

    payload = {
        "envelope_id": "EXP4N_COMMON_RESOURCE_ENVELOPE",
        "frozen_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "source": "reference_network_baseline_peak_by_period",
        "resolved_once_against": "the unedited reference network, before any candidate exists",
        "instrument": ("FrequencyModel.peak_vehicles = cycle/headway, "
                       "cycle = 2*runtime*(1+layover), summed per period — the "
                       "identical quantity candidate usage is measured in"),
        "periods": list(PERIODS),
        "peak_fleet_by_period": {p: peak[p] for p in PERIODS},
        "weekday_revenue_vehicle_hours": VH_CAP,
        "hours_source": "outputs/CANONICAL_ENVELOPE.json",
        "canonical_envelope_digest": str(env["envelope_digest"]),
        "budget_tolerance": TOL,
        "reference_baseline_revenue_veh_hours": float(fit.revenue_veh_hours),
        "n_reference_route_periods": len(e1.model.services),
        "agreement_with_audit_reference_worst_abs": worst,
        "IMMUTABLE": ("every EXP4N candidate must be certified against exactly "
                      "this vector; the launcher asserts it and every result "
                      "carries the digest below"),
        "NOT": ("not a claim that this envelope is a correct or operationally "
                "achievable fleet — it is a COMMON one, measured with a "
                "cycle/headway proxy"),
    }
    payload["envelope_digest"] = digest({
        "peak": {p: round(peak[p], 9) for p in PERIODS},
        "hours": round(VH_CAP, 9),
        "tolerance": TOL,
        "source": payload["source"],
    })
    p = OUT / "COMMON_RESOURCE_ENVELOPE.json"
    p.write_text(json.dumps(payload, indent=1))
    print(f"wrote {p}")
    print(f"  digest {payload['envelope_digest']}")
    for q in PERIODS:
        print(f"  {q:<9} {peak[q]:14.9f}   (audit ref {AUDIT_REFERENCE[q]})")
    print(f"  hours  {VH_CAP:.6f}   tolerance {TOL}")
    print(f"  agreement with the audit-validated reference: worst |d| {worst:.3e}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
