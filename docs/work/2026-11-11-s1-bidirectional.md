# S1 bidirectional typed RORB inputs — implementation handoff

- **Issue:** [#3](https://github.com/Chain-Frost/python-runoff-routing/issues/3). **Stack base:** [S1 PR #13](https://github.com/Chain-Frost/python-runoff-routing/pull/13); S0 [PR #12](https://github.com/Chain-Frost/python-runoff-routing/pull/12) is now merged. **Owner:** Unassigned.
- **Scope (2026-11-11):** Frozen, validated, dialect-independent `ParameterSet`, `CatchmentModel`, `StormModel` and `RunModel`. Conservative CMD-V2 `.par`, RORB_GE 002 `.catg` and explicit single-burst DESIGN `.stm` readers; original-byte mode, canonical writers, stable schema-1 JSON and explicit finite-float S2 payload. Source maps and graphical original metadata are preserved separately.
- **Merged revision:** PR #19 (`be8832e`), originally the `feat/s1-bidirectional-parser` stacked branch.
- **Public synthetic coverage:** canonical parse/write/parse, JSON/class interchange, typed validation, CRLF/BOM/encoding, labels and ordinals, Fortran-D decimals, negative/unknown controls, missing terminators, malformed counts, GUI/mixed/FIT unsupported, path and overwrite safeguards.
- **Private evidence:** No private fixtures committed. The opt-in `repo-scripts/check_private_parser_corpus.py` audits private FILE_INDEX hashes before/after and replays reviewed baseline, truncated storm and unknown control when the separate corpus is available. No native executable is launched.
- **Acceptable exclusions:** GUI `.par`, text `.cat`, mixed `.dat`, multi-burst, FIT, storage/diversion/impervious support, native acceptance of canonical empty RORB_GE drawing scaffold, numerical equivalence and all S2 integration are **open**.
- **Validation status:** Do not claim Windows/Python 3.14, lint/type/build/wheel, private-corpus or numerical acceptance until exact checks are observed and recorded for the PR head.
- **Next action:** Review exact-head Windows CI and run the opt-in private read-only corpus regression on an approved local checkout. Then expand grammar from evidence-backed manual samples, integrate an explicit S2 adapter and verify native compatibility separately. **Do not close issue #3.**

[Public API and capability matrix](../RORB_BIDIRECTIONAL.md) · [Original S1 inspection work](2026-11-10-s1-inspection.md) · [Compatibility contract](../COMPATIBILITY.md).

## Windows quality and private corpus audit (2026-11-11)

- Starting PR head: `abe49a86e344639303b36c6aff43f3322e86c567`. This batch removes a strict Pyright unnecessary cast after the preceding typed JSON changes.
- Windows Python 3.14.6: repository hygiene, Ruff 0.16.6 lint and formatting, strict Pyright (0 errors), and 94 non-native/non-benchmark tests passed with this checkout on `PYTHONPATH`.
- Build succeeded with setuptools 84.2.1. A separate temporary venv installed the built wheel; import resolved to its site-packages and the private audit passed there as well as from source.
- Read-only private corpus audit: 863 indexed files verified before and after; reviewed baseline, truncated storm, unknown control and JSON round trip passed. Corpus checkout revision `6528485`; no native engine was launched. This focused audit does not validate every corpus case or numerical equivalence.
- Hosted Windows status for this batch remains pending until the pushed revision completes. Native canonical-output acceptance and excluded dialects/features above remain open. Next: inspect exact-head hosted result and review S2 offline campaign independently.

## Cleanup merge status (2026-11-11)

PR #19 merged as `be8832e`. [Exact-head Windows run 43038398850](https://github.com/Chain-Frost/python-runoff-routing/actions/runs/43038398850) passed Python 3.14.10, Ruff 0.16.6, strict Pyright, **98 synthetic tests**, wheel build and out-of-checkout import. Earlier pending checks refer to historical heads. The code-7 serialization error observed in CMD 6.44 is fixed in merged PR #25; corrected canonical native acceptance **not yet run**. Next: replay the corrected .catg/.stm/.par and review raw engine echo, output records and effective inputs. Keep issue #3 open.
