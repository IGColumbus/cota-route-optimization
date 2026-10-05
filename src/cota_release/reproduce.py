"""Reproduce Experiment 1 from a clean checkout plus the registered raw data.

* ``--smoke`` rebuilds the Exp 1 evaluation instance exactly as
  ``scripts/seed_check.py`` did (Model B waiting, crowding on, the shared frozen
  path set built from the committed fixpoint plans, 14 peak-express routes
  locked), evaluates the current plan and the three committed certified seed
  plans, and compares the path count and each seed's unserved-demand and
  generalized-cost changes with the canonical record (these decide pass or
  fail). The baseline totals are also compared with the frontier instance's
  record; those rows are informational, because the seed-check instance's own
  baseline was never written to an artifact. No optimization.
* without ``--smoke`` it also re-solves each seed at certification effort
  (400,000 iterations × 20 restarts; about 50 minutes per seed on one core)
  into a scratch store, never the committed one, and compares the result.

Raw data are not committed. Before running, stage the registered inputs under
``data/raw/`` (``config/sources.yaml``; ``docs/REPRODUCE.md`` §0). Without them
the command stops with exit code 3 and says what is missing.
"""
from __future__ import annotations

import hashlib
import json
import platform
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs"
SEP = "::"
#: absolute tolerances for "reproduced": bit-exact is expected in the pinned
#: environment; elsewhere drift is reported against these bounds
TOL_ABS_TRIPS = 1e-6
TOL_PCT_POINTS = 1e-6


def _key(s: str):
    a, b = s.split(SEP, 1)
    return (a, b)


def _rows(path: Path) -> list[dict]:
    return [json.loads(x) for x in path.read_text().splitlines() if x.strip()]


def _environment() -> dict:
    import numpy
    info = {"python": sys.version.split()[0], "platform": platform.platform(),
            "machine": platform.machine(), "numpy": numpy.__version__}
    try:
        cfg = numpy.show_config(mode="dicts")
        info["blas"] = cfg.get("Build Dependencies", {}).get("blas", {})
    except Exception:  # noqa: BLE001
        pass
    import os
    info["env"] = {k: os.environ.get(k) for k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS",
                                                  "MKL_NUM_THREADS", "PYTHONHASHSEED")}
    return info


def exp1(smoke: bool, seeds: list[int], out: str | None, state: str | None = None) -> int:
    sys.path.insert(0, str(ROOT / "src"))
    from cota_opt.registry import Registry
    missing = [k for k in ("cota_gtfs_static", "lodes_od_oh") if Registry().get(k) is None]
    if missing:
        print(f"EXTERNAL_DATA_UNAVAILABLE: registered raw inputs missing: {missing}. "
              "Stage them under data/raw/ (docs/REPRODUCE.md §0).")
        return 3

    from cota_opt.frequency import FrequencyPlan
    from cota_opt.harness import build_harness

    t0 = time.time()
    base_rec = json.loads((OUT / "exp1_baseline_modelB.json").read_text())
    fix = [r for r in _rows(OUT / "fixpoint_modelB.jsonl")
           if str(r.get("cell", "")).startswith("final|lam") and "adequacy" not in r["cell"]]
    finals = {r["lambda"]: {_key(k): float(v) for k, v in r["plan"].items()} for r in fix}
    seed_rows = {r["seed"]: r for r in _rows(OUT / "seedcheck_modelB.jsonl")
                 if str(r.get("cell", "")).startswith("seed") and "|lam2.0|" in r["cell"]}

    H = build_harness(seed=seeds[0], common_lines="same_route")
    extra = [(f"final_lam{m}", finals[m]) for m in sorted(finals)]
    payload = [[n, sorted((f"{k[0]}{SEP}{k[1]}", round(float(v), 6)) for k, v in p.items())]
               for n, p in extra]
    tag = "sc-" + hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:16]
    psets = H.pathsets_with(extra, tag=tag, seed=seeds[0])
    setup = H.setup(with_crowding=True, lock_classes=("peak_express",), seed=seeds[0],
                    pathsets=psets)
    n_paths = sum(p.n_paths for p in setup.pathsets.values())
    bf = setup.model.evaluate(setup.baseline_plan)

    checks = []

    def check(name, got, want, tol, gate=True, note=None):
        d = abs(float(got) - float(want))
        row = {"check": name, "reproduced": float(got), "recorded": float(want),
               "abs_drift": d, "ok": d <= tol, "gate": gate}
        if note:
            row["note"] = note
        checks.append(row)

    check("n_paths", n_paths, base_rec["n_paths"], 0)
    # The seed-check instance's own baseline was never written to an artifact.
    # exp1_baseline_modelB.json holds the baseline of the frontier instance
    # (scripts/fixpoint.py), a different path set of the same size, so these
    # two rows are informational: they show the cross-instance difference,
    # not drift.
    xnote = ("reference is the frontier instance (exp1_baseline_modelB.json); the "
             "seed-check instance's own baseline is not recorded in any artifact")
    check("baseline_unserved_vs_frontier_instance", bf.unserved_demand,
          base_rec["baseline_unserved"], TOL_ABS_TRIPS, gate=False, note=xnote)
    check("baseline_gc_vs_frontier_instance", bf.generalized_cost,
          base_rec["baseline_gc"], TOL_ABS_TRIPS, gate=False, note=xnote)

    for sd in seeds:
        rec = seed_rows[sd]
        plan = FrequencyPlan({_key(k): float(v) for k, v in rec["plan"].items()})
        f = setup.model.evaluate(plan)
        check(f"seed{sd}.unserved_change_pct", (f.unserved_demand / bf.unserved_demand - 1) * 100,
              rec["unserved_change_pct"], TOL_PCT_POINTS)
        check(f"seed{sd}.gc_change_pct", (f.generalized_cost / bf.generalized_cost - 1) * 100,
              rec["gc_change_pct"], TOL_PCT_POINTS)

    solves = []

    def record(status_override=None):
        ok = all(c["ok"] for c in checks if c["gate"])
        rec = {"command": "cota-opt reproduce exp1" + (" --smoke" if smoke else ""),
               "status": status_override or ("REPRODUCED" if ok else "DRIFT"),
               "seconds": round(time.time() - t0, 1), "environment": _environment(),
               "recorded_artifacts": ["outputs/exp1_baseline_modelB.json",
                                      "outputs/seedcheck_modelB.jsonl",
                                      "outputs/fixpoint_modelB.jsonl"],
               "checks": checks}
        if solves:
            rec["solves"] = solves
        text = json.dumps(rec, indent=1)
        if out:
            Path(out).write_text(text + "\n")
        return ok, text

    if not smoke:
        from cota_opt.cache import ResultStore
        from cota_opt.frequency import optimize_frequencies
        # Restart-safe: restart-level progress is checkpointed exactly as the
        # original seed check did (optimize_frequencies progress/resume), and a
        # finished seed is never re-solved. The store lives outside outputs/.
        store = ResultStore(Path(state or (str(out or "reproduce_exp1") + ".state.jsonl")))
        record("IN_PROGRESS")
        for sd in seeds:
            rec = seed_rows[sd]
            done = store.get(f"done|{sd}")
            if done is None:
                part = f"part|{sd}"
                resume = None
                if store.has(part):
                    p = store.get(part)
                    resume = {"next_restart": int(p["next_restart"]),
                              "best_idx": [int(i) for i in p["best_idx"]],
                              "best_obj": float(p["best_obj"]), "moves": int(p.get("moves", 0))}

                def progress(k, idx, obj, moves, _part=part):
                    store.put(_part, {"next_restart": int(k), "best_idx": [int(i) for i in idx],
                                      "best_obj": float(obj), "moves": int(moves),
                                      "at": time.time()})

                ts = time.time()
                r = optimize_frequencies(setup.model, setup.budget, ladder=[],
                                         unserved_multiplier=2.0,
                                         local_search_iterations=400_000, seed=sd,
                                         ladders=setup.ladders, initial=setup.baseline_plan,
                                         n_restarts=20, candidate_width=0, greedy_start=False,
                                         progress=progress, resume=resume)
                done = {"plan": {f"{k[0]}{SEP}{k[1]}": float(v) for k, v in r.plan.headways.items()},
                        "unserved": r.fitness.unserved_demand,
                        "generalized_cost": r.fitness.generalized_cost,
                        "seconds_this_session": round(time.time() - ts, 1),
                        "resumed_at_restart": resume["next_restart"] if resume else 0}
                store.put(f"done|{sd}", done)
            got, want = done["plan"], {k: float(v) for k, v in rec["plan"].items()}
            check(f"seed{sd}.resolved_unserved_change_pct",
                  (done["unserved"] / bf.unserved_demand - 1) * 100,
                  rec["unserved_change_pct"], TOL_PCT_POINTS)
            check(f"seed{sd}.resolved_gc_change_pct",
                  (done["generalized_cost"] / bf.generalized_cost - 1) * 100,
                  rec["gc_change_pct"], TOL_PCT_POINTS)
            n_diff = sum(1 for k in want if k not in got or abs(got[k] - want[k]) > 1e-9) \
                + len(set(got) - set(want))
            check(f"seed{sd}.resolved_plan_route_periods_differing", n_diff, 0, 0)
            solves.append({"seed": sd, "seconds_last_session": done.get("seconds_this_session"),
                           "resumed_at_restart": done.get("resumed_at_restart"),
                           "recorded_seconds": rec.get("seconds"),
                           "plan_digest": _plan_digest(got),
                           "recorded_plan_digest": _plan_digest(want),
                           "unserved": done["unserved"],
                           "generalized_cost": done["generalized_cost"]})
            record("IN_PROGRESS")

    ok, text = record()
    print(text)
    return 0 if ok else 1


def _plan_digest(plan: dict[str, float]) -> str:
    payload = json.dumps(sorted((k, round(v, 6)) for k, v in plan.items()))
    return hashlib.sha256(payload.encode()).hexdigest()[:16]
