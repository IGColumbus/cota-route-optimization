# Experiment 5 closeout: errata

*Append-only. `EXPERIMENT5_CLOSEOUT.md` and registry v5 `experiments.exp5` are
frozen and left unchanged; where they conflict with a row here, the row here
wins.*

| # | date | artifact and key | recorded statement | corrected interpretation | evidence |
|---|---|---|---|---|---|
| E1 | 2026-10-05 | `EXPERIMENT5_CLOSEOUT.md` (closeout commit `d4c9c0c7`), "Below 100%, cutting hours costs +2.05% (H075) and +0.57% (H090)" | +2.05% and +0.57% | +2.04% (H075) and +0.56% (H090). The closeout over-rounded: the artifact values are 2.04496% and 0.56481% (N0, `B_hours_only` arm, objective relative to J100) | `outputs/exp5/EXP5_ANALYSIS.json → frontier` (N0 rows H075, H090, J100); checked by `scripts/verify_report_claims.py`. Found by the 2026-10-05 public-number audit. No conclusion changes. |
