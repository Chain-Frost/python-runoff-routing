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

## 2026-11-09 - existing runner reuse

The user identified a RORB_CMD runner in ryan-tools. Source inspection located PR #145 at `f404642bddf3b7bf8f5d71988cfa0d247d8a0e19`, including `rorb_calibrate.py`, its focused tests and native-acceptance record. The S0/S1 handoff now selects its parameter rendering and process-capture code as a copy/adapt baseline, not a validated dependency. It also records PR #233 as a candidate for the output/parameter-reader work.

Required changes remain explicit: remove the observation/scoring requirement from reference capture; retain the one-ISA/one-burst scope; verify native output placement and isolated input copies; add provenance manifests and complete failure/log evidence. The original runner's real Windows execution gate remains outstanding. No runner source, proprietary inputs or executables were copied, and no numerical stage is accepted.

This follow-up is documentation-only on the existing planning branch. The original two file snapshots were verified against their GitHub blob hashes before editing; changed-document relative links and diff whitespace were checked locally. No Python suite, native execution, benchmark or installed-wheel validation was performed for this follow-up. Earlier scaffold validation belongs to its recorded revision, not a new runtime acceptance result. The PR discussion records the published follow-up commit; no merge, release or automation change is part of this update.

Next implementation action: after scaffold acceptance, adapt the pinned runner and relevant tests under S0, validate one real isolated Windows run, and retain the friend's ensemble workflow as an independent evidence source.

## 2026-11-09 - strict Ruff policy and merge assessment

The user requested aggressive Ruff coverage matching ryan-tools. Added a single pinned `ruff.toml` with all 41 reviewed upstream rule families plus ANN, Python 3.14, 120 columns, a complexity ceiling of 10, and only formatter-related global exceptions. Test/entry-point exceptions and two reviewed subprocess call-site suppressions are narrowly scoped. Lint remains read-only; preview and unsafe fixes are disabled. The previous limited pyproject rule selection was removed and the development dependency pinned consistently.

Extracted Markdown-link checks to keep the repository checker below the complexity ceiling, resolved Git explicitly instead of passing a partial executable name, and added policy/link regression tests. Source snapshots were checked against GitHub blob IDs before editing. On Linux/Python 3.13.5, the selected snapshot's nine scaffold/policy/link tests and syntax compilation pass; these are supplementary checks, not execution of Ruff or target-platform acceptance. Changed-document links were checked against the known repository tree and diff whitespace reviewed.

Ruff, Pyright, Python 3.14 and build tooling are unavailable in this environment; package-index access fails due to DNS restrictions. Consequently Ruff lint/format, strict Pyright, Windows/Python 3.14, package build and installed-wheel smoke remain NOT RUN. No native program was executed. No automatic CI was enabled. PR #11 remains draft and unmerged; issue #1 is the roadmap, not a pull request.

Next action: run the documented local check suite and package/install smoke against the final PR head on Windows/Python 3.14. Resolve any findings before accepting the scaffold. Native RORB, solver and Monte Carlo evidence remain later-stage gates rather than blockers requiring implementation in this planning PR. Runner reuse from ryan-tools PR #145 and reader investigation from PR #233 remain in the handoff.
