# COTA Route Optimization — Release and Reporting Guidelines

Updated 2026-09-23 · Ian

> Stored verbatim in the repo so it survives context compaction. This is the
> governing release spec. Amendments G1-a/b/c below incorporate the three
> corrections raised from `docs/research-record/RELEASE_GUIDELINES_INTAKE.md` (`b5c23226`).

> **How to read this document (2026-10-05).** The text below is the original
> specification, kept so its intent survives. Where the release as built
> differs, a note marked **Implemented 2026-10-05** or **Final implementation
> differs from the original specification** follows the paragraph. Those
> deviations are deliberate, mostly to keep frozen provenance paths and the
> frozen research code intact. Do not "fix" them back to the original design
> without reading the note. Current state of every item: the checklist at the
> end and `docs/RELEASE_PROVENANCE.md`.

## Purpose and definition of done

The release turns the research repository into a harness someone else can pick up, feed their own data, and scale. The findings travel with it, but the harness is the product.

**Audiences:**

- **COTA planners** want the directional findings, what the model can and cannot say, and how to rerun it on their own ridership, AVL, and fare data.
- **Researchers**, such as an OSU planning or operations research group, want the methods, the methodological findings, the retractions, and a clean library to extend.
- **The public**, via Full City Columbus, wants the plain-language brief only.

**Done means all five of these are true:**

1. A cold reader can go from `git clone` to a reproduced Exp 1 headline using only public data, with every setup step visible.
2. A reader with better data can find exactly where it plugs in, and what it would calibrate or validate, in under 15 minutes.
3. Every published number traces to a canonical artifact, a contract digest, and a commit.
4. Anyone reading the report cannot mistake a solver-certified difference for a real-world one.
5. A cold researcher handed any superseded or retracted result can trace it to its original artifact, contract, commit, the reason it was superseded, and its canonical replacement, without help.

## Release gate

Cleanup starts only after the research record is frozen. Every contract digest and provenance record points at specific commits and file paths, so restructuring before the freeze would break the audit trail the project depends on.

**Preconditions:**

- Exp 7 has produced its certified close-out table.
- Every experiment status is resolved, with no halted or in-flight runs.
- Every commit that exists only in the development container has reached GitHub. The sandbox cannot push, so this needs Ian at a keyboard.
- All work branches, including `exp3-clean` and anything newer, are merged into `master`.

> **Implemented 2026-10-05:** all preconditions met. `research-final` (tag object
> `78a4355d`) points at `cd03af9c` and is public, with the historical freeze tags.
> The environment pin is `docs/research-record/ENVIRONMENT_AT_FREEZE.txt` plus
> `requirements-lock.txt`. **Final implementation differs from the original
> specification:** no container image was recorded at the freeze, because the
> sandbox could not export one. A `Dockerfile` was added afterwards; its build
> status is in `docs/RELEASE_PROVENANCE.md`.

**Freeze the research record.** Tag the merged state `research-final` before any cleanup commit. Every contract, digest, and canonical artifact verifies against that tag. The cleaned release reproduces the results; the tag reproduces the exact code that produced them.

**Do not rewrite history.** The bundles and lock debris already in `master` history cost a few MB. Removing them with `git filter-repo` would change every commit hash, and the provenance records cite those hashes, `431b105a` among them. Delete the files in a normal commit and accept the size.

**Pin the environment at the freeze.** Bit-exact reproduction depends on library versions and floating-point behaviour, not just code. Record a lockfile and a container image with the `research-final` tag. Reproduction claims are stated as "bit-exact in the pinned environment; within the `0.0018970%` noise band elsewhere."

## Repository restructure

The release separates the reusable library from the experiments that used it, and moves process history out of the top level. Today the top level has more than 40 markdown files, and `src/cota_opt` mixes core modules with `exp1.py` through `exp5_*.py`.

**Target layout:**

```
src/cota_opt/core/       reusable library: gtfs, raptor, pathset, frequency,
                         cost, retention, odmatrix, blocking, ntd, registry,
                         realtime, contract, firewall, cache
experiments/expN/        per experiment: scripts, contract, closeout, config
config/                  sources.yaml, assumptions.yaml, cost_weights.yaml
docs/                    the documents a user reads (list below)
docs/research-record/    every contract, preregistration, audit, and design doc
docs/process/            keeper beats, push notes, operations, agent rules
outputs/canonical/       artifacts cited by the report
outputs/superseded/      retained, indexed, never deleted
data/                    untracked; rebuilt from sources.yaml
```

**Rules for the move:**

- Moving a module changes its import path, and moving a document breaks references to it. Record every move in `docs/research-record/MOVES.md` as old path → new path, so a reader holding a `research-final` reference can find the file.
- Nothing is deleted from the research record. It moves to `docs/research-record/` or `outputs/superseded/`, with `SUPERSEDED.md` and `CANONICAL_RESULTS.json` kept current.
- Remove only true debris: the `.bundle` files, `_to_delete/`, and lock and tmp-pack files. Add those patterns to `.gitignore`.
- `AGENTS.md` becomes `docs/ENGINEERING_RULES.md`. Its rules are how the harness stays honest, so users extending it need them.
- Collapse each experiment's many documents into one contract and one closeout. Superseded designs and abandoned phases move to the research record.

> **Final implementation differs from the original specification (2026-10-05,
> `6a278bf1`; 231 moves in `docs/research-record/MOVES.md`).** Deliberate
> deviations, each to keep frozen provenance resolvable:
>
> * `src/cota_opt` was **not** split into `core/` and experiment modules. The
>   frozen contracts pin a content digest of `src/cota_opt/**/*.py`, so moving a
>   module would break every certification check. Release-only code lives in
>   `src/cota_release/`.
> * Canonical artifacts stay at their registered paths under `outputs/`, not
>   `outputs/canonical/`. The frozen registry (`CANONICAL_RESULTS_v5.json`), the
>   freeze manifests and the contracts name them by path. `outputs/README.md`
>   is the index; `outputs/canonical/` is an older folder holding three records.
> * Superseded files moved to `outputs/superseded/` where nothing frozen hashes
>   them in place. Four sets stayed put (`outputs/SUPERSEDED.md`).
> * `scripts/` stays at the root, because experiment records cite script paths.
> * Experiment documents were **not merged** into one contract and one
>   closeout. Each `experiments/expN/` has a README naming its one authoritative
>   contract or protocol and its one closeout. Registered contracts, closeouts
>   and errata remain separate immutable documents, and supporting or
>   historical material moved to `docs/research-record/`.

## Required additions

Six additions turn the repository into something another team can use. Each has an acceptance test, and the release is not tagged until all six pass.

### 1. License and citation

The repository has no license. Without an explicit license, downstream reuse rights are restricted by default and unclear in practice, which is enough to stop an agency or university from touching it. Add Apache-2.0 for code (it includes a patent grant) and CC-BY-4.0 for docs, the report, and figures. Add `CITATION.cff`, and archive the release on Zenodo through its GitHub integration so researchers can cite a DOI. Record each data source's terms of use in `sources.yaml`. This is the standard pattern, not legal advice.

*Acceptance:* `LICENSE` and `CITATION.cff` present, the README states the license, and every source in `sources.yaml` has a terms field.

> **Implemented 2026-10-05:** the repository now has licences. Apache-2.0
> (`LICENSE`) covers code; CC BY 4.0 (`LICENSES/CC-BY-4.0.txt`) covers
> documentation, the report and figures. `CITATION.cff` is present, and every
> registered source in `config/sources.yaml` has a licence, version, citation,
> retrieval note and sha256. Still open: the Zenodo archive and DOI, which come
> with `v1.0`.

### 2. Data interfaces

`docs/DATA_INTERFACES.md` lists every place outside data enters, and what a user might bring instead.

| Input | Entry point | Current source | What a user might bring | Status |
| --- | --- | --- | --- | --- |
| Schedule | `registry` + `gtfs` validation | COTA GTFS static | Newer COTA feeds | Wired |
| Demand | `odmatrix` constructors, one output type | LODES OD, gravity fallback | APC-derived OD, fare-card chains, MORPC regional model, on-board survey | Wired; a new source is a new constructor |
| Observed runtimes | `realtime` collector → SQLite | COTA GTFS-RT | AVL archives | Collected, **not wired into cost**; the reliability term is a placeholder |
| Operating statistics | `ntd` parser | NTD 2024 profile | COTA internal reports | Wired |
| Resource envelope | canonical envelope + `blocks` | Published GTFS blocking | COTA blocking and runcut data | Wired |
| Deadhead | `TableDeadheadOracle` | None (same-terminal only) | COTA deadhead matrix | Interface exists, no data |

Each entry documents schema, units, validation checks, and a worked example.

**Units trap in the canonical envelope.** `CANONICAL_ENVELOPE.json` holds two different kinds of quantity under one `contract_text` written in physical-vehicle language:

- the block-derived 197 peak vehicles, a physical count for the existing schedule only; and
- the per-period peak envelope the solver enforces, which is the cycle-over-headway proxy (85.28, 162.01, 159.17, 176.49, 140.19, 35.56 by period).

Live provenance records cite the file, so it stays unchanged through `research-final`. The release adds a sidecar, `CANONICAL_ENVELOPE.units.json`, that classifies every field as physical or proxy and records its provenance. Report and figure generators take units and wording from the sidecar, never from `contract_text`.

*Acceptance:* a new demand source can be added with one constructor and one test, without editing `core`.

> **Implemented 2026-10-05, with a deviation.** `docs/DATA_INTERFACES.md`
> covers every input. It states for each whether exact, newer-version,
> same-schema or different-kind substitution is actually supported, and marks
> inputs with no adapter. The demand-constructor acceptance is met at the
> release boundary rather than inside `core`, because `src/cota_opt` is frozen:
> `src/cota_release/demand.py` (zone-to-zone CSV → `ODTable`, the study's
> market rules, path sets keyed by the table's digest), tested by
> `tests/test_release_demand.py` and exercised by `examples/demand_from_csv.py`.
> The table in this section predates that work; where they differ,
> `docs/DATA_INTERFACES.md` is current.
>
> **Implemented 2026-10-05:** the units sidecar is
> `outputs/CANONICAL_ENVELOPE.units.json`. It is additive; the frozen envelope
> artifacts are unchanged. It classifies every numeric field of
> `outputs/CANONICAL_ENVELOPE.json` and
> `outputs/exp4_normalized/COMMON_RESOURCE_ENVELOPE.json`. The figure tooling
> takes its resource-axis labels from it (`src/cota_release/units.py`), and
> `tests/test_envelope_units.py` fails if a proxy is labelled as vehicles or a
> physical count as a proxy.

### 3. Calibration register

`docs/CALIBRATION.md` lists every assumed parameter, what data would calibrate it, and how sensitive the findings were to it in Exp 7.

| Parameter | Current value | File | Status | Data that would calibrate it |
| --- | --- | --- | --- | --- |
| Full-retention cost | 60 min | `assumptions.yaml` | Assumed | Fare-card trip chains, on-board survey |
| Zero-retention cost | 210 min | `assumptions.yaml` | Assumed | Same |
| Retention floor | 0.10 | `assumptions.yaml` | Assumed | Same |
| Unserved-trip penalty | 60 min | `cost_weights.yaml` | Assumed | Mode-choice or survey data |
| Transfer penalty | 10 min | `cost_weights.yaml` | Assumed | Route-choice data, APC transfer counts |
| λ | 2 (certified ≥ 2) | experiment config | Policy choice | None; it is a value judgement |

The register covers every assumed parameter in `config/`, including walking and waiting terms. Any output produced with an assumed parameter carries the label "uncalibrated". Every current output therefore does, and saying so is correct.

The retention curve is the largest untested assumption, and it is absent from the Exp 7 Class A matrix. Amend the Exp 7 protocol to add it before Exp 7 runs, not after. *(Done: added as Class A perturbation A8.)*

> **Implemented 2026-10-05:** the register is `docs/CALIBRATION.md`. Its Exp 7
> sensitivity table is generated from the artifacts by
> `scripts/make_calibration_tables.py`, and CI checks it.
>
> **Final implementation differs from the original specification:** the
> "uncalibrated" label is **not** written into frozen research artifacts, which
> stay byte-identical. It lives in release-facing `config/model_status.yaml`.
> Every artifact written by release tooling (`cota-opt reproduce`,
> `cota-opt validate-model`) carries it, and the briefs' model-status box is
> generated from it. All existing research outputs are uncalibrated by
> definition.

### 4. Validation step

`cota-opt validate` compares the baseline assignment with observed data on four separate dimensions. Different agencies will have data for different subsets, so there is no single global "validated" flag.

| Dimension | Compares | Typical observed source |
| --- | --- | --- |
| Route volume | Modelled boardings by route and period | APC or farebox route totals |
| Stop pattern | Modelled boardings and alightings by stop | APC stop-level counts |
| Transfer behaviour | Modelled transfer rates and locations | Fare-card transfers, on-board survey |
| Trip length | Modelled trip-length distribution | Fare-card trip chains, on-board survey |

Each dimension is marked `passed`, `failed`, or `unavailable`, against pass thresholds the user sets in config before running. Every artifact carries all four statuses, and there is no roll-up into one bit. Optimization still runs whatever the statuses are, but they follow every result into the report.

*Acceptance:* with deliberately mismatched route-volume data and no stop data, validation reports route volume `failed` and stop pattern `unavailable`, and both statuses appear on the output artifact.

> **Final implementation differs from the original specification (2026-10-05):
> the command is `cota-opt validate-model`, not `cota-opt validate`.** The
> research CLI already had a `validate` command, which checks GTFS feed
> structure (`python -m cota_opt.cli validate`), and historical instructions
> use it. Overloading the name would make those instructions ambiguous.
>
> * **Configuration:** `config/validation.yaml` holds the observed files and
>   the thresholds, set before the run.
> * **Statuses:** each dimension reports `passed`, `failed` or `unavailable`,
>   and there is no global flag.
> * **Acceptance test:** `tests/test_release_validation.py`.
> * **Modeled side:** route volume is extracted from the study model
>   (`--from-study`). Stop pattern, transfer behavior and trip length have no
>   modeled extractor yet, so they stay `unavailable` until one is written or
>   modeled values are supplied (`--modeled`).
> * **Current status:** all four are `unavailable`, because no observed data
>   exists.

### 5. One-command reproduction

`cota-opt reproduce exp1` fetches public inputs by checksum and validates the feed. It then asserts the baseline identities: revenue vehicle-hours equal the published schedule, and COTA's published blocking reconstructs to 197 peak vehicles. That count applies to the existing schedule only. No modified plan has a certified vehicle count, so the Exp 1 plan is reported in the resource terminology Exp 1 actually certified. The command then runs Exp 1 at certification effort and compares the result with the canonical objective. A `--smoke` mode runs the same pipeline at reduced effort in minutes. The full run's time is measured and published in the README, not estimated.

*Acceptance:* on a fresh machine the result is bit-exact in the pinned container and within `0.0018970%` elsewhere. A quickstart of three commands or fewer is the usability goal, but correctness and visible setup win any conflict. No hidden setup steps are added to hit the command count.

> **Final implementation differs from the original specification (2026-10-05).**
>
> * **Inputs:** `cota-opt reproduce exp1` does **not** fetch inputs itself.
>   They are staged first with `cota-opt data status|register|fetch`, which
>   refuses any file whose sha256 differs from the study's. COTA's URL serves
>   its current feed, not the study's, so a fetch-everything command could not
>   be correct.
> * **Smoke mode:** `--smoke` does no optimization. It rebuilds the instance
>   and re-evaluates the three certified plans; the first run takes about 40
>   minutes on one core, for the path sets.
> * **Full mode:** re-solves the three seeds at certification effort.
> * **Recorded results and the evidence level per experiment:**
>   `docs/REPRODUCE.md`.
> * **Container:** the pinned container could not be built in the development
>   sandbox (`docs/RELEASE_PROVENANCE.md`).
> * **Cross-machine drift:** still uncharacterized.

### 6. Scaling

`docs/SCALING.md` explains how to throw compute at it. Certification cells are independent, so the work is trivially parallel. The one-cell-at-a-time pace so far is a limit of the container, not of the method.

- Provide a Slurm job-array recipe for the Ohio Supercomputer Center: one cell per array task, a shared read-only cache, one output file per cell, and resume by file existence.
- Pin BLAS and OpenMP threads to 1 per process. Threaded linear algebra can change floating-point results, and that would break bit-exact checks. Parallelize across cells instead.
- Document the cache keys for the pathset and baseline caches, so shared caches are never mixed across contracts.
- Keeper beats and hold loops are workarounds for the development container. They belong in `docs/process/`, not in the user path.

*Acceptance:* the Exp 5 matrix run as a job array reproduces the serial results cell for cell.

> **Status 2026-10-05:** `docs/SCALING.md` documents the parallel structure,
> with a Slurm/OSC job-array recipe, cache-key rules and thread pinning. The
> Exp 5 job-array acceptance run has **not** been done. It remains a `v1.0`
> requirement for the reusable harness, not for the working paper.

## Report

The written product is three documents for three audiences, built from one source of truth. Every number in all three is generated from canonical artifacts, never typed by hand.

| Document | Audience | Length | Contents |
| --- | --- | --- | --- |
| Public brief | Full City Columbus readers | 1–2 pages | The directional findings in plain language, and what the model is not |
| Planning brief | COTA planners | 4–6 pages | Findings with their Exp 7 labels, the price of each policy regime, how to rerun on COTA data |
| Technical report | Researchers | As long as needed | Full methods, results, methodological findings, limitations, appendices |

> **Implemented 2026-10-05:** all three exist.
>
> * `docs/PUBLIC_BRIEF.md` and `docs/PLANNING_BRIEF.md` take every
>   decision-relevant number from claims that `scripts/verify_report_claims.py`
>   checks against artifacts, audited by `scripts/audit_public_numbers.py`.
> * Their model-status boxes are generated from `config/model_status.yaml` by
>   `scripts/model_status_box.py`, and CI checks the boxes are current.
> * `README.md` is the front door, not a fourth report.

**Model status box — mandatory.** The public brief and the planning brief open with a visually distinct box, placed before any finding. It states the calibration status, the four validation statuses, the demand source (commute-only unless replaced), the service basis (scheduled, not observed), and that the results are not an operating plan and not COTA-endorsed. The box is generated from artifact metadata, so it cannot drift from the actual state of the model. A brief without it does not ship.

**README is the front door.** It says what the harness is, gives each headline finding in one line with its main caveat, then the quickstart, where data plugs in, the license, and how to cite. Everything else is one click away in `docs/`.

The current README's "no additional buses" claim for Exp 1 is replaced with the resource terminology Exp 1 actually certified. No modified plan has a blocking-based vehicle count.

**Technical report outline:**

1. Question and scope.
2. Data and provenance.
3. Model: network, path assignment, Model B waiting, generalized cost, retention, resource envelope and its terminology.
4. Harness: contracts, firewall, certification, convergence contract.
5. Results, Experiments 1–6.
6. Robustness: the Exp 7 close-out table.
7. Methodological findings. These include route-level scoring overstating gains (22.71% vs 7.16% for the same plan), the Model A/B correction, D27 (the optimizer selected by the treatment), matched effort versus matched convergence, D35 (a constraint that never reached scoring), and the rounded envelope digest.
8. Limitations, each with its size and direction.
9. Using this with better data.
10. Appendices: decision log, retractions, preregistration amendments, superseded-artifact index, calibration register, glossary.

### Rules for every number and claim

1. **Full identity.** Every number states its unit, network (N0 or N4), evaluator, resource terminology, and the artifact it came from.
2. **Label the ±.** Seed spread is labelled "solver seed spread". It is never presented as a confidence interval on the real-world effect.
3. **Certified is not significant.** Certification shows the solver found a difference, not that the difference is real. An effect smaller than its Exp 7 magnitude range is reported as "within model uncertainty", even when certified.
4. **No vehicle counts without a blocking certificate.** Proxy resource units are named as proxy units everywhere, including figure axes. Unit labels come from the envelope units sidecar, never from `contract_text`.
5. **Stability words come from Exp 7.** Only the preregistered band wording describes how stable a finding is.
6. **Nulls get equal billing.** Null results get the same prominence and precision as positive ones.
7. **Retractions in the body.** A short table of retractions and protocol amendments appears in the main text, not only in an appendix.
8. **No route-level recommendations.** Under Model B, independent seeds disagree on about 19% of route-periods (worst pair 19.7%, mean 19.1%), so individual headways are never presented as recommendations. Only aggregates and patterns are.
9. **Name the source of every requirement.** Legal requirement, adopted COTA policy, or study safeguard, every time.
10. **Required disclaimers.** Not an operating plan. Not COTA-endorsed. Demand is commute-only unless replaced. Service is scheduled, not observed. Calibration status and the four validation statuses are shown wherever they apply.
11. **Define every term.** Each document defines every technical term it uses, or links to the glossary.

## Figures

The report uses a fixed set of seven figures. Each is generated by a script from canonical artifacts, and none is edited by hand.

> **Final implementation differs from the original specification:** the report
> has **eight** figures. Amendment G2-a (below) added the post hoc F1
> decision-space figure. Report figures are numbered by first mention; the
> guideline IDs G1–G7 map to report figure numbers in
> `docs/report/figures/FIGURES_MANIFEST.json`.

| # | Figure | Shows | Must carry |
| --- | --- | --- | --- |
| 1 | Exp 1 frontier | Unserved demand against generalized cost across λ | Certified region from λ = 2 marked; λ ≤ 1 shaded as uncertified; seed spread |
| 2 | Route-level vs path-level scoring | The same plans scored both ways | The 22.71% vs 7.16% gap for the same plan |
| 3 | Geometry null | Splice effects at ranking effort vs certification effort | The noise floor as a band |
| 4 | Resource curve | Objective against peak envelope level | Axis reads "% of peak envelope — proxy units"; binding periods; the hours arm shown separately as service cuts |
| 5 | Policy frontiers | Policy cost against constraint level, one panel per regime | COTA anchor marked; legal / COTA policy / study safeguard stated |
| 6 | Robustness | Findings against the five Exp 7 dimensions | Preregistered band wording only |
| 7 | Change pattern map | Where service rises and falls, aggregated by corridor or area | The aggregation contract below; "Illustrative pattern, not a route recommendation" |

**Rules:**

- Every caption names its artifact ID, contract digest, network, and evaluator.
- Show uncertainty wherever it exists. No dual y-axes, and use a colourblind-safe palette.
- Maps aggregate. They never label an individual route's headway.
- Every figure ships with the CSV it was drawn from, so users can re-plot it with their own tools.

**Figure 7 aggregation contract.** The map must not reveal an individual route's headway by inspection, so the aggregation rules are part of the figure's contract and are frozen before it is drawn:

1. **Fixed units.** Map units are corridor or area polygons defined before any plan is plotted. They are not drawn around the results.
2. **At least three routes per unit.** Each unit aggregates service change across three or more routes.
3. **No dominant route.** If one route accounts for more than half of a unit's change, the unit is merged with a neighbour until no single route dominates.
4. **Bands, not minutes.** Change is shown as a direction and a coarse band, never as a headway in minutes.
5. **Seed agreement.** A unit is coloured only if every certified seed agrees on the direction of its change. Otherwise it is shown as "no stable pattern". This follows from the Model B seed disagreement of about 19% of route-periods (worst pair 19.7%, mean 19.1%).

## Release checklist

The one pre-Exp 7 item is done; everything else follows the freeze in order.

**Before Exp 7**

- [x] Retention curve added to the Exp 7 protocol as Class A perturbation A8, with preregistered levels.

**Freeze**

- [x] Exp 7 close-out table certified; no halted or in-flight runs.
- [x] (2026-10-05: `master` at `cd03af9c` on GitHub.) Get every container commit to GitHub: bundle → commit to your folder → `git fetch` → merge `cloud/exp3-clean` → push from GitHub Desktop. GitHub has `exp3-clean` only through `099d0527` (9/21); every EXP4N commit so far exists only in the container and in hand-carried bundles.
- [x] All work branches merged into `master` (`exp3-clean`, `exp45-work`, `exp6-work`, `exp7-work`, `exp7-work-b`). `exp3` is the separate pre-collapse history: it stays a branch on GitHub, and `exp3-frozen-v1` is reachable only from it.
- [x] Tag `research-final` at `cd03af9c`, **publicly**. (2026-10-05: annotated tag object `78a4355d` pushed; `git ls-remote origin` shows `refs/tags/research-final^{}` = `cd03af9c`.) Lockfile: `docs/research-record/ENVIRONMENT_AT_FREEZE.txt` (late-stage container only); the container image cannot be exported from the sandbox and is not recorded.

**Clean**

- [x] Remove the `.bundle` files, `_to_delete/`, and lock debris in a normal commit; update `.gitignore`. (2026-10-05: none of these is tracked; `.gitignore` now excludes them.)
- [x] Restructure to the target layout; record every move in `MOVES.md`. (2026-10-05, `6a278bf1`: 231 moves in `docs/research-record/MOVES.md`/`.json`. Deviations: canonical artifacts stay at their registered paths under `outputs/`, `scripts/` stays at the root, and `src/` is not split, because frozen registries, manifests and the code digest cite those paths.)
- [x] Collapse each experiment's documents to one contract and one closeout; move the rest to the research record. (Complete with provenance-preserving deviation, 2026-10-05: each experiment has one obvious contract/protocol and closeout entry point through its README (`experiments/expN/README.md`). Registered contracts, closeouts and errata remain separate immutable documents rather than being merged. Do not merge them.)
- [x] Move process documents to `docs/process/`; `AGENTS.md` becomes `docs/ENGINEERING_RULES.md`. (2026-10-05; a root `AGENTS.md` pointer remains.)

**Add**

- [x] `LICENSE`, `CITATION.cff`, and terms of use for each source in `sources.yaml`. (2026-10-05: Apache-2.0 code, CC BY 4.0 docs; `CITATION.cff`; licence, version, citation, retrieval note and sha256 for every registered source. Original retrieval dates were never recorded and are stated as unknown.)
- [x] `docs/DATA_INTERFACES.md`, with a demand-constructor example and test. (2026-10-05; the adapter is in `src/cota_release/demand.py` because `src/cota_opt` is frozen.)
- [x] `CANONICAL_ENVELOPE.units.json` sidecar; report and figure generators read units from it. (2026-10-05: `outputs/CANONICAL_ENVELOPE.units.json`; figure tooling reads it; `tests/test_envelope_units.py`.)
- [x] `docs/CALIBRATION.md`, with the "uncalibrated" label wired into artifacts. (2026-10-05: the label lives in `config/model_status.yaml` and is stamped into release-generated artifacts and the briefs; frozen artifacts are not retrofitted.)
- [x] `cota-opt validate`, with a failing-validation test. (2026-10-05: implemented as `cota-opt validate-model`; the research CLI's `validate` keeps its meaning. `tests/test_release_validation.py`.)
- [ ] `cota-opt reproduce exp1` and `--smoke`; full runtime measured and published. (2026-10-05: both commands exist; smoke reproduction recorded; full reproduction status in `docs/REPRODUCE.md`.)
- [ ] `docs/SCALING.md`, with the Exp 5 job-array reproduction passing. (2026-10-05: document written; the job-array acceptance run is a `v1.0` requirement and has not been done.)

**Report**

- [x] README rewritten as the front door. (2026-10-05; the long per-experiment text moved unchanged to `docs/FINDINGS.md`.)
- [x] Public brief, planning brief, and technical report drafted from canonical artifacts. (2026-10-05: `docs/PUBLIC_BRIEF.md`, `docs/PLANNING_BRIEF.md`, `docs/report/TECHNICAL_REPORT.md`.)
- [x] Seven figures generated by script, each with its source CSV (`scripts/make_report_figures.py` → `docs/report/figures/`, 2026-10-05; report Figures 1–6 and 8, plus amendment G2-a's Figure 7).
- [ ] Every number in every document checked against rule 1 of the report rules. **Revised acceptance (2026-10-05):** every decision-relevant scientific numerical claim in public-facing documents is machine-traceable to committed evidence. The criterion is not 100% of numeric tokens. `scripts/audit_public_numbers.py` classifies every number in the priority sections (abstract, README headline and results, report summary, limitations, retractions and conclusion, both briefs) and fails if one is neither machine-checked nor explicitly classified as non-scientific. Status: see `docs/RELEASE_PROVENANCE.md`.

**Release**

- [x] Usability test: someone who has never seen the project clones it, runs the quickstart, and finds where their data would go. Note where they got stuck and fix it. (2026-10-05: two passes by fresh-context AI agents, not a human; the second pass ran every command first time. Fixes in `13d1d63d` and `a7153b98`. A human usability test has not been done.)
- [x] Provenance test: a researcher who has never seen the project gets one superseded or retracted result. Without help, they trace its original artifact, contract, commit, the reason it was superseded, and its canonical replacement. Note where the trail broke and fix it. (2026-10-05: two passes by fresh-context AI agents, four results traced; breaks fixed in `13d1d63d` and `a7153b98`, frozen-registry gaps recorded in `outputs/README.md` and Exp 2 errata E2. Open: original commits of condensed history are only on the unpublished `backup-exp3-preclean`. A human provenance test has not been done.)
- [ ] Tag `v1.0` and mint a Zenodo DOI.
- [ ] Update the Full City Columbus work page: link the release and move the COTA card up the maturity ladder, with the reviewer and review scope disclosed.

## Amendment log

| # | Date | Change | Reason |
| --- | --- | --- | --- |
| G1-a | 2026-09-23 | Seed disagreement "19–26%" → "about 19% under Model B (worst pair 19.7%, mean 19.1%)" in report rule 8 and Figure 7 rule 5 | 19.7% is Model B; 26.0% is the superseded Model A (`docs/research-record/DISCOVERIES.md:723–728`). The old range broke report rule 1 by mixing evaluators. The conclusion is unchanged. |
| G1-b | 2026-09-23 | Added the canonical-envelope units trap, the `CANONICAL_ENVELOPE.units.json` sidecar, and a checklist item; report rule 4 now takes unit labels from the sidecar | The artifact mixes the block-derived 197 with the proxy peak envelope under physical-vehicle wording. It is cited by live provenance, so it is labelled, not edited, before `research-final`. |
| G1-c | 2026-09-23 | Added the push-to-GitHub step as a release-gate precondition and the first Freeze item after Exp 7 | EXP4N commits exist only in the container and hand-carried bundles. The merge into `master` cannot happen until they reach Ian's machine and GitHub. |
| G2-a | 2026-10-05 | Added an eighth figure: the post hoc F1 decision space and the two REF fixed points (report Figure 7). Report figures are numbered by first mention; the guideline IDs are kept in `docs/report/figures/FIGURES_MANIFEST.json` (G1 → Fig 1, G7 → Fig 2, G3 → Fig 3, G4 → Fig 4, G5 → Fig 5, G6 → Fig 6, G2 → Fig 8) | The round-2 referee (R2-23) named the frontier and the F1 two-basin figure as essential; journals number figures in order of citation |
| G2-b | 2026-10-05 | The Figure 7 (now report Figure 2) aggregation contract's free parameters were frozen in `config/change_map_aggregation.yaml` (commit `08a16b35`) before any map was drawn | Rule 1 requires the units to be fixed before any plan is plotted |

---

## Verification note on G1-c — what this container can and cannot confirm

Recorded 23 Sep 2026 while storing this document.

**Confirmed here:** `099d0527` exists and is real ("Exp 5 OFF→ON diagnostic: the
binding constraint is not the one Exp 5 varies"). `exp3-clean` is **16 commits
ahead of it** locally, and those 16 are the entire EXP4N body of work.

**Cannot be confirmed here:** what GitHub actually holds. This container has no
configured git remote at all — `git branch -r` shows a single stale
remote-tracking ref, `ian/master`, left over from a remote that is no longer in
the config. So the statement "GitHub has `exp3-clean` only through `099d0527`"
is Ian's from GitHub Desktop, not something this container verified, and it is
recorded as his. The part this container *can* stand behind is the count: 16
commits exist only here and in hand-carried bundles.
