#!/usr/bin/env python3
"""Gate 4-8, N3 -> N4, pair by pair, from the diagnostics' OD dumps.
DIAGNOSTIC ONLY. Writes outputs/exp4_addendum/ABANDONMENT_N3_N4.json."""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path[:0] = [str(ROOT / "scripts")]
from exp45_certify_cell import atomic_write_json, utc
D = ROOT / "outputs/exp4_addendum"
o3 = json.loads((D / "diag_N3.od.json").read_text()); o4 = json.loads((D / "diag_N4.od.json").read_text())
out = {"status": "DIAGNOSTIC_ONLY", "direction": "N3 -> N4", "per_period": {}, "written_utc": utc()}
T = dict(flow=0.0, reachable_N3_not_N4=0.0, reachable_N4_not_N3=0.0, served_N3=0.0, served_N4=0.0,
         served_lost=0.0, served_gained=0.0, one_seat_N3=0.0, one_seat_N4=0.0)
for p in o3:
    a, b = o3[p], o4[p]
    k4 = {(o, d): j for j, (o, d) in enumerate(zip(b["o"], b["d"]))}
    assert len(k4) == len(a["o"])
    t = {k: 0.0 for k in T}
    for i, (o, d) in enumerate(zip(a["o"], a["d"])):
        j = k4[(o, d)]; f = a["flow"][i]; t["flow"] += f
        r3, r4 = a["reach"][i], b["reach"][j]
        t["reachable_N3_not_N4"] += f * (r3 and not r4); t["reachable_N4_not_N3"] += f * (r4 and not r3)
        s3, s4 = f * a["keep"][i], f * b["keep"][j]
        t["served_N3"] += s3; t["served_N4"] += s4
        t["served_lost"] += max(s3 - s4, 0.0); t["served_gained"] += max(s4 - s3, 0.0)
        t["one_seat_N3"] += s3 * (a["rides"][i] == 1); t["one_seat_N4"] += s4 * (b["rides"][j] == 1)
    s3s, s4s = set(a["stops_served"]), set(b["stops_served"])
    t.update(stops_served_N3=len(s3s), stops_served_N4=len(s4s),
             stops_losing_service=len(s3s - s4s), stops_gaining_service=len(s4s - s3s))
    out["per_period"][p] = t
    for k in T: T[k] += t[k]
out["totals"] = T
out["notes"] = ["flow is the model's OD demand (top-20,000 LODES-proxy pairs); 'served' applies the evaluator's retention curve",
                "one-seat = served flow whose chosen cached path has exactly one boarding (walk-only excluded)",
                "neighbourhood-level aggregation is NOT computed here (UNRESOLVED for gate 4-8)"]
atomic_write_json(D / "ABANDONMENT_N3_N4.json", out)
print(json.dumps({k: round(v, 1) for k, v in T.items()}))
