# Reviewer 1: Experiment 7 closeout documentation, proposed improvements

Reviewed 2026-10-04 against HEAD `5dc3f408`. This was a read-only review: no repository file was edited. `python scripts/verify_report_claims.py` returns 30/30.

The closeout's sha256 still matches the registry entry (`27bfc739…` = `CANONICAL_RESULTS_v5.json → experiments.exp7.closeout_sha256`). Every proposed correction to `EXPERIMENT7_CLOSEOUT.md` is therefore written as a new errata row (E7–E13), or as a fix to an existing errata row.

The proposals are ordered by priority, then by how widely each issue spreads. "Reviewer analysis" marks any reasoning that goes beyond what the artifacts state directly.

---

## HIGH

### P1. The "no operating-cost term" explanation is misleading, and E10's design (2) points the wrong way

**Files and locations:**

* `EXPERIMENT7_CLOSEOUT.md`, the one-paragraph answer ("With no operating-cost term…") and §5.2 bullet 1. These go through errata.
* `docs/EXPERIMENT7_RESULTS.md`, "The regime boundary".
* Technical report §3 "Objective", bullet 2, and §6.2 "Two readings", item 2.
* `README.md` Exp 7, the λ = 1 bullet ("because the objective has no operating-cost term").
* `docs/FUTURE_EXPERIMENTS.md` E10, design (2).
* `HANDOFF.md` §6, item 4.

**Problem.** The documents attribute the shedding and collapse to the *absence of an operating-cost term*. Adding such a term would not stop the shedding.

* **TP200 and A6 levels.** Hours are fully used by both the shedding plan and the no-OFF plan (`EXP7_F1_DECISION_SPACE.json → rows[]`):

  | level | REF hours | R1_H60 hours |
  |---|---|---|
  | A5_TP200 | 2,517.14 | 2,515.00 |
  | A6_WALKSPD85 | 2,515.13 | 2,516.07 |
  | A6_MAXWALK75 | 2,515.49 | 2,515.11 |

  An hours-priced term is essentially constant across these plans, so it cannot change which one the optimizer prefers.
* **λ = 1.** The collapsed plan runs 556.6 h. A positive operating-cost term would lower its objective further and make collapse *more* attractive.
* **The actual mechanism**, which the same documents also state: the unserved penalty λ·60 is below the GC of the marginal served trip. At BASE, the mean GC per served trip on the F6-track REF is 1,757,243 / 21,091 = 83.3.
* **Reviewer analysis.** The objective also contradicts the model's own retention curve. Retention runs from 60 to 210 minutes with a floor of 0.10, so at GC = 120 min (the λ = 2 penalty) the curve still retains 64% of riders. Yet at that GC the objective is indifferent between serving and dropping them.

**Proposed change.**

* Add errata row **E7**:

  > §0 and §5.2, "With no operating-cost term, the λ-weighted objective prefers dropping a rider". The cause is that the unserved penalty (λ × 60 min) is below the generalized cost of many served trips (mean 83–86 min). An operating-cost term would not prevent shedding: at A5_TP200 and both A6 levels the shedding and no-OFF plans use the same 2,515–2,517 revenue vehicle-hours, and at λ = 1 a cost on hours would favour the 557-hour plan.

* Replace "has no operating-cost term" in RESULTS, the report and the README with:

  > the unserved-trip penalty (λ × 60 min) is smaller than the generalized cost of many served trips, so dropping them lowers the objective.

* Report §6.2 item 2: replace "an operating-cost term" with "an unserved penalty at least as large as the served-trip GC it replaces (for example, tied to the retention curve's 210-min zero point), an ε-constraint on unserved demand".
* FUTURE E10: replace design (2) with "unserved penalty consistent with the retention curve". Add a note that an operating-cost term must enter together with a hours-floor, or a benefit term, to matter. Make the same edit in HANDOFF §6.

**Category:** OVERSTATED / ERROR. **Priority:** HIGH.

### P2. Exp 7 Stage 2 re-closure at BASE moved the Exp 6 "certified" safeguard prices, and no document says so

**Files and locations:**

* Technical report §5.6 table and §6.1 F6 row.
* `HANDOFF.md` §2 ("Trust … The Exp 6 safeguard prices, under closure") and §1 table ("0 to +0.91%").
* `README.md` Exp 6 block.
* Errata.

**Problem.** Stage 2 BASE is the Exp 6 model: src digest `b63ae2db…` equals Exp 6's, BASE level digest `79b97699…`, "Experiment 6 exactly". Its closure, now with cross-level imports, improved the Exp 6 closed plans and changed the prices (`EXP7_ANALYSIS.json → f6_prices[level=BASE]`, a fraction × 100, compared with `EXP6_ANALYSIS.json → firewall.policy[].effect_pct`).

| cell | N0 Exp 6 | N0 Exp 7 BASE | N3 Exp 6 | N3 Exp 7 BASE |
|---|---|---|---|---|
| R1_H60 (= R4_C00, B1) | 0.482 | 0.531 | 0.524 | 0.561 |
| R1_H30 | 0.575 | 0.633 | 0.634 | 0.671 |
| R1_H20 | 0.912 | 0.967 | infeasible | infeasible |
| R2_S05 | 0.212 | 0.260 | 0.250 | 0.287 |
| R3_SPAN | 0.482 | 0.500 | 0.524 | 0.561 |
| R4_C05 | 0.244 | **0.146** | 0.321 | **0.225** |
| R4_C01 | 0.428 | 0.389 | 0.477 | 0.436 |
| R6_ADA | 0.440 | 0.489 | 0.485 | 0.522 |
| B2 | 0.482 | 0.500 | 0.524 | 0.561 |

* **The N0 ranking flips:** R4_C05 < R2_S05 now, where Exp 6 had R4_C05 > R2_S05.
* **The pricing reference moved:** N0 REF went from 2,941,892.37 (Exp 6 closed) to 2,940,186.29 (F6 track), −0.058%. The F4-track REF at 2,935,446.46 is a further 0.161% better. Prices measured against the *best-known* REF would therefore be about 0.16 pp higher still.
* **Two claims need scoping:** "certified" prices and the Stage 2 "rank changes against BASE" both refer to the Exp 7 BASE ranking, not to Exp 6's.

**Proposed change.**

* Report §5.6: add a column "Exp 7 Stage 2 BASE (re-closed)" with the values above, and a sentence:

  > Re-closing the same cells at BASE in Exp 7, with cross-level anchors, moved each price by −0.10 to +0.06 percentage points and reordered R4_C05 and R2_S05 on N0. The reference plan used for pricing is itself 0.16% worse in objective than the best-known REF plan (F4 track). Exp 6 prices are therefore basin-dependent at the 0.1-point scale (source: `EXP7_ANALYSIS.json → f6_prices`).

* HANDOFF §2: change "The Exp 6 safeguard prices, under closure" to "The Exp 6 safeguard prices as a 0–1% order of magnitude; individual prices move by up to 0.1 pp under further closure (Exp 7 BASE)".
* Add errata row **E8 (omission)** pointing to this.

**Category:** MISSING / OVERSTATED. **Priority:** HIGH.

### P3. The post hoc F1 survival claim loses its scope downstream (errata E6 is not applied)

**Files and locations:**

* `README.md` lines 282–284 ("it holds at every λ ≥ 2 level").
* Technical report §11, bullet 2 ("every λ ≥ 2 level tested").
* `FUTURE_EXPERIMENTS.md` lines 12–14.
* `HANDOFF.md` lines 31–33.
* `EXPERIMENT7_RESULTS.md` line 61.

**Problem.** Errata E6 and the addendum's "What this changes" table restrict the claim to the six Stage 2 levels (A5, A6), one closure per cell, post hoc. Downstream documents drop "re-optimized (A5/A6)", "one closure per cell", or both. The other Class A dimensions (A1, A2, A3, A7, A8) were never re-optimized under R1_H60.

**Proposed change.** Use the addendum's permitted wording verbatim everywhere:

> Re-optimized under Experiment 1's service rules (no route-period switched off, 60-minute maximum headway; study safeguards, not COTA policy), F1 is −2.1% to −7.0% at every λ ≥ 2 level re-optimized in Exp 7 (A5 and A6 only), with one closure per cell. This is post hoc (`docs/EXPERIMENT7_F1_ADDENDUM.md`). At λ = 1 it is +0.12%.

**Category:** INCONSISTENT / OVERSTATED. **Priority:** HIGH.

### P4. Stability words outside the preregistered bands (reporting rule 5)

**Files and locations:**

* `HANDOFF.md` §1: "It is robust for the certified plans. Under service-preservation rules it is also robust after re-optimization".
* `HANDOFF.md` §7: "Exp 7 shows that the frequency result depends on keeping them".
* Technical report §6.2: "robust **as a policy** that keeps every route-period in service".
* Report §11 and FUTURE line 12: "survives every assumption perturbation".

**Problem.**

* "Robust" applied to a post hoc result borrows the preregistered SIGN_ROBUST label. The addendum itself prohibits "using it to relabel".
* For the fixed plans, the preregistered labels are SIGN_ROBUST with magnitude **Highly sensitive** (A6: 68.5%) and Moderately sensitive (A7). Source: `EXP7_CLOSEOUT_TABLE.json → rows[F1].worst_magnitude_band_by_dimension`. "Survives" hides the magnitude band.
* "Depends on keeping them" overstates the evidence. The REF result is *not identified* (errata E3), which is weaker than "reverses without the rules".

**Proposed change.**

* For the fixed plans, write: "keeps its sign at every Stage 1 level (SIGN_ROBUST; −1.9% to −7.0%; magnitude Highly sensitive to walking friction, A6)."
* For re-optimization, use P3's sentence, with no "robust".
* HANDOFF §7: replace with:

  > Exp 7 shows that the frequency result is identified only when service may not be switched off; without such rules the λ = 2 objective does not determine unserved demand.

**Category:** OVERSTATED. **Priority:** HIGH.

### P5. R2 is mislabelled as a "frequency floor"

**Files and locations:**

* `EXPERIMENT7_CLOSEOUT.md` §5.1: "Every sign event is an R2 frequency-floor cell". Goes through errata.
* `EXPERIMENT7_RESULTS.md` lines 104–106: "R2 frequency floors".
* Technical report §6.1, F6 row: "R2 floors become binding". Also §6.2.

**Problem.** `EXPERIMENT6_CONSTRAINT_CATALOG.md:70` defines R2 as the **OFF-share cap** (`max_off_share = s`). R1 is the max-headway floor. The binding pattern fits the cap reading:

* R2_S10 binds whenever REF switches off more than 17 route-periods (38, 60 and 139 OFF);
* R2_S25 binds only when 60 or 139 are OFF.

**Proposed change.**

* Add errata row **E9**: "§5.1 'R2 frequency-floor cell' → 'R2 OFF-share cap cell'. R2 limits the share of baseline-served route-periods switched OFF (catalog R2); it is not a headway floor."
* In RESULTS and the report, replace "R2 frequency floors" and "R2 floors" with "R2 OFF-share caps (25% and 10%)". Add: "they bind because the re-optimized REF plan switches 38–139 route-periods off".

**Category:** ERROR. **Priority:** HIGH.

### P6. Stage 1 λ = 1 flips are attributed to "collapse", but Stage 1 never re-optimizes

**Files and locations:**

* `EXPERIMENT7_CLOSEOUT.md` §5.2: "The F4 flip at λ = 1, in both stages, is this collapse".
* Closeout §8, third permitted claim: "The only reversal is at λ = 1, where re-optimization collapses service on every network".
* `EXPERIMENT7_RESULTS.md` lines 36–37: "F1, F4, F5 and F6 all change sign at A5_LAM1. That is a property of the objective…".
* The registry's `regime_boundary` text, which cannot be edited. Note this in errata.

**Problem.**

* Stage 1 evaluates *fixed* plans, so nothing collapses there. The Stage 1 F4 flip (−1.31%; `EXP7_STAGE1_ANALYSIS.json → values.A5_LAM1.F4_43`) comes from re-weighting N4's large unserved deficit at λ = 1. Closeout §6 itself calls this "scaling with λ because N4's deficit is coverage".
* F5 is never re-optimized, so its λ = 1 flips are fixed-plan re-weighting too.
* F1 does **not** change sign at A5_LAM1 in Stage 1. It is SIGN_ROBUST with no sign events, so "F1 … all change sign" is true only of Stage 2.

**Proposed change.**

* Add errata row **E10**:

  > §5.2 and §8 (third claim): the Stage 1 F4 flip at λ = 1 is fixed plans re-weighted (N4's coverage deficit is penalised less), not a service collapse. Only the Stage 2 flip is the collapse. The registry's `regime_boundary` sentence "F1/F4/F5/F6 sign changes at lambda=1 are this collapse" is likewise true only for Stage 2 F1/F4/F6; F5 is Stage 1 only.

* RESULTS: rewrite as

  > At A5_LAM1, re-optimized F1, F4 and F6 change sign (Stage 2), and fixed-plan F4, F5 and some F6/AF1 cells change sign (Stage 1) because λ re-weights unserved demand. F1 at fixed plans does not.

**Category:** ERROR. **Priority:** HIGH.

### P7. Report §7 item 7 misstates how far apart the two fixed points are

**File:** Technical report §7, item 7: "Independent closures of the same cell in Exp 7 reached fixed points 0.16–0.40% apart".

**Problem.** The addendum table (`EXP7_F1_DECISION_SPACE.json → rows[].ref_f4_track.objective` against `f6_track_objective`) gives, by level:

| level | objective gap |
|---|---|
| BASE | 0.161% |
| A5_LAM1 | same plan |
| A5_LAM4 | 0.007% |
| A5_TP050 | 0.038% |
| A5_TP200 | 0.401% |
| A6_WALKSPD85 | 0.284% |
| A6_MAXWALK75 | 0.071% |

**Proposed change:**

> …reached fixed points up to 0.40% apart in objective (more than 0.03% apart at five of seven levels: 0.04–0.40%), with F1 differing by up to 36 percentage points (BASE: −5.4% vs +30.5%).

**Category:** ERROR. **Priority:** HIGH.

### P8. README limitations table uses the superseded seed-disagreement range (amendment G1-a)

**File:** `README.md` line 332: "per-route headways | 19–26% seed disagreement".

**Problem.** Guideline amendment G1-a retired "19–26%": 26.0% is the superseded Model A figure, and mixing evaluators breaks rule 1. The canonical figures are `exp1_final.json → plan_disagreement`: mean 19.075%, worst 19.653%.

**Proposed change:** "about 19% of route-periods under Model B (worst pair 19.7%, mean 19.1%)".

**Category:** STALE / ERROR. **Priority:** HIGH.

### P9. No statement of what is preregistered and what is post hoc

**Files:** Technical report §1 (claims each experiment was "preregistered before its production run"), §6, and Appendix. README Exp 7.

**Problem.** A cold reader cannot tell which Exp 7 statements carry preregistered weight. The post hoc or descriptive items are:

* the F1 addendum (R1_H60 / R1_H30 / R3_SPAN);
* the F4-track vs F6-track REF comparison (errata E3);
* the A7 rank-mismatch recomputed labels (`sign_label_excluding_mismatched_A7`);
* the F2 not-applicable exclusion fix;
* the §5.2 mechanism tables;
* the EXP4N spend and OFF statistics ("Descriptive, not preregistered");
* the Exp 4 audit, whose preregistered question was **UNANSWERED** (`EXPERIMENT4_AUDIT_CLOSEOUT.md:75`);
* the Exp 1 gates amended during Exp 1 (the Model B adequacy rule; the gate 11 follow-up).

The operationalizations dated 0929 (A1, A3, A6, A7, A8, A4) were amendments made *before* Stage 1 but *after* the Sept 23 protocol (`EXP7_LEVELS.json → levels[].provenance`).

**Proposed change.**

* Add a table in report §6, as a new §6.0, and reference it from §1:

  | statement | status | where frozen |
  |---|---|---|
  | Stage 1 labels (sign, bands), selection metric, Stage 2 F1/F4/F6/AF1 definitions | preregistered | contract `1263bedaebe6a45d`, amendment §14 |
  | Level settings | as issued 0923 / amendment 0929 / additional | `EXP7_LEVELS.json → provenance` |
  | A7 labels excluding RM04/RM05 | post hoc (flag added at closeout) | `exp7_closeout.py` |
  | F1 under R1_H60/R1_H30/R3_SPAN; second REF fixed point | post hoc | addendum, `EXP7_F1_DECISION_SPACE.json` |
  | λ = 1 and shedding mechanism tables | post hoc diagnostic (skeptic pass) | closeout §5.2 |

* Change §1 to: "each experiment froze a contract before its production run. Analyses added afterwards are marked post hoc (§6.0)."

**Category:** MISSING / OVERSTATED. **Priority:** HIGH.

### P10. No reader's guide to which Exp 7 document is authoritative

**Files:** `HANDOFF.md` §1 "The written record"; `EXPERIMENT7_RESULTS.md` header; report front matter.

**Problem.** There are five Exp 7 texts: closeout, errata, addendum, results note and report. They disagree in places (P3, P5, P6, P13). The RESULTS header cites the closeout but not the errata. HANDOFF's document table omits the closeout, errata, addendum and RESULTS.

**Proposed change.** Add this block to HANDOFF §1 and to the top of RESULTS and the report:

> **Authority order for Experiment 7:**
>
> 1. the JSON artifacts (`outputs/exp7/…`, registered in `CANONICAL_RESULTS_v5.json`);
> 2. `EXPERIMENT7_CLOSEOUT.md` **as corrected by** `docs/EXPERIMENT7_CLOSEOUT_ERRATA.md`. Where they conflict, the errata wins;
> 3. `docs/EXPERIMENT7_F1_ADDENDUM.md`: post hoc, never relabels a preregistered result;
> 4. `docs/EXPERIMENT7_RESULTS.md`: a summary of 2 and 3;
> 5. `docs/report/TECHNICAL_REPORT.md`: synthesis, draft.

**Category:** MISSING. **Priority:** HIGH.

### P11. FUTURE_EXPERIMENTS lacks the cheapest high-value experiment: a preregistered confirmation of the post hoc F1 result

**File:** `docs/FUTURE_EXPERIMENTS.md`, Tier 1.

**Problem.** The study's main robustness claim is now post hoc. It rests on one closure per cell, and the addendum admits that "whether R1_H60's result is itself basin-stable was not tested". E8 and E9 need COTA data. This experiment needs none and could run in the current container (Stage 2 took about 4 days for two dimensions).

**Proposed change.** Add **E7b (Tier 1, runnable now)**:

* Preregister the post hoc F1 definition: N0 under R1_H60 against the current plan at the same level.
* Re-run it with at least 3 independent closures or starts per level, at the six A5/A6 levels **plus** the Stage 1 movers not re-optimized: A7 (Moderately sensitive for F1), A1, A3 and A8.
* Add a period-tilt dimension (P19).
* Also run at least 3 independent REF closures at BASE, to put a distribution on the non-identification (−5.4% vs +30.5%).
* Acceptance: SIGN_ROBUST across all closures at every λ ≥ 2 level.

Reference this from HANDOFF §6.

**Category:** MISSING. **Priority:** HIGH.

---

## MEDIUM

### P12. Report §6.2: "Every positive F1 value coincides with 38–139 route-periods switched off" is false as written

**File:** Technical report §6.2, last bullet. Also addendum, Reading 2 ("The span-preserving cells switch off none").

**Problem.** There are counterexamples in `EXP7_F1_DECISION_SPACE.json`:

| cell | level | F1 | route-periods OFF |
|---|---|---|---|
| R3_SPAN | A5_TP200 | +41.15% | 34 |
| R3_SPAN | A6_WALKSPD85 | +0.02% | 6 |
| R1_H60 | A5_LAM1 | +0.12% | 0 |

The 38–139 figure holds only for REF (the F6 and F4 tracks). R3_SPAN is "span-preserving", yet it switches off 1–86 route-periods.

**Proposed change.**

* Report: "Every positive **REF** F1 value (either track) coincides with 38–139 route-periods switched off."
* Addendum: "The span-preserving cells" → "The R1 cells (no baseline-served route-period OFF)".

**Category:** ERROR. **Priority:** MEDIUM.

### P13. The F2 preregistered label is suppressed in the closeout, RESULTS and README (rule 6)

**Files:**

* `EXPERIMENT7_CLOSEOUT.md` §4, F2 row: "(a null; read via the null test)". Goes through errata.
* Closeout §6, F2 row.
* `EXPERIMENT7_RESULTS.md` "F2".
* `README.md` Exp 7, which does not mention F2 at all.

**Problem.** Amendment §13.2 makes F2 subject to classification. The artifact label is **SIGN_SENSITIVE**: 18 Class A sign flips, including 10 of 20 bootstrap draws. Range −0.226 to +0.166; every dimension is Highly sensitive (`EXP7_CLOSEOUT_TABLE.json → rows[F2 (unserved)]`). The technical report §6.1 states this correctly; the other documents do not.

**Proposed change.**

* Add errata row **E11**:

  > §4 and §6 F2: the preregistered sign label is SIGN_SENSITIVE (18 Class A flips, including 10/20 bootstrap draws; range −0.226 to +0.166%; worst A3_RTNOISE). That is the expected behaviour of an effect of 0.0065%. The null test against the 0.287% floor holds at every applicable level.

* RESULTS and README: one line saying the same.

**Category:** MISSING / INCONSISTENT. **Priority:** MEDIUM.

### P14. Report §6.1 omits the evaluator change behind F1, and has no band column

**File:** Technical report §6.1 table.

**Problem.**

* The F1 row places the "certified −6.65%" next to a Stage 1 range without saying that Stage 1 BASE is **−6.02%** under a different model instance: the Exp 6 instance, with no crowding and the Exp 6 path set (closeout §4.1; `rows[F1].note`). This breaks rule 1 on evaluator identity.
* The table says "stability words follow the preregistered bands" but shows none.
* No row names its network.

**Proposed change.**

* Add columns "network", "Stage 1 BASE" and "worst band (dimension)", populated from `EXP7_CLOSEOUT_TABLE.json`:

  | finding | worst band |
  |---|---|
  | F1 | Highly sensitive (A6) |
  | F3 | Highly sensitive (A1, A7) |
  | F4 | Highly sensitive (A5) |
  | Stage 2 rows | Highly sensitive |

* Add a footnote: "Certified values come from each experiment's own model instance; Stage 1 BASE is the classification reference (amendment §14.1)."

**Category:** MISSING / rule 1. **Priority:** MEDIUM.

### P15. AF1 is treated asymmetrically, and its own basin dependence is unreported

**Files:** Technical report §6.1, AF1 row; closeout §6 (errata); RESULTS "AF1".

**Problem.**

* F3 is given its "SIGN_ROBUST without the mismatched A7 levels" label. AF1 is not, although excluding RM04/RM05 makes **9 of 12** AF1 cells SIGN_ROBUST. Only R4_C05, R4_C01 and R6_ADA remain sensitive (`rows[AF1 *].cross_network_a7_mismatch.sign_label_excluding_mismatched_A7`).
* In Stage 2, the same comparison gives different values on the two tracks:

  | level | F4 track | F6 track |
  |---|---|---|
  | BASE | −0.166% | −0.208% |
  | A5_TP200 | −0.164% | −0.310% |

  (`EXP7_ANALYSIS.json → f4[N0→N3]` against `af1_n3_minus_n0[REF]`.)

**Proposed change.**

* §6.1 AF1 Stage 1 cell: "SIGN_SENSITIVE via A7_RM05 in all 12 cells; excluding the rank-mismatched A7 levels, 9 of 12 SIGN_ROBUST (R4_C05, R4_C01, R6_ADA remain SIGN_SENSITIVE)".
* Stage 2 cell: "N3 better by 0.16–0.31% (F6 track); 0.16–0.18% on the independent F4 track; the gap between tracks is up to 0.15 pp, the same order as the effect, so within model uncertainty."

**Category:** INCONSISTENT / MISSING. **Priority:** MEDIUM.

### P16. Inconsistent level counts

**Files:**

* Closeout §1: "BASE + 47 declared levels".
* Report §6: "declared 49 assumption levels and ran 47".
* README: "at 47 assumption levels … That is 192 cells".

**Problem.** `EXP7_LEVELS.json` holds 47 run levels: 44 Class A, B1, X_TOPK40K and X_ROUNDS4. `declared_not_run` lists A4×2, B2, path-width/scenario-count (DROPPED) and period tilt (NOT INCLUDED). "192 cells" is 4 network variants × 48 (BASE + 47), which the README does not explain.

**Proposed change.** Use one sentence everywhere:

> 47 levels plus BASE were run (44 Class A in seven dimensions, 1 Class B, 2 additional) on four network variants (N0, N3, N4, N0S): 192 evaluation cells. Declared but not run: A4 reliability (2 levels, UNIMPLEMENTED), B2 jobs-accessibility (UNTESTED), path-width/scenario count (DROPPED as inert), period tilt (NOT INCLUDED).

**Category:** INCONSISTENT. **Priority:** MEDIUM.

### P17. Report §6 dimension table is too vague, and Class B / additional results are missing

**File:** Technical report §6, the table of dimensions A1–A8.

**Problem.**

* The table gives no level settings or provenance. A8 "the retention curve" hides that `full_min` was not varied.
* A6 is bundled, A1 adds demand only on commute pairs, and A3 holds the envelope fixed. These bounds appear in the closeout and RESULTS but not in the report.
* The Class B and additional values are never reported, although they are informative:

  | finding | X_TOPK40K | B1_COMMONLINES | X_ROUNDS4 |
  |---|---|---|---|
  | F1 | −5.49% | −5.99% | — |
  | F4 | +8.82% | **+7.86%** | +9.67% |

  F4 under B1 independently matches Exp 4A's omission-corrected +7.87% (`rows[].class_b_and_additional`).

**Proposed change.**

* Replace the "what it perturbs" column with the exact settings from `EXP7_LEVELS.json`:
  * A1: +25/50/100% non-commute demand on commute OD pairs only;
  * A3: runtime ×1.1, ×1.2, and lognormal noise (median |error| 20.5%), envelope fixed;
  * A5: λ 1/4, transfer penalty 5/20 min;
  * A6: walk speed 68 m/min; access 450 m and transfer walk 300 m (bundled);
  * A7: remove each of the 10 busiest routes, resources kept in the envelope;
  * A8: retention zero point 150 min; floor 0. `full_min` not varied.
* Add a provenance column (0923 as issued, or 0929 amendment).
* Add a short "Class B and additional (never label findings)" table with the values above.

**Category:** CLARITY / MISSING. **Priority:** MEDIUM.

### P18. Three of the existing errata rows contain errors

**File:** `docs/EXPERIMENT7_CLOSEOUT_ERRATA.md`.

**Problem.**

* **E1** says two later scripts appear. `git diff --stat 4a2ba9f6 HEAD -- scripts/ src/` shows **three** new files: `canonical_results_v5.py`, `exp7_f1_decision_space.py` and `verify_report_claims.py`.
* **E5** corrects nothing: the closeout already said "near-empty". It also cites N0 figures for a claim about N3. Both networks hold the **same plan** at λ = 1 (digest `76430e1f43635d31`, 139 OFF; `EXP7_ANALYSIS.json → f4[A5_LAM1]`).
* **E6** cites "§8 first permitted claim", which actually reads "every implemented Stage 1 assumption level". The phrase "every λ ≥ 2 level" is in §8's **third** claim and in the §6 F4 and AF1 rows.

**Proposed change.**

* E1: list the three files, and add "all reporting-only; `src/cota_opt` unchanged".
* E5: change to "Clarification: N0 and N3 converge to the identical plan `76430e1f…` (139 of 173 route-periods OFF, 557 of 2,516 h). Near-empty, not empty."
* E6: change the location to "§6 F4 and AF1 rows; §8 third permitted claim; addendum".

Errata is unregistered, so editing in place is acceptable. If errata is meant to be append-only, add these as rows "E1′, E5′, E6′".

**Category:** ERROR. **Priority:** MEDIUM.

### P19. Technical report §8 is missing material limitations

**File:** Technical report §8 table.

**Problem.** These limitations are absent (rule: each limitation with its size and direction):

* **Period demand shares are assumed.** LODES has no time dimension, and Exp 7 period tilt was NOT INCLUDED. This is central to a result about moving frequency between periods.
* **Stage 2 covered two of seven dimensions.**
* **One closure per cell.** Closures of the same cell differ by up to 0.40% in objective (P7) and by 36 pp in F1.
* **The unserved penalty is inconsistent with the retention curve** (P1).
* **λ is a value judgement** (the guidelines' calibration register).
* **The A1, A3, A6 and A8 operationalization bounds.**

**Proposed change.** Add rows, for example:

* "Period demand shares | assumed (LODES has no time dimension); untested in Exp 7 (period tilt not included) | unknown; affects where frequency moves by period".
* "Single closure per cell | two closures of one cell differ by ≤0.40% in objective, −5.4% vs +30.5% in F1 | served-trip, GC and OFF-permitting F1 figures are basin-dependent".
* "Stage 2 scope | A5, A6 only | no re-optimized claim for demand, runtime, route-removal or retention perturbations".

**Category:** MISSING. **Priority:** MEDIUM.

### P20. "Exp 1's rules" and R1_H60 are never named as study safeguards (rule 9)

**Files:**

* Addendum, Reading 3: "which rules COTA would plan under".
* Technical report §3 and §6.2.
* `HANDOFF.md` §7: "Exp 6 prices the rules".
* README Exp 7.

**Problem.** `preserve_span` and the 60-minute max headway come from `config/constraints.yaml`. The Exp 6 catalog classes R1 as a **study safeguard**: "none found (S4). S1 requires a COTA headway standard; value UNKNOWN". Calling them "Exp 1's own rules" or "rules COTA would plan under" suggests COTA policy.

**Proposed change.** At first use in each document, write "Experiment 1's service rules (study safeguards in `config/constraints.yaml`; no documented COTA numeric standard)". In the addendum, replace "which rules COTA would plan under" with "which service rules a planner chooses to impose".

**Category:** MISSING / rule 9. **Priority:** MEDIUM.

### P21. F6 counts overstate independent evidence, and rule 3 is not applied

**Files:** Technical report §6.1, F6 row; closeout §4 (via errata E2); RESULTS.

**Problem.**

* **N0 duplicates.** In Stage 1, R1_H60, R3_SPAN, R4_C00, B1 and B2 are the same plan, at 0.482 at every level. Two further cells are identically zero. "11 of 13 SIGN_ROBUST" is therefore 5 of 7 distinct non-zero plans.
* **N3 duplicates.** "5 of 12" is 3 of 6 distinct non-zero plans.
* **Near-zero flips.** The six N3 flips at λ = 4 are to −0.007% and −0.010% (`rows[F6 N3 *].class_a_range`).
* **Rule 3.** Cells whose range spans zero should be labelled "within model uncertainty":

  | cell | range |
  |---|---|
  | N0 R4_C05 | −1.33 to +2.05 |
  | N0 R4_C01 | −0.99 to +2.05 |
  | N3 R6_ADA | −2.25 to +3.60 |
  | N3 R1_H60 group | −0.007 to +0.99 |

**Proposed change.** F6 Stage 1 cell:

> N0: 11 of 13 cells SIGN_ROBUST (5 of 7 distinct non-zero plans; R2_S25/S10 are zero at every level). N3: 5 of 12 (3 of 6 distinct); six flips at λ = 4 are to −0.01% or less. R4_C05, R4_C01 (N0) and R6_ADA (N3) span zero: within model uncertainty (rule 3).

**Category:** OVERSTATED / rule 3. **Priority:** MEDIUM.

### P22. "Prices non-negative at every level" is partly true by construction, and false for Stage 1

**Files:** `EXPERIMENT7_CLOSEOUT.md` §8, fourth permitted claim (errata); `README.md` Exp 7 ("Safeguard prices (F6): non-negative at every level"); `HANDOFF.md`.

**Problem.**

* Stage 1 fixed-plan prices go negative: N0 R4_C05 reaches −1.333%, and N3 R6_ADA reaches −2.251%. Closeout §4 says so.
* Stage 2 non-negativity is enforced by certification (closeout §5.1: "a negative price would have blocked certification"). It is not a robustness finding.
* As the README's only F6 line, it misinforms.

**Proposed change.**

* Add errata row **E12**: "§8 fourth claim: 'non-negative at every level' applies to re-optimized (Stage 2) prices and is guaranteed by certification; fixed-plan prices go negative at λ = 1 and 4 and at A7_RM09."
* README F6 line: "re-optimized rankings unchanged at transfer penalty ×0.5 and moved at λ = 1, transfer ×2 and the walking levels; the R2 OFF-share caps become binding where the optimizer sheds service; fixed-plan prices change sign in 2 of 13 N0 and 7 of 12 N3 cells".

**Category:** OVERSTATED. **Priority:** MEDIUM.

### P23. Provenance gaps: no contract digests or commits, an unregistered post hoc artifact, and weak verifier coverage

**Files:** Technical report Appendix A; addendum header; `scripts/verify_report_claims.py` (coverage only; no edit to JSON proposed).

**Problem.**

* Definition-of-done item 3 requires artifact, contract digest and commit for every number. Appendix A gives artifact and key only. The one commit given is Exp 1's `f1a05645`.
* `EXP7_F1_DECISION_SPACE.json` is not in the registry's `artifact_sha256` list. It is the source of the report's headline robustness claim.
* The verifier covers 30 numbers. It misses:
  * +30.5% and 0.161%;
  * the objectives 2,940,186 / 2,935,446;
  * 557 / 1,583 / 29,366;
  * the F2 range;
  * the F6 counts (11/13, 5/12, 25);
  * the Stage 2 rank-change counts;
  * the AF1 values.

**Proposed change.**

* Add "contract digest" and "commit" columns to Appendix A. Exp 7 values: contract `1263bedaebe6a45d`; Stage 2 analysis at `b0f6f416`; addendum artifact at `5dc3f408`.
* State the addendum artifact's hash in the addendum header: `0d5e3da76ebdc6ad67493e4ce93061c1536e313ac558e605e9d631a764015280`.
* Register the artifact in a v6 registry at the freeze.
* Extend the verifier to the numbers listed above.

**Category:** MISSING / DoD 3. **Priority:** MEDIUM.

### P24. The glossary lacks Exp 7 terms, and docs/GLOSSARY.md's λ entry is stale (rule 11)

**Files:** Technical report Appendix B; `docs/GLOSSARY.md` (dated 2026-09-28).

**Problem.**

* Neither glossary defines: SIGN_ROBUST / SIGN_SENSITIVE, SIGN_FLIP / TO_TIE / FROM_TIE, the magnitude bands, MAGNITUDE_RATIO_UNINFORMATIVE, Stage 1 / Stage 2, F1–F6 / AF1, F4 track / F6 track, REF, R1–R6 / B1–B2, N0S, level codes, "fixed point", "not identified".
* GLOSSARY's λ entry says "every certified comparison here uses λ = 2". Exp 7 certified Stage 2 cells at λ = 1 and λ = 4.

**Proposed change.**

* Add these terms to Appendix B, or link a new GLOSSARY section.
* Fix the λ entry: "…certified frontier begins at λ = 2; Exp 7 also certified Stage 2 cells at λ = 1 and 4 as sensitivity levels, never as findings".

**Category:** MISSING / STALE. **Priority:** MEDIUM.

### P25. Abstract and §5.1 mix two Exp 1 figures without explanation

**File:** Technical report, abstract bullet 1 and §5.1.

**Problem.**

* The headline −6.65% is the **3-seed mean** (`exp1_final.json → headline.unserved_demand.mean_pct = −6.652`).
* "About 680 more trips" and "10,262 → 9,583" come from the **single λ = 2 frontier run** (−6.602%, `frontier[λ=2]`).
* The frontier table then shows −6.60% at λ = 2. A careful reader sees two values for the same quantity.

**Proposed change.** In §5.1, after the trips sentence, add:

> (the frontier run at λ = 2; the three-seed headline mean is −6.65%, about 683 trips.)

In the abstract, write "about 680 (one frontier run)", or derive the figure from the mean.

**Category:** CLARITY / INCONSISTENT. **Priority:** MEDIUM.

### P26. Abstract numbers lack network and source (rules 1 and 6)

**File:** Technical report, abstract: greenfield "worse … by 8–10% of the objective"; safeguards "cost 0 to 0.91% … each".

**Problem.**

* "8–10%" mixes Exp 4A's certified +9.66% with Exp 7 Stage 2 BASE +8.55%, and drops the Stage 2 range +6.8% to +30.8%.
* "0 to 0.91%" is N0 only. It drops N3 (0 to 0.63%) and the infeasible N3 20-minute floor, which is a result with no finite price.

**Proposed change.**

> worse than the Exp 3 redesign (N3) by +9.66% of N3's objective (Exp 4A, λ = 2), and worse at every λ ≥ 2 level re-optimized in Exp 7 (+6.8% to +30.8%).

> Safeguards (study safeguards, not COTA policy) price at 0 to 0.91% of the objective on N0 and 0 to 0.63% on N3 (Exp 6). The 20-minute floor is infeasible under the modeled envelope on N3. Further closure in Exp 7 moved individual prices by up to 0.1 points (P2).

**Category:** OVERSTATED / rule 1. **Priority:** MEDIUM.

### P27. Addendum: the claim that R1_H60 "matches" Exp 1's frontier at λ = 1 is wrong

**File:** `docs/EXPERIMENT7_F1_ADDENDUM.md`, Reading 1, last sub-bullet.

**Problem.**

* At λ = 1, R1_H60 gives **+0.12%** while Exp 1's frontier gives **−1.42%**: opposite signs.
* The comparison also crosses model instances (crowding on and 243k paths, against the Exp 6 instance) and solvers (Gen1 against the (8,3) block certifier).
* "Exp 1's own service rules" is accurate. Calling the setup "Exp 1's model" would not be.

**Proposed change.**

> This agrees in sign and range with the Stage 1 fixed-plan result (−1.9% to −7.0%) at λ ≥ 2. At λ = 1 it differs in sign from Exp 1's uncertified frontier point (−1.42%), which used a different model instance (crowding on, 243,257-path set) and solver (Gen1).

Also add one line to "Why this exists": "Same service rules as Exp 1; model instance and certifier are Exp 6's."

**Category:** ERROR / OVERSTATED. **Priority:** MEDIUM.

### P28. FUTURE E8 proposes calibrating λ, which the guidelines define as a value judgement

**File:** `docs/FUTURE_EXPERIMENTS.md` E8, "What would change the answer", bullet 2.

**Problem.** "A calibrated λ·w_unserved". The guidelines' calibration register lists λ with the calibration data "None; it is a value judgement". Only `w_unserved` (the 60-min penalty) and the retention curve can be calibrated.

**Proposed change.**

> a calibrated unserved-trip penalty w_unserved (or retention curve) such that, at the policy λ, λ·w_unserved falls below typical served-trip GC…

**Category:** ERROR. **Priority:** MEDIUM.

### P29. FUTURE E14 reuses A4 levels that the protocol says cannot represent reliability

**File:** `docs/FUTURE_EXPERIMENTS.md` E14, design bullet 2.

**Problem.** E14 proposes re-running Stage 1 "at its preregistered A4 levels (schedule coefficient 0.375 / 0.50)". `EXP7_LEVELS.json → declared_not_run[A4_*].why` says that coefficient touches wait only above 12-minute headways and has no variance term. A new headway-variance model needs new levels expressed in its own terms.

**Proposed change.**

> Preregister new A4 levels in the new model's terms (for example, headway coefficient of variation by route-period at the AVL-observed median and 90th percentile); the 0929 schedule-coefficient levels are retired as non-representative.

Add AVL data as a precondition, shared with E13.

**Category:** ERROR (infeasible design). **Priority:** MEDIUM.

### P30. Ordering and preconditions in FUTURE_EXPERIMENTS

**File:** `docs/FUTURE_EXPERIMENTS.md`.

**Problem.**

* Period tilt (NOT INCLUDED) is missing from E20.
* Tier 1 puts experiments that need COTA's non-public APC and survey data ahead of runnable ones without saying they are blocked.
* E12 (timed transfers) depends on reliability (E14). Pulses fail under irregular headways, and the document does not note this.
* The "divides wall time by the core count" claim ignores closure. Closure passes run sequentially per (track, network) under an exclusive lock; the F6 cross-level stage took 10–17 min per transfer.

**Proposed change.**

* Add "Period tilt: the period-share assumption (LODES has no time dimension)" to E20, or fold it into E7b (P11).
* Mark E8, E9, E11 and E13 "blocked on COTA data".
* Add an E14 precondition to E12.
* Qualify the parallelism note: "Stage 1 and initial solves parallelise per cell; closure is sequential by pass within a (track, network)."
* Make the same qualification in report §10.

**Category:** MISSING / CLARITY. **Priority:** MEDIUM.

### P31. HANDOFF §3 git state is partly unverifiable and partly wrong

**File:** `HANDOFF.md` header and §3.

**Problem.**

* The header says the previous version is "2026-08-29, written mid-Experiment 2 … at `5eebe36a`". Commit `5eebe36a` is dated 2026-09-29, and its HANDOFF is the Exp 6 results version.
* "Ian's machine holds the same commits on branch `exp7-work`" cannot be checked from the container. The guideline's own G1-c verification note sets the standard: record such statements as Ian's.
* `5dc3f408`, which contains this HANDOFF, the report, the errata and the addendum, may postdate the delivered bundle.
* The container's `github/master` remote-tracking ref is `196295c9` as of last fetch, 612 commits behind HEAD.

**Proposed change.**

* Fix the header: "The previous version (2026-09-29, after Exp 6) is at `5eebe36a`."
* In §3, name the exact commit delivered to `exp7-work`, add "(per Ian; not verifiable from the container)", and add: "Commits after `<hash>`, including `5dc3f408` (this write-up), need a further bundle."

**Category:** STALE / ERROR. **Priority:** MEDIUM.

### P32. README front-door wording outside the Exp 7 block contradicts the guidelines

**File:** `README.md`.

**Problem and fix, by line:**

* **Line 9**, "calibrated where public data allows". This contradicts the model status ("Uncalibrated. Every cost weight…"). Replace with "built from public data, uncalibrated, and explicit about every assumption".
* **Lines 115 and 121**, "common **peak-vehicle** envelope" and "peak-vehicle cap". These break rule 4, because the quantity is in proxy units. Replace with "common resource envelope (revenue vehicle-hours plus the per-period peak-concurrency proxy)".
* **Line 23**, "6.65% ± 0.06". Rule 2 requires the label: "± 0.06 (solver seed spread, SD of 3 seeds)".
* **Line 54**, "satisfied almost for free". No experiment tested this. Use the report's wording: "likely at little cost (untested)".
* **Line 321**, cites `CANONICAL_RESULTS_v4.json`. Update to v5.
* **Exp 7 block.** Add one line: "Not an operating plan; not COTA-endorsed; commute-only proxy demand; scheduled service" (rule 10).

**Category:** STALE / rule 2 / rule 4 / rule 10. **Priority:** MEDIUM.

### P33. README F4 line conflates the two stages

**File:** `README.md` Exp 7: "Greenfield (F4): worse than N3 at every λ ≥ 2 level in both stages, by +6.8% to +30.8%."

**Problem.** +6.8% to +30.8% is Stage 2 only. Stage 1, at every Class A level except λ = 1, runs from +7.70% (A7_RM02) to +19.35% (A5_LAM4) (`EXP7_STAGE1_ANALYSIS.json → values.*.F4_43`).

**Proposed change:**

> worse than N3 at every Class A level except λ = 1 at fixed plans (+7.7% to +19.4%), and at every λ ≥ 2 level re-optimized (+6.8% to +30.8%); at λ = 1, −1.31% (fixed plans) and −0.98% (re-optimized).

**Category:** INCONSISTENT. **Priority:** MEDIUM.

---

## LOW

### P34. REPRODUCE Exp 7 section is stale and incomplete

**File:** `docs/REPRODUCE.md`, Experiment 7 section; also line 116.

**Problem.**

* "the three post-freeze script changes" is stale per errata E1 and P18.
* There is no single-cell spot check, unlike Exp 5 and 6. `exp7_stage1.py cell --variant N0 --level BASE` exists, and the expected values are in `outputs/exp7/stage1/evals/N0/BASE.json`.
* The freeze, levels and A7-ranking steps are missing: `exp7_levels.py`, `exp7_busiest_routes.py --out`, `exp7_freeze.py --levels`.
* "Verified … on local `master`" gives no hash.
* There is no Stage 1 wall time, and "Production took 192 Stage 1 cells" is garbled.
* The Exp 6 heading still says "production in progress".

**Proposed change.**

* Point to the errata for post-freeze changes.
* Add the spot check: "`python scripts/exp7_stage1.py cell --variant N0 --level BASE` → compare `rows[]` with `outputs/exp7/stage1/evals/N0/BASE.json` (N0 current-plan unserved 10,423.684…)".
* List the freeze steps as "done; refuse to overwrite".
* Give the commit hash and a measured Stage 1 wall time.
* Change the Exp 6 heading to "(closed, `EXP6_POLICY_FRONTIER_CERTIFIED`)".

**Category:** STALE / MISSING. **Priority:** LOW.

### P35. RESULTS quotes served-trip figures without basin labels

**File:** `docs/EXPERIMENT7_RESULTS.md`, F4 reading: "at BASE N4 serves 12,700 trips against N0's 17,349".

**Problem.** Closeout §9 prohibits served-trip figures as findings because they are basin-dependent. These come from the F4-track basins (N0 has 48 OFF here, against 21,091 served on the F6 track). The headline comparison is also N4 against N3, not N0.

**Proposed change:**

> (illustrative; F4-track basins: N4 12,700, N3 17,389, N0 17,349 served; basin-dependent and not a finding)

**Category:** OVERSTATED. **Priority:** LOW.

### P36. The technical report deviates from the guideline outline without saying so

**File:** Technical report structure.

**Problem.** The guideline outline is §§1–10 plus appendices: decision log, retractions, preregistration amendments, superseded-artifact index, calibration register, glossary. The report adds §11 and has only Appendices A (sources) and B (glossary).

* Retractions sit in the main text (§9). That satisfies rule 7.
* There is no appendix on preregistration amendments. The Exp 7 sequence is not tabulated: as issued 9/23 → finalization → amendment §§13–14 (two-stage; full closure rejected at about 2,300 h) → 0929 operationalizations.
* There is no superseded-artifact index. Exp 7 items such as `SUPERSEDED.EXP7_LEVELS.PROPOSED.json`, `EXPERIMENT7_AMENDMENT_DRAFT.md` and the replacement protocol draft are not in `outputs/SUPERSEDED.md`.
* There is no calibration register. `docs/CALIBRATION.md` does not exist yet.

**Proposed change.**

* Add an "Outline conformance" note to the draft status.
* Add Appendix C (preregistration amendments, with the Exp 7 sequence), Appendix D (a pointer to `DISCOVERIES.md` with a D-number index), and placeholders for E (superseded index) and F (calibration register) marked "pending release work".
* Add the Exp 7 superseded items to `outputs/SUPERSEDED.md`.

**Category:** MISSING / structure. **Priority:** LOW.

### P37. Minor clarity items in the technical report

**File:** Technical report.

* **Abstract**, methodological result 1, "That error produced and then withdrew a headline twice". Retraction R3 was an evaluator mislabel, not a convergence problem. Write "That error produced, and then withdrew, the 0.5% through-routing headline (R4)", or name the two instances.
* **§1 and §5.1**, "within 0.06 points". Say "within 0.064 percentage points of unserved-demand change".
* **§6**, "every certified plan (60-entry registry)". The registry includes the uncertified N0 current plan and the Exp 5 plans, which come from a failed experiment. Write "60 frozen plans from Exps 1–6 (59 evaluable)".
* **§10**, "AVL … would populate the reliability term". This requires a reviewed `src/cota_opt` change (A4 was UNIMPLEMENTED for that reason). Add "(after the E14 model change)". Also note that `docs/DATA_INTERFACES.md` is planned, not present.

**Category:** CLARITY. **Priority:** LOW.

---

## Proposed errata rows, consolidated

These would be appended to `docs/EXPERIMENT7_CLOSEOUT_ERRATA.md`. The closeout itself stays untouched.

| row | closeout location | issue | source |
|---|---|---|---|
| E7 | §0, §5.2 | "no operating-cost term" is the wrong mechanism | P1 |
| E8 | §6 F6 row, §8 | omission: BASE re-closure moved the Exp 6 prices; the F6-track REF is 0.161% worse than the best-known REF | P2 |
| E9 | §5.1 | R2 is the OFF-share cap, not a frequency floor | P5 |
| E10 | §5.2, §8 third claim, registry `regime_boundary` | the Stage 1 λ = 1 flips are re-weighting, not collapse | P6 |
| E11 | §4, §6 F2 rows | preregistered label SIGN_SENSITIVE omitted | P13 |
| E12 | §8 fourth claim | non-negativity holds only for Stage 2, and is guaranteed by certification | P22 |
| E13 | §6 F1 row | add the magnitude band: Highly sensitive (A6) | P4 |

Also revise E1, E5 and E6 as described in P18.
