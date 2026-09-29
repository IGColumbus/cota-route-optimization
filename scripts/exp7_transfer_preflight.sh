#!/bin/bash
# Experiment 7 production-path transfer / refusal / emptiness preflights.
# Sequential (one lane). Skip-if-exists per step. Evidence: outputs/exp7/preflight/transfer/
set -uo pipefail
cd "$(dirname "$0")/.."
D=outputs/exp7/preflight/transfer; mkdir -p "$D"
CAT=$(python3 -c "import json;print(json.load(open('outputs/exp6/EXP6_CONTRACT.json'))['catalog']['digest'])")
LF=outputs/exp7/preflight/reach_levels.json
ANCHOR=outputs/exp6/closure/N0_REF__from_R2_S25__aed848588abad24d.json
N4=outputs/exp6/preflight/d39/N4_J100_anchor_H090.json
run() { out=$1; shift; [ -f "$out" ] && { echo "skip $out"; return; }; echo "start $out $(date -u +%T)"; python scripts/exp7_cell.py "$@" --out "$out"; echo "end $out rc=$? $(date -u +%T)"; }
# 1. real cross-level transfer: Exp 6 closed N0 REF plan -> N0 REF at level R_LAM1
run $D/N0_REF_lvl_R_LAM1_anchor.json --network N0 --cell REF --role preflight_transfer --catalog-digest $CAT --level R_LAM1 --level-file $LF --anchor-from $ANCHOR --anchor-label "preflight: BASE closed REF -> R_LAM1"
# 2. certifier policy refusal: same plan (15 OFF) -> N0 R1_H20 at BASE
run $D/N0_R1_H20_BASE_anchor_refused.json --network N0 --cell R1_H20 --role preflight_refusal --catalog-digest $CAT --anchor-from $ANCHOR --anchor-label "preflight: must be refused"
# 3. certifier representation refusal: N4 plan -> N0 REF
run $D/N0_REF_BASE_anchor_from_N4.json --network N0 --cell REF --role preflight_refusal --catalog-digest $CAT --anchor-from $N4 --anchor-label "preflight: wrong network, must be refused"
# 4. emptiness re-proof of N3 R1_H20 under a non-BASE level
out=$D/N3_R1_H20_lvl_R_LAM1_emptiness.json
[ -f $out ] || python scripts/exp7_infeasible_cell.py --network N3 --cell R1_H20 --catalog-digest $CAT --level R_LAM1 --level-file $LF --out $out
# 5. greedy initial at the same level, for the transfer-vs-greedy comparison
run $D/N0_REF_lvl_R_LAM1_greedy.json --network N0 --cell REF --role preflight_initial --catalog-digest $CAT --level R_LAM1 --level-file $LF
python scripts/exp7_preflight.py transfer-verdict --anchor-record $ANCHOR
