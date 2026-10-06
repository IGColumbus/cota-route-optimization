#!/usr/bin/env python3
"""Scaling acceptance check (docs/SCALING.md): run a subset of Experiment 5
cells as independent array tasks and compare each with the committed serial
record.

Each task certifies exactly one cell in a fresh process, through the release
redirect (`cota-opt run-script`, so the frozen code reads `data/raw/`), and
writes exactly one record into the output directory. A task whose record
already exists and parses is skipped, so a requeued task simply reruns.

    # one task per array index (Slurm sets SLURM_ARRAY_TASK_ID)
    python scripts/scaling_check.py task --out-dir <dir> [--index i]
    # stand-in for a job array on one machine: P concurrent tasks
    python scripts/scaling_check.py local --out-dir <dir> --parallel 2
    # compare every finished task with outputs/exp5/cells/ (exit 1 on mismatch)
    python scripts/scaling_check.py compare --out-dir <dir> [--receipt file.json]

The comparison is bit-exact on the exact objective string, the plan digest,
the round count, convergence, every exact fitness component and the
per-round objective trajectory. A mismatch is a finding to report, not to
tune away.
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CELLS = ROOT / "outputs" / "exp5" / "cells"
CONTRACT = ROOT / "outputs" / "exp5" / "EXP5_CONTRACT.json"
#: N0 cells with the smallest recorded search (23 solve calls each)
DEFAULT_CELLS = ("N0_H075", "N0_H090", "N0_J075", "N0_J090")
DETERMINISTIC_ENV = {"PYTHONHASHSEED": "0", "OMP_NUM_THREADS": "1",
                     "OPENBLAS_NUM_THREADS": "1", "MKL_NUM_THREADS": "1"}


def parse_cell(name: str) -> tuple[str, float, float]:
    """`N0_H075` -> ("N0", hours, peak) from the committed record's resource block."""
    rec = json.loads((CELLS / f"{name}.json").read_text())
    net = name.split("_", 1)[0]
    req = rec["resource"]["requested"]
    return net, float(req["hours_multiplier"]), float(req["peak_multiplier"])


def contract_digest() -> str:
    return json.loads(CONTRACT.read_text())["contracts"]["EXP5_FRONTIER"]["digest"]


def task(name: str, out_dir: Path) -> int:
    out = out_dir / f"{name}.json"
    if out.exists():
        try:
            json.loads(out.read_text())["outcome"]
            print(f"skip {name} (exists)")
            return 0
        except Exception:
            raise SystemExit(f"{out} exists but does not parse; refusing to overwrite")
    net, hours, peak = parse_cell(name)
    cmd = [sys.executable, "-m", "cota_release.cli", "run-script",
           "scripts/exp45_certify_cell.py", "cell",
           "--network", net, "--hours", repr(hours), "--peak", repr(peak),
           "--experiment", "exp5", "--role", "scaling_check",
           "--contract-digest", contract_digest(),
           "--out", str(out.resolve()),
           "--heartbeat", str((out_dir / f"hb_{name}.json").resolve()),
           "--reach-test"]
    env = {**os.environ, **DETERMINISTIC_ENV,
           "PYTHONPATH": str(ROOT / "src") + os.pathsep + os.environ.get("PYTHONPATH", "")}
    t0 = time.time()
    rc = subprocess.call(cmd, cwd=ROOT, env=env)
    (out_dir / f"{name}.task.json").write_text(json.dumps(
        {"cell": name, "rc": rc, "seconds": round(time.time() - t0, 1),
         "pid": os.getpid(), "host": platform.node()}, indent=1))
    return rc


COMPARED = ("objective_EXACT", "plan_digest", "rounds", "converged")


def compare(out_dir: Path, cells: list[str]) -> dict:
    rows = []
    for name in cells:
        p = out_dir / f"{name}.json"
        if not p.exists():
            rows.append({"cell": name, "status": "MISSING"})
            continue
        got = json.loads(p.read_text())["outcome"]
        want = json.loads((CELLS / f"{name}.json").read_text())["outcome"]
        diffs = [k for k in COMPARED if got[k] != want[k]]
        if got["fitness_EXACT"] != want["fitness_EXACT"]:
            diffs.append("fitness_EXACT")
        if ([t["objective"] for t in got["round_trajectory"]]
                != [t["objective"] for t in want["round_trajectory"]]):
            diffs.append("round_trajectory")
        task_meta = out_dir / f"{name}.task.json"
        rows.append({"cell": name,
                     "status": "IDENTICAL" if not diffs else "MISMATCH",
                     "differing_fields": diffs,
                     "objective_EXACT": got["objective_EXACT"],
                     "recorded_objective_EXACT": want["objective_EXACT"],
                     "plan_digest": got["plan_digest"],
                     "recorded_plan_digest": want["plan_digest"],
                     "rounds": got["rounds"],
                     "seconds": json.loads(task_meta.read_text())["seconds"]
                     if task_meta.exists() else None,
                     "recorded_seconds": want.get("seconds")})
    ok = all(r["status"] == "IDENTICAL" for r in rows)
    return {"status": "PASS" if ok else "FAIL", "cells": rows,
            "compared": list(COMPARED) + ["fitness_EXACT", "round_trajectory"],
            "reference": "outputs/exp5/cells/<cell>.json (serial production records)"}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    for n in ("task", "local", "compare"):
        p = sub.add_parser(n)
        p.add_argument("--out-dir", required=True)
        p.add_argument("--cells", default=",".join(DEFAULT_CELLS))
        if n == "task":
            p.add_argument("--index", type=int, default=None)
        if n == "local":
            p.add_argument("--parallel", type=int, default=2)
        if n == "compare":
            p.add_argument("--receipt", default=None)
    a = ap.parse_args()
    out_dir = Path(a.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    cells = a.cells.split(",")
    if a.cmd == "task":
        i = a.index if a.index is not None else int(os.environ["SLURM_ARRAY_TASK_ID"])
        return task(cells[i], out_dir)
    if a.cmd == "local":
        with ThreadPoolExecutor(max_workers=a.parallel) as ex:
            rcs = list(ex.map(lambda c: task(c, out_dir), cells))
        return max(rcs) if rcs else 0
    r = compare(out_dir, cells)
    print(json.dumps(r, indent=1))
    if a.receipt:
        Path(a.receipt).write_text(json.dumps(r, indent=1) + "\n")
    return 0 if r["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
