# S6 N4: controlled ARF-coefficient sensitivity — pre-run protocol

**Execution follow-up:** [N4 native result](2026-11-14-s6-n4-native-result.md): completed once after the local freeze; 121.88 mm, 24/24 changed forcing cells, strict source FAIL 0/24, replay FAIL 22/24. The pre-run specification below is retained as written.

**Status at preregistration:** N4 PLANNED / NOT RUN. This is an independent, documentation-only protocol; **the local
private 24-cell predictions have not yet been frozen** and must be generated and SHA-256 pinned
before execution. No RORBwin process was launched by this review.
**Date:** 2026-11-14. **Stage:** [S6 #8](https://github.com/Chain-Frost/python-runoff-routing/issues/8).
**Dependency:** [N1–N3 native record](2026-11-14-s6-n123-native-precision.md), [R0/R1 local reauthentication](2026-11-14-s6-r0-r1-local-verification.md), [original precision audit](2026-11-14-s6-r0-r1-precision-audit.md).
**Implementation reference:** original R1 at `b2c89eae7517d1117fd522f24a1897ab7622823d`; current `main` is a separate integration target. Native source/control interpretations are not reclassified by software merges.

## Why N4, and what it can establish

The three completed independent native calculations **N1/N2/N3** produced identical 201-record excess
vectors, including all 24 rainfall increments, with unchanged raw labels. N1 used published coefficient
`e=3.85E-06`, N2 used a different explicit source `e=3.845E-06`, and N3 reopened N1's saved parameters.
N1/N2 storm depths differ by approximately `0.000395464958 mm` at full precision but both print as
`121.85 mm`. The exact location of the observed precision collapse remains **unresolved**. N3 also
does not identify internal coefficient reload behaviour: with the original TXT available, its output
was unchanged. The saved four-decimal GUI cache alone predicts a different depth, so it cannot
simply be assumed to be the computational coefficient set.

N4 changes **only** the synthetic legacy-TXT long-duration South-West WA coefficient `e` to
`3.50E-06`, enough to change the two-decimal storm depth even if total-depth quantisation is
performed before disaggregation. This is a *sensitivity control*, not an ARR-published parameter
recommendation or a valid input for a real catchment.

**Standing permission:** the owner authorises local RORBwin and RORB_CMD calculations under the
`AGENTS.md` now merged on `main` by [#65](https://github.com/Chain-Frost/python-runoff-routing/pull/65).
There is **no standing three-run limit**; the prior N1–N3 three-run figure describes that completed
batch only. Retain deliberate, bounded experiments and exact evidence rather than launching an
uncontrolled sweep. Native execution is local Windows only, not hosted CI.

## Independently calculated numerical anchors (before N4 native execution)

Use the repository's ARR2019 Book 2 long-duration equation with the **unchanged other eight**
published South-West WA coefficients and `area=100 km²`, `duration=1440 min`, `AEP=1%`,
gross BoM design depth `129 mm`. The calculations below were independently repeated using
60-digit `Decimal`; they are **Python predictions, NOT observed native values**.

| Control | Only changed coefficient e | Predicted ARF | Predicted adjusted depth, mm | Expected total printed to 0.01 mm |
| --- | --- | --- | --- | --- |
| N1 published | `3.85E-06` | `0.944602770885481687327531471865` | `121.853757444227137665251559871` | `121.85` |
| N2 previous sensitivity | `3.845E-06` | `0.944605836505309710044278227156` | `121.854152909184952595711891303` | `121.85` |
| **N4 proposed** | **`3.50E-06`** | **`0.944817364273443277499804342289`** | **`121.881439991274182797474760155`** | **`121.88`** |
| N5 conditional stronger diagnostic | `3.00E-06` | `0.945123926256245549174479871466` | `121.920986487055675843507903419` | `121.92` |

The N4 minus N1 full-precision storm-depth change is
`+0.02768254704704513222320028473 mm`. N5 would also change native's *printed ARF* from
`0.94` to `0.95` **if** the native implementation evaluates the same coefficient inputs and
rounds the factor to two decimals. N5 is **conditional / NOT RUN**; do not assume it is needed.

The previously retained source **EventID 9091** is not the same identifier as RORBwin's
deterministic pattern **ordinal 1**. Use the *original 24 source percentages* without renumbering
or rounding them; the full vector belongs in the new local private freeze.

## Predeclared and falsifiable alternatives

Let `p[i]` be the original exact percentage token for event 9091, i=1..24, and `D` the
independently calculated full N4 storm depth above. For the fixed 100 km² area and one-hour
increment, **rate in m³/s = rainfall depth in mm / 0.036**. Predict each complete 24-cell
rate vector, not just the storm total. The conversion and final native CSV's rate printing must
be modelled separately.

| Candidate | Pre-run 24-cell prediction | If observed |
| --- | --- | --- |
| H-FULL-OUTPUT | `rain[i] = D × p[i]/100`; convert to rate and print at four decimals | Consistent with full-depth survival into disaggregation, but float orders may produce variations |
| H-TOTAL-2DP | `rain[i] = round(D, 0.01 mm) × p[i]/100`; convert and print | Consistent with depth quantisation upstream of disaggregation; not proof of its exact location |
| H-STEP-2DP | `rain[i] = round(D × p[i]/100, 0.01 mm)`; convert and print | Separates per-increment quantisation from total-depth quantisation |
| H-F32 and H-F64 | Existing precisely defined casting, accumulation, multiplication, conversion and printing variants from the N1–N3 frozen-protocol corpus, applied to N4 **without retuning** | Can distinguish arithmetic/export orders; a fitted result does not identify native instructions |
| H-NO-EFFECTIVE-CHANGE | All N4 effective output tokens equal N1 despite the modified source TXT | Indicates a source/effective-setting or coefficient-handling issue requiring investigation; cannot conclude engine ignores e without verifying controls |

For Decimal candidates, predefine both `ROUND_HALF_EVEN` and `ROUND_HALF_UP` and do not choose
the better outcome post hoc. For machine-float candidates, record each cast point and explicit
binary32 bits / binary64 `float.hex()`. Preserve intermediate unrounded depth and rate as
separate quantities; a rate-export pass cannot be presented as a depth parity pass. Do not
renormalise percentages or silently correct native time labels.

The reported N1 strict limit `0.0000018 mm` absolute, zero relative, stays frozen.
Native versus full-source Python and native versus diagnostic written-depth replays remain
**separate verdicts**. N4's synthetic input is its *own* controlled source; a failure under
a source-precision comparison is not evidence to change the default Python equation.

## Required OFFLINE freeze before any native calculation

The existing 396 complete vectors were frozen for **N1/N2**; they do **not** automatically cover N4.
Use the **current public typed pattern reader** on the original untouched local
`Areal_FLTwest.zip` (expected SHA-256
`61c60366f953669a9879c5e2c6619b3c420c3a3dceeb296fa41e91606b3c213f`) to select
the source pattern by **EventID 9091, 1440 min, 60 min increment, area bin 100, region
S-SW Flatlands (West)**. Confirm exactly 24 original weights, sum 100 and identity with the
frozen N1/R1 source; reject any mismatch before proceeding.

1. **Create N4 synthetic legacy TXT from a byte-preserved copy of N1's synthetic TXT.**
   Modify *only* the LONGARF `e` coefficient to `3.50E-06` using the characterised
   field/key, not a blind numeric substring replacement. Compare complete parsed legacy documents
   and a byte-level diff to confirm all other coefficients, location metadata, loss values,
   section versions and source profile are identical. Keep original and new TXT with independent
   hashes. The new file must be clearly labelled *synthetic sensitivity control*, not genuine Data Hub.
2. **Freeze independent N4 results before opening RORBwin.** Export source identity, original
   24 percentage strings, N1 and N4 60-digit ARF/depth predictions, each candidate's 24 rainfall
   depths, raw rates, four-decimal expected tokens, binary metadata and predicted totals.
   Write immutable or no-clobber private CSV/JSON and a SHA-256 manifest under a **fresh ignored**
   `.local/s6-n4-coefficient-20261114/` directory. Include source/tool revisions and
   `0.0000018 mm` policy identification.
3. **Precompute distinguishing rows.** Count N1-versus-N4 predicted differing four-decimal rate
   tokens under H-FULL and H-TOTAL-2DP, identify first difference and maximum expected difference.
   If the predicted vectors do not discriminate under actual export formatting, **STOP and
   redesign offline**. Never choose a new coefficient after inspecting native results.
4. **Verify the original records remain unchanged** using previously anchored hashes and
   original 602-file inventory as a baseline. A fresh inventory alone is not a historical proof.

The final local protocol manifest must contain the hashes of all predicted 24-row vectors and
source controls **before a native N4 calculation begins**. A written prediction cannot be added
retroactively and called predeclared.

## N4 native procedure (local Windows agent; NOT RUN here)

Use a new native process and isolated, no-clobber working/output directory. Pin executable SHA-256
`0ca65bcef548f26a5f9bceda6c99ed4f545a9498b61c93aa59a00400732d1aea`,
observed banner `6.52, 1 June 2023`, and graphical model SHA-256
`189bc5d27f9dddbbdf9d555fa3fb0b79137dd54c9c5d06f4f9a5b02c62b3dc09`.
Retain 100 km² pervious area, 1 km natural reach, 24 h / 1% AEP, one-hour steps,
EventID 9091/native ordinal 1, `kc=10`, `m=0.8`, horizon 200, zero IL/CL,
ARFs from file ON, preburst/regional losses/spatial variation OFF.

- Explicitly select **only the new N4 synthetic TXT**, observe/save the native ARFs-updated
  acknowledgement and source locator, and verify the final effective design settings.
  Do not rely on rounded coefficients shown in the `.par` cache or manually entered zeros.
- Run one controlled calculation, retaining a fresh process record, screenshot evidence,
  seed and saved parameters, named generated storm `.stm`, full report, both raw 201-record
  CSVs, batch output, and SHA-256 inventory. Capture the **original** raw labels and entire
  forcing/tail horizon; do not compare routed discharge values.
- Confirm the original TP percentages, source area, selected AEP/duration and all other settings
  before evaluating the numerical outputs. If any effective input differs, mark **INVALID INPUT**
  and preserve its capture separately; never categorise an invalid control as a solver failure.
- Compare 24 forcing cells under each frozen candidate, 201 raw labels, total depth, native
  printed ARF and storm, full-precision source, printed-depth diagnostic, first failure and max
  signed/absolute difference. Preserve even the best model's failed rows.

### Conditional N5, only if it resolves a specific ambiguity

If N4 produces unchanged N1 vectors or gives no decisive proof that changed coefficients affect
the native storm, **do not infer a bug**. Independently predeclare the stronger `e=3.00E-06`
control above, freeze the complete 24-cell predictions/hashes in a separate private packet and
verify fresh effective source selection. A distinct *two-decimal ARF* (`0.95` predicted) and
storm depth (`121.92 mm`) can discriminate a silent coefficient fallback or early precision collapse.
If N4 is decisive, **do not run N5 merely for more data**. There is no blanket three-run limit;
each run still needs a meaningful, predeclared purpose.

## Reporting and acceptance gates

| Gate | Current state before N4 |
| --- | --- |
| Historical N1/N2/N3 input identities, 201-row vectors and original evidence | **PASS / preserved** in their own prior records |
| R0 forcing/excess association and bounded one-increment label mapping | **PASS** for the tested profile |
| R1 full-precision excess | **FAIL, 0/24** at unchanged tolerance |
| R1 printed-121.85-mm diagnostic | **FAIL, 23/24; step 16 +0.0000020 mm** |
| N4 high-precision totals and candidate semantics | **OFFLINE CALCULATED** (anchors above); new 24-cell vectors **NOT YET FROZEN** |
| N4 native calculation and its 201/24-cell verdict | **NOT RUN** |
| N5 conditional native control | **NOT RUN** |
| Universal RORBwin/GUI timing, source-rounding rules, S6 stage and routed acceptance | **NOT ACCEPTED** |

Deliver the complete private frozen prediction/capture manifests and a sanitised follow-up work
record. Report the N4-vs-N1 comparison as **coefficient-sensitivity evidence**, not an ARR design
validation. Keep the original raw inputs, no-clobber evidence, tolerances, prior failures,
default numerical implementation, S2 routing, CI, release/merge and issue #8 status unchanged.
