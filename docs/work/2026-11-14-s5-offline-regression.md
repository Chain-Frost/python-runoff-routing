# S5 — multi-case offline native regression suite

**Updated:** 2026-11-14. **Owner:** S5 implementation branch. **Branch:** `feat/s5-offline-regression-suite-20261114` from main `e00e34d8`. **Status:** draft public work, not merged or accepted. **Review:** on the draft PR/Windows quality and private replay.

## Scope and dependency use

Extend S5 JSON project execution and S0/S1/S2 native diagnostics, without second parser/solver. A versioned multi-event source-pinned JSON suite classifies every declared case `computed/pass`, `computed/fail`, `unsupported`, `incomplete` or `invalid`. Source verification, Python computation, original printed parity and native acceptance are independent statuses.

S0 `verify_manifest` and exact native executable/manifest/output hashes, S1 typed model and native output inspector, S2 `run_model`, frozen printed-precision parity and independent native-inclusive versus physical-trapezoid volume audits remain authoritative. Call one computation per supported project, not one per print column. Retain control-vector order, raw CMD 1-based increment/time tokens, peak magnitude/index and full-horizon integrals; no phase shift, tolerance fitting, rainfall-excess invention or ARR generation. Print-point maps are **caller asserted**, not independently location verified.

The S1 output parser captures the original native `Volume,m³` string only for a unique single-column report; absence/ambiguity remains unavailable. A printed-volume consistency check is reporting evidence only, not a hydrological balance or solver-acceptance gate.

## Previous real-native evidence — unchanged

The separately verified five-subarea RORB_CMD capture used 201 authentic output ordinates. **11/201 match the frozen printed allowance**; first failure index **11**, maximum absolute error **0.22707848694007993 m³/s**. Windows/installed-wheel offline source checks passed in the earlier S5-P2 work, but numerical compatibility failed. Earlier private 65-case work recorded **36 computed numerical failures** and **29 unsupported/uncomputed profiles**. The current suite has **not** independently re-executed that 65-case campaign, and no private bytes were copied to the public repo.

## Quality evidence and outstanding gates

- Public tests: synthetic source/hash/timing, unsupported engine, ambiguity, incomplete reference, native volume and no-clobber cases included in branch; fresh exact-head Windows/Python 3.14, Ruff 0.16.6, strict Pyright, wheel and installed-wheel gates **not yet recorded** here.
- Private 65-case suite: **NOT RUN** against this branch/installed wheel in the present environment; requires isolated private Windows source access, explicitly asserted print mappings and original corpus hash/index audit.
- Native process launches: **NONE authorised or attempted** in this task. Original tolerances, goldens, ARR inputs, compatibility profiles and strict S2 backend unchanged.
- Native numerical acceptance: **unassessed**, while the known CMD failure remains **FAIL**. S2 [#4](https://github.com/Chain-Frost/python-runoff-routing/issues/4) and S5 [#7](https://github.com/Chain-Frost/python-runoff-routing/issues/7) stay open.

**Next action:** run existing Windows/Python 3.14 CI on the exact draft PR head; inspect all quality/wheel checks, correct scoped defects; then execute an offline-only private 65-case read-only replay under an installed wheel and publish **sanitised classifications only**.
