# S6-P0: offline ARR 2026v1 IFD intake

**Status:** source ingestion and matrix validation only. This is **not** a rainfall hyetograph generator, hydraulic/numerical acceptance, an ARR compliance certificate, or a RORB adapter. [Issue #33](https://github.com/Chain-Frost/python-runoff-routing/issues/33) is a first slice of [S6 #8](https://github.com/Chain-Frost/python-runoff-routing/issues/8). The separate [draft source contract](https://github.com/Chain-Frost/python-runoff-routing/pull/34) remains under review.

## References and the observed contract

Reviewed 2026-11-11 against the production [ARR Data Hub changelog](https://data.arr-software.org/changelog) (2026v1 published 2026-08-21), [API guide](https://data.arr-software.org/about), [public illustrative JSON](https://data.arr-software.org/?lon_coord=152.648&lat_coord=-29.573&type=json&All=1), and [public illustrative TXT](https://data.arr-software.org/?lon_coord=152.648&lat_coord=-29.573&type=text&All=1). Do **not** commit a downloaded original without a separate rights review. The public examples are not hydrological recommendations. This implementation uses no online calls.

| Source | Version detection | Parsed fields | Refused or inventoried without interpretation |
| --- | --- | --- | --- |
| 2026v1 JSON | Mandatory `datahub_version: "2026v1"` | `input_data.Latitude/Longitude/Centroid_Used`, optional explicitly named `Outlet Latitude`/`Outlet Longitude`; `layers.RecIFD` exactly `index` (integer minutes), `columns` (numeric AEP %), `data` (mm depths) for three named default baseline tables | Other `layers` recorded as `unprocessed_layers`; selected All IFD/CC adjusted tables remain unprocessed pending inspected schemas |
| 2026v1 TXT | `Data Hub Version,2026v1` and `[STARTTXT]` | `[INPUTDATA]`; `[RECIFD]` with `[RECCURRENTBASELINE]`, `[RECHISTORICALBASELINE]`, `[RECNATIVEBASELINE]`, optional `*_META`; `Datasets` metadata kept raw and single-source release year parsed if unambiguous | Other section markers inventoried but not interpreted; unexpected `RECIFD` headings and missing delimiters rejected |
| Legacy TXT input-only synthetic compatibility profile | Explicit `legacy_profile="2019v1"`; absent or exactly matching version line | `[STARTTXT]`, `[INPUTDATA]` latitude/longitude and optional `Centroid_Used`, `[ENDTXT]`, no rainfall table | **Not** a verified general-purpose 2019 parser. Unknown sections rejected. Missing source version is stored as `null`, never invented from profile |
| Legacy JSON / 2016 IFD | Not accepted | Nothing | Explicit incompatible/unknown-version error |
| CSV/ZIP for IFD and temporal patterns | Not accepted | Nothing | Separate S6-P1 safe-archive and field-matrix contract required |

The real production JSON `RecIFD` table has rows and columns of **numeric JSON values**, not literal `"1%"`, `"2EY"`, ARI years or fractions. AEP is retained as a `Decimal` percentage, without implicit probability conversions. The exact TXT header is `min (h)\AEP(%)`, with duration labels like `5 (0.08)`; the importer takes the integer minutes and does not recalculate using the rounded hours annotation. Baseline names must match the observed canonical three names; native may be absent for regional envelopes. JSON lacks the `Datasets` metadata shown by the TXT export, so JSON cannot legitimately infer provider/release year.

Both formats preserve **source order**, original bytes, SHA-256, content size, optional capture timestamp/locator, coordinates and raw source labels. The importer's own inventory schema version (`1`) is separate from the source version (`2026v1`) and from any later method-policy version. Decimal text in outputs retains the supplied significant digits; it does not recover precision lost to Data Hub's three-significant-figure output rounding. Depths are stored **as exported** with `AS_EXPORTED_NO_FURTHER_UPLIFT`: applying additional climate factors to a 2030/adjusted product is **not** part of the import API.

## Public API

```python
from pathlib import Path

from runoff_routing.arr_import import read_arr_file
from runoff_routing.arr_report import inventory_csv, inventory_json, write_new

result = read_arr_file(Path(r"C:\data\arr_export.json"), captured_at="2026-11-11")
assert result.capability in {"ifd_validated", "location_only"}
write_new(Path(r"C:\data\arr_inventory.json"), inventory_json(result))
write_new(Path(r"C:\data\arr_inventory.csv"), inventory_csv(result))
```

The CSV reports each validated cell with original dataset, baseline, source hash, duration (min), AEP (%), and rainfall depth (mm). The JSON report retains all depth matrices, axes, source/location metadata, missing optional IFD and unprocessed layers. `write_new` uses exclusive creation; existing reports and raw imports cannot be overwritten. `read_arr_file` reads local bytes with an 8 MiB cap; no HTTP requests, archive extraction, RORB execution, numerical solver import, or filesystem writes occur during parsing.

You can opt into a **local, read-only replay** of the public example or an approved source snapshot by pointing `read_arr_file` at an offline local copy. Tests do not retrieve it. The committed fixtures are intentionally synthetic; they exercise schema shapes, *not* real ARR rainfall depths.

## Capability matrix (this PR only)

| Data/workflow | Recognised | Parsed | Validated | Event-generated | Hydrologically accepted |
| --- | --- | --- | --- | --- | --- |
| 2026v1 default current/historical/native IFD JSON | Yes | Yes | Structure, axes and depths | No | No |
| 2026v1 default current/historical/native IFD TXT | Yes | Yes | Structure, axes and depths | No | No |
| 2019v1 explicit legacy input-only TXT profile | Yes | Location only | Input format only | No | No |
| 2026v1 All IFD, BOM original and climate SSP/year products | Layer name only | No | No | No | No |
| TP ZIP/CSV, point/areal bins and pattern IDs | Link/section only | No | No | No | No |
| Storm loss, preburst ratio vs derived depth, ARF and adjusted losses | Layer/section only | No | No | No | No |
| Storm generation, S6→S2/RORB/TUFLOW adapters | No | No | No | No | No |

**Next slices:** S6-P1 inspect authenticated/permission-cleared TP ZIP/CSV samples, enforce member/path/size constraints, preserve event IDs and bins; S6-P2 inspect selected All IFD and CC IFD JSON/TXT/CSV plus climate/loss/preburst/ARF methods and jurisdictions; S6-P3 explicit event generation and independent numerical comparisons. No S2/RORB contract change is implied by this PR.
