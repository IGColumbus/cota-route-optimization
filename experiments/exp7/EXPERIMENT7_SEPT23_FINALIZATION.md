# Experiment 7: same-day classification revision (23 September 2026)

## Provenance

* Ian supplied this on 2026-09-29, as the final 23 September reporting
  convention.
* It supersedes the earlier draft formulation, which used ±50% as part of the
  definition of "Robust".
* It is kept separate from the as-issued matrix
  (`docs/EXPERIMENT7_PROTOCOL_AS_ISSUED.md`) and from the 29 September
  amendments (`docs/EXPERIMENT7_AMENDMENT.md`).

---

## Sign robustness

| label | meaning |
|---|---|
| **SIGN_ROBUST** | the finding's sign survives every supported, applicable sensitivity level |
| **SIGN_SENSITIVE** | a strict sign flip, or a movement into or out of the tie band, occurs at any applicable level |

The existing `SIGN_FLIP`, `TO_TIE` and `FROM_TIE` mechanics in the amendment
remain the machine-level implementation (`scripts/exp7_classify.py`).

## Magnitude stability

Measured relative to the certified BASE effect magnitude:

| change in magnitude vs BASE | label |
|---|---|
| ≤ 10% | Highly stable magnitude |
| > 10% and ≤ 25% | Stable magnitude |
| > 25% and ≤ 50% | Moderately sensitive magnitude |
| > 50% | Highly sensitive magnitude |

These magnitude labels are **descriptive reporting conventions. They do not
determine sign robustness.**

**Near-zero BASE effect.** Sometimes the baseline effect is zero, or so close
to zero that a relative ratio means nothing (defined operationally in
amendment §7). In that case the result is `MAGNITUDE_RATIO_UNINFORMATIVE`,
and the absolute movement is reported instead. A percentage is never
manufactured by dividing by a near-zero baseline.

## Separate descriptors

Operational fragility, policy conflict and model dependence are reported as
separate descriptors. None of them substitutes for sign robustness.
