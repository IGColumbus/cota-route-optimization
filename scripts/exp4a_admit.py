#!/usr/bin/env python3
"""Exp 4A: admit N3 and N4 under EXP4A_MATCHED and compare with the canonical
firewall (`firewall.compare`). Control = N3, treatment = N4, so the firewall's
effect = obj(N4) - obj(N3) = Delta43. Writes outputs/exp4_addendum/DELTA43.json.
N4's receipt is built from the canary record, which is bit-identical to the
authoritative EXP4N production record (checked here again)."""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "scripts")]
import exp45_contracts as C
from exp45_certify_cell import atomic_write_json, utc
from cota_opt.firewall import admit, compare
from cota_opt.firewall.observation import Inadmissible

D = ROOT / "outputs/exp4_addendum"
n3 = json.loads((D / "N3.json").read_text())
n4 = json.loads((D / "N4_canary.json").read_text())
e = json.loads((ROOT / "outputs/exp4_normalized/production_mr120/cc40b4f4aea3aa05.json").read_text())
assert n4["outcome"]["objective_EXACT"] == repr(e["objective_EXACT"])
assert n4["outcome"]["plan_digest"] == e["plan_digest"]
con = C.EXP4A_MATCHED
out = {"contract": C.contracts_payload()["EXP4A_MATCHED"], "written_utc": utc()}
rc = {}
for lab, rec in (("N3", n3), ("N4", n4)):
    assert rec["contract_digest"] == con.digest
    r = C.receipt_for(rec, con)
    a = admit(r, con)
    rc[lab] = r
    out[f"admission_{lab}"] = ("ADMITTED" if not isinstance(a, Inadmissible)
                               else {"INADMISSIBLE": list(a.reasons)})
res = compare(rc["N3"], rc["N4"], con)
if hasattr(res, "as_dict") and res.__class__.__name__ == "ComparisonResult":
    out["comparison"] = res.as_dict()
    out["status"] = "ADMITTED"
else:
    out["comparison"] = {"INADMISSIBLE": repr(res)[:4000]}
    out["status"] = "INADMISSIBLE"
f3, f4 = n3["outcome"]["fitness_EXACT"], n4["outcome"]["fitness_EXACT"]
o3, o4 = float(n3["outcome"]["objective_EXACT"]), float(n4["outcome"]["objective_EXACT"])
out["delta43"] = {
    "definition": "obj(N4) - obj(N3); positive = N4 worse (objective is minimized)",
    "objective_N3": repr(o3), "objective_N4": repr(o4),
    "delta": repr(o4 - o3), "delta_pct_of_N3": 100 * (o4 - o3) / o3,
    "components": {k: {"N3": f3[k], "N4": f4[k], "N4_minus_N3": repr(float(f4[k]) - float(f3[k]))}
                   for k in f3},
    "peak_proxy_by_period": {"N3": n3["resource"]["used"]["peak_proxy_by_period"],
                             "N4": n4["resource"]["used"]["peak_proxy_by_period"]},
    "d33b_band_pct": 0.0018970,
    "ratio_to_band": abs(100 * (o4 - o3) / o3) / 0.0018970,
}
atomic_write_json(D / "DELTA43.json", out)
print(out["status"], out["admission_N3"], out["admission_N4"], out["delta43"]["delta"], out["delta43"]["delta_pct_of_N3"])
if out["status"] != "ADMITTED": print(out["comparison"])
