# Referee report

**Manuscript:** "How much can frequency, stops and geometry do for a mid-sized bus network? A certified-optimization study of the Central Ohio Transit Authority (COTA)". Technical report, draft of 2026-10-04 (`docs/report/TECHNICAL_REPORT.md`, 830 lines).

**Reviewed against:** the repository at `/home/claude/columbus-transit-opt` (HEAD `189dfa64`), the canonical JSON artifacts under `outputs/`, the per-experiment closeouts, `DISCOVERIES.md`, `config/*.yaml`, `src/cota_opt`, and the project's binding reporting standard `docs/RELEASE_AND_REPORTING_GUIDELINES.md`. I ran `python scripts/verify_report_claims.py`; it reports 39/39. I also spot-checked about 120 further numbers by hand (Section 5).

**Venue standard assumed:** Transportation Research Part A/B/C, Transportation Science, Public Transport, or TRR.

---

## 1. Summary of the submission

The manuscript reports seven sequential computational experiments on a model of COTA's weekday bus network. The model is built from public data: GTFS static schedules, LEHD LODES 2022 home–work flows rescaled to an NTD-derived total of 30,949 weekday linked trips, and NTD system totals. The model has five main parts:

- **Decisions.** One headway per route-period (173 route-periods on 39 routes), chosen from a discrete ladder.
- **Assignment.** Paths are enumerated by RAPTOR, at most four per origin–destination (OD) pair and period. Demand is assigned all-or-nothing to the cheapest enumerated path.
- **Waiting.** Model B prices a ride leg on the combined frequency of all same-route patterns that serve the movement.
- **Demand loss.** A retention curve on generalized cost (GC) discards part of the demand. The discarded part is called "unserved".
- **Objective.** GC of served trips + λ·60·(unserved trips), minimized subject to a revenue-vehicle-hour cap and six per-period caps on a cycle/headway "peak-concurrency proxy".

The authors claim:

1. **Frequency redistribution (Exp 1).** Inside existing routes and resources it is the only lever with a material effect: −6.65% modeled unserved demand at λ = 2, with total GC up 0.88%.
2. **Through-routing splices (Exp 2/2B).** A "certified null" across all 240 feasible combinations of 12 candidates.
3. **Route mutation (Exp 3).** 29 certified improvements of −0.01% to −0.19% of the objective, led by an added stop on route 010.
4. **Greenfield design (Exp 4/4N/4A).** The best of 200 promoted candidates is 9.66% worse than the Exp 3 redesign.
5. **Resource frontier and safeguard prices (Exp 5, Exp 6).** Exp 5 failed its monotonicity gate. Study "safeguards" cost 0–0.91% of the objective.
6. **Robustness (Exp 7).** A two-stage experiment shows that F1 keeps its sign for fixed plans. When service may be switched off, the objective no longer identifies unserved demand, and at λ = 1 the optimizer nearly empties the network.
7. **Methodological lessons.** Match convergence, not nominal effort. Do not let candidates draw their own budgets. Recognize start-basin dependence. Match decision spaces. Do not trust a constraint that is hashed but never scored.

The main contribution is an unusually candid account of how an optimization harness can mislead itself, built on a case study. It includes preregistration, a "semantic comparison firewall", a retractions table, and errata.

## 2. Overall assessment and recommendation

**Recommendation: Major revision.** In its current form I would not support acceptance at TR-A/B/C, Transportation Science or Public Transport. The work could become a solid TRR or Public Transport paper, and potentially a TR-A methods paper, after revision.

**Strengths:**

- The project's self-auditing culture is rare and valuable: the retractions table, errata, the firewall concept, and the open reporting of a failed gate (Exp 5).
- Most transcribed numbers match their artifacts. Of the roughly 160 numbers I checked, the large majority match to the stated precision.

**Problems.** The manuscript has several defects that a referee must treat as disqualifying until fixed:

1. **A mislabelled sensitivity level (CRITICAL).** The Exp 7 "cross-route common lines" level (B1) actually ran the retired Model A ("pattern") waiting model. Model A is more pessimistic about waiting than Model B, which is the opposite direction from common lines. This is the exact class of error the paper lists as methodological finding 4.
2. **A superseded number presented as current (CRITICAL).** The splice-null effect +0.0065% comes from an artifact the project itself stamped "SUPERSEDED FOR QUANTITATIVE INTERPRETATION". The matched-start value is +0.0902% unserved. The "certified null of all 240 combinations" also overstates what was certified.
3. **An objective that is not a welfare measure, and a headline on a different metric than the other levers (CRITICAL).** The objective can fall when service gets worse for high-cost trips. The headline (−6.65%) is in unserved demand, while every other lever is reported in % of the objective. So "the only lever that produced a material improvement" compares unlike quantities.
4. **A baseline that contradicts its own anchor (CRITICAL).** Demand is scaled to 30,949 linked trips that NTD says are actually made. Yet the model leaves 10,262 of them (33%) "unserved" under the current timetable. The status box nonetheless reports every validation dimension as "unavailable".
5. **The greenfield conclusion is stronger than the evidence (CRITICAL).** The headline +9.66% is a single-basin value; closure-corrected values for the same comparison are +9.28% (Exp 6) and +8.55% (Exp 7 Stage 2 BASE). The paper also omits caveats the registry attaches to it: the path model fits N4 much worse, and the comparison quotes N0's common-lines figure instead of N3's.

**Missing standard elements.** There is no literature review, no formal problem statement, no description of the waiting-time function, no positioning of the assignment model against frequency-based and common-lines assignment, no threats-to-validity section, no data-availability statement, and no figures. The abstract is 530 words against a typical 250-word limit.

None of this requires new experiments. Every fix below is textual, a re-statement of existing artifacts, or a limitation to declare.

**Counts by severity:** 6 CRITICAL, 11 IMPORTANT, 32 MINOR (m1–m32).

---

## 3. Major comments

### M1 — CRITICAL. The "cross-route common lines" sensitivity level (B1) actually ran Model A, not common lines

**Location:** §6, "Class B and additional levels" table (lines 504–511): "B1 cross-route common lines (Class B) | −5.99% | +7.86%". Also §3, "Cross-route common lines are not modeled" (line 187), and §8, row "Cross-route common lines".

**Problem.** The level is defined with `waiting_model: "pattern"` (`outputs/exp7/EXP7_LEVELS.json`, level `B1_COMMONLINES`; the Stage 1 record `outputs/exp7/stage1/evals/N0/B1_COMMONLINES.json` has `evaluator_checks.common_lines = "pattern"`, `common_lines_source = "explicit"`).

In this code base, `"pattern"` is **Model A**:

- `config/assumptions.yaml`, `path_assignment.common_lines`: "`pattern` Model A: the chosen pattern's own headway".
- `src/cota_opt/pathset.py:413`: the combined-frequency multiplier is applied only when `common_lines == "same_route"`; otherwise `mult_b = mult_a`.

Model A *undervalues* frequent trunk service (§3, D10). Cross-route common lines (Chriqui and Robillard, 1975; Spiess and Florian, 1989) would *reduce* modeled waits relative to Model B. B1 therefore perturbs waiting in the opposite direction from the one claimed.

The as-issued protocol asked for "Common-lines or hyperpath assignment, addressing the cross-route waiting issue" (`docs/EXPERIMENT7_PROTOCOL_AS_ISSUED.md`, Class B). That test was not run. The consolidated protocol (`docs/EXPERIMENT7_PROTOCOL.md:61`) carries the same mislabel ("Common-lines (`pattern`) waiting").

The near-coincidence of B1's F4 (+7.86%) with Exp 4A's omission-corrected Δ43 (+7.87%) makes the mislabel easy to miss. Those two figures measure different things.

**Fix:**

1. Relabel the row "B1 Model A (pattern-headway) waiting; *not* cross-route common lines".
2. Add to §6: "The protocol's Class B common-lines/hyperpath assignment was not implemented. The level named `B1_COMMONLINES` ran the retired Model A evaluator (`common_lines = "pattern"`), so it measures Model A vs Model B disagreement. It does not measure the cross-route waiting omission."
3. Add to §9: "R13 | Exp 7 B1 described as common-lines assignment | the level ran Model A | relabelled; common-lines sensitivity not tested".
4. In §8, state that the cross-route omission (0.516% of GC on N0, 1.16% on N3, 12.47% on N4) was not tested by any Exp 7 level.
5. Correct the protocol consolidated view.

### M2 — CRITICAL. The Exp 2B null is quoted from a superseded artifact, and its scope is overstated

**Locations:**

- Abstract, "All 240 feasible combinations of 12 candidates make up a certified null".
- §5.2: "scores +0.0065% unserved, 0.02 noise floors"; "The null holds at λ ∈ {1, 2, 4}".
- §6.1, F2 row: "certified +0.0065%".
- Appendix A.

**Problems.**

**(a) The headline magnitude is superseded.** `outputs/exp2b_certification.superseded.json` carries `_superseded`: "SUPERSEDED FOR QUANTITATIVE INTERPRETATION — produced with starts='incumbent' … the treatment silently fell back to a greedy build (D27) … The per-quantity magnitudes here are not comparable across arms."

The canonical `outputs/exp2b_certification.json → _confirmation` gives the matched-start result:

- `matched_start_unserved_effect_pct = 0.0902`;
- `matched_start_objective_effect_pct = 0.0540`;
- `floors = 0.314`.

D31 (`DISCOVERIES.md:1763`) says the same. The report therefore quotes the D27-contaminated number, which its own methodological finding 3 says is invalid. (The registry headline `CANONICAL_RESULTS_v5.json → experiments.exp2b.headline` and `EXPERIMENT2_CLOSEOUT.md` are also stale. The verifier checks against the stale registry, so it cannot catch this.)

**(b) "All 240 … make up a certified null" overstates what was certified.** `EXPERIMENT2_CLOSEOUT.md` (table after "What that means for COTA") marks only these rows as certified:

- "six candidates measurably harmful";
- "no candidate measurably beneficial";
- "the leader is null at full effort".

"No multi-edit set beats the best single" and "every multi-edit set substitutes" are "discovery-stage (gate 12)" at 60,000/2/32. Gate 12 fired on this very experiment: the effect moved 0.591 points between discovery and certification effort.

**(c) "The null holds at λ ∈ {1, 2, 4}" contradicts the registry's own limitation.** `CANONICAL_RESULTS_v5.json → experiments.exp2b.limitations` states: "λ=1 and λ=4 ran one seed each, so no noise floor exists at those weights and no headline may be drawn from them". The closeout grades "the leader is the same at λ ∈ {1,2,4}" as "discovery-stage, single seed". The registry headline states only that "best-set identity and cardinality monotonicity hold" at those λ. That is not the same as "the null holds".

**(d) The 0.287-point floor was measured on the contaminated pipeline.** Its replicates (9,749.1–9,765.1) come from the `starts='incumbent'` run. D32 states that floors measured on that path "should not be carried forward". Under matched starts the certification-effort seed spread is 3σ = 0.00657% of the objective (D32). The matched-start effect (+0.054% of objective, positive at every seed) is then larger than solver variance, though D33 notes that variance does not bound error. On the corrected pipeline the honest reading is "no gain; the leader is slightly worse than doing nothing", not "a null of size 0.0065%".

**Fix:**

1. Abstract: "Route-geometry recombination (through-routing): no supportable gain. Of 12 splice candidates, six do measurable harm and none measurable good at certification effort. The best splice, re-solved under matched starts, is +0.09% unserved (worse than no edit at every seed), inside the Exp 2B floor. An exhaustive discovery-stage sweep of all 240 feasible combinations found none better than the best single."
2. Replace +0.0065% everywhere with +0.0902% unserved / +0.054% objective, citing `exp2b_certification.json → _confirmation`, and footnote the superseded value.
3. Delete "The null holds at λ ∈ {1, 2, 4}", or replace it with "At λ = 1 and 4 (one seed, discovery effort, no floor) the same single edit leads and no multi-edit set beats it."
4. State that the 0.287-point floor was measured under the superseded start policy.
5. Add a verifier claim tied to `_confirmation`.
6. Disclose in §6.1 that Exp 7's F2 rows evaluate the contaminated-start plan pair.

### M3 — CRITICAL. The objective is not a passenger-welfare measure, and the lever comparison uses incommensurable metrics

**Locations:**

- Abstract, first paragraph ("how much passenger generalized travel cost COTA could save") and first Results bullet.
- §3, "Objective".
- §6.2.
- §11.

**Problems.**

**(a) The objective can fall when service gets worse.** Per OD, the objective is f·[r(c)·c + (1 − r(c))·λ·60]. Here r(·) is the retention curve: 1 up to 60 min, falling linearly to 0.10 at 210 min (`src/cota_opt/pathset.py`, `PathSetEvaluator.evaluate`).

Since r′(c) < 0 on (60, 210), the derivative r(c) + r′(c)(c − λ·60) can be negative whenever c > λ·60. So for any OD whose cost exceeds λ·60, making its service *worse* can *lower* the objective. This is not only a λ = 1 boundary pathology discovered in Exp 7. It is a structural property of the objective at λ = 2 for every trip above 120 GC-minutes, in every experiment. The paper treats it as an Exp 7 finding (§6.2) and a post hoc limitation (§8). It should be front and centre in §3.

**(b) The metric used is non-standard.** Standard practice with elastic demand uses consumer surplus or welfare (e.g. a rule-of-half or logsum change), which is monotone in level of service; see Lee and Vuchic (2005) on variable demand in transit network design. The manuscript should say explicitly that its objective is not a welfare measure and explain why it was chosen.

**(c) The headline does not answer the question posed.** The abstract asks how much GC could be *saved*, but the headline result *raises* total GC (+0.88%) and is reported in unserved demand. The Exp 1 change in the objective that was actually optimized is never reported. From `outputs/canonical/exp1_final.json`, I compute it for the λ = 2 frontier run as follows:

| plan | GC | unserved | objective (GC + 120·unserved) |
|---|---|---|---|
| baseline | 1,772,726.89 | 10,261.92 | 3,004,156.95 |
| λ = 2 frontier plan | 1,787,699.00 | 9,583.06 | 2,937,665.70 |

The change is **−2.21% of the objective** (single frontier run).

**(d) The lever comparison mixes metrics.** F1 is in % of unserved demand. F2 is in % of unserved demand, against a floor in points. F3, F4 and F6 are in % of the objective. "Frequency redistribution is the only lever that produced a material improvement" therefore compares −6.65% (unserved) with −0.19% (objective). On a common metric the ordering probably survives (≈ −2.2% vs −0.19%), but the reader cannot verify that from the paper.

**(e) "λ is a policy choice, not calibratable" is too strong (§8).** λ·60 is the implied value of a lost trip. Under the paper's own retention curve, a discouraged trip's lost surplus is bounded by the curve, so λ is constrained by the demand model even if not by data.

**Fix:**

1. §3: add a paragraph headed "The objective is not a welfare measure". State the per-OD form above and the non-monotonicity condition c > λ·60. Note that at λ = 2 it applies to every OD above 120 min, and report the served-flow share above 120 min at baseline (computable from existing evaluations).
2. Abstract: replace "how much passenger generalized travel cost COTA could save" with "how much a λ-weighted sum of passenger generalized cost and unserved demand could be reduced".
3. Report F1 also as % change of the objective, with the artifact path. Present one table comparing all levers in % of the λ = 2 objective under a named model instance.
4. Soften §8 to "λ is a value judgement constrained by, but not determined from, the retention curve".

### M4 — CRITICAL. The baseline contradicts the data used to scale it, and the validation status is presented misleadingly

**Locations:** Model status box ("Validation … all four `unavailable`"; "Demand … Non-work travel is absent"); §2; §5.1; Glossary, "Unserved demand".

**Problems.**

**(a) A third of observed trips are "unserved" at the current plan.** The total 30,949 is derived from NTD: 38,694 average weekday unlinked trips × 95.98% bus share ÷ 1.20 (`config/assumptions.yaml → demand_proxy.assumed_weekday_linked_trips`). These are trips COTA riders *actually make* on the current timetable. Yet the model's baseline leaves 10,261.9 of them unserved (33.2%) and serves 20,687.1 (`outputs/exp1_baseline_modelB.json → baseline_unserved`, `baseline_served`). The Exp 6 instance leaves 10,423.7 unserved (`EXP7_ANALYSIS.json → f1_adaptive[BASE].current_plan_unserved`).

**(b) An aggregate validation check is available and fails.** The model fails to reproduce the observed system total it was anchored to by about a third. "Unserved demand", the headline metric, is therefore dominated by model structure: the retention curve, the 600 m access radius, the four-path cap, and the top-20,000 truncation. Under A6_MAXWALK75 alone the current plan serves only 14,301 (`EXP7_F1_DECISION_SPACE.json → rows[A6_MAXWALK75].current_plan_unserved` = 16,648.3). The −6.65% applies to this model quantity, not to riders. The headline "about 680 more of 30,949 modeled weekday trips served" invites the reading that 680 more real riders would travel, while the model already "loses" 10,000 trips that NTD says exist.

**(c) The status box mischaracterizes demand.** Non-work travel is not "absent": its *volume* is inside the NTD-anchored total. What is absent is its *spatial pattern*, because all volume is distributed on commute OD pairs.

**(d) The structural/discouraged split is not reported.** `PathSetEvaluator.evaluate` already reports unserved demand as `unserved_structural` (no path) and `unserved_discouraged` (retention), but the paper never gives the split.

**Fix:**

1. Change the validation row to: "Validation. One system-level check is possible: the model's baseline serves 20,687 of the 30,949 NTD-derived weekday linked trips it is scaled to (66.8%). The 33.2% 'unserved' at the current timetable is a property of the model (retention curve, access radius, path enumeration), not of observed ridership. Route volume, stop pattern, transfer behaviour and trip length: unavailable."
2. Report the structural/discouraged split of baseline unserved demand from the existing baseline evaluation.
3. Change the demand row to "Commute spatial pattern only. All 30,949 NTD-derived weekday linked trips (which include non-work trips) are distributed over LODES commute OD pairs."
4. Rephrase the Exp 1 headline as "a 6.65% reduction in modeled unserved demand (a model quantity; at baseline the model leaves 33% of the NTD-anchored demand unserved)".
5. Add to §8 a row "Baseline reproduction of NTD total | 66.8% | Unserved-demand changes are changes in a model construct."

### M5 — CRITICAL. The greenfield conclusion is overstated, and the registry's mandatory caveats are omitted

**Locations:**

- Abstract, "Greenfield network design: the best of 200 candidates is worse … +9.66%".
- §5.4.
- §6.1, F4 row.
- §11: "the best greenfield design did worse".

**Problems.**

**(a) The same comparison at the same assumptions has three values, and only the largest is reported.** The values are:

- +9.66%: single-basin N3 (`DELTA43.json`);
- +9.28% of N3: N4 against Exp 6's *closed* N3 REF (`EXPERIMENT6_CLOSEOUT.md`, about line 400: "N4 − N3 closed REF = +272,400.39 (+9.28% of N3)");
- +8.55%: Exp 7 Stage 2 BASE, closure on both sides (`EXP7_ANALYSIS.json → f4[BASE, N3→N4].delta_pct` = 8.547).

The spread (1.1 points) is basin dependence. §5.4 reports none of it.

**(b) The path model fits N4 much worse, which biases against N4.** The registry caveat `CANONICAL_RESULTS_v5.json → experiments.exp4a.caveats[0]` reads "conditional on the frozen path model, which fits N4 markedly worse (8.7–34.8% of flow improvable vs 1.0–3.7%)". `EXPERIMENT4_ORIGINAL_QUESTION_ADDENDUM.md` §5 adds that flow-weighted cost overstatement is 0.9–5.5% on N4 vs 0.04–0.43% on N3. The omission-corrected +7.87% is "not certified" (same file); §5.4 omits that qualifier. For scale, Exp 1's own path-set adequacy line was 0.67% improvable flow (`exp1_baseline_modelB.json → gate4_line_pct`).

**(c) The common-lines exposure is quoted for the wrong network.** §3 and §8 quote 0.516% for N0, but F4 is N4 − N3, and N3's measured exposure is **1.16%** (same addendum, gate 4-10 table). The addendum says the measure "is not measured, and it is not excluded" as a bound on the GC effect. Calling it "bounded at 0.516%" (§3) misstates it.

**(d) A common proxy envelope is not a common resource.** The proxy Σ cycle/headway ignores interlining. N0's interlining factor is 197/176.49 ≈ 1.12, and N4's is unknown. Equal proxy budgets may correspond to unequal fleets, in either direction. §3 states that the proxy is not a fleet count but does not draw the consequence for F4.

**(e) "Best of 200" is not identified.** The EXP4N first-to-second margin is 0.387%, while the N4 start-basin residual is at least 1.70% (Exp 5; §5.5 itself says "4.4×"). The registry limitation reads: "the first-to-second margin is not established, only not excluded". The promotion cap was invalid (§5.4), and nothing is known about the 1,800 excluded proposals (registry limitations).

**(f) The conclusion generalizes beyond the evidence.** "The best greenfield design did worse" generalizes from one generator's promoted proposals to greenfield design in general.

**Fix:**

1. Abstract: "Greenfield network design: the leading proposal of 200 certified under a common proxy envelope (leader not distinguishable from runners-up given start-basin residuals) is worse than the Exp 3 redesign by 8.5–9.7% of the objective depending on basin closure (Exp 4A single basin +9.66%; Exp 6 closed reference +9.28%; Exp 7 Stage 2 BASE +8.55%). The path model fits N4 markedly worse than N3 (8.7–34.8% vs 1.0–3.7% of flow improvable), which biases this comparison against N4."
2. §11: "the best greenfield proposal we generated did worse".
3. In §3 and §8, quote common-lines exposure for N0, N3 and N4 (0.516%, 1.16%, 12.47%), and replace "bounded at" with "estimated at (wait saving on served legs only)".
4. Add the proxy-not-fleet consequence to §5.4.

### M6 — CRITICAL. The Exp 3 leader is quoted without its mandatory effort-regime caveat, and the model favours add-stop edits

**Locations:** Abstract (Mutation bullet); §5.3; §6.1, F3 row; §11 ("editing them did almost nothing").

**Problems.**

**(a) The registry orders the caveat quoted with the headline.** `CANONICAL_RESULTS_v5.json → experiments.exp3.regime_caveat` ends "Quote this with the headline." Its content is as follows. The leader was never solved above 20 restarts. All 28 of its pairwise comparisons are at 20 restarts. The best margin confirmed at 40 restarts is 2.33× smaller. The remedy (Phase 5b) was abandoned with zero cells (`EXPERIMENT3_CLOSURE.md` §7). §5.3 mentions the regime split but presents "distinguishable from all 28 other certified candidates" without the qualifier, and the abstract omits it entirely.

**(b) This contradicts the paper's own lesson.** Methodological finding 2 says matched convergence is necessary, yet the leader leads "on the softer measurement" (closure §7).

**(c) Stop service has no runtime cost in the model.** The cost of serving a stop is "unmeasurable from this feed (−157 s/stop)" (§8), and stop edits carry no dwell, deceleration or acceleration penalty (`src/cota_opt/stopedits.py` header; `EXPERIMENT3_CONTRACT.md` §4). That is a bias *in favour of* add-stop edits: the model credits the coverage gain and charges only detour distance. §8 frames the limitation only as blocking consolidation claims. The direction for F3 is the opposite and should be stated.

**(d) N3's base plan had to be trimmed to fit the envelope.** `EXPERIMENT6_CLOSEOUT.md` notes: "N3's own baseline plan overruns the envelope, so route 001 is trimmed in 5 periods (e.g. am_peak 15 → 20 min) to form the base". Readers of the AF1 and F3 comparisons need this.

**Fix:**

1. Abstract: "…the certified leader adds a stop on route 010 (−0.19%). It was measured at 20 restarts while 23 of the 29 were escalated to 40, and its effect is within its own Exp 7 sensitivity range."
2. §5.3: quote the registry caveat verbatim.
3. §8, "Stop cost" row: "Direction: stop service has zero runtime cost in the model, which favours add-stop edits (including F3). No consolidation claim on runtime savings."
4. Mention the N3 base-plan trim in §5.3 or §5.6.

### M7 — IMPORTANT. Cross-experiment confounds: findings come from different model instances, solvers, decision spaces and noise floors, but are compared as if from one model

**Locations:** Abstract and §11 ("Recombining routes did nothing, editing them did almost nothing, and the best greenfield design did worse"); §1 table; §6.1 note (lines 539–541).

**Problem.** The experiments differ in many ways that affect the cross-lever comparison:

| | Exp 1 | Exp 2/2B | Exp 3 | Exp 4N/4A/5/6/7 |
|---|---|---|---|---|
| solver | Gen1, 400k×20, 3 seeds | Gen1 (discovery 60k/2/32; cert 400k/20) | Gen1, 20/40 restarts, 5 seeds | (8, 3)-block certifier, 120 rounds, one start + closure |
| decision space | no OFF, max(60, baseline), express lock | no OFF | no OFF | `allow_off=True` (except R1/R3 cells) |
| crowding | on | ? | off (`exp3_score.py:299`) | off |
| path set | frozen 243,257 paths, widened to pass gate 4 | per-network | per-network | per-candidate, not tested against Exp 1's 0.67% line (N3: 1.0–3.7% improvable) |
| reported metric | % unserved | % unserved vs 0.287-pt floor | % objective, ratio > 3 | % objective |
| start policy | incumbent | incumbent (contaminated, D27) → matched | "both" | greedy + anchors |

Two consequences follow:

- **Model instance alone moves F1 by 0.63 points.** F1 is −6.65% in the Exp 1 instance and −6.02% in the Exp 6 instance at BASE (closeout §4.1). That gap is larger than the Exp 7 movements in A1 and A2 (Highly stable) and comparable to the A3/A5 movements.
- **Detection power differs by more than an order of magnitude.** Exp 2's null rests on a floor of 0.287 points of unserved demand. Exp 3 certifies effects of 0.0096–0.19% of the objective. "Did nothing" versus "almost nothing" partly reflects different power, not different levers.

**Fix:** Add a table like the one above as §4.1, "Model instances and their differences". Add a sentence after it: "Comparisons between levers are qualitative. The experiments differ in solver, decision space, crowding, path set, start policy, metric and noise floor, and the Exp 2 null has a minimum detectable effect (0.287 points of unserved demand) larger than every certified Exp 3 effect." Report the instance-induced F1 difference (−6.65% vs −6.02%) as a separate sensitivity in §6.1.

### M8 — IMPORTANT. "Certified" carries at least three meanings, and the Glossary definition fits none of them exactly

**Locations:** Title; §5 preamble (line 292); Glossary "Certified"; §1 table; abstract ("certified null"); §6.0 ("certified … fixed point").

**Problem.** The word is used for different things:

- **Exp 1:** λ ≥ 2 is "certified" by the path-set adequacy gate, with improvable flow under a 0.67% line (D15).
- **Exp 3:** |mean Δ|/SD > 3 over seeds.
- **Exp 4–7:** "certified" means converged (8, 3)-block-local optimality. That is a local-optimality certificate, not "distinguishable from solver variance".
- **Exp 2B:** "certified null". By the Glossary's own definition ("distinguishable from solver variance") a null cannot be certified.
- **Exp 6:** `EXP6_POLICY_FRONTIER_CERTIFIED` labels an experiment-level gate status.

In OR, "certified" usually suggests an optimality or bound certificate, so the title invites a misreading that the guidelines (done-criterion 4) explicitly aim to prevent.

**Fix:** Define three terms in §4 and the Glossary and use them consistently:

- "path-set adequate (Exp 1 gate 4)";
- "seed-distinguishable (|mean Δ|/SD > 3 at stated effort)";
- "block-local certified ((8, 3)-block-local optimum, converged)".

Replace "certified null" with "not distinguishable from zero at certification effort". Retitle, e.g. "…A convergence-controlled optimization study…".

### M9 — IMPORTANT. No related-work section; the work is not positioned in the literature

**Location:** Entire manuscript. There is no reference list at all.

**Problem.** A journal submission must position itself against the literature on the transit network design problem (TNDP), joint design and frequency setting (TNDFSP), and frequency setting; against transit assignment models; and against experimental-methodology work on heuristics. Several "methodological findings" (§7) are established cautions in the heuristics-testing literature: compare at matched convergence, not nominal effort; normalize budgets. Finding 1 (route-level vs path-level scoring) is the standard argument for assignment-based evaluation. D1 invokes "the square-root rule" without citation.

**Fix:** Add §1.1, "Related work". I verified that the following exist; bibliographic details below are as verified or as commonly cited, and the full list is also in §6 at the end of this report:

- **TNDP/TNDFSP surveys:**
  - Guihaire, V., Hao, J.-K. (2008). Transit network design and scheduling: A global review. *Transportation Research Part A* 42(10), 1251–1273.
  - Ibarra-Rojas, O.J., Delgado, F., Giesen, R., Muñoz, J.C. (2015). Planning, operation, and control of bus transport systems: A literature review. *Transportation Research Part B* 77, 38–75.
  - Durán-Micco, J., Vansteenwegen, P. (2022). A survey on the transit network design and frequency setting problem. *Public Transport* 14(1), 155–190. doi:10.1007/s12469-021-00284-y.
  - Cancela, H., Mauttone, A., Urquhart, M.E. (2015). Mathematical programming formulations for transit network design. *Transportation Research Part B* 77, 17–37.
- **Classic network design and frequency setting:**
  - Ceder, A., Wilson, N.H.M. (1986). Bus network design. *Transportation Research Part B* 20(4), 331–344.
  - Furth, P.G., Wilson, N.H.M. (1981). Setting frequencies on bus routes: theory and practice. *Transportation Research Record* 818 (pages UNVERIFIED; commonly cited 1–7).
  - Mohring, H. (1972). Optimization and scale economies in urban bus transportation. *American Economic Review* 62(4), 591–604 (existence verified; volume, issue and pages as commonly cited). This is the square-root rule behind D1.
- **Frequency-based assignment and common lines** (needed for §3 and M1, M10):
  - Chriqui, C., Robillard, P. (1975). Common bus lines. *Transportation Science* 9(2), 115–121.
  - Spiess, H., Florian, M. (1989). Optimal strategies: A new assignment model for transit networks. *Transportation Research Part B* 23(2), 83–102.
- **Elastic or variable demand in transit network design** (needed for M3):
  - Lee, Y.-J., Vuchic, V.R. (2005). Transit network design with variable demand. *Journal of Transportation Engineering* 131(1), 1–10.
- **Ridership vs coverage objectives** (relevant to λ and to the coverage safeguards):
  - Walker, J. (2008). Purpose-driven public transport: creating a clear conversation about public transport goals. *Journal of Transport Geography* 16(6), 436–442.
- **Experimental evaluation of heuristics** (positions §7 findings 2, 3, 6, 7):
  - Hooker, J.N. (1995). Testing heuristics: We have it all wrong. *Journal of Heuristics* 1(1), 33–42.
  - Rardin, R.L., Uzsoy, R. (2001). Experimental evaluation of heuristic optimization algorithms: A tutorial. *Journal of Heuristics* 7(3), 261–304.
- **Model validation practice** (needed for M4 and M15):
  - Cambridge Systematics (2010). *Travel Model Validation and Reasonableness Checking Manual*, 2nd ed., FHWA Travel Model Improvement Program.

State explicitly what is novel relative to these. As I read the paper, the novel parts are the harness design (firewall, preregistered robustness classes, basin closure) and the negative results, not the frequency-setting method.

### M10 — IMPORTANT. No formal problem statement, and an incomplete, unpositioned model description

**Location:** §3.

**Problems.**

**(a) There is no mathematical statement of the problem.** Readers need:

- decision variables h_{r,p} ∈ L_{r,p} ∪ {OFF};
- the objective (written out, per M3);
- the RVH constraint;
- the per-period proxy constraint Σ_r cycle_{r}/h_{r,p} ≤ K_p, with cycle = 2·runtime·(1 + layover 0.15) (`outputs/exp4_normalized/COMMON_RESOURCE_ENVELOPE.json → instrument`);
- the Exp 1 rules (preserve span; h ≤ max(60, baseline); express lock);
- the policy constraints R1–R6.

**(b) The waiting-time function is missing.** The code uses E[w] = h/2 for h ≤ 12 min, else 6 + 0.25·(h − 12) (`config/assumptions.yaml → waiting`; `pathset.py:_wait`). This drives every frequency result and must be stated. Note also that Exp 7's A4 ("schedule-coefficient waiting") targets exactly this.

**(c) The Model B formula is undefined as written.** "mult = 1 / Σ_q (n_trips(q) / n_direction_trips(q))" does not say what "mult" multiplies (the route headway entering the wait function), or what q ranges over.

**(d) The layover ratio is not mentioned.** The proxy cap depends on the assumed 15% layover ratio ("NOT a verified COTA work rule", `assumptions.yaml`).

**(e) The assignment model is not positioned.** Assignment is all-or-nothing to the cheapest of at most four enumerated paths, with at most one path per pricing scenario (`EXPERIMENT4_ORIGINAL_QUESTION_ADDENDUM.md`: "the cap does not bind … one path per scenario"). That is neither frequency-based optimal-strategy assignment (Spiess and Florian, 1989) nor schedule-based assignment. Its known biases (no route-choice dispersion, no cross-route strategy, path-set dependence) should be stated.

**(f) The retention curve's status is not stated.** The config itself calls it "A crude discouragement proxy, NOT a mode-choice model".

**(g) The ladder description is inconsistent.** Exp 1 plans contain non-ladder values such as 65.45 min owl headways (`exp1_baseline_modelB.json → plans`), and §5.1 refers to a "30–120-minute tier". The text should say that baseline headways above 60 are retained off-ladder.

**Fix:** Add §3.0, "Problem statement", with numbered equations for all of the above, a notation table, and one paragraph comparing the assignment to common-lines, optimal-strategy and frequency-based assignment.

### M11 — IMPORTANT. Demand construction: wrong units, an undisclosed truncation effect, an undisclosed assumption, and an A1 perturbation that changes volume rather than pattern

**Locations:** §2 Demand row; §6, A1 row; §8, "Commute-only demand".

**Problems.**

**(a) LODES counts are jobs, not trips.** LODES OD records count jobs (JT00 = all jobs) by home and workplace block. They are not daily trips. "→ 823,915 commute trips" is a units error. These numbers come from `outputs/verify.log:15` ("823915 trips"), a run log rather than a canonical artifact.

**(b) Demand is concentrated by truncation.** Scaling is applied *after* top-20,000 truncation (`src/cota_opt/harness.py:148–152`: `scale(_top_k(filter_to_accessible(...)), 30949)`). The retained pairs carry 64.9% of accessible flow, so each retained pair's demand is inflated by about 1/0.649 ≈ 1.54×. That concentrates demand spatially. It should be stated as a modelling choice with a direction (it likely favours trunk-heavy plans). Exp 7's X_TOPK40K partially tests it: F1 moves from −6.02% to −5.49%.

**(c) The 30,949 total rests on an assumed transfer rate.** The total divides by (1 + 0.20). The 0.20 transfer rate is assumed ("COTA's observed rate is UNKNOWN", `assumptions.yaml`). §2 calls 30,949 "NTD-derived" without saying so.

**(d) A1 adds volume on top of the NTD total.** A1 *adds* non-commute trips at 25/50/100% (`scripts/exp7_levels.py:197–206`: `od.flow + x_*nc.flow`). Total demand therefore becomes 38,686–61,898 trips, up to 2× the NTD-anchored system ridership, which already contains non-work trips. This conflates a demand-*pattern* test with a demand-*volume* test. At 2× demand the D5 premise that crowding does not bind is outside its stated validity ("Falsified by. A demand model two or three times larger"), and crowding is off in the Exp 4–7 instance. A volume-preserving variant (`noncommute_blend`) exists in the code but was not used.

**Fix:**

1. §2: replace "823,915 commute trips" with "823,915 jobs (LODES JT00 home–work pairs)". Cite the artifact, or move the provenance to a canonical file.
2. Add: "After truncation to the top 20,000 pairs (64.9% of accessible flow), demand is rescaled to 30,949, inflating retained pairs by about 1.54×."
3. Add: "30,949 assumes a 20% transfer rate (unobserved)."
4. In §6 and §8: "A1 adds non-commute demand on top of the NTD-anchored total, raising total demand 25–100%. It therefore tests demand volume as well as pattern, with crowding not modeled."

### M12 — IMPORTANT. Several conclusions are interpretations or extrapolations presented as findings

**Locations and fixes:**

**(a) §5.1, "That is a constructive result … unmodeled operational constraints can likely be met at little cost".** This is untested. D17's "constructive reading" is interpretation, not evidence. The one family of operational constraints the study did price (Exp 6) costs up to 0.91% of the objective, larger than every Exp 3 effect. Fix: delete it, or replace with "Whether unmodeled operational constraints (clock-face headways, interlining, runcutting) can be met at little cost was not tested."

**(b) §5.1, "Where service moves … toward the 30–120-minute tier (D1)."** D1's evidence is "Balanced plan (config C, λ = 2, matched effort)", with Moderate confidence. That predates and is not tied to the certified Model B Exp 1 evaluator, so it breaks reporting rule 1. Under a 19% route-period disagreement across seeds, a "where service moves" pattern also needs a seed-agreement check (the guidelines' Figure 7 rule 5). Fix: delete it, or qualify it as "(pre-Model-B evidence, D1; not re-verified on the certified plans and not checked for seed agreement)".

**(c) §7.1 and Abstract, "Route-level scoring overstates network gains roughly threefold (22.71% vs 7.16%)".** No evaluator is stated (rule 1). The Model B λ = 4 frontier value is −7.12% at +1.24% GC, so 7.16% at +2.51% is not the certified instance. "Threefold" also rests on one plan. Fix: name the evaluator and model instance, and say "for the λ = 4 plan, 22.71% vs 7.16%".

**(d) Abstract, "Two methodological results generalize beyond Columbus".** One case study cannot establish generality, and both results are known cautions (M9). Fix: "Two methodological lessons are likely to apply beyond Columbus".

**(e) Abstract, item 1: R4 attributed solely to unmatched convergence.** D31 says "both errors — the optimizer asymmetry and the effort shortfall — pushed the same way". Fix: "That error, together with the treatment-dependent optimizer of D27, produced and then forced the withdrawal of …".

**(f) §11, "A harness that preregisters, certifies convergence and admits only declared differences is what separated those artifacts from the one result that held."** This is a causal claim about the harness, and the harness did not catch M1 or M2. Fix: "The harness caught several of these artifacts; others (D23, D27, D35, and the B1 mislabel) were found by audit outside it."

### M13 — IMPORTANT. Exp 7 design and interpretation issues that should be disclosed

**Location:** §6.

**Problems.**

**(a) The Stage 2 selection was driven by λ = 1.** The preregistered metric picked A5 on the strength of F4's movement (1.196), driven by the A5_LAM1 sign flip (`EXP7_STAGE2_SELECTION.json`). λ = 1 lies outside Exp 1's certified range, and the paper itself labels it degenerate. As a result, the dimension the authors call "the largest unquantified error" (A1, demand; score 0.415) was never re-optimized. This is a legitimate preregistered outcome, but the consequence belongs in §8's Stage 2 scope row.

**(b) Some exclusions came after the results.** The A7_RM04/RM05 exclusion and the F2 "not applicable" exclusion were decided at closeout. §6.0 flags this, but §4's "Nothing is waived after the fact" should be softened.

**(c) The magnitude bands are anchored on a non-certified reference.** Bands are relative to Stage 1 BASE (−6.02%), not to the certified value (−6.65%).

**(d) Multiple comparisons need stating.** "SIGN_ROBUST" means no sign event among 44 Class A levels, 20 of them bootstrap draws, so the classification is more conservative for some findings than others. It is a descriptive label, not a statistical test.

**(e) The R1_H60 post hoc result needs more qualifiers.** It comes from a single closure per cell. Five of the seven R1_H60 records are initial solves, not closure improvements (`EXP7_F1_DECISION_SPACE.json → rows[].cells.R1_H60.record`). It also runs under the Exp 6 model instance and solver, not Exp 1's.

**Fix:** Add each of these as a sentence or row in §6.0 and §8. In the abstract's re-optimization bullet, add "(Exp 6 model instance and block certifier, one closure per cell)".

### M14 — IMPORTANT. The abstract and conclusion do not match the body exactly, and the abstract exceeds journal limits

**Problems:**

1. **Length.** The abstract is 530 words. Transportation Research Part A's guide for authors sets a maximum of 250 words, plus 3–5 highlights of at most 85 characters each and 1–7 keywords. TR-B and TR-C have similar rules.
2. **Levers not studied.** The abstract lists "where routes stop" as a lever, but stop consolidation was deferred ("stop consolidation is a DEFERRED question", registry exp3 limitations), and stop edits other than add_stop carry zero runtime benefit by construction. "Transfer timing", which is in the mission quoted in §1, is not studied at all; a frequency-based model cannot study it. Neither omission is stated.
3. **Safeguard prices.** "cost 0 to 0.91% … each" omits that the zeros (R2 OFF-share caps) bind against the best-known REF plan and that prices are basin-dependent at the 0.16-point scale (§5.6).
4. **Conclusion wording.** "Re-timing frequencies" suggests timetable offsets; the model changes headways. Say "reallocating frequencies".
5. **Conclusion magnitude.** "by about 6%" is ambiguous between −6.65% (certified) and −6.02% (Stage 1 BASE). Give both.
6. **Conclusion sentence fragment.** "Post hoc (`docs/EXPERIMENT7_F1_ADDENDUM.md`). At λ = 1 it is +0.12%." is a fragment.
7. **Items in M2, M5 and M6.** The "certified null", "best of 200" and missing regime caveat also apply here.

**Fix:** Rewrite the abstract to at most 250 words with the corrections from M2–M6. Move the detailed bullets to a "Summary of findings" table in §1. Add highlights and keywords. Add to §1: "Transfer timing (timetable synchronization) and stop consolidation are outside the scope of this frequency-based model."

### M15 — IMPORTANT. Non-compliance with the project's own binding reporting standard, and no reproducibility or data-availability statement

**Problems** (`docs/RELEASE_AND_REPORTING_GUIDELINES.md`):

- **Figures.** None of the seven required figures exist. Journals will expect at least the Exp 1 frontier, the route-level vs path-level comparison, the policy-price frontier, and the robustness summary.
- **Appendices.** The required decision log, preregistration amendments, superseded-artifact index and calibration register are absent (acknowledged at line 16).
- **Rule 1 (full identity).** Many numbers lack network, evaluator or model instance: all of §7, §5.5's percentages, §8's 22.7%/47.0%, and the abstract's Exp 3 range. Appendix A's "contract / commit" column is empty for Experiments 1–6, but release done-criterion 3 requires a contract digest and commit for every number.
- **Rule 4 (units sidecar).** Unit labels must come from `CANONICAL_ENVELOPE.units.json`, which does not exist.
- **Numbers from logs.** §2's LODES counts and "24.7%" trace only to run logs (`outputs/verify.log`), not canonical artifacts, contradicting line 9's claim that "Every number is transcribed from a named canonical artifact".
- **Tags and access.** Tag `exp3-final-v1`, cited in §5.3, does not exist in this repository (`git tag -l` returns nothing), and `research-final` is not yet cut. There is no LICENSE, no CITATION.cff, and no statement of where the code and data can be obtained.
- **Missing sections.** There is no threats-to-validity section separating internal validity (solver, basin, path set), construct validity (objective, unserved), external validity (one city, commute proxy) and statistical conclusion validity (seed spread vs error, D32/D33).

**Fix:**

1. Add "Data and code availability": repository URL or DOI; commit or tag; license; how to obtain LODES, GTFS and NTD by checksum (`config/sources.yaml`); compute environment and runtime.
2. Add §8.0, "Threats to validity", with the four categories above.
3. Complete Appendix A's contract/commit column.
4. Either generate the figures or state in a visible "Not yet complete" box that the draft is not submission-ready.

### M16 — IMPORTANT. The baseline resource identity and the plan's resource use are reported inconsistently, and the fleet statements should be tightened

**Locations:** §5.1, "The plan uses 2,516.5 of 2,517.2 revenue vehicle-hours"; §2 ("nothing tuned"); §3.

**Problems.**

**(a) It is unclear which plan 2,516.5 refers to.** The λ = 2 frontier run used 2,516.65 RVH (`exp1_final.json → frontier[λ=2].revenue_veh_hours`), and the headline seeds' values are not given. State which plan or seed the 2,516.5 refers to.

**(b) The baseline fleet reconstruction is not validation.** "197 peak vehicles … NTD VOMS 198; nothing tuned" is a useful check, but it depends on GTFS `block_id` and says nothing about modified plans. The text in §2 could imply otherwise.

**(c) The capacity check is broader than claimed.** The Exp 4A addendum found one N3 am-peak route-period over capacity (max load 68.3 against capacity 60) in an instance with crowding off. §3's "Crowding does not bind" should say "does not bind at the system level at the modeled demand; one N3 route-period exceeds planning capacity in Exp 4A; crowding is not modeled in Exp 3–7".

**Fix:** As stated in (a)–(c).

### M17 — IMPORTANT. The current-plan "unserved" baseline differs between the experiments that produce the headline and the robustness label, and the paper reports the robustness of a quantity whose baseline it never reconciles

This is a narrower, numeric companion to M4 and M7. I list it separately because the reader cannot reconcile the two headline baselines from the text.

**Location:** §5.1 vs §6.1 F1 row.

**Problem.** §5.1 reports baseline unserved 10,262 (Exp 1 instance). §6.1 uses Stage 1 BASE −6.02%, computed against a baseline of 10,423.68 (`EXP7_ANALYSIS.json → f1_adaptive[BASE].current_plan_unserved`) and averaged over three plans. Neither the second baseline nor the reason for the 1.6% difference appears in the report; closeout §4.1 gives it. The headline sentence "That result keeps its sign at every implemented Stage 1 level" (§11) thus attaches Exp 7 labels to a quantity measured against a different baseline from the one the reader was given.

**Fix:** In §6.1, add: "Stage 1 evaluates the three certified Exp 1 plans in the Exp 6 model instance (crowding off, per-network path set), where the current plan leaves 10,424 trips unserved (vs 10,262 in the Exp 1 instance). Seed plans give −5.94/−6.16/−5.98% (vs −6.60/−6.72/−6.63%)."

---

## 4. Minor comments

- **m1. Sign wording (§6.1, F6 row).** "the six λ = 4 flips are to −0.01% or less" reads as ≤ −0.01%. The values are −0.0069% and −0.0099% (`EXP7_CLOSEOUT_TABLE.json → rows[F6_N3_*].class_a_range[0]`). Fix: "to between −0.007% and −0.010%".
- **m2. "Zero point" for the retention curve (§6.2, line 600; §8, line 673).** The curve does not reach zero at 210 min; its floor is 0.10 (`assumptions.yaml: cost_retention_zero_min: 210`, `cost_retention_floor: 0.10`). Fix: call it "the 210-min floor point", and explain the config name.
- **m3. "Rounded digests can collide" (§7.9).** Two values that differ in the last ULP mapping to the same rounded digest is the designed behaviour of rounding, not a hash collision. Fix: "A rounded digest cannot distinguish envelopes that differ below its rounding precision".
- **m4. Resource figure (§5.1).** "2,516.5 of 2,517.2": see M16(a). Use the same precision as §3 (2,517.18).
- **m5. λ table (§5.1).** It omits λ = 0.25 (+15.31% unserved, uncertified; `exp1_final.json → frontier[0]`), and the row order (2, 4, 8, 16, 1, 0.5) is unconventional. Fix: order by λ and shade the uncertified rows.
- **m6. Sample size (§7.3).** "r = −0.711" needs "(n = 8 edit kinds)" (D27, `DISCOVERIES.md:1572`). Eight points support a correlation only weakly.
- **m7. Notation for spread (§5.1).** Table headers say "solver seed spread (SD)" and the cells say "±0.06". Use "SD = 0.06 points" consistently, and say "points" when spreads are absolute differences of percentages.
- **m8. Undefined terms (§4, §6).** "Gen1", "D33-B", "fixpoint", "improvable flow share", "ULP", "anchor", "W/X transfers", "sentinel", "Class A/B", "GTFS", "RAPTOR", "LODES", "NTD", "VOMS", and the level codes (A7_RM05, R4_C05, …) in running text are not defined in Appendix B (rule 11). Fix: add them to the Glossary.
- **m9. Parallelism (§10).** "Certification cells are independent, so the work is trivially parallel" contradicts the next sentence and basin closure, whose cells are dependent through anchors. Fix: "Initial solves are independent; basin closure is not."
- **m10. "Nothing is waived after the fact" (§4).** Soften, given the post hoc exclusions in §6.0 and Exp 3's two disclosed post-hoc analysis-code changes (`EXPERIMENT3_CLOSURE.md` §8).
- **m11. Title.** See M8. The subtitle also has two clauses joined by a colon; one is enough.
- **m12. AF1 "certified" value (§6.1).** The closeout table has no certified value for AF1 (`rows[AF1_REF].certified = null`). The −0.23% is the Exp 6 closed-REF difference (−6,726.35 / 2,941,892.37). Fix: label the cell "Exp 6 closed: −0.23%".
- **m13. Units and terms in §6.2 tables.** Generalized cost has no unit. Add "(in-vehicle-minute equivalents per weekday)". "trips served (of 30,949)" should say "modeled trips".
- **m14. Percent vs points.** Mixing "% of objective" and "percentage points" (§5.6, abstract) is confusing. Fix: state on first use that price differences are in percentage points of the objective.
- **m15. Band wording.** Band names should match the Glossary exactly ("Highly sensitive magnitude"), or the Glossary should drop "magnitude".
- **m16. "Noise floors" unit (§5.2).** "0.02 noise floors" needs a definition: the effect divided by the 0.287-point floor.
- **m17. Number formatting.** Appendix A says "+9.659%" while the body says "+9.66%". Use one precision.
- **m18. Jargon (§1 table).** "N0 half informative" is jargon. Fix: "N0 results monotone (informative, not certified)".
- **m19. Level counts (§6, line 473).** "47 levels plus BASE were run" plus "Declared but not run: A4 (2 levels)". State the declared total (49 + BASE), so readers do not compute 4 × 50.
- **m20. "λ is not calibratable" (§8).** See M3(e).
- **m21. Unlabelled post hoc claim (§6.2, line 575).** "Doubling the transfer penalty, or adding walking friction, tips the same trade more gently" is a post hoc mechanism claim. Label it as such, as in errata E7.
- **m22. Route-periods (§3, line 157).** "173 route-periods across 39 routes": say that 39 × 6 = 234, and that 61 route-periods have no baseline service and cannot be opened (`allow_new_service_in_empty_periods: false`). This also defines what OFF can mean.
- **m23. Statistic not defined (§5.3).** "|mean Δ| / SD = 78.6" uses SD, not SE, over five paired seeds. Say so, and give the SD (0.002375%) as the closure does.
- **m24. Dangling reference (§5.4).** "(D36, D38)" points to the decision log, which is not in the paper. Inline the one-line content, or include the appendix.
- **m25. Comparison base (§5.5).** "N4 is worse than N0 at all 16 cells, by 8.07–11.59%" should say "% of N0's objective at the same cell".
- **m26. Undefined notation (§6, A6 row and §5.5).** The cell names J/H/P (joint/hours/peak) and the level suffixes are used without definition.
- **m27. Section numbering.** "§6.0" is unusual. Renumber §6.0 → §6.1.
- **m28. Frontier precision (§5.1).** The λ = 4/8/16 frontier points are single-seed runs, but the table presents them alongside the three-seed headline. Add "(single run)".
- **m29. Table-title wording (§5.6).** "Exp 7 Stage 2 BASE re-closed (N0 / N3)": the N3 entry for the 20-min floor says "infeasible", but it was proven INFEASIBLE_UNDER_ENVELOPE only at BASE and A3 and was not proven at A7 levels. Fine as written for BASE; add a footnote.
- **m30. Rule 8 phrasing.** "adds a stop on route 010" is a route-level statement in the abstract. Add "(model result; not a recommendation)".
- **m31. Missing denominator (§8, "Commute-only demand").** "24.7% of regional commute flow is transit-accessible" should say "(78,210 of 317,706 block-group pairs; by job count)" (`outputs/verify.log:16`).
- **m32. Cross-reference (§3).** "(errata E7)" refers to a document outside the paper. Give the reasoning inline (it is already there) and drop the bare reference, or cite the errata file path.

---

## 5. Numbers spot-checked

✓ = matches to the stated precision; ✗ = mismatch or problem (see the comment cited); ~ = matches but caveated.

**Automated:** `python scripts/verify_report_claims.py` returns 39/39 OK. These include −6.65, ±0.06, +3.30, +0.88, −2.34, 19.1, 19.7, 10,262, 9,583, −1.42, +9.66, +0.12, +0.482, +0.912, +0.212, +0.634, +30.5, 0.161, 2,940,186, 2,935,446, 557, 1,583, 29,366, −0.226, and +0.166. Note that the verifier checks the 2B value against a stale registry (M2).

| report location | number | artifact / key | status |
|---|---|---|---|
| Abstract | ~680 more trips served | 3.30% × 20,687 = 682.6 (`exp1_final.json`) | ✓ |
| §5.1 | SD 0.064, range 0.12 (−6.60/−6.72/−6.63) | `exp1_final.json → headline.unserved_demand.sd_pct` 0.0637; D17 | ✓ |
| §5.1 | 6.9 min | `plan_disagreement.mean_abs_change_min` 6.919 | ✓ |
| §5.1 | λ = 4/8/16: −7.12/−7.25/−7.28; λ = 0.5: +6.85 | `exp1_final.json → frontier[].unserved_change_pct` | ✓ |
| §5.1 | 2,516.5 of 2,517.2 RVH | `resources.weekday_revenue_veh_hours_optimized` 2516.5; λ = 2 frontier run 2,516.65 | ~ (m4, M16) |
| §5.1 | 20,687 → 21,366 served | `exp1_baseline_modelB.json → baseline_served`; `frontier[λ=2].served` 21,365.9 | ✓ |
| — (not in report) | Exp 1 objective change −2.21% | computed from `baseline_gc`, `baseline_unserved`, `frontier[λ=2]` | reviewer computation (M3) |
| §2 | 30,949 | 38,694 × 0.9598 / 1.2 = 30,948.8 (`assumptions.yaml`) | ✓ (assumed 20% transfer rate, M11) |
| §2 | 4,640,957 / 317,706 / 823,915 | `outputs/verify.log:15` (log, not canonical) | ✓ value; ✗ units ("trips" are jobs), M11 |
| §2 | 197 @ 17:13, 284 blocks, VOMS 198 | `outputs/CANONICAL_ENVELOPE.json` | ✓ |
| §3 | caps 85.28/162.01/159.17/176.49/140.19/35.56; 2,517.18 | `outputs/exp4_normalized/COMMON_RESOURCE_ENVELOPE.json → peak_fleet_by_period` | ✓ |
| §3 | digest 3fd5241db44ca9da | same file → `envelope_digest` | ✓ |
| §3 | 176.49 ≈ 10% below 197 | 176.49/197 = 0.896 | ✓ |
| §3 | cost weights 2/2/1/2/+10; w_unserved 60 | `config/cost_weights.yaml` | ✓ |
| §3 | ladder 5–60 | `config/constraints.yaml → headway_ladder_min` | ~ (off-ladder baseline values exist, M10(g)) |
| §3 | 600 m / 400 m / 80 m/min / 4 paths / 2 transfers | `assumptions.yaml → path_assignment` | ✓ |
| §3 / §8 | retention 60 → 0.10 at 210 min; 64% kept at 120 | 1 − 0.9 × 60/150 = 0.64 | ✓ (m2) |
| §3 / §8 | common lines 0.516% (N0), 12.47% (N4) | `EXPERIMENT4_ORIGINAL_QUESTION_ADDENDUM.md` gate 4-10 | ✓ values; ✗ N3 (1.16%) omitted, "bounded" misstated (M5) |
| §5.2 | +0.060%, +0.160%, 0.287 floor | `EXPERIMENT2_CLOSEOUT.md`; D24 | ✓ (floor from superseded pipeline, M2) |
| §5.2 | 240 / 227 | `EXPERIMENT2_CLOSEOUT.md`; registry exp2b | ✓ (discovery-stage, M2) |
| §5.2 / §6.1 | +0.0065%, 0.02 floors | `outputs/exp2b_certification.json → effect_pct` (superseded; `_confirmation.matched_start_unserved_effect_pct` = 0.0902) | ✗ (M2) |
| §5.3 | −0.18657%, 78.6, 28/28 | `outputs/exp3/escalation_report.json → combined[0]` (mean −0.186565, ratio 78.55) | ✓ |
| §5.3 | 84 → 39 → 30 → 29; 23/6 regimes | `EXPERIMENT3_CLOSURE.md` §1, §7 | ✓ |
| Abstract | −0.01% to −0.19% | certified effects −0.0096 to −0.1866 (`escalation_report.json`) | ✓ |
| §5.4 | leader 35e351133d6f at 3,223,885.9475; legacy rank 154 | `outputs/exp4_normalized/EXP4N_RANKING.json → leader` | ✓ |
| §5.4 | margin 0.387006% | `margin_first_to_second.percent` 0.3870058 | ✓ |
| §5.4 | legacy leader rank 185 | `normalized_vs_legacy.legacy_leader.normalized_rank` | ✓ |
| §5.4 | Spearman +0.3566; 7,296/19,900 (36.7%) | `normalized_vs_legacy` (0.35659; 0.36663) | ✓ |
| §5.4 | +9.66% (+283,973.37) | `CANONICAL_RESULTS_v5.json → exp4a.headline` | ✓ (but see M5: +9.28% and +8.55% are omitted) |
| §5.4 | +7.87%, λ flip 1.087 | Exp 4A addendum | ✓ (+7.87% "not certified" omitted) |
| §5.4 | rank 237, 0.0147% better | registry exp4 `out_of_band_audit`: (3,511,184.5658 − 3,510,666.7802)/3,511,184.5658 = 0.01475% | ✓ |
| §5.5 | 12 of 99; up to 1.70% | `EXPERIMENT5_CLOSEOUT.md` (+1.7034%) | ✓ |
| §5.5 | 4.4× | 1.7034/0.387 = 4.40 | ✓ |
| §5.5 | +0.57%, +2.05%; −0.74/−0.94/−1.48% | `EXPERIMENT5_CLOSEOUT.md` §3 | ✓ |
| §5.5 | N4 worse by 8.07–11.59% | `EXPERIMENT5_CLOSEOUT.md` table | ✓ |
| §8 | 32 UNDECIDABLE; 17.8–22.7% / 45.6–47.0% | `EXPERIMENT5_CLOSEOUT.md` §6 | ✓ |
| §5.6 | Exp 6 prices N0: 0.212/0.244/0.428/0.440/0.482/0.575/0.912 | `outputs/exp6/EXP6_ANALYSIS.json → frontier[].policy_cost_closed_pct` | ✓ all |
| §5.6 | Exp 6 prices N3: 0.250/0.321/0.477/0.485/0.524/0.634 | same | ✓ all |
| §5.6 | Exp 7 BASE N0: 0.260/0.146/0.389/0.489/0.531/0.500/0.633/0.967 | `outputs/exp7/EXP7_ANALYSIS.json → f6_prices[level=BASE]` | ✓ all |
| §5.6 | Exp 7 BASE N3: 0.287/0.225/0.436/0.522/0.561/0.671 | same | ✓ all |
| §5.6 | shifts −0.10 to +0.06 points | computed: −0.098 (N0 R4_C05) to +0.058 (N0 R1_H30) | ✓ |
| §5.6 | order reversal R4_C05 vs R2_S05 on both networks | Exp 6 0.212 < 0.244 → Exp 7 0.146 < 0.260 (N0); 0.250 < 0.321 → 0.225 < 0.287 (N3) | ✓ |
| §5.6 | greedy −0.162 to +0.124 points; two negative prices | `EXPERIMENT6_CLOSEOUT.md` §8 | ✓ |
| §5.6 | +4,600 trips (+28%), +45% GC, 0.13–0.16% | `EXPERIMENT6_CLOSEOUT.md` §7 (16,527 → 21,144, +4,616; N3 +4,670) | ✓ |
| §5.6 | N3 better by 0.15–0.23% in 13 cells | `EXPERIMENT6_CLOSEOUT.md` §9 (0.1525–0.2286) | ✓ |
| §5.6 | F6-track REF 0.058% better than Exp 6 REF | (2,941,892.37 − 2,940,186.29)/2,941,892.37 | ✓ |
| §6 | 47 levels = 44 A + 1 B + 2 X; 42 as issued | `outputs/exp7/EXP7_LEVELS.json` (counts by dimension: 3+20+3+4+2+10+2) | ✓ |
| §6 | 192 cells; 0/840; 4/4 sentinels; 5 fixed points | `EXP7_ANALYSIS.json → monotonicity`, `sentinels`, `closure` | ✓ |
| §6 | B1 −5.99%, +7.86%; X_TOPK40K −5.49%, +8.82%; X_ROUNDS4 −6.03%, +9.67% | `EXP7_CLOSEOUT_TABLE.json → rows[F1/F4_43].class_b_and_additional` | ✓ values; ✗ B1 label (M1) |
| §6 | selection scores A5 1.196 … A2 0.094 | `EXP7_STAGE2_SELECTION` via `EXP7_CLOSEOUT_TABLE.json → stage2.selection.scores` | ✓ |
| §6.1 | F1 Stage 1: −6.024; −6.998 to −1.897; worst A6_MAXWALK75 68.5% | `EXP7_CLOSEOUT_TABLE.json → rows[F1]` | ✓ |
| §6.1 | F1 bands: Highly sensitive A6 | `rows[F1].worst_magnitude_band_by_dimension` | ✓ |
| §6.1 | F1 Stage 2 −6.8% to +182% | `stage2.results.F1.per_level` (−6.76 … +181.72) | ✓ |
| §6.1 | F2 range −0.226/+0.166; worst A3_RTNOISE; all dimensions Highly sensitive | `rows[F2_unserved]` (18 flips) | ✓ |
| §6.1 | F3 −0.41 to +0.32; A7_RM05; Highly sensitive A1, A7 | `rows[F3]` (−0.40502, +0.32268) | ✓ |
| §6.1 | F4 −1.31 to +19.35; flip only at λ = 1 | `rows[F4_43]` | ✓ |
| §6.1 | F4 Stage 2 +6.8% to +30.8% (vs N3); abstract +6.6% to +30.8% (vs N0 or N3) | `EXP7_ANALYSIS.json → f4` (N3: 6.766–30.790; N0: 6.569–30.566) | ✓ |
| §6.1 | F4 at λ = 1: −0.98% | `f4[A5_LAM1]` −0.9813 | ✓ |
| §6.1 | F6: N0 11/13 (5 of 7 distinct), N3 5/12 (3 of 6) | `rows[F6_*].sign_label`, by distinct base values | ✓ |
| §6.1 | "six λ = 4 flips to −0.01% or less" | min values −0.0069, −0.0099 | ~ (m1) |
| §6.1 | AF1 10 of 13 SIGN_ROBUST excluding A7 mismatch | `rows[AF1_*].cross_network_a7_mismatch.sign_label_excluding_mismatched_A7` | ✓ |
| §6.1 | AF1 Stage 2: F6 track 0.16–0.31; F4 track 0.16–0.18; tracks differ ≤ 0.15 | `af1_n3_minus_n0[cell=REF]` 0.157–0.310; `f4[N0→N3]` 0.161–0.184; max diff 0.146 | ✓ |
| §6.1 | AF1 "certified −0.23%" | `rows[AF1_REF].certified = null`; stage1_base −0.2286 | ~ (m12) |
| §6.2 | 21,091 / 1,583 served; 2,516 / 557 RVH; 17 / 139 OFF; 1,757,243 / 69,305 GC; 9,858 / 29,366 unserved | `EXP7_F1_DECISION_SPACE.json → rows[BASE, A5_LAM1].cells.REF` | ✓ all |
| §6.2 | objective identity GC + 120·u | 1,757,243.36 + 120 × 9,857.858 = 2,940,186.3 | ✓ |
| §6.2 | 83–86 GC per served trip | 1,757,243/21,091 = 83.3 | ✓ |
| §6.2 | 14,263 vs 19,450; 18,324 vs 20,118; 13,537 vs 14,301 | `EXP7_F1_DECISION_SPACE.json` REF.served; 30,949 − current_plan_unserved | ✓ all |
| §6.2 | positive REF F1 ↔ 38–139 OFF | F6 track 139/60/38/38; F4 track 48/139/48/48/48 | ✓ |
| §6.2 / addendum | R1_H60 −2.1% to −7.0% at λ ≥ 2; +0.12% at λ = 1 | `rows[].cells.R1_H60.f1_pct` (−2.141 … −6.999; +0.118) | ✓ |
| addendum | R1 plans 2,513–2,516 RVH | `cells.R1_H60/R1_H30.revenue_veh_hours` (2,513.38–2,516.42) | ✓ |
| §7.7 | fixed points 0.04–0.40% apart, 5 of 7 > 0.03%; F1 differs by up to 36 points | addendum table: 0.161/0/0.007/0.038/0.401/0.284/0.071; 30.48 + 5.43 = 35.9 | ✓ |
| §7.1 | 22.71% vs 7.16%; seven route-level plans dominated | D3 (`DISCOVERIES.md:75`) | ✓ values; ✗ evaluator not stated (M12c) |
| §7.3 | r = −0.711 | D27 (n = 8) | ✓ (m6) |
| §7.6 | 0.159% vs 2.28% | D38; `STATE_OF_PLAY.md:1121` | ✓ |
| §8 | 24.7% / 64.9% | `outputs/verify.log:16`; `EXPERIMENT4_DEMAND_ROBUSTNESS.md:62` | ✓ (logs, M15) |
| §8 | MAE 17.2 s, bias +0.41%, median APE 20.5% | `EXPERIMENT3_CONTRACT.md:71–72`; `EXP7_LEVELS.json → A3_RTNOISE` (0.205) | ✓ |
| §8 | −157 s/stop | `src/cota_opt/stopedits.py` header; `EXPERIMENT3_CONTRACT.md` §4 | ✓ |
| §6.0 / App. A | contract 1263bedaebe6a45d; commits f1a05645, 5dc3f408, 4a2ba9f6, b0f6f416 | `git cat-file -t` → commit (all four) | ✓ |
| §5.3 | tag exp3-final-v1 | `git tag -l` returns nothing | ✗ (M15) |
| Abstract | length | 530 words (TR-A limit 250) | ✗ (M14) |

---

## 6. Literature recommended (verified via web search unless marked)

- Guihaire, V., Hao, J.-K. (2008). Transit network design and scheduling: A global review. *Transportation Research Part A* 42(10), 1251–1273. ✓ (RePEc v42y2008i10p1251-1273)
- Ibarra-Rojas, O.J., Delgado, F., Giesen, R., Muñoz, J.C. (2015). Planning, operation, and control of bus transport systems: A literature review. *Transportation Research Part B* 77, 38–75. ✓ (RePEc v77y2015icp38-75)
- Durán-Micco, J., Vansteenwegen, P. (2022). A survey on the transit network design and frequency setting problem. *Public Transport* 14(1), 155–190. doi:10.1007/s12469-021-00284-y. ✓
- Cancela, H., Mauttone, A., Urquhart, M.E. (2015). Mathematical programming formulations for transit network design. *Transportation Research Part B* 77, 17–37. ✓ (RePEc v77y2015icp17-37)
- Ceder, A., Wilson, N.H.M. (1986). Bus network design. *Transportation Research Part B* 20(4), 331–344. ✓ (existence verified via TRID/EconBiz; issue and pages as commonly cited)
- Furth, P.G., Wilson, N.H.M. (1981). Setting frequencies on bus routes: theory and practice. *Transportation Research Record* 818. ✓ (existence verified via TRID); pages UNVERIFIED
- Mohring, H. (1972). Optimization and scale economies in urban bus transportation. *American Economic Review* 62(4), 591–604. Existence verified; issue and pages as commonly cited, not independently confirmed.
- Chriqui, C., Robillard, P. (1975). Common bus lines. *Transportation Science* 9(2), 115–121. ✓ (RePEc v9y1975i2p115-121)
- Spiess, H., Florian, M. (1989). Optimal strategies: A new assignment model for transit networks. *Transportation Research Part B* 23(2), 83–102. ✓ (RePEc v23y1989i2p83-102)
- Lee, Y.-J., Vuchic, V.R. (2005). Transit network design with variable demand. *Journal of Transportation Engineering* 131(1), 1–10. ✓ (ASCE DOI 10.1061/(ASCE)0733-947X(2005)131:1(1)); end page as commonly cited
- Walker, J. (2008). Purpose-driven public transport: creating a clear conversation about public transport goals. *Journal of Transport Geography* 16(6), 436–442. ✓ (RePEc v16y2008i6p436-442)
- Hooker, J.N. (1995). Testing heuristics: We have it all wrong. *Journal of Heuristics* 1(1), 33–42. ✓ (DOI 10.1007/BF02430363)
- Rardin, R.L., Uzsoy, R. (2001). Experimental evaluation of heuristic optimization algorithms: A tutorial. *Journal of Heuristics* 7(3), 261–304. ✓
- Cambridge Systematics (2010). *Travel Model Validation and Reasonableness Checking Manual*, 2nd ed. FHWA Travel Model Improvement Program. ✓ (existence verified; publisher details as commonly cited)

Journal requirement checked: Transportation Research Part A guide for authors. Abstract ≤ 250 words; highlights required (3–5 bullets, ≤ 85 characters each); 1–7 keywords.
