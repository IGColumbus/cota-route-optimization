# Handoff

*Rewritten 2026-10-04, after Experiment 7 closed. The previous version
(2026-09-29, after Experiment 6) is in git history at `5eebe36a`.*

This is for whoever picks up this repository next: a COTA planner, a research
group, or a future session. Read `AGENTS.md` first. It is the contract the code
is written to, and the reason several results here were retracted rather than
published.

---

## 1. Where things stand

**The research programme is complete.** All seven experiments are closed. There
are no runs in flight.

| exp | question | status | read |
|---|---|---|---|
| 1 | frequency redistribution, geometry fixed | **CLOSED, certified λ ≥ 2**: ~680 more modeled weekday trips served; −6.65% unserved demand (solver-seed SD 0.06 percentage points) | `outputs/canonical/exp1_final.json` |
| 2 / 2B | through-routing geometry | **CLOSED**: no supportable gain; the leader is +0.090% unserved under matched starts, worse than no edit (errata E17); the 240-set sweep is discovery-stage | `EXPERIMENT2_CLOSEOUT.md`, `outputs/exp2b_certification.json → _confirmation` |
| 3 | route mutation, eight edit kinds | **CLOSED**: certified leader −0.187% (commit `8c2841c4`; tag `exp3-final-v1` not yet public) | `EXPERIMENT3_CLOSURE.md` |
| 4 / 4N / 4A | greenfield design; normalized rerun; vs Exp 3 | **CLOSED**: legacy ordering superseded; N4, the best of the 200 promoted and certified greenfield candidates, worse than N3 by +9.66% | `EXPERIMENT4_NORMALIZED_CLOSEOUT.md`, `EXPERIMENT4_ORIGINAL_QUESTION_ADDENDUM.md` |
| 5 | modeled resource frontier | **FAILED** monotonicity gate (on N4 only); N0 half informative | `EXPERIMENT5_CLOSEOUT.md` |
| 6 | price of service-standard safeguards | **CLOSED, certified**: 0 to +0.91% | `EXPERIMENT6_CLOSEOUT.md` |
| 7 | robustness of F1–F6 | **CLOSED**: Stage 1 and Stage 2 complete | `EXPERIMENT7_CLOSEOUT.md` + `docs/EXPERIMENT7_CLOSEOUT_ERRATA.md`, `docs/EXPERIMENT7_F1_ADDENDUM.md` |

**The answer, one line each:**

* **Frequency is the lever.** About −6% unserved demand at current resources.
  For the certified plans it keeps its sign at every Stage 1 level
  (SIGN_ROBUST; −1.9% to −7.0%; magnitude Highly sensitive to walking
  friction, A6). Re-optimized in the closest cell to Exp 1's rules (R1_H60) it holds at every
  λ ≥ 2 level re-optimized (A5, A6; one closure per cell; post hoc).
* **Geometry adds nothing.** Recombining routes is null, editing them gives
  ~0.2%, and N4, the best of the 200 promoted and certified greenfield
  candidates, is worse than N3 (the best of all 2,000 generated is not
  identified).
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
| `STATE_OF_PLAY.md` | long-form state as of Exp 6 |
| `DISCOVERIES.md` | D1–D39 decision log, including the wrong turns |
| `outputs/CANONICAL_RESULTS_v5.json` | registry of every canonical and superseded artifact |
| `EXPERIMENT7_CLOSEOUT.md` | Exp 7 closeout (registered by sha256; not edited) |
| `docs/EXPERIMENT7_CLOSEOUT_ERRATA.md` | corrections to the Exp 7 closeout (E1–E15) |
| `docs/EXPERIMENT7_F1_ADDENDUM.md` | post hoc F1 analysis (not pre-specified) |
| `docs/EXPERIMENT7_RESULTS.md` | short Exp 7 results note |

> **Authority order for Experiment 7:**
>
> 1. the JSON artifacts (`outputs/exp7/…`, registered in `CANONICAL_RESULTS_v5.json`);
> 2. `EXPERIMENT7_CLOSEOUT.md` **as corrected by** `docs/EXPERIMENT7_CLOSEOUT_ERRATA.md`. Where they conflict, the errata wins;
> 3. `docs/EXPERIMENT7_F1_ADDENDUM.md`: post hoc; never relabels a pre-specified result;
> 4. `docs/EXPERIMENT7_RESULTS.md`: a summary of 2 and 3;
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

## 3. Git and transport state (as of 2026-10-04)

* The **cloud container** holds the full history on local `master`.
* **Ian's machine** holds commits on branch `exp7-work` (as reported; not
  verifiable from the container) in the clone under the connected
  `cota-route-optimization` folder. They were delivered as bundles into
  `Downloads` and fetched there. Commits after the last bundle delivered,
  including `5dc3f408` and later write-up commits, need a further bundle. Last
  bundle delivered: `<commit — Ian to fill in>`.
* **GitHub `master` is behind, at `196295c9`.** It is a direct ancestor of
  `exp7-work`, so merging is a clean fast-forward.
* **Next git action:** in GitHub Desktop, merge `exp7-work` into `master` and
  push. Then verify with `git ls-remote origin refs/heads/master`
  (`OPERATIONS.md` rule 36). The cloud session cannot push: the repository is
  not in its authorized sources.
* After the push, follow the release checklist in
  `docs/RELEASE_AND_REPORTING_GUIDELINES.md`:
  * tag `research-final`;
  * pin the environment;
  * restructure;
  * add the license, citation, data interfaces, calibration register,
    `validate` and `reproduce`;
  * produce the three reports with script-generated figures.

## 4. Reproducing

`docs/REPRODUCE.md` has per-experiment commands, now including Experiment 7.
Reproduction is bit-exact within one environment. Cross-environment drift is
uncharacterized.

## 5. Operational traps

`OPERATIONS.md` has 36 rules, each bought with lost work. The ones that bit
during Experiment 7:

* **The cloud container restarts without warning,** about every 1–24 h, and on
  computer-use grants.
  * Long runs must checkpoint and resume.
  * Keep a liveness check that reads `/proc/<pid>/cmdline`, not `pgrep`.
  * Relaunch scripts must be idempotent (`outputs/exp7/run/s2_ensure.sh`).
* **Two runners on one closure state corrupt it.** `exp7_run.py closure` now
  takes an exclusive lock per (track, network).
* **The output folder used for transfers stops accepting new files** after
  roughly 360. Bundles were then delivered as chat attachments instead.
* **A batch in flight freezes the code that can change its numbers.** Post-freeze
  edits must be reporting-only, and must be disclosed: `EXPERIMENT7_CLOSEOUT.md`
  §1.1.

## 6. What to do next

In order (detail in `docs/FUTURE_EXPERIMENTS.md`):

1. **Release:** push, tag and pin, so that every number has a public commit.
2. **E21:** pre-specified confirmation of the post hoc F1 result across
   independent closures (runnable now; needs no external data).
3. **E8:** validation and calibration against COTA APC, farebox, fare-card and
   survey data.
4. **E9:** all-purpose demand.
5. **E10:** a well-posed objective (ε-constraint on unserved demand, or an
   unserved penalty consistent with the retention curve).
6. **E11:** physical fleet for the frequency plan, which needs deadhead and
   terminal data.
7. **E12 and E13:** transfer timing and stop consolidation. Both are named in
   the mission and never tested.

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
