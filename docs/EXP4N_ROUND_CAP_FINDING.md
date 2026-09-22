# EXP4N — the round cap became binding under normalization

**Status: open finding, recorded while the run is in flight. Nothing here is a
result of the normalized experiment; it is a property of the search under the
new resource envelope.**

Raised 20:55 UTC 22 Sep 2026, at 19 of 200 candidates.

## What happened

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

## What is NOT being done

`max_rounds` is **not** being raised. Ian's execution instructions forbid tuning
the optimizer, and the pilot gate's bit-exact reproduction of the audit depends
on identical search parameters (`n_keys 8, k_rungs 3, max_rounds 40, lam 2.0,
seed 20260825`). Changing it mid-run would split the batch into two
incomparable halves — the same failure `OPERATIONS.md` rule 24 exists to
prevent. The run continues unchanged.

## What IS being done

1. Every `converged == False` is counted and its candidate recorded.
2. The count goes into §7 validation alongside the feasibility counts.
3. §13 discloses it explicitly, distinguishing two cases that must not be
   conflated:
   * `rounds == 40 AND converged` — a genuine certificate reached on the last
     permitted round, with zero headroom (e.g. `rank_25`).
   * `rounds == 40 AND NOT converged` — **no certificate at all** (e.g. this
     one).
4. If the final count is large enough that truncated candidates could
   plausibly occupy or displace the top of the ranking, the ranking is
   reported as **not** a ranking of certified optima, and the §12 gate must
   reckon with that rather than waving it through.

## What is deliberately not claimed

No rate is projected from 1 case in 19. The project rule is no claim on a
bucket under ~20 members and never build a rate out of a few events. The count
is the count; the denominator is 200 and it is not finished.

## Runtime, revised

Observed over the first 19: mean **1007 s**, median 924 s, range 766–1478 s —
faster than the 1442 s pilot mean, because the pilot deliberately sampled the
extremes. 181 candidates remain, so roughly **51 h** of compute, excluding
reclaim losses.
