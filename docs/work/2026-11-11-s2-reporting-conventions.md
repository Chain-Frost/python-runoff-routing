# S2 source-volume reporting convention diagnostic

## Owner-requested integration review, 2026-11-13

PR #40 original implementation `ead4b54989c98da68ae4229e1b006d901a58635c` was reviewed against
main `1cfc72b79b9855f796e1f21d2df27d147d9f225b`. Only the two documentation-index conflicts
needed resolution; current integration records and reporting links are both retained.
The reporting module remains byte-identical (Git blob `be4e91a53adfd59ea50920b1cd3c08999712c3d3`).

Windows/Python 3.14.6: repository checks 90 files / zero errors, pinned Ruff lint/format
(80 Python files), strict Pyright zero errors/warnings, and all 298 non-native tests pass,
without skips. The first pytest attempt imported the global editable checkout and failed
collection; explicitly setting this worktree's source path fixed environment selection.

A fresh wheel was built and installed in its own environment. The private #27 verifier
ran outside this public checkout with no source PYTHONPATH: 36 original reports, 30 CMD
and six GUI, all 116 columns inclusive-sum consistent, 26 trapezoid exclusions; the
40-entry evidence inventory verifies before and after. Installed module origin and
original reporting blob are enforced by that verifier. No new native calculations or
numerical acceptance are implied. The owner requested #40 merge before #45, conditional
on review and exact-head hosted checks. The merge commit and hosted result are recorded
in the PR conversation after publishing; no release or stage closure is authorised here.

- **Date:** 2026-11-11. **Issue:** [#4](https://github.com/Chain-Frost/python-runoff-routing/issues/4).
- **Branch:** `feat/s2-native-report-volume-20261111` (independent `main` slice; S1/S2 integration PR #23 and ARR/JSON agents remain untouched).
- **Purpose:** Introduce a pure Decimal-precision reporting audit so the legacy native inclusive sample-sum summary is not conflated with the physical-horizon trapezoid in S2 conservation checks. Preserve raw printed time tokens and a separate sample-index axis. Both candidate intervals use raw print half-unit bounds; no fitted tolerances.
- **Source:** [Private independently retained 116-column summary study](https://github.com/Chain-Frost/runoff-routing-investigations/blob/main/docs/work/2026-11-11-source-phase-volume.md). Its 26 discriminating cases are not copied as raw files or accepted as full engine equivalence.
- **Implementation:** `reporting_conventions.audit_volume_conventions` and standalone synthetic tests. No numerical kernel, S1 model, parser, live reference runner, source dataset, workflow or package dependency change.
- **Exact implementation-head Windows quality:** [run #43056909818](https://github.com/Chain-Frost/python-runoff-routing/actions/runs/43056909818), commit `59af53673d7cd55d5d12082f67c9355ba1a03a6a`, Python **3.14.10**, hygiene **65 files / 0 errors**, Ruff 0.16.6 lint/format clean, strict Pyright **0 errors**, **158/158 public non-native tests passed**, wheel built and imported outside checkout with `py.typed` verified. The preceding failed runs were lint/format/strict-typing compliance issues, not numerical evidence. No native launch, private-corpus replay or QGIS execution is part of this work.
- **Limit:** Reporting consistency is not hydrological, timestep/phase or native model parity. The old 36/36 S2 printed-ordinate failures remain failures.
- **Next:** Review this pure API and selectively integrate separately labelled reporting fields into the typed S1/S2 result path, without altering the existing independent physical water-balance integrals.

[Design and example](../S2_REPORTING_CONVENTIONS.md) · [S2 regression contract](../REGRESSION.md).
