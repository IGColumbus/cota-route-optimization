#!/usr/bin/env python3
"""Exp 4 resource normalization audit, step 9: the pilot comparison.

AUDIT ONLY. Re-optimizes nothing; reads the pilot results and the frozen Exp 4
records. Writes EXP4_COMMON_CAP_PILOT.csv and EXP4_RESOURCE_AUDIT_RESULT.json.
"""
from __future__ import annotations
import csv, json, math, statistics as st, sys
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "exp4_resource_audit"
PILOT = OUT / "pilot"
PERIODS = ["early", "am_peak", "midday", "pm_peak", "evening", "owl"]
LEADER = "exp4|exp4-pool-v1|65lines#ecb2ffc4bcce"


def rank_of(vals):
    s = sorted(range(len(vals)), key=lambda i: vals[i])
    r = [0]*len(vals)
    for pos, i in enumerate(s): r[i] = pos+1
    return r


def pearson(x, y):
    n = len(x); mx = sum(x)/n; my = sum(y)/n
    num = sum((a-mx)*(b-my) for a, b in zip(x, y))
    den = (sum((a-mx)**2 for a in x)*sum((b-my)**2 for b in y))**0.5
    return num/den if den else float("nan")


def kendall_tau(x, y):
    con = dis = 0
    for i, j in combinations(range(len(x)), 2):
        a = (x[i]-x[j]); b = (y[i]-y[j])
        if a*b > 0: con += 1
        elif a*b < 0: dis += 1
    tot = con+dis
    return ((con-dis)/tot if tot else float("nan")), dis, tot


def main() -> int:
    caps = {r["candidate_id"]: r for r in
            csv.DictReader(open(OUT / "EXP4_CANDIDATE_RESOURCE_CAPS.csv"))}
    spec = json.loads((OUT / "pilot_spec.json").read_text())
    common = {k: float(v) for k, v in spec["common_envelope"].items()}

    rows = []
    for p in sorted(PILOT.glob("*.json")):
        d = json.load(open(p))
        if "error" in d:
            print(f"ERROR RECORD: {d.get('label')} {d['error']}"); return 2
        k = d["candidate_id"]; c = caps[k]
        f = d.get("fitness_EXACT", {})
        rows.append({
            "label": d["label"], "candidate_id": k,
            "original_certified_rank_of_200": int(c["certified_rank"]),
            "original_objective": float(d["original_certified_objective"]),
            "normalized_objective": float(d["objective_EXACT"]),
            "original_sum_cap": float(d["original_sum_cap"]),
            "common_sum_cap": sum(common.values()),
            "normalized_veh_hours": float(f.get("revenue_veh_hours", float("nan"))),
            "normalized_peak_scalar": float(f.get("peak_vehicles", float("nan"))),
            "rounds": int(d.get("rounds", -1)),
            "converged": bool(d.get("converged", False)),
            "guarantee": str(d.get("guarantee", "")),
            "seconds": float(d.get("seconds", float("nan"))),
            **{f"original_{q}_cap": float(c[f"{q}_cap"]) for q in PERIODS},
            **{f"common_{q}_cap": common[q] for q in PERIODS},
        })
    if len(rows) != 10:
        print(f"FATAL: {len(rows)} pilot results, expected 10"); return 2

    orig_r = rank_of([r["original_objective"] for r in rows])
    norm_r = rank_of([r["normalized_objective"] for r in rows])
    for r, a, b in zip(rows, orig_r, norm_r):
        r["original_rank_in_pilot"] = a
        r["normalized_rank_in_pilot"] = b
        r["rank_movement"] = a - b            # positive = improved position
        r["delta_absolute"] = r["normalized_objective"] - r["original_objective"]
        r["delta_percent"] = r["delta_absolute"]/r["original_objective"]*100
        r["hours_cap"] = 2517.1833333333334
        r["hours_feasible"] = r["normalized_veh_hours"] <= 2517.1833333333334
        r["hit_max_rounds"] = r["rounds"] >= 40

    rows.sort(key=lambda r: r["original_rank_in_pilot"])
    with open(OUT / "EXP4_COMMON_CAP_PILOT.csv", "w", newline="") as fh:
        keys = ["label", "candidate_id", "original_certified_rank_of_200",
                "original_rank_in_pilot", "normalized_rank_in_pilot",
                "rank_movement", "original_objective", "normalized_objective",
                "delta_absolute", "delta_percent", "original_sum_cap",
                "common_sum_cap", "normalized_veh_hours", "hours_cap",
                "hours_feasible", "normalized_peak_scalar", "rounds",
                "hit_max_rounds", "converged", "guarantee", "seconds"] + \
               [f"original_{q}_cap" for q in PERIODS] + \
               [f"common_{q}_cap" for q in PERIODS]
        w = csv.DictWriter(fh, fieldnames=keys, extrasaction="ignore")
        w.writeheader()
        for r in rows: w.writerow({k: (repr(r[k]) if isinstance(r[k], float) else r[k]) for k in keys})

    oo = [r["original_objective"] for r in rows]
    nn = [r["normalized_objective"] for r in rows]
    sp = pearson(rank_of(oo), rank_of(nn))
    tau, dis, tot = kendall_tau(oo, nn)
    winner = next(r for r in rows if r["candidate_id"] == LEADER)
    best_norm = min(rows, key=lambda r: r["normalized_objective"])
    dperc = [r["delta_percent"] for r in rows]
    corr_cap_delta = pearson([r["original_sum_cap"] for r in rows], dperc)

    res = {
        "audit": "exp4_resource_normalization",
        "pilot_n": len(rows),
        "common_envelope": common,
        "common_envelope_source": spec["common_envelope_source"],
        "only_change": "cons['resource']['peak_fleet_by_period']: 'baseline' sentinel -> explicit dict",
        "all_converged": all(r["converged"] for r in rows),
        "n_hit_max_rounds": sum(1 for r in rows if r["hit_max_rounds"]),
        "all_hours_feasible": all(r["hours_feasible"] for r in rows),
        "delta_percent": {"min": min(dperc), "median": st.median(dperc),
                          "mean": sum(dperc)/len(dperc), "max": max(dperc),
                          "spread_pp": max(dperc)-min(dperc)},
        "spearman_original_vs_normalized_rank": sp,
        "kendall_tau": tau,
        "pairwise_reversals": dis,
        "pairwise_total": tot,
        "original_winner": {
            "candidate_id": LEADER,
            "original_rank_in_pilot": winner["original_rank_in_pilot"],
            "normalized_rank_in_pilot": winner["normalized_rank_in_pilot"],
            "remains_best": winner["normalized_rank_in_pilot"] == 1,
            "delta_percent": winner["delta_percent"]},
        "best_under_common_cap": {
            "label": best_norm["label"],
            "candidate_id": best_norm["candidate_id"],
            "original_certified_rank_of_200": best_norm["original_certified_rank_of_200"],
            "normalized_objective": best_norm["normalized_objective"],
            "beats_original_winner_by":
                winner["normalized_objective"] - best_norm["normalized_objective"],
            "beats_original_winner_by_pct":
                (winner["normalized_objective"] - best_norm["normalized_objective"])
                / winner["normalized_objective"] * 100},
        "pearson_originalSumCap_vs_deltaPercent": corr_cap_delta,
        "rows": rows,
    }
    (OUT / "EXP4_RESOURCE_AUDIT_RESULT.json").write_text(json.dumps(res, indent=1))

    print("=== §9 PILOT COMPARISON ===")
    print("%-18s %4s %4s %5s %16s %16s %13s %9s %5s %6s" % (
        "label", "o200", "oP", "nP", "original", "normalized", "delta", "pct", "rnds", "conv"))
    for r in rows:
        print("%-18s %4d %4d %5d %16.4f %16.4f %13.4f %+8.4f%% %5d %6s%s" % (
            r["label"], r["original_certified_rank_of_200"], r["original_rank_in_pilot"],
            r["normalized_rank_in_pilot"], r["original_objective"],
            r["normalized_objective"], r["delta_absolute"], r["delta_percent"],
            r["rounds"], r["converged"], "  <MAXR>" if r["hit_max_rounds"] else ""))
    print()
    print("spearman(original rank, normalized rank) = %+.4f" % sp)
    print("kendall tau = %+.4f   pairwise reversals %d of %d" % (tau, dis, tot))
    print("original winner: pilot rank %d -> %d  remains best: %s" % (
        winner["original_rank_in_pilot"], winner["normalized_rank_in_pilot"],
        winner["normalized_rank_in_pilot"] == 1))
    b = res["best_under_common_cap"]
    print("best under common cap: %s (original rank %d of 200), beats the original "
          "winner by %.4f (%.4f%%)" % (b["label"], b["original_certified_rank_of_200"],
                                       b["beats_original_winner_by"],
                                       b["beats_original_winner_by_pct"]))
    print("delta%%: min %.4f median %.4f max %.4f  spread %.4f pp" % (
        res["delta_percent"]["min"], res["delta_percent"]["median"],
        res["delta_percent"]["max"], res["delta_percent"]["spread_pp"]))
    print("pearson(original sum cap, delta%%) = %+.4f" % corr_cap_delta)
    print("all converged: %s   hit max rounds: %d   all hours-feasible: %s" % (
        res["all_converged"], res["n_hit_max_rounds"], res["all_hours_feasible"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
