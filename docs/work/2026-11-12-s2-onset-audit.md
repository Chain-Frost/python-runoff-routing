# S2 onset-relative numerical discrepancy diagnostic

**Date:** 2026-11-12. **State:** bounded pure-Python audit in draft; numerical compatibility not accepted. **Branch:** `feat/s2-onset-divergence-audit-20261112`.

## Scope and dependencies

The S1/S2 integration #23 has merged into `main` but stage issue #4 remains open. This slice reuses the existing `parity_metrics.assess_printed_parity`, with no change to the solver, source parsers, loss/hyetograph conversion, printed-precision budget, native time labels or evidence corpus. It is independent of outstanding nonlinear balance/peak-budget and volume-reporting PRs.

## Retained evidence review

Read-only examination of the 36 private retained CMD calculation-comparison CSVs (36/36 previously known to fail strict printing precision) found that **35 first fail at the first nonzero output sample**, and **one fails at the following sample**. The native result tokens, predictions and first mismatch rows were not copied to the public branch; the original private evidence and indexed hashes remain the source of truth. This onset-relative audit does **not** prove whether source timing, rainfall losses, routing, storage or legacy nonlinear convergence is the mechanism. The 15-case independent linear loss/source/outlet projection agreement and separate four linear profiles limit extrapolation, but do not establish nonlinear or multi-reach parity.

## Validation and limitations

Test with Windows/Python 3.14, Ruff 0.16.6, strict Pyright, all non-native pytest cases, wheel build and import outside checkout. Source-only synthetic tests cover first-sample/next/later disagreement, printed zeros, two explicit native clock axes, separate native/predicted onset, validated offline comparison rows and fail-closed malformed/duplicate inputs.

The `audit_offline_comparison` convenience wrapper consumes an **already verified** `OfflineComparison` record, not raw native files. It does not read source/compare files, infer native `HydNNN` identities, or classify unsupported/incomplete as passing. No private full-corpus installed-wheel replay against this new API, new native run, acceptance decision, merge, release or issue closure is claimed.

**Next:** review exact-head Windows results, then run a private read-only 36-case verification using this exact installed wheel and compare every first-mismatch index against the separately recorded private completion packet before making any computational attribution.
