#!/usr/bin/env python3
"""Experiment 6 cell grid and nesting graph -- derived from the frozen
`PolicySpec` objects, never from cell names.

The catalog digest is the sha256 of `outputs/exp6/EXP6_CONSTRAINT_CATALOG.json`
(written by `exp6_freeze.py`); every PolicySpec carries it, so a spec cannot be
mistaken for one built against a different catalog.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from cota_opt.policy import PolicySpec  # noqa: E402

CATALOG = ROOT / "outputs" / "exp6" / "EXP6_CONSTRAINT_CATALOG.json"
ADA_RADIUS_M = 1207.008          # 3/4 statute mile, 49 CFR 37.131(a)(1)
NETWORKS = ("N0", "N3")

_RAW = [
    ("REF", {}),
    ("R1_H60", {"max_headway": 60.0}),
    ("R1_H30", {"max_headway": 30.0}),
    ("R1_H20", {"max_headway": 20.0}),
    ("R2_S25", {"max_off_share": 0.25}),
    ("R2_S10", {"max_off_share": 0.10}),
    ("R2_S05", {"max_off_share": 0.05}),
    ("R3_SPAN", {"span": True}),
    ("R4_C05", {"max_lost_share": 0.05}),
    ("R4_C01", {"max_lost_share": 0.01}),
    ("R4_C00", {"max_lost_share": 0.0}),
    ("R6_ADA", {"area_radius_m": ADA_RADIUS_M}),
    ("B1", {"max_off_share": 0.10, "span": True, "area_radius_m": ADA_RADIUS_M}),
    ("B2", {"max_lost_share": 0.01, "span": True}),
]


def catalog_digest() -> str:
    return hashlib.sha256(CATALOG.read_bytes()).hexdigest()[:16]


def specs(cat_digest: str | None = None) -> dict[str, PolicySpec]:
    d = catalog_digest() if cat_digest is None else cat_digest
    return {name: PolicySpec(cell=name, catalog_digest=d, **kw)
            for name, kw in _RAW}


def hasse(sp: dict[str, PolicySpec]) -> dict:
    """Strict implication order and its covering (adjacent) edges.

    tighter(A, B) := A implies every constraint of B, and not vice versa.
    equal(A, B)   := each implies the other (identical feasible sets).
    Adjacent edges are the transitive reduction of the strict order.
    """
    names = list(sp)
    imp = {(a, b): sp[a].at_least_as_tight_as(sp[b])
           for a in names for b in names if a != b}
    strict = [(a, b) for (a, b), v in imp.items() if v and not imp[(b, a)]]
    equal = sorted({tuple(sorted((a, b))) for (a, b), v in imp.items()
                    if v and imp[(b, a)]})
    s = set(strict)
    cover = [(a, b) for (a, b) in strict
             if not any((a, c) in s and (c, b) in s for c in names)]
    return {"strict_pairs": sorted(strict), "equal_pairs": equal,
            "adjacent_edges": sorted(cover)}


if __name__ == "__main__":
    sp = specs("PREVIEW")
    h = hasse(sp)
    print(len(sp), "cells;", len(h["strict_pairs"]), "strict pairs;",
          len(h["adjacent_edges"]), "adjacent edges;", h["equal_pairs"])
    for a, b in h["adjacent_edges"]:
        print(f"  {a:8s} tighter than {b}")
