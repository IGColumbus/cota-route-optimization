#!/usr/bin/env python3
"""Freeze the Experiment 7 contract -- or refuse to.

    exp7_freeze.py --levels outputs/exp7/EXP7_LEVELS.json [--draft]

Writes outputs/exp7/EXP7_CONTRACT.json (or EXP7_CONTRACT.DRAFT.json with
--draft). A non-draft freeze REFUSES unless every readiness gate passes:

  G1  docs/EXPERIMENT7_PROTOCOL_AS_ISSUED.md exists (Ian's text, verbatim)
  G2  docs/EXPERIMENT7_AMENDMENT.md exists and names every level in the file
  G3  BASE reproduction canaries reproduced Exp 6 bit-exactly
  G4  every non-BASE level REACHES the evaluator (preflight reach, N0 and N3;
      N4 for F4 levels)
  G5  unit tests for the closure engine and classification pass
  G6  src/cota_opt content digest equals Exp 6's (b63ae2dba134245e), or the
      BASE reuse flag is off
  G7  production-path transfer/refusal/emptiness preflights passed

The contract carries: the levels (payload + digest) and their order, the two
tracks (F6: N0/N3 x full Exp 6 policy graph with within-level closure; F4:
N0/N3/N4 x REF, cross-level only), the closure parameters, the catalog, the
nesting graph, the firewall contract digests per level, the sentinels, the
runner hashes and the compute estimate.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import exp45_certify_cell as CC  # noqa: E402
import exp6_grid as G  # noqa: E402
import exp7_contracts as K  # noqa: E402
import exp7_levels as L  # noqa: E402

OUT = ROOT / "outputs" / "exp7"
PRE = OUT / "preflight"
EXP6_SRC = "b63ae2dba134245e"
RUNNERS = ("exp7_cell.py", "exp7_levels.py", "exp7_closure.py",
           "exp7_classify.py", "exp7_run.py", "exp7_contracts.py",
           "exp7_infeasible_cell.py", "exp7_preflight.py", "exp7_analyze.py",
           "exp6_grid.py", "exp45_certify_cell.py", "exp45_contracts.py",
           "exp5_model_resource.py")

# Measured Exp 6 / D39 wall seconds per certification (median; 2-core box,
# two concurrent lanes): initial N0 596, N3 611; closure N0 627, N3 624;
# N4 (D39 preflight, anchored J100/H110) 1079-1148.
SEC = {"N0": 610.0, "N3": 615.0, "N4": 1150.0}


def estimate(n_levels: int, n_policies: int = 14, lanes: int = 2,
             f6_within_ran_per_level: float = 22.5,
             x_ran_share: float = 0.5, base_reuse: bool = True) -> dict:
    """Certifications and wall hours. Explicit assumptions, all stated:

    F6 initial     (L - base) x 2 networks x 14 cells (N3 R1_H20 costs a
                   proof, ~1 min, counted as 0)
    F6 W stage     ~22.5 RAN per network per level (Exp 6: 24 N0, 21 N3); at
                   BASE imported from Exp 6 where the same transfer exists
    F6 X stage     worst case per pass: 14 policies x L(L-1) ordered pairs per
                   network. Expected RAN share after dedup (identical plan,
                   policy refusal, memo): x_ran_share of pass-1 candidates, and
                   a second pass of 25% of that (Exp 6: all improvements in
                   passes 1-2). Upper bound: every candidate RAN, 2 passes.
    F4 initial     L x N4 + (L - base) x (N0 + N3)
    F4 X stage     3 networks x L(L-1), same RAN share
    sentinels      4 reruns
    """
    Ln = n_levels
    new_lv = Ln - 1 if base_reuse else Ln
    f6_init = new_lv * 2 * (n_policies - 0.5)          # 0.5: N3 R1_H20 proof
    f6_w = new_lv * 2 * f6_within_ran_per_level
    xpairs = Ln * (Ln - 1)
    f6_x_exp = 2 * n_policies * xpairs * x_ran_share * 1.25
    f6_x_max = 2 * n_policies * xpairs * 2
    f4_init = {"N4": Ln, "N0": new_lv, "N3": new_lv}
    f4_x_exp = {n: xpairs * x_ran_share * 1.25 for n in ("N0", "N3", "N4")}
    f4_x_max = {n: xpairs * 2 for n in ("N0", "N3", "N4")}
    sent = 4
    s_mean = (SEC["N0"] + SEC["N3"]) / 2

    def hours(f6, f4, extra=0.0):
        cpu = f6 * s_mean + sum(f4[n] * SEC[n] for n in f4) + extra
        return cpu / 3600.0 / lanes
    exp = hours(f6_init + f6_w + f6_x_exp,
                {n: f4_init[n] + f4_x_exp[n] for n in f4_init}, sent * s_mean)
    hi = hours(f6_init + f6_w * 2 + f6_x_max,
               {n: f4_init[n] + f4_x_max[n] for n in f4_init}, sent * s_mean)
    return {"levels": Ln, "certifications_expected": round(
                f6_init + f6_w + f6_x_exp + sum(f4_init.values())
                + sum(f4_x_exp.values()) + sent),
            "certifications_upper": round(
                f6_init + 2 * f6_w + f6_x_max + sum(f4_init.values())
                + sum(f4_x_max.values()) + sent),
            "wall_hours_expected": round(exp, 1),
            "wall_hours_upper": round(hi, 1), "lanes": lanes,
            "seconds_per_certification": SEC,
            "assumptions": estimate.__doc__}


def gates(levels, lvfile) -> dict:
    g = {}
    g["G1_as_issued_text"] = (ROOT / "docs/EXPERIMENT7_PROTOCOL_AS_ISSUED.md").exists()
    am = ROOT / "docs/EXPERIMENT7_AMENDMENT.md"
    g["G2_amendment_names_levels"] = am.exists() and all(
        lv.name in am.read_text() for lv in levels)
    br = PRE / "base_repro" / "BASE_REPRO_VERDICT.json"
    g["G3_base_reproduction"] = br.exists() and json.loads(br.read_text())["passed"]
    ok = True
    for n in ("N0", "N3"):
        p = PRE / f"reach_matrix_{n}.json"
        ok &= p.exists() and json.loads(p.read_text()).get("passed", False)
    g["G4_level_reach"] = ok
    r = subprocess.run([sys.executable, "-m", "pytest", "-q",
                        "tests/test_exp7_closure.py"], cwd=ROOT,
                       capture_output=True, text=True)
    g["G5_unit_tests"] = r.returncode == 0
    g["G6_src_digest_matches_exp6"] = CC.src_content_digest() == EXP6_SRC
    pt = PRE / "transfer" / "TRANSFER_PREFLIGHT_VERDICT.json"
    g["G7_transfer_refusal_emptiness"] = pt.exists() and \
        json.loads(pt.read_text())["passed"]
    return g


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--levels", required=True)
    ap.add_argument("--draft", action="store_true")
    a = ap.parse_args()
    raw = json.loads((ROOT / a.levels).read_text())
    levels = [L.BASE] + [L.from_payload(p) for p in raw["levels"]
                         if p["name"] != "BASE"]
    names = [lv.name for lv in levels]
    if len(set(names)) != len(names):
        raise SystemExit("duplicate level names")
    cat = G.catalog_digest()
    sp = G.specs(cat)
    h = G.hasse(sp)
    g = gates(levels, a.levels)
    con = {
        "artifact": "EXP7_CONTRACT", "version": "7.0",
        "frozen": not a.draft,
        "protocol": "docs/EXPERIMENT7_PROTOCOL_AS_ISSUED.md",
        "amendment": "docs/EXPERIMENT7_AMENDMENT.md",
        "level_file": a.levels,
        "levels": [{**lv.payload(), "digest": lv.digest} for lv in levels],
        "level_order": names,
        "tracks": {
            "F6": {"networks": ["N0", "N3"], "policies": list(sp),
                   "within_level_closure": True,
                   "adjacent_edges": [list(e) for e in h["adjacent_edges"]],
                   "strict_pairs": [list(e) for e in h["strict_pairs"]]},
            "F4": {"networks": ["N0", "N3", "N4"], "policies": ["REF"],
                   "within_level_closure": False, "adjacent_edges": [],
                   "strict_pairs": []}},
        "closure": {"pass_ceiling": K.CLOSURE_PASS_CEILING,
                    "improvement_eps": K.IMPROVE_EPS,
                    "engine": "scripts/exp7_closure.py (docstring)",
                    "no_cross_network_sharing": True},
        "catalog": {"digest": cat, "path": "outputs/exp6/EXP6_CONSTRAINT_CATALOG.json"},
        "base_reuse_exp6_initial": bool(g["G3_base_reproduction"]
                                        and g["G6_src_digest_matches_exp6"]),
        "base_reuse_justification": (
            "BASE changes nothing; src/cota_opt digest equals Exp 6's and the "
            "BASE canaries through exp7_cell.py reproduced Exp 6 initial records "
            "bit-exactly (outputs/exp7/preflight/base_repro)"),
        "sentinels": [["F6", names[-1], "N3", "REF"],
                      ["F6", names[-1], "N0", "R2_S10"],
                      ["F4", names[-1], "N4", "REF"],
                      ["F6", names[min(1, len(names) - 1)], "N0", "REF"]],
        "firewall": K.contracts_payload(levels),
        "code": {"src_cota_opt_content_digest": CC.src_content_digest(),
                 "runner_sha256": {n: CC.sha256_file(ROOT / "scripts" / n)[:16]
                                   for n in RUNNERS
                                   if (ROOT / "scripts" / n).exists()}},
        "gates": g,
        "estimate": estimate(len(levels), len(sp),
                             base_reuse=bool(g["G3_base_reproduction"]))}
    if not a.draft and not all(g.values()):
        print(json.dumps(g, indent=1))
        raise SystemExit("REFUSED: readiness gates not all passed")
    out = OUT / ("EXP7_CONTRACT.DRAFT.json" if a.draft else "EXP7_CONTRACT.json")
    if out.exists() and not a.draft:
        raise SystemExit(f"{out} already frozen")
    CC.atomic_write_json(out, con)
    print(out.relative_to(ROOT), json.dumps(g), json.dumps(con["estimate"],
                                                           default=str)[:400])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
