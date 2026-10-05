# Round 2 adjudication: TECHNICAL_REPORT.md

*2026-10-04. Response to `ROUND2_REFEREE_REPORT.md` (minor revision; 0 critical,
6 important, 17 minor). Each comment was checked against the repository before
it was accepted. Constraints unchanged from round 1: closeouts, registry and
`outputs/**/*.json` immutable; errata append-only; no new runs; no invented
references.*

## Decisions

| comment | decision | check made | change |
|---|---|---|---|
| R2-1 Hooker DOI | **Accept** | Crossref API: 10.1007/BF02430364 = Hooker, *J. Heuristics* 1(1):33–42 (1995); 10.1007/BF02430363 = Barr et al., 1(1):9–32 | Hooker DOI corrected; Barr entry completed with issue and DOI |
| R2-2 common-lines arithmetic | **Accept, amended** | `diag_N4` 107,248.12; `diag_N3` 13,946.90; net 93,301.22 (the addendum's 93,300 is rounded); Δ43 283,973.37 | §5.4 and §8.1 now give 107,248 for the N4-only case and 93,301 as the net; note on the addendum's wording; Appendix A row; three verifier claims added |
| R2-3 D2 | **Accept** | `DISCOVERIES.md:36–72`; `exp1_final.json → frontier` | D1 paragraph kept (R16); new "Returns in λ plateau" paragraph: λ 4 → 16 buys 0.15 points of unserved demand for 0.25 points of GC (+1.24% → +1.49%) |
| R2-4 stale "pending" | **Accept** | `outputs/SUPERSEDED.md:118–129` | Both statements updated |
| R2-5 walk-only fallback | **Accept** | `pathset.py:246–250, 533, 570` | c_od definition and Appendix B "unserved demand" amended; also `docs/GLOSSARY.md` |
| R2-6 "every number canonical" | **Accept** | — | Status bullet reworded. Data availability now says every number traces to a named file and that superseded files are indexed |
| R2-7 1,800 proposals | Accept | — | "Apart from the one audited proposal…" |
| R2-8 empty route-periods | Accept | grep finds no reader of `allow_new_service_in_empty_periods`; `exp1.py:71–78` | Mechanism corrected |
| R2-9 decision sets | Accept | `frequency.build_ladders` docstring | Exp 2–3 and Exp 4–7 sets stated |
| R2-10 "certified" rule | Accept | — | Sentence replaced |
| R2-11 symbol clash | Accept | — | Caps renamed V_p, direction count d_k |
| R2-12 "closest cell" | Accept | — | README, HANDOFF (two places), FUTURE_EXPERIMENTS (two places) |
| R2-13 GLOSSARY | Accept | `exp4_certify.py:78–86` | 3-rung window wording; entries for unserved demand and `B1_COMMONLINES`; objective entry extended; registry path no longer says v1–v3 |
| R2-14 threshold | Accept | (1/s + 60 + 60λ)/2 = 210 ⇔ λ = 29/9 | "λ ≥ 29/9 ≈ 3.222" |
| R2-15 self-references | Accept | — | §-references made specific |
| R2-16 Highlight 4 | **Accept, amended** | The referee's suggested text is 87 characters, not 73 | "Unmatched convergence and solver starts produced a spurious 0.5% gain" (69) |
| R2-17 Highlights 2/3, abstract | Accept | §5.4: 2,000 generated, 200 certified | H2, H3 and abstract reworded |
| R2-18 bound coverage | Accept | `diag_N3/N4 → periods` lists six periods | §8.1 row states coverage and that the three bounds are not on a common basis |
| R2-19 abstract caveats | Accept | Abstract word count 249 (limit 250) | "certified at 20 restarts"; "path and waiting models that both fit it less well" |
| R2-20 E-number collision | Accept | — | Header note in FUTURE_EXPERIMENTS; the report already prefixes "errata"/"FUTURE" |
| R2-21 "±0.06" | Accept | The verifier searched for the literal "±0.06" | Appendix A reworded; verifier claim changed to "SD 0.06" |
| R2-22 duplicate sentence | Accept | — | Kept under "Operationalization bounds" only |
| R2-23(1) figures | **Defer** | Needs figure generation and a release decision | Status box already lists figures as pending |
| R2-23(2) objective SD | Accept | — | All-levers row: "computed (linear) from 3-seed component means; no seed SD" |
| R2-23(3) external benchmark | Accept | — | §8.0 internal-validity bullet |
| R2-23(4) exposed share | Accept | — | §8.1 row says the threat's size is unquantified |

## Verification after the edits

* `scripts/verify_report_claims.py`: 52/52. There are three new claims (107,248; 93,301; 283,973), and the SD claim token changed.
* `pytest`: all pass.
* `EXPERIMENT7_CLOSEOUT.md` sha256 is unchanged (`27bfc7390c777051…`).
* No file under `src/` changed, and no JSON file under `outputs/` changed.

## Round 3 check (independent, read-only)

The checker recomputed every number this round introduced and found them all correct. It found three IMPORTANT and three MINOR issues, all in text. All six were fixed:

1. A sentence fragment in §5.4 was left over from the R2-2 edit. It is rejoined, and the line-number citation is dropped.
2. The D2 paragraph called the λ = 4–16 frontier "certified", but those rows are single runs. The paragraph now says "single runs" and "path-set-adequate", and notes that the λ = 8 → 16 step is within the seed SD.
3. Appendix A rows that cite `diag_N3/N4.json` and `model_diagnostics_modelB.json` now say these are diagnostic files that are not in registry v5.
4. The Appendix A closing paragraph said the registry indexes "every" artifact. It now says "most", with exceptions labelled.
5. The status bullet and Data availability now say "cited inline or in Appendix A".
6. Two over-long lines in the report were re-wrapped.

The verifier still passes 52/52.

## R2-23(1) closed, 2026-10-05

The figures this round deferred are now done. All eight are generated by
`scripts/make_report_figures.py`: the seven guideline figures plus the F1
decision-space figure (amendment G2-a). The frontier and two-basin figures the
referee named are Figures 1 and 7.

Before the change map was drawn, its aggregation contract was frozen in commit
`08a16b35`. The verifier checks the figures' input hashes and passes 55/55, plus
the figure check.
