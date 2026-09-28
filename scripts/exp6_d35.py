#!/usr/bin/env python3
"""D35 reach tests for every Experiment 6 policy constraint.

For each regime, a KNOWN plan is built from the network's own baseline plan by
removing a little service (so it stays inside the resource envelope and only
the policy can decide it). Its measured value for the constraint is computed,
and the plan is then submitted through the PRODUCTION feasibility path --
`exp3_score.solve_on_network` -> `exp2.build_setup` (policy compiled and
attached) -> `gen2_frequency.solve_exact` on a one-rung ladder ->
`frequency._feasible` -- twice: with the constraint just looser than the
measured value (must be admitted) and just tighter (must be refused).

A regime whose tighter arm is admitted is `EXP6_CONSTRAINT_INERT`.

    exp6_d35.py --network N0 --out outputs/exp6/d35/N0.json
"""
from __future__ import annotations

import argparse
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
    ap.add_argument("--network", required=True, choices=("N0", "N3"))
    ap.add_argument("--catalog-digest", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    import cota_opt.exp3_score as E3
    from cota_opt.configs import load_constraints
    from cota_opt.policy import PolicySpec
    from pyproj import Transformer
    from scipy.spatial import cKDTree

    st = CC.boot()
    H = st["H"]
    net, ts, ident = CC.build_network(a.network, st)
    env = MR.load_base()
    base_cons = env.to_constraints(load_constraints())
    cache: dict = {}
    t0 = time.time()
    common = dict(harness=H, stops_gdf=st["sg"], lam=LAM, seed=SEED,
                  iterations=20_000, restarts=1, width=0,
                  pathset_cache=cache, waiting_model="same_route",
                  starts="greedy", allow_off=True)
    g = E3.solve_on_network(net, ts, constraints=base_cons, solver="gen1",
                            include_setup=True, **common)
    judge = g["judge"]
    keys = list(judge.model.keys)
    full = {k: sorted(judge.ladders[k]) for k in keys}
    base = {k: float(judge.baseline_plan.headways[k]) for k in keys}

    def admit(plan: dict, spec) -> dict:
        cons = base_cons if spec is None else {**base_cons, "policy": spec}
        try:
            r = E3.solve_on_network(
                net, ts, constraints=cons, solver="exact",
                exact_max_combinations=10,
                ladder_override={k: [plan[k]] for k in keys}, **common)
        except ValueError as ex:
            if "no ladder combination fits the envelope" in str(ex):
                return {"admitted": False, "refusal": str(ex)[:120]}
            raise
        return {"admitted": True,
                "policy_violation": float(r["fit"].policy_violation),
                "setup_policy_digest": r["evaluator_checks"].get("policy_digest")}

    # 1. a budget-feasible all-baseline-served plan (the baseline, trimmed
    #    deterministically if the network's own baseline overruns the envelope)
    plan = dict(base)
    trims = []
    ctrl = admit(plan, None)
    B = [k for k in keys if math.isfinite(base[k])]
    i = 0
    while not ctrl["admitted"] and i < len(B):
        k = B[i]
        longer = [v for v in full[k] if math.isfinite(v)
                  and v > plan[k] * (1 + 1e-6)]
        if longer:
            plan[k] = longer[0]
            trims.append([f"{k[0]}|{k[1]}", base[k], plan[k]])
            ctrl = admit(plan, None)
        i += 1
    if not ctrl["admitted"]:
        raise SystemExit("could not build a budget-feasible baseline-derived plan")
    P0 = dict(plan)

    tr = Transformer.from_crs("EPSG:4326", H.assumptions["crs"]["projected"],
                              always_xy=True)
    stop_xy = {s: tr.transform(v.lon, v.lat) for s, v in net.stops.items()}

    def compiled(spec):
        return spec.compile(keys, base, net.route_stops, stop_xy)

    def vec(p):
        return np.array([p[k] for k in keys])

    cat = a.catalog_digest
    out = {"network": a.network, "identity": ident, "catalog_digest": cat,
           "path": ("solve_on_network -> build_setup(policy compiled+attached) "
                    "-> solve_exact(one-rung ladder) -> frequency._feasible"),
           "base_plan_trims_to_fit_envelope": trims,
           "control_no_policy": ctrl, "regimes": {},
           "baseline_headways": {f"{k[0]}|{k[1]}": (None if math.isinf(v)
                                                     else v)
                                  for k, v in sorted(base.items())}}

    def record(name, test_plan, measured, loose, tight, note):
        la, ti = admit(test_plan, loose), admit(test_plan, tight)
        ok = la["admitted"] and not ti["admitted"]
        out["regimes"][name] = {
            "measured": measured, "loose_spec": loose.payload(),
            "tight_spec": tight.payload(), "loose": la, "tight": ti,
            "note": note,
            "verdict": "PASS" if ok else "EXP6_CONSTRAINT_INERT"}

    # R1: lengthen one baseline-served key with baseline <= 30 to a longer rung
    cand = [k for k in B if P0[k] == base[k] and base[k] <= 30.0 and any(
        math.isfinite(v) and base[k] < v <= 60.0 for v in full[k])]
    k1 = cand[0]
    r1 = min(v for v in full[k1] if math.isfinite(v) and base[k1] < v <= 60.0)
    p1 = dict(P0)
    p1[k1] = r1
    # the plan's measured R1 value: the largest headway on any baseline-served
    # route-period that runs longer than its own baseline (the trims included)
    m1 = max(p1[k] for k in B
             if math.isfinite(p1[k]) and p1[k] > base[k] * (1 + 1e-9))
    record("R1", p1, {"key": f"{k1[0]}|{k1[1]}", "baseline": base[k1],
                      "headway": r1, "measured_max_headway_above_baseline": m1},
           PolicySpec("D35_R1_loose", max_headway=m1, catalog_digest=cat),
           PolicySpec("D35_R1_tight", max_headway=m1 - 0.5, catalog_digest=cat),
           "H = measured max admits; H = measured max - 0.5 refuses")

    # R2: m baseline-served keys OFF
    m = 3
    p2 = dict(P0)
    offs = [k for k in B if k[1] == "midday"][:m]
    for k in offs:
        p2[k] = math.inf
    nB = len(B)
    record("R2", p2, {"n_off": m, "n_baseline_served": nB, "share": m / nB},
           PolicySpec("D35_R2_loose", max_off_share=m / nB, catalog_digest=cat),
           PolicySpec("D35_R2_tight", max_off_share=(m - 0.5) / nB,
                      catalog_digest=cat),
           "floor(s*|B|) = m admits; = m-1 refuses")

    # R3: one span key OFF
    cs = compiled(PolicySpec("probe", span=True, catalog_digest=cat))
    ks = keys[int(cs.span_idx[0])]
    p3 = dict(P0)
    p3[ks] = math.inf
    record("R3", p3, {"span_key_off": f"{ks[0]}|{ks[1]}",
                      "n_span_keys": int(len(cs.span_idx))},
           PolicySpec("D35_R3_loose", max_off_share=1.0, catalog_digest=cat),
           PolicySpec("D35_R3_tight", span=True, max_off_share=1.0,
                      catalog_digest=cat),
           "loose = a non-binding attached policy (R2 share 1.0), tight = same "
           "plus span; both attach, so the difference is the span constraint")

    # R4 / R6: a whole route OFF in one period (loses its sole-served stops)
    c4 = compiled(PolicySpec("probe", max_lost_share=0.0, catalog_digest=cat))
    best = None
    for k in B:
        p = dict(P0)
        p[k] = math.inf
        lost = c4.measure(vec(p))["r4_lost_stop_periods"]
        if lost > 0 and (best is None or lost < best[0]):
            best = (lost, k)
    lost, k4 = best
    p4 = dict(P0)
    p4[k4] = math.inf
    nS = c4.n_sp
    record("R4", p4, {"key_off": f"{k4[0]}|{k4[1]}", "lost_stop_periods": lost,
                      "n_stop_periods": nS},
           PolicySpec("D35_R4_loose", max_lost_share=lost / nS,
                      catalog_digest=cat),
           PolicySpec("D35_R4_tight", max_lost_share=(lost - 0.5) / nS,
                      catalog_digest=cat),
           "floor(c*|S|) = lost admits; = lost-1 refuses")
    # R6 on the same plan: distance from each lost stop-period to the nearest
    # stop served in that period
    on = np.isfinite(vec(p4))
    per = k4[1]
    served = sorted({s for i, k in enumerate(keys) if on[i] and k[1] == per
                     for s in net.route_stops.get(k[0], ())})
    tree = cKDTree(np.array([stop_xy[s] for s in served]))
    lost_stops = sorted(set(net.route_stops[k4[0]]) - set(served))
    dstar = max(float(tree.query(stop_xy[s])[0]) for s in lost_stops)
    record("R6", p4, {"key_off": f"{k4[0]}|{k4[1]}",
                      "n_lost_stops": len(lost_stops),
                      "max_distance_to_served_stop_m": dstar},
           PolicySpec("D35_R6_loose", area_radius_m=dstar + 1.0,
                      catalog_digest=cat),
           PolicySpec("D35_R6_tight", area_radius_m=max(dstar - 1.0, 0.5),
                      catalog_digest=cat),
           "radius d*+1 m admits; d*-1 m refuses")

    out["all_pass"] = all(r["verdict"] == "PASS" for r in out["regimes"].values())
    out["seconds"] = round(time.time() - t0, 1)
    out["written_utc"] = CC.utc()
    CC.atomic_write_json(ROOT / a.out, out)
    for n, r in out["regimes"].items():
        print(n, r["verdict"], r["measured"])
    return 0 if out["all_pass"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
