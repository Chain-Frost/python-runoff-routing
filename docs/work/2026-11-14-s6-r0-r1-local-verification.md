# S6 R0/R1: local reauthentication and frozen precision controls

**Owner correction, 2026-11-14:** there is no three-run limit. The cap in the original handoff
and frozen protocol is superseded; it is not a blocker to further relevant local experiments.

**Current status:** [N4 completion review](2026-11-14-s6-n4-completion-review.md) confirms the
later N1-N4 campaign and unchanged evidence. Standing permission is merged in #65; no current
three-run cap or launch-authorisation blocker applies. Earlier statements below are historical.

**Native follow-up completed:** [N1-N3 results](2026-11-14-s6-n123-native-precision.md) supersede
the prospective NOT RUN/reopen status below. Exactly three calculations were performed; all
repeat the strict failure. This record preserves the offline freeze and its original outcomes.

**Owner clarification, 2026-11-14:** standing permission covers local RORBwin and RORB_CMD launches
and calculations without further authorisation. The authority blocker reported below is superseded;
the frozen N1-N3 protocol can proceed within its three-calculation limit. The earlier NOT RUN labels
still describe the actual execution status of this offline batch. A separate AGENTS.md correction
is proposed against main on branch `docs/native-run-standing-permission-20261114`.

**Status:** offline verification complete; R0 retained timing mapping passes for the bounded profile;
R1 strict excess **FAIL**; native N1-N3 **NOT RUN** because applicable authority was not established.
**Owner:** Local Windows agent. **Updated:** 2026-11-14. **Review:** before any new native calculation.
**Stage:** [#8](https://github.com/Chain-Frost/python-runoff-routing/issues/8), open.
**Branch:** `docs/s6-r0-r1-local-verification-20261114`.
**Starting revision:** `d61fdadc91d74e9379d861c53a939ad982dc4898`, [draft #56](https://github.com/Chain-Frost/python-runoff-routing/pull/56).
Delivery revision and follow-up draft PR are recorded in the linked stage issue after commit/push.

This record supersedes the local-unavailable and timing-open gates in the
[earlier audit](2026-11-14-s6-r0-r1-precision-audit.md) only where explicitly rechecked below.
It changes documentation only. The retained experiments still use historical implementation
`b2c89eae7517d1117fd522f24a1897ab7622823d`; current implementation PR #50 has since merged.
Draft #54 has separately advanced to `367ca4cdf53879d4e4615bbe789746b0e06dc483` when checked.
Neither that newer implementation nor its installed wheel is numerically revalidated here.
This follow-up stays stacked on #56 without changing its branch or the experimental profile.

## Fresh verification and effective settings

Windows CPython **3.14.6** read the original private evidence without launching RORBwin.
The new read-only private inventory contains **602 files**, relative locators, sizes and SHA-256s.
All 602 were rehashed after analysis and remained unchanged. Separately, **32 anchor checks pass**:
all **10 R0 + 11 R1** files against their original capture inventories, four frozen source files,
their four original Downloads copies, the installed executable and two original tolerance policies.
Current hashes without an older anchor are labelled fresh hashes only; this is not proof of their
historical capture time. Original sources, native outputs, parameters and goldens were not edited.

The four BoM/ARR source hashes match the full expected identities in the earlier audit:
`depths_margaret_river_ifds.csv`, `depths_margaret_river_all_design.csv`, `Areal_FLTwest.zip`
and `FLTwest.zip`. In particular the areal archive remains
`61c60366f953669a9879c5e2c6619b3c420c3a3dceeb296fa41e91606b3c213f`.
The installed executable is **10,923,068 bytes**, SHA-256
`0ca65bcef548f26a5f9bceda6c99ed4f545a9498b61c93aa59a00400732d1aea`.
Both retained reports identify **6.52, last updated 1 June 2023**. This is a fresh executable hash
and retained-banner check, not a fresh-process version observation.
Both graphical models retain SHA-256
`189bc5d27f9dddbbdf9d555fa3fb0b79137dd54c9c5d06f4f9a5b02c62b3dc09`;
their header identifies `RORB_GE 6.52` and reports confirm **100 km²**, one pervious subarea,
one 1 km natural reach, kc=10, m=0.8, one-hour steps and a 200-step horizon.

Final named storms, saved parameters, reports and all 24 source percentages establish **24 h / 1% AEP**,
areal bin 100, original **EventID 9091**, separately labelled native deterministic **ordinal 1**.
Rainfall starts at zero; IL/CL are **0/0** in saved effective parameters and retained outputs.
The R1 design screenshot confirms file ARFs ON, regional losses OFF, preburst OFF and spatial
variation OFF. R0's retained parameters/design and exact 129-mm storm support ARF OFF.
Preliminary default 63.2% storm files remain inventoried but excluded from effective inputs.
Screenshots were inspected as historical captures; current GUI state was not inspected.

The synthetic TXT's SHA-256 remains
`dcb5633328cc2c2aa2674c79df9644696408c505b0251cf822530159dcccb0da`.
It supplies the full published SW WA coefficients, including e=0.00000385, h=0.00817, i=-0.00045.
Its synthetic losses are not effective run losses and it is not an authentic site Data Hub export.
The saved R1 coefficient line instead has **e=0.0000, h=0.0082, i=-0.0004**, and retains the TXT
locator. A screenshot of the manual coefficient editor shows zero fields despite the file-ARF
selection: that display is not evidence of the effective computational coefficients.
The source-selection capture supports file use, but neither the report nor cached bytes identify
the unrounded internal values. Save-time in-memory effects and fresh-process reload remain unresolved.

## R0 version-specific time mapping

Fresh comparisons account for **201/201** original records in each R0/R1 export family:
one initial zero, 24 forcing records and 176 trailing zeros. Native text explicitly gives rainfall
and excess in the interval *following* time shown, with starts 0 through 23. The storm starts at
zero and has 24 one-hour increments. All 24 source weights match the original archive.

For forcing index **i=1..24**, the retained mapping is:

| Quantity | Value for forcing i |
| --- | --- |
| Native text interval start | i-1 hours |
| Physical forcing interval | [i-1, i] hours |
| Original CSV sample index | i (zero-based, after initial zero) |
| Hydrograph CSV raw Inc / Time | i / i hours |
| Excess CSV raw Inc / Time | i+1 / i+1 hours |

Sample index 0 has hydrograph labels 0/0 and excess labels 1/1; its zero does not represent an
extra rainfall interval. Samples 25..200 are trailing zeros. Every paired export row differs by
exactly +1 increment in the excess labels. The independently authored retained 30-minute control
was reread: all **13/13** export pairs differ by **0.5 h**, supporting one increment, not one hour.
Raw labels are preserved in separate 201-row comparison files; no export is rewritten.

**Verdict: PASS for the retained R0 forcing/excess association and its explicit mapping contract.**
Existing storm/text ordering, complete zero structure, 24 numerical matches and the independent
half-hour control suffice for this bounded interpretation; another timing run is unnecessary.
This does not accept routed phase, interpolation/internal sampling, RORB_CMD, other builds,
variable timesteps or a universal parser correction. Broader S6 timing acceptance remains open.

## Complete-vector precision results

The original absolute allowance remains **0.0000018 mm**, relative **0**.
Conversion remains exact Decimal **depth_mm = rate_m3_s × 0.036**.

| Check | Pass count | First failure / maximum absolute residual |
| --- | --- | --- |
| R0 generated rainfall | 24/24 exact | None |
| R0 raw excess versus source | 24/24 | None; 0.0000012 mm maximum |
| R1 rainfall at printed-depth allowance | 24/24 | Printed precision only |
| R1 raw excess versus full source | **0/24** | Step 1; 0.000249621529950082272279045 mm maximum |
| R1 raw excess versus 121.85-mm replay | **23/24** | **Step 16; +0.0000020 mm** |

The independent calculation uses adjusted total × weight/100. Comparing it to the original
source's gross increment × ARF shows at most **2E-27 mm** regrouping difference at Decimal precision 28.
This accounts for the final digit differing from the earlier reported maximum ending `044`.
The original source predictions and failures are retained; no material acceptance result changes.
An independently regrouped **60-digit** Decimal equation confirms both coefficient-pair totals
to better than 1E-24 mm. Full adjusted depth is **121.8537574442271376652515599 mm**;
sensitivity e=3.845E-06 gives **121.8541529091849525957118913 mm**. Both display 121.85 mm.

The two-decimal replay strongly supports effective total-depth quantisation or an equivalent
pathway over display-only rounding of full source depth. It does not prove where rounding occurs:
the effective coefficients, generated-storm serialization and reload path remain competing causes.
Per-cell two-decimal rounding, full-depth, output-only and explicit binary alternatives are retained
as independent diagnostic vectors, not substituted for the source acceptance contract.

### Step 16 and arithmetic-order diagnostics

The native token is **98.1570 m³/s**, raw Inc **17**, time **17.000 h**; text interval start is
15 h and physical end is 16 h. Exact conversion gives **3.5336520 mm**.
The 121.85-mm replay gives **3.53365 mm**, with exact rate **98.156944444... m³/s**.
Nearest four-decimal printing alone predicts **98.1569**, not 98.1570: the observed residual
exceeds the half-export allowance by **0.0000002 mm**. Ordinary binary64 orders do not explain this.

One explicit binary32 candidate casts inputs, computes `depth × weight / sum`, rounds each
operation to binary32, then computes `rainfall × 100 / binary32(3.6)` with a cast after each operation.
Its step-16 rainfall is **3.5336501598358154296875 mm**, rate
**98.156951904296875 m³/s** (binary32 bits `42c4505c`), which prints **98.1570**.
Across R1 it reproduces **24/24 printed rate tokens** and places **24/24 raw rates** within the
unchanged export allowance of its preformatted candidate rates. However, comparing converted
native depth directly to that candidate's intermediate rainfall passes only **21/24**; the final
conversion also contributes rounding. Step 16 remains **0.0000018401641845703125 mm** from that
intermediate rainfall, still above the frozen depth limit. These are distinct comparisons.

This reproduces a plausible arithmetic/export pathway, not identified native instructions.
The alternative weight-first/factor-first binary32 order produces the same step-16 token but
not the same complete R1 match. The earlier R2-R4 investigation already found no one order
matching all 98 retained R1-R4 tokens. No new R2-R4 search or native calculation was performed.
**Native cause remains UNRESOLVED; full-source and printed-depth numerical acceptance still FAIL.**

## Frozen future controls and private deliverables

The ignored private packet is `.local/s6-r0-r1-verification-20261114/` in the isolated worktree.
It retains a read-only inventory, anchor checks, both complete time grids, both 24-cell comparisons,
all candidate vectors and signed/absolute diagnostics, step-16 details, parameter-byte comparison,
acceptance matrix, protocol, synthetic paired coefficient files and output hashes.
No original captures, rainfall archives, manuals or executables are added to public Git.

There are **396 complete 24-cell vectors / 9,504 prediction rows**: Decimal full/total-rounded/
step-rounded and controlled binary32/binary64 alternatives, both coefficient inputs and both
half-even/half-up final rounding modes. Binary alternatives explicitly vary three rainfall orders,
four conversion orders, exact versus sequential weight summation and full versus rounded total.
Each binary operation is cast explicitly; exact float values, binary64 hex and binary32 bits are
retained. Binary ARF transcendental evaluation is not identified; these candidates cast the
independent Decimal adjusted total before disaggregation. Existing-data comparisons are
retrospective; the same vectors are now frozen before any N1-N3 execution.

| Private artifact | SHA-256 |
| --- | --- |
| 602-file inventory | a68dbeb68f066e21f484555aa2eb7f7ea01ec40fa80662b5aadb11f0cc99d499 |
| All complete candidate vectors | cf5683136b5f78d743cc79c3d2442b1adc549a87b32faaa7cef6c2cb1a7665ba |
| Published-coefficient synthetic control | dcb5633328cc2c2aa2674c79df9644696408c505b0251cf822530159dcccb0da |
| Sensitivity synthetic control | b974607802d20199fa8576790d5dec3e2f019a34fd3fc629183b3e12f82584f3 |
| Initial output hash manifest | 239d13cc24cddb70966545683788699d8deef677315cc909915ac736607877c9 |

The source inventory and predictions are frozen before native runs. The separately named
sensitivity TXT changes only e; no original coefficient file is edited. Same-rounded-total
Decimal predictions are identical for the two controls; full-depth predictions produce different
exported rates, independently checked before any native calculation.

**N1, N2, N3: NOT RUN.** The handoff explicitly requires existing RORBwin-specific authority.
The live issue, available work records and retained protocols establish historical bounded
calculations, not permission for this new three-run campaign. No new process was launched.
The frozen protocol specifies isolated processes/directories, complete inputs/outputs/screenshots,
pre/post-save/reopen parameter bytes, source-selection verification, unchanged tolerances and a
hard maximum of three calculations. An ineffective coefficient source means **INVALID INPUT**,
not evidence for quantisation. No new invalid calculation occurred here.

**Next action:** obtain owner authority for that frozen N1-N3 protocol. The single most useful
experiment is the **N1/N2 coefficient pair**, holding all other verified effective inputs fixed;
it distinguishes same-rounded-total disaggregation from surviving full precision. N3 independently
tests reload/cache behaviour. Saving representation loss is observed; saving in-memory changes,
closing/reopening effects and recalculation differences remain **UNRESOLVED / NOT RUN**.

## Relationship to other stages and validation

R2-R4 and R5 were already run and remain recorded with strict residual failures. Later R6/R7
also ran, as the live issue and current #54 describe; old NOT RUN wording in earlier records is
historical. This slice repeats none of them. Input-depth quantisation, arithmetic/export precision,
full-increment CL, IL crossing and preburst/burst origins remain separate. The opt-in experimental
loss profile remains explicitly selected and unaccepted. S2, default loss code, tolerances,
goldens, CI and package metadata are unchanged. No routed comparison or S6 closure is claimed.

Windows/Python 3.14.6 executed the private offline calculation and a separate read-only verifier:
original/frozen hashes, all 396 complete vectors, independent 60-digit totals, coefficient-pair
discrimination, source-reference comparison, exact step-16 nearest rounding and captured profile
checks pass. Public documentation repository/link hygiene and whitespace are checked for this
batch. No first-party numerical code was introduced, so no new full-suite, Ruff/Pyright or
installed-wheel result is claimed. Historical quality results do not establish current native parity.
