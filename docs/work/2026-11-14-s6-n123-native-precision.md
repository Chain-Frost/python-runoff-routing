# S6 N1-N3: native coefficient pair and saved-parameter reopen

**Current follow-up:** [N4 completion review](2026-11-14-s6-n4-completion-review.md) supersedes
the historical next-action paragraph below: N4 is complete, source sensitivity is established,
strict residuals remain, and N5 was unnecessary. This N1-N3 capture is preserved unchanged.

**Owner correction, 2026-11-14:** there is no three-run limit. The owner has removed the
handoff's cap; further relevant local experiments may proceed under standing permission.
Three runs describes this completed batch, not a current restriction.

**Status:** three native calculations completed; strict rainfall/excess equivalence still **FAIL**.
**Owner:** Local Windows agent. **Updated:** 2026-11-14. **Review:** before selecting another experiment.
**Branch:** `docs/s6-r0-r1-local-verification-20261114`; starting revision
`13387e7bbfe488328bce800862c425fc61848ca7`. Delivery revision is recorded in
[issue #8](https://github.com/Chain-Frost/python-runoff-routing/issues/8) with
[draft PR #64](https://github.com/Chain-Frost/python-runoff-routing/pull/64).

This follows the [offline reauthentication](2026-11-14-s6-r0-r1-local-verification.md).
The owner confirmed standing permission for local RORBwin and RORB_CMD execution without further
authorisation. [PR #65](https://github.com/Chain-Frost/python-runoff-routing/pull/65) passed its
Windows quality workflow and was merged at **0d6735adc7b60262fbf4444d10f76eb43115fad3**;
main now records that permission in AGENTS.md. This removes the earlier authority blocker.
This batch performed exactly three calculations, no CMD run,
and no R2-R7 or routed comparison was repeated.

## Frozen inputs and actual process control

All 396 complete prediction vectors were frozen before N1, SHA-256
`cf5683136b5f78d743cc79c3d2442b1adc549a87b32faaa7cef6c2cb1a7665ba`.
Published and sensitivity TXT hashes are respectively
`dcb5633328cc2c2aa2674c79df9644696408c505b0251cf822530159dcccb0da` and
`b974607802d20199fa8576790d5dec3e2f019a34fd3fc629183b3e12f82584f3`.
Only coefficient **e=3.85E-06 versus 3.845E-06** differs between these files.
The full-precision predicted storm depths differ by about **0.000395464958 mm** but both display
**121.85 mm**. Source predictions, tolerances and original captures were not regenerated.

Each calculation used an isolated fresh process and private output directory, the original
100 km² pervious graphical model, 24 h / 1% AEP, one-hour steps, source EventID **9091** distinct
from native ordinal **1**, kc=10, m=0.8, horizon 200, zero IL/CL and no regional losses/preburst/
spatial variation. Native output reconfirms the model and engine profile; source/model/TXT hashes
are checked in each capture. Installed executable SHA-256 remains
`0ca65bcef548f26a5f9bceda6c99ed4f545a9498b61c93aa59a00400732d1aea`, banner **6.52, 1 June 2023**;
model SHA-256 remains `189bc5d27f9dddbbdf9d555fa3fb0b79137dd54c9c5d06f4f9a5b02c62b3dc09`.

| Calculation | Actual source handling | Outcome |
| --- | --- | --- |
| N1 | Fresh process; explicitly reselected published TXT; native acknowledgement: ARFs updated from ARR file | Completed once; saved native parameters after calculation |
| N2 | Fresh process; explicitly reselected sensitivity TXT; same native acknowledgement | Completed once; saved native parameters after calculation |
| N3 | Fresh process opened N1's saved parameters with only owning directory/output path changes; original TXT available; no coefficient reselection | Completed once; saved parameters after calculation |

Screenshots retain design/source flags, the ARF-read acknowledgements for N1/N2 and parameter
dialogs. Named generated storms, both CSVs, full reports, batch outputs, seed/saved/reopened
parameter bytes, process IDs, calculation-start records and hashes remain private.
N3 had an initial GUI startup/menu-command timeout **before calculation**; that process ended and
its process record is retained separately. A fresh process opened the saved file through the
explicit menu and calculated once. N1 had an automation wrapper error while saving its completed
run; it was corrected in the same process, without recalculation. No failed numerical run was hidden.

## Complete-vector results under the original allowance

The unchanged allowance is **0.0000018 mm absolute, zero relative**; exact conversion remains
**rate_m3_s × 0.036 = depth_mm**. All 24 source percentages match; all three storms report
ARF **0.94** and adjusted depth **121.85 mm**.

| Case | Full-precision source passes | Maximum full-source difference, mm | Printed-depth replay passes | First replay failure |
| --- | --- | --- | --- | --- |
| N1, published | **0/24**, first failure step 1 | 0.000249621529950082272279045 | **23/24** | Step 16, +0.0000020 mm |
| N2, sensitivity | **0/24**, first failure step 1 | 0.00027599904263633813398315 | **23/24** | Step 16, +0.0000020 mm |
| N3, reopened | **0/24**, first failure step 1 | 0.000249621529950082272279045 | **23/24** | Step 16, +0.0000020 mm |

N1/N2 excess rates are identical for **201/201** records, including all 24 forcing cells.
N1/N3 are also identical **201/201**, as is N1 versus the original retained R1 capture.
Each complete export has one initial zero, 24 forcing cells and 176 trailing zeros. Both raw
export axes reproduce the previously established one-increment label offset on all 201 rows.
There is no timestamp rewriting and no numerical comparison of routed hydrograph values.

**Interpretation:** identical coefficient-pair outputs support a common quantised preparation/
disaggregation path over survival of the two independently predicted full-precision depths.
Display-only rounding of those distinct depths cannot explain identical exported vectors.
However, the GUI acknowledgement proves file selection/read, not the exact internal coefficients:
input parsing, coefficient quantisation or an equivalent earlier collapse remain alternatives.
Therefore rounding the total to 0.01 mm **before** disaggregation is strongly supported but its
exact location/internal mechanism remains **UNRESOLVED**, not proven native arithmetic.

Step 16 repeats **98.1570 m³/s → 3.5336520 mm**; printed-depth Decimal replay remains
**3.53365 mm**. Final four-decimal nearest printing alone is insufficient. Previously frozen
binary32 candidates can reproduce this token and one order reproduces the full R1 rate vector;
that does not accept the source rainfall or identify the actual instructions. No Python
numerical implementation, golden or allowance was changed to make these comparisons pass.

## What save/reopen establishes

All three GUI-saved coefficient rows are identical, with **e=0.0000, h=0.0082, i=-0.0004**.
The full TXT inputs and selected source locators remain intact. N3's reopened bytes are checked
against N1's saved bytes with only the documented path substitutions. N3 recreates the same
written storm and all excess rates, so **no numerical change is observed on this reopen path
with the source TXT available**.

An independent Decimal evaluation using only the nine rounded saved-cache coefficients predicts
**122.1335607271614543061130213298606352717 mm**, unlike native **121.85 mm**.
This contradicts simple direct use of only those cached decimals under the same ARF equation.
It supports use of the source TXT or another preserved higher-precision representation, but does
not uniquely identify which. Save-time mutation of in-memory state was not isolated by a separate
post-save calculation; missing/unavailable TXT reload behaviour was not tested. These are
limitations, not passing controls.

## Private records, checks and next action

Ignored `.local/s6-n123-20261114/` retains three capture manifests, all original inputs/outputs,
complete 201-row time grids, 24-cell signed/absolute comparisons, candidate comparisons, saved/
reopened parameter differences, protocol/authority links and the startup limitation.
Campaign inventory SHA-256:
`a8212b0308547b9ad3904e05e0955489102f6c090507baa8334b3beede57caa3`.
The separate post-campaign check confirms **all 602 original inventoried files unchanged** and
the frozen prediction hash unchanged. Original tolerance JSONs remain unchanged.

Windows/Python **3.14.6** executed the capture checks and independent offline analysis.
Documentation repository/link hygiene and whitespace are checked for this batch. There is no
new package source, full-suite, installed-wheel or current-code numerical acceptance claim.
R2-R7 remain historical completed investigations with their existing failures/limitations;
the explicitly selected experimental full-increment CL profile remains unaccepted.

**Next:** the most useful additional control would select a coefficient perturbation large enough
to alter the displayed total, with explicitly verified file loading and a distinct saved/reopen
path, to separate coefficient parsing from total-depth quantisation. It was **not executed**:
that was the original batch boundary, now superseded by the owner's correction. Define and freeze
the next experiment's inputs and predictions before calculating; no new launch permission is required.
S6 #8 remains open. No S2/default loss changes, merge of the numerical drafts, release or issue closure.
