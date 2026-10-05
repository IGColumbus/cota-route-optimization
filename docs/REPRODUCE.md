# Reproduce each closed experiment

*A draft prepared 2026-09-28; the Exp 6 section was updated 2026-09-29 to the
frozen scripts. Each command below was checked to exist in `scripts/` with the
stated arguments, by reading its argparse block or docstring. None was executed
for this draft.*

## 0. Setup common to every experiment

```bash
pip install -e ".[dev]"
# Raw public inputs are gitignored; they must be staged under data/raw/
# (cota_gtfs_static, lodes_od_oh, lodes_rac_oh, lodes_wac_oh, cenpop_bg_oh)
# through the registry. See config/sources.yaml and docs/process/PUSH_TO_GITHUB.md
# ("What the bundle does not carry").
python -m cota_opt.cli sources
python -m cota_opt.cli ingest-gtfs path/to/cota.gtfs.zip
python -m cota_opt.cli validate
python -m cota_opt.cli baseline          # first build ~12 min, then cached in data/cache/
python -m pytest -m "not slow"           # fast suite; the full suite needs data/raw + data/cache
```

**Reproduction standard.** "Bit-exact" means the objective string, the plan
digest and the round trajectory are identical. That holds in the same
environment. Cross-environment reproduction has not been characterized.
`docs/process/RELEASE_AND_REPORTING_GUIDELINES.md` proposes the D33-B band as the
tolerance elsewhere, but D33-B measures a local solver gap and not
floating-point drift across platforms (see the audit note in
`docs/research-record/exp6/EXP6_PARALLEL_CLOSEOUT_PREP.md`).

## Experiment 1 — frequency redistribution (closed, certified λ ≥ 2)

```bash
python scripts/run_exp1.py --iterations 400000 --restarts 20   # certification effort
python scripts/seed_check.py --common-lines same_route          # seed stability (gate 7), 3 seeds, 400000/20
python scripts/run_diagnostics.py --common-lines same_route --plan <certified λ=2 plan csv>
                                                               # writes outputs/fleet_check<suffix>.json (fleet PROXY)
```
Compare against `outputs/canonical/exp1_final.json` (commit `f1a05645`, seeds
20260825–27, Model B). The peak figure in `fleet_check_modelB.json` is a
proxy. Read the Exp 1 fleet-wording correction before quoting it.

## Experiment 2 / 2B (closed)
Runners: `scripts/run_exp2.py`, `run_exp2_eval.py`, `exp2b_subsets.py`,
`exp2b_confirm.py`. The canonical artifacts are listed in
`outputs/CANONICAL_RESULTS_v3.json` → `exp2`, `exp2b`. Re-running 2B in full is
days of compute. The practical check is the certification artifact
`outputs/exp2b_certification.json`.

## Experiment 3 (closed, frozen at commit `8c2841c4`; tag `exp3-final-v1` not yet public)

Re-running Stage B (200 cells, 5 seeds) is days of compute. The closure is
verified, not re-run:

```bash
python scripts/exp3_verify_closure.py        # every number in experiments/exp3/EXPERIMENT3_CLOSURE.md recomputed from JSON
python scripts/exp3_freeze.py --verify       # frozen artifact hashes + receipt stores (default --tag exp3-frozen-v1)
python scripts/gen1_freeze.py --verify       # Gen1 manifest; NEEDS the tags exp3-frozen-v1 / exp3-final-v1, which are not yet public on GitHub (fetch them from a clone that has them)
```
**Known blocker:** the freeze tags are not on GitHub (see §F of the prep note),
so `gen1_freeze.py --verify` fails from a fresh GitHub clone until they are
pushed. The tagged commits themselves are reachable: `8c2841c4` from
`origin/master`, and `80221f75` from `origin/exp3`. `exp3_freeze.py` also
hashes living documents (`docs/research-record/DISCOVERIES.md`, `experiments/ACCEPTANCE.md`, `docs/process/OPERATIONS.md`,
…), so check whether its verify still passes on current `master` before
relying on it.

## Experiment 4 legacy (ordering superseded) and EXP4N (certified)

```bash
# Freeze (already done; refuses to overwrite)
python scripts/exp4n_freeze_production_contract.py
# Production (79.85 h compute in the original run); the wrapper writes a correct pidfile
bash scripts/exp4n_production_run.sh 6          # arg = max hours per launch; resumable
#   = python3 scripts/exp4n_launch.py --max-hours 6 ... (see the script for exact flags)
# Gates and ranking, in this order
python scripts/exp4n_integrity_gate.py          # §8 -- non-zero exit means DO NOT RANK
python scripts/exp4n_rank.py                    # §9 frozen tie-break 0297e180cf30369d
python scripts/exp4n_final_status.py
```
Spot-reproduce one candidate (the leader) with
`python scripts/exp4n_launch.py --only <label-or-key> --out-dir <scratch>`.
Compare with `outputs/exp4_normalized/production_mr120/cc40b4f4aea3aa05.json`:
objective 3223885.947526011, plan `898b95fd93c33414`, 21 rounds.

## Experiment 4A — original question, N3 vs N4 (complete)

```bash
python scripts/exp45_certify_cell.py cell --network N3 --experiment exp4a \
    --role treatment_N3 --contract-digest 0f62aeabfa341a98 --out <scratch>/N3.json
python scripts/exp45_certify_cell.py cell --network N4 --experiment exp4a \
    --role <canary-role> --contract-digest 0f62aeabfa341a98 --out <scratch>/N4_canary.json
python scripts/exp4a_admit.py                   # firewall compare -> outputs/exp4_addendum/DELTA43.json
python scripts/exp4a_diagnostics.py --network N3 --record outputs/exp4_addendum/N3.json \
    --out <scratch>/diag_N3.json
```
Expected: N3 2939912.5807124916 (plan `28135d0fa655e6e1`, 1 round), Δ43
+283,973.3668 (+9.659%). Note that `exp4a_admit.py` reads and writes the fixed
paths under `outputs/exp4_addendum/`. Do not run it on a production checkout
unless you intend to regenerate `DELTA43.json`.

## Experiment 5 — modeled resource frontier (`EXP5_MONOTONICITY_FAILURE`)

```bash
python scripts/exp5_freeze_contract.py          # refuses to overwrite the existing freeze
python scripts/exp5_run.py plan                 # canonical list + shards
python scripts/exp5_run.py shard --k 0 --of 2   # and --k 1 --of 2 in parallel; resumable
python scripts/exp5_run.py sentinels            # 4 reversed-order sentinels, must be bit-exact
python scripts/exp5_analyze.py                  # -> outputs/exp5/EXP5_ANALYSIS.json
python scripts/exp5_blocking.py                 # diagnostic only; all 32 UNDECIDABLE
```
~6.5 h wall on 2 cores. A single cell:
`python scripts/exp45_certify_cell.py cell --network N0 --experiment exp5 --hours 1.0 --peak 1.0 --role <role> --contract-digest 395ee3c960f51935 --out <scratch>/N0_J100.json`
→ 2945632.2349138106, plan `c4591ff0f6e2d8ad`.

## Experiment 6 — policy price on N0/N3 (closed, `EXP6_POLICY_FRONTIER_CERTIFIED`)

The commands below were verified against the argparse blocks and docstrings on
local `master` `7c08b128`, and against the shell scripts the run actually used
(`outputs/exp6/preflight/lane_*.sh`, `outputs/exp6/d35/run2.sh`). The contract is
`outputs/exp6/EXP6_CONTRACT.json` (sha256 `5bf1cb82ad8829a8…`), with Amendment 1
(`EXP6_CONTRACT_AMENDMENT_1.json`). Every freeze step **refuses to overwrite**.

```bash
# 1. Freeze (done; refuses to overwrite)
python scripts/exp6_freeze.py catalog      # -> outputs/exp6/EXP6_CONSTRAINT_CATALOG.json (digest e22f2c94c8f53475)
python scripts/exp6_freeze.py contract     # -> outputs/exp6/EXP6_CONTRACT.json

# 2. Preflight: default-path equivalence on the final source (bit-exact with EXP4N / Exp 4A / Exp 5)
python scripts/exp45_certify_cell.py cell --network N4 --experiment exp4a \
    --role exp6_final_default_equivalence --contract-digest exp6-preflight \
    --out outputs/exp6/preflight/final_equivalence/N4_J100_default.json
python scripts/exp45_certify_cell.py cell --network N3 --experiment exp4a \
    --role exp6_final_default_equivalence --contract-digest exp6-preflight \
    --out outputs/exp6/preflight/final_equivalence/N3_J100_default.json
python scripts/exp45_certify_cell.py cell --network N0 --experiment exp5 \
    --role exp6_final_default_equivalence --contract-digest exp6-preflight \
    --out outputs/exp6/preflight/final_equivalence/N0_J100_default.json

# 3. Preflight: D39 canaries (expect 3,207,566.4177 under J100 and 3,207,230.8312 under H110)
python scripts/exp6_cell.py --network N4 --no-policy --anchor-from outputs/exp5/cells/N4_H090.json \
    --anchor-label "D39 canary: Exp5 N4 H090 plan anchored under N4 J100 (EXP4N envelope)" \
    --role d39_preflight --out outputs/exp6/preflight/d39/N4_J100_anchor_H090.json
python scripts/exp6_cell.py --network N4 --no-policy --hours 1.1 --anchor-from outputs/exp5/cells/N4_H090.json \
    --anchor-label "D39 canary: Exp5 N4 H090 plan anchored under N4 H110" \
    --role d39_preflight --out outputs/exp6/preflight/d39/N4_H110_anchor_H090.json

# 4. D35 reach tests (R1/R2/R3/R4/R6 PASS on both networks)
python scripts/exp6_d35.py --network N3 --catalog-digest e22f2c94c8f53475 --out outputs/exp6/d35/N3.json
python scripts/exp6_d35.py --network N0 --catalog-digest e22f2c94c8f53475 --out outputs/exp6/d35/N0.json

# 5. Production: initial solves (2 shards, one fresh subprocess per cell, resumable)
python scripts/exp6_run.py plan
python scripts/exp6_run.py initial --k 0 --of 2
python scripts/exp6_run.py initial --k 1 --of 2
#    Amendment 1: an R1 cell whose start fails is proven empty, not guessed
python scripts/exp6_infeasible_cell.py --network N3 --cell R1_H20 \
    --catalog-digest e22f2c94c8f53475 --out outputs/exp6/initial/N3_R1_H20.json

# 6. Nesting closure, one writer per network (ledger: outputs/exp6/closure/closure_ledger_<net>.jsonl)
python scripts/exp6_run.py closure --network N0
python scripts/exp6_run.py closure --network N3

# 7. Reversed-order sentinels: N3 R4_C01, N0 R2_S10, N3 REF, N0 REF
python scripts/exp6_run.py sentinels

# 8. Gates, frontier, policy costs -> outputs/exp6/EXP6_ANALYSIS.json
python scripts/exp6_analyze.py            # exit 0 certified, 2 incomplete, 3 failed
python scripts/exp6_analyze.py --partial  # progress view only; never a closeout input
```

Spot-reproduce a single cell with
`python scripts/exp6_cell.py --network N0 --cell R2_S10 --role initial --catalog-digest e22f2c94c8f53475 --out <scratch>/N0_R2_S10.json`
and compare the objective, plan digest and rounds with
`outputs/exp6/initial/N0_R2_S10.json`. This is the same comparison the
sentinel makes.

**Not yet present:** a physical-fleet (blocking) diagnostic for Exp 6 cells
(the Exp 5 analogue is `scripts/exp5_blocking.py`), and a mechanical closeout
checker (the Exp 3 analogue is `scripts/exp3_verify_closure.py`).

## Experiment 7 — robustness of F1–F6 (closed 2026-10-04)

Verified against the argparse blocks on local `master` at the Exp 7 closeout,
at `5dc3f408`. The contract is `outputs/exp7/EXP7_CONTRACT.json` (sha256[:16]
`1263bedaebe6a45d`). Freeze and selection steps **refuse to overwrite**. Read
`experiments/exp7/EXPERIMENT7_CLOSEOUT.md` §1.1, as corrected by errata E14, for the post-freeze
script changes; none affects a number.

Freeze steps (done; do not re-run in the canonical checkout):

* `scripts/exp7_levels.py` is the level library (no CLI); the frozen levels
  are `outputs/exp7/EXP7_LEVELS.json`.
* `python scripts/exp7_busiest_routes.py --out <path>` wrote the A7 ranking
  `outputs/exp7/A7_ROUTE_RANKING.json`. It has no exists-guard: never point
  `--out` at the committed file.
* `python scripts/exp7_freeze.py --levels outputs/exp7/EXP7_LEVELS.json`
  froze the contract; it refuses if `EXP7_CONTRACT.json` already exists.

```bash
# Stage 1 -- fixed-plan evaluation (192 cells + 13 emptiness proofs)
python scripts/exp7_stage1.py registry          # 60-entry frozen registry
python scripts/exp7_stage1.py run --k 0 --of 2  # shard 0 (run k=1 in parallel)
python scripts/exp7_stage1.py run --k 1 --of 2
python scripts/exp7_stage1.py proofs            # N3 R1_H20 at A3/A7 levels
python scripts/exp7_stage1_analyze.py           # -> stage1/EXP7_STAGE1_ANALYSIS.json
python scripts/exp7_stage2_select.py            # freezes EXP7_STAGE2_SELECTION.json

# Stage 2 -- adaptive re-optimization in the selected dimensions (A5, A6)
python scripts/exp7_run.py initial --k 0 --of 2 # and --k 1 in parallel
python scripts/exp7_run.py closure --track F6 --network N0
python scripts/exp7_run.py closure --track F6 --network N3
python scripts/exp7_run.py closure --track F4 --network N0   # also N3, N4
python scripts/exp7_run.py sentinels
python scripts/exp7_analyze.py                  # -> EXP7_ANALYSIS.json (EXP7_STAGE2_REOPT_COMPLETE)
python scripts/exp7_closeout.py                 # -> EXP7_CLOSEOUT_TABLE.{json,md}
python scripts/exp7_f1_decision_space.py        # post hoc F1 addendum (reads only)
python scripts/canonical_results_v5.py          # registry v5 (refuses if it exists)
```

Closures resume from `closure_state_<net>.json` and hold an exclusive lock per
(track, network). Production evaluated 192 Stage 1 cells, then ran about 4
days of Stage 2 wall time on 2 cores (2026-09-30 to 2026-10-04).

**Single-cell spot check.** In a separate clone or `git worktree` (never the
canonical checkout): `python scripts/exp7_stage1.py cell --variant N0 --level
BASE`, then compare `rows` with the committed
`outputs/exp7/stage1/evals/N0/BASE.json` (`F1_BASELINE.unserved_demand`
10,423.684…). The command overwrites that file.

## Cross-experiment consistency check (read-only, minutes)
```bash
python scripts/n3_vs_n0_crossexp_check.py       # -> outputs/n3_vs_n0_crossexp_check.json
```

## Report figures

```
python scripts/make_report_figures.py            # all eight figures (a few minutes; the change map rebuilds the GTFS baseline)
python scripts/make_report_figures.py --skip-map # everything except the change map
python scripts/verify_report_claims.py           # also checks FIGURES_MANIFEST.json input hashes
```

Outputs go to `docs/report/figures/` as SVG, PNG and CSV. The change map's
aggregation rules are frozen in `config/change_map_aggregation.yaml`; it reads
the registered GTFS feed in `data/raw/cota_gtfs_static/`, which is not
committed.
