# S6: native R2–R4 loss and explicit-preburst experiments

Follow-up: [controlled crossing experiment and separate candidate loss profile](2026-11-14-s6-controlled-loss-kernel.md).

**Status:** R2, R3 and corrected R4 completed; experimental Python excess parity fails.

**Owner:** Local Windows agent. **Updated:** 2026-11-14. **Review:** on loss-policy investigation.

**Implementation source:** `b2c89eae7517d1117fd522f24a1897ab7622823d`.
**Previous evidence revision:** `45dd02d9c9c71ad582e6fcf4a03c4f0a02ad4243`.
**Branch:** `feat/s6-rorbwin-native-rainfall`; stage [#8](https://github.com/Chain-Frost/python-runoff-routing/issues/8), open.

Following the owner's instruction to continue, these experiments proceed independently of the
open [R1 precision and R0/R1 timing gates](2026-11-14-s6-r0-timing-r1-arf.md). No Python numerical
implementation, existing tolerance, golden, workflow or draft PR state changed.

## Common profile and retained inputs

All cases use the same editor-authored `RORB_GE 6.52` model: **100 km²**, one pervious subarea,
one natural 1 km reach, outlet print and raw subarea-excess export. Model SHA-256 remains
`189bc5d27f9dddbbdf9d555fa3fb0b79137dd54c9c5d06f4f9a5b02c62b3dc09`.
The computational banner is **6.52, last updated 1 June 2023**, with executable SHA-256
`0ca65bcef548f26a5f9bceda6c99ed4f545a9498b61c93aa59a00400732d1aea`.
Local orchestration uses Windows/Python **3.14.6**.

The BoM/FLTwest source bytes and preceding R0/R1 captures are unchanged. Design selection is
**24 hours / 1% AEP**, one-hour steps, areal bin **100**, native ordinal **1** matching original
**EventID 9091**. File ARFs use the same labelled synthetic legacy TXT containing published SW WA
coefficients. This is not an authentic site loss/preburst export; no ARR Data Hub 2026 input is used.
Routing parameters remain `kc=10`, `m=0.8`, horizon 200 increments; routing values are not compared.

| Case | Entered IL, mm | CL, mm/h | Preburst |
| --- | --- | --- | --- |
| R2 | 21.000 | 2.000 | Off |
| R3 | 14.419897 | 2.000 | Off |
| R4, corrected run | 21.000 | 2.000 | Manual 5.4%, user-defined 25/75 profile |

R3's original full-precision Python reduced IL is `14.41989709801173456607641576 mm`.
The native seed retains entered `14.419897`, while the report shows **14.42** and the GUI-saved
cache stores **14.420**. Do not infer all entered digits from the rounded report or these clamped
loss-crossing values. Save/reopen numerical replay of the final caches was not performed.

## R4 setup failure retained separately from corrected run

The first R4 calculation reported **0.00 mm preburst**, with **84** rainfall slots: 60 empty slots
followed by the 24-step burst. It is retained as an **input/configuration mismatch**, not a valid
explicit-preburst comparison. It is not silently removed from the campaign history.

The manually edited pattern had 25 and 75 in slots 59/60, but preceding cells remained native
`-999` missing sentinels. The installed release notes require explicit **0.0** prefix entries so
they can be trimmed. A separate input replaced exactly those **58** missing entries with zeros;
the failed attempt and its outputs were preserved before the retry.

The corrected file was reopened in RORBwin. Screenshots confirm the 24-hour row has a one-hour
increment, explicit prefix zeros and final 25/75 entries; the manual depth table retains **5.4000%**
at 24 hours / 1% AEP. Default patterns and Data Hub preburst depths are OFF. The corrected native
run is retained locally as **R4b**, representing the effective R4 comparison below.

An earlier R2 setup also failed a pre-run parameter check because integer-looking fixed-width
fields did not give the intended loss values. Explicit decimal seeds corrected this **before** any
R2 calculation. Both seed versions are retained. No incorrect-loss R2 simulation is claimed.

## Rainfall and preburst observations

R2/R3 retain R1's written **121.85 mm** burst versus full-precision Python
**121.8537574442271376652515599 mm**. All 24 source pattern weights match; text rainfall agrees
at its fixed print precision. That does not grant strict excess acceptance.

Corrected R4 reports **6.58 mm preburst**, **26** rainfall increments, **121.85 mm** burst and
**128.43 mm** combined depth. Python's corresponding totals are **6.580102901988...** and
**128.433860346215... mm**. The observed preburst supports the ratio being applied to once-areally
reduced burst depth, rather than the 129 mm point depth or a second ARF application, at printed
precision. No unprinted native precision is inferred.

The generated R4 storm contains prefix weights **1.35 and 4.05**, followed by the original 24
weights, for total weight **105.4**. A separately labelled input-matched reconstruction scales
these relative weights to the written **128.43 mm** combined depth. It preserves all original
tokens; it does not silently force the source pattern to 100% or replace the full-precision Python
event. The prefix retains the requested 25/75 split.

R4's native clock starts at the beginning of preburst; its design burst starts at **native hour 2**.
Python's relative clock places burst start at **0** and preburst end labels at **−60/0 minutes**.
Each per-step report retains both origins and the original raw CSV labels explicitly.

## Complete-vector comparisons

The policy `R234-native-print-precision-v1` was frozen before the runs. Primary and diagnostic
excess checks retain **0.0000018 mm absolute**, zero relative. Three comparison layers remain separate:

1. Native versus the existing full-precision Python source event and experimental loss rule.
2. The **unchanged** Python loss kernel replayed on reconstructed native written rainfall.
3. A labelled hypothesis consuming IL first, then a **full increment's CL** from remaining rainfall,
   capped at available rainfall. This is diagnostic, not a replacement policy or accepted solver.

| Case | Steps | Native excess total, mm | Source Python total, mm | Source Python passes | Input-matched Python passes | Full-increment CL diagnostic passes |
| --- | --- | --- | --- | --- | --- | --- |
| R2 | 24 | 58.2354684 | 59.341139747115... | 3/24 | 22/24 | 23/24 |
| R3 | 24 | 64.2410136 | 64.277006963497... | 2/24 | 22/24 | 23/24 |
| R4 corrected | 26 | 64.2410964 | 64.277006963497... | 4/26 | 23/26 | 24/26 |

R2's main discrepancy is burst step **3**: native excess is zero, while input-matched Python
predicts approximately **1.1021094 mm**. R3's main discrepancy is step **2**, approximately
**0.0323850 mm** input-matched Python versus native zero. R4 shows the corresponding difference at
complete-storm step **4**, approximately **0.0322467 mm** versus native zero. Rainfall quantization
alone therefore does not explain these loss-crossing differences.

The full-increment CL hypothesis removes those large crossing discrepancies but still fails the
fixed fine allowance: **step 11** in R2/R3 has **0.0000020 mm** maximum residual; R4 steps **8/22**
fail, with maximum **0.00000190740038 mm**. These remain failures. No float allowance was invented
after observing them. The evidence supports a candidate loss-convention difference for these
cases, not a universal loss-engine claim.

Text excess checks at their coarser **0.05 mm** allowance pass **23/24, 24/24 and 26/26** respectively.
Those rounded tables can conceal the smaller crossing discrepancy; they do not override the fine
CSV failures.

Each effective run retains and checks **201 raw CSV records**. The initial record and trailing
176/176/174 records are zero; the complete 24/24/26 rainfall-length sequences, including zero excess
cells, are compared. All 201 excess-versus-hydrograph metadata pairs in each run retain the known
**+1 increment / +1 hour** excess-export labels. Timing acceptance remains open; no timestamps shift.

## Independent ARF script cross-check

The owner's local `ryan-tools` `ARF-calcs.py` was imported without running its plotting example.
For **100 km² / 1440 min / 1% / SW WA**, its default coefficient `e=3.845e-6` yields ARF
**0.9446058365053097**, depth **121.85415290918495 mm**. The native test and published-table policy
use `e=3.85e-6`; changing only an **in-memory copy** of the script's table yields
**0.9446027708854816**, depth **121.85375744422713 mm**, agreeing with the Decimal implementation
to floating-point precision. Both depths round to native **121.85 mm**. No source script or native
input changed. This coefficient-version distinction does not explain the input-matched loss mismatch.

## Delivery and remaining gates

Private `.local/s6-rorbwin-native/` retains all inputs, entered and saved parameters, native outputs,
screenshots, fixed policy, per-step CSVs and structured comparison summaries. R2/R3/corrected R4
have separate hashed captures; the first R4 configuration failure has its own retained capture.
R0/R1 inventories are reverified unchanged. Public Git contains only this sanitized evidence record
and index updates, with repository hygiene/link/whitespace checks; no new full software suite or
installed-wheel result is claimed for this documentation-only batch.

**R2–R4 have been run. Experimental Python excess parity fails.** R4's requested preburst is observed
at printed precision; full native timing/precision/loss acceptance remains open. **R5–R7 and routed
comparison: NOT RUN.**

Next: review a named native-profile IL/CL crossing contract and its synthetic regression requirements,
keeping input quantization, the candidate loss rule and small residuals distinct. Any implementation
change must retain the current experimental reference and be separately validated. Do not repeat
earlier numerical claims as passing or close S6 from these experiments. No merge, release or closure.
