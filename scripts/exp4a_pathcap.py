#!/usr/bin/env python3
"""Exp 4A paths-per-OD sensitivity (gate 4-9), DIAGNOSTIC ONLY.
Re-scores the CERTIFIED plan (pinned, one-rung exact solve) with the path set
built at max_paths_per_od = 4 (the contract value; must reproduce the record
bit-exactly) and at 6. Plans are not re-optimized."""
import argparse, json, math, sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "scripts")]
import exp45_certify_cell as CC, exp5_model_resource as MR
from exp45_contracts import LAM, SEED
ap = argparse.ArgumentParser(); ap.add_argument("--network"); ap.add_argument("--record"); ap.add_argument("--out")
a = ap.parse_args()
import cota_opt.exp3_score as E3
from cota_opt.configs import load_constraints
rec = json.loads((ROOT / a.record).read_text())
st = CC.boot(); net, ts, ident = CC.build_network(a.network, st)
cons = MR.load_base().to_constraints(load_constraints())
plan = {tuple(k.split("|", 1)): (math.inf if v is None else float(v)) for k, v in rec["outcome"]["plan_EXACT"].items()}
out = {"network": a.network, "status": "DIAGNOSTIC_ONLY", "plan_digest": rec["outcome"]["plan_digest"], "rows": {}}
for m in (None, 6):
    t0 = time.time()
    r = E3.solve_on_network(net, ts, harness=st["H"], stops_gdf=st["sg"], lam=LAM, seed=SEED,
        iterations=20_000, restarts=1, width=0, constraints=cons, pathset_cache={},
        waiting_model="same_route", starts="greedy", allow_off=True, solver="exact",
        exact_max_combinations=10, ladder_override={k: [v] for k, v in plan.items()},
        max_paths_per_od=m)
    f = r["fit"]; w = r["judge"].model.w.unserved
    out["rows"]["contract(4)" if m is None else str(m)] = {
        "objective": repr(float(f.scalarized(w, LAM))),
        "generalized_cost": repr(float(f.generalized_cost)), "unserved_demand": repr(float(f.unserved_demand)),
        "total_paths": r["evaluator_checks"].get("total_paths"), "seconds": round(time.time() - t0, 1)}
b = out["rows"]["contract(4)"]
assert b["objective"] == rec["outcome"]["objective_EXACT"], (b["objective"], rec["outcome"]["objective_EXACT"])
o6 = float(out["rows"]["6"]["objective"]); o4 = float(b["objective"])
out["objective_change_pct_4_to_6"] = 100 * (o6 - o4) / o4
CC.atomic_write_json(ROOT / a.out, out); print(json.dumps(out["rows"]), out["objective_change_pct_4_to_6"])
