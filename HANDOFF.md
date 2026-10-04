# Handoff

*Rewritten 2026-10-04, after Experiment 7 closed. The previous version
(2026-08-29, written mid-Experiment 2) is in git history at `5eebe36a` and
earlier.*

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
| 1 | frequency redistribution, geometry fixed | **CLOSED, certified λ ≥ 2**: −6.65% unserved demand | `outputs/canonical/exp1_final.json` |
| 2 / 2B | through-routing geometry | **CLOSED**: no supportable claim / certified null | `EXPERIMENT2_CLOSEOUT.md` |
| 3 | route mutation, eight edit kinds | **CLOSED**: certified leader −0.187% (`exp3-final-v1`) | `EXPERIMENT3_CLOSURE.md` |
| 4 / 4N / 4A | greenfield design; normalized rerun; vs Exp 3 | **CLOSED**: legacy ordering superseded; greenfield worse by +9.66% | `EXPERIMENT4_NORMALIZED_CLOSEOUT.md`, `EXPERIMENT4_ORIGINAL_QUESTION_ADDENDUM.md` |
| 5 | modeled resource frontier | **FAILED** monotonicity gate (on N4 only); N0 half informative | `EXPERIMENT5_CLOSEOUT.md` |
| 6 | price of service-standard safeguards | **CLOSED, certified**: 0 to +0.91% | `EXPERIMENT6_CLOSEOUT.md` |
| 7 | robustness of F1–F6 | **CLOSED**: Stage 1 and Stage 2 complete | `EXPERIMENT7_CLOSEOUT.md` + `docs/EXPERIMENT7_CLOSEOUT_ERRATA.md`, `docs/EXPERIMENT7_F1_ADDENDUM.md` |

**The answer, one line each:**

* **Frequency is the lever.** About −6% unserved demand at current resources.
  It is robust for the certified plans. Under service-preservation rules it is
  also robust after re-optimization, at λ ≥ 2 (Exp 7, post hoc).
* **Geometry adds nothing.** Recombining routes is null, editing them gives
  ~0.2%, and the greenfield design is worse.
* **Safeguards are cheap.** 0–0.9% of the objective each.
* **When service may be cut freely, the objective does not identify unserved
  demand.** At λ = 1 it nearly empties the network (Exp 7 errata E3,
  closeout §5.2).

**The written record:**

| document | what it is |
|---|---|
| `docs/report/TECHNICAL_REPORT.md` | full technical report (draft, paper-style) |
| `docs/FUTURE_EXPERIMENTS.md` | what to run next, prioritized |
| `README.md` | front door |
| `STATE_OF_PLAY.md` | long-form state as of Exp 6 |
| `DISCOVERIES.md` | D1–D39 decision log, including the wrong turns |
| `outputs/CANONICAL_RESULTS_v5.json` | registry of every canonical and superseded artifact |

## 2. What to trust, and how much

**Trust, with the stated caveats:**

* **The aggregate frequency result.** It is not per-route: seeds disagree on
  19% of route-periods.
* **The geometry nulls.**
* **The Exp 6 safeguard prices**, under closure.
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
* **Ian's machine** holds the same commits on branch `exp7-work` in the clone
  under the connected `cota-route-optimization` folder. They were delivered as
  bundles into `Downloads` and fetched there.
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
2. **E8:** validation and calibration against COTA APC, farebox, fare-card and
   survey data.
3. **E9:** all-purpose demand.
4. **E10:** a well-posed objective (ε-constraint or operating-cost term).
5. **E11:** physical fleet for the frequency plan, which needs deadhead and
   terminal data.
6. **E12 and E13:** transfer timing and stop consolidation. Both are named in
   the mission and never tested.

## 7. A framing worth keeping

The useful question is not "why doesn't COTA implement the optimum". It is
"what does each service rule cost, and what does the current budget make
possible". Exp 6 prices the rules. Exp 7 shows that the frequency result
depends on keeping them.

The model does not say what COTA should do. It says what the current geometry
and budget make possible under stated assumptions. Its own retractions show how
easily a coarser or less careful model would mislead.
