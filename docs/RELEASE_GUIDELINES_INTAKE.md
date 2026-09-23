# Release guidelines + protocol v2 — intake and corrections

Ian issued the amended Experiments 5–7 protocol (amendment #1, frozen base
`e59bf061`) and the Release and Reporting Guidelines at ~17:35 UTC 23 Sep 2026,
with EXP4N production at 46/200. Both are his text and are authoritative.

**Amendment #1 accepted both corrections I raised**: the noise band is now
D33-B's `0.0018970%` everywhere, and rule 7 is asymmetric — a difference at or
below the band is solver noise; above it is *not thereby established*, only not
excluded. It triggers review or compute and never counts on its own as proof of
an effect or a bug. That is the right reading of `DISCOVERIES.md:2003`.

Three things verified against the repo below. One is a real correction.

---

## CORRECTION — the "19–26%" seed-disagreement range mixes two evaluators

The guidelines use it twice: report rule 8 ("Independent seeds disagree on
19–26% of route-periods, so individual headways are never presented as
recommendations") and the Figure 7 aggregation contract rule 5.

`DISCOVERIES.md:723-728` shows where both ends come from:

> Plan disagreement: worst pair **19.7%** of route-periods, mean 19.1% …
>
> Model B is better conditioned than Model A on both counts — half the
> objective spread (0.064 against 0.127) and a quarter less plan disagreement
> (**19.7% against 26.0%**)

**19.7% is Model B. 26.0% is Model A.** Model A is the superseded evaluator;
Model B is the certified one the whole project runs on. So "19–26%" reads as a
range under the current model when it is actually one figure from the current
model and one from the corrected-away predecessor.

The conclusion is untouched — 19.7% is far more than enough to forbid
route-level recommendations — but the project's own report rule 1 requires every
number to state its evaluator, and this one would fail it.

**Proposed: "Independent seeds disagree on about 19% of route-periods under
Model B (worst pair 19.7%, mean 19.1%)."** If the wider range is wanted for
emphasis, state it as "26.0% under the superseded Model A, 19.7% under
certified Model B".

---

## VERIFIED — 197 peak vehicles has a real basis, and a units trap next to it

`cota-opt reproduce exp1` is specified to assert that COTA's published blocking
reconstructs to 197 peak vehicles. That figure is recorded:

* `outputs/CANONICAL_ENVELOPE.json` — `peak_vehicles: 197.0`, and
  `contract_text: "2,517.183 weekday revenue vehicle-hours · 197 peak vehicles"`
* `outputs/fleet_check_modelB.json` — `peak_vehicles: 197`

So the assertion is well-founded **for the existing schedule**, which is exactly
the scope the guidelines give it.

**The trap:** that 197 is a *block-derived* count. The EXP4N peak envelope is
the *cycle-over-headway proxy* — 85.28 / 162.01 / 159.17 / 176.49 / 140.19 /
35.56 by period. They are different quantities in different units, and
`CANONICAL_ENVELOPE.json` states them side by side in one `contract_text` with
physical-vehicle language. Anything generated from that artifact inherits the
confusion the protocol's rules 5 and 8 exist to prevent. Flagged for the
restructure, not for now: the artifact is cited by existing provenance records
and must not be edited before the `research-final` freeze.

---

## CONFIRMED STILL PRESENT — the README claim the guidelines call out

`README.md:24` still reads:

> by **2.34% ± 0.01** — with **no additional buses** (197.0 peak vehicles

and `HANDOFF.md:112` still opens a section "**It needs no additional buses.**"
(though :114 does qualify it as "the block-derived fleet proxy"). The guidelines
put this in the post-freeze Report block, so it is not touched now — recorded
here so it is not missed.

---

## Blocker on the release gate that is not in the checklist

The gate requires "All work branches, including `exp3-clean` and anything newer,
merged into `master`". **This repository has never been pushed.** There is no
`origin`; the only remote is `ian`, carrying `master` alone. Everything since
the Exp 3 work — all of EXP4N — exists only in this container's git and in the
bundles handed over manually.

Nothing about that is fixable from here: the sandbox cannot push, and the agreed
route is bundle → `SendUserFile` → `device_commit_files` → `git fetch` the
bundle → Ian merges `cloud/exp3-clean` and pushes from GitHub Desktop. It needs
Ian at a keyboard. It belongs on the Freeze checklist ahead of "merge into
master", because the merge cannot happen until the commits reach his machine.

---

## What proceeds now

Nothing in Experiments 5–7 starts until `EXP4_FULL_NORMALIZED_CERTIFIED`.
EXP4N is at 46/200 with ~36h remaining. The Exp 6 constraint catalog is
research-only and formally unblocked, but it is still not started: it competes
with the hold cadence that keeps the container alive, and certification is worth
more than a head start on reading.

The A8 retention-curve perturbation is noted as the largest untested modelling
assumption and is now in the Class A matrix — that addition is right, and it
lands before Exp 7 runs rather than after.
