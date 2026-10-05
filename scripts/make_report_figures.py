"""Generate the technical report's figures from the study's artifacts.

Implements the figure set in ``docs/process/RELEASE_AND_REPORTING_GUIDELINES.md``
§Figures (seven required figures, guideline IDs G1–G7) plus one figure added by
amendment G2-a (the post hoc F1 decision-space figure). Figures are numbered in
order of first mention in ``docs/report/TECHNICAL_REPORT.md``; the guideline ID
of each is recorded in ``FIGURES_MANIFEST.json``.

Every plotted value is read from an artifact under ``outputs/`` (or, for the
change map, recomputed from the registered GTFS feed by the project's own
``cota_opt.baseline`` code); nothing is typed. Each figure is written as SVG
and PNG to ``docs/report/figures/`` with a CSV of exactly the plotted values.
``FIGURES_MANIFEST.json`` records the sha256 of every input. The script
re-solves nothing.

Usage: python scripts/make_report_figures.py [--skip-map]
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "report" / "figures"

# ---------------------------------------------------------------- inputs
EXP1 = "outputs/canonical/exp1_final.json"
SEEDS = "outputs/seedcheck_modelB.jsonl"
MATRIX = "outputs/matrix.jsonl"
EXP2_TREAT = "outputs/exp2_treatments.jsonl"
EXP2 = "outputs/exp2_summary.json"
EXP2B = "outputs/exp2b_certification.json"
EXP2B_CONF = "outputs/exp2b_confirmation.json"
EXP5 = "outputs/exp5/EXP5_ANALYSIS.json"
EXP6 = "outputs/exp6/EXP6_ANALYSIS.json"
EXP7 = "outputs/exp7/EXP7_ANALYSIS.json"
STAGE1 = "outputs/exp7/stage1/EXP7_STAGE1_ANALYSIS.json"
DSPACE = "outputs/exp7/EXP7_F1_DECISION_SPACE.json"
MAP_CONTRACT = "config/change_map_aggregation.yaml"
GTFS = "data/raw/cota_gtfs_static/cota.gtfs.zip"

# ---------------------------------------------------------------- style
# First three categorical slots of the dataviz reference palette, validated
# all-pairs in light mode (CVD dE >= 9.2, normal-vision dE >= 24.0). Aqua sits
# below 3:1 on the surface, so aqua marks are shape-encoded and direct-labelled,
# and every plotted value is in the CSV beside the figure.
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
INK, INK2, MUTED, GRID, SURFACE = "#0b0b0b", "#52514e", "#8a8984", "#e4e3df", "#ffffff"
BAND = "#eeede9"
# diverging pair blue <-> red, neutral grey midpoint (light mode)
DIV = {"falls more than 10%": "#c23b3a", "falls 2-10%": "#f0a09f",
       "about unchanged (within 2%)": "#f0efec",
       "rises 2-10%": "#86b6ef", "rises more than 10%": "#256abf"}

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 9,
    "axes.edgecolor": MUTED, "axes.labelcolor": INK2,
    "axes.titlesize": 9.5, "axes.titleweight": "bold", "axes.titlecolor": INK,
    "axes.titlelocation": "left",
    "axes.spines.top": False, "axes.spines.right": False, "axes.linewidth": 0.8,
    "xtick.color": INK2, "ytick.color": INK2,
    "xtick.major.width": 0.6, "ytick.major.width": 0.6,
    "grid.color": GRID, "grid.linewidth": 0.6,
    "legend.frameon": False, "legend.fontsize": 8,
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
    "svg.fonttype": "none", "savefig.dpi": 200,
    "svg.hashsalt": "cota-report-figures",  # deterministic SVG element ids
})

USED: set[str] = set()


def J(rel: str):
    USED.add(rel)
    return json.loads((ROOT / rel).read_text())


def JL(rel: str) -> list[dict]:
    USED.add(rel)
    return [json.loads(x) for x in (ROOT / rel).read_text().splitlines() if x.strip()]


def sha(rel: str) -> str:
    return hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()


def pct(v: float, nd: int = 2, sign: bool = False) -> str:
    """Format a percentage with a typographic minus."""
    t = f"{v:+.{nd}f}" if sign else f"{v:.{nd}f}"
    return t.replace("-", "−") + "%"


def num(v: float, nd: int = 2) -> str:
    return f"{v:.{nd}f}".replace("-", "−")


def zero_line(ax, axis="y"):
    (ax.axhline if axis == "y" else ax.axvline)(0, color=MUTED, lw=0.8, zorder=1)


def save(fig, name: str, rows: list[dict]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / f"{name}.svg", bbox_inches="tight", metadata={"Date": None})
    fig.savefig(OUT / f"{name}.png", bbox_inches="tight", metadata={"Software": None})
    plt.close(fig)
    keys: list[str] = []
    for r in rows:
        for k in r:
            if k not in keys:
                keys.append(k)
    with open(OUT / f"{name}.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)


# ================================================================ Figure 1
def fig1_frontier() -> None:
    """G1. Exp 1 frontier: unserved vs GC across lambda, certified from 2."""
    d = J(EXP1)
    fr = sorted(d["frontier"], key=lambda r: r["lambda"])
    h = d["headline"]
    rows = [{"lambda": r["lambda"], "gc_change_pct": round(r["gc_change_pct"], 4),
             "unserved_change_pct": round(r["unserved_change_pct"], 4),
             "path_set_adequate": bool(r["certified"])} for r in fr]
    rows.append({"lambda": "2 (3-seed headline)",
                 "gc_change_pct": round(h["generalized_cost"]["mean_pct"], 4),
                 "unserved_change_pct": round(h["unserved_demand"]["mean_pct"], 4),
                 "gc_seed_sd_pts": round(h["generalized_cost"]["sd_pct"], 4),
                 "unserved_seed_sd_pts": round(h["unserved_demand"]["sd_pct"], 4)})

    fig, ax = plt.subplots(figsize=(6.2, 3.9))
    ax.grid(True, zorder=0)
    xs = [r["gc_change_pct"] for r in fr]
    ys = [r["unserved_change_pct"] for r in fr]
    unc = [r for r in fr if not r["certified"]]
    cer = [r for r in fr if r["certified"]]
    edge = (max(r["gc_change_pct"] for r in unc) + min(r["gc_change_pct"] for r in cer)) / 2
    ax.axvspan(min(xs) - 1, edge, color=BAND, zorder=0, lw=0)
    ax.text(min(xs) - 0.25, -3.0, "λ ≤ 1: path set not\nadequate (uncertified)",
            fontsize=7.5, color=INK2, ha="left", va="center")
    zero_line(ax, "y")
    zero_line(ax, "x")
    ax.plot(xs, ys, color=BLUE, lw=1.4, zorder=2)
    fan = {2.0: (-34, 26), 4.0: (-8, 34), 8.0: (14, 26), 16.0: (30, 12)}
    for r in fr:
        ok = bool(r["certified"])
        ax.scatter(r["gc_change_pct"], r["unserved_change_pct"], s=42, zorder=4,
                   facecolor=BLUE if ok else SURFACE, edgecolor=BLUE, linewidth=1.6)
        lam = r["lambda"]
        if lam in fan:
            ax.annotate(f"λ = {lam:g}", (r["gc_change_pct"], r["unserved_change_pct"]),
                        textcoords="offset points", xytext=fan[lam], ha="center",
                        fontsize=8, color=INK2,
                        arrowprops={"arrowstyle": "-", "color": MUTED, "lw": 0.6,
                                    "shrinkA": 1, "shrinkB": 4})
        else:
            ax.annotate(f"λ = {lam:g}", (r["gc_change_pct"], r["unserved_change_pct"]),
                        textcoords="offset points", xytext=(6, 2), fontsize=8, color=INK2)
    ux, uy = h["generalized_cost"], h["unserved_demand"]
    ax.errorbar(ux["mean_pct"], uy["mean_pct"], xerr=ux["sd_pct"], yerr=uy["sd_pct"],
                fmt="D", ms=5.5, color=INK, mfc=SURFACE, mew=1.3, lw=1.0,
                capsize=2.5, zorder=5)
    ax.annotate(f"λ = 2, 3-seed headline {pct(uy['mean_pct'])}\n(bars: ±1 seed SD)",
                (ux["mean_pct"], uy["mean_pct"]), textcoords="offset points",
                xytext=(-70, -16), ha="right", va="center", fontsize=8, color=INK,
                arrowprops={"arrowstyle": "-", "color": MUTED, "lw": 0.6,
                            "shrinkA": 2, "shrinkB": 5})
    ax.scatter(0, 0, s=30, marker="s", color=INK2, zorder=4)
    ax.annotate("current plan", (0, 0), textcoords="offset points", xytext=(5, 5),
                fontsize=8, color=INK2)
    ax.set_xlim(min(xs) - 0.35, max(xs) + 0.35)
    ax.set_ylim(-10, 17)
    ax.set_xlabel("Total generalized cost vs current plan (%)")
    ax.set_ylabel("Unserved demand vs current plan (%)")
    ax.scatter([], [], s=42, facecolor=BLUE, edgecolor=BLUE,
               label="single run, path set adequate (gate 4)")
    ax.scatter([], [], s=42, facecolor=SURFACE, edgecolor=BLUE, linewidth=1.6,
               label="single run, path set not adequate")
    ax.legend(loc="upper right")
    ax.set_title("Experiment 1: frequency reallocation across the unserved-demand weight λ")
    save(fig, "fig1_exp1_frontier", rows)


# ================================================================ Figure 2 (map)
def _hex(cx: float, cy: float, r: float):
    from shapely.geometry import Polygon
    return Polygon([(cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a)))
                    for a in range(0, 360, 60)])


def fig2_change_map() -> dict:
    """G7. Change pattern map under the frozen aggregation contract."""
    import geopandas as gpd
    import pandas as pd
    import yaml
    from shapely.geometry import LineString

    from cota_opt.baseline import build_baseline
    from cota_opt.configs import period_of_seconds

    USED.add(MAP_CONTRACT)
    USED.add(GTFS)
    C = yaml.safe_load((ROOT / MAP_CONTRACT).read_text())
    crs = C["units"]["crs"]
    b = build_baseline(write=False)
    per_cfg = b.assumptions["service_periods"]
    periods = {k: (float(v[0]), float(v[1])) for k, v in per_cfg.items()}
    ts = b.tstats.copy()
    ts["period"] = ts["first_dep_sec"].map(lambda s: period_of_seconds(s, periods))
    ts = ts.dropna(subset=["period"])

    # baseline supply per route-period (exp1.build_setup definition)
    sup = {}
    for (rid, per), g in ts.groupby(["route_id", "period"]):
        k = int(g["direction_id"].nunique())
        T = (periods[per][1] - periods[per][0]) * 60.0
        sup[(str(rid), per)] = (len(g), k, T)

    # representative shape per route: most frequent shape_id
    rep = ts.groupby("route_id")["shape_id"].agg(lambda s: s.value_counts().idxmax())
    shp = b.feed.shapes.sort_values(["shape_id", "shape_pt_sequence"])
    lines = {}
    for rid, sid in rep.items():
        pts = shp[shp["shape_id"] == sid][["shape_pt_lon", "shape_pt_lat"]].to_numpy()
        if len(pts) >= 2:
            lines[str(rid)] = LineString(pts)
    routes = gpd.GeoDataFrame({"route": list(lines)}, geometry=list(lines.values()),
                              crs="EPSG:4326").to_crs(crs)

    # Rule 1: fixed hex grid anchored at the contract origin
    f2f = float(C["units"]["hex_flat_to_flat_m"])
    R = f2f / math.sqrt(3.0)
    ox, oy = C["units"]["origin_m"]
    minx, miny, maxx, maxy = routes.total_bounds
    c0 = math.floor((minx - ox) / (1.5 * R)) - 1
    c1 = math.ceil((maxx - ox) / (1.5 * R)) + 1
    r0 = math.floor((miny - oy) / f2f) - 1
    r1 = math.ceil((maxy - oy) / f2f) + 1
    hexes, ids = [], []
    for col in range(c0, c1 + 1):
        for row in range(r0, r1 + 1):
            cx = ox + 1.5 * R * col
            cy = oy + f2f * (row + 0.5 * (col % 2))
            hexes.append(_hex(cx, cy, R))
            ids.append((col, row))
    grid = gpd.GeoDataFrame({"hid": range(len(ids)), "cr": ids}, geometry=hexes, crs=crs)
    inter = gpd.overlay(routes, grid, how="intersection", keep_geom_type=True)
    inter["km"] = inter.geometry.length / 1000.0
    inter = inter[inter["km"] > 0]
    route_km = defaultdict(dict)              # hid -> route -> km
    for r in inter.itertuples():
        route_km[int(r.hid)][r.route] = route_km[int(r.hid)].get(r.route, 0.0) + r.km
    live = sorted(route_km)

    def neighbours(h: int) -> set[int]:
        col, row = ids[h]
        if col % 2 == 0:
            cand = [(col, row + 1), (col, row - 1), (col + 1, row), (col + 1, row - 1),
                    (col - 1, row), (col - 1, row - 1)]
        else:
            cand = [(col, row + 1), (col, row - 1), (col + 1, row), (col + 1, row + 1),
                    (col - 1, row), (col - 1, row + 1)]
        idx = {c: i for i, c in enumerate(ids)}
        return {idx[c] for c in cand if c in idx}

    # plans: current and the three certified seeds
    seed_rows = [r for r in JL(SEEDS)
                 if str(r.get("cell", "")).startswith("seed")
                 and "|lam2.0|" in str(r.get("cell", "")) and isinstance(r.get("plan"), dict)]
    seed_rows = sorted(seed_rows, key=lambda r: r["cell"])
    if len(seed_rows) != 3:
        raise SystemExit(f"expected 3 certified seed plans, found {len(seed_rows)}")

    def route_trips(plan: dict | None) -> dict[str, float]:
        out = defaultdict(float)
        for (rid, per), (n, k, T) in sup.items():
            if plan is None:
                out[rid] += n
            else:
                hdw = float(plan[f"{rid}::{per}"])
                out[rid] += k * T / hdw
        return out

    base_trips = route_trips(None)
    seed_trips = [route_trips(r["plan"]) for r in seed_rows]
    mean_dtrips = {rid: sum(s[rid] for s in seed_trips) / 3 - base_trips[rid]
                   for rid in base_trips}

    # units as sets of hexes; Rules 2 and 3 with the contract's merge rule
    units: dict[int, set[int]] = {h: {h} for h in live}
    owner = {h: h for h in live}

    def unit_routes(u: int) -> dict[str, float]:
        acc = defaultdict(float)
        for h in units[u]:
            for rid, km in route_km[h].items():
                acc[rid] += km
        return acc

    def fails(u: int) -> bool:
        rk = unit_routes(u)
        if len(rk) < C["min_routes_per_unit"]:
            return True
        contrib = [abs(km * mean_dtrips.get(rid, 0.0)) for rid, km in rk.items()]
        tot = sum(contrib)
        return tot > 0 and max(contrib) / tot > C["dominance_share_max"]

    def adj(u: int) -> set[int]:
        nb = set()
        for h in units[u]:
            for n in neighbours(h):
                if n in owner and owner[n] != u:
                    nb.add(owner[n])
        return nb

    dropped = 0
    for phase in ("routes", "dominance"):
        changed = True
        while changed:
            changed = False
            for u in sorted(units):
                bad = (len(unit_routes(u)) < C["min_routes_per_unit"]) if phase == "routes" else fails(u)
                if not bad:
                    continue
                nb = adj(u)
                if not nb:
                    if phase == "dominance" or len(unit_routes(u)) < C["min_routes_per_unit"]:
                        for h in units[u]:
                            owner.pop(h, None)
                        del units[u]
                        dropped += 1
                        changed = True
                        break
                    continue
                tgt = sorted(nb, key=lambda v: (-len(unit_routes(v)), v))[0]
                units[tgt] |= units[u]
                for h in units[u]:
                    owner[h] = tgt
                del units[u]
                changed = True
                break

    def vkm(trips: dict[str, float], u: int) -> float:
        return sum(km * trips.get(rid, 0.0) for rid, km in unit_routes(u).items())

    def direction(x: float) -> str:
        return "falls" if x < -0.02 else ("rises" if x > 0.02 else "unchanged")

    rows, colour = [], {}
    for u in sorted(units):
        base = vkm(base_trips, u)
        ch = [(vkm(s, u) - base) / base for s in seed_trips]
        dirs = {direction(c) for c in ch}
        mean = sum(ch) / 3
        band = next(bd["label"] for bd in C["bands"]
                    if float(bd["lo"]) <= mean < float(bd["hi"]))
        stable = len(dirs) == 1
        colour[u] = band if stable else None
        rows.append({"unit": u, "n_hex": len(units[u]), "n_routes": len(unit_routes(u)),
                     "seed_directions": "/".join(direction(c) for c in ch),
                     "agreement": stable, "band": band if stable else "no stable pattern"})

    geoms = [grid.geometry.iloc[sorted(units[u])].union_all() for u in sorted(units)]
    ug = gpd.GeoDataFrame({"unit": sorted(units),
                           "band": [colour[u] or "no stable pattern" for u in sorted(units)]},
                          geometry=geoms, crs=crs)

    fig, ax = plt.subplots(figsize=(6.4, 5.6))
    routes.plot(ax=ax, color="#d9d8d3", lw=0.5, zorder=1)
    for band, col in DIV.items():
        sub = ug[ug["band"] == band]
        if len(sub):
            sub.plot(ax=ax, color=col, edgecolor=SURFACE, lw=1.2, zorder=2, alpha=0.92)
    ns = ug[ug["band"] == "no stable pattern"]
    if len(ns):
        ns.plot(ax=ax, facecolor=SURFACE, edgecolor=MUTED, hatch="////", lw=0.6, zorder=2)
    ax.set_axis_off()
    x0, y0, x1, y1 = ug.total_bounds
    sb = 5000
    ax.plot([x0, x0 + sb], [y0 - 1500, y0 - 1500], color=INK, lw=1.5)
    ax.text(x0 + sb / 2, y0 - 2400, "5 km", ha="center", va="top", fontsize=7.5, color=INK)
    handles = [Patch(facecolor=c, edgecolor=MUTED, lw=0.4, label=b) for b, c in DIV.items()
               if (ug["band"] == b).any()]
    handles.append(Patch(facecolor=SURFACE, edgecolor=MUTED, hatch="////",
                         label="no stable pattern (seeds disagree)"))
    ax.legend(handles=handles, loc="upper left", bbox_to_anchor=(1.0, 1.0),
              title="Scheduled vehicle-km, seed mean\n(coloured only if all 3 seeds agree)",
              title_fontsize=7.5)
    ax.set_title("Experiment 1: where scheduled service rises and falls (λ = 2)\n"
                 + C["caption_required"], loc="left")
    save(fig, "fig2_exp1_change_map", rows)
    return {"units": len(units), "dropped": dropped,
            "agreeing": sum(1 for u in units if colour[u]),
            "seed_cells": [r["cell"] for r in seed_rows]}


# ================================================================ Figure 3
def fig3_geometry_null() -> None:
    """G3. Splice effects at ranking vs certification effort, floors as bands."""
    s = J(EXP2)
    b = J(EXP2B)
    conf = J(EXP2B_CONF)
    sing = s["singles"]
    rec = s["recheck_D19"]
    rank = {c["candidate"]: c["unserved_vs_noedit_pct_lam2.0"] for c in sing["candidates"]}
    cert = {c["candidate"]: c["unserved_vs_noedit_pct"] for c in rec["candidates"]}
    order = sorted(rank, key=lambda k: rank[k])
    short = {k: k.split("|")[1] + "+" + k.split("|")[2] for k in order}
    leader = b["set"]
    ms = b["_confirmation"]["matched_start_unserved_effect_pct"]
    per_seed = [p["unserved_effect_pct"] for p in conf["per_seed"]]
    f_rank = sing["noise_floor_pts"]
    f_cert = rec["full_effort_floor_pts"]

    rows = [{"splice": k, "ranking_effort_pct": round(rank[k], 4),
             "certification_effort_pct": round(cert[k], 4) if k in cert else None}
            for k in order]
    rows.append({"splice": leader + " (2B leader, matched starts)",
                 "certification_effort_pct": round(ms, 4),
                 "per_seed": ";".join(f"{v:.4f}" for v in per_seed)})
    rows.append({"splice": "floor (ranking effort, ± pts)", "ranking_effort_pct": round(f_rank, 4)})
    rows.append({"splice": "floor (certification effort, ± pts)",
                 "certification_effort_pct": round(f_cert, 4)})

    fig, (a, c) = plt.subplots(1, 2, figsize=(7.4, 3.7), sharey=True,
                               gridspec_kw={"width_ratios": [2.2, 1], "wspace": 0.08})
    xs = range(len(order))
    for ax, f in ((a, f_rank), (c, f_cert)):
        ax.axhspan(-f, f, color=BAND, zorder=0, lw=0)
        ax.grid(True, axis="y", zorder=0)
        zero_line(ax, "y")
    a.scatter(list(xs), [rank[k] for k in order], s=34, color=BLUE, zorder=3)
    a.set_xticks(list(xs))
    a.set_xticklabels([short[k] for k in order], rotation=60, ha="right", fontsize=7.5)
    a.text(len(order) - 0.6, f_rank + 0.05, f"noise floor ±{num(f_rank)} pts",
           ha="right", fontsize=7.5, color=INK2)
    a.set_ylabel("Unserved demand vs no edit (%)")
    a.set_title("a  Ranking effort (60,000/2), 12 single splices")
    co = [k for k in order if k in cert]
    cx = range(len(co))
    c.scatter(list(cx), [cert[k] for k in co], s=34, facecolor=SURFACE, edgecolor=BLUE,
              linewidth=1.4, zorder=3, label="single-seed recheck")
    li = co.index(leader) if leader in co else None
    if li is not None:
        c.scatter([li + 0.25] * len(per_seed), per_seed, s=14, color=ORANGE, zorder=4,
                  marker="o", label="2B leader, matched starts (per seed)")
        c.scatter([li + 0.25], [ms], s=46, marker="_", color=INK, zorder=5, linewidths=1.6)
        c.annotate(f"{pct(ms, 3, True)}\n(0.31 floors)", (li + 0.25, ms),
                   textcoords="data", xytext=(li + 1.2, -0.5), va="center", fontsize=7.5,
                   color=INK,
                   arrowprops={"arrowstyle": "-", "color": MUTED, "lw": 0.6})
    c.set_xticks(list(cx))
    c.set_xticklabels([short[k] for k in co], rotation=60, ha="right", fontsize=7.5)
    c.set_xlim(-0.6, len(co) - 0.4)
    c.text(-0.5, f_cert + 0.05, f"floor ±{num(f_cert, 3)} pts", ha="left",
           va="bottom", fontsize=7.5, color=INK2)
    c.set_title("b  Certification effort (400,000/20)")
    c.legend(loc="upper left", bbox_to_anchor=(0.0, 0.80), fontsize=6.8, ncol=1)
    fig.suptitle("Experiments 2 and 2B: through-routing splices against the noise floor (λ = 2)",
                 x=0.06, ha="left", y=1.01, fontsize=10, fontweight="bold", color=INK)
    save(fig, "fig3_exp2_geometry_null", rows)


# ================================================================ Figure 4
def _near_binding(r: dict) -> list[str]:
    nb = r.get("near_binding_0.1pct")
    if isinstance(nb, dict):
        return [k for k, v in nb.items() if v]
    if isinstance(nb, (list, tuple)):
        return [str(x) for x in nb]
    return []


def fig4_resource_curve() -> None:
    """G4. Exp 5 objective vs envelope level; hours arm separately."""
    e = J(EXP5)
    fr = e["frontier"]
    viol = [p for p in e["monotonicity"]["pairs"]
            if p.get("status") == "EXP5_MONOTONICITY_FAILURE"]
    viol_cells = defaultdict(set)
    for p in viol:
        for k in ("tighter", "looser", "cell_a", "cell_b", "a", "b"):
            if k in p and isinstance(p[k], str):
                viol_cells[p.get("network", "")].add(p[k])
    rows = []
    fig, axs = plt.subplots(2, 2, figsize=(7.2, 5.4), sharey="row")
    for i, net in enumerate(("N0", "N4")):
        cells = [r for r in fr if r["network"] == net]
        ref = next(r for r in cells if r["cell"].endswith("J100"))
        for r in cells:
            rows.append({"network": net, "cell": r["cell"], "arm": r["arm"],
                         "hours_mult": r["hours_mult"], "peak_mult": r["peak_mult"],
                         "objective": round(r["objective"], 2),
                         "objective_vs_J100_pct": round(100 * (r["objective"] - ref["objective"])
                                                        / ref["objective"], 4),
                         "near_binding_periods": ";".join(_near_binding(r)),
                         "in_monotonicity_failure": r["cell"] in viol_cells.get(net, set())})
        for j, (arm_key, xkey, ttl) in enumerate((
                ("C_peak_proxy_only", "peak_mult", "peak envelope only"),
                ("B_hours_only", "hours_mult", "revenue-hour budget only"))):
            ax = axs[i, j]
            ax.grid(True, zorder=0)
            zero_line(ax, "y")
            ax.axvline(100, color=MUTED, lw=0.6, ls=":", zorder=1)
            joint = sorted([r for r in cells if r["arm"].startswith("A_joint")],
                           key=lambda r: r[xkey])
            arm = sorted([r for r in cells if r["arm"] == arm_key] + [ref],
                         key=lambda r: r[xkey])
            for seq, col, lab, ls in ((joint, MUTED, "joint (both scaled)", "--"),
                                      (arm, BLUE if j == 0 else ORANGE, ttl, "-")):
                xs = [100 * r[xkey] for r in seq]
                ys = [100 * (r["objective"] - ref["objective"]) / ref["objective"] for r in seq]
                ax.plot(xs, ys, color=col, lw=1.4 if ls == "-" else 1.0, ls=ls, zorder=2,
                        label=lab)
                for r, x, y in zip(seq, xs, ys):
                    nb = bool(_near_binding(r))
                    ax.scatter(x, y, s=26, zorder=3, facecolor=col if nb else SURFACE,
                               edgecolor=col, linewidth=1.2)
                    if r["cell"] in viol_cells.get(net, set()) and ls == "-":
                        ax.scatter(x, y, s=70, marker="o", facecolor="none",
                                   edgecolor=INK, linewidth=0.9, zorder=4)
            if i == 1:
                ax.set_xlabel("% of peak envelope — proxy units" if j == 0
                              else "% of revenue-hour budget (below 100 = service cuts)")
            if j == 0:
                ax.set_ylabel(f"{net}: objective vs J100 (%)")
            ax.set_title(f"{'abcd'[2 * i + j]}  {net}, {ttl}")
            ax.legend(loc="upper right", fontsize=7)
    fig.text(0.06, -0.02, "Filled marker: at least one period within 0.1% of its cap "
             "(near-binding). Ringed: cell in a pair that fails monotonicity "
             "(EXP5_MONOTONICITY_FAILURE; N4 only).", fontsize=7.5, color=INK2)
    fig.suptitle("Experiment 5: modeled operating-resource frontier (diagnostic; status FAILED)",
                 x=0.06, ha="left", y=1.01, fontsize=10, fontweight="bold", color=INK)
    fig.tight_layout()
    save(fig, "fig4_exp5_resource_curve", rows)


# ================================================================ Figure 5
REGIMES = [
    ("R1: maximum headway", [("REF", "none"), ("R1_H60", "max(60, base)"),
                             ("R1_H30", "30 min"), ("R1_H20", "20 min")]),
    ("R2: OFF-share cap", [("REF", "none"), ("R2_S25", "25%"), ("R2_S10", "10%"),
                           ("R2_S05", "5%")]),
    ("R4: coverage c", [("REF", "none"), ("R4_C05", "0.05"),
                                     ("R4_C01", "0.01"), ("R4_C00", "0")]),
    ("R3, R6 and bundles", [("REF", "none"), ("R3_SPAN", "span"), ("R6_ADA", "¾-mile"),
                            ("B1", "B1"), ("B2", "B2")]),
]


def fig5_policy_frontiers() -> None:
    """G5. Price against constraint level, one panel per regime."""
    e6 = {(r["network"], r["cell"]): r for r in J(EXP6)["firewall"]["policy"]}
    e7 = {(r["network"], r["cell"]): r for r in J(EXP7)["f6_prices"] if r["level"] == "BASE"}
    infeasible = {r["record"].split(":")[1] for r in J(EXP6)["empty_feasible_sets"]}
    rows = []
    fig, axs = plt.subplots(1, 4, figsize=(8.6, 3.5), sharey=True,
                            gridspec_kw={"wspace": 0.12})
    for ax, (title, levels) in zip(axs, REGIMES):
        ax.grid(True, axis="y", zorder=0)
        zero_line(ax, "y")
        for net, col, dx in (("N0", BLUE, -0.09), ("N3", ORANGE, 0.09)):
            x6, y6 = [], []
            for xi, (cell, lab) in enumerate(levels):
                if cell == "REF":
                    p6, p7 = 0.0, 0.0
                else:
                    r6, r7 = e6.get((net, cell)), e7.get((net, cell))
                    p6 = r6.get("effect_pct") if r6 else None
                    p7 = 100 * r7["price"] if r7 and r7.get("price") is not None else None
                rows.append({"regime": title, "cell": cell, "level": lab, "network": net,
                             "exp6_price_pct": None if p6 is None else round(p6, 4),
                             "exp7_base_reclosed_price_pct": None if p7 is None else round(p7, 4),
                             "infeasible_under_envelope": f"{net}_{cell}" in infeasible})
                if p6 is not None:
                    x6.append(xi + dx)
                    y6.append(p6)
                    ax.scatter(xi + dx, p6, s=30, color=col, zorder=3, edgecolor=SURFACE,
                               linewidth=0.8)
                if p7 is not None and cell != "REF":
                    ax.scatter(xi + dx, p7, s=30, facecolor=SURFACE, edgecolor=col,
                               linewidth=1.3, zorder=3)
                if p6 is None and f"{net}_{cell}" in infeasible:
                    ax.annotate(f"{net}:\ninfeasible", (xi + dx, 0.02), fontsize=7,
                                color=INK2, ha="center", va="bottom", annotation_clip=False)
            if title.startswith(("R1", "R2", "R4")):
                ax.plot(x6, y6, color=col, lw=1.0, zorder=2, alpha=0.8)
        ax.set_xticks(range(len(levels)))
        ax.set_xticklabels([lab for _, lab in levels], rotation=35, ha="right", fontsize=7.5)
        ax.set_xlim(-0.5, len(levels) - 0.5)
        ax.set_title(title, fontsize=8.5)
        ax.text(0.02, 0.97, "study safeguard;\nno COTA anchor", transform=ax.transAxes,
                fontsize=6.8, color=INK2, va="top")
    axs[0].set_ylabel("Modeled price (% of objective)")
    hs = [plt.Line2D([], [], marker="o", ls="", color=BLUE, label="N0, Exp 6"),
          plt.Line2D([], [], marker="o", ls="", color=ORANGE, label="N3, Exp 6"),
          plt.Line2D([], [], marker="o", ls="", mfc=SURFACE, mec=BLUE, mew=1.3,
                     label="N0, Exp 7 BASE re-closed"),
          plt.Line2D([], [], marker="o", ls="", mfc=SURFACE, mec=ORANGE, mew=1.3,
                     label="N3, Exp 7 BASE re-closed")]
    fig.legend(handles=hs, loc="lower center", ncol=4, bbox_to_anchor=(0.5, -0.12), fontsize=7.5)
    fig.suptitle("Experiment 6: modeled price of study safeguards by regime (closed cell − closed REF)",
                 x=0.06, ha="left", y=1.02, fontsize=10, fontweight="bold", color=INK)
    save(fig, "fig5_exp6_policy_frontiers", rows)


# ================================================================ Figure 6
DIMS = [("A1", "A1 demand"), ("A2", "A2 bootstrap"), ("A3", "A3 runtimes"),
        ("A5", "A5 λ / transfers"), ("A6", "A6 walking"), ("A7", "A7 route removal"),
        ("A8", "A8 retention")]
FINDINGS = [("F1", "F1", "F1  Exp 1 plan vs current\nunserved demand (%)"),
            ("F2_unserved", "F2_unserved", "F2  splice vs no edit\nunserved demand (%)"),
            ("F3", "F3", "F3  N3 add_stop vs control\nobjective (%)"),
            ("F4_43", "F4_43", "F4  N4 − N3\nobjective (% of N3)")]


def _sign_label(cls: dict, key: str) -> str:
    c = cls.get(key) or {}
    s = c.get("sign") if isinstance(c, dict) else None
    return (s or {}).get("label", "—") if isinstance(s, dict) else "—"


def fig6_robustness() -> None:
    """G6. Findings against the Exp 7 Class A dimensions (Stage 1, fixed plans)."""
    a = J(STAGE1)
    vals = a["values"]
    cls = a["classification"]
    rows = []
    fig, axs = plt.subplots(1, 4, figsize=(9.0, 3.6), sharey=True,
                            gridspec_kw={"wspace": 0.18})
    ypos = {p: len(DIMS) - i for i, (p, _) in enumerate(DIMS)}
    for ax, (vkey, ckey, title) in zip(axs, FINDINGS):
        base = vals["BASE"][vkey]
        ax.grid(True, axis="x", zorder=0)
        zero_line(ax, "x")
        ax.axvline(base, color=INK2, lw=0.9, ls="--", zorder=2)
        for lvl, v in vals.items():
            if lvl == "BASE" or not isinstance(v, dict) or v.get(vkey) is None:
                continue
            pref = lvl.split("_")[0]
            if pref not in ypos:
                continue
            x = v[vkey]
            rows.append({"finding": vkey, "level": lvl, "value": round(x, 5)})
            flip = (x > 0) != (base > 0) and x != 0
            ax.scatter(x, ypos[pref], s=22, zorder=3,
                       facecolor=SURFACE if flip else BLUE, edgecolor=BLUE, linewidth=1.1)
        rows.append({"finding": vkey, "level": "BASE", "value": round(base, 5)})
        lab = _sign_label(cls, ckey)
        rows.append({"finding": vkey, "level": "preregistered_sign_label", "value": lab})
        ax.set_title(f"{title}\n{lab}", fontsize=7.8)
        ax.tick_params(axis="x", labelsize=7.5)
    axs[0].set_yticks(list(ypos.values()))
    axs[0].set_yticklabels([lab for _, lab in DIMS])
    axs[0].set_ylim(0.4, len(DIMS) + 0.6)
    fig.text(0.06, -0.04, "Dashed line: Stage 1 BASE value. Hollow marker: level whose sign "
             "differs from BASE. Labels are the preregistered sign labels "
             "(EXP7_STAGE1_ANALYSIS.json → classification).", fontsize=7.5, color=INK2)
    fig.suptitle("Experiment 7 Stage 1: findings at 44 Class A levels (fixed plans)",
                 x=0.06, ha="left", y=1.1, fontsize=10, fontweight="bold", color=INK)
    save(fig, "fig6_exp7_robustness", rows)


# ================================================================ Figure 7
CELL_STYLE = {
    "REF": ("REF, F6-track closure", BLUE, "o"),
    "REF_F4": ("REF, F4-track closure", BLUE, "^"),
    "R3_SPAN": ("R3_SPAN (period span kept)", ORANGE, "s"),
    "R1_H60": ("R1_H60 (no OFF, ≤ max(60, baseline) min)", AQUA, "D"),
    "R1_H30": ("R1_H30 (no OFF, ≤ 30 min)", AQUA, "v"),
}
LAM = {"A5_LAM1": 1.0, "A5_LAM4": 4.0}


def fig7_decision_space() -> None:
    """Amendment G2-a. Post hoc F1 decision space and the two REF fixed points."""
    d = J(DSPACE)
    rows = []
    for r in d["rows"]:
        lvl = r["level"]
        lam = LAM.get(lvl, 2.0)
        for cell in ("REF", "R3_SPAN", "R1_H60", "R1_H30"):
            c = r["cells"][cell]
            rows.append({"level": lvl, "cell": cell, "track": "F6",
                         "f1_pct": round(c["f1_pct"], 4), "n_off": c["n_off"],
                         "objective": round(c["generalized_cost"] + lam * 60 * c["unserved"], 2)})
        t = r["ref_f4_track"]
        rows.append({"level": lvl, "cell": "REF", "track": "F4",
                     "f1_pct": round(t["f1_pct"], 4), "n_off": t["n_off"],
                     "objective": round(t["objective"], 2)})

    fig, (axa, axb) = plt.subplots(1, 2, figsize=(7.4, 3.6),
                                   gridspec_kw={"width_ratios": [1, 1.25], "wspace": 0.32})
    base = [x for x in rows if x["level"] == "BASE"]
    ref = next(x for x in base if x["cell"] == "REF" and x["track"] == "F6")
    axa.grid(True, zorder=0)
    zero_line(axa, "y")
    place = {"REF_F4": (-0.10, 30.5), "REF": (-0.30, 8.0), "R3_SPAN": (0.30, 23.0),
             "R1_H60": (0.55, 14.5), "R1_H30": (0.62, 4.5)}
    for x in base:
        key = "REF_F4" if x["track"] == "F4" else x["cell"]
        lab, col, mk = CELL_STYLE[key]
        dobj = 100 * (x["objective"] - ref["objective"]) / ref["objective"]
        x["objective_vs_f6_ref_pct"] = round(dobj, 4)
        axa.scatter(dobj, x["f1_pct"], s=48, marker=mk, color=col, zorder=3,
                    edgecolor=SURFACE, linewidth=1.0)
        short = {"REF_F4": "REF (F4 track)", "REF": "REF (F6 track)"}.get(key, key)
        axa.annotate(f"{short}\n{pct(x['f1_pct'], 1, True)}, {x['n_off']} OFF",
                     (dobj, x["f1_pct"]), textcoords="data", xytext=place[key], ha="left",
                     va="center", fontsize=7.5, color=INK2,
                     arrowprops=None if key == "REF_F4" else
                     {"arrowstyle": "-", "color": MUTED, "lw": 0.6, "shrinkA": 1, "shrinkB": 4})
    axa.set_xlim(-0.35, 1.0)
    axa.set_ylim(-14, 38)
    axa.set_xlabel("Objective vs F6-track REF plan (%)")
    axa.set_ylabel("F1: unserved demand vs current plan (%)")
    axa.set_title("a  BASE (λ = 2)")

    axb.grid(True, zorder=0)
    zero_line(axb, "y")
    seen = set()
    for x in rows:
        key = "REF_F4" if x["track"] == "F4" else x["cell"]
        lab, col, mk = CELL_STYLE[key]
        axb.scatter(x["n_off"], x["f1_pct"], s=34, marker=mk, color=col, zorder=3,
                    edgecolor=SURFACE, linewidth=0.8, label=lab if key not in seen else None)
        seen.add(key)
    p = next(x for x in rows if x["level"] == "A5_LAM1" and x["cell"] == "REF")
    axb.annotate("λ = 1 (both tracks,\nsame plan)", (p["n_off"], p["f1_pct"]),
                 textcoords="offset points", xytext=(-8, -2), ha="right", fontsize=7.5,
                 color=INK2)
    axb.set_yscale("symlog", linthresh=10)
    axb.set_yticks([-10, -5, 0, 5, 10, 30, 100, 200])
    axb.set_yticklabels(["−10", "−5", "0", "5", "10", "30", "100", "200"])
    axb.set_ylim(-12, 260)
    axb.set_xlabel("Route-periods switched OFF")
    axb.set_ylabel("F1 (%; linear within ±10, log beyond)")
    axb.set_title("b  Seven re-optimized levels (A5, A6)")
    h, l = axb.get_legend_handles_labels()
    want = [CELL_STYLE[k][0] for k in ("REF", "REF_F4", "R3_SPAN", "R1_H60", "R1_H30")]
    hl = sorted(zip(h, l), key=lambda t: want.index(t[1]))
    fig.legend([t[0] for t in hl], [t[1] for t in hl], loc="lower center", ncol=2,
               bbox_to_anchor=(0.5, -0.17), fontsize=7.5)
    fig.suptitle("Experiment 7, post hoc: F1 depends on whether service may be switched off",
                 x=0.06, ha="left", y=1.02, fontsize=10, fontweight="bold", color=INK)
    save(fig, "fig7_exp7_f1_decision_space", rows)


# ================================================================ Figure 8
def fig8_route_vs_path() -> None:
    """G2. The same plans scored by the route-level and path-level evaluators."""
    m = [r for r in JL(MATRIX) if r.get("model") in ("R", "C")]
    R = sorted([r for r in m if r["model"] == "R"], key=lambda r: r["lambda"])
    Cm = sorted([r for r in m if r["model"] == "C"], key=lambda r: r["lambda"])
    t = [r for r in JL(EXP2_TREAT) if r.get("treatment") == "route_level"]
    rows = [{"source": "matrix.jsonl (pre-Model-B)", "model": r["model"], "lambda": r["lambda"],
             "route_level_own_unserved_pct": round(r["own_unserved_change_pct"], 4),
             "path_level_scored_unserved_pct": round(r["scored_unserved_change_pct"], 4)}
            for r in R + Cm]
    rows += [{"source": "exp2_treatments.jsonl (Model B)", "network": r["network"],
              "lambda": r["lambda"], "claimed_unserved": round(r["claimed_unserved"], 2),
              "modelB_unserved": round(r["modelB_unserved"], 2),
              "claim_gap_unserved_pct": round(r["claim_gap_unserved_pct"], 4)} for r in t]

    fig, (a, b) = plt.subplots(1, 2, figsize=(7.4, 3.6),
                               gridspec_kw={"width_ratios": [1.15, 1], "wspace": 0.32})
    a.grid(True, zorder=0)
    zero_line(a, "y")
    lx = [math.log2(r["lambda"]) for r in R]
    a.plot(lx, [r["own_unserved_change_pct"] for r in R], color=ORANGE, lw=1.4,
           marker="o", ms=5, label="route-level score (optimizer's own)")
    a.plot(lx, [r["scored_unserved_change_pct"] for r in R], color=BLUE, lw=1.4,
           marker="s", ms=5, label="path-level score, same plans")
    r4 = next(r for r in R if r["lambda"] == 4.0)
    x4 = math.log2(4.0)
    a.annotate("", xy=(x4, r4["own_unserved_change_pct"]),
               xytext=(x4, r4["scored_unserved_change_pct"]),
               arrowprops={"arrowstyle": "<->", "color": INK, "lw": 0.9})
    a.annotate(f"same plan at λ = 4:\n{pct(r4['own_unserved_change_pct'])} claimed vs\n"
               f"{pct(r4['scored_unserved_change_pct'])} path-level",
               (x4, (r4["own_unserved_change_pct"] + r4["scored_unserved_change_pct"]) / 2),
               textcoords="offset points", xytext=(-8, 0), ha="right", va="center",
               fontsize=7.5, color=INK)
    a.set_xticks(lx)
    a.set_xticklabels([f"{r['lambda']:g}" for r in R])
    a.set_xlabel("λ")
    a.set_ylabel("Unserved demand vs current plan (%)")
    a.set_ylim(-30, 75)
    a.legend(loc="upper right", fontsize=7)
    a.set_title("a  One seed, pre-Model-B evaluator")

    b.grid(True, zorder=0)
    lims = [0, max(max(r["modelB_unserved"] for r in t), max(r["claimed_unserved"] for r in t)) * 1.08]
    b.plot(lims, lims, color=MUTED, lw=0.8, ls="--", zorder=1)
    b.text(lims[1] * 0.62, lims[1] * 0.70, "claim = Model B", rotation=38, fontsize=7,
           color=INK2)
    for lam, mk in ((1.0, "o"), (2.0, "s"), (4.0, "^")):
        sub = [r for r in t if r["lambda"] == lam]
        b.scatter([r["modelB_unserved"] for r in sub], [r["claimed_unserved"] for r in sub],
                  s=26, marker=mk, color=ORANGE, edgecolor=SURFACE, linewidth=0.6,
                  label=f"λ = {lam:g}", zorder=3)
    gaps = sorted(r["claim_gap_unserved_pct"] for r in t)
    med = gaps[len(gaps) // 2]
    b.text(0.03, 0.97, f"{len(t)} route-level plans\n(13 networks × 3 λ)\nmedian claim gap "
           f"{pct(med, 1)}", transform=b.transAxes, fontsize=7.5, color=INK2, va="top")
    b.set_xlim(*lims)
    b.set_ylim(*lims)
    b.set_xlabel("Unserved trips, Model B (path-level)")
    b.set_ylabel("Unserved trips, route-level claim")
    b.legend(loc="lower right", fontsize=7)
    b.set_title("b  Exp 2 treatments, Model B")
    fig.suptitle("Route-level scoring overstates the gain: the same plans scored both ways",
                 x=0.06, ha="left", y=1.02, fontsize=10, fontweight="bold", color=INK)
    save(fig, "fig8_route_vs_path_scoring", rows)


GUIDELINE_ID = {
    "fig1_exp1_frontier": "G1", "fig2_exp1_change_map": "G7",
    "fig3_exp2_geometry_null": "G3", "fig4_exp5_resource_curve": "G4",
    "fig5_exp6_policy_frontiers": "G5", "fig6_exp7_robustness": "G6",
    "fig7_exp7_f1_decision_space": "G2-a (amendment)",
    "fig8_route_vs_path_scoring": "G2",
}


def check() -> int:
    """CI mode: regenerate every figure that needs no raw data into a temp dir
    and require its CSV to equal the committed CSV; verify the manifest's input
    hashes for every input present. Inputs that are external raw data (absent
    from a clean clone) are reported, not failed."""
    import filecmp
    import tempfile
    global OUT
    committed = OUT
    m = json.loads((committed / "FIGURES_MANIFEST.json").read_text())
    bad, external = [], []
    for p, h in m["inputs_sha256"].items():
        if not (ROOT / p).exists():
            (external if p.startswith("data/") else bad).append(p)
        elif sha(p) != h:
            bad.append(f"{p}: hash differs")
    with tempfile.TemporaryDirectory() as td:
        OUT = Path(td)
        for f in (fig1_frontier, fig3_geometry_null, fig4_resource_curve,
                  fig5_policy_frontiers, fig6_robustness, fig7_decision_space,
                  fig8_route_vs_path):
            f()
        for csvf in sorted(Path(td).glob("*.csv")):
            if not filecmp.cmp(csvf, committed / csvf.name, shallow=False):
                bad.append(f"{csvf.name}: regenerated CSV differs from committed")
        OUT = committed
    print(json.dumps({"figures_check": "FAIL" if bad else "OK", "problems": bad,
                      "external_inputs_unavailable": external}, indent=1))
    return 1 if bad else 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-map", action="store_true")
    ap.add_argument("--check", action="store_true",
                    help="verify committed figures without writing (CI)")
    args = ap.parse_args()
    sys.path.insert(0, str(ROOT / "src"))
    if args.check:
        return check()
    fig1_frontier()
    map_info = None if args.skip_map else fig2_change_map()
    fig3_geometry_null()
    fig4_resource_curve()
    fig5_policy_frontiers()
    fig6_robustness()
    fig7_decision_space()
    fig8_route_vs_path()
    prev = {}
    mf = OUT / "FIGURES_MANIFEST.json"
    if mf.exists():
        prev = json.loads(mf.read_text())
    manifest = {
        "generator": "scripts/make_report_figures.py",
        "guideline": "docs/process/RELEASE_AND_REPORTING_GUIDELINES.md §Figures",
        "figures": {n: GUIDELINE_ID[n] for n in GUIDELINE_ID},
        "change_map": map_info if map_info is not None else prev.get("change_map"),
        "inputs_sha256": {p: sha(p) for p in sorted(USED | set(prev.get("inputs_sha256", {})))
                          if (ROOT / p).exists()},
    }
    mf.write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"figures": len(GUIDELINE_ID), "change_map": manifest["change_map"]}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
