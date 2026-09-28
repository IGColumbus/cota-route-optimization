set -u
cd /home/claude/columbus-transit-opt
D=outputs/exp6/preflight
while kill -0 $(cat $D/lane_b.pid) 2>/dev/null; do sleep 20; done
python scripts/exp6_cell.py --network N4 --no-policy --anchor-from outputs/exp5/cells/N4_H090.json --anchor-label "D39 canary: Exp5 N4 H090 plan anchored under N4 J100 (EXP4N envelope)" --role d39_preflight --out $D/d39/N4_J100_anchor_H090.json
