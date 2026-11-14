# S5-P0 — JSON-only project files

**Status:** initial source/model import and validation, not solver equivalence. [S5 issue #7](https://github.com/Chain-Frost/python-runoff-routing/issues/7), [JSON-only slice #35](https://github.com/Chain-Frost/python-runoff-routing/issues/35).

**Owner decision (11 November 2026): Ignore every TOML requirement for now.** TOML parsing, output, migrations and JSON/TOML equivalence are explicitly deferred until the rest of the project is working.

## Architecture and source identities

- Keep the immutable S1 `RunModel` as the sole calculation-domain model. Its existing versioned JSON remains unchanged.
- S5 adds a separate version-1 JSON *project manifest*. Its `model_source` is either a self-contained S1 run document (`embedded-run`) or SHA-256-pinned relative paths to original `.par`, `.catg` and `.stm` bytes (`rorb-files`).
- Both source modes validate into the same S1 RunModel. The explicit project paths are used, but embedded filenames inside the original `.par` are preserved and **never followed**. No graphical-to-computational reordering or source rewriting.
- The project selects an explicit `rainfall_profile`: `explicit`, `legacy-rorb`, or `arr-2026v1`. This records a method boundary, **not** proof of a historical/modern calculation or a default selection of rainfall guidance.
- External rainfall, temporal patterns, curves and reference evidence can be catalogued with an independent data-profile ID, relative path and hash. Original assets are read only for verification and are otherwise opaque to S5; the S6 rainfall workpack performs semantic processing. A single project may catalogue modern and legacy data for comparison, but does not silently combine them.

The JSON project version and the S1 model's JSON schema are deliberately independent. File and method provenance are also distinct from the as-yet-unaccepted numerical solver profile.

## Example JSON shape

This is a structural illustration. SHA-256 placeholders below **must be replaced** with actual 64-character lowercase hex digests. No rainfall values in this document are recommended defaults.

```json
{
  "format": "python-runoff-routing-project",
  "schema_version": 1,
  "project_id": "example-one",
  "rainfall_profile": "legacy-rorb",
  "model_source": {
    "kind": "rorb-files",
    "parameters": {"path": "inputs/reference.par", "sha256": "<actual sha256>"},
    "catchment": {"path": "inputs/catchment.catg", "sha256": "<actual sha256>"},
    "storm": {"path": "inputs/storm.stm", "sha256": "<actual sha256>"}
  },
  "external_assets": []
}
```

The alternative embedded source is a JSON object of the form `{"kind": "embedded-run", "run": <existing S1 RunModel JSON object>}`. The S1 document preserves exact unit strings, Decimal numeric strings, stable identities and computational order.

## Python API

```python
from pathlib import Path

from runoff_routing.project_json import (
    EmbeddedRun,
    Project,
    import_rorb_project,
    load_project,
    project_from_json,
    project_to_json,
    write_project,
)
from runoff_routing.rorb_model import RunModel

target = Path(r"C:\models\case\project.json")
project = import_rorb_project(
    target,
    identifier="case-one",
    rainfall_profile="legacy-rorb",
    parameters=target.parent / "reference.par",
    catchment=target.parent / "catchment.catg",
    storm=target.parent / "storm.stm",
)
write_project(target, project)  # exclusive create: never overwrite
loaded = load_project(target)
assert isinstance(loaded.run, RunModel)

# For a pre-existing S1 RunModel named 'run':
# write_project(target, Project("case-one", "explicit", EmbeddedRun(run)))
```

Windows-friendly direct CLI; no argparse dependency:

```powershell
py -3.14 -m runoff_routing.project_json validate "C:\models\case\project.json"
py -3.14 -m runoff_routing.project_json inspect "C:\models\case\project.json"
py -3.14 -m runoff_routing.project_json import-rorb case-one legacy-rorb "C:\models\case\reference.par" "C:\models\case\catchment.catg" "C:\models\case\storm.stm" "C:\models\case\project.json"
```

The validation output deliberately reports `structural_only` and `numerical_parity: not_assessed`; it never launches RORB or the Python solver.

## Security and path rules

File references use forward-slash project-relative paths even on Windows. The selected project directory itself can be local, mapped drive or UNC. Entries reject absolute/drive/UNC references, parent traversal, empty path components and unsafe separators. Readers deliberately resolve symlinks **solely to establish physical containment**, verify original SHA-256 and impose a 64 MiB first-slice file-size bound. Original path spelling and source bytes are retained. Exclusive-create writes never clobber a file.

## Unsupported and deferred

- Full text `.cat`, combined `.dat`, GUI `.par`, uncharacterised S1 dialects and additional external rainfall file parsing remain unsupported.
- The S5-P1 adapter now executes already supplied, supported DESIGN storms through the strict Python S2 reference. This computes unvalidated Python ordinates; it is not RORB native parity or modern ARR rainfall generation. Full native comparisons and an accepted numerical profile remain future work.
- Legacy ARR/RORB rainfall preparation and ARR Data Hub 2026v1 methods remain separate in S6 [#33](https://github.com/Chain-Frost/python-runoff-routing/issues/33). Neither climate adjustments nor rainfall bursts are generated by this S5 layer.

**Stage #7 stays open.** A passing JSON import/validation test does not establish historical RORB, modern ARR, S2, S3, ensemble or Monte Carlo equivalence.

## Project-to-project comparison and S1 export (no solver)

`compare_project_files(left: Path, right: Path)` loads and hash-validates both projects, then compares **the exact typed S1 RunModel**, **rainfall-method profile** and **external asset descriptors** independently. Different project IDs or source storage routes (embedded versus original RORB files) do not by themselves prevent equivalence.

`configuration_equal` requires all three comparisons to match, and the first 24 differing field paths are recorded deterministically. It is **not** native or routed-hydrograph parity. The result always records `numerical_parity: not_assessed`.

`export_run_json(project_path, destination)` writes the existing S1 schema-1 RunModel JSON after verifying project sources and returns the new file SHA-256. That interchange intentionally omits the original project manifest, file hashes, rainfall method and asset registry. Retain the source project file for full provenance.

CLI examples:

```powershell
py -3.14 -m runoff_routing.project_json compare "C:\models\historic\project.json" "C:\models\converted\project.json"
py -3.14 -m runoff_routing.project_json export-run "C:\models\historic\project.json" "C:\models\historic\run.json"
```

Exit codes for compare: **0** when the verified configurations match, **1** when both are valid but different, and **2** for invalid source or usage. No command launches RORB, invokes the S2 solver, adjusts rainfall or alters original legacy source bytes.

Historic and current ARR rainfall-method profiles deliberately compare as **different** even if the underlying nominal S1 storm model happens to be identical.

## S5-P1: Run and compare stored JSON projects using S1/S2

Only explicit or legacy-rorb projects with an already supplied S1-validated DESIGN storm may execute through the existing strict Python S2 integration API. Modern arr-2026v1 projects must fail closed until S6 generates a separately validated storm. Unprocessed rainfall, temporal-pattern and curve assets also reject; external reference-only assets remain metadata.

run_project(Path) verifies the project JSON and every referenced source byte before invoking the pre-existing pure Python solver. It returns full named print-location series, project/model/source SHA-256 hashes and status computed_unvalidated with native_parity_status not_assessed. All computed times are model elapsed, not the native RORB_CMD printed increment/time labels. No input files are modified.

compare_routed_projects(left,right) requires the same declared rainfall profile and separately compares S1 model identity, external asset descriptors, print-location identities and *exact* Python ordinates. There is no tolerance change, time shift or guess about a native HydNNN column.

```powershell
py -3.14 -m runoff_routing.project_json run "C:\models\case\project.json" "C:\models\case\python-result.json"
py -3.14 -m runoff_routing.project_json compare-runs "C:\models\historic\project.json" "C:\models\converted\project.json"
```

The run command writes one exclusive-create JSON report and returns 0 only when successful; a missing, unsupported, or existing destination returns 2. compare-runs returns 0 when both verified configurations and outputs match, 1 for valid differences and 2 for invalid/unsupported input. Existing compare is configuration-only and does not invoke the solver. Long-form model-elapsed CSV is available via ExecutedProject.to_csv().

Native CMD/GUI comparison requires separately verified engine hashes, raw reference data, explicit print-site mapping and the frozen S2 tolerance policy; none is automatically inferred from an equal Python result. S6 owns ARR2016/2026 source processing; TOML remains deferred.

## Portable source comparisons and Windows filenames

Project comparison checks source **identity and content** independently of its relative storage path. External assets are compared in declared order by ID, role, data profile and SHA-256. A renamed or relocated asset with identical verified bytes is still the same input; `external_asset_paths_equal` reports whether the storage paths also match. Different bytes, identifiers, roles, profiles or ordering remain configuration differences. Both projects independently verify all recorded source hashes before comparison.

Portable relative filenames are validated against Windows behaviour even when inspected on another operating system. Reserved device names (`CON`, `NUL`, `AUX`, `PRN`, `COM1`–`COM9`, `LPT1`–`LPT9` and their device-name variants) and components ending in a space or dot are rejected rather than being silently normalised. Unicode ordinary filenames remain supported; project roots themselves may be local, mapped or UNC.

This is a source/provenance safeguard, not a native RORB or rainfall-method parity claim.

## S5-P2 SHA-pinned CMD reference diagnostic

The [S5 native review contract](S5_RECORDED_NATIVE_REVIEW.md) documents the `review-native` CLI. An actual 201-row CMD replay verified source evidence but **failed frozen printed parity: 11/201 within budget, maximum 0.22707849 m³/s**. The native column mapping is caller-asserted; numerical acceptance remains `unassessed`.

## S5 multi-case offline diagnostics (numerical acceptance not implied)

The [source-pinned offline suite](S5_OFFLINE_REGRESSION.md) extends the merged single-project SHA-pinned CMD adapter rather than implementing another parser or solver. It classifies each declared case as `computed/pass`, `computed/fail`, `unsupported`, `incomplete`, or `invalid`, retaining original fingerprints, raw CMD increment/time labels, control order and separate physical versus native volume statistics. The `model_print_id` / `HydNNN` mapping remains **caller asserted**. A previous 201-row CMD diagnostic **failed** frozen numerical parity (11/201 within budget); software integration does not change that result or establish native acceptance. TOML is deferred.
