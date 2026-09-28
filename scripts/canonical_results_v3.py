#!/usr/bin/env python3
"""Write outputs/CANONICAL_RESULTS_v3.json -- ADDITIVE over v2.

v3 = every v2 entry copied VERBATIM, except `exp5`, whose v2 entry ("BUILT AND
TESTED, NOT RUN -- EXP5_REFRAME_REQUIRED") is superseded by the reframed,
executed experiment and is preserved inside the new entry under
`v2_entry_superseded`. One new key, `exp4a`, records the Experiment 4
original-question addendum. v1 and v2 are not touched; v2's sha256 is recorded
as the predecessor.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
V2 = OUT / "CANONICAL_RESULTS_v2.json"
V3 = OUT / "CANONICAL_RESULTS_v3.json"
A = OUT / "exp4_addendum"
E5 = OUT / "exp5"


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def commit() -> str:
    return subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True,
                          capture_output=True).stdout.strip()


def exp4a_entry() -> dict:
    d = json.loads((A / "DELTA43.json").read_text())
    x = d["delta43"]
    return {
        "title": "Experiment 4 original question -- N3 (Exp 3 constrained "
                 "redesign) vs N4 (EXP4N normalized leader) under one contract",
        "status": "COMPLETE -- firewall-admitted comparison; N4 does NOT beat N3",
        "certified": True,
        "contract": d["contract"]["digest"],
        "canonical": ["EXPERIMENT4_ORIGINAL_QUESTION_ADDENDUM.md",
                      "outputs/exp4_addendum/DELTA43.json",
                      "outputs/exp4_addendum/N3.json",
                      "outputs/exp4_addendum/N4_canary.json",
                      "outputs/exp4_addendum/EXP4A_CONTRACT.json"],
        "evaluator": "same_route (Model B), EXP4N block certifier (8,3), "
                     "lambda 2.0, EXP4N common envelope 0b46d1abc9a80c80",
        "headline": (f"obj(N4) - obj(N3) = +{float(x['delta']):,.4f} "
                     f"(+{x['delta_pct_of_N3']:.3f}% of N3); N4 worse. N3 "
                     f"{float(x['objective_N3']):,.4f}, N4 "
                     f"{float(x['objective_N4']):,.4f}."),
        "equivalence_canary": "N4 re-certified through the addendum runner "
                              "equals EXP4N production_mr120 bit-exactly",
        "caveats": [
            "conditional on the frozen path model, which fits N4 markedly "
            "worse (8.7-34.8% of flow improvable vs 1.0-3.7%); "
            "omission-corrected Delta43 +7.87%, not certified",
            "same-route waiting model: N4 cross-route omission 12.47% of GC "
            "(potentially_frontier_changing) -- model-dependent",
            "fixed-plan lambda sign flip at 1.087; preregistered lambda 2",
            "D33-B band is veto-only and a local lower bound",
            "no global optimality, fleet, deployment or implementation claim",
        ],
        "gates_not_discharged": ["4-12 deferred to Exp 7",
                                 "4-13 UNRESOLVED", "fleet/deadhead UNRESOLVED",
                                 "physical inspection UNRESOLVED",
                                 "wider OD deferred to Exp 7"],
    }


def exp5_entry(v2_entry: dict) -> dict:
    an = json.loads((E5 / "EXP5_ANALYSIS.json").read_text())
    con = json.loads((E5 / "EXP5_CONTRACT.json").read_text())
    j = {(t["network"], t["cell"]): t for t in an["frontier"]}
    head = []
    for n in ("N4", "N0"):
        lo, mid, hi = (j.get((n, c)) for c in ("J075", "J100", "J150"))
        if lo and mid and hi:
            head.append(f"{n}: J075 {lo['objective']:,.1f} / J100 "
                        f"{mid['objective']:,.1f} / J150 {hi['objective']:,.1f}")
    return {
        "title": "Modeled operating-resource frontier -- revenue vehicle-hours "
                 "and the six-period solver peak-concurrency proxy",
        "status": an["status"],
        "certified": an["status"] == "EXP5_FRONTIER_CERTIFIED",
        "contract": con["contracts"]["EXP5_FRONTIER"]["digest"],
        "contract_file_sha256": con.get("contract_file_sha256"),
        "canonical": ["EXPERIMENT5_CLOSEOUT.md", "outputs/exp5/EXP5_CONTRACT.json",
                      "outputs/exp5/EXP5_ANALYSIS.json", "outputs/exp5/cells/",
                      "EXPERIMENT5_PREMISE_RETIREMENT.md"],
        "evaluator": "same_route (Model B), EXP4N block certifier (8,3), lambda 2",
        "headline": "; ".join(head),
        "axes": {"hours": "scheduled_weekday_revenue_vehicle_hours",
                 "peak": "solver_peak_concurrency_proxy -- NOT fleet"},
        "not_claimed": ["per-bus value", "fleet feasibility", "a knee",
                        "deployability"],
        "v2_entry_superseded": v2_entry,
    }


def main() -> int:
    v2 = json.loads(V2.read_text())
    exps = dict(v2["experiments"])
    old5 = exps["exp5"]
    exps["exp4a"] = exp4a_entry()
    exps["exp5"] = exp5_entry(old5)
    v3 = {"version": 3, "generated_by": "scripts/canonical_results_v3.py",
          "generated_commit": commit(),
          "predecessor": {"path": "outputs/CANONICAL_RESULTS_v2.json",
                          "sha256": sha256(V2),
                          "status": "unchanged; every entry except exp5 copied "
                                    "verbatim; v2's exp5 kept inside the new "
                                    "entry"},
          **{k: v for k, v in v2.items() if k not in (
              "version", "generated_by", "generated_commit", "predecessor",
              "experiments")},
          "experiments": exps}
    for k in v2["experiments"]:
        if k != "exp5":
            assert v3["experiments"][k] == v2["experiments"][k], k
    V3.write_text(json.dumps(v3, indent=2, ensure_ascii=False))
    print(f"wrote {V3.relative_to(ROOT)}; v2 sha {sha256(V2)[:16]} unchanged")
    for k, e in exps.items():
        print(f"  {k:6s} {str(e.get('status'))[:90]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
