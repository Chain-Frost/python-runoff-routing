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
