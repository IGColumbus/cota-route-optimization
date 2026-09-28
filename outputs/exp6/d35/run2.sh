set -u
cd /home/claude/columbus-transit-opt
python scripts/exp6_d35.py --network N3 --catalog-digest e22f2c94c8f53475 --out outputs/exp6/d35/N3.json
python scripts/exp6_d35.py --network N0 --catalog-digest e22f2c94c8f53475 --out outputs/exp6/d35/N0.json
