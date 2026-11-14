# S6 N4: native coefficient-sensitivity result

**Status:** one N4 calculation completed; coefficient sensitivity demonstrated; strict numerical
acceptance **FAIL**. **Owner:** Local Windows agent. **Updated:** 2026-11-14.
**Review:** before selecting another precision experiment.
**Branch:** `docs/s6-n4-coefficient-sensitivity-20261114`; protocol/source revision
`a4f139a1959b73cd8993630de0cbcfcbda26f3cd`. Delivery revision is recorded in
[issue #8](https://github.com/Chain-Frost/python-runoff-routing/issues/8) and
[draft PR #68](https://github.com/Chain-Frost/python-runoff-routing/pull/68), stacked on #64.

This executes the [predeclared protocol](2026-11-14-s6-n4-coefficient-sensitivity-protocol.md)
under standing local native permission recorded by merged #65. It preserves the
[N1-N3 evidence](2026-11-14-s6-n123-native-precision.md), including prior failures.
No CMD calculation, N5, routed-flow comparison or default numerical change was performed.

## Before native launch

The original areal archive matched SHA-256
`61c60366f953669a9879c5e2c6619b3c420c3a3dceeb296fa41e91606b3c213f`.
The public typed ZIP reader selected EventID **9091**, 1440-minute duration, 60-minute timestep,
100 km2 area bin and S-SW Flatlands (West) region. All 24 original percentages sum to 100 and
match frozen N1/R1 cells. Native ordinal 1 remains distinct from the original EventID.

N4 synthetic legacy TXT differs from N1 bytes only in LONGARF `e`, changing `0.00000385` to
`3.50E-06`. Complete typed-document comparison found only that coefficient's numeric/raw
representations and source byte/hash metadata changed. Other coefficients, section versions,
location, losses and source profile are unchanged. This is synthetic sensitivity data, not a
published coefficient or authentic site Data Hub export.

A 60-digit Decimal calculation reproduced depth
**121.881439991274182797474760155268189172542334300623332287267 mm**.
The freeze contains 396 complete 24-cell vectors across N1/N4, including both Decimal tie rules
and the previously defined binary32/binary64 casting, operation order, summation and conversion
variants. Binary candidates start from the independent Decimal total; they do not identify a
native transcendental implementation. Full-depth and total-0.01-mm candidates each predicted
24/24 changed rate tokens versus N1, starting at step 1; maximum rate differences respectively
0.0513 and 0.0556 m3/s.

| Private artifact | SHA-256 |
| --- | --- |
| Pre-launch freeze manifest | `27d28a49616ba5f1df753b54b9cef34cb7c48c11d3677ed6754d756da9a103b2` |
| Frozen N1/N4 candidate vectors | `641224c911e38632655b2b8bf9e48ba69fa0bfecf66d93c66eda1fd46929b975` |
| N4 synthetic coefficient TXT | `854481e4ce806aba391e24ff4eacb55a481e2ad99e5081052d09c30ca8d3372d` |
| Completed capture inventory | `f4525a10655a621d08da9575cd4e3327026c6a3e03d87375ac4dee9e61ffe967` |

The freeze preceded fresh process launch and was rehashed immediately before calculation and
after capture. The original 602-file inventory and entire N1-N3 campaign inventory matched
before and after N4. An initial offline freeze assertion needed correction to recognise retained
raw bytes/source size and both representations of `e`; no native process had started. The failed
preparation script is retained privately. Final predictions were frozen before launch.

## Effective inputs and native capture

Executable SHA-256 remains
`0ca65bcef548f26a5f9bceda6c99ed4f545a9498b61c93aa59a00400732d1aea`,
observed RORBwin 6.52 (1 June 2023). Graphical model remains
`189bc5d27f9dddbbdf9d555fa3fb0b79137dd54c9c5d06f4f9a5b02c62b3dc09`.

A fresh process used an isolated N4 directory. Explicit TXT reselection produced the captured
**ARFs updated from ARR file** acknowledgement. Effective design screen: 1% AEP, 24 hours,
100 km2 areal-pattern bin, file ARFs ON, regional losses/preburst/spatial variation/filtering OFF.
Native report and generated storm confirm 100 km2, one-hour steps, 200-increment horizon,
uniform pattern, gross 129 mm, zero IL/CL, `kc=10`, `m=0.8`, original 24 percentages.
Saved parameters retain the N4 source locator. Internal unrounded coefficient values remain
unobservable; the effective storm change supplies sensitivity evidence.

Exactly one calculation was invoked at **2026-11-14 12:36 AWST**. The process exited normally
after parameter save. Private capture retains process record, seed/saved parameters,
acknowledgement/settings screenshots, named generated storm, full report, both 201-record CSVs,
batch output, comparisons and hashes. No separate native log was emitted. The automation library
warned about 64-bit Python controlling a 32-bit application; effective settings, complete outputs
and capture authentication were independently checked. An offline analysis assertion was corrected
to match native parameter print precision, without recalculation or changes to native files.

## Complete comparison results

| Check | N4 result |
| --- | --- |
| Native printed ARF / adjusted depth | **0.94 / 121.88 mm**, versus N1 0.94 / 121.85 mm |
| Changed forcing-rate cells versus N1 | **24/24**, first difference step 1 |
| Initial/tail cells unchanged versus N1 | **177/177** |
| Complete raw export label pairs | **201/201 verified**, unchanged from N1 |
| Full-source comparison, fixed 0.0000018 mm absolute / zero relative | **FAIL 0/24**, first failure step 1 |
| Maximum absolute full-source depth error | **0.0000980474179879925915665023564 mm**, step 8 |
| 121.88-mm printed-depth diagnostic | **FAIL 22/24**, steps 8 and 14 |
| Replay error at each failed step | **-0.0000020 mm**, exceeding unchanged allowance |
| Sum of exported rates converted to depth | **121.8799908 mm** |
| Best frozen candidate four-decimal token matches | **22/24**; no complete candidate match |
| Frozen candidate depth passes | No candidate passes all 24 cells |

Step 8 uses 6.67%: native rate 225.8165 m3/s implies 8.1293940 mm versus replay 8.129396 mm.
Step 14 uses 3.43%: native rate 116.1245 m3/s implies 4.1804820 mm versus replay 4.180484 mm.
These rows remain failures; no candidate was retuned after capture. Raw labels remain intact.
Excess labels retain the previously characterised one-increment offset against hydrograph labels;
this does not validate routed phase or universal timing rules.

**Interpretation:** the changed source coefficient reaches RORBwin's effective storm. The unchanged
source/fallback hypothesis is contradicted for this control. Results support total-depth precision
collapse before the retained disaggregated excess export, while residuals leave exact internal
rounding/arithmetic unresolved. A rounded-total diagnostic is not full-source parity.
N5 is **NOT RUN** because N4 supplies the intended sensitivity discrimination.

## Validation, limitations and next action

Windows/Python **3.14.6** read-only capture verification authenticated all 33 inventoried packet
files and independently recalculated the 24 full-source and printed-depth comparisons.
Repository hygiene/relative-link checks and whitespace checks passed for this documentation batch.
No new full-suite, installed-wheel or hosted-CI result is claimed; reusable numerical code was unchanged.
Private evidence is retained under ignored `.local/s6-n4-coefficient-20261114/` in the N4 worktree;
no original archive, native executable, raw source pattern or capture is committed.

S6 #8 remains **OPEN / NOT ACCEPTED**. Historical R1 0/24 and 23/24 replay failures, other S6
residuals, tolerances, goldens, default methods, S2 routing and CI policy remain unchanged.
Next: inspect frozen step-8/14 diagnostics alongside N1 step 16, then predeclare a targeted
arithmetic/export discriminator if justified. Do not infer the exact native instruction sequence
or introduce a numerical workaround from this evidence alone.
