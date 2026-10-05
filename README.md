# Columbus / COTA Transit Digital Twin and Optimization Harness

A research platform for one question:

> Holding COTA's approximate current operating resources constant, how much can
> passenger generalized travel cost be reduced through improved frequency
> allocation, transfer timing, stop structure, and eventually route topology?

Everything here is built from public data, uncalibrated, and explicit about
every assumption. It has retracted its own headline answer **five
times** — for a modelling error, an under-powered search, an evaluator that was
silently the wrong model, a benefit that turned out to be the search rather
than the intervention, and a geometry ranking that turned out to rank each
candidate's self-drawn resource cap. Those retractions are the most useful
output so far, and all five are documented rather than quietly fixed.

## What we currently believe

**Experiment 1 — frequency redistribution, closed and certified.**

> Redistributing service inside COTA's existing routes and existing
> 2,517 weekday revenue vehicle-hours reduces unserved demand by
> **6.65% ± 0.06**, serves **3.30% ± 0.03** more trips, raises total
> generalized cost by **0.88% ± 0.04** and lowers cost per trip actually served
> by **2.34% ± 0.01** — using 2,516.5 of 2,517.2 vehicle-hours and without
> exceeding the baseline's per-period **peak-concurrency proxy**, which the
> solver enforced as a cap. That proxy is not a bus count. **The plan's physical
> fleet requirement has not been verified.**

(± = solver seed spread, SD of 3 seeds.) Total cost rises because the plan serves 3.3% more people; cost per person
served falls. Three seeds at full effort on one shared candidate set.

*Correction (fleet wording).* Earlier versions of this page said "no additional
buses (197.0 peak vehicles against 197.0)". Both 197.0 figures come from one
proxy (`blocks.fleet_estimate`, recorded in `outputs/fleet_check_modelB.json`
→ `candidate_fleet`): the per-route cycle-over-headway sum at pm peak, multiplied
by the baseline's interlining factor 197 / 150.73 = 1.307. The baseline reads
197.0 by construction, and the plan reads 196.999. The only physical count here,
197 from COTA's published blocks, applies to the existing schedule only.
No modified plan has a blocking-based vehicle count
(`FLEET_AND_BLOCKING.md`, `docs/RELEASE_AND_REPORTING_GUIDELINES.md`). The
canonical records (`outputs/canonical/exp1_final.json`,
`CANONICAL_RESULTS*.json`) are immutable and keep the old wording. The
correction is carried additively in the results registry.

Two things travel with that number and may not be dropped:

* **The claim is the aggregate, not any one timetable.** Independent seeds
  produce plans differing on **19% of route-periods** by an average of seven
  minutes while their unserved-demand changes have an SD of 0.064 points
  (range 0.12: −6.60, −6.72, −6.63%). The optimum is flat.
  No individual route headway is a recommendation. The constructive reading is
  the better one: many concrete schedules realise the same benefit, so
  constraints this model cannot see — operator bidding, layover geography,
  garage assignment, politics — can likely be satisfied at little cost
  (untested).
* **The certified frontier begins at λ = 2.** The cost-favouring λ ≤ 1 corner
  fails path-set adequacy on both models and is reported as uncertified.

**Experiment 2 — route geometry, no supportable claim.**

> Twelve splice candidates. **Six do measurable harm. None does measurable
> good.** The best available geometry intervention in this candidate set is no
> geometry intervention.

At the ranking effort used to order candidates, the two leaders looked worth
about half a point each. Re-solved at the effort Experiment 1 is certified at —
400,000 iterations, 20 restarts, with three zero-edit replicates in the same run
— both land inside the 0.287-point noise floor. The replicates score 9749.1,
9748.8 and 9765.1 unserved; the leading candidate scores 9764.8. Re-running the
*baseline* with a different seed moves it further than the edit does.

The unedited network was the under-optimized one: at low effort the baseline had
not been solved as well as the edited networks had. Both sides ran at the same
*nominal* effort, which is what the standing rule requires — the same effort was
simply not equally sufficient for both. **Matched effort is necessary and not
sufficient; what has to match is convergence.**

The harmful candidates stay harmful at full effort. Harm survives more search
and apparent benefit does not, which is the right way round — and a useful
heuristic: a benefit that shrinks with effort probably was never there.

**Experiment 2B — the joint subset search** over all 240 structurally feasible
combinations is **closed, and its answer is the null.** Because edits do not
compose, *it*, not the single-candidate ranking, answers "which combination
should COTA make" — and the answer is none of them. Not one of the 227
multi-edit sets beats the best single, harm rises monotonically with every
edit added, and at λ≥2 every combination *substitutes*: it delivers less than
its members promised separately, with zero exceptions in the entire feasible
space. The leader was then re-solved at certification effort under three seeds
and scores +0.007% — two hundredths of a noise floor.

The same leader wins at λ ∈ {1, 2, 4}, so this is a result about the network
rather than about one point on the cost/coverage trade-off. Full account in
`EXPERIMENT2_CLOSEOUT.md`.

**Experiment 3 — route mutation, closed and certified** (frozen at `exp3-final-v1`).

> Of 84 census states across eight edit kinds, 39 were promoted and **29 remain
> certified** against the unedited control. The leader,
> `add_stop-010#22c4c35ac5b2`, improves the λ=2 objective by **−0.18657%** with
> |mean Δ| / SD = **78.6** over five paired seeds, and is distinguishable from
> all 28 other certified candidates.

Certified means distinguishable from solver variance at the stated effort —
nothing more, and the mechanism is not established. The certified set is not
uniform in effort: 23 of the 29 carry 40-restart verdicts and 6, the leader
among them, carry 20-restart verdicts. Anyone quoting the number quotes that
split with it. The discovery stage was also found to have had its optimizer
chosen by the treatment (D27) and was corrected before certification.
`EXPERIMENT3_CLOSURE.md`.

**Experiment 4 — route geometry at scale, certified under one common resource
envelope.**

> 200 promoted candidate networks were certified by exact optimization, then
> **re-certified under one common resource envelope (revenue vehicle-hours plus
> the per-period peak-concurrency proxy)**
> (`EXP4_FULL_NORMALIZED_CERTIFIED`: 200/200, integrity gate passed). The best
> is `35e351133d6f` at **3,223,885.9475**, ahead of the second by **0.387006%**.

The first run reported a different leader, `ecb2ffc4bcce`. Under the common
envelope it ranks **185 of 200**. That run resolved each candidate's
peak-concurrency-proxy cap against the candidate's own baseline plan (`exp2.py:324`), so
every candidate was optimized inside a box it drew for itself: it ranked
candidate-specific optimization problems, not geometries. Fixing the envelope,
and nothing else, inverted **36.7%** of pairwise orderings (Spearman
**+0.3566**); `src/cota_opt` is byte-identical across the rerun. The first run's
objective values remain exactly reproducible and are not withdrawn — its
ordering is superseded. `EXPERIMENT4_NORMALIZED_CLOSEOUT.md`.

It does not establish:

* **that the 0.387006% margin is meaningful.** It is ~204× the D33-B noise
  band, which rules out solver noise and establishes nothing further. Experiment
  5 later measured a start-basin residual of at least 1.70% on the leader (D39),
  larger than this margin;
* **any fleet or deployability claim** — the fleet instrument returns
  `UNDECIDABLE` for every candidate;
* **anything about the 1,800 proposals** the top-200 promotion cap excluded. An
  out-of-band audit showed that cap is invalid (`EXPERIMENT4_AUDIT_CLOSEOUT.md`).

The common envelope also changed how much service the plans run. Under the
first run's self-drawn caps, certified plans spent **36.16–37.33%** of the 2,517 weekday
vehicle-hours and switched off **78.5–86.9%** of route-periods; under the common
envelope they spend **99.92–100.00%** and switch off **56.2–67.4%**. Descriptive, not
preregistered.

**Experiment 4, original question — the greenfield leader does not beat the
constrained redesign.** Experiment 4 was built to ask whether the best greenfield
network beats Experiment 3's leader. EXP4N never ran that comparison. Run under
the identical EXP4N certification contract (`EXPERIMENT4_ORIGINAL_QUESTION_ADDENDUM.md`):

> obj(N4) − obj(N3) = **+283,973 (+9.66% of N3)**. Lower is better, so the
> greenfield leader is **worse**. Firewall-admitted; only network fields differ.
> (No served-trip comparison is quoted: Experiment 7 showed served demand is not
> identified once service can be switched off.)

The pipeline first reproduced EXP4N's N4 bit-exactly. The result is conditional
on the path model, which fits N4 much worse, and on the same-route waiting
model, whose cross-route omission is 12.47% of generalized cost on N4. It
survives an omission-corrected costing (+7.87%) and every fixed-plan λ above
1.087. Gates 4-12 and 4-13, fleet and physical inspection are not discharged.

**Experiment 5 — modeled resource frontier: run, and its preregistered
acceptance rule FAILED on N4 (`EXP5_MONOTONICITY_FAILURE`).** The original
design is retired (`EXPERIMENT5_PREMISE_RETIREMENT.md`): hours were not slack
once plans were normalized.

The reframed experiment:

* two fixed networks: N4 and N0, COTA's existing geometry;
* two axes: revenue vehicle-hours and the solver's peak-concurrency proxy, which
  is not fleet;
* 16 cells each, from 75% to 150%;
* EXP4N's certifier throughout.

Every gate passed except monotonicity: reproduction, reach, convergence, the
firewall (46/46) and order sentinels (4/4). `EXPERIMENT5_CLOSEOUT.md`.

* **On N0 (all 99 nested pairs monotone):** both axes bind at today's levels.
  Above them, only the peak proxy binds; extra hours change nothing. Below them,
  cutting hours costs 0.57–2.05% of the objective.
* **N4 is worse than N0 at all 16 cells**, by 8.07–11.59%.
* **On N4, 12 of 99 pairs regress** by up to 1.70%: a looser budget certifies a
  worse plan. The cause is the start, which differs by cap, landing the (8,3)
  block search in different local optima (**D39**). That residual is ~4.4×
  EXP4N's first-to-second margin. EXP4N's ranking stays reproducible, but it
  cannot be read as robust among closely spaced candidates.

**Experiment 6 — the modeled price of policy constraints on N0 and N3:
`EXP6_POLICY_FRONTIER_CERTIFIED`.** Details are in `EXPERIMENT6_CLOSEOUT.md`.

The question: what does imposing a policy constraint cost on the **modeled**
objective? It is asked for the existing geometry (N0) and for the Experiment 3
redesign (N3). The setup:

* the frozen Model B demand and evaluation model;
* the EXP4N common envelope;
* λ = 2;
* a declared **basin-closure** search. Each cell is solved from its own greedy
  start, then its best plans are transferred across the policy nesting graph
  as explicit anchors until nothing improves. Monotonicity is then enforced.

Every gate passed: 54/54 record checks, closure fixed point in 3 of 8 passes on
both networks, 0/120 post-closure monotonicity violations, a clean reference
closure, firewall 25/25 policy and 13/13 structure, and 4/4 sentinels.

**The biggest finding is not a price.** Closure moved both unconstrained
reference cells into a different basin, at almost the same objective:

| | objective | served trips | OFF route-periods |
|---|---|---|---|
| N0, greedy basin → closed | −0.127% | 16,527 → 21,144 | 50 → 15 |
| N3, greedy basin → closed | −0.161% | 16,434 → 21,104 | 54 → 17 |

What that means:

* The λ = 2 objective is flat across very different plans.
* D39's start-basin dependence is not special to N4.
* Served-trip and generalized-cost figures from any single-start run are
  basin-dependent.
* The Exp 4A N3 and Exp 5 N0 records are exact records of their own contracts.
  They are not the best-known plans under that envelope, and they are not
  reopened.

**Modeled policy cost** (closed cell − closed reference; objective units, not
dollars):

* **N0: 0 to +0.912%.**
  * R2 OFF caps at 25% and 10%: 0. They do not bind at Exp 6's closed
    unconstrained plan. They would bind at the best-known one found later
    (Exp 7, 48 route-periods OFF; errata E8).
  * R2 at 5%: +0.212%.
  * R4 coverage: +0.244% / +0.428% / +0.482% (c = 0.05 / 0.01 / 0).
  * R6 ¾-mile area: +0.440%.
  * R1 60-min headway floor: +0.482%. R3 span, R4 at c = 0 and both bundles
    ended on the same plan as R1 H = 60.
  * R1 H = 30: +0.575%. R1 H = 20: +0.912%.
* **N3: 0 to +0.634%.** Each binding safeguard costs slightly more than on N0,
  by +0.04 to +0.08 percentage points.
* Exp 7's re-closure at the same settings moved these prices by −0.10 to +0.06
  points (errata E8).
* **R1 at H = 20 is infeasible under the modeled envelope on N3** (Amendment 1).
  Even minimum service exceeds the early-period peak-proxy cap, by 0.0166 proxy
  units. That is a result, and it has no finite cost.

**Single-start pricing would have been wrong.** Greedy-only prices differed
from closure-adjusted prices by −0.162 to +0.124 percentage points. They
included two impossible negative prices: R2_S25 at −0.115% on N0 and −0.081%
on N3. Before closure, 22 of 120 nested pairs were non-monotone.

**N3 vs N0 at matched policy** (firewall-admitted, 13 cells):

* N3 is better in every cell, by **0.153% to 0.229%**.
* At REF the gap is −0.229% closure-adjusted, against −0.194% single-start and
  −0.187% in Exp 3's certification.

Scope notes:

* Every regime is a **study safeguard**. None has a documented COTA numeric
  anchor, so none is COTA policy or Title VI compliance.
* R5 is `UNIMPLEMENTABLE_WITH_CURRENT_DATA` (Title VI form).
* R7 is excluded: there is no authoritative COTA frequent-network definition.
* The "COTA-compliant" combined regime was not run.
* Physical fleet is UNDECIDABLE. No valid instrument exists, and none was run.
* The closure certifies a fixed point of anchor transfers, **not a global
  optimum**. The flat objective above is direct evidence that better plans may
  exist.

**Experiment 7: robustness of findings F1–F6.** Stage 1
`EXP7_STAGE1_EVALUATION_COMPLETE` and Stage 2 `EXP7_STAGE2_REOPT_COMPLETE`
(`EXPERIMENT7_CLOSEOUT.md`). Not an operating plan; not COTA-endorsed;
commute-only proxy demand; scheduled service.

The design:

* **Stage 1** re-evaluated the frozen plans, unchanged. 47 levels plus BASE
  were run (44 Class A in seven dimensions: demand, runtimes, cost weights,
  walking, route removal and the retention curve; 1 Class B (Model A waiting;
  the as-issued common-lines/hyperpath item was not implemented, errata E16);
  2 additional) on
  four network variants (N0, N3, N4, N0S): 4 × 48 = 192 evaluation cells.
  Declared but not run: A4 reliability (2 levels, UNIMPLEMENTED), the B2
  jobs-accessibility objective (UNTESTED), path-width/scenario count (DROPPED
  as inert) and period tilt (NOT INCLUDED).
* **Stage 2** re-optimized, with basin closure, in the two dimensions a
  preregistered metric selected: objective weights (A5) and walking friction
  (A6).

Results:

* **Frequency (F1), fixed plans:** keeps its sign at every level, from −1.9% to
  −7.0% unserved.
* **Frequency, re-optimized:**
  * Re-optimized in the closest cell to Experiment 1's service rules (R1_H60:
    no route-period switched off, 60-minute maximum headway; study safeguards in
    `config/constraints.yaml`, not COTA policy; no documented COTA numeric
    standard), F1 is −2.1% to −7.0% at every λ ≥ 2 level re-optimized in Exp 7
    (A5 and A6 only), with one closure per cell. Post hoc
    (`docs/EXPERIMENT7_F1_ADDENDUM.md`). At λ = 1 it is +0.12%.
  * When the optimizer may switch service off, unserved demand is not
    identified by the objective. Two certified plans 0.16% apart give −5.4%
    and +30.5% at base assumptions.
  * At λ = 1 the optimizer nearly empties the network (557 of 2,516
    vehicle-hours): at λ = 1 a lost trip costs 60 min while the average served
    trip costs 83–86 min of generalized cost.
* **Splice null (F2):** the null test holds at every applicable level; the
  sign label is SIGN_SENSITIVE, as expected for an effect that small (recorded
  +0.0065% on the incumbent-start plans Exp 7 evaluates; +0.090% under matched
  starts, errata E17).
* **Greenfield (F4):** worse than N3 at every Class A level except λ = 1 at
  fixed plans (+7.7% to +19.4%), and at every λ ≥ 2 level re-optimized (+6.8%
  to +30.8%); at λ = 1, −1.31% (fixed plans) and −0.98% (re-optimized).
* **Safeguard prices (F6):** re-optimized prices are non-negative at every
  level (a negative one would have blocked certification); rankings unchanged
  at transfer penalty ×0.5 and moved at λ = 1, transfer ×2 and the walking
  levels, where the R2 OFF-share caps become binding. At fixed plans, prices
  change sign in 2 of 13 N0 and 7 of 12 N3 cells.

Not tested:

* reliability (A4, unimplemented);
* bootstrap re-optimization (A2 not selected);
* the jobs-accessibility objective.

The full write-up is `docs/report/TECHNICAL_REPORT.md` (draft). Next steps are
in `docs/FUTURE_EXPERIMENTS.md`.

## The Model A → Model B correction

A ride leg's waiting time can be priced two ways. **Model A** charges the
chosen pattern's own headway. **Model B** charges the combined frequency of
every same-route pattern that serves the boarding stop, the alighting stop, and
in that order — because a passenger boards whichever comes first. Model A is
the special case where one pattern qualifies.

Model A systematically undervalues frequent trunk service, which runs the most
pattern variants, so it is biased against exactly the routes a frequency
optimizer proposes to cut. Model B is the sole authoritative evaluator.

**And for three days the Experiment 2 evaluator was Model A while reporting
Model B.** The script built its evaluator without specifying the model and got
the config default; the run's log reported the *harness's* setting, which was a
different object. Correcting it changed six of twelve candidates' signs and
halved the headline geometry claim. Every experiment artifact now records the
model the evaluator actually used, and a run that cannot state it produces no
artifact. See `outputs/CANONICAL_RESULTS_v5.json` (v1–v4 are kept unchanged)
for which artifacts are current
and which are superseded — nothing was deleted, and a superseded artifact looks
entirely legitimate from the inside.

## Current limitations, with sizes

| limitation | size | direction |
|---|---|---|
| commute-only LODES demand | 24.7% of regional flow is transit-accessible; the top 20k pairs are 64.9% of that | unknown; the largest unquantified error |
| frontier below λ = 2 | uncertified on both models | quoted from λ = 2 upward |
| per-route headways | about 19% of route-periods under Model B (worst pair 19.7%, mean 19.1%) | aggregate unaffected; no route-level recommendation |
| cross-route common lines | upper bound on served-leg wait saving: 0.516% of GC on N0, 1.16% on N3, 12.47% on N4; untested by Exp 7 | overstates waiting on trunk routes; deferred |
| stop-service penalty | unmeasurable from this feed (−157 s/stop, inverted) | blocks any consolidation claim resting on runtime savings |
| novel-link running time | MAE 17.2 s, aggregate bias +0.41% | unbiased, but 20.5% median APE on a single link |
| scheduled ≠ actual | unquantified | no reliability penalty anywhere |
| fleet requirement | `UNDECIDABLE` for every Exp 4 candidate and all 32 Exp 5 cells; never measured for the Exp 1 plan. Deadhead times and terminal identity are not public | no fleet or deployability claim for any modified plan, Exp 1 included |
| start-basin dependence (D39) | ≥ 1.70% of the objective on N4 (Exp 5); 0.13–0.16% on N0/N3 references (Exp 6) | single-greedy-start certifications are not robust among closely spaced results. Exp 6's nesting closure repairs this within a nested grid, but it is not a global optimum |
| flat objective | plans 0.13–0.16% apart differ by ~4,600 served trips (+28%) and ~45% GC (Exp 6 REF) | served-trip and GC figures from single-basin runs are basin-dependent; quote the objective |
| block-local residual | unmeasured for every Exp 4 candidate, the leader included | a 0.387006% first-to-second margin is not a durable ordering |

## What it does

- **Provenance-first ingestion.** Every external dataset enters through an
  immutable raw store with SHA-256 checksums, retrieval timestamps and a source
  record in `config/sources.yaml`. Unknown data is marked `UNKNOWN`, never
  invented.
- **GTFS parse and validation.** Structural validation that reports malformed
  records rather than silently discarding them. COTA's current feed passes with
  zero errors.
- **Scheduled baseline.** Route/stop/trip counts, headway distributions, service
  spans, runtimes, revenue vehicle-hours and miles, peak vehicle counts, stop
  spacing — all labelled as *scheduled estimates*, not reported operating
  statistics.
- **RAPTOR routing.** Both a timetabled earliest-arrival router (ground truth
  against the published schedule) and a frequency-based generalized-cost router
  that composes with a `FrequencyPlan`, so passengers re-route when service
  changes.
- **Real OD demand.** LEHD LODES block-to-block commute flows aggregated to
  block groups, mapped to stop access, scaled to an NTD-anchored weekday
  linked-trip total.
- **NTD reconciliation.** The FTA agency profile is parsed deterministically and
  *rejected* unless it reproduces the profile's own 18 printed efficiency
  ratios.
- **Frequency optimization.** Marginal-exchange search over a headway ladder
  under a fixed vehicle-hour envelope, with a measured convergence curve rather
  than an assumed search budget. The search also carries a per-period
  peak-vehicle filter, but it is measured with the cycle-over-headway proxy
  (150.73 on the baseline against the block-derived 197) and is **not** a fleet
  constraint — `contract.py` declines the corresponding certification check
  rather than run it against the wrong quantity. No fleet number for any
  candidate network is known; see `FLEET_AND_BLOCKING.md` and
  `EXPERIMENT5_PREMISE_AUDIT.md`.

## Layout

```
src/cota_opt/      production logic (typed, tested)
  registry.py      immutable raw store + provenance
  gtfs.py          parsing and structural validation
  baseline.py      scheduled-service baseline tables
  raptor.py        timetabled + frequency-based routing
  odmatrix.py      LODES OD, gravity fallback, zone system
  pathset.py       candidate path enumeration and fast re-costing
  frequency.py     FrequencyPlan / ResourceBudget / solver
  crowding.py      link loads and peak-load-point crowding
  routeclass.py    service-pattern route classification
  ntd.py           ratio-verified NTD profile parsing
  harness.py       one cached entry point for the whole build chain
  cache.py         content-addressed cache + checkpointed result store
tests/             890 deterministic tests (collected at master f79227cc, 2026-09-29)
config/            sources, assumptions, cost weights, constraints, scenarios
scripts/           experiment runners
outputs/           reports, experiment records, per-cell checkpoints
```

## Running it

```bash
pip install -e ".[dev]"
python -m pytest                      # 890 tests; the `slow` ones need data/raw + data/cache

python -m cota_opt.cli sources        # what data is registered
python -m cota_opt.cli ingest-gtfs path/to/cota.gtfs.zip
python -m cota_opt.cli validate
python -m cota_opt.cli baseline
python -m cota_opt.cli report

python scripts/convergence.py         # how much search this problem needs
python scripts/run_matrix.py --iterations 150000 --restarts 5 --width 48
```

The first build takes ~12 minutes; after that `data/cache/` makes it 0.2
seconds. Long runs checkpoint per cell and resume rather than restart.

## Data sources

COTA GTFS static and GTFS-Realtime; FTA National Transit Database (agency
50016); LEHD LODES8 origin-destination, residence-area and workplace-area
characteristics; 2020 Census block-group population centroids. URLs, licences
and retrieval status are in `config/sources.yaml`.

Some hosts are unreachable from a sandboxed environment; those files are
retrieved externally and registered through the same provenance path, so the
resulting artifact is identical either way.

## Standing caveats

Demand is LODES **commute** flow — non-work travel is absent, which matters most
at midday. Period demand shares are assumed, because LODES has no time
dimension. Stop-level boardings (APC) are not public and are the binding
constraint on everything downstream. Nothing here is a recommendation to COTA.

## Governing contract

`AGENTS.md` is the development and research contract: evidence standards,
provenance rules, CRS discipline, the scheduled-vs-actual distinction, and the
skeptic protocol for surprising results.

`ACCEPTANCE.md` holds the gates, each committed before the run it judges.
`EXPERIMENT3_CONTRACT.md` fixes what Experiment 3 may mutate, before any
candidate exists. `DISCOVERIES.md` is the research diary and keeps every path
taken, including the wrong ones; this README describes what we currently
believe, which is a much shorter list. `STATE_OF_PLAY.md` is the long-form
current state.

## License and data terms

Copyright 2026 Ian Gregory. The code is licensed under the Apache License,
Version 2.0 (`LICENSE`). Documentation, the technical report and its figures are
licensed under CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/).

The licences cover this project's own work, not the source data. Files derived
from external data keep their sources' terms:

* **COTA GTFS** (cota.com/data). COTA grants a non-exclusive, limited and
  revocable right to use, reproduce and redistribute its data, as is. COTA
  keeps ownership. COTA trademarks may not be used in association with the
  data.
* **LEHD LODES and NTD.** These are US federal government works.

This project is independent of COTA. It is not affiliated with or endorsed by
COTA, and nothing here is COTA policy or a recommendation to COTA. This is a
summary, not legal advice. `config/sources.yaml` records the COTA and NTD terms;
the LODES entries do not yet carry a terms field.
