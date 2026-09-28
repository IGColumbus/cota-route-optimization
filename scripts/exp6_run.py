#!/usr/bin/env python3
"""Experiment 6 production driver.

    exp6_run.py plan
    exp6_run.py initial --k 0 --of 2     one fresh subprocess per cell
    exp6_run.py closure --network N0     deterministic nesting closure
    exp6_run.py sentinels                reversed-order reruns of initial cells

Initial: the complete canonical (network, cell) list, sharded index % of.
Closure (per network, one writer): passes over the frozen Hasse edge list, each
edge forward (tighter plan -> looser cell) then reverse (looser plan -> tighter
cell). An attempt is:
  * pre-checked under the target cell's compiled policy (the only mathematics
    that differs between cells -- every cell shares the resource envelope);
    a violating plan is REFUSED and receipted without running;
  * skipped (receipted) if the plan is already the target's best plan, or if
    the same (target, plan) was attempted before -- certification is
    deterministic, so the result is known;
  * otherwise run as an explicit-anchor certification of the target cell,
    whose own admission re-verifies feasibility on the production path.
A result better than the target's best by more than 1e-9 replaces it.
Passes repeat until one full pass improves nothing; the ceiling is frozen in
the contract. Every attempt appends one receipt line to the network's ledger
(fsync'd), and the current best per cell is kept in closure_state_<net>.json.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import exp45_certify_cell as CC  # noqa: E402
import exp6_grid as G  # noqa: E402

OUT = ROOT / "outputs" / "exp6"
INIT = OUT / "initial"
CLOS = OUT / "closure"
SENT = OUT / "sentinels"
RUN = OUT / "run"
CONTRACT = OUT / "EXP6_CONTRACT.json"
SENTINELS = (("N3", "R4_C01"), ("N0", "R2_S10"), ("N3", "REF"), ("N0", "REF"))
IMPROVE_EPS = 1e-9


def contract() -> dict:
    if not CONTRACT.exists():
        raise SystemExit("EXP6_CONTRACT.json is not frozen; no production run")
    return json.loads(CONTRACT.read_text())


def canonical() -> list[tuple[str, str]]:
    cells = list(G.specs("X"))
    out = [(n, c) for c in cells for n in G.NETWORKS]
    assert len(out) == 28 and len(set(out)) == 28
    return out


def halts() -> list[str]:
    return sorted(str(p.relative_to(OUT)) for d in (INIT, CLOS, SENT)
                  if d.exists() for p in d.glob("*.json")
                  if p.name.startswith(("EXP6_", "ERROR.")))


def cell_cmd(net, cell, role, out: Path, cat: str, anchor: Path | None = None,
             label: str = ""):
    cmd = [sys.executable, str(ROOT / "scripts/exp6_cell.py"), "--network",
           net, "--cell", cell, "--role", role, "--catalog-digest", cat,
           "--out", str(out.relative_to(ROOT)),
           "--heartbeat", str((RUN / f"hb_{net}_{cell}.json").relative_to(ROOT))]
    if anchor is not None:
        cmd += ["--anchor-from", str(anchor.relative_to(ROOT)),
                "--anchor-label", label]
    return cmd


def logger(name):
    RUN.mkdir(parents=True, exist_ok=True)
    f = open(RUN / f"{name}.events.log", "a")

    def log(m):
        f.write(f"{time.strftime('%H:%M:%S')} {m}\n")
        f.flush()
        os.fsync(f.fileno())
    return log


def ensure(out: Path, cmd, log) -> dict:
    if out.exists():
        return json.loads(out.read_text())
    log(f"start {out.name}")
    t0 = time.time()
    rc = subprocess.call(cmd, cwd=ROOT)
    log(f"end   {out.name} rc={rc} {time.time() - t0:.0f}s")
    if rc != 0 or not out.exists():
        raise SystemExit(f"cell failed rc={rc}: {out}")
    return json.loads(out.read_text())


def check_cell(rec: dict, path: Path, log):
    if rec["status"] != "CERTIFIED":
        return
    o = rec["outcome"]
    status = None
    if not (o["converged"] and o["rounds"] < 120):
        status = "EXP6_CONVERGENCE_FAILURE"
    elif not rec["resource"]["feasible_under_full_target_constraints"]:
        status = "EXP6_INFEASIBLE_CERTIFIED_PLAN"
    if status:
        (path.parent / f"{status}.{path.name}").write_text(json.dumps(
            {"status": status, "cell": path.name}, indent=1))
        log(f"!!! {status} {path.name}")
        raise SystemExit(4)


def initial(k: int, of: int) -> int:
    con = contract()
    cat = con["catalog"]["digest"]
    log = logger(f"initial{k}")
    INIT.mkdir(parents=True, exist_ok=True)
    for i, (n, c) in enumerate(canonical()):
        if i % of != k:
            continue
        if halts():
            log(f"halt present {halts()}")
            return 3
        out = INIT / f"{n}_{c}.json"
        rec = ensure(out, cell_cmd(n, c, "initial", out, cat), log)
        check_cell(rec, out, log)
    log("initial shard complete")
    return 0


def _plan_vec(rec, keys):
    import numpy as np
    p = rec["outcome"]["plan_EXACT"]
    return np.array([math.inf if p[f"{r}|{q}"] is None else float(p[f"{r}|{q}"])
                     for (r, q) in keys])


def closure(net: str) -> int:
    con = contract()
    cat = con["catalog"]["digest"]
    ceiling = int(con["closure"]["pass_ceiling"])
    edges = [tuple(e) for e in con["nesting"]["adjacent_edges"]]
    log = logger(f"closure_{net}")
    CLOS.mkdir(parents=True, exist_ok=True)
    cells = list(G.specs(cat))
    for c in cells:
        if not (INIT / f"{net}_{c}.json").exists():
            raise SystemExit(f"initial {net}_{c} missing; closure refuses an "
                             f"incomplete upstream stage (OPERATIONS 13)")
    # compiled policies for the pre-check, from the same objects the setup uses
    from cota_opt.configs import load_constraints  # noqa: F401
    comp = _compile_all(net, cat)
    state_p = CLOS / f"closure_state_{net}.json"
    ledger = CLOS / f"closure_ledger_{net}.jsonl"
    if state_p.exists():
        state = json.loads(state_p.read_text())
    else:
        state = {"best": {c: str((INIT / f"{net}_{c}.json").relative_to(ROOT))
                          for c in cells},
                 "found_in_pass": {c: 0 for c in cells},
                 "tried": [], "passes_completed": 0, "fixed_point": False}
    tried = set(tuple(t) for t in state["tried"])

    def rec_of(c):
        return json.loads((ROOT / state["best"][c]).read_text())

    def write_state():
        CC.atomic_write_json(state_p, state)

    def receipt(r):
        with open(ledger, "a") as f:
            f.write(json.dumps(r, sort_keys=True) + "\n")
            f.flush()
            os.fsync(f.fileno())

    p = state["passes_completed"]
    while not state["fixed_point"]:
        if p >= ceiling:
            (CLOS / f"EXP6_START_CLOSURE_FAILURE.{net}.json").write_text(
                json.dumps({"status": "EXP6_START_CLOSURE_FAILURE",
                            "network": net, "passes": p}, indent=1))
            log("!!! EXP6_START_CLOSURE_FAILURE")
            return 3
        p += 1
        improved = False
        for (a, b) in edges:
            for src, tgt, direction in ((a, b, "forward"), (b, a, "reverse")):
                srec = rec_of(src)
                trec = rec_of(tgt)
                sdig = srec["outcome"]["plan_digest"]
                before = float(trec["outcome"]["objective_EXACT"])
                r = {"network": net, "pass": p, "edge": [a, b],
                     "direction": direction, "source_cell": src,
                     "target_cell": tgt, "source_record": state["best"][src],
                     "source_plan_digest": sdig,
                     "target_policy_digest": comp[tgt]["digest"],
                     "objective_before": repr(before),
                     "target_best_before": state["best"][tgt]}
                v = comp[tgt]["violation"](srec)
                r["precheck_policy_violation"] = v
                if v > 0:
                    r.update(action="REFUSED_INFEASIBLE_UNDER_TARGET",
                             reason=f"policy violation {v} under {tgt}")
                    receipt(r)
                    continue
                if sdig == trec["outcome"]["plan_digest"]:
                    r.update(action="SKIPPED_IDENTICAL_PLAN")
                    receipt(r)
                    continue
                key = (tgt, sdig)
                if key in tried:
                    r.update(action="SKIPPED_ALREADY_ATTEMPTED")
                    receipt(r)
                    continue
                out = CLOS / f"{net}_{tgt}__from_{src}__{sdig}.json"
                res = ensure(out, cell_cmd(
                    net, tgt, "closure_transfer", out, cat,
                    anchor=ROOT / state["best"][src],
                    label=f"pass {p} {direction}: {src} -> {tgt}"), log)
                tried.add(key)
                state["tried"] = sorted([list(t) for t in tried])
                r["result_record"] = str(out.relative_to(ROOT))
                if res["status"] != "CERTIFIED":
                    r.update(action="REFUSED_BY_CERTIFIER",
                             reason=res.get("refusal", "")[:300])
                    receipt(r)
                    write_state()
                    continue
                check_cell(res, out, log)
                after = float(res["outcome"]["objective_EXACT"])
                r.update(action="RAN", objective_after=repr(after),
                         returned_plan_digest=res["outcome"]["plan_digest"],
                         rounds=res["outcome"]["rounds"],
                         converged=res["outcome"]["converged"],
                         enforced_policy_digest=(res.get("policy") or {}).get(
                             "setup_policy_digest"),
                         improved=after < before - IMPROVE_EPS)
                if after < before - IMPROVE_EPS:
                    state["best"][tgt] = str(out.relative_to(ROOT))
                    state["found_in_pass"][tgt] = p
                    improved = True
                    log(f"improved {tgt}: {before:.4f} -> {after:.4f} via {src}")
                receipt(r)
                write_state()
        state["passes_completed"] = p
        if not improved:
            state["fixed_point"] = True
        write_state()
        log(f"pass {p} complete; improved={improved}")
    log("closure fixed point reached")
    return 0


def _compile_all(net: str, cat: str) -> dict:
    """Compiled policy per cell on this network, for the admission pre-check.

    Built exactly as exp2.build_setup builds it: same keys order (the
    record's plan keys resolved against the setup's model keys), same
    baseline headways, route stop sets and projected stop coordinates."""
    import numpy as np
    from pyproj import Transformer
    st = CC.boot()
    netw, _, _ = CC.build_network(net, st)
    ref = json.loads((INIT / f"{net}_REF.json").read_text())
    keys = [tuple(k.split("|", 1)) for k in sorted(ref["outcome"]["plan_EXACT"])]
    bh = ref["baseline_headways"]
    base = {k: (math.inf if bh[f"{k[0]}|{k[1]}"] is None
                else float(bh[f"{k[0]}|{k[1]}"])) for k in keys}
    tr = Transformer.from_crs("EPSG:4326",
                              st["H"].assumptions["crs"]["projected"],
                              always_xy=True)
    xy = {s: tr.transform(v.lon, v.lat) for s, v in netw.stops.items()}
    out = {}
    for c, spec in G.specs(cat).items():
        if spec.is_empty:
            out[c] = {"digest": spec.digest, "violation": lambda rec: 0.0}
            continue
        cp = spec.compile(keys, base, netw.route_stops, xy)
        out[c] = {"digest": spec.digest,
                  "violation": (lambda rec, cp=cp: cp.violation(
                      _plan_vec(rec, cp.keys)))}
    return out


def sentinels() -> int:
    con = contract()
    cat = con["catalog"]["digest"]
    log = logger("sentinels")
    SENT.mkdir(parents=True, exist_ok=True)
    for n, c in SENTINELS:
        out = SENT / f"{n}_{c}.json"
        rec = ensure(out, cell_cmd(n, c, "order_sentinel", out, cat), log)
        ref = json.loads((INIT / f"{n}_{c}.json").read_text())
        eq = all(rec["outcome"][f] == ref["outcome"][f]
                 for f in ("objective_EXACT", "plan_digest", "rounds"))
        log(f"sentinel {n} {c} equal={eq}")
        if not eq:
            (SENT / f"EXP6_ORDER_DEPENDENCE_FAILURE.{n}_{c}.json").write_text(
                json.dumps({"status": "EXP6_ORDER_DEPENDENCE_FAILURE"}))
            return 3
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("plan")
    s = sub.add_parser("initial")
    s.add_argument("--k", type=int, required=True)
    s.add_argument("--of", type=int, required=True)
    c = sub.add_parser("closure")
    c.add_argument("--network", required=True, choices=G.NETWORKS)
    sub.add_parser("sentinels")
    a = ap.parse_args()
    if a.cmd == "plan":
        for i, x in enumerate(canonical()):
            print(i, i % 2, *x)
        return 0
    if a.cmd == "initial":
        return initial(a.k, a.of)
    if a.cmd == "closure":
        return closure(a.network)
    return sentinels()


if __name__ == "__main__":
    raise SystemExit(main())
