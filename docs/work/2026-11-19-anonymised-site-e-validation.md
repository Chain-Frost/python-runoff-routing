# Fifth anonymised model set: routing and rainfall audit

19 November 2026. This addendum extends [the first four-set receipt](2026-11-19-anonymised-site-validation.md) and [draft PR #198](https://github.com/Chain-Frost/python-runoff-routing/pull/198). Set E is anonymous; original paths, project/model/site names, coordinates, source arrays and hydrographs remain private.

## Coverage

Inventoried **23,492 loose files**: **24 CATGs, 63 saved PARs, 6,751 output reports and 6,682 storms**. The inventory also records 19 ZIP archives without extracting their contents; no claim covers models found only inside archives. All loose CATG/PAR files were inspected, all output reports received input preflight and all storms received bounded reconstruction attempts. File copies and model variants are not independent catchments.

**Original readers:** seven CATGs parse directly; 17 stop at an uncharacterised graphical version. All 63 saved PARs remain unsupported. The diagnostic adapter represents 23 computational models; one stops explicitly at declared storage. Directly admitted CATGs use their original parsed models; the other represented models require the separately identified graphical-scaffold derivative. No numerical control or storage is removed, coerced or silently substituted.

| Report preflight | Files |
| --- | ---: |
| ready_for_diagnostic_routing | 2,396 |
| not_event_report | 73 |
| not_comparable | 4,282 |

The 4,282 input gaps include **1,800 missing explicitly declared storms**, **600 referenced catchments absent from the supplied set**, and **1,882 unsupported storm formats** (1,663 combined-preburst/non-uniform-depth cases and 219 multiple-pluviograph/ISA/burst cases). Only the explicit report catchment/storm locators, with the documented Q-to-W drive mapping, are followed. No nearby same-named file is used as a replacement.

The source folder documentation describes processed hydrograph products in a mixed processing collection containing **2,501 reports**. None yields an eligible declared-input routing comparison in this audit. These products are not promoted to authenticated native reference observations.

## Routing sample and installed-wheel agreement

The deterministic sample selects minimum/maximum declared-storm depth in each of **73 model/routing/loss/timestep/rainfall-bin/basis/collection groups**. It schedules **135 events**, rather than replaying every one of the 2,396 ready records or every temporal-pattern member. Preflight readiness is not numerical acceptance.

| Event result | Events |
| --- | ---: |
| diagnostic_print_match | 81 |
| not_comparable | 34 |
| diagnostic_difference | 20 |

Bound comparisons contain **105 site series / 36,905 ordinates** across **13 model files**. **0 compared events** use directly admitted original CATGs; the remainder use diagnostic typed derivatives. Remaining event association gaps are listed below, separately from Q differences.

- Native site has no unique identical source label: 2 events.
- Native hydrograph table missing, invalid or ambiguous: 32 events.

The missing-table group has no numeric native hydrograph/site summary; an inspected companion CSV also has zero hydrograph rows. These are absent reference observations, not failed candidate hydraulics. The two label gaps include an unnamed native print and a native label inconsistent with the current source model. Columns are not matched by position. Standard-format files retained from stochastic workflows are treated only as individual realised event snapshots; no Monte Carlo sampling, distribution or frequency method is qualified.

There are **11 all-zero reference events** among the bound comparisons; their peak times and percentage denominators are undefined. **70 nonzero-reference events** match the complete hydrograph within printed precision. Per-site metrics, including unbound event rows, appear in [the anonymous case table](2026-11-19-anonymised-site-e-cases.md).

Both gross rainfall and rainfall-excess checks are within the native printed intervals for **109 events**; **26 events are not assessed** under the available input-table/source mapping. These compare original printed intervals in source order, not hidden native arrays. Q differences remain unresolved profile/effective-input diagnostics; they are not automatically implementation defects. Native per-event printed parameters may have lost precision; historical model/input hashes and executable identities remain unverified. All 135 observed reports identify version 6.52. RORBwin observations remain separate from the accepted original CMD 6.44 public reference population.

The source and isolated installed-wheel runs agree on **every non-timing field and every retained full candidate/native series and clock**. They reuse the exact prior numerical source identity `9c2a87bafdf53f1b1eadc08cd7a1414387551176` and wheel `6ba9543b2c543091c6c79e4f2481fa0fe99827df53d596aafaf849302046f59b`. The 61-file package-code fingerprint is unchanged and matches source/wheel. Imports are asserted to resolve under the selected source or installed root. Runtime is Windows/Python 3.14.4. The prior fresh public 50-case source/wheel and 254-file index receipts are unchanged; this addendum does not claim a second execution of that public suite. No new native process is launched.

## Rainfall reconstruction

Raw bounded workflow attempts regenerate **0/6,682 storms**, retaining reader failures, missing/ambiguous dependency sets and unsupported formats separately. After the previously documented metadata-padding-only BoM workaround, the source rainfall methods produce:

| Outcome | Storm files |
| --- | ---: |
| not_reconstructed | 4,546 |
| reconstruction_difference | 1,993 |
| reconstructed_numerical_match | 143 |

All **1,993 reconstruction differences** have a native embedded-filtering annotation; **1,176 also specify non-uniform spatial rainfall** and **817 specify filtering without that spatial flag**. The tested preparation does not implement these native transformations, so these are unsupported preparation comparisons, not qualified same-input routing failures. The 143 exact matches are numerical STM matches under the stated workaround, not full saved-PAR workflow or hydrological acceptance.

| Remaining bounded reconstruction gap | Storm files |
| --- | ---: |
| No unique source-identified PAR dependency set for this event directory | 2,647 |
| Combined pre-burst timing or uniform rainfall depths are not characterised | 1,671 |
| Multiple pluviographs, ISAs or bursts not characterised | 200 |
| Original probability outside bounded deterministic ensemble selection | 21 |
| BoM probability label '' was not present | 7 |

New STM text was generated from uniquely bound source IFD/Data Hub/pattern files using existing readers, published regional ARF, explicit native point-choice replay where required and the two-decimal written-depth policy. Printed area, original horizon/timestep precision and subarea count were explicit context; conditional saved-PAR interpretation, filtering and spatial generation were not silently invented. Rainfall reconstruction was run from source, not independently replayed from the wheel.

## Combined scope and follow-up

The five sets now contain **100,093 inventoried files, 47 loose CATGs, 174 saved PARs, 29,871 output files and 36,491 storms**. Original CATG admission is **7/47**: the prior first-four result remains 0/23; this fifth set contributes 7/24. Saved-PAR support remains 0/174. These are import counts, not failed hydraulic simulations. The first-four 259-event/207-match/52-difference receipt remains separate from the new counts above.

[Issue #196](https://github.com/Chain-Frost/python-runoff-routing/issues/196) retains the synthetic BoM-padding reproducer. [Issue #197](https://github.com/Chain-Frost/python-runoff-routing/issues/197) receives this compatibility and association evidence. Physical print binding remains under [#91](https://github.com/Chain-Frost/python-runoff-routing/issues/91), saved PAR under [#144](https://github.com/Chain-Frost/python-runoff-routing/issues/144), and preparation/ARF qualifications under [#8](https://github.com/Chain-Frost/python-runoff-routing/issues/8) / [#192](https://github.com/Chain-Frost/python-runoff-routing/issues/192). No source/fixture/golden/tolerance/default is changed and no numerical gate is closed.

Private custody includes the inventory, exact source identities, declared-path bindings, source/wheel JSON and full-series receipts, regenerated storms and anonymous case map. All 24 catchment and 63 parameter files remain hash-stable; selected storm identities agree between routing and rainfall receipts. Original and transformed client files are not published.
