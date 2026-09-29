#!/usr/bin/env python3
"""Experiment 7 preflight: level reach (D35-style) on the production path.

reach  -- one FIXED plan (read from a certified record) is evaluated through
          the production feasibility/evaluation path
              exp3_score.solve_on_network -> exp2.build_setup ->
              gen2_frequency.solve_exact (one-rung ladder) -> _feasible
          under BASE and under every level in a level file. Each level runs
          with a fresh path-set cache. Pass criteria:
            * BASE reproduces the record's objective bit-exactly;
            * every non-BASE level changes the evaluation of the fixed plan
              (objective or a declared component), i.e. the knob REACHES the
              model; a level that changes nothing is EXP7_LEVEL_INERT;
            * the plan is still admitted (resource envelope and policy are
              level-independent), so admission cannot silently differ.

    exp7_preflight.py reach --network N0 \
        --plan-from outputs/exp6/closure/N0_REF__from_R2_S25__aed848588abad24d.json \
        --level-file outputs/exp7/preflight/reach_levels.json \
        --out outputs/exp7/preflight/reach_N0.json
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
import exp7_levels as L  # noqa: E402
from exp45_contracts import SEED  # noqa: E402

FIELDS = ("generalized_cost", "unserved_demand", "served_demand",
          "gc_per_served_trip", "revenue_veh_hours", "peak_vehicles")


def evaluate(net, ts, st, lv, plan_keyed, cons):
    import cota_opt.exp3_score as E3
    H = L.harness_for(st["H"], lv)
    common = dict(harness=H, stops_gdf=st["sg"], lam=float(lv.lam), seed=SEED,
                  iterations=20_000, restarts=1, width=0, pathset_cache={},
                  waiting_model=lv.waiting_model, starts="greedy",
                  allow_off=True)
    t0 = time.time()
    try:
        r = E3.solve_on_network(net, ts, constraints=cons, solver="exact",
                                exact_max_combinations=10,
                                ladder_override={k: [v] for k, v in
                                                 plan_keyed.items()}, **common)
    except ValueError as ex:
        return {"admitted": False, "refusal": str(ex)[:200]}
    f = r["fit"]
    w = r["judge"].model.w.unserved
    return {"admitted": True,
            "objective": float(f.scalarized(w, float(lv.lam))),
            **{k: float(getattr(f, k)) for k in FIELDS},
            "policy_violation": float(f.policy_violation),
            "waiting_model_used": r.get("waiting_model_used"),
            "od_pairs": int(len(H.od)), "od_total": float(H.od.flow.sum()),
            "seconds": round(time.time() - t0, 1)}


def reach(a) -> int:
    from cota_opt.configs import load_constraints
    rec = json.loads((ROOT / a.plan_from).read_text())
    assert rec["status"] == "CERTIFIED" and rec["network"] == a.network
    plan = {tuple(k.split("|", 1)): (math.inf if v is None else float(v))
            for k, v in rec["outcome"]["plan_EXACT"].items()}
    levels = [L.BASE] + [L.from_payload(p) for p in
                         json.loads((ROOT / a.level_file).read_text())["levels"]]
    st = CC.boot()
    net, ts, ident = CC.build_network(a.network, st)
    cons = MR.load_base().to_constraints(load_constraints())
    out_p = ROOT / a.out
    out = json.loads(out_p.read_text()) if out_p.exists() else {"rows": {}}
    out.update(schema="exp7_preflight_reach/v1", network=a.network,
               plan_from=a.plan_from, plan_digest=rec["outcome"]["plan_digest"],
               record_objective=rec["outcome"]["objective_EXACT"],
               identity=ident)
    for lv in levels:
        if lv.name in out["rows"]:
            continue
        row = {"level": lv.payload(), "level_digest": lv.digest,
               **evaluate(net, ts, st, lv, plan, cons)}
        out["rows"][lv.name] = row
        CC.atomic_write_json(out_p, out)
        print(lv.name, row.get("objective"), row.get("seconds"), flush=True)
    b = out["rows"]["BASE"]
    verdict = {"BASE_reproduces_record":
               b.get("objective") == float(rec["outcome"]["objective_EXACT"])}
    for name, r in out["rows"].items():
        if name == "BASE":
            continue
        moved = [k for k in ("objective",) + FIELDS
                 if r.get(k) is not None and r.get(k) != b.get(k)]
        verdict[name] = ("REACHES" if r["admitted"] and moved else
                         "EXP7_LEVEL_INERT" if r["admitted"] else
                         "ADMISSION_CHANGED")
        r["moved"] = moved
    out["verdict"] = verdict
    out["passed"] = verdict["BASE_reproduces_record"] and all(
        v == "REACHES" for k, v in verdict.items()
        if k != "BASE_reproduces_record")
    out["provenance"] = {"src_cota_opt_content_digest": CC.src_content_digest(),
                         "runner_sha256": {n: CC.sha256_file(
                             ROOT / "scripts" / n)[:16] for n in
                             ("exp7_preflight.py", "exp7_levels.py")},
                         "written_utc": CC.utc()}
    CC.atomic_write_json(out_p, out)
    print(json.dumps(verdict, indent=1))
    return 0 if out["passed"] else 3


def base_verdict(a) -> int:
    """BASE canaries (exp7_cell.py --level BASE) vs the frozen Exp 6 initial
    records: objective, plan, rounds, fitness and config digest bit-exact."""
    d = ROOT / "outputs/exp7/preflight/base_repro"
    rows, ok = {}, True
    for p in sorted(d.glob("N*_*.json")):
        if p.name.startswith(("RAW.", "ERROR.")):
            continue
        r = json.loads(p.read_text())
        e = json.loads((ROOT / "outputs/exp6/initial" / p.name).read_text())
        cmp = {f: r["outcome"][f] == e["outcome"][f] for f in
               ("objective_EXACT", "plan_digest", "rounds", "fitness_EXACT",
                "converged")}
        cmp["config_digest"] = r["provenance"]["config_digest"] == \
            e["provenance"]["config_digest"]
        cmp["pathset_digest"] = r["execution"]["pathset_digest"] == \
            e["execution"]["pathset_digest"]
        rows[p.stem] = {"equal": cmp, "objective": r["outcome"]["objective_EXACT"],
                        "exp6_objective": e["outcome"]["objective_EXACT"],
                        "plan_digest": r["outcome"]["plan_digest"],
                        "seconds": r["outcome"]["seconds"]}
        ok &= all(cmp.values())
    out = {"schema": "exp7_base_repro/v1", "rows": rows,
           "passed": bool(rows) and ok,
           "src_cota_opt_content_digest": CC.src_content_digest(),
           "written_utc": CC.utc()}
    CC.atomic_write_json(d / "BASE_REPRO_VERDICT.json", out)
    print(json.dumps(out, indent=1))
    return 0 if out["passed"] else 3


def transfer_verdict(a) -> int:
    """Production-path transfer, refusal and emptiness preflights (run by
    scripts/exp7_transfer_preflight.sh) checked against their expectations."""
    d = ROOT / "outputs/exp7/preflight/transfer"
    j = lambda n: json.loads((d / n).read_text()) if (d / n).exists() else None
    src = json.loads((ROOT / a.anchor_record).read_text())
    t = j("N0_REF_lvl_R_LAM1_anchor.json")
    rf = j("N0_R1_H20_BASE_anchor_refused.json")
    rp = j("N0_REF_BASE_anchor_from_N4.json")
    em = j("N3_R1_H20_lvl_R_LAM1_emptiness.json")
    g = j("N0_REF_lvl_R_LAM1_greedy.json")
    checks = {
        "cross_level_transfer_admitted": bool(t) and t["status"] == "CERTIFIED"
        and t["search"]["start"]["source"] == "anchor"
        and t["search"]["start"]["anchor_plan_digest"] ==
        src["outcome"]["plan_digest"],
        "transfer_reevaluated_under_target_lambda": bool(t) and
        t["search"]["lam"] == 1.0 and float(t["search"]["start"][
            "anchor_objective"]) != float(src["outcome"]["objective_EXACT"]),
        "transfer_never_worse_than_anchor": bool(t) and
        float(t["outcome"]["objective_EXACT"]) <=
        float(t["search"]["start"]["anchor_objective"]),
        "policy_refusal_by_certifier": bool(rf) and
        rf["status"] == "ANCHOR_REFUSED" and "infeasible" in rf["refusal"],
        "representation_refusal_by_certifier": bool(rp) and
        rp["status"] == "ANCHOR_REFUSED" and "route-periods" in rp["refusal"],
        "emptiness_reproven_at_level": bool(em) and
        em["status"] == "INFEASIBLE_UNDER_ENVELOPE" and
        em["level"]["name"] == "R_LAM1",
    }
    if g and t:
        checks["greedy_vs_transfer_at_level_recorded"] = True
    out = {"schema": "exp7_transfer_preflight/v1", "checks": checks,
           "passed": all(checks.values()),
           "detail": {"transfer": t and {
               "objective": t["outcome"]["objective_EXACT"],
               "anchor_objective_under_target": t["search"]["start"]["anchor_objective"],
               "plan_digest": t["outcome"]["plan_digest"],
               "rounds": t["outcome"]["rounds"]},
               "greedy_at_level": g and {
               "objective": g["outcome"]["objective_EXACT"],
               "plan_digest": g["outcome"]["plan_digest"]},
               "policy_refusal": rf and rf.get("refusal", "")[:300],
               "representation_refusal": rp and rp.get("refusal", "")[:300],
               "emptiness": em and em["proof"]["usage_vs_caps"]},
           "written_utc": CC.utc()}
    CC.atomic_write_json(d / "TRANSFER_PREFLIGHT_VERDICT.json", out)
    print(json.dumps(out, indent=1))
    return 0 if out["passed"] else 3


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("reach")
    r.add_argument("--network", required=True, choices=("N0", "N3", "N4"))
    r.add_argument("--plan-from", required=True)
    r.add_argument("--level-file", required=True)
    r.add_argument("--out", required=True)
    sub.add_parser("base-verdict")
    tv = sub.add_parser("transfer-verdict")
    tv.add_argument("--anchor-record", required=True)
    a = ap.parse_args()
    if a.cmd == "base-verdict":
        return base_verdict(a)
    if a.cmd == "transfer-verdict":
        return transfer_verdict(a)
    return reach(a)


if __name__ == "__main__":
    raise SystemExit(main())
