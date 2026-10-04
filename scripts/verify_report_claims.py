#!/usr/bin/env python3
"""Check headline numbers typed into the report documents against the
canonical artifacts they cite.

Each claim: the value as written (rounded), the artifact, a small extractor,
and the documents that state it. A claim passes when the artifact value rounds
to the written value at the written precision, and every listed document
contains the written string. This does NOT make the documents generated (the
release rule); it catches transcription drift until they are.

    python scripts/verify_report_claims.py        # exit 0 iff all pass
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = "docs/report/TECHNICAL_REPORT.md"
CLOSE7 = "EXPERIMENT7_CLOSEOUT.md"
ADD7 = "docs/EXPERIMENT7_F1_ADDENDUM.md"


def J(p):
    return json.loads((ROOT / p).read_text())


def exp1():
    return J("outputs/canonical/exp1_final.json")


def f1a(level):
    return next(r["f1_pct"] for r in J("outputs/exp7/EXP7_ANALYSIS.json")["f1_adaptive"]
                if r["level"] == level)


def f4(level, x):
    return next(r["delta_pct"] for r in J("outputs/exp7/EXP7_ANALYSIS.json")["f4"]
                if r["level"] == level and r["control"] == x and r["treatment"] == "N4")


def r1h60(level):
    return next(r["cells"]["R1_H60"]["f1_pct"] for r in
                J("outputs/exp7/EXP7_F1_DECISION_SPACE.json")["rows"]
                if r["level"] == level)


def e6(net, cell):
    return next(r["policy_cost_closed_pct"] for r in J("outputs/exp6/EXP6_ANALYSIS.json")["frontier"]
                if r["network"] == net and r["cell"] == cell)


def row7(q):
    return next(r for r in J("outputs/exp7/EXP7_CLOSEOUT_TABLE.json")["rows"]
                if r.get("quantity") == q)


def d43():
    return J("outputs/CANONICAL_RESULTS_v5.json")["experiments"]["exp4a"]["headline"]


# (written string, decimals, extractor, documents)
CLAIMS = [
    ("−6.65%", 2, lambda: exp1()["headline"]["unserved_demand"]["mean_pct"], [REPORT]),
    ("±0.06", 2, lambda: exp1()["headline"]["unserved_demand"]["sd_pct"], [REPORT]),
    ("+3.30%", 2, lambda: exp1()["headline"]["trips_served"]["mean_pct"], [REPORT]),
    ("+0.88%", 2, lambda: exp1()["headline"]["generalized_cost"]["mean_pct"], [REPORT]),
    ("−2.34%", 2, lambda: exp1()["headline"]["cost_per_trip_served"]["mean_pct"], [REPORT]),
    ("19.1%", 1, lambda: exp1()["plan_disagreement"]["mean_share_changed_pct"], [REPORT]),
    ("19.7%", 1, lambda: exp1()["plan_disagreement"]["worst_share_changed_pct"], [REPORT]),
    ("10,262", 0, lambda: J("outputs/exp1_baseline_modelB.json")["baseline_unserved"], [REPORT]),
    ("9,583", 0, lambda: next(r["unserved"] for r in exp1()["frontier"] if r["lambda"] == 2.0), [REPORT]),
    ("−1.42%", 2, lambda: next(r["unserved_change_pct"] for r in exp1()["frontier"] if r["lambda"] == 1.0), [REPORT]),
    ("+9.66%", 2, lambda: float(__import__("re").search(r"\(\+([0-9.]+)% of N3\)", d43()).group(1)), [REPORT]),
    ("−5.43%", 2, lambda: f1a("BASE"), [CLOSE7, ADD7]),
    ("+181.72%", 2, lambda: f1a("A5_LAM1"), [CLOSE7, ADD7]),
    ("+45.11%", 2, lambda: f1a("A5_TP200"), [CLOSE7, ADD7]),
    ("+16.57%", 2, lambda: f1a("A6_WALKSPD85"), [CLOSE7, ADD7]),
    ("+4.58%", 2, lambda: f1a("A6_MAXWALK75"), [CLOSE7, ADD7]),
    ("+8.55%", 2, lambda: f4("BASE", "N3"), [CLOSE7]),
    ("+30.79%", 2, lambda: f4("A5_LAM4", "N3"), [CLOSE7]),
    ("−0.98%", 2, lambda: f4("A5_LAM1", "N3"), [CLOSE7, REPORT]),
    ("−6.57%", 2, lambda: r1h60("BASE"), [ADD7]),
    ("+0.12%", 2, lambda: r1h60("A5_LAM1"), [ADD7, REPORT]),
    ("−7.00%", 2, lambda: r1h60("A5_TP050"), [ADD7]),
    ("−2.14%", 2, lambda: r1h60("A6_MAXWALK75"), [ADD7]),
    ("+0.482%", 3, lambda: e6("N0", "R1_H60"), [REPORT]),
    ("+0.912%", 3, lambda: e6("N0", "R1_H20"), [REPORT]),
    ("+0.212%", 3, lambda: e6("N0", "R2_S05"), [REPORT]),
    ("+0.634%", 3, lambda: e6("N3", "R1_H30"), [REPORT]),
    ("−6.024", 3, lambda: row7("F1")["stage1_base"], [CLOSE7]),
    ("−1.897", 3, lambda: row7("F1")["class_a_range"][1], [CLOSE7]),
    ("−6.998", 3, lambda: row7("F1")["class_a_range"][0], [CLOSE7]),
]


def norm(s: str) -> float:
    return float(s.replace("−", "-").replace("±", "").replace("%", "")
                 .replace(",", "").replace("+", ""))


def main() -> int:
    bad = 0
    for text, dec, get, docs in CLAIMS:
        try:
            v = get()
        except Exception as e:  # noqa: BLE001
            print(f"FAIL {text}: extractor error {e!r}")
            bad += 1
            continue
        ok_val = round(v, dec) == round(norm(text), dec)
        missing = [d for d in docs if text not in (ROOT / d).read_text()]
        status = "ok  " if ok_val and not missing else "FAIL"
        bad += status == "FAIL"
        print(f"{status} {text:>10}  artifact={v:.6g}"
              + (f"  missing in {missing}" if missing else "")
              + ("" if ok_val else "  VALUE MISMATCH"))
    print(f"{len(CLAIMS) - bad}/{len(CLAIMS)} claims verified")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
