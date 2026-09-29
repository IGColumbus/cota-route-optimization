#!/usr/bin/env python3
"""Experiment 7 production driver.

    exp7_run.py plan                              canonical cell list + counts
    exp7_run.py initial --k 0 --of 2              one fresh subprocess per cell
    exp7_run.py closure --track F6 --network N0   combined closure (one writer)
    exp7_run.py sentinels                         reversed-order reruns

Everything is read from the frozen `outputs/exp7/EXP7_CONTRACT.json`
(exp7_freeze.py); nothing here chooses a level, a policy or a parameter.

Initial cells: (track, level, network, cell) in canonical order. At BASE, when
the contract sets `base_reuse_exp6_initial`, the Experiment 6 initial record of
the same (network, cell) IS the Exp 7 BASE initial record; it is imported by
reference with its sha256 (never copied, never modified). The contract may set
this only after the BASE reproduction canaries reproduced Exp 6 bit-exactly.

Closure: `exp7_closure.run` over one (track, network) group. Operations:
  precheck   the target cell's compiled policy (level-independent: policy
             constraints and the resource envelope do not depend on demand,
             lambda, waiting or path model) and the representation (same
             route-period key set). A refused anchor is receipted, never
             repaired. Admission is re-verified by the certifier itself.
  transfer   explicit-anchor certification of the target cell under the
             TARGET level (exp7_cell.py --anchor-from), re-evaluated under the
             target objective. At BASE, a transfer that Experiment 6 already
             ran (same network, target cell, anchor plan digest) is imported
             from outputs/exp6/closure by reference -- certification is
             deterministic, so it is the same result -- and receipted as such.
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
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import exp45_certify_cell as CC  # noqa: E402
import exp6_grid as G  # noqa: E402
import exp7_closure as E  # noqa: E402
import exp7_levels as L  # noqa: E402

# EXP7_OUT redirects every output (smoke runs only); production uses the default.
OUT = ROOT / os.environ.get("EXP7_OUT", "outputs/exp7")
INIT = OUT / "initial"
CLOS = OUT / "closure"
SENT = OUT / "sentinels"
RUN = OUT / "run"
CONTRACT = OUT / "EXP7_CONTRACT.json"
EXP6 = ROOT / "outputs" / "exp6"
EMPTY_SET_MSG = "minimum-service plan already exceeds the budget"


def contract() -> dict:
    """The frozen contract. Under the two-stage design (0929 final production
    contract) this driver runs STAGE 2 ONLY, and only over BASE plus the
    levels frozen in EXP7_STAGE2_SELECTION.json, whose contract digest must
    match this contract byte-for-byte."""
    if not CONTRACT.exists():
        raise SystemExit("EXP7_CONTRACT.json is not frozen; no production run")
    con = json.loads(CONTRACT.read_text())
    if con.get("design") != "two_stage":
        return con                      # smoke / legacy contracts
    import hashlib
    sel_p = OUT / "EXP7_STAGE2_SELECTION.json"
    if not sel_p.exists():
        raise SystemExit("Stage 2 selection not frozen; Stage 2 refuses")
    sel = json.loads(sel_p.read_text())
    if sel["exp7_contract_sha256_16"] != hashlib.sha256(
            CONTRACT.read_bytes()).hexdigest()[:16]:
        raise SystemExit("Stage 2 selection was made against another contract")
    keep = ["BASE"] + list(sel["included_levels"])
    con = dict(con)
    con["levels"] = [p for p in con["levels"] if p["name"] in keep]
    con["level_order"] = [n for n in con["level_order"] if n in keep]
    if con["level_order"] != keep:
        raise SystemExit("selection names levels outside the contract order")
    con["stage2_selection"] = sel
    first, last = keep[1], keep[-1]
    # sentinels: reversed-order reruns inside the selected levels only
    con["sentinels"] = [["F6", last, "N3", "REF"], ["F6", last, "N0", "R2_S10"],
                        ["F4", last, "N4", "REF"], ["F6", first, "N0", "REF"]]
    return con


def levels(con) -> dict[str, L.SensitivityLevel]:
    out = {}
    for p in con["levels"]:
        lv = L.from_payload(p)
        if lv.digest != p["digest"]:
            raise SystemExit(f"level {lv.name} digest drift")
        out[lv.name] = lv
    return out


def canonical(con) -> list[tuple[str, str, str, str]]:
    out = []
    for track in ("F6", "F4"):
        if track not in con["tracks"]:
            continue
        t = con["tracks"][track]
        for lv in con["level_order"]:
            for c in t["policies"]:
                for n in t["networks"]:
                    out.append((track, lv, n, c))
    assert len(out) == len(set(out))
    return out


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def init_path(track, lv, n, c) -> Path:
    return INIT / track / lv / f"{n}_{c}.json"


def exp6_initial(n, c) -> Path:
    return EXP6 / "initial" / f"{n}_{c}.json"


def resolve_initial(con, track, lv, n, c) -> Path:
    """The record that IS this initial cell (an Exp 6 import at BASE)."""
    p = init_path(track, lv, n, c)
    imp = p.with_suffix(".import.json")
    if imp.exists():
        d = json.loads(imp.read_text())
        src = ROOT / d["path"]
        if sha(src) != d["sha256"]:
            raise SystemExit(f"imported record changed: {src}")
        return src
    return p


def cell_cmd(con, track, lv, n, c, role, out: Path, anchor: Path | None = None,
             label: str = ""):
    cmd = [sys.executable, str(ROOT / "scripts/exp7_cell.py"), "--network", n,
           "--cell", c, "--role", role, "--catalog-digest",
           con["catalog"]["digest"], "--out", str(out.relative_to(ROOT)),
           "--heartbeat", str((RUN / f"hb_{track}_{lv}_{n}_{c}.json")
                              .relative_to(ROOT)),
           "--level", lv, "--level-file", con["level_file"], "--track", track]
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


def halts() -> list[str]:
    return sorted(str(p.relative_to(OUT)) for d in (INIT, CLOS, SENT)
                  if d.exists() for p in d.rglob("*.json")
                  if p.name.startswith(("EXP", "ERROR.")))


def _pure_r1(spec) -> bool:
    return (spec.max_headway is not None and spec.max_off_share is None
            and not spec.span and spec.max_lost_share is None
            and spec.area_radius_m is None)


def ensure(con, out: Path, cmd, log, *, n=None, c=None, lv=None) -> dict:
    """Run unless the record exists. A pure-R1 start failure with the
    empty-set message is PROVEN empty at this level (exp7_infeasible_cell.py)
    or the run stops; a solver failure is never taken as infeasibility."""
    if out.exists():
        return json.loads(out.read_text())
    out.parent.mkdir(parents=True, exist_ok=True)
    log(f"start {out.relative_to(OUT)}")
    t0 = time.time()
    rc = subprocess.call(cmd, cwd=ROOT)
    log(f"end   {out.relative_to(OUT)} rc={rc} {time.time() - t0:.0f}s")
    err = out.with_name("ERROR." + out.name)
    if rc != 0 and err.exists() and c is not None and \
            EMPTY_SET_MSG in json.loads(err.read_text()).get("error", "") and \
            _pure_r1(G.specs(con["catalog"]["digest"])[c]):
        err.rename(out.with_name("TRACE." + out.name))
        log(f"empty-feasible-set proof for {out.relative_to(OUT)}")
        rc = subprocess.call(
            [sys.executable, str(ROOT / "scripts/exp7_infeasible_cell.py"),
             "--network", n, "--cell", c, "--catalog-digest",
             con["catalog"]["digest"], "--level", lv, "--level-file",
             con["level_file"], "--out", str(out.relative_to(ROOT))], cwd=ROOT)
        log(f"proof rc={rc}")
    if rc != 0 or not out.exists():
        raise SystemExit(f"cell failed rc={rc}: {out}")
    return json.loads(out.read_text())


def check_cell(rec: dict, path: Path, log):
    if rec["status"] != "CERTIFIED":
        if rec["status"] != E.EMPTY:
            _halt(path, "EXP7_UNEXPECTED_STATUS", log)
        return
    o = rec["outcome"]
    if not (o["converged"] and o["rounds"] < 120):
        _halt(path, "EXP7_CONVERGENCE_FAILURE", log)
    if not rec["resource"]["feasible_under_full_target_constraints"]:
        _halt(path, "EXP7_INFEASIBLE_CERTIFIED_PLAN", log)


def _halt(path, status, log):
    (path.parent / f"{status}.{path.name}").write_text(json.dumps(
        {"status": status, "cell": str(path.relative_to(ROOT))}, indent=1))
    log(f"!!! {status} {path.name}")
    raise SystemExit(4)


def initial(k: int, of: int) -> int:
    con = contract()
    log = logger(f"initial{k}")
    for i, (track, lv, n, c) in enumerate(canonical(con)):
        if i % of != k:
            continue
        if halts():
            log(f"halt present {halts()}")
            return 3
        out = init_path(track, lv, n, c)
        if lv == "BASE" and con["base_reuse_exp6_initial"] and \
                exp6_initial(n, c).exists():
            imp = out.with_suffix(".import.json")
            if not imp.exists():
                imp.parent.mkdir(parents=True, exist_ok=True)
                src = exp6_initial(n, c)
                CC.atomic_write_json(imp, {
                    "imported_from": "experiment 6 initial stage",
                    "path": str(src.relative_to(ROOT)), "sha256": sha(src),
                    "justification": con["base_reuse_justification"]})
                log(f"import {imp.relative_to(OUT)}")
            continue
        rec = ensure(con, out, cell_cmd(con, track, lv, n, c, "initial", out),
                     log, n=n, c=c, lv=lv)
        check_cell(rec, out, log)
    log("initial shard complete")
    return 0


def _plan_vec(rec, keys):
    import numpy as np
    p = rec["outcome"]["plan_EXACT"]
    return np.array([math.inf if p[f"{r}|{q}"] is None else float(p[f"{r}|{q}"])
                     for (r, q) in keys])


_BOOT = {}


def _compile_all(con, net: str, ref_rec: dict, lv=None) -> dict:
    """Compiled policy per cell on this network (as exp2.build_setup builds
    it), from the REF baseline headways of the SAME level. Policies do not
    depend on demand, lambda, waiting or path model; they DO depend on the
    network, so a level with a network transform (A3 runtime, A7 route
    removal) is compiled on its transformed network and its own REF record."""
    from pyproj import Transformer
    if "st" not in _BOOT:
        _BOOT["st"] = CC.boot()
    st = _BOOT["st"]
    netw, ts_, id_ = CC.build_network(net, st)
    if lv is not None:
        netw, _, _ = L.network_for(netw, ts_, id_, lv, net)
    keys = [tuple(k.split("|", 1)) for k in sorted(ref_rec["outcome"]["plan_EXACT"])]
    bh = ref_rec["baseline_headways"]
    base = {k: (math.inf if bh[f"{k[0]}|{k[1]}"] is None
                else float(bh[f"{k[0]}|{k[1]}"])) for k in keys}
    tr = Transformer.from_crs("EPSG:4326",
                              st["H"].assumptions["crs"]["projected"],
                              always_xy=True)
    xy = {s: tr.transform(v.lon, v.lat) for s, v in netw.stops.items()}
    out = {"__keys__": {f"{r}|{q}" for r, q in keys}}
    for c, spec in G.specs(con["catalog"]["digest"]).items():
        if spec.is_empty:
            out[c] = {"digest": spec.digest, "violation": lambda rec: 0.0}
            continue
        cp = spec.compile(keys, base, netw.route_stops, xy)
        out[c] = {"digest": spec.digest,
                  "violation": (lambda rec, cp=cp: cp.violation(
                      _plan_vec(rec, cp.keys)))}
    return out


def _rec(path: Path) -> E.Rec:
    r = json.loads(path.read_text())
    if r["status"] != "CERTIFIED":
        return E.Rec(r["status"], ref=str(path.relative_to(ROOT)))
    return E.Rec(E.CERTIFIED, float(r["outcome"]["objective_EXACT"]),
                 r["outcome"]["plan_digest"], str(path.relative_to(ROOT)))


def _exp6_transfer(net, tgt_cell, digest) -> Path | None:
    """An Exp 6 closure record for the same (network, target, anchor plan)."""
    for p in sorted((EXP6 / "closure").glob(f"{net}_{tgt_cell}__from_*__{digest}.json")):
        r = json.loads(p.read_text())
        if r.get("status") == "CERTIFIED" and \
                r["search"]["start"].get("anchor_plan_digest") == digest:
            return p
    return None


def closure(track: str, net: str) -> int:
    con = contract()
    t = con["tracks"][track]
    if net not in t["networks"]:
        raise SystemExit(f"{net} not in {track}")
    log = logger(f"closure_{track}_{net}")
    d = CLOS / track
    d.mkdir(parents=True, exist_ok=True)
    order = con["level_order"]
    group = E.Group(levels=order, policies=list(t["policies"]),
                    edges=[tuple(e) for e in t.get("adjacent_edges", [])],
                    within=bool(t["within_level_closure"]),
                    # 0929 decision: dimension-local X, BASE the only hub
                    dimension_of={lv: levels(con)[lv].dimension
                                  for lv in order[1:]})
    paths = {}
    for lv in order:
        for c in t["policies"]:
            p = resolve_initial(con, track, lv, net, c)
            if not p.exists():
                raise SystemExit(f"initial {track}/{lv}/{net}_{c} missing; "
                                 f"closure refuses an incomplete upstream stage")
            paths[(lv, c)] = p
    lvs = levels(con)
    comp_base = _compile_all(con, net, json.loads(paths[(order[0], "REF")]
                                                  .read_text()))
    comp_by_lv = {lv: (comp_base if not lvs[lv].network else _compile_all(
        con, net, json.loads(paths[(lv, "REF")].read_text()), lvs[lv]))
        for lv in order}
    state_p = d / f"closure_state_{net}.json"
    ledger = d / f"closure_ledger_{net}.jsonl"
    state = json.loads(state_p.read_text()) if state_p.exists() else None
    best = E.best_from_state(state) if state else \
        {k: _rec(p) for k, p in paths.items()}

    def precheck(tgt, src: E.Rec):
        srec = json.loads((ROOT / src.ref).read_text())
        ks = set(srec["outcome"]["plan_EXACT"])
        comp = comp_by_lv[tgt[0]]
        keyset = comp["__keys__"]
        if ks != keyset:
            return f"representation: key sets differ ({len(ks ^ keyset)})"
        v = comp[tgt[1]]["violation"](srec)
        return None if v <= 0 else f"policy violation {v} under {tgt[1]}"

    def transfer(tgt, src: E.Rec, label: str) -> E.Rec:
        lv, c = tgt
        if lv == "BASE" and track == "F6":
            hit = _exp6_transfer(net, c, src.plan_digest)
            if hit is not None:
                log(f"import exp6 transfer {hit.name}")
                return _rec(hit)
        out = d / lv / f"{net}_{c}__anchor_{src.plan_digest}.json"
        res = ensure(con, out, cell_cmd(con, track, lv, net, c,
                                        "closure_transfer", out,
                                        anchor=ROOT / src.ref, label=label), log)
        if res["status"] == "CERTIFIED":
            check_cell(res, out, log)
        else:
            return E.Rec("REFUSED:" + str(res.get("refusal", res["status"]))[:200],
                         ref=str(out.relative_to(ROOT)))
        return _rec(out)

    def receipt(r):
        r = {"track": track, "network": net, **r}
        with open(ledger, "a") as f:
            f.write(json.dumps(r, sort_keys=True) + "\n")
            f.flush()
            os.fsync(f.fileno())

    ops = E.Ops(precheck=precheck, transfer=transfer, receipt=receipt,
                save=lambda s: CC.atomic_write_json(state_p, s))
    st = E.run(group, best, ops, ceiling=int(con["closure"]["pass_ceiling"]),
               eps=float(con["closure"]["improvement_eps"]), state=state)
    if st["status"] != E.FIXED_POINT:
        (d / f"{st['status']}.{net}.json").write_text(json.dumps(
            {"status": st["status"], "track": track, "network": net,
             "passes": st["passes_completed"]}, indent=1))
        log(f"!!! {st['status']}")
        return 3
    log(f"fixed point after {st['passes_completed']} passes")
    return 0


def sentinels() -> int:
    """Reversed-order reruns of frozen initial cells: bit-exact or halt."""
    con = contract()
    log = logger("sentinels")
    for track, lv, n, c in con["sentinels"]:
        out = SENT / track / lv / f"{n}_{c}.json"
        rec = ensure(con, out, cell_cmd(con, track, lv, n, c, "order_sentinel",
                                        out), log)
        ref = json.loads(resolve_initial(con, track, lv, n, c).read_text())
        eq = all(rec["outcome"][f] == ref["outcome"][f]
                 for f in ("objective_EXACT", "plan_digest", "rounds"))
        log(f"sentinel {track} {lv} {n} {c} equal={eq}")
        if not eq:
            (SENT / f"EXP7_ORDER_DEPENDENCE_FAILURE.{track}_{lv}_{n}_{c}.json"
             ).write_text(json.dumps({"status": "EXP7_ORDER_DEPENDENCE_FAILURE"}))
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
    c.add_argument("--track", required=True, choices=("F6", "F4"))
    c.add_argument("--network", required=True, choices=("N0", "N3", "N4"))
    sub.add_parser("sentinels")
    a = ap.parse_args()
    if a.cmd == "plan":
        con = contract()
        cells = canonical(con)
        for i, x in enumerate(cells):
            print(i, *x)
        return 0
    if a.cmd == "initial":
        return initial(a.k, a.of)
    if a.cmd == "closure":
        return closure(a.track, a.network)
    return sentinels()


if __name__ == "__main__":
    raise SystemExit(main())
