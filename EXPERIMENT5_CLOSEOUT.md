# Experiment 5 — modeled operating-resource frontier: CLOSEOUT

**Status: `EXP5_MONOTONICITY_FAILURE`, so the frontier is NOT certified.**

Every other acceptance gate passed, and the failure is confined to N4:

* 12 of the 99 nested cell pairs on N4 regress;
* all 99 nested pairs on N0 are monotone.

The frozen rule makes this a failure of the experiment. It is not waived or
re-labelled here. What the failure shows about the certifier is in §4, and it is
the most important result of this run.

Completed 2026-09-28. The run was:

* 32 production cells, 4 order sentinels and 1 preflight;
* about 6.5 h wall on 2 cores;
* one container reclaim at ~17:14 UTC, during which two in-flight cells died
  without writing. They were re-run from scratch in fresh processes. One of them
  is also a sentinel, N4 J150, and it matched bit-exactly.

**Artifacts:**

* `outputs/exp5/EXP5_CONTRACT.json` — frozen before the first production cell;
  EXP5_FRONTIER `395ee3c960f51935`, file sha256 `f88f04d0…`;
* `outputs/exp5/cells/` (32 records), `sentinels/` (4), `preflight/` (1), `blocking/` (32);
* `outputs/exp5/EXP5_ANALYSIS.json`.

The runner is `scripts/exp5_run.py` over `scripts/exp45_certify_cell.py`. The
analysis is `scripts/exp5_analyze.py`, and the blocking diagnostic is
`scripts/exp5_blocking.py`. The retired design is recorded in
`EXPERIMENT5_PREMISE_RETIREMENT.md`.

## 1. What was run

Two resource axes, both treated as continuous:

* **revenue vehicle-hours**;
* **the six-period solver peak-concurrency proxy**. This is not fleet, buses or
  vehicles, and no per-bus figure exists anywhere in this experiment.

Both are scaled exactly from the EXP4N common envelope (`0b46d1abc9a80c80`)
at 75/90/100/110/125/150%:

* Arm A, joint: J cells;
* Arm B, hours only: H cells;
* Arm C, peak only: P cells.

That gives 16 cells for each of two fixed networks:

* **N4** — the EXP4N normalized leader;
* **N0** — COTA's existing local geometry, with peak express locked.

Only frequency and ON/OFF vary. Every cell is one unmodified EXP4N
certification:

* `exp4_certify.certify`, (8, 3), max 120 rounds, λ 2;
* a Gen1 greedy start under the cell's own caps;
* no warm start and no path-set sharing across cells.

## 2. Acceptance checklist

| Gate | Result |
|---|---|
| Contract frozen and committed before the first production cell | PASS |
| Contract digest, code version (`src-51dd455d9e1a` / `add5d0002d29aa49`), runner hashes = frozen | 32/32 PASS |
| Enforced budget bit-equal to the cell's caps, one budget per cell | 32/32 PASS |
| D35 reach test: hours cap and the most-utilized peak cap each flip admissibility at usage × (1 ± 10⁻⁶) | 32/32 PASS |
| Converged, rounds < 120 (max 27) | 32/32 PASS |
| Certified plan feasible under enforced caps | 32/32 PASS |
| Treatment-independent start (greedy only, no fallback, no rejection) | 32/32 PASS |
| **Reproduction gate**: N4 J100 = EXP4N bit-exactly (objective, plan, 21 rounds, trajectory) | PASS |
| N0 J100 reference cell | 2,945,632.2349138106, identical to the preflight and to the reversed-order sentinel |
| Firewall: every cell vs J100 under EXP5_FRONTIER (only `envelope_digest`, `envelope_used_vh` differ) | 30/30 admitted |
| Firewall: N4 vs N0 at identical cells under EXP5_STRUCTURE (only network fields differ) | 16/16 admitted |
| Order-invariance sentinels (N0 J100, N4 J150, N4 J100, N4 J075; reversed order) | 4/4 bit-exact |
| **Monotonicity** over realized-plan nesting, band 0.0018970% (D33-B) | **N0 99/99 monotone. N4 87/99 monotone, 0 within band, 12 above band → `EXP5_MONOTONICITY_FAILURE`** |
| Blocking (diagnostic only) | 32/32 UNDECIDABLE — see §6 |

## 3. The frontier

Objective (λ = 2, lower is better) and served demand, out of 30,949 modeled
trips:

| cell | N0 objective | N0 served | N4 objective | N4 served | N4 − N0 |
|---|---|---|---|---|---|
| J075 | 3,034,452.2 | 14,609 | 3,351,486.9 | 8,289 | +10.45% |
| J090 | 2,979,723.4 | 15,669 | 3,276,306.9 | 10,306 | +9.95% |
| **J100** | **2,945,632.2** | **16,527** | **3,223,885.9** | **11,249** | **+9.45%** |
| J110 | 2,912,840.7 | 17,073 | 3,193,423.0 | 12,232 | +9.63% |
| J125 | 2,871,618.9 | 17,775 | 3,147,255.5 | 13,066 | +9.60% |
| J150 | 2,803,555.0 | 19,056 | 3,093,943.0 | 13,819 | +10.36% |
| H075 | 3,005,869.2 | 14,974 | 3,248,347.7 | 9,958 | +8.07% |
| H090 | 2,962,269.4 | 16,186 | 3,219,614.7 | 10,856 | +8.69% |
| H110 / H125 / H150 | 2,945,632.2 (= J100) | 16,527 | 3,274,458.2 | 10,710 | +11.16% |
| P075 | 3,034,452.2 (= J075) | 14,609 | 3,386,276.8 | 7,585 | +11.59% |
| P090 | 2,979,723.4 (= J090) | 15,669 | 3,319,339.2 | 9,494 | +11.40% |
| P110 | 2,923,702.6 | 17,147 | 3,194,871.8 | 11,668 | +9.28% |
| P125 | 2,918,019.2 | 16,995 | 3,159,628.2 | 11,975 | +8.28% |
| P150 | 2,901,858.2 | 17,686 | 3,156,282.9 | 11,865 | +8.77% |

**N0 (all gates pass on this network):**

* **Both axes bind at the reference point.** J100 uses 99.987% of hours and
  99.86–100.00% of the peak proxy in every period.
* **Above 100%, the peak proxy is the binding axis and hours are not.**
  H110/H125/H150 return J100's plan exactly. Hours utilization falls to
  90.9/80.0/66.7% and the objective does not move.
* **Below 100%, cutting hours costs** +2.05% (H075) and +0.57% (H090).
* **Cutting the peak proxy costs the same as the joint cut.** P075 and P090
  return exactly the J075 and J090 plans. Once the peak is cut, hours go slack
  (74.7% and 89.9% used).
* **Adding peak proxy with hours fixed helps, with diminishing returns:**
  P110 −0.74%, P125 −0.94%, P150 −1.48% vs J100. Hours stay at 100%, so in
  those cells hours become the binding axis again.

**N0 marginals (adjacent levels only; three separate units; no per-bus figure;
no knee claimed):**

| Arm | Objective change per unit | Unit |
|---|---|---|
| A joint | −3,649, −3,409, −3,279, −2,748, −2,723 (75→150) | per +1 point of joint scale |
| B hours | −115.5 (75→90), −66.1 (90→100), then exactly 0 above 100 | per +1 revenue vehicle-hour |
| C peak | −2,067, −1,932, −1,243, −215, −366 (75→150) | per +1 unit of the pm_peak proxy cap (all periods scale together) |

**N4 vs N0 at identical cells:** N4 is worse at all 16 cells, by +8.07% to
+11.59%, and all 16 comparisons are firewall-admitted. This independently
corroborates the Experiment 4 addendum: N4 does not beat the existing geometry
at any modeled resource level tested.

## 4. The monotonicity failure, and what it says about the certifier

On N4 the certified objective **worsens when resources are loosened** in 12
nested pairs:

| looser | tighter | regression |
|---|---|---|
| H110, H125, H150 | H090 | +1.7034% |
| H110, H125, H150 | J100 | +1.5687% |
| P090 | J090 | +1.3134% |
| P075 | J075 | +1.0380% |
| H110, H125, H150 | H075 | +0.8038% |
| J100 | H090 | +0.1327% |

"Realized-plan nesting" was verified for every pair: the tighter cell's
certified plan fits inside the looser cell's caps. The looser search could have
returned that plan and returned a worse one instead.

The mechanism is the start, not the budget or order:

* the enforced budgets are exact;
* the D35 reach tests pass;
* the sentinels reproduce in reversed order;
* a converged run is deterministic.

The Gen1 greedy start is built under each cell's own caps, so different caps
give different starts. The (8, 3)-block-local search then converges into
**different local optima**. N0 almost always certifies in one round (greedy is
already block-locally optimal) and is monotone throughout. N4 takes 10–27 rounds
across 390 route-periods, about 57% of them OFF, and is not.

**Consequences, stated as evidence and not as a reopening of anything:**

1. **The EXP4N N4 result is not the best known N4 plan under the EXP4N
   envelope.** The H090 plan fits the J100 (= EXP4N) caps and scores
   **3,219,614.74**, 0.133% better than EXP4N's certified 3,223,885.95.
2. **The block certifier's start-basin residual on N4 is at least 1.70% of the
   objective.** That is a lower bound, exhibited by feasible plans. It is about
   **900× the D33-B band** (0.0018970%), which confirms in the strongest terms
   that D33-B is a local lower bound and not a residual estimate. It is also
   **about 4.4× EXP4N's first-to-second margin** (0.387%). The EXP4N ordering
   among closely spaced candidates therefore cannot be read as robust to start
   basin. It remains exactly reproducible under its contract.
3. **Δ43 survives it.** Substituting the best known feasible N4 plan (H090's)
   gives Δ43 = +279,702 (+9.51% of N3), about 5.6× the largest basin gap
   observed.

## 5. What this does NOT establish

* No per-bus, per-vehicle or fleet figure. The peak axis is a concurrency proxy.
* No knee, and no optimal resource level.
* No certified frontier. The experiment status is a failure. The N0 half passed
  every gate on its own, but the experiment was preregistered as one unit.
* No global optimality for any cell, on either network. On N4 the certified
  values are demonstrably not global.
* Everything is conditional on the modeled demand (a LODES commute proxy of the
  top 20,000 OD pairs), the path model and the same-route waiting model. The
  Experiment 4 addendum shows the path model fits N4 worse than N3 or N0.

## 6. Blocking — diagnostic only

EXP4N's blocking instrument was run on all 32 plans against COTA's
block-derived physical fleet (unscaled). **All 32 are UNDECIDABLE**:

* The instrument's materialized timetable does not reproduce the certified
  plans' own vehicle-hours. It is 18–23% off on N0 and 46–47% off on N4.
* A verdict computed on a different amount of service is about a different plan.
  The instrument's raw verdicts (INFEASIBLE for all N0 cells and for N4 J110–J150,
  H110+ and P110+; UNDECIDABLE otherwise) are recorded, not adopted.
* The FEASIBLE route stays closed regardless, because deadhead provenance is
  OPEN.

Reconciling the materializer with the solver's trip accounting is an open
instrument defect. It is not an Experiment 5 result.

## 7. Required language

Experiment 5 measures how a **modeled** objective responds to a **modeled**
revenue-vehicle-hour cap and a **solver peak-concurrency proxy**, on two fixed
geometries, under proxy demand. It does not measure buses, fleet, cost in
dollars or deployability. It does not say what COTA should run. Its preregistered
acceptance rule failed, on N4 only, and the failure is itself the finding: the
EXP4N block certifier is start-basin dependent at the 1–2% scale on a
greenfield network.
