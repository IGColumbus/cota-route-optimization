# Experiment 6: closeout preparation done in parallel with the run

*Prepared 2026-09-28 in an isolated git worktree
(`.claude/worktrees/agent-aaf0a40bcee56c576`, branch
`worktree-agent-aaf0a40bcee56c576`, based on `84d96e0d`). Exp 6 was running in
the main checkout at the same time. The Exp 6 protocol, amendment, catalog and
runner were **read** from the main checkout, where they sit at local `master`
`5ef58e57`, two commits ahead of `origin/master`.*

## FINAL 2026-09-29: Exp 6 closed (`EXP6_POLICY_FRONTIER_CERTIFIED`, master `f79227cc`)

Everything was filled in from artifacts read in the main checkout, which was
not written to. The files below are ready to copy into master.

| prep file | target path on master | notes |
|---|---|---|
| `prep/EXPERIMENT6_CLOSEOUT.md` | `EXPERIMENT6_CLOSEOUT.md` | every number cites an artifact; §4–§8 tables are mechanical |
| `prep/exp6_closeout_tables.py` | `scripts/exp6_closeout_tables.py` | then run `python scripts/exp6_closeout_tables.py` on master, which writes `outputs/exp6/EXP6_CLOSEOUT_TABLES.{json,md}` (the prep copies in `prep/out/` carry this worktree's `source_root`) |
| `prep/out/EXP6_CLOSEOUT_TABLES.{json,md}` | (regenerate; see above) | preview only |
| `prep/canonical_results_v4.py` | `scripts/canonical_results_v4.py` | then run `python scripts/canonical_results_v4.py` on master after the closeout is committed. It refuses to overwrite and hashes the closeout |
| `prep/out/CANONICAL_RESULTS_v4.json` | (regenerate on master as `outputs/CANONICAL_RESULTS_v4.json`) | preview built from the master artifacts; `generated_commit` f79227cc; `closeout_sha256` is of the prep closeout |
| `prep/patches/README.patch` (or `prep/edited/README.md`) | `README.md` | Exp 1 fleet fix, Exp 6 section, limitations, test count 890 (collected at f79227cc) |
| `prep/patches/STATE_OF_PLAY.patch` (or `prep/edited/STATE_OF_PLAY.md`) | `STATE_OF_PLAY.md` | Exp 6 lead section and headline bullet; Exp 1 fix; Exp 5 heading; repo-ref note |
| `prep/patches/HANDOFF.patch` | `HANDOFF.md` | Exp 1 fleet provenance resolved |
| `prep/EXPERIMENT7_AMENDMENT_DRAFT.md` | `docs/EXPERIMENT7_AMENDMENT_DRAFT.md` (a draft, not the amendment) | §4 filled from Exp 6 |
| `prep/N3_VS_N0_CROSSEXP_NOTE.md`, `prep/n3_vs_n0_crossexp_check.{py,json}` | `docs/` + `scripts/` + `outputs/` | historical check; superseded in size by the Exp 6 REF comparison |
| `prep/GLOSSARY.md`, `prep/REPRODUCE.md` | `docs/GLOSSARY.md`, `docs/REPRODUCE.md` | |
| `prep/patches/tests_pathset_scope_needs_data.patch` | `tests/…`, `pyproject.toml` | optional; Ian's call |

All three doc patches pass `git apply --check` against the worktree base. At
f79227cc, `README.md`, `STATE_OF_PLAY.md` and `HANDOFF.md` are byte-identical
to that base (checked with `diff -q`).

**Checks against the coordinator's figures** (all verified against the
artifacts):

* Matches:
  * REF corrections: N0 −0.127%, 16,527 → 21,144 served, 50 → 15 OFF; N3
    −0.161%, 16,434 → 21,104, 54 → 17.
  * Negative greedy-only R2_S25 prices: −0.115% / −0.081%.
  * Monotonicity 22/120 → 0/120.
  * REF N3 − N0 = −6,726.35 (−0.229%), 13 admitted, range −0.2286% to
    −0.1525%.
  * Identical-plan groups.
  * Amendment 2: 33 refusals, then 25/25 and 13/13 admitted.
  * Closure end times 06:36:25 (N3) and 07:01:00 (N0).
  * Sentinels 06:43:07–07:24:40.
  * Initial solves 00:09:58–02:53:29.
  * Halt at 00:45:30, resumed 00:59:33 (shard 0) and 01:09:23 (shard 1).
* **Minor timing difference:** preflight artifacts span 22:18:39 → 00:00:55 by
  file mtime, not ~22:15 → 00:05. The contract froze at 00:09:39.
* **Additional findings not in the brief:**
  1. Most basin contamination came from the **reference** being stuck: every
     cell whose initial was final is off by −(REF correction), −0.127 or
     −0.162 pp.
  2. Greedy-only priced R3_SPAN **above** R1_H30, which implies it. That is a
     nesting inversion.
  3. N3's policy prices exceed N0's in every binding cell (+0.038 to
     +0.077 pp).
  4. Closure did **not** improve N3 R6_ADA. It stays in its greedy basin with
     18 OFF, more than REF's 17.
  5. For orientation, and not firewall-admitted: best-known N4 − closed N3 REF
     = +9.28%.

## Update 2026-09-29: reconciled with the frozen Exp 6 artifacts

The prep files now match what was frozen on local `master` `7c08b128`, read
without modifying the main checkout. The frozen facts below are **filled
in**. Only production outcomes remain as `{{placeholders}}`: initial and
closure objectives, passes, basin changes, monotonicity counts, firewall and
sentinel results, costs, and any further empty cells.

| frozen fact | value | source |
|---|---|---|
| contract | `EXP6_CONTRACT.json`, sha256 `5bf1cb82ad8829a8…`, frozen 2026-09-29T00:09:39Z | file |
| firewall | `EXP6_POLICY` `393f45ac10d28cb9` (allowed: `config_digest`); `EXP6_STRUCTURE` `fad14449dc3db7c6` (network fields) | contract |
| source | `b63ae2dba134245e` / `src-17659e64846b` | contract |
| catalog | `e22f2c94c8f53475` | contract, catalog file sha256 |
| nesting | 60 strict pairs, 20 Hasse edges, 0 equal; 0/3,000 numerical counterexamples per network | contract |
| closure | ceiling 8 passes, eps 1e-9 | contract |
| status vocabulary | **11** statuses (adds ORDER_DEPENDENCE, CONVERGENCE, INFEASIBLE_CERTIFIED_PLAN, INSTRUMENTATION) plus the cell status `INFEASIBLE_UNDER_ENVELOPE` | contract, Amendment 1 |
| Amendment 1 | `EXP6_CONTRACT_AMENDMENT_1.json`, sha256 `02d546487d8ff0c8…`. Runners: `exp6_run.py` `55ffbe0b…`, `exp6_analyze.py` `da6792a1…` (verified against disk), `exp6_infeasible_cell.py` `c655dffe…`. `src/cota_opt` and `exp6_cell.py` unchanged | amendment |
| N3 R1_H20 | `INFEASIBLE_UNDER_ENVELOPE`. Minimum-service plan: early 85.29871576 > cap 85.28208333. Every other period and hours are under cap (hours 2,214.52 / 2,517.18) | `outputs/exp6/initial/N3_R1_H20.json` → `proof.usage_vs_caps` |
| equivalence | bit-exact on the final source: N4 J100, N3, N0 J100 | `EXPERIMENT6_D39_PREFLIGHT.md` §A |
| D39 canary | PASS: 3,207,566.4176655654 (J100, 6 rounds), 3,207,230.8312193276 (H110, 5 rounds) | §C |
| D35 | R1/R2/R3/R4/R6 PASS on N0 and N3 | `outputs/exp6/d35/{N0,N3}.json`, contract `preflight.d35` |

What changed in the prep files:

* **`canonical_results_v4.py`.** `SCHEMA` is reconciled with
  `scripts/exp6_analyze.py`, and the script hard-refuses if the analyzer,
  contract or amendment hashes change. It parses the analyzer's real status
  forms (`EXP6_POLICY_FRONTIER_CERTIFIED` / `INCOMPLETE` → refuse /
  `FAILED: …` → registered, not certified, failures kept verbatim).
  `INFEASIBLE_UNDER_ENVELOPE` rows are registered under `empty_feasible_sets`
  as "policy infeasible under the modeled envelope", with no cost. A dry run
  against the real contract and amendment with a synthetic analysis
  (certified and failed variants) built the entry correctly; nothing was
  written.
* **Closeout template.** §1–§3 are filled with the frozen facts. §3.4 covers
  empty feasible sets. The §5 closure table uses the ledger's real action
  names (`RAN`, `REFUSED_INFEASIBLE_UNDER_TARGET`, `REFUSED_BY_CERTIFIER`,
  `SKIPPED_IDENTICAL_PLAN`, `SKIPPED_ALREADY_ATTEMPTED`,
  `SKIPPED_EMPTY_FEASIBLE_SET`). All field names map to `EXP6_ANALYSIS.json`.
* **`REPRODUCE.md`.** It now has the real Exp 6 commands (`exp6_freeze.py`
  catalog/contract, preflight lanes, `exp6_d35.py`, `exp6_run.py`
  plan/initial/closure/sentinels, `exp6_infeasible_cell.py`,
  `exp6_analyze.py`).
* **After-close sequence.** Steps 1–6, 9 and 12 use the real scripts and paths.
* **README/STATE_OF_PLAY patches.** The frozen digests, preflight results and
  the N3 R1_H20 emptiness are filled in. The patches were regenerated and pass
  `git apply --check`. README, STATE_OF_PLAY and HANDOFF on `7c08b128` are
  still byte-identical to the patch base.

Points worth flagging to the main session:
1. `exp6_analyze.py` never emits the bare stop statuses. It emits
   `FAILED: <reasons>`, and reasons such as "firewall policy N0 X" or
   record-check failures carry no `EXP6_*` name. The closeout must quote the
   reasons verbatim. v4 records both `status` and `status_verbatim`.
2. The analysis computes no physical-fleet verdict. Unless a blocking pass is
   added, the closeout must say "not measured" (template §7.7).
3. In the analysis frontier, empty rows carry
   `usage_vs_caps_of_minimum_service_plan` from `record.proof.usage_vs_caps`.
   This works for the N3 R1_H20 record's structure. If a **final** (closure)
   state ever points at a non-proof record, the field will be null.
4. Nothing in the analysis records D39/equivalence/D35. They live in
   `EXP6_CONTRACT.json` → `preflight`, and v4 copies them from there.

## Index of prepared files

| file | part | what it is |
|---|---|---|
| `prep/EXPERIMENT6_CLOSEOUT.template.md` | B | closeout skeleton, all 36 items, `{{…}}` placeholders |
| `prep/canonical_results_v4.py` | C | registry v4 builder, **not run**; refuses without Exp 6 artifacts |
| `prep/patches/README.patch`, `STATE_OF_PLAY.patch`, `HANDOFF.patch` (+ `prep/edited/`) | A, D | publication edits, **not applied**; `git apply --check` passes against `84d96e0d` |
| `prep/n3_vs_n0_crossexp_check.py` / `.json`, `prep/N3_VS_N0_CROSSEXP_NOTE.md` | E | firewall cross-experiment check |
| `prep/patches/tests_pathset_scope_needs_data.patch` (+ `prep/edited/tests/`, `prep/edited/pyproject.toml`) | F3 | fail-loud data guard and an explicit `needs_data` marker, **not applied** |
| `prep/GLOSSARY.md`, `prep/REPRODUCE.md` | F4 | outsider documents |
| `prep/EXPERIMENT7_AMENDMENT_DRAFT.md` | G | draft only |
| `prep/EXP6_AFTER_CLOSE_SEQUENCE.md` | H | post-close steps with commands |

---

## READY NOW

### A. The Exp 1 fleet claim: what 197.0 actually is

**Instrument.** `blocks.fleet_estimate`, called from `scripts/run_diagnostics.py`
and recorded in `outputs/fleet_check_modelB.json` → `candidate_fleet`:

* `baseline_peak_proxy` 197.0, `candidate_peak_proxy` 196.99929, change −0.0007;
* it computes `blocked_peak_proxy = routewise_peak × interlining_factor`;
* `routewise_peak` is the per-route cycle-over-headway sum at the peak period
  (150.73 on the baseline);
* `interlining_factor` = block-derived 197 / 150.73 = **1.307**.

So **the baseline reads 197.0 by construction**. The "197.0 of 197.0" says only
that the plan's routewise cycle-over-headway peak equals the baseline's. That
is a proxy statement, and it uses the factor `FLEET_AND_BLOCKING.md` forbids
using as an exchange rate. The only physical count, 197 from
`blocks.reconstruct` of COTA's published blocks, applies to the **existing
schedule only**.

Separately, Exp 1's solver *was* constrained on the proxy. `config/constraints.yaml`
sets `peak_fleet_by_period: baseline` with `budget_tolerance: 0.0`. Its sha256
`28ce9062…` matches the input record in `outputs/canonical/exp1_final.json` and
the file at Exp 1's commit `f1a05645`, and `frequency._feasible` enforces it per
period. The plan therefore sits inside the baseline's per-period
peak-concurrency proxy by construction. No modified plan was ever blocked, so
the physical fleet is **not measured**.

**Replacement wording** (used in the patches):
> "…using 2,516.5 of 2,517.2 vehicle-hours and without exceeding the baseline's
> per-period **peak-concurrency proxy**, which the solver enforced as a cap.
> That proxy is not a bus count. **The plan's physical fleet requirement has not
> been verified.**"

**Every occurrence found:**

| location | text | action |
|---|---|---|
| `README.md:25-26` | "no additional buses (197.0 peak vehicles against 197.0)" | **patched** (README.patch) |
| `STATE_OF_PLAY.md:89-90` | "−6.65% … at no additional buses" | **patched** |
| `HANDOFF.md:112-118` | "It needs no additional buses … 197.0 against 197.0", after a 2026-09-21 note that left the provenance unresolved | **patched**: annotated with the resolved provenance; heading kept as history |
| `GEN1_FREEZE.md:14` | "at no additional buses (… 197 of 197 peak vehicles)" | not patched. A freeze document, so an additive correction note is recommended |
| `EXPERIMENT2_CLOSEOUT.md:57` | "−6.65% unserved demand at no additional buses" | not patched. Closeout, so an additive note is recommended |
| `ACCEPTANCE.md:317-318` | "197.0 against 197.0 peak vehicles — no additional buses (D18)" | **do not edit**: hashed by `scripts/exp3_freeze.py` and recorded by `gen1_freeze.py`. Correct it by appending a dated amendment |
| `DISCOVERIES.md:737-770` (D18) | "The recommended plan needs no additional buses" | **do not edit** (hashed diary). Append a new entry correcting D18 |
| `outputs/canonical/exp1_final.json` (`resources`, `gates.fleet`) | "197.0 vs 197.0 peak vehicles, no additional buses" | **immutable**. Corrected in v4 `reporting_corrections` |
| `outputs/CANONICAL_RESULTS.json` / `_v2` / `_v3` → `exp1.headline` | "…and 197.0 of 197.0 peak vehicles" | **immutable** (v1 is asserted by `gen1_freeze.py`). Corrected in v4 `reporting_corrections`; exp1 is copied verbatim |
| `scripts/freeze_records.py:148,184` | writer of the above | historical; leave |
| `docs/RELEASE_GUIDELINES_INTAKE.md:74-76` | quotes the claim in order to flag it | correct as is |

Other historical preregistrations reference "the 197.0 peak-vehicle baseline"
as a gate: `EXPERIMENT3_CONTRACT.md:344,388,440`, `EXPERIMENT3_PREFLIGHT.md:75`
and `ACCEPTANCE.md` gate 3-8. That gate was never measurable for a plan
(`contract.py` records the fleet check as NOT RUN). Leave the text; the
glossary explains it.

### A. Other stale or contradictory public statements

1. `README.md:172`: "Experiments 6–7 are unblocked, and each needs its own
   preregistration first." Stale: Exp 6 is preregistered and running.
   **Patched.**
2. `README.md:192`: points readers to `CANONICAL_RESULTS_v2.json`, but v3 is
   current. **Patched** to v4, with v1–v3 kept.
3. `README.md:259` and `README.md:269`: "354 deterministic tests" / "# 354
   tests". **Stale.** There are 861 `test_` functions in the worktree and 866 in
   the main checkout, before parametrization. Other documents record 840, 871
   (+4 skipped) and 882/885 at various times. **Patched** to `{{TEST_COUNT}}`,
   taken from `pytest --collect-only`.
4. `README.md` limitations table: the fleet row covered Exp 4 only. **Patched**
   to add Exp 5 (32/32 UNDECIDABLE) and Exp 1 (never measured), plus a D39 row.
5. `STATE_OF_PLAY.md:768`: the heading "Experiment 5 — resource frontier:
   built, tested, NOT RUN" contradicts the top of the page. **Patched** to
   name it the retired original design.
6. `STATE_OF_PLAY.md:90`: "Untouched by everything that follows". True for
   the objective, false for the fleet wording. **Patched.**
7. `HANDOFF.md` is "Live as of 2026-08-29" with three in-flight runs and says
   "within 0.13 points" / "20–26%", against README's 0.064 / 19%. It is a stale
   document as a whole. **Recommend** a banner marking it historical and
   pointing to STATE_OF_PLAY.
8. **Clone-path contradiction.** `PUSH_TO_GITHUB.md` says to use
   `…\source\repos\…` and that the OneDrive clone is abandoned.
   `STATE_OF_PLAY.md` §Repository says the reverse. **Ian must resolve this**;
   the patches do not.
9. `docs/RELEASE_AND_REPORTING_GUIDELINES.md` G1-b calls for a
   `CANONICAL_ENVELOPE.units.json` sidecar. **It does not exist yet.** It also
   states reproduction "within the `0.0018970%` noise band elsewhere". D33-B is
   a local solver-gap measurement, not a cross-platform floating-point
   tolerance, so it is flagged.
10. `outputs/CANONICAL_RESULTS_v3.json` → `exp5` has no D39 fields (H090 plan
    3,219,614.74, 0.132% better). These appear only in the closeout. The entry
    is immutable; carry them in the v4 `exp6` provenance.
11. No stale claims found in `EXPERIMENT3_CLOSURE.md`,
    `EXPERIMENT4_NORMALIZED_CLOSEOUT.md`,
    `EXPERIMENT4_ORIGINAL_QUESTION_ADDENDUM.md`, `EXPERIMENT5_CLOSEOUT.md`,
    `EXPERIMENT5_PREMISE_RETIREMENT.md`, `FLEET_AND_BLOCKING.md` or
    `ARCHITECTURE_FIREWALL.md` beyond the items above. Each is dated and its
    "unblocks" statements are historical.

### E. N3 vs N0 across experiments: ADMISSIBLE, as a consistency check

* `firewall.compare` admits the pair under **both** `EXP4A_MATCHED`
  (`0f62aeabfa341a98`, comparison `cmp-aa4c45646faa1d41`) and `EXP5_STRUCTURE`
  (`2315b87e21123cbc`, comparison `cmp-b14894a8598436fd`). Declared
  differences: network fields plus `pathset_digest` only.
* **N3 − N0 = 2,939,912.5807 − 2,945,632.2349 = −5,719.65 (−0.194%)**, against
  Exp 3's certified −0.187%.
* Identical in the records: evaluator `same_route`/explicit, λ 2, exact envelope
  `0b46d1abc9a80c80`, rounded `3fd5241db44ca9da`, certifier (8,3)/120/allow_off,
  greedy 20000/1/0 start (no fallback), seed 20260825, config `9325879176f9070c`,
  data `15fa44df0f1075a2`, code `src-51dd455d9e1a`/`add5d0002d29aa49`, and
  runner hashes.
* Different: the record-level contract (exp4a vs exp5), `repo_revision`, and
  the network, which is the treatment.
* **The admission rests on** the receipts from `receipt_for`, which do not
  include the record's own contract digest. It is therefore a retroactive
  judgement of execution equivalence, not a shared preregistration.
* N3 serves **93.7 fewer** modeled trips. The objective gain comes from
  generalized cost.
* Both results are one-round greedy-basin results, and the gap is smaller than
  D39's N4 residual. **This is corroboration, not certification.** Exp 6 REF
  cells give the within-experiment comparison.

### F. Housekeeping

* **Tags and refs** (`git ls-remote origin`, read-only, 2026-09-28):
  * the remote has only `master` (`84d96e0d`), `exp3`, `exp3-clean` and
    `frombundle`, and **no tags**;
  * the container has **no local tags** and no `backup-exp3-preclean`
    (`e733daa86` is not in the object store);
  * `exp3-final-v1` → `8c2841c4` is reachable from `origin/master`;
    `exp3-frozen-v1` → `80221f75` is reachable only from `origin/exp3`;
  * SHAs for `gen1-frozen-v1` and `pre-exp3-v1/v2` are not recorded in the repo;
  * local `master` `5ef58e57` is two commits ahead of `origin/master` (the Exp 6
    commits are unpublished).

  Publish commands are in `EXP6_AFTER_CLOSE_SEQUENCE.md` §Tag publication, to be
  run from Ian's clone.
* **`EXP3_HISTORY_MAP.json`: absent.** It is not in the working tree, not in
  any branch's history (`git log --all -- EXP3_HISTORY_MAP.json` is empty) and
  not anywhere on disk under `/home/claude`. It is cited by `HISTORY_NOTE.md:71`
  and `STATE_OF_PLAY.md:903,962`. **Provenance risk:** the mapping from the 328
  condensed commits to the 2,875 originals cannot be verified from GitHub or
  from the container. Its only possible copies are in Ian's clone or the Sep 1–23
  bundles. Contents were not invented.
* **Tests.** `tests/test_exp4_certify_pathset_scope.py`: 7 of 10 tests pass in
  the worktree (`-m "not slow"`, run 2026-09-28). The other 3 are
  `@pytest.mark.slow`, and their `small_candidate` fixture calls
  `exp4_c10_fixtures._boot()` → `build_harness`, which needs the **gitignored**
  `data/raw` (and `data/cache` for speed). The worktree has no `data/`, so they
  were not run: CPU was reserved for Exp 6.

  The earlier "882/885, 3 failures" is consistent with exactly these 3 failing
  where data is absent. The main session reports the full suite green today
  with data present. The fixture's docstring deliberately refuses
  `importorskip`/`skip` because silent skips once hid 8 tests. Its premise
  ("both inputs are committed") holds for the envelope and pool, but not for
  `data/raw`.

  The prepared patch therefore does **not** skip. It fails with a message
  naming the missing gitignored inputs, and adds a `needs_data` marker so a
  data-less clone deselects the tests visibly with `-m "not needs_data"`.
* **Canonical vs superseded.** The rule, for outsiders:
  * a number is current only if the newest `outputs/CANONICAL_RESULTS_vN.json`
    lists its artifact under `canonical`;
  * anything under `superseded` (e.g. Exp 4 legacy ordering, Model A outputs,
    Exp 2 unkeyed cells, v2's exp5 entry) stays readable and must not be quoted
    quantitatively;
  * registries are additive: vN copies vN−1 verbatim, and corrections to old
    wording go in new keys, never in edits;
  * a closeout document's status line (e.g. `EXP5_MONOTONICITY_FAILURE`) is
    final and is never relabelled.
* **Directory reorganization (recommendation only; do nothing before
  `research-final`).** Adopt the target layout already specified in
  `docs/RELEASE_AND_REPORTING_GUIDELINES.md` (`src/cota_opt/core/`,
  `experiments/expN/`, `docs/research-record/`, `docs/process/`,
  `outputs/canonical/`, `outputs/superseded/`), with three additions:
  * `docs/START_HERE.md` (README → GLOSSARY → REPRODUCE → registry);
  * move the 37 top-level `EXPERIMENT*.md` files (51 top-level `.md` files in
    all, as of `84d96e0d`) into
    `docs/research-record/expN/` **only after** the freeze tag, because
    `exp3_freeze.py`/`gen1_freeze.py` hash top-level paths
    (`DISCOVERIES.md`, `ACCEPTANCE.md`, `OPERATIONS.md`, `METHODOLOGY.md`,
    `ARCHITECTURE_FIREWALL.md`, `EXPERIMENT3_*`, `EXPERIMENT4_DESIGN.md`) and
    moving them breaks `--verify`;
  * leave a stub at each old path pointing to the new one, since provenance
    records cite paths.

---

## DEFERRED UNTIL EXP6 CLOSE

* Fill `EXPERIMENT6_CLOSEOUT.md` from the template (steps 8–11).
* Run `canonical_results_v4.py` (its schema was reconciled 2026-09-29; steps
  12–13). It hard-refuses if artifacts are missing, if `{{` remains in the
  closeout, if v4 exists, if the analysis is `INCOMPLETE`, or if the v3,
  contract, amendment or analyzer hashes differ from the frozen ones.
* Fill the Exp 6 placeholders in the README/STATE_OF_PLAY patches, and
  `{{TEST_COUNT}}`.
* Compare the Exp 6 REF N3 − N0 with −0.194% / −0.187%, and the N3 REF with
  the Exp 4A N3 (protocol §7).
* `REPRODUCE.md` now has the real Exp 6 commands (done 2026-09-29). Still
  missing: an Exp 6 blocking diagnostic and a mechanical closeout checker.

## PUBLICATION FIXES (independent of Exp 6 results; apply after close to avoid churn)

1. Exp 1 fleet wording: README, STATE_OF_PLAY and HANDOFF via the patches.
   Then add dated notes to GEN1_FREEZE.md and EXPERIMENT2_CLOSEOUT.md, a new
   DISCOVERIES entry correcting D18, an ACCEPTANCE amendment, and the v4
   `reporting_corrections` key.
2. Stale test counts (README ×2).
3. README registry pointer v2 → v4.
4. STATE_OF_PLAY Exp 5 heading.
5. Resolve the clone-path contradiction (PUSH_TO_GITHUB vs STATE_OF_PLAY).
6. Push tags, `backup-exp3-preclean` and the Exp 6 commits, and recover
   `EXP3_HISTORY_MAP.json`.
7. Create `CANONICAL_ENVELOPE.units.json` (release G1-b; outstanding).
8. Mark HANDOFF.md as historical.

## EXP7 DRAFT CONSEQUENCES

* **The Exp 7 base text is not in the repository.** The 23 Sep protocol's Exp 7
  section (F1–F6, the five dimensions, the Class A matrix with A8) is cited but
  not committed. It must be committed verbatim before any amendment.
* New F4: the robustness of the **negative** N4 result against N3 and N0. The
  old `ordering` claim is retired as false at baseline, and `beats_noise` is
  restated.
* New F6: the N0/N3 policy price under Exp 6 closure.
* D39 safeguards are binding (7 items). The proposed analogue for non-nested
  sensitivity dimensions is cross-seeding closure, since feasible sets are
  identical across demand/λ/waiting/path levels.
* Twelve other stale assumptions are listed in the draft §3, including gate
  4-12 and the wider OD universe owed from Exp 4A, the waiting- and path-model
  conditionality of F4, the re-optimized λ sweep, and the blocking materializer
  defect that blocks any fleet verdict.

## CONFLICT CHECK

* **Main checkout: nothing modified.** It was only read (files and directory
  listings). No git command was run against it. A `git merge --ff-only master`
  inside the worktree was refused by the permission system and not retried, so
  the worktree branch stays at `84d96e0d` and Exp 6 files were read from the
  main checkout path.
* **Exp 6 production artifacts, source, contracts, outputs, checkpoints: not
  touched.** No write to `outputs/exp6/`, `src/cota_opt/`, `scripts/`, any
  contract JSON or any registry. `CANONICAL_RESULTS_v4.json` was **not**
  written, and `prep/canonical_results_v4.py` was **not** run.
* **No optimization run started and no process killed.** The lane pids 844/845
  were read, not signalled. Compute used: one read-only firewall script, which
  parses two JSON records and runs no solver, plus 7 fast tests of one file.
* **Patches not applied** to README/STATE_OF_PLAY/HANDOFF/tests/pyproject; they
  were only checked with `git apply --check`.
* **No push.** `git ls-remote` was read-only. Commits exist only on
  `worktree-agent-aaf0a40bcee56c576`.
* Exp 5's status and D39 are not reinterpreted anywhere.
* **Exp 6 numbers.** Only frozen preflight facts appear: the equivalence
  canaries, the D39 canary objectives, the D35 verdicts, and the Amendment 1
  proof values for N3 R1_H20. Every production outcome is still a
  `{{placeholder}}`. Partial initial records existed on 2026-09-29 and were
  not quoted.
* **2026-09-29 update.** The main checkout (`7c08b128`) was read only:
  contract, amendment, catalog, preflight and D35 JSON, the N3 R1_H20 record,
  and the Exp 6 scripts. No write, no git command there, no process touched.
  CPU use was a few JSON reads, a dry run of the v4 entry builder in memory,
  and `git apply --check`.
