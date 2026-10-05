# Experiments

Each directory has one current contract or protocol and one current closeout. Superseded designs, abandoned phases, audits and incident notes live in `docs/research-record/expN/`. Shared acceptance gates are in `ACCEPTANCE.md`. Experiment runners are in `scripts/`; artifacts are in `outputs/`, indexed by `outputs/CANONICAL_RESULTS_v5.json` and `outputs/README.md`.

| experiment | question | contract / protocol | closeout |
|---|---|---|---|
| [exp1](exp1/README.md) | Frequency redistribution, geometry fixed | `ACCEPTANCE.md` (gates committed at `1a2b6e2d`, after a first exploratory run; not pre-specified) | `outputs/canonical/exp1_final.json` (headline, frontier); results narrative in `docs/report/TECHNICAL_REPORT.md` §5.1 |
| [exp2](exp2/README.md) | Through-routing geometry (Exp 2 and 2B) | `ACCEPTANCE.md` gates 2B-1 … 2B-7 (`2ac3b1dd`) | `EXPERIMENT2_CLOSEOUT.md` (frozen), corrected by `EXPERIMENT2_CLOSEOUT_ERRATA.md` |
| [exp3](exp3/README.md) | Route mutation | `EXPERIMENT3_CONTRACT.md`; Stage B rule `EXPERIMENT3_STAGE_B_PREREGISTRATION.md` (historical file name; frozen at `23bb99bd`) | `EXPERIMENT3_CLOSURE.md` (registered closeout) |
| [exp4](exp4/README.md) | Greenfield network design (Exp 4, 4N normalized rerun, 4A original question) | `EXPERIMENT4_CONTRACT.md`; 4A contract `outputs/exp4_addendum/EXP4A_CONTRACT.json` (`16a0c86a`) | `EXPERIMENT4_NORMALIZED_CLOSEOUT.md` (4N) and `EXPERIMENT4_ORIGINAL_QUESTION_ADDENDUM.md` (4A) |
| [exp5](exp5/README.md) | Modeled operating-resource frontier | `outputs/exp5/EXP5_CONTRACT.json` (EXP5_FRONTIER `395ee3c960f51935`, `4a9bc6b5`) | `EXPERIMENT5_CLOSEOUT.md` (status `EXP5_MONOTONICITY_FAILURE`) |
| [exp6](exp6/README.md) | Modeled price of study safeguards | `EXPERIMENT6_PROTOCOL.md` with `EXPERIMENT6_AMENDMENT_1.md`, `EXPERIMENT6_AMENDMENT_2.md`, `EXPERIMENT6_D39_AMENDMENT.md`; catalog `EXPERIMENT6_CONSTRAINT_CATALOG.md` | `EXPERIMENT6_CLOSEOUT.md` |
| [exp7](exp7/README.md) | Robustness under assumption and model perturbations (final experiment) | `EXPERIMENT7_AMENDMENT.md` (§13 frozen at `b18c2f24`; §14 and contract `1263bedaebe6a45d` at `4a2ba9f6`); background `EXPERIMENT7_PROTOCOL.md`, `EXPERIMENT7_PROTOCOL_AS_ISSUED.md`, `EXPERIMENT7_SEPT23_FINALIZATION.md` | `EXPERIMENT7_CLOSEOUT.md` (registered; sha256 `27bfc739…`), corrected by `EXPERIMENT7_CLOSEOUT_ERRATA.md`; summary `EXPERIMENT7_RESULTS.md`; post hoc `EXPERIMENT7_F1_ADDENDUM.md` |
