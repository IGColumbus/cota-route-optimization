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


def _nesting_falsification(net: str, cat: str, n_samples: int = 3000) -> dict:
    """Numerical falsification check of every strict implication on the real
    network: random plans (baseline headways with route-periods switched OFF
    at several rates); for every strict pair (A tighter than B) no sample may
    satisfy A and violate B. Not a proof -- the proof is the parameter-wise
    argument in PolicySpec.at_least_as_tight_as -- but a check that the
    compiled objects agree with it on this network."""
    import math
    import numpy as np
    from pyproj import Transformer
    import exp45_certify_cell as CC
    import exp6_grid as G
    st = CC.boot()
    netw, _, _ = CC.build_network(net, st)
    pre = json.loads((OUT / "d35" / f"{net}.json").read_text())
    base = {tuple(k.split("|", 1)): (math.inf if v is None else float(v))
            for k, v in pre["baseline_headways"].items()}
    keys = sorted(base)
    tr = Transformer.from_crs("EPSG:4326", st["H"].assumptions["crs"]["projected"],
                              always_xy=True)
    xy = {s_: tr.transform(v.lon, v.lat) for s_, v in netw.stops.items()}
    sp = G.specs(cat)
    comp = {c: (None if s_.is_empty else
                s_.compile(keys, base, netw.route_stops, xy))
            for c, s_ in sp.items()}
    h = G.hasse(sp)
    rng = np.random.default_rng(20260928)
    b = np.array([base[k] for k in keys])
    bad = []
    for t in range(n_samples):
        rate = [0.0, 0.01, 0.03, 0.08, 0.2, 0.5][t % 6]
        v = b.copy()
        off = rng.random(len(v)) < rate
        v[off] = math.inf
        lng = (~off) & np.isfinite(b) & (rng.random(len(v)) < 0.2)
        v[lng] = np.maximum(v[lng], rng.choice([20., 30., 45., 60.], lng.sum()))
        ok = {c: (0.0 if cp is None else cp.violation(v)) == 0.0
              for c, cp in comp.items()}
        for a_, b_ in h["strict_pairs"]:
            if ok[a_] and not ok[b_]:
                bad.append([t, a_, b_])
    return {"network": net, "samples": n_samples,
            "counterexamples": bad[:20], "n_counterexamples": len(bad)}


def contract() -> None:
    import exp45_certify_cell as CC
    import exp5_model_resource as MR
    import exp6_contracts as K
    import exp6_grid as G
    from cota_opt.exp3_cell import code_version
    from cota_opt.exp4_certify import CERTIFICATION_DIGEST
    cat_p = OUT / "EXP6_CONSTRAINT_CATALOG.json"
    cat = hashlib.sha256(cat_p.read_bytes()).hexdigest()[:16]
    pre = OUT / "preflight"
    eq = {n: json.loads((pre / "final_equivalence" / f).read_text())["outcome"]
          for n, f in (("N4", "N4_J100_default.json"),
                       ("N3", "N3_J100_default.json"),
                       ("N0", "N0_J100_default.json"))}
    d39 = {n: json.loads((pre / "d39" / f).read_text())
           for n, f in (("J100", "N4_J100_anchor_H090.json"),
                        ("H110", "N4_H110_anchor_H090.json"))}
    d35 = {n: json.loads((OUT / "d35" / f"{n}.json").read_text())
           for n in G.NETWORKS}
    for n, d in d35.items():
        assert d["all_pass"], f"D35 failed on {n}"
    st = CC.boot()
    nets = {}
    for n in G.NETWORKS:
        _, _, ident = CC.build_network(n, st)
        nets[n] = ident
    sp = G.specs(cat)
    h = G.hasse(sp)
    fals = {n: _nesting_falsification(n, cat) for n in G.NETWORKS}
    for n, f in fals.items():
        assert f["n_counterexamples"] == 0, f"nesting counterexample on {n}"
    base = MR.load_base()
    doc = {
        "artifact": "EXP6_CONTRACT", "version": "6.0",
        "frozen_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "protocol": "EXPERIMENT6_PROTOCOL.md", "amendment":
            "EXPERIMENT6_D39_AMENDMENT.md",
        "networks": {n: {k: nets[n][k] for k in (
            "state_key", "state_digest", "construction", "network_label")}
            for n in G.NETWORKS},
        "N4": "not a production network; used only for the D39 preflight",
        "evaluator": "same_route (Model B)", "lam": 2.0,
        "envelope": {"rounded_envelope_digest": base.rounded_envelope_digest,
                     "exact_fingerprint": base.exact_fingerprint,
                     "hours_cap": repr(base.hours_cap),
                     "peak_proxy_caps": {p: repr(v) for p, v in
                                         base.peak_proxy_caps.items()},
                     "tolerance": 0.0, "semantics": "solver peak-concurrency "
                     "proxy, not fleet"},
        "certifier": {"function": "cota_opt.exp4_certify.certify",
                      "n_keys": 8, "k_rungs": 3, "max_rounds": 120,
                      "convergence_mandatory": True,
                      "certification_digest": CERTIFICATION_DIGEST,
                      "base_start": "Gen1 greedy 20000/1/0 built under the "
                                    "cell's own constraints (policy-feasible "
                                    "minimum-service repair first); treatment-"
                                    "independent procedure",
                      "explicit_anchor": "certify(anchor=...): refused unless "
                                         "a real plan on the network, exact "
                                         "ladder rungs, admissible under the "
                                         "target's full constraints; result "
                                         "never worse than the anchor"},
        "code": {"code_version": code_version(),
                 "src_cota_opt_content_digest": CC.src_content_digest(),
                 "runner_sha256": {n: CC.sha256_file(ROOT / "scripts" / n)[:16]
                                   for n in ("exp6_cell.py", "exp6_grid.py",
                                             "exp6_run.py", "exp6_contracts.py",
                                             "exp45_certify_cell.py",
                                             "exp45_contracts.py",
                                             "exp5_model_resource.py")}},
        "catalog": {"path": str(cat_p.relative_to(ROOT)), "digest": cat},
        "cells": {c: {"spec": s_.payload(), "digest": s_.digest}
                  for c, s_ in sp.items()},
        "canonical_order": [list(x) for x in __import__("exp6_run").canonical()],
        "nesting": {**h, "rule": "A tighter than B iff A's PolicySpec implies "
                    "every constraint of B (PolicySpec.at_least_as_tight_as) "
                    "and not vice versa; same network, same envelope, same "
                    "evaluator", "numerical_falsification": fals},
        "closure": {"pass_ceiling": K.CLOSURE_PASS_CEILING,
                    "algorithm": "scripts/exp6_run.py closure (docstring)",
                    "improvement_eps": 1e-9,
                    "no_cross_network_sharing": True},
        "monotonicity": {"rule": "post-closure, for every strict pair (A "
                         "tighter than B) obj(B) <= obj(A) + 1e-9 * |obj(A)|",
                         "failure": "EXP6_POLICY_MONOTONICITY_FAILURE",
                         "d33b_does_not_waive": True},
        "reference": {"cell": "REF", "rule": "after closure no policy cell "
                      "may beat REF on the same network", "failure":
                      "EXP6_REFERENCE_CLOSURE_FAILURE"},
        "firewall": K.contracts_payload(),
        "sentinels": [list(x) for x in __import__("exp6_run").SENTINELS],
        "preflight": {
            "default_equivalence": {n: {k: o[k] for k in (
                "objective_EXACT", "plan_digest", "rounds", "converged")}
                for n, o in eq.items()},
            "d39": {n: {"status": d["status"],
                        "objective": d.get("outcome", {}).get("objective_EXACT"),
                        "anchor_objective": d.get("search", {}).get(
                            "start", {}).get("anchor_objective"),
                        "rounds": d.get("outcome", {}).get("rounds")}
                    for n, d in d39.items()},
            "d35": {n: {r: v["verdict"] for r, v in d["regimes"].items()}
                    for n, d in d35.items()}},
        "statuses": ["EXP6_POLICY_FRONTIER_CERTIFIED",
                     "EXP6_PIPELINE_EQUIVALENCE_FAILURE",
                     "EXP6_D39_PREFLIGHT_FAILURE", "EXP6_CONSTRAINT_INERT",
                     "EXP6_START_CLOSURE_FAILURE",
                     "EXP6_POLICY_MONOTONICITY_FAILURE",
                     "EXP6_REFERENCE_CLOSURE_FAILURE",
                     "EXP6_ORDER_DEPENDENCE_FAILURE",
                     "EXP6_CONVERGENCE_FAILURE",
                     "EXP6_INFEASIBLE_CERTIFIED_PLAN",
                     "EXP6_INSTRUMENTATION_FAILURE"],
        "claims": {"permitted": "Under the frozen Model B demand/evaluation "
                   "model, common modeled operating resource envelope, and the "
                   "declared basin-closure search, imposing policy constraint X "
                   "changes the best-known modeled objective by Y relative to "
                   "the matched unconstrained reference.",
                   "prohibited": ["global optimum", "buses or fleet",
                                  "deployability", "operating dollars",
                                  "study safeguard presented as COTA policy",
                                  "Title VI compliance adjudicated",
                                  "N4 worth implementing"]},
    }
    p = OUT / "EXP6_CONTRACT.json"
    write_new(p, doc)
    blob = p.read_bytes()
    print(p, hashlib.sha256(blob).hexdigest()[:16],
          {n: c["digest"] for n, c in doc["firewall"].items()})


if __name__ == "__main__":
    {"catalog": catalog, "contract": contract}[sys.argv[1]]()
