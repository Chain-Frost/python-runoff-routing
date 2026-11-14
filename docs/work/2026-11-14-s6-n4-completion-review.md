# S6 N4: complete rainfall/excess audit and stack reconciliation

**Status:** N4 sensitivity established; strict equivalence failed; no additional native calculation.
**Owner:** Local Windows agent. **Updated/reviewed:** 2026-11-14.
**Branch:** `docs/s6-n4-complete-20261114`, based on PR #68 head
`fc57c3c0cd3bd98c4daa498074a5875f46c5a584`; delivered as a normal fast-forward update to the
existing PR #68 branch. Exact delivery revision is recorded on [#68](https://github.com/Chain-Frost/python-runoff-routing/pull/68)
and [issue #8](https://github.com/Chain-Frost/python-runoff-routing/issues/8).

This completes the [N4 native result](2026-11-14-s6-n4-native-result.md) audit against the
[preregistered protocol](2026-11-14-s6-n4-coefficient-sensitivity-protocol.md). The captured N4
calculation is reused without rerunning, replacing predictions or changing native evidence.
**Coastal is deferred until the Python routing engine is working and numerically validated.**
No Coastal, CMD routing, ARR2026 generation or general default-pattern investigation was performed.

## Provenance and effective inputs

| Identity | SHA-256 |
| --- | --- |
| Original N1 synthetic coefficient TXT | `dcb5633328cc2c2aa2674c79df9644696408c505b0251cf822530159dcccb0da` |
| N4 synthetic coefficient TXT | `854481e4ce806aba391e24ff4eacb55a481e2ad99e5081052d09c30ca8d3372d` |
| Original areal pattern ZIP | `61c60366f953669a9879c5e2c6619b3c420c3a3dceeb296fa41e91606b3c213f` |
| Original pre-launch freeze manifest | `27d28a49616ba5f1df753b54b9cef34cb7c48c11d3677ed6754d756da9a103b2` |
| Original completed N4 capture inventory | `f4525a10655a621d08da9575cd4e3327026c6a3e03d87375ac4dee9e61ffe967` |

The current typed readers independently reread the archive and both legacy TXTs. Original N1
bytes are recovered exactly by reversing only the N4 LONGARF `e` token replacement. All other
numeric coefficients match. N4 `e=3.50E-06` is synthetic, not a published design recommendation.
The original 602-file inventory, N1-N3 campaign inventory, N4 capture inventory and all frozen
prediction hashes were reauthenticated without modification.

The retained fresh-process capture explicitly selected the new TXT and recorded **ARFs updated
from ARR file**. Effective controls remain 100 km2, 24 hours, 1% AEP, gross 129 mm, FLTwest
EventID 9091/native ordinal 1, 24 original weights summing to 100%, 60-minute steps, zero IL/CL,
file ARFs ON, preburst/regional losses/spatial variation OFF, horizon 200, `kc=10`, `m=0.8`.
Executable and original graphical model hashes are pinned in the native result record.

N4 full-source depth remains **121.881439991274182797474760155268189172542334300623332287267 mm**;
native written depth is **121.88 mm**, versus N1 **121.85 mm**. All 24 nonzero excess-rate cells
changed and all 177 initial/tail cells remained unchanged. The coefficient change therefore
reaches the effective native storm. N5 is **NOT RUN**: its stronger coefficient would repeat
that sensitivity discrimination and does not isolate the remaining arithmetic/export residuals.

## Complete rainfall and excess checks

The generated storm retains all 24 original percentages and serializes one adjusted total at
two decimals. All 24 rainfall cells reconstructed from that written input pass the previously
declared source-to-written-depth print budget (`0.005 mm * percentage / 100`). This is a
reporting/input-serialization check, not strict full-source acceptance.

The native report supplies 24 catchment rainfall values to 0.1 mm and subarea values to whole mm;
the corresponding rainfall-excess tables have the same 24 values. All pass their own printed
half-unit bounds against the written-input rainfall and exported excess, respectively.
Against the full-source rainfall with **only** the 0.05-mm catchment print bound, **23/24** pass:
step 19 reports 6.3 mm versus full source 6.35002302354538492374843500409 mm, difference
approximately -0.0500230235454 mm. Against written-input rainfall 6.349948 mm, its difference
is -0.049948 mm. Keep these comparisons separate; no print budget or strict tolerance was relaxed.

**No separate high-precision rainfall CSV was emitted.** The available CSVs are excess-rate
and routed-hydrograph exports. Excess values and all labels are audited; routed hydrograph
values were not compared. This prevents a label check from becoming a rainfall/routing claim.

All **201/201** excess records and **201/201** hydrograph label records are complete. At sample
index `j=0..200`, excess raw Inc/time are `j+1`, while hydrograph raw Inc/time are `j`.
Sample 0 is the initial zero; samples 1-24 are forcing; samples 25-200 are 176 zero tail rows.
Raw labels are unchanged. Physical rainfall interval for forcing step i is [i-1, i] hours;
this explicit diagnostic association does not rewrite export labels or accept routed timing.

The following sanitised table publishes errors only, omitting original pattern weights and raw
native vectors. Strict decisions use unrounded Decimal errors and the unchanged **0.0000018 mm
absolute, zero-relative** allowance. Displayed source errors below are rounded for this report.

| Step | Excess minus full source (mm) | Excess minus 121.88-mm replay (mm) | Strict full / replay |
| --- | --- | --- | --- |
| 1 | -0.000080431517 | -0.0000008 | FAIL / PASS |
| 2 | -0.000092095447 | -0.0000008 | FAIL / PASS |
| 3 | -0.000094607427 | +0.0000000 | FAIL / PASS |
| 4 | -0.000067471596 | -0.0000008 | FAIL / PASS |
| 5 | -0.000047423720 | -0.0000012 | FAIL / PASS |
| 6 | -0.000066175604 | -0.0000008 | FAIL / PASS |
| 7 | -0.000068079590 | -0.0000004 | FAIL / PASS |
| 8 | -0.000098047418 | -0.0000020 | FAIL / FAIL |
| 9 | -0.000062975626 | -0.0000012 | FAIL / PASS |
| 10 | -0.000078895512 | +0.0000016 | FAIL / PASS |
| 11 | -0.000062207623 | +0.0000000 | FAIL / PASS |
| 12 | -0.000030943803 | +0.0000016 | FAIL / PASS |
| 13 | -0.000039407754 | +0.0000012 | FAIL / PASS |
| 14 | -0.000051391701 | -0.0000020 | FAIL / FAIL |
| 15 | -0.000058319647 | +0.0000000 | FAIL / PASS |
| 16 | -0.000042159747 | -0.0000004 | FAIL / PASS |
| 17 | -0.000047871705 | +0.0000008 | FAIL / PASS |
| 18 | -0.000072495556 | +0.0000008 | FAIL / PASS |
| 19 | -0.000076623545 | -0.0000016 | FAIL / PASS |
| 20 | -0.000070143585 | -0.0000016 | FAIL / PASS |
| 21 | -0.000040863755 | -0.0000004 | FAIL / PASS |
| 22 | -0.000014335918 | -0.0000008 | FAIL / PASS |
| 23 | -0.000033007798 | +0.0000004 | FAIL / PASS |
| 24 | -0.000053215682 | -0.0000008 | FAIL / PASS |

Full-source excess remains **FAIL 0/24**, first failure step 1. Maximum absolute error is
**0.0000980474179879925915665023564 mm**, step 8. The 121.88-mm diagnostic remains
**FAIL 22/24**, steps 8/14 both -0.0000020 mm. Exported-rate reconstructed depth sums to
121.8799908 mm; it is not a replacement for the full-source storm total.

## Disposition of all predeclared hypotheses

Each prediction is expanded to the complete 201-record grid: leading zero, 24 frozen rates,
176 tail zeros. For N4 there are 198 numeric candidate/rounding combinations; the original N1
capture supplies the separate predeclared unchanged-source comparison. Both Decimal tie rules
are retained; no arithmetic variant or coefficient was fitted after seeing N4.

| Frozen hypothesis family | Variants | Best forcing token match | Best complete-grid token match | Disposition |
| --- | --- | --- | --- | --- |
| H-FULL-OUTPUT | 2 | 0/24 | 177/201 | Rejected for this export under both declared rounding rules |
| H-TOTAL-2DP, exact Decimal disaggregation | 2 | 22/24 | 199/201 | Exact model fails steps 8/14; broader total-first interpretation remains consistent |
| H-STEP-2DP | 2 | 0/24 | 177/201 | Rejected for this export |
| H-F32, all declared orders/bases | 96 | 22/24 | 199/201 | No exact survivor; at most 23/24 depth-budget passes, a separate metric |
| H-F64, all declared orders/bases | 96 | 22/24 | 199/201 | No exact survivor; at most 22/24 depth-budget passes |
| H-NO-EFFECTIVE-CHANGE | N1 capture | 0/24 | 177/201 | Rejected after explicit source reselection and effective-storm change |

**Quantisation conclusion:** two-decimal serialization of the generated total is demonstrated in
the retained `.stm`. Total-depth quantisation before disaggregation remains **consistent with
observations**, not established as the complete internal mechanism. The precise frozen Decimal
total-first model fails two cells, and every declared float-order candidate also fails complete
token reproduction. Neither the loading acknowledgement nor the saved rounded coefficient cache
reveals internal precision. These results narrow the question without accepting a workaround.

## Stack reconciliation and validation

The fetched stack was already synchronized by provenance-preserving ancestry commits:

| Ref | Reviewed head | Intended base |
| --- | --- | --- |
| main | `1c2fdb0507e38d0a61718aa8f1ab11fa028c2dd2` | Owner-controlled main |
| PR #56 | `e3a874e5cc5cd38c337a4d6bcefeac25927104d6` | main |
| PR #64 | `72b7cf351c28f4b3ced15846350c90df6202bb32` | #56 |
| PR #68 before this completion update | `fc57c3c0cd3bd98c4daa498074a5875f46c5a584` | #64 |

Each base is an ancestor of its child. Diffing every layer and the cumulative stack against main
shows only S6 evidence Markdown and work-register changes: no historical source implementation,
test, tolerance, golden, executable or workflow is reintroduced. Current main's active register
is preserved; selected S6 next actions are updated for this owner's scope and Coastal deferral.
PR descriptions are refreshed to distinguish historical review limitations from current evidence.
No force-push, merge or closure is performed. Earlier source revisions and captures remain intact.

Windows/Python **3.14.6** ran the independent read-only completion audit, original capture verifier,
and repository/link/whitespace checks. Private completion evidence under ignored
`.local/s6-n4-completion-20261114/` contains complete 24-cell rainfall/excess and 201-row audits,
all candidate checks, summary and hashes. Existing raw files stay in their original private
locations. This documentation batch adds no package implementation and claims no new full-suite,
installed-wheel or numerical acceptance result. Earlier exact-head software CI remains separate.
Completion packet inventory SHA-256:
`864896f1216b5f9eaf7b2576c3ba3b7f8a6c0ce34e978dc8ead6279eec9a61cb`.
Local repository/link check: **159 files, 0 errors**; whitespace check passed. The previously
synchronized #56/#64/#68 heads each have a successful Windows quality check, respectively
[43557749021](https://github.com/Chain-Frost/python-runoff-routing/actions/runs/43557749021),
[43557850569](https://github.com/Chain-Frost/python-runoff-routing/actions/runs/43557850569), and
[43557988786](https://github.com/Chain-Frost/python-runoff-routing/actions/runs/43557988786).
Those checks apply to the reviewed heads above, not automatically to this follow-up commit.

## Remaining failures and next evidence

Preserve R1 strict **0/24**, its printed-depth **23/24** step-16 failure, N4 strict **0/24** and
replay **22/24**, six R2-R5 strict residuals and separate R7 step-31 below-boundary failure.
The merged experimental full-increment CL profile stays explicitly opt-in. S6, routed-engine
equivalence and timing acceptance remain open; **keep issue #8 open**.

Next evidence should distinguish the two N4 rounding-boundary residuals from N1 step 16. First
compare the retained frozen intermediate depth/rate bits and printed tokens offline across those
rows. If no declared variant separates plausible causes, predeclare a narrowly selected native
serialization/arithmetic control with distinguishing full-vector predictions before executing it.
N5's larger `e` alone is not that discriminator. Do not change default mathematics, relax a
tolerance, regenerate a golden or investigate Coastal to resolve this bounded question.
