# Experiment 6 — modeled price of policy constraints on N0 and N3: CLOSEOUT

**Status: `EXP6_POLICY_FRONTIER_CERTIFIED`**
(`outputs/exp6/EXP6_ANALYSIS.json`, sha256 `b96aca0d71996472…`, `failures: []`).

Under the frozen Model B demand/evaluation model, the EXP4N common envelope,
λ = 2 and the declared basin-closure search, every acceptance gate passed:

| gate | result |
|---|---|
| records checked | 54/54 |
| post-closure monotonicity violations | 0 of 120 nested pairs |
| reference closure | clean |
| closure fixed point | both networks, in 3 of 8 passes |
| firewall, EXP6_POLICY | 25/25 admitted |
| firewall, EXP6_STRUCTURE | 13/13 admitted |
| sentinels | 4/4 bit-exact |

One cell, **N3 R1_H20**, has an empty feasible set: **policy infeasible under
the modeled envelope** (Amendment 1).

The most important finding is not a policy price. **The λ = 2 objective is flat
across very different plans on N0 and N3 too, not only on N4.** Closure moved
both reference cells to a plan with the same objective to within 0.13–0.16%.
That plan serves about 4,600 more modeled trips, runs 35–37 fewer OFF
route-periods, and costs about 45% more generalized cost. The single-greedy-start
plans behind Exp 4A's N3 and Exp 5's N0 J100 were therefore not the best-known
plans under the EXP4N envelope. D39 is a property of this objective and
certifier, not of the greenfield network.

Completed 2026-09-29. Governing text:
* `EXPERIMENT6_PROTOCOL.md`;
* `EXPERIMENT6_D39_AMENDMENT.md`;
* `EXPERIMENT6_CONSTRAINT_CATALOG.md`;
* `EXPERIMENT6_D39_PREFLIGHT.md`;
* `EXPERIMENT6_AMENDMENT_1.md` (empty feasible sets);
* `EXPERIMENT6_AMENDMENT_2.md` (receipt start encoding).

Tables in §4–§8 are generated mechanically by `scripts/exp6_closeout_tables.py`
(→ `outputs/exp6/EXP6_CLOSEOUT_TABLES.{json,md}`) from the artifacts cited.
No number was typed by hand.

## 1. Identity and freeze

| item | value | source |
|---|---|---|
| contract | version 6.0, frozen 2026-09-29T00:09:39Z, file sha256 `5bf1cb82ad8829a8…` | `outputs/exp6/EXP6_CONTRACT.json` |
| firewall contracts | `EXP6_POLICY` `393f45ac10d28cb9` (within a network, allowed difference `config_digest` only); `EXP6_STRUCTURE` `fad14449dc3db7c6` (allowed: `state_digest`, `state_key`, `cardinality`, `members`, `pathset_digest`) | contract → `firewall` |
| Amendment 1 | `INFEASIBLE_UNDER_ENVELOPE` cell status, proven on the production path for pure-R1 cells only. Written 2026-09-29T00:59:33Z after 7/28 initial cells. File sha256 `02d546487d8ff0c8…` | `EXP6_CONTRACT_AMENDMENT_1.json` |
| Amendment 2 | receipt encoding: `starts_attempted` = procedure (identical for every cell); winning basin moved to `winning_start` (OUTCOME). Written 2026-09-29T07:34:30Z. File sha256 `35462172b30c6363…`; `exp6_contracts.py` `80085413ac3d72b5` | `EXP6_CONTRACT_AMENDMENT_2.json`, §6 |
| source / evaluator | `src-17659e64846b` / `b63ae2dba134245e`, Model B `same_route`, λ = 2. Runners as frozen in the contract and both amendments (`exp6_run.py` `55ffbe0b…`, `exp6_analyze.py` `da6792a1…`, `exp6_infeasible_cell.py` `c655dffe…`, `exp6_cell.py` `79c60052…` unchanged) | contract → `code`; amendments |
| production cells | 28 planned. **27 certified**, 1 `INFEASIBLE_UNDER_ENVELOPE` (N3 R1_H20). Record checks pass on 54/54 certified records (27 initial + 27 final) for code, runner, envelope, policy, feasibility and convergence, plus one common base config | `EXP6_ANALYSIS.record_checks`, `.empty_feasible_sets` |
| N0 | `cota_existing_local_geometry\|N0`, `f0f24936ab06b4ec` | contract → `networks` |
| N3 | `exp3\|add_stop-010#22c4c35ac5b2`, `430aca035c70715b`. N3's own baseline plan overruns the envelope, so route 001 is trimmed in 5 periods (e.g. am_peak 15 → 20 min) to form the base | contract; `outputs/exp6/d35/N3.json` → `base_plan_trims_to_fit_envelope` |
| envelope | EXP4N common 100/100: rounded `3fd5241db44ca9da`, exact `0b46d1abc9a80c80`, hours 2,517.1833; six peak-proxy caps (proxy, **not fleet**); tolerance 0 | contract → `envelope` |
| certifier | `exp4_certify.certify` (8, 3), max 120 rounds, convergence mandatory, `2125984c82b60a83`. Base start: Gen1 greedy 20000/1/0 under the cell's own constraints | contract → `certifier` |
| catalog | `e22f2c94c8f53475` | contract → `catalog` |
| nesting | 60 strict pairs (120 over two networks), 20 Hasse edges, 0 equal pairs; 0/3,000 numerical counterexamples per network | contract → `nesting` |
| closure | ceiling 8 passes, improvement eps 1e-9, no cross-network sharing | contract → `closure` |

## 2. Regimes

**Included**, all **study safeguards**, none anchored to a documented COTA value:
* R1 max-headway floor, H = 60/30/20;
* R2 OFF-share cap, s = 0.25/0.10/0.05;
* R3 span (period granularity);
* R4 coverage, c = 0.05/0.01/0.00;
* R6 ¾-mile (1,207.008 m) area preservation;
* bundles B1 (R2 0.10 + R3 + R6) and B2 (R4 0.01 + R3).

FTA C 4702.1B requires such standards but prescribes no values. R6 borrows 49
CFR 37.131(a)(1)'s distance, which binds paratransit and does not bind
fixed-route preservation.

**Excluded:**
* R5 is **`UNIMPLEMENTABLE_WITH_CURRENT_DATA`** in its Title VI form, and the
  generic form was not implemented before the freeze.
* R7: no authoritative COTA frequent-network definition.
* R2 s = 0 is identical to R1 H = 60.
* The "COTA-compliant" combined regime was **not run** (no anchor).
Source: `EXPERIMENT6_CONSTRAINT_CATALOG.md`.

## 3. Preflight (2026-09-28 22:18 – 2026-09-29 00:01 UTC, by artifact mtimes)

* **Default-path equivalence: PASS, bit-exact on the final source.**
  * N4 J100: 3223885.947526011, `898b95fd93c33414`, 21 rounds, all trajectory
    objectives, 1,029 block enumerations.
  * N3: 2939912.5807124916, `28135d0fa655e6e1`.
  * N0 J100: 2945632.2349138106, `c4591ff0f6e2d8ad`.

  Sources: `EXPERIMENT6_D39_PREFLIGHT.md` §A;
  `outputs/exp6/preflight/final_equivalence/`.
* **D39 canary: PASS.** The anchor is Exp 5 N4 H090 (`841d596570f1217f`,
  3,219,614.742641489).
  * Under N4 J100 it certifies at **3,207,566.4176655654** (`d319bb5f4d7a6c2b`,
    6 rounds), 0.506% better than EXP4N's certified value.
  * Under N4 H110 it certifies at **3,207,230.8312193276** (`a29f7016d837d1f7`,
    5 rounds).

  Both results are ≤ the anchor and mutually monotone. One run was lost to a
  post-processing serializer bug and repeated (`d39/ERROR.…`). Source:
  `EXPERIMENT6_D39_PREFLIGHT.md` §C, E; `outputs/exp6/preflight/d39/`.
* **D35: PASS**, R1/R2/R3/R4/R6 on N0 and N3 (`outputs/exp6/d35/{N0,N3}.json`,
  `all_pass: true`). Each regime admits at its measured value and refuses one
  step tighter:
  * R1: N0 max headway above baseline 20 min (001 am_peak), N3 24 (002
    am_peak); refused at measured − 0.5.
  * R2: 3 of 173 OFF; ⌊s·|B|⌋ = m admits, m − 1 refuses.
  * R3: span key 001|early off.
  * R4: 1 lost stop-period of 16,855 on N0 and 16,859 on N3.
  * R6: nearest served stop 266.44 m, radius d*+1 m admits and d*−1 m
    refuses.

  Two earlier D35 files are kept as `SUPERSEDED.*`.

## 4. Empty feasible set — N3 R1_H20 (Amendment 1)

The minimum-service plan M (every route-period at its longest admissible rung)
is **refused** under the envelope. It is **admitted with zero policy violation**
when the envelope is relaxed ×10. Its usage against the caps is:

| resource | M uses | cap | over? |
|---|---|---|---|
| **early peak proxy** | **85.29871576** | **85.28208333** | **yes** |
| hours | 2,214.52 | 2,517.18 | no |
| am_peak / midday / pm_peak / evening | 139.56 / 135.21 / 150.80 / 125.26 | 162.01 / 159.17 / 176.49 / 140.19 | no |
| owl | 35.5307 | 35.5574 | no |

Source: `outputs/exp6/initial/N3_R1_H20.json` → `proof`; `EXP6_ANALYSIS.frontier`.

Every resource strictly decreases in headway, so no admissible plan uses less.
The reading is **policy infeasible under the modeled envelope**, and the margin
is 0.0166 proxy units in one period. That is a result, not a failure. The cell
has no plan, no receipt and **no finite policy cost**. Closure receipted 6
transfers into or out of it as `SKIPPED_EMPTY_FEASIBLE_SET`. N0 R1_H20 is
feasible (§7), so this asymmetry is a property of N3's resource use: the added
stop lengthens route 001.

The start-failure trace is kept at
`outputs/exp6/initial/TRACE.N3_R1_H20.certifier_start_error.json`.

## 5. Initial (independent greedy) solves, and initial monotonicity

27 cells were certified from their own treatment-specific Gen1 greedy start
(`exp6_run.py initial`, 2 shards). Per-cell values are in the §8 tables
(columns "initial obj", "served init", "OFF init").

**The initial REF cells reproduce the historical records bit-for-bit**:
* N3 REF initial = `outputs/exp4_addendum/N3.json` (2939912.5807124916,
  `28135d0fa655e6e1`);
* N0 REF initial = `outputs/exp5/cells/N0_J100.json` (2945632.2349138106,
  `c4591ff0f6e2d8ad`).

That satisfies protocol §7 (`outputs/exp6/EXP6_CLOSEOUT_TABLES.json` →
`history_check`).

**Initial-greedy monotonicity: 22 of 120 nested pairs violate** (11 on N0, 11
on N3). The largest are:
* N3 R1_H60 → R3_SPAN +0.2067%;
* N0 R1_H60 → R3_SPAN +0.1798%;
* N3 B2 → R3_SPAN +0.1645%.

It is reported, not gated (`EXP6_ANALYSIS.monotonicity_initial`). Under the Exp
5 design this would have been a monotonicity failure on N0 and N3 as well.

## 6. Nesting closure

`exp6_run.py closure --network <net>`; receipts in
`outputs/exp6/closure/closure_ledger_{N0,N3}.jsonl`; best plan per cell in
`closure_state_{N0,N3}.json`.

| | N0 | N3 |
|---|---|---|
| passes completed / ceiling | **3 / 8**, fixed point | **3 / 8**, fixed point |
| receipts | 120 | 120 |
| RAN (anchored certifications) | 24 | 21 |
| REFUSED_INFEASIBLE_UNDER_TARGET | 40 | 37 |
| SKIPPED_IDENTICAL_PLAN | 32 | 34 |
| SKIPPED_ALREADY_ATTEMPTED | 24 | 22 |
| SKIPPED_EMPTY_FEASIBLE_SET | 0 | 6 |
| REFUSED_BY_CERTIFIER | 0 | 0 |
| cells that changed basin | **9** of 14 | **8** of 13 |
| found in pass 1 / pass 2 | 8 / 1 (R3_SPAN) | 7 / 1 (R3_SPAN) |

Source: `EXP6_ANALYSIS.closure`; event logs `outputs/exp6/run/closure_{N0,N3}.events.log`.

The largest initial → closure corrections:
* N3 R2_S10 −0.278%, via R2_S05;
* N0 R2_S10 −0.251%, via R2_S25;
* N3 R3_SPAN −0.206%, via B1;
* N0 R4_C05 −0.198%, via R4_C01;
* N0 R3_SPAN −0.180%, via B1;
* **N3 REF −0.161%** and **N0 REF −0.127%**, both via R2_S25.

**Post-closure monotonicity: 0 of 120 violations.** **Reference closure: no
violations**; no policy cell beats its REF.

**Amendment 2** (the firewall receipt start encoding). The first analysis run
had every gate passing except the firewall, which refused 35 comparisons. Every
refusal named one dimension only: `starts_attempted`. The receipt had put the
*winning* basin into that opportunity field, so cells given the identical
procedure looked as if they had different opportunity. Per protocol §11,
opportunity is the procedure: same base start, closure algorithm, pass ceiling,
adjacency, certifier and convergence rule.

The correction:
* `starts_attempted` = `start_names + ["exp6_nesting_closure"]`, identical for
  every cell;
* the winning basin goes in `winning_start` (`Sem.OUTCOME`).

After it, **25/25 policy** comparisons (declared: `spec.config_digest` only) and
**13/13 structure** comparisons (declared: the network fields and
`pathset_digest`) were admitted. No record, plan, objective, ledger or contract
digest changed. The first output is kept as
`outputs/exp6/SUPERSEDED.EXP6_ANALYSIS.first_run_receipt_start_encoding.json`.
Source: `EXPERIMENT6_AMENDMENT_2.md`.

**Sentinels: 4/4 PASS.** N3 R4_C01, N0 R2_S10, N3 REF and N0 REF re-run in
reversed order are equal in objective, plan digest and rounds
(`outputs/exp6/sentinels/`, `EXP6_ANALYSIS.sentinels`, `sentinels.events.log`).

## 7. Finding 1 — a flat, multi-basin objective on N0 and N3

| | initial REF (greedy basin) | closed REF | change |
|---|---|---|---|
| **N0** objective | 2,945,632.23 | 2,941,892.37 | **−0.127%** |
| N0 served (of 30,949 modeled trips) | 16,527 | 21,144 | +4,617 |
| N0 OFF route-periods | 50 | 15 | −35 |
| N0 generalized cost | 1,215,043 | 1,765,256 | +45.3% |
| **N3** objective | 2,939,912.58 | 2,935,166.03 | **−0.161%** |
| N3 served | 16,434 | 21,104 | +4,670 |
| N3 OFF route-periods | 54 | 17 | −37 |
| N3 generalized cost | 1,198,081 | 1,753,773 | +46.4% |

Sources: `EXP6_ANALYSIS.frontier`, `initial/{N0,N3}_REF.json`, and the closed
records `closure/N0_REF__from_R2_S25__aed848588abad24d.json` and
`closure/N3_REF__from_R2_S25__fdec5c5475c73736.json`.

What this establishes, and what it does not:

* **The Exp 4A N3 record and the Exp 5 N0 J100 record are not the best-known
  plans under the EXP4N envelope.** The mathematical contract is the same: the
  Exp 6 REF has no policy and the same envelope, evaluator and certifier, and
  its initial solve reproduces those records bit-exactly. Closure found feasible
  plans 0.161% and 0.127% better. Those records remain exact historical records
  of their own contracts. They are **not reopened**, and Δ43 (+9.66%) stays the
  admitted Exp 4A figure.
* **D39 is not specific to N4.** Exp 5 saw it as monotonicity failures on N4
  only, because N0 certified in one round from greedy. On N0 and N3 the greedy
  basin is block-locally optimal (one round) and still 0.13–0.16% from a plan
  that closure reaches.
* **The objective does not identify served demand.** Near-equal λ = 2
  objectives are attained by plans that differ by about 4,600 served trips
  (+28%) and about 45% in generalized cost. Any served-trips or GC figure from a
  single-basin certification can move by that much at almost no objective cost.
  That applies to Exp 4A's "N4 serves 31.5% fewer trips" and to Exp 5's served
  column. **This does not overturn the objective comparisons.** It says the
  secondary metrics are basin-dependent, and they should be quoted only with
  that caveat.
* Exp 1–3 used the Gen1 exchange search, not this certifier, and nothing here
  measures their basin sensitivity. It is not extended to them.

## 8. Per-cell results, initial vs closure-adjusted

Columns:
* greedy-only cost = initial cell − initial REF (% of initial REF);
* closed cost = closed cell − closed REF (% of closed REF);
* contamination = greedy-only % − closed % (percentage points).

Source: `EXP6_ANALYSIS.frontier`, `closure_state_<net>.json`,
`outputs/exp6/EXP6_CLOSEOUT_TABLES.md`.

### N0

| cell | initial obj | closed obj | init→closed | greedy-only cost | **closed cost** | contamination (pp) | winning basin | final plan | served init→closed | OFF |
|---|---|---|---|---|---|---|---|---|---|---|
| REF | 2,945,632.23 | 2,941,892.37 | −0.127% | 0 | **0** | 0 | anchor ← R2_S25 | `aed84858…` | 16,527 → 21,144 | 50 → 15 |
| R1_H60 | 2,956,071.29 | 2,956,071.29 | 0 | +0.354% | **+14,178.92 (+0.482%)** | −0.128 | greedy | `859272a3…` | 21,208 | 0 |
| R1_H30 | 2,958,795.13 | 2,958,795.13 | 0 | +0.447% | **+16,902.75 (+0.575%)** | −0.128 | greedy | `60f0b38c…` | 21,184 | 0 |
| R1_H20 | 2,968,717.08 | 2,968,717.08 | 0 | +0.784% | **+26,824.71 (+0.912%)** | −0.128 | greedy | `f631e3af…` | 21,094 | 0 |
| R2_S25 | 2,942,231.97 | 2,941,892.37 | −0.012% | **−0.115%** | **0** | −0.115 | anchor ← R2_S10 | `aed84858…` (= REF) | 18,395 → 21,144 | 39 → 15 |
| R2_S10 | 2,949,292.57 | 2,941,892.37 | −0.251% | +0.124% | **0** | +0.124 | anchor ← R2_S25 | `aed84858…` (= REF) | 20,303 → 21,144 | 17 → 15 |
| R2_S05 | 2,948,128.77 | 2,948,128.77 | 0 | +0.085% | **+6,236.40 (+0.212%)** | −0.127 | greedy | `2f72d1b9…` | 21,140 | 8 |
| R3_SPAN | 2,961,387.50 | 2,956,071.29 | −0.180% | +0.535% | **+14,178.92 (+0.482%)** | +0.053 | anchor ← B1 | `859272a3…` (= R1_H60) | 17,058 → 21,208 | 25 → 0 |
| R4_C05 | 2,954,931.66 | 2,949,074.50 | −0.198% | +0.316% | **+7,182.13 (+0.244%)** | +0.072 | anchor ← R4_C01 | `a9a538d8…` | 19,556 → 20,501 | 22 → 14 |
| R4_C01 | 2,954,482.00 | 2,954,482.00 | 0 | +0.300% | **+12,589.63 (+0.428%)** | −0.128 | greedy | `b1de91e0…` | 20,546 | 9 |
| R4_C00 | 2,956,115.39 | 2,956,071.29 | −0.001% | +0.356% | **+14,178.92 (+0.482%)** | −0.126 | anchor ← R1_H60 | `859272a3…` (= R1_H60) | 21,205 → 21,208 | 0 |
| R6_ADA | 2,954,998.11 | 2,954,847.73 | −0.005% | +0.318% | **+12,955.36 (+0.440%)** | −0.122 | anchor ← R4_C00 | `b517f673…` | 20,015 → 21,198 | 16 → 2 |
| B1 | 2,959,465.82 | 2,956,071.29 | −0.115% | +0.470% | **+14,178.92 (+0.482%)** | −0.012 | anchor ← R1_H60 | `859272a3…` (= R1_H60) | 20,169 → 21,208 | 7 → 0 |
| B2 | 2,956,692.06 | 2,956,071.29 | −0.021% | +0.375% | **+14,178.92 (+0.482%)** | −0.107 | anchor ← R1_H60 | `859272a3…` (= R1_H60) | 20,521 → 21,208 | 6 → 0 |

### N3

| cell | initial obj | closed obj | init→closed | greedy-only cost | **closed cost** | contamination (pp) | winning basin | final plan | served init→closed | OFF |
|---|---|---|---|---|---|---|---|---|---|---|
| REF | 2,939,912.58 | 2,935,166.03 | −0.161% | 0 | **0** | 0 | anchor ← R2_S25 | `fdec5c54…` | 16,434 → 21,104 | 54 → 17 |
| R1_H60 | 2,950,532.57 | 2,950,532.57 | 0 | +0.361% | **+15,366.54 (+0.524%)** | −0.162 | greedy | `591eebe7…` | 21,234 | 0 |
| R1_H30 | 2,953,789.49 | 2,953,789.49 | 0 | +0.472% | **+18,623.46 (+0.634%)** | −0.162 | greedy | `d5f131ff…` | 21,216 | 0 |
| R1_H20 | — | — | — | — | **policy infeasible under the modeled envelope** | — | — | — | — | — |
| R2_S25 | 2,937,538.03 | 2,935,166.03 | −0.081% | **−0.081%** | **0** | −0.081 | anchor ← R2_S10 | `fdec5c54…` (= REF) | 18,414 → 21,104 | 39 → 17 |
| R2_S10 | 2,943,352.37 | 2,935,166.03 | −0.278% | +0.117% | **0** | +0.117 | anchor ← R2_S05 | `fdec5c54…` (= REF) | 20,311 → 21,104 | 17 → 17 |
| R2_S05 | 2,942,494.16 | 2,942,494.16 | 0 | +0.088% | **+7,328.13 (+0.250%)** | −0.162 | greedy | `561444f6…` | 21,169 | 8 |
| R3_SPAN | 2,956,630.56 | 2,950,532.57 | −0.206% | +0.569% | **+15,366.54 (+0.524%)** | +0.045 | anchor ← B1 | `591eebe7…` (= R1_H60) | 17,093 → 21,234 | 25 → 0 |
| R4_C05 | 2,949,618.18 | 2,944,578.35 | −0.171% | +0.330% | **+9,412.33 (+0.321%)** | +0.009 | anchor ← R4_C01 | `4e49377a…` | 19,570 → 21,167 | 23 → 6 |
| R4_C01 | 2,951,441.29 | 2,949,169.08 | −0.077% | +0.392% | **+14,003.05 (+0.477%)** | −0.085 | anchor ← R4_C00 | `a3134075…` | 20,505 → 21,210 | 10 → 1 |
| R4_C00 | 2,950,532.57 | 2,950,532.57 | 0 | +0.361% | **+15,366.54 (+0.524%)** | −0.162 | greedy (already = R1_H60 plan) | `591eebe7…` (= R1_H60) | 21,234 | 0 |
| R6_ADA | 2,949,413.88 | 2,949,413.88 | 0 | +0.323% | **+14,247.86 (+0.485%)** | −0.162 | greedy | `0afda9bb…` | 19,987 | 18 |
| B1 | 2,954,543.22 | 2,950,532.57 | −0.136% | +0.498% | **+15,366.54 (+0.524%)** | −0.026 | anchor ← R1_H60 | `591eebe7…` (= R1_H60) | 20,121 → 21,234 | 9 → 0 |
| B2 | 2,951,774.42 | 2,950,532.57 | −0.042% | +0.403% | **+15,366.54 (+0.524%)** | −0.120 | anchor ← R1_H60 | `591eebe7…` (= R1_H60) | 20,473 → 21,234 | 8 → 0 |

Closed policy costs match the firewall-admitted EXP6_POLICY effects
(`EXP6_ANALYSIS.firewall.policy`, 25/25 admitted).

### 8.1 Finding 2 — how much single-start basin selection contaminated the price

Contamination (greedy-only − closed) runs from **−0.162 to +0.124 percentage
points**. That is comparable to the smallest non-zero prices (R2_S05 +0.21% on
N0, +0.25% on N3) and about a sixth of the largest (R1_H20 on N0, +0.91%). It
has two sources:

1. **The reference was itself stuck.** For every cell whose initial solve was
   already its final plan, contamination is ≈ −(REF's own correction): −0.127
   to −0.128 pp on N0 and −0.162 pp on N3. That includes all R1 cells, R2_S05,
   R4_C01 on N0, and R4_C00 and R6_ADA on N3. The greedy-only design would have
   **understated** those prices by that much, because it subtracted a
   poorly-solved reference.
2. **The policy cell was stuck.** R2_S10 (+0.124 / +0.117 pp), R4_C05 (+0.072 /
   +0.009) and R3_SPAN (+0.053 / +0.045) were **overstated** by greedy-only.

**Two greedy-only prices were negative**, an impossible "free policy": R2_S25
at **−0.115% (N0)** and **−0.081% (N3)**. The constraint is a subset of REF's
feasible set, so it cannot beat REF. Closure removed both: each converged to
REF's own plan at exactly zero cost.

The greedy-only ranking also contradicts the nesting. R1_H30 implies R3_SPAN,
so R3_SPAN can never cost more. Yet greedy-only prices R3_SPAN (+0.535% on N0,
+0.569% on N3) **above** R1_H30 (+0.447% / +0.472%). Closed, R3_SPAN costs the
same as R1_H60 (+0.482% / +0.524%).

### 8.2 Identical final plans — what they mean

On each network, two groups of cells finish on one plan (`closure_state_*.json`):

* **R2_S25, R2_S10 = REF** (`aed84858…` on N0, `fdec5c54…` on N3). The closed
  REF plan has 15 (N0) or 17 (N3) baseline-served route-periods OFF. That is
  under ⌊0.10·173⌋ = 17 in both cases, so the plan is feasible under R2 at
  10% and 25%. **R2 at s ≥ 0.10 does not bind at the best-known unconstrained
  plan.** Its closed cost is exactly zero, a direct consequence of containment
  and not an estimate. R2 at 5% (⌊8.65⌋ = 8 OFF allowed) does bind.
* **R3_SPAN, R4_C00, B1, B2 = R1_H60** (`859272a3…` on N0, `591eebe7…` on N3).
  R1_H60 implies each of these, so its plan is feasible in all of them. The
  plan has **0 OFF route-periods**. It is also the best plan closure found in
  each of the four looser cells. The precise statement is: **under the declared
  closure, relaxing R1_H60 to R3, R4 at c = 0, B1 or B2 bought nothing.**

  Two readings fit the evidence and this experiment cannot separate them:
  * those feasible sets contain no better plan, so each constraint in effect
    forces "keep everything ON" at this envelope; or
  * better plans exist in them that no transferred anchor reached. R3_SPAN's
    greedy start sat in a much worse basin (25 OFF, +0.535%), so the search
    does not reach them unaided.

  It is **not** shown that span preservation "costs the same as" a 60-minute
  headway floor in any sense stronger than this.

## 9. Finding 3 — N3 against N0 at matched policy (EXP6_STRUCTURE, 13/13 admitted)

| cell | closed N3 − N0 | % of N0 | same pair, greedy-only (raw) |
|---|---|---|---|
| **REF** | **−6,726.35** | **−0.2286%** | −0.1942% |
| R2_S25, R2_S10 (= REF plans) | −6,726.35 | −0.2286% | −0.1595%, −0.2014% |
| R2_S05 | −5,634.61 | −0.1911% | −0.1911% |
| R1_H60, R3_SPAN, R4_C00, B1, B2 (= R1_H60 plans) | −5,538.73 | −0.1874% | −0.1874% (R1_H60) |
| R6_ADA | −5,433.85 | −0.1839% | −0.1890% |
| R4_C01 | −5,312.92 | −0.1798% | −0.1029% |
| R1_H30 | −5,005.64 | −0.1692% | −0.1692% |
| R4_C05 | −4,496.15 | −0.1525% | −0.1798% |
| R1_H20 | not comparable: empty on N3 | — | — |

Source: `EXP6_ANALYSIS.firewall.structure`. Greedy-only is computed from
`frontier.initial_objective`, is not firewall-admitted, and is shown for
orientation only.

* **N3 is better than N0 in every one of the 13 comparable cells**, by
  **0.1525% to 0.2286%**.
* The REF comparison moved from **−0.194%** (greedy-only; identical to the
  cross-experiment Exp 4A/Exp 5 check) to **−0.229%** closure-adjusted. Exp 3's
  certified effect was −0.187% under its own contract.
* The sign is stable across both procedures and all admitted policies. The size
  moves with basin by several hundredths of a percent.
* Policy prices are slightly **higher on N3** in every comparable cell. The
  difference ranges from +0.038 pp (R2_S05) to +0.077 pp (R4_C05), and is 0 for
  the cells that equal REF. So N3's advantage over N0 narrows under every
  binding safeguard, but never reverses.
* For orientation only, and not a firewall comparison: using the best-known N4
  plan from the D39 preflight (3,207,566.42 under the same envelope), N4 − N3
  closed REF = +272,400.39 (+9.28% of N3), and N4 − N0 closed REF = +265,674.05
  (+9.03% of N0). The official Δ43 remains +9.66%.

## 10. Finding 4 — modeled policy costs (closure-adjusted)

Ordered by N0 closed cost:

| safeguard | N0 | N3 |
|---|---|---|
| R2 s = 0.25, 0.10 | 0 (does not bind at the best-known REF plan) | 0 |
| R2 s = 0.05 | +0.212% | +0.250% |
| R4 c = 0.05 | +0.244% | +0.321% |
| R4 c = 0.01 | +0.428% | +0.477% |
| R6 ¾-mile | +0.440% | +0.485% |
| R1 H = 60; R3; R4 c = 0; B1; B2 (one shared plan) | +0.482% | +0.524% |
| R1 H = 30 | +0.575% | +0.634% |
| R1 H = 20 | +0.912% | **infeasible under the modeled envelope** |

These are modeled objective differences in λ = 2 objective units, under the
declared closure. **They are not dollars, buses or fleet.** Every binding
closed plan except N3 R6_ADA has fewer OFF route-periods than its REF. The R1
family, R3, R4 at c = 0, B1 and B2 run 0 OFF, against 15 (N0) and 17 (N3) at
REF. N3 R6_ADA runs 18.

## 11. Physical fleet — UNDECIDABLE, not run

There is no valid instrument. Exp 5 §6 showed that the blocking materializer
does not reproduce the certified plans' own vehicle-hours: it was 17.8–22.7%
off on N0 and 45.6–47.0% off on N4. Deadhead provenance is also OPEN, so
FEASIBLE is unreachable. **Physical fleet status for every Exp 6 cell is
UNDECIDABLE, and no blocking run was made for Exp 6.** The peak axis is the
solver's cycle-over-headway concurrency proxy. No figure here is a bus count.

## 12. Compute (UTC, from `outputs/exp6/run/*.events.log`)

| stage | wall clock | calls | median s/call |
|---|---|---|---|
| preflight (equivalence, D39, D35; by artifact mtimes) | 2026-09-28 22:18:39 → 2026-09-29 00:00:55 | — | N4 J100 default 1,805 s; D39 H110 1,079 s; N0 J100 621 s (`preflight/lane_a.log`) |
| contract frozen | 00:09:39 | — | — |
| initial, shard 0 (N0 + shared cells) | 00:09:58 → 02:44:42 | 14 certified | 597 |
| initial, shard 1 | 00:09:58 → 02:53:29 | 13 certified + 1 start failure (rc=1, N3 R1_H20) | 612 |
| halt/resume for Amendment 1 | halt seen 00:45:30; shard 0 resumed 00:59:33; shard 1 resumed 01:09:23 | 1 infeasibility proof | — |
| closure N0 | 02:45:04 → 07:01:00 (fixed point) | 24 RAN | 629 |
| closure N3 | 02:53:45 → 06:36:25 (fixed point) | 21 RAN | 625 |
| sentinels | 06:43:07 → 07:24:40 | 4 | 615 |
| Amendment 2 written | 07:34:30 | — | — |

Production wall clock was 00:09:58 → 07:24:40, 7 h 15 m on 2 cores. The summed
per-call time of logged certifications is 13.2 h (initial 4.5, closure 8.0,
sentinels 0.7). The event logs record no incident other than the Amendment 1
halt.

## 13. Limitations

* Demand is a LODES commute proxy (top 20,000 OD pairs), with the frozen path
  model and same-route waiting (cross-route omission not corrected).
* **Closure certifies a fixed point of anchor transfers over 20 frozen edges.
  It does not certify a global optimum.** §7 shows that plans 0.13–0.16% apart
  in objective can differ by about 4,600 served trips. Better plans than the
  closed ones may exist in any cell. The identical-plan groups in §8.2 cannot be
  told apart from search limits.
* Prices depend on the closed REF. Had REF closure missed a better REF plan,
  every price on that network would be understated by the same amount. That is
  exactly the failure greedy-only exhibited (§8.1).
* R3 is enforced at period granularity only. R6 approximates corridors by stops
  with straight-line distance. Regime levels are study choices without a COTA
  anchor.
* N3's base plan is trimmed to fit the envelope (route 001, 5 periods). N3
  R1_H20's emptiness is by 0.0166 proxy units in one period.
* Emptiness is proven only for pure-R1 cells. None arose elsewhere.
* Secondary metrics (served, GC, OFF counts) are basin-dependent (§7).

## 14. Permitted claims

> Under the frozen Model B demand/evaluation model, the EXP4N common modeled
> operating-resource envelope (`0b46d1abc9a80c80`) and the declared
> basin-closure search, imposing study safeguard X changes the best-known
> modeled objective by Y (Z%) relative to the matched unconstrained reference.
> The values are in §10, for N0 and N3.

> Under the same model and envelope, study safeguard R1 at H = 20 has an empty
> feasible set on N3: even minimum service exceeds the early-period
> peak-concurrency proxy cap.

> Under the same model, N3 is better than N0 in all 13 comparable policy cells,
> by 0.15–0.23% of the objective (firewall-admitted).

> Single-greedy-start certification misstates these prices by up to 0.16
> percentage points, and it produced two impossible negative prices. The λ = 2
> objective is flat across plans that differ by about 28% in served trips.

## 15. Prohibited claims

* a global optimum or "optimal" plan, for any cell;
* buses, vehicles, fleet, deployability or operating dollars, including any
  reading of peak-proxy units as vehicles;
* that any regime is COTA policy, or any adjudication of Title VI compliance;
* a finite or "infinite" policy cost for N3 R1_H20;
* reading the greedy-only column as a policy price;
* that R3/R4_C00/B1/B2 "cost the same as" R1_H60 beyond "closure found nothing
  better than R1_H60's plan";
* that Exp 4A or Exp 5 were wrong. They are exact records of their contracts;
  their plans are simply not the best known;
* served-trip or GC improvements as findings in their own right (§7);
* that N4 is worth implementing;
* per-route headway recommendations.

## 16. Consequences for Experiment 7

* **F6 (policy price on N0/N3)**: carry the closed prices of §10. Exp 7 needs
  closure (or cross-seeding) at every sensitivity level, because §8.1 shows the
  basin correction is the same order as the prices themselves.
* **F4 (N4 does not beat N3/N0)**: the negative result is robust to the basin
  corrections seen here, which are about 0.1–0.5% against a gap of about 9%.
  Its sensitivity robustness is untested.
* **N3 vs N0** (0.15–0.23%) is of the same order as the basin corrections, so
  any Exp 7 robustness label for it must come from closure-adjusted comparisons.
* **Secondary metrics**: Exp 7 must not label served-trips or GC robustness
  from single-basin runs.
* **Emptiness** (N3 R1_H20) is envelope-sensitive by 0.0166 proxy units, so it
  must be re-proved at every Exp 7 level.

## 17. Artifacts

* `outputs/exp6/`:
  * `EXP6_CONTRACT.json`, `EXP6_CONTRACT_AMENDMENT_1.json`,
    `EXP6_CONTRACT_AMENDMENT_2.json`, `EXP6_CONSTRAINT_CATALOG.json`;
  * `EXP6_ANALYSIS.json` and
    `SUPERSEDED.EXP6_ANALYSIS.first_run_receipt_start_encoding.json`;
  * `initial/`, `closure/` (records, `RAW.*`, ledgers, states), `sentinels/`,
    `d35/`, `preflight/`, `run/` (logs, events, pidfiles, heartbeats), `smoke/`.
* Scripts: `exp6_freeze.py`, `exp6_grid.py`, `exp6_contracts.py`,
  `exp6_cell.py`, `exp6_run.py`, `exp6_infeasible_cell.py`, `exp6_d35.py`,
  `exp6_analyze.py`.
* Tables: `scripts/exp6_closeout_tables.py` → `outputs/exp6/EXP6_CLOSEOUT_TABLES.{json,md}`.
