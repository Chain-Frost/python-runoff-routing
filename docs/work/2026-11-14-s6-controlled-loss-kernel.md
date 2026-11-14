# S6: controlled loss crossing, candidate profile and 30-minute export labels

**Status:** bounded crossing rule characterised; separate candidate implemented; precision acceptance open.

**Owner:** Local Windows agent. **Updated:** 2026-11-14. **Review:** before native-profile acceptance or R5.

**Baseline implementation:** `b2c89eae7517d1117fd522f24a1897ab7622823d`.
**Previous evidence revision:** `8e75f1322862c297cc228c36ad13c51d5643f718`.
**Branch:** `feat/s6-rorbwin-native-rainfall`; stage [#8](https://github.com/Chain-Frost/python-runoff-routing/issues/8), open.

The owner selected this investigation after the [R2–R4 evidence](2026-11-14-s6-r2-r4-loss-preburst.md).
It implements the [separate experimental API](../EXPERIMENTAL_RORBWIN_652_LOSSES.md) while retaining
the existing ARR reference kernel and default method unchanged. PR #50 remains draft and unchanged.

## Seven controlled native calculations

The pre-run protocol bounded execution to **seven** calculations. Each used the same current
editor-saved `RORB_GE 6.52` pervious 100 km² model, with SHA-256
`189bc5d27f9dddbbdf9d555fa3fb0b79137dd54c9c5d06f4f9a5b02c62b3dc09`.
The unchanged RORBwin executable SHA-256 is
`0ca65bcef548f26a5f9bceda6c99ed4f545a9498b61c93aa59a00400732d1aea`, banner **6.52, updated 1 June 2023**.
No executable modification, decompilation or native instrumentation was used.

Independently authored, current DESIGN `.stm` inputs supply **[10, 10, 10, 0, 10, 0] mm**.
They use exact **[25, 25, 25, 0, 25, 0]** weights and 40 mm depth, avoiding ARR/BoM/ARF/preburst
generation and storm-depth quantization. The cumulative boundary after increment 2 is **20 mm**.
Native reports verify the selected losses. The calculation horizon is 12 increments, yielding 13
raw records per CSV; original labels, zero initial sample, all six forcing cells and six trailing
zeros are accounted for. Routing outputs are not numerically compared.

| Timestep | IL, mm | CL, mm/h | Candidate excess vector, mm | Native comparison |
| --- | --- | --- | --- | --- |
| 60 min | 19 | 0 | [0, 1, 10, 0, 10, 0] | 6/6 pass |
| 60 min | 20 | 0 | [0, 0, 10, 0, 10, 0] | 6/6 pass |
| 60 min | 21 | 0 | [0, 0, 9, 0, 10, 0] | 6/6 pass |
| 60 min | 19 | 2 | [0, 0, 8, 0, 8, 0] | 6/6 pass |
| 60 min | 20 | 2 | [0, 0, 8, 0, 8, 0] | 6/6 pass |
| 60 min | 21 | 2 | [0, 0, 7, 0, 8, 0] | 6/6 pass |
| 30 min | 19 | 2 | [0, 0, 9, 0, 9, 0] | 6/6 pass |

All **42/42** forcing-length excess values pass the frozen **0.0000018 mm absolute**, zero-relative
allowance. The largest controlled residual is **0.0000016 mm**. CL=0 controls establish the IL boundary
independently. With CL=2, the below-boundary crossing remainder is zero, rather than the reference
partial-step rule's 0.8 mm; the above-boundary crossing yields 7 rather than 7.2 mm. The 30-minute
crossing yields zero rather than 0.9 mm. These distinguish full-increment from prorated CL in the
selected cases. Dry-gap checks here occur after IL exhaustion; other dry-state behaviours remain
outside the native characterisation.

## Separate implementation and reference preservation

`src/runoff_routing/rorbwin_losses.py` exposes only explicit selection through
`calculate_rorbwin_652_excess`, with profile ID
`rorbwin_6_52_full_increment_cl_experimental_v1`. It returns a frozen per-increment loss ledger,
uses readable Decimal arithmetic and always reports `native_parity="not_accepted"`.
No dependencies or automatic profile dispatch were added. `arr_losses.py` is byte-unchanged;
a regression test exercises its original partial-timestep result alongside the distinct candidate.

Public tests use synthetic independent crossing expectations, dry steps, mass balance, invalid
inputs and immutable results. They launch no native process and contain no private rainfall sources.
The seven controls were run **before** implementing the new profile.

## Cached native replay and precision investigation

Explicit, hash-verified cached replay covers the seven controls and retained R2/R3/corrected R4,
plus the subsequently selected [R5 native default-pattern run](2026-11-14-s6-r5-default-preburst.md).
The candidate uses each native written rainfall as a separately labelled input-matched diagnostic;
the original full-precision Python rainfall and earlier failures are not replaced.

- Source replay: **166 passed, 6 strict expected failures**. This comprises 155 passing ordinate
  tests, six failing ordinate tests and eleven passing complete-grid metadata tests.
- Known failures remain **R2 step 11, R3 step 11, R4 steps 8/22**, plus **R5 steps 27/41**, at the unchanged allowance.
  The expected-failure marks are strict and accept only assertion failures; missing/corrupt evidence
  fails collection or validation instead of becoming a skip or pass.
- Those six failures remain **unaccepted**, despite the green test-process exit status.

A local, bounded investigation evaluated **24** labelled binary32 arithmetic-order hypotheses over
**98** R1–R4 cells. It varied accumulation, rainfall arithmetic and unit-conversion order, without
instrumenting native execution. One uniform hypothesis casts the weight sum to binary32, computes
rainfall as depth × (weight / sum), applies full-increment CL in binary32, then converts using a
binary32 area/time factor. It reproduces **74/74 R2–R4 printed excess tokens exactly**, but **23/24**
R1 tokens. An alternative depth × weight / sum with area-first conversion reproduces **72/72**
R1–R3 tokens but **25/26** R4 tokens. No tested hypothesis matches all 98.

This supports floating representation/evaluation order as an explanation of the small residuals,
but does not identify native instructions or prove native precision. These are post-observation
diagnostics, not new goldens or acceptance backends. The public candidate remains Decimal and the
frozen allowance is unchanged. Native storm-depth quantization remains separately recorded.

## Time-label observation at 30 minutes

All 13 native rows in each control preserve the same record relationship:

| Timestep | Hydrograph CSV labels | Excess CSV labels | Excess minus hydrograph time |
| --- | --- | --- | --- |
| 60 min | Inc 0–12, time 0–12 h | Inc 1–13, time 1–13 h | 1 h |
| 30 min | Inc 0–12, time 0–6 h | Inc 1–13, time 0.5–6.5 h | 0.5 h |

Thus the observed discrepancy scales as **one increment**, not an absolute hour. Per-step evidence
retains raw increment/time, sample index and independently derived physical interval end. There is
no timestamp rewriting or automatic parser mapping. The contract is characterised for this pinned
profile and these constant timesteps; it does not accept all time conventions, engines or events.

## Windows and installed-wheel verification

On Windows CPython **3.14.6**, the full source checker passed repository hygiene, pinned Ruff
**0.16.6** lint/format, strict Pyright **0 errors / 0 warnings**, and **377 tests** with no skips.
Final documentation-inclusive hygiene checked **93 files / 0 errors**; relative links and whitespace passed.

The wheel was built, installed in a separate environment, and exercised from **outside the checkout**
with source `PYTHONPATH` absent and module origin verified in that environment's site-packages.
New public tests plus cached native replay yielded **187 passed, 6 strict expected failures**.
This is installed-code replay of retained observations, not new native executions.
Wheel SHA-256: `61c22351dbf578705a1fd06cc61bb11b355c741052d04ae96d819aefba69e7ae`.

Ignored `.local/s6-rorbwin-native/loss-probe/` retains the pre-run protocol, seven native captures,
saved/entered settings and per-step comparisons. Reports retain both replay logs and all precision
hypotheses. Original R0–R4 captures remain hash-verified and unchanged. No raw private source data,
reference executable, manual or native report is added to public Git.

From this checkout, the following commands replay existing evidence without launching RORBwin:

```powershell
$env:PYTHONPATH = 'src'
py -3.14 -m pytest -q tests/test_rorbwin_losses.py tests/test_arr_losses.py
py -3.14 -m pytest -q .local/s6-rorbwin-native/loss-probe/test_candidate_native.py -ra
```

The second command requires this machine's retained private captures and replay script; missing
evidence is an error, not a passing or skipped native comparison. Ordinary public tests remain
self-contained and native-free.

## Delivery and next action

The candidate is a separate review front stacked on PR #50; #50 remains draft. Full native precision
acceptance remains open, and no default algorithm changed. The crossing hypothesis now has bounded
independent support, with timing characterised at two increments. After that characterisation,
one separately recorded R5 long-duration default GSAM run was executed as the owner recommended;
the short-duration Jordan default was not tested. **R6/R7 and routed-flow acceptance remain unrun.**
Next: review the named candidate contract, R5 observations and residual evidence before selecting
the conditional boundary/interpolation matrix. No merge, release, stage acceptance or issue closure.
