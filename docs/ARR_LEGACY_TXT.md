# Legacy ARR Data Hub 2016-era TXT intake (S6-P0)

**Implementation:** `runoff_routing.arr_import.parse_arr_txt(..., legacy_profile="arr2016")`, optionally `legacy_encoding="cp1252"` for a confirmed Windows-encoded source. **Scope:** byte-preserving offline import and structural validation, *not* ARR 2016 rainfall-method acceptance, storm generation, source IFD download, or equivalence to RORBwin.

## Evidence and discrimination

The historical ARR Data Hub TXT sections are visible in the NSW [2019 Floodplain Risk Management Guide](https://www.environment.nsw.gov.au/sites/default/files/floodplain-risk-management-guide-190036.pdf) (figure showing `[STARTTXT]`, `[INPUTDATA]`, `[LONGARF]`, `[LOSSES]`, `[TP]`), and in the historical [Margate Rivulet assessment](https://assets.kingborough.tas.gov.au/uploads/2021/10/NW30106_R005_Margate_Rivulet-RS.pdf) (APPENDIX ARR Datahub TXT, including `[PREBURST]`, other percentiles, `[CCF]` and `[BASEFLOW]`). The public [2018 Darlington Point study](https://www.murrumbidgee.nsw.gov.au/files/assets/public/v/1/publications/town-plans-etc/flood-studies/murrumbidgee-river-flood-study-2018-reduced.pdf) illustrates `[BOMIFD] No data`, comma-terminated matrices and original section metadata. These are external format references **only**: no data from those reports has been copied into code, fixtures or test goldens.

ARR2016 and ARR2019 **refer to methodology**, not necessarily to a top-level Data Hub export version. Legacy TXT may omit `Data Hub Version` entirely, while each section has a `Version,2016_v1`, `2016_v2`, or `2018_v1` metadata field. Those **layer versions are kept verbatim** and are never used to invent an export version. A legacy parse needs `legacy_profile="arr2016"`; by default, unversioned TXT fails closed. The earlier `legacy_profile="2019v1"` input-only synthetic profile remains available for backward compatibility. An explicit `2026v1` file cannot be parsed as legacy, and legacy JSON is **not** treated as 2026v1.

## Implemented historical TXT section contracts

| Section markers | Parsed / validated | Deliberately not applied |
| --- | --- | --- |
| `[INPUTDATA]` | Original `Latitude`, `Longitude`, optional `Centroid_Used`; geographic coordinate bounds | No coordinates projected or reassigned |
| `[LOSSES]` | Storm IL (`mm`), CL (`mm/h`), optional raw ID; missing-data `-50` represented by `None`, with raw `-50` retained | No direct RORB loss flag; no burst loss or jurisdiction adjustments |
| `[LONGARF]` | Raw `Zone` plus coefficients `a`–`i` as finite `Decimal` (negative coefficients permitted) | No ARF calculated or applied |
| `[TP]` / `[ATP]` | Distinct exact point/areal region codes, labels and optional `per_intersect` fraction | No temporal-pattern IDs/increments loaded; region code is **not** a pattern ID |
| `[PREBURST]`, `[PREBURST10]`, `[PREBURST25]`, `[PREBURST75]`, `[PREBURST90]` | Named percentile, original ordered duration minutes, AEP **percentages**, and paired `depth (ratio)` matrix as independent Decimals; metadata | No depth recomputation, preburst deduction, burst IL or probability conversion; valid source ratios may exceed 1 |
| `[RIVREG]`, `[BOMIFD]`, `[CCF]`, `[BASEFLOW]` | Recognised and retained with raw section lines/metadata and explicit unprocessed status | No inferred IFDs, RCP climate factor, river policy or baseflow calculation |
| Optional `[STARTPATTERNS]` after `[ENDTXT]` (TUFLOW augmentation) | Original bytes retained; explicitly marked `EmbeddedPatterns` **unprocessed** | No embedded-CSV interpretation; separate S6-P1 TP import required |

Historical `BOMIFD` sections often state `No data,No data found at this location!`. The full BOM IFD table is ordinarily downloaded separately from the BoM IFD system. No fabricated zero-depth IFD table is created. Historical RCP climate change metadata remains different from 2026 SSP scenario products; neither is applied by this importer.

The parser rejects unknown bracketed section markers, duplicate sections and field keys, missing terminators, invalid numbers, negative depths/ratios (other than explicit missing `-50` loss sentinel), duplicate duration/AEP axes, ragged matrices, unknown units and cross-version substitution. It is read-only with an 8 MiB input bound, SHA-256 over exact source bytes, and optional explicit CP1252 decoding without altering the input. All public fixtures are synthetic.

## API and reporting

```python
from pathlib import Path
from runoff_routing.arr_import import read_arr_file
from runoff_routing.arr_report import inventory_json, legacy_preburst_csv, write_new

source = Path(r"C:\data\ARR_Web_Data_catchment.txt")
result = read_arr_file(source, legacy_profile="arr2016")
assert result.source.datahub_version is None  # Genuine historical exports may omit it.
assert result.ifd_datasets == ()  # BOM IFDs are a separate source.
write_new(source.with_name("arr_legacy_inventory.json"), inventory_json(result))
write_new(source.with_name("arr_legacy_preburst.csv"), legacy_preburst_csv(result))
```

For a confirmed CP1252 source, pass `legacy_encoding="cp1252"`. The JSON inventory exposes `legacy.storm_losses`, `legacy.arf_parameters`, `legacy.temporal_pattern_regions`, `legacy.preburst_tables`, and `legacy.recognised_unprocessed_sections`. This is **not** a direct input to RORBwin or the routing solver. The original input remains untouched, and report creation uses exclusive no-overwrite semantics.

**Still outstanding:** genuine permission-reviewed historical JSON schema, separate BOM IFD CSV/HTML intake, TP ZIP/CSV increment and areal-bin integrity, NSW/VIC/probability-neutral loss policy, RCP/SSP methods, storm generation and native RORBwin effective-input parity. These require their own fixtures and acceptance gates; a successful import alone does not validate a hydrological calculation.
