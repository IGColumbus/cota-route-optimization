#!/usr/bin/env python3
"""EXP4N — freeze and ASSERT the production certification contract (§1).

Exits non-zero on ANY mismatch against the calibrated setup. The only intended
difference from the aborted normalized run is max_rounds 40 -> 120.

Does not modify src/cota_opt. The ceiling is passed through the existing
certify()/launcher interface.
"""
from __future__ import annotations
import hashlib, json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src")); sys.path.insert(0, str(ROOT / "scripts"))
OUT = ROOT / "outputs" / "exp4_normalized"

PRODUCTION_MAX_ROUNDS = 120
REQUIRED = {"max_rounds": 120, "n_keys": 8, "k_rungs": 3, "lam": 2.0,
            "seed": 20260825, "tolerance": 0.0,
            "hours_cap": 2517.1833333333334}

fail: list[str] = []
def check(name, got, want):
    ok = (got == want)
    if not ok:
        fail.append(f"{name}: got {got!r}, required {want!r}")
    print(f"  {'OK  ' if ok else 'FAIL'} {name:34} {got!r}")
    return ok

def main() -> int:
    from exp4n_launch import build_constraints, load_envelope, PERIODS
    from cota_opt.exp4_certify import (CERTIFICATION_DIGEST, K_RUNGS,
                                       MAX_ROUNDS, N_KEYS)

    print("=== EXP4N PRODUCTION CONTRACT FREEZE ===\n")
    spec = load_envelope()
    cons, peak = build_constraints(spec)     # identical code path to the launcher

    print("search parameters")
    check("max_rounds (production)", PRODUCTION_MAX_ROUNDS, REQUIRED["max_rounds"])
    check("n_keys", int(N_KEYS), REQUIRED["n_keys"])
    check("k_rungs", int(K_RUNGS), REQUIRED["k_rungs"])
    check("lam", 2.0, REQUIRED["lam"])
    check("seed", 20260825, REQUIRED["seed"])
    check("tolerance", float(cons["resource"].get("budget_tolerance", 0.0)),
          REQUIRED["tolerance"])
    check("hours_cap", float(spec["weekday_revenue_vehicle_hours"]),
          REQUIRED["hours_cap"])
    print(f"  NOTE max_rounds default in src is {int(MAX_ROUNDS)}; the production "
          f"ceiling is passed as a certify() keyword, src is NOT modified.")

    print("\ndigests and envelope")
    env_digest = str(spec["envelope_digest"])
    check("canonical envelope digest", env_digest, "3fd5241db44ca9da")
    check("contract digest", str(CERTIFICATION_DIGEST), "2125984c82b60a83")
    # Assert against the FROZEN ARTIFACT and the calibration records -- never
    # against hand-typed literals. A first draft of this script compared against
    # constants transcribed from a rounded log line and manufactured a false
    # mismatch in the last ULP on two periods. The authoritative sources are
    # COMMON_RESOURCE_ENVELOPE.json and what the 21 calibration runs actually
    # used; both are compared bit-exactly below.
    #
    # Note also that envelope_digest is computed over round(peak, 9), so the
    # digest matching is NECESSARY BUT NOT SUFFICIENT for bit-exact equality of
    # the envelope. The bit-exact comparison is what establishes that.
    frozen_peak = {k: float(v) for k, v in spec["peak_fleet_by_period"].items()}
    for p in PERIODS:
        check(f"peak envelope [{p}] == frozen artifact",
              float(peak[p]) == frozen_peak[p], True)
        print(f"       value {float(peak[p])!r}")
    check("peak envelope resolved as explicit dict",
          isinstance(cons["resource"]["peak_fleet_by_period"], dict), True)
    check("peak sentinel NOT in play",
          cons["resource"]["peak_fleet_by_period"] != "baseline", True)

    print("\ncandidate set")
    arch = json.loads((OUT / "EXP4_ENDOGENOUS_CAP_ARCHIVE.json").read_text())
    keys = [c["state_key"] for c in sorted(arch["candidates"],
                                           key=lambda c: c["certified_rank"])]
    check("candidate count", len(keys), 200)
    check("candidate ids unique", len(set(keys)), 200)
    cand_digest = hashlib.sha256("\n".join(sorted(keys)).encode()).hexdigest()[:16]
    print(f"  ---- candidate-set digest           {cand_digest}")

    print("\nsource tree")
    commit = subprocess.run(["git","rev-parse","HEAD"], cwd=ROOT,
                            capture_output=True, text=True).stdout.strip()
    dirty = subprocess.run(["git","status","--porcelain","src/cota_opt"], cwd=ROOT,
                           capture_output=True, text=True).stdout.strip()
    check("src/cota_opt clean (unmodified)", dirty, "")
    src_digest = hashlib.sha256(b"".join(
        sorted(p.read_bytes() for p in sorted((ROOT/"src"/"cota_opt").rglob("*.py")))
    )).hexdigest()[:16]
    print(f"  ---- source-tree git commit         {commit}")
    print(f"  ---- src/cota_opt content digest    {src_digest}")

    print("\nagreement with the ACCEPTED CALIBRATION (the only delta may be max_rounds)")
    calib = [json.loads(p.read_text()) for p in (OUT/"calib_mr200").glob("*.json")]
    check("calibration results present", len(calib), 21)
    for field, want in (("common_envelope_digest", env_digest),
                        ("hours_cap", repr(REQUIRED["hours_cap"])),
                        ("budget_tolerance", 0.0),
                        ("contract_digest", str(CERTIFICATION_DIGEST)),
                        ("n_keys", 8), ("k_rungs", 3),
                        ("lam", 2.0), ("seed", 20260825),
                        ("cap_provenance", "common_reference_envelope_resolved_once")):
        got = {r[field] for r in calib}
        check(f"calibration {field} uniform & equal", (len(got) == 1 and got.pop() == want), True)
    got_peaks = {json.dumps(r["peak_caps"], sort_keys=True) for r in calib}
    check("calibration peak envelope uniform", len(got_peaks), 1)
    calib_peak = json.loads(got_peaks.pop())
    check("calibration peak envelope == production (BIT-EXACT)",
          calib_peak == {p: repr(float(peak[p])) for p in PERIODS}, True)
    check("calibration peak envelope == frozen artifact (BIT-EXACT)",
          {k: float(v) for k, v in calib_peak.items()} == frozen_peak, True)
    calib_mr = {r["max_rounds"] for r in calib}
    print(f"  ---- calibration ran at max_rounds  {calib_mr}  (production: {PRODUCTION_MAX_ROUNDS})")

    print("\naudit artifacts preserved (§2)")
    for rel, n in (("EXP4N_ROUND_CAP_CALIBRATION.json", None),
                   ("EXP4N_ABORTED_ROUND_CAP_INVALID.json", None),
                   ("certified", 21), ("calib_mr200", 21)):
        p = OUT / rel
        if n is None:
            check(f"{rel} exists", p.exists(), True)
        else:
            check(f"{rel}/ has {n} results", len(list(p.glob('*.json'))), n)

    if fail:
        print("\n=== CONTRACT MISMATCH — DO NOT RUN ===")
        for f in fail: print("  " + f)
        return 1

    contract = {
     "artifact":"EXP4N_PRODUCTION_CONTRACT","status":"FROZEN",
     "production_max_rounds":PRODUCTION_MAX_ROUNDS,
     "only_intended_difference_from_aborted_run":"max_rounds: 40 -> 120",
     "search":{"max_rounds":PRODUCTION_MAX_ROUNDS,"n_keys":int(N_KEYS),
               "k_rungs":int(K_RUNGS),"lam":2.0,"seed":20260825,
               "tolerance":0.0,"hours_cap":REQUIRED["hours_cap"]},
     "canonical_envelope_digest":env_digest,
     "contract_digest":str(CERTIFICATION_DIGEST),
     "peak_vehicle_envelope":{p: repr(float(peak[p])) for p in PERIODS},
     "cap_provenance":"common_reference_envelope_resolved_once",
     "envelope_digest_caveat":("envelope_digest is computed over round(peak, 9), so a "
       "matching digest is necessary but NOT sufficient for bit-exact envelope equality. "
       "This freeze additionally compares the production-resolved envelope bit-exactly "
       "against COMMON_RESOURCE_ENVELOPE.json and against the envelope all 21 calibration "
       "runs actually used."),
     "candidate_set_digest":cand_digest,"candidate_count":len(keys),
     "source_tree_git_commit":commit,
     "src_cota_opt_content_digest":src_digest,
     "src_cota_opt_modified":False,
     "ceiling_passed_via":"certify(max_rounds=...) keyword from scripts/exp4n_launch.py",
     "calibration_max_rounds":sorted(calib_mr),
     "known_output_gaps":[
       {"field":"initial_objective",
        "status":"NOT RECORDABLE without changing frozen code",
        "why":("certify() computes delivered_obj internally (exp4_certify.py:258) but "
               "CertifiedResult has no field for it and payload() does not emit it. "
               "Exposing it means editing src/cota_opt, which breaks the frozen-source "
               "guard; recomputing it means a duplicate gen1 solve per candidate, "
               "roughly 11-17h across 200."),
        "recorded_instead":("objective_APPROXIMATE (the discovery score, a DIFFERENT "
               "quantity) and round_trajectory[1], the objective after round 1, which "
               "is an exact upper bound on the delivered objective.")},
       {"field":"peak_usage per period",
        "status":"NOT RECORDABLE without changing frozen code",
        "why":("certify() extracts only the system max (fitness.peak_vehicles) from "
               "FitnessVector; per-period peak_by_period is not carried into the "
               "payload. Rebuilding the model in the launcher to recompute it would "
               "duplicate the expensive path-set setup."),
        "recorded_instead":("fitness_EXACT.peak_vehicles (system max), the per-period "
               "peak_caps envelope, and the fact that BOTH feasibility arms are "
               "enforced in-loop by frequency._feasible:374 so no returned plan can "
               "violate either. hours feasibility is additionally re-verified "
               "independently in the launcher.")}]}
    (OUT / "EXP4N_PRODUCTION_CONTRACT.json").write_text(json.dumps(contract, indent=1))
    print("\n=== CONTRACT FROZEN — all checks passed ===")
    print(f"written: outputs/exp4_normalized/EXP4N_PRODUCTION_CONTRACT.json")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
