# S6 RORBwin local preflight and Python vectors

**Status:** Python preparation checked; native rainfall/excess comparison **NOT RUN**.  
**Owner:** Local Windows agent. **Updated:** 2026-11-13. **Review:** when GUI capture resumes.  
**Source revision:** `b2c89eae7517d1117fd522f24a1897ab7622823d` (PR #50).  
**Branch:** `feat/s6-rorbwin-native-rainfall`. **Stage:** [#8](https://github.com/Chain-Frost/python-runoff-routing/issues/8), open.

This executes the preflight and source-side preparation in the
[handoff](2026-11-12-s6-rorbwin-local-validation-handoff.md). It does not establish native equivalence.
The PR #50 head was checked live and still matched the source revision. No solver code, baseline,
tolerance or hosted workflow changed.

## Verified inputs and environment

All four locally available BoM/FLTwest files match the complete SHA-256 values in the handoff.
Original bytes remain unchanged; private copies and generated evidence are under ignored
`.local/s6-rorbwin-native/`. No original rainfall archive, manual, native output or executable is committed.

Installed RORBwin SHA-256:
`0ca65bcef548f26a5f9bceda6c99ed4f545a9498b61c93aa59a00400732d1aea`.
Its launched window reports **RORBWin - Version 6.52**; this campaign has not captured a computational
report banner or accepted its numerical profile. The installed 6.52 release notes were read locally:
they describe raw subarea excess CSV export and manual preburst percentages of areally reduced burst depth.
Those documented behaviours remain native probe targets.

Windows CPython **3.14.6**, Ruff **0.16.6**:

- Focused rainfall/ARF/selection/preburst/loss tests: **187 passed**.
- Full local checker: repository hygiene **85 files / 0 errors**, Ruff lint/format passed
  (**73 files**), strict Pyright **0 errors / 0 warnings**, **356 tests passed**.
- Wheel built, installed in an isolated environment and imported outside the checkout, with source
  `PYTHONPATH` absent. Installed ARF smoke reproduced the source factor below.
- An initial test attempt imported a different checkout's installed package and failed collection.
  Repeating with this worktree's explicit source path passed; no shared editable installation changed.

## Source-side vectors

Source event **9091**, areal bin **100**, **1440 min / 1% AEP**, **60 min** timestep,
synthetic pervious area **100 km²**. The 24 original burst increments remain in source order.
The legacy loss document is explicitly fabricated from a synthetic test fixture, with matching point
metadata, **21 mm IL / 2 mm/h CL**, source preburst depth **7 mm**, ratio **0.054**.
It is not authentic site loss data. The preburst shape is user-defined **25% / 75%**, not GSAM/Jordan.

| Quantity | Python Decimal result |
| --- | --- |
| Gross point rainfall | `129.0000 mm` |
| Published SW WA ARR2019 ARF | `0.9446027708854816873275314719` |
| Once-adjusted burst rainfall | `121.8537574442271376652515599 mm` |
| Ratio-derived preburst | `6.580102901988265433923584235 mm` |
| R2 experimental excess, no preburst, IL 21 | `59.34113974711524229503098938 mm` |
| R3 experimental excess, reduced burst IL | `64.27700696349762178833652042 mm` |
| R4 experimental complete-storm excess | `64.27700696349762178833652042 mm` |

Private CSVs `python/R0.csv` through `python/R4.csv` retain every rainfall and experimental excess
increment as a Decimal string, with end times relative to burst start. R0–R3 each contain 24 cells;
R4 contains 26, including preburst cells ending at **−60 and 0 minutes**. The JSON ledger retains
source identities, adjustment operations and loss selections. Equal R3/R4 experimental totals are
an arithmetic observation, not proof of matching timestep vectors or native semantics.

## Native limitation and next action

A newly authored one-subarea 100 km² pervious `.cat` was opened in RORBwin's text editor.
Its area and computational validity have **not** been confirmed by a native run. One GUI launch became
unresponsive and was stopped; a second launch responded to file selection, but automation did not
reliably expose the run-specification controls. No native simulation or rainfall/excess export was
obtained. This is a capture/interaction limitation, not evidence of a solver defect.

**R0–R7: NOT RUN.** Native rainfall compared/accepted, native excess accepted and routed output
accepted are all **NOT RUN**. No tolerance was selected because output precision is not yet observed.
The private manifest and matrix explicitly retain those missing gates.

Next action: use an interactive RORBwin session to confirm the synthetic model's calculated area and
enable raw subarea excess export; capture **R0 first**, with saved effective settings and source
storm generation. Then compare all 24 rainfall ordinates before proceeding to R1–R4 losses/preburst.
Keep R5 default-pattern observations separate and R6/R7 conditional. Do not substitute pre-generated
Python storms for independent native rainfall-generation validation or proceed to routed-flow acceptance.

S6 remains unaccepted. No merge, release or stage closure is requested.
