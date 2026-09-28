#!/usr/bin/env python3
"""Experiment 5 analysis gates and frontier tables.

Reads the 32 production records, the sentinel records and the frozen contract;
writes outputs/exp5/EXP5_ANALYSIS.json and prints the acceptance checklist.
Every comparison that is reported as an effect goes through the canonical
firewall (`compare`) under the contract that governs it: EXP5_FRONTIER within a
network across cells, EXP5_STRUCTURE across networks at an identical cell.

    exp5_analyze.py [--partial]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import exp45_contracts as C  # noqa: E402
import exp5_model_resource as MR  # noqa: E402
import exp5_run as RUN  # noqa: E402
from exp45_certify_cell import atomic_write_json, utc  # noqa: E402

EPS = 1e-9


def load(d: Path, net: str, cid: str):
    p = d / f"{net}_{cid}.json"
    return json.loads(p.read_text()) if p.exists() else None


def f(x) -> float:
    return float(x)


def main() -> int:
    from cota_opt.firewall import admit, compare
    from cota_opt.firewall.observation import Inadmissible
    ap = argparse.ArgumentParser()
    ap.add_argument("--partial", action="store_true")
    a = ap.parse_args()
    con = json.loads(RUN.CONTRACT.read_text())
    band = float(con["gates"]["monotonicity"]["band_pct"])
    runner_frozen = con["code"]["runner_sha256"]
    lst = RUN.canonical()
    base = MR.load_base()
    grid = {c.id: c for c in MR.grid(base)}
    recs = {(n, c.id): load(RUN.CELLS, n, c.id) for n, c in lst}
    missing = [f"{n}_{c}" for (n, c), r in recs.items() if r is None]
    if missing and not a.partial:
        print("missing cells:", missing)
        return 2
    checks: dict[str, list] = {k: [] for k in (
        "contract_digest", "code_version", "runner_hash", "enforced_budget",
        "reach_d35", "convergence", "feasible", "start_independent",
        "no_fallback")}
    fails: list[str] = []
    for (n, cid), r in recs.items():
        if r is None:
            continue
        tag = f"{n}_{cid}"
        o, res = r["outcome"], r["resource"]
        ok = r["contract_digest"] == con["contracts"]["EXP5_FRONTIER"]["digest"]
        checks["contract_digest"].append((tag, ok))
        ok = r["provenance"]["code_version"] == con["code"]["code_version"] and \
            r["provenance"]["src_cota_opt_content_digest"] == \
            con["code"]["src_cota_opt_content_digest"]
        checks["code_version"].append((tag, ok))
        ok = all(runner_frozen[k] == v for k, v in
                 r["provenance"]["runner_sha256"].items())
        checks["runner_hash"].append((tag, ok))
        env = grid[cid].envelope
        ok = (res["enforced"]["hours_cap"] == repr(float(env.hours_cap)) and
              res["enforced"]["peak_proxy_caps"] ==
              {p: repr(float(env.peak_proxy_caps[p])) for p in MR.PERIODS} and
              res["enforced_exact_fingerprint"] == env.exact_fingerprint)
        checks["enforced_budget"].append((tag, ok))
        checks["reach_d35"].append((tag, r["reach_test_d35"]["verdict"] == "PASS"))
        checks["convergence"].append((tag, o["converged"] and o["rounds"] < 120))
        checks["feasible"].append((tag, res["feasible_under_enforced_caps"]))
        sa = r["execution"]["start_audit"]
        checks["start_independent"].append(
            (tag, sa["start_names"] == ["greedy"] and sa["winning_start"] == "greedy"))
        checks["no_fallback"].append(
            (tag, not sa["forced_greedy_fallback"] and not sa["initial_rejection"]))
    for k, v in checks.items():
        bad = [t for t, ok in v if not ok]
        if bad:
            fails.append(f"{k}: {bad}")

    # --- reproduction gate ------------------------------------------------
    e = json.loads(RUN.EXP4N_N4.read_text())
    g = recs[("N4", "J100")]
    repro = None
    if g:
        c = g["outcome"]
        repro = (c["objective_EXACT"] == repr(e["objective_EXACT"]) and
                 c["plan_digest"] == e["plan_digest"] and
                 c["rounds"] == e["rounds"] and c["converged"] == e["converged"]
                 and [t["objective"] for t in c["round_trajectory"]] ==
                 [t["objective"] for t in e["round_trajectory"]])
        if not repro:
            fails.append("EXP5_REPRODUCTION_FAILURE")

    # --- firewall: every within-network pair vs J100, every structure pair --
    fw = {"frontier": [], "structure": []}
    for n in RUN.NETWORKS:
        ref = recs[(n, "J100")]
        for cid in grid:
            r = recs[(n, cid)]
            if cid == "J100" or r is None or ref is None:
                continue
            res_ = compare(C.receipt_for(ref, C.EXP5_FRONTIER),
                           C.receipt_for(r, C.EXP5_FRONTIER), C.EXP5_FRONTIER)
            ok = res_.__class__.__name__ == "ComparisonResult"
            fw["frontier"].append({"network": n, "cell": cid, "admitted": ok,
                                   "declared": list(res_.declared_differences)
                                   if ok else repr(res_)[:600]})
            if not ok:
                fails.append(f"frontier comparison {n} J100 vs {cid} refused")
    for cid in grid:
        r0, r4 = recs[("N0", cid)], recs[("N4", cid)]
        if r0 is None or r4 is None:
            continue
        res_ = compare(C.receipt_for(r0, C.EXP5_STRUCTURE),
                       C.receipt_for(r4, C.EXP5_STRUCTURE), C.EXP5_STRUCTURE)
        ok = res_.__class__.__name__ == "ComparisonResult"
        row = {"cell": cid, "admitted": ok}
        if ok:
            row.update(effect_N4_minus_N0=res_.effect,
                       effect_pct_of_N0=res_.effect_pct,
                       declared=list(res_.declared_differences))
        else:
            row["refusal"] = repr(res_)[:600]
            fails.append(f"structure comparison at {cid} refused")
        fw["structure"].append(row)

    # --- monotonicity over realized-plan nesting --------------------------
    mono = []
    for n in RUN.NETWORKS:
        for lo_c, ti_c in MR.nested_pairs(list(grid.values())):
            L, T = recs[(n, lo_c.id)], recs[(n, ti_c.id)]
            if L is None or T is None:
                continue
            uh = f(T["resource"]["used"]["revenue_veh_hours"])
            up = {p: f(v) for p, v in
                  T["resource"]["used"]["peak_proxy_by_period"].items()}
            nests = uh <= lo_c.envelope.hours_cap * (1 + EPS) and all(
                up[p] <= lo_c.envelope.peak_proxy_caps[p] * (1 + EPS)
                for p in MR.PERIODS)
            oL, oT = f(L["outcome"]["objective_EXACT"]), f(T["outcome"]["objective_EXACT"])
            reg = 100.0 * (oL - oT) / oT
            if not nests:
                status = "NOT_NESTED"      # cannot happen under domination
            elif oL <= oT:
                status = "MONOTONE"
            elif reg <= band:
                status = "UNRESOLVED"
            else:
                status = "EXP5_MONOTONICITY_FAILURE"
            mono.append({"network": n, "looser": lo_c.id, "tighter": ti_c.id,
                         "obj_looser": repr(oL), "obj_tighter": repr(oT),
                         "regression_pct": reg if oL > oT else 0.0,
                         "realized_nesting": nests, "status": status})
    mfail = [m for m in mono if m["status"] in ("EXP5_MONOTONICITY_FAILURE",
                                                  "NOT_NESTED")]
    if mfail:
        fails.append(f"EXP5_MONOTONICITY_FAILURE on {len(mfail)} pairs")

    # --- order-invariance sentinels ---------------------------------------
    sent = []
    for n, cid in RUN.SENTINELS:
        s, p = load(RUN.SENT, n, cid), recs.get((n, cid))
        if s is None or p is None:
            sent.append({"network": n, "cell": cid, "status": "NOT_RUN"})
            continue
        eq = (s["outcome"]["objective_EXACT"] == p["outcome"]["objective_EXACT"]
              and s["outcome"]["plan_digest"] == p["outcome"]["plan_digest"]
              and s["outcome"]["rounds"] == p["outcome"]["rounds"])
        sent.append({"network": n, "cell": cid, "equal": eq,
                     "status": "PASS" if eq else "EXP5_ORDER_DEPENDENCE_FAILURE"})
        if not eq:
            fails.append(f"EXP5_ORDER_DEPENDENCE_FAILURE {n} {cid}")
    sent_missing = [x for x in sent if x["status"] == "NOT_RUN"]

    # --- frontier tables and marginals -------------------------------------
    table = []
    for (n, cid), r in recs.items():
        if r is None:
            continue
        o, res = r["outcome"], r["resource"]
        fx = o["fitness_EXACT"]
        table.append({
            "network": n, "cell": cid, "arm": grid[cid].arm,
            "hours_mult": grid[cid].envelope.hours_multiplier,
            "peak_mult": grid[cid].envelope.peak_multiplier,
            "objective": f(o["objective_EXACT"]),
            "generalized_cost": f(fx["generalized_cost"]),
            "unserved_demand": f(fx["unserved_demand"]),
            "served_demand": f(fx["served_demand"]),
            "gc_per_served_trip": f(fx["gc_per_served_trip"]),
            "hours_cap": f(res["requested"]["hours_cap"]),
            "hours_used": f(res["used"]["revenue_veh_hours"]),
            "hours_util_pct": res["utilization_pct"]["hours"],
            "peak_used": {p: f(v) for p, v in
                          res["used"]["peak_proxy_by_period"].items()},
            "peak_util_pct": res["utilization_pct"]["peak_proxy_by_period"],
            "binding_1e-6": res["binding_within_1e-6_rel"],
            "near_binding_0.1pct": res["near_binding_within_0.1pct"],
            "n_off": o["n_off"], "n_active": o["n_active"],
            "rounds": o["rounds"], "plan_digest": o["plan_digest"],
            "seconds": o["seconds"]})
    by = {(t["network"], t["cell"]): t for t in table}

    def chain(n, ids):
        return [by.get((n, i)) for i in ids]

    marg = {"units": {
        "A_joint": "objective change per +1 percentage point of joint scale",
        "B_hours_only": "objective change per +1 revenue vehicle-hour of cap",
        "C_peak_proxy_only": "objective change per +1 proxy unit of the pm_peak "
                             "cap (all six periods scale together; pm_peak is "
                             "the reference period, the base's largest)"},
        "rule": "adjacent-level finite differences only; no per-bus figure; "
                "no knee", "rows": []}
    levels = [round(m * 100) for m in MR.LEVELS]
    for n in RUN.NETWORKS:
        for arm, ids in (
                ("A_joint", [f"J{l:03d}" for l in levels]),
                ("B_hours_only", [("J100" if l == 100 else f"H{l:03d}") for l in levels]),
                ("C_peak_proxy_only", [("J100" if l == 100 else f"P{l:03d}") for l in levels])):
            ch = chain(n, ids)
            for x, y in zip(ch, ch[1:]):
                if x is None or y is None:
                    continue
                d_obj = y["objective"] - x["objective"]
                if arm == "A_joint":
                    d_res = 100 * (y["hours_mult"] - x["hours_mult"])
                elif arm == "B_hours_only":
                    d_res = y["hours_cap"] - x["hours_cap"]
                else:
                    d_res = base.peak_proxy_caps["pm_peak"] * (
                        y["peak_mult"] - x["peak_mult"])
                marg["rows"].append({
                    "network": n, "arm": arm, "from": x["cell"], "to": y["cell"],
                    "d_objective": d_obj, "d_resource": d_res,
                    "objective_per_unit": d_obj / d_res,
                    "d_served": y["served_demand"] - x["served_demand"],
                    "served_per_unit": (y["served_demand"] - x["served_demand"]) / d_res})

    blocking = {}
    for p in sorted((RUN.OUT / "blocking").glob("*.json")):
        b = json.loads(p.read_text())
        blocking[p.stem] = {"verdict": b["verdict"],
                            "raw": b.get("instrument_raw_verdict"),
                            "bracket": b.get("fleet_bracket_blocks"),
                            "tt_vs_model_hours": b.get(
                                "timetable_vs_model_hours_rel_diff")}

    unresolved = [m for m in mono if m["status"] == "UNRESOLVED"]
    complete = not missing and not sent_missing
    status = ("EXP5_FRONTIER_CERTIFIED" if complete and not fails else
              "INCOMPLETE" if not complete and not fails else
              "FAILED: " + "; ".join(fails))
    out = {"artifact": "EXP5_ANALYSIS", "written_utc": utc(),
           "status": status, "contract_file_sha256":
               con.get("contract_file_sha256"),
           "missing_cells": missing, "failures": fails,
           "checks": {k: {"n": len(v), "all_pass": all(ok for _, ok in v)}
                      for k, v in checks.items()},
           "reproduction_gate": {"N4_J100_equals_EXP4N": repro},
           "firewall": fw, "monotonicity": {
               "band_pct": band, "n_pairs": len(mono),
               "n_monotone": sum(m["status"] == "MONOTONE" for m in mono),
               "n_unresolved": len(unresolved), "n_failed": len(mfail),
               "pairs": mono},
           "sentinels": sent, "frontier": table, "marginals": marg,
           "blocking_DIAGNOSTIC_ONLY": blocking}
    atomic_write_json(RUN.OUT / "EXP5_ANALYSIS.json", out)
    print(status)
    for k, v in out["checks"].items():
        print(f"  {k:18s} {v['n']:2d} {'PASS' if v['all_pass'] else 'FAIL'}")
    print(f"  reproduction       {repro}")
    print(f"  monotonicity       {out['monotonicity']['n_monotone']} monotone, "
          f"{len(unresolved)} unresolved, {len(mfail)} failed of {len(mono)}")
    print(f"  sentinels          {[s['status'] for s in sent]}")
    print(f"  firewall           frontier {sum(x['admitted'] for x in fw['frontier'])}/"
          f"{len(fw['frontier'])}, structure "
          f"{sum(x['admitted'] for x in fw['structure'])}/{len(fw['structure'])}")
    return 0 if not fails else 3


if __name__ == "__main__":
    raise SystemExit(main())
