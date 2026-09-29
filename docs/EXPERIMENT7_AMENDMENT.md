# Experiment 7 — Amendment (post-Experiment 6)

*Written 2026-09-29, after Experiment 6 closed as `EXP6_POLICY_FRONTIER_CERTIFIED`
(master `2d2ac09c`). It supersedes `docs/EXPERIMENT7_AMENDMENT_DRAFT.md`, which
is kept unchanged as history. It amends Ian's 23 September Exp 7 protocol. That
text is kept **separately and verbatim** as
`docs/EXPERIMENT7_PROTOCOL_AS_ISSUED.md` and is not restated here.*

**Status: NOT IN FORCE. Nothing here authorizes production compute.** It comes
into force when the gates in §10 pass and `outputs/exp7/EXP7_CONTRACT.json` is
frozen by `scripts/exp7_freeze.py`.

---

## 0. What this amendment does not supply

As of this writing, the as-issued Exp 7 text is **not in the repository**. Its
content has been requested from Ian. Until that text is committed:

* **Sensitivity dimensions and levels.** The dimensions, their levels, the A8
  retention settings, and any λ, waiting-model, path-model or wider-OD levels
  are **not specified here**. They are not reconstructed from references
  elsewhere (e.g. "the five Exp 7 dimensions", "Class A perturbation A8").
* **Findings F1–F3 and F5.** Carried as issued; not restated.
* **Classification bands.** The magnitude band wording (e.g. what counts as
  "small") is carried as issued and not defined here.

This amendment fixes everything that does **not** depend on those inputs: the
search procedure, the tracks, anchor handling, the numerical and
classification rules, and the firewall. The implementation takes the levels as
a data file (`scripts/exp7_levels.py`). The contract cannot be frozen until
the as-issued levels are entered in that file and named in §8 of this
document (gate G2).

---

## 1. Evidence base: Experiment 6, frozen

Experiment 6 is frozen and not reopened. Its records, closure ledgers, analysis
(`outputs/exp6/EXP6_ANALYSIS.json`) and registry entries
(`outputs/CANONICAL_RESULTS_v4.json`) remain as admitted.

**Closure-adjusted references.** Every Exp 7 baseline number is
closure-adjusted, never greedy-only.

| network | Exp 6 closed REF objective | plan | initial (greedy) REF |
|---|---|---|---|
| N0 | 2,941,892.37 | `aed848588abad24d` | 2,945,632.23 |
| N3 | 2,935,166.03 | `fdec5c5475c73736` | 2,939,912.58 |

**Closure-adjusted policy prices** (from `EXP6_CLOSEOUT_TABLES.md`):

* **N0.** 0 for R2_S25 and R2_S10, up to +0.912% for R1_H20.
* **N3.** 0 for R2_S25 and R2_S10, up to +0.634% for R1_H30. N3 R1_H20 is
  `INFEASIBLE_UNDER_ENVELOPE`: it has no price.

**Historical comparisons are preserved.** Each keeps its own contract, number
and label, and none is silently replaced by Exp 7 arithmetic:

* Exp 4A: Δ43 = +9.66%.
* Exp 5: N4 − N0 from +8.07% to +11.59%.
* Exp 6: policy prices, and N3 − N0 at matched policy.

**If Exp 7 changes a BASE number.** Exp 7 runs a new closure. Cross-level
transfers can therefore reach a better BASE plan than Exp 6 found. If that
happens:

* the result is reported as the **Exp 7 BASE** value, next to the Exp 6 value;
* the difference is labeled a **basin correction** of the Exp 6 number;
* the Exp 6 value is not overwritten.

---

## 2. Findings under test

### F4 — N4 remains worse than N0 and N3

> **Under the matched modeled contract, greenfield N4 does not beat N3 or N0.
> F4 tests whether that negative result holds across the Exp 7 sensitivity
> levels.**

* The test is run on the **F4 track** (§5), with matched search opportunity.
* Classification at each level:
  * `sign`: N4 − N3 > τ and N4 − N0 > τ.
  * `magnitude_stable`: the gap stays within the as-issued band.
* A sign flip is a **finding**, reported as such, and not a failure (§7.4).
* The retired claims (`ordering`, and `beats_noise` against an in-run noise
  floor) stay retired, as in the draft §1.

### F6 — the policy price on N0 and N3

> **The price of each Experiment 6 policy regime, closure-adjusted, at every
> sensitivity level.**

* The full Exp 6 policy graph is kept (§4).
* Classification:
  * `sign` (closure plus nesting guarantee it; a violation is a bug);
  * `magnitude_stable`;
  * `rank_stable`, with ties handled as in §7.2.

### AF1 — additional finding: the small N3-over-N0 advantage (identified here)

Experiment 6 found N3 slightly better than N0 at every matched policy cell
where both are feasible. On closed plans the gap is −0.153% to −0.229% of N0
(REF: −6,726.35, −0.229%), and all 13 comparisons are admitted under
EXP6_STRUCTURE.

This amendment **adds** that result as a separately identified finding. It
was not a preregistered Exp 7 claim, and it is labeled that way wherever it is
reported. At each level it is tested for:

* `sign`: N3 − N0 < −τ;
* `magnitude_stable`.

It is tested under EXP7_STRUCTURE on the **F6 track**, where both networks get
the identical procedure. The cause of the asymmetry has not been separated
(Exp 6 closeout), and AF1 makes no causal claim.

### Objective robustness vs basin-dependent descriptors

Experiment 6 showed a flat, multi-basin objective. Near-equal objectives were
reached by plans with very different descriptive statistics. On N0 REF,
closure moved:

* served demand from 16,527 to 21,144;
* OFF count from 50 to 15;
* GC by +45.3%;

while the objective changed by only −0.127%.

Therefore:

* **Robustness classifications apply only to the objective and to prices or
  differences derived from it.**
* Served demand, generalized cost, GC per served trip and OFF count are
  reported **per basin, as descriptors of the winning plan**. They are never
  given a robustness label. "N4 serves fewer trips" and similar statements
  are not F4 claims.
* Any descriptor change between levels is reported with the plans' digests,
  so a basin change is visible as one.

---

## 3. The search procedure: combined closure

The procedure is implemented in `scripts/exp7_closure.py` (a pure engine,
unit-tested in `tests/test_exp7_closure.py`) and driven by
`scripts/exp7_run.py`.

**Initial stage.** Every (track, level, network, cell) gets an independent,
treatment-independent Gen1-greedy start and an (8,3) block certification,
exactly as in Exp 6.

**Group.** Closure runs per (track, network). There is no cross-network
sharing.

**One pass** consists of two stages, always in this order:

* **W — within-level policy closure** (F6 track only).
  * For each level, in contract order, process each adjacent Hasse edge
    (tighter, looser) in sorted order.
  * Each edge is transferred forward (tighter → looser), then in reverse.
  * This is the Exp 6 procedure, applied level by level.
* **X — cross-level all-pairs.** For each policy (in catalog order), for each
  target level, for each source level ≠ target (both in contract order):
  * the source level's **current best** plan for that policy is transferred
    **directly** to the target level;
  * there is no adjacent-level chain;
  * so a plan never needs to win at an intermediate level to reach another;
    a plan rejected at one level is still offered to every other level.

**Order and state.**

* Candidates are considered in the frozen order above.
* Each candidate reads the current bests at the moment it is considered
  (Gauss–Seidel), so an improvement is visible to later candidates in the same
  pass.
* An interrupted run resumes at its persisted cursor, so receipts, pass count
  and ceiling behavior equal those of an uninterrupted run (tested).

**Fixed point and ceiling.**

* Passes repeat until one complete pass improves nothing in either stage.
  Neither stage alone defines closure.
* The pass ceiling is **8**, as in Exp 6. Exp 6 reached its fixed point in 3
  passes.
* If the ceiling is reached while the last pass still improved, the group
  records **`EXP7_CLOSURE_CEILING_FAILURE`**, which **blocks certification**
  of that group.
* Improvement threshold: a result replaces the target's best only if it is
  lower by more than **ε = 1e-9** (absolute objective units, as in Exp 6).

**Handling of each candidate.** Every candidate gets one ledger receipt. The
engine applies these checks in this order:

| condition | action |
|---|---|
| source cell proven empty | `SKIPPED_EMPTY_SOURCE` |
| target precheck fails (§6) | `REFUSED_INFEASIBLE_UNDER_TARGET` (never repaired) |
| target proven empty but source passes the precheck | `EMPTINESS_CONTRADICTED`, which **blocks** |
| source plan digest equals the target's best | `SKIPPED_IDENTICAL_PLAN` |
| (target cell, plan digest) already certified | `SKIPPED_ALREADY_ATTEMPTED` (certification is deterministic) |
| certifier refuses the anchor | `REFUSED_BY_CERTIFIER` |
| certified | `RAN`, with `improved` true or false |

**BASE reuse.** At BASE, a transfer that Exp 6 already ran (same network,
target cell and anchor plan digest) is imported from `outputs/exp6/closure` by
reference. The BASE initial records are the Exp 6 initial records, imported by
path and sha256. Both are allowed only if:

* `src/cota_opt` is unchanged (`b63ae2dba134245e`); and
* the BASE reproduction canaries pass (§10, G3).

Otherwise BASE is recomputed.

---

## 4. The complete policy graph is kept

* All 14 Exp 6 cells are solved and closed at **every** level: REF,
  R1_H60/H30/H20, R2_S25/S10/S05, R3_SPAN, R4_C05/C01/C00, R6_ADA, B1 and B2.
* The draft's proposed trims are withdrawn. R3, R4_C00, B1, B2, R2_S25 and
  R2_S10 are kept.
* **Consolidation is presentation only.** Cells may share one row only when
  their closed final plans have identical digests **at that level**. Equality
  at BASE is not inherited by any other level.
* **Zero prices** are reported only as §7.1 allows. A cell that was
  non-binding at BASE is not assumed non-binding at another level.
* The target-feasibility check of the closed REF plan under the cell's policy
  is recorded at every level.

---

## 5. F4 track: matched search opportunity

**Why a separate track.** On the F6 track, N0 and N3 REF receive
within-level policy closure: plans arrive from 13 policy cells. N4 has no
policy cells. In Exp 6 that closure moved the REF basin by 0.127–0.161%.
Comparing F6 REF cells with N4 would therefore give N0 and N3 search
opportunity that N4 lacks.

**The F4 track.**

* Cells: REF only, on N0, N3 and N4, at every level.
* Procedure, identical for all three networks:
  * the initial greedy certification;
  * X-stage cross-level all-pairs closure;
  * no W stage.

**Anchor eligibility, frozen before running.**

* **Primary F4 comparison.** Anchors come only from certified plans produced
  inside the F4 track, on the same network, at another level. The rule is the
  same for every network; there is no network-specific difference.
* **N4's D39 calibration is not an F4 baseline.** The D39 preflight results
  (anchored H090 plan: J100 3,207,566.42, H110 3,207,230.83) came from a
  different start rule and remain calibration evidence only.
* **Secondary sensitivity**, reported separately and never mixed into the
  primary result: one extra transfer per network and level, from that
  network's best-known BASE plan from earlier experiments:
  * N0 and N3: the Exp 6 closed REF plans;
  * N4: the D39 H090-anchored J100 plan.

  The import rule is the same for all three networks. The secondary result
  shows how much prior best-known plans move F4. It does not replace the
  primary result.

**Historical rows.** The F4 BASE rows are reported next to the historical
Exp 4A and Exp 5 numbers (§1), each under its own label.

---

## 6. Validating every transferred anchor under its target

**Precheck, done by the driver before any compute:**

* **Representation.** The source plan's route-period key set must equal the
  target network's key set.
* **Policy.** The source plan must pass the target cell's compiled policy.
  This check does not depend on the level: policy constraints do not depend on
  demand, λ, the waiting model or the path model.

**Certifier admission** (`exp4_certify.certify(anchor=…)`, under the
**target** level's harness, λ and waiting model):

* the key set is checked again;
* the one-rung exact admission must pass: resource envelope and policy, on the
  production feasibility path;
* every value must be an exact rung of the full ladder;
* the returned plan's digest must equal the anchor's;
* the anchor is then **re-evaluated under the target objective**, and the
  search starts from it;
* the result is never worse than the anchor.

**Refusals.** A refusal at either step is receipted with its reason. Nothing
is repaired.

**Empty cells (N3 R1_H20 and any other pure-R1 cell).**

* Feasibility is established **at every level** by the Amendment 1 proof,
  re-run through that level's harness (`scripts/exp7_infeasible_cell.py`).
* A certifier start failure is **not** an infeasibility proof. It only
  triggers the proof. `INFEASIBILITY_NOT_PROVEN` halts the run.
* Empty cells have **no finite price**.
* If an admissible plan reaches a cell proven empty, the result is
  `EMPTINESS_CONTRADICTED`, which blocks.

---

## 7. Classification and comparison rules

Implemented in `scripts/exp7_classify.py` and unit-tested.

**τ = 1e-9 absolute objective units.** This is the same number as the closure
threshold, so "equal" means exactly "indistinguishable to the closure".

### 7.1 Prices (within a level, closed values only)

price = (obj(cell) − obj(REF)) / obj(REF).

| class | condition |
|---|---|
| `ZERO` | the cell's final plan digest equals the closed REF's, **and** the REF plan passes the cell's policy at this level |
| `ZERO_DISTINCT_PLAN` | different plan, abs(Δ) ≤ τ, and the REF plan is admissible under the cell |
| `ZERO_NOT_ESTABLISHED` | abs(Δ) ≤ τ, but the target-feasibility check does not support a zero (REF plan inadmissible or not checked). Reported, never presented as "free" |
| `POSITIVE` | Δ > τ; the magnitude band comes from the as-issued text |
| `EXP7_REFERENCE_CLOSURE_FAILURE` | Δ < −τ. Impossible after a correct closure, so it blocks |
| `INFEASIBLE_UNDER_ENVELOPE` | proven empty; price = none |

### 7.2 Ties in rankings

* Competition ranking (1, 2, 2, 4).
* A tie group is anchored at its lowest member. It absorbs members within τ of
  **that member**, or with an identical plan digest to any member. Ties do not
  chain.
* Empty cells are unranked.
* `rank_stable` compares tie-aware ranks.

### 7.3 Feasibility transitions

* `FEASIBLE_TO_INFEASIBLE` and `INFEASIBLE_TO_FEASIBLE` between BASE and a
  level are findings.
* The price at an infeasible level is none. No finite change in price is
  computed across such a transition.

### 7.4 Sign flips

* A strict sign change (`SIGN_FLIP`), or a move into or out of the τ band
  (`TO_TIE` / `FROM_TIE`), of a price, of N4 − N3, N4 − N0 or N3 − N0 is a
  **finding**, never a failure.

### 7.5 Hard monotonicity

* Within each level, over the strict nesting pairs: obj(tighter) ≥
  obj(looser) − τ after closure.
* An empty looser cell next to a feasible tighter cell is a violation.
* Violations block. D33-B does not waive them.

### 7.6 Basin correction vs sensitivity effect

* basin correction = closed(level) − initial(level);
* sensitivity effect = closed(level) − closed(BASE), for prices and signed
  differences only.

The two are always reported separately. A robustness label may use only
closed values.

### 7.7 D33-B

D33-B (0.0018970%) is **veto-only**. It never sets a tolerance, a band or a
tie.

---

## 8. Sensitivity dimensions: coverage and claim bounds

**Levels.** *The as-issued levels are entered here and in
`outputs/exp7/EXP7_LEVELS.json` when received.*

**What the implementation can reach.** The reach preflight
(`scripts/exp7_preflight.py reach`) evaluates one fixed certified plan — the
Exp 6 closed REF — under each knob, through the production path. BASE
reproduces the record bit-exactly. The preflight's instrument levels are
**not** matrix levels.

| dimension | knob | reach level | N0 result |
|---|---|---|---|
| λ | `certify(lam=…)` | `R_LAM1` | REACHES |
| waiting model | `same_route` / `pattern` (common lines) | `R_WAIT_PATTERN` | REACHES |
| waiting parameters | `waiting.schedule_coefficient` | `R_WAITCOEF` | REACHES |
| retention (A8-type) | `path_assignment.cost_retention_zero_min` | `R_RET_ZERO300` | REACHES |
| retention (A8-type) | `path_assignment.cost_retention_floor` | `R_RET_FLOOR0` | REACHES |
| demand scale | OD × 1.5 | `R_SCALE15` | REACHES (GC per served trip unchanged, as predicted by `robustness.scale_od`) |
| period mix | `tilt_periods` toward the peaks | `R_TILT_PEAK` | REACHES |
| wider OD universe | the harness's own LODES pipeline, top-k 40,000 | `R_TOPK40K` | REACHES (40,000 pairs, same total trips) |
| path-set width | `path_assignment.max_paths_per_od` = 2 or 8 | `R_PATHS2`, `R_PATHS8` | **INERT** |
| enumeration scenarios | `path_assignment.n_random_scenarios` = 5 | `R_SCEN5` | **INERT** |
| RAPTOR rounds | `path_assignment.max_rounds` = 4 | `R_ROUNDS4` | pending |
| walk/access radius | `path_assignment.walk_radius_m`, `access_radius_m` | — | **refused**: consumed when the harness is built, so a harness view cannot reach it |
| non-commute blend | `noncommute_proxy` + `blend` | — | **not runnable**: its parameterization is unspecified and is not invented here |

**Why the path-model knobs are inert** (read from the frozen source, and
consistent with the measurements):

* `pathset.build_pathset` contributes at most one path per OD per enumeration
  scenario, and raises the per-OD cap to the scenario count. A cap below the
  count is therefore raised, and a cap above it is never reached.
* `exp3_score.solve_on_network` passes `n_random_scenarios=0` explicitly, so
  the configured value (3) is not used on the production path.

Consequence: a path-model dimension expressed through these two knobs would
be a no-op. Any as-issued path-model level must use a knob that reaches the
evaluator (e.g. `max_rounds`, once confirmed). Otherwise F4, F6 and AF1 are
stated as conditional on the path model. `src/cota_opt` is not changed to make
a knob reach; doing so would break BASE reuse (G6).

**Claim bounds for omitted variations.**

* Any dimension absent from the as-issued matrix is **not tested**. F4, F6 and
  AF1 are then stated as conditional on its baseline setting.
* The following are called out explicitly because they were flagged in earlier
  experiments:
  * the cross-route common-lines omission (12.47% of GC on N4) → F4 is
    conditional on the same-route waiting model unless the waiting model is a
    level;
  * the path-model fit on N4 → F4 is conditional on the path model unless it
    is a level;
  * λ below 2 is outside the certified frontier, where the fixed-plan sign
    flip was at λ ≈ 1.087;
  * a wider OD universe (discharges the Exp 4A deferral only if it is a level).
* Envelope and fleet variations are outside Exp 7 unless the as-issued text
  includes them. The fleet materializer defect still blocks every fleet
  verdict.

---

## 9. Firewall

Every reported comparison is admitted under a per-level contract
(`scripts/exp7_contracts.py`). The level fixes the objective version (λ) and
the evaluator (waiting model), and its digest is part of `config_digest`.

| contract | track | what may differ |
|---|---|---|
| `EXP7_POLICY` | F6 | `config_digest` only (the policy) |
| `EXP7_STRUCTURE` | F6 (AF1) | network fields only |
| `EXP7_F4` | F4 | network fields only |

* The two tracks carry different solver-policy names, so an F6 receipt cannot
  be admitted as F4 evidence.
* Receipts follow Exp 6 Amendment 2:
  * `starts_attempted` is the procedure (opportunity): `exp7_combined_closure`
    or `exp7_cross_level_closure`;
  * `winning_start` is the basin that won (outcome).
* **Level binding.** The firewall preflight
  (`outputs/exp7/preflight/FIREWALL_PREFLIGHT.json`) found that, without
  extra binding, EXP7_POLICY admitted a pair certified at different levels.
  The level digest sits inside `config_digest`, which that contract
  whitelists, so the level difference passed as a "policy difference".
  Two fixes close this:
  * `receipt_for` refuses a record whose level is not the contract's level;
  * the level digest is folded into `data_digest`, which no Exp 7 contract
    whitelists, so the firewall itself refuses mixed-level receipts.

  Both refusals are preflight-tested.
* Raw objectives are never compared across levels; the contracts refuse it.
  Cross-level statements are made only about prices and signed differences,
  each admitted within its own level.

---

## 10. Readiness gates

`exp7_freeze.py` refuses to freeze unless all of these pass:

| gate | requirement |
|---|---|
| G1 | the as-issued text is committed verbatim |
| G2 | this amendment names every matrix level |
| G3 | the BASE canaries through `exp7_cell.py` reproduce the Exp 6 initial records bit-exactly (objective, plan, rounds, fitness, config and path-set digests) |
| G4 | every matrix level reaches the evaluator on N0 and N3, and on N4 for F4, while BASE reproduces the record |
| G5 | unit tests pass: propagation, combined closure, refusal, ceiling failure, memo, resume, empty cells, zero/tie classification, sign flips |
| G6 | the `src/cota_opt` digest equals Exp 6's, or BASE reuse is off |
| G7 | production-path preflights pass: a real cross-level transfer, re-evaluation under the target λ, never worse than the anchor, a certifier policy refusal, a certifier representation refusal, and N3 R1_H20 emptiness re-proved under a non-BASE level |

---

## 11. Compute

Estimated by `exp7_freeze.estimate` from measured throughput, with every
assumption stated in its docstring.

**Measured seconds per certification** (2-core box, two lanes):

| work | N0 | N3 | N4 |
|---|---|---|---|
| Exp 6 initial cells | 596 | 611 | — |
| Exp 6 closure transfers | 627 | 624 | — |
| Exp 7 smoke cross-level transfers | 346 and 601 | — | — |
| D39 anchored runs | — | — | 1,079–1,148 |

The estimate uses N0 610 s, N3 615 s and N4 1,150 s.

**The cross-level all-pairs X stage grows as L(L−1)** in the number of levels
L. In the smoke run, every pass-1 candidate RAN (2 of 2), so the expected case
assumes all pass-1 X candidates run.

| L (incl. BASE) | certifications, expected | certifications, upper | wall h, expected | wall h, upper |
|---|---|---|---|---|
| 3 | 388 | 617 | 34 | 54 |
| 4 | 695 | 1,109 | 61 | 96 |
| 5 | 1,080 | 1,725 | 94 | 150 |
| 6 | 1,542 | 2,465 | 135 | 215 |
| 8 | 2,700 | 4,317 | 236 | 376 |
| 11 | 5,018 | 8,025 | 438 | 700 |

The totals include:

* the new initial cells (BASE reuses Exp 6);
* the W stage (≈22.5 RAN per network per level, as measured in Exp 6);
* the X stage (the expected case adds a 25% second pass; the upper bound
  assumes every candidate RAN in 2 passes);
* the F4 track including N4;
* 4 sentinels.

Neither bound covers a closure that needs more than 2 passes (the ceiling is
8). The executed preflight (about 3.5 h wall) is excluded.

## 12. Inputs still required from Ian

1. The 23 September Exp 7 text, verbatim, including dimensions, levels, A8
   retention settings, bands, and F1–F3 and F5.
2. **Scope of the all-pairs X stage.** "All-pairs within each network and
   compatible policy regime" is implemented across **all** levels. That is
   quadratic in L (§11): about 94 h wall for L = 5, and about 438 h for
   L = 11.

   The cheaper alternative is all-pairs **within each dimension**, with BASE
   joining every dimension. It still never forwards only winners along a
   chain. What it gives up is transfers between unrelated dimensions (e.g. a
   λ-level plan offered to a period-tilt level). Whether that loss is
   acceptable is a scientific choice, and it is Ian's.
