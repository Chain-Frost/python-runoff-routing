# First implementation handoff: S0 and S1

Work in Chain-Frost/python-runoff-routing on a new topic branch after the planning scaffold is accepted. Read AGENTS.md, the development/compatibility/regression contracts and issues #2/#3. Do not start the numerical solver, Monte Carlo, ARR generator or graphical editor in this workpack.

## Deliver

1. Inventory the actual supplied/reference binaries and sample files locally. Record SHA-256, version/banner and provenance. Do not add executables, manuals or unapproved data to Git.
2. Agree a versioned capture manifest with the friend's ensemble workflow. Import its original inputs, outputs and effective settings rather than rebuilding that workflow unnecessarily.
3. Adapt the existing runner identified below into an explicit, local Windows CMD capture adapter with timeout, isolated outputs, complete output/log validation and immutable input hashes. GUI captures may be manually produced; retain their effective settings and version separately. Ordinary tests must not launch either binary.
4. Probe loss-model flags and the supplied example inconsistency, code-11 output, timestep labels, print identities and multi-ISA parameter indexing. Record unresolved GUI/CMD differences.
5. Implement source-aware readers for the S2 subset of .cat/.catg/.dat/.stm and CMD .par, plus retained .out results. Identify unsupported GUI .par/dialect/feature cases explicitly. Preserve exact computation order, source locations and area/gauge/ISA mappings.
6. Return typed models and deterministic inspect/validate diagnostics; no solver claims. Add synthetic grammar/error tests and approved reference fixtures. Do not silently rewrite originals or populate numerical expected outputs from the new implementation.

## Reuse existing ryan-tools work first

The user identified an existing runner. Use it as the starting point for S0 rather than writing another launcher from scratch. Copy/adapt selected code and tests with source provenance; do not cherry-pick the entire PR, add a ryan-tools runtime dependency, or wait for the source PR to merge. Reuse does not transfer native acceptance.

**Runner baseline inspected on 2026-11-09:** [ryan-tools PR #145](https://github.com/Chain-Frost/ryan-tools/pull/145), commit `f404642bddf3b7bf8f5d71988cfa0d247d8a0e19`:

- [rorb_calibrate.py](https://github.com/Chain-Frost/ryan-tools/blob/f404642bddf3b7bf8f5d71988cfa0d247d8a0e19/ryan-scripts/RORB-python/rorb_calibrate.py): `render_par`, subprocess handling in `run_one`, run directories, timeouts, failure records and bounded sweep controls.
- [Focused tests](https://github.com/Chain-Frost/ryan-tools/blob/f404642bddf3b7bf8f5d71988cfa0d247d8a0e19/tests/test_rorb_calibrate.py): useful parser, dry-run, failure and mocked-process cases; native execution is not proved by the mocked process.
- [Source acceptance record](https://github.com/Chain-Frost/ryan-tools/blob/f404642bddf3b7bf8f5d71988cfa0d247d8a0e19/docs/work/2026-10-21-rorb-calibration.md): synthetic/archived-output evidence exists, but the attempted real Windows launch was denied with WinError 5 before RORB started. Fresh native execution remains unaccepted.

Adaptation boundaries:

1. Separate execution/capture from calibration scoring. A reference DESIGN event needs no observed hydrograph, RMSE/NSE ranking, plots or PyHMA. Retain all requested calculated hydrographs and explicit location identities; never inherit a project-specific Hyd001/Hyd002 interpretation.
2. Keep the initial one-ISA, one-burst, lumped-kc scope explicit: `render_par` hard-codes those settings. Reject unsupported inputs rather than presenting this writer as a general RORB parameter-file implementation.
3. Verify native output placement before parallel execution. `run_one` currently references supplied input paths, sets a per-run working directory and expects exactly one `.out` there. Stage isolated input copies and verify every native write destination; changing cwd alone is not proof that original inputs/directories are protected.
4. Extend capture to executable/input/output hashes, effective settings, elapsed time, native logs and manifest outcomes. Inspect `.out` and native log diagnostics as well as return codes. Preserve partial process diagnostics on timeouts/failures and distinguish valid zero runoff from incomplete output. Retain original evidence bytes.
5. Start with one worker on permission-cleared inputs. Confirm the actual .par dialect, loss flags, output names/time axes and completeness before testing concurrency, network paths or broader captures. Keep GUI acceptance separate. Apply the existing regression contract to the adapted implementation, not just the source script.

**Related S1 reader candidate:** [ryan-tools PR #233](https://github.com/Chain-Frost/ryan-tools/pull/233), inspected metadata at commit `c5811226bd97343eda7002d5a89513f7b0c5b019`, describes source-preserving output/CSV and CMD V2 parameter readers. Inspect these before extending the calibration script's intentionally narrow `parse_hydrographs`. The PR retains a private 420-pair recheck after a printed-precision change; do not transfer historical pass counts as current acceptance. Catchment/storm readers and broader saved-GUI-settings semantics remain outside its declared scope. Do not bring its MCP or unrelated processing layers into this package.

This is a reuse plan only: no runner or reader source has been copied into python-runoff-routing by this documentation change, and no reference executable has been run.

## Acceptance report

Record the exact commit, Python/tool versions, OS, source and installed-wheel checks, collected/skipped/native case counts, engine hashes, input/output hashes and every unresolved limitation. Run local hygiene, Ruff, strict Pyright and focused tests. Native evidence must come from Windows; Linux passes do not replace it. Keep the PR unmerged and stages open until their gates are met.

## Stop boundary

Do not implement extra features merely to make a complicated sample pass. Classify unsupported features and retain them for S3. Do not change tolerances, expected outputs, GitHub Actions settings, release configuration or repository visibility without the applicable explicit approval. End with an updated work record and one concrete next action.
