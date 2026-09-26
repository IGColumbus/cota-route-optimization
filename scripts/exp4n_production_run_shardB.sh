#!/usr/bin/env bash
# EXP4N production certification, SECOND WORKER (shard B: certified_rank 101-200).
#
# WHY A SEPARATE SCRIPT
# --------------------
# scripts/exp4n_production_run.sh drives the live worker A. OPERATIONS 24 freezes
# the code that can change a batch's numbers while that batch is in flight, and
# even though a runner script is not in that set, editing the file that launched
# the running process is the wrong shape of risk for zero benefit. This is a
# separate file with its own pidfile and its own log. Worker A is never touched.
#
# WHY THIS IS SAFE
# ----------------
# * Each candidate's result is a separate file, outputs/.../production_mr120/
#   <state_digest>.json, written once at the end of its own solve. There is no
#   shared output file and no shared mutable state on the exp4n path.
# * eval_cache.jsonl is written ONLY by the legacy scripts/exp4_launch.py. The
#   normalized launcher never touches it.
# * `todo` is computed as "keys without a result file", so overlapping work is
#   skipped rather than duplicated, and a genuine simultaneous start on one
#   candidate produces byte-identical output twice. Wasteful, never corrupting.
# * Worker A walks the whole ordering from position 1; this shard starts at 101.
#   They converge near the middle, where at most one candidate may be computed
#   twice. That is the accepted cost of not restarting A to give it a range.
#
# THE ONE REAL HAZARD, AND WHERE IT IS HANDLED
# --------------------------------------------
# The only shared write in the whole path is the halt file
# (EXP4N_CONVERGENCE_FAILURE.json / EXP4N_REPRODUCTION_FAILURE.json, written at
# scripts/exp4n_launch.py:170). --stop-on-nonconvergence halts only the process
# that tripped it, so a halt in one worker leaves the other running past a
# condition that is supposed to stop THE RUN. Stopping both is the roll's job,
# not this script's: see scripts/exp4n_halt_both.sh. This script refuses to
# start while a halt file exists, which covers the restart direction.
set -euo pipefail
cd "$(dirname "$0")/.."
HOURS="${1:-6}"
OUTDIR=production_mr120
KEYFILE=outputs/exp4_normalized/shardB_keys.txt
PIDF=outputs/exp4_normalized/exp4n_prod_shardB.pid
LOG=outputs/exp4_normalized/exp4n_prod_shardB.log
CONTRACT=outputs/exp4_normalized/EXP4N_PRODUCTION_CONTRACT.json
[ -f "$CONTRACT" ] || { echo "REFUSING: contract not frozen"; exit 1; }
[ -s "$KEYFILE" ] || { echo "REFUSING: $KEYFILE missing or empty"; exit 1; }
for h in EXP4N_CONVERGENCE_FAILURE EXP4N_REPRODUCTION_FAILURE; do
  if [ -f "outputs/exp4_normalized/$h.json" ]; then
    echo "REFUSING: $h.json present. The run halted on a stop condition and needs review."; exit 1
  fi
done
if [ -f "$PIDF" ] && ps -p "$(cat "$PIDF")" >/dev/null 2>&1; then
  echo "ALREADY RUNNING pid=$(cat "$PIDF")"; exit 0
fi
rm -f "$PIDF"
ONLY="$(cat "$KEYFILE")"
# Same pidfile discipline as the fixed worker-A runner: record $$ inside the
# process that then execs python, because exec preserves the pid and `$!` of a
# setsid does not reliably name the python process.
setsid nohup bash -c 'echo $$ > "$0"; exec python3 scripts/exp4n_launch.py \
  --max-hours "$1" --max-rounds 120 --trajectory \
  --out-dir "$2" --stop-on-nonconvergence \
  --calibration-dir calib_mr200 --only "$3"' "$PIDF" "$HOURS" "$OUTDIR" "$ONLY" >> "$LOG" 2>&1 < /dev/null &
for _ in $(seq 1 20); do [ -s "$PIDF" ] && break; sleep 1; done
RPID="$(cat "$PIDF" 2>/dev/null || true)"
if [ -z "$RPID" ] || ! ps -p "$RPID" >/dev/null 2>&1; then
  echo "FAILED TO START: no live pid in $PIDF -- see $LOG"; tail -5 "$LOG" 2>/dev/null; exit 1
fi
if ! tr '\0' ' ' < "/proc/$RPID/cmdline" 2>/dev/null | grep -q "exp4n_launch.py"; then
  echo "FAILED TO START: pid $RPID is not the launcher -- see $LOG"; exit 1
fi
echo "STARTED shardB pid=$RPID log=$LOG (pidfile verified against /proc/$RPID/cmdline)"
