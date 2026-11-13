# S6: R0 export timing audit and separate R1 ARF experiment

Follow-up: [R2–R4 native loss/preburst experiments](2026-11-14-s6-r2-r4-loss-preburst.md).
The unrun R2–R7 statements below describe this record's earlier stopping point; see the follow-up for current status.

**Status:** R1 completed; printed rainfall agreement observed; strict excess and timing gates open.

**Owner:** Local Windows agent. **Updated:** 2026-11-14. **Review:** before R2–R4.

**Source:** `b2c89eae7517d1117fd522f24a1897ab7622823d`; previous evidence record
`c7f2e2ad257f98e0e4de768b0383fa1ad8bc424e`.
**Branch:** `feat/s6-rorbwin-native-rainfall`. **Stage:** [#8](https://github.com/Chain-Frost/python-runoff-routing/issues/8), open.

Follow-up to the [R0 record](2026-11-13-s6-rorbwin-local-preflight.md) and
[local handoff](2026-11-12-s6-rorbwin-local-validation-handoff.md). The owner reviewed R0 and selected
a separate R1 ARF-only experiment while keeping R0 timing acceptance open. No Python numerical
implementation, golden, existing tolerance, workflow or PR draft state changed.

## R0 timing: independent metadata comparison

The original ten-file R0 capture inventory was rehashed before inspection. All **201** raw excess
records remain unchanged. Comparing only export metadata with the separate native hydrograph CSV:

| Metadata | Hydrograph CSV | Raw excess CSV |
| --- | --- | --- |
| Record count | 201 | 201 |
| Printed increment range | 0–200 | 1–201 |
| Printed time range, hours | 0–200 | 1–201 |
| First nonzero excess sample | Corresponding sample index 1 | Raw `Inc=2`, `Time=2.000 h` |

Across **201/201 corresponding rows**, excess labels exceed hydrograph labels by exactly **one
increment and one hour**. The storm starts at increment 0, its timestep is one hour, and the text
rainfall/excess tables explicitly describe intervals following starts 0–23. This supports a
profile-specific **excess CSV label offset**, rather than a missing rainfall increment. Hydrograph
values were not compared: this is a metadata audit, not routed-flow acceptance.

The installed release notes discuss a historical first-timestep label error, but do not specifically
establish this raw excess export's current contract. The observation is bounded to these captures;
no universal parser correction or automatic timestamp shift is introduced. **R0 full excess timing
acceptance remains open for review.** Private `r0-export-time-grid.csv` preserves both original axes.

## R1 configuration and source provenance

R1 used a separate local directory and byte-identical editor-saved **`RORB_GE 6.52`** catchment:
SHA-256 `189bc5d27f9dddbbdf9d555fa3fb0b79137dd54c9c5d06f4f9a5b02c62b3dc09`.
Native reports confirm **100 km²**, one pervious subarea, one natural 1 km reach, **24 h / 1% AEP**,
one-hour steps, FLTwest areal bin **100**, deterministic ordinal **1**. All 24 percentages match
source **EventID 9091**. IL/CL remain **0/0**; preburst, regional losses, spatial variation and
embedded-burst filtering are off. Routing parameters remain `kc=10`, `m=0.8`, horizon 200 increments.

The original BoM and ARR ZIP bytes remain unchanged. The installed executable SHA-256 remains
`0ca65bcef548f26a5f9bceda6c99ed4f545a9498b61c93aa59a00400732d1aea`; computational banner is
**6.52, last updated 1 June 2023**. GUI/native computation was local on Windows/Python **3.14.6**.

For controlled coefficient intake, a **clearly labelled synthetic legacy Data Hub TXT** supplied the
published ARR2019 Book 2 South-West WA coefficients. It is not an authentic site export. Direct
manual coefficient entry was cancelled after unreliable numeric-field interaction; it was not used
for the completed calculation. The final saved parameter file records **Use ARFs from file ON**,
regional losses OFF and the synthetic coefficient file's locator.

| a | b | c | d | e | f | g | h | i |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.183 | 0.259 | 0.271 | 0.33 | 0.00000385 | 0.41 | 0.55 | 0.00817 | −0.00045 |

Control TXT SHA-256: `dcb5633328cc2c2aa2674c79df9644696408c505b0251cf822530159dcccb0da`.
The GUI-saved `.par` coefficient cache prints only four decimals, losing some precision in `e`, `h`
and `i`; the full source TXT is retained and remains selected. Save/reopen replay has **not** been
tested, so the `.par` cache alone must not be treated as a full-precision coefficient source.

## R1 results: distinguish rounded agreement from strict parity

`reports/r1-tolerance-policy.json` was frozen before calculation. It retains the R0 raw CSV allowance
of **0.0000018 mm absolute**, zero relative. Separate allowances derive from printed precision:
**0.005 mm** for the two-decimal total depth, and **0.05 mm** for one-decimal text catchment cells.
Per-step storm-depth allowance is `0.005 × source percentage / 100` mm.

| Comparison | Result |
| --- | --- |
| Python ARF | `0.9446027708854816873275314719` |
| Native printed ARF | `0.94`; insufficient precision for full-precision ARF acceptance |
| Python adjusted depth | `121.8537574442271376652515599 mm` |
| Native generated storm depth | `121.85 mm` |
| Total depth difference, native minus Python | `−0.0037574442271376652515599 mm`, within 0.005 mm print allowance |
| Original pattern percentages | **24/24 exact** |
| Generated rainfall versus Python | **24/24 within printed-depth budgets; 0/24 exact** |
| Text rainfall and excess versus Python | **24/24 each within text print allowance** |
| Raw excess versus full-precision Python | **0/24 pass** at the unchanged tight CSV allowance |
| Maximum full-precision excess difference | `0.000249621529950082272279044 mm` |
| Raw excess versus diagnostic replay of printed `121.85 mm` storm | **23/24 pass**, step 16 fails |
| Step 16 diagnostic residual | `+0.0000020 mm`, above frozen `0.0000018 mm` allowance |
| Converted raw excess total | `121.8500064 mm` |

The raw CSV is in **m³/s**; multiplication by **0.036** converts its rates to one-hour depths over
100 km². The full-precision differences are consistent with quantization at the generated storm's
two-decimal depth. This is an observed explanation, not grounds to replace Python values, relax a
tolerance or accept strict excess parity. Step 16's additional residual remains an explicit failure.

R1 again has **201** excess records: a leading zero, 24 nonzero cells and 176 trailing zeros. All
201 label pairs reproduce R0's constant one-increment/one-hour export offset. Raw labels are retained.

## Retained evidence, validation and next action

Ignored `.local/s6-rorbwin-native/` retains original inputs, final native storm/report/CSV files,
batch summary, GUI `.par`, screenshots, frozen policy, all 24 per-step comparisons and a separately
hashed R1 capture. Preliminary `RORBWin.stm/.tmp` are retained as preliminary, not effective inputs.
No third-party raw rainfall files, native outputs, executables or manuals are added to public Git.

R0 inventory integrity, R1 source/model identities, full 24-cell coverage and all 201-row metadata
checks were executed. Repository hygiene, relative links and whitespace are checked for this
documentation-only change. Prior software-quality evidence is historical; no new full suite or
wheel acceptance is claimed for this documentation follow-up.

**R1 run completed; printed rainfall agreement only. Full-precision ARF, strict excess and timing
acceptance remain open. R2–R7 and routed-flow comparisons: NOT RUN.**
Next: review the bounded export-label mapping, the observed storm-depth quantization and step 16's
small remaining residual before selecting loss/preburst experiments. Retain the fixed tolerances.
No Python numerical change is justified by this experiment alone. S6 remains unaccepted; no merge,
release or issue closure.
