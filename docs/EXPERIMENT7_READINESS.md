# Experiment 7: readiness (two-stage final production contract)

*Updated 2026-09-29 for Ian's final production contract (amendment §14).*

*The machine-readable state is in:*

* *`outputs/exp7/preflight/freeze_check/FREEZE_ATTEMPT.txt`;*
* *`outputs/exp7/EXP7_CONTRACT.json` (once frozen);*
* *`outputs/exp7/stage1/EXP7_STAGE1_ANALYSIS.json` (status field).*

## Design

| stage | scope | status field |
|---|---|---|
| Stage 1 | Fixed-plan evaluation of 59 frozen plans (60 registry entries; N3 R1_H20 is infeasible) on 4 network variants (N0, N3, N4, N0S) at BASE + 47 levels = **192 evaluation cells**, plus **13** N3 R1_H20 emptiness proofs at A3/A7 levels | `EXP7_STAGE1_EVALUATION_COMPLETE` |
| Stage 2 | D39-safe re-optimization in the 2 Class A dimensions selected by the preregistered metric; A2 limited to draws 1, 5, 10, 15, 20 | `EXP7_STAGE2_REOPT_COMPLETE` |

## Pre-launch evidence

**BASE reproduction through the Stage 1 evaluator.** Every certified
objective that shares the evaluator is **bit-exact**:

* all F3 anchors (N0 controls, N3 add_stop);
* F4 (N0 J100, N3 Exp 4A, N4 EXP4N);
* all F5 cells;
* all 27 feasible F6 plans.

F2's unserved demand also matches its Exp 2B values exactly, on both the
control and the splice network.

**F1 differs, as expected.** Exp 1 was certified with crowding on and a
widened 243k-path set. The Stage 1 evaluator gives:

* N0 current-plan unserved demand 10,423.68, versus 10,261.92 in Exp 1;
* the seed plans −5.94% / −6.16% / −5.98%, versus the certified −6.60% /
  −6.72% / −6.63%.

Same sign. The certified value and the Stage 1 BASE value are both reported
(amendment §14.1).

**Other checks:**

* Smoke of every new level kind: `preflight/stage1/SMOKE_VERDICT.json`.
* Full test suite: passes (`pytest tests/`).
* src unchanged: `b63ae2dba134245e`.

## Not covered (claim bounds)

* A4 reliability: UNIMPLEMENTED.
* A1: non-commute demand only on commute OD pairs.
* The jobs-accessibility objective: untested.
* Path-set width and scenario count: inert, dropped.
* Period tilt: not included.
* A8: full_min is not varied.
* Stage 2 bootstrap: only 5 draws are re-optimized.
