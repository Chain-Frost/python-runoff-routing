# S0 local reference capture and comparison

This is **evidence infrastructure**, not an independent routing solver or proof of numerical parity. No RORB binaries, reference inputs, private absolute paths or third-party manuals belong in Git. Source: [issue #2](https://github.com/Chain-Frost/python-runoff-routing/issues/2), [compatibility contract](COMPATIBILITY.md) and [regression contract](REGRESSION.md).

## Runner reuse and explicit native execution

The limited one-ISA/one-burst CMD parameter rendering and isolated subprocess pattern are adapted from [ryan-tools PR #145 at f404642b](https://github.com/Chain-Frost/ryan-tools/blob/f404642bddf3b7bf8f5d71988cfa0d247d8a0e19/ryan-scripts/RORB-python/rorb_calibrate.py). Calibration ranking, observed hydrographs, plots, PyHMA, sweeps and concurrency are **not** imported. The reuse is code provenance, **not** native-run acceptance. The earlier native attempt was denied by Windows before the program started (WinError 5). The existing script's one-`.out`-in-cwd assumption remains unverified for actual supplied binaries.

Install locally, then use the editable command script (or import the module):

```powershell
py -3.14 -m pip install -e ".[dev]"
py -3.14 repo-scripts/rorb_reference.py cmd .local\specs\case.json
py -3.14 repo-scripts/rorb_reference.py cmd .local\specs\case.json --execute
py -3.14 repo-scripts/rorb_reference.py archive .local\specs\gui-case.json
py -3.14 repo-scripts/rorb_reference.py audit .local\rorb-reference\CASE\manifest.json
py -3.14 repo-scripts/rorb_reference.py compare .local\A\manifest.json .local\B\manifest.json --policy-id pre-reviewed-example --absolute 0 --relative 0
```

The default `cmd` invocation **only validates** the spec and local input availability and writes nothing. Only `--execute` launches RORB_CMD. `archive`, `audit` and `compare` never launch a binary. Source and runtime evidence live under the ignored `.local/rorb-reference` or another expressly selected local path, each case in a new exclusive directory. Never place `--output` in a shared source folder as an attempt at isolation.

The native CMD launcher stages *copies* of the original `.catg` and `.stm` inputs alongside a generated `reference.par`. Parameter paths refer to the **staged copies**. The supplied executable is fingerprinted but not redistributed/copied. Each run uses one process, an explicit timeout, `shell=False` (implicit), `cwd` set to that unique directory, and captured binary stdout/stderr. Raw `.out`, `.log` and other files found recursively beneath the case folder retain original bytes. The source inputs and staged inputs are checked for mutation after the process. The manifest records elapsed monotonic time, return code or launch/timeout diagnostic, fingerprints, environment, requested print IDs and effective settings. It also distinguishes `launch_failed`, `timeout`, `nonzero_exit`, `native_error`, `missing_output`, `incomplete_output`, `zero_runoff`, `success`, `input_mutated` and `captured_unverified`.

**Isolation limitation:** Native RORB may contain absolute/indirect file references or write outside cwd. Staging plus recursive case-folder inventory does not prove it cannot access or write an external path. Do not run against originals that grant write access to production/project directories. Before native acceptance, inspect the real process's output locations, native logs and any external references with a permission-cleared one-case test and independent before/after source-directory inventory. Output found *only* outside the capture folder is `missing_output` here, not silently imported. A completed table with the expected row count proves only a *syntactic* check, not hydrological correctness or a native engine identity.

## Example `case.json` (replace all synthetic values)

The executable and all file paths are local and interpreted relative to the spec file, except for explicitly absolute paths. Do not copy actual private paths into version control. An `observed_version` comes from a verified banner/about screen, **not** from the guide's “6.31” statement.

```json
{
  "schema_version": 1,
  "case_id": "basinA_TP01",
  "engine_kind": "RORB_CMD",
  "executable": "RORB_CMD.exe",
  "observed_banner": null,
  "observed_version": null,
  "documentation_version": "guide mentions a 6.31 base; build unverified",
  "catchment": "basin.catg",
  "storm": "TP01.stm",
  "parameters": {
    "kc": "15", "m": "0.8", "loss_model": 1,
    "initial_loss_mm": "20", "continuing": "2"
  },
  "timeout_seconds": 1800,
  "provenance": {"source": "operator-supplied reference data", "redistribution": "private / not permitted"},
  "generator": {"name": "external ensemble exporter", "revision": null, "event_to_file": "basinA_TP01"},
  "effective_settings": {
    "timestep_hours": null, "horizon": null,
    "isa_mapping": [1], "burst_mapping": [1],
    "calculation_order": null
  },
  "requested_print_locations": {"Hyd001": "verified catchment outlet; specify computational ID"},
  "expected_steps": null
}
```

The null fields are deliberate placeholders requiring **actual observed evidence** before acceptance. No numerical output or version is inferred from this example. `loss_model=1` means IL/continuing loss in mm/h; `loss_model=2` means IL/runoff coefficient. They are separate **physical models**, not alternative encodings of the same values. The initial writer supports a *single lumped kc/m, a single ISA, a single rainfall burst and a .catg/.stm pair only*. Other combinations must use a separately characterised reference workflow; do not silently export them through this writer. An `expected_steps` value is required to classify a table as complete; if unknown, the top-level outcome is `captured_unverified`.

## GUI and externally executed CMD evidence

For offline GUI archiving, use the same common fields as above with `engine_kind: "RORBwin"`, its **distinct** executable identity and an explicit `gui_effective_settings` dictionary. Replace automatic `catchment`/`storm`/`parameters` keys with `inputs` and `outputs` maps of safe evidence file IDs to local paths:

```json
{
  "inputs": {"catchment": "basin.catg", "storm": "TP01.stm", "gui_settings.par": "saved.par"},
  "outputs": {"gui_report.out": "report.out", "gui_report.log": "report.log"},
  "gui_effective_settings": {
    "kc": "observed value", "m": "observed value",
    "losses": "observed model and values", "burst_isa_assignments": "observed mapping",
    "timestep": "observed value", "horizon": "observed value",
    "requested_print_locations": "observed computational IDs"
  }
}
```

Those keys must be merged with the schema/common fields in the CMD example; they do not make a complete standalone JSON document. GUI `.par` files have a different dialect and are **not** passed to the CMD writer. The archive copies the user-collected raw bytes and marks `captured_unverified` because it has not validated how the GUI produced them. A manual reference execution/capture is not an automated GUI test.

## External ensemble-exporter contract

The friend's existing ensemble exporter is an **input producer**, not a dependency to replace. For each case it must supply or document: unique event/TP identity and original TP ID (not simply ordinal), original .catg/.cat/.dat + .stm + applicable .par, generator name/revision and event-to-file map, exactly selected kc/m and loss model/units, ISA and burst mapping, calculation time grid/horizon, stable computational print locations plus displayed labels, any GUI-effective overrides, retained original .out/.log and CSVs, executable hash and observed build where known, and redistribution approval. Keep original bytes, not only peak summaries. A missing item remains missing in the manifest; do not invent its value.

Archive manually collected GUI and CMD cases into **separate** engine profiles. Keep their expected hydrographs separate, even when using the same catchment and storm. The cached comparator rejects cross-engine fingerprints/kinds, effective-input mismatches, missing/corrupted evidence and ambiguous or incomplete tables; it never averages GUI/CMD outputs. A tolerance policy (ID and fixed absolute/relative/near-zero-floor limits) must be approved before comparing. S0 comparisons are retained-report comparisons only; no independent Python runoff model exists yet.

## Characterisation and native acceptance matrix

| Probe | Case design and required observation | State without the supplied native binaries |
| --- | --- | --- |
| Loss flag ambiguity | Run `loss_model=1` with a distinctive continuing loss in mm/h, then flag 2 with a physically meaningful runoff coefficient; compare .par echoes and routed volumes. Do **not** treat the example `2, 20, 2` as proof of a valid runoff coefficient. | Unverified; code supports both explicit flags but not their native meaning. |
| Raw timing labels | Retain exact native increment labels, timestep, starting time, horizon and text/CSV mapping before any timeshift. Confirm whether code-11 excess series uses a different offset. | Unverified; capture preserves raw .out/.csv. |
| Output placement/names | One permission-cleared CMD run with staged inputs; search case and original source directories, expected .out and native log names and nonzero/error text. Confirm zero-runoff output existence. | Unverified; mocked cwd run is not native validation. |
| Code-11 excess | Use explicit catchment print location code 11, distinguish rainfall excess from discharge and inspect all emitted columns, time axis and missing-output paths. | Unsupported by initial hydrograph checker; raw files retained for later S1 inspection. |
| Multiple interstation parameters | Use at least two distinct ISA kc/m and losses with different effective mappings; compare echoed parameters against GUI and CMD separately. | **Unsupported** by initial writer; no parameter-index mapping claim. |
| Banner/build | Fingerprint RORB_CMD.exe and RORBwin.exe **separately**, capture each observed banner/about screen and runtime environment. | Unverified; the manual's 6.31 note is not an observed version. |

## Acceptance / limitations

Run `py -3.14 repo-scripts/check_local.py`, `py -3.14 -m build`, installed-wheel import from outside the checkout, and explicit native Windows one-case probes on the **exact PR head**. Preserve logs, hashes and a native result inventory. Cached synthetic tests only validate the contract and failure classification. Do not claim native pass, exact numerical parity, completed S0, or publishing readiness from these synthetic tests. No hosted Actions workflows or package publication are part of S0.
