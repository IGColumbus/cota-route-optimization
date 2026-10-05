# Data interfaces

Every place outside data enters the model, what the study used, and what a
user can supply instead. The rule throughout: say what is actually supported.
Where no adapter exists, this page says so.

## Four kinds of substitution

Each input below states which of these it supports.

1. **Exact historical source.** The same bytes the study used. `cota-opt data
   register|fetch` accepts a file only if its sha256 matches
   `config/sources.yaml`. This reproduces the study.
2. **Newer version of the same source** (a later COTA feed, LODES 2023). The
   frozen research code runs on it, and caches are keyed by the file's sha256
   so they never mix. The result is a **new study**: not comparable with the
   canonical artifacts, and not covered by any frozen contract. `cota-opt data`
   refuses such files on purpose; register them with the research CLI
   (`python -m cota_opt.cli ingest-gtfs …` for GTFS) only for new work.
3. **New source, same schema** (another agency's GTFS, a different OD table in
   zone-to-zone form). Supported only where an entry point exists, listed per
   input below.
4. **Fundamentally different input** (APC-derived OD, fare-card trip chains,
   AVL running times). Needs an adapter. One adapter exists, for OD demand
   (`src/cota_release/demand.py`); the others below are marked
   *no adapter*.

Frozen boundary: `src/cota_opt` is the research code whose content digest the
frozen contracts pin. Adapters live in `src/cota_release/` or `examples/` and
call the research code unchanged.

## Summary

| input | study source | entry point | exact | newer version | same schema | different input |
|---|---|---|---|---|---|---|
| GTFS schedule | COTA GTFS static, `feed_version 2026-MAY-04-BB_20260630` | registry `cota_gtfs_static` | yes | runs; new study | another agency's feed: runs, untested beyond COTA | n/a |
| OD demand | LODES8 Ohio OD 2022 (commute) | `cota_opt.odmatrix.from_lodes_od`; adapter `cota_release.demand` | yes | runs; new study | **yes**, zone-to-zone CSV via `cota_release.demand` | APC/fare-card OD: convert to the same CSV first |
| system totals (NTD) | NTD 2024 profile, NTD ID 50016 | constants in `config/assumptions.yaml` | yes (constants) | edit constants; new study | same | n/a |
| Census geography | 2020 block-group centroids (CenPop), LODES RAC/WAC 2022 | registry `cenpop_bg_oh`, `lodes_rac_oh`, `lodes_wac_oh` | yes | runs; new study | another state: needs the county filter changed (frozen code) | no adapter |
| running times | GTFS scheduled | GTFS `stop_times.txt` | yes | as GTFS | as GTFS | AVL / GTFS-RT: **no adapter** (collector exists, not wired into cost) |
| ridership (APC / farebox / fare-card) | none | none | — | — | — | **no adapter**; observed totals feed `cota-opt validate-model` only |
| blocking / run-cut | GTFS `block_id` | `cota_opt.blocks.reconstruct` | yes | runs | same | COTA run-cut: **no adapter** |
| deadhead | none (same-terminal only) | `cota_opt.exp4_blocking.TableDeadheadOracle` | — | — | table interface exists | **no data**; the oracle accepts a terminal-pair table |
| validation observations | none | `cota-opt validate-model` + `config/validation.yaml` | — | — | CSV per dimension | route volume: modeled side extracted; other three: no modeled extractor yet |

## GTFS schedule

* **Study source:** COTA GTFS static, sha256 `b11634f1…` (full digest in
  `config/sources.yaml`), service dates 2026-05-04 to 2026-09-06.
* **Schema:** GTFS static zip. Requires `stops.txt`, `routes.txt`,
  `trips.txt`, `stop_times.txt`; uses calendar files, `shapes.txt` and
  `block_id` where present.
* **Units:** times in seconds after midnight (GTFS times past 24:00 fold into
  the `owl` period); distances in metres after projection to EPSG:32617.
* **Checksum and version:** the registry records the sha256. `cota-opt data
  register cota_gtfs_static <zip>` refuses any other file. COTA's URL serves
  its *current* feed, which will not match, and no public archive of the
  study's file exists yet.
* **Entry point:** `cota_opt.registry` → `cota_opt.download.unpack_gtfs` →
  `cota_opt.gtfs.load_feed`. Structural validation: `python -m cota_opt.cli
  validate`. The study feed passes with zero errors.
* **Affects:** everything: network, runtimes, the scheduled revenue
  vehicle-hours envelope, path sets.
* **Validation performed:** structural (above); the model's baseline
  vehicle-hours must reproduce the schedule to 1e-9 (`cota_opt.exp2`), or the
  setup raises.
* **Replacement:** a newer COTA feed runs (kind 2); caches are keyed by the
  feed's sha256. Scripts that read the frozen `outputs/CANONICAL_ENVELOPE.json`
  carry the *study* feed's totals and must not be used with another feed.
* **Example:**
  ```bash
  cota-opt data register cota_gtfs_static ~/Downloads/cota.gtfs.zip
  python -m cota_opt.cli validate
  ```

## OD demand

* **Study source:** LEHD LODES8 Ohio OD, main, JT00, 2022: block-to-block
  home→work jobs. These are commute flows only.
* **Schema (study):** LODES CSV, columns `h_geocode`, `w_geocode`, `S000`.
  The harness aggregates to 2020 block groups (12-digit GEOIDs) and keeps
  Central Ohio counties. It then keeps pairs with a stop in walking range at
  both ends, takes the top 20,000 pairs, and scales to the weekday linked-trip
  total in `config/assumptions.yaml` (`demand_proxy`).
* **Units:** weekday person trips (after scaling).
* **Checksum:** registry `lodes_od_oh`.
* **Entry point:** `cota_opt.harness.build_harness` → `cota_opt.odmatrix.from_lodes_od`.
* **Affects:** every result. Demand defines served and unserved trips and the
  path sets.
* **Supplying a different OD (kinds 3 and 4):** `src/cota_release/demand.py`.
  * **Contract:** a CSV with `origin_zone`, `dest_zone`, `trips`. Zones are the
    study's zone ids (12-digit block-group GEOIDs); trips are non-negative.
  * **Validation:** duplicate pairs are summed. Unknown zones and bad rows are
    refused, unless `allow_unknown_zones=True`, which drops and counts them.
  * **Market rules:** `prepare()` applies the study's own rules using the
    frozen functions: accessible pairs, top-k, and optional scaling.
  * **Path sets:** `harness_with_demand()` puts the table into a harness and
    builds path sets under a cache key that includes the table's content digest.
  * **Tests:** `tests/test_release_demand.py`.

  APC- or fare-card-derived OD must first be expressed as that CSV. Period
  shares stay those of `config/assumptions.yaml`, and results are a new study.
* **Example:** `examples/demand_from_csv.py`. It needs the registered GTFS and
  Census inputs. The path-set build scales with the number of OD pairs: seconds
  for a handful, tens of minutes on one core for a study-sized table.
  ```bash
  python examples/demand_from_csv.py my_od.csv --source "APC-derived OD 2026"
  ```

## System totals (NTD)

* **Study source:** NTD 2024 Annual Agency Profile, NTD ID 50016 (PDF).
* **Schema and units:** a PDF parsed by `cota_opt.ntd.parse_profile`, which
  rejects any parse that fails to reproduce the profile's 18 printed efficiency
  ratios.
* **Entry point:** the study uses NTD values as **constants** in
  `config/assumptions.yaml`. These are `demand_proxy.assumed_weekday_linked_trips`
  (30,949, derived from weekday boardings, bus share and an assumed transfer
  rate), `passenger.avg_ride_fraction`, and `operations.ntd_*` (reporting
  only). No experiment reads the PDF at run time, and it is not registered
  under `data/raw`.
* **Checksum:** none (`sha256: UNKNOWN` in `config/sources.yaml`).
* **Affects:** demand scale (all served and unserved counts).
* **Replacement:** edit the constants. That changes the config digest the
  frozen contracts pin, so the result is a new study.

## Census geography

* **Study source:**
  * 2020 Census block-group centres of population, Ohio (`cenpop_bg_oh`);
  * LODES8 RAC and WAC, Ohio 2022 (`lodes_rac_oh`, `lodes_wac_oh`), giving
    workers by residence and jobs by workplace.
* **Schema:** CenPop CSV (`STATEFP, COUNTYFP, TRACTCE, BLKGRPCE, POPULATION,
  LATITUDE, LONGITUDE`); LODES RAC/WAC CSV (`h_geocode`/`w_geocode`, `C000`).
* **Units:** persons; jobs; WGS84 coordinates, projected to EPSG:32617.
* **Entry point:** `cota_opt.baseline.build_baseline(demand_files=…)`, called
  by `cota_opt.harness.build_harness` with the module constant
  `cota_opt.harness.DEMAND_FILES`.

  Caution: that constant, and the same constant in eight scripts under
  `scripts/`, hard-codes the development container's upload folder
  (`/mnt/user-data/uploads/Downloads`). The research code is frozen and was
  not edited. Release tooling redirects every such path to the registered
  `data/raw/` file of the same name:
  * `cota-opt reproduce` and `cota_release.demand` do this automatically;
  * run any research script as
    `cota-opt run-script scripts/<name>.py [args]` (`docs/REPRODUCE.md` §0).
* **Affects:** the zone system (block groups with transit access) and every
  OD pair's access legs.
* **Replacement:** newer vintages run, as a new study. Another state or region
  needs the county filter (`CENTRAL_OHIO_FIPS`, frozen code) changed. No adapter.

## Observed running times (AVL, GTFS-Realtime)

* **Study source:** none. Running times are GTFS scheduled.
* **Entry point:** `cota_opt.realtime` (`python -m cota_opt.cli rt-collect`)
  fetches GTFS-RT vehicle positions, trip updates and alerts into SQLite.
* **Status:** collected, **not wired into cost**. The reliability weight is a
  placeholder (0). Exp 7's reliability dimension (A4) was not implemented.
* **Replacement:** **no adapter.** A user with AVL would need to build observed
  link times and a reliability term. That is a model change, not a data swap.

## Ridership: APC, farebox, fare-card

* **Study source:** none. No stop-level boardings are public.
* **Entry point:** observed totals enter **only** as validation observations
  (below). There is no adapter that turns APC or fare-card data into demand.
  Convert it to the OD CSV above yourself, or use it to validate.

## Blocking and run-cut

* **Study source:** GTFS `block_id`. `cota_opt.blocks.reconstruct` gives 197
  block-derived peak vehicles at 17:13 for the existing schedule only
  (`outputs/CANONICAL_ENVELOPE.json`; units in
  `outputs/CANONICAL_ENVELOPE.units.json`).
* **Status:** no modified plan has a physical vehicle count. The solver's
  per-period resource is the peak-concurrency proxy, which is not a bus count.
* **Replacement:** COTA run-cut or blocking data: **no adapter**.

## Deadhead

* **Study source:** none. Same-terminal deadhead only.
* **Entry point:** `cota_opt.exp4_blocking.TableDeadheadOracle(table={(from_terminal,
  to_terminal): seconds, …})`. It is a real interface: a pair absent from the
  table is `UNKNOWN`, never inferred. Without a real table, the fleet result is
  a bracket, and asking it for a certified value raises.
* **Status:** interface exists, **no data**. The fleet instrument returns
  `UNDECIDABLE` for every modified plan.

## Validation observations

* **Command:** `cota-opt validate-model` (release CLI). The research CLI's
  `validate` is unrelated: it checks GTFS structure.
* **Setup:** `config/validation.yaml` lists one observed file per dimension and
  a pass threshold per dimension. Set thresholds before running.
* **Schemas:**

  | dimension | observed CSV | statistic |
  |---|---|---|
  | route volume | `route_id, boardings` (weekday) | % RMSE of route boardings |
  | stop pattern | `stop_id, boardings, alightings` | % RMSE of stop boardings |
  | transfer behavior | `metric, value` with `metric = transfer_rate` | absolute difference, transfers per linked trip |
  | trip length | `bin_upper_min, share` | maximum difference of cumulative shares |

* **Output:** four independent statuses, each `passed`, `failed` or
  `unavailable`, plus the model's calibration status. There is no overall
  "validated" flag. Missing observed data, a missing threshold or a missing
  modeled counterpart each give `unavailable`.
* **Modeled side:**
  * Route volume can be computed from the study model (`--from-study`: weekday
    boardings per route on the current plan, Model B, from the frozen path-set
    evaluators). This needs the registered raw inputs and has not been run
    against observed data.
  * Stop pattern, transfer behavior and trip length have **no modeled
    extractor yet**. Supply modeled values with `--modeled file.json`, or they
    stay `unavailable`.
* **Acceptance test:** `tests/test_release_validation.py`. Deliberately
  mismatched route volumes give `failed`, absent stop data gives
  `unavailable`, and both appear in the artifact.
* **Current state:** all four dimensions `unavailable` (`config/model_status.yaml`).
* **Example:**
  ```bash
  # after setting observed.route_volume and thresholds.route_volume_max_pct_rmse
  cota-opt validate-model --from-study --out validation.json
  ```
