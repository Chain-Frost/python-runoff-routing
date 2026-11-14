# S6-P3: Legacy ARR preburst and IL/CL preparation

**Status:** pure, offline method implementation with synthetic-only loss examples. Hydrological and RORBwin numerical acceptance: **NOT RUN**. This work is stacked on S6-P2, S6-P1 and S6-P0; none of those stages implies routed-output parity.

## Source evidence and scope

- [ARR Book 5 v4.2, section 3.3.2](https://www.arr-software.org/pdfs/ARR_190514_Book5_V4.2.pdf): complete-storm regional storm initial loss (IL_s) is not interchangeable with the reduced initial loss of a design rainfall **burst**. For a burst-only series, subtract preburst depth from IL_s by a reviewed method; with a complete storm, retain IL_s.
- **RORBwin v6.52 release notes**, supplied privately to the owner: *Apply Pre-Burst* is available in ARR2016 mode, with **GSAM** default long-duration patterns and **Jordan et al. (2005)** short-duration patterns. At 12 hours, the 75 km² catchment-area threshold determines the default. A user-defined pattern may be supplied, but RORBwin's editor limits this to **60 non-zero-capable positions** and requires a compatible time increment. For ARR Data Hub preburst input, RORBwin applies **the ratio/percentage to the chosen design-storm depth**; its historical ARF double-application to preburst was fixed in the release notes. This module intentionally does **not** embed or re-create GSAM/Jordan tables, select a default GSAM zone, or claim those patterns have been replicated.
- [HARC forum](https://harc.com.au/forums/topic/pre-burst-rainfall/) contains a historical explanation of preburst adjustment in *earlier* RORBwin versions. The RORBwin 6.52 manual supersedes it for the version targeted here.

## APIs and safeties

`runoff_routing.arr_losses` exposes:

- `select_legacy_preburst_loss(document, *, duration_min, aep_percent, percentile=50, method, excess_policy)`: requires an explicitly parsed `arr2016_txt` legacy Data Hub document with both storm IL/CL and the chosen preburst percentile, duration and AEP. Retains original **depth and ratio as separate fields**, full source SHA-256, `source_tag`, loss metadata and original profile. No interpolation, sentinel substitution or implicit site-source matching. Negative burst IL is not silently treated as zero: default rejects preburst depths greater than storm IL; `clamp_burst_il_to_zero` is a separate documented opt-in which **does not recover** the runoff lost by a negative burst IL.
- `derive_preburst_from_areal_rainfall(selection, event)`: separate, **explicit** RORBwin-oriented hypothesis: multiply the original Data Hub ratio by the **already once-ARF-reduced design rainfall depth** (`AreaAdjustedHyetograph`). Keeps the source preburst depth in `source_preburst_depth_mm` and the applied ratio basis in `rainfall_basis_total_mm`. No further ARF is applied to preburst, and repeat ratio processing rejects. This is NOT evidence of exact GUI numerical equivalence.
- `verify_legacy_bom_source_point(bom, selection, event)`: requires identical *requested* WGS84 coordinates and matching original BoM byte hash. Neither grid-cell coordinates nor an invented catchment area override that check.
- `calculate_burst_only_excess(event, selection)`: a bounded, experimental IL/CL arithmetic operation on a design rainfall burst (not verified RORB IL/CL/within-timestep behaviour).
- `prepend_explicit_preburst(event, selection, *, percentages, declared_profile_id)`: requires a deliberate temporal profile that sums to exactly 100%; prepends preburst rainfall ending at time 0 and extends the time grid, retaining the **unaltered** storm IL. No default temporal profile, fraction rounding fix or interpolation is introduced.
- `calculate_complete_storm_excess(combined)`: experimental IL/CL accounting from the first preburst increment using original storm IL. Does not accept a burst-only initial-loss selection, avoiding dual treatment. Its timestep rule is *not* a substitute for verifying the RORBwin loss engine.

## Example: illustrative 100 km² catchment at Margaret River

- Coordinates from user's BoM exports: `lat=-33.953684`, `lon=115.0735`, **catchment area 100 km² is deliberately fabricated** for an end-to-end demonstration; no catchment boundary or calibrated model is claimed.
- Source BoM 24-hour / 1% AEP depth: **129 mm**; area-bin `100` in `Areal_FLTwest.zip`, ten event IDs `9091`–`9100`. Use original pattern `9091` for one check, never as automatically representative of ensemble runoff.
- Published South-West Western Australia coefficients give ARF ≈**0.9446027709**, once-adjusted design depth ≈**121.8537574 mm**.
- For this demonstration **only**, fabricate a legacy Data Hub record with the same requested point, **storm IL 21 mm**, **CL 2 mm/h**, and **preburst ratio 0.054**, with as-exported preburst depth set to 7 mm. These loss values and the two-increment (25%, 75%) preburst profile **are not actual Margaret River data or RORBwin default GSAM**. The applied ratio × 121.8537574 mm gives **6.5801029 mm**, separate from the fictional raw 7 mm. The method emits an operation ledger and confirms mass-balance arithmetic; do not treat its experimental runoff excess as a design figure.
- Original BoM CSV and ARR temporal-pattern ZIP files remain outside the public repository. Automated tests use synthetic data only.

## Acceptance gates remaining

1. Obtain an authentic **legacy** ARR Data Hub TXT export for this coordinate, or a validated 2026 loss product with an explicit source-specific conversion policy. Never substitute the synthetic IL, CL or preburst ratio in a design run.
2. Obtain a RORBwin 6.52 native comparison model and saved effective rainfall/preburst/loss settings (including GSAM zone and preburst pattern, timestep, exact print locations); reproduce the selected design storms and rainfall excess before attempting routing comparisons.
3. Evaluate RORBwin's actual percentage interpolation, 12-hour boundary, preburst duration/spacing, early losses, embedded-burst filtering, and source precision against a pinned native profile. Do not close S6 or declare rainfall-method acceptance from unit checks.
4. Later independently implement ARR Data Hub 2026v1 jurisdiction/SSP/loss/preburst policy. The legacy contract does not silently apply to 2026 outputs.
