# `envelope_digest` does not establish bit-exact envelope identity

**Audit note, 23 Sep 2026. Raised during the EXP4N production contract freeze,
while the production run was already in flight. Nothing here invalidates that
run — see "Why the current run is protected" below.**

## The finding

`envelope_digest` is **necessary but not sufficient** for bit-exact
peak-envelope identity.

`scripts/exp4n_freeze_envelope.py:100-105` computes it as:

```python
payload["envelope_digest"] = digest({
    "peak": {p: round(peak[p], 9) for p in PERIODS},
    "hours": round(VH_CAP, 9),
    "tolerance": TOL,
    "source": payload["source"],
})
```

The `round(..., 9)` is the problem. Two envelopes that differ below the ninth
decimal place hash to the **same digest**. A digest match therefore rules out
gross substitution of the envelope but says nothing about the last few units in
the last place.

## How it surfaced

Not theoretically. The first draft of
`scripts/exp4n_freeze_production_contract.py` asserted the peak envelope against
constants I had transcribed by hand from a log line that printed them rounded to
six decimals. Two were wrong in the last ULP:

| period | hand-typed | actual |
|---|---|---|
| midday | `159.17277777777778` | `159.17277777777775` |
| evening | `140.19458333333333` | `140.19458333333336` |

**The digest matched in both cases.** It would not have caught this. The
explicit bit-exact comparison did — it failed the freeze, which is what sent me
back to check, and the check showed the error was in my typing, not in the
envelope.

The wider lesson is the one the mistake illustrates rather than the mistake
itself: **assert against the frozen artifact, never against a constant
transcribed from human-readable output.** Rounded display is not a source of
truth, and a rounding digest will not save you from treating it as one.

## Why the current run is protected

EXP4N production's envelope identity does not rest on the digest.
`scripts/exp4n_freeze_production_contract.py` asserts the production-resolved
envelope **bit-exactly** against two independent sources, and both passed before
the run was allowed to start:

1. `outputs/exp4_normalized/COMMON_RESOURCE_ENVELOPE.json`, the frozen artifact.
2. The `peak_caps` recorded by all 21 accepted calibration results — i.e. the
   envelope the calibration actually ran under, not a description of it.

The digest is corroborating evidence, not the proof. The run is sound and
continues unchanged.

The exact values this run used are preserved losslessly — `repr`, `float.hex()`,
big-endian IEEE-754 bytes, and the raw 64-bit integer — under
`exact_peak_envelope_used_by_this_run` in
`outputs/exp4_normalized/EXP4N_PRODUCTION_CONTRACT.json`. That record was added
after launch and is purely additive; it changes no existing field and does not
touch the run.

For reference:

| period | value | IEEE-754 hex |
|---|---|---|
| early | `85.28208333333332` | `0x1.5520da740da73p+6` |
| am_peak | `162.00944444444443` | `0x1.4404d5e6f8091p+7` |
| midday | `159.17277777777775` | `0x1.3e587654320fep+7` |
| pm_peak | `176.49305555555554` | `0x1.60fc71c71c71cp+7` |
| evening | `140.19458333333336` | `0x1.1863a06d3a06ep+7` |
| owl | `35.55736111111111` | `0x1.1c7579be02469p+5` |

## Deferred action — AFTER EXP4N completes

Add a **separate** exact-envelope fingerprint for future experiments: a hash over
a canonical lossless representation — raw IEEE-754 bit patterns or `float.hex()`
— rather than a rounded decimal.

Constraints on that change, which are not negotiable:

* **Do not retrofit it into the running contract.** The EXP4N production
  contract is frozen as it stands.
* **Do not use it to invalidate this run.** This run's envelope identity is
  already established by the bit-exact assertions above.
* **Do not replace `envelope_digest`** in artifacts this run has already
  written. The new fingerprint is *additional*, for experiments that come after.

The material needed is already in place: the lossless bit patterns recorded in
the production contract mean the future fingerprint can be computed over this
run's envelope retrospectively, for comparison, without re-resolving anything.
