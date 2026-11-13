# S5-P2 — verified native CMD outputs for JSON projects

**Updated:** 2026-11-13. **Issues:** [#51](https://github.com/Chain-Frost/python-runoff-routing/issues/51), [#44](https://github.com/Chain-Frost/python-runoff-routing/issues/44), parent [#7](https://github.com/Chain-Frost/python-runoff-routing/issues/7). **Status:** draft; installed-wheel private workflow replay passed, frozen numerical comparison failed. Numerical acceptance unassessed.

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

## Private installed-wheel replay, 2026-11-13

Exact PR #52 revision `91b854901465136a6262cfe945daf9279b66920e` was built on Windows/Python 3.14.6
and installed into a separate environment. Import came from site-packages outside the checkout, with
PYTHONPATH unset. Wheel SHA-256: `11f895df54d12c6a60c51c88003d616b014c1e472f73cfab91818c0b1156db4c`.

The retained five-subarea CMD 6.44 corrected-canonical capture completed the S5 adapter review:
all source/capture hashes and the installed executable hash verified; independent raw report checks
confirmed kc=10, m=0.8, IL/CL=24/5, 0.5-hour timestep and 200 calculation increments. All capture files
were fingerprinted before and after and remained unchanged. No native program was launched.

All 201 ordinates were compared using the existing frozen budget. **Numerical comparison FAIL:**
11/201 within budget; first failure sample index 11; maximum absolute error 0.22707848694007993 m3/s.
Both peaks occur at sample index 24. Raw native increment labels 1..201 and time strings 0.50..100.50 h
remain unchanged and distinct from sample-index time. Native inclusive sum is 5,160,288.6 m3;
physical trapezoid is 5,160,283.2 m3. They remain separate statistics.

The diagnostic remains source_verified_diagnostic, mapping_evidence=caller_asserted and
numerical_acceptance=unassessed. The sole final code-7 print is explicitly mapped print_1 to Hyd001;
this is not an independent print-mapping acceptance. Private JSON, full row CSV and hash inventories
are retained in the private investigations branch audit/s5-p2-replay-20261113. No raw evidence is
included here. This supersedes only the historical NOT RUN statement for this single replay;
the 65-case campaign, GUI and full numerical gates remain open. No source code or tolerances changed.

Next: review #47, reconcile #40 mergeability, then review #45 and #52 while preserving the existing
reporting dependencies. Treat #36 as superseded. S2 discrepancy research and S6 remain separate;
further S5 functionality and TOML remain deferred.

## Historical source-quality result

- **PASS on implementation head `9c36efe620470032baed33b08293e95851f4a24c`**: [Windows quality #43148310990](https://github.com/Chain-Frost/python-runoff-routing/actions/runs/43148310990), Python 3.14.10.
- Repository hygiene 104 files, zero errors; Ruff 0.16.6 lint/formatter clean; strict Pyright zero errors/warnings; **370 public synthetic tests passed**; wheel built and installed/imported outside the checkout.
- Tests include synthetic zero-based and CMD one-based output row conventions, SHA-verified input/output/manifest mismatch rejection, profile/effective-parameter mismatches, original time tokens and write-no-clobber.
- **NOT RUN:** the original private CMD five-subarea capture using this adapter; the 65-case campaign; RORBwin native acceptance or any new RORB_CMD launch. Native numerical stage remains unassessed.
