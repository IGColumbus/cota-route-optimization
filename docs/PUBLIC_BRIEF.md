# Could COTA's buses serve more riders with the same resources? A modeling study

*Public brief, 2026-10-05. Ian Gregory. Independent research; not affiliated
with or endorsed by the Central Ohio Transit Authority (COTA). Full report:
`docs/report/TECHNICAL_REPORT.md`.*

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

## What was studied

This project built a computer model of COTA's weekday bus network from public
data: COTA's published schedule, Census commute flows and federal transit
statistics. It then asked a narrow question. Keeping roughly the same amount
of bus service, could the network serve more of the modeled demand, and at
what cost in passengers' travel time?

## What the model found

**Rebalancing how often buses run, on the routes that already exist, helped
the most.** Within the model, moving frequency between existing routes served
~680 more modeled weekday trips (+3.3% served; ~2.2% of the 30,949
modeled weekday trips) and reduced modeled unserved demand by −6.65% (solver-seed
SD 0.06 percentage points), while total passenger travel cost rose +0.88%.
The gain stayed positive in every one of the study's planned stress tests.

**Redrawing routes did not help in the model.**

* Joining routes end to end produced no real gain. The best option was
  slightly worse than doing nothing (+0.090% unserved demand).
* Small edits to existing routes made very small differences.
* The best of the 200 promoted and certified entirely new network designs was
  clearly worse than a lightly edited version of today's network (+9.66% on the
  study's objective).

**Service-standard safeguards cost little in the model.** Rules such as a
maximum wait between buses worsened the study's objective by at most +0.912%
on today's network. These are the study's own safeguards, not COTA policy.

## What the model cannot tell you

* **It is not a plan.** Independent runs of the optimizer disagree on about a
  fifth of route-period frequencies while reaching the same total. So no
  individual route's schedule here is a recommendation.
* **It has not been checked against real ridership.** No stop counts, route
  counts or transfer data were available. The demand is built from commute
  flows only, so trips to shop, study or see a doctor are missing.
* **It counts schedules, not real buses.** Whether the rebalanced service needs
  more vehicles or drivers was not measured.
* **Some settings make the model unreliable.** If the optimizer may switch
  service off entirely, two nearly equal-scoring plans can give very different
  ridership (−5.4% versus +30.5% unserved demand). Results are therefore quoted
  only where service is kept on.

## Where to learn more

* Planning-level summary: `docs/PLANNING_BRIEF.md`.
* Full technical report, limitations and retractions:
  `docs/report/TECHNICAL_REPORT.md`.
* How to rerun it, or plug in better data: `README.md`,
  `docs/DATA_INTERFACES.md`, `docs/CALIBRATION.md`.
