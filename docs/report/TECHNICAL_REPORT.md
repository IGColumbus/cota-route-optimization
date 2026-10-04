# How much can frequency, stops and geometry do for a mid-sized bus network? A certified-optimization study of the Central Ohio Transit Authority (COTA)

**Technical report: DRAFT for review, 2026-10-04.**

*Status of this draft.*

* Written from the frozen research record before the `research-final` tag
  (`docs/RELEASE_AND_REPORTING_GUIDELINES.md`, "Release gate").
* Every number is transcribed from a named canonical artifact (Appendix A).
* The automated claims check (`scripts/verify_report_claims.py`) covers the
  headline numbers. It does not yet cover every number, and the release rule
  "every number generated, never typed" is **not yet met**.
* The seven required figures are not yet generated.

> **Model status**
>
> | item | status |
> |---|---|
> | Calibration | **Uncalibrated.** Every cost weight, the retention curve and the unserved-trip penalty are assumptions (`config/`). |
> | Validation | Route volume, stop pattern, transfer behaviour and trip length: **all four `unavailable`.** No observed boardings, transfers or trip-length data were available. |
> | Demand | **Commute only.** LEHD LODES 2022 work trips, scaled to an NTD-anchored 30,949 weekday linked trips. Non-work travel is absent. |
> | Service basis | **Scheduled, not observed.** GTFS static. No reliability term. |
> | Fleet | **No modified plan has a physical vehicle count.** Resource caps are revenue vehicle-hours and a solver peak-concurrency proxy, not buses. |
> | Standing | **Not an operating plan. Not COTA-endorsed.** Independent research using public data. |

---

## Abstract

We ask how much passenger generalized travel cost COTA could save by changing
four things:

* how often each route runs (frequency);
* where routes stop;
* route geometry;
* the network as a whole;

all while holding COTA's current operating resources fixed.

The model is a path-based, frequency-based assignment model of COTA's weekday
network, built from public data:

* GTFS for the schedule;
* LEHD LODES for commute demand;
* the NTD agency profile for system totals.

Its waiting model, Model B, prices a ride on the combined frequency of every
same-route pattern that can carry it. Every comparison runs inside a harness
that certifies solver convergence and admits a comparison only when the
compared runs differ in declared dimensions alone.

**Results:**

* **Frequency redistribution is the only lever that produced a material
  improvement.** Inside the existing routes and 2,517 weekday revenue
  vehicle-hours, it reduces modeled unserved demand by **6.65%** (solver seed
  spread ±0.06; λ = 2). That is about 680 more of 30,949 modeled weekday trips
  served. Total generalized cost rises by 0.88% and cost per served trip falls
  by 2.34%.
* **Route-geometry recombination (through-routing):** no supportable gain. All
  240 feasible combinations of 12 candidates make up a certified null.
* **Mutation search over eight edit kinds:** 29 certified improvements, all
  small (−0.01% to −0.19% of the objective). The certified leader adds a stop on
  route 010 (−0.19%). That is within its own Experiment 7 sensitivity range.
* **Greenfield network design:** the best of 200 candidates is **worse** than
  the existing geometry with re-optimized frequencies, by 8–10% of the
  objective.
* **Service-standard safeguards** (headway floors, span, coverage, area
  preservation) cost 0 to 0.91% of the objective each.

A two-stage robustness experiment perturbed demand, runtimes, cost weights,
walking friction, route availability and the retention curve:

* **Fixed plans:** the frequency result keeps its sign at every level
  (−1.9% to −7.0%).
* **Re-optimizing under the same service rules** (no route-period switched off;
  post hoc): it keeps its sign at every λ ≥ 2 level re-optimized (−2.1% to
  −7.0%). At λ = 1 it is +0.12%.
* **Re-optimizing while permitting service to be switched off:** unserved
  demand is no longer identified by the objective. Two certified plans 0.16%
  apart in objective give −5.4% and +30.5% at the base assumptions. At λ = 1 the
  optimizer nearly empties the network.

Two methodological results generalize beyond Columbus:

1. Ranking network changes at a fixed nominal search effort is not enough.
   Convergence has to be matched, or the comparison measures the search rather
   than the network. That error produced and then withdrew a headline twice.
2. A resource cap read from each candidate's own baseline turns a geometry
   ranking into a ranking of self-chosen budgets. Fixing it alone inverted 36.7%
   of 19,900 pairwise orderings.

---

## 1. Question and scope

> Holding COTA's approximate current operating resources constant, how much can
> passenger generalized travel cost be reduced through improved frequency
> allocation, transfer timing, stop structure, and route topology?
> (`AGENTS.md`, Mission.)

The study is a **modeled** answer:

* It sizes what the current resource envelope makes possible under stated
  assumptions.
* It measures how much of that answer survives when the assumptions move.

It does not propose a timetable. Section 5.1 shows that the frequency optimum
is flat: plans differing on about 19% of route-periods score within 0.06
points. No individual route's headway is identified, and none is recommended
here (reporting rule 8).

Seven experiments ran in sequence, each preregistered before its production
run (`ACCEPTANCE.md`, the per-experiment contracts):

| # | question | status |
|---|---|---|
| 1 | Frequency redistribution, geometry fixed | Closed, certified (λ ≥ 2) |
| 2 / 2B | Through-routing (splice) geometry, singly and in all feasible combinations | Closed: no supportable claim / certified null |
| 3 | Route mutation over eight edit kinds | Closed, one certified leader |
| 4 / 4N / 4A | Greenfield network design at scale; normalized rerun; original-question comparison | Closed: ordering superseded by 4N; greenfield worse (4A) |
| 5 | Modeled operating-resource frontier on two geometries | **Failed** its monotonicity gate (on N4 only); N0 half informative |
| 6 | Modeled price of service-standard safeguards | Closed, certified |
| 7 | Robustness of findings F1–F6 to model assumptions | Closed: Stage 1 and Stage 2 complete |

## 2. Data and provenance

| input | source | validation |
|---|---|---|
| Schedule | COTA GTFS static, feed `2026-MAY-04-BB_20260630`; representative weekday 2026-05-26 | `validate_feed`: 0 errors, 0 warnings |
| Demand | LEHD LODES8 `oh_od_main_JT00_2022`: 4,640,957 block pairs → 317,706 block-group pairs → 823,915 commute trips | Scaled to an assumed **30,949** weekday linked transit trips (NTD-derived); top 20,000 OD pairs; six period shares assumed (LODES has no time dimension) |
| Zones | 2020 Census block-group population-weighted centroids | — |
| System totals | FTA NTD 2024 agency profile, agency 50016, motorbus directly operated | The parser **refuses** unless it reproduces all 18 of the profile's printed ratios |
| Physical fleet (baseline only) | GTFS `block_id` reconstruction: **197** peak vehicles at 17:13, 284 blocks | NTD VOMS 198; nothing tuned |

Every input enters through an immutable registry: SHA-256 checksum, retrieval
timestamp and source record in `config/sources.yaml`. Raw data is re-fetched,
not committed. Model baseline revenue vehicle-hours reproduce the GTFS schedule
as an identity, asserted at run time to 1e-9.

## 3. Model

**Network and decisions.**

* The decision unit is the route-period. N0, the existing geometry, has 173
  route-periods across 39 routes. Each takes one headway from a discrete ladder
  (5–60 min).
* **Experiment 1 rules:**
  * a route-period with baseline service keeps service;
  * no headway may exceed max(60 min, baseline);
  * 14 peak-only express routes are locked as a class (D4).
* **Experiments 4–7** use a certifier that may also switch route-periods OFF
  (`allow_off`), unless a policy cell forbids it.

**Path assignment.**

* RAPTOR enumerates up to 4 candidate paths per OD pair and period, with up to
  2 transfers, a 600 m access radius, a 400 m transfer-walk radius and
  80 m/min walking.
* Enumeration is widened by frequency scenarios until the improvable flow share
  converges (fixpoint, D6).
* Passengers take the cheapest enumerated path, all-or-nothing.
* A retention curve drops a share of trips whose generalized cost exceeds
  60 min, falling linearly to a floor of 0.10 at 210 min. Dropped trips are
  *unserved*.

**Waiting (Model B).**

* A ride leg is priced at the combined frequency of every same-route pattern
  that serves the boarding stop and then the alighting stop:
  mult = 1 / Σ_q (n_trips(q) / n_direction_trips(q)).
* Model A, the chosen pattern's own headway, is the one-pattern special case.
  It undervalues frequent trunk service and was retired as the evaluator (D10,
  D12).
* Cross-route common lines are not modeled. The omission is bounded at 0.516%
  of generalized cost on N0 (12.47% on N4).

**Generalized cost**, in in-vehicle-minute equivalents (`config/cost_weights.yaml`):

| component | weight |
|---|---|
| walking | 2.0 |
| waiting | 2.0 |
| in-vehicle time | 1.0 |
| transfer wait | 2.0 |
| per-transfer penalty | +10 min |

**Crowding** does not bind at this demand: the median peak-load-point bus is at
9% of capacity (D5).

**Objective.** minimize GC + λ · w_unserved · unserved, with w_unserved = 60
min and λ = 2 unless stated.

* The objective has **no operating-cost term.** Operating resources enter only
  as constraints.
* Below some λ it therefore prefers dropping a hard-to-serve rider to serving
  them (§6.2).
* Experiment 1's frontier is certified only from λ = 2 upward. The λ ≤ 1 corner
  fails the path-set adequacy test on both waiting models (D15).

**Resource envelope.** Experiments 4N–7 use the EXP4N common envelope:
`outputs/exp4_normalized/COMMON_RESOURCE_ENVELOPE.json`, rounded digest
`3fd5241db44ca9da`, exact fingerprint `0b46d1abc9a80c80` in
`outputs/ENVELOPE_FINGERPRINT_V1.json`. It has two parts:

* 2,517.18 weekday revenue vehicle-hours;
* six per-period caps on the solver's peak-concurrency proxy (Σ cycle/headway).
  The caps are 85.28, 162.01, 159.17, 176.49, 140.19 and 35.56, from early
  through owl.

`outputs/CANONICAL_ENVELOPE.json` is a different artifact. It holds the
block-derived **physical** per-period vehicle counts of the existing schedule
(135–197), which apply to the baseline only.

The proxy is **not a vehicle count**:

* it reads 176.49 at the baseline PM peak, about 10% below the 197 physical
  vehicles, because it does not model interlining
  (`CANONICAL_ENVELOPE.json` → `NOT_THE_CAP`);
* the blocking instrument cannot certify any modified plan (§8).

All resource statements in this report are therefore in revenue vehicle-hours
or proxy units.

## 4. Harness

**Contracts and preregistration.** Each experiment freezes, before its
production run:

* a contract: digests of the code, envelope, candidate set and acceptance
  gates;
* its acceptance rules (`ACCEPTANCE.md`).

Amendments are separate, dated documents. Nothing is waived after the fact. A
failed gate is reported as a failure (Experiment 5).

**Semantic comparison firewall** (`ARCHITECTURE_FIREWALL.md`):

* Every field of an evaluation carries a semantic class: identity, opportunity,
  outcome or none.
* A treatment effect is computed only if the two runs differ in dimensions the
  contract explicitly permits. That is a whitelist, not a blacklist.

The firewall cannot prove that a permitted difference was actually applied.
D35 is a constraint that was hashed into identity but never reached scoring.

**Certification.**

* *Experiments 1–3:* a Gen1 exchange search with perturbation restarts at
  400,000 iterations.
  * 20 restarts, with three or five seeds.
  * Exp 3's preregistered escalation used 40 restarts for 23 of its 29 certified
    verdicts.
* *Experiments 4–7:* an exact (8, 3)-block-local certifier
  (`src/cota_opt/exp4_certify.py`).
  * Route-period keys are partitioned into blocks of 8, rotating by 4 each
    round.
  * Each block is enumerated exhaustively over a 3-rung window: the current
    rung and one either side.
  * Rounds repeat until no block improves. The guarantee is (8, 3)-block-local
    optimality.
  * The round ceiling is 40 by module default (legacy Exp 4). The EXP4N, 4A,
    5, 6 and 7 contracts set it to 120. Convergence is mandatory.
* *Experiments 6–7* add a declared **basin closure**:
  * certified plans are transferred as anchors along a frozen nesting graph,
    and across levels;
  * re-certification continues until a fixed point;
  * a fixed point is not a global optimum.

**Reproducibility.** Order sentinels re-run cells in reversed order and must be
bit-exact. Runs checkpoint per cell and resume. Generations of methodology are
frozen (`METHODOLOGY.md`), and a newer algorithm reopens an old result only on
evidence.

## 5. Results

All results are on the λ = 2 objective unless stated. "Certified" means
distinguishable from solver variance at the stated effort. It does **not** mean
real-world significance (reporting rule 3).

### 5.1 Experiment 1: frequency redistribution (geometry fixed)

The headline is three seeds at 400,000 iterations × 20 restarts on one frozen
243,257-path set (`outputs/canonical/exp1_final.json`, commit `f1a05645`).

| quantity | change vs current plan | solver seed spread (SD) |
|---|---|---|
| unserved demand | **−6.65%** | ±0.06 |
| trips served | +3.30% | ±0.03 |
| total generalized cost | +0.88% | ±0.04 |
| generalized cost per served trip | −2.34% | ±0.01 |

* In modeled trips, at the λ = 2 frontier point, unserved demand falls from
  10,262 to 9,583 and served trips rise from 20,687 to 21,366 (of 30,949).
* The plan uses 2,516.5 of 2,517.2 revenue vehicle-hours.
* The plan stays within the baseline's per-period peak-concurrency proxy. Its
  physical fleet requirement is **not** measured
  (`CANONICAL_RESULTS_v4.json → reporting_corrections`).

**The frontier across λ:**

| λ | unserved vs current plan | certified? |
|---|---|---|
| 2 | −6.60% | yes |
| 4 | −7.12% | yes |
| 8 | −7.25% | yes |
| 16 | −7.28% | yes |
| 1 | −1.42% | no |
| 0.5 | +6.85% | no |

Below λ = 2 the path set fails its adequacy test (D15).

**The aggregate is identified; the plan is not.**

* Independent seeds produce plans differing on 19.1% of the 173 route-periods
  (worst pair 19.7%), by a mean of 6.9 minutes, while scoring within 0.064
  points of each other (D17).
* The optimum is flat. That is a constructive result: many concrete timetables
  realize the same aggregate benefit, so unmodeled operational constraints can
  likely be met at little cost.

**Where service moves.** Frequency moves from the most frequent routes toward
the 30–120-minute tier (D1). Returns plateau quickly as search effort grows
(D2).

### 5.2 Experiments 2 and 2B: through-routing geometry

Twelve splice candidates (two routes merged at a shared stop) were screened
from 60 and evaluated with frequency re-optimized on each network
(`EXPERIMENT2_CLOSEOUT.md`).

* **Singles:** six of twelve do measurable harm, and none does measurable good
  at Experiment 1's certification effort. The two best singles land inside the
  0.287-point noise floor (+0.060%, +0.160%).
* **Combinations (2B):** all 240 structurally feasible subsets were solved.
  * Not one of the 227 multi-edit sets beats the best single.
  * At λ ≥ 2, every one *substitutes*: it delivers less than its members
    promised separately.
  * The leader, re-solved at certification effort under three seeds, scores
    +0.0065% unserved, 0.02 noise floors.
  * The null holds at λ ∈ {1, 2, 4} (D22, D25).

The mechanism is the shared envelope. A merged line is longer, so hours that
were buying frequency go into running it (D20, D26).

### 5.3 Experiment 3: route mutation

84 census states across eight edit kinds went through Stage A. 39 were promoted
and 30 certified at Stage B (20 restarts). **29 remain certified** after a
preregistered escalation (40 restarts) (`EXPERIMENT3_CLOSURE.md`, tag
`exp3-final-v1`).

| leader | effect | stability |
|---|---|---|
| `add_stop-010#22c4c35ac5b2` | **−0.18657%** of the objective | \|mean Δ\| / SD = 78.6 over five paired seeds |

* The leader is distinguishable from all 28 other certified candidates.
* **Regime split:** 23 of 29 certified carry 40-restart verdicts. 6, including
  the leader, carry 20-restart verdicts.
* The mechanism is not established.
* Experiment 7 places the effect within its own sensitivity range, so it is
  reported as **within model uncertainty**.

### 5.4 Experiment 4: greenfield network design

A proposal generator produced 2,000 candidate networks. Under discovery-score
ranking, 200 were promoted and certified by the exact certifier.

* **The legacy ranking is superseded.** It resolved each candidate's peak cap
  against that candidate's own baseline plan, so each was optimized inside a
  budget it drew for itself.
* **EXP4N** re-certified all 200 under one common envelope (`src/cota_opt`
  byte-identical):

| | value |
|---|---|
| leader | `35e351133d6f` at 3,223,885.9475 (legacy rank 154) |
| margin to second | 0.387006% |
| legacy leader | now rank **185 of 200** |
| Spearman (legacy vs normalized) | +0.3566 |
| pairwise orderings inverted | 7,296 of 19,900 (36.7%) |

  (`EXPERIMENT4_NORMALIZED_CLOSEOUT.md`)
* **Experiment 4A asked the original question under the same contract:** does
  the best greenfield network (N4) beat the Experiment 3 redesign (N3)?
  * **No:** obj(N4) − obj(N3) = **+9.66% of N3** (firewall-admitted).
  * It survives an omission-corrected costing (+7.87%) and every fixed-plan λ
    above 1.087.
* **The promotion cap was invalid.** An out-of-band audit found an excluded
  proposal (discovery rank 237) that certifies 0.0147% better than the legacy
  leader. That comparison was made under the legacy per-candidate envelope.
  * Discovery scores were close to a constant plus noise in the measured
    region (D36, D38).

### 5.5 Experiment 5: modeled operating-resource frontier

Two resource axes were run: revenue vehicle-hours, and the solver's
peak-concurrency proxy. They were scaled from 75% to 150% in three arms (joint,
hours only, peak only), giving 16 cells on each of N0 and N4.

* **Status: `EXP5_MONOTONICITY_FAILURE`.** On N4, 12 of 99 nested pairs regress
  by up to 1.70%: a looser budget certified a worse plan.
  * The cause is start-basin dependence of the block certifier (D39).
  * The residual is at least 1.70% on N4, about 4.4× EXP4N's
    first-to-second margin.
* **N0, informative though not certified as an experiment:** all 99 pairs are
  monotone.
  * Both axes bind at today's levels.
  * Above 100%, only the peak proxy binds: extra hours alone change nothing.
  * Cutting hours costs +0.57% (to 90%) and +2.05% (to 75%) of the objective.
  * Adding peak-proxy capacity with hours fixed helps, with diminishing
    returns: −0.74%, −0.94% and −1.48% at 110%, 125% and 150%.
* **N4 is worse than N0 at all 16 cells**, by 8.07–11.59%
  (`EXPERIMENT5_CLOSEOUT.md`).

### 5.6 Experiment 6: modeled price of service-standard safeguards

Safeguards were imposed one at a time on N0 and N3, with basin closure
(`EXPERIMENT6_CLOSEOUT.md`). Every regime is a **study safeguard**: none has a
documented COTA numeric anchor, so none is COTA policy or a Title VI
determination.

**Modeled price** (closed cell − closed reference, % of objective):

| safeguard | N0 | N3 |
|---|---|---|
| OFF-share cap 25% / 10% | 0 (non-binding) | 0 |
| OFF-share cap 5% | +0.212% | +0.250% |
| coverage, c = 0.05 / 0.01 | +0.244% / +0.428% | +0.321% / +0.477% |
| ¾-mile area preservation | +0.440% | +0.485% |
| 60-min headway floor (also span, coverage c = 0, both bundles) | +0.482% | +0.524% |
| 30-min headway floor | +0.575% | +0.634% |
| 20-min headway floor | +0.912% | **infeasible under the modeled envelope** |

* **Closure mattered.** Greedy-only prices differed from closure-adjusted ones
  by −0.162 to +0.124 percentage points. They included two impossible negative
  prices.
* **The objective is flat.** Closure moved both unconstrained references
  0.13–0.16% in objective to plans serving about 4,600 more trips (+28%), at
  about 45% more generalized cost. Served-trip and GC figures from any
  single-basin run are therefore basin-dependent.
* **N3 vs N0:** N3 is better than N0 in all 13 comparable cells, by 0.15–0.23%.

## 6. Robustness: Experiment 7

Experiment 7 declared 49 assumption levels and ran 47:

* 44 in seven implemented Class A dimensions;
* one Class B level (cross-route common lines);
* two additional sensitivities (wider OD coverage, more RAPTOR rounds).

The two A4 reliability levels were declared but not implemented. Only Class A
levels label findings:

| dimension | what it perturbs |
|---|---|
| A1 | added non-commute demand on commute pairs |
| A2 | 20 LODES bootstrap draws |
| A3 | runtimes ×1.1 and ×1.2, lognormal noise |
| A4 | reliability: **UNIMPLEMENTED** |
| A5 | λ = 1 and 4; transfer penalty ×0.5 and ×2 |
| A6 | walking speed and walking radii |
| A7 | removing each of the 10 busiest routes |
| A8 | the retention curve |

It ran in two stages (`EXPERIMENT7_CLOSEOUT.md`):

* **Stage 1:** every certified plan (60-entry registry) evaluated unchanged on
  four network variants at every level: 192 cells, all complete.
* **Stage 2:** re-optimization with basin closure in the two dimensions a
  preregistered metric selected from Stage 1, namely A5 (objective weights)
  and A6 (walking).
  * Five closures reached their fixed points.
  * 4/4 sentinels were bit-exact.
  * 0 of 840 monotonicity violations.
  * Every reported comparison was firewall-admitted.

### 6.1 Findings table

Stability words follow the preregistered bands. Worst bands are against
BASE.

| finding | certified | Stage 1 (fixed plans): sign / range / worst | Stage 2 (re-optimized) |
|---|---|---|---|
| **F1** frequency: unserved vs current plan | −6.65% | **SIGN_ROBUST**; −6.998 to −1.897%; worst A6_MAXWALK75 (68.5%) | Preregistered (may switch service OFF): SIGN_SENSITIVE, −6.8% to +182%; **basin-dependent, not identified** (§6.2). Post hoc, under Exp 1's rules: −2.1% to −7.0% at every λ ≥ 2 level re-optimized, +0.12% at λ = 1 |
| **F2** splice null | +0.0065% | Preregistered label SIGN_SENSITIVE (range −0.226 to +0.166%; worst A3_RTNOISE). The effect stays within a few tenths of a percent of zero, and the null test against the Exp 2B floor holds at every applicable level | not re-optimized |
| **F3** add_stop leader | −0.187% | SIGN_SENSITIVE via the rank-mismatched A7_RM05 only; SIGN_ROBUST without it; range −0.41 to +0.32% | not re-optimized |
| **F4** N4 − N3 | +9.66% | SIGN_SENSITIVE (flip only at λ = 1); −1.31 to +19.35% | +6.8% to +30.8% at every λ ≥ 2 level; −0.98% at λ = 1 |
| **F5** resource marginals | — | sign changes only at λ = 1; magnitudes highly sensitive to λ | not re-optimized |
| **F6** safeguard prices | 0 to +0.91% | N0 11 of 13 SIGN_ROBUST; N3 5 of 12 (most flips at λ = 4) | non-negative everywhere; ranking unchanged at transfer ×0.5; R2 floors become binding at λ = 1, transfer ×2 and walking levels |
| **AF1** N3 − N0 at matched policy | −0.23% | SIGN_SENSITIVE, chiefly via A7_RM05 | N3 better by 0.16–0.31% at every λ ≥ 2 level; tie at λ = 1 |

### 6.2 The objective's boundary

**Unserved demand is not identified when service may be switched off.** The
N0 REF cell at the base assumptions (λ = 2) was closed independently on two
Stage 2 tracks:

| track | objective | F1 | route-periods OFF |
|---|---|---|---|
| F6 | 2,940,186 | −5.43% | 17 |
| F4 | 2,935,446 (0.161% better) | **+30.5%** | 48 |

Both are certified fixed points. This is Experiment 6's flat objective,
appearing directly in F1. Plans a fraction of a percent apart in objective
differ by tens of percent in unserved demand. The preregistered F1 adaptive
values are therefore basin-dependent
(`outputs/exp7/EXP7_F1_DECISION_SPACE.json`, `docs/EXPERIMENT7_CLOSEOUT_ERRATA.md`
E3).

**At λ = 1 the network nearly empties.** One basin of the flat λ = 2 objective
is shown for comparison:

| | N0 at BASE (F6-track basin) | N0 at λ = 1 |
|---|---|---|
| revenue vehicle-hours | 2,516 | 557 |
| route-periods OFF | 17 | 139 |
| trips served (of 30,949) | 21,091 | 1,583 |
| generalized cost | 1,757,243 | 69,305 |
| unserved demand | 9,858 | 29,366 |

* At λ = 1 an unserved trip costs 60 while a served trip averages 83–86 GC.
  With no operating-cost term, removing service lowers the objective.
* Doubling the transfer penalty, or adding walking friction, tips the same
  trade more gently. Hours stay fully used, but the re-optimized plan (F6-track
  basin) serves fewer trips than the current plan at the same level:

| level | re-optimized plan | current plan |
|---|---|---|
| transfer penalty ×2 | 14,263 | 19,450 |
| slower walking | 18,324 | 20,118 |
| shorter walking radii | 13,537 | 14,301 |

  At the shorter radii, most of the drop comes from the level itself rather
  than from shedding.

* Every positive F1 value coincides with 38–139 route-periods switched off.
  Under Experiment 1's own rules none is switched off. There, F1 holds at every
  λ ≥ 2 level re-optimized and is +0.12% at λ = 1
  (`docs/EXPERIMENT7_F1_ADDENDUM.md`, post hoc, one closure per cell).

**Two readings follow.**

1. The frequency result is robust **as a policy that keeps every route-period
   in service** (post hoc, at the levels re-optimized).
2. Any future objective that allows service cuts needs one of three things:
   * an operating-cost term;
   * a coverage term;
   * a service-preservation rule.

   Otherwise unserved demand is not identified, and at low λ the optimizer
   rediscovers the degenerate trade.

## 7. Methodological findings

Ordered by how much each would mislead a study that skipped it.

1. **Route-level scoring overstates network gains roughly threefold (D3).**
   * The same λ = 4 frequency plan, scored without path re-assignment, cuts
     unserved demand by **22.71%** while saving 0.76% cost.
   * Scored with path assignment, it cuts **7.16%** at +2.51% cost.
   * All seven route-level plans are dominated at matched effort.
2. **Matched effort is necessary, not sufficient; match convergence (D24).**
   * The 0.5% through-routing benefit was the search, not the network.
   * The unedited baseline was the under-optimized side at ranking effort.
   * A benefit that shrinks with search effort probably was never there.
3. **The optimizer was chosen by the treatment (D27).**
   * A snapped incumbent rejected as infeasible fell back to a greedy
     construction, a different optimizer, depending on the edit.
   * A warning was logged each time but never counted. The fallback rate
     correlated with score (r = −0.711).
   * The corrected 84-state census reordered the edit-kind ranking outright
     (`STATE_OF_PLAY.md`, D27).
4. **The evaluator reported one waiting model and ran another.**
   * For three days Experiment 2 was scored under Model A while reporting
     Model B. Six of twelve candidates changed sign (D23).
   * Every artifact now records the evaluator it actually used.
5. **Self-drawn budgets rank budgets, not designs.**
   * A per-candidate peak cap read from the candidate's own baseline inverted
     36.7% of pairwise orderings.
   * It moved the leader from rank 1 to rank 185 of 200 (EXP4N).
6. **Discovery proposes, exact optimization decides.**
   * Inside the promoted band, discovery scores spanned 0.159% while exact
     objectives spanned 2.28%. The cap selected on noise.
   * An excluded proposal beat the promoted leader (D36, D38).
7. **Start basins matter at the scale of the effects (D39, Exp 6).**
   * Single-start certification left residuals of ≥1.70% on a greenfield
     network and 0.13–0.16% on N0/N3, the same order as policy prices.
   * Declared basin closure removes the monotonicity violations this causes
     within a nested grid. It does not remove basin dependence. Independent
     closures of the same cell in Exp 7 reached fixed points 0.16–0.40% apart
     (§6.2).
8. **A constraint can be a label (D35).**
   * A field hashed into identity reached nothing that scores.
   * The firewall would have admitted a zero effect for an unapplied treatment.
9. **Rounded digests can collide.**
   * Two envelopes differing in the last ULP hashed identically.
   * A lossless IEEE-754 fingerprint now accompanies the digest.
10. **The decision space must match the claim (Exp 7).**
    * Re-optimizing a finding in a larger decision space than it was certified
      in (service may be switched off) produced apparent reversals.
    * Matching the space removed them.

## 8. Limitations, with size and direction

| limitation | size | direction / consequence |
|---|---|---|
| Commute-only demand | 24.7% of regional commute flow is transit-accessible; top 20,000 pairs are 64.9% of that; non-work travel absent | Unknown. The largest unquantified error. Exp 7 A1 tested added non-commute demand on commute pairs only |
| Uncalibrated parameters | cost weights, unserved penalty, retention curve all assumed | Exp 7 A5/A8 bound some. λ and the unserved penalty determine whether the objective is well posed (§6.2) |
| Scheduled ≠ observed | not quantified; reliability (A4) unimplemented | No reliability claim |
| Physical fleet | Not measured for any modified plan. The Exp 1 plan is NOT MEASURED, and all 32 Exp 5 diagnostic cells are UNDECIDABLE. The blocking materializer misses the plans' own vehicle-hours by 17.8–22.7% (N0) and 45.6–47.0% (N4); deadhead and terminal identity not public | No bus, fleet or deployability claim, including for Exp 1 |
| Per-route identification | 19.1% route-period disagreement across seeds | Only aggregates are reported |
| Cross-route common lines | 0.516% of GC on N0; 12.47% on N4 | Overstates waiting on trunk routes; larger on N4 |
| Stop cost | unmeasurable from this feed (−157 s/stop, inverted) | No stop-consolidation claim based on runtime savings |
| Novel-link runtimes | MAE 17.2 s, aggregate bias +0.41%, median APE 20.5% | Unbiased in aggregate; Exp 7 A3 bounds it |
| Local, not global, optimality | (8, 3)-block-local; closure fixed points | Better plans may exist in any cell (Exp 6 flat objective) |
| λ ≤ 1 | uncertified (D15); degenerate under OFF-permitting re-optimization | Quote from λ = 2 upward |

## 9. Retractions and protocol amendments

| # | claim withdrawn or amended | why | now |
|---|---|---|---|
| R1 | Model A as evaluator | undervalues frequent trunk service (D10) | Model B (D12) |
| R2 | an ablation run at a 20× lower effort than its comparator | effort mismatch biased the comparison | matched-effort ladder (convergence study) |
| R3 | "0.9% from through-routing" | the evaluator was Model A under a Model B label (D23) | 0.5%, then withdrawn (R4) |
| R4 | "0.5% from through-routing" | baseline under-optimized at ranking effort (D24) | 0.0%; certified null (2B) |
| R5 | Exp 4 legacy geometry ordering | self-drawn peak caps | EXP4N ordering; legacy objective values stand |
| R6 | "no additional buses" (Exp 1) | both 197.0 figures were one proxy | "within the baseline's peak-concurrency proxy; physical fleet not measured" |
| R7 | Exp 5 original design | hours were not slack once plans were normalized | retired; reframed design ran and failed its gate |
| R8 | Exp 6 first analysis (firewall refused 33) | receipt put the winning basin in an opportunity field | Amendment 2; 25/25 + 13/13 admitted |
| R9 | Exp 7 walk/access "harness-build key" refusal | the knob does reach the evaluator | corrected in amendment §14 |
| R10 | Exp 7 mixed-level comparison admitted in development | level not bound into receipts | level digest in `data_digest` |
| R11 | "F1 is not robust under re-optimization" (stated informally 2026-10-04) | compared a larger decision space than Exp 1 was certified in | preregistered result stands as SIGN_SENSITIVE; post hoc addendum shows F1 holds under Exp 1's rules at λ ≥ 2 |
| R12 | Exp 7 closeout: F1 re-optimized "holds where the unserved penalty dominates"; 26 priced F6 cells; "exactly three" post-freeze changes | Independent closures of the same REF cell reached F1 −5.4% and +30.5% at BASE; the count of cells and the diff list were off | `docs/EXPERIMENT7_CLOSEOUT_ERRATA.md` E1–E6; closeout left unchanged because it is registered |

## 10. Using this with better data

Each assumption above has a defined entry point (`docs/RELEASE_AND_REPORTING_GUIDELINES.md`,
"Data interfaces"):

* **Demand.** A new OD source is a new `odmatrix` constructor. Examples are
  APC-derived OD, fare-card chains, the MORPC regional model and on-board
  surveys.
* **Runtimes and reliability.** AVL or GTFS-Realtime (a collector exists in
  `cota_opt.realtime`) would replace scheduled runtimes and populate the
  reliability term.
* **Fleet.** A COTA deadhead matrix and terminal table would let the blocking
  instrument reach FEASIBLE for a modified plan.
* **Calibration.** Fare-card chains and surveys calibrate the retention curve
  and penalties. Validation is a four-dimension, per-dimension status, never a
  single flag.

Certification cells are independent, so the work is trivially parallel. The
pace of this study was a property of a two-core container, not of the method.

## 11. Conclusion

At COTA's current resources, under a commute-only proxy demand and an
uncalibrated cost model:

* **Re-timing frequencies inside the existing routes is the one lever that
  materially reduced unserved demand**, by about 6%.
* That result survives every assumption perturbation tested for the certified
  plans. Under the same service-preservation rules it also survives
  re-optimization at every λ ≥ 2 level tested (post hoc).
* When service may be switched off, the objective no longer identifies unserved
  demand.
* Recombining routes did nothing, editing them did almost nothing, and the best
  greenfield design did worse.

The most transferable result is methodological. Several plausible network gains
in this study were artifacts of the following:

* unmatched convergence;
* mislabelled evaluators;
* self-drawn budgets;
* start basins;
* mismatched decision spaces.

A harness that preregisters, certifies convergence and admits only declared
differences is what separated those artifacts from the one result that held.

---

## Appendix A. Source of every headline number

| number | artifact | key |
|---|---|---|
| −6.65% ±0.06, +3.30%, +0.88%, −2.34% | `outputs/canonical/exp1_final.json` | `headline` |
| 10,262 → 9,583 unserved; 20,687 → 21,366 served; frontier by λ | `outputs/canonical/exp1_final.json`, `outputs/exp1_baseline_modelB.json` | `frontier[λ=2]`, `baseline_unserved` |
| 19.1% / 19.7% / 6.9 min | `outputs/canonical/exp1_final.json` | `plan_disagreement` |
| 2B leader +0.0065%; 240 / 227 | `outputs/CANONICAL_RESULTS_v5.json` | `experiments.exp2b.headline` |
| −0.18657%, 78.6, 29 certified | `outputs/CANONICAL_RESULTS_v5.json` | `experiments.exp3.headline` |
| EXP4N leader, margin, Spearman, 36.7% | `outputs/exp4_normalized/EXP4N_RANKING.json` via `experiments.exp4.headline` | — |
| +9.659% | `outputs/exp4_addendum/DELTA43.json`; indexed in `outputs/CANONICAL_RESULTS_v5.json` | `experiments.exp4a.headline` (registry) |
| Exp 5 cells | `outputs/exp5/EXP5_ANALYSIS.json` | `EXPERIMENT5_CLOSEOUT.md` §3 |
| Exp 6 prices | `outputs/exp6/EXP6_ANALYSIS.json` | `EXPERIMENT6_CLOSEOUT.md` §10 |
| Exp 7 Stage 1 | `outputs/exp7/stage1/EXP7_STAGE1_ANALYSIS.json`, `outputs/exp7/EXP7_CLOSEOUT_TABLE.json` | `rows` |
| Exp 7 Stage 2 | `outputs/exp7/EXP7_ANALYSIS.json` | `f1_adaptive`, `f4`, `af1_n3_minus_n0`, `f6_ranks` |
| Exp 7 post hoc F1; two REF fixed points | `outputs/exp7/EXP7_F1_DECISION_SPACE.json` | `rows[].cells.R1_H60`, `rows[].ref_f4_track` |

The registry `outputs/CANONICAL_RESULTS_v5.json` indexes every experiment's
canonical and superseded artifacts. `outputs/SUPERSEDED.md` indexes retired
ones.

## Appendix B. Glossary

* **Route-period:** one route in one of six service periods (early, AM peak,
  midday, PM peak, evening, owl). The unit a headway is set on.
* **Generalized cost (GC):** passenger travel time in in-vehicle-minute
  equivalents, with walking, waiting and transfers weighted.
* **Unserved demand:** modeled trips lost through the retention curve or with
  no path.
* **λ:** weight on unserved demand relative to GC in the objective.
* **Peak-concurrency proxy:** Σ over routes of cycle time ÷ headway in a
  period. A solver resource cap, **not** a bus count.
* **Certified:** converged and distinguishable from solver variance at stated
  effort. Not real-world significance.
* **Basin closure:** transferring certified plans as starting anchors between
  related cells until nothing improves.
* **Study safeguard:** a constraint chosen by the study, not documented COTA
  policy.
* **N0 / N3 / N4:** existing geometry / N0 plus the Exp 3 add_stop edit /
  the EXP4N greenfield leader.

The full glossary is `docs/GLOSSARY.md`. The decision log is `DISCOVERIES.md`
(D1–D39).
