"""Stage the registered raw inputs under ``data/raw/`` (release tooling).

    cota-opt data status                 what is registered, what is missing
    cota-opt data register KEY FILE      register a file you downloaded yourself
    cota-opt data fetch KEY              download from the URL in config/sources.yaml

Every file is checked against the sha256 recorded for its source in
``config/sources.yaml`` before it is registered. A file that does not match is
refused: it is a different version of the data from the one the study used.

The study's five inputs are ``REQUIRED`` below. The COTA feed URL serves
whatever feed COTA currently publishes, so ``fetch cota_gtfs_static`` only
succeeds while that is still the registered version
(``feed_version 2026-MAY-04-BB_20260630``); afterwards the archived file is
needed (docs/REPRODUCE.md §0).
"""
from __future__ import annotations

import tempfile
from pathlib import Path

#: the registered inputs every experiment reads, and their file names in data/raw
REQUIRED = {
    "cota_gtfs_static": "cota.gtfs.zip",
    "lodes_od_oh": "oh_od_main_JT00_2022.csv.gz",
    "lodes_wac_oh": "oh_wac_S000_JT00_2022.csv.gz",
    "lodes_rac_oh": "oh_rac_S000_JT00_2022.csv.gz",
    "cenpop_bg_oh": "CenPop2020_Mean_BG39.txt",
}


def _sources():
    import yaml
    from cota_opt.paths import config_dir
    return yaml.safe_load((config_dir() / "sources.yaml").read_text())["sources"]


def status() -> int:
    from cota_opt.registry import Registry
    reg, src = Registry(), _sources()
    missing = 0
    for key, name in REQUIRED.items():
        rec = reg.get(key)
        want = src[key].get("sha256")
        if rec is None:
            missing += 1
            print(f"MISSING     {key:18s} expected file {name}, sha256 {want}")
        elif rec.sha256 != want:
            print(f"WRONG       {key:18s} registered sha256 {rec.sha256} != {want}")
            missing += 1
        else:
            print(f"REGISTERED  {key:18s} {reg.root / rec.path}")
    print(f"\n{len(REQUIRED) - missing}/{len(REQUIRED)} required inputs registered in {reg.root}")
    return 0 if missing == 0 else 3


def register(key: str, file: str, origin: str | None = None) -> int:
    from cota_opt.registry import Registry, sha256_file
    src = _sources()
    if key not in REQUIRED:
        print(f"unknown or optional source key {key!r}; required keys: {', '.join(REQUIRED)}")
        return 2
    path = Path(file)
    if not path.exists():
        print(f"no such file: {path}")
        return 2
    got, want = sha256_file(path), src[key].get("sha256")
    if got != want:
        print(f"REFUSED {key}: sha256 {got} does not match the registered {want}.\n"
              "This is a different version of the data from the one the study used.")
        return 1
    if path.name != REQUIRED[key]:
        print(f"note: registering under the study's file name {REQUIRED[key]}")
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td) / REQUIRED[key]
            tmp.write_bytes(path.read_bytes())
            rec = Registry().register_file(key, tmp, origin=origin or str(path))
    else:
        rec = Registry().register_file(key, path, origin=origin or str(path))
    print(f"REGISTERED {key}: data/raw/{rec.path} (sha256 {rec.sha256[:16]}…)")
    return 0


def fetch(key: str) -> int:
    import requests
    src = _sources()
    if key not in REQUIRED:
        print(f"unknown or optional source key {key!r}; required keys: {', '.join(REQUIRED)}")
        return 2
    url = src[key]["url"]
    print(f"downloading {url}")
    try:
        resp = requests.get(url, timeout=600, headers={"User-Agent": "cota-opt-research"})
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"download failed ({type(e).__name__}): {e}\n"
              f"Download {url} in a browser and run: cota-opt data register {key} <file>")
        return 1
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td) / REQUIRED[key]
        tmp.write_bytes(resp.content)
        return register(key, str(tmp), origin=url)
