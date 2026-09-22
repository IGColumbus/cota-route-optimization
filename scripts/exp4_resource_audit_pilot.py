#!/usr/bin/env python3
"""Exp 4 resource normalization audit, step 7: the common-cap pilot.

AUDIT ONLY. Re-certifies 10 representative candidates changing NOTHING except
the provenance of the peak-resource cap.

Identical to `scripts/exp4_launch.py`: LAM, SEED, POOL_VERSION, `assemble`,
`certify` under CERTIFICATION_DIGEST, n_keys, k_rungs, max_rounds, the
initialization policy (`starts="greedy"` inside certify), the objective and the
evaluator. The ONLY difference is one config key:

    ORIGINAL   cons["resource"]["peak_fleet_by_period"] = "baseline"
               -> exp2.py:324 resolves it to the CANDIDATE's own baseline
                  peak_by_period, so every candidate gets its own cap.

    PILOT      cons["resource"]["peak_fleet_by_period"] = <explicit dict>
               -> exp2.py:326 takes the dict verbatim, so every candidate gets
                  the SAME cap.

The common envelope is the REFERENCE network's baseline `peak_by_period`,
computed by the identical `exp1.build_setup -> model.evaluate(baseline_plan)`
path that produces candidate usage. Same units, same six periods, same absence
of rounding, same instrument, same evaluator contract -- which is the semantic
parity §8 of the audit requires before a common cap may be used at all.

Writes only under outputs/exp4_resource_audit/pilot/. Resumes by file existence.
"""
from __future__ import annotations
import json, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src")); sys.path.insert(0, str(ROOT / "scripts"))
RUN = ROOT / "outputs" / "exp4" / "run"
OUT = ROOT / "outputs" / "exp4_resource_audit"
PILOT = OUT / "pilot"
LAM, SEED = 2.0, 20260825


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser(); ap.add_argument("--max-hours", type=float, default=6.0)
    a = ap.parse_args()
    PILOT.mkdir(parents=True, exist_ok=True)

    from cota_opt.configs import load_constraints
    from cota_opt.exp4_assemble import assemble
    from cota_opt.exp4_certify import CERTIFICATION_DIGEST, certify
    from cota_opt.exp4_network import Exp4Selection
    from cota_opt.firewall.core import digest
    from exp4_c10_fixtures import POOL_VERSION, _BY_RID, _boot, _first_dep_by_period

    spec = json.loads((OUT / "pilot_spec.json").read_text())
    common = {str(k): float(v) for k, v in spec["common_envelope"].items()}
    sel_list = spec["selection"]

    env = json.loads((ROOT / "outputs" / "CANONICAL_ENVELOPE.json").read_text())
    VH_CAP = float(env["weekday_revenue_vehicle_hours"])
    _c = load_constraints()
    assert _c["resource"]["peak_fleet_by_period"] == "baseline", \
        "the original sentinel is not what this pilot thinks it is"
    cons = {**_c, "resource": {**_c["resource"],
                               "weekday_revenue_vehicle_hours": VH_CAP,
                               "peak_fleet_by_period": common}}

    prop = json.loads((RUN / "proposals.json").read_text())["proposals"]
    lines_of = {p["state_key"]: p["lines"] for p in prop}

    st = _boot(); H, sg, graph = st["H"], st["sg"], st["graph"]
    first_dep = _first_dep_by_period()

    print(f"PILOT common cap: {json.dumps({k: round(v,4) for k,v in sorted(common.items())})}")
    print(f"hours cap {VH_CAP:.6f}  lam {LAM}  seed {SEED}  "
          f"contract {CERTIFICATION_DIGEST}")
    todo = [s for s in sel_list
            if not (PILOT / f"{digest(s['candidate_id'])}.json").exists()]
    print(f"pilot: {len(sel_list)-len(todo)} done, {len(todo)} remaining of {len(sel_list)}")

    t_start = time.time(); deadline = t_start + a.max_hours * 3600
    for i, s in enumerate(todo, 1):
        if time.time() > deadline:
            print(f"  shard bound reached; {len(todo)-i+1} remain"); break
        k = s["candidate_id"]
        sel = Exp4Selection(POOL_VERSION, frozenset(lines_of[k]), frozenset())
        built = assemble(sel, _BY_RID, graph, H.baseline.network.stops,
                         pool_version=POOL_VERSION, first_dep_sec_by_period=first_dep)
        t0 = time.time()
        try:
            cr = certify(built.network, built.tstats, state_key=k,
                         state_digest=sel.state_digest, harness=H, stops_gdf=sg,
                         lam=LAM, seed=SEED, constraints=cons,
                         contract_digest=CERTIFICATION_DIGEST)
        except Exception as e:
            (PILOT / f"{digest(k)}.json").write_text(json.dumps(
                {"candidate_id": k, "label": s["label"],
                 "error": f"{type(e).__name__}: {e}"[:400],
                 "original_certified_objective": s["certified_objective"],
                 "original_certified_rank": s["certified_rank"]}, indent=1))
            print(f"  [{i}/{len(todo)}] {s['label']:<18} FAILED {type(e).__name__}: {e}"[:160])
            continue
        (PILOT / f"{digest(k)}.json").write_text(json.dumps(
            {**cr.payload(), "candidate_id": k, "label": s["label"],
             "original_certified_objective": s["certified_objective"],
             "original_certified_rank": s["certified_rank"],
             "original_sum_cap": s["sum_cap"],
             "common_envelope": common,
             "cap_provenance": "reference_network_baseline_peak_by_period"},
            indent=1))
        orig = float(s["certified_objective"])
        d = cr.objective - orig
        print(f"  [{i}/{len(todo)}] {s['label']:<18} r{s['certified_rank']:<4} "
              f"orig {orig:,.4f} -> norm {cr.objective:,.4f}  "
              f"d {d:+,.4f} ({d/orig*100:+.4f}%)  "
              f"rounds {cr.rounds} conv {cr.converged} ({time.time()-t0:.0f}s)")
    done = sorted(PILOT.glob("*.json"))
    print(f"pilot results on disk: {len(done)} of {len(sel_list)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
