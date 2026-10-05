"""Resolve historical repository paths after the 2026-10-05 release restructure.

Frozen artifacts, manifests and archival scripts name files by the paths they
had at `research-final` (`cd03af9c`). `resolve()` returns the current location,
using `docs/research-record/MOVES.json`; a path that was never moved resolves to
itself. Verification scripts use it so that a moved file is still checked
against the hash recorded under its historical name.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MOVES_JSON = ROOT / "docs" / "research-record" / "MOVES.json"


@lru_cache(maxsize=1)
def moves() -> dict[str, str]:
    if not MOVES_JSON.exists():
        return {}
    return json.loads(MOVES_JSON.read_text())["moves"]


def resolve(rel: str | Path) -> Path:
    rel = str(rel)
    p = ROOT / rel
    if p.exists():
        return p
    new = moves().get(rel)
    if new is None:
        # a directory prefix may have moved (e.g. decisions/ -> docs/research-record/decisions/)
        for old, nw in moves().items():
            if rel.startswith(old.rsplit("/", 1)[0] + "/") and old.endswith(rel.rsplit("/", 1)[-1]):
                new = nw
                break
    return ROOT / new if new else p
