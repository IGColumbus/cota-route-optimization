"""Reproducibility tests for the Exp 4 resource normalization audit.

These do NOT re-run certification. They assert that the audit's artifacts are
internally consistent, that its central factual claims still hold against the
committed record, and that the code path the audit is about has not silently
changed underneath it.
"""
from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
AUD = ROOT / "outputs" / "exp4_resource_audit"
PERIODS = ["early", "am_peak", "midday", "pm_peak", "evening", "owl"]
LEADER = "exp4|exp4-pool-v1|65lines#ecb2ffc4bcce"
LEADER_OBJ = 3511184.5657525407

pytestmark = pytest.mark.skipif(
    not (AUD / "EXP4_RESOURCE_AUDIT_RESULT.json").exists(),
    reason="audit artifacts not present")


def _caps():
    return list(csv.DictReader(open(AUD / "EXP4_CANDIDATE_RESOURCE_CAPS.csv")))


def test_the_sentinel_this_audit_is_about_is_still_in_force():
    """If this flips, the audit's premise no longer describes the code."""
    from cota_opt.configs import load_constraints
    assert load_constraints()["resource"]["peak_fleet_by_period"] == "baseline"


def test_budget_tolerance_is_still_zero():
    from cota_opt.configs import load_constraints
    res = load_constraints()["resource"]
    assert float(res.get("budget_tolerance", 0.0)) == 0.0


def test_feasible_still_tests_both_arms():
    """The two-arm structure is what the whole audit rests on."""
    import inspect
    from cota_opt.frequency import _feasible
    src = inspect.getsource(_feasible)
    assert "revenue_veh_hours" in src
    assert "peak_by_period" in src and "peak_cap" in src


def test_peak_budget_is_still_read_off_the_candidate_baseline():
    """exp2.py:324 -- the line the audit is about."""
    import inspect
    from cota_opt import exp2
    src = inspect.getsource(exp2.build_setup)
    assert "peak_budget" in src
    assert "dict(fit.peak_by_period)" in src


def test_caps_csv_covers_200_candidates_plus_the_reference():
    rows = _caps()
    assert len(rows) == 201
    assert sum(1 for r in rows if r["candidate_id"] == "REFERENCE_NETWORK") == 1


def test_every_candidate_cap_vector_is_the_same_shape():
    """The audit's §3 claim: six caps, one degree of freedom.

    Ratios against midday are (3, 2, 1, 2, 1.5, 1) for every candidate.
    """
    expect = {"early": 3.0, "am_peak": 2.0, "midday": 1.0,
              "pm_peak": 2.0, "evening": 1.5, "owl": 1.0}
    for r in _caps():
        if r["candidate_id"] == "REFERENCE_NETWORK":
            continue
        mid = float(r["midday_cap"])
        for p in PERIODS:
            assert float(r[f"{p}_cap"]) / mid == pytest.approx(expect[p], rel=1e-9)


def test_the_reference_network_has_a_different_shape():
    ref = next(r for r in _caps() if r["candidate_id"] == "REFERENCE_NETWORK")
    mid = float(ref["midday_cap"])
    assert float(ref["early_cap"]) / mid != pytest.approx(3.0, rel=1e-6)
    # pm_peak reproduces the documented concurrency proxy of 176.49
    assert float(ref["pm_peak_cap"]) == pytest.approx(176.4931, abs=1e-3)


def test_the_frozen_incumbent_objective_is_unchanged():
    run = ROOT / "outputs" / "exp4" / "run" / "certified"
    hit = [json.load(open(p)) for p in run.glob("*.json")]
    lead = [d for d in hit if d.get("state_key") == LEADER]
    assert len(lead) == 1
    assert lead[0]["objective_EXACT"] == LEADER_OBJ


def test_no_final_plan_is_feasible_under_the_reference_envelope():
    """§5: envelope B admits nothing, and `early` is why."""
    rows = list(csv.DictReader(open(AUD / "EXP4_FINALIST_CROSS_FEASIBILITY.csv")))
    assert len(rows) == 200
    assert all(r["feasible_A_own"] == "True" for r in rows)
    assert all(r["feasible_B_reference"] == "False" for r in rows)
    assert all("early" in r["failing_periods_B_reference"] for r in rows)


def test_pilot_is_ten_candidates_all_converged_and_hours_feasible():
    res = json.loads((AUD / "EXP4_RESOURCE_AUDIT_RESULT.json").read_text())
    assert res["pilot_n"] == 10
    assert res["all_converged"] is True
    assert res["all_hours_feasible"] is True


def test_pilot_used_one_common_envelope_for_every_candidate():
    rows = list(csv.DictReader(open(AUD / "EXP4_COMMON_CAP_PILOT.csv")))
    assert len(rows) == 10
    for p in PERIODS:
        vals = {r[f"common_{p}_cap"] for r in rows}
        assert len(vals) == 1, f"{p} cap differed across pilot candidates"


def test_pilot_reproduces_the_recorded_decision_inputs():
    """Guards the §10 gate against silent drift in its own evidence."""
    res = json.loads((AUD / "EXP4_RESOURCE_AUDIT_RESULT.json").read_text())
    assert res["original_winner"]["remains_best"] is False
    assert res["original_winner"]["normalized_rank_in_pilot"] == 9
    assert res["pairwise_reversals"] == 20
    assert res["pairwise_total"] == 45
    assert res["best_under_common_cap"]["original_certified_rank_of_200"] == 50
    assert res["spearman_original_vs_normalized_rank"] == pytest.approx(0.2121, abs=5e-4)


def test_delta_spread_is_comparable_to_the_whole_original_spread():
    """The size claim in §9: the artifact is as big as the phenomenon."""
    res = json.loads((AUD / "EXP4_RESOURCE_AUDIT_RESULT.json").read_text())
    spread_pp = res["delta_percent"]["spread_pp"]
    assert 2.0 < spread_pp < 2.5          # against the original 2.2788% spread
    assert res["delta_percent"]["max"] < 0  # every candidate improved


def test_larger_endogenous_caps_went_with_smaller_gains():
    res = json.loads((AUD / "EXP4_RESOURCE_AUDIT_RESULT.json").read_text())
    assert res["pearson_originalSumCap_vs_deltaPercent"] > 0.3


def test_provenance_records_the_cap_as_candidate_specific():
    prov = json.loads((AUD / "EXP4_RESOURCE_AUDIT_PROVENANCE.json").read_text())
    assert prov["cap_is_candidate_specific"] is True
    assert prov["peak_usage_instrument"] == prov["peak_cap_instrument"].replace(
        "identical -- both are FitnessVector.peak_by_period",
        prov["peak_usage_instrument"])
    assert prov["budget_tolerance"] == 0.0
    assert not math.isnan(prov["leader_parity_worst_abs_diff"])
    assert prov["leader_parity_worst_abs_diff"] < 5e-5
