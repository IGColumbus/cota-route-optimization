#!/usr/bin/env bash
# EXP4N round-cap calibration pilot.
# Reruns the candidates completed by the aborted MAX_ROUNDS=40 batch, from
# scratch, with the round CEILING raised to 200 and nothing else changed.
# Writes to outputs/exp4_normalized/calib_mr200/ so the aborted diagnostic
# results in certified/ are neither overwritten nor confused with these.
set -euo pipefail
cd "$(dirname "$0")/.."
HOURS="${1:-6}"
PIDF=outputs/exp4_normalized/exp4n_calib.pid
LOG=outputs/exp4_normalized/exp4n_calib.log
if [ -f "$PIDF" ] && ps -p "$(cat "$PIDF")" >/dev/null 2>&1; then
  echo "ALREADY RUNNING pid=$(cat "$PIDF")"; exit 0
fi
KEYS=$(python3 -c "
import json,glob
print(','.join(sorted(json.load(open(f))['candidate_id'] for f in glob.glob('outputs/exp4_normalized/certified/*.json'))))")
N=$(awk -F, '{print NF}' <<<"$KEYS")
echo "calibration set: $N candidates" | tee -a "$LOG"
setsid nohup python3 scripts/exp4n_launch.py \
  --max-hours "$HOURS" --max-rounds 200 --trajectory \
  --out-dir calib_mr200 --only "$KEYS" >> "$LOG" 2>&1 < /dev/null &
echo $! > "$PIDF"
echo "STARTED pid=$(cat "$PIDF") log=$LOG"
