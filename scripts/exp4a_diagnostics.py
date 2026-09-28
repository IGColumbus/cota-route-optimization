#!/usr/bin/env python3
"""Cheap diagnostics on certified Experiment 4A plans (N3, N4; N0 optional).

DIAGNOSTIC ONLY. Nothing here changes an objective, a ranking or an
admission. Every number comes from the SAME setup the certification scored:
`exp3_score.solve_on_network` is called once per network with every ladder key
pinned to the certified plan (a one-rung exact solve), a fresh path-set scope
and `include_setup=True`, and the resulting FitnessVector is asserted equal to
the certified record's fitness before anything else is read. The diagnostics
then read that setup's own evaluators, raptor network and path sets:

  abandonment / access  per-OD reachability and retention under the plan
                        (`PathSetEvaluator.evaluate` / `od_costs`), with OD
                        vectors saved so networks can be compared pair by pair
  path adequacy         `adequacy.adequacy` -- cached path set vs fresh RAPTOR
  common lines          `hyperpath.bound` + `summarize` -- the wait saving the
                        same-route model omits (cross-route upper bound)
  crowding              `crowding.build_load_profile` peak load per trip vs
                        the planning capacity -- NOT priced in the objective
  physical sanity       plan and network structure counts

Usage: exp4a_diagnostics.py --network N3 --record outputs/exp4_addendum/N3.json
                            --out outputs/exp4_addendum/diag_N3.json
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import exp45_certify_cell as CC  # noqa: E402
import exp5_model_resource as MR  # noqa: E402
from exp45_contracts import LAM, SEED  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--network", required=True, choices=("N0", "N3", "N4"))
    ap.add_argument("--record", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--skip-adequacy", action="store_true")
    a = ap.parse_args()

    import cota_opt.exp3_score as E3
    from cota_opt.adequacy import adequacy
    from cota_opt.configs import (load_constraints, load_cost_weights,
                                  service_periods)
    from cota_opt.cost import CostWeights
    from cota_opt.crowding import build_load_profile
    from cota_opt.hyperpath import bound, summarize
    from cota_opt.odmatrix import build_zone_system

    rec = json.loads((ROOT / a.record).read_text())
    st = CC.boot()
    H = st["H"]
    asm = H.assumptions
    pa = asm["path_assignment"]
    net, ts, ident = CC.build_network(a.network, st)
    if ident["state_digest"] != rec["identity"]["state_digest"]:
        raise SystemExit("network digest differs from the certified record")
    env = MR.load_base()
    if rec["resource"]["enforced_exact_fingerprint"] != env.exact_fingerprint:
        raise SystemExit("record was not certified under the base envelope")
    cons = env.to_constraints(load_constraints())

    plan = {tuple(k.split("|", 1)): (math.inf if v is None else float(v))
            for k, v in rec["outcome"]["plan_EXACT"].items()}
    t0 = time.time()
    # the certified plan's keys ARE the solver's ladder keys: certify() builds
    # its plan from the exact solver's own headway dict
    keys = sorted(plan)
    r = E3.solve_on_network(
        net, ts, harness=H, stops_gdf=st["sg"], lam=LAM, seed=SEED,
        iterations=20_000, restarts=1, width=0, constraints=cons,
        pathset_cache={}, waiting_model="same_route",
        starts="greedy", allow_off=True, solver="exact",
        exact_max_combinations=10,
        ladder_override={k: [plan[k]] for k in keys}, include_setup=True)
    fit = r["fit"]
    fx = rec["outcome"]["fitness_EXACT"]
    for k in ("generalized_cost", "unserved_demand", "revenue_veh_hours",
              "peak_vehicles"):
        if repr(float(getattr(fit, k))) != fx[k]:
            raise SystemExit(f"re-pinned {k} {getattr(fit, k)!r} != record "
                             f"{fx[k]} -- the diagnostic setup is not the "
                             f"certified one")
    judge, rn = r["judge"], r["raptor"]
    zs = build_zone_system(
        H.baseline.demand["bg_frame"], st["sg"],
        radius_m=float(pa["access_radius_m"]),
        walk_speed_m_per_min=float(pa["walk_speed_m_per_min"]),
        stop_index=rn.stop_index)
    hw = dict(judge.baseline_plan.headways)
    for k, v in plan.items():
        if k in hw:
            hw[k] = float(v)

    w = CostWeights.from_config(load_cost_weights())
    wk = dict(random_arrival_threshold_min=float(
        asm["waiting"]["random_arrival_threshold_min"]),
        schedule_coefficient=float(asm["waiting"]["schedule_coefficient"]))
    cap = float(asm["crowding"]["bus_capacity"])
    periods = service_periods(asm)
    services = judge.model.services

    out = {"network": a.network, "identity": ident,
           "record_plan_digest": rec["outcome"]["plan_digest"],
           "setup_matches_certified_fitness": True,
           "status": "DIAGNOSTIC_ONLY", "periods": {}}
    od_dump = {}
    legs = []
    for per, ev in judge.model.evaluators.items():
        ps = ev.ps
        sub = np.array([hw[k] for k in ps.rp_keys])
        e = ev.evaluate(sub)
        c = ev.od_costs(sub)
        reach = np.isfinite(c)
        keep = np.zeros_like(ps.od_flow)
        keep[reach] = ev.retention(c[reach])
        flow = ps.od_flow
        od_dump[per] = {"o": ps.od_origin.tolist(), "d": ps.od_dest.tolist(),
                        "flow": flow.tolist(), "reach": reach.tolist(),
                        "keep": keep.tolist()}
        row = {"od_pairs": int(ps.n_od), "flow": float(flow.sum()),
               "structural_unserved_flow": float(flow[~reach].sum()),
               "structural_unserved_share": float(flow[~reach].sum()
                                                  / flow.sum()),
               "served_flow": float((flow * keep).sum()),
               "retention_mean": float((flow * keep).sum() / flow.sum()),
               "evaluate": {k: float(v) for k, v in e.items()
                            if isinstance(v, (int, float))}}
        # gate 4-8: one-seat rides and transfer burden on the chosen paths
        from cota_opt.attribution import best_paths
        idx, _ = best_paths(ev, sub)
        ride = ps.leg_rp >= 0
        nride = np.bincount(ps.leg_path[ride], minlength=ps.n_paths)
        served = flow * keep
        has = idx >= 0
        rides_od = np.zeros(ps.n_od, dtype=np.int64)
        rides_od[has] = nride[idx[has]]
        transit = has & (rides_od >= 1)
        sv = served[transit]
        row["one_seat_and_transfers"] = {
            "served_flow_on_transit_paths": float(sv.sum()),
            "one_seat_share": float(sv[rides_od[transit] == 1].sum()
                                    / max(sv.sum(), 1e-12)),
            "mean_boardings_per_served_trip": float(
                (sv * rides_od[transit]).sum() / max(sv.sum(), 1e-12)),
            "share_with_2plus_transfers": float(
                sv[rides_od[transit] >= 3].sum() / max(sv.sum(), 1e-12))}
        act_routes = {k[0] for k, v in hw.items()
                      if k[1] == per and math.isfinite(v)}
        stops_served = sorted({s_ for p_ in net.patterns.values()
                               if p_.route_id in act_routes
                               for s_ in p_.stops})
        row["stops_served"] = len(stops_served)
        od_dump[per]["stops_served"] = stops_served
        od_dump[per]["rides"] = rides_od.tolist()
        if not a.skip_adequacy:
            mr = int(pa["max_rounds"])
            ad = adequacy(rn, zs, ps, ev, hw, w, wk, mr)
            row["path_adequacy"] = {k: v for k, v in ad.items()
                                    if isinstance(v, (int, float, str))}
            ad4 = adequacy(rn, zs, ps, ev, hw, w, wk, mr + 1)
            row["transfer_depth_probe"] = {
                "max_rounds": mr + 1,
                "note": "cached path set (built at max_rounds=%d) vs fresh "
                        "RAPTOR one boarding deeper; OD-cost gap only, plan "
                        "not re-optimized" % mr,
                **{k: v for k, v in ad4.items()
                   if isinstance(v, (int, float, str))}}
        legs.append(bound(ps, ev, rn, hw, per, w, wk))
        pf = ev.path_flows(sub)
        lp = build_load_profile(ps, rn, pf)
        dur = periods[per][1] - periods[per][0]
        loads = []
        for i, k in enumerate(ps.rp_keys):
            h = hw.get(k, math.inf)
            if not math.isfinite(h) or lp.peak_volume[i] <= 0:
                continue
            svc = services.get(k)
            ndir = getattr(svc, "n_directions", 1) if svc else 1
            trips = ndir * dur * 60.0 / h if dur < 30 else ndir * dur / h
            loads.append(float(lp.peak_volume[i]) / max(trips, 1e-9))
        loads = np.array(loads) if loads else np.zeros(1)
        row["crowding_NOT_PRICED"] = {
            "bus_capacity": cap, "active_route_periods_with_load": int(len(loads)),
            "peak_load_per_trip_median": float(np.median(loads)),
            "peak_load_per_trip_p95": float(np.percentile(loads, 95)),
            "peak_load_per_trip_max": float(loads.max()),
            "share_over_capacity": float((loads > cap).mean()),
            "period_duration_units": ("hours" if dur < 30 else "minutes")}
        out["periods"][per] = row

    per_leg = [f for f in legs if not f.empty]
    import pandas as pd
    pl = pd.concat(per_leg, ignore_index=True) if per_leg else pd.DataFrame()
    hb = summarize(pl, float(fit.generalized_cost))
    out["common_lines_bound"] = {**{k: (float(v) if isinstance(v, (int, float))
                                        else v) for k, v in hb.summary.items()},
                                 "verdict": hb.verdict,
                                 "explanation": hb.explanation}
    act = {k: v for k, v in plan.items() if math.isfinite(v)}
    routes = sorted({k[0] for k in plan})
    active_routes = sorted({k[0] for k in act})
    per_route_periods = {r_: sum(1 for k in act if k[0] == r_)
                         for r_ in active_routes}
    out["physical_sanity"] = {
        "n_patterns": len(net.patterns),
        "n_routes_in_plan": len(routes), "n_routes_active": len(active_routes),
        "n_route_periods": len(plan), "n_off": len(plan) - len(act),
        "headway_min_active": min(act.values()) if act else None,
        "headway_max_active": max(act.values()) if act else None,
        "n_active_headway_over_60": sum(1 for v in act.values() if v > 60),
        "routes_active_in_one_period_only": sorted(
            r_ for r_, n in per_route_periods.items() if n == 1),
        "active_by_period": {p: sum(1 for k in act if k[1] == p)
                             for p in MR.PERIODS},
        "total_stops_in_patterns": len({s for p in net.patterns.values()
                                        for s in p.stops}),
    }
    tot = sum(v["flow"] for v in out["periods"].values())
    out["totals"] = {
        "flow": tot,
        "structural_unserved_share": sum(
            v["structural_unserved_flow"] for v in out["periods"].values()) / tot,
        "served_share": sum(v["served_flow"] for v in out["periods"].values())
        / tot}
    out["seconds"] = round(time.time() - t0, 1)
    out["written_utc"] = CC.utc()
    CC.atomic_write_json(ROOT / a.out, out)
    CC.atomic_write_json((ROOT / a.out).with_suffix(".od.json"), od_dump)
    print(json.dumps(out["totals"]), out["seconds"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
