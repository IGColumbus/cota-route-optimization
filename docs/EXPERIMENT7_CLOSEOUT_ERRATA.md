# Experiment 7 closeout — errata

*2026-10-04. `EXPERIMENT7_CLOSEOUT.md` is registered in
`outputs/CANONICAL_RESULTS_v5.json` with its sha256, so it is left unchanged.
Corrections are recorded here. They come from an independent fact-check of the
closeout against the artifacts. Read this file together with the closeout.*

| # | closeout location | as written | correction |
|---|---|---|---|
| E1 | §1.1 | "`git diff 4a2ba9f6 HEAD -- scripts/ src/` shows exactly three changes" | True when written. Two later reporting-only scripts now also appear: `scripts/canonical_results_v5.py` (registry) and `scripts/exp7_f1_decision_space.py` (post hoc addendum, reads only). `src/cota_opt` is still unchanged. |
| E2 | §4, F6 row | "(26 priced cells)" | **25.** 13 on N0 and 12 on N3; N3 R1_H20 has no plan. Also, R2_S25 and R2_S10 are identically zero at every level on both networks, so 2 of N0's 11 and 2 of N3's 5 SIGN_ROBUST cells are trivially robust. |
| E3 | §5 F1 row, §6 F1 row, §8 second permitted claim | The re-optimized reduction "holds where the unserved-trip penalty dominates (λ = 4, transfer penalty ×0.5)" | **Basin-dependent; do not use as written.** The same cell (N0 REF at BASE, λ = 2) was closed independently on the F4 track. It reached a certified fixed point 0.161% *better* in objective, with F1 = **+30.5%** (48 route-periods OFF), against −5.43% on the F6 track (17 OFF). Once service may be switched off, unserved demand is not identified by the λ = 2 objective. See `docs/EXPERIMENT7_F1_ADDENDUM.md` and `outputs/exp7/EXP7_F1_DECISION_SPACE.json` → `rows[].ref_f4_track`. The preregistered label (SIGN_SENSITIVE) is unaffected. |
| E4 | §5.2 | BASE column of the λ = 1 collapse table (21,091 served, 17 OFF) | That column is one basin of a flat objective (E3). It illustrates the mechanism and is not a finding. The λ = 1 column is the same plan on both tracks. |
| E5 | §5.2 | "N3 converges to the same near-empty service" | Near-empty: 557 of 2,516 revenue vehicle-hours and 34 of 173 route-periods still ON on N0. Not zero service. |
| E6 | §8 first permitted claim and the addendum | "every λ ≥ 2 level" | Means the Stage 2 levels actually re-optimized: BASE, A5_LAM4, A5_TP050, A5_TP200, A6_WALKSPD85 and A6_MAXWALK75. The other Class A dimensions were evaluated at fixed plans only. |
