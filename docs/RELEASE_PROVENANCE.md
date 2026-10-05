# Release provenance

*Keep this file true to what GitHub shows. Last updated 2026-10-05, during the
release cleanup. Nothing here should claim that a tag or branch is public until
`git ls-remote origin` shows it.*

## Starting public state (recorded before the cleanup)

Recorded on 2026-10-05 from `git ls-remote origin`:

| ref | commit |
|---|---|
| `refs/heads/master` | `c90d8b18` (2026-10-05T04:28:29Z) |
| `refs/heads/exp3` | `e162d24b` |
| `refs/heads/exp3-clean` | `63249104` |
| `refs/heads/frombundle` | `884dd4cb` |
| tags | **none** |

`git log --oneline origin/master..HEAD` was empty, so no local-only commits existed.

## Frozen research state

| item | value |
|---|---|
| frozen research commit | `cd03af9c` (`master`, 2026-10-05). Every contract, digest and canonical artifact verifies against it. |
| freeze tag | `research-final`, an annotated tag (object `78a4355d`) pointing at `cd03af9c`. **It exists in the author's clone and in the development container. It is not yet public on GitHub.** Until it is, cite `cd03af9c`. |
| canonical results registry | `outputs/CANONICAL_RESULTS_v5.json` (v5; sha256 `e24c3f0e2bf075c1…`). v1–v4 are kept unchanged. |
| Experiment 7 contract | digest `1263bedaebe6a45d` (`outputs/exp7/EXP7_CONTRACT.json`), frozen at `4a2ba9f6` |
| Experiment 7 closeout | `experiments/exp7/EXPERIMENT7_CLOSEOUT.md`, sha256 `27bfc7390c777051…`. It is registered and unchanged; corrections are in `experiments/exp7/EXPERIMENT7_CLOSEOUT_ERRATA.md`. |
| environment snapshot | `docs/research-record/ENVIRONMENT_AT_FREEZE.txt`: a pip freeze of the late-stage development container, Python 3.11.15. No container image is recorded. Status: dependency snapshot recorded; clean-machine reproduction not yet demonstrated. |

## Historical freeze tags

All of these exist in the author's clone and in the development container. **None is public yet.**

| tag | tag object | commit | commit public? |
|---|---|---|---|
| `exp3-final-v1` | `f0e6a81e` | `8c2841c4` | yes, reachable from `master` |
| `exp3-frozen-v1` | `93a67bdb` | `80221f75` | yes, reachable from the archival branch `exp3` only |
| `gen1-frozen-v1` | `bb533e7c` | `4b62c728` | yes, reachable from `master` |
| `pre-exp3-v1` | `c217a45c` | `5b23446e` | yes, reachable from `master` |
| `pre-exp3-v2` | `34f4f91f` | `9ee905eb` | yes, reachable from `master` |

The branch `backup-exp3-preclean` (`e733daa8`, 190 commits) holds the
pre-collapse Experiment 3 history. It exists in the author's clone and in the
container. **Its history is not on GitHub.**

To publish these refs, run this from a clone that has them (needs push rights):

```
git push origin research-final exp3-final-v1 exp3-frozen-v1 gen1-frozen-v1 pre-exp3-v1 pre-exp3-v2 backup-exp3-preclean
```

## Branches

| branch | role | plan |
|---|---|---|
| `master` | the public line: research record up to `cd03af9c`, then the reporting and release work | kept |
| `exp3-clean` (`63249104`) | condensed Experiment 3 line, an ancestor of `master` | recorded here; delete from GitHub (P1-19) |
| `frombundle` (`884dd4cb`) | transport branch from a bundle hand-off, an ancestor of `master` | recorded here; delete from GitHub (P1-19) |
| `exp3` (`e162d24b`) | divergent pre-collapse Experiment 3 history. It is the only public home of `exp3-frozen-v1`'s commit and of `ddf86518` (the Exp 2B matched-start confirmation rule) | keep as a labelled archival branch |

## Frozen state vs post-freeze work

Commits after `cd03af9c` are reporting and release work:

* the environment lock;
* report wording, framing and terminology corrections;
* licences;
* the provenance and review records;
* the repository restructure.

None of them changes a frozen artifact, a registered closeout, a canonical JSON
or `src/cota_opt` behaviour. Each framing correction is logged in
`docs/REPORTING_CORRECTIONS.md`. Errors found in frozen artifacts are recorded
as errata, for example `experiments/exp2/EXPERIMENT2_CLOSEOUT_ERRATA.md` and
`experiments/exp7/EXPERIMENT7_CLOSEOUT_ERRATA.md`.

## Report verification

`scripts/verify_report_claims.py` checks the report's headline numbers against
their artifacts. It also checks that the figure manifest's input hashes match
the current files. Status at the cleanup's start: 65/65 claims, figures OK.
