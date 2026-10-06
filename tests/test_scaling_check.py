"""scripts/scaling_check.py compares array-task records with the serial records bit-exactly."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("scaling_check", ROOT / "scripts" / "scaling_check.py")
sc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sc)


def _rec(obj="100.5", digest="abc", traj=(3.0, 2.0)):
    return {"outcome": {"objective_EXACT": obj, "plan_digest": digest, "rounds": 1,
                        "converged": True, "fitness_EXACT": {"generalized_cost": "1.0"},
                        "round_trajectory": [{"objective": t} for t in traj],
                        "seconds": 10.0},
            "resource": {"requested": {"hours_multiplier": 0.75, "peak_multiplier": 1.0}}}


def test_compare_identical_mismatch_and_missing(tmp_path, monkeypatch):
    serial, array = tmp_path / "serial", tmp_path / "array"
    serial.mkdir()
    array.mkdir()
    for name in ("N0_A", "N0_B", "N0_C"):
        (serial / f"{name}.json").write_text(json.dumps(_rec()))
    monkeypatch.setattr(sc, "CELLS", serial)
    (array / "N0_A.json").write_text(json.dumps(_rec()))
    (array / "N0_B.json").write_text(json.dumps(_rec(traj=(3.0, 2.0000001))))
    r = sc.compare(array, ["N0_A", "N0_B", "N0_C"])
    by = {c["cell"]: c for c in r["cells"]}
    assert by["N0_A"]["status"] == "IDENTICAL"
    assert by["N0_B"]["status"] == "MISMATCH"
    assert by["N0_B"]["differing_fields"] == ["round_trajectory"]
    assert by["N0_C"]["status"] == "MISSING"
    assert r["status"] == "FAIL"


def test_parse_cell_reads_committed_multipliers(tmp_path, monkeypatch):
    (tmp_path / "N0_H075.json").write_text(json.dumps(_rec()))
    monkeypatch.setattr(sc, "CELLS", tmp_path)
    assert sc.parse_cell("N0_H075") == ("N0", 0.75, 1.0)


def test_default_cells_exist_in_committed_records():
    for name in sc.DEFAULT_CELLS:
        assert (sc.CELLS / f"{name}.json").exists()
