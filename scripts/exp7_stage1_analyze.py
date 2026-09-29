#!/usr/bin/env python3
"""Experiment 7 Stage 1 analysis: finding quantities, classifications,
validation, completion state, and the preregistered Stage 2 selection metric.

Reads outputs/exp7/stage1/evals/<variant>/<level>.json (exp7_stage1.py) and
the frozen registry. Writes outputs/exp7/stage1/EXP7_STAGE1_ANALYSIS.json and
EXP7_STAGE1_TABLES.md. Pure computations are module functions (unit-tested in
tests/test_exp7_stage1.py).

Finding quantities at one level (all from fixed, frozen plans):
  F1   mean over the 3 Exp 1 seed plans of 100*(U(plan)/U(N0 baseline) - 1),
       U = unserved demand (N0).
  F2   100*(mean U(splice plans, N0S) / mean U(control plans, N0) - 1); also
       the objective analogue; NULL holds iff |F2| < the Exp 2B floor 0.287.
  F3   mean over 5 seeds of 100*(O(add_stop plan, N3) - O(control, N0)) / O(control).
  F4   F4_43 = 100*(O(N4) - O(N3 Exp 4A)) / O(N3);
       F4_40 = 100*(O(N4) - O(N0 J100)) / O(N0 J100).
  F5   marginal objective change per unit of resource, fixed Exp 5 plans:
       peak arm (primary, "per unit of peak resource"): (O(J100) - O(P090)) /
       u and (O(P110) - O(J100)) / u, u = 10% of the pm_peak cap in proxy
       units; joint arm: per percentage point between J090/J100/J110.
       Fixed-plan resource-order monotonicity O(90) >= O(100) >= O(110).
  F6   price(c) = 100*(O(c) - O(REF)) / O(REF) per network, the 13 non-REF
       cells; tie-aware ranks; fixed-plan order over the strict nesting pairs.
  AF1  100*(O(N3, c) - O(N0, c)) / O(N0, c) per matched cell.
O = the level's objective (GC + lambda * w_unserved * U).

Classification (Sept 23 finalization), against the Stage 1 BASE value of the
same quantity (same evaluator):
  sign: SIGN_ROBUST / SIGN_SENSITIVE over the implemented Class A levels
  (A1-A3, A5-A8); magnitude band per level; worst band per dimension.
  Movement from the CERTIFIED value is reported where a certified value of
  the same quantity exists. Class B (model disagreement) and additional
  levels are reported, never used for a label.
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

import exp7_classify as C  # noqa: E402

CLASS_A = ("A1", "A2", "A3", "A5", "A6", "A7", "A8")
STAGE2_ELIGIBLE = CLASS_A
F2_FLOOR_PCT = 0.287
SEEDS1 = (20260825, 20260826, 20260827)
SEEDS3 = (20260825, 20260826, 20260827, 20260828, 20260829)
BOOTSTRAP_REOPT_SUBSET = (1, 5, 10, 15, 20)
CELLS = ("REF", "R1_H60", "R1_H30", "R1_H20", "R2_S25", "R2_S10", "R2_S05",
         "R3_SPAN", "R4_C05", "R4_C01", "R4_C00", "R6_ADA", "B1", "B2")


def _o(rows, sid):
    r = rows.get(sid)
    return None if r is None or "error" in r else r["objective"]


def _u(rows, sid):
    r = rows.get(sid)
    return None if r is None or "error" in r else r["unserved_demand"]


def _mean(xs):
    xs = [x for x in xs]
    return None if not xs or any(x is None for x in xs) else sum(xs) / len(xs)


def finding_values(ev: dict, peak_unit: dict) -> dict:
    """ev: {variant: rows} for ONE level. Returns {quantity: value|None}."""
    n0, n3, n4, n0s = (ev.get(v, {}) for v in ("N0", "N3", "N4", "N0S"))
    q = {}
    ub = _u(n0, "F1_BASELINE")
    q["F1"] = _mean([None if ub in (None, 0) or _u(n0, f"F1_PLAN_{s}") is None
                     else 100 * (_u(n0, f"F1_PLAN_{s}") / ub - 1) for s in SEEDS1])
    uc = _mean([_u(n0, f"F2_CONTROL_{s}") for s in SEEDS1])
    ut = _mean([_u(n0s, f"F2_SPLICE_{s}") for s in SEEDS1])
    q["F2_unserved"] = None if uc in (None, 0) or ut is None else 100 * (ut / uc - 1)
    oc = _mean([_o(n0, f"F2_CONTROL_{s}") for s in SEEDS1])
    ot = _mean([_o(n0s, f"F2_SPLICE_{s}") for s in SEEDS1])
    q["F2_objective"] = None if oc in (None, 0) or ot is None else 100 * (ot / oc - 1)
    q["F3"] = _mean([None if _o(n0, f"F3_CONTROL_{s}") is None
                     or _o(n3, f"F3_ADDSTOP_{s}") is None else
                     100 * (_o(n3, f"F3_ADDSTOP_{s}") - _o(n0, f"F3_CONTROL_{s}"))
                     / _o(n0, f"F3_CONTROL_{s}") for s in SEEDS3])
    o4, o3, o0 = _o(n4, "F4_N4_EXP4N"), _o(n3, "F4_N3_EXP4A"), _o(n0, "F4_N0_J100")
    q["F4_43"] = None if None in (o4, o3) else 100 * (o4 - o3) / o3
    q["F4_40"] = None if None in (o4, o0) else 100 * (o4 - o0) / o0
    for net, rows, j100 in (("N0", n0, "F4_N0_J100"), ("N4", n4, "F5_N4_J100")):
        oj = {c: _o(rows, f"F5_{net}_{c}") for c in ("J090", "J110", "P090", "P110")}
        oj["J100"] = _o(rows, j100)
        u = peak_unit[net]
        ok = all(v is not None for v in oj.values())
        q[f"F5_{net}_peak_lower"] = (oj["J100"] - oj["P090"]) / u if ok else None
        q[f"F5_{net}_peak_upper"] = (oj["P110"] - oj["J100"]) / u if ok else None
        q[f"F5_{net}_joint_lower"] = (oj["J100"] - oj["J090"]) / 10 if ok else None
        q[f"F5_{net}_joint_upper"] = (oj["J110"] - oj["J100"]) / 10 if ok else None
        q[f"F5_{net}_monotone_joint"] = (oj["J090"] >= oj["J100"] >= oj["J110"]) if ok else None
        q[f"F5_{net}_monotone_peak"] = (oj["P090"] >= oj["J100"] >= oj["P110"]) if ok else None
    for net, rows in (("N0", n0), ("N3", n3)):
        ref = _o(rows, f"F6_{net}_REF")
        for c in CELLS[1:]:
            oc_ = _o(rows, f"F6_{net}_{c}")
            q[f"F6_{net}_{c}"] = None if None in (ref, oc_) else 100 * (oc_ - ref) / ref
    for c in CELLS:
        a, b = _o(n0, f"F6_N0_{c}"), _o(n3, f"F6_N3_{c}")
        q[f"AF1_{c}"] = None if None in (a, b) else 100 * (b - a) / a
    return q


SIGNED = ("F1", "F2_unserved", "F2_objective", "F3", "F4_43", "F4_40")


def classify_quantity(base: float | None, by_level: dict, dim_of: dict,
                      *, certified: float | None = None) -> dict:
    """Sign robustness over implemented Class A levels, magnitude bands per
    level, worst band per dimension, movement from the certified value."""
    ca = {lv: v for lv, v in by_level.items() if dim_of.get(lv) in CLASS_A}
    sign = C.sign_robustness(base, ca) if base is not None else None
    per_level, per_dim = {}, {}
    for lv, v in by_level.items():
        mb = C.magnitude_band(base, v)
        row = {"value": v, "band": mb["label"],
               "relative_change": mb["relative_change"],
               "absolute_change": mb["absolute_change"],
               "sign_event": (C.sign_flip(base, v) if None not in (base, v)
                              else None)}
        if certified is not None and v is not None and certified != 0:
            row["movement_from_certified_pct"] = 100 * (v - certified) / abs(certified)
        per_level[lv] = row
        d = dim_of.get(lv)
        if d:
            per_dim.setdefault(d, []).append(mb)
    worst = {d: C.worst_magnitude(bs) for d, bs in per_dim.items()}
    vals = [v for lv, v in ca.items() if v is not None]
    return {"base": base, "certified": certified, "sign": sign,
            "per_level": per_level, "worst_band_by_dimension": worst,
            "class_a_range": [min(vals), max(vals)] if vals else None,
            "range_includes_zero": (min(vals) <= 0 <= max(vals)) if vals else None}


def dimension_movement(base: float | None, by_level: dict, dim_of: dict) -> dict:
    """max |v - base| / |base| per Class A dimension (None if uninformative)."""
    out = {}
    for lv, v in by_level.items():
        d = dim_of.get(lv)
        if d not in STAGE2_ELIGIBLE or v is None or base is None:
            continue
        if abs(base) <= C.TAU_ABS:
            continue
        m = abs(v - base) / abs(base)
        out[d] = max(out.get(d, 0.0), m)
    return out


def select_stage2(mov_f1: dict, mov_f4: dict, *, k: int = 2) -> dict:
    """PREREGISTERED (before any Stage 1 result is seen):
    score(d) = max(movement_F1(d), movement_F4(d)), movement = the largest
    relative movement from the Stage 1 BASE value over the dimension's levels
    (F4 = the larger of F4_43 and F4_40). The k highest-scoring eligible
    Class A dimensions are selected; ties broken by dimension id order."""
    dims = sorted(set(mov_f1) | set(mov_f4), key=lambda d: CLASS_A.index(d))
    score = {d: max(mov_f1.get(d, 0.0), mov_f4.get(d, 0.0)) for d in dims}
    ranked = sorted(dims, key=lambda d: (-score[d], CLASS_A.index(d)))
    return {"metric": select_stage2.__doc__, "scores": score,
            "ranking": ranked, "selected": ranked[:k]}


def stage2_levels(selected: list[str], levels: list[dict]) -> list[str]:
    """Every level of the selected dimensions; A2 restricted to the
    preregistered BOOTSTRAP_REOPT_SUBSET (draws 1, 5, 10, 15, 20)."""
    out = []
    for p in levels:
        if p["dimension"] not in selected:
            continue
        if p["dimension"] == "A2":
            draw = int(p["name"].replace("A2_BOOT", ""))
            if draw not in BOOTSTRAP_REOPT_SUBSET:
                continue
        out.append(p["name"])
    return out


# ---------------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--partial", action="store_true")
    a = ap.parse_args()
    import exp45_certify_cell as CC
    import exp6_grid as G
    import exp7_stage1 as S
    reg = json.loads(S.REGISTRY.read_text())
    lv_doc = json.loads((ROOT / S.LEVELS_FILE).read_text())
    levels = lv_doc["levels"]
    dim_of = {p["name"]: p["dimension"] for p in levels}
    names = ["BASE"] + [p["name"] for p in levels]
    fails, missing, bad = [], [], []
    ev_all = {}
    for lvn in names:
        ev = {}
        for v in S.VARIANTS:
            p = S.cell_path(v, lvn)
            if not p.exists():
                missing.append(f"{v}/{lvn}")
                continue
            rec = json.loads(p.read_text())
            if rec["n_errors"] or not rec["internal_consistency_build_plan_equals_solve"]:
                bad.append(f"{v}/{lvn}")
            if rec["registry_sha256"] != S.sha(S.REGISTRY):
                bad.append(f"{v}/{lvn}: registry drift")
            ev[v] = rec["rows"]
        ev_all[lvn] = ev
    # peak unit: 10% of the pm_peak cap (Exp 5 arm C unit), per network
    caps = json.loads((ROOT / "outputs/exp5/cells/N0_J100.json").read_text())[
        "resource"]["requested"]["peak_proxy_caps"]
    pu = 0.10 * float(caps["pm_peak"])
    peak_unit = {"N0": pu, "N4": pu}
    vals = {lvn: finding_values(ev_all[lvn], peak_unit) for lvn in names
            if ev_all.get(lvn)}
    out = {"artifact": "EXP7_STAGE1_ANALYSIS", "written_utc": CC.utc(),
           "registry_sha256": S.sha(S.REGISTRY),
           "levels_sha256": S.sha(ROOT / S.LEVELS_FILE),
           "n_cells_expected": len(names) * len(S.VARIANTS),
           "n_cells_present": len(names) * len(S.VARIANTS) - len(missing),
           "missing": missing, "bad": bad, "peak_unit": peak_unit}
    # ---- BASE reproduction of certified objectives (same evaluator) -------
    rep = []
    base = ev_all.get("BASE", {})
    for s in reg["solutions"]:
        if s.get("plan") is None:
            continue
        want = s["certified"].get("objective")
        got = (base.get(s["variant"], {}).get(s["id"]) or {}).get("objective")
        if want is None or got is None:
            continue
        rep.append({"id": s["id"], "certified": float(want), "stage1_base": got,
                    "bit_exact": float(want) == got,
                    "rel_diff": (got - float(want)) / float(want)})
    out["base_reproduction"] = rep
    same_eval = [r for r in rep if r["id"].startswith(("F4_", "F5_", "F6_"))]
    if base and not all(r["bit_exact"] for r in same_eval):
        fails.append("BASE does not reproduce certified F4/F5/F6 objectives "
                     "bit-exactly (same evaluator): investigate before use")
    # ---- reach per level (N0 variant, every row) ------------------------------
    reach = {}
    b0 = base.get("N0", {})
    for lvn in names[1:]:
        rows = ev_all.get(lvn, {}).get("N0")
        if not rows:
            continue
        moved = any(abs((rows.get(k) or {}).get("objective", math.nan)
                        - (b0.get(k) or {}).get("objective", math.nan)) > 0
                    for k in b0)
        reach[lvn] = "REACHES" if moved else "EXP7_LEVEL_INERT"
    out["reach"] = reach
    inert = [k for k, v in reach.items() if v != "REACHES"]
    # ---- emptiness at network-transforming levels -------------------------
    emp = {}
    for p in levels:
        if not p.get("network"):
            continue
        f = S.OUT / "emptiness" / f"N3_R1_H20__{p['name']}.json"
        emp[p["name"]] = json.loads(f.read_text())["status"] if f.exists() else None
    out["n3_r1_h20_feasibility"] = {"BASE": "INFEASIBLE_UNDER_ENVELOPE", **emp}
    # ---- quantities and classifications ---------------------------------
    cert = {"F1": -6.651987701966629, "F2_unserved": 0.0065,
            "F3": -0.18656513176548822, "F4_43": 9.659}
    usable = {lvn: v for lvn, v in vals.items() if lvn not in inert}
    table = {}
    if "BASE" in vals:
        keys = [k for k in vals["BASE"] if not k.startswith("F5_") or
                not k.endswith(("monotone_joint", "monotone_peak"))]
        for k in keys:
            by = {lvn: v[k] for lvn, v in usable.items() if lvn != "BASE"}
            table[k] = classify_quantity(vals["BASE"][k], by, dim_of,
                                         certified=cert.get(k))
        for k in [k for k in vals["BASE"] if k.endswith(("monotone_joint",
                                                          "monotone_peak"))]:
            table[k] = {"base": vals["BASE"][k],
                        "per_level": {lvn: v[k] for lvn, v in usable.items()},
                        "changes": sorted(lvn for lvn, v in usable.items()
                                          if v[k] != vals["BASE"][k])}
        # F2 null test
        table["F2_null_holds"] = {lvn: (v["F2_unserved"] is not None and
                                        abs(v["F2_unserved"]) < F2_FLOOR_PCT)
                                  for lvn, v in usable.items()}
        # F6 ranks per level
        for net in ("N0", "N3"):
            table[f"F6_{net}_ranks"] = {
                lvn: C.rank({c: v.get(f"F6_{net}_{c}") for c in CELLS[1:]})
                for lvn, v in usable.items()}
    out["values"] = vals
    out["classification"] = table
    out["inert_levels"] = inert
    # ---- Stage 2 selection metric (computed; frozen by exp7_stage2_select) --
    if "BASE" in vals:
        by = lambda k: {lvn: v[k] for lvn, v in usable.items() if lvn != "BASE"}
        m1 = dimension_movement(vals["BASE"]["F1"], by("F1"), dim_of)
        m43 = dimension_movement(vals["BASE"]["F4_43"], by("F4_43"), dim_of)
        m40 = dimension_movement(vals["BASE"]["F4_40"], by("F4_40"), dim_of)
        m4 = {d: max(m43.get(d, 0.0), m40.get(d, 0.0)) for d in set(m43) | set(m40)}
        out["stage2_metric"] = {"movement_F1": m1, "movement_F4": m4,
                                **select_stage2(m1, m4)}
    complete = (not missing and not bad and not fails
                and all(v is not None for v in emp.values()))
    out["failures"] = fails
    out["status"] = ("EXP7_STAGE1_EVALUATION_COMPLETE" if complete
                     else "EXP7_STAGE1_INCOMPLETE")
    out["a4"] = "UNIMPLEMENTED: reliability robustness not tested"
    CC.atomic_write_json(S.OUT / "EXP7_STAGE1_ANALYSIS.json", out)
    print(out["status"], "missing", len(missing), "bad", bad[:5], fails)
    return 0 if complete or a.partial else 2


if __name__ == "__main__":
    raise SystemExit(main())
