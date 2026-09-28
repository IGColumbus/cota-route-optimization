#!/usr/bin/env python3
"""EXP4N §9 — ranking recomputation under the FROZEN tie-break.

Runs only after §8 passes. The ordering key is imported from
cota_opt.exp4_inference rather than reimplemented here: the tie-break is
preregistered and its digest (0297e180cf30369d) is part of the record, so a
local reimplementation that happened to agree would still be the wrong artifact.

`lines_of` follows scripts/exp4_launch.py:635 -- the candidate's proposal line
list -- and `n_off_of` counts OFF route-periods in the certified plan, where
OFF is frequency.OFF = math.inf.

Nothing here decides whether a margin is meaningful. That is §7's noise band,
applied in §10.
"""
import json, math, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from cota_opt.exp4_inference import TIE_BREAK, TIE_BREAK_DIGEST, tie_break_key
from cota_opt.frequency import OFF

OUT = ROOT / "outputs" / "exp4_normalized"
PROD = OUT / "production_mr120"

C = json.loads((OUT / "EXP4N_PRODUCTION_CONTRACT.json").read_text())
ARCH = json.loads((OUT / "EXP4_ENDOGENOUS_CAP_ARCHIVE.json").read_text())
gate = json.loads((OUT / "EXP4N_INTEGRITY_GATE.json").read_text())
if gate["status"] != "PASS":
    sys.exit("REFUSING: §8 integrity gate did not pass. Ranking is gated on it.")

rows = [json.loads(p.read_text()) for p in sorted(PROD.glob("*.json"))]
assert len(rows) == 200

legacy_rank = {c["state_key"]: c["certified_rank"] for c in ARCH["candidates"]}
legacy_obj = {c["state_key"]: float(c.get("objective_EXACT", "nan"))
              for c in ARCH["candidates"] if "objective_EXACT" in c}


class _Shim:
    """Minimal stand-in carrying only what tie_break_key reads."""
    def __init__(self, r): self.r = r


def lines_of(s):  return list(s.r["lines"])
def n_off_of(s):  return sum(1 for v in s.r["plan_EXACT"].values() if v == OFF or v == math.inf)


order = sorted(
    (_Shim(r) for r in rows),
    key=lambda s: (float(s.r["objective_EXACT"]), tie_break_key(s, lines_of(s), n_off_of(s))))
ranked = [s.r for s in order]

# Did the tie-break ever have to decide anything?
objs = [float(r["objective_EXACT"]) for r in ranked]
ties = sum(1 for a, b in zip(objs, objs[1:]) if a == b)

lead = ranked[0]
second = ranked[1]
margin_abs = float(second["objective_EXACT"]) - float(lead["objective_EXACT"])
margin_pct = margin_abs / float(lead["objective_EXACT"]) * 100.0
spread_pct = (float(ranked[-1]["objective_EXACT"]) - float(lead["objective_EXACT"])) \
             / float(lead["objective_EXACT"]) * 100.0

# --- normalized vs legacy ordering -------------------------------------------
new_rank = {r["candidate_id"]: i + 1 for i, r in enumerate(ranked)}
pairs = [(legacy_rank[k], new_rank[k]) for k in new_rank if k in legacy_rank]
n = len(pairs)
mean_l = sum(p[0] for p in pairs) / n
mean_n = sum(p[1] for p in pairs) / n
cov = sum((a - mean_l) * (b - mean_n) for a, b in pairs)
sl = math.sqrt(sum((a - mean_l) ** 2 for a, b in pairs))
sn = math.sqrt(sum((b - mean_n) ** 2 for a, b in pairs))
spearman = cov / (sl * sn) if sl and sn else float("nan")

inverted = sum(1 for i in range(n) for j in range(i + 1, n)
               if (pairs[i][0] - pairs[j][0]) * (pairs[i][1] - pairs[j][1]) < 0)
total_pairs = n * (n - 1) // 2

legacy_leader_key = min(legacy_rank, key=lambda k: legacy_rank[k])
legacy_leader_new = new_rank.get(legacy_leader_key)
new_leader_legacy = legacy_rank.get(lead["candidate_id"])
moves = sorted(((legacy_rank[k] - new_rank[k]), k) for k in new_rank if k in legacy_rank)

art = {
 "artifact": "EXP4N_RANKING", "section": "§9",
 "gated_on": {"integrity_gate": gate["status"], "n_certified": len(rows)},
 "tie_break": list(TIE_BREAK), "tie_break_digest": TIE_BREAK_DIGEST,
 "tie_break_engaged": {"exact_objective_ties": ties,
                       "note": ("the tie-break decides nothing unless two certified "
                                "objectives are exactly equal")},
 "contract_digest": C["contract_digest"],
 "canonical_envelope_digest": C["canonical_envelope_digest"],
 "leader": {"candidate_id": lead["candidate_id"], "state_digest": lead["state_digest"],
            "objective_EXACT": repr(lead["objective_EXACT"]),
            "rounds": lead["rounds"], "converged": lead["converged"],
            "n_lines": len(lead["lines"]), "plan_digest": lead["plan_digest"],
            "legacy_certified_rank": legacy_rank.get(lead["candidate_id"])},
 "runner_up": {"candidate_id": second["candidate_id"],
               "state_digest": second["state_digest"],
               "objective_EXACT": repr(second["objective_EXACT"]),
               "legacy_certified_rank": legacy_rank.get(second["candidate_id"])},
 "margin_first_to_second": {"absolute": repr(margin_abs), "percent": margin_pct},
 "field_spread_percent": spread_pct,
 "normalized_vs_legacy": {
    "spearman_rank_correlation": spearman,
    "pairwise_orderings_inverted": inverted,
    "pairwise_orderings_total": total_pairs,
    "pairwise_inverted_fraction": inverted / total_pairs,
    "legacy_leader": {"candidate_id": legacy_leader_key,
                      "legacy_rank": legacy_rank[legacy_leader_key],
                      "normalized_rank": legacy_leader_new},
    "new_leader_legacy_rank": new_leader_legacy,
    "biggest_risers": [{"key": k[-12:], "legacy": legacy_rank[k], "normalized": new_rank[k]}
                       for _, k in moves[-5:][::-1]],
    "biggest_fallers": [{"key": k[-12:], "legacy": legacy_rank[k], "normalized": new_rank[k]}
                        for _, k in moves[:5]],
 },
 "ordering": [{"rank": i + 1, "key": r["state_digest"][:12],
               "objective_EXACT": repr(r["objective_EXACT"]),
               "rounds": r["rounds"], "n_lines": len(r["lines"]),
               "legacy_rank": legacy_rank.get(r["candidate_id"])}
              for i, r in enumerate(ranked)],
 "what_this_does_not_establish": (
   "That the first-to-second margin is meaningful. §7's noise band is D33-B's "
   "0.0018970%% and the rule is asymmetric: at or below the band is noise; above "
   "it is NOT thereby established, only not excluded. §10 applies it. Also "
   "unchanged: no fleet claim (the instrument returns UNDECIDABLE for every "
   "candidate), no global optimality (the (N,K)-block-local residual is "
   "unmeasured), and nothing about the 1800 uncertified proposals."),
}
(OUT / "EXP4N_RANKING.json").write_text(json.dumps(art, indent=1) + "\n")

print(f"§9 RANKING — 200 certified, frozen tie-break {TIE_BREAK_DIGEST}")
print(f"  exact-objective ties: {ties}  (tie-break engaged only if > 0)")
print(f"\n  LEADER   {lead['state_digest'][:12]}  obj {float(lead['objective_EXACT']):,.4f}  "
      f"{lead['rounds']}r  {len(lead['lines'])} lines   legacy rank {legacy_rank.get(lead['candidate_id'])}")
print(f"  2nd      {second['state_digest'][:12]}  obj {float(second['objective_EXACT']):,.4f}"
      f"   legacy rank {legacy_rank.get(second['candidate_id'])}")
print(f"  margin   {margin_abs:,.4f} absolute = {margin_pct:.6f}%")
print(f"  spread   first to last {spread_pct:.4f}%")
print(f"\n  normalized vs legacy:")
print(f"    spearman rank correlation   {spearman:+.4f}")
print(f"    pairwise orderings inverted {inverted:,} of {total_pairs:,} ({inverted/total_pairs*100:.1f}%)")
print(f"    legacy leader {legacy_leader_key[-12:]} (legacy rank 1) -> normalized rank {legacy_leader_new}")
print(f"    new leader was legacy rank {new_leader_legacy}")
print(f"\n  top 10 normalized:")
for i, r in enumerate(ranked[:10]):
    print(f"    {i+1:>3}  {r['state_digest'][:12]}  {float(r['objective_EXACT']):>15,.4f}  "
          f"{r['rounds']:>3}r   legacy {legacy_rank.get(r['candidate_id'])}")
print(f"\nwrote {OUT/'EXP4N_RANKING.json'}")
