# Referee report, round 2: TECHNICAL_REPORT.md (revision of 2026-10-04, HEAD `f0db4729`)

Second, independent referee. Read-only review of `docs/report/TECHNICAL_REPORT.md` against `docs/report/reviews/ROUND1_ADJUDICATION.md`, the JSON artifacts under `outputs/`, `src/cota_opt`, `config/*.yaml`, `DISCOVERIES.md` and the downstream documents. `python scripts/verify_report_claims.py` gives 49/49. `git diff --stat 189dfa64 HEAD` shows no change to any immutable file: none under `outputs/**/*.json`, `src/`, the registered closeouts or the contract-listed protocol documents.

## Recommendation

**Minor revision.**

The round-1 critical items (M1–M6) are implemented, and implemented correctly. The revision is faithful to the adjudication and, in one place (M14 edit 7), rightly departs from it where the adjudication's own text was wrong.

The revision still contains three errors that a journal referee or reader would catch. Two are carried over from the adjudication and one from the source record:

1. **A wrong DOI.** The DOI given for Hooker (1995) belongs to Barr et al. (1995).
2. **An arithmetic slip on the common-lines bound.** "Crediting N4 with its whole bound and N3 with none (93,300 min)" is wrong: that case is 107,248. 93,300 is the net with both credited.
3. **A false description of D2.** The report calls it pre-Model-B and about search effort. In fact D2 is about the λ-frontier plateau, and it is confirmed on the certified Model B frontier that the report's own λ table shows.

There is also a stale "pending" claim about `outputs/SUPERSEDED.md`, and one gap between equation and code: the walk-only fallback.

All of these are text fixes. None needs new computation.

Counts: 0 CRITICAL, 6 IMPORTANT, 17 MINOR.

---

## Response-to-reviewers check (round-1 items the adjudication accepted)

| item | implemented? | correct? | note |
|---|---|---|---|
| M1 (B1 relabel; §3 bound scope; §8 row; R13; E16; FUTURE:255; README:279/355; RESULTS:120) | Yes, all 8 edits | Yes | The §3/§8 text inherits the 93,300 error (R2-2). README, HANDOFF and FUTURE still say "Experiment 1's service rules" (R2-12). |
| M2 (2B magnitude; §5.2 rewrite; singles caveat; F2 row; §1 row; R4/R14; §11; App. A + note; E17; README/RESULTS; SUPERSEDED.md; verifier) | Yes, all 12 | Mostly | The App. A note and Data availability say the SUPERSEDED.md entry is "pending", but commit `f0db4729` added it (R2-4). |
| M3 (non-welfare paragraph; abstract; §5.1 objective row; all-levers table; §8 λ row; Glossary) | Yes | Mostly | Thresholds 173.3 / 143.3 verified analytically. The cut-off "λ ≥ 3.22" is imprecise (R2-14). |
| M4 (status box; Demand row; §5.1 split; abstract 67%; §8 row; Glossary) | Yes | Yes | 66.8% and 66.3% both verified. |
| M5 (abstract; §5.4 three-way table + conditions; F4 cell; §11; App. A rows) | Yes | One error | 93,300 is mislabelled (R2-2). The abstract omits the common-lines caveat (R2-19). |
| M6 (abstract; §5.3 regime caveat verbatim + SD + N3 trim; §8 stop-cost row; §11) | Yes | Yes | The regime-caveat quote matches the registry. The abstract drops "solved only at 20 restarts" (§3.1 text did too) (R2-19). |
| M7 (§4.1 instance table) | Yes | Yes | — |
| M8 (three meanings; §5 preamble; remove "certified null"; title) | Yes | Partly | "certified null" is gone from prose. The sentence "'Certified' survives unqualified only inside artifact status strings" is contradicted by about 30 unqualified uses (R2-10). |
| M9 (§1.1 related work; References) | Yes | One error | Hooker's DOI is wrong (R2-1). The other 14 references were verified. |
| M10 (§3.0 problem statement) | Yes | Mostly | Eqs (1), (2), (4)–(7) match the code. Eq (3)/c_od omits the walk-only fallback (R2-5). The Exp 4–7 decision set omits h_k^0 and the max(60, h_k^0) cap (R2-9). |
| M11 (§2 units; A1 row; §8 rows) | Yes | Yes | The A1/D5 sentence is duplicated verbatim in two §8.1 rows (R2-22). |
| M12 (a)–(f) | Yes | (b) is wrong | The D2 description is false (R2-3). (e) is implemented in §7, but Highlight 4 still names a single cause (R2-16). |
| M13 (a)–(e) | Yes | Yes | Five-of-seven and the A1 rank (0.415 vs 0.685) checked. |
| M14 (abstract ≤ 250; summary table; highlights/keywords; scope sentence; §11 bullet; fragment; safeguard bullet) | Yes | Yes | 239 words; highlights 70–78 characters. Edit 7 rightly departs from the adjudication's wrong wording ("non-binding at the best-known REF plan"), which §5.6 contradicts. |
| M15 (§8.0; Data availability; status box; tag wording; App. A contract column) | Yes | Yes | Contract digests verified: `45e23ae01be4d071`, `2125984c82b60a83`, `395ee3c960f51935`, `0f62aeabfa341a98`, `7157ce1de9373420`. |
| M16 (a)–(c) | Yes | Yes | 2,516.65 and 68.3 verified. |
| M17 | Yes | Yes | — |
| m1–m10, m12–m19, m21–m26, m28–m32 | Yes | Yes, with exceptions | m7: Appendix A still has "−6.65% ±0.06" (R2-21). m30: not in the abstract (the abstract does not name the stop, so acceptable). m27: optional, not done (acceptable). |
| §4.2 (R12 "E1–E18"; R13–R16) | Yes | R16 partly | R16 is correct for D1. The parallel §5.1 sentence about D2 is wrong (R2-3). |
| §7 issue 13 ("closest cell") | Report yes | — | Not propagated to README:295, HANDOFF:164, FUTURE:14/85 (R2-12). |

---

## Numbered comments

### R2-1 — Hooker (1995) carries Barr et al.'s DOI — IMPORTANT

* **Location:** References, Hooker entry: "doi:10.1007/BF02430363".
* **Problem:** That DOI resolves to Barr, Golden, Kelly, Resende and Stewart, "Designing and reporting on computational experiments with heuristic methods", *J. Heuristics* 1(1):9–32. It is the paper listed directly above Hooker. Hooker's paper is 10.1007/BF02430364. The error comes from adjudication §6, row 9 ("DOI from unpaywall link"); the unpaywall link it used is Barr's.
* **Evidence:**
  * https://link.springer.com/article/10.1007/BF02430363 returns Barr et al., vol. 1, issue 1, pp. 9–32, Sept. 1995.
  * MaRDI portal (https://portal.mardi4nfdi.de/wiki/Testing_heuristics:_We_have_it_all_wrong) gives Hooker's DOI as 10.1007/BF02430364.
  * The Springer page for BF02430364 could not be fetched: the fetch proxy rate-limited it (HTTP 429).
* **Fix:**
  * Hooker: replace `doi:10.1007/BF02430363` with `doi:10.1007/BF02430364`.
  * Barr et al.: complete the entry as "*Journal of Heuristics* 1(1), 9–32. doi:10.1007/BF02430363".
  * Append an erratum note to adjudication §6 if a review log is kept.

### R2-2 — Common-lines bound arithmetic mislabelled — IMPORTANT

* **Location:**
  * §5.4 Conditions: "Crediting N4 with its whole common-lines bound and N3 with none (93,300 min) still leaves Δ43 positive".
  * §8.1 row "Cross-route common lines": "crediting all of N4's bound and none of N3's, 93,300 min".
* **Problem:** Crediting N4 with all of its bound and N3 with none reduces Δ43 by N4's whole bound, 107,248 min. The figure 93,300 = 107,248 − 13,947 is the net with *both* bounds credited. That is the milder case, not the worst case for N3. The conclusion survives (107,248 < 226,948 < 283,973), but the stated figure is wrong.
* **Origin:** The registered `EXPERIMENT4_ORIGINAL_QUESTION_ADDENDUM.md:245` (immutable), repeated in adjudication M5 and §7 item 5.
* **Evidence:**
  * `outputs/exp4_addendum/diag_N4.json → common_lines_bound.total_bound_min` = 107,248.12;
  * `diag_N3.json → … total_bound_min` = 13,946.90;
  * `DELTA43.json` effect = 283,973.37.
* **Fix (§5.4):** replace the sentence with "Crediting N4 with its whole common-lines bound and N3 with none (107,248 min) still leaves Δ43 positive (net of both bounds, 93,300 min)".
* **Fix (§8.1):** in the same cell, write "crediting all of N4's bound and none of N3's (107,248 min; 93,300 net of both) still leaves Δ43 positive".
* **Errata:** add a one-line note that the Exp 4A addendum's wording at line 245 mislabels the case. The addendum is registered, so the note goes in the report or in a future errata file.

### R2-3 — D2 misdescribed as pre-Model-B and as a search-effort plateau — IMPORTANT

* **Location:** §5.1, "Where service moves": "…with returns plateauing quickly in search effort (D2). Neither is re-verified on the certified Model B plans…".
* **Problem:** D2 ("Frequency-only returns plateau fast") is about the λ frontier, not search effort. It carries an explicit addendum: "**Confirmed on the converged Model B frontier, 2026-08-27** (gate 4 certification…)". Its table is the same as the report's own λ table: −6.602 / −7.125 / −7.247 / −7.276%. The statement is therefore false on both counts, and the report contradicts itself a few lines later.
* **Origin:** Adjudication M12(b) ("D2 is of the same vintage") is wrong. The original draft's "as search effort grows" was already a misreading.
* **Evidence:** `DISCOVERIES.md:36–72`; `outputs/canonical/exp1_final.json → frontier`.
* **Fix:**
  * Rewrite the paragraph as: "**Where service moves.** A pre-Model-B analysis found frequency moving from the most frequent routes toward the 30–120-minute tier (D1). It is not re-verified on the certified Model B plans or checked for seed agreement, and is not a finding of this report (R16). Returns in λ do plateau: past λ = 4 the last 0.15 points of unserved demand cost 0.25 points of generalized cost (D2, confirmed on the certified Model B frontier; table below)."
  * Leave R16 as written, since it concerns D1 only.

### R2-4 — Stale "pending" statements about `outputs/SUPERSEDED.md` — IMPORTANT

* **Location:**
  * Data and code availability, Artifacts bullet: "the entry for `outputs/exp2b_certification.superseded.json` is pending (Appendix A)";
  * Appendix A, last paragraph: "`outputs/SUPERSEDED.md` does not yet index that file either; its entry is pending."
* **Problem:** Commit `f0db4729` added the entry (`outputs/SUPERSEDED.md:118–129`, block `exp2b-magnitude-superseded`). The report now contradicts the repository it describes.
* **Fix:**
  * Delete "; the entry for … is pending (Appendix A)".
  * Replace the Appendix A sentence with "`outputs/SUPERSEDED.md` indexes it (block `exp2b-magnitude-superseded`)."

### R2-5 — Problem statement omits the walk-only (intrazonal) fallback — IMPORTANT

* **Location:** §3.0, after eq (3): "c_od(h) = min over π ∈ Π_od of c_π(h); c_od = ∞ if Π_od is empty." The definition of U(h) in (5) depends on it.
* **Problem:** The code takes `od = min(od, od_walk_only)` (`src/cota_opt/pathset.py:533`, also `:570`). `od_walk_only = 0.0` wherever the origin and destination zone are the same (`pathset.py:246–250`). Such pairs are served at zero generalized cost even with no transit path, so they are never structural or discouraged unserved demand. The editor required the equations to match the code (adjudication §3.3 implementer note).
* **Fix:** amend to "c_od(h) = min{min over π ∈ Π_od of c_π(h), c_od^walk}, where c_od^walk = 0 for intrazonal pairs (origin zone = destination zone) and ∞ otherwise (`pathset.py:246–250, 533`); c_od = ∞ only if both are unavailable." Add the same clause to the "structural" definition in the Glossary.

### R2-6 — "Every number is canonical" claims contradicted by the revision's own sources — IMPORTANT

* **Location:**
  * Status bullet 2: "Every number is transcribed from a named canonical artifact (Appendix A)";
  * Data availability: "every number traces to a file under `outputs/` indexed by `outputs/CANONICAL_RESULTS_v5.json`".
* **Problem:** The revision adds numbers that are explicitly not canonical:
  * 22% / 78% (`exp3_ablation_…`, "not canonical");
  * the LODES counts (run log `outputs/verify.log`, "not a canonical artifact");
  * +9.28% (`EXPERIMENT6_CLOSEOUT.md`, "orientation only");
  * the post hoc F1 numbers (`EXP7_F1_DECISION_SPACE.json`, "not in registry v5", Appendix A).
* **Fix:**
  * Status bullet: "Every number is transcribed from a named artifact (Appendix A). Numbers not indexed by registry v5 are labelled (run log, historical ablation, closeout orientation figure, post hoc addendum)."
  * Data availability: "…traces to a named file (Appendix A); most are indexed by `outputs/CANONICAL_RESULTS_v5.json`, and those that are not are labelled there."

### R2-7 — §5.4: "Nothing is known about the 1,800 proposals" next to an audit of one of them — MINOR

* **Location:** §5.4, "The leader is not identified" bullet, and the following "promotion cap was invalid" bullet.
* **Problem:** The second bullet reports an excluded proposal (discovery rank 237) that certifies better than the legacy leader.
* **Fix:** "Apart from the one audited proposal (discovery rank 237, below), nothing is known about the 1,800 proposals the promotion cap excluded (registry `exp4.limitations`)."

### R2-8 — Empty route-periods: the wrong mechanism is cited — MINOR

* **Location:** §3.1 first bullet, "The other 61 cannot be opened (`allow_new_service_in_empty_periods: false`)".
* **Problem:** That config key is read by no code (grep of `src/cota_opt` and `scripts/` finds no reader). Route-periods without baseline trips are simply never created as decision variables: `exp1.py:71–78` builds services only from observed trips.
* **Fix:** "The other 61 are not decision variables: the model builds a route-period only where the feed has trips (`exp1.py:71–78`; the config flag `allow_new_service_in_empty_periods: false` states the same rule but is not read by code)."

### R2-9 — Exp 4–7 decision set incomplete in §3.0 — MINOR

* **Location:** §3.0, Decisions, second bullet: "Experiments 4–7: h_k ∈ L ∪ {OFF}".
* **Problem:** `build_ladders` (`frequency.py:388–436`) builds {h ∈ L : h ≤ max(60, h_k^0)} ∪ {h_k^0} ∪ {max(60, h_k^0)} ∪ {OFF} with `allow_off`. The baseline off-ladder value and the cap are retained in Exp 4–7 as in Exp 1. Experiments 2–3 (no OFF) are not stated at all.
* **Fix:**
  * Exp 4–7: "Experiments 4–7: the Experiment 1 set plus OFF (`build_ladders(allow_off=True)`), subject to …".
  * Add: "Experiments 2–3: the Experiment 1 set on the edited network (no OFF)."

### R2-10 — Overstated terminology rule for "certified" — MINOR

* **Location:** §4, "'Certified' survives unqualified only inside artifact status strings".
* **Problem:** About 30 unqualified uses remain, e.g. the abstract ("certified frequency plans"), the §6.1 column header "certified", §5.3 "29 remain certified", §3.1 "Experiment 1's frontier is certified only from λ = 2". The §5 preamble maps each section to a meaning, which is acceptable, but the §4 sentence is false.
* **Fix:** "In prose, 'certified' always carries one of these meanings; §5's preamble states which applies in each subsection, and in §6.1 the 'certified' column means the value in each experiment's own closeout."

### R2-11 — Symbol clash in §3.0 — MINOR

* **Location:** §3.0. **K** is the set of route-periods (|K| = 173), and **K** / K_p are also the proxy caps in (7). **N** is used for directions (N_k) and for networks (N0/N3/N4).
* **Fix:** rename the caps to **V_p** ("V = (85.28, …)"), and the direction count to **d_k**.

### R2-12 — "Closest cell" wording not propagated downstream — MINOR

* **Location:**
  * `README.md:295` ("Re-optimized under Experiment 1's service rules");
  * `HANDOFF.md:164`;
  * `docs/FUTURE_EXPERIMENTS.md:14` and `:85` ("Re-optimize under Exp 1's rules (R1_H60)").
* **Problem:** The report adopted "the closest cell to Experiment 1's rules (R1_H60)" (adjudication §7 item 13; M13e). These editable documents now contradict it.
* **Fix:** replace each occurrence with "in the closest cell to Experiment 1's rules (R1_H60)".

### R2-13 — `docs/GLOSSARY.md` inconsistent with the report and the code — MINOR

* **Location:**
  * `docs/GLOSSARY.md`, "(8, 3) block certifier": "within ±3 ladder rungs".
  * No `B1_COMMONLINES` entry.
  * No structural/discouraged definition of unserved demand.
* **Problem:**
  * The code uses `K_RUNGS = 3`, "the delivered rung plus one either side" (`exp4_certify.py:78`), i.e. ±1. The report's §4 is correct; the glossary is not.
  * The report calls `docs/GLOSSARY.md` "the full glossary", yet that file lacks terms the report's Appendix B defines.
* **Fix:**
  * Replace "within ±3 ladder rungs" with "within a 3-rung window (the current rung and one either side)".
  * Add the Appendix B entries for `B1_COMMONLINES`, "Unserved demand" and "Objective (λ-weighted)".

### R2-14 — "for λ ≥ 3.22 the interval is empty" is imprecise — MINOR

* **Location:** §3.1, "The objective is not a welfare measure", item 2.
* **Problem:** The interval is empty iff (1/s + 60 + 60λ)/2 ≥ 210, i.e. λ ≥ 29/9 ≈ 3.2222. At λ = 3.22 the lower bound is 209.93, so the band (209.93, 210) is not empty.
* **Fix:** "for λ ≥ 29/9 ≈ 3.222 the interval is empty".

### R2-15 — Self-reference in §3.0 — MINOR

* **Location:** §3.0, last paragraph, "no cross-route strategy (§3, §8)", written inside §3.
* **Fix:** "(§3.1, §8.1)". Similarly, §8.0 and Glossary "(§3)" → "(§3.1)", and §1.1 "(§3.0, §8)" → "(§3.0, §8.1)".

### R2-16 — Highlight 4 names a single cause; §7 finding 2 names two — MINOR

* **Location:** Highlights: "Matching solver convergence, not nominal effort, erased a 0.5% routing gain".
* **Problem:** Per M12(e) and §7 finding 2, the 0.5% was produced by unmatched convergence *together with* a treatment-chosen start policy (D27).
* **Fix:** "Unmatched convergence and treatment-chosen solver starts produced a spurious 0.5% gain" (73 characters).

### R2-17 — Highlight 2 understates greenfield; Highlight 3 overstates "best" — MINOR

* **Location:** Highlights 2 and 3.
* **Problem:**
  * Greenfield was 8.5–9.7% *worse*, not "little or no gain".
  * "The best greenfield network" is not established: the leader is not identified (§5.4), and 1,800 proposals were never certified.
* **Fix:**
  * H2: "Through-routing and added stops gave little or no gain; greenfield was worse".
  * H3: "The best of 200 certified greenfield networks was 8.5–9.7% worse".
* Also, abstract: "best of 200 generated greenfield networks" → "best of 200 certified greenfield networks (of 2,000 generated)". 2,000 were generated (§5.4).

### R2-18 — Instance coverage of the common-lines bounds understated — MINOR

* **Location:** §3.1 Waiting bullet; R15.
* **Problem:** Adjudication M1 said the period coverage of the N3/N4 bounds is not recorded. It is: `diag_N3.json` and `diag_N4.json → periods` list all six periods, while N0's 0.516% covers am_peak and midday only. The three figures are therefore not on a common basis in coverage either.
* **Fix:** "…1.16% on N3 and 12.47% on N4 (Exp 4A instance, all six periods)".

### R2-19 — Abstract omits two caveats the body treats as central — MINOR

* **Location:** Abstract.
* **Problem:**
  * F4 is conditioned only on the path model. The waiting-model omission (common-lines bound 12.47% on N4 vs 1.16% on N3) runs the same way and is the larger exposure.
  * The Exp 3 leader's 20-restart regime (M6 edit 1) is absent.
* **Fix:** within the word limit:
  * "…conditional on path and waiting models that both fit it less well";
  * "the leader, an added stop measured at 20 restarts only, lies within its own sensitivity range".

### R2-20 — Same identifier for different things: errata E16–E18 vs FUTURE E16–E18 — MINOR

* **Location:** `docs/FUTURE_EXPERIMENTS.md` uses E10–E21 as experiment IDs. The errata use E1–E18. FUTURE "E18 Cross-route common lines" now cites "(errata E16)", while FUTURE E16 is a different item.
* **Fix:** in the report, always prefix: "errata E16" (already done) and "FUTURE E18". In FUTURE_EXPERIMENTS, add a header note: "Item numbers here are independent of `EXPERIMENT7_CLOSEOUT_ERRATA.md` row numbers."

### R2-21 — Appendix A retains "±0.06" — MINOR

* **Location:** Appendix A, first row: "−6.65% ±0.06".
* **Problem:** m7 removed "±" in favour of "solver seed SD".
* **Fix:** "−6.65% (solver seed SD 0.06 points)".

### R2-22 — Duplicated sentence in §8.1 — MINOR

* **Location:** §8.1, rows "Commute-only demand" and "Operationalization bounds". Both end with the identical two sentences: "A1 changes demand volume as well as pattern (as issued). At +100%, demand reaches the scale…".
* **Fix:** keep the sentences in "Operationalization bounds". In "Commute-only demand" write "A1 also changes volume (see Operationalization bounds)."

### R2-23 — Remaining gaps a journal would require (no new experiments) — MINOR

1. **Figures** are still missing (status box). A frontier figure and the F1 two-basin figure are essential for TR-A/C.
2. **Per-seed objective** for Exp 1 is not recorded. State in §5.1 that the −2.21% has no seed SD and that the "3-seed mean" in the all-levers table is computed from component means. This is already said in §5.1; the all-levers row should say "computed (linear), no SD".
3. **External benchmark:** no comparison of the Gen1 or block certifier on a standard benchmark instance (e.g. Mandl). Acknowledge this in §8.0 internal validity as a limitation rather than run it.
4. **Exposed share:** the share of baseline flow in the non-monotone cost band (173.3–210 min at λ = 2) is unreported (deferred per M3). Say explicitly in §8.1 that this is the unquantified size of the construct-validity threat.

---

## Numbers spot-checked (beyond the 49 verifier claims)

All match the stated artifact unless marked ✗ or ⚠.

**Exp 1 and the §3 objective analysis**

* Thresholds 173.3 / 143.3 recomputed from s = 0.9/150 and λ·60. The 3.22 cut-off ⚠ (R2-14). r(120) = 0.64. Retention parameters 60 / 210 / 0.10 in `assumptions.yaml` and `retention.py`.
* Eqs (1), (2) (Model A and B multipliers), (4), (5) and (6) checked against `pathset.py:336–370, 513–514, 597–627`, `retention.py`, `exp2.py:126–133` and `frequency.py:242`. Eq (3)/c_od ✗ (R2-5).
* Cost weights 2/2/1/2/+10 and the wait rule (12 min; 0.25): `cost_weights.yaml`, `assumptions.yaml`. Ladder {5 … 60}: `constraints.yaml`. Max rounds 3 (≤ 2 transfers); 4 paths per OD.
* Envelope K = (85.28, 162.01, 159.17, 176.49, 140.19, 35.56) and 2,517.18: `COMMON_RESOURCE_ENVELOPE.json`.
* Exp 1 headline: −6.652 / 3.299 / 0.878 / −2.344%; SDs 0.064 / 0.032 / 0.041 / 0.011.
* λ frontier: +15.31 / +6.85 / −1.42 / −6.60 / −7.12 / −7.25 / −7.28%.
* Plan disagreement: 19.1% / 19.7% / 6.9 min. Baseline: 10,262 / 20,687 → 9,583 / 21,366.
* Objective change −2.208% (linear) / −2.213% (frontier). 66.8% and 66.3% served.
* 22% / 78% split (2,380.3 / 8,505.8; commit `acb0e919`). 1/0.649 = 1.54×. 24.7% / 64.9% / 78,210 / 317,706 / 823,915 (`verify.log`).
* 30,949 derivation (38,694 × 0.9598 / 1.2). 14 express routes (D4).

**Exp 2B and Exp 3**

* Exp 2B: +0.0902% / +0.0540% / 0.314 floors / 0.287 floor; superseded 0.0065.
* Exp 3: −0.18657%, SD 0.002375, ratio 78.55; 29 certified (23 at 40 restarts, 6 at 20); smallest certified 0.0096% (→ "0.01–0.19%"); escalation contract `45e23ae01be4d071`.

**Exp 4N, 4A and 5**

* EXP4N: leader 3,223,885.9475, margin 0.387006%, Spearman +0.3566, 7,296 / 19,900 = 36.7%, rank 185, contract `2125984c82b60a83`.
* Exp 4A: Δ43 283,973.37 / 9.659%; +9.28% (272,400.39, Exp 6 closeout); +8.547% (`EXP7_ANALYSIS f4`); 1.1-point spread.
* Common-lines bounds 1.164% / 12.472% / 0.516%; bound minutes 13,946.9 / 107,248.1 ✗ (R2-2). Diag periods: six for N3/N4, two for N0.
* Exp 4A served / structural shares 53.1 / 35.5% (N3) and 36.3 / 54.7% (N4); max load 68.3. Fixed-plan λ crossover 1.087.
* Audit: rank 237, 0.0147%. Discovery span 0.159% vs exact 2.28% (STATE_OF_PLAY:1121).
* Exp 5: +0.57 / +2.05; −0.74 / −0.94 / −1.48; 8.07–11.59%; 1.7034% residual; 4.4× margin; 12 pairs.

**Exp 6 and Exp 7**

* Exp 6 prices (N0 / N3): 0.212 / 0.250, 0.244 / 0.321, 0.428 / 0.477, 0.440 / 0.485, 0.482 / 0.524, 0.575 / 0.634, 0.912 / —.
* Exp 7 BASE re-closed prices: 0.260 / 0.287, 0.146 / 0.225, 0.389 / 0.436, 0.489 / 0.522, 0.531 / 0.561 (R3_SPAN / B2 0.500), 0.633 / 0.671, 0.967. Movement −0.098 to +0.058; order reversal of c = 0.05 vs S05 on both networks.
* Exp 7 Stage 1:
  * F1 −6.998 to −1.897, BASE −6.024;
  * B1 −5.99 / +7.86 (F2 +0.130, F3 −0.129); X_TOPK40K −5.49 / +8.82; X_ROUNDS4 −6.03 / +9.67;
  * F2 −0.226 / +0.166, BASE 0.00648; F3 −0.405 / +0.323; F4 −1.31 / +19.35;
  * F6 N0 11 / 13 and N3 5 / 12 SIGN_ROBUST; λ = 4 flips −0.00685 / −0.00988;
  * N3 R1_H20 feasibility map (BASE, A3 ×3 infeasible; A7 ×10 not proven).
* Exp 7 Stage 2:
  * F4 6.766–30.79, −0.981 at λ = 1; AF1 F4-track 0.161–0.184;
  * REF two fixed points 2,940,186 / 2,935,446 (0.161%), F1 −5.43 / +30.48, 17 / 48 OFF;
  * R1_H60 F1 −6.57, −6.83, −7.00, −5.53, −6.06, −2.14 (→ −2.1 to −7.0), λ = 1 +0.118; five of seven initial records;
  * closure gaps > 0.03% at 5 of 7 levels (0.038–0.40%).
* Exp 7 design and metadata: 4 × 48 = 192; abstract 239 words; highlights ≤ 78 characters.
* Certifier: K_RUNGS = 3 (±1), rotation N/2 = 4. D33 0.001837 points; D33-B 0.0018970%.

**References.** 14 of 15 verified by title, authors, year, venue and pages:

* Barr et al. 1995 — Springer;
* Cancela et al. 2015 (DOI ✓) — RePEc;
* Ceder & Wilson 1986 — TRID 238094;
* Chriqui & Robillard 1975 (DOI ✓) — RePEc;
* Durán-Micco & Vansteenwegen 2022 (DOI ✓) — RePEc;
* Furth & Wilson 1981, TRR 818:1–7 — TRID 174187;
* Guihaire & Hao 2008 — RePEc;
* Ibarra-Rojas et al. 2015 (DOI ✓) — RePEc;
* Lee & Vuchic 2005 — ASCE Library;
* Mohring 1972, 62(4):591–604;
* Rardin & Uzsoy 2001 — IAOR;
* Spiess & Florian 1989 — RePEc / TRID;
* Walker 2008 (DOI ✓) — RePEc;
* Cambridge Systematics 2010 — FHWA copy.

Hooker 1995: title, venue and pages are right, but the DOI is ✗ (R2-1). MaRDI lists Hooker's publication date as 1996. The common citation, and the issue it shares with Barr et al. (vol. 1, issue 1), is 1995, so no change to the year is recommended.
