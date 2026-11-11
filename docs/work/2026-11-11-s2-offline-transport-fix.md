# S2 offline RORB fixture-transport compatibility

**Date:** 2026-11-11. **Parent:** PR #18 at 53021ff (stacked on S2 PR #14). This narrow patch does **not** alter rainfall losses, reach routing or any tolerance.

The offline corpus's actual RORB_GE file uses `0, -99,No impervious areas in system` for the all-pervious flag. RORB Version 6 Manual Table 5-2 explicitly allows an optional comma and same-line annotation at that position. The previous S2 fixture reader treated the annotation as numeric. CMD sources also contain Windows-1252 text; the previous offline adapter unconditionally decoded UTF-8.

This change accepts only an annotated **zero** impervious flag and retains rejection of nonzero flags, trailing unknown records, and unsupported numerical controls. Verified source bytes and fingerprints remain intact. The narrow offline adapter decodes UTF-8/BOM then Windows-1252; S1's source-aware parser remains authoritative for future integration.

**Source-only supplementary verification:** Python 3.13.5, 53 tests passed including three added cases (annotated pervious, annotated nonpervious rejection, CP1252 complete synthetic comparison). No RORB run. Not run against all 65 private cases, Windows/Python 3.14, pinned Ruff, strict Pyright or installed wheel. No source branch takeover, merge or release. S2 issue #4 remains open.
