# N3 vs N0 across experiments: a consistency check, not a certification

*Prepared 2026-09-28, while Experiment 6 was running. The check was read-only:
nothing was re-scored and no production artifact was touched. Machine record:
`prep/n3_vs_n0_crossexp_check.json`. Script: `prep/n3_vs_n0_crossexp_check.py`.*

## Verdict

**The two records are admitted by the repository firewall, under both
contracts that allow only network differences.** The firewall computes:

| | value |
|---|---|
| obj(N3), Exp 4A matched record `outputs/exp4_addendum/N3.json` | 2,939,912.5807124916 |
| obj(N0), Exp 5 reference cell `outputs/exp5/cells/N0_J100.json` | 2,945,632.2349138106 |
| **N3 − N0** (firewall `compare`, control N0, treatment N3) | **−5,719.654 (−0.19417% of N0)** |
| Exp 3's certified effect for the same edit (Stage B, its own contract) | −0.18657% |
| comparison id under `EXP4A_MATCHED` (`0f62aeabfa341a98`) | `cmp-aa4c45646faa1d41` |
| comparison id under `EXP5_STRUCTURE` (`2315b87e21123cbc`) | `cmp-b14894a8598436fd` |
| declared differences (both contracts) | `spec.state_digest`, `spec.state_key`, `spec.cardinality`, `spec.members`, `pathset_digest` |

What to call it: **an independent cross-experiment corroboration, or
consistency check**, of the sign and rough size of Experiment 3's N3 effect
under a different instrument (the EXP4N block certifier on the EXP4N common
envelope). It is **not** a new certification, and it proves nothing about
global optimality.

## Field-by-field comparison, read from the records

| dimension | N3 (Exp 4A) | N0 (Exp 5 J100) | same? |
|---|---|---|---|
| evaluator | `same_route`, source `explicit` | `same_route`, source `explicit` | yes |
| λ | 2.0 | 2.0 | yes |
| envelope, exact IEEE-754 fingerprint | `0b46d1abc9a80c80` | `0b46d1abc9a80c80` | yes |
| envelope, rounded digest | `3fd5241db44ca9da` | `3fd5241db44ca9da` | yes |
| enforced = requested, bit-exact | true | true | yes |
| certifier | (8, 3), max 120 rounds, allow_off, `certification_digest 2125984c82b60a83` | same | yes |
| start | Gen1 greedy 20000/1/0, winning start `greedy`, no fallback, no rejection | same | yes |
| seed | 20260825 | 20260825 | yes |
| path-set policy | rebuilt per network per certify call | same | yes (policy). The digests differ, as a network difference requires |
| config_digest | `9325879176f9070c` | `9325879176f9070c` | yes |
| data_digest | `15fa44df0f1075a2` | `15fa44df0f1075a2` | yes |
| code_version / src digest | `src-51dd455d9e1a` / `add5d0002d29aa49` | same | yes |
| runner sha256s (exp45_certify_cell, exp45_contracts, exp5_model_resource, envelope_fingerprint) | identical | identical | yes |
| network | `430aca035c70715b`, `geometry.apply_edits(H.baseline, [edit_from_record(pool[N3])])` | `f0f24936ab06b4ec`, `H.baseline.network` | **no, and this is the treatment** |
| repo_revision | `7c4f67cf` | `4a9bc6b5` | no. The source digest and runner hashes are equal, so the digested code is identical |
| experiment contract the record was written under | EXP4A_MATCHED `0f62aeabfa341a98` | EXP5_FRONTIER `395ee3c960f51935` | **no, see below** |
| rounds / converged | 1 / true | 1 / true | yes |

Components (N3, N0): served demand 16,433.7 vs 16,527.4; generalized cost
1,198,080.5 vs 1,215,043.1; revenue vehicle-hours 2,517.163 vs 2,516.853;
peak proxy (system) 176.408 vs 176.259. **N3 serves 93.7 fewer modeled
trips.** Its λ = 2 objective is lower because generalized cost falls by 1.40%.
This agrees with Exp 3's claim being on the λ = 2 objective and not on
unserved demand.

## What the admission rests on, stated exactly

1. `scripts/exp45_contracts.receipt_for` builds each receipt from what the
   execution recorded about itself. That covers the start audit, the enforced
   exact fingerprint, the hours cap, the convergence flag and rounds, the
   config/data/code digests and the seed. `firewall.admit` and
   `firewall.compare` then refuse any identity or opportunity difference the
   contract does not whitelist. The receipts differ only in network fields and
   the path-set digest.
2. **The record-level experiment contract digest is not a receipt field.** Each
   record carries its own `contract_digest`, and they differ (`0f62…` vs
   `395e…`). `receipt_for` stamps the *judging* contract into the spec, so
   the admission is a retroactive judgement that the two executions were
   equivalent in every contract-relevant dimension. It is not a statement that
   they were run under one preregistered contract. EXP4A_MATCHED and
   EXP5_STRUCTURE agree on every identity field (same `_COMMON` block in
   `scripts/exp45_contracts.py`). They also whitelist the same differences
   (`NETWORK_DIFFERENCES`). They differ only in the `experiment`, `version`,
   `envelope` label and `pool_version` label, which are contract metadata and
   not receipt measurements.
3. The firewall's documented limit applies (D35): it proves the arms differed
   only where permitted. It cannot prove a permitted difference was applied.
   The network difference here is carried by distinct `state_digest`s and
   distinct path-set digests built from distinct constructions, so there is no
   sign of a label-only difference.

## Why this corroborates and does not certify

* **Different contracts.** Exp 3 certified −0.18657% under its own Stage B
  contract: Gen1 exchange search, 5 paired seeds, 20 restarts, and its own
  pinned envelope. The −0.194% here is a single-seed, single-start pair on the
  EXP4N certifier and envelope. The two numbers agree in sign and to within
  about 0.008 percentage points. They are measurements by different
  instruments of related quantities, not one quantity measured twice.
* **Start basin (D39).** Both records certify in **one round** from a
  treatment-specific greedy start. Exp 5 exhibited a start-basin residual of at
  least 1.70% on N4. On N0, 99/99 nested pairs were monotone, which is evidence
  of consistency across N0 cells, not a bound on N0's or N3's residual. The
  0.194% gap is smaller than the N4 residual, so this check cannot rule out that
  a different basin would change its size, or even its sign.
* **No noise-band reading.** D33-B (0.0018970%) is veto-only. The gap is about
  102× the band, which rules out that local-gap artifact and establishes
  nothing further.
* Everything is conditional on LODES commute demand (top 20,000 OD pairs), the
  frozen path model and the same-route waiting model.

## What comes next

Experiment 6's two REF cells (N0 REF and N3 REF) use the same network
constructions, envelope, evaluator and certifier. They add basin/nesting
closure in which each reference takes part. That gives the first N0/N3
comparison made **inside one experiment under one closure procedure**. When Exp
6 closes, compare its REF-cell N3 − N0 against the −0.194% here and against
Exp 3's −0.187%. The protocol (§7) also requires the N3 reference to agree with
the matched Exp 4A result where the mathematical contract is identical, or the
difference to be documented.

## Permitted wording

> Under the EXP4N certifier and common envelope, the Exp 4A N3 record and the
> Exp 5 N0 reference record are firewall-admitted as differing only in the
> network. N3 − N0 = −0.194% on the λ = 2 objective, consistent in sign and
> size with Experiment 3's certified −0.187%. This is a cross-experiment
> consistency check, not a new certification. Both are single greedy-basin
> results.

Not permitted: "N3 is certified better than N0 under EXP4N", "confirms the
optimum", or any served-trips improvement claim. N3 serves fewer modeled trips.
