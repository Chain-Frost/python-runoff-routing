# S6 RORBwin local preflight and Python vectors

Follow-up: [2026-11-14 R0 timing audit and separate R1 ARF experiment](2026-11-14-s6-r0-timing-r1-arf.md).
The R1–R7 statements below describe the original R0-only stopping point; see the follow-up for current status.

**Status:** R0 native rainfall matched; zero-loss excess ordinates checked; CSV timing acceptance open.

**Owner:** Local Windows agent. **Updated:** 2026-11-13. **Review:** on CSV timing investigation.
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

## Initial attempt, before the R0 retry

A newly authored one-subarea 100 km² pervious `.cat` was opened in RORBwin's text editor.
Its area and computational validity have **not** been confirmed by a native run. One GUI launch became
unresponsive and was stopped; a second launch responded to file selection, but automation did not
reliably expose the run-specification controls. No native simulation or rainfall/excess export was
obtained. This is a capture/interaction limitation, not evidence of a solver defect.

At that stopping point, **R0–R7 were NOT RUN**. Native rainfall compared/accepted, native excess accepted and routed output
accepted are all **NOT RUN**. No tolerance was selected because output precision is not yet observed.
The private manifest and matrix explicitly retain those missing gates.

Next action: use an interactive RORBwin session to confirm the synthetic model's calculated area and
enable raw subarea excess export; capture **R0 first**, with saved effective settings and source
storm generation. Then compare all 24 rainfall ordinates before proceeding to R1–R4 losses/preburst.
Keep R5 default-pattern observations separate and R6/R7 conditional. Do not substitute pre-generated
Python storms for independent native rainfall-generation validation or proceed to routed-flow acceptance.

## R0 retry: current RORBwin graphical file and native calculation

The owner clarified the target: **current RORBwin graphical catchment files with legacy Data Hub
inputs**, excluding ARR Data Hub 2026. Only **R0** was selected for this retry.

RORBwin's own graphical editor authored and saved a new file with header **`C RORB_GE 6.52`**.
The earlier hand-authored `RORB_GE 002` attempts are not the accepted input. No pyromb dependency
or upstream PR was needed. The editor-produced file contains one pervious **100.00000 km²** subarea,
one natural **1.000 km** reach, an outlet print location and the subarea rainfall-excess CSV flag.
Its SHA-256 is `189bc5d27f9dddbbdf9d555fa3fb0b79137dd54c9c5d06f4f9a5b02c62b3dc09`.
The native report independently confirms total area **100 km²**.

Automation required care: ordinary text-setting messages did not set custom numeric controls;
keyboard entry and the editor's saved bytes established the actual area and reach length. Earlier
attempts also encountered malformed file structure and file-dialog selection errors. These are
input/automation failures, not rainfall algorithm failures. Original source bytes remain unchanged.

The design dialog required a legacy Data Hub TXT before enabling OK, even for R0. The clearly
labelled synthetic test TXT was supplied; **ARF-from-file, regional losses and preburst were off**.
This is not a site-matched legacy loss export. The native effective ARF and zero losses, rather than
the unchecked controls alone, establish R0's configuration.

The completed run produced the native generated `dur24hour_aep1.stm`, `R0.out`, `R0.csv`,
`R0_excess.csv` and a batch summary. GUI parameters were saved as `R0.par`; save/reopen replay was
not performed. Raw files and screenshots stay under ignored `.local/s6-rorbwin-native/`.
The computational banner confirms **6.52, last updated 1 June 2023**, matching the executable hash above.

| Effective setting | Native evidence |
| --- | --- |
| AEP / duration / timestep | **1% / 24 hours / 1 hour** |
| Area / depth / ARF | **100 km² / 129.00 mm / 1.00** |
| Pattern | Areal bin **100**, deterministic ordinal **1**; all 24 percentages match original event **9091** |
| IL / CL | **0.00 mm / 0.00 mm/h** |
| Routing parameters / calculation horizon | `kc=10`, `m=0.8`, **200 increments**; no routed-flow acceptance |

`RORBWin.stm` and `RORBWin.tmp` are preliminary files containing a default **63.2% / 56.20 mm**
event. They are retained as preliminary evidence, **not** the effective R0 event. The completed
run report, batch summary and duration/AEP-specific storm all identify **1% / 129 mm**.

## R0 timestep comparison and remaining timing limitation

- **24/24 generated percentages and derived rainfall depths match exactly**, retaining original
  event identity and sequence. The generated total is **129 mm**.
- Native text rainfall and zero-loss excess tables independently agree with every Python rainfall
  cell within their **0.05 mm** half-unit printing allowance.
- The raw excess CSV reports **m³/s**, not mm. For 100 km² and one hour, multiplying rates by
  **0.036** converts them to increment depths. The frozen half-unit allowance of **0.00005 m³/s**
  is **0.0000018 mm**, with zero relative allowance. All **24/24** compared values pass;
  maximum absolute difference **0.0000012 mm**, converted total **128.9999952 mm**.
- The CSV contains **201 records**: one leading zero, 24 nonzero cells and 176 trailing zeros.
  All records are retained and checked. The first nonzero value has raw `Inc=2`, `Time=2.000 h`;
  the text report labels the corresponding rainfall/excess interval start **0**, and Python labels
  that interval end **1 h**. Diagnostic sequence matching is explicit and **does not accept or
  silently correct the CSV time axis**.

Private `reports/r0-tolerance-policy.json` was written before automated difference calculation;
`r0-per-step.csv` retains raw labels, source percentages, native text values, converted excess
and differences. `r0-comparison.json`, the manifest, matrix and immutable capture inventory record
the separate gates. No goldens or existing tolerances changed.

**R0 native generated rainfall: accepted for this one event.** Zero-loss excess ordinates match
the stated precision; **full native excess acceptance remains open because CSV timing is unresolved**.
**R1–R7: NOT RUN. Routed-flow comparison: NOT RUN.** The previous source/wheel quality results
still apply to the unchanged implementation; this follow-up changes documentation only.

Next action: independently establish the raw excess CSV's leading-zero/time-label convention
against the text interval tables, preserving raw labels. After that review, separately select R1
(ARF) and later loss/preburst runs; they were not executed in this R0-only retry.
S6 remains unaccepted. No merge, release or stage closure is requested.
