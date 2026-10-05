"""Unit labels for resource quantities, read from the envelope units sidecar.

Report and figure tooling takes every resource-unit label from
``outputs/CANONICAL_ENVELOPE.units.json``, never from the frozen envelope's
``contract_text`` or field names (which say "vehicles" and "fleet" for the
proxy). See docs/process/RELEASE_AND_REPORTING_GUIDELINES.md, report rule 4.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SIDECAR = ROOT / "outputs" / "CANONICAL_ENVELOPE.units.json"

PHYSICAL = "physical_vehicle_count"
PROXY = "modeled_peak_concurrency_proxy"


@lru_cache(maxsize=1)
def sidecar() -> dict:
    return json.loads(SIDECAR.read_text())


def field_class(artifact: str, field: str) -> str:
    return sidecar()["fields"][artifact][field]["class"]


def class_label(cls: str) -> str:
    return sidecar()["classes"][cls]["label"]


def display_label(key: str) -> str:
    """Text for a named axis or table label; refuses a label that misstates its class."""
    entry = sidecar()["display_labels"][key]
    check_label(entry["text"], entry["class"])
    return entry["text"]


def check_label(text: str, cls: str) -> None:
    """Raise if a label presents a physical/proxy quantity under the wrong unit."""
    t = text.lower()
    if cls == PROXY:
        if "proxy" not in t:
            raise ValueError(f"proxy quantity labelled without 'proxy': {text!r}")
        if ("vehicle" in t or "bus" in t or "fleet" in t) and "not vehicles" not in t:
            raise ValueError(f"proxy quantity labelled as vehicles: {text!r}")
    elif cls == PHYSICAL:
        if "proxy" in t:
            raise ValueError(f"physical count labelled as a proxy: {text!r}")
        if "vehicle" not in t and "bus" not in t:
            raise ValueError(f"physical count label names no vehicles: {text!r}")


def leaf_fields(obj, prefix: str = "") -> dict[str, float]:
    """Numeric leaves of a JSON object, keyed by dotted path."""
    out: dict[str, float] = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            out.update(leaf_fields(v, f"{prefix}{k}."))
    elif isinstance(obj, (int, float)) and not isinstance(obj, bool):
        out[prefix[:-1]] = float(obj)
    return out
