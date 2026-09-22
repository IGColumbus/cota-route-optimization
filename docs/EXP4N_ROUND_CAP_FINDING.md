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

**Results: PENDING.** Launched 21:35 UTC 22 Sep as pid 2314.

## 8. Basis for the production round cap

**PENDING** the pilot. The cap will be justified by the convergence
distribution observed in *this* regime — min, median, mean, p90 and max
convergence round, plus the count not converged by 200 — with meaningful
headroom above the observed maximum. It will not be justified by the legacy
run, whose distribution has been shown not to transfer.

If any candidate fails to converge by 200, that is not a signal to pick a
larger arbitrary cap. It is a signal that the search or the convergence
criterion has a deeper problem in this regime, and it will be flagged as such.

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
