#!/usr/bin/env python3
"""Freeze the endogenous-cap Exp 4 as EXP4_ENDOGENOUS_CAP_ARCHIVE.

READ-ONLY over outputs/exp4/. Moves nothing, mutates nothing. Records a
per-file digest of every artifact that defines the legacy experiment, so that
any later mutation — by the normalized rerun or anything else — is detectable
rather than merely improbable.
"""
from __future__ import annotations
import hashlib, json, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
RUN = ROOT / "outputs" / "exp4" / "run"
OUT = ROOT / "outputs" / "exp4_normalized"
LEADER = "exp4|exp4-pool-v1|65lines#ecb2ffc4bcce"
LEADER_OBJ = 3511184.5657525407
OOB = "exp4|exp4-pool-v1|65lines#eca7a2a1fb46"      # discovery rank 237
OOB_OBJ = 3510666.7802095017


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    cert = {}
    for p in sorted((RUN / "certified").glob("*.json")):
        d = json.load(open(p))
        if "objective_EXACT" in d:
            cert[d["state_key"]] = d
    if len(cert) != 200:
        print(f"FATAL: {len(cert)} certified records, expected 200"); return 2
    if cert[LEADER]["objective_EXACT"] != LEADER_OBJ:
        print("FATAL: legacy incumbent objective has moved"); return 2

    prop = json.loads((RUN / "proposals.json").read_text())["proposals"]
    lines_of = {p["state_key"]: p["lines"] for p in prop}
    approx_of = {p["state_key"]: p["objective_APPROXIMATE"] for p in prop}
    ranked = sorted(prop, key=lambda p: (p["objective_APPROXIMATE"], p["state_key"]))
    drank = {p["state_key"]: i for i, p in enumerate(ranked, 1)}
    crank = {k: i for i, k in enumerate(
        sorted(cert, key=lambda k: (cert[k]["objective_EXACT"], k)), 1)}

    files = {}
    for p in sorted(RUN.rglob("*")):
        if p.is_file() and p.suffix in (".json", ".md", ".jsonl"):
            files[str(p.relative_to(ROOT))] = {"sha256": sha(p), "bytes": p.stat().st_size}

    objs = sorted(d["objective_EXACT"] for d in cert.values())
    payload = {
        "archive_id": "EXP4_ENDOGENOUS_CAP_ARCHIVE",
        "frozen_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "why": ("the peak_fleet_by_period 'baseline' sentinel resolved against "
                "each candidate's OWN baseline plan (exp2.py:324), so these 200 "
                "objectives are valid for 200 DIFFERENT optimization problems "
                "and their ranking is not a geometry comparison"),
        "status": "PRESERVED, NOT SUPERSEDED — audit artifact and comparison dataset",
        "n_candidates": len(cert),
        "incumbent": {"state_key": LEADER, "objective_EXACT": LEADER_OBJ,
                      "certified_rank": crank[LEADER],
                      "discovery_rank": drank[LEADER]},
        "out_of_band_candidate": {
            "state_key": OOB, "objective_EXACT": OOB_OBJ,
            "discovery_rank": drank.get(OOB),
            "note": ("certified in the out-of-band audit, not in the promoted "
                     "200; inserted at exact rank 1 of 201 against this archive")},
        "objective_spread": {
            "min": objs[0], "max": objs[-1],
            "relative_pct": (objs[-1] - objs[0]) / objs[0] * 100},
        "candidates": [
            {"state_key": k,
             "certified_rank": crank[k],
             "discovery_rank": drank.get(k),
             "objective_EXACT": repr(cert[k]["objective_EXACT"]),
             "objective_APPROXIMATE": repr(approx_of.get(k)),
             "n_lines": len(lines_of.get(k, [])),
             "state_digest": cert[k].get("state_digest", ""),
             "plan_digest": cert[k].get("plan_digest", ""),
             "rounds": cert[k].get("rounds"),
             "converged": cert[k].get("converged"),
             "guarantee": cert[k].get("guarantee", "")}
            for k in sorted(cert, key=lambda k: crank[k])],
        "file_digests": files,
        "n_files_digested": len(files),
        "DO_NOT": ("overwrite, move, regenerate or mutate anything under "
                   "outputs/exp4/. The normalized rerun writes only to "
                   "outputs/exp4_normalized/."),
    }
    p = OUT / "EXP4_ENDOGENOUS_CAP_ARCHIVE.json"
    p.write_text(json.dumps(payload, indent=1))
    print(f"archived {len(cert)} candidates, {len(files)} files digested -> {p}")
    print(f"incumbent {LEADER[-12:]} obj {LEADER_OBJ} certified_rank {crank[LEADER]} "
          f"discovery_rank {drank[LEADER]}")
    print(f"out-of-band {OOB[-12:]} obj {OOB_OBJ} discovery_rank {drank.get(OOB)}")
    print(f"objective spread {objs[0]:.4f} .. {objs[-1]:.4f} "
          f"({(objs[-1]-objs[0])/objs[0]*100:.4f}%)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
