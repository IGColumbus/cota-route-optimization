#!/usr/bin/env python3
"""Experiment 5 blocking diagnostic -- DIAGNOSTIC ONLY, never a gate.

For each certified cell plan: materialize the timetable, block it with EXP4N's
instrument (same-terminal upper oracle, Dilworth zero-deadhead lower bound),
and ask `exp4_blocking.production_feasible` for the three-valued verdict
against COTA's block-derived fleet (outputs/CANONICAL_ENVELOPE.json, NOT
scaled -- the question is only "could today's physical fleet run this plan")
and against the CELL's own hours cap. FEASIBLE is structurally unreachable
while deadhead provenance is OPEN, so the honest outcomes are INFEASIBLE or
UNDECIDABLE. Nothing here filters, ranks, or gates a cell.

    exp5_blocking.py outputs/exp5/cells/N4_J100.json [...]
"""
from __future__ import annotations

import json
import math
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import exp45_certify_cell as CC  # noqa: E402

MIN_LAYOVER_SEC = 300.0          # scripts/exp4_launch.py
FLEET_MAX_EDGES = 4_000_000      # scripts/exp4_launch.py
OUT = ROOT / "outputs" / "exp5" / "blocking"


def main() -> int:
    from cota_opt.configs import service_periods
    from cota_opt.exp4_blocking import (CandidateFleetBound, ConnectionRule,
                                        SameTerminalOracle,
                                        block_candidate_schedule,
                                        materialize_timetable,
                                        period_lower_bounds,
                                        production_feasible)
    from exp4_c10_fixtures import _first_dep_by_period
    st = CC.boot()
    periods_cfg = service_periods(st["H"].assumptions)
    first_dep = _first_dep_by_period()
    env = json.loads((ROOT / "outputs/CANONICAL_ENVELOPE.json").read_text())
    fleet = {k: int(v) for k, v in env["peak_vehicles_by_period"].items()}
    nets = {}
    OUT.mkdir(parents=True, exist_ok=True)
    for p in sys.argv[1:]:
        rec = json.loads((ROOT / p).read_text())
        name = Path(p).name
        dest = OUT / name
        if dest.exists():
            continue
        t0 = time.time()
        n = rec["network"]
        if n not in nets:
            nets[n] = CC.build_network(n, st)[0]
        plan = {tuple(k.split("|", 1)): (math.inf if v is None else float(v))
                for k, v in rec["outcome"]["plan_EXACT"].items()}
        try:
            tbl = materialize_timetable(nets[n], plan, periods_cfg, first_dep,
                                        source=f"exp5:{name}")
            hi = block_candidate_schedule(
                tbl, SameTerminalOracle(MIN_LAYOVER_SEC), periods_cfg,
                ConnectionRule(min_layover_sec=MIN_LAYOVER_SEC),
                max_edges=FLEET_MAX_EDGES)
            _lb, lo_peak, _lm = period_lower_bounds(tbl, periods_cfg,
                                                    MIN_LAYOVER_SEC)
            bound = CandidateFleetBound(
                lower=int(lo_peak), upper=hi.minimum_blocks,
                lower_oracle="zero_deadhead_relaxation (Dilworth identity)",
                upper_oracle=hi.deadhead_provenance["deadhead_source"],
                deadhead_provenance="OPEN", n_trips=len(tbl))
            vh = float(sum(t.runtime_min for t in tbl.trips)) / 60.0
            cap_h = float(rec["resource"]["requested"]["hours_cap"])
            fb = production_feasible(
                hi, fleet, tbl, periods_cfg, envelope_vehicle_hours=cap_h,
                candidate_vehicle_hours=vh, candidate_bound=bound,
                min_layover_sec=MIN_LAYOVER_SEC,
                envelope_digest=env["envelope_digest"])
            used_h = float(rec["resource"]["used"]["revenue_veh_hours"])
            rel = abs(vh - used_h) / used_h
            verdict, reasons = fb.status, list(fb.reasons)
            if rel > 0.01:
                # The instrument must first reproduce the certified plan's own
                # resource accounting. If its timetable carries a different
                # amount of service, its verdict is about a different plan.
                verdict = "UNDECIDABLE"
                reasons = [f"INSTRUMENT INCONSISTENT: the materialized "
                           f"timetable carries {vh:.3f} vehicle-hours, the "
                           f"certified plan's FitnessVector {used_h:.3f} "
                           f"({100 * rel:.1f}% apart); the instrument's own "
                           f"verdict ({fb.status}) is recorded but not "
                           f"adopted"] + reasons
            out = {"cell": name, "network": n, "cell_id": rec["cell_id"],
                   "status": "DIAGNOSTIC_ONLY", "verdict": verdict,
                   "instrument_raw_verdict": fb.status,
                   "timetable_vs_model_hours_rel_diff": rel,
                   "reasons": reasons,
                   "fleet_bracket_blocks": {"lower_zero_deadhead": int(lo_peak),
                                            "upper_same_terminal_NOT_CERTIFIED":
                                                hi.minimum_blocks},
                   "physical_fleet_reference": fleet,
                   "physical_fleet_reference_digest": env["envelope_digest"],
                   "timetable_vehicle_hours": vh, "cell_hours_cap": cap_h,
                   "n_trips": len(tbl), "seconds": round(time.time() - t0, 1)}
        except Exception as e:     # a diagnostic failure is recorded, not hidden
            out = {"cell": name, "network": n, "status": "DIAGNOSTIC_ONLY",
                   "verdict": "UNDECIDABLE",
                   "reasons": [f"instrument error {type(e).__name__}: {e}"[:400]],
                   "seconds": round(time.time() - t0, 1)}
        CC.atomic_write_json(dest, out)
        print(name, out["verdict"], out.get("fleet_bracket_blocks"),
              out["seconds"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
