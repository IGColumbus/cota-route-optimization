#!/usr/bin/env python3
"""Experiment 7 combined closure engine -- pure, side-effect-injectable.

One engine instance closes ONE group: a (network, track) pair. Within the group,
cells are (level, policy). The engine never solves anything itself. It calls
injected operations and records a receipt for every candidate transfer it
considers, including the ones it skips or refuses.

Procedure (frozen; see docs/EXPERIMENT7_AMENDMENT.md section 3)
---------------------------------------------------------------
A pass is two stages, always in this order:

  W  within-level policy closure. For each level in `levels` order, for each
     adjacent nesting edge (tighter, looser) in sorted order, the forward
     transfer tighter -> looser and then the reverse looser -> tighter. This is
     the Experiment 6 procedure, applied level by level.

  X  cross-level all-pairs. For each policy in `policies` order, for each
     target level in `levels` order, for each source level in `levels` order
     with source != target, the source level's CURRENT BEST plan for that
     policy is transferred directly to the target level. There is no chain:
     a plan never has to win at an intermediate level to reach another level.

Each transfer reads the source's current best at the moment it is considered
(Gauss-Seidel order), so an improvement found earlier in a pass is visible to
later transfers in the same pass.

For every candidate:
  * source empty (INFEASIBLE_UNDER_ENVELOPE)       -> SKIPPED_EMPTY_SOURCE
  * precheck(target, source) returns a reason       -> REFUSED_INFEASIBLE_UNDER_TARGET
    (policy constraints, representation, evaluator compatibility under the
    TARGET; the anchor is never repaired)
  * target empty but the source passes the precheck -> EMPTINESS_CONTRADICTED
    (blocking: a proven-empty cell received an admissible plan)
  * identical plan digest to the target's best      -> SKIPPED_IDENTICAL_PLAN
  * (target cell, source plan digest) already tried -> SKIPPED_ALREADY_ATTEMPTED
  * otherwise transfer(); a certifier refusal       -> REFUSED_BY_CERTIFIER
    and a certified result                          -> RAN (improved or not)

A result replaces the target's best only if it is lower by more than `eps`
(absolute objective units, Experiment 6: 1e-9). The group reaches a fixed
point after a pass in which neither stage improved any cell. If `ceiling`
passes complete and the last one still improved, the result is
EXP7_CLOSURE_CEILING_FAILURE, which blocks certification of the whole group.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

CERTIFIED = "CERTIFIED"
EMPTY = "INFEASIBLE_UNDER_ENVELOPE"

FIXED_POINT = "FIXED_POINT"
CEILING_FAILURE = "EXP7_CLOSURE_CEILING_FAILURE"
EMPTINESS_CONTRADICTED = "EMPTINESS_CONTRADICTED"


@dataclass
class Rec:
    """What the engine needs to know about a cell's current best."""
    status: str                      # CERTIFIED | INFEASIBLE_UNDER_ENVELOPE
    objective: float | None = None
    plan_digest: str | None = None
    ref: str = ""                    # record path / id, opaque to the engine


@dataclass
class Ops:
    # precheck(target_cell, source_rec) -> None if admissible, else a reason
    precheck: Callable[[tuple, Rec], str | None]
    # transfer(target_cell, source_rec, label) -> Rec (status CERTIFIED or
    # anything else = refused by certifier, with .ref naming the evidence)
    transfer: Callable[[tuple, Rec, str], Rec]
    receipt: Callable[[dict], None] = lambda r: None
    save: Callable[[dict], None] = lambda s: None


@dataclass
class Group:
    levels: list[str]
    policies: list[str]
    edges: list[tuple[str, str]] = field(default_factory=list)  # (tighter, looser)
    within: bool = True             # False for the F4 (REF-only) track

    def cells(self):
        return [(lv, p) for lv in self.levels for p in self.policies]


def _key(c):
    return f"{c[0]}|{c[1]}"


def run(group: Group, best: dict, ops: Ops, *, ceiling: int, eps: float = 1e-9,
        state: dict | None = None) -> dict:
    """Close `group` starting from `best` {(level, policy): Rec}.

    `state` resumes a previous run (the dict this function saves); pass None
    to start fresh. Returns the final state; state["status"] is FIXED_POINT,
    EXP7_CLOSURE_CEILING_FAILURE or EMPTINESS_CONTRADICTED.
    """
    for c in group.cells():
        if c not in best:
            raise ValueError(f"no initial record for {c}; closure refuses an "
                             f"incomplete upstream stage")
    st = state or {"passes_completed": 0, "status": None, "tried": [],
                   "found_in_pass": {_key(c): 0 for c in group.cells()},
                   "improvements": []}
    tried = {tuple(t) for t in st["tried"]}

    def save():
        st["best"] = {_key(c): {"status": best[c].status,
                                "objective": best[c].objective,
                                "plan_digest": best[c].plan_digest,
                                "ref": best[c].ref} for c in group.cells()}
        ops.save(st)
    edges = sorted(tuple(e) for e in group.edges) if group.within else []
    blocking: list[dict] = []

    def consider(stage, p, src, tgt, label):
        s, t = best[src], best[tgt]
        r = {"pass": p, "stage": stage, "source_cell": list(src),
             "target_cell": list(tgt), "label": label, "source_ref": s.ref,
             "target_ref_before": t.ref}
        if s.status != CERTIFIED:
            r["action"] = "SKIPPED_EMPTY_SOURCE"
            ops.receipt(r)
            return False
        r.update(source_plan_digest=s.plan_digest)
        why = ops.precheck(tgt, s)
        if why is not None:
            r.update(action="REFUSED_INFEASIBLE_UNDER_TARGET", reason=why)
            ops.receipt(r)
            return False
        if t.status != CERTIFIED:
            r.update(action=EMPTINESS_CONTRADICTED,
                     reason="target proven empty, source admissible under "
                            "target precheck")
            ops.receipt(r)
            blocking.append(r)
            return False
        before = float(t.objective)
        r["objective_before"] = repr(before)
        if s.plan_digest == t.plan_digest:
            r["action"] = "SKIPPED_IDENTICAL_PLAN"
            ops.receipt(r)
            return False
        k = (_key(tgt), s.plan_digest)
        if k in tried:
            r["action"] = "SKIPPED_ALREADY_ATTEMPTED"
            ops.receipt(r)
            return False
        res = ops.transfer(tgt, s, label)
        tried.add(k)
        st["tried"] = sorted([list(x) for x in tried])
        r["result_ref"] = res.ref
        if res.status != CERTIFIED:
            r.update(action="REFUSED_BY_CERTIFIER", reason=res.status)
            ops.receipt(r)
            save()
            return False
        after = float(res.objective)
        imp = after < before - eps
        r.update(action="RAN", objective_after=repr(after),
                 returned_plan_digest=res.plan_digest, improved=imp)
        if imp:
            best[tgt] = res
            st["found_in_pass"][_key(tgt)] = p
            st["improvements"].append({"pass": p, "stage": stage,
                                       "cell": list(tgt), "from": list(src),
                                       "before": repr(before),
                                       "after": repr(after)})
        ops.receipt(r)
        save()
        return imp

    def schedule(p):
        """The frozen candidate order of one pass (cells, not plans)."""
        seq = []
        # stage W: within-level policy closure (Experiment 6 order)
        for lv in group.levels:
            for (a, b) in edges:
                for src, tgt, d in (((lv, a), (lv, b), "forward"),
                                    ((lv, b), (lv, a), "reverse")):
                    seq.append(("W", src, tgt,
                                f"pass {p} W {lv} {d}: {src[1]} -> {tgt[1]}"))
        # stage X: cross-level all-pairs, same policy
        for pol in group.policies:
            for tl in group.levels:
                for sl in group.levels:
                    if sl != tl:
                        seq.append(("X", (sl, pol), (tl, pol),
                                    f"pass {p} X {pol}: {sl} -> {tl}"))
        return seq

    # A resumed run continues the interrupted pass at its cursor, so its
    # receipts, pass count and ceiling behaviour equal an uninterrupted run's.
    st.setdefault("cursor", 0)
    st.setdefault("pass_improved", False)
    st.setdefault("blocking", [])
    blocking.extend(st["blocking"])
    p = st["passes_completed"]
    while st["status"] is None:
        if st["cursor"] == 0:
            if p >= ceiling:
                st["status"] = CEILING_FAILURE
                break
        seq = schedule(p + 1)
        for i in range(st["cursor"], len(seq)):
            stage, src, tgt, label = seq[i]
            nb = len(blocking)
            if consider(stage, p + 1, src, tgt, f"{label} [#{i}]"):
                st["pass_improved"] = True
            if len(blocking) > nb:
                st["blocking"] = blocking
            st["cursor"] = i + 1
            save()
        p += 1
        st["passes_completed"] = p
        st["cursor"] = 0
        improved, st["pass_improved"] = st["pass_improved"], False
        if blocking:
            st["status"] = EMPTINESS_CONTRADICTED
        elif not improved:
            st["status"] = FIXED_POINT
        save()
    save()
    return st


def best_from_state(st: dict) -> dict:
    """Rebuild the {(level, policy): Rec} map a resumed run starts from."""
    return {tuple(k.split("|", 1)): Rec(**v) for k, v in st["best"].items()}


def monotonicity(group: Group, best: dict, strict_pairs, *, eps: float = 1e-9):
    """Hard post-closure check within each level, over the STRICT nesting
    order (tighter, looser): obj(tighter) >= obj(looser) - eps. An empty
    tighter cell is consistent with anything; an empty looser cell with a
    feasible tighter cell is a violation (Exp 6 Amendment 1)."""
    out = []
    for lv in group.levels:
        for (t, l) in strict_pairs:
            T, L = best[(lv, t)], best[(lv, l)]
            if T.status != CERTIFIED:
                ok, why = True, "tighter empty"
            elif L.status != CERTIFIED:
                ok, why = False, "looser empty, tighter feasible"
            else:
                ok = T.objective >= L.objective - eps
                why = "" if ok else f"{T.objective!r} < {L.objective!r}"
            out.append({"level": lv, "tighter": t, "looser": l, "ok": ok,
                        "why": why})
    return out
