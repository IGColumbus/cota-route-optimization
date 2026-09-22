#!/usr/bin/env python3
"""Exp 4 resource normalization audit, steps 3-6.

AUDIT ONLY. Reads outputs/exp4/run/ read-only; writes only under
outputs/exp4_resource_audit/. Re-optimizes nothing.
"""
from __future__ import annotations
import csv, json, math, statistics as st, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src")); sys.path.insert(0, str(ROOT / "scripts"))
RUN = ROOT / "outputs" / "exp4" / "run"
OUT = ROOT / "outputs" / "exp4_resource_audit"
LEADER = "exp4|exp4-pool-v1|65lines#ecb2ffc4bcce"
PERIODS = ["early", "am_peak", "midday", "pm_peak", "evening", "owl"]


def pearson(x, y):
    n = len(x); mx = sum(x)/n; my = sum(y)/n
    num = sum((a-mx)*(b-my) for a, b in zip(x, y))
    den = (sum((a-mx)**2 for a in x)*sum((b-my)**2 for b in y))**0.5
    return num/den if den else float("nan")


def rank(v):
    s = sorted(range(len(v)), key=lambda i: v[i]); r = [0.0]*len(v); i = 0
    while i < len(s):
        j = i
        while j+1 < len(s) and v[s[j+1]] == v[s[i]]: j += 1
        avg = (i+j)/2 + 1
        for k in range(i, j+1): r[s[k]] = avg
        i = j+1
    return r


def spearman(x, y):
    return pearson(rank(x), rank(y))


def quant(a, q):
    b = sorted(a); i = q*(len(b)-1); lo = int(math.floor(i)); hi = int(math.ceil(i))
    return b[lo] if lo == hi else b[lo] + (b[hi]-b[lo])*(i-lo)


def main() -> int:
    from cota_opt.configs import load_constraints, load_cost_weights
    from cota_opt.cost import CostWeights
    from cota_opt.exp1 import build_setup as exp1_setup
    from cota_opt.exp4_assemble import assemble
    from cota_opt.exp4_network import Exp4Selection
    from exp2_treatments import _Baseline
    from exp4_c10_fixtures import POOL_VERSION, _BY_RID, _boot, _first_dep_by_period
    import numpy as np

    rows = list(csv.DictReader(open(OUT / "EXP4_CANDIDATE_RESOURCE_CAPS.csv")))
    ref = [r for r in rows if r["candidate_id"] == "REFERENCE_NETWORK"][0]
    cand = [r for r in rows if r["candidate_id"] != "REFERENCE_NETWORK"]
    for r in cand:
        for p in PERIODS: r[f"{p}_cap"] = float(r[f"{p}_cap"])
        r["certified_objective"] = float(r["certified_objective"])
        r["certified_rank"] = int(r["certified_rank"])
        r["discovery_rank"] = int(r["discovery_rank"])
        r["baseline_vehicle_hours"] = float(r["baseline_vehicle_hours"])
        r["optimized_vehicle_hours"] = float(r["optimized_vehicle_hours"])
    REF = {p: float(ref[f"{p}_cap"]) for p in PERIODS}
    REF_BVH = float(ref["baseline_vehicle_hours"])
    print(f"{len(cand)} candidates; reference caps {json.dumps({p: round(REF[p],4) for p in PERIODS})}")

    # ---------- 3. dispersion ------------------------------------------
    summary = {"periods": {}, "reference_caps": REF,
               "reference_baseline_vehicle_hours": REF_BVH,
               "n_candidates": len(cand)}
    srows = []
    for p in PERIODS:
        a = [r[f"{p}_cap"] for r in cand]
        m = sum(a)/len(a); sd = st.pstdev(a)
        d = {"min": min(a), "p05": quant(a, .05), "p25": quant(a, .25),
             "median": st.median(a), "mean": m, "p75": quant(a, .75),
             "p95": quant(a, .95), "max": max(a), "stdev": sd,
             "coefficient_of_variation": sd/m if m else float("nan"),
             "range_absolute": max(a)-min(a),
             "range_ratio_max_over_min": (max(a)/min(a) if min(a) > 0 else None),
             "range_pct_of_min": ((max(a)-min(a))/min(a)*100 if min(a) > 0 else None),
             "reference_cap": REF[p],
             "median_as_pct_of_reference": st.median(a)/REF[p]*100,
             "n_candidates_above_reference": sum(1 for v in a if v > REF[p])}
        summary["periods"][p] = d
        srows.append({"period": p, **{k: repr(v) for k, v in d.items()}})
    with open(OUT / "EXP4_RESOURCE_CAP_SUMMARY.csv", "w", newline="") as f:
        wri = csv.DictWriter(f, fieldnames=list(srows[0].keys()))
        wri.writeheader(); wri.writerows(srows)

    # ---------- 4. cap vs certified performance ------------------------
    obj = [r["certified_objective"] for r in cand]
    crank = [float(r["certified_rank"]) for r in cand]
    aggs = {
        "sum_of_six_period_caps": [sum(r[f"{p}_cap"] for p in PERIODS) for r in cand],
        "max_period_cap": [max(r[f"{p}_cap"] for p in PERIODS) for r in cand],
        "sum_normalized_by_reference_sum":
            [sum(r[f"{p}_cap"] for p in PERIODS)/sum(REF.values()) for r in cand],
        "baseline_vehicle_hours_existing_project_scalar":
            [r["baseline_vehicle_hours"] for r in cand],
    }
    corr = {"note": ("lower objective is better, so a NEGATIVE correlation "
                     "between cap and objective means a larger endogenous "
                     "budget went with a BETTER certified result. Correlation "
                     "is not causation and none is claimed."),
            "per_period": {}, "aggregate": {}}
    for p in PERIODS:
        a = [r[f"{p}_cap"] for r in cand]
        corr["per_period"][p] = {
            "pearson_cap_vs_objective": pearson(a, obj),
            "spearman_cap_vs_objective": spearman(a, obj),
            "spearman_cap_vs_certified_rank": spearman(a, crank)}
    for name, a in aggs.items():
        corr["aggregate"][name] = {
            "pearson_vs_objective": pearson(a, obj),
            "spearman_vs_objective": spearman(a, obj),
            "spearman_vs_certified_rank": spearman(a, crank)}
    # geometry change -> cap change, against the reference
    gsum = [sum(r[f"{p}_cap"] for p in PERIODS) for r in cand]
    dsum = [g - sum(REF.values()) for g in gsum]
    dbvh = [r["baseline_vehicle_hours"] - REF_BVH for r in cand]
    corr["geometry_change_vs_cap_change"] = {
        "pearson_dBaselineVehHours_vs_dSumCap": pearson(dbvh, dsum),
        "spearman_dBaselineVehHours_vs_dSumCap": spearman(dbvh, dsum),
        "interpretation": ("both are read off the same candidate baseline "
                           "evaluation, so a strong positive relation is "
                           "mechanical rather than empirical")}
    summary["correlations"] = corr

    # ---------- 5. cross-feasibility, no re-optimization ---------------
    env = json.loads((ROOT / "outputs" / "CANONICAL_ENVELOPE.json").read_text())
    VH_CAP = float(env["weekday_revenue_vehicle_hours"])
    _c = load_constraints()
    cons = {**_c, "resource": {**_c["resource"],
                               "weekday_revenue_vehicle_hours": VH_CAP}}
    TOL = float(_c["resource"].get("budget_tolerance", 0.0))
    w = CostWeights.from_config(load_cost_weights())
    st_ = _boot(); H, graph = st_["H"], st_["graph"]
    first_dep = _first_dep_by_period()
    prop = json.loads((RUN / "proposals.json").read_text())["proposals"]
    lines_of = {p["state_key"]: p["lines"] for p in prop}
    cert = {}
    for p in (RUN / "certified").glob("*.json"):
        d = json.load(open(p))
        if "objective_EXACT" in d: cert[d["state_key"]] = d

    CAPS = {r["candidate_id"]: {p: r[f"{p}_cap"] for p in PERIODS} for r in cand}
    WIN = CAPS[LEADER]
    MINC = {p: min(CAPS[k][p] for k in CAPS) for p in PERIODS}
    MEDC = {p: st.median([CAPS[k][p] for k in CAPS]) for p in PERIODS}
    MAXC = {p: max(CAPS[k][p] for k in CAPS) for p in PERIODS}
    ENVS = {"A_own": None, "B_reference": REF, "C_winner": WIN,
            "D_componentwise_min": MINC, "E_componentwise_median": MEDC,
            "F_componentwise_max": MAXC}

    frows = []
    t0 = time.time()
    for i, k in enumerate(sorted(cert), 1):
        sel = Exp4Selection(POOL_VERSION, frozenset(lines_of[k]), frozenset())
        blt = assemble(sel, _BY_RID, graph, H.baseline.network.stops,
                       pool_version=POOL_VERSION, first_dep_sec_by_period=first_dep)
        b_ed = _Baseline(H.baseline, blt.network, blt.tstats)
        e1 = exp1_setup(b_ed, constraints=cons, weights=w)
        m = e1.model
        raw = cert[k]["plan_EXACT"]
        pl = {}
        for kk, v in raw.items():
            r_, _, p_ = kk.partition("|")
            pl[(r_, p_)] = (math.inf if (v is None or isinstance(v, str) or
                            (isinstance(v, float) and (math.isinf(v) or v >= 1e5)))
                            else float(v))
        h = np.array([pl[key] for key in m.keys], float)
        fit = m.evaluate_array(h)
        use = {p: float(fit.peak_by_period.get(p, 0.0)) for p in PERIODS}
        row = {"candidate_id": k, "certified_rank": cert_rank_of(cand, k),
               "certified_objective": repr(cert[k]["objective_EXACT"]),
               "hours_used": repr(float(fit.revenue_veh_hours)),
               "hours_cap": repr(VH_CAP),
               "hours_feasible": float(fit.revenue_veh_hours) <= VH_CAP*(1+TOL),
               **{f"use_{p}": repr(use[p]) for p in PERIODS}}
        for name, cap in ENVS.items():
            c = CAPS[k] if cap is None else cap
            bad = [p for p in PERIODS if use[p] > c[p]*(1+TOL) + 1e-9]
            row[f"feasible_{name}"] = (not bad)
            row[f"failing_periods_{name}"] = ";".join(bad)
        frows.append(row)
        if i % 50 == 0: print(f"  cross-feas {i}/{len(cert)} ({time.time()-t0:.0f}s)")
    with open(OUT / "EXP4_FINALIST_CROSS_FEASIBILITY.csv", "w", newline="") as f:
        wri = csv.DictWriter(f, fieldnames=list(frows[0].keys()))
        wri.writeheader(); wri.writerows(frows)

    cf = {"envelopes_are_DIAGNOSTIC_not_recommended_budgets": True,
          "fraction_feasible": {}}
    for name in ENVS:
        n = sum(1 for r in frows if r[f"feasible_{name}"])
        cf["fraction_feasible"][name] = {"n": n, "pct": n/len(frows)*100}
    top20 = sorted(frows, key=lambda r: float(r["certified_objective"]))[:20]
    cf["top20_feasible_under_reference"] = sum(1 for r in top20 if r["feasible_B_reference"])
    cf["winner_feasible_under_reference"] = next(
        r["feasible_B_reference"] for r in frows if r["candidate_id"] == LEADER)
    cf["winner_feasible_under_min"] = next(
        r["feasible_D_componentwise_min"] for r in frows if r["candidate_id"] == LEADER)
    top = sorted(frows, key=lambda r: float(r["certified_objective"]))[:5]
    mutual = {}
    for a in top:
        ka = a["candidate_id"]
        mutual[ka] = {}
        for b in top:
            kb = b["candidate_id"]
            cb = CAPS[kb]
            bad = [p for p in PERIODS if float(a[f"use_{p}"]) > cb[p]*(1+TOL)+1e-9]
            mutual[ka][kb] = (not bad)
    cf["top5_mutual_feasibility_plan_row_vs_cap_col"] = mutual
    summary["cross_feasibility"] = cf

    # ---------- 6. savings hypothesis ----------------------------------
    sav = []
    for r in cand:
        s = sum(r[f"{p}_cap"] for p in PERIODS)
        sav.append((s - sum(REF.values()), r))
    sav.sort(key=lambda t: t[0])
    def brief(r, d):
        return {"candidate_id": r["candidate_id"],
                "certified_rank": r["certified_rank"],
                "certified_objective": r["certified_objective"],
                "sum_cap": sum(r[f"{p}_cap"] for p in PERIODS),
                "sum_cap_minus_reference": d,
                "baseline_vehicle_hours": r["baseline_vehicle_hours"],
                "baseline_vh_minus_reference": r["baseline_vehicle_hours"]-REF_BVH,
                "optimized_vehicle_hours": r["optimized_vehicle_hours"],
                "caps": {p: r[f"{p}_cap"] for p in PERIODS}}
    med = sorted(cand, key=lambda r: r["certified_rank"])[len(cand)//2]
    rk = {r["certified_rank"]: r for r in cand}
    summary["savings_hypothesis"] = {
        "largest_cap_decrease_vs_reference": brief(sav[0][1], sav[0][0]),
        "largest_cap_increase_vs_reference": brief(sav[-1][1], sav[-1][0]),
        "winner": brief(rk[1], sum(rk[1][f"{p}_cap"] for p in PERIODS)-sum(REF.values())),
        "runner_up": brief(rk[2], sum(rk[2][f"{p}_cap"] for p in PERIODS)-sum(REF.values())),
        "median_candidate": brief(med, sum(med[f"{p}_cap"] for p in PERIODS)-sum(REF.values())),
        "mechanism": ("the cap IS the candidate's own baseline peak_by_period "
                      "(exp2.py:324), so any geometry that lowers baseline peak "
                      "demand lowers its own optimization budget by exactly the "
                      "same amount"),
    }
    (OUT / "EXP4_RESOURCE_CAP_SUMMARY.json").write_text(json.dumps(summary, indent=1))
    print("wrote summary + cross-feasibility")
    print(json.dumps({k: v for k, v in cf["fraction_feasible"].items()}, indent=1))
    return 0


def cert_rank_of(cand, k):
    for r in cand:
        if r["candidate_id"] == k: return r["certified_rank"]
    return ""


if __name__ == "__main__":
    raise SystemExit(main())
