# S5-P1: JSON projects and Python-only routing

**Date:** 2026-11-12. **Scope:** isolated implementation from current main. **Issues:** [S5-P1 #44](https://github.com/Chain-Frost/python-runoff-routing/issues/44), [S5-P0 #35](https://github.com/Chain-Frost/python-runoff-routing/issues/35), [S5 #7](https://github.com/Chain-Frost/python-runoff-routing/issues/7). **Status:** draft implementation, exact-head Windows CI and installed-wheel gate pending.

## Implemented

- Includes the prior S5 JSON import/validation/export work from [draft PR #36](https://github.com/Chain-Frost/python-runoff-routing/pull/36), transplanted without changing its source semantics onto main, which now includes the merged S1/S2 integration PR #23. Coordinate reviews; do not merge competing S5 implementations independently.
- Calls the existing S1/S2 integration.run_model and its strict numerical backend; does not fork a catchment model, storm parser or numerical solver.
- Rejects arr-2026v1 execution and unprocessed external rainfall/TP/curve references. Legacy-rorb is executable only for an already supplied, supported explicit storm.
- Records source, project and typed-model SHA-256 provenance, full S1 print-site identities, calculated series and explicit computed_unvalidated / native_parity not_assessed statuses. No source rewriting or time-label shifts.
- Adds exact Python project comparison with independently reported model, asset, print-site and ordinate differences; reports diagnostic_only, not native parity.
- Adds run and compare-runs CLI with deterministic machine-readable output and no-clobber report writes.
- Public synthetic cases cover embedded versus file-backed RunModel identity, coefficient changes, differing print names, old/new ARR profile separation, unsupported feature rejection, unchanged source hashes, no-clobber and no native process invocation.

## Acceptance boundary

- The S1/S2 calculation capability exists in merged code, but whole-ordinate RORB numerical equivalence remains unaccepted. Python-Python identity is not CMD/GUI parity.
- Neither historic ARR nor ARR2026 data are generated here. Separate rainfall agent [PR #38](https://github.com/Chain-Frost/python-runoff-routing/pull/38) owns actual ARR Data Hub ingestion and eventual generation.
- TOML is entirely deferred per owner direction. No merge, release, licence, visibility or automation changes.
- Require exact final-head Windows Python 3.14 / Ruff 0.16.6 / strict Pyright / full public tests / out-of-tree installed-wheel validation before claiming this slice's software checks passed.

- Further S5 review: compare verified external asset content separately from portable relative path spelling; reject Windows reserved device names and trailing-dot/space components, with synthetic relocation and rejection tests. No numerical kernel, rainfall generator, reference evidence or tolerance modification.
