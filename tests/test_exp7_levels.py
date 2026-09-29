"""Experiment 7 level declarations: validation and round-trip (no compute)."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
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


def test_noncommute_requires_declared_parameterization():
    import numpy as np

    class Z:
        workers = np.array([1.0, 2.0, 3.0])
        jobs = np.array([3.0, 2.0, 1.0])
        x = np.array([0.0, 1000.0, 2000.0])
        y = np.zeros(3)

    class OD:
        def __init__(self):
            self.origin = np.array([0, 1, 2, 0])
            self.dest = np.array([1, 2, 0, 2])
            self.flow = np.array([1.0, 2.0, 3.0, 4.0])
            self.source, self.notes = "t", ""

        def __len__(self):
            return 4

    class H:
        zones = Z()
    from cota_opt.odmatrix import ODTable
    od = ODTable(np.array([0, 1, 2, 0]), np.array([1, 2, 0, 2]),
                 np.array([1.0, 2.0, 3.0, 4.0]), "t", "")
    with pytest.raises(ValueError):
        L._od_transform(H, od, "noncommute_blend", {"share_b": 0.3}, {})
    out = L._od_transform(H, od, "noncommute_blend",
                          {"share_b": 0.3, "decay_km": 4.0,
                           "zone_weight": "workers_plus_jobs"}, {})
    assert abs(out.flow.sum() - od.flow.sum()) < 1e-9
    assert not np.allclose(out.flow, od.flow)
