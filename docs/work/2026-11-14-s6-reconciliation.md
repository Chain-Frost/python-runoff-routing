# S6 four-PR reconciliation and next acceptance gates

**Date:** 2026-11-14. **State:** reconciled and **merged** #38 → #48 → #49 → #50. All four exact-head Windows/Python 3.14 workflows passed pinned Ruff, strict Pyright, non-native tests, wheel builds and installed-wheel import. This is an **implementation/quality** milestone, **not** hydrological or RORBwin numerical acceptance. No release, package publication, parent issue closure, S2 solver or tolerance changes.

## Changes and retained boundaries

- Reconciled #38 -> #48 -> #49 -> #50 against `main` `e00e34d8e74ab5e5454aeb03e3f2af3532b12ed7` with curated main-based Git trees. Inherit S1/S2/S5 implementation and index updates instead of overwriting with historical branch content.
- Removed duplicate P1 work-register rows and obsolete documentation index versions. Independent source/preparation modules remain separate from S1 and S2.
- P0 verifies original ARR source SHA-256 in typed record construction. P1 extends only the existing approved wheel smoke.
- P2 rejects all overrides of required ten-pattern ensembles and invalid durations; corrects a mistaken Tony Ladson Inland Arid sign claim. SW WA e precision difference remains and is not fit to a native error.
- P3 checks reconstructed preburst ratios, source rainfall basis, selected percentile and the once-only storm IL reduction; adds a stage-classified [capability matrix](../ARR_S6_INTEGRATION.md).

## Integration commits and Windows quality

| Slice | Squash merge on `main` | Reconciled-head Windows run | Non-native tests |
| --- | --- | --- | ---: |
| [P0 #38](https://github.com/Chain-Frost/python-runoff-routing/pull/38) | `855ea542baf2003917491386390253c3fbf6c5e5` | [43501893876](https://github.com/Chain-Frost/python-runoff-routing/actions/runs/43501893876) | 454 |
| [P1 #48](https://github.com/Chain-Frost/python-runoff-routing/pull/48) | `3770144651215a497cb058522fd79068b72f46fe` | [43547492821](https://github.com/Chain-Frost/python-runoff-routing/actions/runs/43547492821) | 503 |
| [P2 #49](https://github.com/Chain-Frost/python-runoff-routing/pull/49) | `3b4b0577893e3ca388ca50d4089c178311fb2623` | [43547658623](https://github.com/Chain-Frost/python-runoff-routing/actions/runs/43547658623) | 613 |
| [P3 #50](https://github.com/Chain-Frost/python-runoff-routing/pull/50) | `f9ae827fc164357e1ab2ecf24281044d8c19eef9` | [43547821011](https://github.com/Chain-Frost/python-runoff-routing/actions/runs/43547821011) | 649 |

Each downstream PR was reconciled after the preceding squash merge using a **byte-identical reviewed source tree** and a fast-forward ancestry commit; no historical branches were merged wholesale. S6 arithmetic policies, native reference inputs, source hashes and tolerances were not changed during the merge phase.

## Native evidence — not accepted

R0 has 24/24 exact zero-loss source increments. R1 has 24/24 rainfall cells within printed precision but fails the strict full-precision excess gate, including step 16. Native raw excess time labels differ from hydrograph labels by an observed one increment. No automatic timestamp shift, rounding substitution or tolerance change is authorised.

Separate [draft PR #54](https://github.com/Chain-Frost/python-runoff-routing/pull/54) explores an opt-in RORBwin 6.52 full-increment CL profile: 42/42 initial controls, six R2–R5 strict residuals, and one additional R7 residual under separately pinned experiments. The R6/R7 Inland preburst-area boundary is documented, but Coastal saved effective settings remain unresolved. This experimental code is **not** merged into P0–P3 or selected as a default.

## Validation and review sequence

1. Preserve the reviewed exact-head Windows/Python 3.14 quality records above; repeat checks for future implementation or contract changes.
2. Reconfirm authentic ARR2026 optional layers, dataset baselines, missing fields and versioned hashes independently of legacy ARR2019 method assumptions.
3. Freeze site source data, region/area, 10 member event IDs, native engine/profile/effective controls and compare R0/R1 raw rainfall and excess with original tolerances.
4. Review conditional IL/CL and preburst timing, GSAM/Jordan defaults and separate PR #54 strict precision failures without fitting the observed mismatches.
5. Compare routed hydrographs only once generated-input identity passes; keep S2 numerical compatibility separate.

**Merge posture:** #38, #48, #49 and #50 are **merged**. [PR #54](https://github.com/Chain-Frost/python-runoff-routing/pull/54) remains **draft, experimental and separately unaccepted**. Parent issues [#8](https://github.com/Chain-Frost/python-runoff-routing/issues/8) and [#33](https://github.com/Chain-Frost/python-runoff-routing/issues/33) remain open.
