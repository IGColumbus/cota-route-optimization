#!/usr/bin/env python3
"""Experiment 7 firewall contracts and receipts (canonical builders only).

Every reported Exp 7 comparison is WITHIN one sensitivity level. Contracts are
therefore built per level: the level fixes the objective version (lambda) and
the evaluator (waiting model), and its digest is part of `config_digest`
(exp7_cell.py). A receipt from a different level cannot match another level's
contract, so a cross-level raw-objective comparison is refused by construction.
Cross-level statements are made only about quantities that were each admitted
within their own level (prices, signed differences), see
docs/EXPERIMENT7_AMENDMENT.md section 8.

Contracts per level
-------------------
EXP7_POLICY    F6 track, one network, two policy cells. Only config_digest may
               differ (= digest({base_config, level, policy}); base_config and
               level asserted identical by the analysis).
EXP7_STRUCTURE F6 track, one policy cell, N0 vs N3 (the additional finding).
               Only NETWORK_DIFFERENCES.
EXP7_F4        F4 track (REF-only cells, no policy closure), N4 vs N3 and
               N4 vs N0 (and N3 vs N0 within F4). Only NETWORK_DIFFERENCES.

The F6 and F4 tracks have DIFFERENT search procedures (the F4 track has no
within-level policy closure, so N0/N3 get no opportunity N4 lacks). The
procedure is identity, carried in the solver-policy name, so an F6 receipt can
never be admitted under EXP7_F4 or vice versa.

Receipt encoding follows Experiment 6 Amendment 2: `starts_attempted` is the
procedure every cell received (OPPORTUNITY); `winning_start` names the basin
that won (OUTCOME), with the anchor's provenance in the record and ledger.
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
from exp45_contracts import (K_RUNGS, MAX_ROUNDS, N_KEYS, SEED,  # noqa: E402
                             START_EVALS, START_RESTARTS, START_WIDTH)

CLOSURE_PASS_CEILING = 8
IMPROVE_EPS = 1e-9
PROCEDURE = {"F6": "exp7_combined_closure", "F4": "exp7_cross_level_closure"}


def solver(track: str) -> SolverPolicy:
    stages = ("W=hasse_adjacent_both_directions+X=cross_level_all_pairs"
              if track == "F6" else "X=cross_level_all_pairs")
    return SolverPolicy(
        name=(f"{PROCEDURE[track]}|certify n_keys={N_KEYS} k_rungs={K_RUNGS} "
              f"max_rounds={MAX_ROUNDS}|initial=gen1_greedy_{START_EVALS}x"
              f"{START_RESTARTS}_w{START_WIDTH}|closure={stages}|explicit_anchor|"
              f"pass_ceiling={CLOSURE_PASS_CEILING}|eps={IMPROVE_EPS}|"
              f"allow_off=True|tol=0.0"),
        start_policy=StartPolicy.GREEDY_ONLY, restarts=START_RESTARTS,
        evaluation_ceiling=START_EVALS, candidate_width=START_WIDTH,
        require_convergence=True, seeds=(SEED,))


POLICY_DIFFERENCES = {
    "config_digest":
        "The policy cell IS the treatment. config_digest = digest({base_config, "
        "level, policy spec}); the analysis asserts base_config and level "
        "identical across the two cells, so this admits exactly the declared "
        "policy-level difference and nothing else in configuration."}


def _common(lv, track: str) -> dict:
    return dict(
        stage="certification", objective="lambda_scalarized_path_level",
        objective_version=f"lambda={float(lv.lam)}",
        evaluator=lv.waiting_model,
        envelope="exp4n_common_reference_envelope_exact_0b46d1abc9a80c80",
        pathset_policy="rebuilt_per_network_per_certify_call",
        methodology_generation="gen2", solver=solver(track),
        opportunity_tolerances={}, noise_floor=None,
        pool_version=(f"exp7-{track}-level-{lv.name}-{lv.digest}-networks-"
                      + ("N0-N3" if track == "F6" else "N0-N3-N4")))


def contracts_for(lv) -> dict[str, ExperimentContract]:
    return {
        "EXP7_POLICY": ExperimentContract(
            experiment="exp7", version="7.0-policy-within-network-within-level",
            allowed_treatment_differences=frozenset(POLICY_DIFFERENCES),
            justifications=dict(POLICY_DIFFERENCES), **_common(lv, "F6")),
        "EXP7_STRUCTURE": ExperimentContract(
            experiment="exp7", version="7.0-structure-at-matched-policy-and-level",
            allowed_treatment_differences=frozenset(NETWORK_DIFFERENCES),
            justifications=dict(NETWORK_DIFFERENCES), **_common(lv, "F6")),
        "EXP7_F4": ExperimentContract(
            experiment="exp7", version="7.0-f4-reference-cells-matched-procedure",
            allowed_treatment_differences=frozenset(NETWORK_DIFFERENCES),
            justifications=dict(NETWORK_DIFFERENCES), **_common(lv, "F4")),
    }


METRIC_FIELDS = ("generalized_cost", "unserved_demand", "served_demand",
                 "gc_per_served_trip", "revenue_veh_hours", "peak_vehicles")


def receipt_for(rec: dict, contract: ExperimentContract,
                track: str | None = None) -> ExecutionReceipt:
    """Receipt from the FINAL (closure-adjusted) record of an Exp 7 cell.

    `track` is the track the record is being USED in. It must be given for
    Exp 6 records imported at BASE (they carry no track field); for Exp 7
    records it must agree with the record's own field."""
    own = rec.get("track")
    if track is None:
        if own is None:
            raise ValueError("record has no track; pass the track it is used in")
        track = own
    elif own is not None and own != track:
        raise ValueError(f"record is {own}, used as {track}")
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
    starts = tuple(audit.get("start_names") or ()) + (PROCEDURE[track],)
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
        starts_attempted=starts, winning_start=won,
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


def contracts_payload(levels) -> dict:
    out = {}
    for lv in levels:
        for n, c in contracts_for(lv).items():
            out[f"{lv.name}/{n}"] = {
                "digest": c.digest, "version": c.version,
                "solver": c.solver.name, "evaluator": c.evaluator,
                "objective_version": c.objective_version,
                "pool_version": c.pool_version,
                "allowed_treatment_differences":
                    sorted(c.allowed_treatment_differences)}
    return out
