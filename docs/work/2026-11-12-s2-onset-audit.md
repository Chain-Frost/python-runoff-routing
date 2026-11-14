# S2 onset-relative numerical discrepancy diagnostic

**Date:** 2026-11-12. **Original state:** draft #46 at `e9605bc870351786c8c238d6a1957ea972ba60ea`; **2026-11-14 reconciliation:** additive source/tests carried unchanged onto a fresh integration branch from current `main` after the original branch became stale. Native numerical compatibility remains unaccepted.

## Scope and dependencies

The S1/S2 integration #23 has merged into `main` but stage issue #4 remains open. This slice reuses the existing `parity_metrics.assess_printed_parity`, with no change to the solver, source parsers, loss/hyetograph conversion, printed-precision budget, native time labels or evidence corpus. It is independent of outstanding nonlinear balance/peak-budget and volume-reporting PRs.

## Retained evidence review

Read-only examination of the 36 private retained CMD calculation-comparison CSVs (36/36 previously known to fail strict printing precision) found that **35 first fail at the first nonzero output sample**, and **one fails at the following sample**. The native result tokens, predictions and first mismatch rows were not copied to the public branch; the original private evidence and indexed hashes remain the source of truth. This onset-relative audit does **not** prove whether source timing, rainfall losses, routing, storage or legacy nonlinear convergence is the mechanism. The 15-case independent linear loss/source/outlet projection agreement and separate four linear profiles limit extrapolation, but do not establish nonlinear or multi-reach parity.

## Validation and limitations

Test with Windows/Python 3.14, Ruff 0.16.6, strict Pyright, all non-native pytest cases, wheel build and import outside checkout. Source-only synthetic tests cover first-sample/next/later disagreement, printed zeros, two explicit native clock axes, separate native/predicted onset, validated offline comparison rows and fail-closed malformed/duplicate inputs.

The `audit_offline_comparison` convenience wrapper consumes an **already verified** `OfflineComparison` record, not raw native files. It does not read source/compare files, infer native `HydNNN` identities, or classify unsupported/incomplete as passing. No private full-corpus installed-wheel replay against this new API, new native run, acceptance decision, merge, release or issue closure is claimed.

**Next:** review exact-head Windows results, then run a private read-only 36-case verification using this exact installed wheel and compare every first-mismatch index against the separately recorded private completion packet before making any computational attribution.

## Non-destructive successor integration (2026-11-14)

The new reconciliation branch copies the original `onset_diagnostics.py` and `test_onset_diagnostics.py` **byte-for-byte** from [#46](https://github.com/Chain-Frost/python-runoff-routing/pull/46) head `e9605bc870351786c8c238d6a1957ea972ba60ea`, without changing the old branch, existing native source data, or frozen parity policy. The original [#46 Windows quality run](https://github.com/Chain-Frost/python-runoff-routing/actions/runs/43127167387) passed, but this successor must independently pass its exact-head Windows/Python 3.14 Ruff/strict Pyright/public pytest/installed-wheel checks before merge. A historical 35/36 first-at-onset classification is separate private retrospective evidence, not a new native replay or causal attribution. No RORB CMD/RORBwin execution is performed by the successor.
