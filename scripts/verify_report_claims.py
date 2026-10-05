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
CLOSE7 = "experiments/exp7/EXPERIMENT7_CLOSEOUT.md"
ADD7 = "experiments/exp7/EXPERIMENT7_F1_ADDENDUM.md"
RES7 = "experiments/exp7/EXPERIMENT7_RESULTS.md"
ERR7 = "experiments/exp7/EXPERIMENT7_CLOSEOUT_ERRATA.md"
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



# ---- release pass 2026-10-05: decision-relevant numbers in public documents
def f1_class_a():
    return row7("F1")["class_a_range"]


def exp3_certified_effects():
    er = J("outputs/exp3/escalation_report.json")
    return [abs(c["mean_pct"]) for c in er["combined"]
            if c.get("certified") and c["state"] in er["certified"]]


def e6_range(net):
    v = [r["policy_cost_closed_pct"] for r in J("outputs/exp6/EXP6_ANALYSIS.json")["frontier"]
         if r["network"] == net and r.get("policy_cost_closed_pct") is not None]
    return min(v), max(v)


def exp5_n0_hours(mult):
    fr = [r for r in J("outputs/exp5/EXP5_ANALYSIS.json")["frontier"] if r["network"] == "N0"]
    ref = next(r for r in fr if r["cell"].endswith("J100"))
    cell = next(r for r in fr if r["arm"] == "B_hours_only" and abs(r["hours_mult"] - mult) < 1e-9)
    return 100 * (cell["objective"] - ref["objective"]) / ref["objective"]


def n_class_a_levels():
    return sum(1 for lv in J("outputs/exp7/EXP7_LEVELS.json")["levels"]
               if lv["dimension"].startswith("A"))


def served_share_pct():
    return 100 * J("outputs/exp1_baseline_modelB.json")["baseline_served"] / 30949



def _blocking(net: str) -> list[float]:
    b = J("outputs/exp5/EXP5_ANALYSIS.json")["blocking_DIAGNOSTIC_ONLY"]
    return [c["tt_vs_model_hours"] for k, c in b.items() if k.startswith(net)]


def _retention(cost_min: float) -> float:
    """The study's cost-based retention curve, from config/assumptions.yaml."""
    import yaml
    pa = yaml.safe_load((ROOT / "config/assumptions.yaml").read_text())["path_assignment"]
    full, zero, floor = (pa["cost_retention_full_min"], pa["cost_retention_zero_min"],
                         pa["cost_retention_floor"])
    if cost_min <= full:
        return 1.0
    if cost_min >= zero:
        return floor
    return 1.0 - (1.0 - floor) * (cost_min - full) / (zero - full)


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
    ("~680 more", -1, exp1_trip_gain, [REPORT]),
    ("~2.2% of the 30,949", 1, lambda: 100 * exp1_trip_gain() / 30949, [REPORT]),
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
    # release pass 2026-10-05 (scripts/audit_public_numbers.py priority sections)
    ("+3.3%", 1, lambda: exp1()["headline"]["trips_served"]["mean_pct"], [README]),
    ("6.65%", 2, lambda: -exp1()["headline"]["unserved_demand"]["mean_pct"], [README]),
    ("0.88%", 2, lambda: exp1()["headline"]["generalized_cost"]["mean_pct"], [README]),
    ("67% of that total", 0, served_share_pct, [REPORT]),
    ("33% unserved", 0, lambda: 100 - served_share_pct(), [REPORT]),
    ("44 pre-specified", 0, n_class_a_levels, [REPORT, README]),
    ("−1.9% to −7.0%", 1, lambda: f1_class_a()[1], [REPORT, README]),
    ("to −7.0%", 1, lambda: f1_class_a()[0], [REPORT, README]),
    ("−1.897%", 3, lambda: f1_class_a()[1], []),
    ("12 through-routing", 0, lambda: len(J("outputs/exp2_candidate_classes.json")["candidates"]), [REPORT]),
    ("the 0.287", 3, lambda: J("outputs/exp2_summary.json")["recheck_D19"]["full_effort_floor_pts"], [REPORT]),
    ("240-set", 0, lambda: J("outputs/exp2_summary.json")["subset_search_2B"]["n_subsets_solved"], [REPORT, README]),
    ("29 seed-distinguishable", 0, lambda: len(J("outputs/exp3/escalation_report.json")["certified"]), [REPORT, README]),
    ("0.01–0.19%", 2, lambda: min(exp3_certified_effects()), [REPORT]),
    ("at most 0.19%", 2, lambda: max(exp3_certified_effects()), [REPORT]),
    ("−0.18657%", 5, lambda: J("outputs/exp7/stage1/EXP7_STAGE1_ANALYSIS.json")["values"]["BASE"]["F3"], [README]),
    ("−0.19%", 2, lambda: J("outputs/exp7/stage1/EXP7_STAGE1_ANALYSIS.json")["values"]["BASE"]["F3"], [REPORT]),
    ("200 promoted", 0, lambda: len(J("outputs/exp4_normalized/EXP4N_RANKING.json")["ordering"]), [REPORT, README]),
    ("8.5–9.7%", 1, lambda: f4("BASE", "N3"), [REPORT]),
    ("–9.7%", 1, lambda: float(__import__("re").search(r"\(\+([0-9.]+)% of N3\)", d43()).group(1)), [REPORT]),
    ("36.7%", 1, lambda: 100 * J("outputs/exp4_normalized/EXP4N_RANKING.json")["normalized_vs_legacy"]["pairwise_inverted_fraction"], [REPORT]),
    ("0–0.91%", 0, lambda: e6_range("N0")[0], [REPORT, README]),
    ("–0.91%", 2, lambda: e6_range("N0")[1], [REPORT, README]),
    ("0–0.63%", 0, lambda: e6_range("N3")[0], [REPORT, README]),
    ("+0.91%", 2, lambda: e6_range("N0")[1], [REPORT]),
    ("0 to +0.912%", 0, lambda: e6_range("N0")[0], []),
    ("0.16% apart", 2, ref_gap_pct, [REPORT, README]),
    ("give −5.4%", 1, lambda: f1a("BASE"), [REPORT, README]),
    ("+0.56%", 2, lambda: exp5_n0_hours(0.9), [REPORT]),
    ("+2.04%", 2, lambda: exp5_n0_hours(0.75), [REPORT]),
    ("0.56–2.04%", 2, lambda: exp5_n0_hours(0.9), ["docs/FINDINGS.md"]),
    ("1.70%", 2, lambda: max(float(p["regression_pct"]) for p in
                            J("outputs/exp5/EXP5_ANALYSIS.json")["monotonicity"]["pairs"]
                            if p["status"] != "MONOTONE"), [REPORT]),
    ("of 2,516", 0, lambda: dspace("BASE")["cells"]["REF"]["revenue_veh_hours"], [README]),
    ("19% of route-periods", 0, lambda: exp1()["plan_disagreement"]["mean_share_changed_pct"], []),
    ("−2.1% to −7.0%", 1, lambda: r1h60("A6_MAXWALK75"), [REPORT]),
    ("698 and 753", 0, lambda: s1_gains()["A8_FLOOR0"], [REPORT]),
    ("and 753 trips", 0, lambda: s1_gains()["A8_ZERO150"], [REPORT]),
    ("(0.415", 3, lambda: J("outputs/exp7/stage1/EXP7_STAGE1_ANALYSIS.json")["stage2_metric"]["scores"]["A1"], [REPORT]),
    ("0.685", 3, lambda: J("outputs/exp7/stage1/EXP7_STAGE1_ANALYSIS.json")["stage2_metric"]["scores"]["A6"], [REPORT]),
    ("+0.09% unserved", 2, lambda: c2b()["matched_start_unserved_effect_pct"], [REPORT]),
    ("+0.0065% unserved", 4, lambda: J("outputs/exp7/stage1/EXP7_STAGE1_ANALYSIS.json")["values"]["BASE"]["F2_unserved"], [REPORT]),
    ("keeps 64% of riders", 0, lambda: 100 * _retention(120), [REPORT]),
    ("and 10% beyond", 0, lambda: 100 * _retention(1e9), [REPORT]),
    ("(−5.4% versus", 1, lambda: f1a("BASE"), ["docs/PUBLIC_BRIEF.md"]),
    ("(139 route-periods", 0, lambda: dspace("A5_LAM1")["cells"]["REF"]["n_off"], [REPORT]),
    ("by 17.8–22.7%", 1, lambda: 100 * min(_blocking("N0")), [REPORT]),
    ("–22.7% (N0)", 1, lambda: 100 * max(_blocking("N0")), [REPORT]),
    ("and 45.6–47.0% (N4)", 1, lambda: 100 * min(_blocking("N4")), [REPORT]),
    ("–47.0% (N4)", 1, lambda: 100 * max(_blocking("N4")), [REPORT]),
]


def norm(s: str) -> float:
    import re as _re
    s = _re.sub(r"^[^0-9+\-−–±]*", "", s)  # leading words ("about 680")
    s = _re.sub(r"(%?)\s.*$", r"\1", s)  # trailing words ("2.2% of ...")
    s = _re.sub(r"(?<=[0-9%])-[A-Za-z].*$", "", s)  # hyphenated suffix ("240-set")
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
    external = [p for p in m["inputs_sha256"] if p.startswith("data/") and not (ROOT / p).exists()]
    stale = [p for p, h in m["inputs_sha256"].items() if p not in external
             and (not (ROOT / p).exists()
                  or hashlib.sha256((ROOT / p).read_bytes()).hexdigest() != h)]
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
          f"map counts quoted={quoted}"
          + (f", external raw inputs unavailable={external}" if external else ""))
    return 0 if ok else 1


NUMBERS = ROOT / "docs/report/REPORT_NUMBERS.json"


def _evaluate(get):
    """Run one extractor, recording which repository files it read."""
    read: list[str] = []
    orig = Path.read_text

    def spy(self, *a, **k):
        try:
            rel = self.resolve().relative_to(ROOT).as_posix()
            if rel not in read:
                read.append(rel)
        except ValueError:
            pass
        return orig(self, *a, **k)

    Path.read_text = spy
    try:
        return get(), read
    finally:
        Path.read_text = orig


_NUM = __import__("re").compile(r"(?<![A-Za-z0-9_./#-])[+−\-]?\d[\d,]*(?:\.\d+)?%?")


def report_coverage() -> dict:
    """Numeric tokens in the report body, split into artifact-checked and not.

    Coverage is token-level and approximate: a number counts as checked when it
    occurs inside a written claim string listed for the report. Section and
    table numbering, years, commit hashes and code are excluded."""
    import re as _re
    text = (ROOT / REPORT).read_text()
    text = _re.sub(r"```.*?```", " ", text, flags=_re.S)
    text = _re.sub(r"`[^`]*`", " ", text)
    text = _re.sub(r"^#+ .*$", " ", text, flags=_re.M)
    text = _re.sub(r"\]\([^)]*\)", "]", text)          # link targets
    text = _re.sub(r"§\s?[\d.]+", " ", text)
    toks = [t for t in _NUM.findall(text)
            if not _re.fullmatch(r"(19|20)\d\d", t) and t not in ("0", "1", "2", "3", "4", "5", "6", "7", "8", "9")]
    claimed = " ".join(c[0] for c in CLAIMS if REPORT in c[3])
    checked = [t for t in toks if t.lstrip("+−-") in claimed]
    unchecked = sorted(set(toks) - set(checked))
    return {"numeric_tokens": len(toks), "artifact_checked_tokens": len(checked),
            "unchecked_distinct": len(unchecked), "unchecked_examples": unchecked[:60]}


def build_numbers() -> dict:
    rows = []
    for text, dec, get, docs in CLAIMS:
        v, read = _evaluate(get)
        rows.append({"written": text, "decimals": dec, "artifact_value": round(float(v), 9),
                     "sources": read, "documents": docs})
    return {"generated_by": "scripts/verify_report_claims.py --write-numbers",
            "note": ("Every value is computed from the listed committed artifacts by the "
                     "extractor in the verifier; documents are checked to contain the "
                     "written string. coverage reports how much of the report's numeric "
                     "text this registry reaches; the remainder is not yet machine-checked."),
            "claims": rows, "coverage": report_coverage()}


def main() -> int:
    if "--write-numbers" in sys.argv:
        NUMBERS.write_text(json.dumps(build_numbers(), indent=1, ensure_ascii=False) + "\n")
        print(f"wrote {NUMBERS.relative_to(ROOT)}")
        return 0
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
    if NUMBERS.exists():
        current = json.loads(NUMBERS.read_text())
        fresh = build_numbers()
        same = current == fresh
        cov = fresh["coverage"]
        print(("ok  " if same else "FAIL") + " REPORT_NUMBERS.json "
              + ("current" if same else "stale: rerun with --write-numbers")
              + f"; report coverage {cov['artifact_checked_tokens']}/{cov['numeric_tokens']} numeric tokens")
        bad += not same
    else:
        print("FAIL REPORT_NUMBERS.json missing: run with --write-numbers")
        bad += 1
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
