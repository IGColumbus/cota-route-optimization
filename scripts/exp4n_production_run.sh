#!/usr/bin/env bash
# EXP4N production certification: all 200 candidates, MAX_ROUNDS=120.
# Contract frozen in outputs/exp4_normalized/EXP4N_PRODUCTION_CONTRACT.json.
# Resumes by file existence. Halts on a ceiling hit (§5) or a calibration
# divergence (§6).
#
# PIDFILE CORRECTNESS (fixed 2026-09-25, before the post-loss relaunch)
# --------------------------------------------------------------------
# The previous version wrote `$!` -- the pid of `setsid` -- into the pidfile.
# Whether that equals the python pid depends on whether setsid needs to fork,
# which depends on whether the caller is already a process-group leader. It is
# NOT stable across shell contexts: measured 843 in the pidfile against 845 for
# the real python process, while the earlier run happened to record the right
# one. A keeper that checks `ps -p "$(cat pidfile)"` therefore reads a healthy
# run as dead, clears the pidfile and starts a SECOND runner over the same
# output directory.
#
# The fix writes the pid from inside the process that becomes python: bash -c
# records $$ and then `exec`s, and exec preserves the pid. No process-name
# pattern is involved, so OPERATIONS 25 still holds -- the pidfile remains the
# only identity, it is now simply the correct one.
set -euo pipefail
cd "$(dirname "$0")/.."
HOURS="${1:-6}"
OUTDIR=production_mr120
PIDF=outputs/exp4_normalized/exp4n_prod.pid
LOG=outputs/exp4_normalized/exp4n_prod.log
CONTRACT=outputs/exp4_normalized/EXP4N_PRODUCTION_CONTRACT.json
[ -f "$CONTRACT" ] || { echo "REFUSING: contract not frozen. Run scripts/exp4n_freeze_production_contract.py"; exit 1; }
for h in EXP4N_CONVERGENCE_FAILURE EXP4N_REPRODUCTION_FAILURE; do
  if [ -f "outputs/exp4_normalized/$h.json" ]; then
    echo "REFUSING: $h.json present. The run halted on a stop condition and needs review."; exit 1
  fi
done
if [ -f "$PIDF" ] && ps -p "$(cat "$PIDF")" >/dev/null 2>&1; then
  echo "ALREADY RUNNING pid=$(cat "$PIDF")"; exit 0
fi
rm -f "$PIDF"
setsid nohup bash -c 'echo $$ > "$0"; exec python3 scripts/exp4n_launch.py \
  --max-hours "$1" --max-rounds 120 --trajectory \
  --out-dir "$2" --stop-on-nonconvergence \
  --calibration-dir calib_mr200' "$PIDF" "$HOURS" "$OUTDIR" >> "$LOG" 2>&1 < /dev/null &
# Do not report STARTED on the strength of having launched something: verify the
# pidfile names a live process whose command line is this launcher.
for _ in $(seq 1 20); do [ -s "$PIDF" ] && break; sleep 1; done
RPID="$(cat "$PIDF" 2>/dev/null || true)"
if [ -z "$RPID" ] || ! ps -p "$RPID" >/dev/null 2>&1; then
  echo "FAILED TO START: no live pid in $PIDF -- see $LOG"; tail -5 "$LOG" 2>/dev/null; exit 1
fi
if ! tr '\0' ' ' < "/proc/$RPID/cmdline" 2>/dev/null | grep -q "exp4n_launch.py"; then
  echo "FAILED TO START: pid $RPID is not the launcher -- see $LOG"; exit 1
fi
echo "STARTED pid=$RPID log=$LOG (pidfile verified against /proc/$RPID/cmdline)"
