"""Bounded, independent RORB-style single-storm calculation.

Supports explicit DESIGN storms, one uniform pervious ISA, IL/CL, natural
reaches and the stack control-vector subset 1/3/4/5/7. No native process,
I/O, GIS, fitted constants or inferred print-site identities are involved.
The first output sample is at t=0; rainfall in a bin enters at its END sample.
The time/phase and loss-crossing choices require native-profile acceptance.
"""

import math
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

from runoff_routing.reach_routing import RoutingDomainError, route_reach

ControlCode = Literal[1, 3, 4, 5, 7]


@dataclass(frozen=True, slots=True)
class Control:
    """Route/stack/print operation in original computational order."""

    code: ControlCode
    reach_length_km: float = 0.0


@dataclass(frozen=True, slots=True)
class Storm:
    """Single explicit, uniform temporal pattern; depths are per subarea."""

    timestep_hours: float
    calculation_increments: int
    percentages: tuple[float, ...]
    depths_mm: tuple[float, ...]


@dataclass(frozen=True, slots=True)
class Losses:
    initial_mm: float
    continuing_mm_h: float


@dataclass(frozen=True, slots=True)
class Catchment:
    """Computational vector, not graphical node coordinates."""

    controls: tuple[Control, ...]
    areas_km2: tuple[float, ...]


@dataclass(frozen=True, slots=True)
class StormResult:
    """Pure calculation output, with no implied native numeric equivalence."""

    outlets_m3_s: tuple[tuple[float, ...], ...]
    rainfall_excess_mm: tuple[tuple[float, ...], ...]
    source_hydrographs_m3_s: tuple[tuple[float, ...], ...]
    average_distance_km: float
    route_factors: tuple[float, ...]
    dt_hours: float


def _check_finite_nonnegative(value: float, label: str) -> None:
    if not math.isfinite(value) or value < 0:
        message = f"{label} must be finite and nonnegative."
        raise RoutingDomainError(message)


def _check_catchment(catchment: Catchment) -> None:
    if not catchment.areas_km2:
        message = "At least one subarea is required."
        raise RoutingDomainError(message)
    for area in catchment.areas_km2:
        _check_finite_nonnegative(area, "Subarea area")
    if not all(area > 0 for area in catchment.areas_km2):
        message = "All subarea areas must be positive."
        raise RoutingDomainError(message)
    if not catchment.controls or catchment.controls[-1].code != 7:
        message = "The model must terminate at a printed outlet."
        raise RoutingDomainError(message)
    for command in catchment.controls:
        if command.code not in {1, 3, 4, 5, 7}:
            message = f"Unsupported control code: {command.code}."
            raise RoutingDomainError(message)
        _check_finite_nonnegative(command.reach_length_km, "Reach length")
        if command.code not in {1, 5} and command.reach_length_km != 0:
            message = "Only control codes 1 and 5 may specify reach length."
            raise RoutingDomainError(message)


def _distance_analysis(catchment: Catchment) -> tuple[float, tuple[float, ...]]:
    """Area-weighted final-outlet paths; kr=length/dav for natural reaches."""
    _check_catchment(catchment)
    running: dict[int, float] | None = None
    stack: list[dict[int, float]] = []
    source_index = 0
    reaches: list[float] = []
    for command in catchment.controls:
        match command.code:
            case 1:
                if source_index >= len(catchment.areas_km2):
                    message = "More source operations than subarea areas."
                    raise RoutingDomainError(message)
                running = {source_index: command.reach_length_km}
                source_index += 1
                reaches.append(command.reach_length_km)
            case 3:
                running = _running_paths(running)
                stack.append(dict(running))
            case 4:
                running = _join_paths(running, stack)
            case 5:
                running = _running_paths(running)
                running = {index: distance + command.reach_length_km for index, distance in running.items()}
                reaches.append(command.reach_length_km)
            case 7:
                running = _running_paths(running)
    running = _final_paths(catchment, source_index, running, stack)
    total_area = math.fsum(catchment.areas_km2)
    dav = math.fsum(area * running[index] for index, area in enumerate(catchment.areas_km2)) / total_area
    if not math.isfinite(dav) or dav <= 0:
        message = "Average flow distance must be finite and positive."
        raise RoutingDomainError(message)
    return dav, tuple(length / dav for length in reaches)


def rainfall_excess(rainfall_mm: Sequence[float], *, losses: Losses, timestep_hours: float) -> tuple[float, ...]:
    """Pervious IL/CL applied to individual rainfall bins; no carryover CL.

    Initial loss is exhausted before CL applies to residual rain in that bin.
    Exact within-increment crossing and native reporting remain under review.
    """
    _check_finite_nonnegative(losses.initial_mm, "Initial loss")
    _check_finite_nonnegative(losses.continuing_mm_h, "Continuing loss")
    if not math.isfinite(timestep_hours) or timestep_hours <= 0:
        message = "Timestep must be finite and positive."
        raise RoutingDomainError(message)
    continuing_per_bin = losses.continuing_mm_h * timestep_hours
    if not math.isfinite(continuing_per_bin):
        message = "Continuing loss per increment overflowed."
        raise RoutingDomainError(message)
    initial_remaining = losses.initial_mm
    excess: list[float] = []
    for rainfall in rainfall_mm:
        _check_finite_nonnegative(rainfall, "Rainfall")
        consumed = min(initial_remaining, rainfall)
        initial_remaining -= consumed
        excess.append(max(0.0, rainfall - consumed - continuing_per_bin))
    return tuple(excess)


def calculate_storm(catchment: Catchment, storm: Storm, *, losses: Losses, kc: float, m: float) -> StormResult:
    """Route one storm through the control vector using the S2 reference kernel.

    Supported source convention is Q[0]=0 then 1 sample per rainfall bin;
    all remaining calculation increments have zero source rainfall. Models
    requiring a different phase, multiple ISAs, non-natural reaches, lateral
    inflows or special storage are not supported by this API.
    """
    _check_storm(catchment, storm, kc, m)
    dav, factors = _distance_analysis(catchment)
    excesses = tuple(
        rainfall_excess(
            tuple(percent * depth / 100 for percent in storm.percentages),
            losses=losses,
            timestep_hours=storm.timestep_hours,
        )
        for depth in storm.depths_mm
    )
    count = storm.calculation_increments + 1
    sources = tuple(
        tuple(
            [0.0]
            + [depth * area / (3.6 * storm.timestep_hours) for depth in excess]
            + [0.0] * (count - len(excess) - 1)
        )
        for area, excess in zip(catchment.areas_km2, excesses, strict=True)
    )
    outputs = _route_vector(catchment, sources, factors, kc, m, storm.timestep_hours)
    return StormResult(tuple(outputs), excesses, sources, dav, factors, storm.timestep_hours)


def _check_storm(catchment: Catchment, storm: Storm, kc: float, m: float) -> None:
    _check_finite_nonnegative(kc, "kc")
    if not math.isfinite(m) or m <= 0:
        message = "m must be finite and positive."
        raise RoutingDomainError(message)
    if not math.isfinite(storm.timestep_hours) or storm.timestep_hours <= 0:
        message = "Timestep must be finite and positive."
        raise RoutingDomainError(message)
    if storm.calculation_increments < len(storm.percentages) or storm.calculation_increments <= 0:
        message = "Calculation horizon must cover all rainfall bins."
        raise RoutingDomainError(message)
    if len(storm.depths_mm) != len(catchment.areas_km2):
        message = "Each subarea must have one rainfall depth."
        raise RoutingDomainError(message)
    for depth in storm.depths_mm:
        _check_finite_nonnegative(depth, "Rainfall depth")
    for percent in storm.percentages:
        _check_finite_nonnegative(percent, "Temporal percentage")
    if not math.isclose(math.fsum(storm.percentages), 100, rel_tol=0, abs_tol=0.01):
        message = "Temporal pattern percentages must total 100 within printed precision."
        raise RoutingDomainError(message)


def _route_vector(
    catchment: Catchment,
    sources: tuple[tuple[float, ...], ...],
    factors: tuple[float, ...],
    kc: float,
    m: float,
    dt: float,
) -> list[tuple[float, ...]]:
    routed: tuple[float, ...] | None = None
    stack: list[tuple[float, ...]] = []
    outputs: list[tuple[float, ...]] = []
    factor_index = 0
    source_index = 0
    for command in catchment.controls:
        match command.code:
            case 1:
                routed = route_reach(
                    sources[source_index],
                    coefficient_k=kc * factors[factor_index],
                    exponent_m=m,
                    time_step_hours=dt,
                )
                source_index += 1
                factor_index += 1
            case 3:
                stack.append(_running_flow(routed))
            case 4:
                if routed is None or not stack:
                    message = "No stored hydrograph to join."
                    raise RoutingDomainError(message)
                previous = stack.pop()
                routed = tuple(a + b for a, b in zip(previous, routed, strict=True))
            case 5:
                if routed is None:
                    message = "No running hydrograph to route."
                    raise RoutingDomainError(message)
                routed = route_reach(
                    routed,
                    coefficient_k=kc * factors[factor_index],
                    exponent_m=m,
                    time_step_hours=dt,
                )
                factor_index += 1
            case 7:
                if routed is None:
                    message = "No running hydrograph to print."
                    raise RoutingDomainError(message)
                outputs.append(routed)
    return outputs


def _final_paths(
    catchment: Catchment,
    source_index: int,
    running: dict[int, float] | None,
    stack: list[dict[int, float]],
) -> dict[int, float]:
    if source_index != len(catchment.areas_km2) or stack:
        message = "Control vector does not consume each source exactly once or leaves stored flows."
        raise RoutingDomainError(message)
    if running is None or set(running) != set(range(source_index)):
        message = "Final printed outlet must contain each subarea once."
        raise RoutingDomainError(message)
    return running


def _join_paths(running: dict[int, float] | None, stack: list[dict[int, float]]) -> dict[int, float]:
    if running is None or not stack:
        message = "Confluence has no running/stored hydrographs."
        raise RoutingDomainError(message)
    previous = stack.pop()
    if previous.keys() & running.keys():
        message = "A subarea would be counted twice at a confluence."
        raise RoutingDomainError(message)
    return previous | running


def _running_flow(flow: tuple[float, ...] | None) -> tuple[float, ...]:
    if flow is None:
        message = "No running hydrograph to store."
        raise RoutingDomainError(message)
    return flow


def _running_paths(paths: dict[int, float] | None) -> dict[int, float]:
    if paths is None:
        message = "Cannot operate on an uninitialised running hydrograph."
        raise RoutingDomainError(message)
    return paths
