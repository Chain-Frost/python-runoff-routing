# PyRORB quickstart

These commands apply to the public repository and need no private workspace. Python 3.13 **or** 3.14 on Linux **or** Windows is sufficient for pure-Python checks; use the interpreter's actual `python`, `py -3.13` or `py -3.14` command as appropriate. Only native RORB/Windows-specific integration needs a Windows host.

**Current delivery:** CLI/text-file MVP [#119](https://github.com/Chain-Frost/pyrorb/issues/119) / [merged #128](https://github.com/Chain-Frost/pyrorb/pull/128) is completed, including direct CLI acceptance of five original CMD cases / **1,805 ordinates**. [#136](https://github.com/Chain-Frost/pyrorb/pull/136) now adds bounded ARR2019/BoM deterministic design-ensemble software. `python-cmd/cmd-6.44` is the temporary new-project default, independent `python/engineering-v1` the explicit future intended default. The import/edit/export/reader scopes #138–#143, reporting #155 and explicit written-depth preparation #175/#177 are also delivered. Full CMD-native #5 and original rainfall/routed qualification #8 remain open; bounded #137 is complete. See [current status](STATUS.md). No GUI work.

## 1. Installation and quality

Run these commands from a checkout of [Chain-Frost/pyrorb](https://github.com/Chain-Frost/pyrorb). The distribution is named `pyrorb`; imports and module commands continue to use `runoff_routing`. [preliminary v26.11.24.1](https://github.com/Chain-Frost/pyrorb/releases/tag/v26.11.24.1) is published; these remain checkout-installation instructions. The preliminary distribution is not final MVP or scientific acceptance. See the [naming policy](NAMING.md).

```sh
python -m pip install -r requirements-catg.txt -e ".[dev]"
python repo-scripts/check_local.py
```

The package includes the canonical RORB reader directly; no ryan-tools or separate reader distribution is required. Edited CATG writing uses the separately installed pinned PyRomb PR; see [CATG authoring](RORB_GE_AUTHORING.md). A core checkout install (`python -m pip install -e .`) does not install the writer. The local checker runs repository/link hygiene, pinned Ruff lint and formatting, strict Pyright and non-native/non-benchmark pytest. It does not launch CMD, require private data or perform a numerical acceptance campaign. [Development details](DEVELOPMENT.md).

## Export a printed RORB rainfall boundary for TUFLOW

Use [the rainfall export guide](TUFLOW_RAINFALL_EXPORT.md) to select gross or excess rainfall
and named subareas from one supported report and write a new metric STEPPED boundary data CSV.

```sh
python -m runoff_routing.tuflow_rainfall report.out rainfall.csv --kind gross --column Subarea_A_mm
```

This exports printed interval depths, not hydrograph discharge or unrounded storm inputs.

## 2. An explicit, single-storm Python calculation

From the checkout root, run this Python code; `examples/synthetic-run.json` is a **typed S1 RunModel**, not a schema-2 project file:

```python
from pathlib import Path
from runoff_routing.integration import read_run_json, run_model

run = read_run_json(Path("examples/synthetic-run.json").read_text(encoding="utf-8"))
report = run_model(run)  # direct S2 engineering API, not the schema-2 project default
print(report.to_csv())
```

This checks that an already-supplied supported DESIGN event can execute. It does not validate native parity, physical conservation or a general ARR storm generator.

## 3. JSON project and engine selection

For an existing supported [JSON project](PROJECT_JSON.md) (`project.json` below), use a *new* output filename:

```sh
python -m runoff_routing.project_json validate project.json
python -m runoff_routing.project_json run project.json result.json
python -m runoff_routing.project_json run project.json python-result.json --engine python --numerical-profile engineering-v1
python -m runoff_routing.project_json run project.json native-result.json --engine rorb-cmd --numerical-profile cmd-6.44 --native-config local-cmd.json
```

New schema-2 projects temporarily default to `python-cmd/cmd-6.44`; existing projects
keep their stored selection, and schema-1 projects preserve their historical
`python/engineering-v1` selection. The improved `python` engine is available
by explicit override and remains the intended future default. The merged bounded [CMD-compatible engine #79](https://github.com/Chain-Frost/pyrorb/pull/79) computes supported DESIGN events separately and returns `computed_unvalidated`, **not** native equivalence. Unsupported features fail closed. To create and execute a complete publicly reproducible CMD example:

```sh
python examples/create_cmd_project.py
python -m runoff_routing.project_json run cmd-example-project.json cmd-example-result.json
```

Use new result names; exclusive-create refuses overwrites. For **PAR-led import**, file overrides, source preservation, editable settings and relocation, see [PAR project workflow](PAR_PROJECTS.md). Native `rorb-cmd` still requires a separately installed hash-checked executable and original file-backed inputs. See [engine selection](ENGINES.md), [project import](PROJECT_JSON.md) and [single CMD feature matrix](CMD_FEATURE_MATRIX.md).

## 4. Delivered explicit-event batches and ARR design rainfall

From the checkout with the public package installed, [#119's completed workflow](PROJECT_BATCH_MVP.md) runs ordered selected-engine event files, and outputs no-overwrite JSON/CSV/text:

```sh
python examples/create_cmd_project.py
mkdir -p .local
python -m runoff_routing.project_batch cmd-example-project.json .local/mvp-results --events examples/mvp-events.json
python -m runoff_routing.project_batch cmd-example-project.json .local/eng-results --events examples/mvp-events.json --engine python --numerical-profile engineering-v1
```

With no override, the temporary default is `python-cmd/cmd-6.44`. Choose unused prefixes for each run. `examples/mvp-events-with-failure.json` is a deliberate failure-isolation/non-success aggregate example; it preserves the other event outcomes rather than aborting the batch.

The [merged #136 design workflow](ARR_DESIGN_BATCH.md) produces replayable explicit-event requests for the same #119 runner:

```sh
python -m runoff_routing.arr_design_batch examples/arr-design-config.json .local/arr-design
python -m runoff_routing.project_batch cmd-example-project.json .local/arr-replayed --events .local/arr-design.events.json --engine python-cmd
```

Its synthetic source CSVs are **not** real design rainfall. Six generated artifacts preserve original source/effective precipitation, ten-member event IDs, statuses and complete routing reports. The [actual 60-event #137 receipt](work/2026-11-15-issue137-actual-execution.md) demonstrates source/wheel execution, **not** accepted native-effective storm/routed parity; the later explicit written-depth profile #175/#177 resolves the reconstructed written-input difference while native internal precision/routed decisions remain under #8. Persisted deterministic summaries are delivered, and native representative/critical-duration rules remain tracked by [#152](https://github.com/Chain-Frost/pyrorb/issues/152). The separate [engineering explicit prepared-batch API](ENGINEERING_BATCHES.md) from completed #6/#99 remains available, but does not establish Monte Carlo or complete CMD physical acceptance.

## 5. Public cached regression and mathematical controls

The source-controlled register is `tests/fixtures/regression-v1/register.json`. Create `.local` first (ignored by Git), and use unused output names:

```sh
python -m runoff_routing.regression_dataset preflight tests/fixtures/regression-v1/register.json --set cmd-eligible --full-index --output .local/preflight.json
python -m runoff_routing.regression_dataset diagnose tests/fixtures/regression-v1/register.json --case H1-three-source-asymmetric --snapshot --output .local/one.json
python -m runoff_routing.regression_dataset compare tests/fixtures/regression-v1/register.json --set cmd-eligible --snapshot --output .local/cached.json
python -m runoff_routing.regression_dataset preflight tests/fixtures/regression-v1/register.json --set authored --engine python --output .local/analytic.json
python -m pytest tests/test_regression_dataset.py tests/test_regression_scalars.py tests/test_regression_public_native.py -q
```

The `--snapshot` path authenticates a historical candidate snapshot, *not* a fresh execution of `python` or `python-cmd`. The **all-case scalar cached comparison is intentionally non-success** because two all-zero peak times are unavailable; do not suppress its exit code or claim full success. Ordinary `--csv` submission of `computed_unvalidated` legacy output is deliberately rejected. All original hashes, clocks, horizons, status labels and frozen budgets must remain intact. Use [the maintained regression dataset contract](REGRESSION_DATASET.md) for full/subset/wheel commands and the expected status of each case.

## RORB_GE 6.52 graphical source profiling

For a **private** CATG that is not yet admitted, run the read-only, redacted
structural profiler to identify its graphical version, known section counts
and record shapes without copying or modifying the model:

```sh
python repo-scripts/rorb_inspect.py "path/to/catchment.catg" --ge-profile
```

A successful profile **does not** imply typed 6.52 import, executable
support or numerical equivalence. The default JSON excludes model names,
paths, coordinates, operands, raw lines and the source SHA. See
[the exact qualification boundary](GE_652_SOURCE_PROFILE.md).

## 6. Installed wheel and acceptance

```sh
python -m build --wheel
```

Verify the resulting wheel with an **out-of-tree installation and import** before claiming wheel behaviour; do not import from the source checkout by accident. The existing CI checks pure-Python software quality and isolated wheel use; it does not run native CMD. Report distinctly: parser/software conformance; cached reference comparison; freshly executed source and installed-wheel computation; CMD-native numerical equivalence; independent engineering accuracy/conservation/refinement; and batch performance. Do not promote one category to another. [Regression policy](REGRESSION.md).

## Native CMD interoperability acceptance (16 November 2026)

Merged #138–#141 support backed CMD PAR-led input selection, typed edits
and portable native CMD export. See [PAR projects](PAR_PROJECTS.md),
[native export](NATIVE_CMD_EXPORT.md) and
[S5 interoperability](S5_INTEROPERABILITY.md).

[Issue #143 genuine Windows RORB CMD 6.44 acceptance](work/2026-11-16-issue143-native-acceptance.md)
records 5/5 successful direct executions of relocated emitted PARs,
unchanged native input bytes and real verbosity 1/2/3 differences.
The merged, installed #142 canonical reader retained all 1,005
original native ordinates. [#142 PR #165](https://github.com/Chain-Frost/pyrorb/pull/165)
is merged and its bounded reader software acceptance is evidenced by the owner-authorised authentic 490-event 6.45 population; the historical distinct 420-event population remains unlocated.
The five reader states remain `partial`; physical site identities
and numerical equivalence are not accepted. Keep #5 open.

## Provisional Monte Carlo software (23 November 2026)

The owner-approved B/E/C Monte Carlo workflow is available on main as **provisional CLI/API/text software**, not as an accepted RORBwin Monte Carlo or design-flood-frequency calculation. It uses the existing `python-cmd/cmd-6.44` event solver for its defined pervious/one-ISA subset, source-backed persisted sample plans, explicit effective-event materialisation, checkpoint/resume, revised-plan reweighting and per-site weighted-frequency reporting. There is no silent engine substitution.

Follow the [versioned Monte Carlo method](MONTE_CARLO.md) and [complete CLI plan → prepare → validate → run → frequency → replay sequence](MONTE_CARLO_EXECUTION.md). Unknown rainfall tails, missed/failed samples, invalid sources and unsupported profiles remain visibly incomplete; there is no automatic full-design-flood AEP when probability support is partial. [Native rules and statistical convergence remain open under #9](https://github.com/Chain-Frost/pyrorb/issues/9). No publication or change to the normal routing defaults is implied.
