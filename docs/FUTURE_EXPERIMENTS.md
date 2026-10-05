# Future experiments

*Proposed 2026-10-04, after Experiment 7 closed. **None of these is
pre-specified**: each needs its own contract, acceptance gates and freeze
before it runs, as Experiments 1–7 had. They are ordered by how much they could
change the study's answer, not by cost. Item numbers (E8–E21) are independent
of the row numbers in `docs/EXPERIMENT7_CLOSEOUT_ERRATA.md`; "errata E16"
always means the errata row.*

The study's current answer:

* Frequency reallocation was the only tested lever to produce a large
  favorable effect under its own study metric: ~680 more modeled weekday
  trips served, unserved demand −6.65% (Experiment 1). Cross-lever effect
  sizes are not formally comparable because model instances differ.
* It keeps its sign at every implemented Stage 1 level for the certified
  plans (SIGN_ROBUST; magnitude Highly sensitive to walking friction).
  Re-optimized in the closest cell to Experiment 1's service rules (R1_H60: no
  route-period switched off, 60-minute maximum headway; study safeguards, not COTA policy), F1 is
  −2.1% to −7.0% at every λ ≥ 2 level re-optimized in Exp 7 (A5 and A6 only),
  with one closure per cell. Post hoc (`docs/EXPERIMENT7_F1_ADDENDUM.md`). At
  λ = 1 it is +0.12%.
* Geometry and stop edits add little: Exp 3's 29 certified improvements are
  each at most 0.19%, within model uncertainty. Route recombination is null.
  N4, the best of the 200 promoted and certified greenfield candidates, is
  worse than N3.

Everything below either:

* tests whether that answer survives **real data**;
* reaches parts of the original question that were **never tested**;
* fixes a **known defect** in the instruments.

Compute estimates assume the 2-core container used so far. Stage 1 cells and
initial solves are independent and parallelise per cell (a cluster job array,
`docs/RELEASE_AND_REPORTING_GUIDELINES.md`, "Scaling"); basin closure as
implemented runs one process per (track, network) (`exp7_run.py closure`) and
is not divided by core count.

---

## Tier 1: would most change the answer

### E8. Validation and calibration against COTA data

**Blocked on non-public COTA data** (APC, farebox, fare-card, survey).

* **Question:** does the baseline model reproduce what COTA actually observes?
  And do the findings survive once the uncertain parameters are calibrated?
* **Why first:** every output is currently "uncalibrated", with all four
  validation dimensions `unavailable`. No result can leave the "modeled"
  qualifier until this runs.
* **Design:**
  * Implement `cota-opt validate` with four independent statuses: route
    volume, stop pattern, transfer behaviour and trip length.
  * Thresholds are set in config before any comparison.
  * Then calibrate, in this order:
    * the retention curve (60/210/0.10);
    * the unserved-trip penalty (60 min);
    * the transfer penalty (10 min);
    * walking weights.
  * Data is held out: fit on some periods or routes, validate on others.
* **Data:** APC stop-level boardings and alightings, farebox route totals,
  fare-card transfer chains, and the COTA on-board survey.
* **What would change the answer:**
  * a failed route-volume or trip-length validation;
  * a calibrated unserved-trip penalty w_unserved (or retention curve) such
    that, at the policy-chosen λ, λ · w_unserved falls below the generalized
    cost of a material share of served trips. That would put the real system
    in the regime where the objective sheds riders (report §6.2; errata E7).
* **Effort:** mostly data work. Re-running the Exp 1 headline at calibrated
  values is about 3 seeds × 1 h.

### E9. All-purpose demand

**Needs a new OD source** (MORPC model, LBS or APC; not necessarily COTA's).

* **Question:** does a 6% reduction in unserved trips hold when demand
  includes non-work travel?
* **Why:** commute-only LODES is the largest unquantified error. Midday and
  evening service are judged on demand that is mostly absent. Exp 7 A1 added
  non-commute demand only on commute OD pairs.
* **Design:**
  * Add a new `odmatrix` constructor, one of:
    * MORPC regional travel-model transit trips;
    * location-based-services OD;
    * APC-expanded OD.
  * Keep LODES as a comparison arm.
  * Re-run Exp 1 (3 seeds) and Exp 7 Stage 1 on the new demand.
  * Re-optimize in the closest cell to Exp 1's rules (R1_H60), with basin closure.
* **What would change the answer:** a sign change or a large shrinkage of F1.
  Also a different pattern of where frequency moves, though that remains
  aggregate-only (reporting rule 8).
* **Effort:** about 10–20 h of compute after the data is in hand.

### E10. A well-posed objective (Class C reformulation)

* **Question:** what is the frontier between unserved demand and generalized
  cost when losing a trip is priced at least as high as serving it?
* **Why:** Exp 7 showed the λ-scalarized objective, whose unserved penalty
  (λ · 60) is below the generalized cost of many served trips, collapses
  service at λ = 1. It sheds hard trips under higher transfer
  or walking costs. Today the answer depends on whether a service-preservation
  rule is imposed.
* **Design:** three formulations, each versioned separately from Gen1
  (`METHODOLOGY.md`, Class C):
  1. **ε-constraint:** minimize GC subject to unserved ≤ ε, swept over ε.
  2. **Unserved penalty consistent with the retention curve:** set
     λ · w_unserved at or above the generalized cost at which the retention
     curve treats a trip as lost (for example, its 210-min floor point,
     `cost_retention_zero_min`, where retention reaches its 0.10 floor), and
     report whether shedding persists. An operating-cost term is not a remedy
     for shedding (it rewards removing service); it matters only if the fixed
     envelope is replaced by a priced budget.
  3. **Coverage floor:** add an explicit floor (the R4 or R6 forms) as a
     standing rule.
  * Report where each formulation's optimum switches route-periods off.
* **What would change the answer:** if the well-posed formulations reproduce
  the R1_H60 result, F1 stands without the service-preservation qualifier.
* **Effort:** about 20–40 h.

### E11. Physical fleet for the frequency plan

**Blocked on non-public COTA data** (deadhead matrix, terminal table).

* **Question:** does the Exp 1 plan fit within the 197-vehicle peak requirement
  that COTA's published blocking implies (NTD VOMS 198) when actually blocked?
* **Why:** no modified plan has a vehicle count. The blocking materializer
  misses the certified plans' own vehicle-hours by 17.8–47%. Deadhead times and
  terminal identity are not public.
* **Design:**
  * Repair the materializer so it reproduces each plan's vehicle-hours exactly.
    That is an instrument fix, tested on the baseline first.
  * Load a COTA deadhead matrix and terminal table into `TableDeadheadOracle`.
  * Block the three Exp 1 seed plans plus the Exp 7 R1_H60 BASE plan.
  * Report FEASIBLE, INFEASIBLE or UNDECIDABLE per plan.
* **Data:** COTA deadhead and terminal tables, and runcut and blocking rules.
* **What would change the answer:** an INFEASIBLE verdict for all seed plans.
  Then Exp 1 would need a physical-fleet constraint rather than the proxy.
* **Effort:** small compute (minutes per plan). The work is in the data and the
  instrument.

### E21. Pre-specified confirmation of the post hoc F1 result

Runnable now; needs no external data.

* **Question:** is the post hoc F1 result (N0 under R1_H60 against the current
  plan at the same level) sign-stable across independent closures and across
  the Stage 1 movers that were not re-optimized?
* **Design:** pre-specify that definition; at least 3 independent
  starts/closures per level at the six A5/A6 levels plus A7 (Moderately
  sensitive for F1), A1, A3 and A8; a period-tilt dimension; at least 3
  independent N0 REF closures at BASE to put a distribution on the
  non-identification (−5.4% vs +30.5%).
* **Acceptance:** SIGN_ROBUST across all closures at every λ ≥ 2 level.
* **Existing partial evidence:** two closures of R1_H60 at BASE sharing one
  initial solve (Exp 6, Exp 7) give −6.55% and −6.57%. They are not
  independent.

---

## Tier 2: parts of the original question never tested

### E12. Transfer timing (timed transfers / pulses)

* **Question:** how much does coordinating departures at major transfer points
  save, beyond frequency?
* **Why:** the mission names transfer timing, but every experiment so far is
  frequency-based. Waiting is the expected value under random arrival, and
  schedules have no offsets.
* **Design:**
  * Add schedule offsets as decision variables at the top transfer stops, by
    modeled transfer volume.
  * Evaluate with a timetabled (not frequency-based) assignment. The RAPTOR
    timetable router exists.
  * Hold Exp 1's frequencies fixed. Then do a joint search with matched
    convergence.
* **Note:** pulse value depends on headway regularity; interpret jointly with
  E14.
* **Effort:** a new evaluator path, followed by about 20 h.

### E13. Stop consolidation with measured stop cost

* **Question:** does removing closely spaced stops save enough runtime to fund
  frequency?
* **Why:** blocked so far, because stop cost is unmeasurable from the GTFS
  feed. 11 natural experiments gave an inverted −157 s per stop.
* **Design:**
  * Measure dwell and acceleration loss per stop from AVL or GTFS-Realtime.
    A collector exists in `cota_opt.realtime`.
  * Promote the existing stop-removal edit (`src/cota_opt/stopedits.py`) to an
    Exp 3 edit kind. It is not among Exp 3's eight `EDIT_KINDS`.
  * Run it through Exp 3's mutation harness with the measured runtime saving
    recycled into frequency.
* **Data:** a few months of GTFS-Realtime vehicle positions, or AVL.

### E14. Reliability (Exp 7 A4)

* **Question:** do the findings hold when waiting reflects observed headway
  irregularity?
* **Design:**
  * Implement the schedule-coefficient waiting model with route-period headway
    variance from AVL. This requires a reviewed change to `src/cota_opt`, so it
    is a Class C generation.
  * Pre-specify new A4 levels in the new model's terms (for example, headway
    coefficient of variation by route-period at the observed median and 90th
    percentile). Do not reuse the 0929 schedule-coefficient levels:
    `EXP7_LEVELS.json → declared_not_run[A4_*].why` records that they cannot
    represent headway variance.
* **Data:** AVL or months of GTFS-Realtime, shared with E13.

### E15. Equity and incidence

* **Question:** who gains and who loses under the frequency plan?
* **Design:**
  * Compute the change in GC and served status by origin block group.
  * Cross-tabulate with ACS demographics, and with the Title VI form of R5,
    which needs COTA's minority and low-income route definitions.
  * Report as an incidence table. It is not a compliance determination.

---

## Tier 3: instrument and method

### E16. Optimality gap of the certifier

* **Question:** how far is the (8, 3)-block-local optimum from the global
  optimum on N0?
* **Why:**
  * D39 and Exp 6 show basin effects of 0.13–1.70%, the same order as policy
    prices and as Exp 3's effect.
  * The residual is unmeasured for every certified plan.
* **Design:**
  * Run MILP or CP-SAT on a linearized frequency subproblem, or large-neighbourhood
    search with many starts, as a Class B solver.
  * Bridge-test against Gen1 and the block certifier on N0 and N3.
  * Reopen a result only if the measured gap threatens it (`METHODOLOGY.md`).
* **Effort:** high; research-grade.

### E17. Certified resource frontier (Exp 5 redone with closure)

* **Question:** what does each extra revenue-hour, or each extra unit of peak
  capacity, buy on N0?
* **Why:** Exp 5 failed its monotonicity gate through start-basin dependence.
  Its N0 half suggests the peak proxy, not hours, binds above today's levels.
  A funding scenario (LinkUS and similar) needs a certified version.
* **Design:**
  * Exp 5's 16-cell grid on N0 (and N3), with Exp 6/7 basin closure across
    the nesting.
  * Under R1_H60 rules.
  * With the E11 fleet instrument once it exists, so the peak axis can become
    physical.
* **Effort:** about 15–25 h.

### E18. Cross-route common lines (optimal-strategy assignment)

* **Question:** do the findings change under hyperpath / optimal-strategy
  assignment?
* **Why:** the upper bound on the omitted served-leg wait saving is 0.516% of
  GC on N0, 1.16% on N3 and 12.47% on N4 (retained-rider effects unmeasured).
  It disadvantages networks with parallel routes.
* **Design:** add a Class C evaluator. Re-run F1 and F4 under it. Exp 7's
  `B1_COMMONLINES` level ran Model A (`pattern`), not common lines (errata
  E16), so this item is the first actual test of the as-issued Class B
  common-lines question.

### E19. Elastic demand / mode choice

* **Question:** does replacing the retention curve with a calibrated mode-choice
  model change the frontier?
* **Design:** a logit mode choice against auto travel times; requires E8
  calibration data.

### E20. Exp 7 coverage not run

These extend Experiment 7 itself:

* **Bootstrap re-optimization:** the A2 subset, draws 1, 5, 10, 15 and 20.
* **Class B accessibility:** the jobs-accessibility objective (B2).
* **Retention curve:** A8 with `full_min` varied.
* **Commute pairs:** A1 with new OD pairs, not only commute pairs.
* **Period tilt:** the period-share assumption (LODES has no time dimension;
  NOT INCLUDED in Exp 7).

Each is cheap relative to Tier 1, but only worth running if Tier 1 does not
supersede the demand and calibration it depends on.

---

## Not experiments, but required before any of them is quoted

The release work in `docs/RELEASE_AND_REPORTING_GUIDELINES.md`:

* push to GitHub and merge to `master`;
* the `research-final` tag and a pinned environment;
* license and citation;
* data interfaces and the envelope-units sidecar;
* the calibration register;
* `cota-opt reproduce exp1`;
* register `EXP7_F1_DECISION_SPACE.json` in the next registry version at the
  freeze;
* the three reports with script-generated figures.
