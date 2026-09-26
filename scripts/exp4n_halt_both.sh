#!/usr/bin/env bash
# Stop BOTH production workers when a halt condition has been declared.
#
# --stop-on-nonconvergence halts only the process that tripped it. With two
# workers, a §5 ceiling hit or a §6 calibration divergence in one leaves the
# other running past a condition that is supposed to stop THE RUN, which would
# produce results after the point where the protocol says to stop and report.
# This closes that gap.
#
# Termination is by PIDFILE ONLY (OPERATIONS 25: never kill by process-name
# pattern -- that rule was bought with lost work). Each pid is checked against
# /proc/<pid>/cmdline before any signal is sent, so a recycled pid cannot be
# killed by mistake.
set -uo pipefail
cd "$(dirname "$0")/.."
OUT=outputs/exp4_normalized
halted=""
for h in EXP4N_CONVERGENCE_FAILURE EXP4N_REPRODUCTION_FAILURE; do
  [ -f "$OUT/$h.json" ] && halted="$halted $h"
done
if [ -z "$halted" ]; then echo "no halt file present; nothing to do"; exit 0; fi
echo "HALT DECLARED:$halted"
for pf in "$OUT/exp4n_prod.pid" "$OUT/exp4n_prod_shardB.pid"; do
  [ -f "$pf" ] || continue
  p="$(cat "$pf" 2>/dev/null || true)"
  [ -n "$p" ] || continue
  if ! ps -p "$p" >/dev/null 2>&1; then echo "  $(basename "$pf"): pid $p already gone"; continue; fi
  if ! tr '\0' ' ' < "/proc/$p/cmdline" 2>/dev/null | grep -q "exp4n_launch.py"; then
    echo "  $(basename "$pf"): pid $p is NOT the launcher -- refusing to signal it"; continue
  fi
  kill -TERM "$p" && echo "  $(basename "$pf"): TERM sent to $p"
done
echo "Both workers signalled. DO NOT restart, DO NOT raise the ceiling, DO NOT rank."
echo "Report to Ian with the halt artifact."
