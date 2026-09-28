set -u
cd /home/claude/columbus-transit-opt
D=outputs/exp6/preflight
python scripts/exp45_certify_cell.py cell --network N4 --experiment exp4a --role exp6_final_default_equivalence --contract-digest exp6-preflight --out $D/final_equivalence/N4_J100_default.json
python scripts/exp6_cell.py --network N4 --no-policy --hours 1.1 --anchor-from outputs/exp5/cells/N4_H090.json --anchor-label "D39 canary: Exp5 N4 H090 plan anchored under N4 H110" --role d39_preflight --out $D/d39/N4_H110_anchor_H090.json
python scripts/exp45_certify_cell.py cell --network N0 --experiment exp5 --role exp6_final_default_equivalence --contract-digest exp6-preflight --out $D/final_equivalence/N0_J100_default.json
