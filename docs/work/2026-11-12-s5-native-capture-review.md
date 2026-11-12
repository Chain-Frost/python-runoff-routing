# S5-P2 — verified native CMD outputs for JSON projects

**Date:** 2026-11-12. **Issues:** [#51](https://github.com/Chain-Frost/python-runoff-routing/issues/51), [#44](https://github.com/Chain-Frost/python-runoff-routing/issues/44), parent [#7](https://github.com/Chain-Frost/python-runoff-routing/issues/7). **Status:** isolated draft; exact-head Windows quality acceptance pending. Numerical parity unassessed.

## Dependencies

- S5 JSON project files / Python reference execution [PR #47](https://github.com/Chain-Frost/python-runoff-routing/pull/47).
- Typed native output review [PR #45](https://github.com/Chain-Frost/python-runoff-routing/pull/45), based on separate S2 reported-volume audit [PR #40](https://github.com/Chain-Frost/python-runoff-routing/pull/40). Both dependency histories are retained in this candidate integration. **Do not merge in arbitrary order or duplicate files.**
- S0 verify_manifest, S1 source-aware output inspection and the existing S1/S2 computed RunResult remain authoritative. No new solver, custom native parsing algorithm or modified tolerance.

## Implemented slice

- Requires an original-file-backed `legacy-rorb` JSON project and a caller-pinned S0 manifest + executable SHA.
- Checks source .catg/.stm SHA match, complete success/zero-runoff, no diagnostics/provenance gaps, native version and effective kc/m/IL/CL/timestep/one-ISA/burst flags, full 1-based CMD output length and exact S0 raw time labels.
- Requires a caller-supplied mapping from the model print ID to the real native HydNNN column. Retains mapping_evidence caller_asserted rather than inferring identity.
- Passes exact unmodified native printed ordinate/time tokens to review_recorded_print. Returns sample-sum and horizon-volume candidates separately; always numerical_acceptance unassessed.
- S1 read-only inspector recognises real 1-based native output 1..N+1 as well as the previous 0..N convention, with synthetic regression tests and no source clock shifting.
- A read-only project-native review API and `review-native` CLI write an exclusive-create JSON diagnostic. All tests are synthetic; private native captures remain untouched.

## Exclusions

- Full native RORB numerical equivalence and private 65-case replay on this exact head are NOT RUN / NOT ACCEPTED.
- No RORBwin assumptions, new rainfall generation, new numerical kernel or post-hoc precision tolerance.
- TOML entirely deferred; no merge, release, hosted-automation modification or issue closure.
