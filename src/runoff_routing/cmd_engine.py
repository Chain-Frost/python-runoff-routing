"""Typed S1 RunModel -> bounded CMD 6.44 whole-event computation.

This adapter does not reinterpret legacy files, import research data or reuse
the improved Python engine's rainfall, coefficient or routing calculations.
"""

from __future__ import annotations

import hashlib
import math
from dataclasses import asdict, dataclass
from decimal import Decimal
from typing import Literal

from ._cmd644.geometry import Geometry, compute_geometry
from ._cmd644.models import Control, Event, NumberInput
from ._cmd644.native_diagnostics import DIAGNOSTIC_PROFILE, TargetOperands, target_diagnostic
from ._cmd644.precision import UnsupportedNumericPath, store
from ._cmd644.reporting import CONTRACT_ID, execute
from .engine_types import EngineHydrograph, EngineStatus
from .project_json import LoadedProject
from .rorb_model import CatchmentModel, RoutingValue, to_json

CMD_PROFILE = "cmd-6.44"
CANDIDATE_SOURCE = "fea9c80c521127325b779ea0ea87ddf77795b290"

_INVALID_INPUT: EngineStatus = "invalid_input"
_UNSUPPORTED_FEATURE: EngineStatus = "unsupported_feature"
_NUMERICAL_ERROR: EngineStatus = "numerical_error"
_INCOMPLETE_OUTPUT: EngineStatus = "incomplete_output"


class CmdBoundaryError(ValueError):
    """A typed rejection before calculation or failure in bounded arithmetic."""

    def __init__(self, status: EngineStatus, code: str, description: str) -> None:
        super().__init__(description)
        self.status: EngineStatus = status
        self.code = code


@dataclass(frozen=True, slots=True)
class CmdComputed:
    """Common result shape without claiming completed native equivalence."""

    hydrographs: tuple[EngineHydrograph, ...]
    physical_time_hours: tuple[str, ...]
    diagnostics: dict[str, object]


@dataclass(frozen=True, slots=True)
class PreparedCmdModel:
    """One source/control/area/coefficient interpretation, not event hydraulic state."""

    catchment: CatchmentModel
    routing: tuple[RoutingValue, ...]
    geometry: Geometry


def prepare_cmd_model(loaded: LoadedProject) -> PreparedCmdModel:
    """Precompute existing CMD geometry once for invariant CATG and kc/m."""
    event = adapt_event(loaded)
    try:
        geometry = compute_geometry(event)
    except UnsupportedNumericPath as exc:
        raise CmdBoundaryError(_NUMERICAL_ERROR, "cmd_arithmetic", str(exc)) from exc
    return PreparedCmdModel(loaded.run.catchment, loaded.run.parameters.routing, geometry)


def _unsupported(code: str, description: str) -> None:
    raise CmdBoundaryError(_UNSUPPORTED_FEATURE, code, description)


def _number(value: Decimal) -> NumberInput:
    """Use public typed decimal representation and candidate f64->stored-f32 rule."""

    lexeme = str(value)
    try:
        widened = float(lexeme)
    except (OverflowError, ValueError) as exc:
        raise CmdBoundaryError(_INVALID_INPUT, "cmd_decimal_input", f"Cannot convert {lexeme!r}") from exc
    if not math.isfinite(widened):
        raise CmdBoundaryError(_INVALID_INPUT, "cmd_nonfinite_input", "Nonfinite binary64 CMD operand")
    if value != 0 and widened == 0:
        raise CmdBoundaryError(
            _UNSUPPORTED_FEATURE, "cmd_input_representation", "Nonzero CMD decimal operand underflows binary64"
        )
    try:
        stored = store(widened)
    except UnsupportedNumericPath as exc:
        raise CmdBoundaryError(_UNSUPPORTED_FEATURE, "cmd_input_representation", str(exc)) from exc
    return NumberInput(lexeme, widened, stored)


def _check_scope(loaded: LoadedProject) -> None:
    """Reject every input dimension not present in the qualified event path."""

    run = loaded.run
    parameters = run.parameters
    storm = run.storm
    catchment = run.catchment
    if loaded.project.rainfall_profile not in ("explicit", "legacy-rorb"):
        _unsupported("cmd_rainfall_profile", "CMD requires a supplied explicit DESIGN storm")
    if any(asset.role != "reference" for asset in loaded.project.assets):
        _unsupported("cmd_external_assets", "External storm and rainfall assets are not yet converted to CMD events")
    if (
        parameters.num_isa != 1
        or parameters.num_bursts != 1
        or not parameters.lumped_kc
        or parameters.loss_model not in (1, 2)
        or len(parameters.routing) != 1
        or len(parameters.losses) != 1
    ):
        _unsupported("cmd_parameters", "Only lumped kc, one ISA/burst and pervious IL/CL or IL/RoC are implemented")
    if parameters.loss_model == 2 and parameters.losses[0].continuing > Decimal(1):
        raise CmdBoundaryError(_INVALID_INPUT, "cmd_runoff_coefficient", "Runoff coefficient must not exceed 1")
    if (storm.pluviograph_count, storm.isa_count, storm.burst_count) != (1, 1, 1):
        _unsupported("cmd_storm", "Only one DESIGN pluviograph, ISA and burst is characterised")
    if catchment.storages:
        _unsupported("cmd_storages", "Special storages are not characterised")
    if not catchment.print_locations or sum(step.code == 7 for step in catchment.controls) != len(
        catchment.print_locations
    ):
        _unsupported("cmd_print_sites", "Every code-7 print needs a distinct explicit physical site")
    if catchment.controls[-1].code != 7 or any(step.code not in (1, 2, 3, 4, 5, 7) for step in catchment.controls):
        _unsupported("cmd_controls", "Unknown control order or non-terminal outlet")
    if storm.start_increment + len(storm.percentages) > storm.calculation_increments:
        _unsupported("cmd_horizon", "Event calculation horizon does not include all rainfall bins")


def adapt_event(loaded: LoadedProject) -> Event:
    """Convert the existing public typed model once; never parse a second grammar."""

    _check_scope(loaded)
    run = loaded.run
    control_values: list[Control] = []
    reach_index = 0
    for step in run.catchment.controls:
        if step.code in (1, 2, 5):
            length = run.catchment.reaches[reach_index].length_km
            reach_index += 1
        else:
            length = Decimal(0)
        control_values.append(Control(step.code, _number(length)))
    if reach_index != len(run.catchment.reaches):
        raise CmdBoundaryError(_INVALID_INPUT, "cmd_reach_order", "Reach/control count differs")
    pattern = (Decimal(0),) * run.storm.start_increment + run.storm.percentages
    weights = tuple(_number(value) for value in pattern)
    if not any(weight.stored > 0 for weight in weights):
        _unsupported("cmd_zero_pattern", "All rainfall pattern weights vanished after CMD storage")
    parameters = run.parameters
    native_loss_mode: Literal[1, 2] = 1 if parameters.loss_model == 1 else 2
    original_model_json = to_json(run)
    return Event(
        loaded.project.identifier,
        hashlib.sha256(original_model_json.encode("utf-8")).hexdigest(),
        original_model_json,
        tuple(control_values),
        tuple(_number(item.area_km2) for item in run.catchment.subareas),
        tuple(_number(value) for value in run.storm.depths_mm),
        tuple(_number(item.impervious_fraction) for item in run.catchment.subareas),
        weights,
        _number(run.storm.timestep_hours),
        _number(parameters.routing[0].kc),
        _number(parameters.routing[0].m),
        _number(parameters.losses[0].initial_loss_mm),
        _number(parameters.losses[0].continuing),
        run.storm.calculation_increments,
        native_loss_mode,
    )


def run_cmd_model(
    loaded: LoadedProject, implementation_revision: str, *, prepared: PreparedCmdModel | None = None
) -> CmdComputed:
    """Calculate each fresh CMD event with optional invariant prepared geometry."""

    event = adapt_event(loaded)
    if prepared is not None and (
        prepared.catchment != loaded.run.catchment or prepared.routing != loaded.run.parameters.routing
    ):
        raise CmdBoundaryError(_INVALID_INPUT, "prepared_mismatch", "Prepared CATG/routing parameters differ")
    try:
        result = execute(event, implementation_revision, geometry=prepared.geometry if prepared is not None else None)
    except UnsupportedNumericPath as exc:
        raise CmdBoundaryError(_NUMERICAL_ERROR, "cmd_arithmetic", str(exc)) from exc
    if len(result.network.outlet) != event.n + 1:
        raise CmdBoundaryError(_INCOMPLETE_OUTPUT, "cmd_horizon", "CMD backend returned a truncated horizon")
    if len(result.network.reaches) != event.reach_count:
        raise CmdBoundaryError(_INCOMPLETE_OUTPUT, "cmd_reach_count", "CMD backend omitted a physical reach")
    print_locations = loaded.run.catchment.print_locations
    if len(result.network.prints) != len(print_locations) or any(
        len(record.q) != event.n + 1 for record in result.network.prints
    ):
        raise CmdBoundaryError(
            _INCOMPLETE_OUTPUT, "cmd_print_sites", "One or more requested prints are absent or truncated"
        )
    if any(not math.isfinite(value) or value < 0 for record in result.network.prints for value in record.q):
        raise CmdBoundaryError(
            _INCOMPLETE_OUTPUT, "cmd_print_values", "Computed physical print contains non-finite or negative discharge"
        )
    expected_print_positions = tuple(
        index for index, step in enumerate(loaded.run.catchment.controls, start=1) if step.code == 7
    )
    if tuple(record.control_index_one_based for record in result.network.prints) != expected_print_positions:
        raise CmdBoundaryError(
            _INCOMPLETE_OUTPUT, "cmd_print_order", "Computed prints no longer follow original code-7 control order"
        )
    if result.network.prints[-1].q != result.network.outlet:
        raise CmdBoundaryError(_INCOMPLETE_OUTPUT, "cmd_final_print", "Final print does not match connected outlet")
    reach_ids = tuple(item.identifier for item in loaded.run.catchment.reaches)
    per_reach: list[dict[str, object]] = []
    for reach, reach_id in zip(result.network.reaches, reach_ids, strict=True):
        target_views = [
            asdict(
                target_diagnostic(
                    TargetOperands(
                        step.index,
                        reach.exponent,
                        step.previous_q,
                        step.previous_s,
                        step.previous_i,
                        step.current_i,
                        reach.duration_seconds,
                        step.target,
                    )
                )
            )
            for step in reach.steps
        ]
        per_reach.append(
            {
                "reach_id": reach_id,
                "source_membership_one_based": reach.membership,
                "coefficient_hours_stored": reach.coefficient,
                "coefficient_seconds_stored": reach.coefficient_seconds,
                "inflows_m3_s_stored": reach.incoming,
                "Q_m3_s_stored": reach.q,
                "S_m3_stored": reach.s,
                "historical_model_targets_and_separate_native_views": target_views,
                "iteration_counts": tuple(len(step.candidates) for step in reach.steps),
                "linear_routing": reach.is_linear,
                "zero_length_terminal_copy": loaded.run.catchment.reaches[len(per_reach)].length_km == 0,
            }
        )
    source_ids = tuple(item.identifier for item in loaded.run.catchment.subareas)
    crossings = tuple(
        {
            "source_id": crossing.source_id,
            "bin_one_based": crossing.bin_one_based,
            "signed_remaining_exact": str(crossing.signed_remaining),
            "equality_bins_before_crossing": crossing.equality_bins_before_crossing,
        }
        for crossing in result.preparation.crossings
    )
    diagnostics: dict[str, object] = {
        "cmd_profile": CMD_PROFILE,
        "loss_model": event.loss_model,
        "continuing_loss_mm_h_stored": event.cl.stored if event.loss_model == 1 else None,
        "runoff_coefficient_stored": event.cl.stored if event.loss_model == 2 else None,
        "candidate_contract": CONTRACT_ID,
        "candidate_source": CANDIDATE_SOURCE,
        "native_target_diagnostic_profile": DIAGNOSTIC_PROFILE,
        "native_parity": "not_assessed_for_this_public_source_or_wheel",
        "model_input_sha256": event.input_sha256,
        "ordered_source_ids": source_ids,
        "ordered_reach_ids": reach_ids,
        "print_sites": tuple(
            {
                "print_id": location.identifier,
                "label": location.label,
                "control_index_one_based": record.control_index_one_based,
                "source_membership_one_based": record.membership,
                "source_membership_ids": tuple(source_ids[index - 1] for index in record.membership),
                "Q_m3_s_stored": record.q,
            }
            for location, record in zip(print_locations, result.network.prints, strict=True)
        ),
        "source_rainfall_mm_stored": result.preparation.rain,
        "source_rainfall_excess_mm_stored": result.preparation.excess,
        "source_inflow_m3_s_stored": result.preparation.hydrographs,
        "source_loss_crossings": crossings,
        "source_distances_km_stored": result.geometry.distances,
        "mean_distance_km_stored": result.geometry.mean_distance,
        "reaches": per_reach,
        "native_reporting_and_physical_conservation": "not_assessed_for_this_public_source_or_wheel",
    }
    return CmdComputed(
        tuple(
            EngineHydrograph(location.identifier, location.label, record.q)
            for location, record in zip(print_locations, result.network.prints, strict=True)
        ),
        tuple(str(index * loaded.run.storm.timestep_hours) for index in range(event.n + 1)),
        diagnostics,
    )
