"""Regression protections for the EXP4N normalized rerun.

These exist so the normalized run cannot silently revert to candidate-specific
caps, and so the legacy Exp 4 cannot be mutated by it. They cover Ian's ten
required guarantees; the file is deliberately runnable before the rerun has
produced any results, with the result-dependent assertions skipped until then.
"""
from __future__ import annotations

import inspect
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
NORM = ROOT / "outputs" / "exp4_normalized"
LEGACY = ROOT / "outputs" / "exp4" / "run"
PERIODS = ("early", "am_peak", "midday", "pm_peak", "evening", "owl")
LEADER = "exp4|exp4-pool-v1|65lines#ecb2ffc4bcce"
LEADER_OBJ = 3511184.5657525407

ENVELOPE = NORM / "COMMON_RESOURCE_ENVELOPE.json"
ARCHIVE = NORM / "EXP4_ENDOGENOUS_CAP_ARCHIVE.json"

needs_envelope = pytest.mark.skipif(
    not ENVELOPE.exists(), reason="common envelope not frozen yet")
needs_archive = pytest.mark.skipif(
    not ARCHIVE.exists(), reason="legacy archive not written yet")


def _results(sub="certified"):
    d = NORM / sub
    if not d.exists():
        return []
    return [json.load(open(p)) for p in sorted(d.glob("*.json"))]


def _launcher_src():
    return (ROOT / "scripts" / "exp4n_launch.py").read_text()


# --- 1. "baseline" cannot resolve separately inside candidate evaluation ----

@needs_envelope
def test_launcher_passes_an_explicit_dict_not_the_sentinel():
    src = _launcher_src()
    assert '"peak_fleet_by_period": peak' in src
    assert 'must be an explicit dict, never the sentinel' in src
    assert 'assert r["peak_fleet_by_period"] != "baseline"' in src


def test_build_setup_takes_the_dict_branch_when_given_a_dict():
    """exp2.py:324 is only reached for the sentinel; :326 for a dict."""
    from cota_opt import exp2
    src = inspect.getsource(exp2.build_setup)
    assert 'res["peak_fleet_by_period"] == "baseline"' in src
    assert 'dict(fit.peak_by_period)' in src
    # the dict branch must exist and must not consult the candidate fitness
    i = src.index('peak_budget = (')
    branch = src[i:i + 400]
    assert 'else {k: float(v) for k, v in res["peak_fleet_by_period"].items()}' in branch


@needs_envelope
def test_the_resolved_envelope_is_not_candidate_derived():
    spec = json.loads(ENVELOPE.read_text())
    assert spec["source"] == "reference_network_baseline_peak_by_period"
    assert "before any candidate exists" in spec["resolved_once_against"]


# --- 2 & 3. identical peak vector and identical digest across candidates ----

@needs_envelope
def test_all_normalized_results_share_one_peak_vector_and_digest():
    rows = _results()
    if not rows:
        pytest.skip("no normalized results yet")
    spec = json.loads(ENVELOPE.read_text())
    want = {p: repr(float(spec["peak_fleet_by_period"][p])) for p in PERIODS}
    digests = {r["common_envelope_digest"] for r in rows}
    assert len(digests) == 1, f"envelope digest varies across candidates: {digests}"
    assert digests == {str(spec["envelope_digest"])}
    for r in rows:
        assert r["peak_caps"] == want, f"{r['candidate_id']} got a different cap"


# --- 4. tolerance remains exactly 0.0 --------------------------------------

def test_config_tolerance_is_zero():
    from cota_opt.configs import load_constraints
    assert float(load_constraints()["resource"].get("budget_tolerance", 0.0)) == 0.0


@needs_envelope
def test_frozen_envelope_records_zero_tolerance():
    assert json.loads(ENVELOPE.read_text())["budget_tolerance"] == 0.0


def test_normalized_results_record_zero_tolerance():
    rows = _results()
    if not rows:
        pytest.skip("no normalized results yet")
    assert {r["budget_tolerance"] for r in rows} == {0.0}


# --- 5. hours remain pinned to the canonical artifact ----------------------

@needs_envelope
def test_hours_cap_comes_from_the_canonical_artifact():
    spec = json.loads(ENVELOPE.read_text())
    canon = json.loads((ROOT / "outputs" / "CANONICAL_ENVELOPE.json").read_text())
    assert spec["weekday_revenue_vehicle_hours"] == float(
        canon["weekday_revenue_vehicle_hours"])
    assert spec["canonical_envelope_digest"] == str(canon["envelope_digest"])
    rows = _results()
    if rows:
        assert {r["hours_cap"] for r in rows} == {
            repr(float(canon["weekday_revenue_vehicle_hours"]))}


# --- 6. peak usage still goes through FitnessVector.peak_by_period ---------

def test_peak_usage_instrument_is_unchanged():
    from cota_opt.frequency import _feasible
    src = inspect.getsource(_feasible)
    assert "fit.peak_by_period.items()" in src
    assert "budget.peak_cap(p)" in src


def test_peak_vehicles_formula_is_unchanged():
    from cota_opt.frequency import FrequencyModel
    src = inspect.getsource(FrequencyModel.peak_vehicles)
    assert "cycle / headway" in src.replace("cycle/headway", "cycle / headway")


# --- 7. legacy Exp 4 outputs cannot be overwritten -------------------------

def test_launcher_never_writes_under_the_legacy_run():
    src = _launcher_src()
    assert 'LEGACY = ROOT / "outputs" / "exp4" / "run"' in src
    assert "# READ-ONLY" in src
    # every write target is built from OUT
    for marker in ("cert_dir = (OUT /", "OUT / \"COMMON_RESOURCE_ENVELOPE.json\""):
        assert marker in src or marker.replace('"', "'") in src
    assert "LEGACY /" in src          # it reads from legacy
    assert 'LEGACY / f"' not in src   # but never formats a legacy write path


@needs_archive
def test_legacy_file_digests_still_match():
    """If anything under outputs/exp4/ changed, this fails."""
    import hashlib
    arch = json.loads(ARCHIVE.read_text())
    # files moved by the 2026-10-05 release restructure are checked at their
    # new location under their historical name (docs/research-record/MOVES.json)
    mj = ROOT / "docs" / "research-record" / "MOVES.json"
    moved = json.loads(mj.read_text())["moves"] if mj.exists() else {}
    bad = []
    for rel, meta in arch["file_digests"].items():
        p = ROOT / rel
        if not p.exists() and rel in moved:
            p = ROOT / moved[rel]
        if not p.exists():
            bad.append((rel, "MISSING")); continue
        h = hashlib.sha256()
        with open(p, "rb") as f:
            for b in iter(lambda: f.read(1 << 20), b""):
                h.update(b)
        if h.hexdigest() != meta["sha256"]:
            bad.append((rel, "CHANGED"))
    assert not bad, f"legacy Exp 4 artifacts mutated: {bad[:5]}"


# --- 8. candidate geometries unchanged from the original 200 --------------

@needs_archive
def test_archive_holds_exactly_the_original_200():
    arch = json.loads(ARCHIVE.read_text())
    assert arch["n_candidates"] == 200
    assert len({c["state_key"] for c in arch["candidates"]}) == 200


@needs_archive
def test_normalized_candidates_are_the_archived_geometries():
    rows = _results()
    if not rows:
        pytest.skip("no normalized results yet")
    arch = json.loads(ARCHIVE.read_text())
    want = {c["state_key"]: c["state_digest"] for c in arch["candidates"]}
    for r in rows:
        assert r["candidate_id"] in want, f"{r['candidate_id']} is not an Exp 4 candidate"
        assert r["geometry_digest"] == want[r["candidate_id"]], \
            f"{r['candidate_id']} geometry digest differs from the archive"


# --- 9. the frozen old incumbent is untouched ------------------------------

def test_legacy_incumbent_objective_is_unchanged():
    hits = [json.load(open(p)) for p in (LEGACY / "certified").glob("*.json")]
    lead = [d for d in hits if d.get("state_key") == LEADER]
    assert len(lead) == 1
    assert lead[0]["objective_EXACT"] == LEADER_OBJ


@needs_archive
def test_archive_pins_the_old_incumbent():
    arch = json.loads(ARCHIVE.read_text())
    assert arch["incumbent"]["state_key"] == LEADER
    assert arch["incumbent"]["objective_EXACT"] == LEADER_OBJ
    assert arch["incumbent"]["certified_rank"] == 1


# --- 10. normalized output paths are distinct from legacy ------------------

def test_output_namespaces_are_disjoint():
    assert NORM.resolve() != (ROOT / "outputs" / "exp4").resolve()
    assert not str(NORM.resolve()).startswith(str((ROOT / "outputs" / "exp4").resolve()) + "/")


def test_normalized_results_declare_their_own_experiment_id():
    rows = _results()
    if not rows:
        pytest.skip("no normalized results yet")
    assert {r["experiment"] for r in rows} == {"EXP4N"}
    assert {r["cap_provenance"] for r in rows} == {
        "common_reference_envelope_resolved_once"}


# --- search procedure parity ----------------------------------------------

def test_search_parameters_match_the_legacy_run():
    from cota_opt.exp4_certify import K_RUNGS, MAX_ROUNDS, N_KEYS
    assert (N_KEYS, K_RUNGS, MAX_ROUNDS) == (8, 3, 40)
    rows = _results()
    if rows:
        assert {(r["n_keys"], r["k_rungs"], r["max_rounds"]) for r in rows} == \
            {(8, 3, 40)}


def test_lam_and_seed_match_the_legacy_run():
    src = _launcher_src()
    assert "LAM, SEED = 2.0, 20260825" in src
    rows = _results()
    if rows:
        assert {(r["lam"], r["seed"]) for r in rows} == {(2.0, 20260825)}
