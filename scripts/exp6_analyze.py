#!/usr/bin/env python3
"""Experiment 6 acceptance gates, policy frontier and policy costs.

Reads only frozen/produced artifacts; writes outputs/exp6/EXP6_ANALYSIS.json.
Every reported comparison is a firewall `compare()` under the contract that
governs it (EXP6_POLICY within a network, EXP6_STRUCTURE across networks).
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

import exp6_contracts as K  # noqa: E402
import exp6_grid as G  # noqa: E402
import exp6_run as R  # noqa: E402
from exp45_certify_cell import atomic_write_json, utc  # noqa: E402

REL_EQ = 1e-9


def f(x):
    return float(x)


def main() -> int:
    from cota_opt.firewall import compare
    ap = argparse.ArgumentParser()
    ap.add_argument("--partial", action="store_true")
    a = ap.parse_args()
    con = json.loads(R.CONTRACT.read_text())
    cat = con["catalog"]["digest"]
    specs = G.specs(cat)
    cells = list(specs)
    strict = [tuple(x) for x in con["nesting"]["strict_pairs"]]
    fails: list[str] = []
    out: dict = {"artifact": "EXP6_ANALYSIS", "written_utc": utc(),
                 "contract_file": "outputs/exp6/EXP6_CONTRACT.json"}

    init, final, cstate = {}, {}, {}
    for n in G.NETWORKS:
        st_p = R.CLOS / f"closure_state_{n}.json"
        cstate[n] = json.loads(st_p.read_text()) if st_p.exists() else None
        for c in cells:
            p = R.INIT / f"{n}_{c}.json"
            init[(n, c)] = json.loads(p.read_text()) if p.exists() else None
            if cstate[n]:
                final[(n, c)] = json.loads((ROOT / cstate[n]["best"][c]).read_text())
    missing = [f"{n}_{c}" for (n, c), r in init.items() if r is None]
    closure_done = all(cstate[n] and cstate[n]["fixed_point"] for n in G.NETWORKS)
    if (missing or not closure_done) and not a.partial:
        print("incomplete:", missing, closure_done)
        return 2

    # ---- per-record checks (initial and final) ---------------------------
    rec_checks = {k: [] for k in ("code", "runner", "envelope", "policy",
                                  "feasible", "convergence", "base_config")}
    base_cfgs = set()
    for label, recs in (("initial", init), ("final", final)):
        for (n, c), r in recs.items():
            if r is None:
                continue
            tag = f"{label}:{n}_{c}"
            pv = r["provenance"]
            rec_checks["code"].append((tag, pv["code_version"] ==
                                       con["code"]["code_version"] and
                                       pv["src_cota_opt_content_digest"] ==
                                       con["code"]["src_cota_opt_content_digest"]))
            rec_checks["runner"].append((tag, all(
                con["code"]["runner_sha256"].get(k) == v
                for k, v in pv["runner_sha256"].items())))
            rec_checks["envelope"].append((tag, r["resource"][
                "enforced_exact_fingerprint"] == con["envelope"]["exact_fingerprint"]))
            sp = specs[c]
            pol = r.get("policy") or {}
            ok = pol.get("digest") == sp.digest and (
                pol.get("setup_policy_digest") == sp.digest)
            rec_checks["policy"].append((tag, ok))
            rec_checks["feasible"].append((tag, r["resource"][
                "feasible_under_full_target_constraints"]))
            o = r["outcome"]
            rec_checks["convergence"].append((tag, o["converged"] and o["rounds"] < 120))
            base_cfgs.add(pv["base_config_digest"])
    rec_checks["base_config"].append(("all", len(base_cfgs) == 1))
    for k, v in rec_checks.items():
        bad = [t for t, ok in v if not ok]
        if bad:
            fails.append(f"{k}: {bad[:6]}")
    out["record_checks"] = {k: {"n": len(v), "all_pass": all(ok for _, ok in v)}
                            for k, v in rec_checks.items()}

    def obj(r):
        return f(r["outcome"]["objective_EXACT"])

    # ---- monotonicity: initial (reported) and post-closure (hard) --------
    def mono(recs):
        rows = []
        for n in G.NETWORKS:
            for tight, loose in strict:
                A, B = recs.get((n, tight)), recs.get((n, loose))
                if A is None or B is None:
                    continue
                oa, ob = obj(A), obj(B)
                viol = ob > oa + REL_EQ * abs(oa)
                rows.append({"network": n, "tighter": tight, "looser": loose,
                             "obj_tighter": repr(oa), "obj_looser": repr(ob),
                             "regression_pct": 100 * (ob - oa) / oa if viol else 0.0,
                             "violation": viol})
        return rows
    mi, mf = mono(init), mono(final)
    out["monotonicity_initial"] = {"n_pairs": len(mi),
                                   "n_violations": sum(r["violation"] for r in mi),
                                   "violations": [r for r in mi if r["violation"]]}
    out["monotonicity_post_closure"] = {"n_pairs": len(mf),
                                        "n_violations": sum(r["violation"] for r in mf),
                                        "violations": [r for r in mf if r["violation"]]}
    if final and out["monotonicity_post_closure"]["n_violations"]:
        fails.append("EXP6_POLICY_MONOTONICITY_FAILURE")

    # ---- reference closure -----------------------------------------------
    refc = []
    for n in G.NETWORKS:
        if not final:
            break
        oref = obj(final[(n, "REF")])
        for c in cells:
            if c != "REF" and obj(final[(n, c)]) < oref - REL_EQ * abs(oref):
                refc.append([n, c])
    out["reference_closure"] = {"violations": refc}
    if refc:
        fails.append("EXP6_REFERENCE_CLOSURE_FAILURE")

    # ---- closure behaviour -----------------------------------------------
    clos = {}
    for n in G.NETWORKS:
        s = cstate[n]
        if not s:
            continue
        led = [json.loads(x) for x in (R.CLOS / f"closure_ledger_{n}.jsonl")
               .read_text().splitlines() if x.strip()]
        acts = {}
        for r_ in led:
            acts[r_["action"]] = acts.get(r_["action"], 0) + 1
        changed = []
        for c in cells:
            i_, f_ = init[(n, c)], final[(n, c)]
            if i_["outcome"]["plan_digest"] != f_["outcome"]["plan_digest"]:
                changed.append({"cell": c, "initial": repr(obj(i_)),
                                "final": repr(obj(f_)),
                                "improvement_pct": 100 * (obj(i_) - obj(f_)) / obj(i_),
                                "found_in_pass": s["found_in_pass"][c],
                                "winning_basin": f_["search"]["start"].get("source"),
                                "anchor_source": (f_.get("anchor") or {}).get("source_cell")})
        clos[n] = {"passes_completed": s["passes_completed"],
                   "fixed_point": s["fixed_point"],
                   "pass_ceiling": con["closure"]["pass_ceiling"],
                   "attempts_by_action": acts, "n_receipts": len(led),
                   "cells_changed_basin": changed}
        if not s["fixed_point"]:
            fails.append(f"EXP6_START_CLOSURE_FAILURE {n}")
    out["closure"] = clos

    # ---- firewall ---------------------------------------------------------
    fw = {"policy": [], "structure": []}
    for n in G.NETWORKS:
        if not final:
            break
        ref = final[(n, "REF")]
        for c in cells:
            if c == "REF":
                continue
            res = compare(K.receipt_for(ref, K.EXP6_POLICY),
                          K.receipt_for(final[(n, c)], K.EXP6_POLICY), K.EXP6_POLICY)
            ok = res.__class__.__name__ == "ComparisonResult"
            row = {"network": n, "cell": c, "admitted": ok}
            if ok:
                row.update(effect=res.effect, effect_pct=res.effect_pct,
                           declared=list(res.declared_differences))
            else:
                row["refusal"] = repr(res)[:600]
                fails.append(f"firewall policy {n} {c}")
            fw["policy"].append(row)
    for c in cells:
        if not final:
            break
        res = compare(K.receipt_for(final[("N0", c)], K.EXP6_STRUCTURE),
                      K.receipt_for(final[("N3", c)], K.EXP6_STRUCTURE),
                      K.EXP6_STRUCTURE)
        ok = res.__class__.__name__ == "ComparisonResult"
        row = {"cell": c, "admitted": ok}
        if ok:
            row.update(effect_N3_minus_N0=res.effect, effect_pct_of_N0=res.effect_pct,
                       declared=list(res.declared_differences))
        else:
            row["refusal"] = repr(res)[:600]
            fails.append(f"firewall structure {c}")
        fw["structure"].append(row)
    out["firewall"] = fw

    # ---- sentinels ----------------------------------------------------------
    sent = []
    for n, c in R.SENTINELS:
        p = R.SENT / f"{n}_{c}.json"
        if not p.exists() or init.get((n, c)) is None:
            sent.append({"network": n, "cell": c, "status": "NOT_RUN"})
            continue
        s_ = json.loads(p.read_text())
        eq = all(s_["outcome"][k] == init[(n, c)]["outcome"][k]
                 for k in ("objective_EXACT", "plan_digest", "rounds"))
        sent.append({"network": n, "cell": c,
                     "status": "PASS" if eq else "EXP6_ORDER_DEPENDENCE_FAILURE"})
        if not eq:
            fails.append(f"EXP6_ORDER_DEPENDENCE_FAILURE {n} {c}")
    out["sentinels"] = sent

    # ---- frontier, policy costs, contamination ---------------------------
    rows = []
    for n in G.NETWORKS:
        if not final:
            break
        i_ref, f_ref = obj(init[(n, "REF")]), obj(final[(n, "REF")])
        for c in cells:
            i_, f_ = init[(n, c)], final[(n, c)]
            fx = f_["outcome"]["fitness_EXACT"]
            res_ = f_["resource"]
            greedy_cost = obj(i_) - i_ref
            closed_cost = obj(f_) - f_ref
            rows.append({
                "network": n, "cell": c, "spec": specs[c].payload(),
                "initial_objective": obj(i_), "final_objective": obj(f_),
                "initial_plan_digest": i_["outcome"]["plan_digest"],
                "final_plan_digest": f_["outcome"]["plan_digest"],
                "winning_basin": f_["search"]["start"].get("source"),
                "policy_cost_closed": closed_cost,
                "policy_cost_closed_pct": 100 * closed_cost / f_ref,
                "policy_cost_greedy_only": greedy_cost,
                "policy_cost_greedy_only_pct": 100 * greedy_cost / i_ref,
                "basin_contamination": greedy_cost - closed_cost,
                "served_demand": f(fx["served_demand"]),
                "unserved_demand": f(fx["unserved_demand"]),
                "generalized_cost": f(fx["generalized_cost"]),
                "gc_per_served_trip": f(fx["gc_per_served_trip"]),
                "hours_used": f(res_["used"]["revenue_veh_hours"]),
                "hours_cap": f(res_["enforced"]["hours_cap"]),
                "hours_slack": f(res_["slack"]["hours"]),
                "peak_used": res_["used"]["peak_proxy_by_period"],
                "peak_slack": res_["slack"]["peak_proxy_by_period"],
                "binding_resource": res_["binding_within_1e-6_rel"],
                "policy_measure": f_["policy_outcome"]["measure"],
                "n_off": f_["outcome"]["n_off"],
                "n_baseline_on_now_off": f_["outcome"]["n_baseline_on_now_off"],
                "rounds_initial": i_["outcome"]["rounds"],
                "rounds_final": f_["outcome"]["rounds"]})
    out["frontier"] = rows
    out["failures"] = fails
    complete = not missing and closure_done and all(
        s["status"] != "NOT_RUN" for s in sent)
    out["status"] = ("EXP6_POLICY_FRONTIER_CERTIFIED" if complete and not fails
                     else "INCOMPLETE" if not fails else
                     "FAILED: " + "; ".join(fails))
    atomic_write_json(R.OUT / "EXP6_ANALYSIS.json", out)
    print(out["status"])
    print(json.dumps(out["record_checks"]))
    print("mono initial", out["monotonicity_initial"]["n_violations"], "/",
          out["monotonicity_initial"]["n_pairs"], " post-closure",
          out["monotonicity_post_closure"]["n_violations"], "/",
          out["monotonicity_post_closure"]["n_pairs"])
    return 0 if not fails else 3


if __name__ == "__main__":
    raise SystemExit(main())
