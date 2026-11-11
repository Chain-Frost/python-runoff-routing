# S1 native-verified code 7 physical print-location layout

**Date:** 2026-11-11. **Ownership:** S1 parser/writer; merged PR #25 (`3575fb5`), after parent PR #19. Evidence: private [targeted S1/S2 investigation](https://github.com/Chain-Frost/runoff-routing-investigations/blob/audit/targeted-s1-s2-20261111/docs/work/2026-11-11-targeted-s1-s2.md).

## Failure

The native CMD 6.44 run of the previous S1 canonical .catg failed because the writer emitted `7, PRINT\n0`: RORB consumed the next physical record `0` as the print-location name. The S1 parser had independently treated the comma-delimited annotation as the name, concealing this defect in its own canonical round trips.

## Correction

- Code 7 now renders as `7`, then the actual print-location string on **its own physical line**, including an intentionally blank line for a blank name.
- The parser consumes the native physical location after code 7, records its line and original contents, and does not treat the inline explanatory annotation as the executable location name.
- An absent print-location record / terminating zero is rejected. Comment-prefixed character labels remain unsupported in this narrowly characterised reader rather than being silently discarded as comments.
- Synthetic original-byte, canonical parse/write/parse, physical location priority, blank-name, and missing-name checks cover the corrected contract.
- Existing RORB_GE input bytes and private captures remain unchanged. Initial native input failure remains a failure; **native re-execution of the corrected writer has not occurred**.

This does not establish that the empty graphical scaffold or other canonical records are accepted by RORB. No numerical solver, tolerances, corpus, native runner, CI workflow, merge or release is changed. Keep S1 issue #3 and its stage draft open.

## Exact-head validation and merge (2026-11-11)

PR #25 merged as `3575fb5`. [Windows run 43039001047](https://github.com/Chain-Frost/python-runoff-routing/actions/runs/43039001047) on its reconciled head passed Python 3.14.10, Ruff 0.16.6, strict Pyright, **101 synthetic tests**, wheel build and isolated wheel import. Corrected canonical files have **not** been submitted to the native CMD executable; the old native failure remains evidence. Next: perform one permission-cleared complete canonical replay on fingerprinted CMD 6.44 and inspect the effective inputs and output inventory. Issue #3 stays open.

## Subsequent one-case native replay — 2026-11-11

The above 'not yet rerun' statement was a historical snapshot and is **superseded for one case** by private [investigations PR #8](https://github.com/Chain-Frost/runoff-routing-investigations/pull/8): a staged RORB_CMD 6.44 run from the #25 corrected emitter matched **201** reference discharge ordinates, raw increment/time tokens and effective setting echoes. Private raw evidence remains outside this public repository. This does **not** validate #28's new, distinct inline graphical annotation versus physical print-location label bytes, other native/GUI profiles or S1 stage completion. **Next:** run one permission-cleared distinct-label code-7 case against the pinned CMD build and verify the echoed/output physical names; keep issue #3 open.
