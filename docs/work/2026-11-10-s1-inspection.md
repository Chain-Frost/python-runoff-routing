# S1: source-aware CMD parameter and cached output inspection

- **Issue:** [#3](https://github.com/Chain-Frost/python-runoff-routing/issues/3); depends on unaccepted [S0 #2](https://github.com/Chain-Frost/python-runoff-routing/issues/2).
- **Branch:** `feat/s1-cmd-inspection-ci`, stacked on `feat/s0-reference-capture` (PR #12).
- **Owner:** Unassigned; implementation prepared in this session.
- **Scope:** Typed single-burst CMD V2 `.par` subset, retained one-table `.out`, JSON inspect command, native-free synthetic tests and approved lightweight Windows/Python 3.14 CI.
- **Validation:** 30 focused S1 synthetic cases passed locally under Linux/Python 3.13.5. Exact PR-head hosted results to be recorded after run. No native binaries or approved source examples exercised. Ruff/Pyright/Python 3.14 and installed-wheel acceptance are pending until demonstrated.
- **Known gaps:** `.cat`, `.catg`, `.dat`, `.stm` fail closed as unsupported; GUI `.par` and CMD multi-burst are unsupported; retained output `partial` is not a verified print-site mapping or solver result.
- **Next action:** Verify the Windows CI job, then inspect approved sample catchment/storm grammar and expand the S1 records without reordering native control instructions.

The optional CI is owner-authorised for this now-public repository. It cannot access private RORB executables/reference data and is not a numerical acceptance gate. No auto-merge, PyPI, benchmark or release is configured.
