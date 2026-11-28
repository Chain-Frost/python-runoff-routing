"""Versioned agent discovery references, never an alternate hydrological specification.

JSON Schemas are navigation aids for common inputs. Exact admissibility is
defined solely by the existing Python validators linked in every record.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal

REFERENCE_VERSION = 1
SchemaName = Literal["project", "events", "arr-design"]
ApiArea = Literal["model-editing", "interoperability", "execution", "rainfall", "reporting", "verification"]


@dataclass(frozen=True, slots=True)
class ApiEntry:
    """One allowlisted public Python API with its maintained user/test references."""

    entrypoint: str
    guide: str
    tests: str
    purpose: str
    qualification: str


API_AREAS: dict[ApiArea, tuple[ApiEntry, ...]] = {
    "model-editing": (
        ApiEntry(
            "runoff_routing.project_json.Project",
            "docs/PROJECT_JSON.md",
            "tests/test_project_json.py",
            "Construct a typed project from an embedded run or pinned RORB files.",
            "New projects default to python-cmd/cmd-6.44; construction is not numerical approval.",
        ),
        ApiEntry(
            "runoff_routing.project_json.write_project",
            "docs/PROJECT_JSON.md",
            "tests/test_project_json.py",
            "Create a new project JSON file using the authoritative exclusive-create writer.",
            "Python API only; MCP has no project-creation action. Existing files cannot be overwritten.",
        ),
        ApiEntry(
            "runoff_routing.project_json.load_project",
            "docs/PROJECT_JSON.md",
            "tests/test_project_json.py",
            "Validate an existing project, including pinned source hashes.",
            "Structural validation is not numerical approval.",
        ),
        ApiEntry(
            "runoff_routing.rorb_model.edit_run_model",
            "docs/TYPED_PROJECT_EDITING.md",
            "tests/test_typed_effective_model.py",
            "Build an independently checked immutable edited S1 run.",
            "Do not mutate original RORB source bytes.",
        ),
        ApiEntry(
            "runoff_routing.project_json.save_project_as",
            "docs/TYPED_PROJECT_EDITING.md",
            "tests/test_project_json.py",
            "Persist a new project and its provenance through the existing writer.",
            "Existing outputs and original sources remain protected.",
        ),
        ApiEntry(
            "runoff_routing.project_json.compare_project_files",
            "docs/PROJECT_JSON.md",
            "tests/test_project_json.py",
            "Compare effective and original project identity and source content.",
            "Identity comparison is diagnostic, not native equivalence.",
        ),
    ),
    "interoperability": (
        ApiEntry(
            "runoff_routing.tuflow_rainfall.export_tuflow_rainfall",
            "docs/TUFLOW_RAINFALL_EXPORT.md",
            "tests/test_tuflow_rainfall.py",
            "Convert selected printed RORB rainfall intervals to a metric TUFLOW boundary CSV.",
            "Python/CLI only; no TUFLOW execution or unrounded depth reconstruction.",
        ),
        ApiEntry(
            "runoff_routing.project_json.import_rorb_project",
            "docs/PAR_PROJECTS.md",
            "tests/test_par_project_import.py",
            "Stage a PAR-led project with byte-pinned CATG/STM sources.",
            "No source rewriting or executable invocation.",
        ),
        ApiEntry(
            "runoff_routing.native_export.export_cmd_package",
            "docs/NATIVE_CMD_EXPORT.md",
            "tests/test_native_export.py",
            "Export a separate, exclusive native CMD input package.",
            "Package portability does not establish routed numerical accuracy.",
        ),
        ApiEntry(
            "runoff_routing.rorb_ge_authoring.serialize_catg_with_drawing",
            "docs/RORB_GE_AUTHORING.md",
            "tests/test_rorb_ge_authoring.py",
            "Use the pinned PyRomb authoring bridge for edited graphical CATG.",
            "Optional dependency and fidelity checks apply; no second writer.",
        ),
        ApiEntry(
            "runoff_routing.rorb_inspect.inspect_file",
            "docs/S1-INSPECTION.md",
            "tests/test_rorb_inspection.py",
            "Read original RORB inputs with structured parsing diagnostics.",
            "A parsed file may still be unsupported for execution.",
        ),
    ),
    "execution": (
        ApiEntry(
            "runoff_routing.engine_execution.run_engine_project",
            "docs/ENGINES.md",
            "tests/test_engine_contract.py",
            "Dispatch one project through its selected engine without fallback.",
            "Computed results and native/scientific qualifications are separate.",
        ),
        ApiEntry(
            "runoff_routing.project_batch.load_event_request",
            "docs/PROJECT_BATCH_MVP.md",
            "tests/test_project_batch.py",
            "Read a versioned explicit-event request.",
            "Malformed event details can remain per-event failures.",
        ),
        ApiEntry(
            "runoff_routing.project_batch.run_project_events",
            "docs/PROJECT_BATCH_MVP.md",
            "tests/test_project_batch.py",
            "Route ordered explicit events, preserving all unsuccessful outcomes.",
            "No silent engine substitution; full reports use existing writers.",
        ),
    ),
    "rainfall": (
        ApiEntry(
            "runoff_routing.arr_design_batch.read_design_config",
            "docs/ARR_DESIGN_BATCH.md",
            "tests/test_arr_design_batch.py",
            "Validate strict ARR/BoM rainfall axes, sources and profiles.",
            "Published rainfall method and native rainfall parity differ.",
        ),
        ApiEntry(
            "runoff_routing.arr_design_batch.run_design_batch",
            "docs/ARR_DESIGN_BATCH.md",
            "tests/test_arr_design_batch.py",
            "Prepare and route a deterministic ten-pattern ensemble.",
            "Native representative/critical-duration rules remain unqualified.",
        ),
    ),
    "reporting": (
        ApiEntry(
            "runoff_routing.rorb_report_views.inspect_report",
            "docs/S5_INTEROPERABILITY.md",
            "tests/test_rorb_report_views.py",
            "Inspect a canonical native OUT/batch report via the existing reader.",
            "Do not infer physical-site identity from a column label.",
        ),
        ApiEntry(
            "runoff_routing.rorb_report_views.report_json",
            "docs/S5_INTEROPERABILITY.md",
            "tests/test_rorb_report_views.py",
            "Obtain bounded structured sections from an inspected report.",
            "Reporting fidelity is distinct from engine equivalence.",
        ),
        ApiEntry(
            "runoff_routing.arr_result_summary.read_deterministic_results",
            "docs/ARR_DETERMINISTIC_RESULTS.md",
            "tests/test_arr_result_summary.py",
            "Summarise a paired effective and routed design result population.",
            "Observed peak rank is not a qualified native representative rule.",
        ),
    ),
    "verification": (
        ApiEntry(
            "runoff_routing.regression_dataset.compare_fresh_cmd_case",
            "docs/REGRESSION_DATASET.md",
            "tests/test_regression_dataset.py",
            "Use the existing authenticated original-CMD comparator.",
            "Snapshot comparisons are not fresh execution or general accuracy.",
        ),
    ),
}

_FILE_REF: dict[str, object] = {
    "type": "object",
    "required": ["path", "sha256"],
    "additionalProperties": False,
    "properties": {
        "path": {"type": "string", "minLength": 1},
        "sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
    },
}
_ENGINE: dict[str, object] = {
    "type": "object",
    "required": ["id", "numerical_profile"],
    "additionalProperties": False,
    "properties": {
        "id": {"enum": ["python", "python-cmd", "rorb-cmd"]},
        "numerical_profile": {"type": "string", "minLength": 1},
    },
}

# Shallow JSON Schemas deliberately do not replace nested S1, source-identity,
# rainfall-method or per-event semantics in the named Python validators.
SCHEMAS: dict[SchemaName, dict[str, object]] = {
    "project": {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "urn:python-runoff-routing:mcp:project:v1",
        "title": "Versioned JSON project - structural discovery only",
        "type": "object",
        "required": ["format", "schema_version", "project_id", "rainfall_profile", "model_source", "external_assets"],
        "additionalProperties": False,
        "properties": {
            "format": {"const": "python-runoff-routing-project"},
            "schema_version": {"enum": [1, 2, 3]},
            "project_id": {"type": "string", "minLength": 1},
            "rainfall_profile": {"enum": ["explicit", "legacy-rorb", "arr-2026v1"]},
            "engine": _ENGINE,
            "model_source": {
                "oneOf": [
                    {
                        "type": "object",
                        "required": ["kind", "run"],
                        "additionalProperties": False,
                        "properties": {"kind": {"const": "embedded-run"}, "run": {"type": "object"}},
                    },
                    {
                        "type": "object",
                        "required": ["kind", "parameters", "catchment", "storm"],
                        "additionalProperties": False,
                        "properties": {
                            "kind": {"const": "rorb-files"},
                            "parameters": _FILE_REF,
                            "catchment": _FILE_REF,
                            "storm": _FILE_REF,
                        },
                    },
                ],
            },
            "external_assets": {"type": "array"},
            "source_bindings": {"type": "array"},
            "effective_run": {"type": ["object", "null"]},
        },
        "allOf": [
            {
                "if": {"properties": {"schema_version": {"const": 1}}, "required": ["schema_version"]},
                "then": {"not": {"anyOf": [{"required": ["engine"]}, {"required": ["source_bindings"]}]}},
            },
            {
                "if": {"properties": {"schema_version": {"const": 2}}, "required": ["schema_version"]},
                "then": {
                    "required": ["engine"],
                    "not": {"anyOf": [{"required": ["source_bindings"]}, {"required": ["effective_run"]}]},
                },
            },
            {
                "if": {"properties": {"schema_version": {"const": 3}}, "required": ["schema_version"]},
                "then": {"required": ["engine", "source_bindings", "effective_run"]},
            },
        ],
    },
    "events": {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "urn:python-runoff-routing:mcp:events:v1",
        "title": "Explicit event request - structural discovery only",
        "type": "object",
        "required": ["format", "schema_version", "events"],
        "additionalProperties": False,
        "properties": {
            "format": {"const": "python-runoff-routing-explicit-events"},
            "schema_version": {"const": 1},
            "events": {
                "type": "array",
                "minItems": 1,
                "items": {
                    "type": "object",
                    "required": ["event_id"],
                    "additionalProperties": False,
                    "properties": {
                        "event_id": {"type": "string", "pattern": "^[A-Za-z][A-Za-z0-9_.-]{0,127}$"},
                        "storm": {"type": "object"},
                        "losses": {"type": "object"},
                        "routing": {"type": "object"},
                    },
                },
            },
        },
    },
    "arr-design": {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "urn:python-runoff-routing:mcp:arr-design:v1",
        "title": "ARR2019/BoM design batch - structural discovery only",
        "type": "object",
        "required": [
            "format",
            "schema_version",
            "project",
            "bom_ifd",
            "temporal_patterns",
            "pattern_kind",
            "temporal_region",
            "arf_region",
            "catchment_area_km2",
            "durations_min",
            "aep_labels",
            "dry_tail_min",
            "engine",
            "numerical_profile",
            "loss",
        ],
        "additionalProperties": False,
        "properties": {
            "format": {"const": "python-runoff-routing-arr2019-design"},
            "schema_version": {"const": 1},
            "project": {"type": "string", "minLength": 1},
            "bom_ifd": {"type": "string", "minLength": 1},
            "temporal_patterns": {"type": "string", "minLength": 1},
            "pattern_kind": {"enum": ["point", "areal"]},
            "temporal_region": {"type": "string", "minLength": 1},
            "arf_region": {"type": "string", "minLength": 1},
            "catchment_area_km2": {"type": "string"},
            "durations_min": {"type": "array", "minItems": 1, "maxItems": 8, "items": {"type": "integer"}},
            "aep_labels": {"type": "array", "minItems": 1, "maxItems": 6, "items": {"type": "string"}},
            "dry_tail_min": {"type": "integer", "minimum": 0, "maximum": 10080},
            "engine": {"enum": ["python", "python-cmd", "rorb-cmd"]},
            "numerical_profile": {"type": "string"},
            "loss": {"type": "object"},
            "rainfall_preparation": {"enum": ["published_decimal", "published_arf_stm_2dp"]},
        },
    },
}

SCHEMA_AUTHORITIES: dict[SchemaName, str] = {
    "project": "runoff_routing.project_json.project_from_json / load_project",
    "events": "runoff_routing.project_batch.load_event_request and per-event execution validation",
    "arr-design": "runoff_routing.arr_design_batch.read_design_config",
}

EXAMPLES: dict[str, dict[str, object]] = {
    "project": {
        "source": "examples/create_cmd_project.py + examples/synthetic-run.json",
        "commands": [
            "python examples/create_cmd_project.py",
            "python -m runoff_routing.project_json validate cmd-example-project.json",
            "python -m runoff_routing.project_json run cmd-example-project.json .local/model-result.json",
        ],
        "notes": "Run the creation script from the checkout root; create .local first; filenames must not exist.",
    },
    "events": {
        "source": "examples/mvp-events.json",
        "document": {
            "format": "python-runoff-routing-explicit-events",
            "schema_version": 1,
            "events": [
                {"event_id": "base"},
                {"event_id": "wet", "storm": {"depths_mm": ["25.0"]}},
                {"event_id": "higher_loss", "losses": {"initial_loss_mm": "5", "continuing": "0.2"}},
            ],
        },
        "command": (
            "python -m runoff_routing.project_batch cmd-example-project.json "
            ".local/events --events examples/mvp-events.json"
        ),
    },
    "arr-design": {
        "source": "examples/arr-design-config.json",
        "document": {
            "format": "python-runoff-routing-arr2019-design",
            "schema_version": 1,
            "project": "../cmd-example-project.json",
            "bom_ifd": "arr-design-synthetic-ifd.csv",
            "temporal_patterns": "arr-design-synthetic-patterns.csv",
            "pattern_kind": "point",
            "temporal_region": "SyntheticPoint",
            "arf_region": "South-West Western Australia",
            "catchment_area_km2": "2",
            "durations_min": [60, 120],
            "aep_labels": ["1%", "2%"],
            "dry_tail_min": 120,
            "engine": "python-cmd",
            "numerical_profile": "cmd-6.44",
            "loss": {"mode": "project_il_cl"},
        },
        "command": "python -m runoff_routing.arr_design_batch examples/arr-design-config.json .local/arr-design",
        "notes": "Example IFD and temporal patterns are synthetic, not design rainfall evidence.",
    },
}


def schema_manifest() -> dict[str, object]:
    """Return illustrative schema definitions with their real parser authorities."""
    return {
        "reference_version": REFERENCE_VERSION,
        "validation_scope": "structural_discovery_only",
        "authoritative_validation": "Run the named existing Python parsers; these schemas are not acceptance gates.",
        "schemas": {
            name: {"schema": definition, "authoritative_parser": SCHEMA_AUTHORITIES[name]}
            for name, definition in SCHEMAS.items()
        },
    }


def example_manifest() -> dict[str, object]:
    """Return existing checked-in examples without creating a second generator."""
    return {"reference_version": REFERENCE_VERSION, "examples": EXAMPLES}


def api_manifest() -> dict[str, object]:
    """Return the current, explicitly maintained crosswalk of Python functions to references."""
    return {
        "reference_version": REFERENCE_VERSION,
        "validation_scope": "navigation_only",
        "areas": {name: [asdict(entry) for entry in operations] for name, operations in API_AREAS.items()},
    }
