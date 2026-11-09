# Private bootstrap

| Field | Value |
| --- | --- |
| Status | Needs review |
| Owner | Unassigned |
| Created / updated | 2026-11-09 |
| Next review | 2026-11-16 |
| Baseline | main at d5d6b51e80d98cae96d0cef6754989369d3923fc; repository initially empty/private |
| Delivery branch | plan/staged-implementation |
| Tracking | Issues #1-#10; planning/scaffold PR is the delivery record |

## Current state

Staged scope and acceptance contracts, GUI/CMD differences, local tooling configuration, package namespace, data safety and handoff are prepared. No parser, solver, reference runner, sampled events or hydrological regressions exist yet. Do not mark S0 complete from scaffold checks.

## Validation and limitations

The editing environment provides Linux/Python 3.13.5, not target Windows/Python 3.14. Native RORB programs were not run. Ruff, Pyright and build tools are unavailable here; a Python 3.14 download attempt failed due to network/DNS restrictions. The delivery PR records the actual portable hygiene/scaffold/syntax checks. Full target local checks, package build/installed-wheel acceptance and binary fingerprint/reference capture remain required.

No hosted workflows or publication are configured. Repository-level Actions disabling remains an owner/admin step, not a completed settings change. Raw supplied binaries/manuals/sample archive are not committed. No merge, release or visibility change is authorised.

## Next action

Review this scaffold and run its local checks on Windows/Python 3.14, then execute the [S0/S1 handoff](S0-S1-HANDOFF.md). Preserve the distinction between implementation, reference-engine characterisation and numerical acceptance. Record exact-head results in the PR; do not add a source-only commit just to restate a successful check.
