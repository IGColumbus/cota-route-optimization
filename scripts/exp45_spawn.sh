#!/bin/bash
# exp45_spawn.sh NAME DIR -- ARGS...   : detached run with pidfile + log (OPERATIONS pidfile rule)
set -euo pipefail
name=$1; dir=$2; shift 2; [ "$1" = "--" ] && shift
mkdir -p "$dir"
nohup python "$@" > "$dir/$name.log" 2>&1 < /dev/null &
echo $! > "$dir/$name.pid"
echo "$name pid $(cat "$dir/$name.pid")"
