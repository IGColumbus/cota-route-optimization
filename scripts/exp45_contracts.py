#!/usr/bin/env python3
"""Firewall contracts for the Experiment 4 original-question addendum and
Experiment 5 -- built with the repository's canonical `ExperimentContract`,
`build_spec` and `ExecutionReceipt`, not hand-rolled.

WHY NEW CONTRACTS RATHER THAN `firewall.exp4.EXP4_CERTIFICATION`
---------------------------------------------------------------
`EXP4_CERTIFICATION.solver` is `policy.CERTIFICATION` -- starts=BOTH, 20
restarts, three seeds -- which describes the Gen1 exchange search. EXP4N did not
certify that way. `exp4_certify.certify` starts from ONE Gen1 solve with
`starts="greedy"`, 20,000 evaluations, 1 restart, width 0, then runs the
(N,K)-block-local exact search to convergence. A receipt claiming 20 restarts
for that execution would be a false receipt, and `admit()` would (correctly)
refuse the real one. So the solver policy below states what certify actually
does, and its parameters are IDENTITY fields: n_keys, k_rungs and max_rounds
live in the policy name, so any difference refuses a comparison.

WHY `compare()` AND NOT `compare_exp4()`
-----------------------------------------
`compare_exp4` adds the Gen2 SearchAllowance check -- an evaluation budget per
decision dimension for the Gen2 exchange search. The block certifier has no
evaluation budget: its entitlement is the neighbourhood definition (n_keys,
k_rungs, max_rounds) and the stopping rule (a full round with no improving
block), which are network-independent and carried as identity in the policy.
EXP4N itself never used `compare_exp4`. The allowance is therefore
not-applicable rather than skipped, and that is recorded in every contract
freeze artifact.

Receipts are built FROM the recorded execution facts of a cell (start audit,
enforced budget, convergence, rounds) -- the same pattern as
`exp3_cell.receipt_from_scored`. One execution may be judged under more than
one comparison contract (frontier vs structure); each judgement builds its own
receipt under its own contract digest, and `admit()` checks that digest.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from cota_opt.firewall import (EventType, ExecutionEvent,  # noqa: E402
                               ExecutionReceipt, ExperimentContract,
                               NETWORK_DIFFERENCES, SolverPolicy, StartPolicy,
                               StopRule, build_spec, digest)

LAM = 2.0
SEED = 20260825
N_KEYS = 8
K_RUNGS = 3
MAX_ROUNDS = 120
START_EVALS, START_RESTARTS, START_WIDTH = 20_000, 1, 0

BLOCK_CERTIFICATION = SolverPolicy(
    name=(f"exp4_certify.certify|n_keys={N_KEYS}|k_rungs={K_RUNGS}|"
          f"max_rounds={MAX_ROUNDS}|start=gen1_greedy_{START_EVALS}x"
          f"{START_RESTARTS}_w{START_WIDTH}|allow_off=True|tol=0.0"),
    start_policy=StartPolicy.GREEDY_ONLY, restarts=START_RESTARTS,
    evaluation_ceiling=START_EVALS, candidate_width=START_WIDTH,
    require_convergence=True, seeds=(SEED,))

_COMMON = dict(
    stage="certification", objective="lambda_scalarized_path_level",
    objective_version=f"lambda={LAM}", evaluator="same_route",
    pathset_policy="rebuilt_per_network_per_certify_call",
    methodology_generation="gen2", solver=BLOCK_CERTIFICATION,
    opportunity_tolerances={}, noise_floor=None)

#: Experiment 4 original question: N3 (Exp 3 constrained redesign) vs N4
#: (EXP4N normalized leader), same envelope, same everything but the network.
EXP4A_MATCHED = ExperimentContract(
    experiment="exp4", version="4A-original-question-v1",
    envelope="exp4n_common_reference_envelope_exact_0b46d1abc9a80c80",
    pool_version="exp4n-matched-networks-v1",
    allowed_treatment_differences=frozenset(NETWORK_DIFFERENCES),
    justifications=dict(NETWORK_DIFFERENCES), **_COMMON)

#: Within one network, across resource cells. Only the caps may differ.
EXP5_RESOURCE_DIFFERENCES = {
    "envelope_digest":
        "The resource cell IS the treatment: the exact IEEE-754 fingerprint "
        "of the hours cap and six peak-proxy caps. Topology, evaluator, "
        "objective, seed, start policy, search policy and path policy must "
        "all still match.",
    "envelope_used_vh":
        "The hours cap enforced by the budget. One of the two declared "
        "treatment axes; it follows from envelope_digest.",
}
EXP5_FRONTIER = ExperimentContract(
    experiment="exp5", version="5.0-model-resource-frontier",
    envelope="exp5_scaled_exp4n_common_envelope",
    pool_version="exp5-networks-N0-N4-v1",
    allowed_treatment_differences=frozenset(EXP5_RESOURCE_DIFFERENCES),
    justifications=dict(EXP5_RESOURCE_DIFFERENCES), **_COMMON)

#: Across networks, at an IDENTICAL resource cell. Only the network may differ.
EXP5_STRUCTURE = ExperimentContract(
    experiment="exp5", version="5.0-structure-at-matched-cell",
    envelope="exp5_scaled_exp4n_common_envelope",
    pool_version="exp5-networks-N0-N4-v1",
    allowed_treatment_differences=frozenset(NETWORK_DIFFERENCES),
    justifications=dict(NETWORK_DIFFERENCES), **_COMMON)

CONTRACTS = {"EXP4A_MATCHED": EXP4A_MATCHED, "EXP5_FRONTIER": EXP5_FRONTIER,
             "EXP5_STRUCTURE": EXP5_STRUCTURE}

METRIC_FIELDS = ("objective", "generalized_cost", "unserved_demand",
                 "served_demand", "gc_per_served_trip", "revenue_veh_hours",
                 "peak_vehicles", "mean_wait_min")


def receipt_for(rec: dict, contract: ExperimentContract) -> ExecutionReceipt:
    """Evidence from a stored cell record, asserting rather than assuming.

    Every field is read from what the execution reported about itself in the
    record the runner wrote: the start audit of the first solve, the budget
    the setup actually enforced, the convergence flag and the round count.
    Nothing is inferred from what was requested.
    """
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
        events.append(ExecutionEvent(
            EventType.START_FALLBACK,
            "no start survived; greedy substituted", "frequency"))
    if audit.get("initial_rejection"):
        events.append(ExecutionEvent(
            EventType.START_REJECTED, str(audit["initial_rejection"]),
            "frequency"))
    conv = bool(rec["outcome"]["converged"])
    term = StopRule.NO_IMPROVING_MOVE if conv else StopRule.EVALUATION_BUDGET
    fx = rec["outcome"]["fitness_EXACT"]
    metrics = {"objective": float(rec["outcome"]["objective_EXACT"]),
               **{k: float(fx[k]) for k in METRIC_FIELDS if k in fx},
               "rounds": float(rec["outcome"]["rounds"]),
               "block_enumerations": float(rec["outcome"]["block_enumerations"])}
    return ExecutionReceipt(
        spec=spec, evaluator_used=str(rec["execution"]["evaluator_used"]),
        objective_used=contract.objective,
        envelope_used_vh=float(rec["resource"]["enforced"]["hours_cap"]),
        pathset_digest=str(rec["execution"].get("pathset_digest", "")),
        code_version=spec.code_version,
        start_policy_requested=StartPolicy.GREEDY_ONLY,
        starts_attempted=tuple(audit.get("start_names") or ()),
        winning_start=str(audit.get("winning_start", "")),
        fallback_occurred=bool(audit.get("forced_greedy_fallback")),
        restarts_requested=START_RESTARTS,
        restarts_completed=int(audit.get("restarts_completed") or 0),
        evaluations_performed=int(audit.get("evaluations") or 0),
        termination=term, converged=conv,
        resumed=False,
        objective=float(rec["outcome"]["objective_EXACT"]),
        metrics=metrics, plan_digest=str(rec["outcome"]["plan_digest"]),
        feasible=bool(rec["resource"]["feasible_under_enforced_caps"]),
        objective_trajectory=tuple(
            float(t["objective"]) for t in rec["outcome"]["round_trajectory"]),
        events=tuple(events), seconds=float(rec["outcome"]["seconds"]),
        at=str(rec.get("written_utc", "")))


def contracts_payload() -> dict:
    out = {}
    for name, c in CONTRACTS.items():
        out[name] = {
            "digest": c.digest, "experiment": c.experiment,
            "version": c.version, "stage": c.stage,
            "objective": c.objective, "objective_version": c.objective_version,
            "evaluator": c.evaluator, "envelope": c.envelope,
            "pathset_policy": c.pathset_policy, "pool_version": c.pool_version,
            "methodology_generation": c.methodology_generation,
            "solver": {"name": c.solver.name,
                       "start_policy": c.solver.start_policy.value,
                       "restarts": c.solver.restarts,
                       "evaluation_ceiling": c.solver.evaluation_ceiling,
                       "candidate_width": c.solver.candidate_width,
                       "require_convergence": c.solver.require_convergence,
                       "seeds": list(c.solver.seeds)},
            "allowed_treatment_differences": sorted(
                c.allowed_treatment_differences),
            "justifications": dict(sorted(c.justifications.items())),
            "search_allowance": (
                "NOT APPLICABLE: firewall.exp4.EXP4_ALLOWANCE is an evaluation "
                "budget for the Gen2 exchange search. The block certifier's "
                "entitlement is n_keys/k_rungs/max_rounds plus the "
                "no-improving-round stop rule, network-independent and carried "
                "as identity in the solver policy name. EXP4N never used "
                "compare_exp4 either."),
        }
    return out
