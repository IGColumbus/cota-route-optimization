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
RES7 = "docs/EXPERIMENT7_RESULTS.md"
ERR7 = "docs/EXPERIMENT7_CLOSEOUT_ERRATA.md"
README = "README.md"


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


def dspace(level):
    return next(r for r in J("outputs/exp7/EXP7_F1_DECISION_SPACE.json")["rows"]
                if r["level"] == level)


def ref_gap_pct():
    t = dspace("BASE")["ref_f4_track"]
    return (t["f6_track_objective"] - t["objective"]) / t["f6_track_objective"] * 100


def d43():
    return J("outputs/CANONICAL_RESULTS_v5.json")["experiments"]["exp4a"]["headline"]


def c2b():
    return J("outputs/exp2b_certification.json")["_confirmation"]


def obj_change_lam2():
    """Exp 1 objective change, lambda = 2 frontier run vs current plan (%)."""
    b = J("outputs/exp1_baseline_modelB.json")
    f = next(r for r in exp1()["frontier"] if r["lambda"] == 2.0)
    base = b["baseline_gc"] + 120 * b["baseline_unserved"]
    return 100 * ((f["gc"] + 120 * f["unserved"]) - base) / base


def s1_gains() -> dict:
    """Stage 1 served-trip gain per level: mean over the three seed plans."""
    import glob
    out = {}
    for f in sorted(glob.glob(str(ROOT / "outputs/exp7/stage1/evals/N0/*.json"))):
        d = json.loads(Path(f).read_text())
        rows = d["rows"]
        b = rows["F1_BASELINE"]["served_demand"]
        g = [rows[k]["served_demand"] - b for k in rows if k.startswith("F1_PLAN_")]
        out[d["level"]["name"]] = sum(g) / len(g)
    return out


def class_a(fixed_total: bool = False) -> list[float]:
    g = s1_gains()
    keep = ("A2", "A3", "A5", "A6", "A7", "A8") if fixed_total else ("A1", "A2", "A3", "A5", "A6", "A7", "A8")
    return [v for k, v in g.items() if k.split("_")[0] in keep]


def exp1_trip_gain() -> float:
    b = J("outputs/exp1_baseline_modelB.json")["baseline_served"]
    return b * exp1()["headline"]["trips_served"]["mean_pct"] / 100



# (written string, decimals, extractor, documents)
CLAIMS = [
    ("−6.65%", 2, lambda: exp1()["headline"]["unserved_demand"]["mean_pct"], [REPORT]),
    ("SD 0.06", 2, lambda: exp1()["headline"]["unserved_demand"]["sd_pct"], [REPORT]),
    ("+3.30%", 2, lambda: exp1()["headline"]["trips_served"]["mean_pct"], [REPORT]),
    ("+0.88%", 2, lambda: exp1()["headline"]["generalized_cost"]["mean_pct"], [REPORT]),
    ("−2.34%", 2, lambda: exp1()["headline"]["cost_per_trip_served"]["mean_pct"], [REPORT]),
    ("19.1%", 1, lambda: exp1()["plan_disagreement"]["mean_share_changed_pct"], [REPORT]),
    ("19.7%", 1, lambda: exp1()["plan_disagreement"]["worst_share_changed_pct"], [REPORT]),
    ("10,262", 0, lambda: J("outputs/exp1_baseline_modelB.json")["baseline_unserved"], [REPORT]),
    ("9,583", 0, lambda: next(r["unserved"] for r in exp1()["frontier"] if r["lambda"] == 2.0), [REPORT]),
    ("−1.42%", 2, lambda: next(r["unserved_change_pct"] for r in exp1()["frontier"] if r["lambda"] == 1.0), [REPORT]),
    ("107,248", 0, lambda: J("outputs/exp4_addendum/diag_N4.json")["common_lines_bound"]["total_bound_min"], [REPORT]),
    ("93,301", 0, lambda: J("outputs/exp4_addendum/diag_N4.json")["common_lines_bound"]["total_bound_min"]
        - J("outputs/exp4_addendum/diag_N3.json")["common_lines_bound"]["total_bound_min"], [REPORT]),
    ("283,973", 0, lambda: J("outputs/exp4_addendum/DELTA43.json")["comparison"]["effect"], [REPORT]),
    ("70.5%", 1, lambda: sorted(r["claim_gap_unserved_pct"] for r in map(__import__("json").loads, (ROOT / "outputs/exp2_treatments.jsonl").read_text().splitlines()) if r.get("treatment") == "route_level")[19] * -1, [REPORT]),
    ("0.50–0.63%", 2, lambda: 100 * min(r["price"] for r in J("outputs/exp7/EXP7_ANALYSIS.json")["f6_prices"] if r["level"] == "BASE" and r["network"] == "N0" and r["cell"] in ("R1_H60", "R1_H30", "R3_SPAN")), [REPORT]),
    ("–0.63%", 2, lambda: 100 * max(r["price"] for r in J("outputs/exp7/EXP7_ANALYSIS.json")["f6_prices"] if r["level"] == "BASE" and r["network"] == "N0" and r["cell"] in ("R1_H60", "R1_H30", "R3_SPAN")), [REPORT]),
    ("about 680", -1, exp1_trip_gain, [REPORT]),
    ("2.2% of modeled demand", 1, lambda: 100 * exp1_trip_gain() / 30949, [REPORT]),
    ("628", 0, lambda: s1_gains()["BASE"], [REPORT]),
    ("316–970", 0, lambda: min(class_a()), [REPORT]),
    ("–970", 0, lambda: max(class_a()), [REPORT]),
    ("316–760", 0, lambda: min(class_a(True)), [REPORT]),
    ("–760", 0, lambda: max(class_a(True)), [REPORT]),
    ("575–616", 0, lambda: min(v for k, v in s1_gains().items() if k.startswith("A2")), [REPORT]),
    ("–616", 0, lambda: max(v for k, v in s1_gains().items() if k.startswith("A2")), [REPORT]),
    ("to 316 modeled trips", 0, lambda: s1_gains()["A6_MAXWALK75"], [REPORT]),
    ("+9.66%", 2, lambda: float(__import__("re").search(r"\(\+([0-9.]+)% of N3\)", d43()).group(1)), [REPORT]),
    ("−5.43%", 2, lambda: f1a("BASE"), [CLOSE7, ADD7]),
    ("+181.72%", 2, lambda: f1a("A5_LAM1"), [CLOSE7, ADD7]),
    ("+45.11%", 2, lambda: f1a("A5_TP200"), [CLOSE7, ADD7]),
    ("+16.57%", 2, lambda: f1a("A6_WALKSPD85"), [CLOSE7, ADD7]),
    ("+4.58%", 2, lambda: f1a("A6_MAXWALK75"), [CLOSE7, ADD7]),
    ("+8.55%", 2, lambda: f4("BASE", "N3"), [CLOSE7, REPORT]),
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
    # second REF fixed point at BASE and the lambda = 1 collapse (post hoc
    # decision-space artifact; Stage 2 analysis)
    ("+30.5%", 1, lambda: dspace("BASE")["ref_f4_track"]["f1_pct"],
     [REPORT, ADD7, RES7, ERR7, README]),
    ("0.161%", 3, ref_gap_pct, [REPORT, ADD7, ERR7]),
    ("2,940,186", 0, lambda: dspace("BASE")["ref_f4_track"]["f6_track_objective"], [REPORT, ERR7]),
    ("2,935,446", 0, lambda: dspace("BASE")["ref_f4_track"]["objective"], [REPORT, ERR7]),
    ("557", 0, lambda: dspace("A5_LAM1")["cells"]["REF"]["revenue_veh_hours"], [REPORT, RES7, README]),
    ("1,583", 0, lambda: dspace("A5_LAM1")["cells"]["REF"]["served"], [REPORT, RES7]),
    ("29,366", 0, lambda: next(r["ref_unserved"] for r in J("outputs/exp7/EXP7_ANALYSIS.json")["f1_adaptive"]
                               if r["level"] == "A5_LAM1"), [REPORT, RES7]),
    # F2 preregistered Class A range
    ("−0.226", 3, lambda: row7("F2_unserved")["class_a_range"][0], [REPORT, RES7, ERR7]),
    ("+0.166", 3, lambda: row7("F2_unserved")["class_a_range"][1], [REPORT, RES7, ERR7]),
    # first referee review (docs/report/reviews/ROUND1_ADJUDICATION.md §5)
    ("+0.090%", 3, lambda: c2b()["matched_start_unserved_effect_pct"], [REPORT]),
    ("+0.054%", 3, lambda: c2b()["matched_start_objective_effect_pct"], [REPORT]),
    ("0.31", 2, lambda: c2b()["floors"], [REPORT]),
    ("−2.21%", 2, obj_change_lam2, [REPORT]),
    ("66.8%", 1, lambda: 100 * J("outputs/exp1_baseline_modelB.json")["baseline_served"] / 30949, [REPORT]),
    ("1.16%", 2, lambda: J("outputs/exp4_addendum/diag_N3.json")["common_lines_bound"]["bound_share_of_generalized_cost_pct"], [REPORT]),
    ("12.47%", 2, lambda: J("outputs/exp4_addendum/diag_N4.json")["common_lines_bound"]["bound_share_of_generalized_cost_pct"], [REPORT]),
    ("0.516%", 3, lambda: J("outputs/model_diagnostics_modelB.json")["hyperpath"]["bound_share_of_generalized_cost_pct"], [REPORT]),
    ("2,516.65", 2, lambda: next(r["revenue_veh_hours"] for r in exp1()["frontier"] if r["lambda"] == 2.0), [REPORT]),
    ("+15.31%", 2, lambda: next(r["unserved_change_pct"] for r in exp1()["frontier"] if r["lambda"] == 0.25), [REPORT]),
]


def norm(s: str) -> float:
    import re as _re
    s = _re.sub(r"^[^0-9+\-−–±]*", "", s)  # leading words ("about 680")
    s = _re.sub(r"(%?)\s.*$", r"\1", s)  # trailing words ("2.2% of ...")
    if "–" in s:  # a range token: "a–b" checks a, "–b%" checks b
        a, b = s.split("–", 1)
        s = a if a else b
    return float(s.replace("−", "-").replace("±", "").replace("%", "")
                 .replace(",", "").replace("+", "").replace("SD ", ""))


def check_figures() -> int:
    """Figures are current: every input hash in the manifest matches the file,
    and the change-map counts quoted in the report match the manifest."""
    import hashlib
    mf = ROOT / "docs/report/figures/FIGURES_MANIFEST.json"
    if not mf.exists():
        print("FAIL figures: FIGURES_MANIFEST.json missing")
        return 1
    m = json.loads(mf.read_text())
    stale = [p for p, h in m["inputs_sha256"].items()
             if hashlib.sha256((ROOT / p).read_bytes()).hexdigest() != h]
    missing = [n for n in m["figures"]
               if not all((ROOT / "docs/report/figures" / f"{n}.{x}").exists()
                          for x in ("svg", "png", "csv"))]
    cm = m.get("change_map") or {}
    text = (ROOT / REPORT).read_text()
    quoted = f"{cm.get('agreeing')}\nof {cm.get('units')} units" in text or \
        f"{cm.get('agreeing')} of {cm.get('units')} units" in text
    ok = not stale and not missing and quoted
    print(("ok  " if ok else "FAIL") + f" figures: {len(m['figures'])} figures, "
          f"{len(m['inputs_sha256'])} inputs, stale={stale}, missing={missing}, "
          f"map counts quoted={quoted}")
    return 0 if ok else 1


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
    bad += check_figures()
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
