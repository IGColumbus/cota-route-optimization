#!/usr/bin/env python3
"""Experiment 7 closeout: one finding table for F1-F6 (+AF1).

Reads:
  outputs/exp7/stage1/EXP7_STAGE1_ANALYSIS.json   (authoritative matrix)
  outputs/exp7/EXP7_STAGE2_SELECTION.json          (if Stage 2 ran)
  outputs/exp7/EXP7_ANALYSIS.json                  (Stage 2 closure analysis)
Writes outputs/exp7/EXP7_CLOSEOUT_TABLE.{json,md}.

Per finding row: certified base result; Stage 1 BASE (same evaluator); the
complete Stage 1 result over implemented Class A levels (sign label, worst
magnitude band per dimension, Class A range); the worst observed movement
(level, value); sign / ranking / monotonicity changes; the Stage 2 adaptive
result where applicable; the exact supporting cells. Labels are only those the
implemented matrix supports; A4 is UNIMPLEMENTED; A1 covers commute pairs only;
the Stage 2 bootstrap covers the five preregistered draws only.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import exp7_stage1_analyze as A  # noqa: E402

CLASS_A = A.CLASS_A


def _worst(cq: dict):
    """Largest |relative change| over Class A levels (the worst movement)."""
    best = None
    for lv, r in cq["per_level"].items():
        rc = r.get("relative_change")
        if rc is None:
            continue
        if best is None or rc > best[1]:
            best = (lv, rc, r["value"])
    return None if best is None else {"level": best[0], "relative_change": best[1],
                                      "value": best[2]}


def _events(cq: dict, dim_of: dict):
    return sorted((lv, r["sign_event"]) for lv, r in cq["per_level"].items()
                  if r.get("sign_event") and dim_of.get(lv) in CLASS_A)


def _other(cq: dict, dim_of: dict):
    return {lv: r["value"] for lv, r in cq["per_level"].items()
            if dim_of.get(lv) not in CLASS_A}


def row(name, key, an, dim_of, *, certified=None, note=""):
    cq = an["classification"].get(key)
    if cq is None:
        return {"finding": name, "quantity": key, "status": "not computed"}
    return {"finding": name, "quantity": key, "certified": certified,
            "stage1_base": cq["base"],
            "sign_label": (cq["sign"] or {}).get("label"),
            "sign_events_class_a": _events(cq, dim_of),
            "worst_magnitude_band_by_dimension": cq["worst_band_by_dimension"],
            "worst_movement": _worst(cq),
            "class_a_range": cq["class_a_range"],
            "range_includes_zero": cq["range_includes_zero"],
            "class_b_and_additional": _other(cq, dim_of),
            "supporting_cells": "outputs/exp7/stage1/evals/<variant>/<level>.json "
                                "for every level in per_level",
            "note": note}


def main() -> int:
    an = json.loads((ROOT / "outputs/exp7/stage1/EXP7_STAGE1_ANALYSIS.json").read_text())
    lv = json.loads((ROOT / "outputs/exp7/EXP7_LEVELS.json").read_text())["levels"]
    dim_of = {p["name"]: p["dimension"] for p in lv}
    rows = [
        row("F1", "F1", an, dim_of, certified=-6.651987701966629,
            note="unserved % vs the N0 current plan, mean of 3 Exp 1 plans; "
                 "Exp 1 certified under crowding + widened paths (different model "
                 "instance): Stage 1 BASE is the classification reference"),
        row("F2 (unserved)", "F2_unserved", an, dim_of, certified=0.0065,
            note="a certified NULL: read with the null test against the Exp 2B "
                 "floor (F2_null_holds), not as a signed effect"),
        row("F3", "F3", an, dim_of, certified=-0.18656513176548822),
        row("F4 (N4 - N3, Exp 4A)", "F4_43", an, dim_of, certified=9.659),
        row("F4 (N4 - N0 J100)", "F4_40", an, dim_of),
    ]
    for net in ("N0", "N4"):
        for arm in ("peak_lower", "peak_upper", "joint_lower", "joint_upper"):
            rows.append(row(f"F5 {net} {arm}", f"F5_{net}_{arm}", an, dim_of,
                            note="fixed Exp 5 plans; Exp 5's own "
                                 "EXP5_MONOTONICITY_FAILURE is preserved"))
    for net in ("N0", "N3"):
        for c in A.CELLS[1:]:
            rows.append(row(f"F6 {net} {c}", f"F6_{net}_{c}", an, dim_of))
    for c in A.CELLS:
        rows.append(row(f"AF1 {c}", f"AF1_{c}", an, dim_of))
    null = an["classification"].get("F2_null_holds", {})
    mono = {k: an["classification"][k].get("changes")
            for k in an["classification"] if k.endswith(("monotone_joint",
                                                          "monotone_peak"))}
    s2 = {}
    sel_p = ROOT / "outputs/exp7/EXP7_STAGE2_SELECTION.json"
    if sel_p.exists():
        s2["selection"] = json.loads(sel_p.read_text())
        s2_p = ROOT / "outputs/exp7/EXP7_ANALYSIS.json"
        s2["analysis_status"] = (json.loads(s2_p.read_text())["status"]
                                 if s2_p.exists() else "not run")
    out = {"artifact": "EXP7_CLOSEOUT_TABLE", "stage1_status": an["status"],
           "rows": rows, "F2_null_holds_by_level": null,
           "F2_null_breaks_at": sorted(k for k, v in null.items() if not v),
           "F5_monotonicity_changes": mono,
           "F6_ranks": {k: v for k, v in an["classification"].items()
                        if k.endswith("_ranks")},
           "n3_r1_h20_feasibility": an.get("n3_r1_h20_feasibility"),
           "inert_levels": an.get("inert_levels"),
           "stage2": s2,
           "not_covered": [
               "A4 reliability: UNIMPLEMENTED -- reliability robustness NOT tested",
               "A1: non-commute demand only on OD pairs with observed commuting",
               "A6: bundled walking friction (access and transfer caps together)",
               "A3: resource envelope held fixed as runtimes increase",
               "A8: cost_retention_full_min not varied",
               "Stage 2 bootstrap (if selected): draws 1, 5, 10, 15, 20 only",
               "Class B jobs-accessibility objective: untested",
               "Objective-ordering results do not transfer to served demand, GC, "
               "OFF count or accessibility"]}
    (ROOT / "outputs/exp7/EXP7_CLOSEOUT_TABLE.json").write_text(
        json.dumps(out, indent=1))
    md = ["# Experiment 7 closeout table", "",
          f"Stage 1: `{an['status']}`. Stage 2: "
          f"`{s2.get('analysis_status', 'not run')}`.", "",
          "| finding | certified | Stage 1 BASE | sign (Class A) | worst movement "
          "(level, rel.) | Class A range | worst band by dimension |",
          "|---|---|---|---|---|---|---|"]
    for r in rows:
        if r.get("status"):
            continue
        w = r["worst_movement"]
        rng = r["class_a_range"]
        md.append("| {} | {} | {} | {}{} | {} | {} | {} |".format(
            r["finding"], "—" if r["certified"] is None else f"{r['certified']:.4g}",
            "—" if r["stage1_base"] is None else f"{r['stage1_base']:.4g}",
            r["sign_label"],
            "" if not r["sign_events_class_a"] else
            " (" + ", ".join(f"{a}:{b}" for a, b in r["sign_events_class_a"][:4]) + ")",
            "—" if w is None else f"{w['level']}, {w['relative_change']:.1%}",
            "—" if rng is None else f"[{rng[0]:.4g}, {rng[1]:.4g}]",
            "; ".join(f"{d}: {b}" for d, b in sorted(
                r["worst_magnitude_band_by_dimension"].items()) if b)))
    md += ["", "F2 null breaks at: " + (", ".join(out["F2_null_breaks_at"]) or "none"),
           "", "Not covered: " + "; ".join(out["not_covered"])]
    (ROOT / "outputs/exp7/EXP7_CLOSEOUT_TABLE.md").write_text("\n".join(md) + "\n")
    print("\n".join(md[:12]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
