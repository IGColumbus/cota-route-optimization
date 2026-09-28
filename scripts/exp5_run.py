#!/usr/bin/env python3
"""Experiment 5 production driver: the complete canonical cell list, sharded.

    exp5_run.py plan                      print the canonical list + shards
    exp5_run.py shard --k 0 --of 2        run shard k (one subprocess per cell)
    exp5_run.py sentinels                 order-invariance reruns, reversed order

OPERATIONS rules honoured here:
  * the WHOLE canonical list is sharded (k::of), never a hand-picked subset;
  * one fresh subprocess per cell -- no in-process state crosses a cell;
  * a cell whose record exists and parses is skipped (resume), a cell whose
    record is missing is run; nothing is ever overwritten;
  * any halt artifact (EXP5_* / EXP4_* / ERROR.*) anywhere in the cells dir
    stops every shard before its next cell;
  * the reproduction gate (N4 J100) and the N0 reference (N0 J100) are the
    first two entries, so they land first -- one per shard -- and every other
    shard waits for the N4 gate verdict before its third cell.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))

import exp5_model_resource as MR  # noqa: E402

OUT = ROOT / "outputs" / "exp5"
CELLS = OUT / "cells"
SENT = OUT / "sentinels"
RUN = OUT / "run"
CONTRACT = OUT / "EXP5_CONTRACT.json"
EXP4N_N4 = ROOT / "outputs/exp4_normalized/production_mr120/cc40b4f4aea3aa05.json"
NETWORKS = ("N4", "N0")
SENTINELS = (("N0", "J100"), ("N4", "J150"), ("N4", "J100"), ("N4", "J075"))


def canonical() -> list[tuple[str, MR.Cell]]:
    g = MR.grid(MR.load_base())
    by = {c.id: c for c in g}
    rest = [c for c in g if c.id != "J100"]
    out = [("N4", by["J100"]), ("N0", by["J100"])]
    for c in rest:
        for n in NETWORKS:
            out.append((n, c))
    assert len(out) == 32 and len({(n, c.id) for n, c in out}) == 32
    return out


def rec_path(d: Path, net: str, cid: str) -> Path:
    return d / f"{net}_{cid}.json"


def halts(d: Path) -> list[str]:
    return sorted(p.name for p in d.glob("*.json")
                  if p.name.startswith(("EXP5_", "EXP4_", "ERROR.")))


def contract_digest() -> str:
    c = json.loads(CONTRACT.read_text())
    return c["contracts"]["EXP5_FRONTIER"]["digest"]


def run_cell(net: str, cell: MR.Cell, d: Path, role: str, log) -> int:
    out = rec_path(d, net, cell.id)
    if out.exists():
        try:
            json.loads(out.read_text())["outcome"]
            log(f"skip {out.name} (exists)")
            return 0
        except Exception:
            raise SystemExit(f"{out} exists but does not parse; refusing to "
                             f"overwrite -- inspect by hand")
    cmd = [sys.executable, str(ROOT / "scripts/exp45_certify_cell.py"), "cell",
           "--network", net, "--hours", repr(cell.envelope.hours_multiplier),
           "--peak", repr(cell.envelope.peak_multiplier),
           "--experiment", "exp5", "--role", role,
           "--contract-digest", contract_digest(),
           "--out", str(out.relative_to(ROOT)),
           "--heartbeat", str((RUN / f"hb_{net}_{cell.id}.json").relative_to(ROOT)),
           "--reach-test"]
    log(f"start {net} {cell.id} ({role})")
    t0 = time.time()
    rc = subprocess.call(cmd, cwd=ROOT)
    log(f"end   {net} {cell.id} rc={rc} {time.time() - t0:.0f}s")
    if rc == 0:
        rec = json.loads(out.read_text())
        o = rec["outcome"]
        status = None
        if not (o["converged"] and o["rounds"] < 120):
            status = "EXP5_CONVERGENCE_FAILURE"
        elif rec.get("reach_test_d35", {}).get("verdict") != "PASS":
            status = "EXP5_CONSTRAINT_INERT"
        elif not rec["resource"]["feasible_under_enforced_caps"]:
            status = "EXP5_INFEASIBLE_CERTIFIED_PLAN"
        if status:
            (d / f"{status}.{out.name}").write_text(json.dumps(
                {"status": status, "cell": out.name,
                 "rounds": o["rounds"], "converged": o["converged"],
                 "reach": rec.get("reach_test_d35", {}).get("verdict")},
                indent=1))
            log(f"!!! {status} on {out.name}")
            return 4
    return rc


def gate_n4(log) -> str:
    """EXP5_REPRODUCTION_FAILURE unless N4 J100 equals EXP4N bit-exactly."""
    p = rec_path(CELLS, "N4", "J100")
    c = json.loads(p.read_text())["outcome"]
    e = json.loads(EXP4N_N4.read_text())
    ok = (c["objective_EXACT"] == repr(e["objective_EXACT"])
          and c["plan_digest"] == e["plan_digest"]
          and c["rounds"] == e["rounds"] and c["converged"] == e["converged"]
          and [t["objective"] for t in c["round_trajectory"]]
          == [t["objective"] for t in e["round_trajectory"]])
    if not ok:
        blob = {"status": "EXP5_REPRODUCTION_FAILURE",
                "got": {k: c[k] for k in ("objective_EXACT", "plan_digest",
                                          "rounds", "converged")},
                "want": {k: e[k] for k in ("objective_EXACT", "plan_digest",
                                           "rounds", "converged")}}
        (CELLS / "EXP5_REPRODUCTION_FAILURE.json").write_text(
            json.dumps(blob, indent=1))
        log("!!! EXP5_REPRODUCTION_FAILURE")
        return "FAIL"
    log("N4 J100 reproduces EXP4N bit-exactly")
    return "PASS"


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("plan")
    s = sub.add_parser("shard")
    s.add_argument("--k", type=int, required=True)
    s.add_argument("--of", type=int, required=True)
    sub.add_parser("sentinels")
    a = ap.parse_args()
    lst = canonical()
    if a.cmd == "plan":
        for i, (n, c) in enumerate(lst):
            print(i, i % 2, n, c.id, c.arm)
        return 0
    RUN.mkdir(parents=True, exist_ok=True)
    CELLS.mkdir(parents=True, exist_ok=True)
    name = f"shard{a.k}" if a.cmd == "shard" else "sentinels"
    lf = open(RUN / f"{name}.events.log", "a")

    def log(m):
        lf.write(f"{time.strftime('%H:%M:%S')} {m}\n")
        lf.flush()
        os.fsync(lf.fileno())

    if not CONTRACT.exists():
        raise SystemExit("EXP5_CONTRACT.json is not frozen; no production cell "
                         "may run before it")
    if a.cmd == "shard":
        mine = [(i, n, c) for i, (n, c) in enumerate(lst) if i % a.of == a.k]
        for i, n, c in mine:
            h = halts(CELLS)
            if h:
                log(f"halt present {h}; stopping")
                return 3
            if i >= 2:
                g = rec_path(CELLS, "N4", "J100")
                while not g.exists():
                    if halts(CELLS):
                        log("halt while waiting for the N4 gate; stopping")
                        return 3
                    time.sleep(30)
                if gate_n4(log) != "PASS":
                    return 3
            role = ("reproduction_gate" if (n, c.id) == ("N4", "J100") else
                    "reference_cell" if (n, c.id) == ("N0", "J100") else
                    "production")
            rc = run_cell(n, c, CELLS, role, log)
            if rc != 0:
                log(f"cell rc={rc}; stopping shard")
                return rc
        log("shard complete")
        return 0
    # sentinels: after production, reversed order, separate directory
    SENT.mkdir(parents=True, exist_ok=True)
    by = {c.id: c for _, c in lst}
    for n, cid in SENTINELS:
        rc = run_cell(n, by[cid], SENT, "order_sentinel", log)
        if rc != 0:
            return rc
    log("sentinels complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
