# Experiment 7: launch readiness

*2026-09-29. Governing documents:*

* *`docs/EXPERIMENT7_AMENDMENT.md` (not in force);*
* *`docs/EXPERIMENT7_PROTOCOL_AS_ISSUED.md` (**missing**).*

*Experiment 6 is untouched: `EXP6_POLICY_FRONTIER_CERTIFIED`, and
`outputs/exp6/` is unmodified.*

## Decision: NOT READY

The implementation and the executed evidence agree with each other. The
governing text is incomplete.

* The as-issued Exp 7 section is not in the repository, so the sensitivity
  matrix cannot be declared.
* The freeze script refuses, as designed:
  `outputs/exp7/preflight/freeze_check/FREEZE_ATTEMPT.txt`.

No production cell has been run.

## Gates passed (executed, evidence committed)

| gate | evidence | result |
|---|---|---|
| G3 BASE reproduction | `preflight/base_repro/BASE_REPRO_VERDICT.json` | 3/3 cells bit-exact vs Exp 6 initial records: N3 REF 2,939,912.5807124916, N0 R2_S10 2,949,292.57104456, N0 REF 2,945,632.2349138106. Objective, plan, rounds, fitness, config digest and path-set digest all match. The last canary was run with the final code. |
| G5 unit tests | `tests/test_exp7_closure.py`, `tests/test_exp7_levels.py` | 16 pass: cross-level propagation without winner-chaining, combined W+X closure, target-feasibility refusal (certifier never called), certifier refusal, ceiling failure, memo, deterministic resume, empty cells / `EMPTINESS_CONTRADICTED`, monotonicity, zero/near-zero/unsupported-zero classes, anchored ties, sign flips, basin-vs-sensitivity decomposition, level validation |
| G6 source | `src/cota_opt` | digest `b63ae2dba134245e`, unchanged from Exp 6 |
| G7 transfer / refusal / emptiness | `preflight/transfer/TRANSFER_PREFLIGHT_VERDICT.json` | 7/7, detailed below |
| G7 firewall | `preflight/FIREWALL_PREFLIGHT.json` | 8/8 after a fix, detailed below |
| Knob reach | `preflight/reach_N0.json`, `reach_N3.json` | BASE reproduces the Exp 6 closed REF bit-exactly on both networks, detailed below |
| Driver smoke run | `outputs/exp7/smoke/` | end-to-end on F4 / N0 / {BASE, R_LAM1}, detailed below |

**G7 transfer, refusal and emptiness (7/7):**

* A real cross-level transfer: the Exp 6 closed N0 REF plan sent to λ = 1.
  * It was admitted and re-evaluated under the target: 2,353,574.20, equal to
    the reach test's fixed-plan value.
  * It certified to 2,336,835.61, no worse than the anchor.
* The certifier refused the same plan under N0 R1_H20: policy.
* The certifier refused the N4 plan offered to N0: representation, 390 vs 173
  route-periods.
* N3 R1_H20 was re-proved `INFEASIBLE_UNDER_ENVELOPE` at λ = 1: early peak
  85.2987 > 85.2821.

**G7 firewall (8/8 after a fix):**

* The preflight found that EXP7_POLICY admitted a pair certified at different
  levels. The level hides inside the whitelisted `config_digest`.
* Fixed by level binding: the receipt builder refuses a record whose level is
  not the contract's, and the level digest is folded into the
  non-whitelisted `data_digest`.
* Both the builder refusal and the firewall refusal are tested.

**Knob reach:**

* These reach the evaluator on both networks: λ, waiting model,
  waiting coefficient, the two retention knobs, OD scale, period tilt, wider
  OD (top-k 40k) and RAPTOR rounds.
* **INERT: `max_paths_per_od` (2 and 8) and `n_random_scenarios`.**
  * `pathset.py` limits enumeration to one path per scenario per OD, and
    raises the cap to the scenario count.
  * `exp3_score` passes `n_random_scenarios=0`.
* Walk and access radius are consumed when the harness is built, so they are
  refused as level knobs.

**Driver smoke run:**

* The Exp 6 import was recorded with its sha256.
* The new initial cell at R_LAM1 reproduced the separate preflight greedy
  bit-exactly.
* The X stage ran 2/2 transfers and reached a fixed point in 1 pass.
* The sentinel was bit-exact.
* The analysis produced `NOT_CERTIFIABLE_UNFROZEN_CONTRACT(...)`, which is
  correct.

## Blockers (unresolved)

1. **G1: the as-issued Exp 7 text is missing.** It was requested from Ian and
   has not been received. It is not reconstructed.
2. **G2 / G4: the matrix.** The dimensions, levels, A8 retention settings and
   bands come from item 1.
   * Once they are entered in `outputs/exp7/EXP7_LEVELS.json`, each level
     needs a reach run on N0 and N3. That is about 5 min per level per
     network.
   * Any level that is a path-set-width or scenario-count variation will be
     **INERT** and must be re-specified or dropped, with a claim bound.
3. **Decision needed: the scope of the X stage.** All-pairs across all levels
   costs L(L−1) (see the compute table). The alternative is all-pairs within
   each dimension, with BASE joining all dimensions. This is a scientific
   choice, and it is Ian's.

## Compute (from measured throughput; `exp7_freeze.estimate`)

| L levels incl. BASE | certifications, expected | wall h, expected | wall h, upper |
|---|---|---|---|
| 3 | 388 | 34 | 54 |
| 5 | 1,080 | 94 | 150 |
| 6 | 1,542 | 135 | 215 |
| 11 | 5,018 | 438 | 700 |

These figures include:

* F6 initial cells;
* the W stage;
* the all-pairs X stage;
* the F4 track with N4, priced at 1,150 s per certification (the measured N4 greedy BASE
  preflight took 1,024 s, 21 rounds);
* 4 sentinels.

Preflight overhead already spent is about 4 h wall. After G1 and G2, the
remaining preflight is a matrix reach run: about 10 min per level on two
lanes.

## Observations from the preflight (not claims)

* **At λ = 1, the λ = 2 plans are poor starts.**
  * Greedy at λ = 1 reached 1,831,271.79.
  * Anchoring the Exp 6 closed REF plan reached only 2,336,835.61.
  * Anchoring the Exp 6 greedy REF plan reached 2,079,618.15.

  Cross-level basins differ strongly, so the independent initial solve at
  every level is essential. It also means the X stage will often run without
  improving.
* **At BASE, F4 greedy-only N3 − N0 = −5,719.65 (−0.194%)**, admitted under
  EXP7_F4. This is the greedy-only counterpart of AF1. It is not a result
  until the contract is frozen.
* **N4 BASE greedy (F4 track, `preflight/n4/`): 3,223,885.95**, 21 rounds,
  converged. That is 16,319.53 (0.51%) above the D39 anchored J100 value of
  3,207,566.42.
  * This is the basin dependence D39 described. It is why F4 uses a matched
    procedure and keeps D39 as secondary evidence only.
  * Against N0's greedy REF (2,945,632.23), the greedy-only gap is +9.45%.
    This is not an admitted F4 result.
