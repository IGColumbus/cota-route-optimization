# Calibration register

> **The current study is uncalibrated against observed route volumes, stop
> activity, transfer behavior and trip-length distributions.**

This is the one authoritative list of the model's behavioural and modelling
parameters: current value, where it is set, its status, the evidence for it,
what Experiment 7 showed about the findings' sensitivity to it, what data
would calibrate it, and how much calibrating it matters.

Status vocabulary:

* **assumed**: a research assumption with no study-specific evidence;
* **calibrated**: fitted to observed data for this network (none yet);
* **externally observed**: taken or derived from a published observed source;
* **policy/value choice**: a weighting the analyst chooses; data cannot settle it.

The release-facing model status, including calibration status, lives in
`config/model_status.yaml`. It is stamped into every artifact that release
tooling writes (`cota-opt reproduce`, `cota-opt validate-model`) and rendered
into the briefs' model-status box. Frozen research artifacts are not
retrofitted with a calibration field; they predate this register and are
preserved byte for byte. Every one of them is uncalibrated.

## Register

Values are configuration constants, quoted from the files named.

| parameter | current value | set in | status | evidence | data that would calibrate it | priority |
|---|---|---|---|---|---|---|
| walking speed | 80 m/min (4.8 km/h) | `config/assumptions.yaml → path_assignment.walk_speed_m_per_min` | assumed | none; a common planning value | on-board survey access legs; fare-card + GPS | medium: speed alone was stable in Exp 7; the walking dimension (A6) as a whole moved F1 most |
| access radius (zone centroid → boarding stop) | 600 m | `path_assignment.access_radius_m` | assumed | none | survey access distances; APC stop boardings vs catchment | **high** (A6); first calibration target in report §10 |
| transfer walking cap (stop → stop) | 400 m | `path_assignment.walk_radius_m` | assumed | none | fare-card transfer pairs | medium (A6, jointly with access radius) |
| walk / wait / transfer-wait weights | 2.0 / 2.0 / 2.0 per minute (in-vehicle 1.0) | `config/cost_weights.yaml → weights` | assumed | TCRP 165 ranges, not COTA-fitted | route-choice survey; stated preference | medium; not varied in Exp 7 |
| waiting model | Model B: combined frequency of same-route patterns; random arrivals below 12 min headway, schedule coefficient 0.25 above | `path_assignment.common_lines`; `waiting.*` | assumed (functional form) | Model A/B correction (report §9 R1); cross-route common lines omitted | APC boardings by pattern at shared stops; AVL headway regularity | medium; cross-route omission bounded in report §8 |
| transfer penalty | 10 min per transfer | `weights.transfer_penalty` | assumed | TCRP ranges | fare-card transfer rates; route-choice data | **high**: A5_TP200 re-optimized changes F1's sign in the OFF-permitting space |
| λ (unserved-demand weight multiplier) | 2 (certified frontier λ ≥ 2) | experiment configuration (`cota-opt reproduce`, Exp 1 contract) | policy/value choice | Exp 1 frontier; λ ≤ 1 uncertified | none; a value judgement | n/a; report every result with its λ |
| unserved-trip penalty | 60 min-equivalent per unserved trip | `weights.unserved` | assumed / value choice | none | mode-choice or survey data on what lost riders do | high: with λ it defines the objective (report §6.2) |
| retention curve (generalized-cost based) | full retention ≤ 60 min, zero at 210 min, floor 0.10 | `path_assignment.cost_retention_full_min / _zero_min / _floor` | assumed | "a crude discouragement proxy, not a mode-choice model" (config comment) | fare-card trip chains; on-board survey; mode-choice model | **high**: largest untested assumption; the 60-min knee was never varied (report §8.1) |
| period demand shares | early 0.05, am 0.22, midday 0.33, pm 0.24, evening 0.12, owl 0.04 | `demand_proxy.period_shares` | assumed | "typical US bus demand profiles; NOT COTA-observed" | APC boardings by time of day | high; LODES has no time dimension |
| transfer behaviour in demand scaling | 0.20 transfers per linked trip | `passenger.transfer_rate` | assumed | "typical mid-size bus value" | fare-card transfers; APC | medium: sets the linked-trip total below |
| paths per OD / transfer rounds | up to 4 paths, 3 boardings (2 transfers) | `path_assignment.max_paths_per_od`, `max_rounds` | modelling choice | Exp 7 X_ROUNDS4 (4 boardings) | n/a (numerical adequacy) | low |
| OD coverage | top 20,000 pairs | `path_assignment.od_top_k` | modelling choice | Exp 7 X_TOPK40K | n/a | low |
| demand scaling (weekday linked trips) | 30,949 | `demand_proxy.assumed_weekday_linked_trips` | externally observed (NTD 2024 weekday boardings and bus share) × assumed transfer rate | derivation in `config/assumptions.yaml` | APC/farebox linked-trip estimates | medium |
| demand geography | LODES 2022 commute OD (work trips only) | registry `lodes_od_oh` | externally observed commute flows used as a proxy for all transit demand | LEHD | APC-derived OD, fare-card chains, MORPC model, survey | **high**: non-work travel absent; largest unquantified error |
| average ride fraction | 0.349 of one-way route runtime | `passenger.avg_ride_fraction` | externally observed (derived from NTD passenger-miles) | NTD 2024; agrees with the original 0.35 to 0.2% | APC load profiles | low |
| layover / recovery | 15% of round-trip running time | `operations.layover_ratio` | assumed | industry-typical 10–20% | COTA run-cut and blocking | medium: sets the peak-concurrency proxy, not passenger cost |
| bus capacity (crowding) | 60 passengers | `crowding.bus_capacity` | assumed | 40-ft planning capacity | APC load counts | low: crowding does not bind at modeled demand |
| reliability weight | 0 (placeholder) | `weights.reliability` | assumed (absent) | no reliability term exists | AVL / GTFS-RT archives | medium; Exp 7 A4 not implemented |
| running times | GTFS scheduled | registry `cota_gtfs_static` | externally observed (schedule) | novel links: MAE 17.2 s, bias +0.41% | AVL | medium (A3) |

## Sensitivity in Experiment 7

Exp 7 perturbed most of the parameters above; its magnitude bands and sign
labels were pre-specified (`b18c2f24`). Re-optimized values in the R1_H60
decision space are post hoc (`experiments/exp7/EXPERIMENT7_F1_ADDENDUM.md`).
Parameters with no row here were not perturbed by Exp 7.

<!-- calibration-sensitivity:begin -->
Generated by `scripts/make_calibration_tables.py` from `outputs/exp7/stage1/EXP7_STAGE1_ANALYSIS.json`, `outputs/exp7/EXP7_LEVELS.json` and `outputs/exp7/EXP7_F1_DECISION_SPACE.json`. F1 = change in modeled unserved demand (certified Exp 1 plan vs current plan, λ = 2 unless the level changes λ); negative is favourable.

| parameter | Exp 7 level | perturbation | F1 fixed plan, pre-specified (band) | F1 re-optimized, R1_H60, post hoc |
|---|---|---|---|---|
| (reference) | BASE | none | -6.02% | -6.57% |
| walking speed | A6_WALKSPD85 | `path_assignment.walk_speed_m_per_min` = 68.0 | -5.73% (Highly stable magnitude) | -6.06% |
| access radius and transfer walking cap | A6_MAXWALK75 | `path_assignment.access_radius_m` = 450.0; `path_assignment.walk_radius_m` = 300.0 | -1.90% (Highly sensitive magnitude) | -2.14% |
| transfer penalty | A5_TP050 | transfer penalty x0.5 (10 -> 5 min) | -6.40% (Highly stable magnitude) | -7.00% |
| transfer penalty | A5_TP200 | transfer penalty x2 (10 -> 20 min) | -5.21% (Stable magnitude) | -5.53% |
| λ (unserved weight multiplier) | A5_LAM1 | lambda = 1 (below the certified lambda>=2 frontier; labelled as such) | -6.02% (Highly stable magnitude) | +0.12% |
| λ (unserved weight multiplier) | A5_LAM4 | lambda = 4 | -6.02% (Highly stable magnitude) | -6.83% |
| retention curve | A8_ZERO150 | `path_assignment.cost_retention_zero_min` = 150 | -5.27% (Stable magnitude) | not re-optimized |
| retention curve | A8_FLOOR0 | `path_assignment.cost_retention_floor` = 0.0 | -6.17% (Highly stable magnitude) | not re-optimized |
| demand: non-commute travel | A1_NC025 | non-commute trips added at 25% of commute volume | -6.12% (Highly stable magnitude) | not re-optimized |
| demand: non-commute travel | A1_NC050 | non-commute trips added at 50% of commute volume | -6.21% (Highly stable magnitude) | not re-optimized |
| demand: non-commute travel | A1_NC100 | non-commute trips added at 100% of commute volume | -6.33% (Highly stable magnitude) | not re-optimized |
| demand: LODES sampling (bootstrap, 20 draws) | A2_BOOT01–20 | bootstrap resample of LODES OD | -5.91% to -5.46% (Highly stable magnitude) | not selected |
| running times | A3_RT110 | +10% uniform runtime (passenger time and vehicle-hours; envelope unchanged) | -5.72% (Highly stable magnitude) | not re-optimized |
| running times | A3_RT120 | +20% uniform runtime | -5.40% (Stable magnitude) | not re-optimized |
| running times | A3_RTNOISE | per-link lognormal noise, median \|error\| 20.5% (outputs/runtime_validation.json median_ape_pct 20.5035), one seeded draw, same multiplier for a link on every pattern | -5.76% (Highly stable magnitude) | not re-optimized |
| waiting model (Class B: Model A) | B1_COMMONLINES | Model A waiting (`common_lines = pattern`); the as-issued cross-route common-lines item was not implemented (Exp 7 errata E16; report §9 R13) | -5.99% (Highly stable magnitude) | not re-optimized |
<!-- calibration-sensitivity:end -->

## Using this register

* Any output produced under these parameters is **uncalibrated**. Saying so is
  correct, and every release-generated artifact records it.
* To calibrate, supply observed data through the interfaces in
  `docs/DATA_INTERFACES.md`, set pass thresholds in `config/validation.yaml`
  before running `cota-opt validate-model`, and record the result in
  `config/model_status.yaml`. A changed parameter value makes results
  incomparable with the frozen research record (`research-final`).
