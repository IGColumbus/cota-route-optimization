#!/usr/bin/env python3
"""Experiment 7 firewall preflight on real records (no compute).

Checks that the per-level contracts admit what they must and refuse what they
must, using records already on disk:
  admit   EXP7_POLICY(BASE): Exp 6 closed N0 REF (imported) vs N0 R2_S10 BASE
          canary produced by exp7_cell.py
  admit   EXP7_STRUCTURE(BASE): Exp 6 closed N0 REF vs N3 REF (imported)
  admit   EXP7_F4(BASE): Exp 6 initial N0 REF vs N3 REF (greedy-only, F4 rule)
  refuse  EXP7_POLICY(BASE) given a record certified at level R_LAM1
          (receipt builder: level binding), and receipts built under two
          levels' contracts compared under one (the firewall itself)
  refuse  EXP7_POLICY(R_LAM1) given a BASE record
  refuse  an F6-track record offered as F4 evidence (receipt builder)
  refuse  F6 vs F4 receipts mixed in one comparison
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import exp7_contracts as K  # noqa: E402
import exp7_levels as L  # noqa: E402
from exp45_certify_cell import atomic_write_json, utc  # noqa: E402


def j(p):
    return json.loads((ROOT / p).read_text())


def main() -> int:
    from cota_opt.firewall import compare
    b = K.contracts_for(L.BASE)
    lam1 = L.from_file(ROOT / "outputs/exp7/preflight/reach_levels.json", "R_LAM1")
    l1 = K.contracts_for(lam1)
    s0 = j("outputs/exp6/closure/closure_state_N0.json")["best"]
    s3 = j("outputs/exp6/closure/closure_state_N3.json")["best"]
    n0ref = j(s0["REF"])
    n3ref = j(s3["REF"])
    canary = j("outputs/exp7/preflight/base_repro/N0_R2_S10.json")
    i0 = j("outputs/exp6/initial/N0_REF.json")
    i3 = j("outputs/exp6/initial/N3_REF.json")
    t1 = j("outputs/exp7/preflight/transfer/N0_REF_lvl_R_LAM1_anchor.json")
    g1 = j("outputs/exp7/preflight/transfer/N0_REF_lvl_R_LAM1_greedy.json")

    def cmp(a, ta, c, tb, bb, name):
        try:
            res = compare(K.receipt_for(a, c, ta), K.receipt_for(bb, c, tb), c)
        except ValueError as ex:
            return {"admitted": False, "refused_by": "receipt_builder",
                    "why": str(ex)[:300]}
        ok = res.__class__.__name__ == "ComparisonResult"
        return {"admitted": ok, **({"effect": res.effect,
                                    "effect_pct": res.effect_pct,
                                    "declared": list(res.declared_differences)}
                                   if ok else {"why": repr(res)[:400]})}

    rows = {
        "admit_policy_BASE_N0_REF_vs_R2_S10_canary":
            cmp(n0ref, "F6", b["EXP7_POLICY"], "F6", canary, ""),
        "admit_structure_BASE_REF_N0_vs_N3":
            cmp(n0ref, "F6", b["EXP7_STRUCTURE"], "F6", n3ref, ""),
        "admit_f4_BASE_REF_N0_vs_N3_initial":
            cmp(i0, "F4", b["EXP7_F4"], "F4", i3, ""),
        "admit_f4_R_LAM1_greedy_vs_transfer_same_network_is_not_a_structure_comparison":
            None,
        "refuse_policy_BASE_given_R_LAM1_record":
            cmp(n0ref, "F6", b["EXP7_POLICY"], "F6", t1, ""),
        "refuse_policy_R_LAM1_given_BASE_record":
            cmp(t1, "F6", l1["EXP7_POLICY"], "F6", n0ref, ""),
        "refuse_F6_record_used_as_F4":
            cmp(g1, "F4", l1["EXP7_F4"], "F4", t1, ""),
        "refuse_F6_vs_F4_mixed":
            cmp(i0, "F6", b["EXP7_F4"], "F4", i3, ""),
    }
    rows.pop("admit_f4_R_LAM1_greedy_vs_transfer_same_network_is_not_a_structure_comparison")
    # each receipt built under ITS OWN level's contract, then compared under
    # one of them: the firewall itself (not the builder) must refuse
    res = compare(K.receipt_for(n0ref, b["EXP7_POLICY"], "F6"),
                  K.receipt_for(t1, l1["EXP7_POLICY"], "F6"), b["EXP7_POLICY"])
    ok = res.__class__.__name__ == "ComparisonResult"
    rows["refuse_mixed_level_receipts_at_firewall"] = {
        "admitted": ok, "why": "" if ok else repr(res)[:400]}
    passed = all(v["admitted"] == k.startswith("admit") for k, v in rows.items())
    out = {"schema": "exp7_firewall_preflight/v1", "rows": rows,
           "passed": passed, "written_utc": utc()}
    atomic_write_json(ROOT / "outputs/exp7/preflight/FIREWALL_PREFLIGHT.json", out)
    print(json.dumps(out, indent=1)[:4000])
    return 0 if passed else 3


if __name__ == "__main__":
    raise SystemExit(main())
