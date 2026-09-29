"""Experiment 7 Stage 1 analysis and Stage 2 selection -- synthetic tests."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import exp7_stage1 as S  # noqa: E402
import exp7_stage1_analyze as A  # noqa: E402


def R(o, u=100.0):
    return {"objective": o, "unserved_demand": u}


def synthetic(scale=1.0, n4=1.1):
    n0 = {"F1_BASELINE": R(0, 100.0)}
    for i, s in enumerate(A.SEEDS1):
        n0[f"F1_PLAN_{s}"] = R(0, 93.0 + i)            # -7, -6, -5 -> -6
        n0[f"F2_CONTROL_{s}"] = R(1000.0, 50.0)
    n0s = {f"F2_SPLICE_{s}": R(1001.0, 50.1) for s in A.SEEDS1}
    n3 = {}
    for s in A.SEEDS3:
        n0[f"F3_CONTROL_{s}"] = R(1000.0)
        n3[f"F3_ADDSTOP_{s}"] = R(998.0)
    n0["F4_N0_J100"] = R(1000.0 * scale)
    n3["F4_N3_EXP4A"] = R(990.0 * scale)
    n4 = {"F4_N4_EXP4N": R(1000.0 * scale * n4), "F5_N4_J100": R(1100.0)}
    for c, o in (("J090", 1010.0), ("J110", 990.0), ("P090", 1005.0),
                 ("P110", 996.0)):
        n0[f"F5_N0_{c}"] = R(o)
        n4[f"F5_N4_{c}"] = R(o + 100)
    for net, rows in (("N0", n0), ("N3", n3)):
        rows[f"F6_{net}_REF"] = R(2000.0)
        for j, c in enumerate(A.CELLS[1:]):
            rows[f"F6_{net}_{c}"] = R(2000.0 + j)
    return {"N0": n0, "N0S": n0s, "N3": n3, "N4": n4}


def test_finding_values():
    q = A.finding_values(synthetic(), {"N0": 17.6, "N4": 17.6})
    assert q["F1"] == pytest.approx(-6.0)
    assert q["F2_unserved"] == pytest.approx(0.2)
    assert q["F2_objective"] == pytest.approx(0.1)
    assert q["F3"] == pytest.approx(-0.2)
    assert q["F4_43"] == pytest.approx(100 * (1100 - 990) / 990)
    assert q["F4_40"] == pytest.approx(10.0)
    assert q["F5_N0_peak_lower"] == pytest.approx((1000 - 1005) / 17.6)
    assert q["F5_N0_joint_upper"] == pytest.approx((990 - 1000) / 10)
    assert q["F5_N0_monotone_joint"] is True
    assert q["F6_N0_R1_H60"] == 0.0 and q["F6_N0_R1_H30"] == pytest.approx(0.05)
    assert q["AF1_REF"] == 0.0


def test_missing_row_gives_none_not_a_number():
    ev = synthetic()
    ev["N0"]["F1_PLAN_20260826"] = {"error": "x"}
    assert A.finding_values(ev, {"N0": 1, "N4": 1})["F1"] is None


def test_classification_and_certified_movement():
    dim_of = {"a1": "A1", "a2": "A1", "b": "B_assignment"}
    c = A.classify_quantity(-6.0, {"a1": -5.0, "a2": -6.3, "b": 1.0}, dim_of,
                            certified=-6.65)
    assert c["sign"]["label"] == "SIGN_ROBUST"          # b is Class B: excluded
    assert c["per_level"]["a1"]["band"] == "Stable magnitude"
    assert c["per_level"]["b"]["sign_event"] == "SIGN_FLIP"
    assert c["worst_band_by_dimension"]["A1"] == "Stable magnitude"
    assert c["per_level"]["a2"]["movement_from_certified_pct"] == \
        pytest.approx(100 * (-6.3 + 6.65) / 6.65)
    assert c["range_includes_zero"] is False


def test_stage2_selection_is_deterministic_and_class_a_only():
    dim_of = {"x1": "A1", "x2": "A3", "x3": "A7", "b": "B_assignment",
              "t": "X_od_coverage"}
    m1 = A.dimension_movement(-6.0, {"x1": -6.6, "x2": -3.0, "x3": -6.0,
                                     "b": 50.0, "t": 80.0}, dim_of)
    assert set(m1) == {"A1", "A3", "A7"}
    m4 = A.dimension_movement(10.0, {"x1": 10.0, "x2": 10.0, "x3": 15.0},
                              dim_of)
    sel = A.select_stage2(m1, m4)
    assert sel["selected"] == ["A3", "A7"]
    tie = A.select_stage2({"A5": 0.3, "A1": 0.3}, {})
    assert tie["selected"] == ["A1", "A5"]              # id order breaks ties
    assert A.dimension_movement(0.0, {"x1": 1.0}, dim_of) == {}


def test_bootstrap_subset_is_preregistered():
    levels = [{"name": f"A2_BOOT{b:02d}", "dimension": "A2"} for b in range(1, 21)]
    levels += [{"name": "A3_RT110", "dimension": "A3"},
               {"name": "A1_NC025", "dimension": "A1"}]
    got = A.stage2_levels(["A2", "A3"], levels)
    assert got == ["A2_BOOT01", "A2_BOOT05", "A2_BOOT10", "A2_BOOT15",
                   "A2_BOOT20", "A3_RT110"]
    assert A.BOOTSTRAP_REOPT_SUBSET == (1, 5, 10, 15, 20)


def test_plan_normalization_formats():
    a = S.norm_plan({"001::am_peak": 10, "002::owl": float("inf"),
                     "003::x": None})
    b = S.norm_plan({"001|am_peak": 10.0, "002|owl": None, "003|x": "inf"})
    assert a == b and S.plan_digest(a) == S.plan_digest(b)


def _stage2_env(tmp_path, monkeypatch, tamper=False):
    import hashlib
    import importlib
    import json
    monkeypatch.setenv("EXP7_OUT", str(tmp_path))
    import exp7_run
    R = importlib.reload(exp7_run)
    lv = [{"name": n, "dimension": d, "digest": "x"} for n, d in (
        ("BASE", "none"), ("A1_NC025", "A1"), ("A2_BOOT01", "A2"),
        ("A2_BOOT02", "A2"), ("A3_RT110", "A3"))]
    con = {"design": "two_stage", "levels": lv,
           "level_order": [x["name"] for x in lv], "sentinels": []}
    (tmp_path / "EXP7_CONTRACT.json").write_text(json.dumps(con))
    dig = hashlib.sha256((tmp_path / "EXP7_CONTRACT.json").read_bytes()).hexdigest()[:16]
    sel = {"exp7_contract_sha256_16": "0" * 16 if tamper else dig,
           "included_levels": ["A2_BOOT01", "A3_RT110"]}
    (tmp_path / "EXP7_STAGE2_SELECTION.json").write_text(json.dumps(sel))
    return R


def test_stage2_driver_restricts_to_frozen_selection(tmp_path, monkeypatch):
    R = _stage2_env(tmp_path, monkeypatch)
    con = R.contract()
    assert con["level_order"] == ["BASE", "A2_BOOT01", "A3_RT110"]
    assert [p["name"] for p in con["levels"]] == ["BASE", "A2_BOOT01", "A3_RT110"]
    assert con["sentinels"][0] == ["F6", "A3_RT110", "N3", "REF"]


def test_stage2_driver_refuses_other_contract_or_missing_selection(tmp_path,
                                                                   monkeypatch):
    R = _stage2_env(tmp_path, monkeypatch, tamper=True)
    with pytest.raises(SystemExit):
        R.contract()
    (tmp_path / "EXP7_STAGE2_SELECTION.json").unlink()
    with pytest.raises(SystemExit):
        R.contract()
