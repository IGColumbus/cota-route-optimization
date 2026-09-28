#!/usr/bin/env python3
"""CANONICAL_RESULTS_v2 -- the results registry, after Gen1.

WHY A SECOND FILE
-----------------
``outputs/CANONICAL_RESULTS.json`` (v1) is an ASSERTED artifact of the Gen1
freeze: its sha256 is pinned in ``outputs/GEN1_FREEZE_MANIFEST.json`` under
``asserted.artifact_sha256``, and ``scripts/gen1_freeze.py --verify`` fails if a
single byte of it moves. It therefore cannot record Experiment 4 without
breaking the record it is part of. Versions are added, not overwritten
(commit 4963191b), so this writes v2.

v2 = every v1 entry copied VERBATIM, plus the experiments closed after Gen1.
Before copying, v1's hash is asserted against the Gen1 manifest, so v2 is always
built on the intact frozen v1 and never on a locally edited copy of it.

EVERY EXPERIMENT 4 FIGURE IS READ, NOT TYPED
--------------------------------------------
Headline numbers come from EXP4N_FINAL_STATUS.json and EXP4N_RANKING.json; the
resource-use comparison is computed here from the 200 legacy and the 200
normalized per-candidate results. The generator is the artifact: if an input is
missing, it refuses rather than write a registry that quotes a number it cannot
see.

``outputs/SUPERSEDED.md`` is NOT regenerated. It carries a hand-appended
Experiment 3 section that no generator produces, and a full re-render would
delete it. The Experiment 4 section is spliced in between markers instead, so
every other byte of that file is left exactly as it was.
"""
from __future__ import annotations

import glob
import hashlib
import json
import math
import statistics as st
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
V1 = OUT / "CANONICAL_RESULTS.json"
V2 = OUT / "CANONICAL_RESULTS_v2.json"
GEN1 = OUT / "GEN1_FREEZE_MANIFEST.json"
N = OUT / "exp4_normalized"


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def commit() -> str:
    return subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                          capture_output=True, text=True).stdout.strip()


def need(p: Path) -> dict:
    if not p.exists():
        raise SystemExit(f"REFUSING: {p.relative_to(ROOT)} is missing -- will "
                         f"not write a registry that quotes a number it cannot see")
    return json.loads(p.read_text())


def _is_off(x) -> bool:
    return x == "Infinity" or (isinstance(x, (int, float)) and math.isinf(x))


def _plan(r: dict) -> dict:
    p = r["plan_EXACT"]
    return json.loads(p) if isinstance(p, str) else p


def resource_use() -> dict:
    """Descriptive comparison of the two runs, computed from the per-candidate
    results. Same fields, same cap, both sides."""
    cap = float(need(N / "COMMON_RESOURCE_ENVELOPE.json")
                ["weekday_revenue_vehicle_hours"])

    def summarise(paths: list[str]) -> dict:
        rs = [json.loads(Path(p).read_text()) for p in paths]
        vh = [float(r["fitness_EXACT"]["revenue_veh_hours"]) for r in rs]
        off = [sum(map(_is_off, _plan(r).values())) / len(_plan(r)) for r in rs]
        return {"n": len(rs),
                "hours_share_of_cap_pct": [round(min(vh) / cap * 100, 2),
                                           round(max(vh) / cap * 100, 2)],
                "revenue_veh_hours": [round(min(vh), 2), round(max(vh), 2)],
                "off_route_period_share_pct": {
                    "min": round(min(off) * 100, 1),
                    "median": round(st.median(off) * 100, 1),
                    "max": round(max(off) * 100, 1)}}

    legacy = sorted(glob.glob(str(OUT / "exp4/run/certified/*.json")))
    normal = sorted(glob.glob(str(N / "production_mr120/*.json")))
    if len(legacy) != 200 or len(normal) != 200:
        raise SystemExit(f"REFUSING: expected 200+200 results, found "
                         f"{len(legacy)} legacy and {len(normal)} normalized")
    return {
        "hours_cap": cap,
        "legacy_endogenous_cap": summarise(legacy),
        "normalized_common_envelope": summarise(normal),
        "reading": (
            "DESCRIPTIVE, not preregistered. Under the endogenous cap every "
            "certified plan left roughly two thirds of the hours budget unspent; "
            "under the common envelope every certified plan spends essentially "
            "all of it. The Experiment 5 premise audit's finding that the hours "
            "axis never binds was measured on the legacy plans and does not "
            "hold for the normalized ones."),
    }


def exp4_entry() -> dict:
    F = need(N / "EXP4N_FINAL_STATUS.json")
    R = need(N / "EXP4N_RANKING.json")
    A = need(N / "EXP4_ENDOGENOUS_CAP_ARCHIVE.json")
    if F["status"] != "EXP4_FULL_NORMALIZED_CERTIFIED":
        raise SystemExit(f"REFUSING: EXP4N status is {F['status']}")
    L, S = F["leader"], F["runner_up"]
    nv = R["normalized_vs_legacy"]
    band = F["noise_band"]
    inc, oob = A["incumbent"], A["out_of_band_candidate"]
    headline = (
        f"{F['status']}: {F['n_certified']}/200 candidates re-certified under "
        f"ONE common peak-vehicle envelope; integrity gate {F['integrity_gate']}. "
        f"Leader {L['state_digest'][:12]} at {float(L['objective_EXACT']):,.4f} "
        f"({L['rounds']} rounds, {L['n_lines']} lines; legacy rank "
        f"{L['legacy_certified_rank']}), ahead of {S['state_digest'][:12]} by "
        f"{float(F['margin_first_to_second']['percent']):.6f}%. The legacy leader "
        f"{inc['state_key'].split('#')[1]} ranks "
        f"{nv['legacy_leader']['normalized_rank']} of 200. Spearman "
        f"{nv['spearman_rank_correlation']:+.4f}; "
        f"{nv['pairwise_orderings_inverted']:,} of "
        f"{nv['pairwise_orderings_total']:,} pairwise orderings inverted "
        f"({nv['pairwise_inverted_fraction'] * 100:.1f}%).")
    return {
        "title": "Route geometry at scale -- 200 promoted candidate networks "
                 "certified by exact optimization, then re-certified under one "
                 "common resource envelope",
        "status": (f"CLOSED -- {F['status']}. The legacy ORDERING is superseded; "
                   f"its objective values are not withdrawn"),
        "canonical": [
            "EXPERIMENT4_NORMALIZED_CLOSEOUT.md",
            "outputs/exp4_normalized/EXP4N_FINAL_STATUS.json",
            "outputs/exp4_normalized/EXP4N_RANKING.json",
            "outputs/exp4_normalized/EXP4N_INTEGRITY_GATE.json",
            "outputs/exp4_normalized/EXP4N_PRODUCTION_CONTRACT.json",
            "outputs/exp4_normalized/COMMON_RESOURCE_ENVELOPE.json",
            "outputs/exp4_normalized/production_mr120/*.json"],
        "evaluator": ("same_route (Model B) -- exp4_certify.certify defaults "
                      "waiting_model='same_route' (exp4_certify.py:191) and "
                      "exp4n_launch.py:208 does not override it; the legacy "
                      "launcher passes it explicitly and requires it "
                      "(exp4_launch.py:182)"),
        "certified": True,
        "headline": headline,
        "digests": {k: F[k] for k in (
            "contract_digest", "canonical_envelope_digest",
            "candidate_set_digest", "src_cota_opt_content_digest",
            "tie_break_digest")},
        "superseded": ["EXPERIMENT4_CLOSEOUT.md",
                       "outputs/exp4/run/certified/*.json",
                       "outputs/exp4/run/discovery_vs_certified.json"],
        "superseded_why": (
            "ORDERING ONLY. The legacy run resolved each candidate's peak-vehicle "
            "cap against that candidate's own baseline plan (exp2.py:324), so all "
            "200 were optimized inside boxes they defined for themselves: it "
            "ranks candidate-specific optimization problems, not geometries. "
            f"The legacy leader {inc['state_key'].split('#')[1]} "
            f"({inc['objective_EXACT']:,.4f}) ranks "
            f"{nv['legacy_leader']['normalized_rank']} of 200 under the common "
            "envelope. Every legacy objective value remains exactly reproducible "
            "and none is withdrawn."),
        "noise_band": {
            "percent": band["percent"], "source": band["source"],
            "margin_to_band_ratio": round(float(F["margin_first_to_second"]
                                                ["percent"]) / band["percent"], 1),
            "rule": ("ASYMMETRIC: at or below the band a difference is noise; "
                     "above it, a real difference is NOT established, only NOT "
                     "excluded")},
        "resource_use": resource_use(),
        "out_of_band_audit": {
            "closeout": "EXPERIMENT4_AUDIT_CLOSEOUT.md",
            "finding": (
                "the top-200 promotion cap is INVALID: "
                f"{oob['state_key'].split('#')[1]} (discovery rank "
                f"{oob['discovery_rank']}, excluded by the cap) certifies at "
                f"{oob['objective_EXACT']:,.4f}, better than the legacy leader's "
                f"{inc['objective_EXACT']:,.4f}. Both figures are under the "
                "LEGACY endogenous cap; the out-of-band candidate was never "
                "certified under the common envelope")},
        "limitations": [
            "the first-to-second margin is not established, only not excluded: "
            "the (N,K)-block-local residual is unmeasured for every candidate, "
            "the leader included",
            "no fleet or deployability claim: the fleet instrument returns "
            "UNDECIDABLE for every candidate; deadhead times and terminal "
            "identity are unavailable from public data",
            "nothing about the 1,800 proposals the promotion cap excluded",
            "the top-of-table reshuffle (normalized top five from legacy ranks "
            "154 and 191-194) is CONSISTENT with the endogenous-cap mechanism "
            "and has not been tested"],
        "closeout": "EXPERIMENT4_NORMALIZED_CLOSEOUT.md",
    }


def exp5_entry() -> dict:
    return {
        "title": "Resource frontier -- how the objective moves as the resource "
                 "envelope is varied",
        "status": "BUILT AND TESTED, NOT RUN -- EXP5_REFRAME_REQUIRED",
        "canonical": [],
        "evaluator": "n/a -- nothing run",
        "certified": False,
        "headline": ("n/a -- nothing scored. Unblocked by EXP4N certifying; "
                     "needs its own preregistration first "
                     "(docs/EXPERIMENTS_5_7_PROTOCOL_INTAKE.md)."),
        "superseded": [],
        "premise_audit": ["EXPERIMENT5_PREMISE_AUDIT.md",
                          "EXPERIMENT5_OFFON_DIAGNOSTIC.md"],
        "premise_status": (
            "Both premise documents were measured on the LEGACY Exp 4 plans. "
            "Their 'no cell binds / hours never bind' finding does not hold on "
            "the EXP4N plans (see exp4.resource_use). The fleet-axis and "
            "proxy-instrument findings were not re-measured. Re-audit against "
            "EXP4N before reframing or running."),
    }


BEGIN, END = "<!-- exp4-superseded:begin -->", "<!-- exp4-superseded:end -->"


def splice_superseded(e: dict) -> None:
    """Insert or replace ONLY the Experiment 4 block in outputs/SUPERSEDED.md.
    Same layout as freeze_records.superseded_md's per-experiment sections."""
    p = OUT / "SUPERSEDED.md"
    text = p.read_text()
    block = "\n".join(
        [BEGIN, f"## exp4 — {e['title']}", "",
         "*Written by `scripts/canonical_results_v2.py`.*", "",
         f"*{e['superseded_why']}*", ""]
        + [f"- `{rel}`" for rel in e["superseded"]]
        + ["", "**Current instead:** "
           + ", ".join(f"`{c}`" for c in e["canonical"]), "", END])
    if BEGIN in text and END in text:
        head, rest = text.split(BEGIN, 1)
        text = head + block + rest.split(END, 1)[1]
    else:
        text = text.rstrip("\n") + "\n\n" + block + "\n"
    p.write_text(text)


def main() -> int:
    g = need(GEN1)
    pinned = g["asserted"]["artifact_sha256"].get("outputs/CANONICAL_RESULTS.json")
    if pinned is None:
        raise SystemExit("REFUSING: the Gen1 manifest no longer asserts v1")
    if sha256(V1) != pinned:
        raise SystemExit("REFUSING: outputs/CANONICAL_RESULTS.json no longer "
                         "matches the hash the Gen1 freeze asserts; v2 would be "
                         "built on a modified v1")
    v1 = json.loads(V1.read_text())
    exps = dict(v1["experiments"])          # verbatim
    exps["exp4"] = exp4_entry()
    exps["exp5"] = exp5_entry()
    v2 = {
        "version": 2,
        "generated_by": "scripts/canonical_results_v2.py",
        "generated_commit": commit(),
        "predecessor": {
            "path": "outputs/CANONICAL_RESULTS.json",
            "sha256": pinned,
            "status": ("Gen1-frozen, ASSERTED, byte-for-byte unchanged. Its "
                       "entries are copied here verbatim and remain "
                       "authoritative for Experiments 1-3."),
        },
        "why_this_exists": v1.get("why_this_exists"),
        "how_to_check_an_artifact": v1.get("how_to_check_an_artifact"),
        "experiments": exps,
    }
    for k in v1:
        if k not in v2 and k != "generated_commit":
            v2[k] = v1[k]
    V2.write_text(json.dumps(v2, indent=2, ensure_ascii=False))

    splice_superseded(exps["exp4"])

    for k in ("exp1", "exp2", "exp2b", "exp3"):
        assert v2["experiments"][k] == v1["experiments"][k], k
    print(f"wrote {V2.relative_to(ROOT)}  ({len(exps)} experiments)")
    print(f"      outputs/SUPERSEDED.md (exp4 block spliced; nothing else touched)")
    print(f"  v1 intact: sha256 matches the Gen1 freeze ({pinned[:16]})")
    print(f"  exp1-exp3 copied verbatim: verified")
    for k, e in exps.items():
        print(f"    {k:6s} {e['status'][:96]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
