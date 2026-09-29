#!/usr/bin/env python3
"""Freeze the Experiment 7 Stage 2 selection from COMPLETE Stage 1 results.

Refuses unless EXP7_STAGE1_ANALYSIS.json has status
EXP7_STAGE1_EVALUATION_COMPLETE. Writes outputs/exp7/EXP7_STAGE2_SELECTION.json
(refuses to overwrite): the preregistered metric (exp7_stage1_analyze.
select_stage2), its per-dimension values for F1 and F4, the two selected
dimensions, every included level (A2 restricted to BOOTSTRAP_REOPT_SUBSET),
network/finding applicability, the source commit, and the Exp 7 contract
digest. Commit it before any Stage 2 optimization.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import exp7_stage1_analyze as A  # noqa: E402

OUT = ROOT / "outputs" / "exp7" / "EXP7_STAGE2_SELECTION.json"


def main() -> int:
    an = json.loads((ROOT / "outputs/exp7/stage1/EXP7_STAGE1_ANALYSIS.json").read_text())
    if an["status"] != "EXP7_STAGE1_EVALUATION_COMPLETE":
        raise SystemExit(f"Stage 1 not complete: {an['status']}")
    if OUT.exists():
        raise SystemExit(f"{OUT} already frozen; no substitution after the fact")
    con_p = ROOT / "outputs/exp7/EXP7_CONTRACT.json"
    con = json.loads(con_p.read_text())
    levels = json.loads((ROOT / "outputs/exp7/EXP7_LEVELS.json").read_text())["levels"]
    m = an["stage2_metric"]
    sel = m["selected"]
    incl = A.stage2_levels(sel, [p for p in levels
                                 if p["name"] not in an["inert_levels"]])
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                     text=True).strip()
    doc = {
        "artifact": "EXP7_STAGE2_SELECTION",
        "metric": m["metric"], "movement_F1": m["movement_F1"],
        "movement_F4": m["movement_F4"], "scores": m["scores"],
        "ranking": m["ranking"], "selected_dimensions": sel,
        "included_levels": incl,
        "bootstrap_reopt_subset": (list(A.BOOTSTRAP_REOPT_SUBSET)
                                   if "A2" in sel else None),
        "bootstrap_note": ("Complete bootstrap robustness comes from Stage 1 "
                           "(all 20 draws); Stage 2 tests adaptive "
                           "re-optimization on the preregistered subset only."
                           if "A2" in sel else None),
        "applicability": {
            "F4 track (REF only, X-stage within dimension, no W)": ["N0", "N3", "N4"],
            "F6 track (14 policy cells, W + X within dimension)": ["N0", "N3"],
            "findings": {"F4": "F4 track", "F6": "F6 track", "AF1": "F6 track",
                         "F1": "F6-track N0 REF (adaptive plan) vs the N0 "
                               "current plan evaluated at the same level",
                         "F2": "not re-optimized (Stage 1 only)",
                         "F3": "not re-optimized (Stage 1 only)",
                         "F5": "not re-optimized (Stage 1 only)"},
            "A7": "topology-changing: own initial solves only; no plan "
                  "sharing with BASE or other A7 levels"},
        "stage1_analysis_sha256": hashlib.sha256(
            (ROOT / "outputs/exp7/stage1/EXP7_STAGE1_ANALYSIS.json").read_bytes()
        ).hexdigest(),
        "source_commit": commit,
        "exp7_contract_sha256_16": hashlib.sha256(con_p.read_bytes()).hexdigest()[:16],
        "exp7_contract_frozen": bool(con.get("frozen"))}
    OUT.write_text(json.dumps(doc, indent=1, sort_keys=True))
    print(json.dumps({k: doc[k] for k in ("selected_dimensions", "included_levels",
                                          "scores")}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
