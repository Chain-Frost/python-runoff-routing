# S5-P2 — verified native CMD outputs for JSON projects

**Updated:** 2026-11-14. **Issues:** [#51](https://github.com/Chain-Frost/python-runoff-routing/issues/51), [#44](https://github.com/Chain-Frost/python-runoff-routing/issues/44), parent [#7](https://github.com/Chain-Frost/python-runoff-routing/issues/7). **Status:** diagnostic infrastructure merged via [PR #52](https://github.com/Chain-Frost/python-runoff-routing/pull/52) at `ad4d822`; authentic installed-wheel workflow passed, frozen numerical comparison failed. Numerical acceptance remains unassessed.

## Dependencies

- S5 JSON project files / Python reference execution [PR #47](https://github.com/Chain-Frost/python-runoff-routing/pull/47), merged at `0989ca5`.
- Typed native output review [PR #45](https://github.com/Chain-Frost/python-runoff-routing/pull/45) and S2 reporting audit [PR #40](https://github.com/Chain-Frost/python-runoff-routing/pull/40) are also merged. Reconcile S5-P2 against their canonical main implementations, without duplicating their modules.
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

Next: review the reconciled #52 against current main and rerun exact-head Windows quality. #47, #40 and #45 are merged; #36 has been closed as superseded. S2 and S6 remain separate; TOML deferred.

## Historical source-quality result

- **PASS on implementation head `9c36efe620470032baed33b08293e95851f4a24c`**: [Windows quality #43148310990](https://github.com/Chain-Frost/python-runoff-routing/actions/runs/43148310990), Python 3.14.10.
- Repository hygiene 104 files, zero errors; Ruff 0.16.6 lint/formatter clean; strict Pyright zero errors/warnings; **370 public synthetic tests passed**; wheel built and installed/imported outside the checkout.
- Tests include synthetic zero-based and CMD one-based output row conventions, SHA-verified input/output/manifest mismatch rejection, profile/effective-parameter mismatches, original time tokens and write-no-clobber.
- **Historical public-CI limitation:** the original private CMD five-subarea capture was subsequently replayed as detailed above, and numerical parity FAILED. The full 65-case S5 campaign and RORBwin remain NOT RUN. No additional native RORB launch.

## Reconciled branch, 14 November 2026

S5 #47, S2 volume #40 and integrated print review #45 are merged. PR #52 now takes current main as a merge parent and retains only its S5-specific native-review code, 1-based CMD report inspection correction, source tests and S5 documentation. The existing S2 volume and reporting implementations are not replaced. The retained real CMD replay remains a **failed numerical comparison**, not numerical acceptance. [Exact reconciled-head Windows quality #43486014124](https://github.com/Chain-Frost/python-runoff-routing/actions/runs/43486014124) **PASSED** at `f4d9ed0a3a53d03ecbdccc22d790fb50462e71c4`: 386 tests, Ruff 0.16.6 lint/format, strict Pyright 0 errors/warnings, and built/installed wheel outside checkout. The original private replay was on the previous exact wheel `91b8549`. The now-merged S2 parity_metrics module has additional nonlinear diagnostics and a refactor of its printed-precision helper; the source routing kernel is byte-identical. That exact wheel has now also been replayed privately, reproducing the same 11/201 failure with byte-identical full rows; see the 14 November exact-wheel replay record below.

## Exact reconciled-wheel private replay, 14 November 2026

- **Source revision:** PR #52 `86957d319011d311a92aab16a0f67dc3bfa22a60` (before any documentation-only update); Windows/Python 3.14.6; new isolated installed-wheel environment outside the repository; `PYTHONPATH` unset.
- **Wheel SHA-256:** `3c02285a0a960c0d69626cd7571867a4147bbc05b288b959ea106b9871921974`. All 23 installed Python module source hashes match the selected PR revision.
- **Retained reference:** RORB_CMD 6.44, original capture and installed executable identity unchanged before and after; no native launches. Effective kc=10, m=0.8, IL/CL=24/5, timestep 0.5 h, 200 calculation increments independently confirmed.
- **Source/raw labels PASS:** all 201 original increments 1–201 and original times 0.50–100.50 h verified with no shifting or evidence modification; `print_1` → `Hyd001` remains caller asserted.
- **Frozen printed-precision comparison FAIL:** **11/201** within budget; first failed sample index **11**, maximum absolute difference **0.22707848694007993 m³/s**. Native peak **190.247 m³/s** versus Python peak **190.2265449082759 m³/s**, both at index **24**.
- **Reproducibility:** full 201-row comparison CSV matches the previous 13 November replay byte-for-byte. Native inclusive sample-sum volume **5,160,288.6 m³** and physical trapezoidal volume **5,160,283.2 m³** remain separate statistics.
- **Preserved labels:** `source_verified_diagnostic`, `mapping_evidence=caller_asserted`, `numerical_acceptance=unassessed`. Workflow success does not convert the failed numeric parity result into stage acceptance.
- **Private provenance:** [`runoff-routing-investigations` commit `4e7b026`](https://github.com/Chain-Frost/runoff-routing-investigations/commit/4e7b026), `docs/work/2026-11-14-s5-p2-exact-replay.md` and local retained `evidence/s5-p2-20261114/`. Do not copy raw reference data into the public repository.
- **Still open:** full 65-case S5 campaign, independent print-site acceptance, RORBwin/GUI compatibility, S2 #4 and S5 #7. No source solver change, tolerance adjustment, RORB launch, merge, release or TOML work.

## Integration disposition, 14 November 2026

- [S5-P2 PR #52](https://github.com/Chain-Frost/python-runoff-routing/pull/52) was **squash-merged** into `main` as `ad4d822cfd5f978b609f9d2a2763d834a7b4f0d0` after source review. The merge contains the S5-specific CMD evidence adapter, 1-based native row handling, synthetic tests and documentation. No duplicate S2 reporting implementation, native engine launch or routing-kernel change was introduced.
- [Final premerge Windows CI #43491149798](https://github.com/Chain-Frost/python-runoff-routing/actions/runs/43491149798) passed **386** synthetic tests, Ruff 0.16.6, strict Pyright and installed-wheel smoke at `b8c24c8`. The private raw 201-row replay used the byte-identical code revision `86957d3`; **11/201** within frozen print budget, first failure 11, maximum error **0.22707848694007993 m³/s**.
- **Conclusion:** the native-evidence diagnostic workflow is integrated, but **S2 #4 and S5 #7 remain open**, and RORB_CMD numerical parity is not accepted. The native output column/site mapping remains caller asserted. No S6 rainfall integration or TOML functionality is implied.
