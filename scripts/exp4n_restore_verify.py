#!/usr/bin/env python3
"""EXP4N restore verification.

Establishes that the working tree rebuilt from the surviving bundle is a valid
substrate for resuming the production run under the ALREADY FROZEN contract.

Every comparison is made against the frozen artifact or the surviving records.
Nothing is compared against a hand-typed literal: a previous draft of the
contract freeze compared against constants transcribed from a rounded log line
and manufactured a false mismatch in the last ULP on two periods.  The same
trap caught the first draft of this script's src-digest check, which used its
own walk instead of the frozen script's algorithm and reported a mismatch that
did not exist.  Reuse the original algorithm, never a re-derivation.
"""
import hashlib, json, pathlib, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "exp4_normalized"
PERIODS = ["early", "am_peak", "midday", "pm_peak", "evening", "owl"]

checks, fail = [], []


def check(name, got, want):
    ok = got == want
    checks.append({"check": name, "ok": ok, "got": got, "want": want})
    if not ok:
        fail.append(f"{name}: got {got!r} want {want!r}")
    print(f"  [{'ok ' if ok else 'FAIL'}] {name}")
    if not ok:
        print(f"         got  {got!r}\n         want {want!r}")
    return ok


C = json.loads((OUT / "EXP4N_PRODUCTION_CONTRACT.json").read_text())
env = json.loads((OUT / "COMMON_RESOURCE_ENVELOPE.json").read_text())
arch = json.loads((OUT / "EXP4_ENDOGENOUS_CAP_ARCHIVE.json").read_text())

print("frozen contract is present and readable")
check("contract status FROZEN", C["status"], "FROZEN")
check("production_max_rounds", C["production_max_rounds"], 120)

print("\ncandidate inputs")
keys = [c["state_key"] for c in sorted(arch["candidates"], key=lambda c: c["certified_rank"])]
check("candidate count", len(keys), 200)
check("candidate ids unique", len(set(keys)), 200)
check("candidate-set digest == contract",
      hashlib.sha256("\n".join(sorted(keys)).encode()).hexdigest()[:16],
      C["candidate_set_digest"])
check("legacy proposals.json present", (ROOT / "outputs/exp4/run/proposals.json").exists(), True)
check("legacy eval_cache.jsonl present", (ROOT / "outputs/exp4/run/eval_cache.jsonl").exists(), True)

print("\nsource tree (frozen-script algorithm, not a re-derivation)")
src_digest = hashlib.sha256(b"".join(
    sorted(p.read_bytes() for p in sorted((ROOT / "src" / "cota_opt").rglob("*.py")))
)).hexdigest()[:16]
check("src/cota_opt content digest == contract", src_digest, C["src_cota_opt_content_digest"])
dirty = subprocess.run(["git", "status", "--porcelain", "src/cota_opt"], cwd=ROOT,
                       capture_output=True, text=True).stdout.strip()
check("src/cota_opt clean (unmodified)", dirty, "")
contract_commit = C["source_tree_git_commit"]
present = subprocess.run(["git", "cat-file", "-e", contract_commit + "^{commit}"],
                         cwd=ROOT, capture_output=True).returncode == 0
check("contract source commit present in restored history", present, True)
if present:
    diff = subprocess.run(["git", "diff", "--name-only", contract_commit, "HEAD", "--", "src/cota_opt"],
                          cwd=ROOT, capture_output=True, text=True).stdout.strip()
    check("src/cota_opt unchanged contract-commit..HEAD", diff, "")

print("\ncanonical envelope, bit-exact against the frozen artifact")
frozen_peak = {p: float(env["peak_fleet_by_period"][p]) for p in PERIODS}
contract_peak = {p: float(C["peak_vehicle_envelope"][p]) for p in PERIODS}
check("contract envelope == COMMON_RESOURCE_ENVELOPE (BIT-EXACT)", contract_peak, frozen_peak)
check("contract envelope reprs == frozen reprs (BIT-EXACT)",
      {p: repr(contract_peak[p]) for p in PERIODS},
      {p: repr(frozen_peak[p]) for p in PERIODS})

print("\nsurviving audit evidence")
for rel, n in (("certified", 21), ("calib_mr200", 21)):
    check(f"{rel}/ has {n} results", len(list((OUT / rel).glob("*.json"))), n)
for rel in ("EXP4N_ROUND_CAP_CALIBRATION.json", "EXP4N_ABORTED_ROUND_CAP_INVALID.json",
            "EXP4N_PILOT_GATE.json"):
    check(f"{rel} present", (OUT / rel).exists(), True)

print("\nsurviving production results")
prod = sorted((OUT / "production_mr120").glob("*.json"))
rows = [json.loads(p.read_text()) for p in prod]
check("production results recovered", len(rows), 24)
for field, want in (("max_rounds", 120), ("n_keys", 8), ("k_rungs", 3), ("lam", 2.0),
                    ("seed", 20260825), ("budget_tolerance", 0.0),
                    ("common_envelope_digest", C["canonical_envelope_digest"]),
                    ("contract_digest", C["contract_digest"]),
                    ("hours_cap", C["search"]["hours_cap"] if isinstance(C["search"]["hours_cap"], str)
                     else repr(C["search"]["hours_cap"])),
                    ("cap_provenance", "common_reference_envelope_resolved_once")):
    got = {json.dumps(r.get(field), sort_keys=True) for r in rows}
    check(f"survivors uniform {field} == contract", (len(got) == 1, json.loads(got.copy().pop())),
          (True, want))
check("survivors all converged", {r["converged"] for r in rows}, {True})
check("survivors none at the 120 ceiling", sum(1 for r in rows if r["rounds"] == 120), 0)
peaks = {json.dumps(r["peak_caps"], sort_keys=True) for r in rows}
check("survivors share one peak envelope", len(peaks), 1)
check("survivor envelope == contract (BIT-EXACT)",
      json.loads(peaks.copy().pop()), {p: repr(frozen_peak[p]) for p in PERIODS})
check("survivors carry round trajectories", all(r.get("round_trajectory") for r in rows), True)

order = {k: i + 1 for i, k in enumerate(keys)}
pos = sorted(order[r["candidate_id"]] for r in rows)
check("survivors are the contiguous certified_rank prefix 1..24", pos, list(range(1, 25)))

rounds = [r["rounds"] for r in rows]
summary = {"n": len(rows), "rounds_min": min(rounds), "rounds_max": max(rounds),
           "rounds_mean": sum(rounds) / len(rounds), "at_ceiling": 0,
           "all_converged": True}

print("\nlosses (stated, not inferred)")
lost = {"last_reported_progress": "153/200",
        "results_recovered": len(rows),
        "results_lost": 153 - len(rows),
        "lost_checkpoint_commits": ["f69073b3", "65838b9f", "dd06abb0", "ac56813a"],
        "surviving_tip": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                        capture_output=True, text=True).stdout.strip()}

out = {"artifact": "EXP4N_RESTORE_VERIFICATION",
       "status": "PASS" if not fail else "FAIL",
       "purpose": ("Establish that the tree rebuilt after total loss of the ephemeral "
                   "container disk is a valid substrate for resuming the EXP4N production "
                   "run under the already-frozen contract. This verification does NOT "
                   "authorize a relaunch and does NOT interpret any partial result."),
       "restored_from": "cota-exp3-clean-20260923-1825.bundle (tip 4de29b8e), the only durable export of the run",
       "contract_digest": C["contract_digest"],
       "canonical_envelope_digest": C["canonical_envelope_digest"],
       "candidate_set_digest": C["candidate_set_digest"],
       "src_cota_opt_content_digest": src_digest,
       "surviving_production_summary": summary,
       "loss": lost,
       "checks": checks,
       "failures": fail}
def _j(o):
    if isinstance(o, (set, frozenset)):
        return sorted(o, key=repr)
    if isinstance(o, tuple):
        return list(o)
    return repr(o)

(OUT / "EXP4N_RESTORE_VERIFICATION.json").write_text(
    json.dumps(out, indent=1, default=_j) + "\n")

print(f"\n{'PASS' if not fail else 'FAIL'}  {len(checks)} checks, {len(fail)} failures")
print(f"wrote {OUT / 'EXP4N_RESTORE_VERIFICATION.json'}")
sys.exit(0 if not fail else 1)
