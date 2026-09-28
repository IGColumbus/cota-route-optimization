# Experiment 6 — revised protocol after Exp 5 / D39

*Issued by Ian on 2026-09-28. Stored in the repo so that it survives context
compaction; this text governs Experiment 6 and supersedes the 23 September Exp 6
design wherever later evidence contradicts that design. The wording is kept
close to what was issued. Implementation notes and the frozen parameters live
in `EXPERIMENT6_D39_AMENDMENT.md`, `EXPERIMENT6_CONSTRAINT_CATALOG.md` and
`outputs/exp6/EXP6_CONTRACT.json`.*

## 0. Freeze the current record

Experiment 5 is CLOSED with status `EXP5_MONOTONICITY_FAILURE`.

* Do not rerun it as though the failure had not occurred.
* Do not overwrite its contract, cells, analysis, closeout or registry entry.
* Do not change its status to make the frontier pass.

D39 is preserved exactly:

* N0: 99/99 monotone.
* N4: 12/99 regress, largest 1.7034%.
* N4 H090 is feasible under J100 and scores ≈ 3,219,614.74, against J100's
  3,223,885.95.
* D33-B's 0.0018970% band is not a bound on this phenomenon.

Any use of Exp 5 cells is an additive calibration of the successor search, not
a reopened Experiment 5.

## 1. Networks

Production networks are **N0** (existing local geometry, validated pipeline)
and **N3** (`add_stop-010#22c4c35ac5b2`, built with the Exp 4A addendum's
validated construction).

N4 is not an Exp 6 production network. It is used ONLY for the D39 preflight.
The reason is recorded prospectively in the amendment. Exp 4 and Exp 5 records
are not altered.

## 2. Freeze an amendment and contract before the first production score

The contract freezes at least:

* N0/N3 identities and content digests;
* Model B / same-route evaluator; λ = 2;
* the EXP4N common 100/100 envelope, with its rounded digest and exact IEEE-754
  fingerprint;
* the source/evaluator digest;
* max rounds 120, N_KEYS 8, K_RUNGS 3; convergence mandatory;
* policy-cell definitions, the constraint-catalog digest and the nesting
  relationships;
* the start-closure algorithm and stop statuses;
* a treatment-independent base start;
* exact firewall declarations;
* no cross-network sharing of plans or path sets.

Never call the result globally optimal.

## 3. D39 preflight

Extend the validated block certifier, minimally and backwards-compatibly, to
accept an explicit feasible anchor plan. Do not reimplement the scoring
pipeline.

* **A. Default equivalence.** The default invocation must reproduce N4
  J100/EXP4N bit-exactly: objective 3223885.947526011, plan 898b95fd93c33414,
  21 rounds, converged, entire trajectory. It must also reproduce the N3
  matched-contract control and the N0 reference. Otherwise
  `EXP6_PIPELINE_EQUIVALENCE_FAILURE`, STOP.
* **B. Anchor semantics.**
  * The anchor must be a real plan on the target network.
  * It is tested against the target cell's complete feasibility contract, and
    infeasible anchors are refused, not repaired.
  * The anchor's digest and provenance are recorded.
  * The search starts from the anchor.
  * The result may not be worse than the anchor; a violation is a hard error.
* **C. Canary.** Use the Exp 5 N4 H090 plan as an anchor under N4 J100. The
  result must be ≤ the H090 objective. Test at least one larger failure too,
  e.g. H090 under H110. Record the outcome in `EXPERIMENT6_D39_PREFLIGHT.md` and
  `outputs/exp6/preflight/`. Failure is `EXP6_D39_PREFLIGHT_FAILURE`, STOP.

## 4–5. Nesting closure

Every cell keeps its independent/default greedy solve as its INITIAL solve.
Then, for each network independently:

1. Run every policy cell from the normal independent greedy start and keep it
   as `initial`.
2. Build the partial order of the cells from their actual mathematical feasible
   sets. A is tighter than B only where every policy constraint in B is equal to
   or weaker than A's and all non-policy mathematics are identical. Assert this
   from the frozen constraint objects, never from names.
3. For each adjacent pair (A tighter, B looser): test A's current best plan
   under B's full constraints. If it is feasible, run B's (8, 3) certifier from
   it as an explicit anchor, and keep the better result for B.
4. Reverse direction: if B's current best plan satisfies A's constraints, it is
   a legitimate anchor for A and must be tried.
5. Make deterministic passes over the frozen adjacency graph until one complete
   pass improves nothing in any cell.
6. Freeze the maximum number of passes before production, with generous
   headroom. Hitting that ceiling while still improving is
   `EXP6_START_CLOSURE_FAILURE`, STOP.
7. Every attempted transfer gets a receipt:
   * source and target cell;
   * source plan digest;
   * feasibility result under the target, and the enforced target constraint
     digest;
   * objective before and after;
   * returned plan digest, rounds and convergence;
   * the reason when skipped or refused.

Never replace a reported objective with a min over neighbours. A plan is
admitted under the target mathematics and passed through the target certifier.

## 6. Hard monotonicity

After closure, a looser cell may not have a worse best-known objective than a
nested tighter cell. This is set containment, not a statistical expectation,
and D33-B does not waive it. Any post-closure violation beyond floating-point
equality slack is `EXP6_POLICY_MONOTONICITY_FAILURE`, STOP.

Report initial-greedy monotonicity separately from post-closure monotonicity.

## 7. Reference cells

Each network gets an unconstrained-policy reference cell with the same network,
objective, evaluator, envelope, certifier and closure. Policy cells are never
subtracted from a historical stored number.

The reference takes part in closure. Any constrained plan feasible in it must
be allowed to seed it. A negative policy cost that survives closure is
`EXP6_REFERENCE_CLOSURE_FAILURE`, STOP.

The N3 reference should agree with the matched Exp 4A result when the
mathematical contract is identical. Otherwise document the exact difference.

## 8. Constraint catalog — research before compute

Every regime records:

* its authoritative source and publication/version/date;
* the exact quoted or faithfully paraphrased policy;
* the model parameter that represents it;
* the COTA anchor, if one actually exists, and the sweep values;
* its classification: legal requirement, adopted COTA policy/standard, or study
  safeguard;
* whether current public data is sufficient to enforce it.

The candidate regimes:

* **R1** frequency / maximum-headway floor;
* **R2** maximum share of baseline-served route-periods allowed OFF;
* **R3** span preservation;
* **R4** coverage preservation;
* **R5** localized accessibility-loss cap;
* **R6** ADA/paratransit service-area preservation;
* **R7** protected/frequent/core corridors, if an authoritative COTA definition
  exists.

Never label a study-created threshold as a COTA or Title VI rule. A regime that
cannot be enforced with current data is marked
`UNIMPLEMENTABLE_WITH_CURRENT_DATA`. Freeze the catalog and its digest before
scoring.

## 9. D35 for every policy constraint

Each constraint must be shown to pass just above and fail just below its
measured value, on the same feasibility path used in production. Failure is
`EXP6_CONSTRAINT_INERT`, and that regime stops before production.

## 10. Policy grid

* Sweep each valid regime independently.
* Mark the documented COTA or legal anchor.
* Run one combined "COTA-compliant" regime that uses only constraints with a
  defensible anchor.
* Add interaction combinations only where preregistered from the single-regime
  design, capped at six.
* Do not tune combinations after looking. Finalize the cell list before
  scoring.

## 11. Firewall

Reportable comparisons are firewall-admitted.

* Within a network and a sweep, only the declared policy level may differ.
* N0 vs N3 comparisons also declare the network difference.
* Search opportunity must match: same base start, same closure algorithm, pass
  ceiling and adjacency construction, same certifier and convergence rule.
* Receipts record actual execution, including anchor provenance. There is no
  raw-JSON subtraction outside the admitted path.

## 12. Per-cell output

For every cell, record:

* the INITIAL result: greedy objective, plan digest, rounds/convergence, and
  every metric;
* the CLOSURE result: final objective and plan digest, the winning basin source
  (greedy or transferred anchor), the number of anchor attempts, the pass in
  which the final result was found, the improvement over greedy, and the
  constraint/budget identities;
* served/unserved demand, generalized cost and cost per served trip;
* vehicle-hours used/cap/slack, and all six peak-proxy uses/caps/slack;
* ON/OFF changes;
* block-group gains/losses where a policy needs them;
* binding policy constraints, D35 status and the firewall receipt;
* physical fleet status only as FEASIBLE/INFEASIBLE/UNDECIDABLE from a valid
  instrument.

Never convert peak proxy units into buses.

## 13. Policy cost

Modeled policy cost = closed policy-cell objective − closed unconstrained
reference objective, in absolute and percent terms. It is a MODELED cost under
the declared search closure. Where the two differ, also report the greedy-only
apparent cost against the closure-adjusted cost.

## 14. Acceptance — `EXP6_POLICY_FRONTIER_CERTIFIED` requires all of

* protocol, amendment and catalog frozen before production;
* N0/N3 identities frozen;
* the D39 preflight and the default equivalence canaries pass;
* every included constraint passes D35;
* every production cell converges below 120, and every certified plan satisfies
  its full target constraints;
* the firewall passes, and the nesting graph is frozen and validated;
* closure reaches a fixed point below its ceiling;
* no post-closure monotonicity violations;
* the references absorb every better feasible constrained incumbent;
* order/restart sentinels pass;
* no undeclared evaluator, resource or path-set change.

Otherwise use the specific stop status and preserve partial artifacts.

## 15. Claims

The certified claim is bounded to: *"Under the frozen Model B demand/evaluation
model, common modeled operating resource envelope, and the declared
basin-closure search, imposing policy constraint X changes the best-known
modeled objective by Y relative to the matched unconstrained reference."* It
may be compared on N0 and N3.

It may not claim:

* a global optimum;
* actual buses, deployability, or operating dollars;
* that a study safeguard is COTA policy;
* adjudicated Title VI compliance;
* that N4 is worth implementing.

## 16. Experiment 7 — record now, do not run

* Old F4 (EXP4N beats current geometry) is false. It becomes: "Greenfield N4
  does not beat N3 or N0 under the matched modeled contract; classify the
  sign/magnitude robustness of that null/negative result."
* Old F6 becomes: "policy price on N0 and N3 under the Exp 6 basin-closure
  procedure."
* Exp 7 carries D39: robustness runs may not compare treatment-specific local
  basins as though they were model sensitivity.
* The full Exp 7 amendment is not finalized until Exp 6 results exist.

## 17–18. Operations and order

All OPERATIONS rules carry forward. The order of work:

1. Verify the record.
2. Write the amendment.
3. Add anchor support with equivalence tests.
4. Run the D39 preflight.
5. Build the catalog.
6. Implement the constraints and their D35 tests.
7. Freeze the grid and contract.
8. Smoke-test the exact production invocation.
9. Run the initial solves.
10. Run closure to its fixed point.
11. Run the gates.
12. Write the closeout.
13. Build registry v4.
14. Update README and STATE_OF_PLAY.
15. Fact-check every figure.
16. Only then design the Exp 7 amendment.

Production does not start unless steps 1–8 are clean.
