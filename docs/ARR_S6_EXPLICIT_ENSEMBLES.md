# S6: explicit ARR2019 ten-event hyetograph ledger

**Status:** implementation proposed on a separate S6 topic PR; synthetic verification only until the exact-head quality gate. This is not generated-input native acceptance.

`arr_selection.select_arr2019_ensemble` selects ten **source-order** ARR2019 regional temporal patterns. `arr_storm.storm_from_bom` produces one explicitly selected gross storm. This slice composes those existing APIs without adding a new parser, rainfall equation, hydrologic assumption or representative-event policy.

## Opt-in API

```python
from decimal import Decimal

from runoff_routing.arr_ensemble import (
    build_explicit_arr2019_ensemble,
    explicit_ensemble_inventory_json,
)
from runoff_routing.arr_selection import select_arr2019_ensemble

# bom, pattern_source and an explicitly selected BoM probability are loaded separately.
selection = select_arr2019_ensemble(
    pattern_source,
    catchment_area_km2=Decimal("100"),
    duration_min=1440,
    aep_percent=Decimal("1"),
    region="S-SW Flatlands (West)",
)
ensemble = build_explicit_arr2019_ensemble(
    bom, bom.probability("1%"), pattern_source, selection, arf=reviewed_arf
)
ledger = explicit_ensemble_inventory_json(ensemble)
```

In this example, `reviewed_arf` is an **explicitly calculated** `ARFResult` selected separately by the caller (including a reviewed long-duration regional coefficient source); it is not supplied by the adapter.

The adapter requires a source-hash-matching, policy-recomputed ten-member selection; an exact **BoM AEP percentage** (not EY, ARI or one-in-N); exact IFD duration; and, if provided, an ARF with matching area/duration/AEP. It retains source event IDs including leading zeros, separate 1-based *source-order ordinals* for audit only, source hashes, precise `Decimal` gross/areal increments, end times in minutes, unrounded totals and ARF coefficient provenance. It rejects incomplete or reordered selections, mismatched sources, and percentages not summing **exactly** to 100 rather than silently renormalising.

The optional ARF uses the existing `apply_arr2019_arf_to_bom_storm` once for each independent gross storm and retains the original gross event; no second ARF application is possible through that typed API. The ledger uses decimal **strings**, not JSON floating-point numbers, and changes no files. Callers handle all filesystem output and no-clobber policy.

**Explicit exclusions:** no sampling, representative-event or peak-flow selection; no ARR2026 scenario methods, climate uplift, RORB numbering inference, spatial distribution, embedded-burst filtering, losses, preburst, default GSAM/Jordan profiles, RORB `.stm` writer or routed hydrograph comparison. The ledger labels hydrological acceptance `not_assessed`, and a green synthetic test cannot change that status.

## Verification and remaining work

Synthetic point/areal fixtures exercise all ten source IDs, ordinal distinction, exact numeric vectors, once-only ARF, area/AEP/duration identity, source-hash and selection-order mismatch, and failure for a near-100% pattern. No original BoM, Data Hub or FLTwest bytes are published.

Before using this ledger for native acceptance, an independent operator must record the actual native GUI/CMD effective storm settings, native sample-to-EventID mapping, original source hashes, saved/generated 24-cell vectors and frozen printed/full-precision comparison policies. Cross-check all ten generated storm vectors with RORBwin before selecting or routing any representative event. Native R0–R7 and N1–N3 evidence and the unverified Coastal settings remain separate, unchanged investigations. See [S6 acceptance matrix](ARR_S6_INTEGRATION.md), [regression rules](REGRESSION.md) and [stage issue #8](https://github.com/Chain-Frost/python-runoff-routing/issues/8).
