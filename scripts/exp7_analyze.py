#!/usr/bin/env python3
"""Experiment 7 acceptance gates, prices, F4, AF1 and cross-level findings.

Reads only frozen/produced artifacts; writes outputs/exp7/EXP7_ANALYSIS.json.
Every reported within-level comparison is a firewall `compare()` under the
per-level contract that governs it (exp7_contracts.contracts_for). Cross-level
statements use only quantities admitted within their own level, and the
classification rules of exp7_classify (docs/EXPERIMENT7_AMENDMENT.md section 7).

Blocking statuses: EXP7_CLOSURE_CEILING_FAILURE, EMPTINESS_CONTRADICTED,
EXP7_REFERENCE_CLOSURE_FAILURE, a monotonicity violation, a firewall refusal,
a record-check failure, a sentinel mismatch.
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

import exp6_grid as G  # noqa: E402
import exp7_classify as C  # noqa: E402
import exp7_closure as E  # noqa: E402
import exp7_contracts as K  # noqa: E402
import exp7_run as R  # noqa: E402
from exp45_certify_cell import atomic_write_json, utc  # noqa: E402


def _load(p):
    return json.loads((ROOT / p).read_text())


def _cls(r):
    if r["status"] != "CERTIFIED":
        return {"status": r["status"]}
    return {"status": "CERTIFIED", "objective": float(r["outcome"]["objective_EXACT"]),
            "plan_digest": r["outcome"]["plan_digest"]}


def _admitted(res):
    return res.__class__.__name__ == "ComparisonResult"


def main() -> int:
    from cota_opt.firewall import compare
    ap = argparse.ArgumentParser()
    ap.add_argument("--partial", action="store_true")
    a = ap.parse_args()
    con = R.contract()
    lvs = R.levels(con)
    order = con["level_order"]
    base = order[0]
    specs = G.specs(con["catalog"]["digest"])
    fails: list[str] = []
    out: dict = {"artifact": "EXP7_ANALYSIS", "written_utc": utc(),
                 "contract_file": "outputs/exp7/EXP7_CONTRACT.json"}

    # ---- closure states and final/initial records ---------------------------
    init, final, states = {}, {}, {}
    for track, t in con["tracks"].items():
        for n in t["networks"]:
            sp = R.CLOS / track / f"closure_state_{n}.json"
            st = json.loads(sp.read_text()) if sp.exists() else None
            states[(track, n)] = st
            if st is None or st.get("status") != E.FIXED_POINT:
                if st is not None and st.get("status"):
                    fails.append(f"closure {track} {n}: {st['status']}")
                elif not a.partial:
                    print("incomplete closure", track, n)
                    return 2
                continue
            for lv in order:
                for c in t["policies"]:
                    init[(track, lv, n, c)] = json.loads(R.resolve_initial(
                        con, track, lv, n, c).read_text())
                    final[(track, lv, n, c)] = _load(st["best"][f"{lv}|{c}"]["ref"])
    out["closure"] = {f"{t}/{n}": (None if s is None else {
        "status": s["status"], "passes": s["passes_completed"],
        "n_improvements": len(s["improvements"]),
        "improvements_by_stage": {g: sum(1 for i in s["improvements"]
                                         if i["stage"] == g) for g in "WX"}})
        for (t, n), s in states.items()}

    # ---- record checks -------------------------------------------------------
    rc = {"convergence": [], "feasible": [], "policy": [], "level": []}
    for (track, lv, n, c), r in final.items():
        if r["status"] != "CERTIFIED":
            if r["status"] != E.EMPTY:
                fails.append(f"{track}/{lv}/{n}_{c}: status {r['status']}")
            continue
        o = r["outcome"]
        rc["convergence"].append(o["converged"] and o["rounds"] < 120)
        rc["feasible"].append(r["resource"]["feasible_under_full_target_constraints"])
        pol = r.get("policy") or {}
        rc["policy"].append(pol.get("digest") == specs[c].digest)
        want = lvs[lv].digest
        got = r.get("level_digest", lvs[base].digest if lv == base else None)
        rc["level"].append(got == want)
    for k, v in rc.items():
        if not all(v):
            fails.append(f"record check {k}: {v.count(False)} failing")
    out["record_checks"] = {k: {"n": len(v), "all_pass": all(v)} for k, v in rc.items()}

    # ---- monotonicity (hard, within level) -----------------------------------
    t6 = con["tracks"].get("F6") or {"networks": [], "policies": [],
                                      "strict_pairs": []}
    strict = [tuple(x) for x in t6["strict_pairs"]]
    mono = []
    for n in t6["networks"]:
        if (states.get(("F6", n)) or {}).get("status") == E.FIXED_POINT:
            best = {(lv, c): E.Rec(**states[("F6", n)]["best"][f"{lv}|{c}"])
                    for lv in order for c in t6["policies"]}
            g = E.Group(order, t6["policies"])
            for m in E.monotonicity(g, best, strict, eps=C.TAU_ABS):
                mono.append({"network": n, **m})
    bad = [m for m in mono if not m["ok"]]
    if bad:
        fails.append(f"monotonicity: {len(bad)} violations")
    out["monotonicity"] = {"n_pairs": len(mono), "n_violations": len(bad),
                           "violations": bad[:40]}

    # ---- F6 prices (admitted within level) -----------------------------------
    prices = []
    for lv in order:
        cons = K.contracts_for(lvs[lv])
        for n in t6["networks"]:
            key = ("F6", lv, n, "REF")
            if key not in final:
                continue
            ref = final[key]
            comp = R._compile_all(con, n, ref, lvs[lv]) \
                if ref["status"] == "CERTIFIED" else {}
            for c in t6["policies"]:
                cell = final[("F6", lv, n, c)]
                adm = None
                if c in comp and ref["status"] == "CERTIFIED":
                    adm = comp[c]["violation"](ref) <= 0
                row = {"level": lv, "network": n, "cell": c,
                       "ref_plan_admissible_under_cell": adm,
                       **C.classify_price(_cls(ref), _cls(cell),
                                          ref_plan_admissible=adm),
                       "initial_price": None, "final_plan": _cls(cell).get("plan_digest")}
                ini = init[("F6", lv, n, c)]
                iref = init[("F6", lv, n, "REF")]
                if ini["status"] == "CERTIFIED" and iref["status"] == "CERTIFIED":
                    row["initial_price"] = (float(ini["outcome"]["objective_EXACT"])
                                            - float(iref["outcome"]["objective_EXACT"])) \
                        / float(iref["outcome"]["objective_EXACT"])
                if c != "REF" and cell["status"] == "CERTIFIED":
                    res = compare(K.receipt_for(ref, cons["EXP7_POLICY"], "F6"),
                                  K.receipt_for(cell, cons["EXP7_POLICY"], "F6"),
                                  cons["EXP7_POLICY"])
                    row["admitted"] = _admitted(res)
                    if not row["admitted"]:
                        row["refusal"] = repr(res)[:400]
                        fails.append(f"firewall EXP7_POLICY {lv} {n} {c}")
                if row["class"] == C.NEGATIVE:
                    fails.append(f"{C.NEGATIVE} {lv} {n} {c}")
                prices.append(row)
    out["f6_prices"] = prices

    # rank stability and transitions vs BASE
    rk = {}
    for lv in order:
        for n in t6["networks"]:
            vals = {r["cell"]: r["price"] for r in prices
                    if r["level"] == lv and r["network"] == n and r["cell"] != "REF"}
            digs = {r["cell"]: r["final_plan"] for r in prices
                    if r["level"] == lv and r["network"] == n}
            rk[f"{lv}/{n}"] = C.rank(vals, digests=digs, tau=1e-12)
    out["f6_ranks"] = rk
    trans, flips, decomp = [], [], []
    for r in prices:
        b = next((x for x in prices if x["level"] == base and
                  x["network"] == r["network"] and x["cell"] == r["cell"]), None)
        if b is None or r["level"] == base:
            continue
        tr = C.transition(final[("F6", base, r["network"], r["cell"])],
                          final[("F6", r["level"], r["network"], r["cell"])])
        if tr:
            trans.append({**{k: r[k] for k in ("level", "network", "cell")},
                          "transition": tr})
        sf = C.sign_flip(b["price"], r["price"], tau=0.0)
        if sf:
            flips.append({**{k: r[k] for k in ("level", "network", "cell")},
                          "flip": sf, "base_price": b["price"], "price": r["price"]})
        decomp.append({**{k: r[k] for k in ("level", "network", "cell")},
                       **C.decompose(r["initial_price"], r["price"], b["price"])})
    out["f6_transitions"] = trans
    out["f6_sign_changes"] = flips
    out["f6_basin_vs_sensitivity"] = decomp

    # ---- AF1: N3 - N0 at matched policy and level -----------------------------
    af1 = []
    for lv in order:
        cons = K.contracts_for(lvs[lv])
        for c in t6["policies"]:
            a0, a3 = final.get(("F6", lv, "N0", c)), final.get(("F6", lv, "N3", c))
            if not a0 or not a3:
                continue
            if a0["status"] != "CERTIFIED" or a3["status"] != "CERTIFIED":
                af1.append({"level": lv, "cell": c, "admitted": None,
                            "note": "empty feasible set"})
                continue
            res = compare(K.receipt_for(a0, cons["EXP7_STRUCTURE"], "F6"),
                          K.receipt_for(a3, cons["EXP7_STRUCTURE"], "F6"),
                          cons["EXP7_STRUCTURE"])
            row = {"level": lv, "cell": c, "admitted": _admitted(res)}
            if row["admitted"]:
                row.update(delta=res.effect, delta_pct_of_N0=res.effect_pct,
                           sign=C.sign(res.effect, C.TAU_ABS))
            else:
                row["refusal"] = repr(res)[:400]
                fails.append(f"firewall EXP7_STRUCTURE {lv} {c}")
            af1.append(row)
    out["af1_n3_minus_n0"] = af1

    # ---- F4 (REF-only track, matched procedure) --------------------------------
    f4 = []
    for lv in order:
        cons = K.contracts_for(lvs[lv])
        for x, y in (("N3", "N4"), ("N0", "N4"), ("N0", "N3")):
            rx, ry = final.get(("F4", lv, x, "REF")), final.get(("F4", lv, y, "REF"))
            if not rx or not ry:
                continue
            res = compare(K.receipt_for(rx, cons["EXP7_F4"], "F4"),
                          K.receipt_for(ry, cons["EXP7_F4"], "F4"),
                          cons["EXP7_F4"])
            row = {"level": lv, "control": x, "treatment": y,
                   "admitted": _admitted(res)}
            if row["admitted"]:
                row.update(delta=res.effect, delta_pct=res.effect_pct,
                           sign=C.sign(res.effect, C.TAU_ABS),
                           descriptors={n: {k: r["outcome"]["fitness_EXACT"].get(k)
                                            for k in ("served_demand",
                                                      "generalized_cost")}
                                        | {"n_off": r["outcome"]["n_off"],
                                           "plan": r["outcome"]["plan_digest"]}
                                        for n, r in ((x, rx), (y, ry))})
            else:
                row["refusal"] = repr(res)[:400]
                fails.append(f"firewall EXP7_F4 {lv} {x}-{y}")
            f4.append(row)
    for r in f4:
        b = next((z for z in f4 if z["level"] == base and z["control"] == r["control"]
                  and z["treatment"] == r["treatment"]), None)
        if b and r["level"] != base and b.get("delta") is not None \
                and r.get("delta") is not None:
            r["vs_base"] = C.sign_flip(b["delta"], r["delta"])
    out["f4"] = f4

    # ---- F1 adaptive (amendment 14.2): F6-track N0 REF vs the N0 current plan,
    # evaluated at the same level. The current-plan unserved demand at each level
    # is the Stage 1 fixed-plan row F1_BASELINE (same evaluator, same level).
    f1 = []
    for lv in order:
        r = final.get(("F6", lv, "N0", "REF"))
        ev = ROOT / "outputs/exp7/stage1/evals/N0" / f"{lv}.json"
        if not r or r["status"] != "CERTIFIED" or not ev.exists():
            continue
        e = json.loads(ev.read_text())
        if e.get("level_digest") not in (None, lvs[lv].digest):
            fails.append(f"F1 adaptive: stage1 eval level digest mismatch {lv}")
            continue
        ub = (e["rows"].get("F1_BASELINE") or {}).get("unserved_demand")
        u = float(r["outcome"]["fitness_EXACT"]["unserved_demand"])
        f1.append({"level": lv, "ref_unserved": u, "current_plan_unserved": ub,
                   "f1_pct": None if not ub else 100 * (u / ub - 1),
                   "ref_plan": r["outcome"]["plan_digest"]})
    out["f1_adaptive"] = f1

    # ---- sentinels -------------------------------------------------------------
    sent = []
    for track, lv, n, c in con["sentinels"]:
        p = R.SENT / track / lv / f"{n}_{c}.json"
        if not p.exists():
            sent.append({"cell": [track, lv, n, c], "ok": None})
            if not a.partial:
                fails.append("sentinel missing")
            continue
        s = json.loads(p.read_text())
        ref = json.loads(R.resolve_initial(con, track, lv, n, c).read_text())
        ok = all(s["outcome"][k] == ref["outcome"][k]
                 for k in ("objective_EXACT", "plan_digest", "rounds"))
        sent.append({"cell": [track, lv, n, c], "ok": ok})
        if not ok:
            fails.append(f"sentinel {track} {lv} {n} {c}")
    out["sentinels"] = sent

    out["failures"] = fails
    done = ("EXP7_STAGE2_REOPT_COMPLETE" if con.get("design") == "two_stage"
            else "EXP7_SENSITIVITY_CERTIFIED")      # amendment 14.3
    out["status"] = (done if not fails and not a.partial
                     else "EXP7_PARTIAL" if a.partial and not fails
                     else "EXP7_BLOCKED")
    if not con.get("frozen"):
        # a smoke or draft contract can never yield a certified status
        out["status"] = "NOT_CERTIFIABLE_UNFROZEN_CONTRACT(" + out["status"] + ")"
    atomic_write_json(R.OUT / "EXP7_ANALYSIS.json", out)
    print(out["status"], fails[:10])
    return 0 if not fails else 3


if __name__ == "__main__":
    raise SystemExit(main())
