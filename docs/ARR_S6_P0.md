# S6-P0: offline ARR 2026v1 and legacy ARR2016 Data Hub intake

**Status:** S6-P0 source-ingestion implementation **merged via #38**; source validation only. This is **not** an ARR rainfall-method acceptance, hydraulic/numerical acceptance, compliance certificate, or RORB adapter. [Issue #33](https://github.com/Chain-Frost/python-runoff-routing/issues/33) is a first slice of [S6 #8](https://github.com/Chain-Frost/python-runoff-routing/issues/8). The predecessor [source reconnaissance #34](https://github.com/Chain-Frost/python-runoff-routing/pull/34) is retained as a historical record, not a competing active data contract.

## References and the observed contract

Reviewed 2026-11-11 against the production [ARR Data Hub changelog](https://data.arr-software.org/changelog) (2026v1 published 2026-08-21), [API guide](https://data.arr-software.org/about), [public illustrative JSON](https://data.arr-software.org/?lon_coord=152.648&lat_coord=-29.573&type=json&All=1), and [public illustrative TXT](https://data.arr-software.org/?lon_coord=152.648&lat_coord=-29.573&type=text&All=1). Do **not** commit a downloaded original without a separate rights review. The public examples are not hydrological recommendations. This implementation uses no online calls.

| Source | Version detection | Parsed fields | Refused or inventoried without interpretation |
| --- | --- | --- | --- |
| 2026v1 JSON | Mandatory `datahub_version: "2026v1"` | `input_data.Latitude/Longitude/Centroid_Used`, optional explicitly named `Outlet Latitude`/`Outlet Longitude`; `layers.RecIFD` exactly `index` (integer minutes), `columns` (numeric AEP %), `data` (mm depths) for three named default baseline tables | Other `layers` recorded as `unprocessed_layers`; selected All IFD/CC adjusted tables remain unprocessed pending inspected schemas |
| 2026v1 TXT | `Data Hub Version,2026v1` and `[STARTTXT]` | `[INPUTDATA]`; `[RECIFD]` with `[RECCURRENTBASELINE]`, `[RECHISTORICALBASELINE]`, `[RECNATIVEBASELINE]`, optional `*_META`; `Datasets` metadata kept raw and single-source release year parsed if unambiguous | Other section markers inventoried but not interpreted; unexpected `RECIFD` headings and missing delimiters rejected |
| Legacy ARR2016-era TXT | Explicit `legacy_profile="arr2016"`, unversioned legacy file, per-layer `Version` metadata | `[INPUTDATA]`, `[LOSSES]`, `[LONGARF]`, `[TP]`, `[ATP]`, five `[PREBURST*]` paired `depth (ratio)` matrices | Recognised `[RIVREG]`, `[BOMIFD]`, `[CCF]`, `[BASEFLOW]` and embedded patterns are preserved but not used. [Detailed legacy contract](ARR_LEGACY_TXT.md) |
| Legacy input-only synthetic compatibility profile | Explicit `legacy_profile="2019v1"`; absent or exactly matching version line | `[INPUTDATA]` only | Retained for compatibility; no hydrological values or false inferred version |
| Legacy JSON / standalone BOM 2016 IFD | Not accepted | Nothing | No invented JSON schema or assumption that legacy Data Hub contains BOM IFD |
| CSV/ZIP for IFD and temporal patterns | Not accepted | Nothing | Separate S6-P1 safe-archive and field-matrix contract required |

The real production JSON `RecIFD` table has rows and columns of **numeric JSON values**, not literal `"1%"`, `"2EY"`, ARI years or fractions. AEP is retained as a `Decimal` percentage, without implicit probability conversions. The exact TXT header is `min (h)\AEP(%)`, with duration labels like `5 (0.08)`; the importer takes the integer minutes and does not recalculate using the rounded hours annotation. Baseline names must match the observed canonical three names; native may be absent for regional envelopes. JSON lacks the `Datasets` metadata shown by the TXT export, so JSON cannot legitimately infer provider/release year.

Both formats preserve **source order**, original bytes, SHA-256, content size, optional capture timestamp/locator, coordinates and raw source labels. The importer's own inventory schema version (`1`) is separate from the source version (`2026v1`) and from any later method-policy version. Decimal text in outputs retains the supplied significant digits; it does not recover precision lost to Data Hub's three-significant-figure output rounding. Depths are stored **as exported** with `AS_EXPORTED_NO_FURTHER_UPLIFT`: applying additional climate factors to a 2030/adjusted product is **not** part of the import API.

## Historical ARR 2026v1 reconnaissance preserved from draft #34

This section carries forward the distinct *source-observation cautions* from [historical #34](https://github.com/Chain-Frost/python-runoff-routing/pull/34) (exact head `1eb4a456eab76170a99546c6239a1124949d8859`) without adding a second schema/parser contract. These are **dated production export observations** and exclusions, not claims that optional ARR2026 datasets have been implemented or numerically accepted.

- The production source examples used `All=1`, but the Data Hub's documented **Select All** option does not necessarily include special `All IFD` or **climate-adjusted IFD** datasets. Their absence from an illustrative export is **not** proof that the layers do not exist; request them explicitly and retain source/export options and raw hashes before adding parser support.
- The production [ARR Data Hub changelog](https://data.arr-software.org/changelog) and a *development-server* changelog may describe different feature deployment states. Do not treat fields observed only on a development server as part of an implemented production schema without a captured original export.
- Jurisdiction-selected `Default IFD` can be an **envelope** based on named underlying datasets, not a licence to reconstruct an envelope by cell-wise maxima. Distinct current/historical/native baselines and any future **already adjusted** curves must retain their original release and scenario identities. The original exported **three-significant-figure** precision does not justify recovering higher digits.
- Reported **preburst ratios** and derived preburst depths have different semantics and potentially different source baselines; do not multiply, rederive or subtract either twice. The legacy ARR2016 preburst logic in merged P3 must **not** be presented as automatically validated for a 2026v1 scenario.
- Requested centroid, separately provided outlet and the source's representative-point policy can affect jurisdiction-sensitive layers. Retain original geographical coordinate labels and supplied CRS; do not infer MGA metres from latitude/longitude. Source version, project-inventory schema and selected method-policy version remain independent.
- The separate [TUFLOW ARR-to-TUFLOW QGIS plugin reference](https://wiki.tuflow.com/QGIS_ARR_to_TUFLOW) is a useful independent source/method cross-check, **not** evidence that RORBwin's effective numerical inputs or any particular jurisdiction default have been matched.

**Scope check:** these are format/provenance safeguards only. Merged [S6-P1/P2/P3](ARR_S6_INTEGRATION.md) add explicitly selected legacy BoM/pattern, ARF, and preburst functionality; they do not establish generic ARR2026 climate/loss generation, S6 native effective-input parity, or S2 routed-output equivalence. Original #34 source observations and source-handoff history remain available by immutable commit.

## Public API

```python
from pathlib import Path

from runoff_routing.arr_import import read_arr_file
from runoff_routing.arr_report import inventory_csv, inventory_json, write_new

result = read_arr_file(Path(r"C:\data\arr_export.json"), captured_at="2026-11-11")
assert result.capability in {"ifd_validated", "location_only", "legacy_layers_validated"}
write_new(Path(r"C:\data\arr_inventory.json"), inventory_json(result))
write_new(Path(r"C:\data\arr_inventory.csv"), inventory_csv(result))
```

The CSV reports each validated cell with original dataset, baseline, source hash, duration (min), AEP (%), and rainfall depth (mm). The JSON report retains all depth matrices, axes, source/location metadata, missing optional IFD and unprocessed layers. `write_new` uses exclusive creation; existing reports and raw imports cannot be overwritten. `read_arr_file` reads local bytes with an 8 MiB cap; no HTTP requests, archive extraction, RORB execution, numerical solver import, or filesystem writes occur during parsing.

You can opt into a **local, read-only replay** of the public example or an approved source snapshot by pointing `read_arr_file` at an offline local copy. Tests do not retrieve it. The committed fixtures are intentionally synthetic; they exercise schema shapes, *not* real ARR rainfall depths.

## S6-P0 capability matrix (merged source-intake scope only)

| Data/workflow | Recognised | Parsed | Validated | Event-generated | Hydrologically accepted |
| --- | --- | --- | --- | --- | --- |
| 2026v1 default current/historical/native IFD JSON | Yes | Yes | Structure, axes and depths | No | No |
| 2026v1 default current/historical/native IFD TXT | Yes | Yes | Structure, axes and depths | No | No |
| Historical ARR2016-era TXT losses, ARF, TP regions, preburst depths and ratios | Yes, opt-in | Yes | Shape, source units, axes and values | No | No |
| Historical region, BOMIFD no-data, CCF and baseflow sections | Yes | Raw only | Marker/metadata integrity | No | No |
| 2019v1 explicit legacy input-only TXT profile | Yes | Location only | Input format only | No | No |
| 2026v1 All IFD, BOM original and climate SSP/year products | Layer name only | No | No | No | No |
| TP ZIP/CSV, point/areal bins and pattern IDs | Link/section only | No | No | No | No |
| 2026v1 storm loss, preburst ratio vs derived depth, ARF and adjusted losses | Layer/section only | No | No | No | No |
| Storm generation, S6→S2/RORB/TUFLOW adapters | No | No | No | No | No |

**Legacy ARR2016-era TXT** is implemented as a separate source profile; see [the historical TXT format and API contract](ARR_LEGACY_TXT.md). Imported preburst depths and ratios, storm losses, ARF coefficients and TP *region IDs* are not rainfall events. Legacy BoM IFD rainfall depths typically require a separate BoM IFD export.

**Later integration:** P1's legacy BoM IFD/ARR patterns, P2's ARR2019 selection/ARFs and P3's explicit legacy preburst/loss policies have separately merged as #48/#49/#50. Consult the [S6 capability/acceptance matrix](ARR_S6_INTEGRATION.md) for their exact supported subsets. Selected ARR2026 All IFD, climate SSP/year and jurisdiction-specific adjusted products, general native RORBwin effective-input parity and S2 routed-output equivalence remain **unaccepted or unsupported**. No source-contract reconciliation changes the mathematical routing policy.
