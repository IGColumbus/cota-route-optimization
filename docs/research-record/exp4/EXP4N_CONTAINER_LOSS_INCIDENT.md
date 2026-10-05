# EXP4N container-loss incident — 2026-09-24

Status: **`EXP4N_PRODUCTION_RUN_LOST_AT_153`**. The run is not paused, not
resumable in place, and not certified. Its process and 129 of its results no
longer exist. No EXP4N conclusion of any kind is licensed by this document.

---

## 1. What happened

At approximately **23:40 UTC on 2026-09-24** the ephemeral cloud container
running the EXP4N full normalized production batch was rebuilt. `uptime`
reported `up 5 min` at 23:45 UTC. `/home/claude` contained only base-image
dotfiles dated 8 May. `/home/claude/columbus-transit-opt` did not exist, and a
filesystem-wide search for the repository and for `exp4n_launch.py` returned
nothing. The run's worker process died with the container.

Last reported state before the loss: **153/200 complete**, every completed
candidate `converged == True`, zero errors, one envelope digest across all rows,
`max_rounds == 120` on every row, maximum observed `rounds == 44`, **zero
candidates at the ceiling**, and all seven §6 calibration controls reproduced
exactly.

## 2. What was lost

**Candidates 25–153 — 129 certified production results, approximately 30 hours
of compute.** Also lost: the four post-bundle checkpoint commits `f69073b3`
(50/200), `65838b9f` (100/200), `dd06abb0` (125/200), `ac56813a` (150/200).

These are gone, not misplaced. Every place they could survive was checked:

| Location | Result |
| --- | --- |
| Container filesystem | rebuilt; no repository anywhere |
| Durable repo object store (`git cat-file -e`) | all four checkpoint commits **ABSENT** |
| All 27 bundles in the durable `Downloads` folder | newest is 2026-09-23, tip `4de29b8e` |
| GitHub `origin/exp3-clean` | `099d05278`, dated 2026-09-21 — predates all EXP4N work |
| Attached project docs | documentation only, no result records |
| This session's own log | 55 lines post-compaction; no per-candidate records |

The lost results cannot be reconstructed from anything that survives. Partial
objective values quoted in progress reports are aggregate statistics and would
not constitute certified records even if they were complete, which they are not.

## 3. What survived

Durable tip **`4de29b8e9`** (2026-09-23 18:14:59), reachable both as
`cloud/exp3-clean` in the durable repo and as
`cota-exp3-clean-20260923-1825.bundle`:

- `scripts/exp4n_launch.py` — the entire normalization fix, with `src/cota_opt` untouched
- `outputs/exp4_normalized/EXP4N_PRODUCTION_CONTRACT.json` — the frozen contract, including the exact IEEE-754 peak envelope
- `outputs/exp4_normalized/COMMON_RESOURCE_ENVELOPE.json`
- `outputs/exp4_normalized/EXP4_ENDOGENOUS_CAP_ARCHIVE.json` — all 200 candidate keys
- `outputs/exp4/run/` — `proposals.json` and the 35 MB `eval_cache.jsonl`
- 21 aborted 40-cap results, 21 MAX_ROUNDS=200 calibration results, the pilot gate
- every document: round-cap finding, digest insufficiency, the 5–7 protocol intake, the release guidelines
- **24 production results** — exactly positions 1–24 of the `certified_rank` ordering, a contiguous prefix with no gaps

`scripts/exp4n_restore_verify.py` re-establishes all of this against the frozen
artifacts: **35 checks, 0 failures**, recorded in
`outputs/exp4_normalized/EXP4N_RESTORE_VERIFICATION.json`. The 24 survivors
carry the contract digest, the canonical envelope digest, `max_rounds == 120`,
`n_keys == 8`, `k_rungs == 3`, `lam == 2.0`, `seed == 20260825`,
`budget_tolerance == 0.0`, the bit-exact six-period peak envelope, full round
trajectories, `converged == True`, and none sits at the ceiling.

## 4. Root cause

Preregistration §12 required: *"Commit durable intermediate results/checkpoints
periodically enough that container loss cannot destroy substantial completed
work."*

The checkpoints were committed to a git repository **inside the ephemeral
container** and that was treated as satisfying §12. It never did. A commit to a
reclaimable disk records history on the same disk that can vanish; it is a
convenience, not a checkpoint. The only genuine durability event in the entire
run was a single bundle export on 2026-09-23 at 18:25, which predated every
production result but the first 24.

Two aggravating factors, both known at the time:

1. **A container loss had already occurred on 2026-09-23.** The lesson drawn
   from it was that holds are load-bearing — a correct lesson about keeping the
   container *alive*. The lesson not drawn was that the disk itself is not a
   safe place to record anything, and that no aliveness discipline can substitute
   for getting bytes off the machine.
2. **The standing instruction to push to GitHub so there is an actual record on
   git was not satisfied for any EXP4N work.** `origin/exp3-clean` still sits at
   `099d05278` from 21 September. Had that instruction been followed, the four
   checkpoint commits would have survived.

This is an operator failure, not an environment surprise. §12 named this exact
outcome and the mechanism built to prevent it did not do so.

## 5. Measurements taken after the loss

Three facts were established by direct measurement, not assumption, because the
recovery design depends on them.

**5.1 — Processes on the durable machine do not survive between calls.** A
detached `nohup` heartbeat writing every 3 seconds was launched on the durable
machine's shell. Across the call boundary it had written exactly **2 beats**,
both inside the launching call's lifetime, and nothing after. The shell runs
under `bwrap --die-with-parent --unshare-pid`: every process dies when the call
returns. Combined with 2 cores and 3 GB of memory there, **running the batch on
the durable machine is not possible.** This also retroactively confirms the
earlier finding that the batch was running in the cloud container and not on
that machine.

**5.2 — GitHub push is blocked from both sides.** From the durable machine:
`fatal: could not read Username for 'https://github.com'` — no credentials in
that shell. From the container: `remote: access denied by the git proxy:
ian-gregory94/cota-route-optimization is not in this session's authorized
repository set, so the proxy will not inject a credential for it`, HTTP 403.
Anonymous read works from both. Generating a personal access token is out of
scope by standing instruction and would not help, since the proxy refuses
unconfigured repositories regardless of credential. **Unblocking GitHub requires
an action only the repository owner can take**: add the repository to the
session's authorized sources, or push from a shell outside the sandboxed VM.

**5.3 — A false mismatch was caught before it was reported.** The first
recomputation of `src_cota_opt_content_digest` used its own directory walk
(paths plus contents, all files) and produced `594b1e47be4b0384` against the
contract's `add5d0002d29aa49`. That was a bug in the re-derivation, not a
mismatch in the tree. Recomputed with the frozen script's own algorithm —
`sha256` over the sorted *contents* of `rglob("*.py")`, no paths — it matches
exactly. This is the same trap that produced the hand-typed envelope-constant
mismatch during the contract freeze, and the standing rule held: **compare
against the frozen artifact using the frozen algorithm, never against a
re-derivation.**

## 6. What this does and does not license

**Does not license:** any statement about the EXP4 winner, geometry conclusions,
ranking stability, or normalized-versus-legacy comparison. Preregistration §7
forbids interpretation until all 200 candidates have completed and passed
certification. 153 completed and 24 survive; neither is 200. The 24 survivors
are inputs to a future run, not evidence about anything.

**Does license:** the statement that the restored tree is parameterically
identical to the frozen contract, and that the 24 survivors were produced under
that contract.

## 7. Corrective design

The durable side must hold the authoritative pointer to what is safe. Local
state cannot be trusted to record what has been exported, because local state
dies with the disk it describes.

`scripts/exp4n_durable_export.sh` takes the base commit as an argument, read
from the durable repo immediately before the call, and produces a verified
incremental bundle. It refuses to run if the base is absent or is not an
ancestor of `HEAD`, and it prints the steps it cannot perform itself.

The export is only complete when the bundle has been **fetched into the durable
repository's object store** and that repository's `cloud/<branch>` ref has been
confirmed to point at the exported head. A bundle sitting unfetched beside a
repository is a file, not a checkpoint.

Checkpoint cadence for any relaunch must be chosen as a **maximum acceptable
loss window**, not as a convenient interval. At the measured 17.3 min/candidate,
a 5-candidate cadence caps the loss at roughly 1.5 hours. The failed run's
effective cadence was 30 hours.

## 8. Open decisions

Both belong to the repository owner and neither is assumed here.

1. **Relaunch scope.** A clean 200 is ~44 h at the measured rate. Resuming over
   the 24 survivors is ~38 h. The launcher already skips completed candidates by
   globbing the results directory, so resumption needs no code change — but
   whether reuse is admissible under the §5 identical-parameterization rule is
   the owner's call. The survivors are parameterically identical to the contract
   on every recorded field, which is a necessary condition for reuse, not a
   decision to reuse.
2. **Durability sign-off before relaunch.** Option "run it on the durable
   machine" is closed by §5.1. What remains is per-checkpoint export to the
   durable repository, plus whichever GitHub unblock the owner chooses.

Until both are settled, nothing is relaunched.
