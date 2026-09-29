"""Experiment 7 level declarations: validation and round-trip (no compute)."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import exp7_levels as L  # noqa: E402


def test_base_is_identity_and_digest_stable():
    assert L.BASE.is_base and not L.BASE.changes_pathsets
    assert L.BASE.digest == L.level("BASE", "none",
                                    rationale="Experiment 6 exactly").digest
    H = object()
    assert L.harness_for(H, L.BASE) is H


def test_round_trip_and_digest_sensitivity():
    a = L.level("X", "retention",
                overrides={"path_assignment.cost_retention_floor": 0.0},
                od=[("scale", {"factor": 1.5})])
    b = L.from_payload(a.payload())
    assert b == a and b.digest == a.digest
    c = L.level("X", "retention",
                overrides={"path_assignment.cost_retention_floor": 0.05},
                od=[("scale", {"factor": 1.5})])
    assert c.digest != a.digest
    assert a.changes_pathsets and not L.level("l", "lambda", lam=1.0).changes_pathsets


def test_undeclared_and_harness_build_knobs_refused():
    with pytest.raises(ValueError):
        L.level("x", "d", overrides={"crowding.bus_capacity": 80})
    for k in L.HARNESS_BUILD_KEYS:
        with pytest.raises(ValueError):
            L.level("x", "d", overrides={k: 800})
    with pytest.raises(ValueError):
        L.level("x", "d", od=[("reweight_everything", {})])
    with pytest.raises(ValueError):
        L.level("x", "d", waiting_model="magic")
