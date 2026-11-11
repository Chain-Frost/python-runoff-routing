# S2 source-volume reporting convention diagnostic

- **Date:** 2026-11-11. **Issue:** [#4](https://github.com/Chain-Frost/python-runoff-routing/issues/4).
- **Branch:** `feat/s2-native-report-volume-20261111` (independent `main` slice; S1/S2 integration PR #23 and ARR/JSON agents remain untouched).
- **Purpose:** Introduce a pure Decimal-precision reporting audit so the legacy native inclusive sample-sum summary is not conflated with the physical-horizon trapezoid in S2 conservation checks. Preserve raw printed time tokens and a separate sample-index axis. Both candidate intervals use raw print half-unit bounds; no fitted tolerances.
- **Source:** [Private independently retained 116-column summary study](https://github.com/Chain-Frost/runoff-routing-investigations/blob/main/docs/work/2026-11-11-source-phase-volume.md). Its 26 discriminating cases are not copied as raw files or accepted as full engine equivalence.
- **Implementation:** `reporting_conventions.audit_volume_conventions` and standalone synthetic tests. No numerical kernel, S1 model, parser, live reference runner, source dataset, workflow or package dependency change.
- **Validation:** Exact-head Windows/Python 3.14 quality and installed-wheel evidence to be recorded before review. No native launch, private-corpus replay or QGIS execution is part of this work.
- **Limit:** Reporting consistency is not hydrological, timestep/phase or native model parity. The old 36/36 S2 printed-ordinate failures remain failures.
- **Next:** Review this pure API and selectively integrate separately labelled reporting fields into the typed S1/S2 result path, without altering the existing independent physical water-balance integrals.

[Design and example](../S2_REPORTING_CONVENTIONS.md) · [S2 regression contract](../REGRESSION.md).
