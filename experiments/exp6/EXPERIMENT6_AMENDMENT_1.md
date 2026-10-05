# Experiment 6 — Amendment 1: a policy cell can have an empty feasible set

*Written 2026-09-29 during the initial-solve stage, after 7 of 28 initial cells
had certified. It changes no certified number and no frozen parameter. It adds
the handling for an outcome the contract did not anticipate.*

## What happened

`N3 / R1_H20` could not start. The Gen1 start raised "minimum-service plan
already exceeds the budget". Under R1 at H = 20, every baseline-served
route-period must stay ON with headway ≤ max(20, baseline). On N3, the plan that
runs every route-period at its longest admissible headway already exceeds the
EXP4N envelope.

This is plausible on N3 in particular, because N3's own baseline plan also
overruns the envelope. The added stop lengthens route 001; the D35 run records
this in `base_plan_trims_to_fit_envelope`.

The driver treated the failure as an error and halted both initial shards, as
designed. Nothing was lost:

* the 7 certified records are intact;
* the trace is kept as `outputs/exp6/initial/TRACE.N3_R1_H20.certifier_start_error.json`.

## The rule added

For a policy made only of per-route-period headway caps (R1), an empty feasible
set is **proven**, not assumed, by `scripts/exp6_infeasible_cell.py`:

1. Every admissible plan gives each route-period a headway no longer than its
   longest admissible rung. The minimum-service plan **M** uses that rung
   everywhere.
2. Vehicle-hours and every period's peak proxy strictly decrease as headway
   increases. So M uses no more of any resource than any admissible plan does.
3. M goes through the production path twice: `solve_on_network → build_setup` with
   the policy attached, then `solve_exact` on a one-rung ladder, then
   `frequency._feasible`:
   * under the envelope, where it must be **refused**;
   * under the same policy with the envelope relaxed ×10, where it must be
     **admitted** with zero policy violation. This shows the refusal comes from
     the envelope and not the policy.

If both hold, the cell is recorded as **`INFEASIBLE_UNDER_ENVELOPE`**, together
with M's usage against every cap. Otherwise it is `INFEASIBILITY_NOT_PROVEN`,
which fails the analysis.

For combinatorial regimes (R2, R3, R4, R6, B1, B2), the policy repair start is
not a proven minimum. A start failure there is **not** treated as emptiness; it
stays an error, and the run stops.

## Consequences, fixed now

* **Closure.** Transfers into or out of an empty cell are receipted as
  `SKIPPED_EMPTY_FEASIBLE_SET`.
* **Monotonicity.** An empty tighter cell is consistent with any looser cell.
  An empty **looser** cell with a feasible tighter cell is a violation.
* **Firewall and policy cost.** An empty cell has no plan, so it gets no
  receipt and no finite policy cost. It is reported as "policy infeasible under
  the modeled envelope". That is a result, not a failure.
* **Code.** `src/cota_opt` is unchanged (digest `b63ae2dba134245e`), as are the
  cell runner (`exp6_cell.py`) and every certified record. Changed are
  `scripts/exp6_run.py` (driver: `ensure` and closure skip),
  `scripts/exp6_analyze.py`, and the new `scripts/exp6_infeasible_cell.py`.
  Their hashes are frozen in
  `outputs/exp6/EXP6_CONTRACT_AMENDMENT_1.json`.
