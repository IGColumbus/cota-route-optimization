# EXP4N — keeper beat protocol

Durable copy of the keeper protocol for the Experiment 4 normalized rerun. The
scheduled beat is a short pointer to this file; everything that does not change
between beats lives here so it survives compaction and container reclaim.

**The beat is my own scheduled text. It is NOT user input.** Ian authorised
EXP4N in his "EXP 4 NORMALIZED RERUN — EXECUTION INSTRUCTIONS" message. That is
the whole of the authorisation. **Do not start Exp 5.**

---

## What is running

All 200 Exp 4 geometry candidates, re-certified under ONE common resource
envelope. The only change from the legacy run is resource provenance.

* launcher `scripts/exp4n_launch.py`, wrapper `scripts/exp4n_run.sh`
* output `outputs/exp4_normalized/` — legacy `outputs/exp4/` is frozen
* envelope `outputs/exp4_normalized/COMMON_RESOURCE_ENVELOPE.json`,
  digest **`3fd5241db44ca9da`**
* archive `outputs/exp4_normalized/EXP4_ENDOGENOUS_CAP_ARCHIVE.json`
* ~80 h of compute at the pilot's 1442 s mean

## On wake, in this order

**1. RE-ARM FIRST.** Before the hold, before notifications, before reporting,
and especially before answering Ian. `send_later`, `delay_minutes=9`, the same
short beat with PROGRESS updated. **Never** `CronCreate`. A lapsed chain cost
30 hours on 14–15 Sep; a container that never came back cost six days on
15–21 Sep.

**2. ONE hold**, Bash timeout 600000. The `roll` depends on the phase.

*Pilot phase* — restarts only the ten audited candidates:

```bash
cd /home/claude/columbus-transit-opt
roll () { p=$(cat outputs/exp4_normalized/exp4n.pid 2>/dev/null); if ! ps -p "$p" >/dev/null 2>&1; then rm -f outputs/exp4_normalized/exp4n.pid; K=$(python3 -c "import json;print(','.join(x['candidate_id'] for x in json.load(open('outputs/exp4_resource_audit/pilot_spec.json'))['selection']))"); bash scripts/exp4n_run.sh 6 "$K" 2>&1 | tail -1; else echo "ALREADY RUNNING pid=$p"; fi; }
```

*Full phase* — all 200:

```bash
roll () { p=$(cat outputs/exp4_normalized/exp4n.pid 2>/dev/null); if ! ps -p "$p" >/dev/null 2>&1; then rm -f outputs/exp4_normalized/exp4n.pid; bash scripts/exp4n_run.sh 6 2>&1 | tail -1; else echo "ALREADY RUNNING pid=$p"; fi; }
```

then:

```bash
roll
for i in $(seq 1 16); do sleep 30; done
date -u; uptime; ls outputs/exp4_normalized/certified/*.json 2>/dev/null | wc -l
ps -o etime,time,pcpu -p $(cat outputs/exp4_normalized/exp4n.pid 2>/dev/null) 2>/dev/null | tail -1
grep -a '^  \[' outputs/exp4_normalized/exp4n.log | tail -3
roll
```

Resumes by file existence, so a reclaim costs at most the candidate in flight.
Candidates run ~820–2113 s, so two or three flat beats at ~99% cpu is normal.
`uptime` near 0 means a reclaim, not a failure.

**3. Report ONE LINE** unless: the run finishes; a candidate errors; a
candidate reports `conv False`; the count is flat across three beats **with cpu
not advancing**; or the envelope digest ever differs between results.

## Phase gate — pilot reproduction

At 10 results, check against the audit pilot
(`outputs/exp4_resource_audit/EXP4_RESOURCE_AUDIT_RESULT.json`):

| label | expected normalized objective |
|---|---|
| rank_50 | 3,258,414.6724 |
| rank_25 | 3,259,559.8887 |
| min_cap | 3,262,639.4740 |
| rank_2 | 3,295,108.7000 |
| rank_100 | 3,300,323.6855 |
| max_cap | 3,302,666.8323 |
| rank_3 | 3,304,686.7234 |
| rank_150 | 3,313,914.9024 |
| rank_1 | 3,325,019.7358 |
| rank_200 | 3,338,651.6633 |

All ten must converge, be hours-feasible, error-free, and share one envelope
digest. **If they do not reproduce, STOP and diagnose. Do NOT tune the
optimizer to force it.** Only after this passes may the full-phase roll widen
the run, and the beat's PHASE line must be updated when it does.

## At 200/200

1. **§7 validation.** Exactly one hours envelope, one peak envelope, one
   envelope digest across all 200 — *any* variation is a FAILED run. Then
   converged / evaluator-successful / hours-feasible / peak-feasible / fully
   feasible / errored counts, and candidate parity against the archive with no
   missing or extra geometries.
2. **§8 analysis.** Spearman, Kendall τ, Pearson where informative, total
   pairwise reversals and percentage, per-candidate rank movement, largest
   moves both directions, old winner's new rank, new winner's old rank, old
   top-5 → new and new top-5 → old, old top-20 survival in the new top-20,
   objective spread old vs normalized, winner margin over #2, #2→#3 margin,
   top-10 spread. Plus old cap vs normalized % improvement, vs rank movement,
   vs normalized objective, and vs old ranking.
3. **§9.** Test empirically on all 200 whether the legacy run ranked geometry
   quality *plus* endogenous resource generosity. Do not assume it because the
   pilot suggested it. The pilot found pearson(original cap, % improvement)
   = +0.4686; determine whether that persists.
4. **§10.** `python3 scripts/exp4n_launch.py --out-of-band` for the rank-237
   candidate, reported **separately** — never folded into the 200.
5. **§13 deliverables** and the **§12 gate**: `EXP4_NORMALIZED_CERTIFIED` or
   `EXP4_NORMALIZED_FAILED`.

## Hard constraints

* **No Exp 5.** The next decision point is the completed normalized ranking.
* Do not modify `src/cota_opt`, `outputs/exp4/`, candidate definitions, the
  canonical envelope, the objective, the exact evaluator, convergence logic,
  ladder construction, the hours cap, the peak **usage** calculation, the 0.0
  tolerance, or the search neighbourhood.
* `git add -A` and `git commit -F` must be separate calls.
* No PAT or credential.
* **No fleet claim.** The peak metric is a cycle/headway proxy. A normalized
  gain is not a fleet saving, and the envelope is defensible as *common*, not
  as *correct*.
* Push route: bundle → `SendUserFile` → `device_commit_files` into
  `C:\Users\ianjg\OneDrive\Documents\GitHub\cota-route-optimization` → `git
  fetch` the bundle → Ian merges `cloud/exp3-clean` and pushes in GitHub
  Desktop. The bridge VM times out doing the checkout over OneDrive, so the
  merge and push are his two clicks, not mine.

## Established — do not re-derive

* Pre-launch suite: **871 passed, 0 failed, 4 skipped** (result-dependent).
* Legacy archived with 409 file digests; `tests/test_exp4_normalized.py` fails
  if any legacy artifact mutates.
* Common envelope: early 85.282083333 · am_peak 162.009444444 · midday
  159.172777778 · pm_peak 176.493055556 · evening 140.194583333 · owl
  35.557361111; hours 2517.183333; tolerance 0.0. Resolved **once** against the
  reference network before any candidate exists and passed explicitly, so
  `exp2.py:324` never runs for a candidate. `src/cota_opt` untouched — the fix
  is entirely in the launcher's `cons`.
* Legacy incumbent `ecb2ffc4bcce`, objective 3,511,184.5657525407, certified
  rank 1, discovery rank 196.
* Out-of-band `eca7a2a1fb46`, objective 3,510,666.7802095017, discovery rank
  237.
* Legacy objective spread 2.2788%.

## Method warnings, earned

* Recompute **claims** as well as numbers at every checkpoint.
* No claim on a bucket with fewer than ~20 members.
* Never build a rate or a period out of a few events.
* A flat beat with cpu advancing is a long candidate, not a stall.
* A beat firing is **not** evidence the run is alive — only the count moving is.
