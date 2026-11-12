# S6 follow-up: BoM IFD CSV, ARR temporal patterns and explicit gross rainfall

**Status:** implemented as independent, source-preserving import/validation and arithmetic-only gross hyetograph construction. **No ARR design-method acceptance, RORBwin parity or hydrological solver acceptance.** This change is intentionally stacked on the draft [S6-P0 ARR import PR #38](https://github.com/Chain-Frost/python-runoff-routing/pull/38).

## Distinct input systems

| Source | Recognised | Parsed | Validated | Gross event created | Hydrologically accepted |
| --- | --- | --- | --- | --- | --- |
| BoM 2016-methodology IFD Design Rainfall CSV with two duration columns | Yes | Yes | Yes, finite nonnegative depths/intensities and typed probability axis | With manually selected ARR TP only | **No** |
| BoM All Design Rainfall CSV (EY / AEP percent / 1-in-N) | Yes | Yes | Yes, no implicit probability conversion | Exact original label only | **No** |
| ARR 2016/2019 point `*Increments.csv` | Yes | Yes | Yes, full vector and total | With exact IFD selection only | **No** |
| ARR 2016/2019 areal `*Increments.csv` | Yes | Yes | Yes, area bin preserved | With exact IFD selection only | **No** |
| ARR temporal-pattern `.zip` with `*Increments.csv` members | Yes | Yes | Yes, member hashes, paths, size and zip integrity | As above | **No** |
| ARR Data Hub 2026v1 IFD `RecIFD` | Yes (from #38) | Yes | Yes | Explicit raw distribution via manual table/pattern selection | **No** |
| BoM HTML, spatial grids, multipoint/coefficient tables | No | No | No | No | **No** |
| ARR 2026v1 TP ZIP variants beyond observed 2016 `Increments` schema | Unverified | No implied support | No | No | **No** |
| Losses, ARF, preburst, climate policies, burst extraction, TP choice, RORBwin adapter | Deferred | No | No | No | **No** |

These statuses distinguish data parsing, structural validation and storm arithmetic from method selection or routed-output acceptance. **BoM data is a separate source, not an ARR Data Hub JSON layer.** A BoM source's copyright statement may refer to the 2016 method even when its export date is much later; both are retained independently.

## BoM CSV source contract

- Supported observed shape: `IFD Design Rainfall Depth (mm)` **or** `All Design Rainfall Depth (mm)`, or corresponding explicit `Intensity (mm/h)` titles; `Issued:`, `Location Label:`, `Requested coordinate:`, `Nearest grid cell:` metadata; an optional frequency group row; then exactly `Duration,Duration in min,<probability labels...>` followed by a rectangular matrix.
- Both duration columns must agree. `1.5 hour` must correspond to numeric minute value `90` or `90.0`. Original duration labels, explicit numeric minute axis, full source bytes, SHA-256, source path spelling, issued date, requested WGS84 coordinates, nearest grid cell and unchanged rainfall values remain available.
- `12EY`, `0.5EY` and other exceedances/year labels are **EY**. `63.2%`, `50%`, `1%` and similar labels are **AEP_PERCENT**. `1 in 200` is **AEP_ONE_IN**, not `200%` or an ARI year without an explicit conversion. Optional `ARI_YEARS` is typed distinctly. The parser never converts any of these categories to one another. Duplicate axes, nonfinite/negative values and unknown units fail closed. No loss, ARF or climate adjustment is implicit.
- Intensity-to-depth is possible only using `depth_mm_at(..., convert_intensity=True)`; the unmodified input retains intensity units. No automatic interpolation, climate adjustment, year substitution, spatial averaging or duration rounding.
- Source bytes are bounded to 8 MiB; tests do not contact BoM. The CSV and ZIP payloads are **not** copied to the public repository without a rights review.

Two owner-supplied BoM point CSVs were reviewed locally (not committed). **Both parsed successfully**: 29 durations each, with 7 AEP columns and 18 mixed EY/AEP/rare columns respectively. Their requested and nearest-grid coordinates, duration sequence, and **all 203 corresponding IFD depths** agreed exactly. The original two files, coordinates and rainfall tables remain outside this public repository. This is **structural and overlap validation**, not an independent BoM numerical verification.

## Temporal-pattern intake

- Separate `point` and `areal` readers accept the characterised `EventID,Duration,TimeStep,Region,AEP,Increments` and `EventID,Duration,TimeStep,Region,Area,AEP,Increments` CSV schemas. Preserve source pattern IDs including leading zeros, source order, original region, AEP bin, area bin, percentages and byte hash. AEP bins are not converted to percentage probability (that belongs to an explicit later policy).
- Check `duration_min % timestep_min == 0`, vector length equals duration/timestep, percentages are finite and nonnegative, event IDs are unambiguous within their bin, and increments sum to 100% within an **explicit** rounding budget (default exactly 100%; budget capped at 0.5 percentage points).
- ZIP import validates all archive names (no absolute paths, `..`, backslashes or duplicates ignoring case), prohibits symlinks/encryption, imposes per-file/total byte, member-count and compression-ratio limits, and reads into memory without extracting. Individual CSV member SHA-256 and order are retained.
- Synthetically characterised CSVs do not constitute acceptance of **every** legacy/2026 temporal-pattern archive dialect. Real ARR TP ZIP replay remains an opt-in local acceptance requirement.

## Explicit unadjusted hyetograph API

```python
from decimal import Decimal
from pathlib import Path

from runoff_routing.arr_patterns import read_pattern_file
from runoff_routing.arr_storm import storm_from_bom
from runoff_routing.bom_ifd import read_bom_ifd_csv

ifd = read_bom_ifd_csv(Path(r"C:\rainfall\design.csv"))
patterns = read_pattern_file(Path(r"C:\rainfall\point_patterns.zip"), kind="point")
probability = ifd.probability("1%")
pattern = next(p for p in patterns.patterns if p.duration_min == 1440 and p.event_id == "001")
storm = storm_from_bom(ifd, probability, patterns, pattern)
assert sum(storm.increments_mm) == storm.total_mm
```

**This API is not an ARR storm generator.** The caller selects the original IFD probability label, exact source duration, and explicit TP ID. `depth_mm * increment_percent / 100` produces gross rainfall with end times in minutes, immutable provenance and an operation ledger. Increments not summing exactly to 100% are rejected for raw hyetograph creation (no hidden normalisation). No storm loss, ARF, climate uplift, preburst depth/ratio policy, embedded-burst screening, areal spatial pattern, ensemble choice or RORB `.stm` output is applied. Raw rainfall events are **not equivalent to accepted RORBwin or TUFLOW outputs**.

## Next review gates

1. Obtain permission-reviewed real legacy and 2026v1 point/areal TP ZIP exports; compare raw IDs, region/area/bin semantics and malformed archive response. Separate input shape verification from method interpretation.
2. Design **explicit policy** for IFD dataset selection (BoM vs Data Hub envelope), spatial/ARF, 2016 preburst methods vs 2026 ratio/derived-depth methods, loss layers, climate baseline/SSP/year and TP selection/embedded-burst filters. Prevent double adjustments by construction.
3. Design an S6-to-S2/RORBwin adapter that writes independent explicit storms, verifies effective inputs and compares engine-specific routed results. None of these acceptance gates are closed by import tests.

**Sources:** [BoM Design Rainfalls documentation](https://www.bom.gov.au/water/designRainfalls/); [ARR Data Hub legacy usage](https://data-legacy.arr-software.org/about); [ARR2016 temporal-pattern data semantics](https://www.arr-software.org/pdfs/ARR_190514_Book2.pdf); [RORB compatibility contract](COMPATIBILITY.md).
