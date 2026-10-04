#!/usr/bin/env python3
"""Experiment 7 POST HOC addendum: F1 adaptive under Experiment 1's own
service rules.

NOT PREREGISTERED. Amendment §14.2 defines F1 adaptive as the F6-track N0 REF
plan against the N0 current plan at the same level (EXP7_ANALYSIS.f1_adaptive).
REF may switch route-periods OFF. Experiment 1's certified plans could not:
config/constraints.yaml sets preserve_span: true and policy_max_headway_min:
60. The Exp 6 policy cell R1_H60 (60-minute max-headway floor; implies no OFF,
identical to R2 at s = 0) is the closest certified Stage 2 cell to those rules.

This script reads only certified Stage 2 closure records and Stage 1 current-
plan evaluations, and writes outputs/exp7/EXP7_F1_DECISION_SPACE.json. It
re-solves nothing. Descriptive; no firewall comparison is involved (neither is
there one for the preregistered F1 adaptive).
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
E7 = ROOT / "outputs/exp7"
CELLS = ("REF", "R1_H60", "R1_H30", "R3_SPAN")


def main() -> int:
    an = json.loads((E7 / "EXP7_ANALYSIS.json").read_text())
    if an["status"] != "EXP7_STAGE2_REOPT_COMPLETE":
        raise SystemExit("refusing: Stage 2 not complete")
    st = json.loads((E7 / "closure/F6/closure_state_N0.json").read_text())
    s4 = json.loads((E7 / "closure/F4/closure_state_N0.json").read_text())
    if st["status"] != "FIXED_POINT" or s4["status"] != "FIXED_POINT":
        raise SystemExit("refusing: N0 closure not at fixed point")
    levels = [r["level"] for r in an["f1_adaptive"]]
    rows = []
    for lv in levels:
        ev = json.loads((E7 / f"stage1/evals/N0/{lv}.json").read_text())
        cur = ev["rows"]["F1_BASELINE"]["unserved_demand"]
        row = {"level": lv, "current_plan_unserved": cur, "cells": {}}
        for c in CELLS:
            ref = st["best"][f"{lv}|{c}"]["ref"]
            r = json.loads((ROOT / ref).read_text())
            o, f = r["outcome"], r["outcome"]["fitness_EXACT"]
            u = float(f["unserved_demand"])
            row["cells"][c] = {
                "record": ref,
                "f1_pct": 100 * (u / cur - 1),
                "unserved": u, "served": float(f["served_demand"]),
                "generalized_cost": float(f["generalized_cost"]),
                "revenue_veh_hours": float(f["revenue_veh_hours"]),
                "n_off": o["n_off"], "plan": o["plan_digest"]}
        # The same cell (N0, REF, this level) closed independently on the F4
        # track: a second fixed point of the same mathematical problem.
        r4 = json.loads((ROOT / s4["best"][f"{lv}|REF"]["ref"]).read_text())
        u4 = float(r4["outcome"]["fitness_EXACT"]["unserved_demand"])
        row["ref_f4_track"] = {
            "record": s4["best"][f"{lv}|REF"]["ref"],
            "objective": float(r4["outcome"]["objective_EXACT"]),
            "f6_track_objective": float(json.loads((ROOT / row["cells"]["REF"]["record"])
                                                   .read_text())["outcome"]["objective_EXACT"]),
            "f1_pct": 100 * (u4 / cur - 1), "n_off": r4["outcome"]["n_off"],
            "served": float(r4["outcome"]["fitness_EXACT"]["served_demand"])}
        rows.append(row)
    out = {"artifact": "EXP7_F1_DECISION_SPACE",
           "preregistered": False,
           "purpose": "F1 adaptive with the decision space matched to "
                      "Experiment 1's service rules (no route-period switched "
                      "OFF, 60-minute maximum headway), against the "
                      "preregistered REF version",
           "closest_cell_to_exp1_rules": "R1_H60",
           "inputs_sha256": {
               p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest()[:16]
               for p in ("outputs/exp7/EXP7_ANALYSIS.json",
                         "outputs/exp7/closure/F6/closure_state_N0.json",
                         "outputs/exp7/closure/F4/closure_state_N0.json")},
           "rows": rows}
    p = E7 / "EXP7_F1_DECISION_SPACE.json"
    p.write_text(json.dumps(out, indent=1) + "\n")
    for r in rows:
        print(r["level"], "  ".join(f"{c} {r['cells'][c]['f1_pct']:+.2f}% "
                                    f"(OFF {r['cells'][c]['n_off']})" for c in CELLS))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
