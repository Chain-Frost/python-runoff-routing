# S6 #63 — PyTUFLOW optional offline ARR source audit

**Updated:** 14 November 2026. **Status:** drafted source-only review and optional probe, not merged or accepted. **Owner:** Unassigned. **Tracking:** [#63](https://github.com/Chain-Frost/python-runoff-routing/issues/63); parent [#8](https://github.com/Chain-Frost/python-runoff-routing/issues/8). **Branch:** research/s6-pytuflow-offline-interop-63. **Base revision:** 1c2fdb0507e38d0a61718aa8f1ab11fa028c2dd2.

## Scope and findings

Pinned release/1.3.0 Git commit 1a9459ddec9fb14e339cbfcd5413a701b6ab1ac9 and PyPI wheel SHA-256 8984c48104af418e24f086580e9176189c416ccc8ccd4eb77ad6aebda88ded50. Independently reviewed PyTUFLOW RecIFD baseline, point/areal CSV and optional temporal-pattern selection source. Added an opt-in source-only probe and synthetic boundary tests without replacing ARRDocument, IFDDataset, PatternSet, BoM data, loss methods or the routing solver. Documented [reuse versus independent decision](../ARR_PYTUFLOW_INTEROPERABILITY.md). No third-party code, original data or new mandatory dependencies.

## Verification

Exact-head quality check and existing Windows/Python 3.14 CI must be recorded after PR creation; this note does not preclaim their outcome. No PyTUFLOW runtime is installed in the execution environment used to author this slice. Pinned PyTUFLOW import and authentic offline 2026 JSON/TP comparisons: **NOT RUN**. No reference-engine runs, generated-input comparisons, climate/preburst method acceptance, native tolerance changes or routed-output acceptance.

## Next action

Use a separately controlled Windows/Python 3.14 environment to install/verify the exact PyTUFLOW 1.3.0 wheel, run optional offline source comparisons on rights-cleared Data Hub JSON and point/areal CSV/ZIP (both areal layouts), and record complete original hash/ID/axis/unit outcomes and import failures. Preserve separate RORBwin native input and solver acceptance gates, with S6 #8 and #33 open.


## Actual historical-source diagnostic replay

See the [Margaret River evidence record](2026-11-14-s6-margaret-river-source-replay.md): four source hashes verified, 203/203 overlapping BoM values equal, 1,611 original TP patterns each total exactly 100%, explicit incomplete 40,000-km² cohort and upstream area-bin source-policy differences. This is a **source-reproduced audit**, not an installed PyTUFLOW or ARR2026 numerical pass. The original files remain out of the public repo.
