#!/usr/bin/env python3
"""Exp 4A path-set-omission probe (gate 4-9), DIAGNOSTIC ONLY.

Re-costs each CERTIFIED plan (not re-optimized) with OD cost =
min(cached-path-set cost, fresh RAPTOR cost) -- the same fresh RAPTOR that
`adequacy.adequacy` uses -- and recomputes served demand, served-only
generalized cost and objective = gc + w_unserved*lam*unserved with the
evaluator's own retention curve. First re-derives the certified objective from
the cached costs alone and asserts it matches, so the arithmetic is the
evaluator's. The corrected figure approximates what a path set without
omissions would charge the SAME plan; it is not a certified number."""
import argparse, json, math, sys, time
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "scripts")]
import exp45_certify_cell as CC, exp5_model_resource as MR
from exp45_contracts import LAM, SEED
ap = argparse.ArgumentParser(); ap.add_argument("--network"); ap.add_argument("--record"); ap.add_argument("--out")
a = ap.parse_args()
import cota_opt.exp3_score as E3
from cota_opt.configs import load_constraints, load_cost_weights
from cota_opt.cost import CostWeights
from cota_opt.odmatrix import build_zone_system
from cota_opt.raptor import generalized_cost, pattern_headways
rec = json.loads((ROOT / a.record).read_text())
st = CC.boot(); H = st["H"]; pa = H.assumptions["path_assignment"]
net, ts, ident = CC.build_network(a.network, st)
cons = MR.load_base().to_constraints(load_constraints())
plan = {tuple(k.split("|", 1)): (math.inf if v is None else float(v)) for k, v in rec["outcome"]["plan_EXACT"].items()}
t0 = time.time()
r = E3.solve_on_network(net, ts, harness=H, stops_gdf=st["sg"], lam=LAM, seed=SEED,
    iterations=20_000, restarts=1, width=0, constraints=cons, pathset_cache={},
    waiting_model="same_route", starts="greedy", allow_off=True, solver="exact",
    exact_max_combinations=10, ladder_override={k: [v] for k, v in plan.items()})
judge, rn = r["judge"], r["raptor"]
assert repr(float(r["fit"].scalarized(judge.model.w.unserved, LAM))) == rec["outcome"]["objective_EXACT"]
zs = build_zone_system(H.baseline.demand["bg_frame"], st["sg"], radius_m=float(pa["access_radius_m"]),
    walk_speed_m_per_min=float(pa["walk_speed_m_per_min"]), stop_index=rn.stop_index)
hw = dict(judge.baseline_plan.headways); hw.update({k: v for k, v in plan.items() if k in hw})
w = CostWeights.from_config(load_cost_weights())
wk = dict(random_arrival_threshold_min=float(H.assumptions["waiting"]["random_arrival_threshold_min"]),
          schedule_coefficient=float(H.assumptions["waiting"]["schedule_coefficient"]))
pen = judge.model.w.unserved * LAM
def score(ev, c, flow):
    reach = np.isfinite(c); keep = np.zeros_like(flow); keep[reach] = ev.retention(c[reach])
    served = flow * keep
    return float((served[reach] * c[reach]).sum()), float(served.sum()), float(flow.sum() - served.sum())
tot = {"cached": [0.0, 0.0, 0.0], "corrected": [0.0, 0.0, 0.0]}; per_out = {}
for per, ev in judge.model.evaluators.items():
    ps = ev.ps; sub = np.array([hw[k] for k in ps.rp_keys]); cache = ev.od_costs(sub)
    ph = pattern_headways(rn, hw, ps.period); fresh = np.full(ps.n_od, np.inf)
    origins = np.unique(ps.od_origin)
    s0s = np.searchsorted(ps.od_origin, origins, "left"); s1s = np.searchsorted(ps.od_origin, origins, "right")
    for z, s0, s1 in zip(origins, s0s, s1s):
        a_st, a_w = zs.access_of(int(z))
        if len(a_st) == 0: continue
        cost, _, _ = generalized_cost(rn, [rn.stop_ids[s] for s in a_st], ph, w, wk, max_rounds=int(pa["max_rounds"]),
                                      source_costs=[w.walking * x for x in a_w])
        for oi in range(s0, s1):
            e_st, e_w = zs.access_of(int(ps.od_dest[oi]))
            if len(e_st): fresh[oi] = float(np.min(cost[e_st] + w.walking * e_w))
    corr = np.minimum(cache, fresh)
    for lab, c in (("cached", cache), ("corrected", corr)):
        g, s, u = score(ev, c, ps.od_flow); tot[lab][0] += g; tot[lab][1] += s; tot[lab][2] += u
    per_out[per] = {"pairs_newly_reachable": int((np.isfinite(fresh) & ~np.isfinite(cache)).sum()),
                    "flow_newly_reachable": float(ps.od_flow[np.isfinite(fresh) & ~np.isfinite(cache)].sum())}
out = {"network": a.network, "status": "DIAGNOSTIC_ONLY_NOT_CERTIFIED", "plan_digest": rec["outcome"]["plan_digest"],
       "unserved_weight_x_lambda": pen, "per_period": per_out}
for lab, (g, s, u) in tot.items():
    out[lab] = {"gc_served_only": g, "served": s, "unserved": u, "objective": g + pen * u}
fx = rec["outcome"]["fitness_EXACT"]
out["cached_reproduces_certified"] = {
    "objective_rel_err": abs(out["cached"]["objective"] - float(rec["outcome"]["objective_EXACT"])) / float(rec["outcome"]["objective_EXACT"]),
    "served_rel_err": abs(out["cached"]["served"] - float(fx["served_demand"])) / float(fx["served_demand"])}
out["seconds"] = round(time.time() - t0, 1)
CC.atomic_write_json(ROOT / a.out, out)
print(json.dumps({k: out[k] for k in ("cached", "corrected", "cached_reproduces_certified")}))
