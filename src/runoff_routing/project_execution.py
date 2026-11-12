"""Execute validated S5 JSON projects through the existing S1/S2 reference API.

The S1 typed model remains authoritative. These are deterministic Python
calculations, NOT approved RORB_CMD/RORBwin or ARR rainfall equivalents.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal

from .integration import RunInputError, RunResult, run_model
from .project_json import EmbeddedRun, LoadedProject, ProjectError, load_project
from .rorb_model import to_json

CalculationStatus = Literal["computed_unvalidated"]
NativeParityStatus = Literal["not_assessed"]


@dataclass(frozen=True, slots=True)
class ExecutedProject:
    """A Python reference calculation with immutable project and model provenance."""

    project_id: str
    rainfall_profile: Literal["explicit", "legacy-rorb"]
    source_kind: Literal["embedded-run", "rorb-files"]
    project_sha256: str
    model_sha256: str
    source_file_hashes: tuple[tuple[str, str], ...]
    calculation: RunResult
    calculation_status: CalculationStatus = "computed_unvalidated"
    native_parity_status: NativeParityStatus = "not_assessed"

    def to_json(self) -> str:
        """Report computed ordinates without claiming native clock or numerical parity."""
        return json.dumps(asdict(self), indent=2, sort_keys=True, allow_nan=False) + "\n"

    def to_csv(self) -> str:
        """Return the existing S2 long-form CSV with model-elapsed time only."""
        return self.calculation.to_csv()


@dataclass(frozen=True, slots=True)
class ComputedProjectComparison:
    """Exact Python outputs from two projects; native parity is not evaluated."""

    left_project_id: str
    right_project_id: str
    same_typed_model: bool
    same_external_assets: bool
    same_print_locations: bool
    same_computed_ordinates: bool
    first_difference: str | None
    comparison_status: Literal["diagnostic_only"] = "diagnostic_only"
    native_parity_status: NativeParityStatus = "not_assessed"

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2, sort_keys=True, allow_nan=False) + "\n"

    @property
    def identical(self) -> bool:
        """All supported model, metadata, print and computed-output checks match."""
        return (
            self.same_typed_model
            and self.same_external_assets
            and self.same_print_locations
            and self.same_computed_ordinates
        )


def _validated_profile(loaded: LoadedProject) -> Literal["explicit", "legacy-rorb"]:
    """Require already explicit rainfall forcing; never interpret an ARR export here."""
    profile = loaded.project.rainfall_profile
    if profile == "arr-2026v1":
        message = "ARR 2026 rainfall must be prepared through a separately validated S6 event adapter"
        raise ProjectError(message)
    if any(asset.role != "reference" for asset in loaded.project.assets):
        message = "Rainfall, temporal-pattern and curve assets are unprocessed; explicit forcing is required"
        raise ProjectError(message)
    if profile == "explicit":
        return "explicit"
    if profile == "legacy-rorb":
        return "legacy-rorb"
    message = f"Unrecognised calculation profile: {profile}"
    raise ProjectError(message)


def execute_loaded_project(loaded: LoadedProject) -> ExecutedProject:
    """Use S1's RunModel with the existing pure S2 single-storm solver only."""
    profile = _validated_profile(loaded)
    try:
        calculated = run_model(loaded.run)
    except RunInputError as exc:
        message = f"Unsupported S1/S2 calculation profile: {exc}"
        raise ProjectError(message) from exc
    model_bytes = to_json(loaded.run).encode("utf-8")
    return ExecutedProject(
        loaded.project.identifier,
        profile,
        "embedded-run" if isinstance(loaded.project.model_source, EmbeddedRun) else "rorb-files",
        hashlib.sha256(loaded.original_json_bytes).hexdigest(),
        hashlib.sha256(model_bytes).hexdigest(),
        loaded.file_hashes,
        calculated,
    )


def run_project(path: Path) -> ExecutedProject:
    """Load a JSON project, verify every referenced byte, then compute offline."""
    return execute_loaded_project(load_project(path))


def write_execution_json(path: Path, result: ExecutedProject) -> None:
    """Write one report exclusively. Inputs and existing outputs are never replaced."""
    with path.open("xb") as handle:
        handle.write(result.to_json().encode("utf-8"))


def _first_output_difference(left: RunResult, right: RunResult) -> str | None:
    if left.numerical.dt_hours != right.numerical.dt_hours:
        return "timestep_hours"
    if len(left.prints) != len(right.prints):
        return "print_locations.length"
    for first, second in zip(left.prints, right.prints, strict=True):
        if first.print_id != second.print_id or first.label != second.label:
            return f"print_location.{first.print_id}"
        if len(first.discharge_m3_s) != len(second.discharge_m3_s):
            return f"print_location.{first.print_id}.ordinate_count"
        for index, (a, b) in enumerate(zip(first.discharge_m3_s, second.discharge_m3_s, strict=True)):
            if a != b:
                return f"print_location.{first.print_id}.sample[{index}]"
    return None


def compare_routed_projects(left: Path, right: Path) -> ComputedProjectComparison:
    """Require equal rainfall methods; compare explicit Python outputs without time shifts.

    This is NOT a RORB or ARR compliance check. It compares two supported
    JSON project representations through the same strict reference kernel.
    """
    original = load_project(left)
    alternative = load_project(right)
    if original.project.rainfall_profile != alternative.project.rainfall_profile:
        message = "Cannot run a cross-method comparison: rainfall profiles differ"
        raise ProjectError(message)
    left_run = execute_loaded_project(original)
    right_run = execute_loaded_project(alternative)
    first_difference = _first_output_difference(left_run.calculation, right_run.calculation)
    locations_equal = tuple((item.print_id, item.label) for item in left_run.calculation.prints) == tuple(
        (item.print_id, item.label) for item in right_run.calculation.prints
    )
    return ComputedProjectComparison(
        original.project.identifier,
        alternative.project.identifier,
        original.run == alternative.run,
        original.project.assets == alternative.project.assets,
        locations_equal,
        first_difference is None,
        first_difference,
    )
