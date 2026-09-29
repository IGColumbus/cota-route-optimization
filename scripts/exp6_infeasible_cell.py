#!/usr/bin/env python3
"""Prove that a policy cell has an EMPTY feasible set under the envelope.

Used only for policy cells whose every constraint is a per-route-period
headway cap (R1: baseline-served route-periods ON with headway <= max(H,
baseline); no combinatorial constraint), where the certifier's start fails with
"minimum-service plan already exceeds the budget".

Proof, on the production path:
  1. Every plan admissible under such a policy gives each route-period a
     headway no longer than its longest admissible rung (the policy-filtered
     ladder's largest finite rung; locked keys: their single rung).
  2. Revenue vehicle-hours (sum of n_dir * T / h * runtime) and every period's
     peak proxy (sum of cycle / h) are strictly decreasing in every headway.
  3. Hence the plan using every route-period's longest admissible rung -- the
     minimum-service plan M -- uses no more hours and no more peak proxy in any
     period than any admissible plan.
  4. M is submitted through solve_on_network -> build_setup -> solve_exact on a
     one-rung ladder -> frequency._feasible under the cell's policy and the
     envelope. If it is refused, and it is admitted under the same policy with
     the envelope relaxed (so the refusal is the envelope, not the policy),
     then no admissible plan fits the envelope: the feasible set is empty.

Writes a record with status INFEASIBLE_UNDER_ENVELOPE, M's measured usage
against the caps, and the refusal text.

    exp6_infeasible_cell.py --network N3 --cell R1_H20 --catalog-digest ... --out ...
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import exp45_certify_cell as CC  # noqa: E402
import exp5_model_resource as MR  # noqa: E402
import exp6_grid as G  # noqa: E402
from exp45_contracts import LAM, SEED  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--network", required=True)
    ap.add_argument("--cell", required=True)
    ap.add_argument("--catalog-digest", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    import cota_opt.exp3_score as E3
    from cota_opt.configs import load_constraints

    spec = G.specs(a.catalog_digest)[a.cell]
    if not (spec.max_headway is not None and spec.max_off_share is None
            and not spec.span and spec.max_lost_share is None
            and spec.area_radius_m is None):
        raise SystemExit("this proof applies only to pure per-route-period "
                         "headway-cap policies (R1)")
    st = CC.boot()
    net, ts, ident = CC.build_network(a.network, st)
    env = MR.load_base()
    cons = {**env.to_constraints(load_constraints()), "policy": spec}
    relaxed = {**MR.scale(env, 10.0, 10.0).to_constraints(load_constraints()),
               "policy": spec}
    t0 = time.time()
    cache: dict = {}
    common = dict(harness=st["H"], stops_gdf=st["sg"], lam=LAM, seed=SEED,
                  iterations=20_000, restarts=1, width=0, pathset_cache=cache,
                  waiting_model="same_route", starts="greedy", allow_off=True)
    # the policy-filtered ladders, from a setup under the RELAXED envelope
    g = E3.solve_on_network(net, ts, constraints=relaxed, solver="gen1",
                            include_setup=True, **common)
    judge = g["judge"]
    keys = list(judge.model.keys)
    M = {k: max(v for v in judge.ladders[k] if math.isfinite(v)) for k in keys}

    def submit(c):
        try:
            r = E3.solve_on_network(net, ts, constraints=c, solver="exact",
                                    exact_max_combinations=10,
                                    ladder_override={k: [M[k]] for k in keys},
                                    **common)
            f = r["fit"]
            return {"admitted": True,
                    "revenue_veh_hours": repr(float(f.revenue_veh_hours)),
                    "peak_proxy_by_period": {p: repr(float(v)) for p, v in
                                             f.peak_by_period.items()},
                    "policy_violation": float(f.policy_violation)}
        except ValueError as ex:
            if "no ladder combination fits the envelope" in str(ex):
                return {"admitted": False, "refusal": str(ex)[:160]}
            raise

    under_env = submit(cons)
    under_relaxed = submit(relaxed)
    proven = (not under_env["admitted"]) and under_relaxed["admitted"] \
        and under_relaxed["policy_violation"] == 0.0
    use = under_relaxed if under_relaxed["admitted"] else {}
    over = {}
    if use:
        over["hours"] = [use["revenue_veh_hours"], repr(env.hours_cap),
                         float(use["revenue_veh_hours"]) > env.hours_cap]
        for p, v in use["peak_proxy_by_period"].items():
            over[p] = [v, repr(env.peak_proxy_caps[p]),
                       float(v) > env.peak_proxy_caps[p]]
    rec = {"schema": "exp6_cell/v1", "experiment": "exp6", "role": "initial",
           "network": a.network, "cell": a.cell, "identity": ident,
           "status": ("INFEASIBLE_UNDER_ENVELOPE" if proven
                      else "INFEASIBILITY_NOT_PROVEN"),
           "policy": {"spec": spec.payload(), "digest": spec.digest},
           "proof": {"method": __doc__.split("Proof, on the production path:")[1]
                     .split("Writes a record")[0].strip(),
                     "minimum_service_plan_EXACT": {f"{r}|{p}": v for (r, p), v
                                                    in sorted(M.items())},
                     "under_envelope": under_env,
                     "under_relaxed_envelope_x10": under_relaxed,
                     "usage_vs_caps": over,
                     "certifier_start_error": "minimum-service plan already "
                     "exceeds the budget; the policy maximum headway is "
                     "infeasible under this envelope"},
           "envelope": {"exact_fingerprint": env.exact_fingerprint},
           "provenance": {"code_version": __import__(
               "cota_opt.exp3_cell", fromlist=["x"]).code_version(),
               "src_cota_opt_content_digest": CC.src_content_digest(),
               "runner_sha256": {n: CC.sha256_file(ROOT / "scripts" / n)[:16]
                                 for n in ("exp6_infeasible_cell.py",
                                           "exp6_grid.py")}},
           "seconds": round(time.time() - t0, 1), "written_utc": CC.utc()}
    CC.atomic_write_json(ROOT / a.out, rec)
    print(rec["status"], json.dumps(over))
    return 0 if proven else 3


if __name__ == "__main__":
    raise SystemExit(main())
