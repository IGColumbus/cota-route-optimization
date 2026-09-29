#!/usr/bin/env python3
"""Read-only cross-experiment firewall check: Exp 4A N3 vs Exp 5 N0 J100.

Builds firewall receipts for the two STORED records with the repository's own
machinery (scripts/exp45_contracts.receipt_for + cota_opt.firewall.compare) and
judges them under every existing contract that allows only network differences
(EXP4A_MATCHED, EXP5_STRUCTURE). Writes prep/n3_vs_n0_crossexp_check.json.

It re-scores nothing, touches no production artifact and runs no optimizer.
Control = N0 (Exp 5, J100 cell). Treatment = N3 (Exp 4A matched record).
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from exp45_contracts import CONTRACTS, receipt_for  # noqa: E402
from cota_opt.firewall import admit, compare  # noqa: E402
from cota_opt.firewall.observation import Inadmissible  # noqa: E402

N3 = ROOT / "outputs/exp4_addendum/N3.json"
N0 = ROOT / "outputs/exp5/cells/N0_J100.json"
OUT = ROOT / "prep/n3_vs_n0_crossexp_check.json"


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def facts(r: dict) -> dict:
    """Every field the question asks about, read from the record."""
    s, res, pv, ex = r["search"], r["resource"], r["provenance"], r["execution"]
    return {
        "experiment": r["experiment"], "role": r["role"], "cell_id": r["cell_id"],
        "record_contract_digest": r["contract_digest"],
        "state_key": r["identity"]["state_key"],
        "state_digest": r["identity"]["state_digest"],
        "construction": r["identity"]["construction"],
        "evaluator_used": ex["evaluator_used"],
        "evaluator_source": ex["evaluator_source"],
        "lam": s["lam"], "seed": s["seed"], "n_keys": s["n_keys"],
        "k_rungs": s["k_rungs"], "max_rounds": s["max_rounds"],
        "allow_off": s["allow_off"], "waiting_model": s["waiting_model"],
        "start": s["start"], "certification_digest": s["certification_digest"],
        "envelope_exact_fingerprint": res["enforced_exact_fingerprint"],
        "envelope_rounded_digest": res["enforced_rounded_envelope_digest"],
        "enforced_matches_requested_bit_exact":
            res["enforced_matches_requested_bit_exact"],
        "feasible_under_enforced_caps": res["feasible_under_enforced_caps"],
        "pathset_digest": ex.get("pathset_digest"),
        "start_audit_winning_start": ex["start_audit"].get("winning_start"),
        "start_audit_forced_greedy_fallback":
            ex["start_audit"].get("forced_greedy_fallback"),
        "start_audit_initial_rejection": ex["start_audit"].get("initial_rejection"),
        "config_digest": pv["config_digest"], "data_digest": pv["data_digest"],
        "code_version": pv["code_version"],
        "src_cota_opt_content_digest": pv["src_cota_opt_content_digest"],
        "repo_revision": pv["repo_revision"],
        "runner_sha256": pv["runner_sha256"],
        "objective_EXACT": r["outcome"]["objective_EXACT"],
        "plan_digest": r["outcome"]["plan_digest"],
        "rounds": r["outcome"]["rounds"], "converged": r["outcome"]["converged"],
    }


def main() -> int:
    n3, n0 = json.loads(N3.read_text()), json.loads(N0.read_text())
    f3, f0 = facts(n3), facts(n0)
    field_diff = {k: {"N0_exp5": f0[k], "N3_exp4a": f3[k]}
                  for k in f0 if f0[k] != f3[k]}
    judgements = {}
    for name in ("EXP4A_MATCHED", "EXP5_STRUCTURE"):
        c = CONTRACTS[name]
        r0, r3 = receipt_for(n0, c), receipt_for(n3, c)
        a0, a3 = admit(r0, c), admit(r3, c)
        res = compare(r0, r3, c)
        j = {"contract_digest": c.digest,
             "admit_N0": "ADMITTED" if not isinstance(a0, Inadmissible)
             else list(a0.reasons),
             "admit_N3": "ADMITTED" if not isinstance(a3, Inadmissible)
             else list(a3.reasons),
             "admissible": bool(res)}
        if res:
            d = res.as_dict()
            j.update({"comparison_id": d["comparison_id"],
                      "effect_N3_minus_N0": d["effect"],
                      "effect_pct_of_N0": d["effect_pct"],
                      "declared_differences": d["declared_differences"],
                      "components_treatment_N3_control_N0": d["components"]})
        else:
            j.update({"refusal": str(res)})
        judgements[name] = j
    obj3, obj0 = float(f3["objective_EXACT"]), float(f0["objective_EXACT"])
    out = {
        "what": "cross-experiment consistency check, N3 (Exp 4A) vs N0 (Exp 5 J100)",
        "generated_by": "prep/n3_vs_n0_crossexp_check.py (read-only)",
        "inputs": {str(N3.relative_to(ROOT)): sha(N3),
                   str(N0.relative_to(ROOT)): sha(N0)},
        "raw_objectives": {"N3": obj3, "N0": obj0,
                           "raw_difference_N3_minus_N0": obj3 - obj0,
                           "raw_pct_of_N0": 100.0 * (obj3 - obj0) / obj0,
                           "note": "raw numbers for orientation only; the "
                                   "reportable figure is the firewall "
                                   "comparison's effect, if admitted"},
        "record_facts": {"N0_exp5_J100": f0, "N3_exp4a": f3},
        "fields_that_differ": field_diff,
        "firewall": judgements,
        "exp3_certified_reference": {
            "leader": "add_stop-010#22c4c35ac5b2", "effect_pct": -0.18657,
            "note": "Exp 3's certified effect is under the Exp 3 contract "
                    "(Stage B, 5 paired seeds, 20 restarts), a different "
                    "instrument and envelope; it is quoted for orientation, "
                    "not firewall-compared here"},
    }
    OUT.write_text(json.dumps(out, indent=2) + "\n")
    for name, j in judgements.items():
        print(name, j["admissible"], j.get("effect_pct_of_N0"),
              j.get("declared_differences"), j.get("refusal", "")[:400])
    print("fields differing:", sorted(field_diff))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
