# Adjudication of Referee Report 1 — TECHNICAL_REPORT.md (draft 2026-10-04)

Handling editor's adjudication. Repository `/home/claude/columbus-transit-opt`, HEAD `189dfa64`.
Everything below was checked read-only against artifacts, code and documents. `python scripts/verify_report_claims.py` → 39/39 at HEAD.

**What can be edited and what cannot.** This list binds every edit instruction below.

* **Editable:** `docs/report/TECHNICAL_REPORT.md`; `README.md`; `docs/EXPERIMENT7_RESULTS.md`; `docs/FUTURE_EXPERIMENTS.md`; `docs/EXPERIMENT7_CLOSEOUT_ERRATA.md` (append rows only); `outputs/SUPERSEDED.md` (hand-appended Markdown index, not a JSON artifact); `scripts/verify_report_claims.py` (reporting-only, already post-freeze per errata E14).
* **Immutable.** The files below are not edited; corrections to them go to errata, to report notes, or to a future registry v6:
  * `EXPERIMENT7_CLOSEOUT.md`.
  * Every `outputs/**/*.json`, including `outputs/exp7/EXP7_LEVELS.json`.
  * `CANONICAL_RESULTS_v*.json`.
  * `src/cota_opt`.
  * Runner and closeout scripts: `exp*_run.py`, `exp*_cell.py`, `exp7_stage1*.py`, `exp7_closeout.py`.
  * Every document registered by path in `CANONICAL_RESULTS_v5.json`: `EXPERIMENT2_CLOSEOUT.md`, `EXPERIMENT3_CLOSURE.md`, `EXPERIMENT3_CONTRACT.md`, `EXPERIMENT4_ORIGINAL_QUESTION_ADDENDUM.md`, `EXPERIMENT6_CLOSEOUT.md` and the others listed there.
  * **The Exp 7 contract-listed protocol documents.** These are `docs/EXPERIMENT7_PROTOCOL.md`, `docs/EXPERIMENT7_AMENDMENT.md`, `docs/EXPERIMENT7_PROTOCOL_AS_ISSUED.md` and `docs/EXPERIMENT7_SEPT23_FINALIZATION.md`. `outputs/exp7/EXP7_CONTRACT.json → protocol` lists all four, and none has been touched since the freeze commit `4a2ba9f6`.
* No new experiments are run. No new evaluations are run either, including a re-run of the baseline evaluator to obtain numbers that are not already recorded.

---

## 0. Decision summary

| # | Sev. | Decision | One-line reason |
|---|---|---|---|
| M1 | CRIT | **ACCEPT WITH MODIFICATION** | Verified: B1 ran Model A. Two changes to the fix. The consolidated protocol is contract-listed, so it is corrected through errata rather than edited. The cross-route figure is an upper bound on served-leg wait savings, which is not the same thing as "the omission". |
| M2 | CRIT | **ACCEPT WITH MODIFICATION** | Verified: 0.0065% is superseded; the canonical result is +0.0902% unserved / +0.054% objective. Two corrections to the referee. (1) D32 retires the 0.039% A1 floor, not the 0.287 floor; the 0.287 floor stays the 2B judging threshold but its provenance is disclosed. (2) The verifier holds no 2B claim at all. |
| M3 | CRIT | **ACCEPT WITH MODIFICATION** | Verified: objective change −2.21%. The referee's monotonicity condition is wrong as stated (correct thresholds below). The "served share above 120 min" figure is not in any artifact; that part is rejected. |
| M4 | CRIT | **ACCEPT WITH MODIFICATION** | Verified: 66.8% served at baseline. Calling it a "failed validation" is softened to "aggregate reproduction not met". No artifact records the structural/discouraged split for the certified instance; a labelled historical figure exists. |
| M5 | CRIT | **ACCEPT WITH MODIFICATION** | Values verified. +9.28% is "orientation only, not firewall-admitted" and must be labelled so. The referee also omitted Exp 4A's counterpoint: crediting all of N4's common-lines bound still does not close Δ43. |
| M6 | CRIT | **ACCEPT WITH MODIFICATION** | (a), (b) and (d) are verified. (c) is wrong: add_stop is not cost-free. Its new links get observed times or the estimator's dwell intercept. The direction of bias is therefore unknown, not "favours add_stop". |
| M7 | IMP | ACCEPT WITH MODIFICATION | The table is verified, with cells corrected (Exp 2/2B crowding off; path-set counts). |
| M8 | IMP | ACCEPT WITH MODIFICATION | Adopt the three terms. Retitling is recommended, not required. |
| M9 | IMP | ACCEPT WITH MODIFICATION | 14 of 14 references verified; 2 had details corrected or completed; 1 added (Barr et al. 1995). |
| M10 | IMP | ACCEPT | Problem statement supplied below. |
| M11 | IMP | ACCEPT WITH MODIFICATION | A1's volume addition is the as-issued design, not an implementation error. The direction of the truncation bias is not asserted. |
| M12 | IMP | ACCEPT (a, b, c, d, f); ACCEPT WITH MOD (e) | (e): R4 involved both D24 and D27 (D27's table shows Exp 2's treatments fell back to greedy 72/72). |
| M13 | IMP | ACCEPT (b, c, d, e); **REJECT (a)'s causal claim** | A5 is selected without λ = 1 (λ = 4 alone scores 1.064 > A6's 0.685), and A1 (0.415) ranks below A6 regardless. |
| M14 | IMP | ACCEPT WITH MODIFICATION | Abstract ≤ 250 words supplied. The journal limit is phrased as "typical", to be confirmed at submission (not independently verified). |
| M15 | IMP | ACCEPT WITH MODIFICATION | The tag `exp3-final-v1` exists in Ian's clone (STATE_OF_PLAY:1090), not in this container. Figures are deferred; the existing `outputs/figures/*.svg` are Model A and must not be used. |
| M16 | IMP | ACCEPT | — |
| M17 | IMP | ACCEPT | Verified against closeout §4.1. |
| m1–m32 | MIN | 27 ACCEPT, 4 ACCEPT WITH MOD (m6, m19, m27, m29), 1 REJECT (m20, a duplicate of M3(e)) | §2 below. |

The most consequential corrections:

1. Relabel B1 and add a retraction. Cross-route common lines were never tested.
2. Replace the superseded 2B magnitude, and stop calling the 240-set sweep "certified".
3. State and size the objective's non-monotonicity correctly.
4. Show the 66.8% baseline reproduction in the status box.
5. Give F4 as a closure-dependent range, with its model conditions.
6. Quote the Exp 3 regime caveat.

---

## 1. Major comments

### M1 — B1 "cross-route common lines" actually ran Model A — **ACCEPT WITH MODIFICATION**

**Evidence (verified).**

* **The level definition.** `outputs/exp7/EXP7_LEVELS.json → levels[name=B1_COMMONLINES]` has `waiting_model: "pattern"`, `provenance: "class_b_0923"`, and rationale "Class B as issued: common-lines assignment (cross-route waiting)."
* **The Stage 1 records.** `outputs/exp7/stage1/evals/N0/B1_COMMONLINES.json → evaluator_checks.common_lines = "pattern"`, `common_lines_source = "explicit"`. BASE has `"same_route"`.
* **The record runs in the pessimistic direction:**

  | quantity at baseline | B1 | BASE |
  |---|---|---|
  | unserved | 10,959.06 | 10,423.68 |
  | GC per served trip | 89.29 | 86.26 |

  The path count is identical (152,241). B1 raises modeled waits relative to BASE; cross-route common lines would lower them.
* **The code.** `src/cota_opt/pathset.py:409–416`: `mult_b = mult_a`, and it is replaced by `common_lines_multiplier` (same-route patterns only, `qualifying_patterns` requires `pattern_route[q] == route`) only when `common_lines == "same_route"`.
* **No cross-route option exists.** `src/cota_opt/hyperpath.py` is a diagnostic *upper bound* ("This module answers that with an upper bound rather than a model"), not an evaluator.
* **The config.** `config/assumptions.yaml → path_assignment` defines `pattern` as Model A.
* **Where the mislabel came from.** The as-issued protocol (`docs/EXPERIMENT7_PROTOCOL_AS_ISSUED.md:62–65`) asked for "Common-lines or hyperpath assignment, addressing the cross-route waiting issue". The project's own vocabulary calls Model B the "same-route common-lines" correction (ACCEPTANCE.md:290; D10/D12), and the evaluator knob is named `common_lines`. Setting the knob to `pattern` therefore *turns off* same-route common lines; it does not turn on cross-route common lines. The mislabel is repeated in:
  * `docs/EXPERIMENT7_PROTOCOL.md:61` ("Common-lines (`pattern`) waiting");
  * `docs/EXPERIMENT7_AMENDMENT.md:402` (`same_route` / `pattern` (common lines)) and §13.5 (line 627);
  * `docs/FUTURE_EXPERIMENTS.md:255` ("Re-run F1, F4 and Exp 7 Class B level B1", which implies B1 was a common-lines level).

**Consequence for the Exp 7 closeout.** The amendment's claim bound (`docs/EXPERIMENT7_AMENDMENT.md`, "Claim bounds for omitted variations") reads: "the cross-route common-lines omission (12.47% of GC on N4) → F4 is conditional on the same-route waiting model unless the waiting model is a level". The only waiting-model level run was Model A, so the condition is **not discharged**. Despite that:

* the closeout's §8 third permitted claim states F4 without that condition;
* §9 lists only the jobs-accessibility objective as "Class B untested";
* `EXP7_CLOSEOUT_TABLE.json → not_covered` omits cross-route common lines.

This requires errata rows (E16, E18 below).

**Other documents relying on B1 as a common-lines test.**

* Report §6 Class B table (line 509).
* `README.md:279` ("1 Class B"; neutral, but should say what it was).
* `docs/FUTURE_EXPERIMENTS.md:249–256` (E18 "Re-run … Class B level B1").
* The contract-listed protocol and amendment, left unchanged and corrected by errata.
* HANDOFF.md, STATE_OF_PLAY.md and EXPERIMENT7_RESULTS.md do not cite B1 numbers. RESULTS.md:120 lists only the jobs objective as untested, so it needs the same addition.

**What B1 did measure.** The fixed certified plans re-scored with Model A's per-pattern headway multiplier, a model-disagreement level in the *opposite* direction from common lines.

* F1 moves only from −6.02% to −5.99%.
* F4 (N4 − N3) moves from +9.66% to +7.86%. Model A narrows the gap.
* F2 moves to +0.130%, and F3 to −0.129% (`EXP7_CLOSEOUT_TABLE.json → rows[].class_b_and_additional`).

These are legitimate Model A vs Model B disagreement figures and may stay in the table under the correct label.

**Modifications to the referee's fix.**

* Fix 5, "Correct the protocol consolidated view", is **rejected as an edit**. `docs/EXPERIMENT7_PROTOCOL.md` and `docs/EXPERIMENT7_AMENDMENT.md` are contract-listed (`EXP7_CONTRACT.json → protocol`), so the correction is recorded in errata E16 instead.
* Fix 4's figures need scope. 0.516% (N0), 1.16% (N3) and 12.47% (N4) are `hyperpath` upper bounds on the *wait saving on legs already served*. They do not include riders retained by shorter waits (Exp 4A addendum, gate 4-10: "It is not measured, and it is not excluded").
  * N0's figure covers only am_peak and midday, in the Exp 1 instance (`outputs/model_diagnostics_modelB.json → hyperpath.periods = ["am_peak","midday"]`).
  * N3's and N4's figures come from the Exp 4A diagnostics (`outputs/exp4_addendum/diag_N3.json`, `diag_N4.json → common_lines_bound`), whose period coverage is not recorded.

**Edits.**

1. **Report §6, Class B table, row 509.**
   * Old: `| B1 cross-route common lines (Class B) | −5.99% | +7.86% |`
   * New: `| B1_COMMONLINES: Model A (per-pattern headway) waiting, **not** cross-route common lines (Class B; model disagreement) | −5.99% | +7.86% |`
   * Add directly under the table:
     > The as-issued Class B item "common-lines or hyperpath assignment" was not implemented. No cross-route evaluator exists in `src/cota_opt`; `hyperpath.py` computes only a diagnostic bound. The level named `B1_COMMONLINES` ran the retired Model A evaluator (`common_lines = "pattern"`, `EXP7_LEVELS.json`; Stage 1 `evaluator_checks`). It therefore measures Model A vs Model B disagreement, which *raises* modeled waits (N0 baseline unserved 10,959 vs 10,424 at BASE). It is not a test of the cross-route omission, which runs the other way. Every Exp 7 finding remains conditional on the same-route (Model B) waiting model (errata E16; R13). (The Exp 6 safeguard bundle also called "B1" is unrelated; see Glossary.)
2. **Report §3, line 187–188.**
   * Old: "Cross-route common lines are not modeled. The omission is bounded at 0.516% of generalized cost on N0 (12.47% on N4)."
   * New:
     > Cross-route common lines (Chriqui and Robillard, 1975; Spiess and Florian, 1989) are not modeled. A diagnostic upper bound on the wait saving they would give *on legs already served* is 0.516% of GC on N0 (Exp 1 instance, am_peak and midday only), 1.16% on N3 and 12.47% on N4 (Exp 4A instance). Riders who would be retained by shorter waits are not included, so the effect on the objective is neither measured nor bounded. No experiment varied this (§6, R13).
3. **Report §8, row "Cross-route common lines".** New size cell: "upper bound on served-leg wait saving: 0.516% of GC (N0), 1.16% (N3), 12.47% (N4); retention effect unmeasured". New direction cell: "Overstates waiting where parallel routes overlap. Biases F4 against N4 (Exp 4A: crediting all of N4's bound and none of N3's, 93,300 min, still leaves Δ43 positive). Not tested by any Exp 7 level, including B1 (R13)."
4. **Report §9.** Add row R13 (§4 below).
5. **Errata.** Append E16 (§4 below).
6. **`docs/FUTURE_EXPERIMENTS.md:255`.**
   * Old: "Re-run F1, F4 and Exp 7 Class B level B1."
   * New: "Re-run F1 and F4 under it. Exp 7's `B1_COMMONLINES` level ran Model A (`pattern`), not common lines (errata E16), so this item is the first actual test of the as-issued Class B common-lines question."
7. **`README.md:279`.**
   * Old: "1 Class B"
   * New: "1 Class B (Model A waiting; the as-issued common-lines/hyperpath item was not implemented, errata E16)"
   * Also update the README limitation row at line 355: "0.516% of generalized cost under Model B" → "upper bound on served-leg wait saving: 0.516% of GC on N0, 1.16% on N3, 12.47% on N4; untested by Exp 7".
8. **`docs/EXPERIMENT7_RESULTS.md:120`.** Add a bullet: "**Untested:** cross-route common-lines / optimal-strategy assignment. The level named `B1_COMMONLINES` ran Model A (errata E16)."

### M2 — Exp 2B magnitude superseded; scope overstated — **ACCEPT WITH MODIFICATION**

**Evidence (verified).**

* **The superseded artifact.** `outputs/exp2b_certification.superseded.json → _superseded`: "SUPERSEDED FOR QUANTITATIVE INTERPRETATION — produced with starts='incumbent' …"
* **The current values.** `outputs/exp2b_certification.json → _confirmation`:
  * `matched_start_unserved_effect_pct` = 0.09016;
  * `matched_start_objective_effect_pct` = 0.05403;
  * `floors` = 0.314;
  * `verdict`: "NULL stands … positive at every seed: the candidate is worse than doing nothing."
* **The per-seed results.** `outputs/exp2b_confirmation.json` (contract `7157ce1de9373420`, `starts="both"`), as (treatment − control) per `firewall/compare.py:173`:

  | seed | objective | unserved |
  |---|---|---|
  | 20260825 | +0.0528% | +0.0931% |
  | 20260826 | +0.0528% | +0.0931% |
  | 20260827 | +0.0566% | +0.0843% |

  Seeds 1 and 2 are bit-identical in both arms, so there are two distinct outcomes, not three. D31 (`DISCOVERIES.md:1763`) reproduces this table.
* **The stale registry entry.** `CANONICAL_RESULTS_v5.json → experiments.exp2b` is stale. Its `headline` still quotes +0.0065% / 0.02 floors and its `superseded` list is `[]`. Registry files are immutable, so a future v6 corrects them; for now a documented note goes in the report and `outputs/SUPERSEDED.md`.
* **The registered closeout.** `EXPERIMENT2_CLOSEOUT.md` is registered and also quotes the old value ("+0.007%").
* **(b) Certification table.** Verified in `EXPERIMENT2_CLOSEOUT.md`, "Certification status". Only three rows are certified: six harmful, none beneficial, and the leader null at full effort. "No multi-edit set beats the best single", "every multi-edit set substitutes" and "leader same at λ ∈ {1,2,4}" are discovery-stage (gate 12; single seed for the λ row).
* **(c) Registry limitation.** Verified: "λ=1 and λ=4 ran one seed each, so no noise floor exists at those weights and no headline may be drawn from them."
* **(d) Floor provenance, partly accepted.**
  * The 0.287-point floor comes from the zero-edit replicates 9,749.1 / 9,748.8 / 9,765.1 (D24). Those are the incumbent-start runs that `exp7` also uses for F2 (`EXP7_STAGE1_SOLUTIONS.json → F2_CONTROL_*`, `source outputs/exp2b_subsets.jsonl`, certified unserved 9,749.13 / 9,748.77 / 9,765.11).
  * Under matched starts the control's unserved demand is 9,745.90 / 9,745.90 / 9,746.75, a spread of 0.85 trips, or about 0.009 points. D32 gives 3σ = 0.00657% of the objective.
  * **Correction to the referee.** D32 and `decisions/2026-08-31-replicate-spread-is-not-a-materiality-floor.md` explicitly retire the **0.039%** A1-census floor, not the 0.287 floor. D31 and the registry still judge 2B against 0.287. The report should disclose the provenance, not declare the floor invalid. Per the decision document, replicate spread bounds solver variance, not error, so "larger than solver variance" does not establish materiality either.
* **(e) The verifier.** The referee says the verifier "checks the 2B value against a stale registry". **Incorrect.** `scripts/verify_report_claims.py` has no 2B/F2 headline claim; its only F2 claims are the Class A range (−0.226/+0.166).
* **Fix 6, verified.** Exp 7's F2 rows evaluate the incumbent-start control plans against one splice plan (digest `1c435b33f6dfa8d5`, identical for all three seeds). The closeout's F2 "certified" value is hard-coded as 0.0065 (`scripts/exp7_stage1.py:188`, `scripts/exp7_closeout.py:166`), and errata E11 says "expected of a 0.0065% effect". Stage 1 F2 labels are fixed-plan properties of those plans. They are not invalid, but they are not plans from the matched-start pipeline.

**Edits.**

1. **Abstract.** Replaced in the M14 rewrite (§3). The splice sentence is: "Through-routing splices give no gain: the best of 12 is slightly worse than no edit under matched solver starts."
2. **Report §5.2.** Replace the "Combinations (2B)" bullet block (lines 352–358) with:
   > * **Combinations (2B), discovery stage:** all 240 structurally feasible subsets were solved at discovery effort (60,000/2/32). This exhaustive sweep is discovery-stage under gate 12: it orders sets and does not size effects. It found that:
   >   * none of the 227 multi-edit sets beats the best single;
   >   * at λ ≥ 2 all 227 *substitute*, delivering less than their members promised separately.
   > * **The leader at certification effort (400,000/20/0, three seeds).**
   >   * Re-solved with matched starts (`starts="both"`), `splice|011|034|WESHIGW` is **worse than no edit**: **+0.090% unserved demand, +0.054% of the objective**, positive at every seed. Two of the three seeds are bit-identical.
   >   * That is 0.31 of the 0.287-point floor Exp 2B judges against, so the preregistered verdict is NULL (`outputs/exp2b_certification.json → _confirmation`; D31).
   >   * The originally recorded +0.0065% came from an incumbent-start run in which the splice silently fell back to a greedy build (D27). It is superseded for quantitative interpretation (`outputs/exp2b_certification.superseded.json`).
   > * **Floor provenance.** The 0.287-point floor is the spread of three incumbent-start zero-edit replicates (9,749.1–9,765.1 unserved; D24). Under matched starts the control's spread is about 0.009 points (D32). Replicate spread bounds solver variance, not solver error (D32–D33). The floor is therefore the preregistered judging threshold, not a measured materiality bound.
   > * **Other weights.** At λ = 1 and λ = 4 (one seed each, discovery effort, no floor), the same single edit leads and no multi-edit set beats it (D25). No headline is drawn at those weights.
3. **Report §5.2, singles bullet (line 349–351).** Append: "These single-candidate runs also used incumbent starts. At certification effort the start policy moved the control by 0.008% of the objective (D27), so the harm verdicts stand; the +0.060% and +0.160% magnitudes carry the same caveat."
4. **Report §6.1, F2 row.**
   * Certified cell: replace "+0.0065%" with "+0.090% unserved (matched starts; superseded record +0.0065%)".
   * Stage 1 cell: append "Stage 1 evaluates the incumbent-start Exp 2B control plans against the splice plan (BASE +0.0065%), not matched-start plans (errata E17)."
5. **Report §1 table, row "2 / 2B".**
   * Old: "Closed: no supportable claim / certified null"
   * New: "Closed: no supportable gain (leader not better than no edit at certification effort; 240-set sweep discovery-stage)"
6. **Report §9, R4 "now" cell.**
   * Old: "0.0%; certified null (2B)"
   * New: "no gain; under matched starts the leader is +0.09% unserved, worse than no edit (2B; R14)"
   * Add row R14 (§4).
7. **Report §11, "Recombining routes did nothing".**
   * New: "Through-routing splices gave no gain (the best was slightly worse than no edit)".
8. **Appendix A row.**
   * Old: `| 2B leader +0.0065%; 240 / 227 | outputs/CANONICAL_RESULTS_v5.json | experiments.exp2b.headline | |`
   * New: `| 2B leader +0.090% unserved / +0.054% objective, 0.31 floors | outputs/exp2b_certification.json | _confirmation.matched_start_*; per-seed in outputs/exp2b_confirmation.json | contract 7157ce1de9373420 |` and `| 240 / 227 (discovery stage) | EXPERIMENT2_CLOSEOUT.md; outputs/exp2b_stageA.csv | — | |`
   * Add a note under Appendix A: "Registry v5 `experiments.exp2b.headline` and `EXPERIMENT2_CLOSEOUT.md` still quote the superseded +0.0065%. Both are immutable; the canonical value is `exp2b_certification.json → _confirmation`, and a future registry v6 should correct the headline and list `exp2b_certification.superseded.json` under `superseded`."
9. **Errata.** Append E17 (§4).
10. **`README.md:306` and `docs/EXPERIMENT7_RESULTS.md:64`.**
    * Old: "as expected for a 0.0065% effect"
    * New: "as expected for an effect that small (recorded +0.0065% on the incumbent-start plans Exp 7 evaluates; +0.090% under matched starts, errata E17)"
11. **`outputs/SUPERSEDED.md`.** Append a block:
    > ## exp2b — leader certification magnitude (superseded for quantitative interpretation 2026-08-31)
    >
    > - `outputs/exp2b_certification.superseded.json` (effect_pct +0.0065, incumbent starts, D27)
    >
    > **Current instead:** `outputs/exp2b_certification.json → _confirmation` and `outputs/exp2b_confirmation.json` (+0.0902% unserved, +0.0540% objective, matched starts; D31).
    >
    > The registry v5 `exp2b.headline` and `EXPERIMENT2_CLOSEOUT.md` still quote the superseded value; both are immutable.
12. **Verifier.** Add claims (§5).

### M3 — Objective is not a welfare measure; incommensurable metrics — **ACCEPT WITH MODIFICATION**

**Evidence.**

* **(c) The objective change, verified.**
  * From `outputs/exp1_baseline_modelB.json`: baseline GC 1,772,726.89, unserved 10,261.92, so baseline objective = 1,772,726.89 + 120 × 10,261.92 = 3,004,156.95.
  * λ = 2 frontier plan (`outputs/canonical/exp1_final.json → frontier[λ=2]`): GC 1,787,699.00, unserved 9,583.06, objective 2,937,665.70, a change of **−2.213%**.
  * The three-seed mean computed linearly from the headline means (+0.8782% GC, −6.6520% unserved) is **−2.21%**.
  * Per-seed objectives are not recorded, so no SD can be given.
  * The objective identity (served-only GC + λ·60·unserved) is verified in `src/cota_opt/exp2.py:135–151` and `pathset.py:597–627`.
* **(a) The referee's monotonicity condition is mathematically wrong as stated.** Per OD with flow f and cost c, the contribution is f·[r(c)·c + (1 − r(c))·L], where L = 60λ. On 60 < c < 210, r = 1 − s(c − 60) with s = 0.9/150 = 0.006, so

  dZ/dc = f·[1 + s(60 + L) − 2sc].

  This is negative only for c > (1/s + 60 + L)/2:

  | λ | threshold | does the band exist? |
  |---|---|---|
  | 2 | **173.3 min** | yes, (173.3, 210) |
  | 1 | 143.3 min | yes |
  | ≥ 3.22 | ≥ 210 min | no; marginal worsening never lowers Z |

  For c ≥ 210, r = 0.10 is constant and dZ/dc = 0.1f > 0. The condition c > λ·60 (the referee's) is the condition for **removing the OD's last path entirely** (ΔZ = f·r(c)·(L − c)). The report's §3 already states that correctly.
  * **When the removal channel is available.** Removal is available only where the decision space can delete every path for an OD: OFF in Exp 4–7, or geometry edits. Exp 1 forbids OFF and caps h ≤ max(60, baseline), so in Exp 1 only the marginal channel, for OD costs in (173.3, 210) at λ = 2, can make worse service score better.
  * **Retained points of the referee's comment.** The objective is not monotone in level of service. The property is structural, not specific to Exp 7. It should be stated in §3.
* **The served-flow share above 120 min** (fix 1) **is not recorded in any artifact.** Producing it requires building the evaluator and scoring the baseline, which is new computation. **Rejected for this round.** Defer it to FUTURE work with the analytic statement in its place.
* **(b) Positioning.** Accept that the objective is not a consumer-surplus or welfare measure. Do **not** attribute a welfare objective to Lee and Vuchic (2005) beyond "variable-demand network design with modal split" (verified abstract); the referee's characterization of their objective was not verified.
* **(d) Metric mixing.** Accepted; table below.
* **(e) λ calibratability.** Modify. The binding guidelines' calibration register says λ is "Policy choice; … it is a value judgement". Keep that, and add the interaction with the retention curve.

**Edits.**

1. **Report §3, "Objective".** Insert after the first bullet a new paragraph headed **"The objective is not a welfare measure."**
   > Per OD pair with flow f and least cost c, the objective counts f·[r(c)·c + (1 − r(c))·λ·60], where r is the retention curve (1 up to 60 min, falling linearly to 0.10 at 210 min). It is a λ-weighted sum of served-trip generalized cost and lost trips, not consumer surplus. Two consequences follow, both independent of experiment:
   >
   > 1. *Removing* an OD's last path lowers the objective whenever c > λ·60 (by f·r(c)·(c − λ·60)). That needs a decision space that can delete every path for an OD: OFF in Experiments 4–7, or geometry edits.
   > 2. *Marginally worsening* an OD's service lowers the objective whenever c lies between (1/s + 60 + λ·60)/2 and 210 min, where s = 0.006 per minute is the retention slope. At λ = 2 that is c ∈ (173.3, 210) min; at λ = 1, c ∈ (143.3, 210); for λ ≥ 3.22 the interval is empty. Experiment 1 forbids OFF, so only this second channel is open to it.
   >
   > Lower objective therefore does not always mean better service. The share of baseline flow in the exposed cost band is not recorded in any artifact and is not reported here.
   * Then edit the existing bullet "A served trip counts its full generalized cost c … (errata E7)" so that it refers back to this paragraph and drops the bare "(errata E7)" (see m32).
2. **Abstract.** The new abstract (§3) uses "a λ-weighted sum of passenger generalized cost and modeled unserved demand".
3. **Report §5.1 table.** Add a row: `| objective (GC + 120·unserved) | **−2.21%** | not recorded per seed |`. Add a source line: "Computed from `exp1_baseline_modelB.json → baseline_gc, baseline_unserved` and `exp1_final.json → headline` means (linear); the λ = 2 frontier run gives −2.213%."
4. **New table in §5 preamble** (after line 294), "**All levers on one metric (% of the λ = 2 objective, each in its own model instance)**":

   | lever | effect, % of objective | instance / status |
   |---|---|---|
   | Frequency reallocation (Exp 1) | −2.21% | Exp 1 instance (crowding on, frozen 243,257-path set); 3-seed mean, computed |
   | Through-routing leader (Exp 2B) | +0.054% | Exp 2B instance (crowding off); matched starts, 3 seeds (2 identical) |
   | add_stop leader (Exp 3) | −0.187% | Exp 3 instance; 20 restarts; seed-distinguishable |
   | Greenfield N4 vs N3 (Exp 4A / 6 / 7) | +8.55% to +9.66% | Exp 4A–7 instance; single basin to closed |
   | Safeguards (Exp 6) | 0 to +0.91% (N0) | Exp 6 instance; closed |

   Follow it with: "The instances differ (§4.1); the ordering is qualitative."
5. **Report §8, "Uncalibrated parameters" row.** Replace "λ is a policy choice, not calibratable (guidelines, calibration register)" with "λ is a value judgement (calibration register). It interacts with the retention curve: λ·60 sets the cost band in which the objective rewards worse service (§3)."
6. **Glossary.** Add "**Objective (λ-weighted):** GC of served trips + λ·60·unserved trips; not a welfare measure (§3)."

### M4 — Baseline vs its anchor; validation box — **ACCEPT WITH MODIFICATION**

**Evidence.**

* **The anchor and the shortfall.** `config/assumptions.yaml:45–51` derives 30,949 as 38,694 × 95.98% ÷ 1.20. `exp1_baseline_modelB.json`: served 20,687.08 (**66.84%**), unserved 10,261.92 (33.16%). In the Exp 6/7 instance the current plan's unserved is 10,423.68 (`EXP7_ANALYSIS.json → f1_adaptive[BASE].current_plan_unserved`; Stage 1 `evaluator_checks.baseline_unserved_demand`).
* **(b) Framing.** Fair in substance. The guideline's four validation dimensions (`RELEASE_AND_REPORTING_GUIDELINES.md` §4) do not include a system total, and the 30,949 is used as a demand *pool*. The report nonetheless calls it "weekday linked transit trips", and those trips are made today, so failing to reproduce them by a third is a documented inconsistency. Word it as "aggregate reproduction not met", not as a fifth formal validation dimension marked `failed`.
* **(d) Split.** `PathSetEvaluator.evaluate` computes `unserved_structural` and `unserved_discouraged`, but **no canonical artifact records them for the certified Exp 1 or Exp 6 baseline.** The only N0-baseline split on disk is a pre-Model-B ablation run: `outputs/experiments/exp3_ablation_20260826T112047Z/experiment.json → metrics.configs["A path"].baseline.total`, commit `acb0e919`, run before gate 10's Model B pass. It gives unserved 10,886.2 = 2,380.3 structural (21.9%) + 8,505.8 discouraged (78.1%).
* **Structural (no-path) loss is evaluator-independent but path-set dependent.** Report that historical split only as labelled indicative evidence, or defer it. *Adjudication:* report it, labelled.
* **Additional verified context for OFF-permitting instances.** Exp 4A diagnostics (`outputs/exp4_addendum/diag_N3.json`, `diag_N4.json → totals`):

  | network | served share | structural (no-path) share |
  |---|---|---|
  | N3 | 53.1% | 35.5% |
  | N4 | 36.3% | 54.7% |

  In the OFF-permitting instance most of the gap is structural.

**Edits.**

1. **Model status box, "Validation" row.** Replace with:
   > **Aggregate reproduction: not met.** At the current timetable the model serves 20,687 of the 30,949 NTD-derived weekday linked trips it is scaled to (66.8%; `exp1_baseline_modelB.json`). The 33% "unserved" is a property of the model (retention curve, 600 m access radius, path enumeration, OD truncation), not of observed ridership. Route volume, stop pattern, transfer behaviour and trip length: **all four `unavailable`** (no observed boardings, transfers or trip-length data).
2. **Model status box, "Demand" row.** Replace with:
   > **Commute spatial pattern only.** The NTD-derived total of 30,949 weekday linked trips (which includes non-work trips) is distributed over LEHD LODES 2022 home–work pairs; the spatial pattern of non-work travel is absent. The total assumes a 20% transfer rate (unobserved).
3. **Report §5.1, first bullet.** Append:
   > Unserved demand is a model construct: the current plan already leaves 33% of the NTD-anchored total unserved. In an earlier, pre-Model-B evaluation of the same baseline (`outputs/experiments/exp3_ablation_20260826T112047Z`, not canonical), 22% of baseline unserved demand had no path at all and 78% was lost through the retention curve. The split is not recorded for the certified instance.
4. **Abstract.** The new abstract says "at the current timetable it serves 67% of that total".
5. **Report §8.** New row:
   `| Baseline reproduction of the NTD total | 66.8% served at the current plan (Exp 1 instance; 66.3% in the Exp 6/7 instance) | Unserved-demand changes are changes in a model construct. In OFF-permitting instances most unserved demand is structural (Exp 4A: N3 35.5%, N4 54.7% of all demand has no path) |`
6. **Glossary, "Unserved demand".** New text: "modeled trips with no enumerated path (*structural*) or dropped by the retention curve (*discouraged*). At the current plan, 33% of the NTD-anchored total. A model quantity, not observed riders."

### M5 — Greenfield conclusion overstated — **ACCEPT WITH MODIFICATION**

**Evidence (verified).**

* **The three values:**

  | value | source | status |
  |---|---|---|
  | **+9.66%** | `DELTA43.json`, effect 283,973.37, `admission_N3/N4 ADMITTED` | single-basin, firewall-admitted |
  | **+9.28%** | `EXPERIMENT6_CLOSEOUT.md:398–401`: best-known N4 from the D39 preflight (3,207,566.42) − N3 closed REF = 272,400.39 | **"For orientation only, and not a firewall comparison"**; the referee omitted this qualifier |
  | **+8.547%** | `EXP7_ANALYSIS.json → f4[level=BASE, control=N3, treatment=N4].delta_pct`, `admitted: true` | Stage 2 closure, preregistered adaptive F4 |

* **(b) Path-model caveat.** Verified: `CANONICAL_RESULTS_v5.json → experiments.exp4a.caveats[0]`, including "omission-corrected Delta43 +7.87%, not certified". Exp 1's gate-4 line is 0.6706% (`exp1_baseline_modelB.json → gate4_line_pct`).
* **(c) Common-lines exposure.** N3 = 1.164% (`diag_N3.json → common_lines_bound.bound_share_of_generalized_cost_pct`).
  * **The referee omitted** Exp 4A's own bound arithmetic (`EXPERIMENT4_ORIGINAL_QUESTION_ADDENDUM.md`, gate 4-10). Crediting all of N4's bound (107,248 min) and none of N3's (about 13,950) gives 93,300, which is less than Δ43 (283,973) and less than the omission-corrected Δ43 (226,948).
  * The sign survives the served-leg wait re-pricing bound. The addendum adds that retention effects are "not measured, and … not excluded". Report both halves.
* **(d) Proxy vs physical vehicles.** The proxy is 176.49 at the baseline PM peak against 197 physical vehicles (`CANONICAL_ENVELOPE.json`). The ratio for N4 is unknown (fleet instrument UNDECIDABLE). Accepted.
* **(e) Leader not established.** Verified: registry `exp4.limitations[0]`, and the Exp 5 residual of 1.7034% against the 0.387% margin.
* **(f)** Accepted.

**Edits.**

1. **Abstract.** In the M14 rewrite: "The best of 200 generated greenfield networks is 8.5–9.7% worse than the redesigned existing network, conditional on a path model that fits it worse." (The +9.28% sits inside the range, so the abstract does not need to label it.)
2. **Report §5.4, the 4A bullet (lines 401–405).** Replace with:
   > * **Experiment 4A asked the original question under the same contract:** does the best greenfield network (N4) beat the Experiment 3 redesign (N3)?
   >   * **No, in every measurement.** obj(N4) − obj(N3) at λ = 2:
   >
   >     | comparison | Δ, % of N3's objective | status |
   >     |---|---|---|
   >     | Exp 4A, one start basin per network | **+9.66%** | firewall-admitted, preregistered |
   >     | Exp 6, best-known N4 vs closed N3 REF | +9.28% | orientation only, not firewall-admitted |
   >     | Exp 7 Stage 2 BASE, closure on both sides | +8.55% | firewall-admitted |
   >
   >     The 1.1-point spread is start-basin dependence.
   >   * **Conditions.** The path model fits N4 markedly worse: 8.7–34.8% of flow improvable on N4 vs 1.0–3.7% on N3, against Exp 1's 0.67% adequacy line. Its omission-corrected Δ43 is +7.87% and is **not certified**. The waiting model omits cross-route common lines: the served-leg wait-saving bound is 12.47% of GC on N4 vs 1.16% on N3. Both biases run against N4. Crediting N4 with its whole common-lines bound and N3 with none (93,300 min) still leaves Δ43 positive, but retained-rider effects are not measured (`EXPERIMENT4_ORIGINAL_QUESTION_ADDENDUM.md` §5; registry `exp4a.caveats`).
   >   * **Resources.** Both networks share the EXP4N proxy envelope, not a common fleet. The proxy reads 176.49 against 197 physical vehicles on N0, and the corresponding ratio for N4 is unknown, so equal proxy budgets may be unequal fleets in either direction.
   >   * **The leader is not identified.** EXP4N's first-to-second margin (0.387%) is smaller than the N4 start-basin residual measured in Exp 5 (≥ 1.70%). Nothing is known about the 1,800 proposals the promotion cap excluded (registry `exp4.limitations`).
   >   * N4 stays worse at every fixed-plan λ above 1.087.
   >   * In this instance N3 serves 53.1% and N4 36.3% of the 30,949 modeled trips (`diag_N3/N4.json → totals`).
3. **Report §6.1, F4 row, "certified" cell.** "+9.66%" → "+9.66% (single basin; +8.55% closed, Stage 2 BASE)".
4. **Report §11.** "the best greenfield design did worse" → "the best greenfield proposal we generated did worse, under a path model that fits it less well".
5. **Report §3 / §8.** Common-lines figures for N0, N3 and N4, as in M1 edits 2–3.
6. **Appendix A.** Add a row: `| +8.55% (F4 Stage 2 BASE) | outputs/exp7/EXP7_ANALYSIS.json | f4[level=BASE, control=N3] | contract 1263bedaebe6a45d |`. Add `| +9.28% | EXPERIMENT6_CLOSEOUT.md §9 (orientation only) | — | |`.

### M6 — Exp 3 regime caveat; stop-cost bias — **ACCEPT WITH MODIFICATION**

**Evidence.**

* **(a) Regime caveat.** Verified: `CANONICAL_RESULTS_v5.json → experiments.exp3.regime_caveat` ends "Quote this with the headline." Leader statistics: `outputs/exp3/escalation_report.json → combined[0]`: mean −0.186565%, sd 0.002375%, ratio 78.55, 20 restarts.
* **(b)** Accepted as consequence of (a).
* **(c) Rejected as stated.** `stopedits.py`'s "zero assumed benefit" applies to stop *removal*, which holds runtime fixed. **add_stop** is applied by `geometry.py:411–430` (stop inserted at least detour) and retimed by `_retime` (`geometry.py:447–479`):
  * Each new link takes this pattern's observed time, else another route's observed time for that link, else `SegmentTimeModel.predict` = intercept + slope × distance.
  * The intercept "absorbs dwell and stop-to-stop acceleration" (`geometry.py:72–76`), clamped non-negative (`_lsq`).
  * An added stop on a modeled link therefore costs about one fitted intercept. On an observed link it costs whatever the other route's schedule implies.
  * The leader adds stop NORTER5 to route 010 at a 0 m detour (`outputs/exp3/stageA_rows.jsonl`), so its runtime cost is exactly this implicit per-segment term.
  * That term is not validated as a stop cost: the feed's natural experiment gives −157 s/stop. The **direction is unknown**, not "favours add-stop".
  * What *is* true: removal and consolidation edits are credited zero runtime saving (conservative against consolidation), and add_stop's runtime cost rests on an unvalidated regression intercept.
* **(d) N3 trim.** Verified: `outputs/exp6/d35/N3.json → base_plan_trims_to_fit_envelope` lists route 001 trimmed in five periods (am_peak, midday, pm_peak 15 → 20; evening 15.48 → 20; early 21.82 → 24).
  * **Missed by referee:** `EXPERIMENT6_CLOSEOUT.md:139` says "the added stop lengthens route 001", but the add_stop edit is on route **010**; the trim is on route 001. The closeout is registered and immutable. The report must state only the trim, not that causal attribution.

**Edits.**

1. **Abstract.** In the M14 rewrite: "Route mutation yields 29 seed-distinguishable improvements of 0.01–0.19% of the objective; the leader (an added stop, −0.19%, solved only at 20 restarts) lies within its Exp 7 sensitivity range."
2. **Report §5.3.** After the stability table, replace "The leader is distinguishable from all 28 other certified candidates." with:
   > * The leader is distinguishable from all 28 other certified candidates **at 20 restarts**. Registry regime caveat, quoted verbatim as the registry requires: "The certified set is NOT uniform in solver effort. 23 of the 29 carry 40-restart verdicts; 6 -- every state section 6 never triggered on, the leader among them -- carry 20-restart verdicts, because section 6 escalates what is unresolved or failing and that is by construction the smaller margins. All 28 of the leader's pairwise comparisons are at 20 restarts and the best margin confirmed at 40 restarts is 2.33x smaller. Phase 5b would have closed this and was abandoned with zero cells completed." (`CANONICAL_RESULTS_v5.json → experiments.exp3.regime_caveat`.) The leader therefore leads on the softer measurement (§7, finding 2).
   * Also add "|mean Δ| / SD (sample SD over five paired seeds; SD = 0.0024% of the objective)" (m23).
   * Add a bullet: "N3, the network Experiments 4A–7 carry forward, is N0 plus this edit. To fit the EXP4N envelope, its base plan trims route 001 in five periods (e.g. am_peak 15 → 20 min; `outputs/exp6/d35/N3.json → base_plan_trims_to_fit_envelope`)."
3. **Report §8, "Stop cost" row.** New direction cell: "Stop removal and consolidation are credited zero runtime saving, so no consolidation claim. Added stops are timed by observed link times or by the novel-link estimator, whose intercept absorbs dwell and acceleration but is not validated as a stop cost. The bias on add_stop effects, F3 included, has unknown direction."
4. **Report §11.** "editing them did almost nothing" → "route edits gave effects of at most 0.19% of the objective, within model uncertainty".

### M7 — Cross-experiment confounds — **ACCEPT WITH MODIFICATION**

**Evidence (verified cells).**

* **Crowding.**
  * Exp 1 on (`scripts/seed_check.py:154` `with_crowding=True`; closeout §4.1).
  * Exp 2/2B off (`scripts/exp2_treatments.py:195`, `scripts/exp2b_subsets.py:452`).
  * Exp 3 off (`src/cota_opt/exp3_score.py:299`; the referee wrote `exp3_score.py`, which is under `src/`).
  * Exp 4–7 off.
* **Path set.** Exp 1 is frozen at 243,257 paths. Exp 4A–7 rebuild the path set per network and per certify call (`DELTA43.json → pathset_policy`; Exp 7 N0 BASE 152,241 paths).
* **F1 instance gap.** −6.65% vs −6.02% (closeout §4.1).
* **Matched-start 2B effect.** In objective terms +0.054%, below Exp 3's leader magnitude but above its smallest certified effect (0.0096%). "Detection power differs" is accepted.

**Edit.** Add **§4.1 "Model instances and their differences"** after §4's Reproducibility paragraph:

> | | Exp 1 | Exp 2 / 2B | Exp 3 | Exp 4N / 4A / 5 / 6 / 7 |
> |---|---|---|---|---|
> | solver | Gen1 exchange, 400,000 × 20, 3 seeds | Gen1; discovery 60,000/2/32, certification 400,000/20, 3 seeds | Gen1, 20 restarts (23 of 29 escalated to 40), 5 paired seeds | (8, 3)-block certifier, ≤ 120 rounds, greedy start (+ closure in Exp 6–7) |
> | decision space | no OFF; h ≤ max(60, baseline); express lock | no OFF | no OFF | OFF allowed (`allow_off`) except where a policy cell forbids it |
> | crowding | on | off | off | off |
> | path set | frozen, 243,257 paths, widened to pass gate 4 | rebuilt per network | rebuilt per network | rebuilt per network per certify call (N0: 152,241) |
> | headline metric | % unserved | % unserved vs 0.287-point floor | % objective, seed-distinguishability ratio > 3 | % objective |
> | start policy | incumbent (no treatment arm) | incumbent (treatment-dependent, D27) → matched (`both`) for the leader | `both` | greedy + closure anchors |
>
> Comparisons between levers are qualitative. The experiments differ in solver, decision space, crowding, path set, start policy, metric and noise floor. The model instance alone moves F1 from −6.65% (Exp 1) to −6.02% (Exp 6/7 Stage 1 BASE, §6.1). The Exp 2B null is judged against 0.287 points of unserved demand, which exceeds every certified Exp 3 effect on its own scale, so "no gain" and "small gain" partly reflect different detection thresholds.

In §6.1, M17's sentence carries the instance difference.

### M8 — "Certified" overloaded — **ACCEPT WITH MODIFICATION**

**Edits.**

1. **§4 and Glossary.** Replace the Glossary's "Certified" entry with three terms:
   * **Path-set adequate (Exp 1, gate 4):** improvable flow under the 0.67% line; holds for λ ≥ 2 (D15).
   * **Seed-distinguishable:** |mean Δ| / SD > 3 over the stated seeds at the stated effort (Exp 3); or, for Exp 1 and 2B, effect against the seed spread or the preregistered floor.
   * **Block-local certified:** a converged (8, 3)-block-local optimum (Exp 4–7). It is a local-optimality certificate, not a statement about solver variance.
   * Add to each: "None is real-world significance (reporting rule 3)".
   * Keep "certified" in experiment-status labels that are artifact strings (e.g. `EXP6_POLICY_FRONTIER_CERTIFIED`), in code font.
2. **Report §5 preamble (line 292–294).** Replace the definition with a pointer to these three terms, and state which one each section uses.
3. **"Certified null".** Remove it everywhere (abstract, §1 table, §6.1). Use "not distinguishable from zero at certification effort (Exp 2B floor)".
4. **Title.** Retitling is *recommended*, not required. Suggested: "How much can frequency, stops and geometry do for a mid-sized bus network? A convergence-controlled optimization study of the Central Ohio Transit Authority (COTA)". The "two clauses joined by a colon" point (m11) is not adopted: a question plus a descriptive subtitle is standard.

### M9 — Related work — **ACCEPT WITH MODIFICATION** (verified list in §6)

**Edit.** Add **§1.1 "Related work"** after the §1 table:

> **Network design and frequency setting.** The transit network design and frequency-setting problems (TNDP, TNDFSP) are surveyed by Guihaire and Hao (2008), Ibarra-Rojas et al. (2015) and Durán-Micco and Vansteenwegen (2022). Cancela et al. (2015) give mathematical-programming formulations with user waiting times and multiple line options. Classic heuristic network design is Ceder and Wilson (1986). Frequency setting under a fleet constraint goes back to Furth and Wilson (1981). The scale economy behind frequency reallocation, waiting time falling with frequency, is Mohring (1972), the source of the "square-root rule" invoked in D1. Variable-demand network design, in which ridership responds to the network, is treated by Lee and Vuchic (2005). The tension this study's λ and coverage safeguards encode, ridership against coverage, is set out by Walker (2008).
>
> **Assignment.** Frequency-based assignment with *common lines* lets a passenger board whichever attractive line arrives first (Chriqui and Robillard, 1975). *Optimal strategies* (hyperpath) assignment generalizes this to networks (Spiess and Florian, 1989). This study does neither. It assigns all-or-nothing to the cheapest of at most four RAPTOR-enumerated paths, and combines frequency only across patterns of the same route (Model B; §3). Its known consequences are no route-choice dispersion, no cross-route strategy, and dependence on the enumerated path set (§3.0, §8).
>
> **Computational experiments with heuristics.** Comparing heuristics at matched effort, normalizing resource budgets and reporting controlled experiments rather than competitive tables are established cautions (Barr et al., 1995; Hooker, 1995; Rardin and Uzsoy, 2001). Our methodological findings 2, 3, 5 and 7 (§7) are instances of them, found the hard way in a transit setting.
>
> **Model validation.** Standard travel-model practice separates calibration from validation against observed aggregates (Cambridge Systematics, 2010). This model is uncalibrated, and validation data are unavailable on all four dimensions (status box).
>
> **What is new here.** The contribution is not a new frequency-setting algorithm. It is:
> 1. a harness that preregisters contracts, admits only declared treatment differences (semantic firewall), certifies convergence and applies declared basin closure;
> 2. a sequence of negative and bounded results for one real mid-sized network under a common resource envelope;
> 3. a documented record of how such a harness misled itself, and the retractions that followed (§9).

**Edit.** Add a **References** section before Appendix A, listing the §6 entries exactly as given there.

### M10 — Problem statement — **ACCEPT**

All quantities verified:

* wait function: `config/assumptions.yaml:62–68`; `pathset.py:513–514`;
* `common_lines_multiplier`: `pathset.py:336–370`;
* proxy cycle: `COMMON_RESOURCE_ENVELOPE.json → instrument`;
* layover 0.15: `assumptions.yaml:24` ("NOT a verified COTA work rule");
* retention: `assumptions.yaml` (`cost_retention_*`; "A crude discouragement proxy, NOT a mode-choice model");
* ladder: `config/constraints.yaml:14`;
* empty periods: `allow_new_service_in_empty_periods: false`;
* off-ladder baseline values (65.45, 72, 80, 90, 102.86, 120, 144, 180, 240): `exp1_baseline_modelB.json → plans`.

The edit is the full new §3.0 in §3 of this document.

### M11 — Demand construction — **ACCEPT WITH MODIFICATION**

**Evidence (verified).**

* **(a) Units.** `outputs/verify.log:15` reads "LODES OD: 4640957 block rows read, 317706 block-group pairs, 823915 trips". LODES JT00 OD counts are jobs (home–work pairs), so "trips" is a units error inherited from the log string.
* **(b) Scale-after-truncation.** Confirmed at `src/cota_opt/harness.py:140–152`. The retained pairs carry 64.9% of accessible flow (verify.log:17), giving ×1/0.649 = 1.54. The direction of the bias is **not** asserted (the referee's "likely favours trunk-heavy plans" is speculation). X_TOPK40K (same total trips, 40,000 pairs) moved F1 from −6.02% to −5.49% at fixed plans (`EXP7_CLOSEOUT_TABLE.json → rows[F1].class_b_and_additional.X_TOPK40K`).
* **(c) Transfer rate.** Verified: `assumptions.yaml:87`, "COTA's observed rate is UNKNOWN".
* **(d) A1 adds volume.** Verified at `scripts/exp7_levels.py:197–206`. **However, this is the as-issued design:** `EXPERIMENT7_PROTOCOL_AS_ISSUED.md` A1 reads "gravity-model trips at 25%, 50%, and 100% of commute volume" "added to LODES". The report must describe it accurately, not as an implementation error. D5's falsifier ("A demand model two or three times larger") is reached at +100%, while crowding is off in the Exp 4–7 instance.

**Edits.**

1. **§2 Demand row.**
   * "→ 823,915 commute trips" → "→ 823,915 jobs (LODES JT00 home–work pairs, block-group aggregated)".
   * Cell 3 becomes: "Restricted to transit-accessible pairs (24.7% of jobs), truncated to the top 20,000 pairs (64.9% of accessible jobs), then rescaled to an assumed **30,949** weekday linked transit trips. That total is derived from NTD as 38,694 weekday unlinked trips × 95.98% bus share ÷ 1.20, assuming a 20% transfer rate that is unobserved. Rescaling after truncation inflates each retained pair by about 1.54×. Six period shares are assumed, because LODES has no time dimension. Counts from the run log `outputs/verify.log` (not a canonical artifact)."
2. **§6 dimension table, A1 row.** "+25/50/100% non-commute trips …" → "Non-commute trips *added on top of* the NTD-anchored total at 25/50/100% of commute volume (as issued). Total modeled demand rises 25–100%, so A1 perturbs volume as well as pattern; gravity form, commute OD pairs only; crowding not modeled."
3. **§8 "Commute-only demand" and "Operationalization bounds" rows.** Add "A1 changes demand volume as well as pattern (as issued). At +100%, demand reaches the scale at which D5's no-crowding premise is stated to fail, and crowding is off in that instance."

### M12 — Interpretations presented as findings — **ACCEPT (a–d, f); ACCEPT WITH MOD (e)**

* **(a)** Delete §5.1 lines 335–337 ("That is a constructive result … at little cost."). Replace with: "The optimum is flat. Whether unmodeled operational constraints (clock-face headways, interlining, runcutting) can be met at little cost was not tested. The safeguards that were priced (Exp 6) cost up to 0.91% of the objective."
* **(b)** D1's evidence is "Balanced plan (config C, λ=2, matched effort)", Moderate confidence, from before the Model B correction. D2 is of the same vintage, which the referee missed.
  * Replace §5.1 "Where service moves" with: "**Where service moves.** Pre-Model-B analyses found frequency moving from the most frequent routes toward the 30–120-minute tier (D1), with returns plateauing quickly in search effort (D2). Neither is re-verified on the certified Model B plans or checked for seed agreement, and neither is a finding of this report."
  * Add retraction row R16 (§4).
* **(c)** D3 predates the Model B evaluator (D12), and the guidelines require the figure.
  * §7 finding 1 becomes: "**Route-level scoring overstated the network gain of one plan roughly threefold (D3).** The route-level model's λ = 4 plan claims −22.71% unserved demand at −0.76% GC; scored by path assignment it gives −7.16% at +2.51% GC. This is the pre-Model-B path evaluator (D3 predates D12), for one plan; all seven route-level plans were dominated at matched effort."
  * Abstract: drop the number, or say "for the one plan tested".
* **(d)** "generalize beyond Columbus" → "are likely to apply beyond Columbus".
* **(e)** Modified. R4's 0.5% (`splice|033|034`) came from ranking effort, where the D27 table shows Exp 2's treatments fell back to greedy 72/72 while the control kept its incumbent start. Both mechanisms contributed. D31's "both errors pushed the same way" is about the 2B leader, not R4 itself.
  * Abstract (if retained) and §7 finding 2 become: "That error, together with a start policy chosen by the treatment (D27), produced and then forced the withdrawal of the 0.5% through-routing headline (R4)."
* **(f)** §11's last sentence becomes: "The harness caught several of these artifacts. Others (D23, D27, D35, the B1 mislabel and the superseded 2B magnitude) were found by audits outside it."

### M13 — Exp 7 design disclosures — **(a) REJECT causal claim / ACCEPT disclosure; (b)–(e) ACCEPT**

* **(a) The causal claim is wrong.** `outputs/exp7/EXP7_STAGE2_SELECTION.json`:
  * A5's score of 1.1956 is from F4_40 at A5_LAM1: (−1.848 − 9.446)/9.446.
  * Without λ = 1, A5_LAM4 alone gives F4_40 movement (19.495 − 9.446)/9.446 = 1.064, still the top score.
  * A6 scores 0.685 (F1 at A6_MAXWALK75), A1 0.415, A7 0.414.
  * With k = 2 the selection is A5 and A6 whether or not λ = 1 is counted. A1 was not crowded out by λ = 1.
  * **Edit:** in the §8 "Stage 2 scope" row, append: "A1 (demand) ranked third under the preregistered metric (0.415, vs A6 0.685), so no demand perturbation was re-optimized."
* **(b)** §4: "Nothing is waived after the fact" → "Acceptance rules are not waived after the fact. Analysis exclusions made after results were seen are labelled post hoc (§6.0), as are Exp 3's two display-only analysis-code fixes (`EXPERIMENT3_CLOSURE.md` §8)." This also covers m10.
* **(c)** Add to the §6.1 note: "Magnitude bands are relative to Stage 1 BASE (−6.02%), not the certified −6.65% (preregistered, amendment §14.1)."
* **(d)** Add to §6.0: "SIGN_ROBUST and the bands are descriptive labels across 44 Class A levels, 20 of them bootstrap draws. They are not statistical tests, and dimensions with more levels have more chances to register a sign event."
* **(e)** Verified at `EXP7_F1_DECISION_SPACE.json → rows[].cells.R1_H60.record`: at A5_LAM1, A5_LAM4, A5_TP200, A6_WALKSPD85 and A6_MAXWALK75 the record is the initial solve, which closure did not improve.
  * §6.2 and the abstract's re-optimization bullet: append "(Exp 6 model instance and block certifier; one closure per cell; at five of seven levels closure did not improve the initial solve)".
  * Note that R1_H60 is the "closest cell to Exp 1 rules" (`EXP7_F1_DECISION_SPACE.json → closest_cell_to_exp1_rules`): it forbids OFF and caps headways at 60. Say "the closest cell to Experiment 1's rules" instead of "under Experiment 1's rules".

### M14 — Abstract and conclusion — **ACCEPT WITH MODIFICATION**

**Evidence.** The abstract is 528 words by `wc -w` (lines 36–102). The 250-word / highlights / keywords norms are the usual Elsevier TR-family requirements, but the current Guide for Authors was **not** independently verified in this adjudication. State them as a target, to be confirmed at submission.

**Edits.**

1. Replace the abstract with the text in §3.
2. Move the current bullets into a new "**Summary of findings**" table at the start of §1, with one row per lever: lever, effect with metric, status, main caveat.
3. Add Highlights and Keywords (§3).
4. Add to §1 after the mission quote: "Transfer timing (timetable synchronization) is outside this frequency-based model, and stop consolidation is deferred (registry `exp3.limitations`). 'Stop structure' here means adding stops to existing routes."
5. §11 bullet 1 becomes: "**Reallocating frequencies inside the existing routes is the one lever that materially reduced modeled unserved demand:** −6.65% in the Exp 1 instance (−6.02% at Exp 7 Stage 1 BASE), −2.21% of the objective."
6. Fix the fragment at lines 731–732: "…with one closure per cell (post hoc; `docs/EXPERIMENT7_F1_ADDENDUM.md`). At λ = 1 it is +0.12%."
7. Safeguard bullet: add "the zeros are non-binding caps at the best-known REF plan, and prices are basin-dependent at about 0.1–0.16 points (§5.6)."

### M15 — Reporting-standard compliance — **ACCEPT WITH MODIFICATION**

* **Figures.** Defer. Add the visible box (edit 4).
  * **Missed by referee:** `outputs/figures/*.svg` exist (dated Sep 24, from `scripts/make_figures.py`), but `exp1_frontier` and most others read `outputs/fixpoint.jsonl`, the **Model A** run (`make_figures.py:306`). They must not be embedded: that would break rule 1 and repeat D23's error.
* **Tag.** `git tag -l` is empty in this container. Per `STATE_OF_PLAY.md:1090–1103`, `exp3-final-v1` and four other freeze tags exist in Ian's local clone and are not on GitHub.
  * Edit §5.3: "tag `exp3-final-v1`" → "tag `exp3-final-v1` (in the project's local clone, not yet pushed; see Data and code availability)".
* **Appendix A, contract/commit column.** Fill it from the closeouts where available:
  * Exp 1: commit `f1a05645` (`exp1_final.json → commit`).
  * Exp 2B confirmation: contract `7157ce1de9373420`.
  * Exp 4A: contract `0f62aeabfa341a98` (`DELTA43.json → contract.digest`).
  * Elsewhere, write "not recorded in artifact" instead of leaving the cell blank. Do not invent values.

**Edits.**

1. Add §8.0 "Threats to validity" and a "Data and code availability" section (full text in §3).
2. Leave the guideline appendices pending, as the draft already says.
3. Move the LODES counts to "run log, not canonical" wording (M11).
4. Replace the "Status of this draft" bullet "The seven required figures are not yet generated." with: "**Not submission-ready.** The seven required figures are not generated. The existing `outputs/figures` are pre-Model-B and are not used. The units sidecar `CANONICAL_ENVELOPE.units.json`, `LICENSE` and `CITATION.cff` do not exist yet."

### M16 — Resource identity — **ACCEPT**

* **(a)** `exp1_final.json → resources.weekday_revenue_veh_hours_optimized = 2516.5` does not match the λ = 2 frontier run (2,516.645, which rounds to 2,516.6), and the artifact does not say which plan it is.
  * §5.1 becomes: "The λ = 2 frontier plan uses 2,516.65 of 2,517.18 revenue vehicle-hours (`exp1_final.json → frontier[λ=2].revenue_veh_hours`)."
* **(b)** §2 fleet row validation cell: "NTD VOMS 198; nothing tuned. A check on the baseline schedule only; it says nothing about modified plans."
* **(c)** §3 "Crowding" becomes: "Crowding does not bind at the system level at the modeled demand: the median peak-load-point bus is at 9% of capacity (D5). In Exp 4A one N3 am-peak route-period exceeds the 60-passenger planning capacity (max load 68.3). Crowding is priced only in Experiment 1; it is off in Experiments 2–7."

### M17 — Two F1 baselines — **ACCEPT**

Verified at `EXPERIMENT7_CLOSEOUT.md` §4.1. Add after the §6.1 table note:

> Stage 1 evaluates the three certified Exp 1 plans in the Exp 6 model instance (crowding off, per-network path set). There the current plan leaves 10,424 trips unserved, against 10,262 in the Exp 1 instance. The seed plans give −5.94 / −6.16 / −5.98%, against −6.60 / −6.72 / −6.63% (closeout §4.1).

---

## 2. Minor comments

| # | Decision | Edit / note |
|---|---|---|
| m1 | ACCEPT | Verified −0.006854 and −0.009881 (`rows[F6 N3 *].class_a_range[0]`). §6.1 F6: "to between −0.007% and −0.010%". |
| m2 | ACCEPT | §6.2 line 600 and §8 line 673: "zero point" → "the 210-min floor point (`cost_retention_zero_min`, where retention reaches its 0.10 floor)". |
| m3 | ACCEPT | §7.9 title: "A rounded digest cannot distinguish envelopes that differ below its rounding precision." Body: "Two envelopes differing in the last ULP received the same rounded digest; …" |
| m4 | ACCEPT | Covered by M16(a). |
| m5 | ACCEPT | λ table: order 0.25, 0.5, 1, 2, 4, 8, 16. Add λ = 0.25: +15.31%, uncertified (`frontier[0]`). Mark uncertified rows. |
| m6 | ACCEPT WITH MOD | "r = −0.711 (n = 8 edit kinds; descriptive)". |
| m7 | ACCEPT | §5.1 header: "solver seed SD (percentage points)"; cells "0.06" without ±. Keep "solver seed spread" wording per rule 2. |
| m8 | ACCEPT | Glossary additions: Gen1, D33-B, fixpoint, improvable flow share, ULP, anchor, W/X transfers, sentinel, Class A/B, GTFS, RAPTOR, LODES, NTD, VOMS, level-code scheme (A1_NC025 …, R4_C05 …). |
| m9 | ACCEPT | §10: "Stage 1 cells and initial solves are independent and parallelize per cell; basin closure is not (cells depend on each other through anchors)." Delete "trivially parallel". |
| m10 | ACCEPT | Covered by M13(b). |
| m11 | REJECT (colon) | See M8 edit 4. The retitle itself is optional. |
| m12 | ACCEPT | Verified: `rows[AF1 REF].certified = null`; −0.2286 = Exp 6 closed REF. Cell: "Exp 6 closed: −0.23%". |
| m13 | ACCEPT | §6.2 tables: "generalized cost (in-vehicle-minute equivalents per weekday)"; "modeled trips served (of 30,949)". |
| m14 | ACCEPT | First use in §5.6: "Price differences between basins are in percentage points of the objective." |
| m15 | ACCEPT | Glossary bands: "Highly stable / Stable / Moderately sensitive / Highly sensitive (magnitude)", matching artifact strings. |
| m16 | ACCEPT | Superseded by M2's rewrite. If "floors" is retained, define it as effect ÷ 0.287-point floor. |
| m17 | ACCEPT | Appendix A: "+9.66% (+9.659%)" or use 9.66 throughout. |
| m18 | ACCEPT | §1 table Exp 5: "N0 results monotone (informative, not certified)". |
| m19 | ACCEPT WITH MOD | Referee's "49" is wrong. `EXP7_LEVELS.json` has 47 levels plus `declared_not_run` = A4_WAIT375, A4_WAIT500, B2_JOBS_ACCESS_OBJECTIVE (and two dropped/not-included additional items). Text: "50 levels were declared (47 run plus BASE; A4 ×2 and the B2 objective not run)…" |
| m20 | REJECT (duplicate) | Handled under M3(e). |
| m21 | ACCEPT | §6.2 line 575: prefix "Post hoc (errata E7):". |
| m22 | ACCEPT | Verified `allow_new_service_in_empty_periods: false`. §3: "39 routes × 6 periods = 234 route-periods, of which 173 have baseline service. The other 61 cannot be opened, so OFF means switching off a baseline-served route-period." |
| m23 | ACCEPT | Covered by M6 edit 2. |
| m24 | ACCEPT | §5.4: inline "(D36: discovery's ordering was inverted relative to exact objectives; D38: discovery scores are nearly flat)". |
| m25 | ACCEPT | §5.5: "% of N0's objective at the same cell". |
| m26 | ACCEPT | Define J/H/P (joint / hours only / peak only) and the suffix as % of the envelope (e.g. J100) at first use in §5.5. |
| m27 | ACCEPT WITH MOD | Renumber §6.0 → §6.1 and shift later subsections. Optional; do it only if all internal cross-references (§6.1, §6.2 cited in §§3, 5, 7, 8) are updated in the same pass. |
| m28 | ACCEPT | λ table: "(single run)" for every λ ≠ 2 row and for the λ = 2 row; the headline −6.65% is the three-seed mean. |
| m29 | ACCEPT WITH MOD | Footnote: "INFEASIBLE_UNDER_ENVELOPE proven at the levels where it was evaluated (`EXP7_CLOSEOUT_TABLE.json → n3_r1_h20_feasibility`)". The referee's "BASE and A3 only" was not independently verified, so the implementer should read that key and list it exactly. |
| m30 | ACCEPT | Abstract and §5.3: "(model result; not a recommendation)". |
| m31 | ACCEPT | "(78,210 of 317,706 block-group pairs; 24.7% of jobs; run log `outputs/verify.log`)". |
| m32 | ACCEPT | Drop the bare "(errata E7)" in §3. Cite "`docs/EXPERIMENT7_CLOSEOUT_ERRATA.md` E7" in the new M3 paragraph if a pointer is wanted. |

---

## 3. Full text of new and replaced sections

### 3.1 Abstract (replaces lines 36–102; 236 words, `wc -w`)

> We estimate how far changes to service frequency, stop placement, route geometry and whole-network design could reduce a λ-weighted sum of passenger generalized cost and modeled unserved demand on the Central Ohio Transit Authority's (COTA) weekday bus network, holding revenue vehicle-hours and a peak-concurrency proxy fixed. The model assigns LEHD LODES commute flows, scaled to an NTD-derived weekday total, to enumerated paths on the GTFS schedule, with an uncalibrated retention curve; at the current timetable it serves 67% of that total. At λ = 2, reallocating frequencies reduces modeled unserved demand by 6.65% (solver seed SD 0.06 points) and the objective by 2.21%, while total generalized cost rises 0.88%. Through-routing splices give no gain: the best of 12 is slightly worse than no edit under matched solver starts. Route mutation yields 29 seed-distinguishable improvements of 0.01–0.19% of the objective; the leader, an added stop, lies within its own sensitivity range. The best of 200 generated greenfield networks is 8.5–9.7% worse than the mutated existing network, conditional on a path model that fits it less well. Study safeguards cost 0–0.91%. Across 44 preregistered perturbations the certified frequency plans keep their sign (−1.9% to −7.0%); when re-optimization may switch service off, the objective no longer identifies unserved demand. Two methodological lessons are likely to transfer: compare at matched convergence, not matched nominal effort; and a resource cap drawn from each candidate's own baseline ranks budgets, not designs (36.7% of pairwise orderings inverted).

### 3.2 Highlights (after the abstract; all ≤ 85 characters)

* Frequency reallocation cut modeled unserved demand 6.65% at fixed resources (76)
* Through-routing, added stops and greenfield redesigns gave little or no gain (76)
* The best greenfield network was 8.5–9.7% worse on the study objective (69)
* Matching solver convergence, not nominal effort, erased a 0.5% routing gain (74)
* Self-drawn resource caps inverted 36.7% of pairwise network rankings (68)

**Keywords:** transit network design; frequency setting; transit assignment; robustness analysis; computational experiments; Columbus, Ohio

### 3.3 New §3.0 "Problem statement" (insert at the top of §3)

> **Notation.**
>
> | symbol | meaning |
> |---|---|
> | k ∈ K | route-period with baseline service (N0: \|K\| = 173 of 39 × 6 = 234) |
> | h_k | headway (min); h_k^0 its baseline value |
> | L | headway ladder {5, 6, 7.5, 10, 12, 15, 20, 24, 30, 40, 45, 60} (`config/constraints.yaml`) |
> | (o,d) ∈ D | OD pairs, top 20,000; f_od their flow by period |
> | Π_od | ≤ 4 RAPTOR-enumerated paths, ≤ 2 transfers |
> | λ | weight on unserved demand; w_u = 60 min |
>
> **Decisions.**
>
> * Experiment 1: h_k ∈ L ∪ {h_k^0}, with h_k ≤ max(60, h_k^0). Baseline headways above 60 min are kept off-ladder (e.g. 65.45, 72, …, 240), and the 14 peak-only express routes are locked as a class.
> * Experiments 4–7: h_k ∈ L ∪ {OFF}, subject to the active policy constraints R1–R6 (`EXPERIMENT6_CONSTRAINT_CATALOG.md`).
>
> **Waiting.** Expected wait for effective headway H (`config/assumptions.yaml → waiting`):
>
> (1) w(H) = H/2 if H ≤ 12; w(H) = 6 + 0.25·(H − 12) if H > 12.
>
> A ride leg ℓ on pattern q of route-period k has effective headway H_ℓ = h_k · m_ℓ.
>
> * **Model A:** m_ℓ = n_dir(q)/n_pat(q).
> * **Model B:** m_ℓ = 1 / Σ_{q′ ∈ Q(ℓ)} n_pat(q′)/n_dir(q′), where Q(ℓ) is the set of patterns of the *same route* that serve ℓ's boarding stop and then its alighting stop in that period (2), and n_pat, n_dir are the period's trips on the pattern and in its direction. With |Q(ℓ)| = 1, Model B reduces to Model A.
>
> **Path and OD cost** (minutes; `config/cost_weights.yaml`):
>
> (3) c_π(h) = 2·walk + 1·IVT + 2·w(H_first) + Σ_transfers [2·w(H_ℓ) + 10].
>
> c_od(h) = min over π ∈ Π_od of c_π(h); c_od = ∞ if Π_od is empty.
>
> **Retention** (a discouragement proxy, not a mode-choice model):
>
> (4) r(c) = 1 for c ≤ 60; 1 − 0.9·(c − 60)/150 for 60 < c < 210; 0.10 for c ≥ 210.
>
> **Objective:**
>
> (5) min Z(h) = Σ_od f_od·r(c_od)·c_od + λ·w_u·U(h),
>
> where U(h) = Σ_{c_od < ∞} f_od·(1 − r(c_od)) + Σ_{c_od = ∞} f_od is unserved demand (discouraged + structural). Experiment 1 adds a crowding cost on in-vehicle time; Experiments 2–7 do not.
>
> **Resources.** With T_k the period length, N_k the number of directions, ρ_k the mean one-way runtime (min) and layover ratio 0.15 (assumed; `assumptions.yaml`):
>
> (6) RVH(h) = Σ_k N_k·T_k·ρ_k / (60·h_k) ≤ 2,517.18
>
> (7) Σ_{k ∈ p} C_k / h_k ≤ K_p for each period p, with C_k = 2·ρ_k·(1 + 0.15),
>
> K = (85.28, 162.01, 159.17, 176.49, 140.19, 35.56) from early through owl (EXP4N; Experiments 4N–7). In Experiment 1, K_p is the baseline plan's own proxy value. OFF route-periods contribute zero to (6) and (7).
>
> **Assignment, positioned.** Demand is assigned all-or-nothing to the cheapest enumerated path. That is neither frequency-based optimal-strategy (hyperpath) assignment (Spiess and Florian, 1989), nor cross-route common lines (Chriqui and Robillard, 1975), nor schedule-based assignment. Frequencies combine only across patterns of one route (Model B). Path diversity is limited by the number of pricing scenarios, at one path per scenario, so the four-path cap does not bind (Exp 4A, gate 4-9). The known consequences are no route-choice dispersion, no cross-route strategy (§3, §8), and results conditional on the enumerated path set (gate 4, D15).

*Implementer note:* (6) paraphrases `exp2.evaluate_array` (`trips = n_dir·T/h`; `vh = Σ trips·runtime/60`). Before finalizing, confirm the exact symbols against `src/cota_opt/exp2.py:126–133` and the frequency model, and adjust the notation without changing the substance.

### 3.4 New §8.0 "Threats to validity" (insert before the §8 table)

> **Internal validity (did the solver measure the model?).**
> * Heuristic and block-local optima: Gen1 in Experiments 1–3, the (8, 3)-block certifier in 4–7.
> * Start-basin dependence of 0.13–0.16% on N0/N3 and ≥ 1.70% on N4 (D39, Exp 6), with independent closures reaching up to 0.40% apart (§6.2).
> * A treatment-dependent start policy in Exp 2/2B and Exp 3 Phase A (D27).
> * Seed spread bounds solver variance, not solver error. D33's local differential-error check (≤ 0.0018 points) is a lower bound (D32–D33).
>
> **Construct validity (does the objective measure what the question asks?).**
> * The objective is not a welfare measure and can reward worse service (§3).
> * "Unserved demand" is a model construct: 33% of the NTD-anchored total is unserved at the current plan.
> * The proxy resource is not a vehicle count.
> * λ is a value judgement.
>
> **External validity (does it transfer?).**
> * One city and one representative weekday.
> * A commute-only spatial pattern.
> * Scheduled, not observed, service.
> * Uncalibrated weights and retention.
> * One candidate generator per lever (splices only in Exp 2; one greenfield generator in Exp 4).
>
> **Statistical-conclusion validity.**
> * "Certified" labels are seed-distinguishability or local-optimality statements at stated effort, not inference about the real system.
> * Exp 7 labels are descriptive across 44 levels (§6.0).
> * Several comparisons rest on two or three seeds; two of the three Exp 2B matched-start seeds are bit-identical.

### 3.5 New "Data and code availability" (insert before Appendix A)

> * **Code:** this repository (`cota_opt` package, scripts and configs). The research record is to be frozen at tag `research-final`, not yet cut (`docs/RELEASE_AND_REPORTING_GUIDELINES.md`). Earlier freeze tags, such as `exp3-final-v1`, exist in the project's local clone and are not yet published. No license file exists yet; Apache-2.0 for code and CC-BY-4.0 for documents are planned (guidelines §1).
> * **Data:** public, re-fetched by checksum through the registry (`config/sources.yaml`: SHA-256, retrieval timestamp, source record):
>   * COTA GTFS static feed `2026-MAY-04-BB_20260630`;
>   * LEHD LODES8 `oh_od_main_JT00_2022`, plus RAC/WAC;
>   * 2020 Census block-group population centroids;
>   * FTA NTD 2024 agency profile, agency 50016.
>
>   Raw data are not committed.
> * **Artifacts:** every number traces to a file under `outputs/` indexed by `outputs/CANONICAL_RESULTS_v5.json` (Appendix A). Superseded artifacts are indexed in `outputs/SUPERSEDED.md`.
> * **Reproduction:** `docs/REPRODUCE.md`. Runs were made in a two-core container. Per-experiment runtimes are in the closeouts. The one-command reproduction and the pinned environment are pending release work.

*Do not invent a URL or DOI.* Add them when they exist.

---

## 4. New errata and retraction rows

### 4.1 Append to `docs/EXPERIMENT7_CLOSEOUT_ERRATA.md`

First update the header's last sentence, appending: "Rows E16–E18 added 2026-10-04 from the first external referee review (`B1_COMMONLINES` waiting model; F2 provenance; F4 model conditions)." Then append:

| # | closeout location | as written | correction |
|---|---|---|---|
| E16 | §2 (Class B level), §8 third permitted claim, §9 prohibited claims; `EXP7_CLOSEOUT_TABLE.json → not_covered`; also `docs/EXPERIMENT7_PROTOCOL.md:61` and `docs/EXPERIMENT7_AMENDMENT.md:402, 627` (contract-listed, left unchanged) | Class B level `B1_COMMONLINES`, described as "common-lines assignment (cross-route waiting)"; "Class B untested" listed only for the jobs-accessibility objective | **Mislabel.** `B1_COMMONLINES` ran the retired Model A evaluator (`waiting_model: "pattern"`; Stage 1 `evaluator_checks.common_lines = "pattern"`, `common_lines_source = "explicit"`). It does not run cross-route common lines: `src/cota_opt` has no cross-route evaluator (`pathset.py:409–416`; `hyperpath.py` is a diagnostic bound). B1 raises modeled waits relative to BASE (N0 current-plan unserved 10,959.06 vs 10,423.68; GC per served trip 89.29 vs 86.26), whereas common lines would lower them. B1 is valid as a Model A vs Model B disagreement level (F1 −5.99%, F4 +7.86%) and is reported under that name. The as-issued Class B item "common-lines or hyperpath assignment" was **not implemented**. Per the amendment's claim bound ("F4 is conditional on the same-route waiting model unless the waiting model is a level"), F4, and likewise F1, F3, F6 and AF1, remain conditional on the same-route (Model B) waiting model. Add to §9: "Robustness to cross-route common-lines / optimal-strategy assignment (as-issued Class B; not implemented)". Add to `not_covered`: "Class B common-lines assignment: not implemented; `B1_COMMONLINES` is Model A". The upper bound on the omitted served-leg wait saving is 0.516% of GC (N0), 1.16% (N3) and 12.47% (N4) (`model_diagnostics_modelB.json`, `exp4_addendum/diag_N3.json`, `diag_N4.json`); retained-rider effects are unmeasured. |
| E17 | §4 F2 row ("certified 0.0065"); §6 F2 row; E11 ("expected of a 0.0065% effect") | F2 certified value 0.0065% | The 0.0065% is from the incumbent-start Exp 2B certification, stamped SUPERSEDED FOR QUANTITATIVE INTERPRETATION (`outputs/exp2b_certification.superseded.json`; D27). The current value under matched starts is **+0.0902% unserved, +0.0540% of the objective**, positive at every seed (two of three bit-identical), 0.31 of the 0.287-point floor; NULL verdict unchanged (`outputs/exp2b_certification.json → _confirmation`; D31). Stage 1's F2 rows evaluate the incumbent-start control plans (`EXP7_STAGE1_SOLUTIONS.json → F2_CONTROL_20260825/26/27`, source `outputs/exp2b_subsets.jsonl`, certified unserved 9,749.13 / 9,748.77 / 9,765.11) against one splice plan (`1c435b33f6dfa8d5`). Their labels are fixed-plan properties of those plans. The 0.287-point floor used by the F2 null test was measured from the same incumbent-start replicates (D24). Under matched starts the control spread is about 0.009 points (D32). Not re-run. |
| E18 | §8 third permitted claim | "The greenfield network N4 is worse than N3 and N0 at every λ ≥ 2 level in both stages." | Add the amendment's claim bounds, which were not discharged. The claim is conditional on (i) the same-route waiting model (E16) and (ii) the frozen path model, which fits N4 markedly worse (8.7–34.8% of flow improvable vs 1.0–3.7%; omission-corrected Δ43 +7.87%, not certified; registry `exp4a.caveats`). `X_ROUNDS4` and `X_TOPK40K` are additional levels and do not label findings. The size of F4 is closure-dependent: +9.66% (Exp 4A, single basin), +8.55% (Stage 2 BASE, `EXP7_ANALYSIS.json → f4`). |

### 4.2 Report §9 — new rows (and an update to R12)

* **R12 "now" cell.** "E1–E15" → "E1–E18".
* **R4 "now" cell.** As in M2 edit 6.
* **New rows:**

| # | claim withdrawn or amended | why | now |
|---|---|---|---|
| R13 | Exp 7 level B1 reported as "cross-route common lines" (§6) | The level ran Model A (`common_lines = "pattern"`); the as-issued common-lines/hyperpath assignment was never implemented | Relabelled "Model A waiting (model disagreement)"; cross-route common lines untested; findings conditional on Model B waiting (errata E16) |
| R14 | Exp 2B leader "+0.0065% unserved, 0.02 noise floors"; "all 240 combinations make up a certified null"; "the null holds at λ ∈ {1, 2, 4}" | The value came from an incumbent-start run superseded after D27. The 240-set sweep is discovery-stage (gate 12). λ = 1 and 4 have one seed and no floor | +0.090% unserved / +0.054% objective under matched starts, the leader worse than no edit, 0.31 floors (D31). Certified rows: six harmful, none beneficial, leader not better than no edit (errata E17) |
| R15 | Cross-route common-lines omission "bounded at 0.516%" and quoted for N0 only | 0.516% is an upper bound on served-leg wait savings (two periods, Exp 1 instance), not on the objective; F4 compares N4 with N3 | Quoted for N0, N3 and N4 (0.516%, 1.16%, 12.47%) with scope; retention effect unmeasured |
| R16 | "Frequency moves from the most frequent routes toward the 30–120-minute tier" (§5.1, D1) | Pre-Model-B evidence (D1, config C), never re-verified on the certified plans or checked for seed agreement | Withdrawn as a finding; mentioned only as a pre-Model-B observation |

---

## 5. Verifier claims to add (`scripts/verify_report_claims.py`)

Add an extractor `def c2b(): return J("outputs/exp2b_certification.json")["_confirmation"]` and the claims below. Each written string must appear verbatim in the listed documents after the edits.

```python
("+0.090%", 3, lambda: c2b()["matched_start_unserved_effect_pct"], [REPORT]),
("+0.054%", 3, lambda: c2b()["matched_start_objective_effect_pct"], [REPORT]),
("0.31", 2, lambda: c2b()["floors"], [REPORT]),
("−2.21%", 2, lambda: (lambda b, f: 100 * ((f["gc"] + 120 * f["unserved"]) - (b["baseline_gc"] + 120 * b["baseline_unserved"])) / (b["baseline_gc"] + 120 * b["baseline_unserved"]))(J("outputs/exp1_baseline_modelB.json"), next(r for r in exp1()["frontier"] if r["lambda"] == 2.0)), [REPORT]),
("66.8%", 1, lambda: 100 * J("outputs/exp1_baseline_modelB.json")["baseline_served"] / 30949, [REPORT]),
("+8.55%", 2, lambda: f4("BASE", "N3"), [CLOSE7, REPORT]),
("1.16%", 2, lambda: J("outputs/exp4_addendum/diag_N3.json")["common_lines_bound"]["bound_share_of_generalized_cost_pct"], [REPORT]),
("12.47%", 2, lambda: J("outputs/exp4_addendum/diag_N4.json")["common_lines_bound"]["bound_share_of_generalized_cost_pct"], [REPORT]),
("0.516%", 3, lambda: J("outputs/model_diagnostics_modelB.json")["hyperpath"]["bound_share_of_generalized_cost_pct"], [REPORT]),
("2,516.65", 2, lambda: next(r["revenue_veh_hours"] for r in exp1()["frontier"] if r["lambda"] == 2.0), [REPORT]),
("+15.31%", 2, lambda: next(r["unserved_change_pct"] for r in exp1()["frontier"] if r["lambda"] == 0.25), [REPORT]),
```

Notes on these claims:

* The `−2.21%` claim checks the λ = 2 frontier run (−2.213%). The three-seed linear mean (−2.208%) also rounds to −2.21.
* The "+8.55%" claim already exists for CLOSE7; extend its document list rather than duplicating the tuple.
* The verifier's rounding requires the written precision to match. With `"0.31"` at 2 decimals, `floors` = 0.314 rounds to 0.31 and passes.

The run must end at N/N.

---

## 6. Verified references (all checked by web search on 2026-10-04)

| # | Reference | Verified via | Status |
|---|---|---|---|
| 1 | Barr, R.S., Golden, B.L., Kelly, J.P., Resende, M.G.C., Stewart, W.R. (1995). Designing and reporting on computational experiments with heuristic methods. *Journal of Heuristics* 1, 9–32. | mauricio.resende.info abstract page | **Added** (not in the referee's list); issue number not independently confirmed |
| 2 | Cambridge Systematics, Inc. (2010). *Travel Model Validation and Reasonableness Checking Manual*, 2nd ed. Prepared for the Federal Highway Administration, Travel Model Improvement Program. September 24, 2010. | title page (snohomishcountywa.gov copy) | Verified. Omit any report number (not confirmed) |
| 3 | Cancela, H., Mauttone, A., Urquhart, M.E. (2015). Mathematical programming formulations for transit network design. *Transportation Research Part B: Methodological* 77, 17–37. doi:10.1016/j.trb.2015.03.006 | RePEc | Verified |
| 4 | Ceder, A., Wilson, N.H.M. (1986). Bus network design. *Transportation Research Part B: Methodological* 20(4), 331–344. | TRID 238094 | Verified (the referee had pages "as commonly cited"; now confirmed) |
| 5 | Chriqui, C., Robillard, P. (1975). Common bus lines. *Transportation Science* 9(2), 115–121. doi:10.1287/trsc.9.2.115 | RePEc | Verified |
| 6 | Durán-Micco, J., Vansteenwegen, P. (2022). A survey on the transit network design and frequency setting problem. *Public Transport* 14(1), 155–190. doi:10.1007/s12469-021-00284-y | RePEc | Verified |
| 7 | Furth, P.G., Wilson, N.H.M. (1981). Setting frequencies on bus routes: theory and practice. *Transportation Research Record* 818, 1–7. | TRID 174187 | Verified (the referee had pages UNVERIFIED; now confirmed) |
| 8 | Guihaire, V., Hao, J.-K. (2008). Transit network design and scheduling: A global review. *Transportation Research Part A: Policy and Practice* 42(10), 1251–1273. | RePEc | Verified. DOI not confirmed; omit it |
| 9 | Hooker, J.N. (1995). Testing heuristics: We have it all wrong. *Journal of Heuristics* 1(1), 33–42. doi:10.1007/BF02430363 | IAOR record; DOI from unpaywall link | Verified |
| 10 | Ibarra-Rojas, O.J., Delgado, F., Giesen, R., Muñoz, J.C. (2015). Planning, operation, and control of bus transport systems: A literature review. *Transportation Research Part B: Methodological* 77, 38–75. doi:10.1016/j.trb.2015.03.002 | RePEc | Verified |
| 11 | Lee, Y.-J., Vuchic, V.R. (2005). Transit network design with variable demand. *Journal of Transportation Engineering* 131(1), 1–10. doi:10.1061/(ASCE)0733-947X(2005)131:1(1) | ASCE Library | Verified |
| 12 | Mohring, H. (1972). Optimization and scale economies in urban bus transportation. *American Economic Review* 62(4), 591–604. | Wikipedia (Herbert Mohring) citation | Verified (secondary source; volume, issue and pages consistent across sources) |
| 13 | Rardin, R.L., Uzsoy, R. (2001). Experimental evaluation of heuristic optimization algorithms: A tutorial. *Journal of Heuristics* 7(3), 261–304. | IAOR | Verified. DOI not confirmed; omit it |
| 14 | Spiess, H., Florian, M. (1989). Optimal strategies: A new assignment model for transit networks. *Transportation Research Part B: Methodological* 23(2), 83–102. | RePEc | Verified. DOI not confirmed; omit it |
| 15 | Walker, J. (2008). Purpose-driven public transport: creating a clear conversation about public transport goals. *Journal of Transport Geography* 16(6), 436–442. doi:10.1016/j.jtrangeo.2008.06.005 | RePEc | Verified |

**Dropped:** none of the referee's 14. One caveat applies to Lee and Vuchic (2005): cite it only for variable-demand network design. The referee's implication that it uses a welfare objective was not verified.

---

## 7. Issues the referee missed

1. **Exp 6 closeout misattribution.** `EXPERIMENT6_CLOSEOUT.md:139` says "the added stop lengthens route 001". The edit is on route **010**; route 001 is the route trimmed. The closeout is registered, so the report states only the trim (M6). Note it for a future errata to Exp 6, if one is opened.
2. **Model A figures on disk.** `outputs/figures/*.svg` exist but are drawn mostly from the Model A `fixpoint.jsonl` (`scripts/make_figures.py:306`). They must not be embedded (M15).
3. **The "B1" name collision.** The Exp 7 Class B level and the Exp 6 safeguard bundle B1 (R2 s = 0.10 + R3 + R6) share the name; the Glossary defines only the bundle. Always write `B1_COMMONLINES` for the level.
4. **The 0.516% N0 figure** covers only am_peak and midday in the Exp 1 instance. N3 and N4 come from the Exp 4A instance, so the three are not on a common basis (M1, M5).
5. **Exp 4A's counterpoint to M5(c).** Crediting all of N4's common-lines bound still does not close Δ43 (93,300 < 226,948 < 283,973).
6. **OFF-permitting instances are dominated by structural unserved demand.** In Exp 4A N3 serves 53.1% and N4 36.3% of demand; 35.5% and 54.7% of all demand has no path (`diag_N3/N4.json → totals`). This belongs next to M4 and M5.
7. **Two seeds of three are identical in the Exp 2B matched-start confirmation**, in both arms.
8. **Exp 2 singles used incumbent starts as well** (D27: `exp2_treatments_full` 72/72). At certification effort the control start gap was 0.008% of the objective, so the harm verdicts stand, but the +0.060 and +0.160 magnitudes carry the caveat (M2 edit 3).
9. **D2** ("returns plateau quickly", §5.1) has the same pre-Model-B provenance problem as D1 (M12b).
10. **Errata E11 and two documents propagate the superseded value.** E11's "expected of a 0.0065% effect" and the same phrase in `README.md:306` and `docs/EXPERIMENT7_RESULTS.md:64` propagate it (E17, M2 edit 10).
11. **The verifier has no 2B headline claim.** The referee's statement that it checks one against the stale registry is inaccurate.
12. **`resources.weekday_revenue_veh_hours_optimized = 2516.5`** in `exp1_final.json` does not correspond to the λ = 2 frontier run (2,516.645) and has no plan identifier (M16a).
13. **R1_H60 is the closest cell to Exp 1's rules, not identical to them.** The no-OFF and ≤ 60-minute conditions match, but the Exp 1 off-ladder and express-lock treatment within the Exp 6 instance is not asserted by the artifact. The report says "under Experiment 1's rules" in §6.2, §11 and the abstract; change it to "the closest cell to Experiment 1's rules (R1_H60)" (M13e).

---

## 8. Ordered implementation plan

1. **Errata first** (they are cited by everything else). Append E16–E18 to `docs/EXPERIMENT7_CLOSEOUT_ERRATA.md` and update its header (§4.1).
2. **`outputs/SUPERSEDED.md`.** Append the exp2b block (M2 edit 11).
3. **Report: correctness edits.**
   * M1 edits 1–3 (B1 relabel, §3, §8).
   * M2 edits 2–8.
   * M5 edits 2–4 and 6.
   * M6 edits 2–4.
   * M16.
   * M17.
   * §9 rows R13–R16 and the R4/R12 updates.
4. **Report: framing edits.**
   * M3: §3 paragraph, §5.1 objective row, the all-levers table, §8 λ wording, Glossary.
   * M4: status box, §5.1, §8 row, Glossary.
   * M11.
   * M12.
   * M13.
5. **Report: new sections.**
   * §1.1 Related work and References (M9, §6).
   * §3.0 Problem statement (§3.3; confirm the RVH notation against `exp2.py`).
   * §4.1 Model instances (M7).
   * §8.0 Threats to validity (§3.4).
   * Data and code availability (§3.5).
   * Glossary terms (M8, m8).
6. **Report: abstract and front matter.**
   * New abstract (§3.1); check ≤ 250 words with `wc -w`.
   * Highlights and keywords.
   * Summary-of-findings table in §1 (M14).
   * Scope sentence on transfer timing and stop consolidation.
   * Status-of-draft box (M15 edit 4).
   * Title (optional).
7. **Report: minor comments** m1–m32 per §2.
8. **Other documents.**
   * `README.md`: lines 279, 306, 355.
   * `docs/EXPERIMENT7_RESULTS.md`: lines 64, 120.
   * `docs/FUTURE_EXPERIMENTS.md:255`.
9. **Verifier.** Add the §5 claims; run `python scripts/verify_report_claims.py` until it reports N/N; fix any missing-string failures by aligning the report text, never the extractor.
10. **Final consistency greps.** Each search should return only intentional matches:

    | search | intended matches only |
    |---|---|
    | `0.0065` | superseded mentions labelled as such |
    | `certified null` | none |
    | `bounded at 0.516` | none |
    | `cross-route common lines (Class B)` | none |
    | `zero point` | config-name mentions |
    | `generalize beyond` | none |
    | `trivially parallel` | none |
    | `Re-timing` | none |

    Then confirm that the registered documents, `EXPERIMENT7_CLOSEOUT.md`, the contract-listed protocol documents, `outputs/**/*.json` and `src/` are byte-unchanged (`git diff --stat`).
