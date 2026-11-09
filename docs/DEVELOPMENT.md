# Development guide

## Environment and layout

Windows / Python 3.14 is the target. Use the normal user installation; a virtual environment is not mandatory. Install `py -3.14 -m pip install -e ".[dev]"`. The bootstrap deliberately has no numerical, GIS, pandas, Excel or acceleration dependencies. Add only what a selected feature needs; retain exact environment versions in acceptance records. Development tools are initially unpinned; reproducible lock/constraint selection is an S0 follow-up, not an assumed environment guarantee.

Use src/runoff_routing for reusable code, tests for focused tests, repo-scripts for developer tools, docs for contracts and work records, and ignored .local for native/reference evidence. Add numerical submodules only when needed. Do not import ryan-tools as a dependency or copy its large workflow/dependency estate.

Inspired by ryan-tools: Python 3.14 typing, Ruff at 120 columns, strict Pyright, Windows acceptance, installed-wheel checks, safe mapped/UNC paths, coherent batch pushes, focused tests and one authoritative work record. Do not inherit automatic version bumps, bundled wheels, broad GIS dependencies, submodules, recurring audits or release-on-main automation.

## Local checks

```powershell
py -3.14 repo-scripts/check_local.py
py -3.14 -m build
```

The first command runs repository hygiene, Ruff lint/format checks, strict Pyright, then non-native/non-benchmark tests. It stops on failure and does not install dependencies or launch reference programs. `check_local.cmd` is the double-click, pause-at-end equivalent. The source-only hygiene check can also run independently: `python repo-scripts/check_repository.py`.

The build command is a separate package milestone check. Install the wheel outside the repository, verify import location and exercise the selected public API there. Record source and wheel outcomes separately. The current namespace contains no solver; a build or scaffold test does not establish numerical validity.

Documentation changes require relative-link and factual-claim review. Numerical/parser changes require focused tests plus affected prior-stage regressions and native evidence where the contract changes. Linux checks are useful but never replace Windows/Python 3.14 acceptance. Report every missing tool, failed check and unexpected skip; do not downgrade the target interpreter to manufacture a pass.

## CI policy during private development

No active files under .github/workflows. No scheduled/manual hosted workflows, dependency-update bots, release jobs or publication. The local hygiene check rejects workflow files; do not rely on draft PR status or skip-CI markers.

Private repositories may receive included GitHub Actions usage; additional usage can be billed. Disabling hosted CI is a cost-control choice, not a requirement of privacy. Repository-level Actions permissions are a separate setting. The bootstrap does not assert that this switch has been changed.

The owner can apply the stronger switch under Settings > Actions > General > Actions permissions > Disable actions > Save. Do not configure required hosted status checks while no workflow can supply them. The available connector does not expose an administration write action for this switch, so an owner/admin step remains.

Later CI requires explicit approval: start with inexpensive static checks, then focused Windows tests, batch pushes, dependency caching and scoped collection. Native executables/corpora and long benchmarks remain explicit local campaigns unless separately approved. Do not enable CI merely because the repository becomes public.

## Git and data safety

Topic branches and reviewable PRs; never merge or publish without owner instruction. Preserve concurrent/unrelated work and re-read the target head before publishing a batch. Do not force-push. Keep versions unchanged unless a version change is selected; bootstrap version is 0.0.0.dev0.

Ignore generated directories rather than all .out/.dat/.csv files: these extensions can be legitimate regression inputs. Original approved RORB fixtures under tests/fixtures/rorb are byte-preserved. The hygiene checker enforces no reference executables/manual PDFs/wheels, private local folders, generated results or files over the 1 MB bootstrap review threshold. This is a guard, not a comprehensive secret scanner or a substitute for provenance review.

Use no-clobber defaults; no silent destructive cleans or baseline regeneration. Preserve Windows path spelling and resolve paths relative to their owning configuration. Kernels have no filesystem side effects or process-level logging setup.

## Work tracking and completion

[docs/work/README.md](work/README.md) indexes the live records. One record per active work front; stage issues hold detailed task scope. Record status, owner (Unassigned unless accepted), update/review date, branch/revision, exact validation, blockers and one concrete next action. Do not imply an agent is running in the background. Review dates are session-driven, not scheduled tasks.

Distinguish implemented, validated, committed, pushed, reviewed, merged and released. Link limitations rather than closing them implicitly. Before public release, review third-party/data rights and select a licence; no open-source licence or publication permission is assumed now.
