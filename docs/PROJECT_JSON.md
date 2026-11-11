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
    EmbeddedRun, Project, import_rorb_project, load_project,
    project_from_json, project_to_json, write_project,
)
from runoff_routing.rorb_model import RunModel

target = Path(r"C:\models\case\project.json")
project = import_rorb_project(
    target, identifier="case-one", rainfall_profile="legacy-rorb",
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
- This is not an S2 project runner: S5's future validate/import/run/compare CLI, migration policy and hydrograph agreement tests depend on an independently accepted S2 numerical profile.
- Legacy ARR/RORB rainfall preparation and ARR Data Hub 2026v1 methods remain separate in S6 [#33](https://github.com/Chain-Frost/python-runoff-routing/issues/33). Neither climate adjustments nor rainfall bursts are generated by this S5 layer.

**Stage #7 stays open.** A passing JSON import/validation test does not establish historical RORB, modern ARR, S2, S3, ensemble or Monte Carlo equivalence.
