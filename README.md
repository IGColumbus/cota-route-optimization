# COTA Transit Network Model and Optimization Harness

*(Formerly titled "Transit Digital Twin". That was a prototype description: the
model is uncalibrated and is not an operational digital twin.)*

A research platform for one question:

> Holding modeled operating resources approximately constant, how do frequency
> allocation and network-design interventions trade off modeled unserved demand
> and passenger generalized cost, and how much can the study's λ-weighted
> objective improve under those interventions?

In short: holding modeled operating resources approximately constant, what
service and network changes improve the modeled coverage–generalized-cost
trade-off? (An earlier framing as "reducing passenger generalized travel cost"
was corrected; `docs/REPORTING_CORRECTIONS.md` C1.)

**Author and disclosures.** Human author: Ian Gregory, who is responsible for
all content. Generative AI (Anthropic's Claude) assisted with code, analysis,
internal review passes and drafting; AI systems are not authors or referees,
and no external human peer review has taken place
(`docs/report/reviews/README.md`). The project is independent of the Central
Ohio Transit Authority (COTA) and is not affiliated with or endorsed by COTA.

Everything here is built from public data, uncalibrated, and explicit about
every assumption. It has retracted its own headline answer **five
times** — for a modelling error, an under-powered search, an evaluator that was
silently the wrong model, a benefit that turned out to be the search rather
than the intervention, and a geometry ranking that turned out to rank each
candidate's self-drawn resource cap (report §9, R1–R5). Those retractions are
the most useful output so far, and all five are documented rather than quietly
fixed; §9 lists all 16 retractions and protocol amendments.

## Status

* **Frozen research record:** commit `cd03af9c`, tag `research-final` (public).
  Everything after it is reporting and release work that changes no frozen
  artifact (`docs/RELEASE_PROVENANCE.md`).
* **Stage:** working paper. Not peer reviewed, not submission-ready, and no
  `v1.0` release yet. The model is uncalibrated and has no external validation
  data (route volumes, stop boardings, transfers, trip lengths).

## Bottom line

Within the modeled system, reallocating frequency within the existing route
structure produced a substantial favorable coverage effect at approximately
fixed modeled resources. The fixed-plan sign remained positive across the
implemented sensitivity perturbations. The post hoc service-preserving
re-optimization analysis is encouraging but remains labelled post hoc unless
independently confirmed. Through-routing produced no supportable gain, local
route-mutation effects were small, and N4, the best of the 200 promoted and
certified greenfield candidates, remained materially worse than N3 under the
tested matched model, subject to known path-assignment and waiting-model
limitations. OFF-permitting optimization exposed an important
objective-identification problem. Several of the strongest findings are
methodological: matched convergence, matched starts, resource normalization,
evaluator identity, basin dependence and decision-space matching materially
change conclusions.

**Experiment 1, the headline:**

> Within the model, reallocating frequency within existing routes at fixed
> modeled resources served **~680 more modeled weekday trips** (+3.3% served;
> ~2.2% of the 30,949 modeled weekday trips) and reduced modeled unserved
> demand by **6.65%** (solver-seed SD 0.06 percentage points), while total
> generalized cost rose 0.88%. The gain stayed positive under all 44
> pre-specified fixed-plan perturbations (−1.9% to −7.0% unserved).

*Solver-seed SD measures optimization variability with data and assumptions
fixed. It is not a confidence interval and does not quantify real-world
uncertainty.* The claim is the aggregate: independent seeds disagree on about
19% of route-periods, so no individual route headway is a recommendation. The
plan's physical fleet requirement has not been verified.

## Results at a glance

Every effect is on the study's λ = 2 objective unless stated, each in its own
model instance; cross-lever effect sizes are not formally comparable. Lower
objective is better.

| experiment | result | detail |
|---|---|---|
| 1. Frequency reallocation | the headline above | report §5.1 |
| 2 / 2B. Through-routing splices | no supportable gain: under matched starts the leading splice is +0.090% unserved, worse than no edit and inside the noise floor; the 240-set combination sweep is discovery-stage | report §5.2 |
| 3. Route mutation | 29 seed-distinguishable improvements; the leader (20 restarts) **−0.18657%** of the objective | report §5.3 |
| 4 / 4N / 4A. Greenfield design | N4, the best of the 200 promoted and certified greenfield candidates, is +8.55% to **+9.66%** of N3's objective (worse) across the matched comparisons; the best of all 2,000 generated is not identified | report §5.4 |
| 5. Resource frontier | failed its monotonicity gate on N4; on N0 both resource axes bind at today's levels | report §5.5 |
| 6. Study safeguards | on N0, study-safeguard constraints worsened the modeled objective by 0–0.91% (N3: 0–0.63%); these are study safeguards, not COTA policy | report §5.6 |
| 7. Robustness | Exp 1's sign holds at every fixed-plan level. At λ = 2 with route-periods allowed OFF, two fixed points 0.16% apart give −5.4% and **+30.5%** unserved, so unserved demand is not identified there. At λ = 1 the optimizer nearly empties the network (**557** of 2,516 vehicle-hours) | report §6 |

Retractions: report §9. Superseded artifacts: `outputs/SUPERSEDED.md`.
`docs/FINDINGS.md` gives each experiment in plain language.

## Primary limitations

* **Demand is a commute proxy.** LODES commute flows only; non-work travel is
  absent and period shares are assumed. This is the largest unquantified error.
* **No calibration or external validation.** The model serves 66.8% of the
  NTD-derived 30,949 linked trips; that is a fit statistic, not validation.
* **Waiting and assignment.** Same-route waiting only; the cross-route
  common-lines omission is up to 12.47% of generalized cost on N4.
  All-or-nothing assignment.
* **Data vintages differ:** 2020 Census, 2022 LODES, 2024 NTD, 2026 GTFS. The
  direction and size of the resulting error are unquantified.
* **No fleet or deployability claim** for any modified plan; scheduled service,
  not actual.
* **Start-basin dependence:** the λ = 2 objective is flat across very different
  plans, so served-trip figures from single-start runs are basin-dependent.

Full table with sizes: report §8.

## Quick start

Requires Python 3.11.

```bash
git clone https://github.com/ian-gregory94/cota-route-optimization.git
cd cota-route-optimization
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements-lock.txt && pip install --no-deps -e .   # pinned
# or: pip install -e ".[dev]"                                         # unpinned

python -m pytest -rs -m "not slow"       # seconds; leaves out the three slow tests, which need the raw data
# python -m pytest -rs                   # all tests: without data/raw the slow ones skip (EXTERNAL_DATA_UNAVAILABLE);
#                                        # with it they run real solves and take minutes
python scripts/verify_report_claims.py   # report numbers against the committed artifacts
cota-opt --help
```

None of that needs data. The committed artifacts under `outputs/` hold every
result; the raw inputs are only needed to recompute them.

### Where the data goes

Raw public inputs are not committed. They live in `data/raw/<source>/`, which
the registry creates and checksums. Each must be the exact version the study
used; the sha256 of each is in `config/sources.yaml`.

```bash
cota-opt data status                       # what is registered, what is missing
cota-opt data fetch lodes_od_oh            # download from the recorded URL and register
cota-opt data register cota_gtfs_static ~/Downloads/cota.gtfs.zip   # or register a file you downloaded
```

The five inputs are `cota_gtfs_static`, `lodes_od_oh`, `lodes_wac_oh`,
`lodes_rac_oh` and `cenpop_bg_oh`. A file whose sha256 differs is refused.
Caveat: COTA's URL serves its *current* feed. The study used `feed_version
2026-MAY-04-BB_20260630` (service dates 2026-05-04 to 2026-09-06), so that URL
may already serve a later feed, which will be refused. No public archive of the
study's feed file exists yet.

Using other data (another feed, other demand) is not yet packaged: report §10
lists what would change, and the planned interface document
(`docs/process/RELEASE_AND_REPORTING_GUIDELINES.md`, "Data interfaces") has not
been written.

### Reproduce

```bash
# the recorded (bit-exact) environment also set these:
export PYTHONHASHSEED=0 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
cota-opt reproduce exp1 --smoke   # rebuild the Exp 1 instance, re-evaluate the certified plans, compare
cota-opt reproduce exp1           # also re-solve the three seeds at certification effort
```

Both need the five raw inputs and build everything else themselves (no
separate `validate` or `baseline` step). The smoke run does no optimization, but its
first run builds the path sets: 42 min 42 s on one core in the recorded run,
then about a second once `data/cache/` is warm. The full run adds three
certification solves; the original runs took 2,829–3,008 s each
(`outputs/seedcheck_modelB.jsonl → seconds`), and the full command has not
been timed from a clean checkout. Exit codes: 0 reproduced, 1 drift, 3 raw
inputs missing. The recorded result and environment are in
`docs/REPRODUCE.md`, with commands for every other experiment.

## Where to find things

| you want | go to |
|---|---|
| the current result and its limits | `docs/report/TECHNICAL_REPORT.md` (abstract, §1 summary table, §8 limitations); longer plain-language summary in `docs/FINDINGS.md` |
| one experiment's contract and closeout | `experiments/exp1/README.md` … `experiments/exp7/README.md` (index: `experiments/README.md`) |
| canonical artifacts | `outputs/CANONICAL_RESULTS_v5.json` (authority), `outputs/README.md` (index). `outputs/canonical/` holds only three early records, not the canonical set |
| superseded and retracted material | `outputs/SUPERSEDED.md`, `outputs/superseded/`, report §9 (retractions), errata files in `experiments/exp2/` and `experiments/exp7/` |
| the frozen research state and what is public | `docs/RELEASE_PROVENANCE.md` (frozen commit `cd03af9c`) |
| how to reproduce | `docs/REPRODUCE.md`; `cota-opt reproduce exp1 --smoke` |
| wording corrections since the freeze | `docs/REPORTING_CORRECTIONS.md` |
| where an old path went | `docs/research-record/MOVES.md` |
| the research history | `docs/research-record/` (`DISCOVERIES.md`, `STATE_OF_PLAY.md`, superseded designs) |

## Layout

```
src/cota_opt/      the research code (its content digest is pinned by the frozen contracts)
src/cota_release/  release tooling: the `cota-opt` entry point and `reproduce`
experiments/       one folder per experiment: contract/protocol, closeout, README
scripts/           experiment runners and report tooling (verifier, figures)
config/            sources (with terms), assumptions, cost weights, constraints
tests/             deterministic tests; tests needing registered raw data skip
                   with the reason EXTERNAL_DATA_UNAVAILABLE
outputs/           canonical and superseded artifacts (see outputs/README.md)
docs/              report, reproduction, glossary, provenance, engineering rules,
                   process notes (docs/process/), research record (docs/research-record/)
```

## Citing

Cite the frozen research commit `cd03af9c` (tag `research-final`) and the
report; `CITATION.cff` has the metadata.

## License and data terms

Copyright 2026 Ian Gregory.

* **Apache-2.0** (`LICENSE`): project code — `src/`, `scripts/`, `tests/`,
  `config/` and other code.
* **CC BY 4.0** (`LICENSES/CC-BY-4.0.txt`): `docs/`, the technical report, the
  report figures and other project-authored documentation.

The licences cover this project's own work, not the source data. Derived
artifacts under `outputs/` remain subject to the source-data terms recorded in
`config/sources.yaml`:

* **COTA GTFS** (cota.com/data). COTA grants a non-exclusive, limited and
  revocable right to use, reproduce and redistribute its data, as is. COTA
  keeps ownership. COTA trademarks may not be used in association with the
  data.
* **LEHD LODES and NTD.** These are US federal government works.

This project is independent of COTA. It is not affiliated with or endorsed by
COTA, and nothing here is COTA policy or a recommendation to COTA. This is a
summary, not legal advice. `config/sources.yaml` records the terms, version,
citation and sha256 of every source.
