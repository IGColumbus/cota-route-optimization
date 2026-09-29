#!/usr/bin/env python3
"""Experiment 7 Stage 1: fixed-plan robustness evaluation.

Every frozen solution under test is evaluated, UNCHANGED, at BASE and at every
level of `outputs/exp7/EXP7_LEVELS.json`, through the production evaluation
path, under that level's model. There is no search, no warm start, no closure
and no plan sharing: a Stage 1 number is a pure function of (frozen plan,
network variant, level).

Mechanism (one evaluation cell = one (network variant, level)):
  1. network: exp45_certify_cell.build_network (N0, N3, N4), or N0 with the
     Exp 2B splice edit (N0S); then the level's network transform
     (exp7_levels.network_for: A3 runtime, A7 route removal);
  2. model: exp3_score.solve_on_network under the level's harness view
     (exp7_levels.harness_for), lambda, waiting model and cost-weight patch,
     solver="exact" on a one-rung ladder of the variant's first solution plan,
     include_setup=True, with a x10 relaxed envelope so that the setup is
     built whatever the plan's resource use. Only the setup (the path-level
     model with its freshly enumerated path sets) is used;
  3. every solution plan of that variant is evaluated with
     judge.model.evaluate_array(h): objective = GC + lambda * w_unserved *
     unserved, plus every fitness component and resource usage. Feasibility
     against any envelope is recorded by the analysis, never enforced here.
The build plan's own evaluate_array result must equal the solve's fitness
(internal consistency check, recorded).

A7 (route removal): the frozen plan is evaluated with the removed route's
route-periods deleted (the unchanged plan on the disrupted network). This is
the only transformation ever applied to a plan, and it is recorded.

    exp7_stage1.py registry                 write/verify the frozen registry
    exp7_stage1.py cell --variant N0 --level A3_RT110
    exp7_stage1.py run --k 0 --of 2         canonical cells, sharded
    exp7_stage1.py proofs                   N3 R1_H20 emptiness at network levels
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import subprocess
import sys
import time
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

OUT = ROOT / "outputs" / "exp7" / "stage1"
EVALS = OUT / "evals"
REGISTRY = OUT / "EXP7_STAGE1_SOLUTIONS.json"
LEVELS_FILE = "outputs/exp7/EXP7_LEVELS.json"
VARIANTS = ("N0", "N3", "N4", "N0S")
SPLICE_ID = "splice-011-034-WESHIGW#2c53c24a4f24"
SPLICE_ROUTES = {"011", "034"}
SEEDS1 = (20260825, 20260826, 20260827)
SEEDS3 = (20260825, 20260826, 20260827, 20260828, 20260829)
EXP6_CELLS = ("REF", "R1_H60", "R1_H30", "R1_H20", "R2_S25", "R2_S10", "R2_S05",
              "R3_SPAN", "R4_C05", "R4_C01", "R4_C00", "R6_ADA", "B1", "B2")
FIXED_LAMBDA_BASE = 2.0


# ---------------------------------------------------------------------------
# plans
# ---------------------------------------------------------------------------
def norm_plan(raw: dict) -> dict[str, float | None]:
    """{"route|period": minutes or None (OFF)} from any persisted format
    ("r|p" or "r::p" keys; None / inf / "inf" for OFF)."""
    out = {}
    for k, v in raw.items():
        k2 = k.replace("::", "|")
        if v is None or (isinstance(v, str) and v.lower() in ("inf", "infinity")):
            out[k2] = None
        else:
            f = float(v)
            out[k2] = None if math.isinf(f) else f
    return dict(sorted(out.items()))


def plan_digest(p: dict) -> str:
    return hashlib.sha256(json.dumps(p, sort_keys=True).encode()).hexdigest()[:16]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _jsonl_plan(path: str, cell: str) -> dict:
    for ln in (ROOT / path).read_text().splitlines():
        r = json.loads(ln)
        if r.get("cell") == cell and "plan" in r:
            return r
    raise KeyError(f"{cell} not in {path}")


def build_registry() -> dict:
    """The frozen solutions under test, each with its source, plan and the
    certified numbers it carries. Built only from committed artifacts."""
    sols = []

    def add(sid, variant, findings, source, selector, raw_plan, certified):
        p = norm_plan(raw_plan)
        sols.append({"id": sid, "variant": variant, "findings": findings,
                     "source": source, "source_sha256": sha(ROOT / source),
                     "selector": selector, "plan": p,
                     "stage1_plan_digest": plan_digest(p),
                     "certified": certified})

    # F1 -- Exp 1: three lambda-2 seed plans vs the N0 current (baseline) plan
    ref0 = json.loads((ROOT / "outputs/exp6/closure/N0_REF__from_R2_S25__"
                       "aed848588abad24d.json").read_text())
    add("F1_BASELINE", "N0", ["F1"],
        "outputs/exp6/closure/N0_REF__from_R2_S25__aed848588abad24d.json",
        "baseline_headways (N0 current service, the Exp 1 control)",
        ref0["baseline_headways"], {})
    for s in SEEDS1:
        r = _jsonl_plan("outputs/seedcheck_modelB.jsonl", f"seed{s}|lam2.0|r2")
        add(f"F1_PLAN_{s}", "N0", ["F1"], "outputs/seedcheck_modelB.jsonl",
            f"cell seed{s}|lam2.0|r2", r["plan"],
            {"unserved_change_pct": r["unserved_change_pct"]})
    # F2 -- Exp 2B: control (unedited N0) and treatment (splice 011+034)
    for s in SEEDS1:
        c = _jsonl_plan("outputs/exp2b_subsets.jsonl",
                        f"b|<none>|lam2.0|seed{s}|400000/20/0")
        t = _jsonl_plan("outputs/exp2b_subsets.jsonl",
                        f"b|splice|011|034|WESHIGW|lam2.0|seed{s}|400000/20/0")
        add(f"F2_CONTROL_{s}", "N0", ["F2"], "outputs/exp2b_subsets.jsonl",
            c["cell"], c["plan"], {"modelB_unserved": c["modelB_unserved"]})
        add(f"F2_SPLICE_{s}", "N0S", ["F2"], "outputs/exp2b_subsets.jsonl",
            t["cell"], t["plan"], {"modelB_unserved": t["modelB_unserved"]})
    # F3 -- Exp 3 Stage B anchors: control (N0) and add_stop (N3), 5 seeds
    for s in SEEDS3:
        for role, var, fn in (("CONTROL", "N0", "control"),
                              ("ADDSTOP", "N3", "lengthen_add_stop")):
            src = f"outputs/exp3/d33_stageb/anchors/{fn}.{s}.json"
            a = json.loads((ROOT / src).read_text())
            add(f"F3_{role}_{s}", var, ["F3"], src, "headways", a["headways"],
                {"objective": a["objective"], "plan_digest": a["plan_digest"]})
    # F4 -- certified comparisons: Exp 4A (N3 vs N4) and Exp 5 J100 (N0 vs N4)
    for sid, var, src in (
            ("F4_N3_EXP4A", "N3", "outputs/exp4_addendum/N3.json"),
            ("F4_N4_EXP4N", "N4", "outputs/exp4_addendum/N4_canary.json"),
            ("F4_N0_J100", "N0", "outputs/exp5/cells/N0_J100.json")):
        r = json.loads((ROOT / src).read_text())
        add(sid, var, ["F4", "F5"] if sid == "F4_N0_J100" else ["F4"], src,
            "outcome.plan_EXACT", r["outcome"]["plan_EXACT"],
            {"objective": r["outcome"]["objective_EXACT"],
             "plan_digest": r["outcome"]["plan_digest"]})
    # F5 -- Exp 5 cells at 90/100/110 (joint J and peak-only P arms)
    for net, var in (("N0", "N0"), ("N4", "N4")):
        for cell in ("J090", "J110", "P090", "P110") + (("J100",) if net == "N4"
                                                          else ()):
            src = f"outputs/exp5/cells/{net}_{cell}.json"
            r = json.loads((ROOT / src).read_text())
            add(f"F5_{net}_{cell}", var, ["F5"], src, "outcome.plan_EXACT",
                r["outcome"]["plan_EXACT"],
                {"objective": r["outcome"]["objective_EXACT"],
                 "plan_digest": r["outcome"]["plan_digest"],
                 "caps": r["resource"]["requested"]})
    # F6 / AF1 -- Exp 6 closed final plans, 14 cells x N0/N3
    for net in ("N0", "N3"):
        st = json.loads((ROOT / f"outputs/exp6/closure/closure_state_{net}.json")
                        .read_text())
        for c in EXP6_CELLS:
            src = st["best"][c]
            r = json.loads((ROOT / src).read_text())
            if r["status"] != "CERTIFIED":
                sols.append({"id": f"F6_{net}_{c}", "variant": net,
                             "findings": ["F6", "AF1"], "source": src,
                             "source_sha256": sha(ROOT / src),
                             "status": r["status"], "plan": None,
                             "certified": {"status": r["status"]}})
                continue
            add(f"F6_{net}_{c}", net, ["F6", "AF1"], src, "outcome.plan_EXACT",
                r["outcome"]["plan_EXACT"],
                {"objective": r["outcome"]["objective_EXACT"],
                 "plan_digest": r["outcome"]["plan_digest"]})
    reg = {"schema": "exp7_stage1_solutions/v1", "solutions": sols,
           "n_solutions": len(sols),
           "n_evaluable": sum(1 for s in sols if s.get("plan") is not None),
           "certified_findings": {
               "F1": {"value_pct": -6.651987701966629,
                      "source": "outputs/canonical/exp1_final.json headline.unserved_demand.mean_pct"},
               "F2": {"value_pct": 0.0065, "floor_pct": 0.287,
                      "source": "outputs/exp2b_certification.json (effect_pct, floor_pts)"},
               "F3": {"value_pct": -0.18656513176548822,
                      "source": "outputs/exp3/stageB_report.json add_stop-010#22c4c35ac5b2 mean_pct"},
               "F4_N4_minus_N3": {"value": 283973.3668, "value_pct": 9.659,
                                  "source": "outputs/exp4_addendum/DELTA43.json"},
               "F4_N4_minus_N0_J100": {"source": "outputs/exp5/cells/N{0,4}_J100.json objective_EXACT"},
               "F5": {"source": "outputs/exp5/EXP5_ANALYSIS.json marginals; status EXP5_MONOTONICITY_FAILURE (12 N4 pairs) preserved"},
               "F6": {"source": "outputs/exp6/EXP6_ANALYSIS.json / EXP6_CLOSEOUT_TABLES.md"}}}
    return reg


# ---------------------------------------------------------------------------
# network variants and one evaluation cell
# ---------------------------------------------------------------------------
def variant_network(variant: str, st: dict):
    import exp45_certify_cell as CC
    if variant in ("N0", "N3", "N4"):
        return CC.build_network(variant, st)
    if variant == "N0S":
        from cota_opt.geometry import SegmentTimeModel, apply_edits
        from cota_opt.mutate import edit_from_record
        H = st["H"]
        net, ts = H.baseline.network, H.baseline.tstats
        pool = json.loads((ROOT / "outputs/exp3/mutation_pool.json")
                          .read_text())["mutations"]
        rec = {m["id"]: m for m in pool}[SPLICE_ID]
        stm = SegmentTimeModel.fit(net, st["sg"])
        ed = apply_edits(net, ts, stm, [edit_from_record(rec)])
        cd = CC.network_content_digest(ed.network, ed.tstats)
        return ed.network, ed.tstats, {
            "state_key": "exp2b|" + SPLICE_ID, "state_digest": cd,
            "cardinality": 1, "members": [SPLICE_ID],
            "construction": "geometry.apply_edits(H.baseline, "
                            "[edit_from_record(pool[splice-011-034])])",
            "network_label": "N0 + Exp 2B splice 011+034 at WESHIGW"}
    raise ValueError(variant)


def _h(model, plan: dict[str, float | None], removed: set[str]):
    import numpy as np
    keys = [f"{r}|{p}" for (r, p) in model.keys]
    pk = {k for k in plan if k.split("|", 1)[0] not in removed}
    if set(keys) != pk:
        raise ValueError(f"plan keys != model keys: missing "
                         f"{sorted(set(keys) - pk)[:4]}, extra "
                         f"{sorted(pk - set(keys))[:4]}")
    return np.array([math.inf if plan[k] is None else float(plan[k])
                     for k in keys], float)


FIELDS = ("generalized_cost", "unserved_demand", "served_demand",
          "gc_per_served_trip", "revenue_veh_hours", "peak_vehicles")


def evaluate_cell(variant: str, level_name: str, out: Path) -> dict:
    import exp45_certify_cell as CC
    import exp5_model_resource as MR
    import exp7_levels as L
    import cota_opt.exp3_score as E3
    from cota_opt.configs import load_constraints
    from exp45_contracts import SEED
    reg = json.loads(REGISTRY.read_text())
    sols = [s for s in reg["solutions"]
            if s["variant"] == variant and s.get("plan") is not None]
    lv = L.BASE if level_name == "BASE" else L.from_file(ROOT / LEVELS_FILE,
                                                         level_name)
    t0 = time.time()
    if variant == "N0S":
        rm = [json.loads(pj) for k, pj in lv.network if k == "remove_route"]
        if rm:
            rid = L.route_ranking(ROOT / rm[0]["ranking_file"], "N0")[
                int(rm[0]["rank"]) - 1]
            if rid in SPLICE_ROUTES:
                import exp45_certify_cell as CC2
                rec = {"schema": "exp7_stage1_cell/v1", "variant": variant,
                       "level": lv.payload(), "level_digest": lv.digest,
                       "status": "NOT_APPLICABLE",
                       "why": f"A7 removes route {rid}, which is a member of "
                              f"the Exp 2B splice treatment {SPLICE_ID}; the "
                              f"treatment is undefined on that network",
                       "rows": {}, "n_rows": 0, "n_errors": 0,
                       "internal_consistency_build_plan_equals_solve": True,
                       "registry_sha256": sha(REGISTRY), "written_utc": CC2.utc()}
                out.parent.mkdir(parents=True, exist_ok=True)
                CC2.atomic_write_json(out, rec)
                return rec
    st = CC.boot()
    net, ts, ident = variant_network(variant, st)
    net, ts, ident = L.network_for(net, ts, ident, lv,
                                   "N0" if variant == "N0S" else variant)
    removed = {t.get("removed_route") for t in ident.get("network_transform", [])
               if "removed_route" in t} - {None}
    H = L.harness_for(st["H"], lv)
    relaxed = MR.scale(MR.load_base(), 10.0, 10.0).to_constraints(load_constraints())
    build = sols[0]
    bplan = {tuple(k.split("|", 1)): (math.inf if v is None else v)
             for k, v in build["plan"].items() if k.split("|", 1)[0] not in removed}
    with L.weights_patch(lv):
        r = E3.solve_on_network(
            net, ts, harness=H, stops_gdf=st["sg"], lam=float(lv.lam),
            seed=SEED, iterations=20_000, restarts=1, width=0,
            constraints=relaxed, pathset_cache={}, waiting_model=lv.waiting_model,
            starts="greedy", allow_off=True, solver="exact",
            exact_max_combinations=10,
            ladder_override={k: [v] for k, v in bplan.items()},
            include_setup=True)
        model = r["judge"].model
        w = float(model.w.unserved)
        rows = {}
        for s in sols:
            try:
                h = _h(model, s["plan"], removed)
                f = model.evaluate_array(h)
                rows[s["id"]] = {
                    "objective": float(f.scalarized(w, float(lv.lam))),
                    **{k: float(getattr(f, k)) for k in FIELDS},
                    "peak_by_period": {p: float(v) for p, v in
                                       f.peak_by_period.items()},
                    "n_off": int(sum(1 for v in h if math.isinf(v))),
                    "plan_restricted_routes": sorted(removed & {
                        k.split("|", 1)[0] for k in s["plan"]})}
            except Exception as ex:
                rows[s["id"]] = {"error": f"{type(ex).__name__}: {ex}"[:400]}
        solve_obj = float(r["fit"].scalarized(w, float(lv.lam)))
    cons_check = rows.get(build["id"], {}).get("objective") == solve_obj
    rec = {"schema": "exp7_stage1_cell/v1", "variant": variant,
           "level": lv.payload(), "level_digest": lv.digest,
           "identity": ident, "lam": float(lv.lam),
           "waiting_model": lv.waiting_model, "w_unserved": w,
           "build_solution": build["id"],
           "internal_consistency_build_plan_equals_solve": cons_check,
           "evaluator_checks": CC._clean(dict(r["judge"].checks)),
           "pathset_total_paths": r["judge"].checks.get("total_paths"),
           "rows": rows, "n_rows": len(rows),
           "n_errors": sum(1 for v in rows.values() if "error" in v),
           "registry_sha256": sha(REGISTRY),
           "provenance": {"src_cota_opt_content_digest": CC.src_content_digest(),
                          "runner_sha256": {n: CC.sha256_file(
                              ROOT / "scripts" / n)[:16] for n in (
                              "exp7_stage1.py", "exp7_levels.py")},
                          "levels_file_sha256": sha(ROOT / LEVELS_FILE)},
           "seconds": round(time.time() - t0, 1), "written_utc": CC.utc()}
    out.parent.mkdir(parents=True, exist_ok=True)
    CC.atomic_write_json(out, rec)
    return rec


# ---------------------------------------------------------------------------
# driver
# ---------------------------------------------------------------------------
def level_names() -> list[str]:
    d = json.loads((ROOT / LEVELS_FILE).read_text())
    return ["BASE"] + [p["name"] for p in d["levels"]]


def canonical() -> list[tuple[str, str]]:
    """BASE for every variant first (reproduction is checked first), then
    level-major order. N4 cells are the slowest; interleaving keeps lanes
    balanced under k % of sharding."""
    out = []
    for lvn in level_names():
        for v in VARIANTS:
            out.append((v, lvn))
    return out


def cell_path(v, lvn) -> Path:
    return EVALS / v / f"{lvn}.json"


def run(k: int, of: int) -> int:
    log = open(OUT / f"run{k}.events.log", "a")
    for i, (v, lvn) in enumerate(canonical()):
        if i % of != k:
            continue
        p = cell_path(v, lvn)
        if p.exists():
            continue
        t0 = time.time()
        log.write(f"{time.strftime('%H:%M:%S')} start {v} {lvn}\n")
        log.flush()
        rc = subprocess.call([sys.executable, __file__, "cell", "--variant", v,
                              "--level", lvn], cwd=ROOT)
        log.write(f"{time.strftime('%H:%M:%S')} end {v} {lvn} rc={rc} "
                  f"{time.time() - t0:.0f}s\n")
        log.flush()
        os.fsync(log.fileno())
        if rc != 0:
            log.write("halt: cell failed\n")
            return 3
    return 0


SMOKE = [("N0", "BASE"), ("N0S", "BASE"), ("N3", "BASE"), ("N4", "BASE"),
         ("N0", "A1_NC025"), ("N0", "A2_BOOT01"), ("N0", "A3_RT110"),
         ("N0", "A3_RTNOISE"), ("N0", "A5_TP200"), ("N0", "A6_WALKSPD85"),
         ("N0", "A6_MAXWALK75"), ("N0", "A7_RM01"), ("N4", "A7_RM01")]
SMOKE_DIR = ROOT / "outputs" / "exp7" / "preflight" / "stage1"


def smoke(k: int, of: int) -> int:
    """G4 pre-launch smoke: every NEW level kind (non-commute add, LODES
    bootstrap, runtime scale, runtime noise, transfer-penalty patch, walk
    speed, walk caps, route removal on N0 and N4) plus BASE on every variant,
    through this evaluator. Verdict by smoke_verdict()."""
    for i, (v, lvn) in enumerate(SMOKE):
        if i % of != k:
            continue
        p = SMOKE_DIR / f"{v}_{lvn}.json"
        if p.exists():
            continue
        subprocess.call([sys.executable, "-c",
                         "import sys; sys.path.insert(0,'scripts'); "
                         "import exp7_stage1 as S; from pathlib import Path; "
                         f"S.evaluate_cell('{v}','{lvn}', Path('{p}'))"], cwd=ROOT)
    return 0


def smoke_verdict() -> int:
    reg = json.loads(REGISTRY.read_text())
    cert = {s["id"]: s["certified"].get("objective") for s in reg["solutions"]
            if s.get("plan") is not None}
    rows, ok = {}, True
    base = {}
    for v, lvn in SMOKE:
        p = SMOKE_DIR / f"{v}_{lvn}.json"
        if not p.exists():
            rows[f"{v}/{lvn}"] = {"present": False}
            ok = False
            continue
        r = json.loads(p.read_text())
        row = {"present": True, "n_errors": r["n_errors"],
               "consistent": r["internal_consistency_build_plan_equals_solve"],
               "seconds": r.get("seconds")}
        ok &= r["n_errors"] == 0 and row["consistent"]
        if lvn == "BASE":
            base[v] = r["rows"]
            rep = {sid: (x["objective"] == float(cert[sid]))
                   for sid, x in r["rows"].items()
                   if cert.get(sid) is not None and sid.startswith(("F4_", "F5_", "F6_"))}
            row["certified_F4F5F6_bit_exact"] = rep
            ok &= all(rep.values())
            f3 = {sid: [x["objective"], float(cert[sid])]
                  for sid, x in r["rows"].items()
                  if sid.startswith("F3_") and cert.get(sid) is not None}
            row["F3_stage1_vs_certified"] = f3
        rows[f"{v}/{lvn}"] = row
    for v, lvn in SMOKE:
        if lvn == "BASE" or not rows[f"{v}/{lvn}"].get("present"):
            continue
        r = json.loads((SMOKE_DIR / f"{v}_{lvn}.json").read_text())["rows"]
        moved = any(r[k]["objective"] != base[v][k]["objective"] for k in r
                    if k in base.get(v, {}))
        rows[f"{v}/{lvn}"]["reaches"] = moved
        ok &= moved
    out = {"schema": "exp7_stage1_smoke/v1", "rows": rows, "passed": bool(ok)}
    (SMOKE_DIR / "SMOKE_VERDICT.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1)[:3000])
    return 0 if ok else 3


def proofs() -> int:
    """N3 R1_H20 is INFEASIBLE_UNDER_ENVELOPE at BASE (Exp 6 Amendment 1).
    Its feasibility depends on the network, so it is re-established on the
    production path at every level that transforms the network (A3, A7)."""
    import exp7_levels as L
    cat = json.loads((ROOT / "outputs/exp6/EXP6_CONTRACT.json").read_text())[
        "catalog"]["digest"]
    d = json.loads((ROOT / LEVELS_FILE).read_text())
    for p in d["levels"]:
        lv = L.from_payload(p)
        if not lv.network:
            continue
        out = OUT / "emptiness" / f"N3_R1_H20__{lv.name}.json"
        if out.exists():
            continue
        out.parent.mkdir(parents=True, exist_ok=True)
        rc = subprocess.call([sys.executable, str(ROOT / "scripts/exp7_infeasible_cell.py"),
                              "--network", "N3", "--cell", "R1_H20",
                              "--catalog-digest", cat, "--level", lv.name,
                              "--level-file", LEVELS_FILE,
                              "--out", str(out.relative_to(ROOT))], cwd=ROOT)
        if not out.exists():
            print(f"proof produced no record for {lv.name} rc={rc}")
            return 3
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("registry")
    c = sub.add_parser("cell")
    c.add_argument("--variant", required=True, choices=VARIANTS)
    c.add_argument("--level", required=True)
    r = sub.add_parser("run")
    r.add_argument("--k", type=int, required=True)
    r.add_argument("--of", type=int, required=True)
    sub.add_parser("proofs")
    sm = sub.add_parser("smoke")
    sm.add_argument("--k", type=int, default=0)
    sm.add_argument("--of", type=int, default=1)
    sub.add_parser("smoke-verdict")
    a = ap.parse_args()
    if a.cmd == "smoke":
        return smoke(a.k, a.of)
    if a.cmd == "smoke-verdict":
        return smoke_verdict()
    if a.cmd == "registry":
        reg = build_registry()
        if REGISTRY.exists():
            old = json.loads(REGISTRY.read_text())
            if old != reg:
                raise SystemExit("registry differs from the frozen one; refuse")
            print("registry verified", reg["n_solutions"])
            return 0
        OUT.mkdir(parents=True, exist_ok=True)
        REGISTRY.write_text(json.dumps(reg, indent=1, sort_keys=True))
        print("registry written", reg["n_solutions"], reg["n_evaluable"])
        return 0
    if a.cmd == "cell":
        p = cell_path(a.variant, a.level)
        try:
            rec = evaluate_cell(a.variant, a.level, p)
        except Exception as e:
            p.parent.mkdir(parents=True, exist_ok=True)
            (p.parent / f"ERROR.{p.name}").write_text(json.dumps({
                "error": f"{type(e).__name__}: {e}"[:800],
                "traceback": traceback.format_exc()[-4000:]}, indent=1))
            raise
        print(a.variant, a.level, rec["n_rows"], "rows", rec["n_errors"],
              "errors", rec.get("seconds"), "s", rec.get("status", ""))
        return 0 if rec["n_errors"] == 0 and \
            rec["internal_consistency_build_plan_equals_solve"] else 3
    if a.cmd == "run":
        return run(a.k, a.of)
    return proofs()


if __name__ == "__main__":
    raise SystemExit(main())
