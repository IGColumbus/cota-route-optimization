# Reviewer 2 adjudication of Reviewer 1's proposals (P1–P37, errata E7–E13)

Adjudicated 2026-10-04 against HEAD `5dc3f408` (working tree clean). Read-only: no repository file edited, no experiment script run. `python scripts/verify_report_claims.py` returns 30/30. `EXPERIMENT7_CLOSEOUT.md` is untouched and still registered by sha256 (`27bfc739…`).

**Totals (37 proposals):** ACCEPT 9 (P3, P5, P7, P8, P12, P13, P20, P33, P35); ACCEPT WITH MODIFICATION 28 (all others); REJECT in full 0. Parts are rejected inside five proposals: P17 (the "B1 independently matches Exp 4A" sentence), P18 (the E5 rewrite), P23 (creating a v6 registry now), P30 (E13 "blocked on COTA data"; unsourced timings), P37 (the DATA_INTERFACES note and Reviewer 1's own "0.064" fix).

Reviewer 2 also found five issues Reviewer 1 missed (N1–N5, end of this file). Two of them matter: N2 (the zero R2 prices hold only in the F6-track basin) and N3 (the Exp 1 "within 0.064 points" wording is a standard deviation, not a bound).

**Two hazards for the implementer:**

* `scripts/verify_report_claims.py` passes only if each listed document still contains the exact written string. Re-run it after every edit batch; strings such as `+0.12%` in the report and `−6.57%`, `−7.00%`, `−2.14%` in the addendum must survive.
* `python scripts/exp7_stage1.py cell …` **overwrites** the git-tracked canonical file `outputs/exp7/stage1/evals/<variant>/<level>.json` without a guard (`evaluate_cell` → `atomic_write_json`). Never run it in this checkout (see P34).

**Errata numbering.** Existing rows are E1–E6, so new rows are E7–E15. `docs/FUTURE_EXPERIMENTS.md` also uses E8–E20 for proposed experiments. To avoid collisions, always write "errata E7" or "FUTURE E10" in cross-references, and number Reviewer 1's proposed new experiment **E21**, not "E7b".

**Errata editing policy.** Append only. E1 and E6 are superseded by new rows E14 and E15. The errata file is unregistered and dated today, so editing in place would be allowed. It is still cited by row range from report §9 R12 ("E1–E6"), and a correction record should not silently change. E5 is left as written (see P18).

---

## HIGH

### P1 — "no operating-cost term" is the wrong mechanism — **ACCEPT WITH MODIFICATION**

**Verified.**

* `src/cota_opt/pathset.py` `PathSetEvaluator.evaluate`: objective = Σ served·c + (λ·60)·unserved, with retention `keep(c)` linear from 1.0 at 60 min to 0.10 at 210 min (`config/assumptions.yaml` 60/210/0.10; A8 varies only zero point and floor).
* Making an OD unservable changes its contribution from f·[r(c)·c + λ60·(1−r(c))] to f·λ60, a saving of f·r(c)·(c − λ60). The saving is positive iff c > λ·60, and the hours freed are re-spent elsewhere under the fixed envelope. The envelope is a cap: records carry `resource.requested.hours_cap 2517.18`.
* Hours (`EXP7_F1_DECISION_SPACE.json → rows[].cells`): REF and R1_H60 use 2,517.14 and 2,515.00 h at A5_TP200, 2,515.13 and 2,516.07 h at A6_WALKSPD85, and 2,515.49 and 2,515.11 h at A6_MAXWALK75. At BASE they use 2,515.54 and 2,515.83 h. An hours-priced term is essentially constant across these plans. At λ = 1 the collapsed plan uses 556.6 h, so an operating cost would favour it further.
* r(120) = 1 − 0.9·60/150 = 0.64. Correct.

**Correction to Reviewer 1.** Reviewer 1's E7 text says "λ × 60 is below the generalized cost of many served trips (mean 83–86 min)". At λ = 2 the penalty is 120, which is **above** the mean (GC per served trip at BASE is 83.3 for REF, 84.3 for R1_H60 and 86.3 for the current plan). The mean is below the penalty only at λ = 1. At λ ≥ 2 the mechanism works on the **high-GC tail**: the closeout's own "marginal served trip". The A5_TP200 and A6 levels enlarge that tail. Reviewer 1's "reviewer analysis" wording ("contradicts" the retention curve) is also stronger than needed; "is not consistent with" is enough.

**Edits:**

1. Errata **E7**: final text in the errata block below.
2. `docs/report/TECHNICAL_REPORT.md` §3 "Objective", replace the two bullets "The objective has **no operating-cost term.** …" and "Below some λ it therefore prefers …" with:
   > * The objective has no operating-cost term; operating resources enter only as constraints (the envelope is a cap).
   > * A served trip counts its full generalized cost c; a lost trip counts λ · 60. Whenever c > λ · 60, making the trip unservable lowers the objective, and the freed hours are spent elsewhere. Below some λ the optimizer therefore drops hard-to-serve riders (§6.2). An operating-cost term would not prevent this (errata E7).
3. Report §6.2, first bullet after the λ = 1 table. Old: "At λ = 1 an unserved trip costs 60 while a served trip averages 83–86 GC. With no operating-cost term, removing service lowers the objective." New:
   > At λ = 1 an unserved trip costs 60 while a served trip averages 83–86 GC, so removing most service lowers the objective. At λ = 2 only trips above 120 min of GC are exposed.
4. Report §6.2 "Two readings", item 2. Replace "an operating-cost term;" with:
   > an unserved-trip penalty at least as large as the generalized cost of the trips it would replace (for example, tied to the retention curve's 210-min zero point), or an ε-constraint on unserved demand;
5. Report §8, add a row (see P19):
   > Unserved penalty vs retention curve | λ · 60 = 120 min at λ = 2, while the retention curve still keeps 64% of riders at 120 min and 10% beyond 210 min | the objective prefers losing trips the model's own demand curve treats as mostly still made; drives the shedding in §6.2 (post hoc analysis)
6. `README.md` line 288–289. Old: "…(557 of 2,516 vehicle-hours), because the objective has no operating-cost term." New:
   > …(557 of 2,516 vehicle-hours): at λ = 1 a lost trip costs 60 min while the average served trip costs 83–86 min of generalized cost.
7. `docs/EXPERIMENT7_RESULTS.md` "The regime boundary". Old: "It has no operating-cost term. When λ · 60 is below…" New:
   > It has no operating-cost term, but that is not the cause (errata E7). When λ · 60 is below the generalized cost of a served trip, making that trip unservable lowers the objective.
8. `docs/EXPERIMENT7_F1_ADDENDUM.md` Reading 3 (the addendum is unregistered, so edit it directly). Old: "With no operating-cost term, the λ-weighted objective rewards shedding hard-to-serve riders when their generalized cost exceeds λ × 60." New:
   > Because a lost trip costs λ × 60 while a served trip costs its full generalized cost, the λ-weighted objective rewards shedding hard-to-serve riders whose generalized cost exceeds λ × 60.
9. `docs/FUTURE_EXPERIMENTS.md` E10:
   * **Question:** "…when service can be cut but cutting service has a price?" → "…when losing a trip is priced at least as high as serving it?"
   * **Why:** "with no operating-cost term, collapses service" → "whose unserved penalty (λ · 60) is below the generalized cost of many served trips, collapses service"
   * **Design (2):** replace with:
     > **Unserved penalty consistent with the retention curve:** set λ · w_unserved at or above the generalized cost at which the retention curve treats a trip as lost (for example, its 210-min zero point), and report whether shedding persists. An operating-cost term is not a remedy for shedding (it rewards removing service); it matters only if the fixed envelope is replaced by a priced budget.
10. `HANDOFF.md` §6 item 4. Old: "(ε-constraint or operating-cost term)". New:
    > (ε-constraint on unserved demand, or an unserved penalty consistent with the retention curve)

### P2 — Exp 7 BASE re-closure moved the Exp 6 prices — **ACCEPT WITH MODIFICATION**

**Verified.**

* BASE is Exp 6's model: record `level.rationale` reads "Experiment 6 exactly", `level_digest 79b97699909ebb59`, the src digest equals Exp 6's, and the contract carries `base_reuse_exp6_initial`.
* `EXP7_ANALYSIS.json → f6_prices[BASE]` against `EXP6_ANALYSIS.json → firewall.policy[].effect_pct` (equal to `frontier[].policy_cost_closed_pct`) reproduces every value in Reviewer 1's table. Range of change: −0.098 (N0 R4_C05) to +0.058 (N0 R1_H30) percentage points.
* REF: Exp 6 closed 2,941,892.37 (Stage 1 row `F6_N0_REF`, 15 OFF) → F6 track 2,940,186.29 (17 OFF) → F4 track 2,935,446.46 (48 OFF), which is 0.161% better.
* Exp 7 also improved R1_H60 at BASE, by 270.65 (0.009%), via a cross-level import from the A5_TP050 plan (record `N0_R1_H60__anchor_9f93440c…`). Most of the price movement is the REF improving.

**Correction to Reviewer 1.** The R4_C05 / R2_S05 reorder happens on **both** networks, not N0 only. N3 goes from 0.321 / 0.250 to 0.225 / 0.287. Also, R3_SPAN and B2 (0.500) now separate from R1_H60 (0.531) on N0, where Exp 6 had them tied at 0.482.

**Addition (Reviewer 2, N2).** On N0, R2's caps are ⌊0.25·173⌋ = 43 and ⌊0.10·173⌋ = 17 route-periods. Records report `n_baseline_served_rp 173`. The best-known REF at BASE (F4 track, 48 OFF) violates both caps. The zero prices of R2_S25 and R2_S10 therefore hold only relative to the F6-track (and Exp 6) REF basin. Against the best-known REF they would be positive, about 0.16%. The README's "They do not bind at the best-known unconstrained plan" is now stale.

**Edits:**

1. Errata **E8**: final text below.
2. Report §5.6. Add a column "Exp 7 Stage 2 BASE re-closed (N0 / N3)" with the values from `EXP7_ANALYSIS.json → f6_prices[level=BASE]` × 100, rounded to 3 dp:
   * OFF-share 25% / 10%: 0 / 0
   * OFF-share 5%: 0.260 / 0.287
   * coverage c = 0.05: 0.146 / 0.225
   * coverage c = 0.01: 0.389 / 0.436
   * ¾-mile: 0.489 / 0.522
   * 60-min floor: 0.531 / 0.561 (R3_SPAN and B2 0.500 on N0)
   * 30-min floor: 0.633 / 0.671
   * 20-min floor: 0.967 / infeasible

   Then add after the table:
   > Re-closing the same cells at BASE in Exp 7 (same model; closure now with cross-level anchors) moved each price by −0.10 to +0.06 percentage points and reversed the order of coverage c = 0.05 and OFF-share 5% on both networks. The Exp 7 pricing reference is itself 0.16% worse in objective than the best-known REF plan (F4 track, 48 route-periods OFF). Against that plan every price would be about 0.16 points higher, and the 25% and 10% OFF-share caps would bind. Exp 6 prices are therefore basin-dependent at the 0.1-point scale (post hoc comparison; `EXP7_ANALYSIS.json → f6_prices`, `EXP7_F1_DECISION_SPACE.json → rows[BASE].ref_f4_track`).
3. Report §6.1 F6 row, Stage 2 cell: append "BASE re-closure moved Exp 6 prices by −0.10 to +0.06 points (§5.6)."
4. `HANDOFF.md` §2. Old: "**The Exp 6 safeguard prices**, under closure." New:
   > **The Exp 6 safeguard prices** as a 0–1% order of magnitude. Individual prices moved by up to 0.1 points under further closure in Exp 7, and the zero prices of the 25%/10% OFF-share caps hold only in one basin (errata E8).
5. `README.md` Exp 6 block, line 226–227. Old: "They do not bind at the best-known unconstrained plan." New:
   > They do not bind at Exp 6's closed unconstrained plan. They would bind at the best-known one found later (Exp 7, 48 route-periods OFF; errata E8).

   After the N3 bullet, add one bullet:
   > * Exp 7's re-closure at the same settings moved these prices by −0.10 to +0.06 points (errata E8).
6. Do **not** change `HANDOFF.md` §1 "0 to +0.91%". It is Exp 6's certified figure; the caveat lives in §2.

### P3 — post hoc F1 scope lost downstream — **ACCEPT**

**Verified.** `README.md` 282–284, report §11 (lines 663–665), `FUTURE_EXPERIMENTS.md` 12–14, `HANDOFF.md` 31–33 and `EXPERIMENT7_RESULTS.md` 61 all drop "A5/A6" and/or "one closure per cell". Only A5 and A6 were re-optimized (registry `stage2_selection.selected_levels`).

**Edit.** Use the addendum's permitted wording at each location, in sentence form appropriate to the context:
> Re-optimized under Experiment 1's service rules (no route-period switched off, 60-minute maximum headway; study safeguards, not COTA policy), F1 is −2.1% to −7.0% at every λ ≥ 2 level re-optimized in Exp 7 (A5 and A6 only), with one closure per cell. Post hoc (`docs/EXPERIMENT7_F1_ADDENDUM.md`). At λ = 1 it is +0.12%.

In the report §11 bullet keep the string `+0.12%` present somewhere in the report; the verifier needs it, and it already appears in the abstract.

### P4 — stability words outside the bands — **ACCEPT WITH MODIFICATION**

**Verified.**

* F1 bands: A6 Highly sensitive, A7 Moderately sensitive, A3/A5/A8 Stable, A1/A2 Highly stable (`EXP7_CLOSEOUT_TABLE.json → rows[F1]`).
* Rule 5 limits stability words to the band vocabulary.
* "Robust" is acceptable only as the label SIGN_ROBUST on fixed plans. It must not be used for the post hoc result.

**Modification.** Reviewer 1's HANDOFF §7 replacement ("identified **only** when service may not be switched off") overstates in the other direction. R1_H60's own basin stability rests on one Exp 7 closure plus the Exp 6 closure (N4).

**Edits:**

1. `HANDOFF.md` §1 first bullet, replace the last two sentences with:
   > For the certified plans it keeps its sign at every Stage 1 level (SIGN_ROBUST; −1.9% to −7.0%; magnitude Highly sensitive to walking friction, A6). Re-optimized under Exp 1's service rules it holds at every λ ≥ 2 level re-optimized (A5, A6; one closure per cell; post hoc).
2. Report §11 bullet 2 and `FUTURE_EXPERIMENTS.md` line 12. "survives every assumption perturbation tested for the certified plans" → "keeps its sign at every implemented Stage 1 level for the certified plans (SIGN_ROBUST; magnitude Highly sensitive to walking friction)". Use the P3 sentence for the re-optimized half.
3. Report §6.2 reading 1. "The frequency result is robust **as a policy that keeps every route-period in service**" → "The frequency result holds **as a policy that keeps every route-period in service**". Keep "(post hoc, at the levels re-optimized)".
4. `HANDOFF.md` §7. Old: "Exp 7 shows that the frequency result depends on keeping them." New:
   > Exp 7 shows that the re-optimized frequency result holds under those rules (post hoc, A5 and A6 levels), while without them the λ = 2 objective does not identify unserved demand.
5. `EXPERIMENT7_RESULTS.md` line 59. "F1 is robust for the fixed plans Exp 1 produced." → "F1 is SIGN_ROBUST for the fixed plans Exp 1 produced (magnitude Highly sensitive, A6)."
6. Errata **E13**: below.

### P5 — R2 is the OFF-share cap — **ACCEPT**

**Verified.** `EXPERIMENT6_CONSTRAINT_CATALOG.md:70` defines R2 as the OFF-share cap (`max_off_share`); R1 is the max-headway floor. The caps on N0 are 43 and 17 of 173. REF OFF counts are 38 (A6), 60 (A5_TP200) and 139 (A5_LAM1), so R2_S10 binds at all four levels and R2_S25 only at TP200 and LAM1. That matches closeout §5.1 exactly.

**Edits:**

1. Errata **E9** (below).
2. `EXPERIMENT7_RESULTS.md` line 104: "R2 frequency floors" → "R2 OFF-share caps (25% and 10%)". Append: "They bind because the re-optimized N0 REF switches 38–139 route-periods off, against caps of 43 and 17."
3. Report §6.1 F6 row: "R2 floors become binding" → "the R2 OFF-share caps (25%, 10%) become binding".

### P6 — Stage 1 λ = 1 flips are not collapse — **ACCEPT WITH MODIFICATION**

**Verified.**

* Stage 1 F1 has no sign events. Stage 1 F4 is −1.31% at A5_LAM1.
* Six of eight F5 arms flip at LAM1, and F5 is never re-optimized.
* Stage 1 F6 LAM1 flips: N0 R4_C05 and R4_C01, N3 R6_ADA. AF1 R4_C05 and R4_C01 also flip at LAM1.
* Stage 2 LAM1 events: F1 +181.72%, F4 −0.98%, AF1 TO_TIE, and R2 cells going from zero to positive.

**Modification.** Wording is tightened and F1/AF1 are listed exactly.

**Edits:**

1. Errata **E10** (below).
2. `EXPERIMENT7_RESULTS.md` line 36, "F1, F4, F5 and F6 all change sign at A5_LAM1." Replace with:
   > At A5_LAM1, the re-optimized F1, F4 and AF1 (tie) change sign and R2 prices become positive (Stage 2): that is the collapse. At fixed plans, F4, six F5 arms and a few F6/AF1 cells also change sign (Stage 1), because halving λ re-weights unserved demand; nothing collapses there. Fixed-plan F1 does not change sign.

### P7 — fixed-point gap range — **ACCEPT**

**Verified.** Objective gaps by level: 0.161, 0, 0.007, 0.038, 0.401, 0.284 and 0.071%. Five exceed 0.03%. F1 differs by 35.9 pp at BASE.

**Edit.** Report §7 item 7, last sentence. New:
> Independent closures of the same cell in Exp 7 reached fixed points up to 0.40% apart in objective (more than 0.03% apart at five of seven levels: 0.04–0.40%), with F1 differing by up to 36 percentage points (BASE: −5.4% vs +30.5%) (§6.2).

### P8 — README "19–26%" — **ACCEPT**

**Verified.** Amendment G1-a. `exp1_final.json → plan_disagreement`: mean 19.075, worst 19.653.

**Edit.** `README.md` line 332: "19–26% seed disagreement" → "about 19% of route-periods under Model B (worst pair 19.7%, mean 19.1%)".

### P9 — preregistered vs post hoc map — **ACCEPT WITH MODIFICATION**

**Correction to Reviewer 1.** The claim that "operationalizations dated 0929 (A1, A3, A6, A7, A8, A4) were amendments" is wrong per `EXP7_LEVELS.json`:

* 42 levels are `as_issued_0923`. A1's gravity form and A6_MAXWALK75's bundling of both caps are 0929 *operationalizations of as-issued rows*.
* 2 are `amendment_0929` (A8). A4 is also amendment_0929 but was not run.
* 2 are `additional_post_exp6`.
* 1 is `class_b_0923`.

Drop the unverified "Exp 1 gates amended during Exp 1" bullet from the table.

**Edits:**

1. Report: add §6.0 "What is preregistered and what is post hoc":

   | statement | status | where frozen |
   |---|---|---|
   | Stage 1 sign labels and magnitude bands; Stage 2 selection metric; F1/F4/F6/AF1 adaptive definitions | preregistered | contract `1263bedaebe6a45d`; amendment §§13–14 |
   | Level settings | 42 as issued 23 Sep (A1 and A6_MAXWALK75 operationalized 29 Sep); A8 amendment 29 Sep; 2 additional; 1 Class B | `EXP7_LEVELS.json → levels[].provenance` |
   | F3/AF1 labels excluding A7_RM04/RM05 | added at closeout (post hoc flag) | `scripts/exp7_closeout.py` |
   | F2 not-applicable exclusion | corrected at closeout | `scripts/exp7_closeout.py` |
   | F1 under R1_H60/R1_H30/R3_SPAN; second REF fixed point | post hoc | `docs/EXPERIMENT7_F1_ADDENDUM.md`, `EXP7_F1_DECISION_SPACE.json` (preregistered: false) |
   | λ = 1 and shedding mechanism tables (closeout §5.2); errata E7–E8 analyses | post hoc diagnostic | closeout §5.2, errata |

2. Report §1. "Seven experiments ran in sequence, each preregistered before its production run" → "Seven experiments ran in sequence. Each froze a contract before its production run (`ACCEPTANCE.md`, the per-experiment contracts); analyses added afterwards are marked post hoc (§6.0)."

### P10 — authority order — **ACCEPT WITH MODIFICATION**

**Modification.** Put the full block once, in `HANDOFF.md` §1 under "The written record". Add the closeout, errata, addendum and RESULTS to that table. In the RESULTS header and the report's draft-status list, add a one-line pointer instead of repeating the block: "Authority order for Exp 7: `HANDOFF.md` §1; where the closeout and `docs/EXPERIMENT7_CLOSEOUT_ERRATA.md` conflict, the errata wins."

Block text, as Reviewer 1 wrote it, with item 3 reworded: "`docs/EXPERIMENT7_F1_ADDENDUM.md`: post hoc; never relabels a preregistered result."

### P11 — preregistered confirmation of post hoc F1 — **ACCEPT WITH MODIFICATION**

**Modification.**

* Number the experiment **E21** and place it in Tier 1 with the note "runnable now; needs no external data".
* Drop "Stage 2 took about 4 days for two dimensions" from the justification. `REPRODUCE.md` states it, but it is not artifact-backed.
* Add the existing partial evidence (N4) so the proposal is not overstated: at BASE, Exp 6's closed R1_H60 plan gives F1 −6.55% (Stage 1 row `F6_N0_R1_H60`) and Exp 7's gives −6.57%, 0.009% apart in objective. These are two closures sharing one initial solve, so they are not independent.

**Text for FUTURE E21:**
> * **Question:** is the post hoc F1 result (N0 under R1_H60 against the current plan at the same level) sign-stable across independent closures and across the Stage 1 movers that were not re-optimized?
> * **Design:** preregister that definition; at least 3 independent starts/closures per level at the six A5/A6 levels plus A7 (Moderately sensitive for F1), A1, A3 and A8; a period-tilt dimension; at least 3 independent N0 REF closures at BASE to put a distribution on the non-identification (−5.4% vs +30.5%).
> * **Acceptance:** SIGN_ROBUST across all closures at every λ ≥ 2 level.
> * **Existing partial evidence:** two closures of R1_H60 at BASE sharing one initial solve (Exp 6, Exp 7) give −6.55% and −6.57%.

Add "E21" to `HANDOFF.md` §6 after item 1.

---

## MEDIUM

### P12 — "every positive F1 value" — **ACCEPT**

**Verified counterexamples.** R3_SPAN +41.15% (34 OFF, A5_TP200), +0.02% (6 OFF, A6_WALKSPD85), +167.37% (86 OFF, A5_LAM1). R1_H60 +0.12% (0 OFF, A5_LAM1).

**Edits:**

1. Report §6.2: "Every positive F1 value coincides…" → "Every positive **REF** F1 value (either track) coincides with 38–139 route-periods switched off."
2. Addendum Reading 2: "Every positive value coincides with 38–139 route-periods switched OFF. The span-preserving cells switch off none." → "Every positive REF value coincides with 38–139 route-periods switched OFF. The R1 cells (no baseline-served route-period OFF) switch off none." Also `EXPERIMENT7_RESULTS.md` line 63 is already scoped to "preregistered reversal", so no change there.

### P13 — F2 preregistered label — **ACCEPT**

**Verified.** `rows[F2 (unserved)]`: SIGN_SENSITIVE, 18 Class A flips (10 among A2 draws), range −0.226 to +0.166, all dimensions Highly sensitive, worst A3_RTNOISE. The amendment §13.2 includes F2 in classification, and the null test against the 0.287% floor holds at every applicable level.

**Edits:**

1. Errata **E11** (below).
2. `EXPERIMENT7_RESULTS.md` F2 line: append "Its preregistered sign label is SIGN_SENSITIVE (18 Class A flips, 10 of them bootstrap draws; range −0.226% to +0.166%), as expected for a 0.0065% effect."
3. `README.md` Exp 7 results: add a bullet: "**Splice null (F2):** the null test holds at every applicable level; the sign label is SIGN_SENSITIVE, as expected for a 0.0065% effect."

### P14 — report §6.1 evaluator and bands — **ACCEPT WITH MODIFICATION**

**Modification.** Do not add three columns; the table is already wide. Instead:

* insert "Stage 1 BASE −6.02% (Exp 6 model instance, no crowding);" at the start of the F1 Stage 1 cell;
* append the worst band(s) to each Stage 1 cell: F1 "Highly sensitive (A6)"; F3 "Highly sensitive (A1, A7)"; F4 "Highly sensitive (A5)"; F2 "Highly sensitive (all)";
* append to Stage 2 cells "worst band Highly sensitive";
* add a footnote below the table:
  > Certified values come from each experiment's own model instance; Stage 1 BASE is the classification reference (amendment §14.1). F1, F2, F3 and AF1 are on N0/N3; F4 is N4 − N3.

### P15 — AF1 asymmetry and track dependence — **ACCEPT WITH MODIFICATION**

**Correction to Reviewer 1.** There are 13 labelled AF1 cells (R1_H20 is null). Excluding A7_RM04/RM05, **10 of 13** are SIGN_ROBUST, not 9 of 12. Only R4_C05, R4_C01 and R6_ADA remain SIGN_SENSITIVE. The track values are verified: F4 track N3−N0 runs from −0.161 to −0.184% at λ ≥ 2; F6 track runs from −0.157 to −0.310%; the maximum gap is 0.146 pp at A5_TP200.

**Edits.** Report §6.1 AF1 row:

* Stage 1 cell: "SIGN_SENSITIVE via A7_RM05 in all 13 cells; excluding the rank-mismatched A7 levels, 10 of 13 SIGN_ROBUST (R4_C05, R4_C01, R6_ADA remain SIGN_SENSITIVE)".
* Stage 2 cell: "N3 better by 0.16–0.31% (F6 track) and 0.16–0.18% (independent F4 track, REF only) at every λ ≥ 2 level; the tracks differ by up to 0.15 points, the same order as the effect (within model uncertainty); tie at λ = 1".

### P16 — level counts — **ACCEPT WITH MODIFICATION**

**Modification.** The closeout's "BASE + 47 declared levels" is accurate, since §1 separately tabulates declared-but-not-run items. No errata row is needed. Edit the report §6 opening and README only.

**Text:**
> 47 levels plus BASE were run (44 Class A in seven dimensions, 1 Class B, 2 additional) on four network variants (N0, N3, N4, N0S): 4 × 48 = 192 evaluation cells. Declared but not run: A4 reliability (2 levels, UNIMPLEMENTED), the B2 jobs-accessibility objective (UNTESTED), path-width/scenario count (DROPPED as inert) and period tilt (NOT INCLUDED).

### P17 — dimension table and Class B values — **ACCEPT WITH MODIFICATION**

**Corrections to Reviewer 1:**

* F1 at X_ROUNDS4 is **−6.03%**, not "—".
* **Reject** "F4 under B1 independently matches Exp 4A's omission-corrected +7.87%". The Exp 4A correction is a RAPTOR path-omission re-costing (`EXPERIMENT4_ORIGINAL_QUESTION_ADDENDUM.md:196`), while B1 is cross-route common lines. The closeness is a coincidence of two different corrections and must not be presented as corroboration.
* Provenance: A8 is `amendment_0929`; A1 and A6_MAXWALK75 are as-issued rows with 0929 operationalizations; everything else is as issued.

**Edits:**

1. Report §6 table: replace the "what it perturbs" column with:
   * A1: +25/50/100% non-commute trips, gravity form, on commute OD pairs only (as issued; operationalized 29 Sep)
   * A2: 20 LODES bootstrap draws
   * A3: runtime ×1.1, ×1.2, and per-link lognormal noise (median |error| 20.5%), envelope fixed
   * A4: UNIMPLEMENTED
   * A5: λ = 1 and 4; transfer penalty 5 and 20 min
   * A6: walk speed 68 m/min; access 450 m with transfer walk 300 m (bundled; operationalized 29 Sep)
   * A7: remove each of the 10 busiest routes, resources kept in the envelope
   * A8: retention zero point 150 min; floor 0 (amendment 29 Sep; `full_min` not varied)
2. Add the table "Class B and additional (reported, never label findings)": F1 −5.99% (B1), −5.49% (X_TOPK40K), −6.03% (X_ROUNDS4); F4 N4−N3 +7.86%, +8.82%, +9.67%. Source: `EXP7_CLOSEOUT_TABLE.json → rows[].class_b_and_additional`.

### P18 — errors in existing errata rows — **ACCEPT WITH MODIFICATION** (E1, E6) / **REJECT** (E5 rewrite)

**E1.** Verified: `git diff --stat 4a2ba9f6 HEAD -- scripts/ src/` lists six files. Three are later additions: `canonical_results_v5.py`, `exp7_f1_decision_space.py` and `verify_report_claims.py`. Superseded by new row **E14**.

**E6.** Verified: §8's first claim says "every implemented Stage 1 assumption level". "Every λ ≥ 2 level" is in §6's F4 and AF1 rows and §8's third claim. There it is correct for Stage 1 (every Class A level except A5_LAM1) and already scoped for Stage 2. Superseded by new row **E15**. Reviewer 1's wording would wrongly restrict the Stage 1 F4 claim.

**E5. REJECT the rewrite.** E5 is a clarification rather than an error. Its N0 figures are valid for N3, because both hold plan `76430e1f43635d31` at A5_LAM1 (`EXP7_ANALYSIS.json → f4[A5_LAM1]`). Churn is not justified.

Append rows only (see policy at top). Also update report §9 R12 "E1–E6" → "E1–E15".

### P19 — missing limitations — **ACCEPT WITH MODIFICATION**

**Edit.** Add these rows to report §8. The P1 row is given above. Drop Reviewer 1's "λ is a value judgement" as a separate row and instead extend the existing "Uncalibrated parameters" row with "λ is a policy choice, not calibratable (guidelines, calibration register)".

* Period demand shares | six shares assumed (LODES has no time dimension); period tilt NOT INCLUDED in Exp 7 | unknown; bears directly on where frequency moves by period
* Single closure per cell | the only cell closed twice (N0 REF) differs by up to 0.40% in objective and 36 points in F1 across tracks | re-optimized F1, served-trip and GC figures in OFF-permitting cells are basin-dependent; R1 cells not independently re-closed (FUTURE E21)
* Stage 2 scope | A5 and A6 only | no re-optimized claim for demand, runtime, route-removal or retention perturbations
* Operationalization bounds | A1 commute pairs only; A3 envelope fixed; A6 caps bundled; A8 `full_min` fixed | Exp 7 claims are bounded to these forms

### P20 — "Exp 1's rules" as study safeguards — **ACCEPT**

**Verified.** Catalog S5: "The study's own pre-existing ladder policy, a study safeguard since Exp 1". R1 is classed as a study safeguard.

**Edits:**

* At first use in the addendum, report §6.2, README Exp 7 and HANDOFF §7, write "Experiment 1's service rules (study safeguards in `config/constraints.yaml`; no documented COTA numeric standard)".
* Addendum Reading 3: "which rules COTA would plan under" → "which service rules a planner chooses to impose".
* HANDOFF §7 "Exp 6 prices the rules" → "Exp 6 prices the study's safeguard rules".

### P21 — F6 counts and rule 3 — **ACCEPT WITH MODIFICATION**

**Verified.**

* N0: R1_H60, R3_SPAN, R4_C00, B1 and B2 have the identical range at every level. R2_S25/S10 are zero. That gives 7 distinct non-zero plans, 5 of them SIGN_ROBUST.
* N3: 6 distinct non-zero plans, 3 SIGN_ROBUST. The six λ = 4 flips are to −0.0069% and −0.0099%.

**Modification.** Rule 3 is "an effect smaller than its Exp 7 magnitude range is reported as within model uncertainty", not "range spans zero". Cite it that way.

**Edit.** Report §6.1 F6 Stage 1 cell:
> N0: 11 of 13 cells SIGN_ROBUST (5 of 7 distinct non-zero plans; R2_S25/S10 are zero at every level). N3: 5 of 12 (3 of 6 distinct); the six λ = 4 flips are to −0.01% or less. N0 R4_C05 and R4_C01 and N3 R6_ADA move by more than their own size and change sign: within model uncertainty (rule 3).

### P22 — "non-negative at every level" — **ACCEPT WITH MODIFICATION**

**Modification.** Use the closeout's own justification ("a negative price would have blocked certification", §5.1) rather than "guaranteed by certification". The Stage 1 list is made exact.

**Edits:**

1. Errata **E12** (below).
2. `README.md` Exp 7 F6 line:
   > **Safeguard prices (F6):** re-optimized prices are non-negative at every level (a negative one would have blocked certification); rankings unchanged at transfer penalty ×0.5 and moved at λ = 1, transfer ×2 and the walking levels, where the R2 OFF-share caps become binding. At fixed plans, prices change sign in 2 of 13 N0 and 7 of 12 N3 cells.
3. Report §6.1 F6 Stage 2 cell: "non-negative everywhere" → "non-negative everywhere (enforced: a negative price blocks certification)".
4. `HANDOFF.md` has no such line, so no change there.

### P23 — provenance gaps — **ACCEPT WITH MODIFICATION**

**Verified.** `EXP7_F1_DECISION_SPACE.json` sha256 is `0d5e3da76ebdc6ad67493e4ce93061c1536e313ac558e605e9d631a764015280`. It is absent from the v5 `artifact_sha256`, and was last changed in `5dc3f408` (created in `0426ee1f`). The Stage 2 analysis commit is `b0f6f416` and the contract freeze is `4a2ba9f6`.

**Edits:**

* **Appendix A:** add a "contract / commit" column for the Exp 7 rows only. Exp 7 Stage 1/2: contract `1263bedaebe6a45d`, analysis `b0f6f416`. Post hoc F1: `5dc3f408` (artifact sha256 above, "not in registry v5"). Do not retrofit Exp 1–6 rows here; that is release work.
* **Addendum header:** add the sha256 and "not registered in `CANONICAL_RESULTS_v5.json`".
* **Reject** "Register the artifact in a v6 registry" as a current action, since it would edit or create a registry. List it under FUTURE "Not experiments, but required" as "register `EXP7_F1_DECISION_SPACE.json` in the next registry version at the freeze".
* **Verifier extension: ACCEPT** as reporting-only. Add claims for `+30.5%` (`rows[BASE].ref_f4_track.f1_pct`, 1 dp), `0.161%`, `2,940,186` and `2,935,446` (0 dp), `557` (A5_LAM1 REF hours), `1,583` and `29,366` (`EXP7_ANALYSIS.json → f1_adaptive[A5_LAM1]` / decision-space REF served), and the F2 range ends. Point each claim at the documents that contain the exact string after the edits above.

### P24 — glossary — **ACCEPT WITH MODIFICATION**

**Correction to Reviewer 1.** The `docs/GLOSSARY.md` λ entry was already wrong before Exp 7: Exp 1 certified λ = 4, 8 and 16 frontier points.

**Edits:**

* λ entry: "…The certified frontier begins at λ = 2; headline comparisons use λ = 2. Exp 1 also certified λ = 4, 8, 16, and Exp 7 ran converged Stage 2 cells at λ = 1 and 4 as sensitivity levels (λ = 1 lies below the certified frontier)."
* Add to report Appendix B, briefly: SIGN_ROBUST / SIGN_SENSITIVE (with SIGN_FLIP / TO_TIE / FROM_TIE), the four magnitude bands, Stage 1 / Stage 2, F1–F6 / AF1 (one line each), REF, F4 track / F6 track, R1–R6 and B1–B2 (one line each, "study safeguards"), N0S, fixed point, "not identified".

### P25 — two Exp 1 figures — **ACCEPT WITH MODIFICATION**

**Modification.** The abstract's "about 680" is consistent with both figures: 6.652% × 10,262 = 683 and 10,262 − 9,583 = 679. Leave the abstract unchanged.

**Edit.** Report §5.1, after the trips bullet, add: "(This is the single λ = 2 frontier run, −6.60%; the three-seed headline mean is −6.65%.)"

### P26 — abstract numbers lack network/source — **ACCEPT WITH MODIFICATION**

**Edits.** Report abstract:

* Greenfield bullet: "…is **worse** than the existing geometry with re-optimized frequencies, by 8–10% of the objective." → "…is **worse** than the existing geometry and the Exp 3 redesign with re-optimized frequencies: +9.66% of the redesign's (N3's) objective (Exp 4A, λ = 2), and worse at every λ ≥ 2 level re-optimized in Exp 7 (+6.6% to +30.8% against N0 or N3)."
* Safeguards bullet: "(study safeguards, not COTA policy) … cost 0 to 0.91% of the objective each on N0 and 0 to 0.63% on N3 (Exp 6). A 20-minute headway floor is infeasible under the modeled envelope on N3. Further closure in Exp 7 moved individual prices by up to 0.1 points (§5.6)." Do not cite "P2".

Keep `+9.66%` in the report; the verifier needs it.

### P27 — addendum "matches Exp 1's frontier" — **ACCEPT WITH MODIFICATION**

**Verified.** R1_H60 at λ = 1 is +0.12% against Exp 1's frontier at −1.42% (opposite sign). Exp 1 used crowding and the 243,257-path set with Gen1 (closeout §4.1).

**Edits:**

* Addendum Reading 1, last sub-bullet:
  > At λ ≥ 2 this agrees in sign and range with the Stage 1 fixed-plan result (−1.9% to −7.0%). At λ = 1 it differs in sign from Exp 1's uncertified frontier point (−1.42%), which used a different model instance (crowding on, 243,257-path set) and solver (Gen1).
* "Why this exists": add "Same service rules as Exp 1; the model instance and certifier are Exp 6's."
* Reading 2 sub-bullet "Exp 6 found that R1 cells did not change basin under closure": append "; in Exp 7, R1_H60 at BASE did change basin (a cross-level import, 0.009% in objective), with F1 moving from −6.55% (Exp 6 plan) to −6.57% (post hoc; N4)".

### P28 — FUTURE E8 "calibrated λ·w_unserved" — **ACCEPT WITH MODIFICATION**

**Edit.** Second bullet of "What would change the answer":
> a calibrated unserved-trip penalty w_unserved (or retention curve) such that, at the policy-chosen λ, λ · w_unserved falls below the generalized cost of a material share of served trips. That would put the real system in the regime where the objective sheds riders (report §6.2; errata E7).

Use "material share" rather than "typical": the mechanism is the tail (P1).

### P29 — FUTURE E14 reuses A4 levels — **ACCEPT WITH MODIFICATION**

**Edit.** E14 design bullet 2:
> Preregister new A4 levels in the new model's terms (for example, headway coefficient of variation by route-period at the observed median and 90th percentile). Do not reuse the 0929 schedule-coefficient levels: `EXP7_LEVELS.json → declared_not_run[A4_*].why` records that they cannot represent headway variance.

Add "**Data:** AVL or months of GTFS-Realtime, shared with E13."

### P30 — FUTURE ordering and preconditions — **ACCEPT WITH MODIFICATION**

**Corrections to Reviewer 1.**

* E13's data is GTFS-Realtime, which is public and has a collector in `cota_opt.realtime`, so it is **not** blocked on COTA.
* E9 needs a non-LODES OD source (MORPC model, LBS or APC), not necessarily COTA's.
* The "10–17 min per transfer" figure is unverified; drop it.
* Calling E14 a hard precondition of E12 is too strong; make it a note.

**Edits:**

* E20: add "**Period tilt:** the period-share assumption (LODES has no time dimension; NOT INCLUDED in Exp 7)".
* Mark E8 and E11 "**blocked on non-public COTA data**" (APC/farebox/fare-card/survey; deadhead/terminals). Mark E9 "needs a new OD source".
* E12: add "Pulse value depends on headway regularity; interpret jointly with E14."
* Header compute note: "Certification cells are independent…" → "Stage 1 cells and initial solves are independent and parallelise per cell; basin closure as implemented runs one process per (track, network) (`exp7_run.py closure`) and is not divided by core count."
* Report §10 "Certification cells are independent, so the work is trivially parallel": append the same qualification.

### P31 — HANDOFF git state — **ACCEPT WITH MODIFICATION**

**Verified.** `5eebe36a` is 2026-09-29, the Exp 6 results HANDOFF. `github/master` = `196295c9`, 612 commits behind HEAD.

**Edits:**

* Header: "The previous version (2026-09-29, after Experiment 6) is in git history at `5eebe36a`."
* §3: "Ian's machine holds the same commits…" → "Ian's machine holds commits on branch `exp7-work` (as reported; not verifiable from the container) …". Add: "Commits after the last bundle delivered, including `5dc3f408` and later write-up commits, need a further bundle."

Do not invent a delivered-bundle hash. Leave a placeholder for Ian to fill if unknown.

### P32 — README front-door wording — **ACCEPT WITH MODIFICATION**

All six items verified (lines 9, 115, 121, 23, 54, 321; Exp 7 block lacks the rule-10 line).

**Modifications:**

* Line 23: append "(± = solver seed spread, SD of 3 seeds)" once after the quote.
* Line 121: "peak-vehicle cap" → "peak-concurrency-proxy cap".
* Line 321: "`outputs/CANONICAL_RESULTS_v5.json` (v1–v4 are kept unchanged)".
* Line 54: "can be satisfied almost for free" → "can likely be satisfied at little cost (untested)".

### P33 — README F4 conflates stages — **ACCEPT**

**Verified.** Stage 1 Class A F4_43 excluding A5_LAM1 ranges from +7.70% (A7_RM02) to +19.35% (A5_LAM4).

**Edit.** As written by Reviewer 1.

---

## LOW

### P34 — REPRODUCE Exp 7 — **ACCEPT WITH MODIFICATION**

**Hazard.** The proposed spot check `python scripts/exp7_stage1.py cell --variant N0 --level BASE` **overwrites** the git-tracked canonical `outputs/exp7/stage1/evals/N0/BASE.json`, with no exists-guard in `evaluate_cell`.

**Edits:**

* Spot check text:
  > In a separate clone or `git worktree` (never the canonical checkout): `python scripts/exp7_stage1.py cell --variant N0 --level BASE`, then compare `rows` with the committed `outputs/exp7/stage1/evals/N0/BASE.json` (`F1_BASELINE.unserved_demand` 10,423.684…). The command overwrites that file.
* "the three post-freeze script changes" → "the post-freeze script changes (closeout §1.1 as corrected by errata E14)".
* Exp 6 heading → "(closed, `EXP6_POLICY_FRONTIER_CERTIFIED`)". First confirm that this label string appears in `EXPERIMENT6_CLOSEOUT.md`; otherwise use "(closed, certified)".
* Fix the garbled sentence: "Production evaluated 192 Stage 1 cells, then ran about 4 days of Stage 2 wall time on 2 cores (2026-09-30 to 2026-10-04)." Drop the per-transfer minutes unless sourced from `outputs/exp7/run/` logs.
* "Verified … on local `master`" → add "at `5dc3f408`".
* Freeze steps: list `exp7_levels.py`, `exp7_busiest_routes.py` and `exp7_freeze.py` as "done; refuse to overwrite". Check each one's argparse before quoting flags.

### P35 — RESULTS served-trip figures — **ACCEPT**

**Verified.** F4 track at BASE serves N4 12,700, N3 17,389 and N0 17,349 (48 OFF).

**Edit.** `EXPERIMENT7_RESULTS.md` line 84: "…because N4's deficit is coverage: at BASE N4 serves 12,700 trips against N0's 17,349." → "…because N4's deficit is coverage (illustrative, F4-track basins: N4 12,700, N3 17,389, N0 17,349 served at BASE; basin-dependent, not a finding)."

### P36 — report outline conformance — **ACCEPT WITH MODIFICATION** (minimal)

**Edits:**

* Draft-status list: add "Outline: §§1–11 plus Appendices A–B; the guideline appendices (decision log → `DISCOVERIES.md`, preregistration amendments, superseded-artifact index, calibration register) are pending release work."
* Add a short **Appendix C**, the Exp 7 amendment sequence: as issued 23 Sep → Sept 23 finalization → amendment §§13–14 (two-stage; full ~2,300 h closure rejected) → 29 Sep operationalizations (A1, A6_MAXWALK75, A8, A4). Source: closeout §7.
* `outputs/SUPERSEDED.md` (Markdown, unregistered): add an Exp 7 entry for `outputs/exp7/SUPERSEDED.EXP7_LEVELS.PROPOSED.json` and `docs/EXPERIMENT7_AMENDMENT_DRAFT.md`.
* **Skip** placeholder appendices E/F; they are churn.

### P37 — minor clarity — **ACCEPT WITH MODIFICATION**

* **Abstract.** "That error produced and then withdrew a headline twice." → "That error produced, and then forced the withdrawal of, the 0.5% through-routing headline (R4)." The 0.9% retraction, R3, was an evaluator mislabel.
* **"within 0.06 points".** Reviewer 1's replacement is itself wrong; see N3.
* **§6 "every certified plan (60-entry registry)".** → "60 frozen solutions from Experiments 1–6, including the N0 current plan (59 evaluable)".
* **§10 AVL.** Append "(after a reviewed `src/cota_opt` change; FUTURE E14)". **Reject** the `DATA_INTERFACES.md` note: the report cites the guidelines section, not that file.

---

## Additional findings by Reviewer 2

* **N1 — RESULTS still carries the E3-retracted reading (MEDIUM).** `docs/EXPERIMENT7_RESULTS.md` lines 56–58 say: "The sign holds where the unserved penalty dominates (LAM4, TP050). It reverses where trips become costlier than the penalty." Errata E3 says "do not use as written". Replace lines 56–58 with:
  > **Reading:** the preregistered F1 adaptive label is SIGN_SENSITIVE. Its values are basin-dependent: a second certified closure of the BASE cell gives +30.5% (errata E3), so the per-level signs are not a finding.
* **N2 — zero R2 prices are basin-specific (MEDIUM).** Folded into P2 and errata E8.
* **N3 — "within 0.064 points of each other" (MEDIUM).** 0.064 is the seed SD (`exp1_final.json → headline.unserved_demand.sd_pct` = 0.0637). The three seeds are −6.60, −6.72 and −6.63% (closeout §4.1), a spread of 0.12 points. With n = 3, any SD of 0.064 implies a range of at least 0.11. The wording originates in the immutable `exp1_final.json → the_claim` and D17. Edits:
  * Report line 110: "score within 0.06 points" → "score with a solver seed spread (SD) of 0.064 points".
  * Report line 316–317: "while scoring within 0.064 points of each other" → "while their unserved-demand changes have an SD of 0.064 points (range 0.12: −6.60, −6.72, −6.63%)".
  * `README.md` line 50: the same change.
  * Optionally note in report §9: "wording in `exp1_final.json` (immutable) says 'within'; it is an SD".
* **N4 — R1_H60 basin evidence (LOW, post hoc).** At BASE, two closures of R1_H60 (Exp 6 and Exp 7, sharing an initial solve) give F1 −6.55% and −6.57%, 0.009% apart in objective. Used in P11 and P27. Sources: Stage 1 `evals/N0/BASE.json → rows.F6_N0_R1_H60` (objective 2,956,071.29, unserved 9,740.54) against `EXP7_F1_DECISION_SPACE.json → rows[BASE].cells.R1_H60`.
* **N5 — report §9 R12.** Update "E1–E6" → "E1–E15", and add to the "why" column "mechanism wording, R2 label, λ = 1 attribution, F2 label, non-negativity scope, BASE price movement".

---

## Errata rows to append to `docs/EXPERIMENT7_CLOSEOUT_ERRATA.md`

Append below E6. Also extend the header note with: "Rows E7–E15 added 2026-10-04 from a second review. E14 supersedes E1; E15 supersedes E6's location. Rows marked post hoc are analyses beyond the preregistered contract."

| # | closeout location | as written | correction |
|---|---|---|---|
| E7 | §0 one-paragraph answer; §5.2 first bullet; registry `experiments.exp7.regime_boundary` | "With no operating-cost term, the λ-weighted objective prefers dropping a rider to serving them" | **Wrong cause.** The objective counts a served trip at its full generalized cost c and a lost trip at λ · 60. Making a trip unservable lowers the objective whenever c > λ · 60, by c − λ · 60 per retained rider, and the freed vehicle-hours are reused elsewhere. At λ = 1 the penalty (60) is below the mean served-trip GC at BASE (83–86), so most service goes. At λ = 2 (penalty 120) only the high-GC tail is exposed; A5_TP200 and the A6 levels enlarge it. An operating-cost term would not prevent this: at A5_TP200 and both A6 levels the shedding REF plan and the no-OFF R1_H60 plan use the same 2,515–2,517 revenue vehicle-hours, and at λ = 1 a cost on hours would favour the 557-hour plan further. The retention curve (full to 60 min, zero point 210, floor 0.10) still keeps 64% of riders at 120 min, so the λ = 2 objective prefers losing trips the model's own demand curve treats as mostly still made. "No operating-cost term" is a true description of the objective, not the explanation. Post hoc analysis: `EXP7_F1_DECISION_SPACE.json` → `rows[].cells.{REF,R1_H60}.revenue_veh_hours`; `config/assumptions.yaml`; `src/cota_opt/pathset.py` (`PathSetEvaluator.evaluate`). |
| E8 | §6 F6 row; §8 fourth claim (omission) | — | **Omission.** Stage 2 BASE is Experiment 6's model (level rationale "Experiment 6 exactly", digest `79b97699…`, same `src/cota_opt` digest). Its closure, with cross-level anchors, moved BASE prices from Exp 6's certified values by −0.10 to +0.06 percentage points (N0 R4_C05 0.244% → 0.146%; N0 R1_H60 0.482% → 0.531%) and reversed the order of R4_C05 and R2_S05 on both N0 and N3. The F6-track BASE REF (2,940,186.29; 17 OFF) is 0.058% better than Exp 6's closed REF and 0.161% worse than the F4-track REF (2,935,446.46; 48 OFF). Against that best-known REF every price would be about 0.16 points higher, and R2_S25 and R2_S10 (caps of 43 and 17 of 173 route-periods) would bind. Exp 6 prices are basin-dependent at the 0.1-point scale. Source: `EXP7_ANALYSIS.json → f6_prices[level=BASE]` against `EXP6_ANALYSIS.json → frontier[].policy_cost_closed_pct`. The cross-track comparison is post hoc. |
| E9 | §5.1 | "Every sign event is an R2 frequency-floor cell" | R2 is the **OFF-share cap** (`EXPERIMENT6_CONSTRAINT_CATALOG.md` R2, `max_off_share`): the number of baseline-served route-periods switched OFF may not exceed ⌊s · 173⌋ on N0, i.e. 43 at s = 0.25 and 17 at s = 0.10. It is not a headway floor; that is R1. The caps bind because the re-optimized N0 REF switches off 38 (both A6 levels), 60 (A5_TP200) or 139 (A5_LAM1) route-periods. |
| E10 | §5.2 fourth bullet; §8 third claim; registry `experiments.exp7.regime_boundary` | "The F4 flip at λ = 1, in both stages, is this collapse"; registry: "F1/F4/F5/F6 sign changes at lambda=1 are this collapse" | Only the **Stage 2** sign events at A5_LAM1 are the collapse: F1 (+181.72%), F4 (−0.98%), AF1 (TO_TIE), and R2 prices becoming positive. Stage 1 never re-optimizes. Its λ = 1 flips are fixed plans re-weighted when λ halves the cost of unserved demand: F4 −1.31%, six of eight F5 arms, F6 N0 R4_C05 and R4_C01 and N3 R6_ADA, and AF1 R4_C05 and R4_C01. F1 does not change sign in Stage 1 (SIGN_ROBUST, no sign events), and F5 is never re-optimized. |
| E11 | §4 F2 row; §6 F2 row | "(a null; read via the null test)"; "Null holds at every applicable Stage 1 level" | The preregistered sign label (amendment §13.2) is **SIGN_SENSITIVE**: 18 Class A sign flips, 10 of them among the 20 bootstrap draws; Class A range −0.226% to +0.166%; Highly sensitive in every dimension; worst A3_RTNOISE. That is expected of a 0.0065% effect. The null test against the Exp 2B floor (0.287%) holds at every applicable level (not applicable at A7_RM09). Both are reported (reporting rule 6). Source: `EXP7_CLOSEOUT_TABLE.json → rows[F2 (unserved)]`. |
| E12 | §8 fourth claim; §6 F6 row | "Policy prices (study safeguards) are non-negative at every level"; "Prices are non-negative everywhere" | True of the **re-optimized (Stage 2)** prices only, and enforced there: a negative closed price would have blocked certification (§5.1), so it is not a robustness finding. Fixed-plan (Stage 1) prices go negative: N0 R4_C05 at A5_LAM1 (to −1.33%) and A7_RM09, N0 R4_C01 at A5_LAM1, N3 R6_ADA at A5_LAM1 (to −2.25%), and six N3 cells at A5_LAM4 (to −0.01%) (§4). |
| E13 | §0 "fixed plans keep their reduction … under every perturbation tested", "So F1 is robust for the plans that were certified"; §6 F1 row | — | Robustness here refers to **sign** only. Stage 1 F1 is SIGN_ROBUST (−6.998% to −1.897%). Its magnitude bands are Highly sensitive in A6 (68.5% at A6_MAXWALK75), Moderately sensitive in A7, Stable in A3, A5 and A8, and Highly stable in A1 and A2 (`EXP7_CLOSEOUT_TABLE.json → rows[F1].worst_magnitude_band_by_dimension`). "Every perturbation tested" means every implemented Class A level; A4 and period tilt were not run. |
| E14 | supersedes E1 (§1.1) | E1: "Two later reporting-only scripts now also appear" | **Three** later scripts appear in `git diff 4a2ba9f6 HEAD -- scripts/ src/`: `scripts/canonical_results_v5.py`, `scripts/exp7_f1_decision_space.py` and `scripts/verify_report_claims.py`. All are reporting-only, and `src/cota_opt` is unchanged. |
| E15 | supersedes E6's location | E6: "§8 first permitted claim and the addendum" | §8's first claim reads "every implemented Stage 1 assumption level" and is not affected. "Every λ ≥ 2 level" appears in §6's F4 and AF1 rows and §8's third claim. There it is correct for Stage 1 (every Class A level except A5_LAM1) and, for Stage 2, means the six Stage 2 levels other than A5_LAM1. E6's restriction applies to the addendum's F1 claim and to downstream documents. |

---

## Final ordered implementation list

1. **Errata:** append E7–E15 and the header note (above). Do not touch the closeout, registry, outputs JSON or src.
2. **P1:** report §3 and §6.2 (both places) and the new §8 row; README Exp 7; RESULTS "regime boundary"; addendum Reading 3; FUTURE E10; HANDOFF §6.
3. **P2/N2:** report §5.6 column and paragraph; report §6.1 F6; HANDOFF §2; README Exp 6 block.
4. **N1:** RESULTS lines 56–58 (E3 reading).
5. **P3 and P4:** README, report §11 and §6.2, FUTURE lines 12–14, HANDOFF §1 and §7, RESULTS lines 59 and 61.
6. **P5 and P6:** RESULTS lines 36 and 104; report §6.1 F6.
7. **P12, P27, P20:** addendum Readings 1–3 and "Why this exists"; report §6.2 last bullet.
8. **P7, P14, P15, P21, P22:** report §7 item 7 and §6.1 rows; README F6 line.
9. **P13 and P33:** RESULTS F2; README F2 and F4 lines.
10. **P8, P32, N3:** README lines 9, 23, 50, 54, 115, 121, 321, 332 and the Exp 7 disclaimer; report lines 110 and 316.
11. **P9, P16, P17, P19:** report §1, new §6.0, §6 opening, dimension table and Class B table, §8 rows.
12. **P10 and P31:** HANDOFF §1 written-record table and authority block, header, §3; one-line pointers in RESULTS and the report.
13. **P23:** Appendix A columns; addendum header sha256; verifier claims extension; FUTURE release-list item.
14. **P11, P28, P29, P30:** FUTURE E21, E8, E14, E20, E9/E11/E12 notes and the compute note; report §10 note; HANDOFF §6 item.
15. **P24, P25, P26, P35, P36, P37, N5:** glossary and Appendix B; §5.1 parenthetical; abstract; RESULTS line 84; draft-status note, Appendix C and `outputs/SUPERSEDED.md`; abstract "twice"; §6 registry wording; §10; §9 R12.
16. **P34:** REPRODUCE Exp 7 and Exp 6 heading, with the worktree warning.
17. **Verify:** run `python scripts/verify_report_claims.py` (must stay 30/30 plus any new claims). Run `sha256sum EXPERIMENT7_CLOSEOUT.md` and confirm it still equals `27bfc7390c777051ecce6e313366e5214ba8372b404f1570dca5151639734be7`. Run `git diff --stat -- outputs/ src/ scripts/exp7_*` and confirm it is empty apart from `outputs/SUPERSEDED.md` and `scripts/verify_report_claims.py`.
