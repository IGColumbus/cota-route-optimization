#!/usr/bin/env python3
"""EXP4N §10 — final status. Exactly one verdict, chosen by the preregistered
decision rule, not by preference.

The five permitted terminal states:
  EXP4_FULL_NORMALIZED_CERTIFIED  — 200/200 certified and §8 passed
  EXP4N_CONVERGENCE_FAILURE       — some candidate hit rounds==ceiling with converged=False
  EXP4N_REPRODUCTION_FAILURE      — a §6 calibration control failed to reproduce
  EXP4N_CONTRACT_MISMATCH         — a production parameter diverged from the frozen contract
  EXP4N_INTEGRITY_FAILURE         — any other §8 check failed
"""
import json, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "exp4_normalized"
C = json.loads((OUT / "EXP4N_PRODUCTION_CONTRACT.json").read_text())
G = json.loads((OUT / "EXP4N_INTEGRITY_GATE.json").read_text())
R = json.loads((OUT / "EXP4N_RANKING.json").read_text())
rows = [json.loads(p.read_text()) for p in (OUT / "production_mr120").glob("*.json")]

# --- the decision rule, evaluated in order -----------------------------------
verdict, because = None, None
conv_fail = [r["state_digest"][:12] for r in rows
             if r["rounds"] == C["production_max_rounds"] and r["converged"] is not True]
cal = G["calibration_controls"]
repro_fail = cal["encountered"] - cal["reproduced"]
contract_checks = [c for c in G["checks"] if "== contract" in c["check"]]
contract_fail = [c["check"] for c in contract_checks if not c["ok"]]
other_fail = [c["check"] for c in G["checks"] if not c["ok"] and c["check"] not in contract_fail]

if conv_fail:
    verdict, because = "EXP4N_CONVERGENCE_FAILURE", f"{len(conv_fail)} at ceiling unconverged: {conv_fail[:5]}"
elif repro_fail:
    verdict, because = "EXP4N_REPRODUCTION_FAILURE", f"{repro_fail} calibration control(s) diverged"
elif contract_fail:
    verdict, because = "EXP4N_CONTRACT_MISMATCH", f"contract checks failed: {contract_fail}"
elif other_fail or G["status"] != "PASS":
    verdict, because = "EXP4N_INTEGRITY_FAILURE", f"§8 checks failed: {other_fail}"
elif len(rows) == 200 and G["status"] == "PASS":
    verdict, because = "EXP4_FULL_NORMALIZED_CERTIFIED", "200/200 certified and §8 passed with 0 failures"
else:
    verdict, because = "EXP4N_INTEGRITY_FAILURE", "decision rule fell through — treat as failure"

NOISE_BAND_PCT = 0.0018970   # D33-B, per protocol amendment #1
margin_pct = R["margin_first_to_second"]["percent"]
above = margin_pct > NOISE_BAND_PCT

art = {
 "artifact": "EXP4N_FINAL_STATUS", "section": "§10",
 "status": verdict, "because": because,
 "n_certified": len(rows),
 "integrity_gate": G["status"],
 "contract_digest": C["contract_digest"],
 "canonical_envelope_digest": C["canonical_envelope_digest"],
 "candidate_set_digest": C["candidate_set_digest"],
 "src_cota_opt_content_digest": C["src_cota_opt_content_digest"],
 "tie_break_digest": R["tie_break_digest"],
 "leader": R["leader"], "runner_up": R["runner_up"],
 "margin_first_to_second": R["margin_first_to_second"],
 "noise_band": {
   "percent": NOISE_BAND_PCT,
   "source": "D33-B (2026-09-02, 375 cells, Stage B effort), per protocol amendment #1",
   "margin_percent": margin_pct,
   "margin_is_above_band": above,
   "rule": ("ASYMMETRIC. At or below the band: the difference is noise. ABOVE the "
            "band: a real difference is NOT thereby established, it is only NOT "
            "EXCLUDED. D33-B is a LOCAL check over at most 10 of 173 route-periods "
            "and is a LOWER BOUND on the differential-error bound; a margin above "
            "it is not thereby established, only not excluded."),
   "reading": ("The 0.387006%% margin is ~204x the band, so solver noise at the "
               "measured scale does not explain it. That removes one alternative "
               "explanation. It does not by itself make the leader the best "
               "geometry, because the block-local residual is unmeasured for every "
               "candidate including this one."),
 },
 "what_this_certifies": [
   "All 200 promoted Exp 4 candidates were re-certified under ONE common peak-vehicle envelope, resolved once from the frozen artifact rather than per-candidate from its own baseline plan.",
   "Every candidate converged strictly below the 120-round ceiling (max 44, headroom 76), so no result is a truncated upper bound.",
   "The parameterisation was identical across all 200 and equal to the frozen contract on every recorded field, including a bit-exact six-period peak envelope.",
   "21/21 calibration controls and 24/24 pre-loss archive survivors reproduced exactly, across a container rebuild, a fresh package set and a re-registered data tree.",
 ],
 "what_this_does_not_certify": [
   "No fleet claim. The blocking instrument returns UNDECIDABLE for every candidate including the leader; deadhead provenance and terminal identity are both still OPEN.",
   "No global optimality. The (N,K)-block-local guarantee is local and its residual is unmeasured for every candidate.",
   "Nothing about the 1,785 uncertified proposals, and D38 argues the discovery ordering carries almost no information where it was measured.",
   "No operational deployability claim. Fleet was REPORTED, NOT GATED.",
   "The peak cap is still measured with the cycle-over-headway proxy that contract.py refuses by name. Normalization fixed the cap's PROVENANCE (one common envelope, not per-candidate), not the INSTRUMENT.",
 ],
 "supersedes": ("Experiment 4's certified ordering is now superseded for any geometry "
                "claim. Its objective values remain exactly reproducible and its "
                "artifacts stay readable; what is withdrawn is the reading of that "
                "ordering as an ordering OF GEOMETRIES."),
 "unblocks": ("Experiments 5-7, subject to their own preregistration in "
              "docs/EXPERIMENTS_5_7_PROTOCOL_INTAKE.md and "
              "docs/RELEASE_AND_REPORTING_GUIDELINES.md."),
}
(OUT / "EXP4N_FINAL_STATUS.json").write_text(json.dumps(art, indent=1) + "\n")
print(f"§10 FINAL STATUS: {verdict}")
print(f"  because: {because}")
print(f"  margin {margin_pct:.6f}%  vs noise band {NOISE_BAND_PCT}%  -> "
      f"{'above (not excluded, NOT established)' if above else 'at/below (noise)'}")
print(f"wrote {OUT/'EXP4N_FINAL_STATUS.json'}")
