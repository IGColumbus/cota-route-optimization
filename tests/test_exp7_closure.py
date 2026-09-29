"""Experiment 7 closure engine and classification -- mock-based unit tests.

The toy world: a plan is a string; each (level, policy) cell has a table of
objectives for the plans admissible there. A "certify from anchor" returns the
anchor's own objective under the target, or a scripted better neighbour.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import exp7_classify as K  # noqa: E402
import exp7_closure as E  # noqa: E402


class World:
    def __init__(self, obj, neighbour=None, forbid=None):
        self.obj = obj                        # {(level, policy): {plan: value}}
        self.neighbour = neighbour or {}      # {(cell, plan): better_plan}
        self.forbid = forbid or {}            # {(cell): set(plans)} precheck
        self.calls, self.receipts = [], []

    def rec(self, cell, plan):
        return E.Rec(E.CERTIFIED, self.obj[cell][plan], plan, f"{cell}:{plan}")

    def ops(self):
        def precheck(tgt, src):
            if src.plan_digest in self.forbid.get(tgt, set()) or \
                    src.plan_digest not in self.obj.get(tgt, {}):
                return f"{src.plan_digest} violates {tgt}"
            return None

        def transfer(tgt, src, label):
            self.calls.append((tgt, src.plan_digest))
            p = self.neighbour.get((tgt, src.plan_digest), src.plan_digest)
            return self.rec(tgt, p)
        return E.Ops(precheck=precheck, transfer=transfer,
                     receipt=self.receipts.append)


def test_cross_level_all_pairs_reaches_level_without_winning_in_between():
    # Plan P is best at A, WORSE than the incumbent at B, best at C.
    # An adjacent chain A -> B -> C would lose P at B; all-pairs must not.
    L = ["A", "B", "C"]
    obj = {("A", "REF"): {"a": 10, "P": 9, "b": 20, "c": 20},
           ("B", "REF"): {"a": 20, "P": 12, "b": 10, "c": 20},
           ("C", "REF"): {"a": 20, "P": 5, "b": 20, "c": 10}}
    w = World(obj)
    best = {("A", "REF"): w.rec(("A", "REF"), "P"),
            ("B", "REF"): w.rec(("B", "REF"), "b"),
            ("C", "REF"): w.rec(("C", "REF"), "c")}
    g = E.Group(levels=L, policies=["REF"], within=False)
    st = E.run(g, best, w.ops(), ceiling=8)
    assert st["status"] == E.FIXED_POINT
    assert best[("C", "REF")].plan_digest == "P"
    assert best[("B", "REF")].plan_digest == "b"       # rejected at B
    imp = [i for i in st["improvements"] if i["cell"] == ["C", "REF"]]
    assert imp[0]["from"] == ["A", "REF"] and imp[0]["stage"] == "X"


def test_combined_closure_needs_both_stages_and_repeats_until_neither_improves():
    # Q is found only at (B, T). It helps (A, T) (cross-level), and from
    # there helps (A, L) (within-level, tighter -> looser). Then (A, L)'s new
    # plan helps (B, L) cross-level.
    L = ["A", "B"]
    obj = {("A", "T"): {"t": 10, "Q": 8},
           ("A", "L"): {"t": 9, "l": 9, "Q": 7},
           ("B", "T"): {"t": 10, "Q": 6},
           ("B", "L"): {"t": 10, "l": 9, "Q": 5, "Z": 4}}
    w = World(obj, neighbour={(("B", "L"), "Q"): "Z"})
    best = {("A", "T"): w.rec(("A", "T"), "t"), ("A", "L"): w.rec(("A", "L"), "l"),
            ("B", "T"): w.rec(("B", "T"), "Q"), ("B", "L"): w.rec(("B", "L"), "l")}
    g = E.Group(levels=L, policies=["T", "L"], edges=[("T", "L")])
    st = E.run(g, best, w.ops(), ceiling=8)
    assert st["status"] == E.FIXED_POINT
    assert best[("A", "T")].plan_digest == "Q"
    assert best[("A", "L")].plan_digest == "Q"
    assert best[("B", "L")].plan_digest == "Z"
    stages = {(i["stage"], tuple(i["cell"])) for i in st["improvements"]}
    assert ("X", ("A", "T")) in stages and ("W", ("B", "L")) in stages
    assert ("W", ("A", "L")) in stages
    # final pass improved nothing
    assert max(i["pass"] for i in st["improvements"]) < st["passes_completed"]
    # Z (found at B,L) is not admissible at A,L and must be refused, not repaired
    assert any(r["action"] == "REFUSED_INFEASIBLE_UNDER_TARGET"
               and r["source_plan_digest"] == "Z" for r in w.receipts)


def test_target_feasibility_refusal_never_calls_certifier():
    obj = {("A", "REF"): {"x": 5}, ("B", "REF"): {"y": 7, "x": 1}}
    w = World(obj, forbid={("B", "REF"): {"x"}})
    best = {("A", "REF"): w.rec(("A", "REF"), "x"),
            ("B", "REF"): w.rec(("B", "REF"), "y")}
    st = E.run(E.Group(["A", "B"], ["REF"], within=False), best, w.ops(),
               ceiling=8)
    assert st["status"] == E.FIXED_POINT
    assert best[("B", "REF")].plan_digest == "y"
    assert w.calls == []
    r = [r for r in w.receipts if r["target_cell"] == ["B", "REF"]][0]
    assert r["action"] == "REFUSED_INFEASIBLE_UNDER_TARGET" and "x" in r["reason"]


def test_certifier_refusal_is_receipted_and_not_repaired():
    obj = {("A", "REF"): {"x": 5}, ("B", "REF"): {"y": 7, "x": 1}}
    w = World(obj)
    o = w.ops()
    o.transfer = lambda t, s, lab: E.Rec("REFUSED:AnchorRefused", ref="trace")
    best = {("A", "REF"): w.rec(("A", "REF"), "x"),
            ("B", "REF"): w.rec(("B", "REF"), "y")}
    st = E.run(E.Group(["A", "B"], ["REF"], within=False), best, o, ceiling=8)
    assert st["status"] == E.FIXED_POINT and best[("B", "REF")].plan_digest == "y"
    assert any(r["action"] == "REFUSED_BY_CERTIFIER" for r in w.receipts)


def test_ceiling_without_closure_blocks():
    counter = {"n": 0}
    obj = {("A", "REF"): {"p0": 100}, ("B", "REF"): {"q0": 100}}

    def transfer(tgt, src, label):
        counter["n"] += 1
        return E.Rec(E.CERTIFIED, src.objective - 1, f"p{counter['n']}", "")
    o = E.Ops(precheck=lambda t, s: None, transfer=transfer)
    best = {("A", "REF"): E.Rec(E.CERTIFIED, 100, "p0"),
            ("B", "REF"): E.Rec(E.CERTIFIED, 100, "q0")}
    st = E.run(E.Group(["A", "B"], ["REF"], within=False), best, o, ceiling=3)
    assert st["status"] == E.CEILING_FAILURE
    assert st["passes_completed"] == 3


def test_memo_skips_repeated_anchor_in_later_pass():
    # C improves in pass 1, forcing pass 2, where x -> B is already tried.
    obj = {("A", "REF"): {"x": 5}, ("B", "REF"): {"y": 7, "x": 8},
           ("C", "REF"): {"c": 10, "x": 3}}
    w = World(obj)
    best = {("A", "REF"): w.rec(("A", "REF"), "x"),
            ("B", "REF"): w.rec(("B", "REF"), "y"),
            ("C", "REF"): w.rec(("C", "REF"), "c")}
    st = E.run(E.Group(["A", "B", "C"], ["REF"], within=False), best, w.ops(),
               ceiling=8)
    assert st["status"] == E.FIXED_POINT and st["passes_completed"] == 2
    assert w.calls.count((("B", "REF"), "x")) == 1
    assert any(r["action"] == "SKIPPED_ALREADY_ATTEMPTED" and r["pass"] == 2
               for r in w.receipts)


def test_empty_cells():
    obj = {("A", "T"): {"t": 10}, ("A", "L"): {"t": 9, "l": 8}}
    w = World(obj)
    best = {("A", "T"): E.Rec(E.EMPTY), ("A", "L"): w.rec(("A", "L"), "l")}
    # L's plan "l" is not admissible under T -> refused, T stays empty
    st = E.run(E.Group(["A"], ["T", "L"], edges=[("T", "L")]), best, w.ops(),
               ceiling=8)
    assert st["status"] == E.FIXED_POINT
    acts = {r["action"] for r in w.receipts}
    assert "SKIPPED_EMPTY_SOURCE" in acts
    assert "REFUSED_INFEASIBLE_UNDER_TARGET" in acts
    # an admissible plan reaching a "proven empty" cell contradicts the proof
    w2 = World({("A", "T"): {"l": 10}, ("A", "L"): {"l": 8}})
    best2 = {("A", "T"): E.Rec(E.EMPTY), ("A", "L"): w2.rec(("A", "L"), "l")}
    st2 = E.run(E.Group(["A"], ["T", "L"], edges=[("T", "L")]), best2,
                w2.ops(), ceiling=8)
    assert st2["status"] == E.EMPTINESS_CONTRADICTED
    # monotonicity: empty tighter ok; empty looser with feasible tighter not
    g = E.Group(["A"], ["T", "L"], edges=[("T", "L")])
    m = E.monotonicity(g, best, [("T", "L")])
    assert m[0]["ok"]
    bad = {("A", "T"): E.Rec(E.CERTIFIED, 5, "t"), ("A", "L"): E.Rec(E.EMPTY)}
    assert not E.monotonicity(g, bad, [("T", "L")])[0]["ok"]
    worse = {("A", "T"): E.Rec(E.CERTIFIED, 5, "t"),
             ("A", "L"): E.Rec(E.CERTIFIED, 6, "l")}
    assert not E.monotonicity(g, worse, [("T", "L")])[0]["ok"]


def test_missing_initial_refused():
    with pytest.raises(ValueError):
        E.run(E.Group(["A"], ["REF"]), {}, E.Ops(lambda *a: None,
                                                  lambda *a: None), ceiling=8)


# ---------------- classification ----------------
REF = {"status": "CERTIFIED", "objective": 1000.0, "plan_digest": "r"}


def test_zero_price_classes():
    same = {"status": "CERTIFIED", "objective": 1000.0, "plan_digest": "r"}
    assert K.classify_price(REF, same, ref_plan_admissible=True)["class"] == K.ZERO
    other = {"status": "CERTIFIED", "objective": 1000.0 + 5e-10, "plan_digest": "o"}
    assert K.classify_price(REF, other, ref_plan_admissible=True)["class"] \
        == K.ZERO_DISTINCT
    # zero objective gap but REF plan not admissible under the cell -> not a
    # supported zero
    assert K.classify_price(REF, other, ref_plan_admissible=False)["class"] \
        == K.ZERO_UNSUPPORTED
    assert K.classify_price(REF, other, ref_plan_admissible=None)["class"] \
        == K.ZERO_UNSUPPORTED
    assert K.classify_price(REF, same, ref_plan_admissible=False)["class"] \
        == K.ZERO_UNSUPPORTED
    pos = {"status": "CERTIFIED", "objective": 1001.0, "plan_digest": "p"}
    c = K.classify_price(REF, pos, ref_plan_admissible=False)
    assert c["class"] == K.POSITIVE and abs(c["price"] - 1e-3) < 1e-15
    neg = {"status": "CERTIFIED", "objective": 999.0, "plan_digest": "n"}
    assert K.classify_price(REF, neg, ref_plan_admissible=True)["class"] \
        == K.NEGATIVE


def test_infeasible_cell_has_no_finite_price():
    c = K.classify_price(REF, {"status": "INFEASIBLE_UNDER_ENVELOPE"},
                         ref_plan_admissible=False)
    assert c == {"class": K.INFEASIBLE, "price": None, "delta": None}
    assert K.transition({"status": "CERTIFIED"},
                        {"status": "INFEASIBLE_UNDER_ENVELOPE"}) \
        == "FEASIBLE_TO_INFEASIBLE"
    assert K.transition({"status": "INFEASIBLE_UNDER_ENVELOPE"},
                        {"status": "CERTIFIED"}) == "INFEASIBLE_TO_FEASIBLE"
    r = K.rank({"a": 1.0, "b": None})
    assert r["b"]["rank"] is None and r["a"]["rank"] == 1


def test_ties_are_anchored_and_share_rank():
    r = K.rank({"a": 0.0, "b": 5e-10, "c": 9e-10, "d": 1.6e-9, "e": 1.0},
               tau=1e-9)
    assert r["a"]["rank"] == r["b"]["rank"] == r["c"]["rank"] == 1
    assert r["d"]["rank"] == 4          # 1.6e-9 is > tau from anchor a: no chain
    assert r["e"]["rank"] == 5
    r2 = K.rank({"a": 0.0, "b": 0.5, "c": 0.7}, digests={"a": "x", "b": "y",
                                                           "c": "y"})
    assert r2["b"]["rank"] == r2["c"]["rank"] == 2


def test_sign_flips_are_findings():
    assert K.sign_flip(-6726.0, 12.0) == "SIGN_FLIP"
    assert K.sign_flip(-6726.0, 0.0) == "TO_TIE"
    assert K.sign_flip(0.0, 3.0) == "FROM_TIE"
    assert K.sign_flip(-1.0, -2.0) is None
    d = K.decompose(initial_level=10.0, closed_level=9.0, closed_base=8.5)
    assert d == {"basin_correction": -1.0, "sensitivity_effect": 0.5}


def test_interrupted_run_resumes_to_same_fixed_point():
    obj = {("A", "T"): {"t": 10, "Q": 8},
           ("A", "L"): {"t": 9, "l": 9, "Q": 7},
           ("B", "T"): {"t": 10, "Q": 6},
           ("B", "L"): {"t": 10, "l": 9, "Q": 5, "Z": 4}}
    g = E.Group(levels=["A", "B"], policies=["T", "L"], edges=[("T", "L")])

    def fresh(w):
        return {("A", "T"): w.rec(("A", "T"), "t"),
                ("A", "L"): w.rec(("A", "L"), "l"),
                ("B", "T"): w.rec(("B", "T"), "Q"),
                ("B", "L"): w.rec(("B", "L"), "l")}
    w0 = World(obj, neighbour={(("B", "L"), "Q"): "Z"})
    ref = E.run(g, fresh(w0), w0.ops(), ceiling=8)

    w1 = World(obj, neighbour={(("B", "L"), "Q"): "Z"})
    saved = {}
    o = w1.ops()
    o.save = lambda s: saved.update(__import__("copy").deepcopy(s))
    real = o.transfer

    def boom(t, s, lab):
        if len(w1.calls) >= 2:
            raise KeyboardInterrupt
        return real(t, s, lab)
    o.transfer = boom
    with pytest.raises(KeyboardInterrupt):
        E.run(g, fresh(w1), o, ceiling=8)
    o.transfer = real
    st = E.run(g, E.best_from_state(saved), o, ceiling=8,
               state=__import__("copy").deepcopy(saved))
    assert st["status"] == ref["status"] == E.FIXED_POINT
    assert st["best"] == ref["best"]
    assert st["passes_completed"] == ref["passes_completed"]
    assert st["improvements"] == ref["improvements"]
    assert st["tried"] == ref["tried"]
