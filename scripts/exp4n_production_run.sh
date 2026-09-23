#!/usr/bin/env bash
# EXP4N production certification: all 200 candidates, MAX_ROUNDS=120.
# Contract frozen in outputs/exp4_normalized/EXP4N_PRODUCTION_CONTRACT.json.
# Resumes by file existence. Halts on a ceiling hit (§5) or a calibration
# divergence (§6).
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
setsid nohup python3 scripts/exp4n_launch.py \
  --max-hours "$HOURS" --max-rounds 120 --trajectory \
  --out-dir "$OUTDIR" --stop-on-nonconvergence \
  --calibration-dir calib_mr200 >> "$LOG" 2>&1 < /dev/null &
echo $! > "$PIDF"
echo "STARTED pid=$(cat "$PIDF") log=$LOG"
