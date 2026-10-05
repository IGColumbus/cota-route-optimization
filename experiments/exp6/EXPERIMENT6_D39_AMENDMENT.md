# Experiment 6 — D39 amendment (pre-compute)

*Written and committed 2026-09-28, before any Experiment 6 compute. Additive: the
Experiment 4, 4A and 5 records are not edited. The governing protocol text is
`EXPERIMENT6_PROTOCOL.md`; this note records what changed from the 23 September
Exp 6 design and why, prospectively.*

## 1. What the record says going in (frozen, not reopened)

Experiment 5 is **CLOSED** with status **`EXP5_MONOTONICITY_FAILURE`**
(`EXPERIMENT5_CLOSEOUT.md`; `outputs/CANONICAL_RESULTS_v3.json` → `exp5`).

It established **D39**:

* N0: all 99 nested comparisons monotone.
* N4: 12 of 99 regress. The largest observed regression is **1.7034%**.
* N4 H090 is feasible under the J100 (= EXP4N) envelope. It scores
  **3,219,614.742641489** against EXP4N/J100's **3,223,885.947526011**. EXP4N's
  N4 result is therefore reproducible, but it is not the best known feasible N4
  plan under its own envelope.
* D33-B's 0.0018970% band does **not** bound this. D39 is a start-basin /
  local-optimum failure mode, and a separate one.

Any use of Exp 5 cells below is an **additive calibration of the successor
search procedure**. It is not a reopened Experiment 5.

## 2. Networks — changed from N0/N4 to N0/N3

| | Identity | Construction |
|---|---|---|
| **N0** | COTA existing local geometry, content digest `f0f24936ab06b4ec` | `H.baseline.network` / `H.baseline.tstats`, the validated pipeline used by EXP5 |
| **N3** | Experiment 3 incumbent `add_stop-010#22c4c35ac5b2`, content digest `430aca035c70715b` | `geometry.apply_edits(H.baseline, [mutate.edit_from_record(pool[N3])])` + `contract.validate_applied`, exactly as the Exp 4A addendum built it (`scripts/exp45_certify_cell.build_network`) |

**N4 is not an Exp 6 production network.** It is used **only** for the D39
preflight (§3 of the protocol). The reason is recorded here prospectively:

* the matched EXP4N-contract comparison gives N4 − N3 = **+9.66%**;
* N4 is worse than N0 at every one of the 16 matched Exp 5 resource cells, by
  **8.07–11.59%**;
* D39 was observed specifically on N4;
* the policy question relevant to COTA is now current geometry versus the best
  supported constrained redesign. It is not current geometry versus a dominated
  greenfield candidate.

## 3. What replaces "one greedy start per cell"

Experiment 5 showed that a converged block-local search started from a
treatment-specific greedy start can return a worse plan under a looser feasible
set. Experiment 6 therefore certifies each cell with a two-stage procedure,
frozen in the contract before production:

1. **Initial.** Every cell gets the unchanged EXP4N certification from its own
   independent greedy start. It is kept as `initial`.
2. **Nesting closure.** Over a nesting graph built from the frozen constraint
   objects, not from cell names:
   * every cell's current best plan is tested under each neighbour's **full**
     target constraints;
   * if it is admissible, it is re-certified in the target cell as an
     **explicit anchor** through the same (8, 3) block certifier;
   * this runs in both directions, in deterministic passes, until one whole pass
     improves nothing, under a pass ceiling frozen in advance. Reaching the
     ceiling while still improving is `EXP6_START_CLOSURE_FAILURE`.
3. **Hard monotonicity after closure.** A looser cell may never be worse than a
   nested tighter one. Any violation beyond floating-point equality slack is
   `EXP6_POLICY_MONOTONICITY_FAILURE`, and the experiment stops. D33-B does
   **not** waive it.
4. **References close too.** Each network's unconstrained-policy reference takes
   part in closure. A negative "policy cost" that survives closure is
   `EXP6_REFERENCE_CLOSURE_FAILURE`.

The explicit-anchor extension of the certifier must reproduce every existing
default invocation bit-exactly, or the result is
`EXP6_PIPELINE_EQUIVALENCE_FAILURE`. It must also recover the known D39 basin
on N4, or the result is `EXP6_D39_PREFLIGHT_FAILURE`. Either one stops the run
before any production compute.

## 4. Consequences for Experiment 7 — recorded now, not run

The 23 September Exp 7 design is stale in two places, and it is **not** amended
in full until Exp 6 closes.

* **Old F4:** "EXP4N incumbent beats current geometry". This is **false**.
  Conceptually it becomes: *"Greenfield N4 does not beat N3 or N0 under the
  matched modeled contract; classify the sign/magnitude robustness of that
  null/negative result."*
* **Old F6:** "policy price on N0 and N4". It becomes *"policy price on N0 and
  N3 under the Exp 6 basin-closure procedure."*
* **D39 carries into Exp 7.** Robustness runs may not compare
  treatment-specific local basins as though the differences were model
  sensitivity.
