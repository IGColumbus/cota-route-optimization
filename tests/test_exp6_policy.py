"""Experiment 6 policy constraints on a synthetic network (no data needed)."""
import math
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from cota_opt.frequency import FitnessVector, ResourceBudget, _feasible  # noqa: E402
from cota_opt.policy import PolicySpec  # noqa: E402

KEYS = [("A", "early"), ("A", "am_peak"), ("B", "early"), ("B", "am_peak"),
        ("C", "am_peak")]
BASE = {("A", "early"): 30., ("A", "am_peak"): 15., ("B", "early"): math.inf,
        ("B", "am_peak"): 20., ("C", "am_peak"): 60.}
RS = {"A": {"s1", "s2"}, "B": {"s2", "s3"}, "C": {"s4"}}
XY = {"s1": (0, 0), "s2": (500, 0), "s3": (1000, 0), "s4": (3000, 0)}
H_A_AM_OFF = np.array([30., math.inf, math.inf, 20., 60.])


def comp(**kw):
    return PolicySpec("t", **kw).compile(KEYS, BASE, RS, XY)


def test_measurements():
    assert comp(max_off_share=0.25).violation(H_A_AM_OFF) == 0.0   # 1 of 4 allowed
    assert comp(max_off_share=0.0).violation(H_A_AM_OFF) == 1.0
    assert comp(span=True).violation(H_A_AM_OFF) == 1.0            # A's last period
    assert comp(max_lost_share=0.0).violation(H_A_AM_OFF) == 1.0   # s1 in am_peak
    assert comp(area_radius_m=1207.008).violation(H_A_AM_OFF) == 0.0  # s2 is 500 m
    assert comp(area_radius_m=400.0).violation(H_A_AM_OFF) == 1.0
    assert comp(max_headway=20.).violation(H_A_AM_OFF) == 1.0


def test_baseline_is_always_feasible():
    b = np.array([BASE[k] for k in KEYS])
    for kw in ({"max_headway": 20.}, {"max_off_share": 0.0}, {"span": True},
               {"max_lost_share": 0.0}, {"area_radius_m": 10.0}):
        assert comp(**kw).violation(b) == 0.0


def test_feasible_refuses_policy_violation_and_default_unchanged():
    bud = ResourceBudget(100.0, {"am_peak": 10.0}, tolerance=0.0)
    f = FitnessVector(0.0, 0.0, 50.0, 5.0, {"am_peak": 5.0})
    assert _feasible(None, f, bud)
    g = FitnessVector(0.0, 0.0, 50.0, 5.0, {"am_peak": 5.0},
                      policy_violation=1.0)
    assert not _feasible(None, g, bud)


def test_ladder_filter_and_minimum_start():
    c = comp(max_headway=20.)
    lad = {k: [15., 20., 30., 60., math.inf] for k in KEYS}
    out = c.filter_ladders(lad)
    assert out[("A", "early")] == [15., 20., 30.]     # cap max(20, 30)
    assert math.inf in out[("B", "early")]            # not baseline-served
    c2 = comp(max_lost_share=0.0)
    L = np.array([[15., 20., 30., 60., math.inf]] * 5)
    idx = c2.minimum_start(L, np.array([5] * 5), np.array([4] * 5))
    h = L[np.arange(5), idx]
    assert c2.violation(h) == 0.0


def test_nesting_is_parameterwise_implication():
    import exp6_grid as G
    sp = G.specs("TEST")
    assert sp["R1_H20"].at_least_as_tight_as(sp["R1_H30"])
    assert not sp["R1_H30"].at_least_as_tight_as(sp["R1_H20"])
    assert sp["R1_H60"].at_least_as_tight_as(sp["B1"])
    assert sp["R4_C00"].at_least_as_tight_as(sp["R6_ADA"])
    assert not sp["R4_C00"].at_least_as_tight_as(sp["B2"])   # no span
    h = G.hasse(sp)
    assert ("R2_S25", "REF") in h["adjacent_edges"]
    assert h["equal_pairs"] == []
