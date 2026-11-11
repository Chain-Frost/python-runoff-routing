# S6-P0 implementation record — ARR 2026v1 offline data intake

**Issue:** [#33](https://github.com/Chain-Frost/python-runoff-routing/issues/33). **Parent:** [#8](https://github.com/Chain-Frost/python-runoff-routing/issues/8). **Date:** 2026-11-11. **Status:** source-only work; no ARR method, generated event, or routed-flow acceptance.

## Scope

Standalone immutable and Decimal-preserving ARR data records, offline JSON/TXT readers, version/units validation, no-clobber JSON/CSV inventory exports and synthetic test corpus. This does not change S1 file APIs or S2 numerical kernels, and no external export content is committed.

## Source evidence

Production source: [2026v1 changelog](https://data.arr-software.org/changelog), [official API/export format](https://data.arr-software.org/about), and its linked public example at (-29.573, 152.648). The 2026v1 JSON `layers.RecIFD` uses three baseline keys with `index`, `columns`, `data`, while TXT uses `[RECIFD]`, baseline markers and metadata. The production JSON's `RecIFD` does not contain the TXT `Datasets` metadata. This distinction is retained. The example was inspected online to establish shape, not committed or counted as a local test. Live 2026 TXT baseline metadata includes `Datasets,BoM IFD (2016)`; no provider/year is invented from JSON.

## Verification and limitations

- Tests use three synthetic fixtures, with repeated baselines, numeric labels, malformed tables, duplicate AEP/duration, provenance bytes, missing layers, no-clobber and explicit legacy gating.
- The synthetic legacy 2019 location-only profile has **not** been tested against a genuine 2019 export; no legacy IFD support is claimed.
- External 2026 All IFD, CC-adj IFD and IFD CSV/ZIP structures have **not** been validated in this slice. Unknown default baseline shapes fail rather than being guessed.
- Linux/Python 3.13 test outcomes are supplementary; Windows/Python 3.14, pinned Ruff 0.16.6, strict Pyright and installed-wheel validation must be read from the implementation PR CI before acceptance.
- Exact implementation branch head and CI evidence are recorded on the implementation PR; this work record must not be interpreted as a stage gate.

See [S6-P0 format/capability matrix](../ARR_S6_P0.md). Remaining implementation phases are S6-P1 (safe temporal-pattern files), S6-P2 (jurisdiction/climate/loss policy) and S6-P3 (explicit storm generation and route adapters).

## Extension — historical ARR2016 TXT support (2026-11-11)

Implemented in the existing independent draft implementation PR #38, not PR #34 or the S1/S2 branches. Added the opt-in `arr2016` profile, typed source-faithful `LOSSES`, `LONGARF`, point/areal TP **regional IDs**, five paired-depth-and-ratio `PREBURST*` tables, and explicit unprocessed legacy `RIVREG`, `BOMIFD`, `CCF`, `BASEFLOW`/TUFLOW embedded patterns. Layer `Version` remains separate from the absent historical top-level Data Hub version. Added fail-closed `-50` missing sentinel handling and opt-in Windows CP1252 text decoding. The implementation does not invent missing BoM IFD depths or apply any historic RCP or current SSP uplift.

Documentation: [legacy format and limits](../ARR_LEGACY_TXT.md). Tests: `tests/test_arr_legacy.py` using synthetic fixtures. Initial local supplementary Linux/Python 3.13 checks: **67 focused tests passed** (`test_arr_legacy.py`, `test_arr_data.py`). Windows/Python 3.14 strict Ruff/Pyright and installed-wheel acceptance require final PR-head CI. No native RORBwin or hydrological acceptance has been claimed; legacy JSON and native parity remain explicitly open.
