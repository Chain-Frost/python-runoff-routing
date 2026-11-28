"""Agent-facing capability index, not a second CMD feature/acceptance matrix."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Exposure = Literal["mcp_tool", "python_or_cli", "staged", "planned"]


@dataclass(frozen=True, slots=True)
class Capability:
    """Locate an established API or an explicitly unavailable future function."""

    name: str
    exposure: Exposure
    category: str
    entrypoint: str | None
    cli: str | None
    docs: str
    description: str
    limitation: str
    tracking: str | None = None


CATALOG: tuple[Capability, ...] = (
    Capability(
        "list_capabilities",
        "mcp_tool",
        "discovery",
        "runoff_routing.mcp_server.list_capabilities",
        None,
        "docs/MCP.md",
        "List current, staged and planned agent-facing capabilities.",
        "Availability is not scientific verification.",
    ),
    Capability(
        "describe_capability",
        "mcp_tool",
        "discovery",
        "runoff_routing.mcp_server.describe_capability",
        None,
        "docs/MCP.md",
        "Show the documented function and its actual signature.",
        "Only catalogue entries may be introspected; no arbitrary imports.",
    ),
    Capability(
        "get_api_reference",
        "mcp_tool",
        "discovery",
        "runoff_routing.mcp_server.get_api_reference",
        None,
        "docs/MCP.md",
        "Find module-level Python APIs, live signatures, maintained guides and tests by area.",
        "Reference index is navigation only; source validators and feature matrix remain authoritative.",
    ),
    Capability(
        "get_engine_capabilities",
        "mcp_tool",
        "discovery",
        "runoff_routing.mcp_server.get_engine_capabilities",
        None,
        "docs/ENGINES.md",
        "Show the package's canonical three-engine declarations.",
        "Native numerical parity and physical accuracy remain separate.",
    ),
    Capability(
        "inspect_rorb_file",
        "mcp_tool",
        "inspection",
        "runoff_routing.rorb_inspect.inspect_file",
        "python repo-scripts/rorb_inspect.py",
        "docs/S1-INSPECTION.md",
        "Read-only inspection of PAR, CATG, STM and OUT source files.",
        "Parsed syntax is not execution or native equivalence.",
    ),
    Capability(
        "validate_project",
        "mcp_tool",
        "validation",
        "runoff_routing.project_json.load_project",
        "python -m runoff_routing.project_json validate PROJECT.json",
        "docs/PROJECT_JSON.md",
        "Structural project validation with pinned external-file hashes.",
        "Never executes an engine.",
    ),
    Capability(
        "inspect_event_request",
        "mcp_tool",
        "validation",
        "runoff_routing.project_batch.load_event_request",
        None,
        "docs/PROJECT_BATCH_MVP.md",
        "Check a versioned explicit-event request envelope.",
        "Per-event feature validation happens at execution.",
    ),
    Capability(
        "summarize_arr_results",
        "mcp_tool",
        "reporting",
        "runoff_routing.arr_result_summary.read_deterministic_results",
        "python -m runoff_routing.arr_result_summary",
        "docs/ARR_DETERMINISTIC_RESULTS.md",
        "Read-only persisted ARR result population summary.",
        "Observed peak ranks are not native representative selections.",
    ),
    Capability(
        "get_result_summary",
        "mcp_tool",
        "reporting",
        "runoff_routing.mcp_results.summarize_result_file",
        None,
        "docs/MCP.md",
        "Read bounded metadata from existing single, batch and ARR JSON result contracts.",
        "Structural projection only; full hydrographs remain in the saved files.",
    ),
    Capability(
        "run_project",
        "mcp_tool",
        "execution",
        "runoff_routing.engine_execution.run_engine_project",
        "python -m runoff_routing.project_json run",
        "docs/PROJECT_JSON.md",
        "Run a single stored project event and persist a new JSON result.",
        "Requires allow_write=true; Python engines only and no overwrite or native parity claim.",
    ),
    Capability(
        "run_project_events",
        "mcp_tool",
        "execution",
        "runoff_routing.project_batch.run_project_events",
        "python -m runoff_routing.project_batch",
        "docs/PROJECT_BATCH_MVP.md",
        "Run explicit-event batches through the existing selected-engine dispatcher.",
        "Requires allow_write=true and new outputs; computed_unvalidated is not native parity.",
    ),
    Capability(
        "prepare_arr_design",
        "mcp_tool",
        "rainfall",
        "runoff_routing.arr_design_batch.run_design_batch",
        "python -m runoff_routing.arr_design_batch",
        "docs/ARR_DESIGN_BATCH.md",
        "Prepare deterministic ARR/BoM rainfall and event requests.",
        "Requires allow_write=true; generates and routes ten TPs/cell, but native parity remains unassessed.",
    ),
    Capability(
        "export_tuflow_rainfall",
        "python_or_cli",
        "interoperability",
        "runoff_routing.tuflow_rainfall.export_tuflow_rainfall",
        "python -m runoff_routing.tuflow_rainfall",
        "docs/TUFLOW_RAINFALL_EXPORT.md",
        "Export selected printed gross or excess interval depths as a metric rainfall boundary CSV.",
        "Explicit selection and new file only; printed precision and native TUFLOW verification limits apply.",
    ),
    Capability(
        "export_cmd_package",
        "python_or_cli",
        "interoperability",
        "runoff_routing.native_export.export_cmd_package",
        "python -m runoff_routing.native_export",
        "docs/NATIVE_CMD_EXPORT.md",
        "Export portable native CMD inputs with existing file safeguards.",
        "A successful export is not evidence of native numerical parity.",
    ),
    Capability(
        "regression_diagnostics",
        "python_or_cli",
        "verification",
        "runoff_routing.regression_dataset.compare_fresh_cmd_case",
        "python -m runoff_routing.regression_dataset",
        "docs/REGRESSION_DATASET.md",
        "Use the one maintained original-CMD register and comparator.",
        "Historical snapshots are not fresh runs; preserve incomplete states.",
    ),
    Capability(
        "monte_carlo",
        "staged",
        "statistics",
        None,
        None,
        "docs/STATUS.md",
        "Monte Carlo sampling, execution and frequency analysis under development.",
        "Not shipped on main; original RORB statistical equivalence unqualified.",
        "https://github.com/Chain-Frost/pyrorb/pull/151",
    ),
    Capability(
        "native_representative_selection",
        "planned",
        "reporting",
        None,
        None,
        "docs/ARR_DETERMINISTIC_RESULTS.md",
        "Native representative-event and critical-duration selection qualification.",
        "Do not treat diagnostic observed-peak ranks as native rules.",
        "https://github.com/Chain-Frost/pyrorb/issues/152",
    ),
    Capability(
        "advanced_structures",
        "planned",
        "execution",
        None,
        None,
        "docs/CMD_FEATURE_MATRIX.md",
        "Special storages and other deferred advanced features.",
        "Must continue to fail closed until separately implemented and qualified.",
        "https://github.com/Chain-Frost/pyrorb/issues/5",
    ),
)


def find_capability(name: str) -> Capability | None:
    """Return a declared item without ever importing an arbitrary user-supplied module."""
    return next((item for item in CATALOG if item.name == name), None)
