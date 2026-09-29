#!/usr/bin/env python3
"""Experiment 7 comparison and classification rules -- pure functions.

Everything here operates on CLOSED (post-closure) cell results. Numerical
tolerances are absolute, in objective units, and equal to the closure's own
improvement threshold, so "equal" means exactly what the closure could not
distinguish. Magnitude bands (e.g. small/moderate/large) are NOT defined here:
they come from the as-issued protocol and are applied by exp7_analyze.

Definitions (docs/EXPERIMENT7_AMENDMENT.md section 7)
-----------------------------------------------------
price(cell)            (obj(cell) - obj(REF)) / obj(REF), both closed, same
                       level, same network. None for an empty cell.
ZERO                   final plan digest identical to the closed REF's.
ZERO_DISTINCT_PLAN     different plan, |obj(cell) - obj(REF)| <= TAU_ABS.
POSITIVE               obj(cell) - obj(REF) > TAU_ABS.
NEGATIVE               obj(cell) - obj(REF) < -TAU_ABS: impossible after a
                       correct closure (REF is looser than every cell and must
                       absorb better incumbents) -> EXP7_REFERENCE_CLOSURE_FAILURE.
INFEASIBLE             proven empty (Amendment 1 procedure, re-proved at this
                       level). No finite price.
ZERO_NOT_ESTABLISHED   the REF plan is policy-infeasible under the cell, yet
                       the cell's closed objective equals REF's within TAU_ABS
                       -- a zero price that the target-feasibility check does
                       not support; reported, never presented as "free".
"""
from __future__ import annotations

TAU_ABS = 1e-9

ZERO = "ZERO"
ZERO_DISTINCT = "ZERO_DISTINCT_PLAN"
POSITIVE = "POSITIVE"
NEGATIVE = "EXP7_REFERENCE_CLOSURE_FAILURE"
INFEASIBLE = "INFEASIBLE_UNDER_ENVELOPE"
ZERO_UNSUPPORTED = "ZERO_NOT_ESTABLISHED"


def classify_price(ref: dict, cell: dict, *, ref_plan_admissible: bool | None,
                   tau: float = TAU_ABS) -> dict:
    """ref/cell: {"status", "objective", "plan_digest"}.

    `ref_plan_admissible` is the target-feasibility check of the closed REF
    plan under this cell's compiled policy AT THIS LEVEL (None if not run).
    A zero is only reported as ZERO / ZERO_DISTINCT_PLAN when that check
    passed or the cell's own plan is the REF plan; baseline (BASE-level)
    non-binding status is never inherited.
    """
    if cell["status"] != "CERTIFIED":
        return {"class": INFEASIBLE, "price": None, "delta": None}
    if ref["status"] != "CERTIFIED":
        raise ValueError("REF empty: every cell would be empty")
    d = float(cell["objective"]) - float(ref["objective"])
    price = d / float(ref["objective"])
    same = cell["plan_digest"] == ref["plan_digest"]
    if d < -tau:
        c = NEGATIVE
    elif same:
        c = ZERO
    elif abs(d) <= tau:
        c = ZERO_DISTINCT if ref_plan_admissible else ZERO_UNSUPPORTED
    else:
        c = POSITIVE
    if c == ZERO and ref_plan_admissible is False:
        c = ZERO_UNSUPPORTED        # contradiction: same plan, yet inadmissible
    return {"class": c, "price": price, "delta": d}


def rank(values: dict, *, digests: dict | None = None, tau: float = TAU_ABS):
    """Competition ranking ("1, 2, 2, 4") with ties.

    Items sorted ascending (lower = better / cheaper). A tie group starts at
    its lowest member and absorbs every following item within `tau` of THAT
    member (anchored, so ties do not chain), or with an identical plan digest
    to any member. None values (empty cells) are unranked.
    """
    items = sorted((v, k) for k, v in values.items() if v is not None)
    out, i, pos = {}, 0, 1
    while i < len(items):
        v0, k0 = items[i]
        grp = [k0]
        dg = {digests.get(k0)} if digests else set()
        j = i + 1
        while j < len(items) and (items[j][0] - v0 <= tau or
                                  (digests and digests.get(items[j][1]) in dg)):
            grp.append(items[j][1])
            if digests:
                dg.add(digests.get(items[j][1]))
            j += 1
        for k in grp:
            out[k] = {"rank": pos, "tied_with": sorted(set(grp) - {k})}
        pos += len(grp)
        i = j
    for k, v in values.items():
        if v is None:
            out[k] = {"rank": None, "tied_with": []}
    return out


def transition(base: dict, lv: dict) -> str | None:
    """Feasibility transition of one cell between BASE and a level."""
    a, b = base["status"] == "CERTIFIED", lv["status"] == "CERTIFIED"
    if a and not b:
        return "FEASIBLE_TO_INFEASIBLE"
    if b and not a:
        return "INFEASIBLE_TO_FEASIBLE"
    return None


def sign(x: float | None, tau: float) -> int | None:
    if x is None:
        return None
    return 0 if abs(x) <= tau else (1 if x > 0 else -1)


def sign_flip(base_delta, lv_delta, *, tau: float = TAU_ABS) -> str | None:
    """A sign change of a difference (e.g. N3 - N0 at matched policy, or a
    price) between BASE and a level. A FINDING, never a failure. Moves into
    or out of the tie band are reported separately from strict flips."""
    a, b = sign(base_delta, tau), sign(lv_delta, tau)
    if a is None or b is None or a == b:
        return None
    if a * b == -1:
        return "SIGN_FLIP"
    return "TO_TIE" if b == 0 else "FROM_TIE"


def decompose(initial_level, closed_level, closed_base) -> dict:
    """Keep the basin correction apart from the sensitivity effect.

    basin_correction   closed(level) - initial(level): what closure found at
                       this level (search outcome, not a model effect)
    sensitivity_effect closed(level) - closed(BASE): the level's effect on the
                       closed quantity (only meaningful for quantities
                       comparable across levels, e.g. prices, not raw
                       objectives under different objective definitions)
    """
    return {"basin_correction": None if closed_level is None or initial_level
            is None else closed_level - initial_level,
            "sensitivity_effect": None if closed_level is None or closed_base
            is None else closed_level - closed_base}
