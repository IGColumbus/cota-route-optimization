"""Release tooling redirects the frozen code's container-only paths to the registry."""
from __future__ import annotations

import cota_opt.baseline as baseline
import cota_opt.harness as harness
import cota_opt.registry as registry
from cota_release import reproduce


def test_container_paths_are_redirected_to_registered_files(monkeypatch, tmp_path):
    monkeypatch.setattr(registry, "data_raw", lambda: tmp_path / "raw")
    reg = registry.Registry()
    names = {"lodes_rac_oh": "oh_rac_S000_JT00_2022.csv.gz",
             "lodes_wac_oh": "oh_wac_S000_JT00_2022.csv.gz",
             "cenpop_bg_oh": "CenPop2020_Mean_BG39.txt"}
    for key, name in names.items():
        f = tmp_path / name
        f.write_text(key)
        reg.register_file(key, f, origin="test")

    seen = {}

    def fake_build_baseline(*a, demand_files=None, **k):
        seen.update(demand_files or {})
        return "built"

    monkeypatch.setattr(baseline, "build_baseline", fake_build_baseline)
    monkeypatch.setattr(harness, "build_baseline", fake_build_baseline)
    monkeypatch.setattr(harness, "DEMAND_FILES", dict(harness.DEMAND_FILES))
    reproduce.redirect_container_paths()   # monkeypatch restores both modules afterwards
    out = baseline.build_baseline(demand_files={
        "rac": f"{reproduce.CONTAINER_UPLOADS}/oh_rac_S000_JT00_2022.csv.gz",
        "other": "/somewhere/else.csv"})
    assert out == "built"
    assert seen["rac"] == reg.path_for("lodes_rac_oh")
    assert seen["other"] == "/somewhere/else.csv"          # non-container paths untouched
    assert harness.DEMAND_FILES["centroids"] == reg.path_for("cenpop_bg_oh")
