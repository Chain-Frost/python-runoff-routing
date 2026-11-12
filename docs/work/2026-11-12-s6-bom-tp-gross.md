# S6 follow-up implementation record — BoM IFD, ARR TP and gross rainfall

**Date:** 2026-11-12. **Scope:** source-only rainfall input and arithmetic; dependent on draft [S6-P0 PR #38](https://github.com/Chain-Frost/python-runoff-routing/pull/38); separate S1/S2 numerical stages are not accepted. **Source contract:** [BoM and TP compatibility](../ARR_BOM_TP_GROSS.md).

## Implemented

- `bom_ifd.py`: exact BoM `IFD Design` and `All Design` CSV intake; separate location and nearest-grid metadata; double-duration axis consistency; typed EY/AEP-percent/1-in-N/ARI labels; depths versus explicitly requested intensity conversion; immutable original byte/hash identity.
- `arr_patterns.py`: offline point/areal ARR temporal pattern CSV and safe ZIP reads with member hash/ID/order/bin preservation and explicit percentages/rounding budget.
- `arr_storm.py`: explicit **unadjusted** gross per-timestep rainfall from an exact IFD axis cell and caller-selected temporal pattern; no design-method, climate, loss, preburst, ARF or RORB adapter.
- Synthetic tests include invalid axes/matrices, probability naming, duplicate duration/events, source bytes, areal/point bin confusion, unsafe ZIP paths/symlinks/compression, and gross rainfall conservation.

## Evidence and limitations

- Two private owner-supplied BoM CSV files were read without rewriting. 29 durations in each, 7 vs 18 probability columns; 203 shared AEP/duration rainfall-depth cells compared exactly, all equal. Raw BoM files and values are **not** distributed through this repository.
- Synthetic fixture tests and non-native quality checks recorded in PR CI. Target acceptance requires Windows Python 3.14, Ruff 0.16.6, strict Pyright and installed wheel outside checkout; pending until that CI has run on the final implementation head.
- No owner-supplied ARR TP archive was supplied for real ZIP replay. All temporal-pattern fixture tests are synthetic. Source-specific TP semantics and real ARR archive compatibility remain an open local gate.
- RORBwin input generation, engine execution, hydrological loss/climate policy and S6 numerical parity **not implemented**. No releases, merges, issue closure or new hosted workflows are implied.
