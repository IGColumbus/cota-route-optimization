"""One-off release restructure (P1-17/P1-18), recorded for provenance.

Moves files with ``git mv`` (never deletes), keeps every file name, and writes
``docs/research-record/MOVES.md`` and ``MOVES.json`` mapping old path → new path.
Run once from a clean tree; refuses to run if MOVES.json already exists.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RR = "docs/research-record"

EXPERIMENTS = {
    "experiments": ["ACCEPTANCE.md"],
    "experiments/exp2": ["EXPERIMENT2_CLOSEOUT.md", "docs/EXPERIMENT2_CLOSEOUT_ERRATA.md"],
    "experiments/exp3": ["EXPERIMENT3_CONTRACT.md", "EXPERIMENT3_CLOSURE.md",
                         "EXPERIMENT3_STAGE_B_PREREGISTRATION.md"],
    "experiments/exp4": ["EXPERIMENT4_CONTRACT.md", "EXPERIMENT4_NORMALIZED_CLOSEOUT.md",
                         "EXPERIMENT4_ORIGINAL_QUESTION_ADDENDUM.md"],
    "experiments/exp5": ["EXPERIMENT5_CLOSEOUT.md"],
    "experiments/exp6": ["EXPERIMENT6_PROTOCOL.md", "EXPERIMENT6_AMENDMENT_1.md",
                         "EXPERIMENT6_AMENDMENT_2.md", "EXPERIMENT6_D39_AMENDMENT.md",
                         "EXPERIMENT6_CONSTRAINT_CATALOG.md", "EXPERIMENT6_CLOSEOUT.md"],
    "experiments/exp7": ["docs/EXPERIMENT7_AMENDMENT.md", "docs/EXPERIMENT7_PROTOCOL.md",
                         "docs/EXPERIMENT7_PROTOCOL_AS_ISSUED.md",
                         "docs/EXPERIMENT7_SEPT23_FINALIZATION.md", "EXPERIMENT7_CLOSEOUT.md",
                         "docs/EXPERIMENT7_CLOSEOUT_ERRATA.md", "docs/EXPERIMENT7_RESULTS.md",
                         "docs/EXPERIMENT7_F1_ADDENDUM.md"],
}
RESEARCH_RECORD = {
    f"{RR}/exp3": ["EXPERIMENT3_A1.md", "EXPERIMENT3_CLOSEOUT.md", "EXPERIMENT3_D33_STAGEB_DESIGN.md",
                   "EXPERIMENT3_PHASE5B_ABANDONED.md", "EXPERIMENT3_PHASE5B_DESIGN.md",
                   "EXPERIMENT3_PHASE5_DESIGN.md", "EXPERIMENT3_PREFLIGHT.md",
                   "EXPERIMENT3_ROBUSTNESS.md", "HISTORY_NOTE.md", "GEN1_FREEZE.md"],
    f"{RR}/exp4": ["EXPERIMENT4_AUDIT_BEAT.md", "EXPERIMENT4_AUDIT_CLOSEOUT.md",
                   "EXPERIMENT4_AUDIT_DESIGN.md", "EXPERIMENT4_AUDIT_INCUMBENT_BEATEN.md",
                   "EXPERIMENT4_BLOCKERS.md", "EXPERIMENT4_BLOCKING_CONTRACT.md",
                   "EXPERIMENT4_C9_RECALL.md", "EXPERIMENT4_CLOSEOUT.md", "EXPERIMENT4_D18_COST.md",
                   "EXPERIMENT4_D18_RESULT.md", "EXPERIMENT4_DEMAND_ROBUSTNESS.md",
                   "EXPERIMENT4_DESIGN.md", "EXPERIMENT4_ENVELOPE_PROVENANCE.md",
                   "EXPERIMENT4_GATE47.md", "EXPERIMENT4_KEEPER_BEAT.md", "EXPERIMENT4_MASTERPATH.md",
                   "EXPERIMENT4_SCORING_INTERFACE.md", "EXP4N_KEEPER_BEAT.md",
                   "docs/EXP4N_CONTAINER_LOSS_INCIDENT.md", "docs/EXP4N_RELAUNCH_AUTHORIZATION.md",
                   "docs/EXP4N_ROUND_CAP_FINDING.md", "docs/EXP4_RESOURCE_NORMALIZATION_AUDIT.md",
                   "docs/ENVELOPE_DIGEST_INSUFFICIENCY.md", "FLEET_AND_BLOCKING.md"],
    f"{RR}/exp5": ["EXPERIMENT5_OFFON_DIAGNOSTIC.md", "EXPERIMENT5_PREMISE_AUDIT.md",
                   "EXPERIMENT5_PREMISE_RETIREMENT.md"],
    f"{RR}/exp6": ["EXPERIMENT6_D39_PREFLIGHT.md", "docs/EXP6_PARALLEL_CLOSEOUT_PREP.md",
                   "docs/N3_VS_N0_CROSSEXP_NOTE.md"],
    f"{RR}/exp7": ["docs/EXPERIMENT7_AMENDMENT_DRAFT.md", "docs/EXPERIMENT7_READINESS.md",
                   "docs/EXPERIMENTS_5_7_PROTOCOL_INTAKE.md"],
    RR: ["DISCOVERIES.md", "STATE_OF_PLAY.md", "docs/RELEASE_GUIDELINES_INTAKE.md"],
}
PROCESS = {
    "docs/process": ["OPERATIONS.md", "PUSH_TO_GITHUB.md", "HANDOFF.md",
                     "docs/RELEASE_AND_REPORTING_GUIDELINES.md"],
    "docs": ["METHODOLOGY.md", "ARCHITECTURE_FIREWALL.md"],
}


def git(*a: str) -> str:
    return subprocess.run(("git",) + a, cwd=ROOT, check=True, capture_output=True, text=True).stdout


def plan() -> dict[str, str]:
    moves: dict[str, str] = {}
    for table in (EXPERIMENTS, RESEARCH_RECORD, PROCESS):
        for dest, files in table.items():
            for f in files:
                moves[f] = f"{dest}/{Path(f).name}"
    moves["AGENTS.md"] = "docs/ENGINEERING_RULES.md"
    tracked = git("ls-files").splitlines()
    for f in tracked:
        if f.startswith("decisions/"):
            moves[f] = f"{RR}/{f}"
        elif f.startswith("outputs/") and f.endswith(".log"):
            moves[f] = f"{RR}/run-logs/{f[len('outputs/'):]}"
        elif f.startswith("outputs/figures/"):
            moves[f] = f"outputs/superseded/{f[len('outputs/'):]}"
    for f in ["outputs/certify_frontier.csv", "outputs/exp2_ladder.csv",
              "outputs/exp4/run/discovery_vs_certified.json",
              "outputs/exp6/SUPERSEDED.EXP6_ANALYSIS.first_run_receipt_start_encoding.json",
              "outputs/exp6/d35/SUPERSEDED.N0.first_run.json",
              "outputs/exp6/d35/SUPERSEDED.N3.first_run_test_plan_bug.json",
              "outputs/fixpoint_frontier.csv", "outputs/seedcheck.json",
              "outputs/exp2b_certification.superseded.json"]:
        if f in tracked:
            moves[f] = f"outputs/superseded/{f[len('outputs/'):]}"
    missing = [f for f in moves if f not in tracked]
    if missing:
        sys.exit(f"not tracked: {missing}")
    return moves


def main() -> int:
    mj = ROOT / RR / "MOVES.json"
    if mj.exists():
        sys.exit("MOVES.json exists; the restructure already ran")
    moves = plan()
    for old, new in moves.items():
        (ROOT / new).parent.mkdir(parents=True, exist_ok=True)
        git("mv", old, new)
    head = git("rev-parse", "HEAD").strip()
    mj.write_text(json.dumps({"base_commit": head, "research_final": "cd03af9c",
                              "moves": moves}, indent=1) + "\n")
    lines = ["# Moves", "",
             f"*Release restructure, 2026-10-05, applied on top of `{head[:8]}`. Every file was",
             "moved with `git mv`; none was deleted. File names are unchanged; only directories",
             "changed. A reader holding a `research-final` (`cd03af9c`) path finds the file",
             "here. Machine-readable copy: `MOVES.json`. Frozen documents and artifacts keep",
             "their historical paths in their text; resolve them through this table.*", "",
             "| old path | new path |", "|---|---|"]
    lines += [f"| `{o}` | `{n}` |" for o, n in sorted(moves.items())]
    (ROOT / RR / "MOVES.md").write_text("\n".join(lines) + "\n")
    print(f"{len(moves)} files moved")
    return 0


if __name__ == "__main__":
    sys.exit(main())
