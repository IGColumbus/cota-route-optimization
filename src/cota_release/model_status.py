"""Release-facing model status: calibration and validation labels.

Source of truth: ``config/model_status.yaml``. Release tooling stamps
``status_record()`` into every artifact it writes, and ``render_box()`` produces
the model-status box at the top of the briefs, so the box cannot drift from
the recorded state (checked by ``scripts/model_status_box.py --check``).
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
STATUS_FILE = ROOT / "config" / "model_status.yaml"
DIMENSIONS = ("route_volume", "stop_pattern", "transfer_behavior", "trip_length")
STATUSES = ("passed", "failed", "unavailable")


@lru_cache(maxsize=1)
def load() -> dict:
    s = yaml.safe_load(STATUS_FILE.read_text())
    for d in DIMENSIONS:
        if s["validation"].get(d) not in STATUSES:
            raise ValueError(f"validation.{d} must be one of {STATUSES}")
    return s


def status_record() -> dict:
    """The block every release-generated artifact carries."""
    s = load()
    return {"calibration_status": s["calibration"]["status"],
            "validation_status": {d: s["validation"][d] for d in DIMENSIONS},
            "validation_as_of": s["validation"]["as_of"],
            "demand_source": " ".join(s["demand_source"].split()),
            "service_basis": s["service_basis"],
            "source": "config/model_status.yaml"}


def render_box() -> str:
    s = load()
    v = s["validation"]
    names = {"route_volume": "route volume", "stop_pattern": "stop pattern",
             "transfer_behavior": "transfer behavior", "trip_length": "trip length"}
    rows = "\n".join(f"> | {names[d]} | `{v[d]}` |" for d in DIMENSIONS)
    disc = " ".join(s["disclaimers"])
    return (
        "> **Model status** (generated from `config/model_status.yaml`; do not edit by hand)\n"
        ">\n"
        f"> * **Calibration:** {s['calibration']['status']}. "
        f"{' '.join(s['calibration']['statement'].split())}\n"
        f"> * **Demand:** {' '.join(s['demand_source'].split())}.\n"
        f"> * **Service:** {s['service_basis']}.\n"
        f"> * **{disc}**\n"
        ">\n"
        f"> | validation dimension | status (as of {v['as_of']}) |\n"
        "> |---|---|\n"
        f"{rows}\n"
        ">\n"
        f"> There is no single \"validated\" flag. Reason for `unavailable`: {v['reason']}.")
