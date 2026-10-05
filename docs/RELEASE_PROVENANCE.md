# Release provenance

*Keep this file true to what GitHub shows. Last updated 2026-10-05, at the
end of the release cleanup. Nothing here should claim that a tag or branch is public until
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

## Public state after the cleanup (2026-10-05)

Recorded from `git ls-remote origin` after the push:

| ref | object | commit |
|---|---|---|
| `refs/heads/master` | | release/reporting line. Its HEAD is the commit that carries this file; the last commit before this update was `f11f5233`. |
| `refs/heads/exp3` | | `e162d24b` (archival) |
| `refs/tags/research-final` | `78a4355d` | `cd03af9c` |
| `refs/tags/exp3-final-v1` | `f0e6a81e` | `8c2841c4` |
| `refs/tags/exp3-frozen-v1` | `93a67bdb` | `80221f75` |
| `refs/tags/gen1-frozen-v1` | `bb533e7c` | `4b62c728` |
| `refs/tags/pre-exp3-v1` | `c217a45c` | `5b23446e` |
| `refs/tags/pre-exp3-v2` | `34f4f91f` | `9ee905eb` |

`exp3-clean` and `frombundle` were deleted from GitHub (P1-19). Both were
ancestors of `master`, so no commit was lost; their tips are recorded under
Branches below.

## Frozen research state

| item | value |
|---|---|
| frozen research commit | `cd03af9c` (`master`, 2026-10-05). Every contract, digest and canonical artifact verifies against it. |
| freeze tag | `research-final`, an annotated tag (object `78a4355d`) pointing at `cd03af9c`. Public on GitHub since 2026-10-05. |
| canonical results registry | `outputs/CANONICAL_RESULTS_v5.json` (v5; sha256 `e24c3f0e2bf075c1…`). v1–v4 are kept unchanged. |
| Experiment 7 contract | digest `1263bedaebe6a45d` (`outputs/exp7/EXP7_CONTRACT.json`), frozen at `4a2ba9f6` |
| Experiment 7 closeout | `experiments/exp7/EXPERIMENT7_CLOSEOUT.md`, sha256 `27bfc7390c777051…`. It is registered and unchanged; corrections are in `experiments/exp7/EXPERIMENT7_CLOSEOUT_ERRATA.md`. |
| environment snapshot | `docs/research-record/ENVIRONMENT_AT_FREEZE.txt`: a pip freeze of the late-stage development container, Python 3.11.15. No container image is recorded. `requirements-lock.txt` pins the project's dependency closure to these versions, and a `Dockerfile` is provided (its build has not been tested). Status: the Experiment 1 smoke reproduction passed from a clean clone in a fresh venv built from the lock (2026-10-05; `docs/REPRODUCE.md`, "Recorded reproduction"). The full re-solve and the other experiments have not been reproduced on a clean machine. |

## Historical freeze tags

All are public (table above). `exp3-frozen-v1`'s commit is reachable only from
the archival branch `exp3`; the others are reachable from `master`.

The branch `backup-exp3-preclean` (`e733daa8`, 190 commits) holds the
pre-collapse Experiment 3 history. It exists in the author's clone and in the
development container. **It is not on GitHub**, and no public document should
cite it as inspectable. To publish it, run from a clone that has it:

```
git push origin backup-exp3-preclean
```

## Branches

| branch | role | status |
|---|---|---|
| `master` | the public line: research record up to `cd03af9c`, then the reporting and release work | public |
| `exp3` (`e162d24b`) | divergent pre-collapse Experiment 3 history. It is the only public home of `exp3-frozen-v1`'s commit and of `ddf86518` (the Exp 2B matched-start confirmation rule) | public, archival |
| `exp3-clean` (`63249104`) | condensed Experiment 3 line, an ancestor of `master` | deleted from GitHub 2026-10-05 |
| `frombundle` (`884dd4cb`) | transport branch from a bundle hand-off, an ancestor of `master` | deleted from GitHub 2026-10-05 |
| `backup-exp3-preclean` (`e733daa8`) | pre-collapse Exp 3 working history | local only (see above) |

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

`python scripts/verify_report_claims.py --write-numbers` regenerates
`docs/report/REPORT_NUMBERS.json`: every checked value, the artifacts it was
computed from, and the share of the report's numeric text that is checked. The
verifier fails when that file is stale. Status after the P1 work: 65/65 claims,
figures OK, REPORT_NUMBERS current, 326 of 921 numeric tokens in the report
machine-checked. The rest are not yet covered.

CI (`.github/workflows/ci.yml`) runs the tests, this verifier, the figure
check, a CLI/import smoke test and the path-reference and MOVES checks on a
checkout with no raw data. Tests that need the registered raw data skip with
the reason prefix `EXTERNAL_DATA_UNAVAILABLE`.
