# S1/S2 reconciliation: native code-7 identity and offline source decoding

**Date:** 2026-11-11. **Status:** source-only integration follow-up, numerical parity unaccepted. **Parent:** integration [PR #23](https://github.com/Chain-Frost/python-runoff-routing/pull/23). Use an isolated topic branch; neither the original S1/S2 PR authors nor their branch heads were changed.

## Reconciliation decisions

1. **Code-7 source identity:** take the implementation and tests from [S1 PR #26](https://github.com/Chain-Frost/python-runoff-routing/pull/26), with its distinct inline `ControlStep.label` (graphical annotation) and physical `PrintLocation.label` (native output location), rather than flatten them into one field. The older [#25](https://github.com/Chain-Frost/python-runoff-routing/pull/25) serializer has a **verified native CMD 6.44** replay of the 201-row five-subarea reference (private investigations PR #8), but that evidence does **not** automatically establish byte-identical executable output or GUI compatibility for #26's annotation-preserving variant. Do not merge #25 and #26 independently.
2. **Offline legacy encoding:** keep the S1-owned `.catg`/`.stm` grammar from integration PR #23; do **not** restore an independent fixture parser. Reuse `SourceDocument.from_bytes` to classify UTF-8/BOM or CP1252 content before handing it to the narrow compatibility shim, after verifying the recorded source hashes. Add a CP1252 source/fingerprint and unchanged-byte regression.
3. **Integrated print behaviour:** the calculation/report API displays the **actual physical native location label**; the graphical annotation remains separate in the immutable typed model and survives schema-1 JSON and canonical parse/write/parse. Code 7 with an absent physical record fails closed.
4. **S2 parity remains open:** [S2 repair PR #21](https://github.com/Chain-Frost/python-runoff-routing/pull/21) previously reported 36 computed whole-catchment cases outside strict printed precision, 25 unreviewed, three expected failures and one incomplete reference. This source-only reconciliation does not rerun those private outcomes. The mathematical kernel and the original half-last-print-unit comparison policy are unchanged. The manual's finite nonlinear convergence allowance (private investigations PR #9) is an **explanation hypothesis**, not an accepted native routing profile.

## Verification gates

The parent integration PR #23 previously passed Windows/Python 3.14, Ruff 0.16.6, strict Pyright, 193 synthetic tests and an out-of-tree wheel import. S1 PR #26 also passed its own Windows quality checks. **Those are parent/independent checks, not checks on this combination**. Run exact-head Windows/Python 3.14 CI plus private opt-in corpus regression in an owner-authorised checkout. Do not launch RORB on hosted CI, copy private data publicly, merge, publish, or close S1/S2 stages.

Native accepted profile: corrected canonical file input under the exact PR #25 emitter, CMD 6.44 only. Full S1/S2 parity, wider legacy grammar and RORBwin graphical editor remain unaccepted.
