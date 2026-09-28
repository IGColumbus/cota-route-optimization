# Experiment 4 — original-question addendum (N3 → N4 under one contract)

*Additive, 2026-09-28. `EXPERIMENT4_NORMALIZED_CLOSEOUT.md`, the EXP4N ranking,
the 200 certified candidates and the 1,785 excluded proposals are not reopened,
rerun or edited. The promotion cap is not repaired.*

Artifacts are in `outputs/exp4_addendum/`:

* `EXP4A_CONTRACT.json` — frozen before any run;
* `N4_canary.json`, `N3.json`, `N3_bridge.json`;
* `DELTA43.json` — firewall admission and comparison;
* `diag_N3.json`, `diag_N4.json`;
* `ABANDONMENT_N3_N4.json`;
* `rescore_N3.json`, `rescore_N4.json`;
* `pathcap_N3.json`, `pathcap_N4.json`.

The runners are `scripts/exp45_certify_cell.py`, `exp45_contracts.py`,
`exp4a_admit.py`, `exp4a_diagnostics.py`, `exp4a_abandonment.py`,
`exp4a_raptor_rescore.py` and `exp4a_pathcap.py`.

## 1. Why this addendum exists

EXP4N answered a narrow question: how 200 promoted greenfield candidates rank
against each other under one common envelope. It did not answer the question
Experiment 4 was built to ask: does the best greenfield network beat the best
constrained redesign from Experiment 3 (N3) under the same contract?
`pre_exp4_baseline_v1.json` states the obligation: Exp 4 "must beat the best
matched-effort member of this set, re-solved in the same run at matched
convergence". That comparison was never run. This addendum runs it.

| | Identity |
|---|---|
| **N4** | `exp4\|exp4-pool-v1\|65lines#35e351133d6f`, state digest `35e351133d6fcafc`. Its EXP4N result is authoritative. |
| **N3** | `add_stop-010#22c4c35ac5b2`, the singleton incumbent of `pre_exp4_baseline_v1`. Built with Experiment 3's own construction (`geometry.apply_edits` on the baseline, `mutate.edit_from_record`, validated by `contract.validate_applied`). Content digest `430aca035c70715b`. Its historical Stage B score is **provenance only**. |

## 2. One pipeline, proven equal to EXP4N first

There is no second scoring pipeline (OPERATIONS rule 15). Every number comes
from `exp4_certify.certify`, called exactly as `scripts/exp4n_launch.py` calls it:

* λ 2.0, seed 20260825;
* n_keys 8, k_rungs 3, max_rounds 120;
* `allow_off=True`, same-route waiting;
* a Gen1 greedy 20000/1/0 start inside `certify`, with no warm start from N4;
* one `_CandidatePathsets` scope per call.

The runner adds one observation-only wrapper around `exp3_score.solve_on_network`.
It records the enforced budget, the start audit and the per-period peak proxy,
and returns the callee's value untouched.

**Equivalence canary — PASS.** N4 was re-certified through the runner, and every
field equals `production_mr120/cc40b4f4aea3aa05.json` bit-exactly:

* objective `3223885.947526011`;
* plan `898b95fd93c33414`;
* 21 rounds, converged True;
* all 21 per-round objectives, 1,029 block enumerations, 6,628,797 combinations;
* every fitness field and all 390 plan entries.

The EXP4N contract was not violated, so `EXP4_CONTROL_PIPELINE_EQUIVALENCE_FAILURE`
does not apply. The Exp 5 production run later reproduced the same values a
second time (N4 J100 reproduction gate).

**Envelope.** Read from `COMMON_RESOURCE_ENVELOPE.json` and asserted against:

* the EXP4N production contract's IEEE-754 bit patterns;
* `ENVELOPE_FINGERPRINT_V1.json`.

It carries rounded `envelope_digest` **`3fd5241db44ca9da`** and exact fingerprint
**`0b46d1abc9a80c80`**. Both runs saw exactly one enforced budget, bit-equal to
it, with tolerance 0.0.

**D35 reach test — PASS on both networks.** With every route-period pinned to the
certified plan:

* moving the hours cap from usage × (1+10⁻⁶) to usage × (1−10⁻⁶) flips the plan
  from admitted to refused;
* the same holds for the most-utilized period's peak-proxy cap.

Both caps reach the feasibility decision.

**Representation bridge (D34).** N3 was certified in its own legacy
representation, as Experiment 3 built it. It was then scored at `certify`'s
first step through both the legacy construction and
`exp4_assemble.rebuild_like_assembler`, using the existing equivalence
machinery with no synthetic route IDs:

* Identical: plan digest `28135d0fa655e6e1`, generalized cost, unserved and
  served demand, revenue hours, and cost per served trip.
* Different: the peak proxy, by one unit in the last place
  (`176.408056390597` vs `176.40805639059698`) — summation order.
* The peak proxy is not in the objective. The feasibility tolerance (10⁻⁹
  relative) is about 10⁵ times larger than the difference.

## 3. The N3 re-solve

| | N3 | N4 |
|---|---|---|
| objective (λ=2) | **2,939,912.5807124916** | **3,223,885.947526011** |
| generalized cost | 1,198,080.52 | 859,908.52 |
| unserved demand | 14,515.27 | 19,699.81 |
| served demand | 16,433.73 | 11,249.19 |
| GC per served trip | 72.90 | 76.44 |
| revenue vehicle-hours (cap 2517.1833) | 2517.1631 (99.9992%) | 2517.0171 (99.9934%) |
| peak proxy, system max (cap 176.4931 pm) | 176.4081 | 176.0737 |
| rounds / converged | 1 / True | 21 / True |
| route-periods / OFF / locked | 173 / 54 / 28 (peak express) | 390 / 224 / 0 |
| start | greedy, no fallback, no rejection | greedy, no fallback, no rejection |
| plan digest | `28135d0fa655e6e1` | `898b95fd93c33414` |

N3 converged in one round: its greedy start was already block-locally optimal
at (8, 3). Both runs meet the requirements:

* treatment-independent starts;
* no warm start from N4;
* converged below the 120-round ceiling;
* feasible under the enforced caps.

## 4. Δ43 — firewall-admitted

Both receipts were built from the recorded execution facts and admitted by
`firewall.admit` under contract `EXP4A_MATCHED` (`0f62aeabfa341a98`).
`firewall.compare` (control N3, treatment N4) returned a `ComparisonResult`. The
only differences it declared are the network fields `NETWORK_DIFFERENCES`
permits: state digest, state key, cardinality, members and path-set digest.

```
Δ43 = obj(N4) − obj(N3) = +283,973.3668135195   (+9.659% of N3)
  generalized cost      −338,171.99
  unserved demand        +5,184.54 trips   (served −5,184.54, −31.5%)
  revenue vehicle-hours  −0.146
  peak proxy (max)       −0.334
  GC per served trip     +3.54
```

The objective is minimized, so positive means **N4 is worse**. N4's lower
generalized cost is not an efficiency gain: it carries 31.5% fewer riders, and
each served trip costs more.

**Interpretation.** Under the EXP4N contract — same envelope, evaluator,
objective, λ, seed, start policy and certifier — N4 does not beat N3. The
difference is +9.659% of N3's objective, 5,092× the D33-B band of 0.0018970%.

D33-B is **veto-only, asymmetric and a local lower bound**. At or below the band,
a difference would be noise. Above it, as here, the difference is **not thereby
established**, only not excluded. It is also local: over at most 10 of 173
route-periods, three rungs. The (N,K)-block-local residual of both plans is
unmeasured. Neither plan is known to be globally optimal for its network.

## 5. Cheap diagnostics on N3 and N4 (diagnostic only)

Every diagnostic reads the same setup that scored the certified plan. The plan
is re-pinned, and the resulting fitness is asserted bit-equal to the certified
record before anything is read.

**Abandonment and access (gate 4-8), N3 → N4, pair by pair:**

| | Result |
|---|---|
| OD flow reachable in N3 but not N4 | 8,736 of 30,949 (28.2%) |
| OD flow reachable in N4 but not N3 | 2,797 |
| Served flow lost / gained | 7,150 / 1,966 |
| Structurally unserved share | N3 35.5%, N4 54.7% |

Stops served per period (N3 → N4; stops losing service in brackets):

| Period | Stops served | Losing service |
|---|---|---|
| early | 1,870 → 1,584 | 702 |
| am_peak | 2,478 → 1,678 | 1,053 |
| midday | 2,249 → 1,994 | 563 |
| pm_peak | 2,504 → 1,924 | 831 |
| evening | 2,157 → 1,887 | 684 |
| owl | 1,053 → 1,000 | 573 |

For the riders N4 does serve, the ride is simpler:

* one-seat share 69–89% in N4 vs 55–79% in N3;
* 1.11–1.32 mean boardings vs 1.21–1.48.

N4 serves fewer, more direct trips. Neighbourhood-level aggregation was not
computed.

**Path adequacy (gate 4-9).** The cached path set was compared with fresh RAPTOR
under the certified plan (`adequacy.adequacy`):

| | N3 | N4 |
|---|---|---|
| flow with a cheaper path than the cache holds | 1.0–3.7% | **8.7–34.8%** (17–35% outside owl) |
| flow-weighted cost overstatement | 0.04–0.43% | **0.9–5.5%** |
| OD pairs reachable only by RAPTOR, per period | 1,379–2,662 | **3,252–5,870** |

**The frozen path model fits N4 much worse than N3.** N4's plan switches off
57% of its route-periods, which strands cached paths.

The omission-corrected probe re-costs each certified plan at min(cache, RAPTOR)
with the evaluator's own retention curve and arithmetic. It reproduces the
certified objective exactly from the cache first. It does not re-optimize.

| | N3 | N4 |
|---|---|---|
| objective | 2,885,539.84 (−1.85%) | 3,112,487.66 (−3.46%) |
| served | 18,101 | 15,605 |

Δ43 under omission correction is **+226,948 (+7.87%)**. The sign survives; the
size shrinks by a fifth. These are not certified numbers.

**Transfer depth (gate 4-9).** The OD-cost gap against RAPTOR one boarding deeper
(four boardings) barely moves from three:

* N4 pm_peak overstatement 5.47% → 5.48%;
* N3 am_peak 0.33% → 0.33%.

This probes the path set, not a re-optimized plan.

**Paths per OD (gate 4-9).** Raising `max_paths_per_od` from 4 to 6 leaves both
certified plans bit-identical:

* same objective;
* same path count (N3 152,381; N4 85,857).

The cap does not bind. `pathset.enumerate` keeps at most one path per OD per
pricing scenario, so path diversity is limited by the number of scenarios, not
by the cap. The 4→6 sensitivity is therefore null by construction. The real
adequacy gap is the one the omission probe above measures.

**Common lines (gate 4-10).** `hyperpath.bound` / `summarize` measure the
cross-route wait saving the same-route model omits:

| | Share of GC | Verdict |
|---|---|---|
| N3 | 1.16% | `locally_meaningful` |
| N4 | **12.47%** | **`potentially_frontier_changing`** |

Today's network measured 0.516%. N4's exposure has ballooned, which is exactly
the case gate 4-10 anticipated. Under the gate's rule, any N4 margin of this size
is **model-dependent** until a general waiting model is implemented.

The omitted saving would lower N4's cost more than N3's, so this caveat runs
against the sign of Δ43. For scale, the upper bounds are:

* N4: 107,248 weighted minutes;
* N3: about 13,950.

Even if all of N4's bound were credited and none of N3's, that is 93,300, less
than Δ43 (283,973) and less than the omission-corrected Δ43 (226,948). The
bound prices waits on legs already served. It does not model the extra riders
that shorter waits would retain, so it cannot settle the question. It is not
measured, and it is not excluded.

**Crowding (gate 4-11), not priced.** Peak segment load per trip against the
60-passenger planning capacity:

* **N4:** 0 overloaded route-periods; max 17.7 (pm_peak).
* **N3:** 1 of 31 active am_peak route-periods over capacity (max 68.3); all
  other periods under.

At this demand scale — a top-20,000 LODES commute proxy of 30,949 trips —
crowding does not bind on either network.

**Physical sanity:**

| | N4 | N3 |
|---|---|---|
| Patterns | 130 | 111 |
| Routes active | 49 of 65 | 33 of 39 |
| Active headway range | 5–240 min | 10–180 min |
| Other | 13 lines run in one period only | 25 headways over 60 min, all locked peak express |
| Stops in patterns | 2,059 | 2,949 |

No map-level physical inspection was done.

**λ sensitivity (fixed plans, not re-optimized).**
Δ(λ) = ΔGC + 60·λ·Δunserved = −338,172 + 311,073·λ.

| λ | 1.0 | 1.5 | **2.0** | 3.0 | 4.0 |
|---|---|---|---|---|---|
| Δ43 % of N3 | −1.31 | +5.13 | **+9.66** | +15.61 | +19.35 |

The sign flips at **λ ≈ 1.087**. The preregistered comparison is λ = 2, and the
certification contract requires robustness at λ ≥ 2, where N4 stays worse and
the gap widens. A re-optimized λ sweep was not run.

## 6. Gate table

| Obligation | Status | Evidence / reason |
|---|---|---|
| 4-8 abandonment | **RUN_IN_ADDENDUM** | §5: OD reachability, served loss, stops losing service, one-seat, transfers. Neighbourhood aggregation not done. |
| 4-9 path adequacy | **RUN_IN_ADDENDUM** | §5: adequacy on both networks; the path model is materially worse on N4; omission probe. |
| 4-10 common lines | **RUN_IN_ADDENDUM** | N4 12.47% of GC, `potentially_frontier_changing`: model-dependent. |
| 4-11 crowding | **RUN_IN_ADDENDUM** | Load profiles; does not bind at this demand scale. No crowding-enabled re-solve. |
| 4-12 demand robustness | **DEFERRED_TO_EXP7** | MET means preregistered, **not run**. |
| 4-13 structural identity | **UNRESOLVED** | MET means machinery exists, **not** that structure is stable. N3 vs N4 are plainly different maps; stability across independent optima was not measured. |
| Gate 12 convergence | **RUN_IN_ADDENDUM** | Treatment-independent greedy starts, both converged below 120, receipts admitted and compared. Restart-diversity residual unmeasured for the block certifier. |
| Wider OD universe | **DEFERRED_TO_EXP7** | Top-20,000 pairs only. |
| Transfer depth | **RUN_IN_ADDENDUM** | Four-boarding RAPTOR probe; negligible change. Plans not re-optimized. |
| Paths per OD | **RUN_IN_ADDENDUM** | 4→6 changes nothing, because the cap is non-binding (one path per scenario). Scenario-limited diversity is covered by the omission probe. |
| λ robustness | **RUN_IN_ADDENDUM** | Fixed-plan rescoring, sign flip at λ≈1.087; re-optimized sweep not run. |
| Physical inspection | **UNRESOLVED** | Structural counts only; no map review. |
| Fleet / deadhead | **UNRESOLVED** | EXP4N's instrument returns UNDECIDABLE for N4 and every candidate; deadhead provenance and terminal identity OPEN. Not run for N3. |

Gates 4-8 to 4-11 are **run in this addendum as diagnostics**. They are not
discharged as certification gates.

## 7. Final wording

**Result A — closed normalized ranking.** Under one common envelope, EXP4N
certified 200 promoted Experiment 4 candidates to (8, 3)-block-local optimality
and ranked them. N4 (`35e351133d6f`) is first, 0.387% ahead of second. That
ranking is closed and is not reopened here.

**Result B — the N3 → N4 comparison, with its limitations.** Under the identical
EXP4N certification contract, the Experiment 4 normalized leader N4 does **not**
beat Experiment 3's constrained redesign N3:

* N4's objective is 283,973 higher (+9.66% of N3); lower is better;
* N4 serves 5,185 fewer modeled trips (−31.5%) for the same vehicle-hours and
  peak proxy;
* the comparison is firewall-admitted;
* it survives an omission-corrected path costing (+7.87%);
* it holds for every fixed-plan λ above 1.087.

It is conditional on:

* the frozen path model, which fits N4 markedly worse than N3;
* the same-route waiting model, whose cross-route omission on N4 is 12.47% of
  generalized cost;
* the LODES-proxy demand;
* the modeled resource envelope.

Neither network is shown to be globally optimal. Nothing here is a fleet,
deployment or implementation claim.

Not claimed: global optimality; "best of 2,000"; deployable; fleet-feasible;
"COTA should implement" either network.

## 8. Post-script from Experiment 5 (added 2026-09-28, after §1–7 were written)

Experiment 5 re-certified N4 at 16 resource cells (`EXPERIMENT5_CLOSEOUT.md` §4).
That run showed the block certifier lands in **start-dependent local optima on
N4, differing by up to 1.70%**. Two consequences for this addendum:

* **The EXP4N N4 plan is not the best known N4 plan under the EXP4N
  envelope.** The Exp 5 H090 plan fits the same caps and scores
  3,219,614.74, which is 0.133% better. Using it, Δ43 = **+279,702 (+9.51%)**.
  The sign and order of magnitude are unchanged.
* **Result A needs a stronger caveat.** The observed start-basin gap (≥1.70%)
  is about 4.4× EXP4N's first-to-second margin (0.387%). The EXP4N ordering is
  exactly reproducible under its contract, but it is not robust to start basin
  among closely spaced candidates.

Experiment 5 also compared N4 with N0 (the existing geometry) at all 16 cells.
N4 is worse at every cell, by 8.07–11.59%, and all 16 comparisons are
firewall-admitted.
