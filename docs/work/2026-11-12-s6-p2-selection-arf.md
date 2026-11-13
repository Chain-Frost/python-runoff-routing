# S6-P2 ARR2019 source selection and ARF implementation record

**Date:** 2026-11-12. **Scope:** source-only ARR2019 temporal-pattern area/frequency rules, regional ARF equations and an explicit BoM gross-storm ARF adapter. Independent of S1/S2/RORB. **Status:** Draft stacked on S6-P1; no merge/release/stage closure.

## Exact files

- `src/runoff_routing/arr_selection.py` and `tests/test_arr_selection.py` — point vs areal area bands and exact regional ensemble filters.
- `src/runoff_routing/arr_arf.py` and `tests/test_arr_arf.py` — region-coefficient provenance, strict ARF equations and a distinct areal-reduced storm.
- `docs/ARR_S6_P2_SELECTION_ARF.md` — externally supported formulas, cross-implementation coefficient reconciliation, usage and applicability boundaries.

## Independent validation and exceptions

- Verified ARR2019 Book 2 v4.1 Table 2.4.2 **and** Tony Ladson's R gist **and** ryan-tools all have Inland Arid `g = +0.129`; the earlier claim of a negative gist coefficient was a source-review error. South-West WA `e = 3.85E−06` in Book 2 versus `3.845E−06` in the scripts remains a genuine difference. Do not alter the published coefficient or fit numerical errors.
- Book 2 Chapter 6.5.3 published East Coast North worked example: 245.07 km², 1440 min, 1% AEP → ARF approximately 0.929; exact Decimal computation ~0.9291683534.
- Scope excludes undocumented 2026 Data Hub method changes, implicit AEP/YR conversion, missing temporal patterns, silently chosen catchment size/region, unreviewed below-30-min/rare extrapolation and automatic climate/loss/preburst factors.
- Local real FLTwest pattern replay and synthetic regression counts are included in review evidence; keep originals private. Remote CI checks are tracked on the draft PR head and do not imply hydrological stage acceptance.

**Next review:** compare locally generated gross and ARF-reduced 10-pattern ensembles with a pinned RORBwin export for the same effective area, duration, AEP and model/region; select and record loss/preburst/climate policies before any runoff routing.

**2026-11-14 reconciliation:** `expected_count` no longer permits an incomplete ten-member ensemble; regression cases cover bypass attempts and duration bounds. Source-comparison wording corrected against the actual gist and ryan-tools file. No external numerical reference was fitted and ARR2026 policies remain unsupported.
