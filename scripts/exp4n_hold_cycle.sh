#!/usr/bin/env bash
# One hold cycle: sleep, then keep BOTH workers alive, then print one line.
#
# Exists because a hold that only reports is not a keeper. Both workers exit
# cleanly at their --max-hours shard bound (routine, not a failure), and without
# a restart in the same loop the run sits dead until the next backstop beat.
# That is the 2-hour hole that cost ~38h of wall clock on 25-26 Sep, in miniature.
set -uo pipefail
# Ref-lock sweep is the caller's job on the durable side, not here, but record
# why it must be depth-unlimited: on 27 Sep a failed `gc` task on the durable
# machine left a .lock on ALL 16 refs, including
# .git/refs/remotes/cloud/exp3-clean.lock at depth 4. A cleanup written with
# `find .git -maxdepth 2` missed every one of them, and the NEXT fetch failed
# with "unable to update local ref" -- caught only because the checkpoint
# verifies the pointer instead of trusting the fetch's exit status. The gc error
# had been dismissed as cosmetic one checkpoint earlier. It was not.
# Fix applied on the durable side: maintenance.auto=false, gc.auto=0,
# gc.autoDetach=false, fetch.writeCommitGraph=false -- git cannot finish
# maintenance in a VM that cannot unlink, so it must not start.

cd "$(dirname "$0")/.."
OUT=outputs/exp4_normalized
SLEEP_CYCLES="${1:-9}"
# DURABLE-SIDE FETCH: always pass --no-write-fetch-head. On 28 Sep at 05:41 a
# fetch into the durable repo failed with "cannot open .git/FETCH_HEAD:
# Permission denied" -- a zero-byte FETCH_HEAD the VM could not rewrite, most
# likely held by OneDrive sync on the Windows side. The fetch printed "verified"
# for the bundle and then did NOT move the ref; the pointer check caught it.
# --no-write-fetch-head skips that file entirely and the same fetch succeeded.
# That is the THIRD silent transport failure in two days (ref locks, the staging
# mount, this), and all three reported success or said nothing. The pointer
# comparison is the only reason none of them cost a result.

for _ in $(seq 1 "$SLEEP_CYCLES"); do sleep 58; done

note=""
for h in EXP4N_CONVERGENCE_FAILURE EXP4N_REPRODUCTION_FAILURE; do
  if [ -f "$OUT/$h.json" ]; then
    echo "*** HALT ARTIFACT PRESENT: $h — stopping both workers ***"
    bash scripts/exp4n_halt_both.sh
    exit 3
  fi
done

a="$(cat "$OUT/exp4n_prod.pid" 2>/dev/null || true)"
if [ -z "$a" ] || ! ps -p "$a" >/dev/null 2>&1; then
  rm -f "$OUT/exp4n_prod.pid"
  note="$note A-restarted:$(bash scripts/exp4n_production_run.sh 6 2>&1 | tail -1 | sed 's/ .*pid=/pid/;s/ log=.*//')"
fi
b="$(cat "$OUT/exp4n_prod_shardB.pid" 2>/dev/null || true)"
if [ -z "$b" ] || ! ps -p "$b" >/dev/null 2>&1; then
  rm -f "$OUT/exp4n_prod_shardB.pid"
  note="$note B-restarted:$(bash scripts/exp4n_production_run_shardB.sh 6 2>&1 | tail -1 | sed 's/ .*pid=/pid/;s/ log=.*//')"
fi

printf "%s n=%s A=%s B=%s%s\n" "$(date -u +%H:%M)" \
  "$(ls -1 "$OUT"/production_mr120/*.json 2>/dev/null | wc -l)" \
  "$(ps -o time= -p "$(cat "$OUT/exp4n_prod.pid" 2>/dev/null)" 2>/dev/null || echo DEAD)" \
  "$(ps -o time= -p "$(cat "$OUT/exp4n_prod_shardB.pid" 2>/dev/null)" 2>/dev/null || echo DEAD)" \
  "$note"
