"""Bring-your-own OD demand: an adapter at the release boundary.

The frozen research harness (``cota_opt.harness.build_harness``) builds demand
from LODES OD only. This module lets a user supply a different OD table
without editing ``src/cota_opt``:

1. ``from_od_csv`` reads a zone-to-zone CSV into the same ``ODTable`` type the
   harness uses, refusing anything it cannot map;
2. ``prepare`` applies the study's own transit-market rules (pairs with a stop
   in walking range at both ends, the top-k cap, the weekday scale), using the
   frozen ``cota_opt.odmatrix`` functions unchanged;
3. ``harness_with_demand`` swaps the table into a harness and enumerates path
   sets under a cache key that includes the table's content digest, so cached
   LODES path sets can never be reused for different demand.

What this does not do: it does not calibrate the new demand, does not change
the period shares (``config/assumptions.yaml``), and produces results that are
not comparable with the study's canonical artifacts. See docs/DATA_INTERFACES.md.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from cota_opt.odmatrix import ODTable, ZoneSystem, _top_k, filter_to_accessible, scale_to

REQUIRED_COLUMNS = ("origin_zone", "dest_zone", "trips")


class DemandInputError(ValueError):
    """The supplied OD file does not satisfy the adapter contract."""


def from_od_csv(path: str | Path, zones: ZoneSystem, source: str,
                allow_unknown_zones: bool = False) -> ODTable:
    """Zone-to-zone weekday trips → ``ODTable``.

    Contract: columns ``origin_zone``, ``dest_zone`` (zone ids as in
    ``zones.zone_ids``; for the study's zone system, 12-digit 2020 block-group
    GEOIDs), ``trips`` (non-negative weekday person trips). Duplicate pairs are
    summed. Unknown zones are refused unless ``allow_unknown_zones``, in which
    case their rows are dropped and counted in ``notes``.
    """
    df = pd.read_csv(path, dtype={"origin_zone": str, "dest_zone": str})
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise DemandInputError(f"missing columns {missing}; need {list(REQUIRED_COLUMNS)}")
    trips = pd.to_numeric(df["trips"], errors="coerce")
    if trips.isna().any() or (trips < 0).any():
        raise DemandInputError("trips must be numeric and non-negative")
    o = df["origin_zone"].map(zones.index)
    d = df["dest_zone"].map(zones.index)
    unknown = o.isna() | d.isna()
    if unknown.any() and not allow_unknown_zones:
        bad = sorted(set(df.loc[o.isna(), "origin_zone"]) | set(df.loc[d.isna(), "dest_zone"]))
        raise DemandInputError(f"{int(unknown.sum())} rows name zones not in the zone system, "
                               f"e.g. {bad[:5]}")
    keep = ~unknown
    oi = o[keep].astype(np.int64).to_numpy()
    di = d[keep].astype(np.int64).to_numpy()
    fl = trips[keep].astype(float).to_numpy()
    key = oi * zones.n + di
    uniq, inv = np.unique(key, return_inverse=True)
    flow = np.bincount(inv, weights=fl)
    notes = f"User-supplied OD from {Path(path).name}: {len(df)} rows, {len(uniq)} zone pairs."
    if unknown.any():
        notes += f" {int(unknown.sum())} rows with unknown zones dropped."
    return ODTable((uniq // zones.n).astype(np.int64), (uniq % zones.n).astype(np.int64),
                   flow, source=source, notes=notes)


def prepare(od: ODTable, zones: ZoneSystem, assumptions: dict,
            rescale: bool = True) -> ODTable:
    """Apply the study's market rules to a supplied table (frozen functions, unchanged).

    ``rescale=True`` scales to ``demand_proxy.assumed_weekday_linked_trips``
    exactly as the study does for LODES; pass ``False`` if the table is already
    in observed weekday trips and should keep its own total.
    """
    pa = assumptions["path_assignment"]
    out = _top_k(filter_to_accessible(od, zones), int(pa["od_top_k"]))
    if rescale:
        out = scale_to(out, float(assumptions["demand_proxy"]["assumed_weekday_linked_trips"]))
    return out


def od_digest(od: ODTable) -> str:
    from cota_opt.cache import digest
    return digest({"o": od.origin, "d": od.dest, "f": od.flow})


def harness_with_demand(od: ODTable, seed: int = 20260825,
                        common_lines: str = "same_route"):
    """A harness whose demand is ``od`` and whose path sets are keyed by its digest.

    Requires the registered GTFS and Census inputs (the network and zones are
    the study's). Returns the harness with ``pathsets`` built for ``od``.
    """
    from cota_opt.harness import build_harness
    from cota_release.reproduce import use_registered_demand_files
    use_registered_demand_files()
    h = build_harness(seed=seed, common_lines=common_lines, with_pathsets=False)
    h.od = od
    h.pathsets = h.pathsets_with([], tag=f"user-od-{od_digest(od)}", seed=seed)
    return h
