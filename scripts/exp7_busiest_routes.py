#!/usr/bin/env python3
"""Freeze the A7 route ranking: the 10 busiest routes per network.

"Busiest" = modelled boardings per route summed over the six periods, under
the network's reference service, through the production path-level evaluator
at BASE (same_route waiting, lambda 2):
  N0, N3  the current (baseline) headways from the Exp 6 REF record;
  N4      the EXP4N incumbent plan (N4 has no current service).
The judge is built by the one-rung exact admission of a known admissible plan
(Exp 6 closed REF on N0/N3; the EXP4N incumbent on N4); boardings do not
depend on the plan used to build the judge, only on the path sets.

    exp7_busiest_routes.py --out outputs/exp7/A7_ROUTE_RANKING.json
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import exp45_certify_cell as CC  # noqa: E402
import exp5_model_resource as MR  # noqa: E402
from exp45_contracts import LAM, SEED  # noqa: E402

SRC = {
    "N0": ("outputs/exp6/closure/N0_REF__from_R2_S25__aed848588abad24d.json", "baseline"),
    "N3": ("outputs/exp6/closure/N3_REF__from_R2_S25__fdec5c5475c73736.json", "baseline"),
    "N4": ("outputs/exp7/preflight/n4/N4_REF_BASE_F4_greedy.json", "plan"),
}


def main() -> int:
    import numpy as np
    import cota_opt.exp3_score as E3
    from cota_opt.configs import load_constraints
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    st = CC.boot()
    cons = MR.load_base().to_constraints(load_constraints())
    out = {"schema": "exp7_a7_ranking/v1", "definition": __doc__.split("\n\n")[1],
           "rankings": {}}
    for kind, (rp, which) in SRC.items():
        rec = json.loads((ROOT / rp).read_text())
        net, ts, ident = CC.build_network(kind, st)
        plan = {tuple(k.split("|", 1)): (math.inf if v is None else float(v))
                for k, v in rec["outcome"]["plan_EXACT"].items()}
        r = E3.solve_on_network(net, ts, harness=st["H"], stops_gdf=st["sg"],
                                lam=LAM, seed=SEED, iterations=20_000,
                                restarts=1, width=0, constraints=cons,
                                pathset_cache={}, waiting_model="same_route",
                                starts="greedy", allow_off=True, solver="exact",
                                exact_max_combinations=10,
                                ladder_override={k: [v] for k, v in plan.items()},
                                include_setup=True)
        model = r["judge"].model
        if which == "baseline":
            bh = rec["baseline_headways"]
            svc = {tuple(k.split("|", 1)): (math.inf if v is None else float(v))
                   for k, v in bh.items()}
        else:
            svc = plan
        h = np.array([svc[k] for k in model.keys], float)
        by_route: dict[str, float] = {}
        for per, ev in model.evaluators.items():
            sub = h[model._sel[per]]
            b = ev.boardings_by_rp(sub)
            for (rid, _p), v in zip(ev.ps.rp_keys, b):
                by_route[rid] = by_route.get(rid, 0.0) + float(v)
        ranked = sorted(by_route.items(), key=lambda kv: (-kv[1], kv[0]))
        out["rankings"][kind] = {
            "service": which, "source_record": rp,
            "routes": [rid for rid, _ in ranked[:10]],
            "boardings_top10": [[rid, v] for rid, v in ranked[:10]],
            "n_routes": len(ranked),
            "total_boardings": sum(by_route.values())}
        print(kind, out["rankings"][kind]["routes"], flush=True)
    out["written_utc"] = CC.utc()
    CC.atomic_write_json(ROOT / a.out, out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
