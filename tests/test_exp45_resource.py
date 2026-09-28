"""Experiment 5 modeled-resource envelope and Exp 4A/5 firewall contracts."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import exp5_model_resource as MR  # noqa: E402
import exp45_contracts as C  # noqa: E402


@pytest.fixture(scope="module")
def base():
    return MR.load_base()


def test_base_is_the_exp4n_envelope(base):
    assert base.exact_fingerprint == "0b46d1abc9a80c80"
    assert base.rounded_envelope_digest == "3fd5241db44ca9da"
    assert repr(base.hours_cap) == "2517.1833333333334"


def test_unit_scale_is_bit_identical(base):
    e = MR.scale(base, 1.0, 1.0)
    assert e.exact_fingerprint == base.exact_fingerprint
    assert e.hours_cap == base.hours_cap
    assert dict(e.peak_proxy_caps) == dict(base.peak_proxy_caps)


def test_scaling_is_continuous_not_floored(base):
    e = MR.scale(base, 0.75, 0.75)
    for p in MR.PERIODS:
        assert e.peak_proxy_caps[p] == base.peak_proxy_caps[p] * 0.75
    assert any(v != int(v) for v in e.peak_proxy_caps.values())


def test_scale_refuses_chaining(base):
    with pytest.raises(MR.ModelResourceError):
        MR.scale(MR.scale(base, 0.9, 0.9), 0.9, 0.9)


def test_grid_is_sixteen_unique_cells(base):
    g = MR.grid(base)
    assert len(g) == 16
    arms = [c.arm for c in g]
    assert arms.count(MR.ARM_JOINT) == 6
    assert arms.count(MR.ARM_HOURS) == 5
    assert arms.count(MR.ARM_PEAK) == 5
    assert len({c.envelope.exact_fingerprint for c in g}) == 16
    assert {c.id for c in g} >= {"J100", "H075", "P150"}


def test_nesting_is_exact_domination(base):
    g = {c.id: c for c in MR.grid(base)}
    pairs = {(a.id, b.id) for a, b in MR.nested_pairs(list(g.values()))}
    assert ("J150", "J075") in pairs
    assert ("H150", "J100") in pairs
    assert ("H150", "P150") not in pairs and ("P150", "H150") not in pairs


def test_constraints_carry_explicit_caps(base):
    from cota_opt.configs import load_constraints
    e = MR.scale(base, 0.9, 1.1)
    c = e.to_constraints(load_constraints())
    r = c["resource"]
    assert r["weekday_revenue_vehicle_hours"] == e.hours_cap
    assert r["peak_fleet_by_period"] == dict(e.peak_proxy_caps)
    assert r["peak_fleet_by_period"] != {}
    assert float(r.get("budget_tolerance", 0.0)) == 0.0


def test_payload_never_calls_the_proxy_fleet(base):
    p = MR.scale(base, 1.25, 1.25).payload()
    assert p["peak_semantics"] == "solver_peak_concurrency_proxy"
    assert p["peak_units"].startswith("proxy units")
    with pytest.raises(MR.ModelResourceError):
        MR._assert_no_fleet_language({"peak_semantics": "peak fleet",
                                      "peak_units": "proxy units"})


def test_tolerance_must_stay_zero(base):
    with pytest.raises(MR.ModelResourceError):
        MR.ModelResourceEnvelope(
            hours_cap=base.hours_cap, peak_proxy_caps=base.peak_proxy_caps,
            hours_multiplier=1.0, peak_multiplier=1.0, tolerance=0.005)


def test_contracts_are_distinct_and_scoped():
    p = C.contracts_payload()
    assert len({v["digest"] for v in p.values()}) == 3
    assert set(p["EXP5_FRONTIER"]["allowed_treatment_differences"]) == {
        "envelope_digest", "envelope_used_vh"}
    assert "envelope_digest" not in p["EXP5_STRUCTURE"][
        "allowed_treatment_differences"]
    assert "envelope_digest" not in p["EXP4A_MATCHED"][
        "allowed_treatment_differences"]
    for v in p.values():
        assert "n_keys=8" in v["solver"]["name"]
        assert v["solver"]["require_convergence"] is True
