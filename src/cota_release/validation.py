"""`cota-opt validate-model`: four-dimensional external validation.

Compares modeled baseline behaviour with observed agency data on four
independent dimensions: route volume, stop pattern, transfer behavior and
trip length. Each reports ``passed``, ``failed`` or ``unavailable``. There is
no overall "validated" result, by design.

A dimension is ``unavailable`` when any of these is missing: observed data,
a threshold set in ``config/validation.yaml`` before the run, or a modeled
counterpart. Modeled metrics come from ``--modeled`` (a JSON file) or, for
route volume only, from the study model itself (``--from-study``, needs the
registered raw inputs). Stop pattern, transfer behavior and trip length have
no modeled extractor yet, so they stay ``unavailable`` even with observed data
until one is written (docs/DATA_INTERFACES.md).

The research CLI's older command ``python -m cota_opt.cli validate`` (GTFS
feed structure validation) is unchanged and unrelated.
"""
from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import yaml

from cota_release.model_status import DIMENSIONS, ROOT, status_record

CONFIG = ROOT / "config" / "validation.yaml"


def _read_csv(path: Path) -> list[dict]:
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def _pct_rmse(modeled: dict[str, float], observed: dict[str, float]) -> tuple[float, int]:
    common = sorted(set(modeled) & set(observed))
    if not common:
        raise ValueError("no ids in common between modeled and observed")
    se = sum((modeled[k] - observed[k]) ** 2 for k in common) / len(common)
    mean_obs = sum(observed[k] for k in common) / len(common)
    return 100.0 * math.sqrt(se) / mean_obs, len(common)


def _unavailable(reason: str) -> dict:
    return {"status": "unavailable", "reason": reason}


def _judge(stat: float, threshold: float, detail: dict) -> dict:
    return {"status": "passed" if stat <= threshold else "failed",
            "statistic": round(stat, 6), "threshold": threshold, **detail}


def validate(observed: dict[str, str | None], thresholds: dict[str, float | None],
             modeled: dict, root: Path = ROOT) -> dict:
    """Return one result per dimension. ``modeled`` keys mirror the dimensions."""
    out: dict[str, dict] = {}

    def obs_path(dim):
        p = observed.get(dim)
        if not p:
            return None
        p = Path(p)
        return p if p.is_absolute() else root / p

    # route volume
    p, t = obs_path("route_volume"), thresholds.get("route_volume_max_pct_rmse")
    if p is None:
        out["route_volume"] = _unavailable("no observed route volumes supplied")
    elif t is None:
        out["route_volume"] = _unavailable("no threshold set before the run")
    elif not modeled.get("route_volume"):
        out["route_volume"] = _unavailable("no modeled route volumes supplied")
    else:
        obs = {r["route_id"]: float(r["boardings"]) for r in _read_csv(p)}
        stat, n = _pct_rmse({k: float(v) for k, v in modeled["route_volume"].items()}, obs)
        out["route_volume"] = _judge(stat, float(t), {"metric": "percent RMSE of route boardings",
                                                      "n_routes_compared": n, "observed": str(p)})
    # stop pattern
    p, t = obs_path("stop_pattern"), thresholds.get("stop_pattern_max_pct_rmse")
    if p is None:
        out["stop_pattern"] = _unavailable("no observed stop activity supplied")
    elif t is None:
        out["stop_pattern"] = _unavailable("no threshold set before the run")
    elif not modeled.get("stop_pattern"):
        out["stop_pattern"] = _unavailable("no modeled stop boardings (no extractor yet)")
    else:
        obs = {r["stop_id"]: float(r["boardings"]) for r in _read_csv(p)}
        stat, n = _pct_rmse({k: float(v) for k, v in modeled["stop_pattern"].items()}, obs)
        out["stop_pattern"] = _judge(stat, float(t), {"metric": "percent RMSE of stop boardings",
                                                      "n_stops_compared": n, "observed": str(p)})
    # transfer behavior
    p, t = obs_path("transfer_behavior"), thresholds.get("transfer_rate_max_abs_diff")
    if p is None:
        out["transfer_behavior"] = _unavailable("no observed transfer data supplied")
    elif t is None:
        out["transfer_behavior"] = _unavailable("no threshold set before the run")
    elif modeled.get("transfer_behavior") is None:
        out["transfer_behavior"] = _unavailable("no modeled transfer rate (no extractor yet)")
    else:
        obs = {r["metric"]: float(r["value"]) for r in _read_csv(p)}
        stat = abs(float(modeled["transfer_behavior"]) - obs["transfer_rate"])
        out["transfer_behavior"] = _judge(stat, float(t), {"metric": "abs diff, transfers per linked trip",
                                                           "observed": str(p)})
    # trip length
    p, t = obs_path("trip_length"), thresholds.get("trip_length_max_ks")
    if p is None:
        out["trip_length"] = _unavailable("no observed trip-length distribution supplied")
    elif t is None:
        out["trip_length"] = _unavailable("no threshold set before the run")
    elif not modeled.get("trip_length"):
        out["trip_length"] = _unavailable("no modeled trip-length distribution (no extractor yet)")
    else:
        rows = sorted(_read_csv(p), key=lambda r: float(r["bin_upper_min"]))
        obs_cum, mod_cum, stat = 0.0, 0.0, 0.0
        mod = {float(k): float(v) for k, v in modeled["trip_length"].items()}
        for r in rows:
            b = float(r["bin_upper_min"])
            obs_cum += float(r["share"])
            mod_cum += mod.get(b, 0.0)
            stat = max(stat, abs(obs_cum - mod_cum))
        out["trip_length"] = _judge(stat, float(t), {"metric": "max abs diff of cumulative shares",
                                                     "observed": str(p)})
    assert set(out) == set(DIMENSIONS)
    return out


def modeled_route_volume_from_study() -> dict[str, float]:
    """Modeled weekday boardings per route on the current plan (Model B, crowding on).

    Needs the registered raw inputs; builds the Exp 1 harness (cached after the
    first run). Boardings are summed over periods from the frozen path-set
    evaluators; the research code is used unchanged.
    """
    from cota_opt.harness import build_harness
    from cota_release.reproduce import use_registered_demand_files
    use_registered_demand_files()
    h = build_harness(common_lines="same_route")
    setup = h.setup(with_crowding=True, lock_classes=("peak_express",))
    model = setup.model
    harr = model.headway_array(setup.baseline_plan)
    vol: dict[str, float] = {}
    for per, ev in model.evaluators.items():
        sub = harr[model._sel[per]]
        b = ev.boardings_by_rp(sub)
        for (route, _period), x in zip(ev.ps.rp_keys, b):
            vol[route] = vol.get(route, 0.0) + float(x)
    return vol


def run(config: Path = CONFIG, modeled_file: str | None = None, from_study: bool = False,
        out: str | None = None) -> int:
    cfg = yaml.safe_load(Path(config).read_text())
    modeled: dict = {}
    if modeled_file:
        modeled = json.loads(Path(modeled_file).read_text())
    if from_study and not modeled.get("route_volume") and cfg["observed"].get("route_volume"):
        modeled["route_volume"] = modeled_route_volume_from_study()
    results = validate(cfg["observed"], cfg["thresholds"], modeled)
    record = {"artifact": "external_validation", "dimensions": results,
              "note": "Four independent statuses; there is deliberately no overall validated flag.",
              "model_status": status_record(), "config": str(config)}
    text = json.dumps(record, indent=1)
    if out:
        Path(out).write_text(text + "\n")
    print(text)
    return 0
