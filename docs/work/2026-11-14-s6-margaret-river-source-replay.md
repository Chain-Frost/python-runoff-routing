# S6 #63 — Margaret River original-source offline replay

**Updated:** 14 November 2026. **Status:** source integrity and upstream-*source-reproduced* comparisons completed; installed PyTUFLOW and RORBwin numerical validation **not performed**. **Related:** [#63](https://github.com/Chain-Frost/python-runoff-routing/issues/63), [draft PR #71](https://github.com/Chain-Frost/python-runoff-routing/pull/71), [S6 acceptance #8](https://github.com/Chain-Frost/python-runoff-routing/issues/8).

## Inputs and integrity

Original files were recovered from the owner's previous private ChatGPT Library uploads, examined offline and left unchanged. No original CSV or ZIP was committed to the public repository.

| File | SHA-256 of original bytes | Result |
| --- | --- | --- |
| depths_margaret_river_ifds.csv | `0ca11f66c2a1cb7e48e8bd6fc852f52dfa68014377c16301f5d57495c54864db` | exact hash verified |
| depths_margaret_river_all_design.csv | `7a739958861f82c26e37a568ebabc56fe1dfe16f442b891d7978d54e710a5197` | exact hash verified |
| FLTwest.zip | `0cd57da5e7dffd8f235b72d3e59c83ac1ab9f2e54f03e94201340e307ed83adb` | exact hash verified |
| Areal_FLTwest.zip | `61c60366f953669a9879c5e2c6619b3c420c3a3dceeb296fa41e91606b3c213f` | exact hash verified |

## Offline replay results

- BoM 2016-methodology exports issued November 2026: **29 × 7** IFD depth table and **29 × 18** All Design table (mixed EY, AEP percent and one-in-N); **203/203** common depth cells agree exactly. Example 24 h / 1%: **129 mm** unadjusted.
- Original point ZIP `FLTwest.zip`: **720/720** event vectors sum to exactly 100%, **14,340** increments. Frequency bands frequent, intermediate and rare; original source IDs retained.
- Original areal ZIP `Areal_FLTwest.zip`: **891/891** event vectors sum to exactly 100%, **27,216** increments. Original areal AEP **absent**, not inferred.
- **41,556/41,556** percentage values are numerically preserved by the pinned parser's `Decimal(str(float(value)))` representation for these original tokens, but only **3,410/41,556** are exactly representable in binary64. Do not generalise this to higher-precision sources.
- **1,611/1,611** source IDs roundtrip through the pinned parser's integer conversion for this specific dataset; the general source-ID-token policy remains stricter because arbitrary leading zeros cannot be recovered from integers.
- **One incomplete source cohort:** area-bin `40000` at **10,080 min** contains only one areal pattern. Upstream 1.3.0 source-selection logic accepts this nonempty partial cohort; strict ARR2019 ten-member selection must reject.
- **Area-bin policy difference:** pinned PyTUFLOW selects first bucket ≥ catchment area (for example, at 125 km² it uses 200), while the implemented ARR2019 lower-bound bins select 100 at 125 km². No automatic policy substitution.

## Execution classification

Environment: local Linux/Python **3.13.5**, standard-library CSV/ZIP/Decimal validation and a **reproduction of the relevant upstream 1.3.0 parser/selection expressions** from source review. **PyTUFLOW package not installed, imported or run; no Windows/Python 3.14 third-party compatibility claim.** No authentic ARR2026 `RecIFD` JSON among these files. No RORBwin/CMD launches. No original source archives or tables exported to the repository.

**Next:** run the already implemented optional probe with a verified installed pinned PyTUFLOW 1.3.0 wheel on Windows/Python 3.14, using original local point/areal ZIPs; compare optional ARR2026 baseline `RecIFD` inputs separately when an authentic export is available. Keep #8 and #63 open and preserve source versus native numerical acceptance gates.
