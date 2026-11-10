# S1: source-aware CMD parameter and cached output inspection

- **Issue:** [#3](https://github.com/Chain-Frost/python-runoff-routing/issues/3); depends on unaccepted [S0 #2](https://github.com/Chain-Frost/python-runoff-routing/issues/2).
- **Branch:** `feat/s1-cmd-inspection-ci`, stacked on `feat/s0-reference-capture` (PR #12).
- **Owner:** Unassigned; implementation prepared in this session.
- **Scope:** Typed single-burst CMD V2 `.par` subset, retained one-table `.out`, JSON inspect command, native-free synthetic tests and approved lightweight Windows/Python 3.14 CI.
- **Validation:** 30 focused S1 synthetic cases passed locally under Linux/Python 3.13.5. The [Windows/Python 3.14.10 quality run](https://github.com/Chain-Frost/python-runoff-routing/actions/runs/42742462277) passed at combined source head `af5240ccc0d294923fa9cedaf5d4640e5e2430af`: repository hygiene, Ruff 0.16.6 lint/format, strict Pyright (0 errors), **60/60 synthetic tests** (30 S1), wheel build and installed-wheel import outside checkout with `py.typed`. No native executables or approved RORB example/source corpus were exercised; this is not parsing completeness or hydrological parity evidence.
- **Known gaps:** `.cat`, `.catg`, `.dat`, `.stm` fail closed as unsupported; GUI `.par` and CMD multi-burst are unsupported; retained output `partial` is not a verified print-site mapping or solver result.
- **Next action:** Obtain permission-cleared `.cat`, `.catg`, `.dat`, and `.stm` examples and implement source-aware grammar records without reordering control instructions; independently verify retained output/location mappings against native evidence.

The optional CI is owner-authorised for this now-public repository. It cannot access private RORB executables/reference data and is not a numerical acceptance gate. No auto-merge, PyPI, benchmark or release is configured.
