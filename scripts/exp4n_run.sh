#!/usr/bin/env bash
set -u
cd "$(dirname "$0")/.."
PID_FILE=outputs/exp4_normalized/exp4n.pid
LOG=outputs/exp4_normalized/exp4n.log
if [ -f "$PID_FILE" ] && ps -p "$(cat "$PID_FILE")" >/dev/null 2>&1; then
  echo "ALREADY RUNNING pid=$(cat "$PID_FILE")"; exit 0
fi
nohup python3 scripts/exp4n_launch.py --max-hours "${1:-6}" ${2:+--only "$2"} >> "$LOG" 2>&1 &
echo $! > "$PID_FILE"
echo "STARTED pid=$(cat "$PID_FILE") log=$LOG"
