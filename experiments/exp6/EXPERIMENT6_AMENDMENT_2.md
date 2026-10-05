# Experiment 6 — Amendment 2: how a closure-adjusted receipt encodes its start

*Written 2026-09-29 at the analysis stage. Production, closure and sentinels
were complete. It changes no certified plan, no objective and no record. It
changes how `scripts/exp6_contracts.receipt_for` encodes a closure-adjusted
cell's start.*

## What happened

The first analysis run had every other gate passing:

* record checks 54/54;
* post-closure monotonicity 0/120 violations;
* reference closure clean;
* sentinels 4/4.

The firewall still **refused 33 comparisons** (policy 23, structure 10). Every
refusal named one dimension, `starts_attempted`. The superseded analysis
truncates its refusal text, so this was confirmed by recomputing the
comparisons with the old receipt encoding. The receipt put the **winning** basin into that
opportunity field (`["greedy", "anchor:<digest>"]` for a cell whose best plan
came from a transfer, `["greedy"]` otherwise). Two cells that received the
identical procedure therefore looked as if they had received different
opportunity.

That encoding contradicts the frozen protocol. §11 defines search opportunity
as the procedure: the same independent base start, the same nesting-closure
algorithm, pass ceiling and adjacency construction, the same certifier and the
same convergence rule. Every Exp 6 cell received exactly that procedure. Which
basin won is an **outcome** of it. The firewall schema already carries that as
`winning_start`, which is `Sem.OUTCOME`.

## The correction

* `starts_attempted` (opportunity) is now `start_names + ["exp6_nesting_closure"]`,
  identical for every cell.
* `winning_start` (outcome) is now `"greedy"` or `"anchor:<plan digest>"`.
* Anchor provenance is unchanged and complete:
  * the record's `anchor` block (source record, source cell, plan digest, sha256);
  * the record's `search.start`;
  * the closure ledgers, one receipt per attempted transfer.

The first analysis output is kept, unchanged, as
`outputs/exp6/SUPERSEDED.EXP6_ANALYSIS.first_run_receipt_start_encoding.json`.

After the correction:

* policy comparisons: 25/25 admitted, declaring only `config_digest`;
* structure comparisons: 13/13 admitted, declaring only the network fields.

No other opportunity field differs between any pair. The procedure-level match
is itself checked by the analysis: both networks reached a closure fixed point
(3 passes each) under the same frozen graph and ceiling.

## Why this is not tuning to pass

The refusal was total: it hit every pair whose two cells had different winning
basins. It was not selective. The field it keyed on is not a configuration or
execution difference between cells; the whole point of closure is that
winning basins differ. The fix moves the value to the field the schema defines
for it, and no information is dropped. The contract digests (`EXP6_POLICY`
`393f45ac10d28cb9`, `EXP6_STRUCTURE` `fad14449dc3db7c6`) are unchanged.
