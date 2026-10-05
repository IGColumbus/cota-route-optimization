# Experiment 4 — Normalized rerun (EXP4N): CLOSEOUT

**Status: `EXP4_FULL_NORMALIZED_CERTIFIED`** — 200 of 200 candidates certified,
§8 integrity gate passed 44 checks with zero failures, §10 decision rule reached
its terminal branch. Completed 2026-09-28.

Artifacts: `outputs/exp4_normalized/EXP4N_FINAL_STATUS.json`,
`EXP4N_INTEGRITY_GATE.json`, `EXP4N_RANKING.json`,
`EXP4N_PRODUCTION_CONTRACT.json`, `EXP4N_ENVIRONMENT_GATE.json`,
`EXP4N_ROUND_CAP_CALIBRATION.json`, `production_mr120/` (200 results).

---

## 1. The headline, and it goes against Experiment 4

```
LEADER   35e351133d6f   3,223,885.9475   21 rounds   65 lines   was LEGACY RANK 154
2nd      d451584c40c6   3,236,362.5736                          was legacy rank 193
margin   12,476.6261 absolute  =  0.387006%
spread   first to last 4.1710%          (legacy spread was 2.2788%)

legacy leader ecb2ffc4bcce, legacy rank 1   ->   NORMALIZED RANK 185 OF 200
spearman rank correlation                        +0.3566
pairwise orderings inverted                      7,296 of 19,900   (36.7%)
```

**Only one of Experiment 4's top ten survives in the normalized top ten.** The
legacy top ten map to normalized ranks **185, 97, 135, 43, 69, 23, 41, 103, 6,
48** — they scatter across the entire field.

The 10-candidate pilot that triggered this rerun predicted the direction and
**understated the size**. It moved 20 of 45 pairwise orderings (44%), dropped the
incumbent to 9th of 10, and handed first place to a candidate legacy-ranked 50.
At full scale the incumbent falls to **185th** and the leader comes from
**154th**.

### A pattern in the top of the table, stated as a consistency

The top five normalized candidates carry legacy ranks **154, 193, 192, 194, 191**
— drawn almost entirely from the *bottom* of the legacy ordering. That shape is
consistent with the defect the resource-normalization audit named: under the
endogenous cap (`exp2.py:324` resolving `peak_fleet_by_period: "baseline"`
against each candidate's own baseline plan) a candidate was optimized inside a
box it defined for itself, so legacy rank partly recorded *how generous that
candidate's own envelope happened to be* rather than how good its geometry is.

**This is a consistency, not a demonstration.** Testing it — regressing the
normalized improvement on each candidate's own legacy envelope — is a separate
diagnostic and has not been run. It is written here so that nobody later mistakes
the pattern for a tested mechanism.

## 2. What the run actually was

200 candidates, `MAX_ROUNDS = 120`, one common peak-vehicle envelope resolved
**once** from the frozen artifact rather than per-candidate:

| | |
|---|---|
| contract digest | `2125984c82b60a83` |
| canonical envelope digest | `3fd5241db44ca9da` |
| candidate-set digest | `38e52f0b14b1d554` |
| `src/cota_opt` content digest | `add5d0002d29aa49` (unmodified) |
| tie-break digest | `0297e180cf30369d` (the legacy frozen tie-break) |
| search | n_keys 8, k_rungs 3, λ 2.0, seed 20260825, tolerance 0.0 |
| hours cap | 2517.1833333333334 |

Compute: **79.85 hours** across 200 candidates, mean 1,437 s each, on two
parallel workers sharing a 2-core container.

**Rounds: min 11, median 21, mean 22.2, p90 31, max 44 — against a ceiling of
120.** Nothing came within 76 rounds of the cap. The round-cap calibration chose
120 against an observed max of 44 across 21 candidates; across all 200 the
observed max is still exactly 44. §5's hard stop never armed.

Zero exact-objective ties, so the frozen tie-break never had to decide anything.
The ordering is by certified objective alone.

## 3. Reproduction — two independent channels, both perfect

This run was rebuilt from scratch after the container holding its predecessor was
destroyed, on a different container, a fresh package set and a re-registered data
tree. Both channels agree completely:

* **§6 calibration controls — 21/21** reproduced exactly on objective, rounds,
  converged flag **and plan digest**, against the stored MAX_ROUNDS=200
  calibration set. Including `12ab99b5915e` at 44 rounds, the single candidate the
  old 40-round cap truncated, which is where a changed substrate would surface
  first.
* **Pre-loss archive — 24/24** bit-exact across 16 fields plus every per-round
  trajectory objective, against the results that survived the destroyed run.

Plus a **2/2 bit-exact environment gate** run before production started, because
the contract pinned `src/cota_opt` but never pinned the environment and no
lockfile existed. `EXP4N_ENVIRONMENT_GATE.json`; the environment is now recorded
in `EXP4N_RERUN_ENVIRONMENT.txt`.

Every data input was recovered and its sha256 verified against the
`input_checksums` recorded in 43 committed `experiment.json` artifacts **before**
ingest. Nothing was re-downloaded, so a republished upstream feed cannot have
entered: `cota_gtfs_static b11634f1…`, `lodes_od_oh 98cd08aa…`,
`lodes_rac_oh 848b5941…`, `lodes_wac_oh 92157333…`, `cenpop_bg_oh ca6e3344…`.

## 4. The margin, read under the preregistered rule

Margin first-to-second is **0.387006%**, about **204×** the D33-B noise band of
**0.0018970%**.

Amendment #1's rule is **asymmetric**. At or below the band, a difference is
noise. **Above the band, a real difference is NOT thereby established — it is
only not excluded.** D33-B is a *local* check over at most 10 of 173
route-periods and is a *lower bound* on the differential-error bound.

So the honest reading is narrow: solver noise at the measured scale does not
explain this gap. That removes one alternative explanation and does not install a
conclusion. The `(N,K)`-block-local residual remains unmeasured for every
candidate, this leader included.

Note the contrast with Experiment 4, whose first-to-second margin was 0.0106% —
about 5.6× the band. This run's ordering is far less tightly packed at the top.

## 5. What this does NOT certify

* **No fleet claim.** The blocking instrument returns `UNDECIDABLE` for every
  candidate including the leader. Deadhead provenance and terminal identity are
  both still OPEN. Fleet was REPORTED, NOT GATED.
* **No global optimality.** The guarantee is `(N,K)`-block-local and its residual
  is unmeasured.
* **Nothing about the 1,785 uncertified proposals**, and D38 argues the discovery
  ordering carries almost no information where it was measured.
* **No operational deployability claim.**
* **The instrument was not fixed, only the provenance.** The peak cap is still
  compared using `FitnessVector.peak_by_period` — Σ cycle/headway, the
  cycle-over-headway proxy `contract.py:451` refuses by name. Normalization made
  the cap *common* rather than self-chosen; it did not make it a vehicle count.
  This limitation survived the entire rerun intact and travels with every number
  above.

## 6. What is superseded

**Experiment 4's certified ordering is superseded for geometry claims.** Its
objective values remain exactly reproducible and its artifacts stay readable —
nothing is deleted, as everywhere else in this project. What is withdrawn is the
reading of that ordering as an ordering *of geometries*. It was an ordering of
candidate-specific optimization problems, and now there is a measured figure for
how much that mattered: 36.7% of pairwise orderings, and a leader that falls 184
places.

## 7. Operational record

The predecessor run reached 153/200 and was destroyed on 2026-09-24 when the
ephemeral container was reclaimed; 129 results existed only on that disk.
`docs/EXP4N_CONTAINER_LOSS_INCIDENT.md`. The owner chose a fresh 200 rather than
resuming across the 24 survivors, and those 24 are preserved as
`production_mr120_PRE_LOSS_DIAGNOSTIC/` with a sha256 manifest, marked DIAGNOSTIC
ONLY — they passed every reuse check, and the decision was provenance, not
defect. `docs/EXP4N_RELAUNCH_AUTHORIZATION.md`.

This run was checkpointed every 3–5 candidates to a git object store on hardware
outside the container, with each checkpoint verified by comparing the durable
ref against the exported head. **Worst-case loss never exceeded one checkpoint
interval.**

Four defects were found and fixed *during* the run, and every one of them either
reported success or said nothing:

1. **Pidfile recorded setsid's pid, not python's** (843 vs 845 measured). The
   keeper would have read a healthy run as dead and started a second runner over
   the same output directory. Latent through the entire destroyed run.
2. **A failed background `gc`** on the durable machine left a `.lock` on all 16
   refs; a depth-2 sweep missed them; the next fetch failed and the durable
   pointer silently lagged a checkpoint.
3. **The staging mount** began returning I/O errors on every write while
   reporting 1.0P free; the export died and the pointer sat three results behind.
4. **`FETCH_HEAD` permission denied** on the durable side; the fetch printed a
   successful bundle verification and then did not move the ref.

All four were caught by the same discipline: **verify the pointer against the
exported head rather than trusting an exit status.** None cost a result. The
recurring lesson is the project's own — *a mechanism that looks like it is
working is not evidence that it ran.*

## 8. What this unblocks

Experiments 5, 6 and 7, subject to their own preregistration in
`docs/EXPERIMENTS_5_7_PROTOCOL_INTAKE.md` and
`docs/RELEASE_AND_REPORTING_GUIDELINES.md`. Note that Exp 5's premise audit
returned `EXP5_REFRAME_REQUIRED` independently of this run, and the OFF→ON
diagnostic found the binding constraint is the peak-vehicle cap rather than the
hours axis Exp 5 varies. **This certification removes Exp 5's block condition; it
does not answer Exp 5's premise problem.**

Also outstanding, approved on 2026-09-25 and deliberately deferred until after
completion: an **exact-envelope fingerprint** over raw IEEE-754 values rather than
`round(peak, 9)`. It is ADDITIONAL, is never retrofitted into this contract, and
may never be used to invalidate this run — which rests on explicit bit-exact
assertions, not on `envelope_digest`.
