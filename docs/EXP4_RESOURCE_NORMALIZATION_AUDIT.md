# Experiment 4 — resource normalization audit

**Opened 2026-09-22. Audit only.** No experiment was launched. Nothing under
`src/cota_opt/`, `outputs/exp4/`, `outputs/CANONICAL_ENVELOPE.json`, the
candidate definitions or the baseline data was modified. All new artifacts are
under `outputs/exp4_resource_audit/` and this file.

Motivated by the 2026-09-21 Exp 5 OFF→ON diagnostic, which found that the Exp 4
evaluator's two-arm feasibility test was being decided entirely by its
peak-vehicle arm while the revenue-hours arm sat at 36.658% of cap.

---

## 0. Preconditions

**Test suite.** `python3 -m pytest tests/ -q` — **840 passed, 0 failed, 0
errors, 0 skipped.** The summary line was truncated when the process was reaped
at teardown; the outcome characters are complete and unambiguous (840 `.`, no
`F`, `E`, `s` or `x`), so the result is recorded from those rather than from a
summary line this audit did not see.

**Bit-exact reproduction of the frozen incumbent.**

```
certified   3511184.5657525407
reproduced  3511184.5657525407      relative error 0.000e+00
```

Reproduced twice on 2026-09-21, in both passes of the OFF→ON diagnostic, on the
same network, pathset and evaluator the run used. Recorded in
`outputs/exp5_diag/offon_probe.json` and
`outputs/exp5_diag/offon_full_feasibility.json`, committed at `099d0527`. This
audit changed nothing in between and did not spend a third 350-second setup to
repeat it; the frozen certified record on disk still carries the same value.

Documents read: `README.md`, `AGENTS.md`, `STATE_OF_PLAY.md`,
`FLEET_AND_BLOCKING.md`, `HANDOFF.md`, `EXPERIMENT4_CONTRACT.md`,
`EXPERIMENT4_CLOSEOUT.md`, `EXPERIMENT4_AUDIT_DESIGN.md`,
`EXPERIMENT4_AUDIT_CLOSEOUT.md`, `EXPERIMENT5_PREMISE_AUDIT.md`,
`EXPERIMENT5_OFFON_DIAGNOSTIC.md`, `DISCOVERIES.md`, `OPERATIONS.md`,
`CANONICAL_ENVELOPE.json`, and the resource, contract, frequency and evaluator
code cited throughout.

`AGENTS.md` states the project's mission as **"Holding COTA's approximate
current operating resources constant"**. That sentence is what makes §1's
finding a problem rather than a curiosity.

## 1. The resource contract

### The call path, with citations

| step | where |
|---|---|
| candidate geometry assembled | `src/cota_opt/exp4_assemble.py: assemble(...)` → `(network, tstats)` |
| candidate substituted for the baseline | `src/cota_opt/exp3_score.py:273` `b_ed = _Baseline(H.baseline, net, ts)` — overrides network and tstats with the **candidate's** |
| supply model built from that | `src/cota_opt/exp2.py:209` `e1 = exp1_setup(b, constraints=cons, weights=w)`; `:210-211` `services = e1.model.services`, `baseline_plan = e1.baseline_plan` |
| route-period supply derived | `src/cota_opt/exp1.py:72-82` — `headway = k * T / n_trips` per `(route_id, period)` from the candidate's own `tstats` |
| **revenue vehicle-hours computed** | `src/cota_opt/frequency.py:277` `revenue_veh_hours = trips(svc,h) * runtime/60` |
| **peak_by_period computed** | `src/cota_opt/frequency.py:280` `peak_vehicles = cycle/headway`, `cycle = 2*runtime*(1+layover)` (`:238`), summed per period in `evaluate_array` |
| baseline evaluated | `src/cota_opt/exp2.py:~300` `fit = model.evaluate(baseline_plan)` |
| **hours cap origin** | `src/cota_opt/exp2.py:321-323` — sentinel `"baseline"` → `fit.revenue_veh_hours`; **overridden** by `scripts/exp4_launch.py` to the canonical `2517.183333` |
| **peak cap origin** | `src/cota_opt/exp2.py:324-326` — sentinel `"baseline"` → **`dict(fit.peak_by_period)`**, *not* overridden by the launcher, which asserts the sentinel is still in force |
| budget assembled | `src/cota_opt/exp2.py:327` `ResourceBudget(vh_budget, peak_budget, tolerance=res.get("budget_tolerance", 0.0))` |
| **feasibility test** | `src/cota_opt/frequency.py:374-382` — hours arm, then every period named in the budget |

### The answers

* **Where hours are calculated** — `frequency.py:277`, summed over route-periods.
* **Where `peak_by_period` is calculated** — `frequency.py:280`, `cycle/headway`,
  aggregated per period. This is the `routewise_peak` construction that
  `exp5_resource.REJECTED_AS_CAP` lists at 150.73 on the real baseline.
* **Hours cap origin** — the frozen canonical artifact, digest
  `b6c647d3766338a6`, value `2517.183333`. Global, identical for every candidate.
* **Peak cap origin** — the candidate's own baseline plan's evaluated fitness.
* **How `"baseline"` is interpreted** — resolved *against whatever network the
  setup is handed*. `exp3_score.py:277-295` documents this behaviour for the
  hours arm and refuses to run without a pinned envelope, precisely because
  "every state was being judged against a different budget, which is the one
  thing the whole method depends on not happening." **The same reasoning was
  applied to hours and not to peak vehicles.**
* **Global or candidate-specific** — hours global; **peak candidate-specific**.
* **Does candidate geometry affect its own baseline peak** — yes, entirely.
  `assemble` determines which lines exist, `exp1.build_setup` derives runtime,
  direction count and baseline headway from that candidate's `tstats`, and the
  cap is the sum of `cycle/headway` over exactly those route-periods.
* **`_feasible` behaviour** — hours first, then **every period present in
  `budget.peak_vehicles_by_period`**; a period absent from the budget is not
  tested. Both arms use `> cap * (1 + tolerance) * (1 + 1e-9)`.
* **Tolerance** — `budget_tolerance` from config, measured in force as
  **`0.0`**. `_EPS_REL = 1e-9` is float slack, not policy.
* **Period definitions** — six, from `config` via `service_periods`: `early`,
  `am_peak`, `midday`, `pm_peak`, `evening`, `owl`. Identical on both sides.
* **Rounding** — **none**. Both cap and usage are continuous floats. The `floor`
  rule in `exp5_resource` applies to the *canonical block-derived* envelope,
  which is a different quantity and is not involved here.
* **Same quantity on both sides** — **yes.** Cap and usage are both
  `FitnessVector.peak_by_period`, produced by the same method on the same model
  class. `PathBasedModel` documents that "Resource physics (vehicle-hours, peak
  vehicles) are inherited unchanged. Only the passenger side is replaced"
  (`exp2.py:53`). This is the one thing that is *not* broken here, and it is
  what makes a common-cap pilot possible at all.

> ### Is the Exp 4 peak resource cap candidate-specific?
> # YES

Verified empirically as well as by reading: the reconstruction path used in §2
reproduces the leader's six caps against the values read off the **live**
`judge.budget` during certification, to within 4-decimal print rounding
(worst |Δ| 4.5e-05).

### The effective formulation

```
candidate geometry
  -> the candidate's own baseline service evaluation
  -> that candidate's peak_by_period
  -> that candidate's peak resource cap
  -> that candidate's feasible optimization space
```

Each of the 200 candidates was optimized inside a box it defined for itself.

## 2. Caps for all 200 candidates

`outputs/exp4_resource_audit/EXP4_CANDIDATE_RESOURCE_CAPS.csv` — 201 rows (200
candidates plus the reference network), values stored unrounded via `repr`.

Reconstructed with `exp1.build_setup` on each candidate network rather than the
full 350-second certification setup, which is sound because the cap depends only
on the supply side that `PathBasedModel` inherits unchanged. The script refuses
to continue unless the leader's caps match the live budget, and they do.

**Reference network** (173 route-periods, baseline 2517.183333 vehicle-hours):

```
early 85.2821   am_peak 162.0094   midday 159.1728
pm_peak 176.4931   evening 140.1946   owl 35.5574
```

`pm_peak = 176.4931` is the same 176.49 that `FLEET_AND_BLOCKING.md` records as
the frequency model's peak concurrency against the block-derived 197 — an
independent confirmation that this reconstruction is measuring the documented
quantity.

## 3. Cap dispersion

`EXP4_RESOURCE_CAP_SUMMARY.json` / `.csv`.

| period | min | median | max | range | range % | CV | reference | median ÷ ref |
|---|---|---|---|---|---|---|---|---|
| early | 87.4771 | 88.8258 | 90.2733 | 2.7963 | 3.20% | 0.0074 | 85.2821 | **104.16%** |
| am_peak | 58.3180 | 59.2172 | 60.1822 | 1.8642 | 3.20% | 0.0074 | 162.0094 | 36.55% |
| midday | 29.1590 | 29.6086 | 30.0911 | 0.9321 | 3.20% | 0.0074 | 159.1728 | 18.60% |
| pm_peak | 58.3180 | 59.2172 | 60.1822 | 1.8642 | 3.20% | 0.0074 | 176.4931 | 33.55% |
| evening | 43.7385 | 44.4129 | 45.1367 | 1.3981 | 3.20% | 0.0074 | 140.1946 | 31.68% |
| owl | 29.1590 | 29.6086 | 30.0911 | 0.9321 | 3.20% | 0.0074 | 35.5574 | 83.27% |

**The six caps carry one degree of freedom, not six.** Every period shows an
identical 3.20% range and identical CV, and every candidate's cap vector has the
ratios **(3.000, 2.000, 1.000, 2.000, 1.500, 1.000)** against its own midday
value. The synthetic candidates share a per-period baseline headway schedule, so
`peak_p = (Σ cycle) / headway_p` with `headway_p` common across candidates: the
vector is one candidate-specific scalar times a fixed shape.

The reference network's shape is **(0.536, 1.018, 1.000, 1.109, 0.881, 0.223)** —
a real operator's weekday profile, and nothing like the synthetic one.

**Is 3.20% material?** Not judged by intuition — judged against the outcome
scale this project already publishes:

| quantity | size |
|---|---|
| cap dispersion across candidates | **3.20%** (absolute 0.93–2.80 vehicles) |
| certified objective spread across the same 200 | 2.2788% |
| Exp 4 first-to-second margin | 0.0106% |
| margin by which discovery rank 237 beat the incumbent | 0.0147% |
| best single OFF→ON improvement found in the Exp 5 diagnostic | 0.5346% |

The dispersion in the binding budget is **larger than the entire spread of the
outcome it was meant to rank**, and roughly 300× the margin that decided first
place. It is not trivial on any reading.

**Every candidate exceeds the reference in `early` (200 of 200) and falls below
it in all five other periods (0 of 200 above).**

## 4. Cap versus certified performance

Lower objective is better, so a **negative** correlation would mean a larger
endogenous budget bought a better result.

| measure | Pearson vs objective | Spearman vs objective | Spearman vs certified rank |
|---|---|---|---|
| every individual period | **+0.0870** | **+0.0598** | +0.0598 |
| sum of the six caps | +0.0870 | +0.0598 | +0.0598 |
| max period cap | +0.0870 | +0.0598 | +0.0598 |
| sum normalized by the reference sum | +0.0870 | +0.0598 | +0.0598 |
| baseline vehicle-hours (existing project scalar) | +0.0870 | +0.0598 | +0.0598 |

Every figure is identical because of the collinearity established in §3 — these
are not five independent measures, they are one measure five ways. No new
weighting scheme was invented.

**Did candidates with larger endogenous budgets obtain better certified
objectives? No — very slightly the reverse, and weakly.** The sign is positive,
meaning a larger cap went with a marginally *worse* objective, and r² ≈ 0.0076:
cap explains under 1% of the variance in certified objective.

**Correlation is not causation, and none is claimed.** The cap is collinear with
candidate network size (it is that candidate's own baseline vehicle demand), so
this statistic cannot separate "budget helps" from "bigger networks score
differently", and it is reported only to show that the *cross-sectional*
association is weak.

**Geometry change → baseline cap change: Pearson +1.0000, Spearman +1.0000.**
Exactly unity, because both quantities are read off the same candidate baseline
evaluation. This is mechanical identity, not an empirical relationship, and §6
is where it matters.

## 5. Finalist cross-feasibility

`EXP4_FINALIST_CROSS_FEASIBILITY.csv`. Each candidate's **final returned plan**
was scored against six envelopes with **no re-optimization**. These envelopes
are diagnostic instruments, not recommended operating budgets.

| envelope | feasible | % |
|---|---|---|
| **A** its own candidate-specific cap | 200 / 200 | 100.0% |
| **B** the reference network's cap | **0 / 200** | **0.0%** |
| **C** the Exp 4 winner's cap | 78 / 200 | 39.0% |
| **D** componentwise minimum across candidates | 2 / 200 | 1.0% |
| **E** componentwise median | 103 / 200 | 51.5% |
| **F** componentwise maximum | 200 / 200 | 100.0% |

* **A is 100% by construction** and is evidence of nothing except that the
  constraint was enforced.
* **B is zero, including the winner**, and the cause is a single period: every
  candidate's `early` usage exceeds the reference's `early` cap of 85.2821. The
  reference envelope is 2.7–5.4× *looser* in the other five periods and still
  admits nothing.
* **Top-20 by certified objective feasible under the reference: 0 of 20.**
* **The Exp 4 winner is infeasible under the reference cap and under the
  componentwise-minimum cap.**

**Top-5 mutual feasibility** (plan in the row, cap in the column; `Y` = that
plan fits that cap):

| plan ↓ / cap → | …c4bcce | …545e31 | …497954 | …1c4311 | …fc0287 |
|---|---|---|---|---|---|
| **…c4bcce** (rank 1) | Y | n | Y | Y | Y |
| **…545e31** (rank 2) | Y | Y | Y | Y | Y |
| **…497954** (rank 3) | n | n | Y | Y | Y |
| **…1c4311** (rank 4) | n | n | n | Y | n |
| **…fc0287** (rank 5) | n | n | Y | Y | Y |

**The major contenders are not mutually feasible.** 11 of 25 cells fail, the
matrix is asymmetric, and rank 4's plan fits no cap but its own. Whatever else
is true, these five candidates were not compared on equal resources.

## 6. The "savings get taken away" hypothesis

| case | rank | certified objective | Σ cap | Σ cap − ref | baseline vh | optimized vh |
|---|---|---|---|---|---|---|
| largest cap decrease | 17 | 3,518,981.4459 | 306.1697 | −452.5396 | 912.8042 | 911.0761 |
| largest cap increase | 71 | 3,531,144.8139 | 315.9566 | −442.7527 | 941.9825 | 939.6504 |
| **winner** | 1 | 3,511,184.5658 | 309.9471 | −448.7622 | 924.0658 | 922.7448 |
| runner-up | 2 | 3,511,557.9642 | 309.2136 | −449.4957 | 921.8792 | 918.0173 |
| median candidate | 101 | 3,538,302.3786 | 315.4479 | −443.2614 | 940.4658 | 939.1522 |
| *reference* | — | — | 758.7093 | 0 | 2517.1833 | — |

Read the `baseline vh` and `Σ cap` columns together. They move in lockstep, and
they must: the cap **is** the baseline peak demand. Pearson +1.0000.

* Candidate 17 needs 912.80 baseline vehicle-hours — the least of any candidate
  — and receives the smallest optimization budget of any candidate.
* Candidate 71 needs 941.98 — the most — and receives the largest budget.
* The winner sits between them on both, as it must.

> ### Can a geometry improvement that frees peak capacity reinvest that capacity under the original Exp 4 formulation?
> # NO

The freed capacity is subtracted from the budget by the same arithmetic that
freed it. A geometry whose baseline needs one fewer vehicle at the peak minute
is granted exactly one fewer vehicle to spend. There is no mechanism anywhere in
the path by which a saving becomes available for reinvestment, because the cap
is not a budget the candidate is measured against — it is a restatement of the
candidate's own starting demand.

This is not a bug in `_feasible`, which does exactly what it says. It is a
consequence of the `"baseline"` sentinel being resolved against the candidate
rather than pinned, which `exp3_score.py:277-295` already identifies as a
three-day failure mode for the hours arm and then fixes for that arm only.

## 7–8. The pilot and its envelope

**Semantic parity, established before any common cap was chosen.** The common
envelope must share units, period definitions, rounding, semantics and evaluator
contract with candidate usage. The reference network's baseline `peak_by_period`
does, on all five counts, because it is produced by the *identical*
`exp1.build_setup → model.evaluate(baseline_plan) → peak_by_period` path that
produces candidate usage: same `cycle/headway` instrument, same six periods, no
rounding on either side, same `FitnessVector` field, same model class.

The canonical block-derived envelope (early 135 · am_peak 187 · midday 173 ·
pm_peak 197 · evening 178 · owl 149) was **not** used, exactly as §8 instructs.
It measures a different resource concept — a peak count of published vehicle
blocks — against which the cycle/headway proxy reads 176.49 where the
block-derived figure reads 197 on the identical network. Comparing them is the
comparison `contract.py:451` refuses.

**Pilot set** (10 candidates, deduplicated): certified ranks 1, 2, 3, 25, 50,
100, 150, 200, plus the minimum-aggregate-cap candidate (rank 17) and the
maximum-aggregate-cap candidate (rank 71).

**What changed: one config key, and nothing else.**

```
ORIGINAL  cons["resource"]["peak_fleet_by_period"] = "baseline"
          -> exp2.py:324  dict(fit.peak_by_period)  -- per candidate

PILOT     cons["resource"]["peak_fleet_by_period"] = {explicit reference dict}
          -> exp2.py:326  the dict verbatim          -- identical for all
```

`LAM`, `SEED`, `POOL_VERSION`, `assemble`, `certify`, `CERTIFICATION_DIGEST`,
`n_keys`, `k_rungs`, `max_rounds`, the greedy initialization policy, the
objective and the evaluator are all unchanged.

## 9. Pilot comparison

All ten completed. **Every one converged** (`converged=True`), all stayed under
the hours cap, none errored. One — `rank_25` — used the full `MAX_ROUNDS = 40`
budget; `exp4_certify.py:290` sets the flag only on a round that finds no
improvement, so it genuinely converged, on its last permitted round.

`EXP4_COMMON_CAP_PILOT.csv` carries the full record unrounded. o200 is the
original certified rank out of 200; oP and nP are rank within the pilot.

| label | o200 | oP | nP | move | original | normalized | Δ | Δ% | rounds |
|---|---|---|---|---|---|---|---|---|---|
| rank_1 | 1 | 1 | **9** | **−8** | 3,511,184.5658 | 3,325,019.7358 | −186,164.83 | −5.3021% | 25 |
| rank_2 | 2 | 2 | 4 | −2 | 3,511,557.9642 | 3,295,108.7000 | −216,449.26 | −6.1639% | 17 |
| rank_3 | 3 | 3 | 7 | −4 | 3,514,611.1824 | 3,304,686.7234 | −209,924.46 | −5.9729% | 16 |
| min_aggregate_cap | 17 | 4 | **3** | +1 | 3,518,981.4459 | 3,262,639.4740 | −256,341.97 | −7.2846% | 25 |
| rank_25 | 25 | 5 | **2** | +3 | 3,520,776.1031 | 3,259,559.8887 | −261,216.21 | −7.4193% | 40 |
| rank_50 | 50 | 6 | **1** | **+5** | 3,525,178.3986 | **3,258,414.6724** | −266,763.73 | −7.5674% | 31 |
| max_aggregate_cap | 71 | 7 | 6 | +1 | 3,531,144.8139 | 3,302,666.8323 | −228,477.98 | −6.4704% | 17 |
| rank_100 | 100 | 8 | 5 | +3 | 3,538,293.1173 | 3,300,323.6855 | −237,969.43 | −6.7255% | 30 |
| rank_150 | 150 | 9 | 8 | +1 | 3,554,415.5565 | 3,313,914.9024 | −240,500.65 | −6.7663% | 17 |
| rank_200 | 200 | 10 | 10 | 0 | 3,591,198.3836 | 3,338,651.6633 | −252,546.72 | −7.0324% | 28 |

Caps: each candidate's original six-period vector is in the CSV; the common
envelope is early 85.2821 · am_peak 162.0094 · midday 159.1728 · pm_peak
176.4931 · evening 140.1946 · owl 35.5574 for all ten. Hours cap 2,517.183333
throughout, and every normalized plan stayed under it.

### Rank agreement

| | |
|---|---|
| Spearman (original rank vs normalized rank) | **+0.2121** |
| Kendall τ | **+0.1111** |
| pairwise ordering reversals | **20 of 45 (44.4%)** |
| original winner remains best | **NO — falls from 1st to 9th of 10** |

Nearly half of all pairwise orderings flip. A Spearman of +0.21 on ten points
is indistinguishable from no relationship.

### The four questions §9 asks

**Does the original winner remain the best pilot candidate?** No. The Exp 4
incumbent finishes **9th of 10**. The best candidate under the common cap is
`rank_50` — original certified rank **50 of 200** — which beats the original
winner by **66,605.06, or 2.0031%**. For scale, the entire original
200-candidate spread was 2.2788% and first place was decided by 0.0106%.

**Does an originally weak geometry become competitive?** Yes, repeatedly. The
top three under a common cap are originally ranked **50, 25 and 17**. The three
originally ranked 1, 2 and 3 finish 9th, 4th and 7th.

**Was a strong geometry benefiting from a larger endogenous cap?**
**Yes, and it is measurable.** Pearson between a candidate's original aggregate
cap and its percentage improvement under normalization is **+0.4686**. The
deltas are negative, so a *more positive* delta means a *smaller* gain: the
candidates that had been granted the largest endogenous budgets are exactly the
ones that gain least when everyone is given the same budget. They were already
being carried by their own caps.

**How large is the effect against the effect being measured?** The deltas span
**2.2653 percentage points** (−5.3021% to −7.5674%), min −7.5674, median
−6.7459, max −5.3021. That spread is **99.4% of the entire original
200-candidate objective spread of 2.2788%**, and roughly **214× the 0.0106%
margin that decided first place**. The resource-provenance artifact is the same
size as the phenomenon Exp 4 was built to measure.

## 10. Decision gate

> # `EXP4_FULL_NORMALIZED_RERUN_REQUIRED`

Every trigger condition for this status is met, and no condition for a weaker
one is:

* **rank order materially changes** — 20 of 45 pairwise reversals, Spearman
  +0.2121, Kendall τ +0.1111;
* **the winner changes** — 1st of 10 to 9th of 10, beaten by 2.0031%;
* **major contenders reverse** — the original top three land 9th, 4th and 7th;
  the new top three were originally 50th, 25th and 17th;
* **candidate-specific resource allowance predicts performance under
  normalization** — Pearson +0.4686 between original cap and improvement;
* **the geometry conclusion becomes uncertain** — "which 65-line network is
  best" has no stable answer across the two resource provenances.

`EXP4_RESOURCE_EFFECT_NEGLIGIBLE` is excluded: the dispersion is not trivial
(3.20%, larger than the outcome spread) and the pilot does not reproduce the
ordering. `EXP4_RANKING_ROBUST_TO_NORMALIZATION` is excluded: the ranking is
not preserved, weakly or otherwise. `RESOURCE_PROVENANCE_REPAIR_REQUIRED` is
**not** selected, and the reason is narrow and worth stating: a defensible
common envelope **does** exist for this proxy — the reference network's own
`peak_by_period`, produced by the identical evaluator path, with matching
units, periods, rounding and semantics (§7–8). The pilot ran on it without
incident. The resource *model* is not broken in the sense that status
describes; the resource *provenance* was wrong, and it is fixable by pinning
the envelope exactly as the hours arm was already pinned.

**Interpretation.** Rerun all 200 candidates under one fixed resource envelope
before relying on any Exp 4 geometry finding. Until that happens, Exp 4's
certified ordering should be treated as an ordering **of candidate-specific
optimization problems**, not of geometries.

### What this does NOT license

* It does **not** say the Exp 4 objective values are wrong. They are exactly
  reproducible and were computed by the exact evaluator.
* It does **not** say `rank_50` is the right geometry. It is the best of ten
  under one common envelope, on a 10-candidate pilot with no claim about the
  other 190.
* It does **not** say the normalized objectives are achievable operationally.
  They are computed against a cycle/headway proxy with no fleet meaning, and
  the 5–8% improvements come from spending a much larger peak-vehicle budget
  that nothing has shown to exist.
* It does **not** validate the reference envelope as a *correct* budget. It is
  defensible as a *common* one, which is all the pilot needed.
* A full rerun is **not** started. Per §15 this audit stops here.

## 11. What is and is not established

**Established:**

* the certified Exp 4 objective is exactly reproducible;
* the revenue-hours cap is not binding at the incumbent (36.658%);
* the peak-resource arm blocks all 4,095 tested finite perturbations;
* 3,076 of those blocked perturbations improve the objective;
* the optimizer neighbourhood is not the reason for the unused revenue hours —
  all 315 OFF route-periods are one rung from service;
* candidate peak caps originate from candidate baseline fitness
  (`exp2.py:324`), confirmed by reading and by reconstruction against the live
  budget;
* the caps disperse by 3.20% across candidates and carry one degree of freedom;
* no candidate's final plan is feasible under the reference envelope;
* the top five candidates are not mutually feasible under one another's caps;
* freed peak capacity cannot be reinvested under the original formulation.

**NOT established:**

* that Exp 4 selected the wrong geometry;
* that the Exp 4 winner would change under normalization;
* that the canonical block-derived fleet values are valid caps for this proxy;
* that more buses produce any specific systemwide improvement;
* that the 3,076 improvements can be combined;
* that their objective deltas are additive;
* that Exp 5 has a valid resource axis.

Nothing in the pilot can establish the first two for the other 190 candidates.
A pilot of ten bounds the question; it does not close it.

## 12. Taxonomy patch

The diagnostic taxonomy used on 2026-09-21 had four cases and none of them
covered what was observed. Added here, for use in future diagnostics; no
historical result file is altered.

**`OTHER_RESOURCE_CONSTRAINT_BINDS`** — the objective admits improving service
additions and the tested primary resource has slack, but candidate feasibility
is prevented by another active resource constraint.

The Exp 5 OFF→ON diagnostic is **this** case. It must not be classified as
`OBJECTIVE_PREFERS_SPARSE_SERVICE`, whose interpretation — that λ and the
objective prefer sparse service — is contradicted by the exact probes: 3,076
single-coordinate service additions improve the objective and every one of them
is refused by the peak-resource arm.

The four original cases remain valid for the questions they were written for:
`OBJECTIVE_PREFERS_SPARSE_SERVICE`, `NEIGHBORHOOD_BLOCKS_IMPROVEMENT`,
`OPTIMIZER_MISSED_REACHABLE_IMPROVEMENT`, `INCONCLUSIVE`.

## 13. Experiment 5 implications — documentation only

**Exp 5 was not run and is not scheduled.**

The current Exp 5 formulation is invalid: scaling revenue vehicle-hours from
0.75× to 1.50× leaves the actual binding peak-resource constraint untouched, and
every one of those levels sits above the 922.74 operating point. All sixteen
cells would return the same plan.

A future Exp 5 resource frontier must use an axis that binds. Three directions,
**not chosen here**:

* **A** — a fixed common peak-resource proxy frontier.
* **B** — a repaired true-fleet frontier.
* **C** — jointly varying fleet and hours, if both become defensible.

Choosing among them requires resource provenance to be resolved first, which is
what this audit's status is about.

**Prior retraction preserved.** Passing `peak_vehicles_by_period={}` would
delete the operative binding resource constraint and create enormous
unconstrained headroom — 1,594 vehicle-hours with no vehicle limit at all. It
was recommended in `EXPERIMENT5_PREMISE_AUDIT.md` §10 item 1, is struck there,
and must not be done.
