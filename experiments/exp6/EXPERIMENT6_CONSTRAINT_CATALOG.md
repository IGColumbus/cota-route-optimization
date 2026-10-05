# Experiment 6 — policy constraint catalog

*Researched 2026-09-28 before any Experiment 6 scoring. It is frozen by digest
in `outputs/exp6/EXP6_CONSTRAINT_CATALOG.json` and referenced from
`outputs/exp6/EXP6_CONTRACT.json`. Implementation is in
`src/cota_opt/policy.py`. Every constraint is enforced by the production
feasibility predicate (`frequency._feasible`); the D35 reach tests are in
`outputs/exp6/d35/`.*

## Bottom line first

**No regime below has a documented COTA numeric anchor.** Searches of cota.com
turned up no published service standards and no Title VI program document. The
pages checked were the Title VI page, Codes & Policies, Service Changes and the
Services page. The things not found are:

* headway, span or service-availability standards;
* a major-service-change threshold;
* disparate-impact or disproportionate-burden thresholds;
* a frequent-network definition.

COTA must hold such standards: FTA C 4702.1B, Ch. IV, requires them of
fixed-route providers, and the major-service-change / disparate-impact /
disproportionate-burden policies of providers with 50+ peak fixed-route vehicles
in a 200,000+ UZA. **FTA prescribes no values.** The agency sets them, so the
federal circular supplies no number to anchor a sweep. The values are therefore
`UNKNOWN` to this study. They are not invented.

Consequences, stated before any compute:

* Every implemented regime is a **study safeguard**. None may be reported as
  COTA policy or as Title VI compliance.
* The protocol's combined **"COTA-compliant" regime cannot be formed**, because
  no constraint has a defensible COTA or legal anchor. It is **not run**, and it
  is not replaced by a proxy under that name.
* The two preregistered interaction bundles below are labelled **study-safeguard
  bundles**.

If COTA's adopted Title VI service standards are obtained (e.g. from its
triennial Title VI program submission to FTA), R1–R4 can be re-anchored
without code changes. Only `PolicySpec` values would change, which would be a
new contract version.

## Sources

| id | source | version / date | what it establishes |
|---|---|---|---|
| S1 | FTA Circular C 4702.1B, *Title VI Requirements and Guidelines for FTA Recipients*, Ch. IV | 1 Oct 2012 (current) | Fixed-route providers must set quantitative system-wide standards for vehicle load, vehicle headway, on-time performance and service availability, plus policies. Larger providers must also adopt major-service-change, disparate-impact and disproportionate-burden policies. **The provider sets the thresholds**; FTA gives illustrative examples only (e.g. headways "might be" 15 min peak / 30 min off-peak in dense areas). |
| S2 | 49 CFR 37.131(a)(1), ADA complementary paratransit service area | eCFR current as of 22 Sep 2026 | "The entity shall provide complementary paratransit service to origins and destinations within corridors with a width of three-fourths of a mile on each side of each fixed route." |
| S3 | 49 CFR 37.131(e) | same | "The complementary paratransit service shall be available throughout the same hours and days as the entity's fixed route service." |
| S4 | cota.com: Title VI page, Codes & Policies, Service Changes, Services | retrieved 28 Sep 2026 | No numeric service standard, major-service-change definition, or frequent-network definition published. Service changes happen three times a year (Jan/May/Sep) with public meetings. |
| S5 | `config/constraints.yaml`: `policy_max_headway_min: 60`, ladder, `policy_min_headway_min: 5` | repo | The study's own pre-existing ladder policy, a **study safeguard** since Exp 1. It already caps every ladder at max(60 min, baseline headway). |

Both ADA provisions (S2, S3) bind **paratransit given the fixed route**. They do
**not** require any fixed-route service to be preserved. Removing a fixed route
lawfully shrinks the paratransit obligation. So a fixed-route preservation
constraint built on the ¾-mile width is a study safeguard that borrows a legal
distance. It is not a legal requirement.

## Regimes

"Baseline" means each network's own baseline plan: the scheduled GTFS
headways, on N3 with the one added stop. A **baseline-served** route-period
has a finite baseline headway. A **stop-period** is a (stop, period) pair that
a baseline-served route-period serves.

| regime | model parameter (`PolicySpec`) | exact mathematics | COTA anchor | sweep | classification | data sufficient? | status |
|---|---|---|---|---|---|---|---|
| **R1** max-headway floor | `max_headway = H` | every baseline-served route-period stays ON with headway ≤ max(H, its baseline headway) | none found (S4). S1 requires a COTA headway standard; value UNKNOWN | H = 60, 30, 20 min | study safeguard | yes | IMPLEMENTED |
| **R2** OFF share cap | `max_off_share = s` | #OFF among baseline-served route-periods ≤ ⌊s·\|B\|⌋ | none | s = 0.25, 0.10, 0.05. s = 0 is **identical** to R1 H=60, because the ladder already caps at max(60, baseline) (S5). It is not run twice. | study safeguard | yes | IMPLEMENTED |
| **R3** span preservation | `span = True` | each route's first and last baseline-served periods stay ON. This is period granularity: the model has six periods and no within-period span | none | on | study safeguard | yes, at period granularity only | IMPLEMENTED |
| **R4** coverage preservation | `max_lost_share = c` | #baseline stop-periods left with no ON serving route-period ≤ ⌊c·\|S\|⌋ | none | c = 0.05, 0.01, 0.00 | study safeguard | yes | IMPLEMENTED |
| **R5** localized accessibility-loss cap | — | would cap per-block-group loss of served demand or accessibility against baseline | none | — | study safeguard (a Title VI disparate-impact version would need S1's COTA thresholds plus minority/low-income block-group data) | **Title VI form: no.** Neither the thresholds (S4) nor ACS minority/low-income data are in the data registry. The generic form has the data but needs per-zone evaluator output inside the feasibility predicate, which is not built | **UNIMPLEMENTABLE_WITH_CURRENT_DATA** (Title VI form); generic form **EXCLUDED — not implemented before freeze** |
| **R6** ADA-corridor area preservation | `area_radius_m = 1207.008` (¾ statute mile) | every baseline stop-period stays within 1,207 m (straight line, EPSG:32617) of a stop served in that period | the ¾-mile width is S2's legal distance. Its use as a **fixed-route preservation** rule is the study's. Stop points approximate route corridors | one level: ¾ mile | study safeguard borrowing a legal distance | stops yes; route alignments are approximated by stops, stated here and in every report | IMPLEMENTED |
| **R7** protected / frequent corridors | — | — | **no authoritative COTA frequent-network definition found** (S4); secondary sources (press, Wikipedia) are not authoritative | — | — | no | **EXCLUDED — no authoritative definition** |

## Nesting (from the frozen objects, not names)

`PolicySpec.at_least_as_tight_as` decides implication parameter by parameter:

* R1: smaller H is tighter. Any R1 implies R2 at every s, R3, R4 at every c, and
  R6, because every baseline-served route-period stays ON.
* R2: smaller s is tighter. s = 0 would imply R3, R4 and R6 (not run
  separately; see R2 row).
* R4: smaller c is tighter. c = 0 implies R6.
* R6 and R3 are single-level.
* The unconstrained reference is implied by everything.

The contract freezes the resulting Hasse graph together with an equality check.
Every edge's implication is also verified numerically on each network by the
compiled constraint objects.

## Grid (per network; the same on N0 and N3)

| cell | spec |
|---|---|
| REF | no policy |
| R1_H60, R1_H30, R1_H20 | max_headway 60 / 30 / 20 |
| R2_S25, R2_S10, R2_S05 | max_off_share 0.25 / 0.10 / 0.05 |
| R3_SPAN | span |
| R4_C05, R4_C01, R4_C00 | max_lost_share 0.05 / 0.01 / 0.00 |
| R6_ADA | area_radius_m 1207.008 |
| B1 (study-safeguard bundle) | R2 s = 0.10 + R3 + R6 |
| B2 (study-safeguard bundle) | R4 c = 0.01 + R3 |

That is 14 cells per network and **28 in total**. The two bundles are
preregistered here, before any single-regime result exists; the cap is six.
The COTA-compliant combination is not run, for lack of any anchor.
