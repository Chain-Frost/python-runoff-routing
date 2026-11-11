"""S1 typed-input to S2 offline solver integration, without native RORB.

Parsing, source evidence and canonical writers belong to S1. All numerical
conversion is made at S1's one-ISA payload boundary. A calculation is never
an assertion of native compatibility or numerical parity.
"""

from __future__ import annotations

import csv
import io
import json
import math
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal, cast

from .parity_metrics import PrintedParity, assess_printed_parity
from .reach_routing import RoutingDomainError
from .rorb_codec import (
    FormatProblem,
    ParsedDocument,
    parse_catg,
    parse_cmd_par,
    parse_design_stm,
    to_s2_payload,
    write_new,
)
from .rorb_model import CatchmentModel, ParameterSet, RunModel, StormModel, from_json
from .single_storm import Catchment, Control, ControlCode, Losses, Storm, StormResult, calculate_storm

InputStatus = Literal["invalid", "unsupported"]
InputRole = Literal["parameters", "catchment", "storm", "run"]


@dataclass(frozen=True, slots=True)
class InputDiagnostic:
    """The input role is explicit; line numbers always refer to the original source."""

    status: InputStatus
    code: str
    message: str
    role: InputRole
    line: int | None = None


class RunInputError(ValueError):
    """Fail-closed validation error with a machine-readable diagnostic."""

    def __init__(
        self, status: InputStatus, code: str, message: str, *, role: InputRole = "run", line: int | None = None
    ) -> None:
        super().__init__(message)
        self.diagnostic = InputDiagnostic(status, code, message, role, line)
        self.status = status
        self.code = code
        self.role = role
        self.line = line


@dataclass(frozen=True, slots=True)
class ParsedRun:
    """Complete parsed input with exact original bytes and field-level S1 source maps."""

    model: RunModel
    parameters: ParsedDocument[ParameterSet]
    catchment: ParsedDocument[CatchmentModel]
    storm: ParsedDocument[StormModel]


def parse_run_bytes(par: bytes, catg: bytes, stm: bytes) -> ParsedRun:
    """Parse three explicit source blobs; embedded .par references are never dereferenced."""
    try:
        parameters = parse_cmd_par(par)
    except FormatProblem as exc:
        error = RunInputError(exc.status, exc.code, str(exc), role="parameters", line=exc.line)
        raise error from exc
    try:
        catchment = parse_catg(catg)
    except FormatProblem as exc:
        error = RunInputError(exc.status, exc.code, str(exc), role="catchment", line=exc.line)
        raise error from exc
    try:
        storm = parse_design_stm(stm)
    except FormatProblem as exc:
        error = RunInputError(exc.status, exc.code, str(exc), role="storm", line=exc.line)
        raise error from exc
    try:
        model = RunModel(parameters.model, catchment.model, storm.model)
    except ValueError as exc:
        error = RunInputError("invalid", "cross_document_mismatch", str(exc))
        raise error from exc
    return ParsedRun(model, parameters, catchment, storm)


def read_run_files(par_path: Path, catg_path: Path, stm_path: Path) -> ParsedRun:
    """Read only explicitly provided paths; never trust source-relative paths."""
    return parse_run_bytes(par_path.read_bytes(), catg_path.read_bytes(), stm_path.read_bytes())


def read_run_json(source: str) -> RunModel:
    """Require a versioned S1 *run* document rather than an incomplete model."""
    try:
        parsed = from_json(source)
    except (TypeError, ValueError) as exc:
        error = RunInputError("invalid", "json_schema", str(exc))
        raise error from exc
    if not isinstance(parsed, RunModel):
        message = "An executable input must be a schema-1 run, not an individual document"
        error = RunInputError("unsupported", "incomplete_run", message)
        raise error
    return parsed


@dataclass(frozen=True, slots=True)
class PrintedHydrograph:
    """Computed print identity and original S1 label, never an inferred native HydNNN."""

    print_id: str
    label: str
    discharge_m3_s: tuple[float, ...]


@dataclass(frozen=True, slots=True)
class RunResult:
    """Calculated series and provenance; parity is always unassessed here."""

    prints: tuple[PrintedHydrograph, ...]
    numerical: StormResult
    parity_status: Literal["unassessed"] = "unassessed"
    output_time_convention: Literal["model_elapsed_from_zero"] = "model_elapsed_from_zero"

    def to_json(self) -> str:
        """JSON offline report with clearly marked, unverified model time coordinates."""
        return json.dumps(asdict(self), indent=2, sort_keys=True, allow_nan=False) + "\n"

    def to_csv(self) -> str:
        """Long-form CSV. Elapsed time is calculated, not copied from native labels."""
        buffer = io.StringIO(newline="")
        writer = csv.writer(buffer, lineterminator="\n")
        writer.writerow(("print_id", "print_label", "sample_index", "model_elapsed_hours", "discharge_m3_s"))
        for item in self.prints:
            for index, discharge in enumerate(item.discharge_m3_s):
                writer.writerow((item.print_id, item.label, index, index * self.numerical.dt_hours, discharge))
        return buffer.getvalue()


def _checked_positive(value: float, field: str, role: InputRole) -> None:
    if not math.isfinite(value) or value <= 0:
        message = f"{field} underflows, overflows or is not strictly positive at the float boundary"
        error = RunInputError("unsupported", "float_boundary", message, role=role)
        raise error


def _validated_solver_inputs(model: RunModel) -> tuple[Catchment, Storm, Losses, float, float]:
    """One normalization boundary: source Decimal -> S1 payload -> pure S2 classes."""
    try:
        payload = to_s2_payload(model)
    except (ValueError, OverflowError) as exc:
        message = str(exc)
        error = RunInputError("unsupported", "unsupported_s2_profile", message)
        raise error from exc
    for index, value in enumerate(payload.areas_km2, start=1):
        _checked_positive(value, f"Subarea {index} area", "catchment")
    for command in payload.controls:
        if command[0] in (1, 5):
            _checked_positive(command[1], "Natural reach length", "catchment")
    _checked_positive(payload.timestep_hours, "Storm timestep", "storm")
    _checked_positive(payload.kc, "Routing kc", "parameters")
    _checked_positive(payload.m, "Routing exponent m", "parameters")
    if not math.isfinite(payload.initial_loss_mm) or not math.isfinite(payload.continuing_loss_mm_h):
        message = "Loss values cannot be represented at the finite float boundary"
        error = RunInputError("unsupported", "float_boundary", message, role="parameters")
        raise error
    if not all(math.isfinite(value) for value in (*payload.percentages, *payload.depths_mm)):
        message = "Storm depths/percentages cannot be represented as finite floats"
        error = RunInputError("unsupported", "float_boundary", message, role="storm")
        raise error
    source_values = (
        *zip(model.storm.percentages, payload.percentages, strict=True),
        *zip(model.storm.depths_mm, payload.depths_mm, strict=True),
        (model.parameters.losses[0].initial_loss_mm, payload.initial_loss_mm),
        (model.parameters.losses[0].continuing, payload.continuing_loss_mm_h),
    )
    if any(source != 0 and converted == 0.0 for source, converted in source_values):
        message = "A nonzero source value underflows to zero at the S2 float boundary"
        error = RunInputError("unsupported", "float_boundary", message)
        raise error
    if abs(math.fsum(payload.percentages) - 100.0) > 0.01:
        message = "S2 requires percentages to total 100 within its 0.01 numerical tolerance"
        error = RunInputError("unsupported", "storm_precision", message, role="storm")
        raise error
    if any(code not in (1, 3, 4, 5, 7) for code, _ in payload.controls):
        message = "An uncharacterised control code reached the S2 input boundary"
        error = RunInputError("unsupported", "control_code", message, role="catchment")
        raise error
    controls = tuple(Control(cast("ControlCode", code), length) for code, length in payload.controls)
    catchment = Catchment(controls, payload.areas_km2)
    storm = Storm(
        payload.timestep_hours,
        payload.calculation_increments,
        payload.percentages,
        payload.depths_mm,
    )
    losses = Losses(payload.initial_loss_mm, payload.continuing_loss_mm_h)
    return catchment, storm, losses, payload.kc, payload.m


def run_model(model: RunModel) -> RunResult:
    """Execute only S1-validated, S2-supported models; no native engine or I/O.

    Unsupported configurations raise RunInputError *before* calculation.
    Printed identities follow S1 control order; no native output associations,
    print-time offsets or hidden routing conventions are guessed.
    """
    catchment, storm, losses, kc, m = _validated_solver_inputs(model)
    try:
        numerical = calculate_storm(catchment, storm, losses=losses, kc=kc, m=m)
    except (RoutingDomainError, ArithmeticError, ValueError) as exc:
        error = RunInputError("unsupported", "solver_domain", str(exc))
        raise error from exc
    if any(
        not math.isfinite(value) or value < 0
        for series in (*numerical.outlets_m3_s, *numerical.rainfall_excess_mm, *numerical.source_hydrographs_m3_s)
        for value in series
    ):
        message = "Solver produced non-finite or negative discharge or rainfall excess"
        error = RunInputError("unsupported", "nonfinite_result", message)
        raise error
    if len(numerical.outlets_m3_s) != len(model.catchment.print_locations):
        message = "Solver output count differs from the explicit ordered S1 print locations"
        error = RunInputError("invalid", "print_count", message, role="catchment")
        raise error
    prints = tuple(
        PrintedHydrograph(location.identifier, location.label, values)
        for location, values in zip(model.catchment.print_locations, numerical.outlets_m3_s, strict=True)
    )
    return RunResult(prints, numerical)


def assess_recorded_print(result: RunResult, native_discharge_tokens: Sequence[str], *, print_id: str) -> PrintedParity:
    """Reuse S2's all-ordinate comparator for an *explicitly identified* print.

    The caller must independently establish native column identity, phase,
    timestamps and source fingerprints. A comparison is not parity acceptance.
    """
    matching = tuple(item for item in result.prints if item.print_id == print_id)
    if len(matching) != 1:
        message = f"The print_id {print_id!r} does not uniquely identify a calculated outlet"
        error = RunInputError("invalid", "print_identity", message, role="catchment")
        raise error
    return assess_printed_parity(
        matching[0].discharge_m3_s, native_discharge_tokens, dt_hours=result.numerical.dt_hours
    )


def write_result_json(path: Path, result: RunResult) -> None:
    """Write one report with exclusive-create semantics (never clobber)."""
    write_new(path, result.to_json().encode("utf-8"))


def write_result_csv(path: Path, result: RunResult) -> None:
    """Write one CSV with exclusive-create semantics (never clobber)."""
    write_new(path, result.to_csv().encode("utf-8"))
