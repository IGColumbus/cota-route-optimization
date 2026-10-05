# Experiment 7: results (two-stage final production contract)

*Written 2026-10-04. The formal closeout is `EXPERIMENT7_CLOSEOUT.md`. The governing contract is `docs/EXPERIMENT7_AMENDMENT.md` §14. The machine-readable results are in `outputs/exp7/EXP7_CLOSEOUT_TABLE.{json,md}`, `outputs/exp7/stage1/EXP7_STAGE1_ANALYSIS.json` and `outputs/exp7/EXP7_ANALYSIS.json`. Authority order for Exp 7: `HANDOFF.md` §1; where the closeout and `docs/EXPERIMENT7_CLOSEOUT_ERRATA.md` conflict, the errata wins.*

## Status

| stage | status | evidence |
|---|---|---|
| Stage 1 | `EXP7_STAGE1_EVALUATION_COMPLETE` | 192/192 cells, 0 errors. Every certified objective that shares the evaluator reproduces bit-exactly at BASE. |
| Stage 2 selection | frozen before Stage 2: **A5, A6** | `outputs/exp7/EXP7_STAGE2_SELECTION.json`. Scores: A5 1.196, A6 0.685, A1 0.415, A7 0.414, A3 0.152, A8 0.124, A2 0.094. |
| Stage 2 | `EXP7_STAGE2_REOPT_COMPLETE` | All five closures at FIXED_POINT; 4/4 sentinels bit-exact; 210 final records pass the record checks; 0 monotonicity violations in 840 pairs; every reported comparison firewall-admitted. |

**Stage 2 closures**

| closure | passes | certified improvements |
|---|---|---|
| F6 N0 | 4 | 92 |
| F6 N3 | 4 | 76 |
| F4 N0 | 2 | 6 |
| F4 N3 | 2 | 5 |
| F4 N4 | 4 | 23 |

The improvements are within-level (W) and cross-level (X, with BASE as the hub). Every one is certified under its destination level's own model.

## The regime boundary

The objective is GC + λ · w_unserved · unserved (w_unserved = 60). It has no operating-cost term, but that is not the cause (errata E7). When λ · 60 is below the generalized cost of a served trip, making that trip unservable lowers the objective.

**At A5_LAM1 (λ = 1), re-optimization collapses service.**

| network | route-periods off | revenue-vehicle hours | served trips | unserved trips |
|---|---|---|---|---|
| N0 | 139 | 557 (BASE 2,516) | 1,583 | 29,366 |
| N4 | 375 | 1,132 | 1,122 | — |

- At A5_LAM1, the re-optimized F1, F4 and AF1 (tie) change sign and R2 prices become positive (Stage 2): that is the collapse. At fixed plans, F4, six F5 arms and a few F6/AF1 cells also change sign (Stage 1), because halving λ re-weights unserved demand; nothing collapses there. Fixed-plan F1 does not change sign.
- That is a property of the objective below its well-posed range, not a solver fault. The components were checked directly.
- Results at A5_LAM1 are reported. They are not evidence that a finding fails within the certified λ ≥ 2 regime.

The same mechanism appears in milder form at A5_TP200, A6_WALKSPD85 and A6_MAXWALK75. Those levels raise the generalized cost of the harder trips, so the optimizer sheds them while revenue-vehicle hours stay unchanged.

## Findings

**F1: re-optimizing reduces unserved demand vs the current plan** (certified −6.65%)

- **Stage 1 (fixed plans):**
  - At BASE, F1 is −6.02%, measured through the Stage 1 evaluator (no crowding).
  - The sign label is SIGN_ROBUST. The Class A range is −7.0% to −1.9%.
  - The worst movement is at A6_MAXWALK75 (68.5%).
- **Stage 2 (adaptive):** the F6 N0 REF plan is compared with the current plan at the same level.

| BASE | LAM1 | LAM4 | TP050 | TP200 | WALKSPD85 | MAXWALK75 |
|---|---|---|---|---|---|---|
| −5.43% | +181.7% | −6.76% | −5.74% | +45.1% | +16.6% | +4.6% |

- **Reading:** the pre-specified F1 adaptive label is SIGN_SENSITIVE. Its values are basin-dependent: a second certified closure of the BASE cell gives +30.5% (errata E3), so the per-level signs are not a finding.
  - F1 is SIGN_ROBUST for the fixed plans Exp 1 produced (magnitude Highly sensitive, A6). It is **not** a property of re-optimization under every objective calibration.
- **Post hoc, not pre-specified (`docs/EXPERIMENT7_F1_ADDENDUM.md`).** REF may switch route-periods OFF; Exp 1's plans could not (span preserved, 60-minute maximum headway).
  - Re-optimized under Exp 1's service rules (the R1_H60 cell: no route-period switched off, 60-minute maximum headway; study safeguards, not COTA policy), F1 is −2.1% to −7.0% at every λ ≥ 2 level re-optimized in Exp 7 (A5 and A6 only), with one closure per cell.
  - At λ = 1 it is +0.12%, a near-tie.
  - Every pre-specified reversal coincides with the optimizer switching 38–139 route-periods off.
  - At λ = 2 in the OFF-permitting decision space, F1 is not identified. Two certified fixed points of the same BASE cell, 0.16% apart in objective, give −5.4% and +30.5% (errata E3).

**F2: the splice null.** It holds at every applicable Stage 1 level. F2 is not re-optimized (§14.2). Its pre-specified sign label is SIGN_SENSITIVE (18 Class A flips, 10 of them bootstrap draws; range −0.226% to +0.166%), as expected for an effect that small (recorded +0.0065% on the incumbent-start plans Exp 7 evaluates; +0.090% under matched starts, errata E17).

**F3: N3 add_stop vs control.**

- Stage 1 label: SIGN_SENSITIVE, because of a sign flip at A7_RM05.
- The A7 rank mismatch between N0 and N3 is flagged at RM04/RM05. Recomputed without those levels, the label is SIGN_ROBUST.
- F3 is not re-optimized.

**F4: the redesigned network N4 is worse than N3** (certified +9.66%)

- **Stage 1:** SIGN_SENSITIVE, with a sign flip only at A5_LAM1 (Class A range −1.31% to +19.35%).
- **Stage 2 (adaptive):** N4 − N3 as a percentage of N3.

| BASE | LAM1 | LAM4 | TP050 | TP200 | WALKSPD85 | MAXWALK75 |
|---|---|---|---|---|---|---|
| +8.55% | −0.98% | +30.8% | +9.88% | +6.77% | +7.72% | +6.77% |

- N4 − N0 is within 0.2 percentage points of N4 − N3 at every level.
- **Reading:** N4 stays worse at every level in the λ ≥ 2 regime. The magnitude scales with λ, because N4's deficit is coverage (illustrative, F4-track basins: N4 12,700, N3 17,389, N0 17,349 served at BASE; basin-dependent, not a finding). The only flip is the degenerate λ = 1 level.

**F5: the J/P resource prices** (fixed Exp 5 plans)

- Several arms flip at A5_LAM1. Magnitudes are highly sensitive to λ.
- F5 is not re-optimized. Exp 5's own monotonicity failure is preserved.

**F6: policy prices and rankings**

- **Stage 1:**
  - Most N0 prices are SIGN_ROBUST.
  - The R4_C05 and R4_C01 prices flip at A5_LAM1. R4_C05 also flips at A7_RM09.
  - On N3, several cells flip at A5_LAM4.
- **Stage 2 (adaptive):** the number of cells whose rank changes against BASE.

| network | TP050 | LAM4 | WALKSPD85 | MAXWALK75 | TP200 | LAM1 |
|---|---|---|---|---|---|---|
| N0 | 0 | 1 | 3 | 3 | 8 | 11 |
| N3 | 0 | 3 | 6 | 5 | 9 | 9 |

- The recurring sign events are R2 OFF-share caps (25% and 10%) moving from a zero price (tie with REF) to a positive price. They bind because the re-optimized N0 REF switches 38–139 route-periods off, against caps of 43 and 17. N0 LAM4 also has one TO_TIE event (R4_C05).
- R2_S25 and R2_S10 have a zero price at every Stage 1 level and at Stage 2 BASE.
- Under re-optimization they become binding (a positive price): R2_S10 at LAM1, TP200 and both walking levels, and R2_S25 at LAM1 and TP200.
- No closed cell is cheaper than REF at any level. A negative price would have blocked certification.

**AF1: N3 − N0 at a matched policy.**

- The REF delta is −0.16% to −0.31% at every λ ≥ 2 level.
- At LAM1 the two networks collapse to the same near-empty service, giving +0.00%. That counts as a TO_TIE event.

## Claim bounds

- **A4 reliability:** UNIMPLEMENTED. Reliability robustness is not tested.
- **A1:** non-commute demand is added only on OD pairs that have observed commuting.
- **A6:** walking friction is bundled; the access and transfer caps move together.
- **A3:** the resource envelope is held fixed as runtimes increase.
- **A8:** cost_retention_full_min is not varied.
- **Stage 2 scope:** only A5 and A6 are re-optimized. A2 was not selected, so no bootstrap re-optimization ran.
- **Untested:** the Class B jobs-accessibility objective.
- **Untested:** cross-route common-lines / optimal-strategy assignment. The level named `B1_COMMONLINES` ran Model A (errata E16).
- **Objective-ordering results** do not transfer to served demand, GC, OFF count or accessibility.
- **Proxy demand:** all results use proxy demand (AGENTS.md rule 7).
