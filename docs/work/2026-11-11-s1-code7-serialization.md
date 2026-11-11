# S1 native-verified code 7 physical print-location layout

**Date:** 2026-11-11. **Ownership:** S1 parser/writer, stacked on draft PR #19. Evidence: private [targeted S1/S2 investigation](https://github.com/Chain-Frost/runoff-routing-investigations/blob/audit/targeted-s1-s2-20261111/docs/work/2026-11-11-targeted-s1-s2.md).

## Failure

The native CMD 6.44 run of the previous S1 canonical .catg failed because the writer emitted `7, PRINT\n0`: RORB consumed the next physical record `0` as the print-location name. The S1 parser had independently treated the comma-delimited annotation as the name, concealing this defect in its own canonical round trips.

## Correction

- Code 7 now renders as `7`, then the actual print-location string on **its own physical line**, including an intentionally blank line for a blank name.
- The parser consumes the native physical location after code 7, records its line and original contents, and does not treat the inline explanatory annotation as the executable location name.
- An absent print-location record / terminating zero is rejected. Comment-prefixed character labels remain unsupported in this narrowly characterised reader rather than being silently discarded as comments.
- Synthetic original-byte, canonical parse/write/parse, physical location priority, blank-name, and missing-name checks cover the corrected contract.
- Existing RORB_GE input bytes and private captures remain unchanged. Initial native input failure remains a failure; **native re-execution of the corrected writer has not occurred**.

This does not establish that the empty graphical scaffold or other canonical records are accepted by RORB. No numerical solver, tolerances, corpus, native runner, CI workflow, merge or release is changed. Keep S1 issue #3 and its stage draft open.
