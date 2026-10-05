# Planning brief: frequency, geometry and service safeguards in a model of COTA's weekday network

*Planning brief, 2026-10-05. Ian Gregory. Independent research; **not an
operating plan and not COTA-endorsed**. Every number below is checked against
the study's committed artifacts by `scripts/verify_report_claims.py`. The
technical report (`docs/report/TECHNICAL_REPORT.md`) has the methods,
uncertainty and sources.*

<!-- model-status:begin -->
> **Model status** (generated from `config/model_status.yaml`; do not edit by hand)
>
> * **Calibration:** uncalibrated. The current study is uncalibrated against observed route volumes, stop activity, transfer behavior and trip-length distributions.
> * **Demand:** LODES-based commute OD proxy (LEHD LODES8 Ohio 2022), scaled to an NTD-derived 30,949 weekday linked trips; non-work travel absent.
> * **Service:** scheduled service (GTFS), not observed operations.
> * **Not an operating plan. Not COTA-endorsed; the project is independent of COTA. No route-level headway is a recommendation.**
>
> | validation dimension | status (as of 2026-10-05) |
> |---|---|
> | route volume | `unavailable` |
> | stop pattern | `unavailable` |
> | transfer behavior | `unavailable` |
> | trip length | `unavailable` |
>
> There is no single "validated" flag. Reason for `unavailable`: no observed agency data (APC, farebox, fare-card, survey) has been supplied.
<!-- model-status:end -->

## 1. The question

Holding modeled operating resources approximately constant, how do frequency
allocation and network-design interventions trade off modeled unserved demand
and passenger generalized cost, and how much can the study's λ-weighted
objective improve? "Modeled resources" means the current schedule's weekday
revenue vehicle-hours and a per-period peak-concurrency proxy. The proxy is
not a bus count.

## 2. Headline: frequency reallocation

Within the model, reallocating frequency within existing routes at fixed
modeled resources served ~680 more modeled weekday trips (+3.3% served;
~2.2% of the 30,949 modeled weekday trips) and reduced modeled unserved demand
by −6.65% (solver-seed SD 0.06 percentage points), while total generalized
cost rose +0.88%. Generalized cost per served trip fell −2.34%.

How to read this:

* **The aggregate is identified; the plan is not.** Independent optimizer
  seeds reach the same total but disagree on 19.7% of route-periods in the
  worst pair. No route-level headway is a recommendation.
* **Solver-seed SD is not a confidence interval.** It measures optimizer
  variability with data and assumptions fixed, not real-world uncertainty.
* **The frontier is certified from λ = 2 upward.** At λ = 2 the plan uses
  2,516.65 of the schedule's weekday revenue vehicle-hours.

## 3. Robustness (Experiment 7)

* **Fixed plans, pre-specified:** the certified plan's unserved-demand gain
  kept its sign at every one of the 44 pre-specified fixed-plan perturbations
  (−1.9% to −7.0% unserved). These perturbations cover demand, running times,
  cost weights, walking, route removal and the retention curve. The magnitude
  is highly sensitive to walking friction: with access and transfer walking
  caps cut by a quarter, the gain shrinks to −1.897%.
* **Re-optimized with service kept on (post hoc):** in the closest decision
  space to Experiment 1's rules (no route-period switched off, 60-minute
  maximum headway), the re-optimized gain is −2.14% to −7.00% at every λ ≥ 2
  level tested, and +0.12% at λ = 1. This analysis was added after the
  pre-specified results and remains labelled post hoc.
* **Objective identification:** when the optimizer may switch service off,
  two independently closed plans 0.161% apart in objective give −5.4% and
  +30.5% changes in unserved demand. At λ = 1 the optimizer nearly empties the
  network (557 of 2,516 vehicle-hours). The study therefore quotes results only
  where they are identified.

## 4. Geometry

* **Through-routing (Experiment 2 / 2B):** no supportable gain. The leading
  splice is +0.090% unserved demand under matched starts, worse than no edit
  and inside the noise floor.
* **Route mutation (Experiment 3):** effects are small. The certified leader
  adds a stop and moves the objective by −0.18657%. It is a model result, not a
  recommendation.
* **Greenfield design (Experiment 4):** N4, the best of the 200 promoted and
  certified greenfield candidates, was +8.55% to +9.66% worse than N3 (the
  edited existing network) on the modeled objective across the matched
  comparisons. The best of all 2,000 generated candidates is not identified.
  The path model fits N4 less well, and the cross-route waiting omission is
  12.47% of generalized cost on N4.

## 5. Price of service-standard safeguards (Experiment 6)

On N0 (today's geometry), study-safeguard constraints worsened the modeled
objective by 0 to +0.912% (N3: 0 to +0.634%). The prices are in objective
units, not dollars or vehicle-hours. Examples on N0:

* a 60-minute headway floor: +0.482%;
* a 20-minute floor: +0.912%;
* a 5% cap on switched-off service: +0.212%.

None of these regimes has a documented COTA numeric anchor; they are study
safeguards, not COTA policy or Title VI compliance.

## 6. Major limitations

* **Demand is a commute proxy** (LODES 2022), scaled to an NTD-derived weekday
  total. Non-work travel is absent and period shares are assumed.
* **Uncalibrated and unvalidated.** The current schedule serves 66.8% of the
  modeled weekday total; that is a fit statistic, not validation. All four
  validation dimensions are unavailable (box above).
* **Waiting model.** Same-route common lines only; cross-route waiting is
  omitted.
* **No fleet or deployability claim** for any modified plan.
* **Data vintages differ:** 2020 Census, 2022 LODES, 2024 NTD, 2026 GTFS.
* **Start-basin dependence:** the objective is flat across very different plans.

## 7. What COTA data would improve the analysis

In priority order (`docs/CALIBRATION.md`):

1. **APC stop and route boardings, by time of day.** They validate route
   volumes and stop patterns, and set period shares.
2. **Fare-card trip chains or an on-board survey.** They calibrate retention,
   transfer penalty, walking and access distances, and support all-purpose
   demand.
3. **AVL running times.** They give reliability and observed runtimes.
4. **Blocking, run-cut and deadhead tables.** They allow a physical fleet
   count for modified plans.

## 8. Rerunning it

* **Reproduce the headline:** `README.md` and `docs/REPRODUCE.md`.
  `cota-opt reproduce exp1 --smoke` rebuilds the model and checks it against
  the record.
* **Plug in data:** `docs/DATA_INTERFACES.md`. There is a tested adapter for
  OD demand. `cota-opt validate-model` reports route volume, stop pattern,
  transfer behavior and trip length separately, with no overall pass flag.
