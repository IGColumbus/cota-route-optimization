# Experiment 7: replacement protocol (proposed)

**Dated 2026-09-29.**

**Status: PROPOSED — for Ian's review. Not frozen, and no sensitivity
experiment has been run under it.** It comes into force only when Ian approves
it and `scripts/exp7_freeze.py` freezes `outputs/exp7/EXP7_CONTRACT.json`.
On approval, this line changes to `Status: APPROVED <date>`; the freeze script
checks for that line.

---

## 0. The original is unavailable, and this document replaces it

**The original.**

* Ian's 23 September Experiments 5–7 protocol was "frozen as issued" per
  `docs/EXPERIMENTS_5_7_PROTOCOL_INTAKE.md`.
* Its Exp 7 section is **not in the repository**. On 2026-09-28/29 I searched:
  * all git history (`git log -S`);
  * the project knowledge base;
  * the connected folders on Ian's computer;
  * this session's transcript.
* Ian has chosen not to block on recovering it.
* There is therefore **no** `docs/EXPERIMENT7_PROTOCOL_AS_ISSUED.md`, and
  none will be created without the original text.

**What this document supersedes.** Once approved, it replaces every
unverified reference to that text. The replacement is deliberate, not a
reconstruction. It does **not** recover or restate:

* the original findings F1, F2, F3 or F5;
* the original A8 retention levels;
* the "five Exp 7 dimensions";
* the original band wording.

Where the repository refers to those items (see §1.2), the reference is marked
**unverified** and is replaced by the choices in §§2–5.

**What stays in force alongside it.** `docs/EXPERIMENT7_AMENDMENT.md` keeps
governing the search procedure, anchor validation, classification mechanics
and the firewall. That amendment was written against the missing text. This
protocol is now its base. Where the two differ, this protocol wins.

**Labels used throughout:**

* **[INHERITED]** — a requirement documented in a committed repository file,
  cited by path.
* **[NEW]** — a choice proposed here, with its rationale.
* **[FROM EXP 6]** — a number from the frozen Exp 6 evidence.

---

## 1. Evidence base and inherited requirements

### 1.1 Documented requirements carried into Exp 7 [INHERITED]

| # | requirement | source |
|---|---|---|
| I1 | F4 is redefined: "Greenfield N4 does not beat N3 or N0 under the matched modeled contract; classify the sign/magnitude robustness of that null/negative result." | `EXPERIMENT6_D39_AMENDMENT.md` §4; `EXPERIMENT6_PROTOCOL.md` §16 |
| I2 | F6 is redefined: "policy price on N0 and N3 under the Exp 6 basin-closure procedure." | same |
| I3 | D39 carries into Exp 7: robustness runs may not compare treatment-specific local basins as though the differences were model sensitivity. | same |
| I4 | The retention curve must be a Class A perturbation, added before Exp 7 runs. | `docs/RELEASE_AND_REPORTING_GUIDELINES.md` (calibration register, "Before Exp 7" checklist) |
| I5 | "Stability words come from Exp 7": only preregistered band wording describes stability. | release guidelines, reporting rule 5 |
| I6 | "Certified is not significant": an effect smaller than its Exp 7 magnitude range is reported as "within model uncertainty". | release guidelines, rule 3 |
| I7 | λ = 2 is the policy choice, and the certified frontier is λ ≥ 2. | release guidelines, calibration register |
| I8 | The demand-robustness claim forms `sign`, `magnitude_stable` (a factor-of-two band), `not_od_truncation` and `not_commute_geometry` (a stress direction, never an estimate). | `EXPERIMENT4_DEMAND_ROBUSTNESS.md`; `src/cota_opt/exp4_claims.py` |
| I9 | The Exp 4 perturbation plan (never run): `scale_0.7`, `scale_1.5`, `periods_flat` (toward midday/evening), `periods_peaked` (toward am/pm peak), `noncommute_30`, `noncommute_50`, `retention_wider_od` (top 40,000 OD pairs). No tilt strength or non-commute parameterization is given. | same |
| I10 | The Exp 4A deferrals to Exp 7: gate 4-12 demand robustness and the wider OD universe. | `docs/EXPERIMENT7_AMENDMENT_DRAFT.md` §3 row 6 |
| I11 | The documented model caveats: the cross-route common-lines omission (12.47% of GC on N4, `potentially_frontier_changing`); the path model fits N4 worse (8.7–34.8% improvable flow); the fixed-plan λ sign flip at λ ≈ 1.087. | same, rows 7–9 |
| I12 | D33-B (0.0018970%) is veto-only. | `EXPERIMENT6_D39_AMENDMENT.md`; `docs/EXPERIMENTS_5_7_PROTOCOL_INTAKE.md` |
| I13 | Ian's Exp 7 preparation instructions (2026-09-29): all-pairs cross-seeding to a fixed point with a frozen ceiling; the full policy graph at every level; matched F4 opportunity; target validation of every anchor; the §7 rules; firewall admission for every reported comparison. | recorded in `docs/EXPERIMENT7_AMENDMENT.md` |

### 1.2 References that remain unverified (superseded, not used)

* The "Class A matrix", and A8's original preregistered levels (release
  guidelines checklist, marked done).
* "The five Exp 7 dimensions" (release guidelines, outline item 6).
* The "preregistered band wording" (rules 3 and 5, outline item 6).
* The original F1, F2, F3 and F5.

### 1.3 Frozen baseline evidence [FROM EXP 6]

The closed references and policy prices are in `EXP6_CLOSEOUT_TABLES.md`:

* **N0 closed REF: 2,941,892.37.** Policy prices run from 0 (R2_S25, R2_S10)
  to +0.912% (R1_H20).
* **N3 closed REF: 2,935,166.03.** Policy prices run from 0 to +0.634%
  (R1_H30). N3 R1_H20 is `INFEASIBLE_UNDER_ENVELOPE`.
* **N3 − N0 at matched policy:** −0.153% to −0.229%, 13/13 admitted.
* **Historical N4 comparisons** (preserved as admitted, not replaced):
  * Exp 4A Δ43 = +9.66%;
  * Exp 5 N4 − N0 = +8.07% to +11.59%, 16/16.

---

## 2. Findings under test

The labels F4 and F6 are used **only** because their current definitions are
documented (I1, I2). The other findings get new identifiers, so nothing is
mistaken for a recovered original.

### F4 — N4 does not beat N0 or N3 [INHERITED definition; NEW test design]

* **Quantities:**
  * obj(N4) − obj(N3) and obj(N4) − obj(N0), both REF;
  * closed on the **F4 track**: same procedure for all three networks, no
    policy closure (amendment §5).
* **Claims:** `sign` (N4 worse by more than τ) and `magnitude_stable`, at
  every level.
* **Retired:** `ordering` and the old `beats_noise` are not tested (amendment
  §2). Rationale: the first is false at baseline, and the second's in-run
  noise floor does not exist (D32).
* **Reporting:** the historical Exp 4A and Exp 5 numbers are reported next to
  F4 under their own labels.

### F6 — policy prices on N0 and N3 [INHERITED definition; NEW test design]

* **Quantity:** each regime's closed price against the closed REF at the same
  level and network.
* **Scope:** all 14 cells, including R3, R4_C00, B1, B2, R2_S25 and R2_S10,
  at every level.
* **Claims:**
  * `sign` — guaranteed by closure and nesting; a failure is a bug;
  * `magnitude_stable`;
  * `rank_stable` — tie-aware;
  * `zero_status` — whether a zero price is supported at that level
    (`ZERO` / `ZERO_DISTINCT_PLAN` / `ZERO_NOT_ESTABLISHED`);
  * `feasibility_status` — for N3 R1_H20 and any cell that becomes empty.

### AF1 — N3 is slightly better than N0 at matched policy [NEW; identified by Exp 6]

* **Quantity:** obj(N3) − obj(N0) at each policy cell, on the F6 track.
* **Claims:** `sign` (negative) and `magnitude_stable`.
* **Rationale:** it is small (about 0.2%) but consistent across 13 admitted
  comparisons in Exp 6. Its cause has not been separated, so it is tested for
  stability only. **No causal claim.**

### AF2 — frequency reallocation beats the current schedule on N0 [NEW, proposed]

* **Quantity:** closed N0 REF objective minus the objective of N0's current
  (baseline-headway) plan, evaluated through the same production path at the
  same level.
* **Claims:** `sign` (the reallocation improves) and `magnitude_stable`.
* **Rationale:** this is the project's stated mission quantity (AGENTS.md).
  Exp 7 is the first point where it can be given stability words.
* **Scope:** N0 only. N3's current plan does not fit the envelope (Exp 6 D35
  record `base_plan_trims_to_fit_envelope`), so N3 has no untrimmed
  current-schedule reference.
* **Cost:** one fixed-plan evaluation per level (about 5 min).
* **Caveat:** a fixed-plan evaluation is not a certified cell. It is reported
  as a **descriptive** comparison, not a firewall-admitted one, unless you
  prefer to drop AF2.

### What each finding does NOT claim [NEW]

* **Served demand, generalized cost, GC per trip and OFF count get no
  stability label.** Exp 6 showed a flat multi-basin objective: closure moved
  N0 REF served demand from 16,527 to 21,144, and OFF count from 50 to 15,
  while the objective moved 0.127%. These are reported per level as
  descriptors of the winning plan, with its digest.
* **No finding is a statement about real riders.** All outputs remain
  "uncalibrated" (release guidelines, calibration register).

---

## 3. Sensitivity dimensions and exact levels [NEW, except where marked]

**BASE.** Everything exactly as in Exp 6: λ = 2, `same_route` waiting,
retention 60/210/0.10, commute LODES top 20,000, the period shares in
`config/assumptions.yaml`, max_rounds 3. BASE reproduces Exp 6 bit-exactly
(preflight G3, 3/3 cells).

**The matrix.** 11 levels in 7 dimensions, declared in
`outputs/exp7/EXP7_LEVELS.PROPOSED.json`:

| dimension | level | exact setting | origin |
|---|---|---|---|
| λ (value judgement) | `LAM_1_5` | λ = 1.5 | NEW |
| | `LAM_4` | λ = 4.0 | NEW |
| waiting model | `WAIT_PATTERN` | `pattern` (common-lines waiting across routes) | NEW level; addresses caveat I11 |
| retention curve | `RET_STRICT` | full 45 min, zero 150 min, floor 0.05 | NEW (I4 requires the dimension; the levels are new) |
| | `RET_LENIENT` | full 90 min, zero 300 min, floor 0.20 | NEW |
| temporal profile | `PERIODS_FLAT` | `tilt_periods` toward midday + evening, strength 0.5 | direction INHERITED (I9); strength NEW |
| | `PERIODS_PEAKED` | toward am_peak + pm_peak, strength 0.5 | same |
| spatial shape | `NONCOMMUTE_30` | blend share 0.30 of `noncommute_proxy`: zone weight = workers + jobs; Euclidean centroid distance; decay 4 km | shares INHERITED (I9); parameterization NEW |
| | `NONCOMMUTE_50` | share 0.50, same parameterization | same |
| OD coverage | `TOPK_40K` | top 40,000 OD pairs through the harness's own LODES pipeline, same total trips | INHERITED (I9, I10) |
| path enumeration | `ROUNDS_4` | `path_assignment.max_rounds` = 4 | NEW |

**What each period tilt does to the period shares:**

| level | early | am | midday | pm | evening | owl |
|---|---|---|---|---|---|---|
| BASE | .050 | .220 | .330 | .240 | .120 | .040 |
| `PERIODS_FLAT` | .041 | .180 | .404 | .196 | .147 | .033 |
| `PERIODS_PEAKED` | .041 | .268 | .268 | .293 | .098 | .033 |

**Rationale by dimension:**

* **λ.** λ is a value judgement, so it is the dimension a reader most needs
  varied.
  * λ = 4 doubles the weight on unserved trips and stays in the certified
    region.
  * λ = 1.5 sits below the certified frontier (I7) but above the fixed-plan
    flip at ≈ 1.087 (I11). It asks whether conclusions survive a lighter
    unserved-trip weight. Every λ = 1.5 result carries the label "outside the
    certified λ frontier".
* **Waiting model.** The common-lines omission is the documented caveat most
  likely to move F4 (I11: 12.47% of GC on N4, `potentially_frontier_changing`).
  Reach preflight: `pattern` changes the evaluation of a fixed plan by about
  +2.6% on N0.
* **Retention (I4).** The curve is linear, from 1.0 at `full` to the floor at
  `zero`.
  * Each level moves **all three** parameters in one direction, so each is a
    coherent alternative behavior rather than a one-knob probe:
    * strict: discouragement starts at 45 min instead of 60, reaches the floor
      by 150 min, and the floor halves;
    * lenient: 90 min, 300 min, and the floor doubles.
  * The brackets are about ±25–50% on the thresholds. That is wide enough to
    matter and not so wide as to be implausible for a crude discouragement
    proxy (the config calls it "not a mode-choice model").
  * These are **not** the original A8 levels, which are unrecovered.
* **Temporal and spatial.** These are the directions the Exp 4 plan committed
  to (I9). Strength 0.5 is the `tilt_periods` docstring's own example ("half
  again as attractive").
  * The non-commute proxy uses workers + jobs as zone activity, and 4 km, the
    function's default decay.
  * At a 30% share, the blended OD table correlates only 0.49 with commute
    flows. That is a strong stress direction, as intended; it is not an
    estimate (I8).
* **OD coverage.** The 40,000 pairs discharge the Exp 4A deferral (I10) and
  test `not_od_truncation` (I8).
* **Path enumeration.** Of the path-model knobs, only `max_rounds` reaches
  the production evaluator:
  * `max_paths_per_od` is inert at 2 and at 8;
  * `n_random_scenarios` is inert, because `exp3_score` passes 0;
  * walk and access radius are fixed when the harness is built.

  One extra boarding is the smallest meaningful widening.

### Deliberately NOT run as dimensions, with claim bounds [NEW]

* **Uniform demand scale (`scale_0.7`, `scale_1.5`, I9).**
  * The certified evaluator runs with `with_crowding=False` (`exp3_score`).
    Every component of a plan's objective then scales exactly with the OD
    total. The reach preflight measured the ratio at 1.4999999999999998 on
    both networks, with GC per served trip unchanged.
  * The minimizer and every price are therefore invariant **by
    construction**, up to floating-point tie resolution.
  * Running the scale levels would spend about 60 h certifying an identity.
  * Reported instead as: "invariant to uniform demand scale because crowding
    is not modeled — a model property, not evidence of robustness".
* **Path-set width and scenario count.** Inert in the production path (above).
  F4, F6 and AF1 are stated as conditional on the enumeration design.
* **Walk/access radius, envelope, fleet, cost weights other than λ.** Not
  varied. Claims are conditional on them. The fleet materializer defect still
  blocks any fleet statement.
* **Non-commute travel as such.** Never modeled. Surviving the spatial stress
  test does not mean non-commute demand was represented (I8).

---

## 4. Search procedure [INHERITED instructions (I13); mechanics in the amendment]

The combined closure, anchor validation, empty-cell handling and firewall
rules are as in `docs/EXPERIMENT7_AMENDMENT.md` §§3–6 and §9, with one
change:

**X-stage scope [NEW, needs your decision].** Cross-level all-pairs runs
within **each dimension plus BASE**. BASE is in every dimension's group, so
any level's plan reaches every other level of its dimension directly, and
reaches other dimensions via BASE on the next pass.

* **Rationale:** the levels of a dimension are alternative models of the same
  thing. Transfers there are the D39-relevant ones. Across dimensions (say, a
  λ = 4 plan offered to a period-tilt level) the search opportunity has no
  special claim.
* **Cost:** 30 X pairs instead of 132, which saves about 346 h.
* **What it gives up:** direct cross-dimension transfers. It is still never a
  winner-only chain within a dimension.
* **Your earlier instruction** said "all-pairs within each declared network
  and compatible policy regime". If you read that as all levels, the cost is
  about 519 h instead of 173 h (see §6).

---

## 5. Stability classifications [NEW band wording; I5, I6 require it]

Every classification uses **closed**, firewall-admitted values only, at
matched level. τ = 1e-9 objective units (amendment §7).

**Per dimension**, for a finding's quantity q (a difference or a price):

| label | condition |
|---|---|
| `STABLE` | sign(q) equals the BASE sign at every level of the dimension, **and** q(level)/q(BASE) lies in [0.5, 2] (the factor-of-two band, I8) |
| `SIGN_STABLE` | sign preserved at every level; the magnitude leaves the factor-of-two band at one or more |
| `SENSITIVE` | the sign flips, or q enters the tie band at one or more levels. The level is named. This is a finding, not a failure |
| `UNDEFINED` | q is undefined at a level (e.g. an empty cell). The feasibility transition is reported |

**Across all dimensions**, for each finding:

* **`ROBUST`**: `STABLE` in every dimension.
* **`ROBUST_IN_SIGN`**: at least `SIGN_STABLE` everywhere, and not `ROBUST`.
* **`CONDITIONAL ON <dimensions>`**: `SENSITIVE` or `UNDEFINED` in the named
  dimensions.
* **Magnitude range:** the [min, max] of q over BASE and every level. Per
  rule I6, a certified effect whose range includes 0 is reported as "within
  model uncertainty".
* **Level outside the certified frontier:** λ = 1.5 enters the
  classification, but a finding that is `SENSITIVE` **only** at λ = 1.5 is
  reported as "`ROBUST` within the certified λ frontier; sign changes at
  λ = 1.5".

**Additional classifications for F6:**

* **`rank_stable`:** yes if the tie-aware competition ranks are identical at
  every level. Otherwise each rank change is listed.
* **Zero prices:** classified per level, never inherited from BASE (amendment
  §7.1).

**Basin guard (I3).** Every row reports the basin correction (closed −
initial at that level) next to the sensitivity effect (closed(level) −
closed(BASE)). A label is **withheld** (`BASIN_DOMINATED`, in place of any
other label) when:

* the sensitivity effect is smaller in magnitude than the largest basin
  correction seen for that quantity; **and**
* the classification would change if the greedy-only value were used.

**D33-B (I12).** Veto-only. Exceeding D33-B never makes an effect
significant or stable.

---

## 6. Matrix, runs and compute [NEW]

**Tracks:**

* **F6:** N0 and N3 × 14 policies × {BASE + 11 levels}, with W + X closure.
* **F4:** N0, N3 and N4 × REF × {BASE + 11 levels}, X closure only.
* BASE reuses Exp 6 records (G3, G6).

**Estimate** (`exp7_freeze.estimate_dims`). Throughput is as measured: N0
about 610 s and N3 about 615 s per certification, and N4 1,024–1,150 s. Every
pass-1 X candidate is assumed to run, plus a 25% second pass.

| option | new levels | X pairs | certifications | F4 wall h | F6 wall h | total wall h (2 lanes) |
|---|---|---|---|---|---|---|
| **proposed** (X within dimension + BASE) | 11 | 30 | ≈ 1,992 | 16 | 157 | **≈ 173 h (7.2 days)** |
| X across all levels | 11 | 132 | ≈ 5,944 | 58 | 461 | ≈ 519 h (21.6 days) |
| proposed, without `LAM_1_5` | 10 | 26 | ≈ 1,762 | 14 | 139 | ≈ 153 h |

**Additional costs:**

* sentinels (included);
* the remaining preflight: matrix reach on N0, N3 and N4, about 3 h,
  **running now**;
* the analysis (minutes).

**Order.** The F4 track runs first (about 16 h). It answers the headline
negative result and exercises the whole pipeline, including N4, before the
157 h F6 track starts.

---

## 7. Readiness gates

Unchanged from the amendment §10, except that G1 becomes "this protocol
approved".

**Current state, from executed checks, not predicted:**

| gate | state | evidence |
|---|---|---|
| G1 protocol approved | **FAIL**: awaiting your review | this file, `Status: PROPOSED` |
| G2 levels named and frozen | **FAIL**: the levels are proposed, not frozen | `EXP7_LEVELS.PROPOSED.json` |
| G3 BASE reproduction | PASS, 3/3 bit-exact | `preflight/base_repro/BASE_REPRO_VERDICT.json` |
| G4 matrix reach N0, N3, N4 | **NOT YET PASSED**: running | `preflight/reach_matrix_{N0,N3,N4}.json` |
| G5 unit tests | PASS (as last run) | `tests/test_exp7_*.py` |
| G6 source unchanged | PASS, `b63ae2dba134245e` | — |
| G7 transfer/refusal/emptiness + firewall | PASS, 7/7 and 8/8 | `preflight/transfer/`, `preflight/FIREWALL_PREFLIGHT.json` |
| X-stage scope | **OPEN**: your decision (§4) | — |
| AF2 in or out | **OPEN**: your decision (§2) | — |

Other gates could still fail when executed: G4 for the new non-commute and
tilt levels, and the N4 reach. Nothing here is marked ready until every row
passes.
