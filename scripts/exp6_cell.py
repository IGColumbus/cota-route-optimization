#!/usr/bin/env python3
"""One Experiment 6 certification: EXP4N's certifier, optionally under a policy
cell and optionally from an explicit anchor.

    exp6_cell.py --network N0 --cell R2_S10 --role initial --out ...
    exp6_cell.py --network N0 --cell REF --anchor-from rec.json --anchor-label \
        "closure pass 1: R2_S25 -> REF" --role transfer --out ...
    exp6_cell.py --network N4 --no-policy --hours 1.1 --anchor-from <exp5 H090> \
        --role d39_preflight --out ...

Nothing is re-scored. Everything numeric comes from `exp4_certify.certify`
(through the observation-only wrapper of scripts/exp45_certify_cell.py, which
records the budget the setup enforced and the FitnessVector of the certified
plan). The policy is attached through `constraints["policy"]` and enforced by
`frequency._feasible`; the record carries the policy measurement of the
certified plan taken from the compiled policy object of the same setup.

An anchor that is not admissible in the target cell is REFUSED by certify
(`AnchorRefused`); the runner writes a refusal record rather than an error so a
closure pass can record the transfer receipt and move on.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import platform
import sys
import time
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import exp45_certify_cell as CC  # noqa: E402
import exp5_model_resource as MR  # noqa: E402
from exp45_contracts import (K_RUNGS, LAM, MAX_ROUNDS, N_KEYS,  # noqa: E402
                             SEED)

PERIODS = MR.PERIODS


def base_config_digest(st: dict, cons: dict) -> str:
    from cota_opt.configs import load_cost_weights
    from cota_opt.firewall.core import digest
    res = {k: v for k, v in cons["resource"].items()
           if k not in ("weekday_revenue_vehicle_hours", "peak_fleet_by_period")}
    rest = {k: v for k, v in cons.items() if k not in ("resource", "policy")}
    return digest({"constraints_non_cap": {**rest, "resource": res},
                   "assumptions": st["H"].assumptions,
                   "cost_weights": load_cost_weights()})


def run(kind: str, spec, env, *, st: dict, role: str, cell: str,
        anchor: dict | None, anchor_meta: dict | None,
        heartbeat: Path | None) -> dict:
    import cota_opt.exp3_score as E3
    from cota_opt.configs import load_constraints
    from cota_opt.exp3_cell import code_version, repo_revision
    from cota_opt.exp4_certify import (AnchorRefused, CERTIFICATION_DIGEST,
                                       certify)
    from cota_opt.firewall.core import digest

    net, ts, ident = CC.build_network(kind, st)
    cons = env.to_constraints(load_constraints())
    if spec is not None:
        cons = {**cons, "policy": spec}
    bcd = base_config_digest(st, cons)
    cfg = digest({"base_config": bcd,
                  "policy": None if spec is None else spec.payload()})
    traj: list[dict] = []
    t0 = time.time()

    def prog(rnd, obj, blocks):
        traj.append({"round": int(rnd), "objective": repr(float(obj)),
                     "block_enumerations": int(blocks),
                     "elapsed_s": round(time.time() - t0, 1)})
        if heartbeat:
            CC.atomic_write_json(heartbeat, {
                "at": CC.utc(), "pid": os.getpid(), "network": kind,
                "cell": cell, "role": role, "round": int(rnd),
                "objective": repr(float(obj))})

    obs = CC.Observer()
    judges: list = []
    orig = E3.solve_on_network

    def wrapped(n_, t_, **kw):
        r = obs.wrap(orig)(n_, t_, **kw)
        if not judges:
            judges.append(r["judge"])
        return r

    E3.solve_on_network = wrapped
    refused = None
    try:
        cr = certify(net, ts, state_key=ident["state_key"],
                     state_digest=ident["state_digest"], harness=st["H"],
                     stops_gdf=st["sg"], lam=LAM, seed=SEED, constraints=cons,
                     contract_digest=CERTIFICATION_DIGEST,
                     max_rounds=MAX_ROUNDS, progress=prog, anchor=anchor,
                     anchor_provenance=json.dumps(anchor_meta or {},
                                                  sort_keys=True))
    except AnchorRefused as ex:
        refused = str(ex)
    finally:
        E3.solve_on_network = orig
    secs = time.time() - t0
    judge = judges[0] if judges else None
    pol = getattr(judge.model, "policy", None) if judge else None
    base_rec = {
        "schema": "exp6_cell/v1", "experiment": "exp6", "role": role,
        "network": kind, "cell": cell, "identity": ident,
        "policy": None if spec is None else {
            "spec": spec.payload(), "digest": spec.digest,
            "attached": pol is not None,
            "setup_policy_digest": obs.checks.get("policy_digest")
            if obs.checks else None},
        "anchor": anchor_meta,
        "provenance": {
            "code_version": code_version(),
            "src_cota_opt_content_digest": CC.src_content_digest(),
            "repo_revision": repo_revision(),
            "base_config_digest": bcd, "config_digest": cfg,
            "data_inputs": CC.data_inputs(),
            "data_digest": hashlib.sha256(json.dumps(
                CC.data_inputs(), sort_keys=True).encode()).hexdigest()[:16],
            "runner_sha256": {n: CC.sha256_file(ROOT / "scripts" / n)[:16]
                              for n in ("exp6_cell.py", "exp6_grid.py",
                                        "exp45_certify_cell.py",
                                        "exp45_contracts.py",
                                        "exp5_model_resource.py")},
            "python": platform.python_version(), "pid": os.getpid()},
        "written_utc": CC.utc(),
    }
    if refused is not None:
        return {**base_rec, "status": "ANCHOR_REFUSED", "refusal": refused,
                "seconds": round(secs, 1)}

    if len(obs.budgets) != 1:
        raise CC.HaltError("EXP6_CONSTRAINT_INERT", {
            "why": "setups enforced more than one budget within one cell"})
    (bh, bpeak, btol), = obs.budgets.keys()
    if bh != repr(float(env.hours_cap)) or dict(bpeak) != {
            p: repr(float(env.peak_proxy_caps[p])) for p in PERIODS} \
            or btol != repr(0.0):
        raise CC.HaltError("EXP6_CONSTRAINT_INERT", {
            "why": "the enforced budget is not the envelope's caps"})
    rec_fit = obs.fits.get(cr.plan_digest)
    if rec_fit is None:
        raise CC.HaltError("EXP6_INSTRUMENTATION_FAILURE",
                           {"why": "certified plan not observed"})
    for k in ("revenue_veh_hours", "peak_vehicles", "generalized_cost",
              "unserved_demand"):
        if repr(rec_fit[k]) != repr(float(cr.fitness[k])):
            raise CC.HaltError("EXP6_INSTRUMENTATION_FAILURE",
                               {"why": f"observed {k} != certify's"})
    used_peak = rec_fit["peak_by_period"]
    used_h = float(cr.fitness["revenue_veh_hours"])
    cap_h = float(env.hours_cap)
    caps = {p: float(env.peak_proxy_caps[p]) for p in PERIODS}
    plan = {k: (None if math.isinf(v) else float(v))
            for k, v in sorted(cr.plan.items())}
    policy_measure = pol_violation = None
    if pol is not None:
        import numpy as np
        hvec = np.array([cr.plan[f"{r}|{p}"] for (r, p) in pol.keys])
        policy_measure = pol.measure(hvec)
        pol_violation = pol.violation(hvec)
    feas = (used_h <= cap_h * (1 + CC.EPS_REL) and all(
        used_peak[p] <= caps[p] * (1 + CC.EPS_REL) for p in PERIODS)
        and (pol_violation in (None, 0.0)))
    base_plan = judge.baseline_plan.headways if judge else {}
    n_on_to_off = sum(1 for (r, p), v in cr.plan.items()
                      if math.isinf(v) and math.isfinite(base_plan.get((r, p),
                                                                      math.inf)))
    return {**base_rec, "status": "CERTIFIED",
            "search": {"lam": LAM, "seed": SEED, "n_keys": N_KEYS,
                       "k_rungs": K_RUNGS, "max_rounds": MAX_ROUNDS,
                       "allow_off": True, "waiting_model": "same_route",
                       "certification_digest": CERTIFICATION_DIGEST,
                       "guarantee": cr.guarantee, "start": dict(cr.start)},
            "resource": {
                "requested": env.payload(),
                "enforced": {"hours_cap": bh, "peak_proxy_caps": dict(bpeak),
                             "tolerance": btol},
                "enforced_exact_fingerprint": env.exact_fingerprint,
                "enforced_rounded_envelope_digest": env.rounded_envelope_digest,
                "used": {"revenue_veh_hours": repr(used_h),
                         "peak_proxy_by_period": {p: repr(used_peak[p])
                                                  for p in PERIODS}},
                "slack": {"hours": repr(cap_h - used_h),
                          "peak_proxy_by_period": {p: repr(caps[p] - used_peak[p])
                                                   for p in PERIODS}},
                "binding_within_1e-6_rel": {
                    "hours": used_h >= cap_h * (1 - 1e-6),
                    "peak_proxy_by_period": {p: used_peak[p] >= caps[p] * (1 - 1e-6)
                                             for p in PERIODS}},
                "feasible_under_full_target_constraints": bool(feas)},
            "policy_outcome": {"measure": policy_measure,
                               "violation": pol_violation},
            "outcome": {
                "objective_EXACT": repr(float(cr.objective)),
                "fitness_EXACT": {k: repr(float(v)) for k, v in cr.fitness.items()},
                "plan_digest": cr.plan_digest, "rounds": int(cr.rounds),
                "converged": bool(cr.converged),
                "rounds_below_ceiling": int(cr.rounds) < MAX_ROUNDS,
                "block_enumerations": int(cr.block_enumerations),
                "combinations": int(cr.combinations),
                "seconds": round(secs, 1),
                "n_route_periods": len(plan),
                "n_off": sum(1 for v in plan.values() if v is None),
                "n_baseline_on_now_off": n_on_to_off,
                "round_trajectory": traj, "plan_EXACT": plan,
                "plan_encoding": "route|period -> headway minutes; null = OFF"},
            "execution": {
                "start_audit": CC._clean(obs.start_audit),
                "evaluator_used": obs.checks.get("common_lines"),
                "evaluator_checks": CC._clean({k: obs.checks.get(k) for k in (
                    "common_lines", "common_lines_source",
                    "locked_route_periods", "total_paths", "n_route_periods",
                    "od_pairs", "vh_relative_error", "policy_digest",
                    "policy_cell", "policy_baseline_violation")}),
                "pathset_digest": (CC.pathset_content_digest(obs.cache)
                                   if obs.cache else ""),
                "n_solve_calls_observed": obs.calls}}


def load_anchor(path: Path) -> tuple[dict, dict]:
    rec = json.loads(path.read_text())
    plan = {k: (math.inf if v is None else float(v))
            for k, v in rec["outcome"]["plan_EXACT"].items()}
    meta = {"source_record": str(path.relative_to(ROOT)),
            "source_record_sha256": CC.sha256_file(path)[:16],
            "source_network": rec.get("network"),
            "source_cell": rec.get("cell", rec.get("cell_id")),
            "source_plan_digest": rec["outcome"]["plan_digest"],
            "source_objective_in_source_cell": rec["outcome"]["objective_EXACT"]}
    return plan, meta


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--network", required=True, choices=("N0", "N3", "N4"))
    ap.add_argument("--cell", default="REF")
    ap.add_argument("--no-policy", action="store_true")
    ap.add_argument("--hours", type=float, default=1.0)
    ap.add_argument("--peak", type=float, default=1.0)
    ap.add_argument("--anchor-from", default="")
    ap.add_argument("--anchor-label", default="")
    ap.add_argument("--catalog-digest", default="")
    ap.add_argument("--role", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--heartbeat", default="")
    a = ap.parse_args()
    out = ROOT / a.out
    try:
        st = CC.boot()
        env = MR.scale(MR.load_base(), a.hours, a.peak)
        spec = None
        if not a.no_policy:
            import exp6_grid as G
            spec = G.specs(a.catalog_digest or None)[a.cell]
        anchor = meta = None
        if a.anchor_from:
            anchor, meta = load_anchor(ROOT / a.anchor_from)
            meta["label"] = a.anchor_label
        rec = run(a.network, spec, env, st=st, role=a.role,
                  cell=a.cell if spec is not None else MR.cell_id(a.hours, a.peak),
                  anchor=anchor, anchor_meta=meta,
                  heartbeat=ROOT / a.heartbeat if a.heartbeat else None)
        CC.atomic_write_json(out, rec)
        if rec["status"] == "ANCHOR_REFUSED":
            print(f"{a.network} {rec['cell']} ANCHOR_REFUSED: {rec['refusal'][:160]}")
        else:
            o = rec["outcome"]
            print(f"{a.network} {rec['cell']} obj {o['objective_EXACT']} "
                  f"{o['rounds']}r conv {o['converged']} plan {o['plan_digest']} "
                  f"start {rec['search']['start'].get('source')} "
                  f"({o['seconds']:.0f}s)")
        return 0
    except CC.HaltError as h:
        CC.atomic_write_json(out.with_name(h.status + "." + out.name),
                             {"status": h.status, "written_utc": CC.utc(),
                              **h.payload})
        print(f"!!! {h.status}: {h.payload.get('why')}")
        return 3
    except Exception as e:
        CC.atomic_write_json(out.with_name("ERROR." + out.name), {
            "error": f"{type(e).__name__}: {e}"[:800],
            "traceback": traceback.format_exc()[-4000:], "written_utc": CC.utc()})
        raise


if __name__ == "__main__":
    raise SystemExit(main())
