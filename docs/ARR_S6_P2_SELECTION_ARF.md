# S6-P2: ARR2019 temporal-pattern selection and areal reduction factors

**Status:** deterministic source-only computations and guarded storm adjustment; no RORBwin event/flow parity, ARR2026 method certification, or climate/loss/preburst selection. No external package dependency, network access, geospatial inference or plotting. Branch based on the S6-P1 implementation PR.

## Sources and scope

- Australian Rainfall and Runoff **ARR2019 Book 2 v4.1**, Chapter 4.3, equations 2.4.1–2.4.4 and Table 2.4.2; Chapter 5.9, Table 2.5.9, [PDF](https://www.arr-software.org/pdfs/ARR_190514_Book2_V4.1.pdf). Original ARF coefficients and policies are based on this document's explicit ranges, **not** imported plotting software.
- [Tony Ladson's 2020 ARF explanation](https://tonyladson.wordpress.com/2020/04/05/arr2019-areal-reduction-factors/) and [R reference](https://gist.github.com/TonyLadson/fc870cf7ebfe39ea3d1a812bcc53c8fb), used as an independent cross-check, not copied or vendored.
- [`Chain-Frost/ryan-tools` `ARF-calcs.py`](https://github.com/Chain-Frost/ryan-tools/blob/main/ryan-scripts/hydrology-python/ARF-calcs.py) is useful precedent, but has matplotlib/pandas requirements, `float` input, warnings/`None` for invalid inputs, and an example script. This work implements a small, typed, dependency-free version.

**Source coefficient audit:** Official 2019 Book 2 Table 2.4.2, Tony Ladson's 2020 R gist and ryan-tools **all list Inland Arid `g = +0.129`**; the previous claim that the gist uses a negative value was incorrect. The verified discrepancy is **South-West Western Australia `e`**: Book 2 prints **`3.85E−06`**, while both scripts use **`3.845E−06`**. The package's built-in reference uses the published Book 2 values; users may instead supply the original *versioned* Data Hub coefficients through `legacy_datahub_coefficients(document)`. Such values are not silently substituted, averaged or rounded to the published value.

## Temporal pattern selection — `arr_selection.py`

`select_arr2019_ensemble(source, *, catchment_area_km2, duration_min, aep_percent, region, expected_count=10)` selects **the exact source-order 10-pattern ensemble**; attempts to override `expected_count` to any value other than 10 now fail closed; never selects the maximum/representative event and does not infer a catchment area from coordinates.

- **Point** patterns for catchments strictly **below 75 km²**. Common design probability bins: 50/20% AEP → frequent, 10/5% → intermediate, 2/1% → rare. Other AEP/EY/ARI labels reject pending explicit frequency policy.
- **Areal** patterns from 75 km² onward. Table 2.5.9 defines half-open catchment-area intervals: `[75,140) → 100`, `[140,300) → 200`, `[300,700) → 500`, `[700,1600) → 1000`, `[1600,3500) → 2500`, `[3500,7000) → 5000`, `[7000,14000) → 10000`, `[14000,28000) → 20000`, `[28000,+∞) → 40000`.
- Exact region, source kind, duration and area bin are mandatory. An **areal archive without an AEP field** stays `aep_band=None`; it is not silently assigned the requested AEP. Areal archives that provide a frequency label must agree with the selected band.
- A regional archive lacking the requested 10-member ensemble **raises** rather than borrowing another region/duration/area bin. For FLTwest the large-area 10,080-minute (`40000`) sample is incomplete (one member), and regional areal events below 12 hours are absent; neither is repaired or misreported.

## ARF calculation — `arr_arf.py`

`calculate_arr2019_arf(*, catchment_area_km2, duration_min, aep_percent, coefficients=None, ...)` returns a frozen `ARFResult` containing **Decimal** input/output, factor, coefficient source, method-version and exact applied formula steps:

1. Area ≤1 km²: ARF = 1. Area 1–10 km²: Book 2 equation 2.4.4 interpolation from area 10 km².
2. Duration ≤720 min: nationwide short-duration equation 2.4.1; unsupported for area >1000 km².
3. Duration ≥1440 min: region-specific long-duration equation 2.4.2; require explicit regional coefficients for area >1 km².
4. Between 720 and 1440 min: linear interpolation 2.4.3 between the 12-hour short and 24-hour long endpoints. For area >1000 km², the method explicitly records that the short endpoint is an ARR2019-recommended extrapolation.
5. Inputs are explicit units: area **km²**, duration **whole minutes**, AEP **percentage** (not fraction/EY/ARI). AEP is converted to a fraction internally only for the equation. Area >30000 km² and duration >10080 min reject; no extrapolation without operator acknowledgement.
6. Equations were calibrated for event durations at least **30 min** and AEP roughly **1–50%**. Durations below 30 min and 0.05–1% AEP require separate opt-ins and generate visible operation codes. AEP below 0.05% rejects. Nonphysical negative ARFs fail by default; `negative_policy="floor_zero"` is an explicit opt-in, recorded in the method ledger.

`apply_arr2019_arf_to_bom_storm(gross, calculation)` operates **only** on an unadjusted `RawHyetograph` created from a BoM gross IFD depth. It verifies the exact AEP and duration, returns a different `AreaAdjustedHyetograph` type, and retains original gross depths, factor, IDs, SHA-256 and adjustment ledger. Do not use it to apply ARF to an ARR climate/areal-adjusted IFD or to silently re-apply a factor. **No effective-rainfall excess, spatial rainfall distribution or runoff** is computed.

## Explicit Margaret River replay (private source files remain uncommitted)

- BoM requested coordinate: **−33.953684, 115.0735**; BoM IFD source supplies the *24-hour / 1% AEP* gross depth **129 mm**.
- `FLTwest.zip` point region label in the CSV: `S-SW Flatlands (West)`; `Areal_FLTwest.zip` uses the same label. A catchment of **50 km²** correctly selects point patterns; **75 or 100 km²** correctly selects areal bin `100`.
- For a hypothetical **100 km² catchment**, choosing the **South-West Western Australia** ARF coefficient set from Book 2 gives approximately **0.944603** (24-hour, 1% AEP), and **121.85 mm** gross areal-reduced rainfall. This is a *worked arithmetic illustration*, not a claim that the actual Margaret River catchment is 100 km² or that the selected ARF region has been independently spatially verified. The actual catchment polygon/area, regional overlaps, hydrological losses, climate period and RORBwin method must be reviewed before design use.
- Point ZIP SHA-256: `0cd57da5e7dffd8f235b72d3e59c83ac1ab9f2e54f03e94201340e307ed83adb` (50 km², 24h/1%: ten patterns, original IDs beginning `1929`, `7638`). Areal ZIP SHA-256: `61c60366f953669a9879c5e2c6619b3c420c3a3dceeb296fa41e91606b3c213f` (100 km², 24h/1%: ten patterns, original IDs `9091`–`9100`). Each disaggregates 129 mm gross rainfall without gain/loss. Original FLTwest ZIP and BoM CSV bytes remain private local evidence only. Public tests use **synthetic pattern and depth values**.

## Test and acceptance boundaries

- Synthetic tests exercise every area-band boundary, point frequency grouping, source order, missing areal AEP, incomplete ensembles, invalid area/frequency/duration, ARF equation branches (including independent double-precision formulas and the published 0.929 worked example), range exclusions, and once-only adjustment.
- Local pure-Python replay on the supplied **unmodified** FLTwest archives demonstrates both source types and failure modes; no original ZIP or BoM CSV committed.
- Windows/Python 3.14, pinned Ruff, strict Pyright, wheel installation and CI are the required gates for merging this slice. ARF validation is computational **method/formula** verification, not field-engineering approval or parity with RORBwin.
- Remaining: characterize ARR2026-specific default/regional ARF and scenario rules; obtain actual catchment boundary and confirm region by catchment overlap; loss/preburst/ARF interaction; RORBwin source storm generation and hydrological acceptance; ensemble hydraulic ranking/representative selection (not yet known).
