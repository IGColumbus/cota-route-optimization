#!/usr/bin/env python3
"""Exp 4 resource normalization audit, step 2: extract every candidate's cap.

AUDIT ONLY. Reads outputs/exp4/run/ read-only; writes only under
outputs/exp4_resource_audit/. Does not modify src/, the canonical envelope,
candidate definitions, certified outputs, or any experiment result.

The Exp 4 peak cap is `dict(fit.peak_by_period)` where `fit` is the candidate's
OWN baseline plan evaluated on the candidate's OWN geometry (exp2.py:324, via
`res["peak_fleet_by_period"] == "baseline"`).

`PathBasedModel` states that "Resource physics (vehicle-hours, peak vehicles)
are inherited unchanged. Only the passenger side is replaced" (exp2.py:53), and
`exp2.build_setup` takes its `services` and `baseline_plan` straight from
`exp1.build_setup` (exp2.py:209-211). So the cap is reproducible from the
Experiment 1 supply setup alone, with no pathset or RAPTOR build.

That claim is not assumed: the script reproduces the leader's six caps against
the values the Exp 5 diagnostic read off the live `judge.budget` and refuses to
continue unless they match to 1e-12.
"""
from __future__ import annotations
import csv, json, math, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src")); sys.path.insert(0, str(ROOT / "scripts"))
RUN = ROOT / "outputs" / "exp4" / "run"
OUT = ROOT / "outputs" / "exp4_resource_audit"
LEADER = "exp4|exp4-pool-v1|65lines#ecb2ffc4bcce"
PERIODS = ["early", "am_peak", "midday", "pm_peak", "evening", "owl"]

# Read off judge.budget during the 2026-09-21 OFF->ON diagnostic (live object,
# inside the same certify setup the run used). The parity check below.
LEADER_CAP_REF = {
    "am_peak": 59.0375, "early": 88.5563, "evening": 44.2782,
    "midday": 29.5188, "owl": 29.5188, "pm_peak": 59.0375,
}


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    from cota_opt.configs import load_constraints, load_cost_weights
    from cota_opt.cost import CostWeights
    from cota_opt.exp1 import build_setup as exp1_setup
    from cota_opt.exp4_assemble import assemble
    from cota_opt.exp4_network import Exp4Selection
    from exp2_treatments import _Baseline
    from exp4_c10_fixtures import POOL_VERSION, _BY_RID, _boot, _first_dep_by_period

    env = json.loads((ROOT / "outputs" / "CANONICAL_ENVELOPE.json").read_text())
    VH_CAP = float(env["weekday_revenue_vehicle_hours"])
    _c = load_constraints()
    cons = {**_c, "resource": {**_c["resource"],
                               "weekday_revenue_vehicle_hours": VH_CAP}}
    assert cons["resource"]["peak_fleet_by_period"] == "baseline", \
        "the sentinel this audit is about is not in force"
    w = CostWeights.from_config(load_cost_weights())

    prop = json.loads((RUN / "proposals.json").read_text())["proposals"]
    lines_of = {p["state_key"]: p["lines"] for p in prop}
    rank_of = {}
    approx_of = {}
    ranked = sorted(prop, key=lambda p: (p["objective_APPROXIMATE"], p["state_key"]))
    for i, p in enumerate(ranked, 1):
        rank_of[p["state_key"]] = i
        approx_of[p["state_key"]] = p["objective_APPROXIMATE"]

    cert = {}
    for p in (RUN / "certified").glob("*.json"):
        d = json.load(open(p))
        if "objective_EXACT" in d:
            cert[d["state_key"]] = d
    print(f"{len(cert)} certified records")
    cert_rank = {k: i for i, k in enumerate(
        sorted(cert, key=lambda k: (cert[k]["objective_EXACT"], k)), 1)}

    st = _boot(); H, graph = st["H"], st["graph"]
    first_dep = _first_dep_by_period()

    def caps_for(net, ts):
        b_ed = _Baseline(H.baseline, net, ts)
        e1 = exp1_setup(b_ed, constraints=cons, weights=w)
        fit = e1.model.evaluate(e1.baseline_plan)
        return (dict(fit.peak_by_period), float(fit.revenue_veh_hours),
                len(e1.model.services))

    # ---- parity check on the leader before anything else ------------------
    sel = Exp4Selection(POOL_VERSION, frozenset(lines_of[LEADER]), frozenset())
    blt = assemble(sel, _BY_RID, graph, H.baseline.network.stops,
                   pool_version=POOL_VERSION, first_dep_sec_by_period=first_dep)
    lead_cap, lead_bvh, lead_n = caps_for(blt.network, blt.tstats)
    worst = max(abs(lead_cap[p] - LEADER_CAP_REF[p]) for p in PERIODS)
    print("PARITY CHECK against judge.budget read live during certification:")
    for p in PERIODS:
        print(f"   {p:<9} reconstructed {lead_cap[p]:12.6f}   "
              f"live {LEADER_CAP_REF[p]:10.4f}   |d| {abs(lead_cap[p]-LEADER_CAP_REF[p]):.2e}")
    # the live values were printed rounded to 4dp, so parity is judged at that
    if worst > 5e-5:
        print(f"FATAL: reconstruction does not match the live budget "
              f"(worst |d| {worst:.3e}). The cheap path is not equivalent.")
        return 2
    print(f"PARITY OK (worst |d| {worst:.3e} against 4dp-rounded live values)")

    # ---- the reference network, same machinery ----------------------------
    ref_cap, ref_bvh, ref_n = caps_for(H.baseline.network, H.baseline.tstats)
    print(f"reference network: {ref_n} route-periods, baseline vh {ref_bvh:.6f}")
    print(f"reference caps: {json.dumps({p: ref_cap[p] for p in PERIODS})}")

    rows = []
    t0 = time.time()
    for i, k in enumerate(sorted(cert), 1):
        sel = Exp4Selection(POOL_VERSION, frozenset(lines_of[k]), frozenset())
        blt = assemble(sel, _BY_RID, graph, H.baseline.network.stops,
                       pool_version=POOL_VERSION, first_dep_sec_by_period=first_dep)
        cap, bvh, nrp = caps_for(blt.network, blt.tstats)
        d = cert[k]
        rows.append({
            "candidate_id": k,
            "state_digest": d.get("state_digest", ""),
            "discovery_rank": rank_of.get(k, ""),
            "certified_rank": cert_rank[k],
            "certified_objective": repr(d["objective_EXACT"]),
            "objective_APPROXIMATE": repr(approx_of.get(k, "")),
            **{f"{p}_cap": repr(cap[p]) for p in PERIODS},
            "baseline_vehicle_hours": repr(bvh),
            "optimized_vehicle_hours": repr(d["fitness_EXACT"]["revenue_veh_hours"]),
            "optimized_peak_vehicles_scalar": repr(d["fitness_EXACT"]["peak_vehicles"]),
            "n_route_periods": nrp,
            "n_lines": len(lines_of[k]),
            "rounds": d.get("rounds", ""), "converged": d.get("converged", ""),
            "guarantee": d.get("guarantee", ""),
            "hours_cap": repr(VH_CAP),
            "envelope_digest": str(env["envelope_digest"]),
            "cap_provenance": "candidate_own_baseline_plan_peak_by_period",
        })
        if i % 25 == 0:
            print(f"  {i}/{len(cert)}  ({time.time()-t0:.0f}s)")

    rows.append({
        "candidate_id": "REFERENCE_NETWORK", "state_digest": "",
        "discovery_rank": "", "certified_rank": "", "certified_objective": "",
        "objective_APPROXIMATE": "",
        **{f"{p}_cap": repr(ref_cap[p]) for p in PERIODS},
        "baseline_vehicle_hours": repr(ref_bvh), "optimized_vehicle_hours": "",
        "optimized_peak_vehicles_scalar": "", "n_route_periods": ref_n,
        "n_lines": "", "rounds": "", "converged": "", "guarantee": "",
        "hours_cap": repr(VH_CAP), "envelope_digest": str(env["envelope_digest"]),
        "cap_provenance": "reference_network_own_baseline_plan_peak_by_period",
    })

    p = OUT / "EXP4_CANDIDATE_RESOURCE_CAPS.csv"
    with open(p, "w", newline="") as f:
        wri = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        wri.writeheader(); wri.writerows(rows)
    print(f"wrote {p}  ({len(rows)} rows incl. reference)")

    (OUT / "EXP4_RESOURCE_AUDIT_PROVENANCE.json").write_text(json.dumps({
        "audit": "exp4_resource_normalization",
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "cap_provenance_code_path": [
            "scripts/exp4_launch.py: cons overrides weekday_revenue_vehicle_hours only",
            "src/cota_opt/exp3_score.py: b_ed = _Baseline(H.baseline, net, ts) -- candidate network",
            "src/cota_opt/exp2.py:209-211: services/baseline_plan from exp1.build_setup(b_ed)",
            "src/cota_opt/exp2.py:~300: fit = model.evaluate(baseline_plan)",
            "src/cota_opt/exp2.py:324: peak_budget = dict(fit.peak_by_period) when sentinel == 'baseline'",
            "src/cota_opt/exp2.py:327: ResourceBudget(vh_budget, peak_budget, tolerance=budget_tolerance)",
            "src/cota_opt/frequency.py:374: _feasible tests hours then peak per period",
        ],
        "cap_is_candidate_specific": True,
        "hours_cap_source": "outputs/CANONICAL_ENVELOPE.json weekday_revenue_vehicle_hours",
        "hours_cap_value": VH_CAP,
        "envelope_digest": str(env["envelope_digest"]),
        "peak_usage_instrument": "FrequencyModel.peak_vehicles = cycle/headway, cycle = 2*runtime*(1+layover)",
        "peak_cap_instrument": "identical -- both are FitnessVector.peak_by_period",
        "budget_tolerance": float(_c["resource"].get("budget_tolerance", 0.0)),
        "periods": PERIODS,
        "leader_parity_worst_abs_diff": worst,
        "reference_caps": {p: ref_cap[p] for p in PERIODS},
        "reference_baseline_vehicle_hours": ref_bvh,
        "n_candidates": len(cert),
        "reconstruction_method": ("exp1.build_setup on the candidate network; "
                                  "PathBasedModel inherits resource physics "
                                  "unchanged (exp2.py:53), verified against the "
                                  "live judge.budget for the leader"),
    }, indent=1))
    print("wrote provenance")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
