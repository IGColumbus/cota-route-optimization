# Glossary

*A draft for outsiders, prepared 2026-09-28. Every definition points at the
file that governs it. Where a term has been used loosely in older documents,
the entry says so.*

## Networks

| term | meaning | source |
|---|---|---|
| **N0** | COTA's existing local route geometry as built from the GTFS feed (`H.baseline.network`), content digest `f0f24936ab06b4ec`. In Exp 5/6 the peak-only express routes are locked. | `experiments/exp6/EXPERIMENT6_D39_AMENDMENT.md` §2 |
| **N3** | N0 plus the single Experiment 3 edit `add_stop-010#22c4c35ac5b2`, the certified Exp 3 leader. Content digest `430aca035c70715b`. The "constrained redesign". | `experiments/exp3/EXPERIMENT3_CLOSURE.md`, `experiments/exp4/EXPERIMENT4_ORIGINAL_QUESTION_ADDENDUM.md` |
| **N4** | The EXP4N normalized leader `…35e351133d6f`, a 65-line greenfield network from the Experiment 4 proposal generator. It is **not** an Exp 6 production network and is used only for the D39 preflight. | `experiments/exp4/EXPERIMENT4_NORMALIZED_CLOSEOUT.md` |

## Experiments and runs

| term | meaning |
|---|---|
| **Exp 1** | Frequency redistribution on fixed geometry. Closed and certified for λ ≥ 2. |
| **Exp 2 / 2B** | Route-geometry splices, individually (no supportable claim) and in all 240 feasible combinations (discovery-stage sweep). The leader is not distinguishable from zero at certification effort: +0.090% unserved under matched starts, worse than no edit (`outputs/exp2b_certification.json → _confirmation`; the earlier +0.0065% is superseded). |
| **Exp 3** | Route mutation over 84 census states. 29 certified, leader N3 at −0.18657% on the λ = 2 objective. Frozen at commit `8c2841c4` (tag `exp3-final-v1`, not yet public). |
| **Exp 4 (legacy)** | 200 promoted greenfield candidates, certified exactly. Its **ordering is superseded**, because each candidate was optimized under a peak cap drawn from its own baseline. Its objective values are not withdrawn. |
| **EXP4N** | The normalized rerun of Exp 4: the same 200 candidates under **one common resource envelope**. Status `EXP4_FULL_NORMALIZED_CERTIFIED`. |
| **EXP4A** | The Exp 4 original-question addendum: N3 vs N4 under the matched EXP4N contract (`EXP4A_MATCHED`, `0f62aeabfa341a98`). N4 is worse by +9.66%. |
| **Exp 5** | Modeled operating-resource frontier on N0 and N4, 32 cells. Status `EXP5_MONOTONICITY_FAILURE` (on N4 only). |
| **Exp 6** | Modeled price of policy constraints (study safeguards) on N0 and N3 under the basin-closure procedure. In progress on 2026-09-28. |
| **Exp 7** | Robustness/sensitivity. Not yet amended or run. |
| **J / H / P cells** | Exp 5 resource cells: J scales hours and peak proxy jointly, H scales hours only, P scales the peak proxy only. The number is the percentage of the EXP4N envelope (J100 = the EXP4N envelope). |
| **REF** | An Exp 6 cell with no policy constraint, the matched reference for policy cost on its network. |

## Model and objective

| term | meaning |
|---|---|
| **Model A / Model B** | Two ways to price waiting. Model A uses the chosen pattern's headway. Model B (`same_route`) uses the combined frequency of every same-route pattern serving the movement. **Model B is the only authoritative evaluator.** |
| **λ (lambda)** | Weight on unserved demand in the scalarized objective. The certified frontier begins at λ = 2; headline comparisons use λ = 2. Exp 1 also certified λ = 4, 8, 16, and Exp 7 ran converged Stage 2 cells at λ = 1 and 4 as sensitivity levels (λ = 1 lies below the certified frontier). |
| **objective** | The λ-scalarized path-level generalized cost including unserved demand: GC of served trips + λ·60·unserved trips. Lower is better. Unit: equivalent in-vehicle minutes. Not a welfare measure: it can reward worse service where a served trip's GC exceeds λ·60 (`docs/report/TECHNICAL_REPORT.md` §3.1). |
| **unserved demand** | Modeled trips with no enumerated path and no intrazonal walk-only option (*structural*), or dropped by the retention curve (*discouraged*). A model quantity, not observed riders; the current plan leaves about 33% of the NTD-anchored total unserved. |
| **`B1_COMMONLINES`** | The Exp 7 Class B level. Despite its name it ran Model A waiting, not cross-route common lines (errata E16). Unrelated to the Exp 6 safeguard bundle B1. |
| **route-period** | One route in one of six service periods (early, am_peak, midday, pm_peak, evening, owl). The decision variable is its headway. |
| **OFF** | A route-period with infinite headway: no trips, no hours, no peak proxy. |
| **LODES demand** | LEHD commute OD flows, top 20,000 pairs, scaled to an NTD-anchored total. Commute-only: this is the largest unquantified limitation. |

## Resources and fleet

| term | meaning |
|---|---|
| **resource envelope** | The caps a plan must satisfy: weekday revenue vehicle-hours (2,517.183) and the six-period peak-concurrency proxy caps. The **EXP4N common envelope** is resolved once from the frozen artifact and shared by every cell. |
| **rounded envelope digest** | `3fd5241db44ca9da`. A hash of `round(value, 9)`. It can collide for envelopes differing below the 9th decimal. |
| **exact envelope fingerprint** | `0b46d1abc9a80c80`. A lossless IEEE-754 fingerprint of the same inputs (`scripts/envelope_fingerprint.py`). Used from Exp 5 onward. |
| **peak-concurrency proxy** | `max over periods of Σ cycle_time / headway`. It is what the solver constrains (`frequency._feasible`). **It is not a bus count.** On the baseline the solver's version (`FitnessVector.peak_vehicles`) reads 176.49. The `routewise_peak` variant in `blocks.py` reads 150.73. Never convert either into buses. |
| **block-derived peak vehicles** | 197 at 17:13 from COTA's own published vehicle blocks (284 blocks). A physical count **for the existing schedule only**. NTD VOMS is 198. |
| **interlining factor** | 197 / 150.73 = 1.307. Evidence of proxy error, **not an exchange rate**. The old Exp 1 "197.0 vs 197.0" was this factor times the proxy; see the Exp 1 wording correction. |
| **fleet UNDECIDABLE** | The three-valued physical-fleet verdict (`exp4_blocking.production_feasible`) is FEASIBLE / INFEASIBLE / UNDECIDABLE. FEASIBLE is unreachable while deadhead provenance is OPEN, and UNDECIDABLE is returned when the instrument cannot decide (e.g. its materialized timetable does not reproduce the plan's own hours). Every Exp 4 candidate and every Exp 5 cell is UNDECIDABLE. |
| **deadhead provenance OPEN** | COTA's deadhead times are not public, so no reblocked plan can be certified feasible. |

## Search and certification

| term | meaning |
|---|---|
| **Gen1 / Gen2** | Methodology generations. Gen1 is the exchange search of Exps 1–3, frozen at commit `4b62c728` (tag `gen1-frozen-v1`, not yet public). Gen2 is the Exp 4+ exact block certifier. |
| **(8, 3) block certifier** | `exp4_certify.certify`: from a Gen1 greedy start, repeatedly solves every block of 8 route-periods exactly within a 3-rung window (the current rung and one either side), until a full round improves nothing (max 120 rounds). Guarantee: *no block of 8 route-periods moved within that 3-rung window improves the objective*. That is a local, not global, guarantee. |
| **certified** | Used in three senses; the report (`docs/report/TECHNICAL_REPORT.md` §4) keeps them apart: **path-set adequate** (Exp 1, gate 4), **seed-distinguishable** (\|mean Δ\| / SD > 3 at stated effort, or effect against the seed spread or pre-specified floor), and **block-local certified** (a converged (8, 3)-block-local optimum, Exp 4–7). **Not** "real-world significant" and **not** "globally optimal". |
| **D17** | The Exp 1 optimum is flat: seeds disagree on ~19% of route-periods at equal score. There are no per-route recommendations. |
| **D27** | The optimizer was chosen by the treatment: a snapped incumbent was rejected on some networks and the solver silently fell back to greedy. This led to the firewall's execution-receipt rule. |
| **D33-B** | The maximum local heuristic gap, 0.0018970% (375 cells, Stage B effort). **Veto-only**: below it a difference is noise; above it nothing is established. It is **not** a bound on start-basin effects (D39 exceeds it ~900×). |
| **D35** | "A constraint that was a label": a hashed selection field that reached nothing that scores. Hence the **D35 reach test**: every constraint must flip admissibility when moved just across its measured value on the production feasibility path. |
| **D36 / D37 / D38** | Exp 4 discovery-ranking findings. D38 reframes D36: discovery scores are near-flat, i.e. a constant plus noise, not an inverted ranker. |
| **D39** | Start-basin dependence (Exp 5). Greedy starts built under each cell's own caps land the block search in different local optima. On N4, 12 of 99 nested pairs regress, by up to **1.7034%**. The EXP4N N4 plan is not the best known N4 plan under its own envelope (H090's plan is 0.132% better). |
| **start basin** | The local optimum a converged local search reaches from a given start. |
| **explicit anchor** | A feasible plan handed to the certifier as its start (Exp 6 extension). It is refused, not repaired, if infeasible under the target cell. The result may not be worse than the anchor. |
| **nesting / Hasse graph** | The partial order of Exp 6 cells by feasible-set containment, derived from `PolicySpec.at_least_as_tight_as` and never from names. The Hasse graph is its transitive reduction (adjacent pairs). |
| **basin (nesting) closure** | Exp 6 stage 2: transfer each cell's best plan to its graph neighbours in both directions as explicit anchors, in deterministic passes, until a full pass improves nothing. The pass ceiling is frozen in advance. |
| **initial vs closure-adjusted** | The Exp 6 per-cell result from the independent greedy start, and the result after closure. **Policy cost is reported closure-adjusted.** The greedy-only apparent cost is shown next to it, never alone. |
| **policy cost** | Closed policy-cell objective − closed REF objective, same network. A MODELED quantity, not dollars. |
| **study safeguard** | A constraint the study chose, with no documented COTA or legal anchor. Every Exp 6 regime is one. |
| **UNIMPLEMENTABLE_WITH_CURRENT_DATA** | A regime that cannot be enforced with the data in the registry (R5's Title VI form). |
| **order / restart sentinels** | Re-runs of selected cells in reversed order, in fresh processes, that must reproduce bit-exactly. |

## Firewall and provenance

| term | meaning |
|---|---|
| **firewall** | `cota_opt.firewall`: `compare(control, treatment, contract)` is the only operation allowed to produce a reportable effect. It refuses any **undeclared** difference in how two arms were actually executed, read from **execution receipts**. It works by whitelist, not blacklist. Limit (D35): it proves only that arms differed where permitted, not that a permitted difference was applied. |
| **experiment contract** | An `ExperimentContract`: evaluator, objective, envelope label, path-set policy, solver policy and the whitelist of allowed treatment differences. |
| **contract digest** | A 16-hex content hash of a contract (e.g. `EXP4A_MATCHED` = `0f62aeabfa341a98`, `EXP5_FRONTIER` = `395ee3c960f51935`). A receipt built under one digest is refused under another. Frozen contract files also carry a file sha256. |
| **code_version / src digest** | The content hash of `src/cota_opt` (e.g. `src-51dd455d9e1a` / `add5d0002d29aa49`). Scripts sit outside it by design. |
| **canonical registry** | `outputs/CANONICAL_RESULTS*.json` (v5 current): which artifacts are current, which are superseded and why. Each version is additive and copies its predecessor verbatim. |
| **superseded** | Kept, readable and never deleted, but not to be used for quantitative interpretation. "A superseded artifact looks entirely legitimate from the inside." |
