# COTA route optimization — state of play

Last updated 2026-09-29. **Experiment 6 closed with
`EXP6_POLICY_FRONTIER_CERTIFIED`**
(`outputs/exp6/EXP6_ANALYSIS.json`, `EXPERIMENT6_CLOSEOUT.md`).

It measured the **modeled** price of policy constraints on two networks:
* N0: existing geometry, `f0f24936ab06b4ec`;
* N3: `add_stop-010#22c4c35ac5b2`, `430aca035c70715b`.

The setup:
* the frozen Model B demand and evaluation model;
* the EXP4N common envelope (`3fd5241db44ca9da` / exact `0b46d1abc9a80c80`);
* λ = 2;
* the declared basin-closure procedure. Each cell is first solved from its own
  greedy start. It is then closed over the policy nesting graph (60 strict
  pairs, 20 Hasse edges) with explicit anchors until a full pass improves
  nothing. Monotonicity is enforced after closure, and the reference cells take
  part in the closure.

Frozen artifacts:
* contract `outputs/exp6/EXP6_CONTRACT.json`: sha256 `5bf1cb82ad8829a8…`,
  frozen 2026-09-29T00:09Z; firewall `EXP6_POLICY` `393f45ac10d28cb9` and
  `EXP6_STRUCTURE` `fad14449dc3db7c6`;
* source `b63ae2dba134245e` / `src-17659e64846b`;
* catalog `e22f2c94c8f53475`;
* Amendment 1 (`INFEASIBLE_UNDER_ENVELOPE` cells) and Amendment 2 (receipt
  start encoding; §6 of the closeout).

**Gates, all passed:**
* **Preflight.** Default-path equivalence was bit-exact for N4 (EXP4N), N3
  (Exp 4A) and N0 (Exp 5 J100). The D39 canary passed: anchored at Exp 5's N4
  H090 plan, N4 certifies at **3,207,566.4177** under the EXP4N envelope, 0.506%
  better than EXP4N's own plan. D35 passed for R1/R2/R3/R4/R6 on both networks.
* **Records.** 27 of 28 cells certified. 54/54 record checks passed (27 initial
  + 27 final).
* **Closure** reached its fixed point in **3 of 8 passes** on both networks. N0
  ran 24 anchored certifications and N3 ran 21, across 120 receipts each. Cells
  that changed basin: 9 on N0, 8 on N3.
* **Monotonicity: 22/120 violations** after the initial greedy solves (reported,
  not gated), and **0/120 after closure**. Reference closure is clean.
* **Firewall** (after Amendment 2): policy 25/25 admitted, structure 13/13
  admitted.
* **Sentinels:** 4/4 bit-exact.

**Finding 1 — the objective is flat across very different plans on N0 and N3,
not only on N4.** Closure moved both reference cells to a different basin:

| network | objective | served trips (of 30,949) | OFF route-periods | GC |
|---|---|---|---|---|
| N0 | 2,945,632.23 → 2,941,892.37 (**−0.127%**) | 16,527 → 21,144 | 50 → 15 | +45% |
| N3 | 2,939,912.58 → 2,935,166.03 (**−0.161%**) | 16,434 → 21,104 | 54 → 17 | +46% |

* The Exp 6 initial REFs reproduce the Exp 4A N3 and Exp 5 N0 J100 records
  bit-for-bit. So those records, exact under their contracts, are **not the
  best-known plans** under the EXP4N envelope. They are not reopened, and Δ43
  stays +9.66%.
* Start-basin dependence (D39) appears on N0, N3 and N4 under this objective
  and certifier. Whether the objective or the search is the cause is not
  separated.
* Served trips and GC from any single-basin run are basin-dependent.

**Finding 2 — modeled policy cost**, closed cell − closed REF, in objective
units and not dollars:

| safeguard | N0 | N3 |
|---|---|---|
| R2 OFF share 25%, 10% | 0 (does not bind at the best-known REF plan) | 0 |
| R2 5% | +0.212% | +0.250% |
| R4 coverage, c = 0.05 / 0.01 | +0.244% / +0.428% | +0.321% / +0.477% |
| R6 ¾-mile | +0.440% | +0.485% |
| R1 H = 60 = R3 span = R4 c = 0 = B1 = B2 (one shared final plan, 0 OFF) | +0.482% | +0.524% |
| R1 H = 30 | +0.575% | +0.634% |
| R1 H = 20 | +0.912% | **infeasible under the modeled envelope** (minimum service: early peak proxy 85.2987 > 85.2821) |

The shared plans mean one of two things, and the experiment cannot separate
them. Either relaxing R1_H60 to R3, R4 at c = 0 or the bundles buys nothing, or
closure found nothing better. It is not a claim that the constraints are
equivalent.

**Finding 3 — single-start pricing is contaminated at the scale of the prices.**
* Greedy-only prices differ from closure-adjusted prices by −0.162 to +0.124
  percentage points.
* Most of that comes from the reference itself being stuck in its greedy basin
  (0.13–0.16 pp too high). For most cells this made the greedy-only price too
  low; R2_S10, R3_SPAN and R4_C05 went the other way.
* It produced **two impossible negative prices**: R2_S25 at −0.115% on N0 and
  −0.081% on N3.
* It priced R3 span above R1 H = 30, although R1 H = 30 implies R3.

**Finding 4 — N3 is better than N0 in all 13 comparable cells** (EXP6_STRUCTURE),
by **0.153% to 0.229%**. At REF the gap is −6,726.35 (−0.229%), against −0.194%
from single starts and −0.187% in Exp 3's certification. Each binding
safeguard costs 0.04–0.08 pp more on N3.

**Every regime is a study safeguard.** None is COTA policy or Title VI
compliance, and no COTA numeric anchor was found. R5 is
`UNIMPLEMENTABLE_WITH_CURRENT_DATA` (Title VI form), and R7 is excluded. The
"COTA-compliant" combined regime was not run. **Physical fleet is UNDECIDABLE
for every cell.** No valid instrument exists (Exp 5's materializer is off by
17.8–47% on vehicle-hours), so none was run. There is no dollar, bus,
deployability or global-optimum claim, and Finding 1 is direct evidence
against reading any closed plan as optimal.

Compute: preflight 2026-09-28 22:18 → 2026-09-29 00:01; production 00:09:58 →
07:24:40 UTC on 2 cores. The Amendment 1 halt ran 00:45:30 → 00:59:33 / 01:09:23.
Closure reached its fixed point at 06:36:25 (N3) and 07:01:00 (N0).

**Cross-experiment consistency check, 2026-09-28 (additive, read-only;
superseded in size by Exp 6's closed REF comparison, −0.229%).** The
Exp 4A matched N3 record (`outputs/exp4_addendum/N3.json`, 2,939,912.5807) and
the Exp 5 N0 J100 reference cell (`outputs/exp5/cells/N0_J100.json`,
2,945,632.2349) were built under different experiment contracts, `0f62…` and
`395e…`. Their recorded execution is otherwise identical: evaluator, λ, exact
envelope, certifier, seed, config, data, code and runner hashes. Rebuilt as
receipts and judged with `firewall.compare`, they are **admitted** under both
`EXP4A_MATCHED` and `EXP5_STRUCTURE`, with only network fields differing:

* N3 − N0 = **−5,719.65 (−0.194%)**, against Exp 3's certified −0.187%;
* N3 serves 93.7 fewer modeled trips, and its lower generalized cost carries
  the λ = 2 objective.

This is corroboration, not a new certification. Both are one-round
greedy-basin results, and the gap is smaller than D39's N4 basin residual.

---

Earlier on 2026-09-28 (evening). **The original Experiment 4 question has now
been answered, and the answer is no.** Under the identical EXP4N certification
contract, the normalized leader N4 (`...35e351133d6f`) does **not** beat
Experiment 3's constrained redesign N3 (`add_stop-010`):

* Δ43 = obj(N4) − obj(N3) = **+283,973 (+9.66% of N3)**; lower is better;
* N4 serves **31.5% fewer** modeled trips for the same hours and peak proxy;
* the comparison is firewall-admitted;
* it survives an omission-corrected path costing (+7.87%);
* it holds for every fixed-plan λ above 1.087.

The result is conditional on the frozen path model, which fits N4 markedly
worse, and on the same-route waiting model, whose cross-route omission on N4 is
12.47% of GC. See `EXPERIMENT4_ORIGINAL_QUESTION_ADDENDUM.md` (additive; the
EXP4N ranking is not reopened). Before any number was used, the runner
reproduced EXP4N's N4 bit-exactly (objective, plan, 21 rounds, full trajectory).

**EXP4N**, completed 2026-09-28 with `EXP4_FULL_NORMALIZED_CERTIFIED`:

* 200 of 200 candidates re-certified under ONE common peak-vehicle envelope;
* §8 integrity gate: 44 checks, 0 failures;
* **Exp 4's leader `...ecb2ffc4bcce` is now rank 185 of 200**; the leader is
  `...35e351133d6f` (legacy rank 154);
* Spearman **+0.3566**; **36.7% of pairwise orderings inverted**;
* only one of Exp 4's top ten survives in the normalized top ten.

See `EXPERIMENT4_NORMALIZED_CLOSEOUT.md`.

Experiments 1, 2, 2B, 3 and 4 are closed, as is the Experiment 4 out-of-band
audit. Experiment 3 is frozen at tag `exp3-final-v1`. **Both** Exp 4 runs were
made with **fleet REPORTED, NOT GATED**. The fleet question is *still open*, and
**neither run advanced it**.

**Experiment 5 ran and its preregistered acceptance rule FAILED, on N4 only:
`EXP5_MONOTONICITY_FAILURE`.** See `EXPERIMENT5_CLOSEOUT.md`.

The original premise and design are retired in
`EXPERIMENT5_PREMISE_RETIREMENT.md`. Hours were not slack under the common
envelope (99.92–100.00% used).

The reframed experiment:

* a modeled frontier over revenue vehicle-hours and the solver peak-concurrency
  proxy (not fleet);
* N4 and N0 at 16 cells each, 75–150%;
* 32 certifications with EXP4N's unchanged certifier;
* the contract frozen before the first production cell.

Every other gate passed:

* reproduction of EXP4N's N4 was bit-exact;
* D35 reach, convergence and feasibility 32/32;
* firewall 46/46;
* reversed-order sentinels 4/4 bit-exact.

The results:

* **N0 is monotone on all 99 nested pairs.** Both axes bind at today's levels.
  Above them only the peak proxy binds; below them, cutting hours costs
  0.57–2.05%.
* **N4 is worse than N0 at every cell**, by 8.07–11.59%.
* **On N4, 12 of 99 pairs regress by up to 1.70%.** Cause: certification starts
  from a greedy build under each cell's own caps and lands in different local
  optima (**D39**).
* That start-basin residual is at least 1.70%, about 4.4× EXP4N's
  first-to-second margin.
* The EXP4N N4 plan is not the best known N4 plan under the EXP4N envelope: the
  H090 plan is 0.132% better. Using it, Δ43 is still +9.51%.

Blocking is diagnostic only. It is UNDECIDABLE for all 32 cells: the
materializer does not reproduce the plans' own vehicle-hours.

(A version of this page written earlier on 2026-09-28 said EXP4N changed none
of Exp 5's premises. That was asserted without being measured, and it was
wrong.)

**The Exp 4 audit was stopped by decision at 15 of 200 on 2026-09-21.** It
established that the top-200 promotion cap was **invalid**: an excluded candidate
certifies better than the Exp 4 leader. It also produced **D38**, which reframes
D36: discovery scores are nearly flat in the region measured, so discovery is
not an inverted ranker but close to a constant plus noise. Its own
preregistered question, whether discovery enriches at the population level, is
**unanswered and not answerable from what was run**.

## The headline, in one line each

* **Experiment 1 — frequency redistribution: −6.65% ± 0.06 unserved demand inside
  the baseline's hours and per-period peak-concurrency proxy.** Certified, λ≥2.
  The objective result is untouched by everything that follows. The old
  wording, "at no additional buses" (197.0 against 197.0), is **withdrawn as a
  fleet claim**. Both figures are the cycle-over-headway proxy scaled by the
  baseline interlining factor (`blocks.fleet_estimate`), so the baseline reads
  197.0 by construction. The plan's physical fleet was never measured.
* **Experiment 2 — route geometry: no supportable claim.**
* **Experiment 2B — all 240 feasible combinations: certified NULL**, surviving a
  matched-start re-test (D31).
* **Experiment 3 — eight edit kinds, 84 states: 29 mutations certified, one
  certified leader at −0.187% on the λ=2 objective**, with a two-regime caveat
  that travels with it. (Earlier versions of this page said "unserved demand";
  the certified effect is on the scalarized λ=2 objective.)
* **Experiment 4 — COMPLETE, and its RANKING IS SUPERSEDED by EXP4N.** Best
  certified objective 3,511,184.5658 from `...ecb2ffc4bcce` over 200 certified
  candidates, margin to second **0.0106%**. Those numbers remain exactly
  reproducible and are **not** withdrawn — but they are an ordering of
  *candidate-specific optimization problems*, not of geometries, and that
  candidate now ranks **185 of 200** under a common envelope. Do not quote the
  Exp 4 ordering as a geometry result; quote EXP4N. Two findings survive: **D36**,
  discovery rank *anti*-correlates with certified rank and the promotion cap came
  within four ranks of excluding the winner (reframed by D38); **D37**, fast
  convergence excludes a candidate from contention. **No fleet claim and no
  deployability claim** — see below.
* **Experiment 4 — RESOURCE NORMALIZATION AUDIT, 2026-09-22:
  `EXP4_FULL_NORMALIZED_RERUN_REQUIRED`.** The peak-vehicle cap each candidate
  was optimized against was **its own baseline plan's `peak_by_period`**
  (`exp2.py:324`), so all 200 were optimized inside boxes they defined for
  themselves. The hours cap was pinned to the canonical artifact; the peak cap
  never was. A 10-candidate pilot under ONE common envelope, changing nothing
  but that provenance, moved **20 of 45 pairwise orderings**, dropped the
  incumbent from 1st to **9th of 10**, and handed first place to the candidate
  originally ranked **50 of 200** by **2.0031%**. Improvements span 2.2653
  percentage points — **99.4% of the entire original 200-candidate spread**.
  Exp 4's certified ordering must be read as an ordering *of candidate-specific
  optimization problems*, not of geometries, until a normalized rerun exists.
  `docs/EXP4_RESOURCE_NORMALIZATION_AUDIT.md`. **The objective values remain
  exactly reproducible. The rerun has since been done, and the pilot understated
  the size of the effect** — next bullet.
* **EXP4N — NORMALIZED RERUN, COMPLETE 2026-09-28:
  `EXP4_FULL_NORMALIZED_CERTIFIED`.** 200 of 200 re-certified under one common
  envelope resolved **once** from the frozen artifact, `MAX_ROUNDS = 120`,
  79.85 h compute. Leader **`...35e351133d6f`, 3,223,885.9475**, 21 rounds, 65
  lines, **legacy rank 154**; second `...d451584c40c6` at **+0.387006%**, legacy
  rank 193. The legacy leader falls to **185 of 200**. Spearman **+0.3566**,
  **7,296 of 19,900 pairwise orderings inverted (36.7%)**, field spread 4.1710%
  against legacy's 2.2788%. Rounds min 11 / median 21 / **max 44 against a
  ceiling of 120** — nothing within 76 rounds of the cap. Verified on two
  independent channels: §6 calibration controls **21/21** reproduced exactly, and
  the pre-loss archive **24/24 bit-exact** across 16 fields plus every per-round
  trajectory objective. **The margin is ~204× the D33-B noise band, which removes
  solver noise as an explanation and establishes nothing further** — the rule is
  asymmetric and the block-local residual is unmeasured for every candidate
  including this one. `EXPERIMENT4_NORMALIZED_CLOSEOUT.md`.
* **Experiment 4 — ORIGINAL QUESTION ADDENDUM, 2026-09-28: N4 does NOT beat
  N3.** Matched EXP4N contract `EXP4A_MATCHED` (`0f62aeabfa341a98`):
  * N3 re-solved from a treatment-independent greedy start: **2,939,912.5807**,
    1 round, converged;
  * N4 (EXP4N, authoritative): **3,223,885.9475**;
  * Δ43 **+283,973.37 (+9.66%)**, firewall-admitted, with only network fields
    differing; 5,092× the D33-B band, which is veto-only and establishes
    nothing by itself;
  * N4 loses 5,185 served trips and serves fewer stops in every period.

  The diagnostics are gates 4-8 to 4-11, run as diagnostics and not discharged:
  * path adequacy is much worse on N4 (8.7–34.8% of flow improvable vs 1.0–3.7%);
  * common-lines exposure is 12.47% of GC on N4 (`potentially_frontier_changing`),
    so the margin is model-dependent;
  * crowding does not bind at this demand scale.

  Gate 4-12 is deferred to Exp 7. Gate 4-13, fleet and physical inspection are
  UNRESOLVED. No global-optimality, deployment or fleet claim.
  `EXPERIMENT4_ORIGINAL_QUESTION_ADDENDUM.md`.
* **Experiment 4 audit — STOPPED at 15 of 200, and the cap was invalid.**
  Discovery rank 237, excluded by the cap, certifies at **3,510,666.7802** —
  **0.014747% better than the incumbent**, inserting at exact rank 1 of 201.
  An existence claim, immune to the audit's sampling defects. **D38**: across
  the 15, `objective_APPROXIMATE` spans 0.0077% while `objective_EXACT` spans
  1.7284%, so the perfect −1.0000 exact-vs-overstatement inversion is close to
  arithmetically forced and D36's −0.9930 was largely the same artifact. The
  audit's own question is **unanswered**: certifying in rank order left four of
  five strata empty. `EXPERIMENT4_AUDIT_CLOSEOUT.md`.
* **Experiment 5 — ORIGINAL DESIGN RETIRED (history below); reframed as a
  modeled operating-resource frontier, RUN, `EXP5_MONOTONICITY_FAILURE` (N4 only; D39)** — see the top of this page
  and `EXPERIMENT5_PREMISE_RETIREMENT.md`. The superseded audit, preserved:
  *(2026-09-21, legacy plans)* `EXP5_REFRAME_REQUIRED`. Three independent defects, any one sufficient —
  all measured on the LEGACY Exp 4 plans; EXP4N removes the second:
  the fleet axis cannot be measured (200 of 200 Exp 4 candidates have a fleet
  bracket containing the *entire* Exp 5 cap grid); no cell binds (every
  certified plan spends 36–37% of the hours cap, and 0 of 200 exceed even the
  tightest 0.75× level); and the only path that could apply a fleet cap
  measures it with the cycle-over-headway proxy that `contract.py` refuses by
  name. **The 2026-09-21 OFF→ON diagnostic settled the third point and
  overturned the recommendation:** the 80.8% OFF share is neither λ=2 nor the
  neighbourhood — all 315 OFF route-periods are one rung from service and
  every one of 3,076 improving activations is blocked by the peak-vehicle cap,
  which binds at 99.71–99.97% in all six periods while hours sit at 36.66%.
  Reframing onto revenue vehicle-hours is **retracted**: it would delete the
  only binding constraint.

* **Experiment 6 — modeled policy price on N0/N3: `EXP6_POLICY_FRONTIER_CERTIFIED`.**
  * Closure-adjusted costs are 0 to +0.912% on N0 and 0 to +0.634% on N3.
  * R1 at H = 20 is infeasible under the envelope on N3.
  * N3 beats N0 in all 13 comparable cells, by 0.153–0.229%.
  * Single-start pricing was off by up to 0.16 pp, with two negative prices.
  * The objective is flat across plans that differ by ~28% in served trips.
  * All regimes are study safeguards; fleet is UNDECIDABLE; no global optimum.
  * `EXPERIMENT6_CLOSEOUT.md`.

## D27 — the optimizer was chosen by the treatment

The single most consequential finding of the project, and it is about the
harness rather than about transit.

At discovery effort the frequency plan was snapped to a headway ladder. For some
networks the snapped incumbent was rejected as infeasible and the solver
**silently fell back to a greedy construction** — a *different optimizer*. Which
optimizer ran therefore depended on the treatment.

Nothing was deleted. Contaminated artifacts are marked **SUPERSEDED FOR
QUANTITATIVE INTERPRETATION** and remain readable, because *a superseded artifact
looks entirely legitimate from the inside*, and the record of how it looked is
part of the evidence.

### What the correction did to the answer

Stage A was re-scored across all 88 cells with treatment-independent starts. The
corrected 84-state census **reorders the kind ranking outright**:

| edit kind | n | corrected mean | best single |
|---|---|---|---|
| `add_stop` | 10 | **−0.033%** | −0.189% |
| `straighten` | 12 | −0.024% | −0.083% |
| `change_terminal` | 10 | +0.002% | −0.035% |
| `truncate` | 12 | +0.008% | −0.139% |
| `reroute` | 12 | +0.017% | −0.159% |
| `extend` | 12 | +0.028% | −0.070% |
| `split` | 4 | +0.090% | +0.031% |
| `splice` | 12 | **+0.239%** | +0.053% |

`extend` and `reroute` both changed sign. `straighten` moved from seventh to
second. **`splice` remained worst throughout, which is the internal control** —
Experiments 2 and 2B independently established splices as the harmful kind, so a
correction that leaves that standing while reordering everything above it is
behaving like a correction rather than a new error.

The census is **descriptive only**; its floor is *undefined*, not 0%.

## What D27 forced, and what it taught

* **D28 — the iteration ceiling was never binding.** Effort is bought with
  *restarts*, not iterations.
* **D30 — the fallback states were already in the winning basin.** Maximum |Δ|
  0.000000000 across eight stratified states. Mechanism real, displacement nil.
* **D31 — 2B's certified NULL survives matched starts.**
* **D32 — fixing the start policy collapsed the noise floor to zero.** Replicate
  spread had been measuring solver *variance*, not *error*.
* **D33 — the heuristic is locally optimal almost everywhere.** Max gap
  0.001837%, **not correlated with treatment**. It can veto a conclusion; it may
  never *be* a threshold.
* **D34 — the evaluator was not invariant to pattern identifier renaming.** Fixed
  by ordering patterns on content; verified end-to-end at 0.000e+00.
* **D35 — a constraint that was a label.** `Exp4Selection.pinned_off` was
  validated and hashed into `state_digest` and **reached nothing that scores**.
  Two selections differing only in it produced identical fitness under different
  digests — and `state_digest` is a declared treatment difference, so the
  firewall would have admitted the comparison and reported a zero effect for a
  treatment never applied. *A state space with a member nothing generates is a
  state space with a member nothing checks.*

D29 gates Experiment 4 separately: **an observed link is not an observed turn.**
150 of 206 candidate lines use at least one turn never observed; crosstown 40/40.

## The firewall — why this cannot recur quietly

> No treatment effect may be computed, promoted, certified, plotted, or reported
> unless the harness can prove that treatment and control differed only in
> dimensions the experiment contract explicitly permits.

**Whitelist, not blacklist.** Every field carries a `Sem` classification
(IDENTITY / OPPORTUNITY / OUTCOME / NONE); permitted differences are declared per
event type with written justifications; observations are content-addressed.

**D35 marks its limit.** The firewall proves two arms differed only where
permitted. It cannot prove a permitted difference was actually *applied*.

## Experiment 3 — complete, and it is not the null

Stage B preregistered and frozen before any cell ran. 200 cells, 0 firewall
refusals, evaluation-path digest identical at first and last cell.

> **`add_stop-010#22c4c35ac5b2`: −0.1866% on the λ=2 objective, |mean Δ| / SD(Δ) =
> 78.6**, certified against control *and* distinguishable from all 28 other
> certified candidates.

**29 of 39 certified.** The effects did **not** shrink under more search — the
opposite of the Experiment 2 pattern, where two geometry leaders moved 0.645
points and both crossed zero across the identical effort transition.

Two caveats travel with the number: nine of the 39 are seed-invariant, so their
paired SD inherits the control's variance entirely; and two analysis-code fixes
were made after the numbers were visible, each bounded by demonstration (payload
byte-identical, stdout delta one line) and disclosed in full.

**The two-regime split is the result's weakest point and it stands.** §6
escalates what is unresolved or failing, which is by construction the smaller
margins — so the leader has never been solved above 20 restarts, all 28 of its
pairwise comparisons are at 20 restarts, and the best margin confirmed at 40 is
2.33× smaller. Final split: 23 of 29 certified carry 40-restart verdicts; 6 —
the leader among them — carry 20-restart verdicts. Phase 5b would have closed
this and was **abandoned with zero cells completed**, for operational reasons
only, verified against the observation store. Anyone quoting −0.187% should
quote the regime split with it.

**Certified means distinguishable from solver variance at this effort, and
nothing more.**

---

# Experiment 4 — RUN COMPLETE (ordering SUPERSEDED by EXP4N)

> **Read this section as the record of the legacy run, not as the current
> ranking.** Every number below is exactly reproducible and none is withdrawn.
> What changed is what they are an ordering *of*: each candidate was optimized
> against a peak-vehicle cap read off its own baseline plan, so this table ranks
> candidate-specific optimization problems. Under one common envelope the
> candidate below ranks **185 of 200**. The instruments documented further down
> — the envelope, the two blocking instruments, the three verdicts, the type
> system — are unaffected and all still stand.

```
exact_leader        exp4|exp4-pool-v1|65lines#ecb2ffc4bcce
objective_EXACT     3,511,184.5657525407
rounds              12 (converged),  65 lines
status.json         complete: true
```

| | objective | rel. to leader | rounds |
|---|---|---|---|
| 1st | 3,511,184.5658 | — | 12 |
| 2nd `...08f377545e31` | 3,511,557.9642 | **+0.0106%** | 11 |
| 3rd | 3,514,611.1824 | +0.0976% | 14 |
| worst | 3,591,198.3836 | +2.2788% | 11 |

200 of 200 promoted candidates certified. Zero errors, zero
`PathsetScopeViolation`, zero empty-scope `CertificationError`, all 200
converged — none reached `MAX_ROUNDS = 40`. 36.19 h wall, 130,308 s compute,
mean 652 s per candidate, six shards, nothing lost to a rollover. Median gap
0.7721%; nine candidates within 0.18% of the leader.

`rank_certified` ordered the complete set on `objective_EXACT` alone under the
frozen tie-break `0297e180cf30369d`. Closeout: `EXPERIMENT4_CLOSEOUT.md`.

**The margin is the first thing to say about it.** First to second is 373.40
absolute — a hundredth of a percent, against ~0.19% effects elsewhere in this
project. And the leader *changed at candidate 190 of 200*: `...08f377545e31`
led from candidate 16 through 189, and every checkpoint from the 20 mark to the
180 mark reported it as best. Cutting the run anywhere before candidate 190
would have reported a different winner.

## D36 — discovery's ordering is inverted, and the cap nearly cost the run its answer

```
spearman(discovery rank, certified rank), n=200      -0.3361
spearman(exact objective, overstatement)             -0.9930
```

**The certified winner was discovery rank 196 of 200.** Promotion takes the top
200 of 2000 by discovery score; the winner sat **four slots above the cut**,
separated from the 201st proposal by 0.000154% of score. The CAP BOUND recall
risk carried in `promotion.json` since promotion was not hypothetical.

The mechanism: discovery always overstates (0.9116%–3.2279%), and it overstates
the *good* candidates most — the leader carries the largest overstatement in
the field. That shape means the discovery score is nearly **constant**, so its
residual tracks `−exact`. Across the same 200, the exact objective spans 2.2788%
and the discovery score spans 0.1589% — **exact varies 14× more** — and
discovery's error stdev (0.4638 pts) **exceeds** the signal stdev (0.4361%).

This is D18 measured rather than predicted: the gap tracks network structure so
precisely that it inverts the ordering. *Discovery proposes, exact optimization
decides* is not a stylistic preference — the proposing half would have given the
wrong answer.

**The band caveat travels with it.** Measured inside the promoted 200, whose
discovery scores span 0.159%. It does **not** extrapolate to proposals 201–2000;
what those contain is unknown, and certifying them is ~326 h.

## D37 — fast convergence excludes a candidate from contention, and says nothing else

```
best rank among rounds <=  8 :  80 of 200   (13 such candidates)
best rank among rounds <= 10 :  70 of 200   (28 such candidates)
```

The top **69** is entirely 11+ rounds, and the boundary *widened* with n (60th
at 180, 66th at 191, 70th at 200). Consistent with the `(N,K)`-block-local
contract rather than a discovery about it: a plan with no improving 8-key block
within 3 ladder rungs sits in a shallow basin. **The claim is about certified
rank, not about truth** — those same fast candidates have the widest unmeasured
block-local residual. D36 and D37 are independent
(`spearman(discovery rank, rounds) = −0.0202`).

## Three retractions from this run

Recorded because the checkpoint commits are the running record and a reader
working forward through them will otherwise carry the errors.

1. *"Every candidate converging in ≤8 rounds lands in the bottom half"* — FALSE,
   and false since candidate 147; that candidate finished **80th of 200**. It
   was restated as holding at the 150, 160 and 170 checkpoints. Cause: numbers
   were recomputed each checkpoint, **claims were not**.
2. *Every enrichment table before the 190 checkpoint.* At 180 the 12-round
   bucket read 0.00×/0.33× — the most depleted non-empty row — and ten
   candidates later it held first place. No row with fewer than ~20 members
   supports a claim, which is six of the ten rows.
3. *Two ranks stated without being computed* (candidates 138 and 157).

`spearman(rounds, certified)` finished at **−0.2653** after wandering across
nine checkpoints without direction. With 56% of the field in one bucket it
measures intra-bucket scatter. **Recorded, not argued.**

## What Experiment 4 does NOT establish

* **No fleet requirement.** The fleet instrument returns `UNDECIDABLE` for every
  candidate *including the leader*. Deadhead provenance is OPEN; terminal
  identity is degenerate on synthesised candidates. The 180–212 bracket is a
  `CANDIDATE_BLOCK_BOUND` and **neither end may be reported as a fleet number**.
* **No operational deployability claim.** Fleet was REPORTED, NOT GATED — no
  fleet verdict filtered, ranked or rejected any candidate, per
  `READINESS_FROZEN` (authorised by Ian, 2026-09-07). D24 remains open as
  post-result operational validation. **Certification finishing did not advance
  the fleet question at all.**
* **No global optimality.** The `(N,K)`-block-local guarantee is local and the
  residual is unmeasured for every candidate including the leader.
* **Nothing about proposals 201–2000.** 1800 were never certified, and D36 makes
  that question sharper rather than answering it.
* **Nothing about whether a 0.0106% margin is durable.** Two candidates a
  hundredth of a percent apart, under a local guarantee with an unmeasured
  residual, are not meaningfully ordered by this experiment. They are ordered by
  `rank_certified` under the frozen tie-break, which is a different statement.

---

# Experiment 4 — the instruments, as built

Readiness stood at **23 MET · 1 OPEN · 1 MANUAL of 25** at launch; gates 15: 11
MET, 4 ARMED, 0 OPEN. The earlier aborted run is preserved at
`outputs/exp4/run/STATUS.md` as **DIAGNOSTIC — INVALID RESOURCE ENVELOPE**.
Everything below documents the instruments the completed run used, and all of it
still stands.

## D18 — MET, and it is what forced the architecture (now measured as D36)

The gap benchmark ran on 36 cells over 4 network structures by exhaustive
enumeration of a reduced neighbourhood under the production objective. Median
gap +0.297432%, max +0.645892%.

**Q3's answer: the gap TRACKS network structure.** Largest structure-paired
differential 0.381749 pp against a median absolute gap of 0.297432 pp — ratio
**1.283** against a limit of **0.5** declared before any number existed. §3's
**forbidding branch** was taken: `discovery_effort_comparison_permitted = False`,
**no promotion band emitted**.

D18 is MET and Experiment 4 was blocked *by its answer*, which is a different
thing. **D36 has now measured how far that goes: inside the promoted band the
discovery ordering is not merely weak, it is inverted.** This is **D27 one level up**: D27 was the optimizer being *chosen* by the
treatment; this is the optimizer's *answer quality* being correlated with it. The
firewall catches the first and structurally cannot catch the second, because both
arms genuinely run the same optimizer under the same contract.

The remedy is an architecture, not a firewall rule:

> **Discovery proposes. Exact optimization decides.**

`ProposalScore` holds a discovery objective and refuses to be compared, ordered,
or converted to a float. The only way to read it is `for_promotion_only()`, whose
name is the audit trail.

## C9 — MET, after the proposal generator was revised

C9 asks whether the discovery approximation identifies the exact leader. Revision
1 failed on a single steepest-descent trajectory from one start. Revision 2 — the
full preregistered multi-start family — passes **6/6 with 100% frontier recall**,
under the exact master-path reuse configuration the production run uses.

Gate 4-7 was corrected to one factor, measured, and then **disposed of by the
architecture** rather than closed: reuse output is a `ProposalScore` that cannot
decide anything, and every promoted candidate is re-certified by `solve_exact`
with no path cache at all. The measured residual is enumeration richness, not
filtering — at survival fraction 1.000, where filtering is the identity, the
reuse arm still differs and is *better* in 4 of 5 cases.

## The envelope: three fleet numbers, one cap

A cap was being read off evaluated plans. Twice. Then invented outright.

| quantity | value | what it is |
|---|---|---|
| **block-derived peak vehicles** | **197 @ 17:13, 284 blocks** | COTA's own blocks, reconstructed from the feed. **This is the cap.** |
| `FitnessVector.peak_vehicles` | 176.132352 | the frequency model's peak concurrency. An evaluation **output**. |
| `routewise_peak` | 150.73 | the same proxy before interlining. |

197 / 150.73 = **1.307**, the "interlining factor". It is **evidence of proxy
error, not an exchange rate**, and nothing may multiply by it.

Frozen in `outputs/CANONICAL_ENVELOPE.json`, digest **`b6c647d3766338a6`**:
2,517.183333 weekday revenue vehicle-hours and `{early 135, am_peak 187,
midday 173, pm_peak 197, evening 178, owl 149}`. NTD VOMS is 198 — 0.51% apart.
The artifact carries a `NOT_THE_CAP` block naming each rejected quantity, because
the failure was never ignorance of the right number: the wrong one looked equally
plausible at the point of use.

**A resource cap is read from that artifact or from the production `baseline`
sentinel. Never off an evaluated plan, and never retyped into a script.**
`scripts/exp4_launch.py` carried `2507.0` hours and a scalar `200.0` peak until
2026-09-07; both are gone, and the launcher now reads the artifact.

## Two blocking instruments, because they answer different questions

`blocks.reconstruct` reads `block_id` off real trips. **A candidate network has
no `block_id`** — its trips do not exist yet — so the instrument that produced
the cap cannot measure the thing being capped. Something else was silently
supplying that number.

* `blocks.reconstruct` — "how many vehicles does COTA's **published** blocking
  use?" Semantics frozen; reproduces the envelope exactly.
* `exp4_blocking.block_candidate_schedule` — "what fleet do **these** trips
  require if feasibly reblocked?" No blocking to read, so it solves for one:
  **DAG minimum path cover by maximum bipartite matching**,
  `minimum_blocks = n_trips − maximum_matching`. Hopcroft–Karp; no min-cost
  flow, because counting buses does not need costs.

Both count vehicles through one shared `blocks.block_concurrency`, so they cannot
drift into slightly different timestamp logic.

`materialize_timetable` turns a frequency plan into concrete trips, reusing
`exp4_assemble`'s reading of a headway rather than inventing a second one.
Deterministic, order-independent, content-addressed.

### Test A — published-block reconstruction

`[135, 187, 173, 197, 178, 149]`, system peak **197 @ 17:13**, 284 blocks.
Exact. It is the provenance test and it guards the shared-counter refactor.

### Test B — the bracket

    180  ≤  true minimum fleet  ≤  212        (2,331 stripped-block trips)

Upper: every cross-terminal connection forbidden. Lower: all of them free, and
labelled a relaxation that certifies nothing. **The published 197 sits inside.**
That is the entire honest claim — the historical blocking is consistent with the
physics, and the instrument neither reproduces it nor contradicts it.

**Dilworth cross-check.** Under the relaxation the reachability relation is
transitively closed, so minimum chain cover = maximum antichain = peak interval
concurrency. Solver 180, analytic 180. That validates Hopcroft–Karp on 2,331 real
trips independently of any transit assumption.

### The audit of COTA's own blocking

2,047 transitions: **2,007** same-terminal feasible, **7** under the 300 s
layover (which measures the *assumption*, not COTA), **33** cross-terminal.
**98.4% of the published blocking needs no deadhead data at all.**

## §9 — amended before execution, with the original preserved

The preregistered arm was `candidate_fleet[p] <= envelope.fleet[p]` for all six
periods, plus vehicle-hours. **That question is not well posed.**

A maximum matching is not unique. Reversing the adjacency order yields an
*equally maximum* matching — same 212 blocks — whose per-period concurrency moves
by up to **15 vehicles** (midday 199 → 210, am_peak 195 → 210). Longer chains
hold a vehicle nominally in service across an idle midday it never worked, and
which chains you get is an artifact of list order.

**AMENDMENT 1** (2026-09-07, before any execution) removes the per-period arm as
a gate. The question is now **existential** — *does there exist a feasible
blocking of the candidate timetable within the envelope?* — and the invariant
quantity is `minimum_blocks`. Per-period figures survive as **diagnostics**.

Deliberately **not** done: canonicalising the adjacency order to make the
statistic reproducible. That would make it stable without making it mean
anything, which is the worse failure. Nor was min-cost flow added to rescue it —
that answers a different question, and belongs to a separate constrained-blocking
experiment if anyone wants it.

The original §9 text is preserved verbatim in `FLEET_ARM_ORIGINAL`, in
`EXPERIMENT4_BLOCKING_CONTRACT.md` under "ORIGINAL, PRESERVED", and in tests that
fail if either is quietly rewritten.

## Three verdicts, and refusal is one of them

`production_feasible` returns `FEASIBLE`, `INFEASIBLE`, or `UNDECIDABLE`.

**INFEASIBLE** always runs through a matching-independent quantity, so a
refutation can never be an artifact of which matching turned up: vehicle-hours
over the envelope; `period_lower_bounds` over the envelope; block count above the
baseline's *under the same instrument*; or a bracket that cannot be reconciled.

**FEASIBLE** requires an oracle whose provenance satisfies the certification
contract. Currently unreachable, and correctly so.

**UNDECIDABLE** everywhere else — and *every* blocker is reported, not the first
found, because a blocker list revealed one item per run is a queue.

*The instrument can refute a plan. It cannot yet approve one, and it says so.*
**The baseline returns UNDECIDABLE, which is correct behaviour.**

## Four fleet numbers are now four types

`FleetQuantity` refuses `float()`, refuses ordering, refuses comparison across
kinds, and requires a named purpose to read; the legacy proxy refuses any purpose
containing "certif". `CandidateFleetBound` carries both ends of the bracket as
one object and raises on `certified_value()`. Neither the cap nor the proxy is
defaulted anywhere in source — a test asserts it, because a correct constant is
still a constant.

## Deadhead provenance — OPEN

A vehicle can only continue onto a trip it can reach, and this project has no
defensible source for terminal-to-terminal deadhead time:

* `walk_speed_m_per_min` is pedestrian;
* NTD's 12.20 mph is *in-service* speed, with stops and dwell;
* `linkgraph.ObservedLink` covers movements operated in revenue service, which a
  deadhead generally is not;
* the slack between consecutive trips in a published block proves a connection
  *happened* and bounds deadhead from above by whatever the scheduler left. **It
  is not a travel time**, and calling it one manufactures evidence out of a
  scheduling artifact.

`DeadheadOracle.time_sec` **raises** rather than returning zero. An unknown
connection is infeasible, never free. `TableDeadheadOracle` accepts a real table
without touching the solver.

## Terminal identity — OPEN, and found by running the thing (D24)

`--stage preflight` executes the whole fleet path on a real 6-line candidate
without starting a search. D23 checks the launcher's *text*; something had to
check that the text *runs*. It ran, and it found a second missing input.

GTFS `parent_station` is **empty in all 2,949 stop rows**, so nothing states
which stop_ids are one physical terminal. On the published feed this barely
matters — 9 of 2,331 trips (0.4%) end where nothing starts. On a synthesised pool
candidate it dominates: an outbound ends at `HIGHALS` while its own inbound
starts at `HIGHALN`, and **240 of 288 trips (83.3%)** are stranded, so the
same-terminal upper bound is one block per trip almost by construction.

Barred substitutes, each for the same reason estimating deadhead from block slack
is barred: a distance threshold (invented, and the answer moves with it); a
`stop_name` prefix or `BAY` suffix (infers geography from a label); assuming a
route's two directions share a terminal because they are the same route.

`terminal_identity()` measures it, and `production_feasible` **withholds every
terminal-dependent comparison** on a degenerate timetable — in both directions,
so it neither refutes nor approves on an artifact. Terminal-free lower bounds
still bite.

**Both open inputs would be closed by the same artifact: an operator-supplied
terminal/garage table.** Neither is replaced with a convenient assumption.

## D23 — ten assertions, MET

A production run's envelope must equal the canonical one **and constrain the
right quantity**. Nine assertions can pass while the run still constrains the
wrong thing: right numbers, wrong variable. The ten check that hours and the
fleet vector are *read from the frozen artifact rather than typed*; that no
scalar peak stands in for a six-period vector; that `peak_vehicle_budget` is not
set to a number `contract.py` can only record as `NOT RUN`; that the envelope
digest is propagated; that no concurrency-to-fleet conversion appears; that the
candidate solver is actually called; that a bound-only oracle's verdict routes
through `production_feasible` and its provenance status is propagated; that
`fleet_by_period` is not read as a gate; and that `BLOCKING_CONTRACT_DIGEST` and
`OPERATIONAL_RECOURSE` are carried.

`OPERATIONAL_RECOURSE` (digest `44a81590ff1b1e81`): reblocking is permitted; no
additional fleet beyond the frozen envelope, and no change to the network,
frequency plan, deadhead assumptions or layover assumptions alongside it.

## Exhaustive enumeration is a one-line instrument

**336.6 µs per ladder combination.** One line is 7.53e6 combinations and 42
minutes; two lines is 5.67e13 and roughly 600 years. Any gap benchmark on
realistic networks must use a reduced neighbourhood, as D33 did. No crossover is
claimed — Gen2 remains at 0.90× exhaustive enumeration on the spaces tested.

**Gen1 is frozen** (`gen1-frozen-v1`) and the bridge has run: verdict
**SUPERSEDED**, Gen1's optimization gap 1.270619 (3.49e-07 relative) over
7,529,536 combinations, leaving 6.1 vehicle-hours of the envelope unspent, at
5,032× the speed.

---

# EXP4N — the normalized rerun: CERTIFIED

`EXPERIMENT4_NORMALIZED_CLOSEOUT.md` is the record. This is the summary.

```
status      EXP4_FULL_NORMALIZED_CERTIFIED     200/200,  §8 gate 44/44
leader      35e351133d6f   3,223,885.9475   21 rounds  65 lines   legacy 154
2nd         d451584c40c6   3,236,362.5736   +0.387006%            legacy 193
legacy #1   ecb2ffc4bcce                     -> NORMALIZED 185 OF 200
spearman    +0.3566        pairwise inverted 7,296/19,900 (36.7%)
spread      4.1710% first to last            (legacy spread 2.2788%)
```

**The one change.** The peak-vehicle envelope is resolved **once**, against the
unedited reference network, before any candidate exists, and passed to every
candidate explicitly — so `exp2.py:324` never resolves `"baseline"` against a
candidate's own geometry. `src/cota_opt` was **not modified**; its content digest
is `add5d0002d29aa49` at the start and the end of the run. Nothing about the
demand model, the objective, the exact evaluator, convergence, ladders,
geometries, the hours cap, the peak *usage* calculation, tolerance or the search
neighbourhood changed. **This is not the optimizer being adjusted to obtain a
better answer**; it is the same optimizer asked a well-posed question.

| | |
|---|---|
| contract digest | `2125984c82b60a83` |
| envelope digest | `3fd5241db44ca9da` |
| candidate-set digest | `38e52f0b14b1d554` |
| `src/cota_opt` digest | `add5d0002d29aa49` |
| tie-break digest | `0297e180cf30369d` |

**Two independent verification channels, both clean.** §6's 21 calibration
controls reproduced **exactly** on objective, rounds and plan — including
`12ab99b5915e` at 44 rounds, the deepest candidate in the field. And the archive
that survived the container loss reproduced **24/24 bit-exact** across 16 fields
plus every per-round trajectory objective. Neither channel was chosen after
seeing the result.

**Rounds: min 11, median 21, mean 22.2, p90 31, max 44 — ceiling 120.** Nothing
came within 76 rounds of the cap, so no result is an uncertified upper bound.
`rounds == MAX_ROUNDS && converged == True` and `rounds == MAX_ROUNDS &&
converged == False` are different statements and are never conflated: the first
is a certificate with zero headroom, the second is not a certificate at all.

**The tie-break decided nothing** — zero exact-objective ties in 200 results.

**Resource use changed, not only the ordering.** Same fields, same cap, both
runs: legacy plans spent 36.16–37.33% of the hours cap and switched off 78.5–86.9% of
route-periods; EXP4N plans spend 99.92–100.00% and switch off 56.2–67.4%. Descriptive, not
preregistered — recorded in `outputs/CANONICAL_RESULTS_v2.json` under
`exp4.resource_use`, computed from the per-candidate results rather than typed.

## The pattern at the top, and why it is only a consistency

The normalized top five carry legacy ranks **154, 193, 192, 194, 191** — almost
entirely from the *bottom* of the legacy ordering. That is consistent with the
endogenous cap: legacy rank partly recorded how generous a candidate's own
self-defined envelope happened to be. **It has not been tested.** The test —
regressing normalized improvement on each candidate's own legacy envelope — is a
separate diagnostic and has not been run. Recorded so nobody later reads the
pattern as a demonstrated mechanism.

## What EXP4N does NOT establish

* **Not that the 0.387006% margin is meaningful.** It is ~204× the D33-B noise
  band, and the band's rule is **asymmetric**: at or below it, the difference is
  noise; above it, a real difference is **not established, only not excluded**.
  D33-B is a local check over at most 10 of 173 route-periods and a *lower bound*
  on the differential-error bound.
* **No fleet claim.** The instrument still returns `UNDECIDABLE` for every
  candidate including this leader. Fleet was REPORTED, NOT GATED.
* **No global optimality.** The `(N,K)` = (8,3) block-local residual is
  unmeasured for every candidate including the leader.
* **Nothing about the 1,800 uncertified proposals**, and nothing about the
  promotion cap, which the out-of-band audit had already shown to be invalid.
* **Nothing about deployability.** D24 is still open.

## `envelope_digest` is not sufficient, and now there is one that is

`envelope_digest` hashes `round(peak, 9)`, so two envelopes differing below the
ninth decimal hash the same — which happened: two hand-transcribed peak values
were wrong in the last ULP during the contract freeze and the digest matched both
times. The bit-exact assertion caught it. `docs/ENVELOPE_DIGEST_INSUFFICIENCY.md`.

EXP4N's own envelope identity never rested on the digest — it was asserted
bit-exactly against the frozen artifact *and* against the `peak_caps` of all 21
accepted calibration results, before launch. `scripts/envelope_fingerprint.py`
(exact fingerprint **`0b46d1abc9a80c80`**, artifact
`outputs/ENVELOPE_FINGERPRINT_V1.json`) now supplies a lossless IEEE-754
fingerprint over the *same four inputs*, for experiments after this one. It is
**additive**: not retrofitted into the frozen contract, not a replacement in any
artifact already written, and **not usable to re-verdict a completed run**. It
lives in `scripts/` precisely so it cannot move `src_cota_opt_content_digest`.
Its self-test replays the ULP pair and shows the rounded digest colliding where
the fingerprint separates.

---

# Experiment 5 — the ORIGINAL design: built, tested, NOT RUN (retired; the reframed experiment ran — see the top of this page)

`src/cota_opt/exp5_resource.py` and `exp5_frontier.py`, 32 tests. Its stated
block condition cleared twice over — Experiment 4 on 2026-09-14, and the EXP4N
certification on 2026-09-28 — and **it still must not run as specified.** But
the premise audit below was measured on the LEGACY Exp 4 plans, and EXP4N moved
one of its three defects outright: under the common envelope every certified
plan spends **99.92–100.00%** of the hours cap (legacy 36.16–37.33%) and switches off 56.2–67.4% of
route-periods (legacy 78.5–86.9%). "No cell binds" was a property of the endogenous
cap. The fleet-axis and proxy-instrument defects were not re-measured.
Re-audit against EXP4N before reframing or running anything. Neither Exp 4 run
established a fleet number.

### The 2026-09-21 OFF→ON diagnostic — the binding constraint is not the one Exp 5 varies

`EXPERIMENT5_OFFON_DIAGNOSTIC.md`. Status `OBJECTIVE_PREFERS_SPARSE_SERVICE` by
the letter of its criteria, with its stated interpretation refuted by the same
measurement. The certified leader's objective was reproduced **bit-exactly**
(relative error 0.000e+00) before any probe was read.

* **Reachability is not the problem.** All **315 OFF route-periods (80.77%)**
  sit **one rung** from service — `build_ladders` appends OFF last, so its
  neighbour is the worst finite headway — and all 315 have two finite rungs
  inside the k=3 window. Zero need more than 3 rungs; zero are unreachable.
* **4,095 exact probes.** 3,076 improve the objective. **Zero are admissible.**
  Every one is blocked by the peak-vehicle arm of `frequency._feasible`; **not
  one** violates the hours cap.
* **The peak-vehicle cap binds everywhere**: am_peak 99.840%, early 99.912%,
  evening 99.705%, midday 99.967%, owl 99.879%, pm_peak 99.840%, tolerance
  **0.0**. Hours sit at **36.658%** with 1,594 vehicle-hours of slack.
* **That cap is read off the candidate's own baseline plan** (`exp2.py:324`,
  `peak_fleet_by_period: baseline`) and measured with `cycle/headway` — the
  project's own named original sin, and the proxy `contract.py:451` refuses.
  **D5-C is therefore not a latent hazard but the operative constraint of
  Experiment 4.**
* **Scope narrowed, ranking intact.** The Exp 4 leader is the best certified
  objective *under a per-candidate vehicle cap read off that candidate's own
  baseline plan and measured with a rejected proxy*. The ranking stands — same
  machinery for all 200, `objective_EXACT` throughout, no fleet verdict filtered
  anything — but that sentence belongs wherever the leader is quoted.
* **Exp 5 as designed is not a resource frontier.** Hours appear nowhere in
  `FitnessVector.scalarized`; they are purely a constraint, and every level from
  0.75× to 1.50× is above the 922.74 operating point. All sixteen cells would
  return the same plan. The axis has to be the resource that binds.
* **The premise audit's own central recommendation is retracted** — zeroing
  `peak_vehicles_by_period` would have removed the only binding constraint.

**A premise audit on 2026-09-21 returned `EXP5_REFRAME_REQUIRED`.** Full
reasoning, with file/function citations and every figure recomputed from the
committed artifacts, in `EXPERIMENT5_PREMISE_AUDIT.md`. In summary:

* **The fleet axis cannot be measured for any candidate.** All 200 Exp 4
  candidates returned `UNDECIDABLE`; their `CANDIDATE_BLOCK_BOUND` brackets run
  253–411 vehicles wide, and **200 of 200 contain the entire Exp 5 fleet-cap
  grid (101–295)**. Every cell is simultaneously possibly-feasible and
  possibly-infeasible for every candidate. The uncertainty is not common-mode:
  widths vary 1.62× and are candidate-specific even at fixed trip count.
* **No cell binds.** Certified plans spend **36.16–37.33%** of the hours cap and
  44.4–45.8% of the fleet proxy cap; **0 of 200 exceed even the 0.75× level**.
  Sixteen certified cells would report that nothing changed. The hours axis
  needs levels below **≈0.37×** to bind at all.
* **The cap would be applied with the wrong instrument.** `frequency._feasible`
  compares `FitnessVector.peak_by_period` (Σ cycle/headway, the 150.73 proxy)
  against `ResourceBudget.peak_vehicles_by_period`, which is the comparison
  `contract.py:451` declines to run because it "would pass every plan while
  appearing to check something." Tolerable in a search filter; fatal where the
  cap *is* the treatment.
* **Open and unanswered:** why **80.8%** of the leader's route-periods are OFF
  while 63% of the hour budget goes unspent. Either the λ=2 objective prefers
  that little service, or the block-local neighbourhood cannot reach denser
  plans (lifting a route from OFF may exceed the 3-rung move the guarantee
  covers). A resource frontier built on the second case would measure the
  optimizer, not the network. Cheap test specified in the audit.

**D38 still applies if a proposal stage is ever added.** Exp 5 as specified
ranks nothing — sixteen cells, enumerated — so no cheap score is used as a
ranker today. The preregistered variance gate is in the audit's §7, along with
the gate run against `FitnessVector.peak_vehicles`: it **passes** on variance
(3.19% relative range against the exact objective's 2.29%) and is **still the
wrong quantity**. The D38 gate is necessary, not sufficient.

The envelope is the same frozen artifact, and the type system enforces it:
`ResourceEnvelope` holds fleet **per period as integers** and **rejects a
one-entry mapping outright** — `{"all": 197}` is a scalar cap in a dict costume,
and a test caught it accepting one. `Exp5Feasibility` refuses a non-block
`fleet_source`. `FLEET_ROUNDING = "floor"`; the superseded continuous proxy is
recorded as `"none_continuous_proxy"` rather than deleted.

`exp5_frontier` supplies treatment isolation, monotonicity, feasibility,
traversal invariance, marginals, diminishing returns and transition matrices.

---

## Operations — 36 rules, each bought with lost work

`OPERATIONS.md`. The costly ones:

* **24 — a batch in flight freezes the code that can change its numbers.** Cost:
  one certification batch and five census states.
* **25 — use a pidfile, never a process-name pattern.**
* **26 — shard the whole list, not the remaining one.**
* **27 — a keeper you never checked is not a keeper.** An hourly trigger had been
  failing at startup on *every* firing while reporting `enabled: true` and a
  healthy `next_run_at`. Nine hours lost to a dead watchdog.
* **28 — this container dies of SESSION idleness, not process idleness.**
* **29 — a wake chain does not survive a foreground hold.**
* **30 — match the wake ladder to what is actually at risk.**
* **31 — checkpoint an expensive result the instant it exists.** An exact
  enumeration ran 41.9 minutes, computed its answer, printed its verdict, and
  died in `json.dumps` on a tuple key with nothing on disk.
* **32 — validate a serializer before the long run, not after it.**
* **33 — a pidfile must hold the pid of the process you want to signal.**
  `setsid nohup cmd & echo $! > pidfile` records *setsid's* pid, not the
  worker's. The keeper then reads a healthy run as dead and starts a second one
  over the same output directory. Fix: `echo $$` inside a `bash -c` that
  `exec`s the worker, then confirm against `/proc/<pid>/cmdline`.
* **34 — `pgrep -cf <pattern>` counts itself.** Its own command line contains
  the pattern, so it never returns 0 and "runner alive: 1" can mean nothing is
  running. Caught only because it contradicted a zero result count.
* **35 — a hold that only reports is not a keeper.** The first hold cycle
  checked and printed and did not restart; it would have left the run dead at
  every 6 h shard boundary.
* **36 — a git operation that prints success may not have moved the ref.**
  Verify with `git ls-remote`, never from a GUI or an exit code.

The recurring shape across 24, 26, 27, 29, 31 and D35: *a mechanism that looks
like it is working is not evidence that it ran.* The §9 amendment is the same
shape once more — a per-period test that would have returned a verdict on every
run, where the verdict was a property of the solver's tie-break.

## Repository

`github.com/ian-gregory94/cota-route-optimization`.

The Experiment 3 history was collapsed from 2,875 commits to 328 with a
**byte-identical tree**; `HISTORY_NOTE.md` and `EXP3_HISTORY_MAP.json` record it.

The sandbox holds no git credential and neither does the VM behind the folder
bridge. **GitHub Desktop has its own token and can push.** The loop: sandbox
bundles → `device_commit_files` into the clone → `git fetch <bundle>` →
fast-forward the local branch → **Push in GitHub Desktop**, which can be driven
by computer control rather than waiting for Ian. `PUSH_TO_GITHUB.md` documents
the traps. Two learned on 2026-09-27/28:

* **`git fetch` from a bundle can print success and not move the ref.** It wrote
  `FETCH_HEAD` in a directory it could not write and reported the fetch as done.
  Use `--no-write-fetch-head`, and **verify with `git ls-remote`** — never from
  the GUI's own display or the fetch's exit code.
* **A failed `gc` leaves a `.lock` on every ref, at any depth.** `find .git
  -maxdepth 2` sweeps none of the deep ones and the next fetch fails with
  "unable to update local ref". The repo now runs with `maintenance.auto=false`,
  `gc.auto=0`, `gc.autoDetach=false`, `fetch.writeCommitGraph=false`.

**Use the clone at `C:\Users\ianjg\OneDrive\Documents\GitHub\cota-route-optimization`.**
The one at `C:\Users\ianjg\source\repos\cota-route-optimization` is stale —
350 commits behind `origin/exp3-clean` as of 2026-09-21 — and earlier versions
of this document pointed at it.

**The bridge VM cannot delete files**, so `git fetch` there leaves
`.git/index.lock` behind and every subsequent GitHub Desktop operation reports
the repository as locked. The fix is to `mv` the lock (and any
`.git/objects/pack/tmp_*`) into a `_to_delete/` folder rather than trying to
remove it.

The files the clone reports as modified are **pure CRLF noise** — 23 at the time
this was first written, 35 as of 2026-09-28, zero changed lines under
`--ignore-cr-at-eol` in every case. Do not commit them. **Check the count each
time rather than trusting this number**; the point is the test, not the total.

**`master` is the main branch, and it is current.** It had fallen 616 commits
behind `exp3-clean`. On 2026-09-28 its four master-only commits were merged in —
history preserved, nothing force-pushed — and `master` was fast-forwarded to the
result, so both branches point at the same commit. Those four commits had added
`HISTORY_NOTE.md`, which is kept, plus 32 git lock/temp files under `_to_delete/`
and six transport bundles at the root, which were debris: gone from the tree,
still in history. Work lands on `master` from here on.

**GitHub is not yet the complete record.** Checked 2026-09-28 against
`git ls-remote`, and re-checked from the container later that day with the same
result: GitHub holds four branches (`master`, `exp3`, `exp3-clean`,
`frombundle`) and **no tags**. At that check `origin/master` was `84d96e0d`, so
the Exp 6 commits were not on GitHub.

* **The five freeze tags** — `exp3-final-v1`, `exp3-frozen-v1`,
  `gen1-frozen-v1`, `pre-exp3-v1`, `pre-exp3-v2` — exist in the clone. Every
  tagged commit is reachable from a GitHub branch, so the code at each freeze
  point is safe; only the *names* this document cites are missing upstream.
* **`backup-exp3-preclean` (`e733daa86`), the pre-collapse Experiment 3
  history, is not on GitHub at all.** Its only durable copies are the older
  `cota-*.bundle` files in Ian's Downloads (25 of them, Sep 1–23), plus
  unreferenced objects in the clone that any future `gc` would be free to
  discard. The cloud container holds neither the tags nor this branch.
* **Consequence: the Gen1 freeze cannot be verified from a GitHub clone.**
  `scripts/gen1_freeze.py --verify` checks that `exp3-frozen-v1` and
  `exp3-final-v1` still point at their frozen commits; without the tags it
  fails. In Ian's clone both point exactly where the freeze recorded.
* **`EXP3_HISTORY_MAP.json`**, cited by `HISTORY_NOTE.md` and in this section,
  is not in any branch on GitHub.

**Do not delete those 25 older bundles** until the tags and
`backup-exp3-preclean` are on GitHub — which needs an explicit push of those
refs (e.g. `git push origin backup-exp3-preclean --tags` from the clone, or from
the container once the repo is in the session's authorized sources and the refs
have been bundled across). The 69 EXP4N checkpoint bundles were deleted on
2026-09-28 only after every one of their heads was proven reachable from
GitHub's `exp3-clean`; the older bundles do not pass that test.

## Known limitations, with sizes

| Limitation | Size | Direction |
|---|---|---|
| Commute-only LODES demand | 24.7% of regional flow transit-accessible | unknown; largest unquantified error |
| **Deadhead travel time** | **unavailable; bracket width 180–212 (18%)** | **still open. Exp 4 ran with fleet REPORTED, NOT GATED; no fleet claim follows from it** |
| **Terminal identity** | **`parent_station` empty in 2,949/2,949 stops; 83.3% of candidate trips stranded** | **still open (D24), reclassified as post-result validation. Exp 4 completed without it** |
| **Discovery ordering (D36, reframed by D38)** | **discovery span 0.159% in band and 0.0077% out of band, against exact spans of 2.28% and 1.73%** | **not an inverted ranker — close to a constant plus noise in the regions measured. The cap selected on a quantity ~1,100× smaller than its own error** |
| **Endogenous peak-vehicle cap (Exp 4)** | **CLOSED for the promoted 200 by EXP4N: 36.7% of pairwise orderings inverted, legacy leader 1 → 185** | **repaired, not merely measured. Exp 4's ordering is superseded; its objective values stand. The mechanism behind the top-of-table reshuffle is a stated consistency, NOT a tested one** |
| **Block-local residual (EXP4N leader included)** | **unmeasured for all 200; (N,K) = (8,3)** | **open, and unchanged by certification. A 0.387006% first-to-second margin under an unmeasured residual is not a durable ordering** |
| **Promotion cap** | **INVALID — an excluded candidate (rank 237) beats the Exp 4 leader by 0.0147%** | **established. Does not tell you what to replace the cap with** |
| **Uncertified proposals** | **1,785 of 2000 never certified; ~326–360 h to close** | **unknown, and D38 argues against paying it: the ranking an expansion would use carries almost no information where it was measured** |
| **Population-level enrichment** | **unanswered; 4 of 5 audit strata empty, the 5th biased to its top third** | **open. Indistinguishable on current evidence from a near-uniform pool** |
| Frontier below λ = 2 | uncertified on both models | quoted from λ = 2 upward |
| Per-route headways | 19–26% seed disagreement | aggregate unaffected; no route-level recommendation |
| Cross-route hyperpath | 0.516% of generalized cost | overstates waiting on trunk routes; deferred |
| Stop cost | unmeasurable from this feed (−157 s/stop, inverted) | blocks any consolidation claim resting on runtime savings |
| Novel-link running time | MAE 17.2 s, bias +0.41% | not exploitable |
| Novel *turns* (D29) | 150/206 candidate lines; crosstown 40/40 | gates Experiment 4 |
| Scheduled ≠ actual | unquantified | no reliability penalty |
| Gen1 frequency optimality | gap 1.270619 (3.49e-07) on the one network measured exactly | leaves envelope unspent; unmeasured at scale |
