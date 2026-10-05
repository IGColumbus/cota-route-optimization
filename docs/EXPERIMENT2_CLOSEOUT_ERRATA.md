# Experiment 2 closeout: errata

*Append-only. `EXPERIMENT2_CLOSEOUT.md` and registry v5 `experiments.exp2.headline`
are frozen and are left unchanged; where they conflict with a row here, the row
here wins.*

| # | date | artifact and key | recorded statement | corrected interpretation | evidence |
|---|---|---|---|---|---|
| E1 | 2026-10-05 | `EXPERIMENT2_CLOSEOUT.md` §"Certification status" (row "six candidates measurably harmful … 400,000/20, 3 replicates … yes") and §headline bullet "Six of the twelve candidates do measurable harm"; `outputs/CANONICAL_RESULTS_v5.json → experiments.exp2.headline` ("At the effort Experiment 1 is certified at, six of twelve candidates do measurable harm") | Six single splices measurably harmful at certification effort | The six-harmful classification is at ranking effort (60,000/2/32, discovery stage, floor 0.13 percentage points): `outputs/exp2_candidate_classes.json → rule.counts` (`harmful: 6`, effort `60000/2/32`), whose own `recheck_required` field says the harmful candidates must be re-run at full effort before being described as harmful. Only four singles were re-run at 400,000/20 (one seed each): `outputs/exp2_summary.json → recheck_D19.candidates` and `outputs/exp2_eval.jsonl` cells `…|same_route|400000/20/0`. Two of them (002+033 +2.119%, 007+101 +0.802%) exceed the 0.287-percentage-point floor; two (011+034 +0.060%, 033+034 +0.160%) do not. None is beneficial at certification effort. No harm magnitude is re-sized here (no new computation; matched-start confirmation exists for the Exp 2B leader only). | Found during the 2026-10-05 release cleanup (P0-11). No number changed; the count of certified-harmful singles changes from six to two. |
