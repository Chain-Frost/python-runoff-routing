# S1 bidirectional typed RORB inputs — implementation handoff

- **Issue:** [#3](https://github.com/Chain-Frost/python-runoff-routing/issues/3). **Stack base:** [S1 PR #13](https://github.com/Chain-Frost/python-runoff-routing/pull/13); S0 [PR #12](https://github.com/Chain-Frost/python-runoff-routing/pull/12) is still a prerequisite. **Owner:** Unassigned.
- **Scope (2026-11-11):** Frozen, validated, dialect-independent `ParameterSet`, `CatchmentModel`, `StormModel` and `RunModel`. Conservative CMD-V2 `.par`, RORB_GE 002 `.catg` and explicit single-burst DESIGN `.stm` readers; original-byte mode, canonical writers, stable schema-1 JSON and explicit finite-float S2 payload. Source maps and graphical original metadata are preserved separately.
- **Branch:** `feat/s1-bidirectional-parser` (stacked draft PR; no changes to S1 PR #13 owner branch).
- **Public synthetic coverage:** canonical parse/write/parse, JSON/class interchange, typed validation, CRLF/BOM/encoding, labels and ordinals, Fortran-D decimals, negative/unknown controls, missing terminators, malformed counts, GUI/mixed/FIT unsupported, path and overwrite safeguards.
- **Private evidence:** No private fixtures committed. The opt-in `repo-scripts/check_private_parser_corpus.py` audits private FILE_INDEX hashes before/after and replays reviewed baseline, truncated storm and unknown control when the separate corpus is available. No native executable is launched.
- **Acceptable exclusions:** GUI `.par`, text `.cat`, mixed `.dat`, multi-burst, FIT, storage/diversion/impervious support, native acceptance of canonical empty RORB_GE drawing scaffold, numerical equivalence and all S2 integration are **open**.
- **Validation status:** Do not claim Windows/Python 3.14, lint/type/build/wheel, private-corpus or numerical acceptance until exact checks are observed and recorded for the PR head.
- **Next action:** Review exact-head Windows CI and run the opt-in private read-only corpus regression on an approved local checkout. Then expand grammar from evidence-backed manual samples, integrate an explicit S2 adapter and verify native compatibility separately. **Do not close issue #3.**

[Public API and capability matrix](../RORB_BIDIRECTIONAL.md) · [Original S1 inspection work](2026-11-10-s1-inspection.md) · [Compatibility contract](../COMPATIBILITY.md).
