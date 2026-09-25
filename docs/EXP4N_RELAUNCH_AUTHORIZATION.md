# EXP4N relaunch authorization — 2026-09-25

Recorded because the relaunch is not a resumption. It is a second execution of
the same frozen contract after total loss of the first, and the scope decision
was the owner's, not mine.

## The two decisions

Asked after the loss was reported and the restored tree had been verified
(35 checks, 0 failures, `EXP4N_RESTORE_VERIFICATION.json`).

**1. Relaunch scope: FRESH 200 FROM SCRATCH.** Not a resume across the 24
surviving results.

The survivors passed every automated check that would have permitted reuse —
identical contract digest, identical canonical envelope digest, bit-exact
six-period peak envelope, `max_rounds == 120`, `n_keys == 8`, `k_rungs == 3`,
`lam == 2.0`, `seed == 20260825`, `budget_tolerance == 0.0`, all converged, none
at the ceiling, and a contiguous `certified_rank` prefix 1..24 with no gaps.
**Nothing technical excluded them.** The owner chose the cleaner provenance
story at a cost of roughly six hours, and that is recorded here so no later
reader concludes the survivors failed something.

They are moved to `outputs/exp4_normalized/production_mr120_PRE_LOSS_DIAGNOSTIC/`
with a `STATUS.json` manifesting all 24 by sha256, marked DIAGNOSTIC ONLY. They
are preserved rather than deleted, for the same reason every other superseded
artifact in this project is preserved. `production_mr120/` starts empty, so the
launcher's file-existence resume cannot splice them in.

**2. Durability: BOTH mechanisms.** Bundle every checkpoint now; switch to direct
push once the repository is authorized for this session.

- **Now, and requiring nothing from the owner:** every checkpoint is committed,
  exported as a verified incremental bundle, written to the owner's machine, and
  **fetched into that repository's object store**, with its `cloud/exp3-clean`
  ref confirmed to point at the exported head. A bundle sitting unfetched beside
  a repository is a file, not a checkpoint.
- **When the owner authorizes the repo for this session:** push to GitHub
  directly on the same beat. This is the part that matters, because the four
  checkpoint commits that died on 2026-09-24 died behind a manual step at the end
  of a chain. A GUI click is the same shape of dependency.

Checkpoint cadence is chosen as a **maximum acceptable loss window**, not a
convenient interval: every 5 completed candidates, roughly 1.5 h at the measured
17.3 min/candidate. The failed run's effective cadence was 30 h.

## What is unchanged, and must stay unchanged

The contract is **not re-frozen**. `EXP4N_PRODUCTION_CONTRACT.json` stands as
written, digest `2125984c82b60a83`, envelope digest `3fd5241db44ca9da`,
candidate-set digest `38e52f0b14b1d554`, source commit `431b105a`,
`src/cota_opt` content digest `add5d0002d29aa49`.

`src/cota_opt` is untouched and verified unmodified. The ceiling is still passed
through the existing `certify()`/launcher interface. `--stop-on-nonconvergence`
and `--calibration-dir calib_mr200` are still set, so the §5 ceiling-hit halt and
the §6 calibration controls are both armed exactly as before.

No search parameter changed. The only differences from the lost run are the
output directory's starting emptiness and the checkpoint cadence — neither of
which can change a number.

## What is still forbidden

§7 stands: no statement about the EXP4 winner, geometry conclusions, ranking
stability, or normalized-versus-legacy comparison until all 200 complete and pass
certification. Experiments 5, 6 and 7 stay gated on
`EXP4_FULL_NORMALIZED_CERTIFIED`.

On `rounds == 120 && converged == False`: stop, classify
`EXP4N_CONVERGENCE_FAILURE`, and report. Do not accept the objective, do not
raise the ceiling, do not restart at 200 and carry on.
