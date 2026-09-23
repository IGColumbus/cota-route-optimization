#!/usr/bin/env python3
"""EXP4N — Experiment 4 rerun under ONE common resource envelope.

Reruns the identical 200 geometry candidates from Exp 4. The ONLY change is
resource provenance: `peak_fleet_by_period` is the frozen common vector from
`outputs/exp4_normalized/COMMON_RESOURCE_ENVELOPE.json`, passed explicitly, so
`exp2.py:324`'s per-candidate resolution of the `"baseline"` sentinel never
runs. Hours were already pinned this way.

Unchanged and asserted: LAM, SEED, POOL_VERSION, `assemble`, `certify` under
CERTIFICATION_DIGEST, n_keys, k_rungs, max_rounds, the greedy initialization,
the objective, the exact evaluator, the ladders, the peak USAGE calculation and
the 0.0 tolerance. `src/cota_opt` is not modified.

Writes ONLY under outputs/exp4_normalized/. Never touches outputs/exp4/, which
is frozen as EXP4_ENDOGENOUS_CAP_ARCHIVE. Resumes by file existence.
"""
from __future__ import annotations
import argparse, json, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src")); sys.path.insert(0, str(ROOT / "scripts"))
LEGACY = ROOT / "outputs" / "exp4" / "run"          # READ-ONLY
OUT = ROOT / "outputs" / "exp4_normalized"
CERT = OUT / "certified"
EXPERIMENT = "EXP4N"
POOL_TAG = "exp4-normalized-v1"
LAM, SEED = 2.0, 20260825
PERIODS = ("early", "am_peak", "midday", "pm_peak", "evening", "owl")
OOB_KEY = "exp4|exp4-pool-v1|65lines#eca7a2a1fb46"   # discovery rank 237


def load_envelope():
    p = OUT / "COMMON_RESOURCE_ENVELOPE.json"
    if not p.exists():
        raise SystemExit("COMMON_RESOURCE_ENVELOPE.json is missing; run "
                         "scripts/exp4n_freeze_envelope.py first. This script "
                         "does not resolve the envelope itself, because a "
                         "second resolution is a second envelope.")
    return json.loads(p.read_text())


def build_constraints(spec):
    """The one change, and the assertions that keep it the only one."""
    from cota_opt.configs import load_constraints
    _c = load_constraints()
    assert _c["resource"]["peak_fleet_by_period"] == "baseline", (
        "the config sentinel changed; EXP4N's premise is that the launcher, "
        "not the config, supplies the peak vector")
    tol = float(_c["resource"].get("budget_tolerance", 0.0))
    assert tol == 0.0, f"budget_tolerance is {tol}, must remain 0.0"
    peak = {str(p): float(spec["peak_fleet_by_period"][p]) for p in PERIODS}
    cons = {**_c, "resource": {
        **_c["resource"],
        "weekday_revenue_vehicle_hours": float(spec["weekday_revenue_vehicle_hours"]),
        "peak_fleet_by_period": peak,          # explicit -> exp2.py:326
    }}
    r = cons["resource"]
    assert isinstance(r["peak_fleet_by_period"], dict), \
        "peak_fleet_by_period must be an explicit dict, never the sentinel"
    assert r["peak_fleet_by_period"] != "baseline"
    assert set(r["peak_fleet_by_period"]) == set(PERIODS)
    assert float(r["budget_tolerance"] if "budget_tolerance" in r else 0.0) == 0.0
    return cons, peak


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-hours", type=float, default=6.0)
    ap.add_argument("--only", default="", help="comma-separated labels/keys; "
                    "empty means the whole 200")
    ap.add_argument("--out-of-band", action="store_true",
                    help="certify the rank-237 out-of-band candidate instead, "
                    "into its own directory")
    ap.add_argument("--max-rounds", type=int, default=None,
                    help="override the round CEILING only. Default None keeps "
                    "exp4_certify.MAX_ROUNDS. This is the maximum permitted "
                    "search duration, NOT the convergence criterion: `converged` "
                    "is still set only when a full round finds no improving "
                    "block move. Nothing else about the search changes.")
    ap.add_argument("--out-dir", default=None,
                    help="subdirectory under outputs/exp4_normalized/ to write "
                    "into. Default 'certified'. Use a separate directory for "
                    "any run that must not be mistaken for the production one.")
    ap.add_argument("--trajectory", action="store_true",
                    help="record the per-round incumbent objective so "
                    "convergence shape can be inspected")
    ap.add_argument("--stop-on-nonconvergence", action="store_true",
                    help="PRODUCTION RULE. Halt the whole run the moment any "
                    "candidate returns rounds==max_rounds with converged=False, "
                    "and write EXP4N_CONVERGENCE_FAILURE.json. A ceiling hit is "
                    "a diagnostic alarm, not a result to rank.")
    ap.add_argument("--calibration-dir", default="",
                    help="PRODUCTION CONTROL. Directory of stored calibration "
                    "results. Any candidate present there must reproduce its "
                    "rounds, converged flag and objective exactly; divergence "
                    "halts the run, because it implies something other than the "
                    "round ceiling changed.")
    a = ap.parse_args()

    from cota_opt.exp4_assemble import assemble
    from cota_opt.exp4_certify import (CERTIFICATION_DIGEST, K_RUNGS, MAX_ROUNDS,
                                       N_KEYS, certify)
    from cota_opt.exp4_network import Exp4Selection
    from cota_opt.firewall.core import digest
    from exp4_c10_fixtures import POOL_VERSION, _BY_RID, _boot, _first_dep_by_period

    spec = load_envelope()
    cons, peak = build_constraints(spec)
    ENV_DIGEST = str(spec["envelope_digest"])
    VH_CAP = float(spec["weekday_revenue_vehicle_hours"])

    EFF_MAX_ROUNDS = int(a.max_rounds) if a.max_rounds is not None else int(MAX_ROUNDS)
    assert EFF_MAX_ROUNDS >= 1
    if a.out_dir:
        cert_dir = OUT / a.out_dir
    else:
        cert_dir = (OUT / "out_of_band") if a.out_of_band else CERT
    cert_dir.mkdir(parents=True, exist_ok=True)

    prop = json.loads((LEGACY / "proposals.json").read_text())["proposals"]
    lines_of = {p["state_key"]: p["lines"] for p in prop}
    approx_of = {p["state_key"]: p["objective_APPROXIMATE"] for p in prop}
    ranked = sorted(prop, key=lambda p: (p["objective_APPROXIMATE"], p["state_key"]))
    drank = {p["state_key"]: i for i, p in enumerate(ranked, 1)}

    arch = json.loads((OUT / "EXP4_ENDOGENOUS_CAP_ARCHIVE.json").read_text())
    legacy = {c["state_key"]: c for c in arch["candidates"]}

    if a.out_of_band:
        keys = [OOB_KEY]
    else:
        keys = [c["state_key"] for c in
                sorted(arch["candidates"], key=lambda c: c["certified_rank"])]
        assert len(keys) == 200, f"{len(keys)} candidates, expected 200"
        if a.only:
            want = {s.strip() for s in a.only.split(",") if s.strip()}
            keys = [k for k in keys if k in want or k[-12:] in want]

    st = _boot(); H, sg, graph = st["H"], st["sg"], st["graph"]
    first_dep = _first_dep_by_period()

    todo = [k for k in keys if not (cert_dir / f"{digest(k)}.json").exists()]
    print(f"{EXPERIMENT}  envelope {ENV_DIGEST}  hours {VH_CAP:.6f}  "
          f"lam {LAM}  seed {SEED}  contract {CERTIFICATION_DIGEST}")
    print(f"  peak {json.dumps({p: round(peak[p], 6) for p in PERIODS})}")
    print(f"  n_keys {N_KEYS}  k_rungs {K_RUNGS}  max_rounds {EFF_MAX_ROUNDS}"
          + ("" if EFF_MAX_ROUNDS == MAX_ROUNDS else f"  [CEILING OVERRIDDEN from {MAX_ROUNDS}]"))
    print(f"  writing -> {cert_dir.relative_to(ROOT)}")
    print(f"  {len(keys) - len(todo)} done, {len(todo)} remaining of {len(keys)}"
          + ("  [OUT-OF-BAND]" if a.out_of_band else ""))

    calib = {}
    if a.calibration_dir:
        cd = OUT / a.calibration_dir
        for f in cd.glob("*.json"):
            c = json.loads(f.read_text())
            calib[c["state_key"]] = c
        print(f"  calibration control: {len(calib)} stored results from "
              f"{cd.relative_to(ROOT)}")
    if a.stop_on_nonconvergence:
        print(f"  STOP-ON-NONCONVERGENCE armed: rounds=={EFF_MAX_ROUNDS} with "
              f"converged=False halts the run")

    def _halt(kind: str, payload: dict) -> None:
        payload = {"status": kind, "halted_utc": __import__("datetime").datetime.now(
                       __import__("datetime").timezone.utc).isoformat(timespec="seconds"),
                   **payload}
        (cert_dir.parent / f"{kind}.json").write_text(json.dumps(payload, indent=1))
        print(f"\n!!! {kind} !!!  written to "
              f"{(cert_dir.parent / (kind + '.json')).relative_to(ROOT)}")

    t0 = time.time(); deadline = t0 + a.max_hours * 3600
    for i, k in enumerate(todo, 1):
        if time.time() > deadline:
            print(f"  shard bound reached ({a.max_hours}h); "
                  f"{len(todo) - i + 1} remain. Re-run to resume.")
            break
        sel = Exp4Selection(POOL_VERSION, frozenset(lines_of[k]), frozenset())
        built = assemble(sel, _BY_RID, graph, H.baseline.network.stops,
                         pool_version=POOL_VERSION, first_dep_sec_by_period=first_dep)
        ts = time.time()
        rec = {"experiment": EXPERIMENT, "pool_tag": POOL_TAG,
               "candidate_id": k, "state_digest": sel.state_digest,
               "geometry_digest": sel.state_digest,
               "n_lines": len(lines_of[k]),
               "legacy_certified_rank": legacy[k]["certified_rank"] if k in legacy else None,
               "legacy_objective_EXACT": legacy[k]["objective_EXACT"] if k in legacy else None,
               "discovery_rank": drank.get(k),
               "objective_APPROXIMATE": repr(approx_of.get(k)),
               "common_envelope_digest": ENV_DIGEST,
               "hours_cap": repr(VH_CAP),
               "peak_caps": {p: repr(peak[p]) for p in PERIODS},
               "budget_tolerance": 0.0,
               "lam": LAM, "seed": SEED,
               "contract_digest": CERTIFICATION_DIGEST,
               "n_keys": N_KEYS, "k_rungs": K_RUNGS, "max_rounds": EFF_MAX_ROUNDS,
               "max_rounds_default": MAX_ROUNDS,
               "round_ceiling_overridden": EFF_MAX_ROUNDS != MAX_ROUNDS,
               "cap_provenance": "common_reference_envelope_resolved_once"}
        traj = []
        def _prog(rnd, obj, blocks, _t=traj, _t0=None):
            _t.append({"round": int(rnd), "objective": repr(float(obj)),
                       "block_enumerations": int(blocks),
                       "elapsed_s": round(time.time() - ts, 1)})
        try:
            cr = certify(built.network, built.tstats, state_key=k,
                         state_digest=sel.state_digest, harness=H, stops_gdf=sg,
                         lam=LAM, seed=SEED, constraints=cons,
                         contract_digest=CERTIFICATION_DIGEST,
                         max_rounds=EFF_MAX_ROUNDS,
                         progress=_prog if a.trajectory else None)
        except Exception as e:
            rec.update({"error": f"{type(e).__name__}: {e}"[:500],
                        "seconds": time.time() - ts})
            (cert_dir / f"{digest(k)}.json").write_text(json.dumps(rec, indent=1))
            print(f"  [{i}/{len(todo)}] {k[-12:]} FAILED {type(e).__name__}"[:160])
            continue
        f = cr.payload().get("fitness_EXACT", {})
        hrs = float(f.get("revenue_veh_hours", float("nan")))
        rec.update({**cr.payload(), "lines": lines_of[k],
                    "hours_used": repr(hrs),
                    "hours_feasible": hrs <= VH_CAP,
                    "error": None})
        rec["max_rounds"] = EFF_MAX_ROUNDS      # payload() reports the default
        rec["max_rounds_default"] = int(MAX_ROUNDS)
        rec["round_ceiling_overridden"] = EFF_MAX_ROUNDS != int(MAX_ROUNDS)
        if a.trajectory:
            rec["round_trajectory"] = traj
        (cert_dir / f"{digest(k)}.json").write_text(json.dumps(rec, indent=1))

        # ---- PRODUCTION RULE §5: a ceiling hit is an alarm, not a result ----
        if a.stop_on_nonconvergence and cr.rounds >= EFF_MAX_ROUNDS and not cr.converged:
            t = rec.get("round_trajectory") or []
            objs = [float(x["objective"]) for x in t]
            impr = [t[i]["round"] for i in range(1, len(objs))
                    if objs[i] < objs[i - 1] - 1e-9]
            def _gain(n):
                return (objs[-1 - n] - objs[-1]) if len(objs) > n else None
            _halt("EXP4N_CONVERGENCE_FAILURE", {
                "candidate_id": k, "state_digest": sel.state_digest,
                "legacy_certified_rank": legacy.get(k, {}).get("certified_rank"),
                "max_rounds": EFF_MAX_ROUNDS, "rounds": cr.rounds,
                "converged": cr.converged,
                "objective_at_ceiling": repr(cr.objective),
                "objective_trajectory": t,
                "improving_rounds": impr,
                "every_round_improved": len(impr) == max(len(objs) - 1, 0),
                "still_improving_at_ceiling": (len(objs) >= 2 and
                                               objs[-1] < objs[-2] - 1e-9),
                "improvement_over_final_10_rounds": (repr(_gain(10))
                                                     if _gain(10) is not None else None),
                "improvement_over_final_20_rounds": (repr(_gain(20))
                                                     if _gain(20) is not None else None),
                "n_rounds_with_no_improvement": max(len(objs) - 1, 0) - len(impr),
                "monotone_nonincreasing": all(objs[i] <= objs[i - 1] + 1e-9
                                              for i in range(1, len(objs))),
                "hours_used": rec["hours_used"], "hours_cap": repr(VH_CAP),
                "hours_feasible": rec["hours_feasible"],
                "peak_vehicles_system": repr(float(f.get("peak_vehicles", float("nan")))),
                "peak_caps": rec["peak_caps"],
                "fitness_EXACT": rec.get("fitness_EXACT"),
                "comparison_vs_40_cap": (
                    {kk: calib[k].get(kk) for kk in ("rounds", "converged", "objective_EXACT")}
                    if k in calib else "no stored calibration result for this candidate"),
                "interpretation_REQUIRED": (
                    "Mechanical signals only. Classify slow descent vs cycling vs "
                    "numerical pathology by reading the trajectory; do NOT raise "
                    "max_rounds, do NOT rank this objective, do NOT treat it as "
                    "certified."),
                "candidates_completed_before_halt": len(keys) - len(todo) + i - 1})
            return 2

        # ---- PRODUCTION CONTROL §6: calibration candidates must reproduce ----
        if k in calib:
            c = calib[k]
            same = (cr.rounds == c["rounds"]
                    and bool(cr.converged) == bool(c["converged"])
                    and float(cr.objective) == float(c["objective_EXACT"]))
            if not same:
                _halt("EXP4N_REPRODUCTION_FAILURE", {
                    "candidate_id": k,
                    "legacy_certified_rank": legacy.get(k, {}).get("certified_rank"),
                    "stored_calibration": {"rounds": c["rounds"],
                                           "converged": c["converged"],
                                           "objective_EXACT": c["objective_EXACT"],
                                           "max_rounds": c["max_rounds"]},
                    "production": {"rounds": cr.rounds, "converged": cr.converged,
                                   "objective_EXACT": repr(cr.objective),
                                   "max_rounds": EFF_MAX_ROUNDS},
                    "objective_delta": repr(float(cr.objective) - float(c["objective_EXACT"])),
                    "why_this_halts": (
                        "The calibration established that raising the ceiling changes "
                        "only whether a truncated search is allowed to finish. A "
                        "divergence here means something OTHER than the round ceiling "
                        "differs between the two runs, which invalidates the "
                        "ceiling-only interpretation. Investigate before certifying."),
                    "candidates_completed_before_halt": len(keys) - len(todo) + i - 1})
                return 3
            print(f"       calib-control OK  {k[-12:]} reproduces "
                  f"{c['rounds']}r conv {c['converged']} exactly")

        lg = legacy.get(k, {})
        old = float(lg["legacy_objective_EXACT"]) if "legacy_objective_EXACT" in lg \
            else (float(lg["objective_EXACT"]) if "objective_EXACT" in lg else None)
        tail = ""
        if old:
            tail = f"  old {old:,.4f} d {cr.objective-old:+,.4f} ({(cr.objective-old)/old*100:+.4f}%)"
        print(f"  [{i}/{len(todo)}] r{lg.get('certified_rank','?'):>4} {k[-12:]} "
              f"obj {cr.objective:,.4f} {cr.rounds}r conv {cr.converged} "
              f"({time.time()-ts:.0f}s){tail}")
    done = sorted(cert_dir.glob("*.json"))
    print(f"{EXPERIMENT} results on disk: {len(done)} of {len(keys)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
