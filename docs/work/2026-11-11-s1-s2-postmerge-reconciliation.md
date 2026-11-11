# S1–S2 integration follow-up: print labels and S2 test evidence

**Date:** 2026-11-11. **State:** draft, source quality awaiting exact-head Windows CI; numerical parity not accepted. **Topic:** `feat/s1-s2-postmerge-reconcile-20261111`.

## Dependency and resolution

- Parent: [integration PR #23](https://github.com/Chain-Frost/python-runoff-routing/pull/23), selected head `26428d50a4522ce0c4646edf9f213a6084a82ec6` (review target). This parent has Windows/Python 3.14 CI success [#43041317100](https://github.com/Chain-Frost/python-runoff-routing/actions/runs/43041317100), 203 public tests and wheel import; this is **not** parity.
- S0 #12 and S1 #13/#19/#25/#26 have merged to main. Preserve #25's native physical code-7 record parsing. [Draft #28](https://github.com/Chain-Frost/python-runoff-routing/pull/28) targets an outdated integration parent; port only the unique distinction between inline graphical annotation and physical print location plus regression tests.
- S2 [#14](https://github.com/Chain-Frost/python-runoff-routing/pull/14) / [#18](https://github.com/Chain-Frost/python-runoff-routing/pull/18) remain independent draft histories. Source-only fixes from [#21](https://github.com/Chain-Frost/python-runoff-routing/pull/21) are already present in #23's S1-backed original-byte `.catg/.stm` adapters (UTF-8 BOM / CP1252 and annotated zero imperviousness). Retain a single grammar and unchanged `route_reach`. Port #21's six independent manufactured/equilibrium nonlinear checks and annotated nonzero failure.

## Behaviour and evidence

- `ControlStep.label`: optional inline graphical annotation. `PrintLocation.label`: native physical text on the line after code 7. Neither is inferred from a `HydNNN` column. Explicit typed model, canonical output and schema-1 JSON preserve both; reporting uses the physical location.
- Blank physical records are preserved, while physical `0` (the terminator) is always rejected. Original source bytes/sha/line mappings remain S1-owned. Fail closed for unknown constructs and do not introduce a second parser or a changed numerical profile.
- The independent CMD 6.44 five-subarea replay verified 201 ordinates against #25's **bare code-7** canonical output. Optional annotated code-7 emission in this follow-up has **not** been natively approved.
- The separately pinned earlier private 65-case S2 campaign reported 36 whole-catchment cases above the strict printed precision budget, 25 unreviewed, three expected native failures and one incomplete reference. This follow-up does **not** rerun, overwrite or accept these profiles.

## Verification and merge control

Run exact-head Windows Python 3.14 with Ruff 0.16.6, strict Pyright, complete public synthetic tests, built-wheel installed import outside checkout. Run the full private offline corpus **separately** on the final installed source wheel with frozen hashes; missing corpus is not a pass. No hosted native runs, raw evidence, S0 change, forced update, releases, merges or issue closure. S1 issue #3 and S2 issue #4 remain open.

**Next:** Review the child PR, validate exact head, then reconcile uniquely supported changes into #23 after review; rerun 65-case private comparator before any numerical acceptance.

## Source-quality result

At implementation/test commit `95bedce591dbf296bc4a909a6378d44adb2be472`, [Windows Python 3.14 quality run #43046717476](https://github.com/Chain-Frost/python-runoff-routing/actions/runs/43046717476) completed **successfully**: repository hygiene (76 files, 0 errors), Ruff 0.16.6 lint and formatting, strict Pyright 1.1.414 (0 errors/warnings), **213 public synthetic tests passed**, wheel build and independent outside-checkout installed-wheel import. This paragraph is a documentation-only revision; CI on its resulting exact head remains a separate check until confirmed.

Neither that run nor an installed-wheel import uses the private corpus or launches RORB. The previously published S2 65-case outcomes remain unaccepted as parity of this combined revision.

## Private-runner legacy decoder bridge (2026-11-11)

The owner's private offline script imports `decode_legacy_source(data: bytes) -> str` from the selected S2 #21 wheel (`947a9aa6e2f3e32aa098db42fd6d665eab10f202`). This entry point is absent in current post-merge integration child #32, although its file comparison now correctly uses S1's authoritative original-byte parsers. The older stacked #28 exposed the compatibility function but has been superseded by #32's two-label code-7 work.

This separate narrow stacked change restores **only the historical decoder entry point**, implemented through `SourceDocument.from_bytes` and its encoding classification. It does not reinstate the prior S2 legacy grammar or modify the current S1 byte-based comparator, solver, numerical tolerances, fixture bytes or published API model. New synthetic tests check UTF-8 BOM, Unicode UTF-8, CP1252, blank content, retained source identity, CRLF and rejection of invalid CP1252 bytes. The previous decoder's `UnicodeDecodeError` for invalid CP1252 bytes is now the S1 `RorbFormatError` (also a `ValueError`); valid input text is unchanged.

Source parent at preparation: #32 `52386df53e52c014c3ad1b80c5ce4331e111c9fc`. **Exact-head Windows/Python 3.14 quality and out-of-tree wheel checks are pending; private 65-case comparison at this combined revision is NOT RUN.** Select that new installed wheel only after hash-preserving, no-clobber private campaign validation. Preserve the frozen 36 computed failures, 25 unreviewed, three expected failures and one incomplete status unless independently re-evaluated; a passing source suite does not establish S2 parity. No new RORB launches or source golden changes.

## Full catalogue replay selection

The public `repo-scripts/s2_compare_corpus.py` previously selected only `RORB_CMD` by default. The private schema-1 catalogue is confirmed at **65 case IDs**: **36** successful CMD captures, **25** captured-unverified cases (15 CMD and 10 RORBwin), **3** native CMD errors and **1** CMD incomplete output. This source change selects all catalogue cases by default, retaining the existing `CASE_IDS` opt-in subset override, and rejects duplicate/missing identifiers rather than silently omitting cases. GUI/unverified/reference failures must be recorded as `unsupported` or `invalid` outcomes rather than counted as passing parity. The batch's `status="compared"` means *comparison executed*, not hydrological acceptance.

A full private Python installed-wheel replay still requires an owner-authorised local checkout containing original source data and `FILE_INDEX.json`; the public CI and this environment have no mounted private corpus. **No 65-case runtime results are claimed from this source change.** Use the existing script against the private path; redirect JSON to a private location, preserve original hashes, and keep raw results out of the public repository.
