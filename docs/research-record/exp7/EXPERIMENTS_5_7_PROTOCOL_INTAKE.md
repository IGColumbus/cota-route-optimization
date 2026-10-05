# Experiments 5–7 protocol — intake note

Ian issued the full Experiments 5–7 protocol at ~17:10 UTC 23 Sep 2026, while
EXP4N production was at 45/200. The protocol itself is his text and is frozen as
issued; this note records intake, the two blocking corrections raised before any
of it becomes load-bearing, and what may legitimately proceed now.

**Nothing in Experiments 5–7 starts until EXP4N returns
`EXP4_FULL_NORMALIZED_CERTIFIED`.** That is the protocol's own gate and the run
is at 45/200. Priority remains keeping EXP4N alive.

---

## BLOCKING CORRECTION 1 — the solver-noise threshold cites a superseded figure

The protocol's shared rule §7 states:

> D33 measured the maximum local heuristic gap as `0.001837%`. This becomes the
> preregistered solver-noise threshold.

**That figure was superseded on 2026-09-02 by D33-B**, and D33-B exists
precisely because it was not allowed to transfer. From `DISCOVERIES.md:1945`:

> D33 was measured at discovery effort and preregistration §7 forbids that
> figure from transferring. This is the re-measurement …
>
> **The design predicted the gap would shrink with more search. It did not.**
>
> | | discovery effort | Stage B effort |
> |---|---|---|
> | max gap | 0.0018370% | **0.0018970%** |
> | cells with any gap | 9 of 75 | 17 of 375 |

D33-B is the larger measurement, on 375 cells rather than 75, anchored on plans
whose digests were verified against the Stage B receipts. Preregistering
`0.001837%` would preregister the number the project already retired, and it is
*smaller*, so it under-states the band.

**Proposed: preregister `0.0018970%`** (D33-B, 375 cells, Stage B effort).

## BLOCKING CORRECTION 2 — the threshold is a veto, not a certificate

`DISCOVERIES.md:2003` attaches a caveat that it says must travel with the
figure:

> this is a **local** optimality check over at most 10 of 173 route-periods
> across three ladder rungs. It is a *lower* bound on the differential-error
> bound; the full-problem differential can only be larger. A margin above it is
> **not thereby established** — it is only *not excluded* by this measurement.

So the two halves of §7 are not symmetric:

* **`≤ threshold` → solver noise. SOUND.** If the local gap can be that large, a
  difference that small cannot be distinguished from it.
* **`> threshold` → substantive. NOT SOUND as written.** The true full-problem
  differential can only be *larger* than the measured bound, so a difference
  just above it may still be solver error. The doc says a margin above it is
  "not thereby established".

This is the same inversion an earlier standing rule on this project guarded
against ("do not use D33's 0.0018 points as a threshold — it is a veto-only
diagnostic").

**Proposed:** keep §7 as a veto — below the band, claim nothing — and read the
`> threshold` side as *triggering review*, not as *establishing an effect*.

Most of the protocol already does exactly this and needs no change:
`EXP5_MONOTONICITY_FAILURE` halts pending review, `EXP5_N4_HOURS_NULL_VIOLATION`
halts and audits, and the N0 hours-expansion trigger activates more compute.
All three fail safe. The wording to fix is §7's "differences > 0.001837%
require substantive interpretation", and any later reading of a supra-threshold
difference as a certified effect.

---

## What may proceed before EXP4N certifies

The protocol permits Experiment 6 policy-document research during EXP4N, since
it needs no optimizer compute. It does, however, compete with the hold cadence
that keeps the container alive, so it is deliberately NOT started while EXP4N is
mid-run. EXP4N certification is worth more than a head start on document
research.

Deferred to EXP4N completion, in order: the exact IEEE-754 envelope fingerprint
(shared rule §4, and the deferred action already recorded in
`docs/ENVELOPE_DIGEST_INSUFFICIENCY.md`), the Exp 5 Step 0 resource-axis
provenance note, and the Exp 6 constraint catalog.

## Compute estimates — checked against measured throughput

EXP4N production is measuring ~1002 s per certified cell.

| stage | cells | implied | Ian's estimate |
|---|---|---|---|
| Exp 5 Arm A | 6 levels × 2 networks = 12 | ~3.3 h | — |
| Exp 5 Arm B | 2 | ~0.6 h | — |
| Exp 5 Arm C | 3 × 2 = 6 | ~1.7 h | — |
| **Exp 5 total** | **20** | **~5.6 h** | **~6 h** |
| Exp 6 single regimes | ~21 × 2 = 42 | ~11.7 h | — |
| Exp 6 combinations | ≤6 × 2 = 12 | ~3.3 h | — |
| **Exp 6 total** | **~54** | **~15.0 h** | **~15 h** |

Both estimates check out against measured throughput. Two caveats: cells needing
more rounds cost more (the runtime model is ~366 s + ~26.7 s per round), and N0
throughput is unmeasured — no N0 cell has ever been run under this contract.

## Consistency with the earlier Exp 5 premise audit

The protocol's structure matches what the premise audit found and is consistent
with `EXP5_REFRAME_REQUIRED`: the peak arm binds (99.705–99.967% across all six
periods) while hours sit at ~36.66% utilisation. Arm A sweeping peak, Arm B
null-checking hours, and Arm C probing where hours *start* to bind is the
reframe the audit asked for. The proxy-units labelling rules (§5, §8, Step 0)
also adopt the audit's finding that the constrained quantity is a
cycle/headway proxy and not a fleet count.
