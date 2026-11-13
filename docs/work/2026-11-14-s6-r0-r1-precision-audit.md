# S6 R0/R1: rainfall quantisation, export clocks and frozen follow-up protocol

**Status:** documentation/evidence reconciliation only; R1 strict excess FAIL; complete R0 timing acceptance OPEN. No new native calculation, no local-private raw-file rehash in this review, and no numerical implementation change.
**Date:** 2026-11-14. **Stage:** [S6 #8](https://github.com/Chain-Frost/python-runoff-routing/issues/8).
**Source implementation:** [PR #50 at b2c89eae](https://github.com/Chain-Frost/python-runoff-routing/commit/b2c89eae7517d1117fd522f24a1897ab7622823d).
**Prior evidence branch:** [draft PR #54](https://github.com/Chain-Frost/python-runoff-routing/pull/54), head bb34c3aa0cb2cd1f3afcafeb4d5b076b35948223 when prepared. This documentation is stacked on #54 to retain the already recorded R2–R5 investigations. PR #50 and the reference/default loss kernel are not modified.

## What is evidence, and what remains to be verified

This document reviews the *published, sanitised work records* and independently recomputes the stated ARF coefficient control using Decimal arithmetic. The original local private files, GUI screenshots, full R0/R1 per-step CSVs, the installed executable and native saved-input files are not available to this review environment. Historical statements that the local Windows agent hashed or compared them are cited as **reported earlier**, not claimed to have been repeated here. No actual RORBwin process was launched. Reauthentication of every raw file and effective parameter remains a required local gate.

Authoritative records: [R0 preflight](2026-11-13-s6-rorbwin-local-preflight.md), [R0 timing/R1](2026-11-14-s6-r0-timing-r1-arf.md), [R2–R4](2026-11-14-s6-r2-r4-loss-preburst.md), [seven loss controls](2026-11-14-s6-controlled-loss-kernel.md), [R5 default](2026-11-14-s6-r5-default-preburst.md) and the [original local handoff](2026-11-12-s6-rorbwin-local-validation-handoff.md). The existing latter records describe later experiments; their earlier NOT RUN wording is historical rather than present campaign status.

### Reported provenance anchors — compare actual local bytes before further work

| Identity and role | Expected SHA-256 from existing records | This review |
| --- | --- | --- |
| BoM depths_margaret_river_ifds.csv | 0ca11f66c2a1cb7e48e8bd6fc852f52dfa68014377c16301f5d57495c54864db | Previously reported matched; not rehashed here |
| BoM depths_margaret_river_all_design.csv | 7a739958861f82c26e37a568ebabc56fe1dfe16f442b891d7978d54e710a5197 | Previously reported matched; not rehashed here |
| Areal_FLTwest.zip, source EventID 9091, areal bin 100 | 61c60366f953669a9879c5e2c6619b3c420c3a3dceeb296fa41e91606b3c213f | Previously reported matched; not rehashed here |
| FLTwest.zip, independent point-pattern source | 0cd57da5e7dffd8f235b72d3e59c83ac1ab9f2e54f03e94201340e307ed83adb | Previously reported matched; not rehashed here |
| Editor-authored RORB_GE 6.52 100 km² catchment | 189bc5d27f9dddbbdf9d555fa3fb0b79137dd54c9c5d06f4f9a5b02c62b3dc09 | Previously reported matched; not rehashed here |
| Labelled synthetic legacy TXT for full SW WA ARF coefficients | dcb5633328cc2c2aa2674c79df9644696408c505b0251cf822530159dcccb0da | Previously reported matched; not rehashed here |
| Installed RORBwin / native RORB_GE engine | 0ca65bcef548f26a5f9bceda6c99ed4f545a9498b61c93aa59a00400732d1aea | Previously reported matched; not rehashed here |

The recorded native computational banner is **6.52, last updated 1 June 2023**; previous runs used Windows/Python **3.14.6**. Check actual executable path, file size, hash, observed calculation banner and OS again before any new run. A release-note version or window title alone does not establish executable identity.

Original rainfall archives and BoM files must remain byte-for-byte preserved and private. The synthetic TXT supplies published **ARF parameters only**; it is **not** an authentic Margaret River Data Hub loss/preburst source. Do not misattribute fabricated losses or the assumed SW WA region to an actual delineated catchment.

For the 100 km² pervious graphical model, the native report previously established one 1 km natural reach, 24 h, 1% AEP, 60-minute steps, 200-step calculation horizon, 129 mm point depth, and routing settings kc=10 / m=0.8. Both runs used original source **EventID 9091**, while the native selected pattern is labelled **deterministic ordinal 1**. These identifiers must remain separate and traceable by the full 24 percentages, not inferred from their numeric labels.

R0: file ARF OFF, IL/CL 0/0, no preburst, no spatial variation and no regional losses.
R1: **Use ARFs from file ON**, file containing the nine published SW WA coefficients (a=0.183, b=0.259, c=0.271, d=0.33, e=3.85E-06, f=0.41, g=0.55, h=0.00817, i=-0.00045); IL/CL 0/0; regional losses, preburst and spatial variation OFF.

The saved GUI .par coefficient cache was previously observed to display only four decimal places, losing important e/h/i precision; the source TXT retains the full values. Manual typed coefficients were abandoned, not the completed R1 setting. **Reopening/reloading the saved .par and retesting effective coefficients has not been performed**. Do not infer internal ARF precision from the cached text or the 0.94 printed factor alone. Record source TXT locator/hash, selected flags, final named design storm, .par, report and post-reopen output hashes separately. Earlier preliminary RORBWin.stm/.tmp with a 63.2% default event are **not effective R0/R1 storm inputs**.

## R0: label convention supported, full acceptance still open

The previously retained R0 and R1 exports each comprise **201 raw rows**. For corresponding row index j=0..200, hydrograph CSV labels are Inc=j and Time=j hours, while excess CSV labels are Inc=j+1 and Time=j+1 hours. Thus all **201/201** paired metadata rows have exactly **+1 increment / +1 hour** excess-export labels at 60 minutes. For the first nonzero excess entry, the raw excess label is Inc=2 / Time=2 h, but the separate hydrograph label is Inc=1 / Time=1 h and the native text table identifies the rainfall interval as beginning at 0 h. The physical interval is 0–1 h, not a second missing or shifted rainfall increment.

Independent seven-case controlled experiments include 30-minute forcing: 13 original rows per output, hydrograph labels 0–12 and excess labels 1–13; the excess time offset is **0.5 h**, establishing that the observation is one **increment**, not necessarily a fixed hour. The 60-minute controls show a 1 h offset. This is a bounded **RORBwin 6.52 export-labelling hypothesis supported by native comparisons**, not a parser correction for all profiles or a complete physical time-origin contract. Raw Inc/Time tokens and text interval origins stay unchanged; join by independently verified original row/sample index in diagnostics, never by silently subtracting one from source data.

The earlier R0 verdict remains: **24/24 generated rainfall cells exactly agree**; zero-loss converted excess **24/24 pass** the original numeric print-derived allowance (max 0.0000012 mm). The raw 201 labels, first-zero semantics, terminal zeros and text timing must be signed off before calling the entire R0 excess/timing gate accepted. No routed values were used.

## R1: numerical record and strict verdict

| Check | Previously recorded result | Acceptance interpretation |
| --- | --- | --- |
| Python ARF, 28-digit Decimal | 0.9446027708854816873275314719 | Computational source prediction |
| Native ARF text | 0.94 | Printed only; cannot identify hidden precision |
| Python areally adjusted storm | 121.8537574442271376652515599 mm | Full-precision expectation |
| Native written/printed storm | 121.85 mm | Difference -0.0037574442271376652515599 mm; inside 0.005 mm total *print* allowance |
| TP percentages | 24/24 exact | EventID 9091 identity retained |
| Rainfall ordinates | 24/24 within 0.005 × percentage/100 mm | Print-derived agreement, not exact cells |
| Text rainfall and excess | 24/24 at 0.05 mm allowance | Coarser print checks only |
| Raw R1 excess vs full-precision Python | **0/24 pass**, max absolute difference 0.000249621529950082272279044 mm | **STRICT FAIL** |
| Raw R1 excess vs separate 121.85 mm replay | **23/24 pass**, remaining step **16** differs by +0.0000020 mm | **STRICT FAIL**; diagnostic model only |
| Native raw excess depth sum | 121.8500064 mm after conversion | Not proof of input precision; CSV rate printing affects summed depth |

R0/R1 excess CSV rates are in **m³/s**. For one hour and 100 km², depth in mm = rate × **0.036**. A four-decimal rate export has half-unit **0.00005 m³/s**, equivalent to **0.0000018 mm**. The frozen raw allowance is therefore **0.0000018 mm absolute, zero relative**. The reported +0.0000020 mm step-16 residual corresponds in magnitude to **0.0000555555556 m³/s**, marginally above one half-export unit; the plus sign's native-minus-reference orientation must be checked from the private comparison file. There is no rounding-up of the budget, no retuned tolerance, no replacement source golden and no accepted strict parity.

The 121.85 mm replay strongly suggests an effective-depth quantisation or equivalent arithmetic/formatting pathway, **but does not demonstrate that the native engine rounds the storm before temporal disaggregation**. The step-16 residual also does not establish binary32 instructions, operation order or an error in Python. The later controlled investigation tested **24** floating-point hypotheses: one order reproduced **74/74 R2–R4 tokens but 23/24 R1**; another reproduced **72/72 R1–R3 but 25/26 R4**. No one candidate explained all **98** R1–R4 cells. These are *post-observation* diagnostics, not independently predeclared validations.

## Predeclare independent models before another native calculation

Let p[1..24] be the unchanged original EventID-9091 percentages, each parsed as its original Decimal token; sum(p)=100. Let A=100 km², timestep=1 hour, gross depth=129 mm, and c=0.036 mm per (m³/s). All predicted 24-cell depth and flow vectors below must be materialised privately, independently of native outputs, and SHA-256 frozen in a protocol file **before** any new calculation; do not use a native token to choose a formula, casting point, tie rule or tolerance.

| Model | Predeclared predicted increment depth | Distinguishing consequence |
| --- | --- | --- |
| H-FULL, no internal storm rounding | (129 × ARF) × p[i]/100 at Decimal context precision 28 or better | Different unrounded total-depth controls yield different raw flow vectors |
| H-TOTAL-2DP, quantised storm before splitting | round-to-0.01-mm(129 × ARF) × p[i]/100 | Distinct coefficient controls with the same two-decimal total must generate matching vectors (apart from bounded export rounding) |
| H-STEP-2DP, per-increment quantisation | round-to-0.01-mm((129 × ARF) × p[i]/100) independently per increment | Total can differ from 121.85 and shows stepwise changes; do not force sum back to the storm |
| H-OUTPUT-ONLY, reporting quantisation | Full-precision increment converted to flow, then rate exported to four decimals; storm/report display independently rounded | Printed storm may agree while CSV flow distinguishes the coefficient controls |
| H-F32-WEIGHT-FIRST | Explicit float32 cast of total, p[i] and float32 weight sum; then float32 p/sum, float32 depth product, float32 mm-to-rate conversion; finally format rate | Binary32 rounding/operation path test, not a general inference about native internals |
| H-F32-DEPTH-FIRST | Explicit float32 cast of total, p[i] and sum; float32 total × weight before float32 divide; then float32 conversion to rate; finally format rate | Separates non-associative binary32 order from weight-first |
| H-F64 | Native-style binary64 arithmetic with the same two explicit operation orders and final rate formatting | Separates machine precision from decimal quantisation |

Record separately round-half-even and round-half-up for candidate two-decimal and four-decimal formatting; do not select the one that gives the best fit after seeing a native output. For every model record exact Decimal strings, Python float.hex (binary64), explicit struct-packed IEEE-754 binary32 bit patterns and unrounded/preformatted values. Reconstruct candidate differences from original **rate tokens** using Decimal before any float conversion. Preserve source field order, step 1-based index, raw native Inc and Time, and physical interval-start/end as separate columns. The printed storm and CSV are two different measurement channels, not interchangeable precision estimates.

### Particularly discriminating two-coefficient control

ARR Book 2 v4.2 Table 2.4.2 explicitly publishes **e=3.85E-06** for South-West Western Australia ([source](https://www.arr-software.org/pdfs/ARR_190514_Book2_V4.2.pdf)); the separately documented local and independent R scripts use **3.845E-06**. This is a deliberately **synthetic sensitivity probe**, not authority to replace the published coefficient or modify an original ARR download. Holding every other coefficient and input constant gives these independent Decimal predictions:

| Coefficient e | Predicted ARF | Predicted adjusted depth (mm) | Two-decimal depth |
| --- | --- | --- | --- |
| 0.00000385 (published / R1) | 0.9446027708854816873275314719 | 121.8537574442271376652515599 | 121.85 |
| 0.000003845 (sensitivity control) | 0.9446058365053097100442782272 | 121.8541529091849525957118913 | 121.85 |

The full-depth difference is **0.0003954649578149304603314 mm**. If the original nonnegative 24 source percentages sum to 100 and internal full precision survives, at least one forcing cell has an unrounded **rate difference of at least 0.0004577140715 m³/s** (difference ÷ 24 ÷ 0.036): greater than four 0.0001-m³/s display quanta. If total storm depth is actually quantised to 121.85 mm **before** splitting, and every other effective input is the same, the H-TOTAL-2DP predicted vectors for these two coefficient inputs are identical. Export formatting alone cannot conceal the full-precision difference in every cell under the stated assumptions. This is the priority falsifiable control; it does **not** yet have a native result.

**Pre-run rule:** create two separately named synthetic coefficient TXT files; do not edit the R1 source TXT in place. Keep the same model/TP/duration/loss settings and record each file's full hash and the saved .par, effective storm and report before/reopen/after. If the GUI cache or reload silently rounds a coefficient, or the controls are not shown to be the actual effective input, classify the test **INVALID INPUT CONTROL** rather than attributing its outcome to computation. The former R1 direct-entry attempt is not acceptable proof. The exact 24 predicted vectors and their SHA-256 must be frozen before either new native run.

### Step-16 audit and bounded run decision

Independently compare, for step 16 and all other 23 cells: original CSV rate *string*, Decimal rate × 0.036, original source percentage token, Decimal full-depth prediction, 121.85-mm diagnostic, candidate binary32 casts and candidate binary64 rates. Record first failing index, signed difference, native rate decimal quantum, 32-bit ULP distance where applicable, conversion order and per-row print interval. Use the **unchanged** 0.0000018-mm allowance for both the baseline and diagnostic; do not convert a print-precision pass into strict acceptance. Save the step-16 observation even if a newly selected model removes it.

Recommended follow-up native controls, only after an explicit authority check and frozen predictions: **N1** rerun original R1 from a fresh process and rehash the entire capture (repeatability); **N2** run the independent e=3.845E-06 control from a fresh process; **N3** reopen the separately saved published-e parameter set and rerun from a fresh process (cache/reload control). Maximum **three** new calculations for this protocol; no unbounded combinations or GUI automation retries masquerading as fresh numerical controls. The prior seven loss controls and R5 had their own bounded run approvals; they do **not** document blanket permission for N1–N3. **N1–N3 NOT RUN / new-run authorisation not established in this review environment.**

Each fresh process must use an isolated working directory and report: actual executed file/executable identity, full input/capture SHA-256 inventory, subprocess launch/exit/diagnostics where available, exact preflight settings and screenshots, generated .stm, named .out, raw hydrograph/excess CSVs, 201 original labels, full 24-cell predictions and comparison, OS/locale and run timestamp. A GUI failure or incomplete export is a capture failure, not a passing test. Never overwrite the original R0/R1 evidence.

## Local reauthentication and private inventory contract

Retain a **read-only local inventory** under ignored .local/s6-rorbwin-native/reports using a new unique filename. Record relative locator, size, SHA-256 and case role for every R0/R1 source, parameter, named storm, report, both CSVs, screenshots, frozen policy and per-step diagnostic. Compare the seven pinned identities above, then compare *every file* against its previous immutable R0 (reported ten-file) and R1 (reported eleven-file) capture manifests. Flag missing/replaced/duplicate outputs. An inventory of current hashes alone is **not** proof that old captured files are unchanged. Never store a private absolute path or original source bytes in public Git.

Local semantic recheck must explicitly confirm: total catchment area; AEP 1% (not 1 EY / preliminary 63.2%); duration 1440 minutes; timestep 60 minutes; original areal bin 100 and EventID 9091 distinct from native ordinal 1; final storm 129.00 or 121.85 mm as appropriate; full coefficient file and ARF checkbox; IL/CL 0/0; regional-loss/preburst modes OFF; row counts, 24 forcing cells, 201 raw rows, leading/trailing zero structure; model/executable hashes; and unchanged named tolerance JSON files. Missing raw evidence means **NOT REAUTHENTICATED**, never PASS. Any actual area/ARF/source mismatch is an input mismatch, not a numerical-kernel failure.

## R2–R4: existing runs and prospective controls must not be confused

The earlier R2–R4 native runs **were already completed**, as documented in their own record. Do not falsely label them NOT RUN or retroactively call their hypotheses pre-registered. R2 IL=21/CL=2, R3 entered reduced IL=14.419897/CL=2 and corrected R4 full IL=21/CL=2 plus two 25/75 preburst increments gave distinct observed results, with strict loss residuals retained. The first R4 attempt with 58 missing prefix cells and 84 slots is a **preserved invalid configuration**; corrected R4b replaces the missing prefix with explicit zeros and gives 26 increments, preburst 6.58 mm and combined 128.43 mm. The 58-cell correction is not a modification of the original failed capture. R3 saved/displayed 14.420/14.42 is not evidence that the entered 14.419897 was retained on reload.

If specifically authorised for *new* independent loss controls, predeclare: **R2-Z**, exactly zero IL/CL on the native-written R1 storm to isolate rainfall precision; **R2-C**, fixed rectangular input [10,10,10,0,10,0] mm with IL=19/20/21 and CL=0/2 as an already-observed control, not a novelty claim; **R3-S**, exact storm IL versus reduced burst IL while preburst is OFF; and **R4-P**, original storm IL with manual 5.4% preburst, explicit 58 prefix zeros and two 25/75 nonzero positions, comparing once-ARF ratio depth to raw/point/second-ARF alternatives. Never treat R2-C's seven historical runs as a new preregistration, and do not rerun them without a new bounded reason. R4-P must separately retain source preburst **depth 7 mm** and source **ratio 0.054** without substituting one for the other. The default long-duration GSAM/Inland R5 has also **already run**, but the selected default region is not independently geographically validated and short-duration Jordan/R6/R7 are unrun.

## Acceptance ledger and next decisions

| Gate | Current status |
| --- | --- |
| Exact local private rehash in this review | **NOT RUN** (private files and executable unavailable here) |
| R0 source 24-cell rainfall | **PASS for the previously recorded one-event profile only** |
| R0 zero-loss 24-cell values | **PASS under the frozen numerical allowance**; full timestamp sign-off OPEN |
| R0/R1 one-increment raw export-label hypothesis | **SUPPORTED in recorded 60- and 30-minute controls**, not universal |
| R1 ARF/depth and rainfall printed-precision checks | **PASS at printed allowances only** |
| R1 exact internal ARF/storm quantisation | **UNRESOLVED** |
| R1 24-cell full-precision excess at 0.0000018 mm | **FAIL, 0/24** |
| R1 121.85-mm replay at 0.0000018 mm | **FAIL, 23/24; first remaining failure step 16** |
| R2–R4 and R5 | Previously **RUN**, with recorded limits and strict residuals retained |
| New N1–N3 controls, reload and binary-mode interpretation | **NOT RUN; authority/effective input proof required** |
| Native routed hydrograph acceptance | **NOT RUN** |

**Next executable gate:** on the approved local Windows machine, rehash and semantically reauthenticate R0/R1 against their *original* private manifests, freeze exact model-prediction CSV hashes and execute no new controls until their native-run authority is documented. Then select only N1–N3 and report every failure. Keep stage #8, PR #50 and #54 draft/native acceptance states unchanged; do not change S2, defaults, budgets, goldens, publication visibility, CI, release or merge state.
