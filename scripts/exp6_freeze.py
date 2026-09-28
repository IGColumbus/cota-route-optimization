#!/usr/bin/env python3
"""Freeze Experiment 6 artifacts. Each subcommand refuses to overwrite.

    exp6_freeze.py catalog     -> outputs/exp6/EXP6_CONSTRAINT_CATALOG.json
    exp6_freeze.py contract    -> outputs/exp6/EXP6_CONTRACT.json
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

OUT = ROOT / "outputs" / "exp6"

SOURCES = {
    "S1": {"title": "FTA Circular C 4702.1B, Title VI Requirements and "
                    "Guidelines for FTA Recipients, Chapter IV",
           "date": "2012-10-01 (current)",
           "url": "https://www.transit.dot.gov/sites/fta.dot.gov/files/docs/FTA_Title_VI_FINAL.pdf",
           "establishes": "fixed-route providers must set quantitative system-"
                          "wide standards (vehicle load, vehicle headway, on-"
                          "time performance, service availability) and, for "
                          "50+ peak vehicles in a 200,000+ UZA, major-service-"
                          "change / disparate-impact / disproportionate-burden "
                          "policies; FTA prescribes no values (the provider "
                          "sets thresholds; examples are illustrative)"},
    "S2": {"title": "49 CFR 37.131(a)(1)", "date": "eCFR current as of 2026-09-22",
           "url": "https://www.ecfr.gov/current/title-49/subtitle-A/part-37/subpart-F/section-37.131",
           "quote": "The entity shall provide complementary paratransit service "
                    "to origins and destinations within corridors with a width "
                    "of three-fourths of a mile on each side of each fixed route."},
    "S3": {"title": "49 CFR 37.131(e)", "date": "eCFR current as of 2026-09-22",
           "url": "https://www.ecfr.gov/current/title-49/subtitle-A/part-37/subpart-F/section-37.131",
           "quote": "The complementary paratransit service shall be available "
                    "throughout the same hours and days as the entity's fixed "
                    "route service."},
    "S4": {"title": "cota.com Title VI page, Codes & Policies, Service Changes, "
                    "Services pages", "date": "retrieved 2026-09-28",
           "urls": ["https://www.cota.com/title-vi/",
                    "https://www.cota.com/about-us/codes-policies/",
                    "https://www.cota.com/servicechanges/",
                    "https://www.cota.com/services/"],
           "establishes": "no published numeric service standard, major-"
                          "service-change definition, or frequent-network "
                          "definition located; COTA values are UNKNOWN to this "
                          "study"},
    "S5": {"title": "config/constraints.yaml service policy (repo)",
           "establishes": "study's own ladder: policy_max_headway_min 60 with "
                          "baseline exception, policy_min_headway_min 5 -- a "
                          "study safeguard since Exp 1"},
}

REGIMES = {
    "R1": {"name": "maximum-headway floor", "parameter": "max_headway",
           "classification": "study safeguard", "cota_anchor": None,
           "sweep": [60.0, 30.0, 20.0], "data_sufficient": True,
           "status": "IMPLEMENTED", "sources": ["S1", "S4", "S5"]},
    "R2": {"name": "OFF share cap", "parameter": "max_off_share",
           "classification": "study safeguard", "cota_anchor": None,
           "sweep": [0.25, 0.10, 0.05], "data_sufficient": True,
           "status": "IMPLEMENTED",
           "note": "share 0 is identical to R1 H=60 (ladder already caps at "
                   "max(60, baseline)) and is not run twice",
           "sources": ["S4", "S5"]},
    "R3": {"name": "span preservation (period granularity)",
           "parameter": "span", "classification": "study safeguard",
           "cota_anchor": None, "sweep": [True], "data_sufficient": True,
           "status": "IMPLEMENTED", "sources": ["S4"]},
    "R4": {"name": "stop-period coverage preservation",
           "parameter": "max_lost_share", "classification": "study safeguard",
           "cota_anchor": None, "sweep": [0.05, 0.01, 0.0],
           "data_sufficient": True, "status": "IMPLEMENTED", "sources": ["S1", "S4"]},
    "R5": {"name": "localized accessibility-loss cap", "parameter": None,
           "classification": "study safeguard (Title VI form would need COTA "
                             "thresholds and demographic data)",
           "cota_anchor": None, "sweep": [], "data_sufficient": False,
           "status": "UNIMPLEMENTABLE_WITH_CURRENT_DATA (Title VI form: no COTA "
                     "thresholds, no ACS minority/low-income data in the "
                     "registry); generic form EXCLUDED -- not implemented "
                     "before freeze (needs per-zone evaluator output inside the "
                     "feasibility predicate)", "sources": ["S1", "S4"]},
    "R6": {"name": "ADA-corridor area preservation (fixed-route safeguard)",
           "parameter": "area_radius_m", "classification":
               "study safeguard borrowing the legal 3/4-mile corridor width "
               "(S2); ADA binds paratransit given the fixed route and does not "
               "require fixed-route preservation",
           "cota_anchor": None, "sweep": [1207.008], "data_sufficient": True,
           "approximation": "route corridors approximated by stop points, "
                            "straight-line distance in EPSG:32617",
           "status": "IMPLEMENTED", "sources": ["S2", "S3"]},
    "R7": {"name": "protected / frequent / core corridors", "parameter": None,
           "classification": None, "cota_anchor": None, "sweep": [],
           "data_sufficient": False,
           "status": "EXCLUDED -- no authoritative COTA frequent-network "
                     "definition located", "sources": ["S4"]},
}


def write_new(path: Path, obj: dict) -> None:
    if path.exists():
        raise SystemExit(f"{path} already frozen; refusing to overwrite")
    import exp45_certify_cell as CC
    CC.atomic_write_json(path, obj)


def catalog() -> None:
    import exp6_grid as G
    doc = {"artifact": "EXP6_CONSTRAINT_CATALOG", "version": "1.0",
           "frozen_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "prose": "EXPERIMENT6_CONSTRAINT_CATALOG.md",
           "prose_sha256": hashlib.sha256(
               (ROOT / "EXPERIMENT6_CONSTRAINT_CATALOG.md").read_bytes()).hexdigest(),
           "bottom_line": "no implemented regime has a documented COTA numeric "
                          "anchor; all are study safeguards; the COTA-compliant "
                          "combined regime is NOT run",
           "sources": SOURCES, "regimes": REGIMES,
           "grid": {n: kw for n, kw in G._RAW},
           "bundles_preregistered": {"B1": "R2 0.10 + R3 + R6",
                                     "B2": "R4 0.01 + R3"},
           "implementation": "src/cota_opt/policy.py (PolicySpec, "
                             "CompiledPolicy); enforced in frequency._feasible"}
    p = OUT / "EXP6_CONSTRAINT_CATALOG.json"
    write_new(p, doc)
    print(p, hashlib.sha256(p.read_bytes()).hexdigest()[:16])


if __name__ == "__main__":
    {"catalog": catalog}[sys.argv[1]]()
