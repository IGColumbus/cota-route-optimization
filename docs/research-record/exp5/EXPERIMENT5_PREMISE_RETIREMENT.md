# Experiment 5 — retirement of the original premise and design

*Additive record, 2026-09-28. Nothing here edits `EXPERIMENT5_PREMISE_AUDIT.md`,
`EXPERIMENT5_OFFON_DIAGNOSTIC.md` or `src/cota_opt/exp5_resource.py`; they stay
as history.*

## What is retired

| Retired | Why |
|---|---|
| **The hours-slack premise** ("hours are ~36–37% used, the peak is the only binding resource") | Measured on the *legacy endogenous-cap* Experiment 4 plans. Under EXP4N's common envelope every certified plan uses 99.92–100.00% of the hours cap; the leader N4 uses **2517.0171064814813 of 2517.1833333333334 h (99.9934%)**. The operating point the premise described no longer exists. |
| **Arm B as a predicted hours-null** | Follows from the premise above. Hours bind, so there is no null to predict. |
| **30 / 35 / 40% hours service cuts** | Designed to find where hours *start* to bind. They already bind at 100%. |
| **Block-derived physical fleet as the second axis** (135/187/173/197/178/149, integral, floored) and **the 1.307 factor** | The production optimizer does not enforce physical fleet. `frequency._feasible` constrains the cycle-over-headway **solver peak-concurrency proxy**. The old axis was internally consistent for a physical-fleet experiment and is not the resource the solver constrains. |
| **`src/cota_opt/exp5_resource.py` as the treatment** | Preserved unmodified. Not run as the Experiment 5 treatment. |

A correction that belongs with this record: an earlier status note said "EXP4N
changed none of Exp 5's premises". The hours measurement above shows it did;
that sentence was retracted in `STATE_OF_PLAY.md`.

## What replaces it

Experiment 5 is a **modeled operating-resource frontier** over two axes:

* **revenue vehicle-hours** (`scheduled_weekday_revenue_vehicle_hours`), and
* the **six-period solver peak-concurrency proxy** (`solver_peak_concurrency_proxy`).
  This is **not** fleet, buses, or physical vehicles, and no per-bus figure can
  come out of it.

The networks are **N4** (the EXP4N normalized leader) and **N0** (COTA's
existing local geometry, validated path, peak express locked as the frozen model
requires). Only frequency and ON/OFF vary. N3 is not an Experiment 5 network.

The caps are the EXP4N common envelope (exact fingerprint `0b46d1abc9a80c80`)
scaled continuously and exactly — no rounding, no flooring — at 75/90/100/110/125/150%:

* Arm A, joint: 6 cells;
* Arm B, hours only: 5 cells;
* Arm C, peak proxy only: 5 cells.

That is 16 cells per network and 32 in total. Every cell runs EXP4N's validated
certification path unchanged.

The implementation is in `scripts/exp5_model_resource.py`, `scripts/exp45_certify_cell.py`,
`scripts/exp45_contracts.py` and `scripts/exp5_run.py`. The frozen contract is
`outputs/exp5/EXP5_CONTRACT.json`, written before the first production cell.

Blocking and fleet are **diagnostic only**. They are reported as FEASIBLE,
INFEASIBLE or UNDECIDABLE, and they never gate, filter or rank a cell.
