# S1 optional PyROMB-derived GE authoring

- **Stage:** [S1 issue #3](https://github.com/Chain-Frost/python-runoff-routing/issues/3), with [code-7 fix PR #25](https://github.com/Chain-Frost/python-runoff-routing/pull/25) merged into baseline. **Owner:** Unassigned.
- **Date:** 2026-11-11. **Branch:** `feat/s1-pyromb-ge-authoring-20261111`, isolated on the live `main` head.
- **Reference:** [PyROMB PR #16](https://github.com/norman-tom/pyromb/pull/16) at `a323d5709f7ce14c6adf46f01e0224b60668340c`, MIT; source and licence notices retained. PR #16 adds error checks and OGR GIS matching but does **not** modify PyROMB's GE writer/traveller.
- **Scope:** Optional direct-coordinate GE 002 drawing writer, exact computational-vector preservation, explicit GIS-to-source/reach identity checks, basin-polygon OGR matching and validation of connected outlet-rooted topology. No changes to S0, solver equations, existing corpus, execution or CI workflow.
- **Software-quality validation (implementation head `ec745ea7db7f3d6b29e2f3d6781cc0fd3c6d13ce`):** [Windows quality run #43044618442](https://github.com/Chain-Frost/python-runoff-routing/actions/runs/43044618442) **passed** on CPython 3.14.10: repository hygiene 0 errors, Ruff 0.16.6 lint/format clean, strict Pyright 0 errors, **123/123 non-native tests** (0 skips), wheel built and installed/imported outside checkout with `py.typed` checked. Synthetic OGR doubles cover validation paths, not the installed GDAL driver or live QGIS. Earlier run #43044273893 had 122 passes and one flawed test setup, corrected without changing the writer or solver.
- **Native acceptance:** QGIS/OSGeo4W real GDAL/OGR and native RORB_CMD/RORBwin execution are **NOT RUN** for this authoring layer; model parse/write/parse equivalence is not native acceptance.
- **Unsupported:** GE 6.45 input dialect, non-tree GIS networks, special storage/diversions, imperviousness, intermediate/multiple print points, automatic CRS discovery/transforms, GUI profile or numerical native parity.
- **Next action:** Review the authoring API and run named, isolated native CMD/GE acceptance; inspect field widths and code-7 location semantics against native output. Keep issue #3 open.

[Detailed authoring API](../RORB_GE_AUTHORING.md) · [Bidirectional input boundary](../RORB_BIDIRECTIONAL.md) · [Private/reference evidence contract](../REGRESSION.md).
