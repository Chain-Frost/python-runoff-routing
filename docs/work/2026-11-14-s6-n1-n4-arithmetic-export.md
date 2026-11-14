# S6 N1/N4: arithmetic and excess-export investigation

**Status:** a consistent model reproduces all 48 N1/N4 rate tokens and a new prediction-first native
control; exact native mechanism and numerical acceptance remain open. **Owner:** Local Windows agent.
**Updated:** 2026-11-14. **Review:** independent arithmetic/evidence review.
**Stage:** [#8](https://github.com/Chain-Frost/python-runoff-routing/issues/8), open.
**Branch:** `audit/s6-n1-n4-arithmetic-20261114`.
**Starting/source revision:** `fc57c3c0cd3bd98c4daa498074a5875f46c5a584`,
[draft #68](https://github.com/Chain-Frost/python-runoff-routing/pull/68).
The delivery commit and new draft PR are recorded in the stage issue after push.

This follows [N1–N3](2026-11-14-s6-n123-native-precision.md) and the
[N4 result](2026-11-14-s6-n4-native-result.md). Dependencies remain #56 → #64 → #68 → this follow-up.
No dependency branch, default method or production numerical code was changed.
The pre-publication check found #68 had advanced by a documentation-only completion audit to
`ff424eb34da6c3971819c5f1880670f55c3359b2`. This follow-up retains that audit and its concurrent entries;
the experiment/source pin above remains unchanged. Its prior no-survivor result concerns the original
frozen family, rather than the broader hypotheses investigated here. Coastal remains deferred.

## Reauthenticated originals and unchanged failure contract

Before calculations, **739 checks authenticated 720 distinct original files**, including the original
602-file inventory, N1–N3 campaign, N4 capture/freeze, source archive, saved parameters, frozen predictions,
tolerance policies and installed executable. All 720 files were rehashed after the work and remain unchanged.
Historical inventory anchors are distinguished from newly computed package hashes.

Executable SHA-256 remains
`0ca65bcef548f26a5f9bceda6c99ed4f545a9498b61c93aa59a00400732d1aea`, **10,923,068 bytes**;
retained and new native reports identify **RORBwin 6.52, updated 1 June 2023**. All models match current
graphical `RORB_GE 6.52` hash `189bc5d27f9dddbbdf9d555fa3fb0b79137dd54c9c5d06f4f9a5b02c62b3dc09`.
The source areal archive matches `61c60366f953669a9879c5e2c6619b3c420c3a3dceeb296fa41e91606b3c213f`.
The current typed reader confirms EventID **9091**, separate native ordinal **1**, all **24 original
percentages**, sum **100**, 100 km² bin, 24 hours, one-hour steps and original region identity.
Reports/parameters confirm 100 km², zero IL/CL, no preburst, kc=10, m=0.8 and horizon 200.

All **201 raw excess and hydrograph records per N1–N4 run** remain byte-preserved, including original
rate strings and labels, initial zero and 176 trailing zeros. N1/N2/N3 equal original R1 for all 201
excess records. They are repeatability controls, not three independent numerical vectors. The primary
investigation therefore has **48 distinct N1/N4 forcing positions**.

The frozen allowance is **0.0000018 mm absolute, zero relative**. Independent Decimal calculations at
**28 and 80 digits** reproduce the original results without replacing the frozen predictions:

| Case | Written storm depth | Full-source strict pass | Printed-depth Decimal diagnostic |
| --- | --- | --- | --- |
| N1 / original R1 | 121.85 mm | 0/24 | 23/24; step 16 fails |
| N2, separate coefficient | 121.85 mm | 0/24 | 23/24; step 16 fails |
| N3, saved-parameter reopen | 121.85 mm | 0/24 | 23/24; step 16 fails |
| N4 | 121.88 mm | 0/24 | 22/24; steps 8/14 fail |

## Offline matrix and coherent model

The previous **396 frozen vectors** were reviewed first: **198 shared policies across two depths**,
with best joint token agreement **45/48**. The new explicit matrix separates input casts, percentage
accumulation, multiplication/division order, rainfall storage, conversion-factor precision, rate storage
and final formatting. It includes Decimal 28/80, binary32, binary64, mixed precision, declared increment
rounding/truncation and cumulative-difference alternatives.

There are **428 declared rainfall graphs**, deduplicated to **116 numerical classes**, crossed with
**96 conversion graphs** and three uniform export rules: nearest/half-even, nearest/half-up and truncation.
The **33,408 labelled evaluations** reduce to **7,236 distinct complete rainfall/rate/token predictions**.
Equivalent spellings and carried-forward baselines are aliases, not new independent evidence. The private
matrix retains all 48 comparisons, complete mismatch vectors, signed errors and totals for every distinct
prediction: **347,328 per-cell traces**, plus complete conversion-node traces, binary32 bits and binary64 hex.

**Six canonical graphs reproduce all 48 rate tokens** with one policy across both depths. They share
higher precision in the volume/time conversion factor and binary32 stored rate before nearest four-decimal
export. A readable representative, private ID **R068-C024-ROUND_HALF_EVEN**, uses the written-depth basis
and binary32 inputs, binary64 disaggregation intermediates, binary32 rainfall storage, then a binary64
volume/time factor and binary32 rate storage. The same representations/order apply to all timesteps.

This is a **computational hypothesis**, not native source reconstruction or an adopted compatibility
profile. Half-even and half-up remain indistinguishable for the matching observations. Storage and
parenthesisation alternatives remain output-equivalent; exact native register/storage precision and the
upstream location of total-depth precision collapse are not uniquely identified.

Independent exact-rational reconstruction rounded every declared node to a 24- or 53-bit significand
using nearest/ties-even, then formatted through integer quotient/remainder. All **288 candidate-cell
reconstructions** agree, avoiding reliance on the same Python floating-point implementation twice.

| Declared family | Best joint token agreement |
| --- | --- |
| Full-source depth survives disaggregation | 0/48 |
| Decimal rainfall/conversion, including declared increment quantisation | 45/48 |
| Homogeneous binary32 nodes | 46/48 |
| Homogeneous binary64 nodes | 45/48 |
| Direct division by 0.036 in tested representations | 45/48 |
| Four-decimal truncation | 29/48 |
| Matching mixed-precision family | **48/48** |

These reject only the specified graph families as complete explanations. No case- or timestep-specific
rule, fitted correction or rounding selection was introduced.

## The three original residuals

The SAME representative graph explains both residual directions. Private diagnostics retain original
inputs, Decimal 28/80 predictions, every binary intermediate, ULP shifts and final export bins.

| Case / step | Percentage | Decimal printed-depth rate, m³/s | Candidate stored rate, m³/s | Native token |
| --- | --- | --- | --- | --- |
| N1 / 16 | 2.90 | 98.156944444… | 98.156951904296875 | 98.1570 |
| N4 / 8 | 6.67 | 225.816555556… | 225.8165435791015625 | 225.8165 |
| N4 / 14 | 3.43 | 116.124555556… | 116.12454986572265625 | 116.1245 |

Candidate-to-Decimal rate shifts are approximately **+0.978**, **−0.785** and **−0.746 binary32 ULP**.
A printed native token does not expose its internal float. Input/intermediate/storage rounding moves
the candidate values across final decimal boundaries; formatting the unchanged Decimal rate alone
still cannot explain the observations. No timestep correction is needed for the consistent candidate.

## Independent retained controls

Before loading their ordinates for comparison, all six graphs' predictions and two explicit loss
extensions were frozen and hashed for **365 retained control positions**. These are not 365 new or
statistically independent simulations. N2/N3 add 48 repeatability positions, all matched, without
increasing the number of distinct primary numerical cases.

The representative graph with unchanged Decimal full-increment loss semantics gives:

| Control | Exact rate-token agreement |
| --- | --- |
| R0, independent zero-loss total | 24/24 |
| Seven IL/CL crossing/timestep controls | 42/42 |
| R2 / R3 / R4 / R5 | 24/24, 24/24, 26/26, 45/45 |
| R6 rare, 15-minute / 74.9 km² | 37/40; steps 19/21/38 differ |
| R7 below / exactly / above 75 km² | 34/34, 33/34, 72/72; exactly-75 step 26 differs |
| **Total** | **361/365** |

Area/timestep conversion and loss arithmetic are explicit extensions, not inferred as native from the
zero-loss fit. R3 uses intended IL **14.419897 mm**; saved/report decimals alone do not establish those
effective digits. An all-binary32 loss-state extension gives **360/365**, so it is not a universal
replacement. Neither extension was retuned after held-out comparison. Prior R2–R7 failures remain archived.

## P1: one prediction-first native discriminator

After offline comparisons/diagnostics, zero-loss N1/N4/R0 still did not separate strict per-operation
binary32 multiplication from the higher-intermediate-precision group. Loss-bearing controls involve
additional arithmetic. A distinct zero-loss test was therefore justified.

A fixed **50-input synthetic grid** was scored offline: maximise separated candidate pairs, then
discriminating cells, then token span, with deterministic ties. Selected **P1**: authored depth
**129.01 mm**, percentages **33.33/66.67**, two hourly increments, the same 100 km² graphical model,
zero IL/CL, no ARF/Data Hub/preburst generator, horizon 12. Complete predictions, inputs and provenance
were frozen **before fresh process launch**. Freeze SHA-256:
`c88c940a43ecd8856b43a51af1d7631046f6a35f9b3501eeb0bf64d19a1533eb`.

| P1 hypothesis | Predicted rate 1 | Predicted rate 2 | Native matches |
| --- | --- | --- | --- |
| Strict per-operation binary32 disaggregation | 1194.4176 | **2389.1931** | 1/2 |
| Higher-intermediate-precision group | 1194.4176 | **2389.1934** | **2/2** |
| Native observation | **1194.4176** | **2389.1934** | — |

**Exactly one calculation** ran under standing local permission. The fresh process saved parameters
and exited; all **13 raw records** per export family, full report, model/storm, screenshots, parameters
and process record are retained. An initial file-open timeout occurred before calculation; the same
process accepted an explicit command. No numerical run was discarded or repeated. The automation
library's 64-bit/32-bit warning was retained; effective inputs and outputs were independently checked.
Raw clocks remain one increment apart; no timestamps or routed-flow values were adjusted/compared.

P1 supports the higher-intermediate-precision group and rejects the strict binary32 alternative for
this input. **Five** remaining canonical graphs still predict identical P1 tokens. No second native
test or coefficient sweep ran; exact internal storage distinctions remain unresolved.

## Token agreement is not numerical acceptance

| Gate at unchanged 0.0000018 mm allowance | Result |
| --- | --- |
| Original full-source N1/N4 comparison | **FAIL 0/48**, unchanged |
| Original printed-depth Decimal diagnostic | **FAIL 45/48**, original three residuals unchanged |
| Representative predicted rate-token equality | **48/48** |
| Native token versus representative preformatted rate, converted to depth | **48/48** |
| Native depth versus representative pre-conversion rainfall | **FAIL 45/48**: N1 22/24, N4 23/24 |
| Retained controls, representative pre-conversion excess diagnostic | **FAIL 363/365** |
| P1 exact nominal-source diagnostic | **FAIL 1/2**; step 2 = **−0.0000046 mm** |

Native exported-rate sums convert to **121.8500064 mm** for N1 and **121.8799908 mm** for N4.
Representative rainfall sums are approximately **121.8500001431 / 121.8799980879 mm**; preformatted
rate sums convert to **121.8500004501 / 121.8799987564 mm**. P1 exported depth totals **129.0099960 mm**
against nominal **129.01 mm**. These distinct totals are retained without renormalising percentages,
storm depth or loss accounting to force conservation/acceptance.

## Evidence, checks and next action

The private package contains **78 artifacts**: authenticated snapshots, complete candidate/mismatch
matrices, arithmetic definitions/traces, three-residual diagnostics, rejected hypotheses, held-out
freezes and P1 evidence. Package manifest SHA-256:
`3da8f20ccf04ffebb6c3efaecdfb39a0f5f21d22aa470f1b55d10fd9399edc68`.
P1 capture inventory SHA-256:
`83142ba376c81db69569a2315d70fd3bd72dba54468a1f877f4e6c6585bab905`.

Windows / CPython **3.14.6** read-only verification checks all package hashes, **720 original files**,
**347,328 distinct candidate-cell comparisons**, original failures, held-out freeze and P1 capture.
Exact-rational verification separately covers 288 primary candidate cells. Public changes are Markdown
only; repository/link checks pass **160 files / 0 errors**, and whitespace checks pass. No new full-suite, installed-wheel or current-code
numerical acceptance is claimed. Private source archives, captures, manuals and executables remain local.

**Conclusion:** one uniform, independently supported model explains all N1/N4 rate tokens. The exact
native mechanism remains nonunique, extension coverage is incomplete and numerical compatibility is
**NOT ACCEPTED**. Hydrological/design acceptance is separate. Default ARR/loss code, original predictions,
tolerances, goldens, raw clocks, S2 routing and CI remain unchanged.

**Next:** independently review the private model, then isolate remaining loss/area/timestep behaviour
before proposing any named compatibility implementation. A broad coefficient sweep is not justified.
Keep the follow-up PR draft and #8 open; no merge or release.
