# Experiment 6 — D39 preflight and default-path equivalence

*Run 2026-09-28, before any Experiment 6 production cell. Artifacts are in
`outputs/exp6/preflight/`. This is an additive calibration of the successor
search procedure. It does not reopen Experiment 5, and every Exp 5 record is
untouched.*

## A. Default invocation is unchanged (bit-exact)

The certifier was extended with an explicit-anchor option
(`exp4_certify.certify(anchor=...)`) and with policy constraints on the
feasibility path (`policy.py`, `exp2.build_setup`, `frequency._feasible`).
With neither in use, the unchanged EXP4N runner
(`scripts/exp45_certify_cell.py`) was re-run on the final source,
`src_cota_opt_content_digest` `b63ae2dba134245e` (code_version `src-17659e64846b`):

| network | reference result | reproduced |
|---|---|---|
| N4 J100 (EXP4N `production_mr120/cc40b4f4aea3aa05.json`) | 3223885.947526011, plan `898b95fd93c33414`, 21 rounds, converged | **bit-exact**: objective, plan, 21 rounds, all 21 trajectory objectives, 1,029 block enumerations |
| N3 (Exp 4A `outputs/exp4_addendum/N3.json`) | 2939912.5807124916, plan `28135d0fa655e6e1`, 1 round | **bit-exact**: objective, plan, rounds, fitness, trajectory |
| N0 J100 (Exp 5 `outputs/exp5/cells/N0_J100.json`) | 2945632.2349138106, plan `c4591ff0f6e2d8ad`, 1 round | **bit-exact**: objective, plan, rounds, fitness, trajectory |

The anchor extension was also checked on its own, before the policy code
landed (`outputs/exp6/preflight/equivalence/`). N4 was bit-exact, including all
21 trajectory objectives and 1,029 block enumerations, and N3 was bit-exact.

**Verdict:** PASS. `EXP6_PIPELINE_EQUIVALENCE_FAILURE` does not apply.

## B. Anchor semantics

`certify(anchor=...)` behaves as follows:

* **It still runs the Gen1 greedy start.** That start builds the setup and the
  full ladders, and its objective is recorded as `greedy_objective`.
* **It refuses an anchor** (`AnchorRefused`) that is not a real plan for this
  network. That means an anchor that:
  * does not cover exactly this network's route-periods; or
  * is inadmissible under the target cell's complete constraints. This is
    tested by the target's own exact solver on a one-rung ladder, i.e. the same
    `frequency._feasible` that decides every plan; or
  * uses values that are not exact rungs of the full ladder.

  A refused anchor is never repaired.
* **It records the anchor's provenance:** its digest, its objective under the
  target, and the source record.
* **It starts the block search from the anchor.** The existing guard now reads
  "result not worse than the **anchor**", and a violation raises.

## C. The known D39 failure is recovered

The anchor is the committed Exp 5 **N4 H090** plan (`outputs/exp5/cells/N4_H090.json`):

* objective 3,219,614.742641489;
* plan `841d596570f1217f`.

The target runs:

| target | anchor objective under target | result | rounds | vs the failing Exp 5 value |
|---|---|---|---|---|
| **N4 J100** (EXP4N envelope) | 3,219,614.742641489 (admitted) | **3,207,566.4176655654**, plan `d319bb5f4d7a6c2b`, converged | 6 | EXP4N/J100: 3,223,885.95; **0.506% better**, and below the anchor |
| **N4 H110** (hours 110%) | 3,219,614.742641489 (admitted) | **3,207,230.8312193276**, plan `a29f7016d837d1f7`, converged | 5 | Exp 5 H110: 3,274,458.25; **2.053% better** |

The requirement was a result at or below the H090 objective, without falling
back to the worse J100 basin. **Both runs meet it.** The two results are also
mutually monotone: H110 is looser than J100, and 3,207,230.83 ≤ 3,207,566.42.
For comparison, the independent greedy start inside the same calls scored
3,600,775.44.

**Status: PASS.** `EXP6_D39_PREFLIGHT_FAILURE` does not apply.

What this adds to D39, stated as calibration and not as a revision of Exp 5:
under its own envelope, the best known feasible N4 plan is now
3,207,566.42. That is 0.506% better than EXP4N's certified 3,223,885.95 and
0.374% better than the H090 plan. Δ43 computed against this plan would be
+267,654 (+9.10% of N3). The sign and order of magnitude are unchanged. The
official Δ43 remains the admitted +283,973 in the Exp 4A addendum.

## D. Consequence for the closure ceiling

Anchored certifications converged in 5–6 rounds. The longest chain in the Exp 6
nesting graph is R1_H20 → R1_H30 → R1_H60 → R2_S05 → R2_S10 → R2_S25 → REF:
7 cells, 6 edges. Each pass walks every edge in both directions, so an
improvement can travel the whole chain within one pass. The contract freezes a ceiling of **8 passes**, and a
pass that improves nothing ends closure.

## E. A preflight incident, recorded

The first N4 J100 anchor run finished its certification. The runner then
crashed in post-processing: a key-format bug in `scripts/exp6_cell.py`, where
certify's plan keys are `"route|period"` strings. The result had not been
checkpointed, so it was lost. The artifact is kept as
`d39/ERROR.N4_J100_anchor_H090.first_attempt_serializer_bug.json`.

Two fixes followed:

* the runner now writes the raw `certify()` result (`RAW.<out>.json`) before
  any post-processing (OPERATIONS rule 31);
* the key bug is fixed.

The run was then repeated. Those are the numbers above.
