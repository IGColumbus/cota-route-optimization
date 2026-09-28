#!/usr/bin/env python3
"""One certified cell, through EXP4N's validated certification path.

Shared by the Experiment 4 original-question addendum (N4 canary, N3) and by
Experiment 5 (N0 and N4 at 16 resource cells). There is no second scoring
pipeline here. Everything that computes a number is imported and called:

    network   N4  exp4_assemble.assemble(Exp4Selection(pool, N4 lines))  -- as
                  scripts/exp4n_launch.py does, byte for byte in the call
              N0  H.baseline.network / H.baseline.tstats -- the unedited
                  legacy network every Gen1 experiment scored
              N3  geometry.apply_edits(N0, [mutate.edit_from_record(pool
                  record add_stop-010#22c4c35ac5b2)]) -- Experiment 3's own
                  construction, validated with contract.validate_applied
    solve     exp4_certify.certify(network, tstats, ...) with EXP4N's
              arguments: lam 2.0, seed 20260825, n_keys 8, k_rungs 3,
              max_rounds 120, allow_off True, waiting model same_route,
              contract_digest = exp4_certify.CERTIFICATION_DIGEST
    caps      exp5_model_resource.ModelResourceEnvelope.to_constraints(),
              which mirrors exp4n_launch.build_constraints field for field

THE ONE ADDITION IS OBSERVATION-ONLY
------------------------------------
EXP4N did not record per-period peak usage: `certify()` keeps only the system
maximum. Experiment 5 must record it, from the SAME FitnessVector that decided
feasibility -- not from a re-score. `certify()` imports `solve_on_network` at
call time, so this module wraps that one name for the duration of the call.
The wrapper returns the callee's own return value, untouched, and records:

  * the budget each setup ENFORCED (`judge.budget`) -- which proves the
    requested caps reached the feasibility check, and that no call saw a
    different budget (D35's lesson: a label is not a constraint);
  * the start audit of the first solve (which starts ran, which won, fallbacks);
  * for every returned plan, the FitnessVector's per-period peak proxy.

After `certify()` returns, the certified plan's record is looked up by the plan
digest `certify()` itself computed, and cross-checked field by field against
the fitness `certify()` reports. Nothing is re-evaluated. The N4 canary proves
the wrapper changes no number: objective, plan digest, rounds, convergence and
the whole per-round trajectory must equal EXP4N's stored result exactly.
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

import exp5_model_resource as MR  # noqa: E402
from exp45_contracts import (K_RUNGS, LAM, MAX_ROUNDS, N_KEYS,  # noqa: E402
                             SEED, START_EVALS, START_RESTARTS, START_WIDTH)

PERIODS = MR.PERIODS
N4_KEY = "exp4|exp4-pool-v1|65lines#35e351133d6f"
N3_ID = "add_stop-010#22c4c35ac5b2"
EXP4N_DIR = ROOT / "outputs" / "exp4_normalized"
EPS_REL = 1e-9          # frequency._EPS_REL, read below and asserted
REACH_DELTA = 1e-6      # >> EPS_REL: moves a cap across usage decisively


class HaltError(RuntimeError):
    def __init__(self, status: str, payload: dict):
        super().__init__(status)
        self.status, self.payload = status, payload


# ---------------------------------------------------------------------------
# small utilities
# ---------------------------------------------------------------------------
def utc() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def atomic_write_json(path: Path, obj: dict) -> None:
    """Write, fsync, rename, fsync the directory (OPERATIONS 3, 31)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + f".tmp{os.getpid()}")
    blob = json.dumps(obj, indent=1, allow_nan=False)
    with open(tmp, "w") as f:
        f.write(blob)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)
    fd = os.open(str(path.parent), os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def plan_key_str(rp) -> str:
    r, p = rp
    return f"{r}|{p}"


def plan_digest(headways: dict) -> str:
    """The digest `certify()` computes: digest({"route|period": float(v)})."""
    from cota_opt.firewall.core import digest
    return digest({plan_key_str(k): float(v) for k, v in headways.items()})


def src_content_digest() -> str:
    """EXP4N's own algorithm (exp4n_restore_verify.py), reused verbatim."""
    return hashlib.sha256(b"".join(sorted(
        p.read_bytes() for p in sorted((ROOT / "src" / "cota_opt").rglob("*.py"))
    ))).hexdigest()[:16]


def data_inputs() -> dict:
    d = json.loads((ROOT / "data" / "raw" / "_provenance.json").read_text())
    return {k: v["sha256"] for k, v in sorted(d.items())}


def pathset_content_digest(cache: dict) -> str:
    h = hashlib.sha256()
    for per in sorted(cache):
        ps = cache[per]
        h.update(per.encode())
        for name in sorted(vars(ps)):
            v = getattr(ps, name)
            if hasattr(v, "tobytes") and hasattr(v, "dtype"):
                h.update(name.encode()); h.update(str(v.dtype).encode())
                h.update(v.tobytes())
            elif name == "rp_keys":
                h.update(repr(list(v)).encode())
    return h.hexdigest()[:16]


def network_content_digest(net, ts) -> str:
    from cota_opt.firewall.core import digest
    pats = sorted((p.route_id, int(p.direction_id), tuple(p.stops),
                   tuple(float(s.run_time_sec) for s in p.segments),
                   int(p.n_trips)) for p in net.patterns.values())
    return digest({"patterns": [list(map(repr, x)) for x in pats],
                   "n_tstats": int(len(ts)),
                   "runtime_min_sum": repr(float(ts["runtime_min"].sum()))})


# ---------------------------------------------------------------------------
# networks
# ---------------------------------------------------------------------------
def build_network(kind: str, st: dict) -> tuple:
    H = st["H"]
    if kind == "N4":
        from cota_opt.exp4_assemble import assemble
        from cota_opt.exp4_network import Exp4Selection
        from exp4_c10_fixtures import POOL_VERSION, _BY_RID, _first_dep_by_period
        prop = json.loads((ROOT / "outputs" / "exp4" / "run" /
                           "proposals.json").read_text())["proposals"]
        lines = {p["state_key"]: p["lines"] for p in prop}[N4_KEY]
        sel = Exp4Selection(POOL_VERSION, frozenset(lines), frozenset())
        fs = json.loads((EXP4N_DIR / "EXP4N_FINAL_STATUS.json").read_text())
        want = fs["leader"]["state_digest"]
        if sel.state_digest != want or fs["leader"]["candidate_id"] != N4_KEY:
            raise HaltError("EXP4_CONTROL_PIPELINE_EQUIVALENCE_FAILURE", {
                "why": "N4 selection does not reproduce the EXP4N leader's "
                       "state digest", "got": sel.state_digest, "want": want})
        built = assemble(sel, _BY_RID, st["graph"], H.baseline.network.stops,
                         pool_version=POOL_VERSION,
                         first_dep_sec_by_period=_first_dep_by_period())
        meta = {"state_key": N4_KEY, "state_digest": sel.state_digest,
                "cardinality": len(lines), "members": sorted(lines),
                "construction": "exp4_assemble.assemble(Exp4Selection)",
                "network_label": "N4 EXP4N normalized leader"}
        return built.network, built.tstats, meta
    if kind in ("N0", "N3"):
        net, ts = H.baseline.network, H.baseline.tstats
        members: list[str] = []
        validation = None
        if kind == "N3":
            from cota_opt import geo
            from cota_opt.contract import ContractLimits, validate_applied
            from cota_opt.geometry import SegmentTimeModel, apply_edits
            from cota_opt.mutate import edit_from_record
            pool = json.loads((ROOT / "outputs" / "exp3" /
                               "mutation_pool.json").read_text())["mutations"]
            rec = {m["id"]: m for m in pool}[N3_ID]
            base = json.loads((ROOT / "outputs" / "exp4" /
                               "pre_exp4_baseline_v1.json").read_text())
            tied = [t["state_key"] for t in base["incumbent"]["tied_set"]]
            if tied != [N3_ID]:
                raise HaltError("EXP4_CONTROL_PIPELINE_EQUIVALENCE_FAILURE", {
                    "why": "pre_exp4_baseline_v1 incumbent is not the "
                           "singleton N3 this runner expects", "tied": tied})
            sg = st["sg"]
            stm = SegmentTimeModel.fit(net, sg)
            edits = [edit_from_record(rec)]
            ed = apply_edits(net, ts, stm, edits)
            limits = ContractLimits(
                veh_hour_budget=float(ts["runtime_min"].sum() / 60.0),
                peak_vehicle_budget=197.0,
                required_waiting_model="same_route")
            chk = validate_applied(
                net, ed.network, edits, limits, coords=stm.coords,
                report=ed.report,
                edited_baseline_veh_hours=float(
                    ed.tstats["runtime_min"].sum() / 60.0),
                waiting_model="same_route")
            chk.raise_if_bad()
            validation = "contract.validate_applied: OK (Experiment 3's own " \
                         "structural validator, as Stage B ran it)"
            net, ts = ed.network, ed.tstats
            members = [N3_ID]
        cd = network_content_digest(net, ts)
        meta = {"state_key": ("exp3|" + N3_ID) if kind == "N3"
                else "cota_existing_local_geometry|N0",
                "state_digest": cd, "cardinality": len(members),
                "members": members,
                "construction": ("geometry.apply_edits(H.baseline, "
                                 "[edit_from_record(pool[N3])])"
                                 if kind == "N3" else
                                 "H.baseline.network / H.baseline.tstats"),
                "network_label": {"N0": "N0 COTA existing local geometry",
                                  "N3": "N3 final Exp 3 constrained redesign"
                                  }[kind],
                "validation": validation}
        return net, ts, meta
    raise ValueError(kind)


# ---------------------------------------------------------------------------
# the observer
# ---------------------------------------------------------------------------
class Observer:
    """Records what each `solve_on_network` call returned. Changes nothing."""

    def __init__(self):
        self.calls = 0
        self.budgets: dict[tuple, int] = {}
        self.start_audit = None
        self.start_meta = None
        self.checks = None
        self.fits: dict[str, dict] = {}
        self.cache = None
        self.keys = None

    def wrap(self, orig):
        def wrapped(net, ts, **kw):
            r = orig(net, ts, **kw)
            self.calls += 1
            b = r["judge"].budget
            key = (repr(float(b.revenue_veh_hours)),
                   tuple(sorted((p, repr(float(v))) for p, v in
                                b.peak_vehicles_by_period.items())),
                   repr(float(b.tolerance)))
            self.budgets[key] = self.budgets.get(key, 0) + 1
            if self.calls == 1:
                self.start_audit = dict(r["repair_audit"])
                self.start_meta = {k: v for k, v in r["solver_meta"].items()
                                   if isinstance(v, (int, float, str, bool))
                                   or v is None}
                self.checks = dict(r["evaluator_checks"])
                self.cache = kw.get("pathset_cache")
                self.keys = list(r["judge"].model.keys)
            f = r["fit"]
            self.fits[plan_digest(r["plan"].headways)] = {
                "peak_by_period": {p: float(v) for p, v in
                                   f.peak_by_period.items()},
                "revenue_veh_hours": float(f.revenue_veh_hours),
                "peak_vehicles": float(f.peak_vehicles),
                "generalized_cost": float(f.generalized_cost),
                "unserved_demand": float(f.unserved_demand),
            }
            return r
        return wrapped


# ---------------------------------------------------------------------------
# one cell
# ---------------------------------------------------------------------------
def boot() -> dict:
    from exp4_c10_fixtures import _boot
    return _boot()


def config_digest(st: dict, cons: dict) -> str:
    from cota_opt.configs import load_cost_weights
    from cota_opt.firewall.core import digest
    res = {k: v for k, v in cons["resource"].items()
           if k not in ("weekday_revenue_vehicle_hours", "peak_fleet_by_period")}
    rest = {k: v for k, v in cons.items() if k != "resource"}
    return digest({"constraints_non_cap": {**rest, "resource": res},
                   "assumptions": st["H"].assumptions,
                   "cost_weights": load_cost_weights()})


def certify_cell(kind: str, env: "MR.ModelResourceEnvelope", *, st: dict,
                 experiment: str, role: str, cell_id: str, arm: str,
                 contract_digest: str, heartbeat: Path | None = None,
                 reach_test: bool = False) -> dict:
    import cota_opt.exp3_score as E3
    from cota_opt import frequency
    from cota_opt.configs import load_constraints
    from cota_opt.exp3_cell import code_version, repo_revision
    from cota_opt.exp4_certify import (CERTIFICATION_CONTRACT,
                                       CERTIFICATION_DIGEST, certify)
    assert frequency._EPS_REL == EPS_REL, "frequency._EPS_REL changed"

    net, ts, ident = build_network(kind, st)
    cons = env.to_constraints(load_constraints())
    traj: list[dict] = []
    t0 = time.time()

    def prog(rnd, obj, blocks):
        traj.append({"round": int(rnd), "objective": repr(float(obj)),
                     "block_enumerations": int(blocks),
                     "elapsed_s": round(time.time() - t0, 1)})
        if heartbeat:
            atomic_write_json(heartbeat, {
                "at": utc(), "pid": os.getpid(), "network": kind,
                "cell_id": cell_id, "role": role, "round": int(rnd),
                "objective": repr(float(obj)),
                "elapsed_s": round(time.time() - t0, 1)})

    obs = Observer()
    orig = E3.solve_on_network
    E3.solve_on_network = obs.wrap(orig)
    try:
        cr = certify(net, ts, state_key=ident["state_key"],
                     state_digest=ident["state_digest"], harness=st["H"],
                     stops_gdf=st["sg"], lam=LAM, seed=SEED, constraints=cons,
                     contract_digest=CERTIFICATION_DIGEST,
                     max_rounds=MAX_ROUNDS, progress=prog)
    finally:
        E3.solve_on_network = orig
    secs = time.time() - t0

    # --- the enforced resource: exactly one budget, equal to the request ----
    if len(obs.budgets) != 1:
        raise HaltError("EXP5_CONSTRAINT_INERT", {
            "why": "setups enforced more than one budget within one cell",
            "budgets": [list(map(str, k)) for k in obs.budgets]})
    (bh, bpeak, btol), = obs.budgets.keys()
    enforced = {"hours_cap": bh, "peak_proxy_caps": dict(bpeak),
                "tolerance": btol, "n_setup_calls_observed": obs.calls}
    req_h = repr(float(env.hours_cap))
    req_p = {p: repr(float(env.peak_proxy_caps[p])) for p in PERIODS}
    if bh != req_h or dict(bpeak) != req_p or btol != repr(0.0):
        raise HaltError("EXP5_CONSTRAINT_INERT", {
            "why": "the budget the setup enforced is not the treatment's caps",
            "requested": {"hours": req_h, "peak": req_p, "tol": "0.0"},
            "enforced": enforced})

    # --- the certified plan's per-period usage, from the same FitnessVector --
    rec_fit = obs.fits.get(cr.plan_digest)
    if rec_fit is None:
        raise HaltError("EXP5_INSTRUMENTATION_FAILURE", {
            "why": "no observed solve returned the certified plan digest"})
    for k in ("revenue_veh_hours", "peak_vehicles", "generalized_cost",
              "unserved_demand"):
        if repr(rec_fit[k]) != repr(float(cr.fitness[k])):
            raise HaltError("EXP5_INSTRUMENTATION_FAILURE", {
                "why": f"observed {k} does not equal certify's own fitness",
                "observed": repr(rec_fit[k]), "certify": repr(cr.fitness[k])})
    if repr(max(rec_fit["peak_by_period"].values())) != repr(
            float(cr.fitness["peak_vehicles"])):
        raise HaltError("EXP5_INSTRUMENTATION_FAILURE", {
            "why": "max of per-period peak != certify's system peak"})
    used_peak = rec_fit["peak_by_period"]
    used_h = float(cr.fitness["revenue_veh_hours"])
    cap_h = float(env.hours_cap)
    caps = {p: float(env.peak_proxy_caps[p]) for p in PERIODS}
    feas = used_h <= cap_h * (1 + EPS_REL) and all(
        used_peak[p] <= caps[p] * (1 + EPS_REL) for p in PERIODS)

    def util(u, c):
        return 100.0 * u / c

    plan = {k: (None if math.isinf(v) else float(v))
            for k, v in sorted(cr.plan.items())}
    n_off = sum(1 for v in plan.values() if v is None)
    locked = int(obs.checks.get("locked_route_periods", 0))

    res_payload = {
        "requested": env.payload(),
        "enforced": enforced,
        "enforced_matches_requested_bit_exact": True,
        "enforced_exact_fingerprint": env.exact_fingerprint,
        "enforced_rounded_envelope_digest": env.rounded_envelope_digest,
        "used": {"revenue_veh_hours": repr(used_h),
                 "peak_proxy_by_period": {p: repr(used_peak[p])
                                          for p in PERIODS},
                 "peak_proxy_source": (
                     "FitnessVector.peak_by_period of the certified plan, "
                     "captured from the solve_on_network return certify() "
                     "adopted; cross-checked against certify's fitness")},
        "slack": {"hours": repr(cap_h - used_h),
                  "peak_proxy_by_period": {p: repr(caps[p] - used_peak[p])
                                           for p in PERIODS}},
        "utilization_pct": {"hours": util(used_h, cap_h),
                            "peak_proxy_by_period": {
                                p: util(used_peak[p], caps[p])
                                for p in PERIODS}},
        "binding_within_1e-6_rel": {
            "hours": used_h >= cap_h * (1 - 1e-6),
            "peak_proxy_by_period": {p: used_peak[p] >= caps[p] * (1 - 1e-6)
                                     for p in PERIODS}},
        "near_binding_within_0.1pct": {
            "hours": used_h >= cap_h * 0.999,
            "peak_proxy_by_period": {p: used_peak[p] >= caps[p] * 0.999
                                     for p in PERIODS}},
        "feasible_under_enforced_caps": bool(feas),
    }
    rec = {
        "schema": "exp45_cell/v1",
        "experiment": experiment, "role": role, "cell_id": cell_id,
        "arm": arm, "network": kind, "contract_digest": contract_digest,
        "identity": ident,
        "search": {"lam": LAM, "seed": SEED, "n_keys": N_KEYS,
                   "k_rungs": K_RUNGS, "max_rounds": MAX_ROUNDS,
                   "allow_off": True, "waiting_model": "same_route",
                   "start": f"gen1 greedy {START_EVALS}/{START_RESTARTS}/"
                            f"{START_WIDTH}",
                   "certification_digest": CERTIFICATION_DIGEST,
                   "certification_contract": CERTIFICATION_CONTRACT,
                   "guarantee": cr.guarantee},
        "resource": res_payload,
        "outcome": {
            "objective_EXACT": repr(float(cr.objective)),
            "fitness_EXACT": {k: repr(float(v)) for k, v in cr.fitness.items()},
            "plan_digest": cr.plan_digest,
            "rounds": int(cr.rounds), "converged": bool(cr.converged),
            "rounds_below_ceiling": int(cr.rounds) < MAX_ROUNDS,
            "block_enumerations": int(cr.block_enumerations),
            "combinations": int(cr.combinations),
            "seconds": round(secs, 1),
            "n_route_periods": len(plan), "n_off": n_off,
            "n_active": len(plan) - n_off, "n_locked_route_periods": locked,
            "round_trajectory": traj,
            "plan_EXACT": plan,
            "plan_encoding": "route|period -> headway minutes; null = OFF "
                             "(frequency.OFF = math.inf)",
        },
        "execution": {
            "start_audit": _clean(obs.start_audit),
            "start_solver_meta": obs.start_meta,
            "evaluator_used": obs.checks.get("common_lines"),
            "evaluator_source": obs.checks.get("common_lines_source"),
            "evaluator_checks": _clean({k: obs.checks.get(k) for k in (
                "common_lines", "common_lines_source", "locked_route_periods",
                "locked_routes", "total_paths", "n_route_periods",
                "od_pairs", "vh_relative_error")}),
            "pathset_digest": (pathset_content_digest(obs.cache)
                               if obs.cache else ""),
            "n_solve_calls_observed": obs.calls,
            "observer": "observation-only wrapper around "
                        "cota_opt.exp3_score.solve_on_network",
        },
        "provenance": {
            "code_version": code_version(),
            "src_cota_opt_content_digest": src_content_digest(),
            "repo_revision": repo_revision(),
            "config_digest": config_digest(st, cons),
            "data_inputs": data_inputs(),
            "data_digest": hashlib.sha256(json.dumps(
                data_inputs(), sort_keys=True).encode()).hexdigest()[:16],
            "runner_sha256": {n: sha256_file(ROOT / "scripts" / n)[:16] for n in
                              ("exp45_certify_cell.py", "exp45_contracts.py",
                               "exp5_model_resource.py",
                               "envelope_fingerprint.py")},
            "python": platform.python_version(),
            "pid": os.getpid(),
        },
        "written_utc": utc(),
    }
    if reach_test:
        rec["reach_test_d35"] = reach_test_run(
            net, ts, env, cr.plan, obs.cache, st, orig, obs.keys)
    return rec


def _clean(d):
    if d is None:
        return None
    out = {}
    for k, v in d.items():
        if isinstance(v, float) and not math.isfinite(v):
            out[k] = repr(v)
        elif isinstance(v, (str, int, float, bool)) or v is None:
            out[k] = v
        elif isinstance(v, (list, tuple)):
            out[k] = [x if isinstance(x, (str, int, float, bool)) else repr(x)
                      for x in v]
        else:
            out[k] = repr(v)
    return out


# ---------------------------------------------------------------------------
# D35 -- does each resource axis actually reach the feasibility decision?
# ---------------------------------------------------------------------------
def reach_test_run(net, ts, env, plan_str: dict, cache, st, solve,
                   keys) -> dict:
    """Pin every route-period to the certified plan (a one-rung ladder), then
    move ONE cap from just above its usage to just below it and nothing else.

    Runs through the whole boundary -- constraints dict -> exp2.build_setup ->
    ResourceBudget -> frequency._feasible inside gen2 solve_exact -- on the
    cell's own path-set scope (paths do not depend on the budget; exp2.py:241).
    Above: the plan must be returned. Below: `solve_exact` must refuse with "no
    ladder combination fits the envelope". Anything else is EXP5_CONSTRAINT_INERT.
    """
    from cota_opt.configs import load_constraints
    plan = {tuple(k.split("|", 1)): float(v) for k, v in plan_str.items()}
    want = plan_digest(plan)
    # exactly certify's ladder keys (locked route-periods are not keys)
    lad = {k: [plan[k]] for k in keys}

    def attempt(e: "MR.ModelResourceEnvelope") -> dict:
        cons = e.to_constraints(load_constraints())
        try:
            r = solve(net, ts, harness=st["H"], stops_gdf=st["sg"], lam=LAM,
                      seed=SEED, iterations=START_EVALS,
                      restarts=START_RESTARTS, width=START_WIDTH,
                      constraints=cons, pathset_cache=cache,
                      waiting_model="same_route", starts="greedy",
                      allow_off=True, solver="exact",
                      exact_max_combinations=10, ladder_override=lad)
        except ValueError as ex:
            if "no ladder combination fits the envelope" in str(ex):
                return {"admissible": False, "refusal": str(ex)[:160]}
            raise
        b = r["judge"].budget
        return {"admissible": True,
                "returned_plan_is_the_pinned_plan":
                    plan_digest(r["plan"].headways) == want,
                "budget_seen_hours": repr(float(b.revenue_veh_hours)),
                "budget_seen_peak": {p: repr(float(v)) for p, v in
                                     b.peak_vehicles_by_period.items()},
                "used_hours": repr(float(r["fit"].revenue_veh_hours)),
                "used_peak": {p: repr(float(v)) for p, v in
                              r["fit"].peak_by_period.items()}}

    def with_caps(hours, peak):
        return MR.ModelResourceEnvelope(
            hours_cap=hours, peak_proxy_caps=peak,
            hours_multiplier=env.hours_multiplier,
            peak_multiplier=env.peak_multiplier,
            source_label=env.source_label,
            base_envelope_digest=env.base_envelope_digest,
            base_exact_fingerprint=env.base_exact_fingerprint)

    base = attempt(env)
    used_h = float(base["used_hours"]) if base["admissible"] else None
    used_p = ({p: float(v) for p, v in base["used_peak"].items()}
              if base["admissible"] else None)
    out = {"method": reach_test_run.__doc__.strip().split("\n\n")[0],
           "delta_rel": REACH_DELTA, "eps_rel_in_feasible": EPS_REL,
           "at_cell_caps": base}
    if not base["admissible"] or not base["returned_plan_is_the_pinned_plan"]:
        out["verdict"] = "EXP5_CONSTRAINT_INERT"
        out["why"] = "the certified plan is not admissible at its own caps"
        return out
    caps = {p: float(env.peak_proxy_caps[p]) for p in PERIODS}
    hi = attempt(with_caps(used_h * (1 + REACH_DELTA), caps))
    lo = attempt(with_caps(used_h * (1 - REACH_DELTA), caps))
    pstar = max(PERIODS, key=lambda p: used_p[p] / caps[p])
    hi_p = attempt(with_caps(float(env.hours_cap),
                             {**caps, pstar: used_p[pstar] * (1 + REACH_DELTA)}))
    lo_p = attempt(with_caps(float(env.hours_cap),
                             {**caps, pstar: used_p[pstar] * (1 - REACH_DELTA)}))
    out.update({
        "hours": {"used": repr(used_h), "cap_above": hi, "cap_below": lo,
                  "reaches_feasibility": hi["admissible"] and not lo["admissible"]},
        "peak_proxy": {"period": pstar, "used": repr(used_p[pstar]),
                       "cap_above": hi_p, "cap_below": lo_p,
                       "reaches_feasibility":
                           hi_p["admissible"] and not lo_p["admissible"]},
    })
    ok = out["hours"]["reaches_feasibility"] and \
        out["peak_proxy"]["reaches_feasibility"]
    out["verdict"] = "PASS" if ok else "EXP5_CONSTRAINT_INERT"
    return out


# ---------------------------------------------------------------------------
# the representation bridge (D34), for a legacy-built network
# ---------------------------------------------------------------------------
def bridge(kind: str, st: dict) -> dict:
    """Score the same network through the legacy construction and through the
    assembler's construction (`exp4_assemble.rebuild_like_assembler`), at
    certify()'s own first step under the EXP4N envelope, and compare exactly.
    This is `scripts/exp4_equivalence.py`'s test, re-aimed at the network and
    configuration the addendum actually uses."""
    import cota_opt.exp3_score as E3
    from cota_opt.configs import load_constraints
    from cota_opt.exp4_assemble import rebuild_like_assembler
    net, ts, ident = build_network(kind, st)
    env = MR.load_base()
    cons = env.to_constraints(load_constraints())
    out = {"network": kind, "identity": ident, "rows": {}}
    for label, (n2, t2) in (("legacy", (net, ts)),
                            ("assembled", rebuild_like_assembler(net, ts))):
        t0 = time.time()
        r = E3.solve_on_network(
            n2, t2, harness=st["H"], stops_gdf=st["sg"], lam=LAM, seed=SEED,
            iterations=START_EVALS, restarts=START_RESTARTS, width=START_WIDTH,
            constraints=cons, pathset_cache={}, waiting_model="same_route",
            starts="greedy", allow_off=True, solver="gen1")
        f = r["fit"]
        out["rows"][label] = {
            "n_patterns": len(n2.patterns),
            "plan_digest": plan_digest(r["plan"].headways),
            "fitness": {k: repr(float(getattr(f, k))) for k in (
                "generalized_cost", "unserved_demand", "served_demand",
                "revenue_veh_hours", "peak_vehicles", "gc_per_served_trip")},
            "peak_by_period": {p: repr(float(v)) for p, v in
                               f.peak_by_period.items()},
            "seconds": round(time.time() - t0, 1)}
    a, b = out["rows"]["legacy"], out["rows"]["assembled"]
    out["identical"] = (a["plan_digest"] == b["plan_digest"]
                        and a["fitness"] == b["fitness"]
                        and a["peak_by_period"] == b["peak_by_period"])
    out["configuration"] = ("certify()'s first step: gen1 greedy "
                            f"{START_EVALS}/{START_RESTARTS}/{START_WIDTH}, "
                            "allow_off=True, EXP4N common envelope, fresh "
                            "path-set scope per arm")
    return out


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("cell")
    c.add_argument("--network", required=True, choices=("N0", "N3", "N4"))
    c.add_argument("--hours", type=float, default=1.0)
    c.add_argument("--peak", type=float, default=1.0)
    c.add_argument("--experiment", required=True, choices=("exp4a", "exp5"))
    c.add_argument("--role", required=True)
    c.add_argument("--contract-digest", required=True)
    c.add_argument("--out", required=True)
    c.add_argument("--heartbeat", default="")
    c.add_argument("--reach-test", action="store_true")
    b = sub.add_parser("bridge")
    b.add_argument("--network", required=True, choices=("N0", "N3"))
    b.add_argument("--out", required=True)
    a = ap.parse_args()

    out = ROOT / a.out
    try:
        st = boot()
        if a.cmd == "bridge":
            atomic_write_json(out, {"written_utc": utc(), **bridge(a.network, st)})
            print(json.dumps({"identical": json.loads(out.read_text())["identical"]}))
            return 0
        base = MR.load_base()
        env = MR.scale(base, a.hours, a.peak)
        cid = MR.cell_id(a.hours, a.peak)
        arm = (MR.ARM_JOINT if a.hours == a.peak else
               MR.ARM_HOURS if a.peak == 1.0 else MR.ARM_PEAK)
        rec = certify_cell(a.network, env, st=st, experiment=a.experiment,
                           role=a.role, cell_id=cid, arm=arm,
                           contract_digest=a.contract_digest,
                           heartbeat=ROOT / a.heartbeat if a.heartbeat else None,
                           reach_test=a.reach_test)
        atomic_write_json(out, rec)
        o = rec["outcome"]
        print(f"{a.network} {cid} obj {o['objective_EXACT']} "
              f"{o['rounds']}r conv {o['converged']} plan {o['plan_digest']} "
              f"({o['seconds']:.0f}s)")
        return 0
    except HaltError as h:
        atomic_write_json(out.with_name(h.status + "." + out.name),
                          {"status": h.status, "written_utc": utc(), **h.payload})
        print(f"!!! {h.status}: {h.payload.get('why')}")
        return 3
    except Exception as e:
        atomic_write_json(out.with_name("ERROR." + out.name), {
            "error": f"{type(e).__name__}: {e}"[:800],
            "traceback": traceback.format_exc()[-4000:], "written_utc": utc()})
        raise


if __name__ == "__main__":
    raise SystemExit(main())
