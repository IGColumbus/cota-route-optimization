set -u
cd /home/claude/columbus-transit-opt
D=outputs/exp6/preflight
python scripts/exp6_cell.py --network N4 --no-policy --anchor-from outputs/exp5/cells/N4_H090.json --anchor-label "D39 canary: Exp5 N4 H090 plan anchored under N4 J100 (EXP4N envelope)" --role d39_preflight --out $D/d39/N4_J100_anchor_H090.json
python scripts/exp45_certify_cell.py cell --network N3 --experiment exp4a --role exp6_final_default_equivalence --contract-digest exp6-preflight --out $D/final_equivalence/N3_J100_default.json
