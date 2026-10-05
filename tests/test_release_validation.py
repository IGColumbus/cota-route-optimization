"""Acceptance test for `cota-opt validate-model` (release guidelines, Validation step).

Deliberately mismatched route-volume data must report `failed`, absent stop
data must report `unavailable`, both statuses must appear on the output
artifact, and there must be no overall "validated" flag.
"""
from __future__ import annotations

import json

import yaml

from cota_release import validation
from cota_release.cli import main as cli_main


def _cfg(tmp_path, route_csv: str | None):
    obs = {"route_volume": None, "stop_pattern": None, "transfer_behavior": None,
           "trip_length": None}
    if route_csv:
        p = tmp_path / "route_volume.csv"
        p.write_text(route_csv)
        obs["route_volume"] = str(p)
    cfg = {"observed": obs, "thresholds": {"route_volume_max_pct_rmse": 25.0,
                                           "stop_pattern_max_pct_rmse": 25.0,
                                           "transfer_rate_max_abs_diff": 0.05,
                                           "trip_length_max_ks": 0.1}}
    c = tmp_path / "validation.yaml"
    c.write_text(yaml.safe_dump(cfg))
    return c


def _modeled(tmp_path):
    m = tmp_path / "modeled.json"
    m.write_text(json.dumps({"route_volume": {"1": 1000.0, "2": 2000.0, "10": 500.0}}))
    return m


def test_mismatched_routes_fail_and_absent_stops_are_unavailable(tmp_path, capsys):
    # observed volumes far from modeled: route 1 is 3x, route 2 is a third
    cfg = _cfg(tmp_path, "route_id,boardings\n1,3000\n2,700\n10,500\n")
    out = tmp_path / "validation_result.json"
    rc = cli_main(["validate-model", "--config", str(cfg), "--modeled", str(_modeled(tmp_path)),
                   "--out", str(out)])
    assert rc == 0
    rec = json.loads(out.read_text())
    dims = rec["dimensions"]
    assert dims["route_volume"]["status"] == "failed"
    assert dims["stop_pattern"]["status"] == "unavailable"
    assert set(dims) == {"route_volume", "stop_pattern", "transfer_behavior", "trip_length"}
    assert not any("validated" == k or k.endswith("_validated") for k in rec)
    assert rec["model_status"]["calibration_status"] == "uncalibrated"


def test_matching_routes_pass(tmp_path):
    cfg = _cfg(tmp_path, "route_id,boardings\n1,1010\n2,1990\n10,505\n")
    rec = validation.validate(yaml.safe_load(cfg.read_text())["observed"],
                              yaml.safe_load(cfg.read_text())["thresholds"],
                              json.loads(_modeled(tmp_path).read_text()))
    assert rec["route_volume"]["status"] == "passed"


def test_missing_threshold_is_unavailable_not_passed(tmp_path):
    cfg = _cfg(tmp_path, "route_id,boardings\n1,1000\n2,2000\n10,500\n")
    c = yaml.safe_load(cfg.read_text())
    c["thresholds"]["route_volume_max_pct_rmse"] = None
    rec = validation.validate(c["observed"], c["thresholds"],
                              json.loads(_modeled(tmp_path).read_text()))
    assert rec["route_volume"]["status"] == "unavailable"


def test_committed_config_reports_all_four_unavailable(capsys):
    rec = validation.validate(*(lambda c: (c["observed"], c["thresholds"]))(
        yaml.safe_load(validation.CONFIG.read_text())), {})
    assert {v["status"] for v in rec.values()} == {"unavailable"}
