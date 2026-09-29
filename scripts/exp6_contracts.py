#!/usr/bin/env python3
"""Experiment 6 firewall contracts and receipts (canonical builders only).

Two comparison contracts, both over the SAME search opportunity -- the Exp 6
certification procedure: an independent Gen1-greedy-started (8,3) block
certification per cell, then the preregistered nesting closure with explicit
anchors, under a frozen pass ceiling. That procedure is identity, carried in the
solver-policy name, so a receipt from any other procedure is refused.

* EXP6_POLICY   -- one network, two policy cells. The only permitted difference
                   is `config_digest`, which the Exp 6 runner defines as
                   digest({base_config, policy}) and whose base_config part the
                   analysis asserts identical across every cell. So the
                   difference admitted is exactly the declared policy level.
* EXP6_STRUCTURE -- one policy cell, two networks (N0 vs N3). Only the
                   network fields (`NETWORK_DIFFERENCES`) may differ.

Receipts are built from the FINAL (closure-adjusted) record of a cell, which
names its winning basin (greedy or transferred anchor) and the anchor's
provenance; nothing is inferred from what was requested.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from cota_opt.firewall import (EventType, ExecutionEvent,  # noqa: E402
                               ExecutionReceipt, ExperimentContract,
                               NETWORK_DIFFERENCES, SolverPolicy, StartPolicy,
                               StopRule, build_spec)
from exp45_contracts import (K_RUNGS, LAM, MAX_ROUNDS, N_KEYS, SEED,  # noqa: E402
                             START_EVALS, START_RESTARTS, START_WIDTH)

CLOSURE_PASS_CEILING = 8

EXP6_SEARCH = SolverPolicy(
    name=(f"exp6_basin_closure|certify n_keys={N_KEYS} k_rungs={K_RUNGS} "
          f"max_rounds={MAX_ROUNDS}|initial=gen1_greedy_{START_EVALS}x"
          f"{START_RESTARTS}_w{START_WIDTH}|closure=hasse_adjacent_both_"
          f"directions_explicit_anchor|pass_ceiling={CLOSURE_PASS_CEILING}|"
          f"allow_off=True|tol=0.0"),
    start_policy=StartPolicy.GREEDY_ONLY, restarts=START_RESTARTS,
    evaluation_ceiling=START_EVALS, candidate_width=START_WIDTH,
    require_convergence=True, seeds=(SEED,))

_COMMON = dict(
    stage="certification", objective="lambda_scalarized_path_level",
    objective_version=f"lambda={LAM}", evaluator="same_route",
    envelope="exp4n_common_reference_envelope_exact_0b46d1abc9a80c80",
    pathset_policy="rebuilt_per_network_per_certify_call",
    methodology_generation="gen2", solver=EXP6_SEARCH,
    opportunity_tolerances={}, noise_floor=None,
    pool_version="exp6-networks-N0-N3-v1")

POLICY_DIFFERENCES = {
    "config_digest":
        "The policy cell IS the treatment. config_digest = digest({base_config, "
        "policy spec}); the analysis asserts base_config identical across all "
        "cells, so this admits exactly the declared policy-level difference and "
        "nothing else in configuration."}

EXP6_POLICY = ExperimentContract(
    experiment="exp6", version="6.0-policy-within-network",
    allowed_treatment_differences=frozenset(POLICY_DIFFERENCES),
    justifications=dict(POLICY_DIFFERENCES), **_COMMON)

EXP6_STRUCTURE = ExperimentContract(
    experiment="exp6", version="6.0-structure-at-matched-policy",
    allowed_treatment_differences=frozenset(NETWORK_DIFFERENCES),
    justifications=dict(NETWORK_DIFFERENCES), **_COMMON)

CONTRACTS = {"EXP6_POLICY": EXP6_POLICY, "EXP6_STRUCTURE": EXP6_STRUCTURE}
METRIC_FIELDS = ("generalized_cost", "unserved_demand", "served_demand",
                 "gc_per_served_trip", "revenue_veh_hours", "peak_vehicles")


def receipt_for(rec: dict, contract: ExperimentContract) -> ExecutionReceipt:
    ident = rec["identity"]
    audit = rec["execution"]["start_audit"]
    spec = build_spec(
        contract, state_digest=ident["state_digest"],
        state_key=ident["state_key"], cardinality=int(ident["cardinality"]),
        members=tuple(ident["members"]),
        envelope_digest=rec["resource"]["enforced_exact_fingerprint"],
        config_digest=rec["provenance"]["config_digest"],
        data_digest=rec["provenance"]["data_digest"],
        code_version=rec["provenance"]["code_version"],
        seed=int(rec["search"]["seed"]))
    events = []
    if audit.get("forced_greedy_fallback"):
        events.append(ExecutionEvent(EventType.START_FALLBACK,
                                     "no start survived", "frequency"))
    if audit.get("initial_rejection"):
        events.append(ExecutionEvent(EventType.START_REJECTED,
                                     str(audit["initial_rejection"]), "frequency"))
    st = rec["search"]["start"]
    # OPPORTUNITY is the procedure every cell received: its own independent
    # greedy start plus the frozen nesting closure (Amendment 2). WHICH basin
    # won -- greedy, or a named transferred anchor -- is an OUTCOME, carried
    # in winning_start, with the full anchor provenance in the record and the
    # closure ledger.
    starts = tuple(audit.get("start_names") or ()) + ("exp6_nesting_closure",)
    won = ("anchor:" + st.get("anchor_plan_digest", "")
           if st.get("source") == "anchor" else str(st.get("source", "")))
    o = rec["outcome"]
    conv = bool(o["converged"])
    fx = o["fitness_EXACT"]
    return ExecutionReceipt(
        spec=spec, evaluator_used=str(rec["execution"]["evaluator_used"]),
        objective_used=contract.objective,
        envelope_used_vh=float(rec["resource"]["enforced"]["hours_cap"]),
        pathset_digest=str(rec["execution"].get("pathset_digest", "")),
        code_version=spec.code_version,
        start_policy_requested=StartPolicy.GREEDY_ONLY,
        starts_attempted=starts,
        winning_start=won,
        fallback_occurred=bool(audit.get("forced_greedy_fallback")),
        restarts_requested=START_RESTARTS,
        restarts_completed=int(audit.get("restarts_completed") or 0),
        evaluations_performed=int(audit.get("evaluations") or 0),
        termination=StopRule.NO_IMPROVING_MOVE if conv else StopRule.EVALUATION_BUDGET,
        converged=conv, resumed=False,
        objective=float(o["objective_EXACT"]),
        metrics={"objective": float(o["objective_EXACT"]),
                 **{k: float(fx[k]) for k in METRIC_FIELDS if k in fx},
                 "rounds": float(o["rounds"])},
        plan_digest=str(o["plan_digest"]),
        feasible=bool(rec["resource"]["feasible_under_full_target_constraints"]),
        objective_trajectory=tuple(float(t["objective"])
                                   for t in o["round_trajectory"]),
        events=tuple(events), seconds=float(o["seconds"]),
        at=str(rec.get("written_utc", "")))


def contracts_payload() -> dict:
    out = {}
    for n, c in CONTRACTS.items():
        out[n] = {"digest": c.digest, "version": c.version,
                  "solver": c.solver.name, "envelope": c.envelope,
                  "evaluator": c.evaluator, "objective": c.objective,
                  "objective_version": c.objective_version,
                  "pathset_policy": c.pathset_policy,
                  "allowed_treatment_differences":
                      sorted(c.allowed_treatment_differences),
                  "justifications": dict(sorted(c.justifications.items()))}
    return out
