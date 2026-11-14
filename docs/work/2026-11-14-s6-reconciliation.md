# S6 four-PR reconciliation and next acceptance gates

**Date:** 2026-11-14. **State:** draft, unmerged. Windows/Python 3.14 quality must be verified at the revised PR heads. No package publication, parent issue closure, S2 solver or tolerance changes.

## Changes and retained boundaries

- Reconciled #38 -> #48 -> #49 -> #50 against `main` `e00e34d8e74ab5e5454aeb03e3f2af3532b12ed7` with curated main-based Git trees. Inherit S1/S2/S5 implementation and index updates instead of overwriting with historical branch content.
- Removed duplicate P1 work-register rows and obsolete documentation index versions. Independent source/preparation modules remain separate from S1 and S2.
- P0 verifies original ARR source SHA-256 in typed record construction. P1 extends only the existing approved wheel smoke.
- P2 rejects all overrides of required ten-pattern ensembles and invalid durations; corrects a mistaken Tony Ladson Inland Arid sign claim. SW WA e precision difference remains and is not fit to a native error.
- P3 checks reconstructed preburst ratios, source rainfall basis, selected percentile and the once-only storm IL reduction; adds a stage-classified [capability matrix](../ARR_S6_INTEGRATION.md).

## Native evidence — not accepted

R0 has 24/24 exact zero-loss source increments. R1 has 24/24 rainfall cells within printed precision but fails the strict full-precision excess gate, including step 16. Native raw excess time labels differ from hydrograph labels by an observed one increment. No automatic timestamp shift, rounding substitution or tolerance change is authorised.

Concurrent [PR #54](https://github.com/Chain-Frost/python-runoff-routing/pull/54) explores a separate RORBwin 6.52 full-increment CL profile, including 42/42 isolated controls and six unaccepted cached precision failures. This experimental code is **not** integrated into P0-P3 or selected as the default.

## Validation and review sequence

1. Record revised exact-head Windows/Python 3.14 results for hygiene, pinned Ruff 0.16.6, strict Pyright, full synthetic suite, wheel build and independent installed-wheel imports. Earlier CI cannot validate the updated stack.
2. Reconfirm authentic ARR2026 optional layers, dataset baselines, missing fields and versioned hashes independently of legacy ARR2019 method assumptions.
3. Freeze site source data, region/area, 10 member event IDs, native engine/profile/effective controls and compare R0/R1 raw rainfall and excess with original tolerances.
4. Review conditional IL/CL and preburst timing, GSAM/Jordan defaults and separate PR #54 strict precision failures without fitting the observed mismatches.
5. Compare routed hydrographs only once generated-input identity passes; keep S2 numerical compatibility separate.

**Merge posture:** #38, #48, #49, #50 remain draft and unmerged pending owner authorisation and exact-head review. Parent issues #8/#33 stay open.
