# Experiment 7 — amendment DRAFT (not in force)

*Drafted 2026-09-28 while Experiment 6 was running. Per `EXPERIMENT6_PROTOCOL.md`
§16 and §18 step 16, the Exp 7 amendment is **not finalized until Exp 6 has
closed**. Updated 2026-09-29 after Exp 6 closed as
`EXP6_POLICY_FRONTIER_CERTIFIED`; §4 records what it found. It is still a draft
for Ian's review, and nothing here authorizes compute.*

## 0. Blocking precondition: the base text is not in the repository

The 23 September Experiments 5–7 protocol is Ian's text, "frozen as issued"
(`docs/EXPERIMENTS_5_7_PROTOCOL_INTAKE.md`). **Its Exp 7 section is not
committed anywhere in the repository**, and neither is the project knowledge
base as searched on 2026-09-28. Other documents refer to parts of it that
cannot be read here:

* F4 and F6 (`EXPERIMENT6_D39_AMENDMENT.md` §4, protocol §16);
* the "Class A matrix" and perturbation A8, the retention curve
  (`docs/RELEASE_AND_REPORTING_GUIDELINES.md` §3 and checklist);
* "the five Exp 7 dimensions" and "preregistered band wording"
  (release guidelines, report rules 3 and 5, and outline item 6).

**Action:** commit Ian's 23 September Exp 7 text verbatim, for example as
`docs/EXPERIMENT7_PROTOCOL_AS_ISSUED.md`, before this amendment is finalized. An
amendment to text that is not in the record cannot be audited. The F-numbers
below follow the D39 amendment. F1–F3 and F5 are carried unchanged and cannot
be restated here.

## 1. Amended findings to test

### New F4 — replaces "EXP4N incumbent beats current geometry" (false)
> **Greenfield N4 does not beat N3 or N0 under the matched modeled contract.
> Test the sign/magnitude robustness of that negative/null result across the
> Exp 7 sensitivity dimensions.**

Baseline evidence, frozen:

* Exp 4A: Δ43 = obj(N4) − obj(N3) = +283,973.37 (+9.66%), firewall-admitted;
  +9.51% using the best known feasible N4 plan (Exp 5 H090 under J100).
* Exp 5: N4 − N0 = +8.07% to +11.59% at all 16 matched cells, 16/16 admitted.
* Omission-corrected costing gives +7.87% (not certified). The fixed-plan λ sign
  flips at λ ≈ 1.087, and no re-optimized λ sweep has been run.

The robustness classes, as for the old gate 4-12 claims in
`EXPERIMENT4_DEMAND_ROBUSTNESS.md`, **re-signed**:

* `sign`: N4 stays worse than N3, and worse than N0, under each perturbation.
  A sign flip is a result and must be reported, not treated as a failure.
* `magnitude_stable`: the gap stays within a factor of two of baseline.
* `not_od_truncation`: this also discharges the Exp 4A "wider OD universe"
  deferral.
* `not_commute_geometry`: a stress direction, not a non-commute estimate.
* The old `ordering` claim ("the greenfield winner still beats the best
  constrained redesign") is **false at baseline**. It is retired, not tested.
* The old `beats_noise` claim ("margin exceeds the noise floor measured in the
  same run") must be restated. D32 set replicate spread to zero, D33-B is
  veto-only, and D39 shows start-basin effects of at least 1.70% on N4. Only a
  basin-controlled comparison (§2) can support a magnitude statement.

Networks for F4: N4 against N3 and N4 against N0. Each N4 cell needs the §2
safeguards, because D39 was observed on N4.

### New F6 — replaces "policy price on N0 and N4"
> **The policy price on N0 and N3 under the Experiment 6 basin-closure
> procedure.**

* Regimes carried: R1 (H = 60/30/20), R2 at s = 0.05, R4 (c = 0.05/0.01), R6
  and R3, all of which passed D35 in Exp 6. R2 at s = 0.25/0.10 is non-binding
  at the closed REF, and B1, B2 and R4 at c = 0 ended on R1_H60's plan. Those
  cells stay in the closure graph and are priced only if they separate (§4).
* Levels carried: proposed as above. **Ian to decide.**
* Baseline prices: from `EXPERIMENT6_CLOSEOUT.md` §10, closure-adjusted only.
* Classification per regime: `sign` (a policy never helps: guaranteed by
  closure and nesting, so any violation is a bug), `magnitude_stable`, and
  `rank_stable` (the ordering of regime prices across sensitivity levels).
* Exp 6 is certified on both networks, so F6 is not scope-limited.

## 2. D39 safeguards Exp 7 inherits (binding for every comparison)

1. **Explicit anchors.** The certifier accepts a feasible anchor, refuses and
   does not repair an infeasible one, and never returns a result worse than the
   anchor (the Exp 6 extension, `exp4_certify` anchor path).
2. **Treatment-independent initial starts.** Every cell's initial solve uses
   the unchanged default greedy start. Nothing is warm-started from a result
   under a different treatment unless it is admitted as an explicit anchor
   under the target's full constraints.
3. **Basin/nesting closure, or a justified sensitivity analogue.** Where cells
   nest (policy levels, resource scalings), run the Exp 6 closure. Where they
   do not (demand shapes, λ, waiting model, path model, retention curve), the
   feasible sets are identical, so plans can always be transferred. **Proposed
   analogue:** cross-seeding closure. Every level's best plan is tried as an
   anchor at every other level of the same dimension and network, to a fixed
   point, under a frozen pass ceiling. Exp 6 evidence: closure over 20 edges
   reached its fixed point in 3 of 8 passes, with 21–24 RAN certifications per
   network. Every improvement arrived in pass 1 or 2. So an **adjacent-level
   chain** (both directions) is proposed as the default. Full all-pairs
   cross-seeding is reserved for dimensions with more than 4 levels, or where
   the chain leaves a monotonicity or sign ambiguity. **Ian to decide.**
4. **Matched reference closure.** Each network's reference cell at each
   sensitivity level takes part in the closure, and policy prices are taken
   against the closed reference at the **same** level.
5. **Firewall admission.** Every reported comparison goes through
   `firewall.compare` under a contract that whitelists exactly the sensitivity
   field (and the network fields for cross-network comparisons). Anchor
   provenance is recorded in receipts.
6. **Monotonicity where nested.** Hard post-closure monotonicity for nested
   cells, as in Exp 6 §6. D33-B does not waive it.
7. **Separate reporting of the search-basin correction and the sensitivity
   effect.** For every comparison, report (a) greedy-only against greedy-only,
   (b) closure-adjusted against closure-adjusted, and (c) the basin-correction
   component (a − b). A robustness label (`sign`, `magnitude_stable`, …) may be
   assigned only from (b). Treatment-specific local basins may not be compared
   as though the difference were model sensitivity.

## 3. Other stale assumptions found in the repository

| # | where | stale assumption | proposed change |
|---|---|---|---|
| 1 | `EXPERIMENT4_DEMAND_ROBUSTNESS.md` / `src/cota_opt/exp4_claims.py` | `ordering` claim: greenfield beats the best constrained redesign | false at baseline; retire it and re-sign as in new F4 |
| 2 | same | `beats_noise` against an in-run noise floor | D32/D33-B/D39: replace with the basin-controlled magnitude statement |
| 3 | `docs/RELEASE_AND_REPORTING_GUIDELINES.md` §Freeze | reproduction "within the `0.0018970%` noise band elsewhere" | D33-B is a local solver gap, not a cross-platform float tolerance. Measure the cross-environment drift, or state bit-exact-only |
| 4 | release guidelines report rule 3 | "An effect smaller than its Exp 7 magnitude range is within model uncertainty" | keep, but the magnitude range must come from closure-adjusted comparisons (§2.7), not greedy-only ones |
| 5 | `EXPERIMENTS_5_7_PROTOCOL_INTAKE.md` compute table | Exp 6 ≈ 54 cells / 15 h; "N0 throughput unmeasured" | Exp 6 is 28 initial cells plus closure transfers. N0 is measured (N0 J100 1,216 s; N3 646 s), so re-estimate Exp 7 from Exp 6 actuals: a median of about 600–630 s per certification, and about 72 certifications (about 6.5 h wall on 2 cores) per full N0+N3 level (§4) |
| 6 | Exp 4A gate table | 4-12 demand robustness and the wider OD universe DEFERRED_TO_EXP7 | Exp 7 must discharge both explicitly (F4 `not_od_truncation`) or re-defer with a reason |
| 7 | Exp 4A caveat | cross-route common-lines omission 12.47% of GC on N4, `potentially_frontier_changing` | add a waiting-model dimension, or state explicitly that F4 is conditional on same-route waiting |
| 8 | Exp 4A caveat | path model fits N4 much worse (8.7–34.8% improvable flow, vs 1.0–3.7%) | F4 needs a path-set/omission-correction dimension; otherwise F4 is conditional on the path model |
| 9 | Exp 4A λ | fixed-plan λ flip at 1.087; no re-optimized sweep | a re-optimized λ dimension with §2 closure; the certified frontier begins at λ = 2, so report λ < 2 as uncertified |
| 10 | Exp 1 wording | "no additional buses" | any fleet-related Exp 7 output uses FEASIBLE/INFEASIBLE/UNDECIDABLE only. The blocking materializer defect (17.8–47.0% hours mismatch, Exp 5 §6) blocks every fleet verdict until fixed |
| 11 | Exp 5 closeout | "EXP4N ranking … cannot be read as robust" | any Exp 7 use of the EXP4N ordering beyond N4 needs basin control; the ordering among closely spaced candidates is not an input |
| 12 | `EXPERIMENT6_PROTOCOL.md` §10 | "COTA-compliant" combined regime | cannot be formed (no anchors). F6 must not reintroduce it under Exp 7 unless COTA's Title VI standards are obtained, which would be a new catalog and contract version |

## 4. What Exp 6 found, and the decisions it forces (filled 2026-09-29)

The source is `EXPERIMENT6_CLOSEOUT.md` (prep copy) and
`outputs/exp6/EXP6_ANALYSIS.json`, status `EXP6_POLICY_FRONTIER_CERTIFIED`.

* **F6 scope.** The status is certified, so F6 carries every regime, on both
  networks. The baseline prices are the closed costs:
  * N0: 0 to +0.912%;
  * N3: 0 to +0.634%;
  * N3 R1_H20 is infeasible under the envelope.

  **Proposed trims:**
  * **R2 at s = 0.25 and 0.10**: closed cost is exactly 0 on both networks,
    because the best-known REF plan satisfies them. They may be dropped from the
    F6 price matrix. They must still be re-checked for non-binding at each
    level, which is cheap: test the closed REF plan against the constraint.
  * **R3, R4 c = 0, B1, B2**: each ended on R1_H60's plan. Keep **one**
    representative (R1_H60) for pricing. Keep R3 **in the closure graph**,
    because its greedy basin was the worst contaminated.
* **Basin correction against price.** Contamination (greedy-only − closed) was
  −0.162 to +0.124 pp, the same order as the prices (0.21–0.91%). Two
  greedy-only prices were negative. **Decision:**
  * every Exp 7 sensitivity level needs closure over the Exp 6 graph (or the
    §2.3 cross-seeding analogue);
  * the reference must take part at each level;
  * a single-start Exp 7 is not admissible for F6.
* **The flat objective (new, and it changes F4 and every secondary metric).**
  Closure moved both REF cells to plans 0.127% (N0) and 0.161% (N3) better
  that serve about 4,600 more trips, with about 45% higher GC.
  * Exp 7 may assign robustness labels only to **objective** comparisons.
  * Served-trips, GC, OFF-count and per-route statements need their own
    basin-controlled design, or they are reported as basin-dependent.
  * Old claims to revisit under this caveat: Exp 4A's "N4 serves 31.5% fewer
    trips" and Exp 5's served column.
* **N3 REF against Exp 4A (protocol §7).** The N3 REF *initial* equals Exp 4A's
  N3 bit-exactly. The *closed* N3 REF is 0.161% better. N0 REF against Exp 5
  J100 is the same case at 0.127%. For F4, use the closed REFs as N3 and N0.
  N4 has **no** closure-equivalent here. Its best known plan is the D39-preflight
  anchored result, 3,207,566.42, which is a calibration and not an F4 input.
  **Decision:** F4 needs N4 closed by the same procedure, for example
  cross-seeding N4 across Exp 5's resource cells, before any Exp 7 F4
  magnitude is labelled. Arithmetic on the best-known plans gives N4 − N3 about
  +9.28% and N4 − N0 about +9.03% (not firewall-admitted). That is roughly 57× (9.28 / 0.161)
  the basin corrections seen on N0/N3, so the **sign** of F4 is very unlikely
  to flip on basin grounds alone.
* **N3 against N0.** The closed gap is 0.153–0.229% in all 13 comparable cells
  (firewall-admitted). That is the same order as the basin corrections, so **N3
  vs N0 is an Exp 7 finding only with closure at every level**. Propose adding
  it as F-new: "N3 beats N0 at matched policy". The labels are `sign` and
  `magnitude_stable`.
* **Emptiness.** N3 R1_H20 is empty by 0.0166 proxy units in one period
  (early). Under any perturbation that moves the envelope or the base plan,
  emptiness must be re-proved (`exp6_infeasible_cell.py`) or refuted, never
  inherited. It is a candidate `sign`-type finding in its own right: "R1 at
  H = 20 is infeasible on N3 at the modeled envelope".
* **Throughput.** Anchored certifications took a median 625–629 s. Initial
  solves took 597–612 s, and sentinels 615 s (`outputs/exp6/run/*.events.log`).
  * Closure cost 45 RAN certifications for 27 cells, in 3 passes.
  * Exp 6 production took 7 h 15 m wall on 2 cores, about 13.2 h of summed
    certify time.
  * Per Exp 7 sensitivity level with the full N0+N3 grid, expect about
    27 + 45 ≈ 72 certifications, about 12.5 h of certify time and about 6.5 h
    wall on 2 cores. That is before any trims.
  * With the trims above (R2_S25/S10 and three of the five R1_H60-equivalent
    cells dropped from pricing but kept in the graph), the saving is small.
    The closure graph dominates.
* **Frozen already (Exp 6 Amendment 1):** N3 R1_H20 is
  `INFEASIBLE_UNDER_ENVELOPE`, with the early peak proxy of the minimum-service
  plan at 85.2987 against a cap of 85.2821.
