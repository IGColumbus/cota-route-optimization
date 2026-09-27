#!/usr/bin/env bash
# Durable export for EXP4N.
#
# WHY THIS EXISTS
# ---------------
# The EXP4N production run lost candidates 25-153 (129 certified results, ~30h
# of compute) when the ephemeral container disk was reclaimed on 2026-09-24.
# Checkpoints had been committed to a git repo INSIDE that container and treated
# as satisfying the requirement to "commit durable intermediate results /
# checkpoints periodically enough that container loss cannot destroy substantial
# completed work". A commit to a reclaimable disk is not a durable checkpoint.
# Only one genuine export had ever happened: a single bundle on 2026-09-23,
# which predated every production result but the first 24.
#
# THE RULE THIS ENFORCES
# ----------------------
# The authoritative pointer to "what is safe" lives on the DURABLE side, never
# here. This script takes the base commit as an argument, read from the durable
# repo immediately before the call. It never trusts local state to decide what
# has already been exported, because local state dies with the disk it describes.
#
# Usage:
#   exp4n_durable_export.sh <base_commit_present_on_the_durable_side>
#   exp4n_durable_export.sh --full        # no usable base; export everything
#
# Writes the bundle to /mnt/user-data/outputs/ so it can be committed to the
# durable side, and verifies it before claiming success.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
# DEST fallback (added 27 Sep, 18:47 UTC). /mnt/user-data/outputs is an rclone
# filestore mount and it began returning "Input/output error" on every write
# mid-run, with 1.0P reported free -- a transport failure, not a disk-space one.
# device_commit_files accepts EITHER a stagedPath under that mount OR a fileUuid
# from SendUserFile, so a broken mount degrades the checkpoint path but does not
# break it. Write where we can, and let the caller choose the transport.
DEST="/mnt/user-data/outputs"
if ! ( mkdir -p "$DEST" 2>/dev/null && touch "$DEST/.probe" 2>/dev/null ); then
    DEST="$HOME/exports"
    mkdir -p "$DEST"
    echo "NOTE: /mnt/user-data/outputs is unwritable; writing to $DEST instead." >&2
    echo "NOTE: commit it with SendUserFile -> device_commit_files fileUuid." >&2
else
    rm -f "$DEST/.probe"
fi

BRANCH="$(git rev-parse --abbrev-ref HEAD)"
HEAD_SHA="$(git rev-parse HEAD)"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"

if [ "${1:-}" = "--full" ]; then
    MODE="full"
    OUT="$DEST/cota-${BRANCH}-FULL-${STAMP}.bundle"
    git bundle create "$OUT" "$BRANCH"
else
    BASE="${1:?need a base commit present on the durable side, or --full}"
    if ! git cat-file -e "${BASE}^{commit}" 2>/dev/null; then
        echo "FATAL: base $BASE is not in this repository. Re-run with --full." >&2
        exit 2
    fi
    if [ "$(git rev-parse "$BASE")" = "$HEAD_SHA" ]; then
        echo "nothing to export: durable side is already at HEAD ($(git rev-parse --short=9 HEAD))"
        exit 3
    fi
    if ! git merge-base --is-ancestor "$BASE" HEAD; then
        echo "FATAL: $BASE is not an ancestor of HEAD; an incremental bundle would not apply." >&2
        exit 2
    fi
    MODE="incremental"
    OUT="$DEST/cota-${BRANCH}-$(git rev-parse --short=9 "$BASE")..$(git rev-parse --short=9 HEAD)-${STAMP}.bundle"
    git bundle create "$OUT" "${BASE}..HEAD" "$BRANCH"
fi

# Verify before claiming success. An unverified bundle is not a checkpoint.
git bundle verify "$OUT" >/dev/null

N_COMMITS=$([ "$MODE" = full ] && git rev-list --count "$BRANCH" || git rev-list --count "${1}..HEAD")
cat <<EOF
mode        $MODE
branch      $BRANCH
head        $HEAD_SHA
commits     $N_COMMITS
bundle      $OUT
bytes       $(stat -c%s "$OUT")
verified    yes

NEXT (must be done by the agent, this script cannot do it):
  1. device_commit_files the bundle to the durable side
  2. git fetch it into the durable repo so the OBJECTS land in its object store,
     not just a loose file, and move its cloud/<branch> ref to $HEAD_SHA
  3. re-read the durable repo's cloud/<branch> ref and confirm it is $HEAD_SHA
     A bundle sitting unfetched next to a repo is a file, not a checkpoint.
EOF
