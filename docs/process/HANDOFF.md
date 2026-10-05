# Handoff

*A durable takeover document. Rewritten 2026-10-04 after Experiment 7 closed;
§3 and §6 rewritten 2026-10-05 at the end of the release cleanup. Earlier
versions, including the October 4 git and bundle-transport state, are in git
history (`5eebe36a`, `f452c1a1`).*

This is for whoever picks up this repository next: a COTA planner, a research
group, or a future session. Read `AGENTS.md` and `docs/ENGINEERING_RULES.md`
first. They are the contract the code is written to, and the reason several
results here were retracted rather than published.

---

## 1. Where things stand

**The research programme is complete.** All seven experiments are closed. There
are no runs in flight.

| exp | question | status | read |
|---|---|---|---|
| 1 | frequency redistribution, geometry fixed | **CLOSED, certified λ ≥ 2**: ~680 more modeled weekday trips served; −6.65% unserved demand (solver-seed SD 0.06 percentage points) | `outputs/canonical/exp1_final.json` |
| 2 / 2B | through-routing geometry | **CLOSED**: no supportable gain; the leader is +0.090% unserved under matched starts, worse than no edit (errata E17); the 240-set sweep is discovery-stage | `experiments/exp2/EXPERIMENT2_CLOSEOUT.md`, `outputs/exp2b_certification.json → _confirmation` |
| 3 | route mutation, eight edit kinds | **CLOSED**: certified leader −0.187% (commit `8c2841c4`, tag `exp3-final-v1`) | `experiments/exp3/EXPERIMENT3_CLOSURE.md` |
| 4 / 4N / 4A | greenfield design; normalized rerun; vs Exp 3 | **CLOSED**: legacy ordering superseded; N4, the best of the 200 promoted and certified greenfield candidates, worse than N3 by +9.66% | `experiments/exp4/EXPERIMENT4_NORMALIZED_CLOSEOUT.md`, `experiments/exp4/EXPERIMENT4_ORIGINAL_QUESTION_ADDENDUM.md` |
| 5 | modeled resource frontier | **FAILED** monotonicity gate (on N4 only); N0 half informative | `experiments/exp5/EXPERIMENT5_CLOSEOUT.md` |
| 6 | price of service-standard safeguards | **CLOSED, certified**: 0 to +0.91% | `experiments/exp6/EXPERIMENT6_CLOSEOUT.md` |
| 7 | robustness of F1–F6 | **CLOSED**: Stage 1 and Stage 2 complete | `experiments/exp7/EXPERIMENT7_CLOSEOUT.md` + `experiments/exp7/EXPERIMENT7_CLOSEOUT_ERRATA.md`, `experiments/exp7/EXPERIMENT7_F1_ADDENDUM.md` |

**The answer, one line each:**

* **Frequency reallocation produced the largest favorable modeled effect
  among the interventions tested.** About −6% unserved demand at current resources.
  For the certified plans it keeps its sign at every Stage 1 level
  (SIGN_ROBUST; −1.9% to −7.0%; magnitude Highly sensitive to walking
  friction, A6). Re-optimized in the closest cell to Exp 1's rules (R1_H60) it holds at every
  λ ≥ 2 level re-optimized (A5, A6; one closure per cell; post hoc).
* **The tested geometry interventions produced no large favorable effect:**
  through-routing was null, local route mutations were small (~0.2%), and N4,
  the best of the 200 promoted and certified greenfield candidates, was worse
  than N3 under the certified matched comparisons (the best of all 2,000
  generated is not identified).
* **Safeguards are cheap in the model.** On N0 each study safeguard worsened
  the modeled objective by 0–0.91% (N3: 0–0.63%); study safeguards, not COTA
  policy.
* **At λ = 2 in the OFF-permitting decision space, the objective does not
  identify unserved demand:** two fixed points 0.16% apart in objective give
  −5.4% and +30.5% (Exp 7 errata E3). At λ = 1 re-optimization nearly empties
  the network, a stronger low-penalty failure (closeout §5.2).

**The written record:**

| document | what it is |
|---|---|
| `docs/report/TECHNICAL_REPORT.md` | full technical report (draft, paper-style) |
| `docs/FUTURE_EXPERIMENTS.md` | what to run next, prioritized |
| `README.md` | front door |
| `docs/research-record/STATE_OF_PLAY.md` | long-form state as of Exp 6 |
| `docs/research-record/DISCOVERIES.md` | D1–D39 decision log, including the wrong turns |
| `outputs/CANONICAL_RESULTS_v5.json` | registry of every canonical and superseded artifact |
| `experiments/exp7/EXPERIMENT7_CLOSEOUT.md` | Exp 7 closeout (registered by sha256; not edited) |
| `experiments/exp7/EXPERIMENT7_CLOSEOUT_ERRATA.md` | corrections to the Exp 7 closeout (E1–E15) |
| `experiments/exp7/EXPERIMENT7_F1_ADDENDUM.md` | post hoc F1 analysis (not pre-specified) |
| `experiments/exp7/EXPERIMENT7_RESULTS.md` | short Exp 7 results note |

> **Authority order for Experiment 7:**
>
> 1. the JSON artifacts (`outputs/exp7/…`, registered in `CANONICAL_RESULTS_v5.json`);
> 2. `experiments/exp7/EXPERIMENT7_CLOSEOUT.md` **as corrected by** `experiments/exp7/EXPERIMENT7_CLOSEOUT_ERRATA.md`. Where they conflict, the errata wins;
> 3. `experiments/exp7/EXPERIMENT7_F1_ADDENDUM.md`: post hoc; never relabels a pre-specified result;
> 4. `experiments/exp7/EXPERIMENT7_RESULTS.md`: a summary of 2 and 3;
> 5. `docs/report/TECHNICAL_REPORT.md`: synthesis, draft.

## 2. What to trust, and how much

**Trust, with the stated caveats:**

* **The aggregate frequency result.** It is not per-route: seeds disagree on
  19% of route-periods.
* **The geometry nulls.**
* **The Exp 6 safeguard prices** as a 0–1% order of magnitude. Individual
  prices moved by up to 0.1 percentage points under further closure in Exp 7, and the
  zero prices of the 25%/10% OFF-share caps hold only in one basin (errata
  E8).
* **The direction of F4.**

**Treat as modeled only.** Everything is:

* proxy commute demand;
* uncalibrated weights;
* scheduled service.

All four validation dimensions are `unavailable`.

**Do not quote:**

* any per-route headway;
* any bus or fleet number for a modified plan;
* served-trip or GC figures from single-basin runs as findings;
* anything at λ ≤ 1;
* the legacy Exp 4 ordering.

## 3. State

The research program is complete and no production run is in flight. The
frozen research state and current public branch structure are documented in
`docs/RELEASE_PROVENANCE.md`. `master` contains post-freeze reporting and
release work. Before making changes, confirm current CI is green and read
`AGENTS.md` / `docs/ENGINEERING_RULES.md`.

## 4. Reproducing

`docs/REPRODUCE.md` has per-experiment commands and a table of the
reproduction evidence each experiment has from a clean checkout. Reproduction
is bit-exact within one environment. Cross-machine drift is uncharacterized.

## 5. Operational traps

`docs/process/OPERATIONS.md` has 36 rules, each bought with lost work. The ones that bit
during Experiment 7:

* **The cloud container restarts without warning,** about every 1–24 h, and on
  computer-use grants.
  * Long runs must checkpoint and resume.
  * Keep a liveness check that reads `/proc/<pid>/cmdline`, not `pgrep`.
  * Relaunch scripts must be idempotent (the Exp 7 Stage 2 relauncher was a container-only script, never committed).
* **Two runners on one closure state corrupt it.** `exp7_run.py closure` now
  takes an exclusive lock per (track, network).
* **A batch in flight freezes the code that can change its numbers.** Post-freeze
  edits must be reporting-only, and must be disclosed: `experiments/exp7/EXPERIMENT7_CLOSEOUT.md`
  §1.1.

## 6. What to do next

In order (detail in `docs/FUTURE_EXPERIMENTS.md`):

1. **Finish the remaining release infrastructure** (`docs/process/RELEASE_AND_REPORTING_GUIDELINES.md`,
   checklist; `docs/RELEASE_PROVENANCE.md`).
2. **E21 (optional):** independent confirmation of the post hoc Exp 7
   service-preserving (R1_H60) result across independent closures. Runnable
   now; needs no external data.
3. **E8:** external calibration and validation against agency data (APC,
   farebox, fare-card, AVL, survey).
4. **E9:** all-purpose demand.
5. **E10:** objective reformulation (ε-constraint on unserved demand, or an
   unserved penalty consistent with the retention curve).
6. **E11:** physical fleet and deadhead validation for the frequency plan.
7. **E12 and E13:** transfer timing and stop consolidation. Both are named in
   the mission and never tested.

Better data is worth more than more optimization machinery: the experimental
apparatus is already more sophisticated than its empirical foundation.

## 7. A framing worth keeping

The useful question is not "why doesn't COTA implement the optimum". It is
"what does each service rule cost, and what does the current budget make
possible". Exp 6 prices the study's safeguard rules. Exp 7 shows that the
re-optimized frequency result holds in the closest cell to Experiment 1's
service rules (R1_H60; study
safeguards in `config/constraints.yaml`; no documented COTA numeric standard)
(post hoc, A5 and A6 levels), while without them the λ = 2 objective does not
identify unserved demand in the OFF-permitting decision space.

The model does not say what COTA should do. It says what the current geometry
and budget make possible under stated assumptions. Its own retractions show how
easily a coarser or less careful model would mislead.
