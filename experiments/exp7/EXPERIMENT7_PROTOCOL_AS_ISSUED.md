# Experiment 7: as-issued protocol (23 September 2026)

## Provenance

* Ian supplied this content on 2026-09-29, as the **substantive content of
  the original 23 September Experiment 7 section**.
* It is kept as the historical, as-issued protocol.
* It does not contain two later texts, which are kept in their own files so
  the chronology stays visible:
  * the same-day 23 September classification revision:
    `docs/EXPERIMENT7_SEPT23_FINALIZATION.md`;
  * the 29 September amendments: `docs/EXPERIMENT7_AMENDMENT.md`.
* Parts of this text are superseded:
  * the F4 and F6 definitions;
  * the "COTA-compliant" solution;
  * the re-optimization rule.

  They are preserved here unchanged, **strictly as historical protocol**. They
  are not restored as current claims.
* The consolidated governing view is `docs/EXPERIMENT7_PROTOCOL.md`.

The text below, between the rules, is the as-issued content exactly as
supplied.

---

## Experiment 7 — Robustness and wrap-up

Exp 7 tests whether each conclusion survives worse assumptions, using a fixed,
preregistered matrix. It classifies findings, not objective values, and it
closes the project.

**Findings under test.** Exp 7 classifies each of these; nothing outside the
list gets a label:

1. F1 — Exp 1: −6.65% unserved demand at no added buses.
2. F2 — Exp 2/2B: route splices produce a certified null.
3. F3 — Exp 3: the single certified add_stop mutation, −0.187%.
4. F4 — EXP4N: the normalized incumbent beats current geometry, by its
   certified margin.
5. F5 — Exp 5: the marginal return per unit of peak resource.
6. F6 — Exp 6: the price of the COTA-compliant regime, on N0 and N4.

**Solutions under test.** The Exp 1 plan, the EXP4N incumbent, the
COTA-compliant Exp 6 plan on each network, and Exp 5 at 90% and 110%.

**Class A — perturbations of the same model.**

| ID | Perturbation | As-issued levels |
|---|---|---|
| A1 | Non-commute demand added to LODES | gravity-model trips at 25%, 50%, and 100% of commute volume |
| A2 | Demand sampling | 20 bootstrap draws of the LODES block pairs |
| A3 | Runtime | +10% uniform, +20% uniform, and per-link noise at the measured 20.5% median error |
| A4 | Reliability | wait penalty inflated for headway variance, 2 preregistered levels |
| A5 | Cost weights | λ ∈ {1, 4}; transfer penalty ×0.5 and ×2 |
| A6 | Walking | walk speed −15%; maximum walking distance −25% |
| A7 | Disruption | remove each of the 10 busiest routes, one at a time |

Non-commute demand was first priority because commute-only LODES was
considered the largest unquantified demand error.

**Class B — alternate models, reported as model disagreement.**

* Common-lines or hyperpath assignment, addressing the cross-route waiting
  issue.
* A jobs-accessibility objective in place of generalized cost.

A disagreement here is a model disagreement, not a Class A perturbation
result.

**Re-optimization rule.** Re-optimize only under the two Class A
perturbations that moved F1 and F4 most.

---

## Notes on this record (not part of the as-issued text)

* The as-issued text did not give numeric values for A4's two reliability
  levels. None are claimed here.
* A8 (the journey-cost retention curve) is **not** in this matrix. It was
  added afterwards (see the amendment).
* "No added buses" (F1) is historical wording. Current reporting uses the
  solver's resource terminology (the Exp 1 fleet-wording correction in
  `outputs/CANONICAL_RESULTS_v4.json`).
