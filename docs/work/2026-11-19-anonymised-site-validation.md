# Four anonymised existing-model sets: routing and rainfall audit

Extended by [the fifth-set addendum](2026-11-19-anonymised-site-e-validation.md). The four-set counts below remain a separate dated receipt.

Dated 19 November 2026. Owner-authorised local validation; publication is limited to anonymised Markdown and issues. No original models, rainfall tables, reports, hydrographs, local paths, project names or locations are distributed.

All four sets were inventoried and all 23 catchment files were screened. Original product CATG import admitted **0/23**; all **111** saved parameter files were recognised but unsupported. Diagnostic derivatives permitted a **259-event numerical sample across 7 model files**: **207 complete printed-series matches / 52 differences**. This is not a claim that every saved event was numerically executed or that the original projects run unchanged.

## Coverage and distinct states

| Anonymous set | CATG files | Saved PAR files | Output files | Storm files |
| --- | ---: | ---: | ---: | ---: |
| A | 6 | 47 | 21354 | 28095 |
| B | 10 | 25 | 430 | 403 |
| C | 1 | 2 | 0 | 2 |
| D | 6 | 37 | 1336 | 1309 |

The inventory contains 76,601 files in total. All **23,120 output files** received a canonical report/input preflight; all **29,809 storm files** received a reconstruction attempt with explicit unsupported/missing-source outcomes. File counts include copies and variants; they are not counts of independent catchments or successful calculations.

| Set | Ready for diagnostic routing | Unsupported catchment computation | Other input gap | Batch/other report |
| --- | ---: | ---: | ---: | ---: |
| A | 8510 | 10620 | 2180 | 44 |
| B | 10 | 327 | 51 | 42 |
| C | 0 | 0 | 0 | 0 |
| D | 841 | 224 | 240 | 31 |

**Totals:** 9,361 ready, 11,171 unsupported catchment, 2,471 other input gaps, 117 batch/other outputs. The input gaps comprise **2,180 missing explicitly declared storms** and **291 other unsupported storm/input combinations**. A ready record is structural preflight only, not proof of complete native tables or a numerical pass. Set C has workbook results, including a hydrograph sheet, but no standard event `.out` files; workbook data were not promoted to verified native references.

## What the original readers rejected

Original CATG errors cover background-image flags, graphical node annotation/continuation records, multiple physical prints and version 6.52. No production parser gate was disabled. A local derivative used a characterised graphical scaffold, retained numerical record order/operands, and made implicit natural reach type 1 explicit. One model received an identified output-only terminal diagnostic print. The maintained CATG decoder then admitted 10 computational representations; this does not accept the original graphical files.

The remaining 13 computational representations stopped explicitly: six with storage sections, three with control 8, two with control 7.1, one with 7.2 and one with a zero-length reach. No control was coerced, no routing operation removed, and no positive length substituted. 3 of the ten representable models had no eligible event/reference combination in the numerical sample. See [issue #197](https://github.com/Chain-Frost/python-runoff-routing/issues/197), the existing [single feature matrix](../CMD_FEATURE_MATRIX.md), and the separate [saved-PAR scope #144](https://github.com/Chain-Frost/python-runoff-routing/issues/144).

## Routing comparison

The final selection retained the minimum/maximum declared-storm depth in each model/routing/loss/timestep/rainfall-bin/basis group, with path order only breaking selection ties. Eligible earlier pilot selections were also retained. This is a deterministic 259-event coverage sample, not an exhaustive replay of all 9,361 ready records or all temporal-pattern members. Storms are selected exclusively from the explicit source path inside each native report, with only the documented Q-to-W drive mapping. A similarly named neighbouring storm is not accepted. Some copied result folders contain reports referencing a different rainfall scenario; preliminary basename-paired calculations were discarded and are not included in this final numerical result.

The 259 comparisons contain **259 distinct computational input identities** and **259 source kernel invocations**. Every selected event was freshly calculated from source and again from the installed wheel. Only descriptive storm titles and parameter-reference paths are normalised for input-identity comparison. Each native event report is compared independently: **451 site series / 90,651 ordinates**. Observed report versions are 6.45 (256 events) and 6.52 (three events); executable identities remain unverified.

Of the 207 fully matching events, **104 have nonzero reference flow**. There are **103 all-zero reference events** in the sample; their peak times and percentage denominators are undefined. Every selected comparison retained full-horizon Q, strict printed-resolution status, peak magnitude, raw clocks/index order and physical trapezoidal-volume differences. No clock shift, native-reference regeneration or tolerance relaxation was used. Physical integrals are not native inclusive reported-volume fields or a conservation qualification. Per-event/site metrics are in [the anonymous case table](2026-11-19-anonymised-site-cases.md).

| Set | Sampled events | Full printed match | Difference | Executed model files |
| --- | ---: | ---: | ---: | ---: |
| A | 191 | 146 | 45 | 2 |
| B | 3 | 1 | 2 | 2 |
| C | 0 | 0 | 0 | 0 |
| D | 65 | 60 | 5 | 3 |

For both gross source rainfall and rainfall excess, **258 events are within the native printed intervals**; **one event is not assessed** because the native input increment convention does not map to the candidate pattern under this diagnostic. These checks use original printed numeric intervals and preserve source order; interval agreement does not prove native hidden-state input identity.

Differences remain **diagnostic/unqualified**, not confirmed routing defects. Parameters came from each individual report, not its batch summary or a similarly named current PAR. Printed settings can differ from both and can lose full-precision IL/CL values. Current source geometry/storm hashes are retained locally, but historical input hashes and executable hashes are unavailable. Report banners/observed versions do not establish RORBwin versus CMD executable provenance. The archived observations remain separate from the qualified CMD 6.44 public corpus. Bind full effective settings and historical geometry before attributing these differences to the solver.

## Rainfall and actual regenerated STM files

Raw workflow attempts reconstructed **0/29,809 storms**. This includes unsupported storms, missing/ambiguous dependencies and reader failures; it does not mean 29,809 rainfall calculations failed. In supported source chains, trailing empty coordinate-metadata columns blocked BoM import. [Issue #196](https://github.com/Chain-Frost/python-runoff-routing/issues/196) contains an independently executed authored synthetic reproducer.

A diagnostic derivative removed only trailing empty preamble cells, retaining the rainfall matrix. Source IFD, Data Hub and pattern files were bound through a unique saved-PAR dependency set for the event directory, not chosen to fit target depths. Existing BoM/ARR readers, published regional ARF calculations, original temporal-pattern source order and the explicit two-decimal depth policy then generated new STM text. No additional climate factor or losses were applied to already supplied rainfall. Unsupported rare-frequency/sub-30-minute extrapolation remained rejected.

Point-pattern global ordinals were retained separately from frequency-group/source EventIDs. Where an original point-pattern choice conflicts with the current area-based product selection, the result is explicitly a native-choice source replay, not a pass of product pattern selection. Original timestep text precision, horizon and subarea cardinality were supplied explicitly; the full conditional saved-PAR workflow was not regenerated.

**Final numerical rainfall findings:**

- **10,250** regenerated storms exactly match the saved numerical storm model after the padding-only workaround and explicit original point-choice replay where needed.
- **10** additional storms initially differed by 0.01 mm using the rounded printed catchment area. Recomputing with the full sum of current CATG subareas generated exact matching STM numerical fields for all ten. This is a demonstrated area-precision sensitivity, not evidence of an ARF formula defect; the historical generator area remains unverified.
- **909** uniform-method attempts differ from native non-uniform spatial rainfall; some also require embedded filtering. These are unsupported preparation features, not accepted same-input rainfall or routing failures.
- **18,640** storms remain not reconstructed under the bounded method for the reasons below.

| Remaining reconstruction gap | Storm files |
| --- | ---: |
| No unique source-identified PAR dependency set for this event directory | 8597 |
| Original probability outside bounded deterministic ensemble selection | 7206 |
| ARR ARF durations below 30 minutes require explicit extrapolation opt-in | 2160 |
| Combined pre-burst timing or uniform rainfall depths are not characterised | 656 |
| Multiple pluviographs, ISAs or bursts not characterised | 17 |
| BoM probability label '' was not present | 2 |
| Only title followed by an explicit DESIGN storm is supported | 2 |

Of the 10,250 primary exact matches, 3,780 used current product temporal selection and 6,470 used an explicitly different original point-pattern choice. The ten area-sensitivity matches are reported separately. Local receipts preserve each attempt and the subsequent ordinal/area diagnostics, rather than silently replacing earlier results.

## Source, installed wheel and evidence custody

- Numerical source: `9c2a87bafdf53f1b1eadc08cd7a1414387551176`; unmodified `python-cmd/cmd-6.44`.
- Runtime: Windows 11, Python 3.14.4. Canonical ryan-tools reader dependency pinned at `8940f46b251f4d2ba6e52d6cb2ef74cd71fbe33f`.
- Built wheel SHA-256: `6ba9543b2c543091c6c79e4f2481fa0fe99827df53d596aafaf849302046f59b`.
- Source/installed package-code fingerprint: `c9fa9849d2e388e340237f5210686d82c523a6b20497337d138e27d6f27ac1f4` (61 Python files).
- Probe execution ran outside the checkout. Source imports resolved under the checkout src directory; wheel imports resolved under the separate installed destination. Package-code fingerprints match.
- Fresh public source and isolated-wheel probes agree in all 50 per-case fields: 50 printed Q passes / 19,550 ordinates; 48 reporting-scalar passes and two undefined all-zero peak-time incompletes.
- Installed-wheel full-index preflight verified all 50 selected cases and 254 published native files.
- The final site source/wheel runs agree on every non-timing result field and every retained full hydrograph/native token/clock. Rainfall reconstruction was evaluated from source, not independently replayed from the wheel.
- All 23 source catchment and 111 saved parameter files remained hash-stable through the audit; selected storm fingerprints agree between routing and rainfall receipts.
- Private local custody includes the inventory, source identity map, raw diagnostics, full candidate/reference series, regenerated STM files, source/wheel receipts and anonymous-case mapping. They are intentionally absent from public Git.

This documentation adds external diagnostic evidence only. It does not change solver code, public fixtures, baselines, thresholds or engine defaults; it does not close [CMD #5](https://github.com/Chain-Frost/python-runoff-routing/issues/5), [rainfall #8](https://github.com/Chain-Frost/python-runoff-routing/issues/8), [native ARF #192](https://github.com/Chain-Frost/python-runoff-routing/issues/192) or any deferred feature scope.
