#!/usr/bin/env python3
"""Write outputs/CANONICAL_RESULTS_v4.json -- ADDITIVE over v3.  [PREPARED, NOT RUN]

Prepared 2026-09-28/29 in parallel with the Experiment 6 run; schema reconciled
2026-09-29 against the frozen contract (outputs/exp6/EXP6_CONTRACT.json, file
sha256 5bf1cb82ad8829a8...), Amendment 1 (EXP6_CONTRACT_AMENDMENT_1.json) and
the analysis writer scripts/exp6_analyze.py (runner sha256 da6792a144c041e2 as
frozen by Amendment 1). Move to scripts/canonical_results_v4.py and run ONLY
after Experiment 6 has closed and EXPERIMENT6_CLOSEOUT.md is committed.

v4 = every v3 top-level key and every v3 experiment entry copied VERBATIM
(exp1, exp2, exp2b, exp3, exp4, exp4a, exp5 -- including EXP5_MONOTONICITY_FAILURE,
every `superseded` list and every `v2_entry_superseded`), plus:

  * `exp6`                  -- new entry from EXP6_ANALYSIS.json, EXP6_CONTRACT.json,
                               EXP6_CONTRACT_AMENDMENT_1.json, EXPERIMENT6_CLOSEOUT.md;
  * `reporting_corrections` -- new TOP-LEVEL key (Exp 1 fleet wording), because
                               the exp1 entry must stay verbatim;
  * `predecessor`           -- v3's path and sha256.

Refuses if: any Exp 6 artifact is absent; the closeout still has '{{'; v4 exists;
v3's sha256 changed; the analysis status is INCOMPLETE; the contract or
Amendment-1 hashes differ from what was frozen; the exp6_analyze.py on disk is
not the Amendment-1 hash (the schema below was read from that exact file).

Analysis status semantics (scripts/exp6_analyze.py lines 295-299):
  "EXP6_POLICY_FRONTIER_CERTIFIED" | "INCOMPLETE" | "FAILED: <reason>; <reason>..."
A FAILED run is still registered (certified=False, failures preserved verbatim).

INFEASIBLE_UNDER_ENVELOPE (Amendment 1): a frontier row whose status is not
CERTIFIED has no objective and NO finite policy cost. It is registered as
"policy infeasible under the modeled envelope" -- a result, not a failure --
with the minimum-service plan's usage against every cap.
"""
from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _configure(src: Path, closeout: Path | None, out: Path | None) -> None:
    """Point every path at `src` (the repository holding the artifacts).
    `closeout` / `out` override the closeout document and the v4 destination
    (used by the parallel-prep worktree: read the main checkout, write here)."""
    global ROOT, OUT, V3, V4, E6, ANALYSIS, CONTRACT, AMEND1, AMEND2, CATALOG
    global CLOSEOUT, ANALYZER
    ROOT = src
    OUT = ROOT / "outputs"
    V3 = OUT / "CANONICAL_RESULTS_v3.json"
    V4 = out or OUT / "CANONICAL_RESULTS_v4.json"
    E6 = OUT / "exp6"
    ANALYSIS = E6 / "EXP6_ANALYSIS.json"
    CONTRACT = E6 / "EXP6_CONTRACT.json"
    AMEND1 = E6 / "EXP6_CONTRACT_AMENDMENT_1.json"
    AMEND2 = E6 / "EXP6_CONTRACT_AMENDMENT_2.json"
    CATALOG = E6 / "EXP6_CONSTRAINT_CATALOG.json"
    CLOSEOUT = closeout or ROOT / "EXPERIMENT6_CLOSEOUT.md"
    ANALYZER = ROOT / "scripts" / "exp6_analyze.py"


_configure(ROOT, None, None)
PROVENANCE_DOCS = ["EXPERIMENT6_PROTOCOL.md", "EXPERIMENT6_D39_AMENDMENT.md",
                   "EXPERIMENT6_CONSTRAINT_CATALOG.md",
                   "EXPERIMENT6_D39_PREFLIGHT.md", "EXPERIMENT6_AMENDMENT_1.md",
                   "EXPERIMENT6_AMENDMENT_2.md"]   # + the closeout, hashed separately

VERBATIM_KEYS = ("exp1", "exp2", "exp2b", "exp3", "exp4", "exp4a", "exp5")
EXPECTED_V3_EXP5_STATUS = "FAILED: EXP5_MONOTONICITY_FAILURE on 12 pairs"
EXPECTED_V3_SHA256 = \
    "026c5327335c45e47e5b78c27f8c5210894d7cb6510191091a14c524240c95a4"

# Frozen identities read from the artifacts on 2026-09-29 (prefix match).
FROZEN = {
    "contract_sha256_prefix": "5bf1cb82ad8829a8",
    "amendment1_sha256_prefix": "02d546487d8ff0c8",
    "catalog_digest": "e22f2c94c8f53475",
    "src_cota_opt_content_digest": "b63ae2dba134245e",
    "code_version": "src-17659e64846b",
    "EXP6_POLICY": "393f45ac10d28cb9",
    "EXP6_STRUCTURE": "fad14449dc3db7c6",
    "pass_ceiling": 8,
    "analyzer_sha256_prefix": "da6792a144c041e2",   # Amendment 1 & 2 runner hash
    "amendment2_sha256_prefix": "35462172b30c6363",
    "analysis_sha256_prefix": "b96aca0d71996472",   # the certified analysis
}

#: Statuses a single cell record may carry (exp6_cell.py / exp6_infeasible_cell.py).
CELL_STATUSES = {"CERTIFIED", "INFEASIBLE_UNDER_ENVELOPE",
                 "INFEASIBILITY_NOT_PROVEN", "ANCHOR_REFUSED"}

# ---------------------------------------------------------------------------
# SCHEMA -- reconciled with scripts/exp6_analyze.py (sha256 da6792a1...).
# Top level: status, record_checks, empty_feasible_sets, monotonicity_initial,
# monotonicity_post_closure, reference_closure, closure{N0,N3}, firewall
# {policy, structure}, sentinels, frontier[], failures.
# ---------------------------------------------------------------------------
SCHEMA = {
    "analysis_top": ("status", "record_checks", "empty_feasible_sets",
                     "monotonicity_initial", "monotonicity_post_closure",
                     "reference_closure", "closure", "firewall", "sentinels",
                     "frontier", "failures"),
    "closure_per_network": ("passes_completed", "fixed_point", "pass_ceiling",
                            "attempts_by_action", "n_receipts",
                            "cells_changed_basin"),
    "frontier_certified": ("network", "cell", "spec", "status",
                           "initial_objective", "final_objective",
                           "initial_plan_digest", "final_plan_digest",
                           "winning_basin", "policy_cost_closed",
                           "policy_cost_closed_pct", "policy_cost_greedy_only",
                           "policy_cost_greedy_only_pct", "basin_contamination",
                           "served_demand", "unserved_demand",
                           "generalized_cost", "gc_per_served_trip",
                           "hours_used", "hours_cap", "hours_slack",
                           "peak_used", "peak_slack", "binding_resource",
                           "policy_measure", "n_off", "n_baseline_on_now_off",
                           "rounds_initial", "rounds_final"),
    "frontier_empty": ("network", "cell", "spec", "status",
                       "usage_vs_caps_of_minimum_service_plan"),
    "contract": {"networks": "networks", "envelope_exact":
                 "envelope.exact_fingerprint", "envelope_rounded":
                 "envelope.rounded_envelope_digest", "catalog_digest":
                 "catalog.digest", "pass_ceiling": "closure.pass_ceiling",
                 "source_digest": "code.src_cota_opt_content_digest",
                 "code_version": "code.code_version",
                 "fw_policy": "firewall.EXP6_POLICY.digest",
                 "fw_structure": "firewall.EXP6_STRUCTURE.digest",
                 "preflight": "preflight", "nesting": "nesting",
                 "sentinels": "sentinels"},
}


class SchemaMismatch(KeyError):
    pass


def need(obj: dict, dotted: str, where: str):
    cur = obj
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            raise SchemaMismatch(f"{where}: '{dotted}' missing at '{part}'")
        cur = cur[part]
    return cur


def need_keys(obj: dict, keys, where: str) -> None:
    miss = [k for k in keys if k not in obj]
    if miss:
        raise SchemaMismatch(f"{where}: missing {miss}")


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def commit() -> str:
    return subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True,
                          capture_output=True).stdout.strip()


def preconditions() -> None:
    missing = [p for p in (V3, ANALYSIS, CONTRACT, AMEND1, AMEND2, CATALOG,
                           CLOSEOUT, ANALYZER) if not p.exists()]
    missing += [ROOT / d for d in PROVENANCE_DOCS if not (ROOT / d).exists()]
    if missing:
        sys.exit("REFUSED: Exp 6 is not closed -- missing: " +
                 ", ".join(str(p) for p in missing))
    if V4.exists():
        sys.exit(f"REFUSED: {V4} exists; never overwritten.")
    if "{{" in CLOSEOUT.read_text():
        sys.exit("REFUSED: EXPERIMENT6_CLOSEOUT.md still has '{{' placeholders.")
    checks = [(V3, EXPECTED_V3_SHA256, "v3"),
              (CONTRACT, FROZEN["contract_sha256_prefix"], "EXP6_CONTRACT.json"),
              (AMEND1, FROZEN["amendment1_sha256_prefix"], "Amendment 1"),
              (AMEND2, FROZEN["amendment2_sha256_prefix"], "Amendment 2"),
              (ANALYSIS, FROZEN["analysis_sha256_prefix"], "EXP6_ANALYSIS.json"),
              (ANALYZER, FROZEN["analyzer_sha256_prefix"], "exp6_analyze.py")]
    for p, want, label in checks:
        if not sha256(p).startswith(want):
            sys.exit(f"REFUSED: {label} sha256 {sha256(p)[:16]} != frozen "
                     f"{want[:16]}. If a new amendment changed it, re-reconcile "
                     f"SCHEMA against the new file first.")


def split_status(s: str) -> tuple[str, list[str]]:
    if s == "EXP6_POLICY_FRONTIER_CERTIFIED":
        return s, []
    if s == "INCOMPLETE":
        sys.exit("REFUSED: analysis status INCOMPLETE -- Exp 6 has not closed.")
    if s.startswith("FAILED: "):
        reasons = s[len("FAILED: "):].split("; ")
        named = sorted({r.split()[0] for r in reasons if r.startswith("EXP6_")})
        return ("FAILED: " + ", ".join(named) if named else s), reasons
    raise SystemExit(f"REFUSED: unrecognised analysis status {s!r}")


def exp6_entry(an: dict, con: dict, am1: dict) -> dict:
    need_keys(an, SCHEMA["analysis_top"], "analysis")
    C = SCHEMA["contract"]
    got = {k: need(con, C[k], "contract") for k in
           ("catalog_digest", "source_digest", "code_version", "fw_policy",
            "fw_structure", "pass_ceiling")}
    for k, fk in (("catalog_digest", "catalog_digest"),
                  ("source_digest", "src_cota_opt_content_digest"),
                  ("code_version", "code_version"), ("fw_policy", "EXP6_POLICY"),
                  ("fw_structure", "EXP6_STRUCTURE"),
                  ("pass_ceiling", "pass_ceiling")):
        assert got[k] == FROZEN[fk], (k, got[k], FROZEN[fk])
    status, reasons = split_status(an["status"])
    certified = status == "EXP6_POLICY_FRONTIER_CERTIFIED"

    certified_rows, empty_rows = [], []
    for i, r in enumerate(an["frontier"]):
        if r["status"] == "CERTIFIED":
            need_keys(r, SCHEMA["frontier_certified"], f"frontier[{i}]")
            certified_rows.append({k: r[k] for k in SCHEMA["frontier_certified"]
                                   if k != "spec"})
        else:
            need_keys(r, SCHEMA["frontier_empty"], f"frontier[{i}]")
            if r["status"] not in CELL_STATUSES:
                raise SystemExit(f"REFUSED: cell status {r['status']!r}")
            empty_rows.append({
                "network": r["network"], "cell": r["cell"],
                "status": r["status"],
                "reading": ("policy infeasible under the modeled envelope -- a "
                            "result; no plan, no receipt, no finite policy cost"
                            if r["status"] == "INFEASIBLE_UNDER_ENVELOPE" else
                            "NOT a proven empty set -- analysis fails on it"),
                "minimum_service_plan_usage_vs_caps":
                    r["usage_vs_caps_of_minimum_service_plan"]})
    for n, c in an["closure"].items():
        need_keys(c, SCHEMA["closure_per_network"], f"closure.{n}")

    return {
        "title": "Modeled price of policy constraints (study safeguards) on "
                 "N0 and N3 under the Experiment 6 basin-closure procedure",
        "status": status,
        "status_verbatim": an["status"],
        "certified": certified,
        "failures": an["failures"],
        "contract": {"file": "outputs/exp6/EXP6_CONTRACT.json",
                     "file_sha256": sha256(CONTRACT),
                     "firewall_EXP6_POLICY": got["fw_policy"],
                     "firewall_EXP6_STRUCTURE": got["fw_structure"],
                     "amendment_1": {"file": "outputs/exp6/EXP6_CONTRACT_AMENDMENT_1.json",
                                     "file_sha256": sha256(AMEND1),
                                     "new_status": am1.get("new_status")},
                     "amendment_2": {"file": "outputs/exp6/EXP6_CONTRACT_AMENDMENT_2.json",
                                     "file_sha256": sha256(AMEND2),
                                     "change": json.loads(AMEND2.read_text()).get("change"),
                                     "superseded_analysis": "outputs/exp6/SUPERSEDED."
                                     "EXP6_ANALYSIS.first_run_receipt_start_encoding.json"}},
        "analysis": {"file": "outputs/exp6/EXP6_ANALYSIS.json",
                     "file_sha256": sha256(ANALYSIS)},
        "closeout_sha256": sha256(CLOSEOUT),
        "constraint_catalog": {"digest": got["catalog_digest"],
                               "file_sha256": sha256(CATALOG)},
        "canonical": ["EXPERIMENT6_CLOSEOUT.md", "outputs/exp6/EXP6_CONTRACT.json",
                      "outputs/exp6/EXP6_CONTRACT_AMENDMENT_1.json",
                      "outputs/exp6/EXP6_CONTRACT_AMENDMENT_2.json",
                      "outputs/exp6/EXP6_CONSTRAINT_CATALOG.json",
                      "outputs/exp6/EXP6_ANALYSIS.json", "outputs/exp6/initial/",
                      "outputs/exp6/closure/", "outputs/exp6/sentinels/",
                      "outputs/exp6/d35/", "outputs/exp6/preflight/",
                      *PROVENANCE_DOCS],
        "superseded": ["outputs/exp6/SUPERSEDED.EXP6_ANALYSIS.first_run_receipt_"
                       "start_encoding.json",
                       "outputs/exp6/d35/SUPERSEDED.N0.first_run.json",
                       "outputs/exp6/d35/SUPERSEDED.N3.first_run_test_plan_bug.json"],
        "superseded_why": "receipt start encoding (Amendment 2); D35 first runs "
                          "(test-plan bug) -- kept, not used",
        "evaluator": "same_route (Model B), EXP4N block certifier (8,3), "
                     "max_rounds 120, lambda 2, EXP4N common envelope "
                     f"{need(con, C['envelope_exact'], 'contract')} "
                     f"(rounded {need(con, C['envelope_rounded'], 'contract')})",
        "networks": need(con, C["networks"], "contract"),
        "source": {"code_version": got["code_version"],
                   "src_cota_opt_content_digest": got["source_digest"]},
        "preflight": need(con, C["preflight"], "contract"),
        "search_procedure": {
            "stage_1_initial": "independent Gen1 greedy start per cell under the "
                               "cell's own constraints, unchanged EXP4N certifier",
            "stage_2_closure": "explicit-anchor transfers over the frozen Hasse "
                               "edges, both directions, deterministic passes to "
                               "a fixed point (scripts/exp6_run.py closure)",
            "pass_ceiling_frozen": got["pass_ceiling"],
            "per_network": an["closure"],
            "reference_participates_in_closure": True,
            "empty_cells": "transfers receipted SKIPPED_EMPTY_FEASIBLE_SET "
                           "(Amendment 1)",
            "defined_in": {d: sha256(ROOT / d) for d in PROVENANCE_DOCS},
            "why": "D39 (Exp 5): single greedy starts land in cap-dependent "
                   "local basins; residual >= 1.70% on N4",
        },
        "record_checks": an["record_checks"],
        "monotonicity": {"initial_greedy": an["monotonicity_initial"],
                         "post_closure": an["monotonicity_post_closure"]},
        "reference_closure": an["reference_closure"],
        "firewall": an["firewall"],
        "sentinels": an["sentinels"],
        "cells": certified_rows,
        "empty_feasible_sets": empty_rows,
        "policy_cost_definition": "policy_cost_closed = closed policy-cell "
                                  "objective minus closed REF objective, same "
                                  "network; MODELED, objective units and percent",
        "greedy_only_cost_definition": "policy_cost_greedy_only = initial cell "
                                       "minus initial REF; basin_contamination = "
                                       "greedy_only minus closed; never quoted alone",
        "regimes": {
            "included": ["R1", "R2", "R3", "R4", "R6", "B1", "B2"],
            "classification": "ALL study safeguards; no documented COTA "
                              "numeric anchor (FTA C 4702.1B prescribes none)",
            "R5": "UNIMPLEMENTABLE_WITH_CURRENT_DATA (Title VI form); generic "
                  "form EXCLUDED -- not implemented before freeze",
            "R7": "EXCLUDED -- no authoritative COTA frequent-network definition",
            "cota_compliant_combined": "NOT RUN -- no defensible anchor",
        },
        "headline": headline(an),
        "basin_note": ("Closure moved both REF cells to a different basin at a "
                       "near-equal objective; the Exp 4A N3 record and the Exp 5 "
                       "N0 J100 record (bit-identical to the Exp 6 initial REFs) "
                       "are therefore not the best-known plans under the EXP4N "
                       "envelope. They remain exact records of their own "
                       "contracts and are NOT reopened; exp4a and exp5 entries "
                       "are copied verbatim. Served demand / GC are "
                       "basin-dependent at near-equal objective."),
        "physical_fleet": "UNDECIDABLE for every cell; no blocking run -- no "
                          "valid instrument (Exp 5 materializer off by "
                          "17.8-47.0% on vehicle-hours; deadhead OPEN)",
        "not_claimed": ["global optimum", "buses, fleet or vehicles",
                        "operating dollars", "deployability",
                        "COTA policy or Title VI compliance",
                        "that N4 is worth implementing",
                        "per-route headway recommendations",
                        "a finite policy cost for an empty feasible set"],
    }


def headline(an: dict) -> str:
    """Formatted from the analysis -- never typed."""
    fr = [r for r in an["frontier"] if r["status"] == "CERTIFIED"]
    parts = []
    for n in ("N0", "N3"):
        ref = next(r for r in fr if r["network"] == n and r["cell"] == "REF")
        costs = [r["policy_cost_closed_pct"] for r in fr
                 if r["network"] == n and r["cell"] != "REF"]
        parts.append(f"{n}: REF {ref['initial_objective']:,.2f} -> "
                     f"{ref['final_objective']:,.2f} under closure; closed "
                     f"policy costs {min(costs):+.3f}% to {max(costs):+.3f}%")
    st = [s for s in an["firewall"]["structure"] if s["admitted"]]
    ref_s = next(s for s in st if s["cell"] == "REF")
    empty = [f"{r['network']} {r['cell']}" for r in an["frontier"]
             if r["status"] == "INFEASIBLE_UNDER_ENVELOPE"]
    mi, mf = an["monotonicity_initial"], an["monotonicity_post_closure"]
    return (f"{an['status']}. " + "; ".join(parts) +
            f". N3 - N0 at matched policy ({len(st)} admitted): REF "
            f"{ref_s['effect_N3_minus_N0']:,.2f} ({ref_s['effect_pct_of_N0']:+.4f}%), "
            f"range {min(s['effect_pct_of_N0'] for s in st):+.4f}% to "
            f"{max(s['effect_pct_of_N0'] for s in st):+.4f}%. Empty feasible "
            f"sets: {', '.join(empty) or 'none'}. Monotonicity initial "
            f"{mi['n_violations']}/{mi['n_pairs']} violations, post-closure "
            f"{mf['n_violations']}/{mf['n_pairs']}.")


def reporting_corrections(v3: dict) -> dict:
    """Additive wording corrections to VERBATIM entries. Never edits them."""
    head = v3["experiments"]["exp1"]["headline"]
    assert "197.0 of 197.0 peak vehicles" in head, "exp1 headline changed?"
    return {
        "exp1.headline.fleet_wording": {
            "verbatim_in": ["outputs/CANONICAL_RESULTS.json (v1)",
                            "outputs/CANONICAL_RESULTS_v2.json",
                            "outputs/CANONICAL_RESULTS_v3.json",
                            "outputs/canonical/exp1_final.json "
                            "(resources, gates.fleet)",
                            "this file, experiments.exp1.headline"],
            "status": "WITHDRAWN AS A FLEET CLAIM; objective result unaffected",
            "what_the_number_is": "blocks.fleet_estimate: routewise "
                                  "cycle-over-headway peak (baseline 150.73) x "
                                  "baseline interlining factor 197/150.73 = "
                                  "1.307; baseline reads 197.0 by "
                                  "construction, plan 196.999 "
                                  "(outputs/fleet_check_modelB.json "
                                  "candidate_fleet)",
            "replacement": "at 2,516.5 of 2,517.2 vehicle-hours and within "
                           "the baseline's per-period solver peak-concurrency "
                           "proxy (enforced as a cap); physical fleet "
                           "requirement not verified",
            "physical_fleet_status": "NOT MEASURED for the Exp 1 plan (no "
                                     "valid blocking of a modified plan exists)",
            "sources": ["FLEET_AND_BLOCKING.md",
                        "docs/RELEASE_AND_REPORTING_GUIDELINES.md",
                        "README.md (Exp 1 fleet-wording correction note)",
                        "HANDOFF.md (provenance resolved 2026-09-29)"],
        },
    }


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=None,
                    help="repository holding the artifacts (default: this repo)")
    ap.add_argument("--closeout", default=None,
                    help="EXPERIMENT6_CLOSEOUT.md to hash (default: <src>/...)")
    ap.add_argument("--out", default=None,
                    help="v4 destination (default: <src>/outputs/"
                         "CANONICAL_RESULTS_v4.json)")
    a = ap.parse_args()
    if a.src or a.closeout or a.out:
        _configure(Path(a.src).resolve() if a.src else ROOT,
                   Path(a.closeout).resolve() if a.closeout else None,
                   Path(a.out).resolve() if a.out else None)
    preconditions()
    v3 = json.loads(V3.read_text())
    an = json.loads(ANALYSIS.read_text())
    con = json.loads(CONTRACT.read_text())
    assert v3["experiments"]["exp5"]["status"] == EXPECTED_V3_EXP5_STATUS
    exps = copy.deepcopy(v3["experiments"])
    assert "exp6" not in exps
    am1 = json.loads(AMEND1.read_text())
    exps["exp6"] = exp6_entry(an, con, am1)
    v4 = {"version": 4, "generated_by": "scripts/canonical_results_v4.py",
          "generated_commit": commit(),
          "predecessor": {"path": "outputs/CANONICAL_RESULTS_v3.json",
                          "sha256": sha256(V3),
                          "status": "unchanged; every v3 entry copied verbatim; "
                                    "exp6 and reporting_corrections added"},
          **{k: copy.deepcopy(v) for k, v in v3.items() if k not in (
              "version", "generated_by", "generated_commit", "predecessor",
              "experiments")},
          "reporting_corrections": reporting_corrections(v3),
          "experiments": exps}
    # Verbatim guarantees.
    for k in VERBATIM_KEYS:
        assert v4["experiments"][k] == v3["experiments"][k], k
    for k, v in v3.items():
        if k not in ("version", "generated_by", "generated_commit",
                     "predecessor", "experiments"):
            assert v4[k] == v, k
    assert v4["experiments"]["exp5"]["status"] == EXPECTED_V3_EXP5_STATUS
    assert v4["experiments"]["exp5"]["v2_entry_superseded"] == \
        v3["experiments"]["exp5"]["v2_entry_superseded"]
    V4.parent.mkdir(parents=True, exist_ok=True)
    V4.write_text(json.dumps(v4, indent=2, ensure_ascii=False))
    print(f"wrote {V4}; v3 sha {sha256(V3)[:16]} unchanged")
    for k, e in exps.items():
        print(f"  {k:6s} {str(e.get('status'))[:90]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
