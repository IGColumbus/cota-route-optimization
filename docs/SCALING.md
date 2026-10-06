# Scaling

How to run the harness's certification work in parallel, for example on an
Ohio Supercomputer Center (OSC) cluster with Slurm.

**Status (2026-10-06):** the acceptance check passed on a small subset.
Four Experiment 5 cells were run as independent array tasks, two at a time,
and each is bit-identical to its committed serial record: exact objective,
plan digest, rounds, every fitness component and the round trajectory
(receipt `docs/research-record/reproductions/scaling_check_2026-10-06.json`).

The limits of that check:

* the four cells are N0 cells that converge in one round, the cheapest in the grid;
* it ran as a local stand-in for a job array (`scripts/scaling_check.py local`),
  not under Slurm, and the Slurm template below has not been executed;
* it ran on the same host class as the study.

The study results themselves were produced one cell per process in a two-core
container.

## Why it parallelizes

Certification work is a grid of **independent cells**:

* Exp 5: network × resource level;
* Exp 6: network × policy regime;
* Exp 7: level × network × decision space;
* Exp 1: seed × λ.

A cell reads the frozen contract, the shared caches and the raw inputs, and
writes exactly one output record. No cell reads another cell's output.

The exceptions are ordering gates and closure. Exp 5's shards wait for the N4
J100 reproduction cell, and the nesting closure of Exp 6/7 transfers plans
between cells over rounds. Run gates first and closure as its own step; both
are described below.

## Rules

1. **One cell, one task, one output file.** Runners name the output by cell
   (for example `outputs/exp5/cells/N0_H090.json`). Never let two tasks write
   one file. Exp 6/7 closure takes an exclusive lock
   per (track, network) for this reason.
2. **Resume by artifact existence.** A runner skips a cell whose record exists
   and parses, and stops rather than overwrite one that does not parse
   (`scripts/exp5_run.py`, `scripts/exp6_run.py`). A requeued or preempted
   task simply reruns its shard.
3. **Pin threads to 1 per process.** Threaded BLAS can change floating-point
   summation order, which breaks bit-exact checks. Parallelize across cells,
   never within one:
   ```bash
   export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONHASHSEED=0
   ```
4. **Share caches read-only.** Path sets, the baseline, zones, OD and the
   RAPTOR network are cached in `data/cache/<name>-<key>.pkl`. The key is
   `sha256({"name", "params"})[:16]`
   (`cota_opt.cache.key_of`). `params` carries every input that determines the
   artifact: the GTFS and LODES sha256 prefixes, radii, OD top-k, path-set
   settings, seed and waiting model. Build the caches once in a serial
   pre-step, then mount `data/cache/` read-only for the array. Two tasks
   missing the same key would both build it, and the last writer would win.
5. **Never mix caches across contracts.** A cache key encodes the inputs, not
   the contract. Use one `data/cache/` per frozen contract, or, for new work,
   one per configuration, so that a changed parameter never meets a stale file
   under a hand-chosen label. The keys are content-derived, so a changed input
   produces a new key rather than a silent hit.
6. **Isolate contracts.** A runner refuses to start a production cell before
   its contract file is frozen (for example `EXP5_CONTRACT.json`). Every
   record carries the contract digest and the `src/cota_opt` content digest,
   and the firewall refuses comparisons across them. Keep one checkout per
   contract. Do not edit code under a running array.
7. **Use registered inputs.** Run research scripts through
   `cota-opt run-script` so the frozen code reads `data/raw/` instead of the
   development container's upload folder (`docs/DATA_INTERFACES.md`).

## Slurm job array (OSC)

Exp 5 as the worked example. Its runner already shards with `--k/--of`.

```bash
#!/bin/bash
#SBATCH --job-name=cota-exp5
#SBATCH --array=0-15
#SBATCH --cpus-per-task=1
#SBATCH --mem=6G
#SBATCH --time=06:00:00
#SBATCH --output=logs/exp5_%a.out
set -euo pipefail
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONHASHSEED=0
cd "$SLURM_SUBMIT_DIR"                  # a checkout at the contract's commit, data/raw staged
source .venv/bin/activate               # built from requirements-lock.txt
cota-opt run-script scripts/exp5_run.py shard --k "$SLURM_ARRAY_TASK_ID" --of "$SLURM_ARRAY_TASK_COUNT"
```

Before the array:

1. Stage the inputs (`cota-opt data status` shows 5/5).
2. Build the caches serially once, for example by running the reproduction gate
   cell or `cota-opt reproduce exp1 --smoke` for the Exp 1 instance.
3. Run any ordering gate the runner waits for. For Exp 5, the N4 J100 cell
   must reproduce EXP4N first; shards that reach a later cell wait for its
   record.

After the array, run the experiment's sentinels and analysis serially, for
example `scripts/exp5_run.py sentinels` and then `scripts/exp5_analyze.py`.

## Acceptance check

`scripts/scaling_check.py` runs a subset of Exp 5 cells as array tasks and
compares each with the committed `outputs/exp5/cells/*.json`. Bit-exact
equality is expected on the same platform with threads pinned. A mismatch is a
finding to report, not to tune away.

```bash
# on one machine: P concurrent tasks (the recorded check used P=2)
python scripts/scaling_check.py local --out-dir <dir> --parallel 2
# under Slurm: one cell per array index (default subset has 4 cells)
#SBATCH --array=0-3
python scripts/scaling_check.py task --out-dir <dir>      # reads SLURM_ARRAY_TASK_ID
# afterwards, serially
python scripts/scaling_check.py compare --out-dir <dir> --receipt <file>
```

Each task needs about 250 MB of memory and 8–9 minutes on one core with the
caches built. `--cells` takes any comma-separated list of committed cell names
(for example `N4_J100`, recorded at about 35 minutes).
