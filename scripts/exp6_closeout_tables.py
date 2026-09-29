#!/usr/bin/env python3
"""Mechanical tables for EXPERIMENT6_CLOSEOUT.md -- every number from an artifact.

Reads (read-only) the Exp 6 artifacts under --src (default: the repository this
script sits in; in the parallel-prep worktree pass the main checkout), and
writes EXP6_CLOSEOUT_TABLES.json + .md into --out-dir (default outputs/exp6/ of THIS repository).

No re-scoring, no solver. Sources:
  outputs/exp6/EXP6_ANALYSIS.json            gates, frontier, closure, firewall
  outputs/exp6/closure/closure_state_<n>.json final record per cell
  outputs/exp6/initial/<n>_<cell>.json       initial records (n_off, served)
  outputs/exp6/run/*.events.log              wall-clock times (UTC, HH:MM:SS)
  outputs/exp4_addendum/N3.json, outputs/exp5/cells/N0_J100.json   history
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]


def load(p: Path):
    return json.loads(p.read_text())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=str(HERE))
    ap.add_argument("--out-dir", default=None,
                    help="default: <this repo>/outputs/exp6 (as "
                         "EXP6_CLOSEOUT_TABLES.*); prep run: prep/out")
    a = ap.parse_args()
    S = Path(a.src)
    E = S / "outputs/exp6"
    an = load(E / "EXP6_ANALYSIS.json")
    out: dict = {"source_root": str(S),
                 "analysis_sha256": hashlib.sha256(
                     (E / "EXP6_ANALYSIS.json").read_bytes()).hexdigest(),
                 "analysis_status": an["status"]}

    cells = [r["cell"] for r in an["frontier"] if r["network"] == "N0"]
    rows = {(r["network"], r["cell"]): r for r in an["frontier"]}

    # initial / final records for served & OFF on both ends
    recs = {}
    for n in ("N0", "N3"):
        st = load(E / f"closure/closure_state_{n}.json")
        for c in cells:
            ip = E / f"initial/{n}_{c}.json"
            fp = S / st["best"][c]
            recs[(n, c)] = (load(ip), load(fp), st["best"][c])

    def fx(rec, k):
        return float(rec["outcome"]["fitness_EXACT"][k])

    table = []
    for n in ("N0", "N3"):
        for c in cells:
            r = rows[(n, c)]
            ir, fr, fpath = recs[(n, c)]
            row = {"network": n, "cell": c, "status": r["status"],
                   "final_record": fpath}
            if r["status"] == "CERTIFIED":
                row.update({
                    "initial_objective": r["initial_objective"],
                    "final_objective": r["final_objective"],
                    "initial_to_final_pct": 100 * (r["final_objective"] -
                                                   r["initial_objective"]) /
                    r["initial_objective"],
                    "initial_plan": r["initial_plan_digest"],
                    "final_plan": r["final_plan_digest"],
                    "winning_basin": r["winning_basin"],
                    "anchor_source_cell": (fr.get("anchor") or {}).get("source_cell"),
                    "greedy_cost": r["policy_cost_greedy_only"],
                    "greedy_cost_pct": r["policy_cost_greedy_only_pct"],
                    "closed_cost": r["policy_cost_closed"],
                    "closed_cost_pct": r["policy_cost_closed_pct"],
                    "basin_contamination": r["basin_contamination"],
                    "served_initial": fx(ir, "served_demand"),
                    "served_final": r["served_demand"],
                    "unserved_final": r["unserved_demand"],
                    "gc_final": r["generalized_cost"],
                    "gc_initial": fx(ir, "generalized_cost"),
                    "gc_per_served_final": r["gc_per_served_trip"],
                    "n_off_initial": ir["outcome"]["n_off"],
                    "n_off_final": r["n_off"],
                    "n_baseline_on_now_off": r["n_baseline_on_now_off"],
                    "hours_used": r["hours_used"], "hours_cap": r["hours_cap"],
                    "binding_resource": r["binding_resource"],
                    "policy_measure": r["policy_measure"],
                    "rounds_initial": r["rounds_initial"],
                    "rounds_final": r["rounds_final"]})
            else:
                row["usage_vs_caps_of_minimum_service_plan"] = \
                    r["usage_vs_caps_of_minimum_service_plan"]
            table.append(row)
    out["cells"] = table

    # identical final plans per network
    groups = {}
    for n in ("N0", "N3"):
        g: dict = {}
        for r in table:
            if r["network"] == n and r["status"] == "CERTIFIED":
                g.setdefault(r["final_plan"], []).append(r["cell"])
        groups[n] = {k: v for k, v in g.items() if len(v) > 1}
    out["identical_final_plans"] = groups

    # structure N3 - N0 (firewall) closed, and greedy-only from initial objectives
    st_rows = []
    for s in an["firewall"]["structure"]:
        c = s["cell"]
        r0, r3 = rows[("N0", c)], rows[("N3", c)]
        d = {"cell": c, "admitted": s["admitted"]}
        if s["admitted"]:
            d.update(closed_effect=s["effect_N3_minus_N0"],
                     closed_effect_pct=s["effect_pct_of_N0"],
                     greedy_only_raw_pct=100 * (r3["initial_objective"] -
                                                r0["initial_objective"]) /
                     r0["initial_objective"],
                     cost_diff_pct_points=r3["policy_cost_closed_pct"] -
                     r0["policy_cost_closed_pct"])
        else:
            d["note"] = s.get("note")
        st_rows.append(d)
    out["structure"] = st_rows
    adm = [x for x in st_rows if x["admitted"]]
    out["structure_range_pct"] = [min(x["closed_effect_pct"] for x in adm),
                                  max(x["closed_effect_pct"] for x in adm)]

    # history: initial REF vs Exp 4A N3 / Exp 5 N0 J100
    h = {}
    for n, p in (("N3", "outputs/exp4_addendum/N3.json"),
                 ("N0", "outputs/exp5/cells/N0_J100.json")):
        old = load(S / p)
        ir = recs[(n, "REF")][0]
        h[n] = {"historical_record": p,
                "historical_objective": old["outcome"]["objective_EXACT"],
                "historical_plan": old["outcome"]["plan_digest"],
                "exp6_initial_REF_objective": ir["outcome"]["objective_EXACT"],
                "exp6_initial_REF_plan": ir["outcome"]["plan_digest"],
                "bit_identical": (old["outcome"]["objective_EXACT"] ==
                                  ir["outcome"]["objective_EXACT"] and
                                  old["outcome"]["plan_digest"] ==
                                  ir["outcome"]["plan_digest"])}
    out["history_check"] = h

    # contamination summary
    cert = [r for r in table if r["status"] == "CERTIFIED" and r["cell"] != "REF"]
    out["contamination_summary"] = {
        "n_cells": len(cert),
        "n_negative_greedy_cost": sum(r["greedy_cost"] < 0 for r in cert),
        "negative_greedy": [(r["network"], r["cell"], r["greedy_cost_pct"])
                            for r in cert if r["greedy_cost"] < 0],
        "max_abs_contamination_pct_points": max(
            abs(r["greedy_cost_pct"] - r["closed_cost_pct"]) for r in cert),
        "n_cells_changed_basin": {n: len(an["closure"][n]["cells_changed_basin"])
                                  for n in ("N0", "N3")},
    }

    # wall clock from event logs
    ev = {}
    for f in sorted((E / "run").glob("*.events.log")):
        lines = [x for x in f.read_text().splitlines() if x.strip()]
        ev[f.name] = {"first": lines[0], "last": lines[-1],
                      "notable": [x for x in lines if not (" start " in x or
                                  " end " in x)]}
    out["event_logs"] = ev

    P = Path(a.out_dir).resolve() if a.out_dir else HERE / "outputs/exp6"
    P.mkdir(parents=True, exist_ok=True)
    (P / "EXP6_CLOSEOUT_TABLES.json").write_text(json.dumps(out, indent=2) + "\n")

    # markdown tables
    md = ["# Exp 6 closeout tables (generated by scripts/exp6_closeout_tables.py)", "",
          f"Source analysis sha256 `{out['analysis_sha256'][:16]}`, status "
          f"`{out['analysis_status']}`.", ""]
    for n in ("N0", "N3"):
        md += [f"## {n}", "",
               "| cell | status | initial obj | final obj | Δ init→final % | "
               "greedy-only cost % | closed cost % | closed cost (abs) | "
               "contamination (pp) | winning basin (from) | final plan | served init→final | OFF init→final |",
               "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
        for r in table:
            if r["network"] != n:
                continue
            if r["status"] != "CERTIFIED":
                u = r["usage_vs_caps_of_minimum_service_plan"]
                md.append(f"| {r['cell']} | **{r['status']}** | — | — | — | — | "
                          f"**policy infeasible under the modeled envelope** | — | — | — | — | — | "
                          f"early {float(u['early'][0]):.4f} > cap {float(u['early'][1]):.4f} |")
                continue
            src = r["anchor_source_cell"] or ""
            md.append(
                f"| {r['cell']} | CERTIFIED | {r['initial_objective']:,.2f} | "
                f"{r['final_objective']:,.2f} | {r['initial_to_final_pct']:+.3f} | "
                f"{r['greedy_cost_pct']:+.3f} | {r['closed_cost_pct']:+.3f} | "
                f"{r['closed_cost']:,.2f} | "
                f"{r['greedy_cost_pct'] - r['closed_cost_pct']:+.3f} | "
                f"{r['winning_basin']}{' (' + src + ')' if src else ''} | "
                f"`{r['final_plan']}` | {r['served_initial']:,.0f} → "
                f"{r['served_final']:,.0f} | {r['n_off_initial']} → {r['n_off_final']} |")
        md.append("")
    md += ["## N3 − N0 at matched policy (EXP6_STRUCTURE)", "",
           "| cell | admitted | closed N3−N0 | closed % of N0 | greedy-only raw % | "
           "policy-cost difference (pp, N3−N0) |", "|---|---|---|---|---|---|"]
    for x in st_rows:
        if x["admitted"]:
            md.append(f"| {x['cell']} | yes | {x['closed_effect']:,.2f} | "
                      f"{x['closed_effect_pct']:+.4f} | {x['greedy_only_raw_pct']:+.4f} | "
                      f"{x['cost_diff_pct_points']:+.4f} |")
        else:
            md.append(f"| {x['cell']} | — | {x['note']} | | | |")
    md += ["", "## Identical final plans", ""]
    for n, g in groups.items():
        for d, cs in g.items():
            md.append(f"* {n} `{d}`: {', '.join(cs)}")
    (P / "EXP6_CLOSEOUT_TABLES.md").write_text("\n".join(md) + "\n")
    print(json.dumps({k: out[k] for k in ("identical_final_plans",
                                          "structure_range_pct",
                                          "history_check",
                                          "contamination_summary")}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
