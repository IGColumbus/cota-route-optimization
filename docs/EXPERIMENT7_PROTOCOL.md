# Experiment 7: governing protocol (consolidated view)

*Updated 2026-09-29 under Ian's governing instruction of the same date. This
file brings the chronology together; it adds no finding.*

**Status: NOT FROZEN.** `scripts/exp7_freeze.py` gates the freeze (§7).
Production starts only after every gate passes, and after the one decision
in §6.

*The earlier "replacement protocol (PROPOSED)" version of this file is
superseded and survives only in git history. Its AF2 finding and its
invented bands are withdrawn. It was replaced when Ian supplied the
as-issued text.*

## 1. The documents, in chronological order

| date | document | status |
|---|---|---|
| 23 Sep (as issued) | `docs/EXPERIMENT7_PROTOCOL_AS_ISSUED.md` | historical protocol; **its F4, F6, COTA-compliant solution and re-optimization rule are superseded, and preserved only as history** |
| 23 Sep (same-day revision) | `docs/EXPERIMENT7_SEPT23_FINALIZATION.md` | in force: sign robustness is separate from magnitude stability; the magnitude bands |
| 29 Sep | `docs/EXPERIMENT7_AMENDMENT.md` | in force: post-Exp-6 amendment (F4/F6 definitions, AF1, search, anchors, firewall, the A4/A8 operationalizations, the X-stage decision, the additional sensitivities, claim bounds) |
| 29 Sep | `outputs/exp7/EXP7_LEVELS.json` | the declared matrix; each level carries its provenance class |

Where two documents disagree, the later one governs. The only exception is
the as-issued text, which is preserved as history.

## 2. Findings under test

Nothing outside this list gets a label.

| id | definition in force | source |
|---|---|---|
| F1 | Exp 1 unserved-demand improvement (−6.65%, mean of 3 seeds), under the actually certified resource definition. "No added buses" survives only inside the historical text. | as issued; wording per the v4 fleet-wording correction |
| F2 | Exp 2/2B: the route-splice certified null | as issued |
| F3 | Exp 3: the single certified add_stop mutation (−0.187%) | as issued |
| F4 | Greenfield N4 does not beat N3 or N0 under the matched modeled contract; classify sign/magnitude robustness | 29 Sep amendment (`EXPERIMENT6_D39_AMENDMENT.md` §4) |
| F5 | Exp 5: the marginal return per unit of peak resource. Exp 5's terminal `EXP5_MONOTONICITY_FAILURE` (12 N4 pairs) and its basin dependence are preserved. Exp 7 tests and reports the robustness of that evidence; it does not recast Exp 5 as a clean monotone frontier. | as issued, with its caveats |
| F6 | Policy price on N0 and N3 under the Exp 6 basin-closure procedure; the full 14-cell policy graph | 29 Sep amendment |
| AF1 | N3 slightly better than N0 at matched policy (Exp 6: −0.153% to −0.229%) | 29 Sep amendment, labelled as an additional finding |

## 3. The matrix (47 production levels plus BASE)

Each level in `EXP7_LEVELS.json` carries one provenance class:

* **as issued**: the Sept 23 row. The level is as issued; any numeric
  operationalization is stated.
* **amendment**: 29 Sep.
* **Class B**: model disagreement.
* **additional**: post-Exp-6, not a Sept 23 row.

| dimension | levels | provenance | operationalization |
|---|---|---|---|
| A1 non-commute added | `A1_NC025`, `A1_NC050`, `A1_NC100` | as issued | Gravity-form trips (`noncommute_proxy`: workers+jobs attraction, 4 km exponential decay), added at 25/50/100% of commute volume. **Bound:** confined to the commute OD pair set, so non-commute trips between pairs with no commuting are not represented. |
| A2 demand sampling | `A2_BOOT01`…`A2_BOOT20` | as issued | Block-pair rows resampled with replacement (seeds 20260901–20260920); the harness pipeline is unchanged. |
| A3 runtime | `A3_RT110`, `A3_RT120`, `A3_RTNOISE` | as issued | Segment run times scaled; trip runtimes rescaled per pattern (vehicle-hours and peak move too); **the envelope is unchanged**. Noise: per-link lognormal with median \|error\| 20.5% (`runtime_validation.json`), seed 20260929. |
| A4 reliability | `A4_WAIT375`, `A4_WAIT500` (declared) | amendment | **UNIMPLEMENTED** (see below) |
| A5 cost weights | `A5_LAM1`, `A5_LAM4`, `A5_TP050`, `A5_TP200` | as issued | λ ∈ {1, 4}; transfer penalty ×0.5 and ×2 (via a scoped patch of `exp2.load_cost_weights`; src unchanged). λ = 1 is outside the certified λ ≥ 2 frontier and is labelled that way. |
| A6 walking | `A6_WALKSPD85`, `A6_MAXWALK75` | as issued | Walk speed 80 → 68 m/min. "Maximum walking distance −25%" is applied to both walking caps: access 600 → 450 m and transfer walk 400 → 300 m. |
| A7 disruption | `A7_RM01`…`A7_RM10` | as issued | Remove the rank-k route; the ranking is frozen per network by modelled boardings (`outputs/exp7/A7_ROUTE_RANKING.json`). The removed route's resources stay in the envelope. |
| A8 retention | `A8_ZERO150`, `A8_FLOOR0` | amendment | zero_min 210 → 150; floor 0.10 → 0.00. **full_min = 60 fixed, so robustness to full_min itself is not tested.** |
| B assignment | `B1_COMMONLINES` | Class B | Common-lines (`pattern`) waiting. Reported as model disagreement, never as a Class A result. |
| additional | `X_TOPK40K`, `X_ROUNDS4` | additional | Top 40,000 OD pairs (the Exp 4A deferral); max_rounds 4 |

**Not run, with claim bounds:**

* **A4 (declared, UNIMPLEMENTED).**
  * `waiting.schedule_coefficient` only changes expected wait for effective
    headways above 12 min (`pathset.py` `_wait`).
  * The production path has no headway-variance term: `weights.reliability`
    is 0.0 and unused.
  * A headway-variance penalty mainly inflates random-arrival wait on
    frequent service, which this coefficient cannot reach. The coefficient
    therefore does not faithfully represent the A4 question.
  * **Bound:** no finding is claimed robust to service reliability.
* **B2 jobs-accessibility objective.** It does not exist on the frozen
  production path. **Untested.**
* **Path-set width and scenario count.** Measured inert; dropped. **Bound:**
  findings are conditional on the path-enumeration design.
* **Period-profile tilt.** Not a Sept 23 row; omitted. **Bound:** the
  period-share assumption is untested.
* **Uniform demand scale.** Not a Sept 23 row; invariant by construction
  (no crowding in the certified evaluator).

## 4. Search (amendment §3, as decided on 29 Sep)

* Combined closure: within-level policy closure (W), then cross-level
  transfers (X), repeated until a whole pass improves nothing. Ceiling 8
  passes, ε = 1e-9, deduplication, deterministic resume, refusal handling;
  hitting the ceiling blocks certification.
* **The X stage is dimension-local.**
  * All-pairs runs among BASE plus one dimension's levels. There is **one
    canonical BASE**.
  * No edge exists between non-BASE levels of different dimensions.
  * A plan from dimension A reaches dimension B only by first becoming the
    certified BASE incumbent: improving BASE by more than ε under the BASE
    contract.
  * Dimensions run in the frozen order of `EXP7_LEVELS.json`.
  * Implemented in `scripts/exp7_closure.py` (`Group.dimension_of`) and
    unit-tested.
* A7 levels change the network's route-period set. Every plan moving
  between an A7 level and BASE is therefore refused on representation,
  receipted, never repaired. A7 cells get only their independent initial
  solves.

## 5. Classification

Sept 23 finalization, implemented in `scripts/exp7_classify.py`:

* **Sign.** `SIGN_ROBUST` / `SIGN_SENSITIVE`, using the existing
  `SIGN_FLIP` / `TO_TIE` / `FROM_TIE` mechanics.
* **Magnitude.** Relative to the certified BASE magnitude: Highly stable
  (≤ 10%) / Stable (≤ 25%) / Moderately sensitive (≤ 50%) / Highly
  sensitive (> 50%). This label is descriptive only.
* **`MAGNITUDE_RATIO_UNINFORMATIVE`.** Emitted when the absolute BASE effect
  is at or below the tie band τ. Absolute movement is reported instead.
* **Separate descriptors, never labels:** operational fragility, policy
  conflict and model dependence. That includes every Class B disagreement.
* **Separate from robustness labels:**
  * zero-price rules, ties, feasibility transitions, hard monotonicity and
    the basin-vs-sensitivity split (amendment §7);
  * D33-B, which stays veto-only.

## 6. The decision needed before production

**Closing every one of the 47 levels is not feasible.** Re-optimizing and
closing every F6 and F4 cell at every level costs about **2,300 h** wall on
two cores (about 26,000 certifications; A2's 20 draws alone account for about
1,400 h).

The as-issued rule already answers this. The 29 Sep amendment supersedes it
only where D39 makes it necessary.

**Recommended two-stage design:**

1. **Stage 1: fixed-solution evaluation.**
   * Every solution under test is evaluated, unchanged, at all 47 levels.
     This is the as-issued design.
   * No search runs in Stage 1, so D39 basin effects cannot contaminate it.
   * One path-set build per (network variant, level), about 190 builds. Any
     number of plans are then evaluated on each build. Wall time is about
     10–12 h.
   * Every finding gets a sign and magnitude label from Stage 1.
   * Stage 1 takes F6 prices from the frozen Exp 6 closed plans.
2. **Stage 2: re-optimization, with the combined closure on the F4 and F6
   tracks.**
   * Stage 2 runs in the two Class A dimensions that moved F1 and F4 most in
     Stage 1. This is the as-issued rule, with the D39-safe closure replacing
     plain re-optimization.
   * Where Stage 2 runs, its labels supersede Stage 1's.
   * If A2 is selected, the protocol needs a stated subset of draws. Twenty
     draws under full closure cost about 800 h.
   * Cost depends on which dimensions are selected. For two 3-level
     dimensions it is about 100–120 h.

**Alternative:** full closure at every level, about 2,300 h.

This is a scientific choice, and it is Ian's.

## 7. Readiness gates (from executed checks)

| gate | requirement | state |
|---|---|---|
| G1 | governing text committed and consistent | PASS once this commit lands. As-issued text, Sept 23 finalization and 29 Sep amendment are all present. |
| G2 | levels declared and named in the amendment | declared; freeze pending G4 |
| G3 | BASE reproduction | PASS (3/3 bit-exact) |
| G4 | every production level reaches the evaluator on N0, N3, N4 | **RUNNING**: `preflight/reach_matrix/` |
| G5 | unit tests | PASS (21) |
| G6 | src unchanged | PASS (`b63ae2dba134245e`) |
| G7 | transfer/refusal/emptiness + firewall preflights | PASS (7/7, 8/8) |
| — | Stage 1 evaluator for F1/F2/F3/F5 | **NOT BUILT**: depends on §6 |
| — | stage design (§6) | **OPEN**: Ian |
