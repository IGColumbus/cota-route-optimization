# Experiment 4: Greenfield network design (Exp 4, 4N normalized rerun, 4A original question)

* **Contract / protocol:** `EXPERIMENT4_CONTRACT.md`; 4N production contract `outputs/exp4_normalized/EXP4N_PRODUCTION_CONTRACT.json`; 4A contract `outputs/exp4_addendum/EXP4A_CONTRACT.json` (`16a0c86a`)
* **Closeout / results:** `EXPERIMENT4_NORMALIZED_CLOSEOUT.md` (4N, current ordering) and `EXPERIMENT4_ORIGINAL_QUESTION_ADDENDUM.md` (4A)
* **Canonical artifacts:** `outputs/exp4_normalized/EXP4N_RANKING.json`, `outputs/exp4_addendum/DELTA43.json` (full list: `outputs/CANONICAL_RESULTS_v5.json → experiments.exp4`)
* **Superseded (legacy ordering):** closeout `docs/research-record/exp4/EXPERIMENT4_CLOSEOUT.md`; certified files `outputs/exp4/run/certified/*.json` (not moved). The legacy leader `ecb2ffc4bcce` is in `outputs/exp4/run/certified/0c486f6d440fc5b5.json` (files are named by state hash, not candidate id) and ranks 185 of 200 in `EXP4N_RANKING.json`. Why: `outputs/SUPERSEDED.md` (exp4 section), report §9 R5.
* **Telling legacy from normalized files:** both carry the same `contract_digest` (`2125984c82b60a83`, the certification-code constant in `src/cota_opt/exp4_certify.py`), and both have an empty `code_version`. The regime is identified by directory: `outputs/exp4/run/certified/` is legacy, `outputs/exp4_normalized/production_mr120/` is normalized.
* **Other historical material:** `docs/research-record/exp4/` and `docs/research-record/MOVES.md`

Paths inside frozen documents are the paths at `research-final` (`cd03af9c`); `docs/research-record/MOVES.md` maps them to the current tree.
