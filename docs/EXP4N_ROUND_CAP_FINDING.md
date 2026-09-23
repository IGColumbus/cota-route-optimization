# EXP4N — the round cap became binding under normalization

**Status: the full-200 batch was ABORTED on this finding at 21:32 UTC 22 Sep
2026. A round-cap calibration pilot is running in its place. Nothing here is a
result of the normalized experiment; it is a property of the search under the
new resource envelope.**

Raised 20:55 UTC 22 Sep 2026 at 19 of 200; batch aborted at 21:32 with 21
completed.

## 1. Why MAX_ROUNDS = 40 was defensible under legacy Exp 4

It was not arbitrary for the regime it was chosen in. Across all 200 legacy
candidates the round counts were mean 12.0, median 13, **maximum 14**, with
**zero** candidates at the cap and **200/200 converged**. A ceiling of 40 sat
at roughly 2.9x the worst observed case. Nothing in that run gave any reason to
think the ceiling was reachable, let alone binding.

## 2. Why normalization changed the search regime

Under the endogenous cap, `exp2.py:324` resolved `peak_fleet_by_period:
"baseline"` against *each candidate's own* baseline plan, so every candidate
faced an envelope that was loose for it by construction. Under the common
reference envelope the peak arm actually binds. Two independent measurements
say so: the resource-normalization audit found **0/200** legacy certified plans
feasible under the reference envelope, and the OFF-ON diagnostic found peak
binding at **99.705-99.967%** in all six periods while the hours arm still had
1,594 vehicle-hours of slack. A binding constraint forces the block-local
search to crawl along the feasible boundary instead of moving freely through
the interior, so exhausting the neighbourhood takes far more rounds.

## 3. The paired increase: 21 of 21

## What happened

## 4. The non-converged candidate at the ceiling

Legacy rank 12, candidate `12ab99b5915e`, returned

```
obj 3,262,415.1115   rounds 40   converged False
```

`rounds == MAX_ROUNDS == 40` **and** `converged == False` means the block-local
search was still finding improving moves when the round cap stopped it. Per
`src/cota_opt/exp4_certify.py:264-292`, `converged` is set only when a full
round finds no improving block move. So this candidate carries **no
block-local optimality certificate**, and its objective is an **upper bound** —
the true block-local optimum for it is at least as good, possibly better. It
can therefore be **under-ranked**.

## This is not parity with the legacy run

The legacy endogenous-cap Exp 4, frozen in
`outputs/exp4_normalized/EXP4_ENDOGENOUS_CAP_ARCHIVE.json`:

| | legacy, all 200 | normalized, first 19 |
|---|---|---|
| rounds mean | 12.0 | 23.5 |
| rounds median | 13 | 20 |
| rounds max | **14** | **40** |
| at the cap (40) | **0** | 2 |
| not converged | **0 / 200** | 1 / 19 |

Paired on the same 19 candidates: legacy mean 12.7, normalized mean 23.5,
**every one of the 19 took more rounds**, mean delta **+10.8**, no decreases.

## Mechanism

Under the endogenous cap each candidate was optimized against *its own*
baseline peak envelope, which is loose for it by construction. Under the common
reference envelope the peak arm actually binds — the resource-normalization
audit found **0/200** legacy certified plans feasible under the reference
envelope, and the OFF→ON diagnostic found peak binding at 99.705–99.967% in all
six periods with 1,594 vehicle-hours of slack on the hours arm. A binding
constraint forces the local search along the feasible boundary instead of
moving freely, so it needs far more rounds to exhaust the neighbourhood.

**`MAX_ROUNDS = 40` was adequate for a regime whose observed maximum was 14. It
is not obviously adequate for this one.** The parameter was not chosen for the
problem it is now solving.

## 5. Why the full batch was aborted

At 21 of 200, continuing would have spent roughly 50 more hours of compute
producing a ranking that mixes certified block-local optima with uncertified
upper bounds. Those two things are not comparable, and no amount of downstream
analysis repairs the mixture. A candidate stopped at the ceiling while still
improving can only be **under**-ranked, so the contamination is directional,
not random noise that averages out.

pid 827 was stopped with SIGTERM at 21:32:43 UTC after 03:02:47 elapsed and
exited within two seconds. Nothing was deleted or overwritten. One candidate
was in flight and produced no file — results are written per candidate only on
completion, so there are no partial records.

Full state in `outputs/exp4_normalized/EXP4N_ABORTED_ROUND_CAP_INVALID.json`:
21 completed, 0 partial, 179 not started, 0 errored; 20/21 converged, 1 not;
2 at the ceiling of which 1 converged and 1 did not; wall mean 1009 s, total
5.89 h.

> The abort instruction said 19 completed. It was written from the 20:55
> report; two more candidates finished before the 21:32 stop. The calibration
> set is all **21**.

## 6. Why the 21 outputs are diagnostic only

They were produced under a ceiling now known to be capable of truncating an
active search in this regime. Even the 20 that converged converged *under that
ceiling*, and one of them (`rank_25`, 40 rounds, converged) had zero headroom.
They are therefore evidence about search behaviour, not about candidate
quality. They **must not** be used as the normalized Exp 4 ranking and **must
not** be spliced into the production batch. The production certification
restarts all 200 from scratch under one identical parameterization.

## 7. The MAX_ROUNDS = 200 calibration pilot

**Method.** The same 21 candidates, rerun from scratch, with the round ceiling
raised to 200 and *nothing else changed*. Held fixed: the common normalized
envelope (digest `3fd5241db44ca9da`), the objective and exact evaluator, the
candidate geometries, the greedy initialization, the neighbourhood, move
generation, move ordering, acceptance logic, tolerances (0.0), `lam` 2.0, seed
20260825, tie-breaking, the resource constraints, `n_keys` 8, `k_rungs` 3, and
the contract digest `2125984c82b60a83`.

**The convergence criterion is untouched.** `exp4_certify.py` still sets
`converged` only when a full round finds no improving block move. What changed
is the maximum permitted search duration, so that criterion can actually
operate instead of being pre-empted.

**Implementation.** `certify()` already accepted `max_rounds` and `progress` as
keyword arguments, so `src/cota_opt` did **not** need to change — verified
clean, with `tests/test_exp4_normalized.py` and
`tests/test_exp4_resource_audit.py` passing. `scripts/exp4n_launch.py` gained
three additive flags that default to existing behaviour: `--max-rounds`
(ceiling only), `--out-dir`, `--trajectory`. Records now carry the *effective*
ceiling plus `max_rounds_default` and `round_ceiling_overridden`, so no result
can misreport which ceiling produced it. Calibration and production use the
same launcher deliberately — that is a stronger guarantee of identical search
behaviour than a parallel script.

Output goes to `outputs/exp4_normalized/calib_mr200/`, never to `certified/`.

**Per candidate, recorded:** convergence status, convergence round, final
objective, objective at round 40, improvement after round 40, final improvement
round, total runtime, improving rounds after 40, whether the incumbent was
still improving in rounds 35-40, and whether it was still improving near
termination — plus the full per-round incumbent trajectory.

> One honest limit. The progress callback fires once per round, so what is
> observable is the number of **rounds** in which the incumbent improved after
> round 40, not the number of individual accepted moves. Counting accepted
> moves would require modifying the frozen optimizer. The distinction is stated
> rather than papered over.

**Results.** Ran 21:35 UTC 22 Sep to 03:25 UTC 23 Sep, 5.84 h of compute, all
21 candidates, zero errors. Full artifact:
`outputs/exp4_normalized/EXP4N_ROUND_CAP_CALIBRATION.json`.

| legacy rank | candidate | rounds @40-cap | rounds @200-cap | converged | reproduces |
|---|---|---|---|---|---|
| 7 | c85f68507f8c | 15 | 15 | yes | exact |
| 3 | d1f8d2497954 | 16 | 16 | yes | exact |
| 11 | 32217e8b5098 | 16 | 16 | yes | exact |
| 2 | 08f377545e31 | 17 | 17 | yes | exact |
| 10 | 113872a5a967 | 17 | 17 | yes | exact |
| 5 | 24e142fc0287 | 17 | 17 | yes | exact |
| 71 | 99c5d391c164 | 17 | 17 | yes | exact |
| 150 | 350c7cf4e725 | 17 | 17 | yes | exact |
| 6 | 03fce0e3f398 | 18 | 18 | yes | exact |
| 14 | 81d9a2f8c376 | 19 | 19 | yes | exact |
| 4 | 21fa771c4311 | 20 | 20 | yes | exact |
| 8 | 98054c48fe48 | 21 | 21 | yes | exact |
| 1 | ecb2ffc4bcce | 25 | 25 | yes | exact |
| 17 | e10f2321e79b | 25 | 25 | yes | exact |
| 200 | 96485eb1a98e | 28 | 28 | yes | exact |
| 100 | 229cb1654b51 | 30 | 30 | yes | exact |
| 50 | d6f401185657 | 31 | 31 | yes | exact |
| 13 | 80a5c289e861 | 32 | 32 | yes | exact |
| 9 | 3302f2af66ee | 36 | 36 | yes | exact |
| 25 | 12165a4c04c6 | 40 | **40** | yes | exact |
| 12 | 12ab99b5915e | 40 *(conv False)* | **44** | **yes** | **differs** |

**Distribution:** min 15 · median 20 · mean 23.86 · p90 36 · **max 44** ·
stdev 8.47. **Not converged by 200: zero.**

**Exactly one of 21 was truncated by the old ceiling**, and 20 of 21 reproduce
the aborted run's rounds *and* objective exactly.

### The truncated candidate

`12ab99b5915e`, legacy rank 12. Under the 40-cap: `3262415.111480918`, 40
rounds, `converged False`. Under the 200-cap: `3262379.764323833`, **44
rounds, `converged True`**.

Its calibration trajectory's objective **at round 40 is bit-identical to the
aborted run's final objective**. The search path is therefore the same up to
the old ceiling — direct evidence that only the ceiling moved and no other
search behaviour changed. It improved in rounds 41, 42 and 43; round 44 found
no improving move and it converged. It had in fact improved in **every round
from 2 to 43**, a long monotone descent rather than an oscillation.

Truncation cost: **35.3472 objective units, 0.001083%** — real, but two orders
of magnitude below the 2.2788% legacy objective spread.

### The zero-headroom candidate

`12165a4c04c6`, legacy rank 25, was the other candidate at the ceiling: 40
rounds, `converged True`. Under the 200-cap it returned **40 rounds,
`converged True`, identical objective**. It genuinely converged at round 40;
the zero headroom was coincidence, not truncation. `converged == True` at the
ceiling means what it says.

### Runtime model

`seconds ~ 366 + 26.7 * rounds`, pearson r = 0.9922. Fixed overhead ~366 s,
marginal ~26.7 s per round.

### Sample caveats, stated plainly

n = 21 is **not** a random sample of the 200. It is the 10-candidate audit
pilot plus legacy ranks 1-14 in order: ranks 1-14, 17, 25, 50, 71, 100, 150,
200. Fourteen of the 21 are legacy ranks 1-14, so the top of the legacy ranking
is over-represented and 179 candidates are unsampled. Correlation between
legacy rank and convergence round is pearson +0.0791, spearman +0.3366 —
**not a reliable relationship at this n with this composition**, so the
convergence behaviour of the unsampled 179 should be treated as unknown. The
maximum of a 21-candidate sample also understates the maximum of 200. All of
this argues for headroom, not against it.

## 8. Basis for the production round cap

**Recommendation: `MAX_ROUNDS = 120`.**

The decisive structural fact is that **raising the ceiling costs nothing for
candidates that converge earlier.** `exp4_certify.py` breaks out of the round
loop the moment a full round finds no improving move, so the ceiling only
consumes time for candidates that would otherwise have been truncated — which
are precisely the ones that should be allowed to finish. Erring high is close
to free, and the choice is therefore governed by where a ceiling stops being
useful as an alarm, not by compute cost.

* **2.7x** the observed maximum natural convergence round of 44.
* mean 23.86 + **11.3 standard deviations**.
* A candidate that actually ran the full 120 would take about **59 minutes**
  (366 + 26.7 x 120 = 3564 s) — tolerable as a worst case.
* Still low enough that a candidate reaching it is a genuine alarm worth
  stopping for, rather than a silent multi-hour burn.

Alternatives considered: **100** (2.3x observed max) is defensible but leaves
less headroom for the 179 unsampled candidates. **200** is known safe — 0/21
reached it — but a capped candidate would cost ~95 min and the extra headroom
buys little over 120. **60** is only 1.4x the observed max and sits too close
to a tail that a 21-candidate sample understates; not recommended.

**Expected full-200 runtime: ~56 h** (200 x the observed 1002 s mean), ~50 h on
the median, bracketed 42-85 h if every candidate were as fast or as slow as the
extremes seen. The ceiling does not change runtime for candidates that converge
naturally, so this is driven by the convergence distribution rather than by the
cap; even ten candidates running the full 120 rounds would add only about 7 h.

**Stop condition.** If any candidate fails to converge by 120, that is not a
signal to raise the ceiling again. It is a signal that the search or the
convergence criterion has a deeper problem in this regime, and it will be
flagged as such rather than papered over with another arbitrary number.

## How this should and should not be characterized

**Not:** "the optimizer was changed to get a better answer."

**Accurately:** the normalized common envelope changed the optimization regime.
That exposed a stopping ceiling calibrated on the legacy regime as capable of
truncating searches that were still active. The calibration changes only the
maximum permitted search duration, so that the existing, unmodified convergence
criterion can operate. No candidate becomes certified by being given more
rounds — it becomes certified by satisfying the same criterion it always had
to satisfy.

Throughout, and in the final certification:

* `rounds == MAX_ROUNDS && converged == True` — a genuine block-local
  certificate, reached with zero headroom.
* `rounds == MAX_ROUNDS && converged == False` — **no certificate**, an
  uncertified upper bound.

These must never be conflated.
