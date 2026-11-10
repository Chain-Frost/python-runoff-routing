# Agent instructions

Read [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md), [docs/work/README.md](docs/work/README.md), the selected stage issue and [docs/COMPATIBILITY.md](docs/COMPATIBILITY.md) before changing code. The plan describes future scope, not implemented capabilities.

## Scope and delivery

- Work on one selected stage/slice. Preserve unrelated changes and concurrent work. Use a topic branch or isolated worktree.
- Commit and push a coherent locally checked batch; with GitHub APIs use one tree/commit and one branch update, not a commit per file.
- Re-read remote heads before publishing. Do not force-push, merge, release, publish, change visibility or enable hosted automation without explicit owner approval.
- The repository is public: keep private data, executables and unreviewed reference assets out of Git. Do not vendor RORB binaries or unreviewed reference data. Implement documented methods independently; do not decompile or modify supplied executables.
- Update the selected work record and issue with exact revision, scope, evidence, limitations and next action. Do not close a numerical stage merely because code was merged.

## Implementation

- Target Windows / Python 3.14. Use built-in generics, `X | None`, explicit public annotations, Ruff formatting (120 columns) and strict Pyright for first-party code.
- Apply the pinned, comprehensive policy in `ruff.toml`. Fix findings instead of weakening rule families. Any suppression must name the exact rule, use the narrowest scope and explain the behavioural reason. No blanket `noqa`, broad legacy exemptions or unattended unsafe fixes.
- Keep parsing, the typed domain model, numerical computation, event generation and reporting distinct. Avoid pass-through layers, generic plugin frameworks and unnecessary dependencies.
- Preserve imported computational order and stable source identities. Graphical layout is not a reason to reorder a model.
- Recognised input, supported execution and validated equivalence are separate states. Reject unsupported numerical behaviour explicitly.
- Pure kernels do not read files, draw randomness, configure logging, pause or terminate the process. Wrappers own process behaviour and editable settings.
- Preserve user path spelling; use `Path.absolute()` for ordinary paths. Resolve links only deliberately for physical identity/security, with tests. Never weaken overwrite or containment protections.

## Evidence and cost

- Follow [docs/REGRESSION.md](docs/REGRESSION.md). Keep GUI and CMD profiles/results separate; pin hashes and effective inputs. Never silently regenerate goldens or relax tolerances.
- Add focused executable tests for each parser or numerical behaviour. Run relevant prior-stage regressions. Documentation-only edits need link/claim checks, not unrelated simulation suites.
- Windows/Python 3.14 and installed-wheel evidence are acceptance gates. Linux checks are supplementary; report missing checks and unexpected skips honestly.
- Native runs, baseline updates and costly benchmarks are explicit opt-ins. Missing reference data is not a passing native test.
- The owner authorised one low-cost Windows/Python 3.14 quality workflow on 2026-11-10 after making the repository public. Keep `.github/workflows/quality.yml` limited to lint, type checks, synthetic tests and wheel import. No native engine execution, third-party/private fixtures, dependency-update bots, automatic releases or package uploads.
- Retain the readable reference backend when optimising. Validate acceleration dependencies before selection; no unmeasured speed claims or silent fast-math.
