"""Adapter contract for user-supplied OD demand (src/cota_release/demand.py).

Deterministic and data-free: a three-zone system built by hand stands in for
the study's block-group zones.
"""
from __future__ import annotations

import numpy as np
import pytest

from cota_opt.odmatrix import ODTable, ZoneSystem
from cota_release import demand


def zones() -> ZoneSystem:
    ids = ["390490001001", "390490001002", "390490001003"]
    # zones 0 and 1 have a stop in walking range; zone 2 has none
    return ZoneSystem(zone_ids=ids, index={z: i for i, z in enumerate(ids)},
                      x=np.zeros(3), y=np.zeros(3), workers=np.ones(3), jobs=np.ones(3),
                      access_offsets=np.array([0, 1, 2, 2]),
                      access_stop=np.array([0, 1]), access_walk=np.array([2.0, 3.0]))


def write(tmp_path, text):
    p = tmp_path / "od.csv"
    p.write_text(text)
    return p


def test_reads_maps_and_sums_duplicates(tmp_path):
    p = write(tmp_path, "origin_zone,dest_zone,trips\n"
                        "390490001001,390490001002,10\n"
                        "390490001001,390490001002,5\n"
                        "390490001002,390490001003,7\n")
    od = demand.from_od_csv(p, zones(), source="test")
    assert isinstance(od, ODTable)
    pairs = {(int(o), int(d)): float(f) for o, d, f in zip(od.origin, od.dest, od.flow)}
    assert pairs == {(0, 1): 15.0, (1, 2): 7.0}
    assert od.source == "test"


def test_refuses_missing_columns_negative_trips_and_unknown_zones(tmp_path):
    with pytest.raises(demand.DemandInputError):
        demand.from_od_csv(write(tmp_path, "o,d,trips\n1,2,3\n"), zones(), source="t")
    with pytest.raises(demand.DemandInputError):
        demand.from_od_csv(write(tmp_path, "origin_zone,dest_zone,trips\n"
                                           "390490001001,390490001002,-1\n"), zones(), source="t")
    p = write(tmp_path, "origin_zone,dest_zone,trips\n390490001001,999999999999,4\n"
                        "390490001001,390490001002,6\n")
    with pytest.raises(demand.DemandInputError):
        demand.from_od_csv(p, zones(), source="t")
    od = demand.from_od_csv(p, zones(), source="t", allow_unknown_zones=True)
    assert od.total() == 6.0 and "1 rows with unknown zones dropped" in od.notes


def test_prepare_applies_study_market_rules(tmp_path):
    p = write(tmp_path, "origin_zone,dest_zone,trips\n"
                        "390490001001,390490001002,30\n"
                        "390490001002,390490001001,10\n"
                        "390490001001,390490001003,60\n")
    od = demand.from_od_csv(p, zones(), source="t")
    a = {"path_assignment": {"od_top_k": 1},
         "demand_proxy": {"assumed_weekday_linked_trips": 100.0}}
    out = demand.prepare(od, zones(), a)
    # zone 2 has no stop -> its pair is dropped; top-1 keeps 0->1; scaled to 100
    assert len(out) == 1 and (int(out.origin[0]), int(out.dest[0])) == (0, 1)
    assert out.total() == pytest.approx(100.0)
    kept = demand.prepare(od, zones(), a, rescale=False)
    assert kept.total() == pytest.approx(30.0)


def test_digest_tracks_content():
    a = ODTable(np.array([0]), np.array([1]), np.array([1.0]))
    b = ODTable(np.array([0]), np.array([1]), np.array([2.0]))
    assert demand.od_digest(a) == demand.od_digest(ODTable(a.origin, a.dest, a.flow.copy()))
    assert demand.od_digest(a) != demand.od_digest(b)
