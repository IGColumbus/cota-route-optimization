#!/usr/bin/env python3
"""Freeze outputs/exp5/EXP5_CONTRACT.json before the first production cell.

Refuses to overwrite an existing freeze. Everything a production cell may vary
(the 16 cells' exact caps) and everything it may not (networks, solver,
starts, path policy, evaluator, objective, seed, code, runner) is written down
here, with digests, before any production number exists.
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

import exp45_certify_cell as CC  # noqa: E402
import exp45_contracts as C  # noqa: E402
import exp5_model_resource as MR  # noqa: E402
import exp5_run as RUN  # noqa: E402

D33B_BAND_PCT = 0.0018970


def main() -> int:
    out = RUN.CONTRACT
    if out.exists():
        raise SystemExit(f"{out} already frozen; a new freeze needs a new "
                         f"version and a recorded reason")
    pre = [json.loads((ROOT / p).read_text()) for p in sys.argv[1:]]
    for p in pre:
        assert p["reach_test_d35"]["verdict"] == "PASS", p["network"]
        assert p["outcome"]["converged"] and p["outcome"]["rounds"] < 120
    from cota_opt.exp3_cell import code_version
    from cota_opt.exp4_certify import CERTIFICATION_DIGEST
    st = CC.boot()
    nets = {}
    for n in RUN.NETWORKS:
        _, _, ident = CC.build_network(n, st)
        nets[n] = {k: ident[k] for k in ("state_key", "state_digest",
                                         "cardinality", "construction",
                                         "network_label")}
    nets["N4"]["exp4n_result"] = str(RUN.EXP4N_N4.relative_to(ROOT))
    nets["N0"]["definition"] = (
        "COTA existing local geometry (H.baseline.network), validated path, "
        "peak express locked (lock_classes=('peak_express',)) exactly as the "
        "frozen model requires for every network")
    nets["N3"] = {"status": "NOT AN EXPERIMENT 5 NETWORK"}
    base = MR.load_base()
    grid = MR.grid(base)
    pairs = MR.nested_pairs(grid)
    lst = RUN.canonical()
    runner = {n: CC.sha256_file(ROOT / "scripts" / n)[:16] for n in (
        "exp45_certify_cell.py", "exp45_contracts.py", "exp5_model_resource.py",
        "envelope_fingerprint.py", "exp5_run.py", "exp5_freeze_contract.py")}
    doc = {
        "artifact": "EXP5_CONTRACT", "version": "5.0",
        "frozen_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "question": ("Modeled operating-resource frontier: how the certified "
                     "objective of a FIXED network responds to revenue "
                     "vehicle-hours and to the six-period solver peak-"
                     "concurrency proxy, separately and jointly. Frequency "
                     "and ON/OFF only; geometry fixed per network."),
        "retired": MR.RETIRED,
        "retired_premises": [
            "hours are slack (36-37% used) -- measured on legacy endogenous-"
            "cap plans; EXP4N N4 uses 2517.0171064814813 of "
            "2517.1833333333334 h (99.9934%)",
            "Arm B hours-only predicted null",
            "30/35/40% hours service cuts",
            "block-derived physical fleet as the peak axis; the 1.307 factor",
        ],
        "contracts": {k: v for k, v in C.contracts_payload().items()
                      if k.startswith("EXP5_")},
        "comparison_rules": {
            "within_network_across_cells": "EXP5_FRONTIER (only envelope "
                                           "fields may differ)",
            "across_networks": "EXP5_STRUCTURE, IDENTICAL cell only",
        },
        "networks": nets,
        "resource_axes": {
            "hours": MR.HOURS_SEMANTICS, "peak": MR.PEAK_SEMANTICS,
            "peak_instrument": MR.PEAK_INSTRUMENT,
            "scaling_rule": MR.SCALING_RULE, "tolerance": 0.0,
            "base": {"rounded_envelope_digest": base.rounded_envelope_digest,
                     "exact_fingerprint": base.exact_fingerprint,
                     "hours_cap": repr(base.hours_cap),
                     "peak_proxy_caps": {p: repr(base.peak_proxy_caps[p])
                                         for p in MR.PERIODS}},
            "not": "physical vehicles, fleet or buses; no per-bus figure is "
                   "derivable from this experiment",
        },
        "levels": list(MR.LEVELS),
        "cells": [c.payload() | {"arm": c.arm} for c in grid],
        "nested_pairs": [[a.id, b.id] for a, b in pairs],
        "canonical_order": [[n, c.id] for n, c in lst],
        "sharding": "index % 2 over the complete canonical list; one fresh "
                    "subprocess per cell",
        "solver": {"certify_call": "cota_opt.exp4_certify.certify",
                   "lam": C.LAM, "seed": C.SEED, "n_keys": C.N_KEYS,
                   "k_rungs": C.K_RUNGS, "max_rounds": C.MAX_ROUNDS,
                   "allow_off": True, "waiting_model": "same_route",
                   "contract_digest_arg": CERTIFICATION_DIGEST,
                   "start": "gen1 greedy 20000/1/0 inside certify, per cell; "
                            "treatment-independent; NO warm start across "
                            "cells",
                   "pathsets": "rebuilt per certify call (one "
                               "_CandidatePathsets scope); no cross-cell "
                               "sharing"},
        "gates": {
            "reproduction": "N4 J100 must equal EXP4N production_mr120 "
                            "bit-exactly (objective, plan digest, rounds, "
                            "converged, trajectory) else "
                            "EXP5_REPRODUCTION_FAILURE",
            "reference": "N0 J100 is a NEW reference cell (no prior value); "
                         "re-run as the N0 sentinel/control",
            "reach_D35": "every cell runs the reach test: hours cap and the "
                         "most-utilized period's peak cap each moved to "
                         "usage x (1 +/- 1e-6) must flip admissibility, else "
                         "EXP5_CONSTRAINT_INERT",
            "enforced_budget": "exactly one budget per cell, bit-equal to "
                               "the cell's caps, else EXP5_CONSTRAINT_INERT",
            "convergence": "converged and rounds < 120 else "
                           "EXP5_CONVERGENCE_FAILURE",
            "feasibility": "certified plan within enforced caps (x(1+1e-9)) "
                           "else EXP5_INFEASIBLE_CERTIFIED_PLAN",
            "monotonicity": {
                "check": "for every nested (looser, tighter) pair on one "
                         "network: the tighter cell's realized plan usage "
                         "fits the looser caps, so obj(looser) <= "
                         "obj(tighter) is required",
                "band_pct": D33B_BAND_PCT,
                "band_source": "D33-B (local lower bound; veto-only)",
                "within_band_regression": "UNRESOLVED",
                "above_band_regression": "EXP5_MONOTONICITY_FAILURE"},
            "order_invariance": {
                "sentinels_reversed_order": [list(s) for s in RUN.SENTINELS],
                "rule": "each sentinel must equal its production cell "
                        "bit-exactly (objective, plan digest, rounds) else "
                        "EXP5_ORDER_DEPENDENCE_FAILURE"},
        },
        "blocking": "DIAGNOSTIC ONLY: FEASIBLE / INFEASIBLE / UNDECIDABLE at "
                    "analysis time; never filters, ranks or gates a cell",
        "marginals": "three separate units -- objective per revenue "
                     "vehicle-hour (Arm B), objective per proxy unit at the "
                     "binding period (Arm C), objective per joint 1% scale "
                     "(Arm A); finite differences between adjacent levels "
                     "only; no per-bus figure; no knee claimed",
        "record_schema": "exp45_cell/v1 (identity, search, resource "
                         "{requested, enforced, used, slack, utilization_pct, "
                         "binding, feasible}, outcome {objective, fitness, "
                         "plan (null=OFF), rounds, trajectory}, execution "
                         "{start_audit, evaluator, pathset_digest}, "
                         "provenance, reach_test_d35)",
        "statuses": ["EXP5_FRONTIER_CERTIFIED", "EXP5_REPRODUCTION_FAILURE",
                     "EXP5_CONSTRAINT_INERT", "EXP5_CONVERGENCE_FAILURE",
                     "EXP5_INFEASIBLE_CERTIFIED_PLAN",
                     "EXP5_MONOTONICITY_FAILURE",
                     "EXP5_ORDER_DEPENDENCE_FAILURE",
                     "EXP5_INSTRUMENTATION_FAILURE", "UNRESOLVED"],
        "preflight": [{"network": p["network"], "cell": p["cell_id"],
                       "objective_EXACT": p["outcome"]["objective_EXACT"],
                       "plan_digest": p["outcome"]["plan_digest"],
                       "reach": p["reach_test_d35"]["verdict"]} for p in pre],
        "code": {"code_version": code_version(),
                 "src_cota_opt_content_digest": CC.src_content_digest(),
                 "runner_sha256": runner},
    }
    blob = json.dumps(doc, indent=1, sort_keys=False)
    doc["contract_file_sha256"] = hashlib.sha256(blob.encode()).hexdigest()
    CC.atomic_write_json(out, doc)
    print(out, doc["contracts"]["EXP5_FRONTIER"]["digest"],
          doc["contract_file_sha256"][:16])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
