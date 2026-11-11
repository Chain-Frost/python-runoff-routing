# Development guide

## Environment and layout

Windows / Python 3.14 is the target. Use the normal user installation; a virtual environment is not mandatory. Install `py -3.14 -m pip install -e ".[dev]"`. The bootstrap deliberately has no numerical, GIS, pandas, Excel or acceleration dependencies. Add only what a selected feature needs; retain exact environment versions in acceptance records. Ruff is pinned to 0.16.6 in both its configuration and the development dependency. Other development tools are initially unpinned; reproducible lock/constraint selection is an S0 follow-up, not an assumed environment guarantee.

Use src/runoff_routing for reusable code, tests for focused tests, repo-scripts for developer tools, docs for contracts and work records, and ignored .local for native/reference evidence. Add numerical submodules only when needed. Do not import ryan-tools as a dependency or copy its large workflow/dependency estate.

Inspired by ryan-tools: Python 3.14 typing, Ruff at 120 columns, strict Pyright, Windows acceptance, installed-wheel checks, safe mapped/UNC paths, coherent batch pushes, focused tests and one authoritative work record. Do not inherit automatic version bumps, bundled wheels, broad GIS dependencies, submodules, recurring audits or release-on-main automation.

## Ruff policy

[`ruff.toml`](../ruff.toml) is the single lint configuration. It adopts all 41 explicit rule families selected in the reviewed ryan-tools configuration, plus annotation checks (`ANN`): 42 families covering correctness, modern Python, imports, naming, security, exceptions, logging, complexity, paths, performance, NumPy/pandas and pytest. Python 3.14 and 120-column formatting are retained. Ruff 0.16.6 is required; upgrades must change the dependency and configuration together and review the resulting diagnostics.

This greenfield package does not inherit ryan-tools' legacy exceptions. Global ignores are limited to formatter overlap/line wrapping. Tests permit assertions and non-package discovery; developer entry points permit non-package discovery. Subprocess exemptions are confined to reviewed fixed-command call sites, with comments; the security family remains enabled elsewhere. Complexity is capped at 10. Broad exceptions, unused suppressions, old NumPy RNG APIs and parser code do not get automatic exemptions.

Lint and format checks are read-only. Preview rules and unsafe fixes are off; use deliberate, reviewed fixes rather than an automatic baseline rewrite. Tests protect the policy itself but are not substitutes for executing Ruff and Pyright. Missing tools or an unrun target environment must not be reported as a passing gate.

## Local checks

```powershell
py -3.14 repo-scripts/check_local.py
py -3.14 -m build
```

The first command runs repository hygiene, Ruff lint/format checks, strict Pyright, then non-native/non-benchmark tests. It stops on failure and does not install dependencies or launch reference programs. `check_local.cmd` is the double-click, pause-at-end equivalent. The source-only hygiene check can also run independently: `python repo-scripts/check_repository.py`.

The build command is a separate package milestone check. Install the wheel outside the repository, verify import location and exercise the selected public API there. Record source and wheel outcomes separately. Main has S0 capture and S1 restricted parser APIs but no accepted numerical solver; a build or parser check does not establish numerical validity.

Documentation changes require relative-link and factual-claim review. Numerical/parser changes require focused tests plus affected prior-stage regressions and native evidence where the contract changes. Linux checks are useful but never replace Windows/Python 3.14 acceptance. Report every missing tool, failed check and unexpected skip; do not downgrade the target interpreter to manufacture a pass.

Planning/scaffold and S0/S1 code have merged after recorded Windows quality and package checks. These do not close independent S0-S7 native, hydrological or numerical acceptance gates.

## CI policy for the public repository (owner-approved 2026-11-10)

The owner explicitly authorised adding helpful CI now that this repository is public. Only `.github/workflows/quality.yml` is allowed by the repository checker. Pull requests and pushes to main run a scoped **Windows/Python 3.14** check with read-only GitHub permissions and cancellation of superseded runs. It installs the lightweight dev extras, runs the unchanged local repository hygiene, pinned Ruff lint/format checks, strict Pyright and all non-native/non-benchmark pytest cases, builds a wheel, and imports that installed wheel from outside the checkout.

Do not execute RORB_CMD/RORBwin, use client fixtures, access private executables, run expensive benchmarks or publish packages on hosted runners. CI validates *software quality*, not native numerical equivalence or Windows permission-cleared reference execution. Native and historical acceptance must be recorded separately on an actual reference machine.

The workflow is intentionally one Windows lane and no release/dependency-update job. Cache pip dependencies and cancel stale PR runs to limit costs. Keep the workflow explicitly reviewed, without unapproved matrix expansion, automatic publication or runtime secrets. A CI green result does not close S0-S7.

## Git and data safety

Topic branches and reviewable PRs; never merge or publish without owner instruction. Preserve concurrent/unrelated work and re-read the target head before publishing a batch. Do not force-push. Keep versions unchanged unless a version change is selected; bootstrap version is 0.0.0.dev0.

Ignore generated directories rather than all .out/.dat/.csv files: these extensions can be legitimate regression inputs. Original approved RORB fixtures under tests/fixtures/rorb are byte-preserved. The hygiene checker enforces no reference executables/manual PDFs/wheels, private local folders, generated results or files over the 1 MB bootstrap review threshold. This is a guard, not a comprehensive secret scanner or a substitute for provenance review.

Use no-clobber defaults; no silent destructive cleans or baseline regeneration. Preserve Windows path spelling and resolve paths relative to their owning configuration. Kernels have no filesystem side effects or process-level logging setup.

## Work tracking and completion

[docs/work/README.md](work/README.md) indexes the live records. One record per active work front; stage issues hold detailed task scope. Record status, owner (Unassigned unless accepted), update/review date, branch/revision, exact validation, blockers and one concrete next action. Do not imply an agent is running in the background. Review dates are session-driven, not scheduled tasks.

Distinguish implemented, validated, committed, pushed, reviewed, merged and released. Link limitations rather than closing them implicitly. Before public release, review third-party/data rights and select a licence; no open-source licence or publication permission is assumed now.
