#!/usr/bin/env python3
"""Evaluate the current COTA plan under a user-supplied OD table.

    python examples/demand_from_csv.py my_od.csv --source "APC-derived OD 2026" [--no-rescale]

The CSV needs columns origin_zone, dest_zone, trips, with zones given as the
study's 12-digit 2020 block-group GEOIDs (docs/DATA_INTERFACES.md, "OD demand").
Needs the registered GTFS and Census inputs (`cota-opt data status`). The
path-set build for new demand takes tens of minutes on one core and is cached
under a key that includes the table's content digest.

The result is a new study: it is not comparable with the canonical artifacts,
and it is uncalibrated.
"""
from __future__ import annotations

import argparse
import json

from cota_opt.harness import build_harness

from cota_release.demand import from_od_csv, harness_with_demand, prepare
from cota_release.model_status import status_record
from cota_release.reproduce import use_registered_demand_files


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("--source", required=True, help="what the table is, for provenance")
    ap.add_argument("--no-rescale", action="store_true",
                    help="keep the table's own total instead of the study's weekday scale")
    a = ap.parse_args()
    use_registered_demand_files()
    base = build_harness(common_lines="same_route", with_pathsets=False)
    od = prepare(from_od_csv(a.csv, base.zones, source=a.source), base.zones,
                 base.assumptions, rescale=not a.no_rescale)
    h = harness_with_demand(od)
    setup = h.setup(with_crowding=True, lock_classes=("peak_express",))
    f = setup.model.evaluate(setup.baseline_plan)
    status = status_record()
    status["demand_source"] = f"user-supplied: {od.source}"
    print(json.dumps({"od_source": od.source, "od_notes": od.notes, "od_total": od.total(),
                      "current_plan": {"unserved": f.unserved_demand,
                                       "served": f.served_demand,
                                       "generalized_cost": f.generalized_cost},
                      "model_status": status}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
