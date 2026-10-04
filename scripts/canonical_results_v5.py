#!/usr/bin/env python3
"""Write outputs/CANONICAL_RESULTS_v5.json -- ADDITIVE over v4.

v5 = every v4 top-level key and every v4 experiment entry copied VERBATIM,
plus:
  * `exp7`        -- new entry built only from the Exp 7 artifacts
                     (EXP7_CONTRACT.json, EXP7_STAGE2_SELECTION.json,
                     stage1/EXP7_STAGE1_ANALYSIS.json, EXP7_ANALYSIS.json,
                     EXP7_CLOSEOUT_TABLE.json) and EXPERIMENT7_CLOSEOUT.md;
  * `predecessor` -- v4's path and sha256.

Refuses if: any artifact is absent; v5 already exists (unless --force-rewrite
is given AND the existing v5 is byte-identical to what would be written);
the Stage 1 or Stage 2 status is not the contract's completion state; the
selection is not bound to the frozen contract; the closeout document is
missing.
"""
from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
V4 = OUT / "CANONICAL_RESULTS_v4.json"
V5 = OUT / "CANONICAL_RESULTS_v5.json"
E7 = OUT / "exp7"
CONTRACT = E7 / "EXP7_CONTRACT.json"
SELECTION = E7 / "EXP7_STAGE2_SELECTION.json"
STAGE1 = E7 / "stage1" / "EXP7_STAGE1_ANALYSIS.json"
ANALYSIS = E7 / "EXP7_ANALYSIS.json"
TABLE = E7 / "EXP7_CLOSEOUT_TABLE.json"
CLOSEOUT = ROOT / "EXPERIMENT7_CLOSEOUT.md"


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def load(p: Path) -> dict:
    if not p.exists():
        raise SystemExit(f"refusing: {p.relative_to(ROOT)} missing")
    return json.loads(p.read_text())


def commit() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                   text=True).strip()


def _row(table: dict, key: str) -> dict:
    for r in table["rows"]:
        if r.get("quantity") == key:
            return {k: r.get(k) for k in (
                "certified", "stage1_base", "sign_label", "sign_events_class_a",
                "worst_movement", "class_a_range", "worst_magnitude_band_by_dimension",
                "cross_network_a7_mismatch")}
    raise SystemExit(f"refusing: closeout table has no row {key}")


def exp7_entry() -> dict:
    con, sel, s1, an, tab = (load(p) for p in (CONTRACT, SELECTION, STAGE1,
                                               ANALYSIS, TABLE))
    if not CLOSEOUT.exists():
        raise SystemExit("refusing: EXPERIMENT7_CLOSEOUT.md missing")
    con16 = sha(CONTRACT)[:16]
    if sel.get("exp7_contract_sha256_16") != con16:
        raise SystemExit("refusing: Stage 2 selection not bound to this contract")
    if s1["status"] != "EXP7_STAGE1_EVALUATION_COMPLETE":
        raise SystemExit(f"refusing: Stage 1 status {s1['status']}")
    if an["status"] != "EXP7_STAGE2_REOPT_COMPLETE" or an["failures"]:
        raise SystemExit(f"refusing: Stage 2 status {an['status']}")
    s2 = tab["stage2"]["results"]
    return {
        "title": "Robustness of findings F1-F6 (and AF1) to model assumptions: "
                 "Stage 1 fixed-plan evaluation of every certified plan at every "
                 "implemented level; Stage 2 adaptive re-optimization in the two "
                 "preregistered-selected dimensions",
        "status": "STAGE1 EXP7_STAGE1_EVALUATION_COMPLETE; STAGE2 "
                  "EXP7_STAGE2_REOPT_COMPLETE",
        "certified": True,
        "contract": {"file": str(CONTRACT.relative_to(ROOT)), "sha256_16": con16,
                     "version": con["version"], "design": con["design"],
                     "gates": con["gates"],
                     "src_cota_opt_content_digest":
                         con["code"]["src_cota_opt_content_digest"]},
        "evaluator": "same_route (Model B), EXP4N block certifier (8,3), max 120 "
                     "rounds, EXP4N common envelope 0b46d1abc9a80c80, lambda 2 at BASE",
        "stage2_selection": {"selected_levels": sel["included_levels"],
                             "movement_F1": sel["movement_F1"],
                             "movement_F4": sel["movement_F4"]},
        "stage1": {"cells": f"{s1['n_cells_present']}/{s1['n_cells_expected']}",
                   "failures": s1["failures"],
                   "n3_r1_h20_feasibility": s1["n3_r1_h20_feasibility"],
                   "a4": s1["a4"],
                   "findings": {k: _row(tab, k) for k in
                                ("F1", "F2_unserved", "F3", "F4_43", "F4_40")},
                   "F2_null_breaks_at": tab["F2_null_breaks_at"],
                   "F2_not_applicable_at": tab["F2_not_applicable_at"],
                   "a7_cross_network_mismatch_levels":
                       tab["a7_cross_network_mismatch_levels"],
                   "F5_monotonicity_changes": tab["F5_monotonicity_changes"]},
        "stage2": {"closure": an["closure"], "sentinels": an["sentinels"],
                   "record_checks": an["record_checks"],
                   "monotonicity": {k: an["monotonicity"][k]
                                    for k in ("n_pairs", "n_violations")},
                   "F1_adaptive": an["f1_adaptive"],
                   "F4": an["f4"],
                   "AF1": s2["AF1"],
                   "F6_rank_and_sign_changes": s2["F6"],
                   "labels": {k: (s2[k].get("sign") or {}).get("label")
                              for k in ("F1", "F4_43", "F4_40")}},
        "regime_boundary": (
            "Objective = GC + lambda*60*unserved with no operating-cost term. At "
            "A5_LAM1 re-optimization collapses service (N0 REF 557 of 2,516 "
            "revenue vehicle-hours, 1,583 served); F1/F4/F5/F6 sign changes at "
            "lambda=1 are this collapse, not reversals inside the certified "
            "lambda>=2 regime. At A5_TP200 and both A6 levels the re-optimized "
            "plan keeps full hours but serves fewer, cheaper trips."),
        "post_freeze_code_changes": [
            "scripts/exp7_analyze.py: completion label + F1 adaptive (reporting only)",
            "scripts/exp7_run.py: closure exclusive lock (no numeric effect)",
            "scripts/exp7_closeout.py: Stage 2 section (reporting only)"],
        "not_claimed": tab["not_covered"] + [
            "lambda=1 results as evidence against F1/F4 inside lambda>=2",
            "served-trip or GC figures as findings (basin-dependent)",
            "fleet, buses or deployability", "per-route headways",
            "global optimality of any closed cell"],
        "closeout": "EXPERIMENT7_CLOSEOUT.md",
        "closeout_sha256": sha(CLOSEOUT),
        "canonical": [str(p.relative_to(ROOT)) for p in
                      (CONTRACT, SELECTION, STAGE1, ANALYSIS, TABLE)],
        "artifact_sha256": {str(p.relative_to(ROOT)): sha(p) for p in
                            (CONTRACT, SELECTION, STAGE1, ANALYSIS, TABLE)},
    }


def main() -> int:
    v4 = load(V4)
    v5 = copy.deepcopy(v4)
    v5["version"] = 5
    v5["generated_by"] = "scripts/canonical_results_v5.py"
    v5["generated_commit"] = commit()
    v5["predecessor"] = {"path": str(V4.relative_to(ROOT)), "sha256": sha(V4),
                         "status": "unchanged; every v4 entry copied verbatim; "
                                   "exp7 added"}
    v5["experiments"]["exp7"] = exp7_entry()
    text = json.dumps(v5, indent=1, ensure_ascii=False) + "\n"
    if V5.exists():
        raise SystemExit("refusing: CANONICAL_RESULTS_v5.json exists (never "
                         "overwrite a registry version; write v6)")
    V5.write_text(text)
    for k in v4["experiments"]:
        assert v5["experiments"][k] == v4["experiments"][k], k
    print("wrote", V5.relative_to(ROOT), sha(V5)[:16])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
