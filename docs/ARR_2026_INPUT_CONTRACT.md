# ARR Data Hub 2026v1 — rainfall input and version contract

**Date:** 2026-11-11. **Status:** source reconnaissance only; no ARR hydrological generation or rainfall-method acceptance. **Workpack:** [S6-P0 #33](https://github.com/Chain-Frost/python-runoff-routing/issues/33), a deliberately independent subset of [S6 #8](https://github.com/Chain-Frost/python-runoff-routing/issues/8).

## Authoritative public evidence

- Live [ARR Data Hub 2026 v1 changelog](https://data.arr-software.org/changelog): major update **21 August 2026**. The *development server* [changelog](https://data-dev.arr-software.org/changelog) contains additional loss/IFD details **that may not yet be deployed to the live server**; record those as candidates, not guaranteed live fields.
- [ARR Data Hub usage and API guidance](https://data.arr-software.org/about): live point GET, boundary POST; exports in JSON/TXT/PDF, IFD CSV/ZIP and temporal-pattern ZIP.
- Live public example [JSON](https://data.arr-software.org/?lon_coord=152.648&lat_coord=-29.573&type=json&All=1) and [TXT](https://data.arr-software.org/?lon_coord=152.648&lat_coord=-29.573&type=text&All=1). These are **public examples at arbitrary illustrative coordinates**, not user/client catchments or recommended rainfall values. Save an original raw offline snapshot and SHA-256 in a permission-reviewed location if a regression uses them. Do **not** commit a large raw export into this public code repository without a separate rights/size review.
- TUFLOW [2026 v1 plugin compatibility](https://wiki.tuflow.com/QGIS_ARR_to_TUFLOW): a **separate** ARR-to-TUFLOW tool was introduced in QGIS plugin v2026.2.0; old legacy tool remains. Treat its methods/output as an independent comparison source, not the sole interpretation of ARR.

## Observed live 2026v1 export envelope

The publicly accessible live JSON example includes these fields (names shown exactly where noted):

| JSON path | Observed structure | First-pass contract |
| --- | --- | --- |
| \`datahub_version\` | \`"2026v1"\` | Source-format discriminator; independent of our own project schema version |
| \`input_data\` | \`Latitude\`, \`Longitude\`, \`Centroid_Used\` | Preserve user-requested point, representative point status, and optional outlet when present |
| \`layers.ARFParams\` | regional \`Zone\` and \`a\`–\`i\` coefficient strings | Do **not** assume these are an applied ARF; keep raw typed coefficients |
| \`layers.NewStormLosses.losses\` | objects with \`AEP\`, \`Preburst\`, \`Storm Initial Loss (mm)\`, \`Continuing Loss (mm/h)\` | Distinguish source loss labels, spatial policy, preburst and method; do not map to an S2 loss flag automatically |
| \`layers.PointTP\`, \`layers.ArealTP\` | region code/label and a \`url\` to temporal-pattern ZIP | URL is a locator, **not** an embedded TP array or permission to fetch it in ordinary tests |
| \`layers.RecIFD\` | named \`Default Current (2030) Baseline\`, \`Default Historical (1961-1990) Baseline\`, \`Default Native Baseline\` where applicable | Multiple distinct curves and baselines; preserve exact displayed dataset identity |
| \`layers.RecIFD[table]\` | \`index\` (duration in minutes), \`columns\` (AEP percentages), \`data\` (depth matrix in mm) | Validate lengths: one row per duration; one depth per AEP; order retained |

The live TXT example begins with a title, a separate \`Data Hub Version,2026v1\` line and \`[STARTTXT]\`. Structured section markers include \`[INPUTDATA]\`, \`[RIVREG]\`, \`[LONGARF]\`, \`[NEWLOSSES]\`, \`[TP]\`, \`[ATP]\`, \`[RECIFD]\` and individual baseline subheadings. Use a format-aware reader; never assume old 2016 section positions.

**Important:** the public example was requested with \`All=1\`. The Data Hub documentation says some special layers, notably all-IFD datasets and climate-adjusted IFDs, are **not included in Select All**. Missing optional datasets in that example are expected, not evidence that the source has no climate functionality. Test expressly selected exported layers later.

## Current 2026 changes to support

- \`Default IFD\` can be a jurisdiction-recommended **envelope of multiple datasets**, not necessarily the original 2016 BOM IFD; historical (1961–1990), current (2030) and native baseline products must stay distinct. An envelope must not be reconstructed by arbitrary table-wise maxima.
- \`All IFD Datasets\` and \`Climate Change Adjusted IFDs\` introduce extra curves/scenario combinations; current change log lists SSP1/2/3/5 and 2030/2050/2090, with jurisdiction/dataset release-year metadata.
- Output IFD depths are rounded to **three significant figures** by the 2026 Data Hub. Do not infer unrounded precision or use a tighter numeric acceptance budget than retained data supports.
- The changelog says **preburst ratios are stored** and depths derive from the current (2030) default IFD. Store \`preburst_ratio\` and \`derived_depth\` separately and record source policy/baseline; do not derive a second time.
- Climate-change-adjusted loss layers and jurisdiction-specific storm losses are distinct from historical loss flags. A downloaded **already adjusted** rainfall depth/loss is not to be uplifted again.
- Catchment outlets can be supplied for jurisdiction-sensitive layers; the representative interior point is used if the geometric centroid is outside a polygon. Source latitude/longitude and CRS must not be conflated with MGA metres.
- Output is not fixed-width or globally fixed shape: table sizes, optional dataset presence, layer ordering, AEPs/durations, notes and raw metadata can vary by location, selected options and data release.

## Explicit model semantics proposed for S6-P0

Keep this rainfall data separate from S1's RORB \`RunModel\` until an adapter is explicitly designed:

- \`DataHubSource\`: source system, export type \`json/txt/zip/csv\`, observed version, raw bytes SHA-256/size, capture date/locator and permission policy.
- \`QueryLocation\`: requested centroid/point, optional outlet, supplied catchment polygon fingerprint/CRS, selected jurisdiction and representative-point policy.
- \`IFDDataset\`: exact source dataset name, provider/release year (if provided), selected baseline, scenario SSP and future year (if applicable), units, durations, AEP dimension/unit and immutable depth matrix (prefer \`Decimal\` at boundary).
- \`TemporalPatternSet\`: regional code, point/areal selection, source identifier, pattern ID, duration/bin, percentages and source rounding budget; do not renumber patterns.
- \`LossDataset\` / \`PreburstDataset\`: raw IL/CL, current/native baseline, derived-vs-native preburst distinction, probability-neutral policy where explicitly selected; avoid a universal default.
- \`PreparedStorm\` (later): explicit rainfall per timestep, depth source/method chain, TP identity, area/ARF, loss/preburst provenance and scenario; no numerical routing.

Model **source version**, **project schema version**, and **method policy version** separately. The RORB compatibility output path is a *later explicit adapter*, not a constraint on the data model.

## First PR scope and exclusions

**First PR:** strict offline JSON 2026v1 parser/inventory and an initial legacy TXT version discriminator/reader for explicitly characterised sections. Validate IFD table dimensions, finiteness/nonnegativity, duplicate duration/AEP keys, missing and extra unsupported shape, source hash, original order and baseline/scenario distinction. Fail closed when required units or version cannot be confirmed; accept optional omitted layers with an explicit absence record. Keep parser, model and file access distinct.

**Next slices:** zipped point/areal TP and areal bins with ZIP path traversal/size protection; optional BOM 2016 source reader; climate adjusted products and dataset selection; ARF/preburst/loss policies; burst/complete-storm generation; eventual S6→S2/RORB input conversion, external TUFLOW exports and independent hydrologic verification.

The **full S6 #8 gate** requires reviewed rainfall generation methods and eventually routed-output parity. An S6-P0 import success must never close #8 or make claims of ARR numerical method acceptance.

## Tests and engineering guards

- Synthetic JSON/TXT with clearly marked illustrative values only; no real site/client data. Validate both modern and legacy variants and explicitly reject unknown source versions rather than silently treating 2026 IFD as BOM 2016.
- Cases: absent optional layer, two IFD datasets, same AEP labels in separate baselines, ragged/empty matrices, duplicate keys, nonfinite/negative values, unrecognised SSP, 2016-vs-2026 distinction, Unicode/path spelling, and no-clobber file output.
- Identify AEP-percent versus annual probability fraction, EY and ARI; never interpret \`63.2\` as a fraction or \`2EY\` as \`2% AEP\`.
- Strong provenance: original download hashes, input metadata and selected dataset origin; zero hidden network access during tests.
- Preserve unmodified raw values in import; when computing an output later, retain a full transformation ledger identifying any area factor, preburst policy, climate scenario and loss policy applied exactly once.
- Windows/Python 3.14, Ruff 0.16.6, strict Pyright, pytest and installed-wheel outside the checkout are acceptance gates for the independent first PR. No RORB executable, QGIS/GDAL, NumPy or pandas dependency is required for this first pure-source slice.
