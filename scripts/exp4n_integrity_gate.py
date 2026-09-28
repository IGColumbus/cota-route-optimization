#!/usr/bin/env python3
"""EXP4N §8 integrity gate.

Runs AFTER 200/200 results exist and BEFORE anything is ranked. Every check is
made against the frozen contract, the frozen envelope artifact, the stored
calibration set, or the pre-loss archive -- never against a literal typed here.
That rule is not stylistic: a first draft of the production-contract freeze
compared the envelope against constants transcribed from a rounded log line and
manufactured a false mismatch in the last ULP on two periods.

Exit 0 only if every check passes. A non-zero exit means DO NOT RANK.
"""
import hashlib, json, pathlib, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
OUT = ROOT / "outputs" / "exp4_normalized"
PROD = OUT / "production_mr120"
CALIB = OUT / "calib_mr200"
ARCHIVE = OUT / "production_mr120_PRE_LOSS_DIAGNOSTIC"
PERIODS = ["early", "am_peak", "midday", "pm_peak", "evening", "owl"]

checks, fail = [], []


def check(name, got, want, detail=None):
    ok = got == want
    checks.append({"check": name, "ok": bool(ok), "got": got, "want": want,
                   **({"detail": detail} if detail else {})})
    if not ok:
        fail.append(f"{name}: got {got!r} want {want!r}")
    print(f"  [{'ok ' if ok else 'FAIL'}] {name}")
    if not ok:
        print(f"         got  {got!r}\n         want {want!r}")
    return ok


C = json.loads((OUT / "EXP4N_PRODUCTION_CONTRACT.json").read_text())
ENV = json.loads((OUT / "COMMON_RESOURCE_ENVELOPE.json").read_text())
ARCH = json.loads((OUT / "EXP4_ENDOGENOUS_CAP_ARCHIVE.json").read_text())
rows = [json.loads(p.read_text()) for p in sorted(PROD.glob("*.json"))]

print("§8.1 completeness")
keys = [c["state_key"] for c in sorted(ARCH["candidates"], key=lambda c: c["certified_rank"])]
check("candidate set is 200", len(keys), 200)
check("result files == 200", len(rows), 200)
ids = [r["candidate_id"] for r in rows]
check("no duplicate results", len(set(ids)), 200)
check("no missing candidates", sorted(set(keys) - set(ids)), [])
check("no extra results", sorted(set(ids) - set(keys)), [])
check("candidate-set digest == contract",
      hashlib.sha256("\n".join(sorted(keys)).encode()).hexdigest()[:16],
      C["candidate_set_digest"])

print("\n§8.2 every candidate certified, converged, feasible, error-free")
check("all converged is True", sorted({repr(r["converged"]) for r in rows}), ["True"])
check("no errors", [r["state_digest"][:12] for r in rows if r.get("error")], [])
check("all hours_feasible", sorted({repr(r["hours_feasible"]) for r in rows}), ["True"])
check("every record carries a guarantee string",
      all(isinstance(r.get("guarantee"), str) and r["guarantee"] for r in rows), True)
check("every record carries a round trajectory",
      all(r.get("round_trajectory") for r in rows), True)

print("\n§8.3 the ceiling — §5's hard stop")
at_ceiling = [r["state_digest"][:12] for r in rows if r["rounds"] == C["production_max_rounds"]]
unconverged_at_ceiling = [r["state_digest"][:12] for r in rows
                          if r["rounds"] == C["production_max_rounds"] and r["converged"] is not True]
check("no candidate reached the 120 ceiling", at_ceiling, [])
check("no candidate is rounds==ceiling AND converged==False", unconverged_at_ceiling, [])
rd = sorted(r["rounds"] for r in rows)
print(f"  ---- rounds min {rd[0]} median {rd[len(rd)//2]} p90 {rd[int(.9*len(rd))]} max {rd[-1]}"
      f"  (ceiling {C['production_max_rounds']}, headroom {C['production_max_rounds']-rd[-1]} rounds)")

print("\n§8.4 one parameterisation, equal to the frozen contract")
hours_cap_want = C["search"]["hours_cap"]
hours_cap_want = hours_cap_want if isinstance(hours_cap_want, str) else repr(hours_cap_want)
for field, want in (("max_rounds", C["production_max_rounds"]),
                    ("n_keys", C["search"]["n_keys"]),
                    ("k_rungs", C["search"]["k_rungs"]),
                    ("lam", C["search"]["lam"]),
                    ("seed", C["search"]["seed"]),
                    ("budget_tolerance", C["search"]["tolerance"]),
                    ("hours_cap", hours_cap_want),
                    ("common_envelope_digest", C["canonical_envelope_digest"]),
                    ("contract_digest", C["contract_digest"]),
                    ("cap_provenance", "common_reference_envelope_resolved_once")):
    got = {json.dumps(r.get(field), sort_keys=True) for r in rows}
    check(f"{field} uniform across 200 and == contract",
          (len(got), json.loads(got.copy().pop()) if len(got) == 1 else None),
          (1, want))

print("\n§8.5 the peak envelope, bit-exact, on every row")
frozen = {p: repr(float(ENV["peak_fleet_by_period"][p])) for p in PERIODS}
contract_env = {p: C["peak_vehicle_envelope"][p] for p in PERIODS}
check("contract envelope == frozen artifact (BIT-EXACT)", contract_env, frozen)
payloads = {json.dumps(r["peak_caps"], sort_keys=True) for r in rows}
check("all 200 share ONE peak envelope", len(payloads), 1)
if len(payloads) == 1:
    check("that envelope == frozen artifact (BIT-EXACT)", json.loads(payloads.pop()), frozen)

print("\n§8.6 distinctness — 200 geometries, 200 plans")
check("200 distinct state_digests", len({r["state_digest"] for r in rows}), 200)
check("200 distinct geometry_digests", len({r["geometry_digest"] for r in rows}), 200)
check("200 distinct plan_digests", len({r["plan_digest"] for r in rows}), 200)

print("\n§8.7 the optimizer was not touched")
src_digest = hashlib.sha256(b"".join(
    sorted(p.read_bytes() for p in sorted((ROOT / "src" / "cota_opt").rglob("*.py")))
)).hexdigest()[:16]
check("src/cota_opt content digest == contract", src_digest, C["src_cota_opt_content_digest"])
check("src/cota_opt clean in git",
      subprocess.run(["git", "status", "--porcelain", "src/cota_opt"], cwd=ROOT,
                     capture_output=True, text=True).stdout.strip(), "")
check("contract records src_cota_opt_modified False", C["src_cota_opt_modified"], False)

print("\n§8.8 the frozen tie-break is the legacy one")
from cota_opt.exp4_inference import TIE_BREAK, TIE_BREAK_DIGEST
check("TIE_BREAK constant unchanged", list(TIE_BREAK),
      ["fewer_active_lines", "fewer_off_route_periods", "lexicographic_line_ids"])
print(f"  ---- TIE_BREAK_DIGEST {TIE_BREAK_DIGEST}")

print("\n§8.9 §6 calibration controls — every one must reproduce exactly")
calib = {}
for p in CALIB.glob("*.json"):
    r = json.loads(p.read_text()); calib[r["candidate_id"]] = r
hit, repro, ctl = 0, 0, []
for r in rows:
    c = calib.get(r["candidate_id"])
    if not c:
        continue
    hit += 1
    same = (repr(r["objective_EXACT"]) == repr(c["objective_EXACT"])
            and r["rounds"] == c["rounds"] and r["converged"] == c["converged"]
            and r.get("plan_digest") == c.get("plan_digest"))
    repro += same
    ctl.append({"key": r["state_digest"][:12], "rounds": r["rounds"],
                "objective": repr(r["objective_EXACT"]), "reproduced": bool(same)})
check("calibration set size", len(calib), 21)
check("every calibration candidate in the 200 reproduced exactly", (hit, repro), (hit, hit))
print(f"  ---- {repro}/{hit} controls reproduced on objective, rounds, converged AND plan_digest")

print("\n§8.10 pre-loss archive cross-check (independent of §6)")
arch_hit = arch_ok = 0
AF = ["objective_EXACT", "rounds", "converged", "plan_digest", "state_digest",
      "geometry_digest", "block_enumerations", "combinations", "hours_used",
      "hours_feasible", "fitness_EXACT", "plan_EXACT", "common_envelope_digest",
      "contract_digest", "max_rounds", "peak_caps"]
for p in sorted(PROD.glob("*.json")):
    o = ARCHIVE / p.name
    if not o.exists():
        continue
    n = json.loads(p.read_text()); ov = json.loads(o.read_text())
    d = [f for f in AF if repr(n.get(f)) != repr(ov.get(f))]
    tn = [x["objective"] for x in n.get("round_trajectory") or []]
    to = [x["objective"] for x in ov.get("round_trajectory") or []]
    arch_hit += 1; arch_ok += (not d) and tn == to
check("every archived survivor reproduced bit-exactly", (arch_hit, arch_ok), (arch_hit, arch_hit))
print(f"  ---- {arch_ok}/{arch_hit} bit-exact across {len(AF)} fields + every per-round objective")

print("\n§8.11 nothing spliced in from another directory")
for other in ("certified", "calib_mr200", "envgate_mr120", "production_mr120_PRE_LOSS_DIAGNOSTIC"):
    d = OUT / other
    if not d.exists():
        continue
    shared = {p.name for p in d.glob("*.json")} & {p.name for p in PROD.glob("*.json")}
    # sharing a FILENAME is expected (same candidate); sharing an inode is not
    inodes = {(PROD / n).stat().st_ino for n in shared} & {(d / n).stat().st_ino for n in shared}
    check(f"no hardlink/symlink shared with {other}/", sorted(inodes), [])
    check(f"no symlinks in production_mr120/", [p.name for p in PROD.iterdir() if p.is_symlink()], [])

status = "PASS" if not fail else "FAIL"
art = {"artifact": "EXP4N_INTEGRITY_GATE", "section": "§8", "status": status,
       "contract_digest": C["contract_digest"],
       "canonical_envelope_digest": C["canonical_envelope_digest"],
       "candidate_set_digest": C["candidate_set_digest"],
       "src_cota_opt_content_digest": src_digest,
       "tie_break_digest": TIE_BREAK_DIGEST,
       "n_results": len(rows),
       "rounds": {"min": rd[0], "median": rd[len(rd)//2], "p90": rd[int(.9*len(rd))],
                  "max": rd[-1], "ceiling": C["production_max_rounds"],
                  "headroom_rounds": C["production_max_rounds"] - rd[-1],
                  "at_ceiling": len(at_ceiling)},
       "calibration_controls": {"in_set": len(calib), "encountered": hit,
                                "reproduced": repro, "detail": ctl},
       "pre_loss_archive_crosscheck": {"compared": arch_hit, "bit_exact": arch_ok,
                                       "fields": AF},
       "what_a_pass_licenses": ("§9 ranking recomputation under the frozen tie-break may "
                               "proceed. It does NOT by itself establish any margin as "
                               "meaningful — §7's noise band and the standing D36/D38 and "
                               "fleet caveats still govern every claim."),
       "checks": checks, "failures": fail}
(OUT / "EXP4N_INTEGRITY_GATE.json").write_text(json.dumps(art, indent=1, default=repr) + "\n")
print(f"\n§8 INTEGRITY GATE: {status}  ({len(checks)} checks, {len(fail)} failures)")
print(f"wrote {OUT / 'EXP4N_INTEGRITY_GATE.json'}")
sys.exit(0 if not fail else 1)
