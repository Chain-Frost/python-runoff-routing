# S6 R6/R7: short-duration defaults and the 12-hour area boundary

**Status:** R6 and the Inland boundary characterised; Coastal effective settings unresolved; full parity open.

**Owner:** Local Windows agent. **Updated:** 2026-11-14. **Review:** before Coastal or default-pattern acceptance.

**Unchanged implementation revision:** `bb34c3aa0cb2cd1f3afcafeb4d5b076b35948223`.
**Experiment dependency pin:** draft [#50](https://github.com/Chain-Frost/python-runoff-routing/pull/50),
`b2c89eae7517d1117fd522f24a1897ab7622823d`.
**Delivery:** documentation follow-up on draft [#54](https://github.com/Chain-Frost/python-runoff-routing/pull/54),
branch `feat/s6-rorbwin-native-rainfall`; stage [#8](https://github.com/Chain-Frost/python-runoff-routing/issues/8) open.

The owner's review selected **R6 = short-duration Jordan default** and **R7 = the 12-hour / 75 km²
boundary**. These names supersede the original handoff's conditional boundary/interpolation labels.
The [R5 observation](2026-11-14-s6-r5-default-preburst.md) and
[controlled loss profile](2026-11-14-s6-controlled-loss-kernel.md) remain separate evidence.

## Inputs, controls and calculation count

The unchanged executable is RORBwin **6.52, updated 1 June 2023**, SHA-256
`0ca65bcef548f26a5f9bceda6c99ed4f545a9498b61c93aa59a00400732d1aea`.
Runs used Windows / CPython **3.14.6** local automation, current editor-saved **RORB_GE 6.52** graphical
catchments, one pervious subarea, a 1 km natural reach and the same outlet/excess reporting configuration.
Both graphical and computational areas were checked after native editor saves:

| Computational area, km² | Editor-authored model SHA-256 |
| --- | --- |
| 74.90000 | `62936d3fdee7641b5342f2ce22ae0eecb3996ad832566ac39eac47a105fc5126` |
| 75.00000 | `ea619cd92e967af0e5b701864b747e880422e07b5606c7197e7247da21017b39` |
| 75.10000 | `bcfe88fc2b7731af04cbefa5217be8f8a9d1b905508aa3ead76b4c2695b9f077` |

An initial numeric-entry attempt saved zero area. It remains a rejected local setup artifact and was
**never calculated**. Model files were authored in the installed editor, without pyromb or external edits.
The editor's graphical binary32 spellings of 74.9 and 75.1 differ slightly from their computational
five-decimal values; the exactly 75 km² case is represented exactly in both sections.

All events use **1% AEP**, IL **21 mm**, CL **2 mm/h**, kc **10**, m **0.8**, file ARF coefficients,
default preburst enabled, manual preburst depth ratio **5.4%**, and a **200-increment** horizon.
Regional losses, area override, embedded-burst filtering and nonuniform spatial rainfall are disabled.
The synthetic legacy Data Hub coefficient TXT is inherited from R5; it is not a genuine site loss export.
The manual ratio table was explicitly set to 5.4% throughout and its 6-/12-hour, 1% cells checked in the GUI.
ARR2026 inputs were not used. No geographic GSAM-zone acceptance is inferred for Margaret River.

Original offline sources remain unchanged:

| Source | SHA-256 |
| --- | --- |
| Margaret River BoM IFD2016 depth CSV | `0ca11f66c2a1cb7e48e8bd6fc852f52dfa68014377c16301f5d57495c54864db` |
| FLTwest point archive | `0cd57da5e7dffd8f235b72d3e59c83ac1ab9f2e54f03e94201340e307ed83adb` |
| FLTwest areal archive | `61c60366f953669a9879c5e2c6619b3c420c3a3dceeb296fa41e91606b3c213f` |

The first protocol bounded **seven calculations**: one 6-hour case and six 12-hour area/zone requests.
The audit exposed incorrect point-pattern ordinals and unestablished Coastal settings. A separate,
retained corrective protocol then bounded **two additional calculations**, with corrected point ordinals
verified against generated preview vectors before calculation. **Nine calculations total**, no automatic
repeat, overwrite of captures or further precision-search runs. Setup/preview operations are not solver runs.

## Retained intended Inland cases

These four cases have verified source identities. Every one of their **96 burst weights** matches its
original source vector exactly. RORB's default source tables and generated preburst sequences are retained
privately; this change does not implement a Python Jordan/GSAM generator.

| Case | Area, km² | Burst | Source EventID / ordinal | Native default | Source / effective step | Preburst / burst cells |
| --- | --- | --- | --- | --- | --- | --- |
| R6 corrected | 74.9 | 6 h | point rare 7550 / 21 | Jordan short | 1 h / 15 min | 16 / 24 |
| R7 below, corrected | 74.9 | 12 h | point rare 7604 / 21 | Jordan short | 1 h / 30 min | 10 / 24 |
| R7 exactly | 75.0 | 12 h | areal 8911 / 1, 100 km² bin | Jordan short | 1 h / 30 min | 10 / 24 |
| R7 above | 75.1 | 12 h | areal 8911 / 1, 100 km² bin | GSAM Inland long | 3 h / 30 min | 48 / 24 |

The 12-hour preburst vectors at **74.9 and exactly 75.0 km² are identical**. Their preburst duration is
**5 hours**. At **75.1 km²**, the default changes to **24 hours**, even with the same areal source and
ordinal used at exactly 75. This distinguishes an area-dependent default from a point/areal-file switch.
The 6-hour case has **4 hours** of preburst. These are observations at the tested areas and durations,
not acceptance of every duration or an inferred implementation of the native selection routine.

The areal input at exactly 75 km² produces the native recommendation warning that point patterns be used
at areas <=75 km². That warning is retained and acknowledged for this deliberate boundary probe. The model
passes the native data check; the source type, area bin and warning are not hidden or treated as site approval.

| Case | Python ARF | Native nominal burst / preburst / combined depth, mm | Written preburst / combined weight |
| --- | --- | --- | --- |
| R6 corrected | 0.8889489329670484 | 76.89 / 4.15 / 81.05 | 5.44 / 105.44 |
| R7 below, corrected | 0.9261769941999553 | 98.17 / 5.30 / 103.48 | 5.42 / 105.42 |
| R7 exactly | 0.9261401771034207 | 98.17 / 5.30 / 103.47 | 5.42 / 105.42 |
| R7 above | 0.9261033964333983 | 98.17 / 5.30 / 103.47 | 5.46 / 105.46 |

BoM gross depths are **86.5 mm** at 6 hours and **106 mm** at 12 hours. Independent Decimal ARFs give
the displayed nominal burst and 5.4% preburst depths within their 0.01 mm display precision. The generated
storm's two-decimal weights do **not** sum to the nominal 105.4. The diagnostic consumes the actual written
weights and combined depth; it does not force the preburst sum to 5.4 or independently round burst and
preburst depths. For example, R6's reconstructed effective preburst is approximately **4.18163885 mm**,
distinct from its nominal header value **4.15 mm**. All effective rainfall cells agree with the native
catchment rainfall text at its **one-decimal** display precision; this is a reporting check, not a new
full-precision rainfall or excess tolerance.

## Strict excess replay and raw clocks

The unchanged experimental Decimal kernel was replayed on every reconstructed native forcing cell.
Native excess m³/s is converted using the computational area and effective timestep. The allowance
remains **0.0000018 mm absolute, zero relative**.

| Case | Input-matched excess cells passing | Failing step | Maximum absolute difference, mm |
| --- | --- | --- | --- |
| R6 corrected | 40/40 | none | 0.000000893098 |
| R7 below, corrected | 33/34 | **31** | **0.000002161359** |
| R7 exactly | 34/34 | none | 0.000001214798 |
| R7 above | 72/72 | none | 0.000001350649 |

This is **179/180** for the four retained intended cases, with one new unresolved residual. The original
six R2–R5 strict expected failures remain untouched; there are now **seven observed unresolved cells**
across those prior cases and the corrected R7 below-boundary case. The new failure is recorded in this
separate diagnostic, not added to or silently absorbed into the old six-xfail replay. No arithmetic
hypothesis search, default-kernel replacement, tolerance change or golden regeneration was performed.

All **201 raw excess and 201 raw hydrograph records per run** are preserved, including every initial and
trailing zero. Across nine runs this is **1,809 records in each CSV family**, 394 forcing positions,
nine initial positions and 1,406 trailing zeros. The four intended cases account for 180 forcing cells.
All raw excess/hydrograph pairs retain the observed **one-increment** label difference: **0.25 h** in R6,
**0.5 h** in R7. Per-step diagnostics retain raw Inc/time, derived interval end and burst-relative time
in separate columns. No timestamps were shifted in raw files. Routing was not compared.

## Setup discrepancies and Coastal limitation

Initial deterministic ordinal **1** selected point frequent EventID **8230** at 6 hours and **8267** at
12 hours, despite the selected 1% AEP depth. All 24 weights identify those actual source events exactly.
The intended rare patterns **7550/7604** occupy ordinal **21** in these complete point samples; the two
corrective cases verify all their weights. The original three point runs are retained as setup deviations,
not accepted rare-band cases. This observation concerns this deterministic sample/ordinal configuration;
it does not establish the Monte Carlo AEP-bin rule or a universal parser defect.

The three requested **Coastal** runs also fail effective-setting verification. The GUI combo displayed
Coastal under automation, but their saved parameter tables and generated vectors match the Inland runs.
Additional **non-calculating** GUI checks captured a distinct Coastal table after a real dropdown selection,
yet reopening/applying/saving did not establish that table in the effective saved parameters. The cause
is unresolved: automation/event handling and native persistence have not been distinguished.
**No Coastal calculation is accepted and no native software bug is asserted.** Equal generated outputs
cannot establish that Jordan ignores zone, since the Coastal setting itself was not established.

The five initial setup-deviation/Coastal-unestablished captures pass their own 214 input-matched excess
cells, but are excluded from the four intended-case acceptance denominator. They do not fill missing
Coastal coverage. Next, establish Coastal settings in a saved parameter file and generated preview
before authorising/performing any further bounded native cases.

## Evidence, checks and next action

All sources, generated storms, outputs, screenshots, saved parameters, protocols, per-step diagnostics
and nine inventories remain private under the ignored local campaign. The campaign manifest SHA-256 is
`9cd538f3c3e907e31a9144a3e3b8f68ca7e6119481402cd25b7fe7489e894168`.
The intended case inventory hashes are:

| Case | Inventory SHA-256 |
| --- | --- |
| R6 corrected | `2d13dde7013059126b76cb8c9e0425c42d2f4ebf52f7fe59457ec3b92b999ae5` |
| R7 below, corrected | `2ed70304025e0caace20e272663e30d4784d4c2e15edf1eaca9ab32ad21c069f` |
| R7 exactly | `4fd8103edf81d3b6c2a146406bb649cd64fc316fab07b9b0b867a0ef8bf7e26c` |
| R7 above | `7b166299ed7782ef85c8411eb7da42a759bb7e82be3a2113dca4c90c70f02d51` |

Hash verification also confirms **146 prior capture files** and the executable unchanged. This follow-up
changes documentation only. Local checks cover repository hygiene, changed relative links, claims against
the retained audit, and whitespace; the implementation's previous 377-test Windows/source/wheel evidence
remains the historical result at `bb34c3a`, not a newly rerun test claim or acceptance of the new residual.

The pre-publication remote check found #50 had advanced to
`9a014f4c23b260721b37be24734b03df4be0b304`; #54 is reported **not mergeable** against that newer base.
This batch preserves the experiment's pinned implementation and does not integrate the concurrently
updated dependency or claim validation of its new code. Stack reconciliation and exact-head quality
checks remain separate work before #54 could become ready for acceptance.

R6 is characterised for the selected native case; R7 has an observed Inland boundary and incomplete
Coastal coverage. Python default-pattern generation, strict excess precision and full native event
acceptance remain open. Keep #54 draft on draft #50 and #8 open. The next investigation is Coastal
effective-input persistence, followed by a discriminating precision case; no broad binary32 search,
merge, release or routed-flow comparison is justified by this batch.
