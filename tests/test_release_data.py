"""`cota-opt data register` refuses files that are not the registered version."""
from __future__ import annotations

import hashlib

import cota_opt.registry as registry
from cota_release import data


def _patch(monkeypatch, tmp_path, key, payload):
    monkeypatch.setattr(registry, "data_raw", lambda: tmp_path / "raw")
    sha = hashlib.sha256(payload).hexdigest()
    monkeypatch.setattr(data, "_sources", lambda: {key: {"sha256": sha, "url": "x"}})


def test_register_accepts_matching_file_under_study_name(monkeypatch, tmp_path):
    payload = b"GEOID,POP\n1,2\n"
    _patch(monkeypatch, tmp_path, "cenpop_bg_oh", payload)
    f = tmp_path / "download.txt"
    f.write_bytes(payload)
    assert data.register("cenpop_bg_oh", str(f)) == 0
    rec = registry.Registry().get("cenpop_bg_oh")
    assert rec.path == "cenpop_bg_oh/CenPop2020_Mean_BG39.txt"


def test_register_refuses_other_version(monkeypatch, tmp_path):
    _patch(monkeypatch, tmp_path, "cenpop_bg_oh", b"the registered bytes")
    f = tmp_path / "CenPop2020_Mean_BG39.txt"
    f.write_bytes(b"a newer release")
    assert data.register("cenpop_bg_oh", str(f)) == 1
    assert registry.Registry().get("cenpop_bg_oh") is None


def test_register_rejects_unknown_key(tmp_path):
    assert data.register("not_a_source", str(tmp_path)) == 2
