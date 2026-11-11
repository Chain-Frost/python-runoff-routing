"""Independent reference numerics for one nonlinear RORB-style reach.

This module is a mathematical prototype, not a validated RORB-compatible solver.
No file parsing, random draws, network traversal or process behaviour belongs here.
"""

import math
from collections.abc import Sequence
from itertools import pairwise


class RoutingDomainError(ValueError):
    """Inputs or a timestep do not permit a finite nonnegative routed flow."""


def storage_volume(discharge_m3_s: float, *, coefficient_k: float, exponent_m: float) -> float:
    """Return reach storage in m³ under S = 3600 k Q**m.

    k is RORB's *combined* kc * kr, with dimensional units that depend on m.
    Only nonnegative, finite discharges and valid parameters are accepted.
    """
    _check_parameters(coefficient_k, exponent_m)
    _check_nonnegative_finite(discharge_m3_s, "Discharge")
    storage = 3600.0 * _storage_term(discharge_m3_s, coefficient_k, exponent_m)
    if not math.isfinite(storage):
        message = "The storage-discharge relation overflowed."
        raise RoutingDomainError(message)
    return storage


def _check_nonnegative_finite(value: float, name: str) -> None:
    if not math.isfinite(value) or value < 0.0:
        message = f"{name} must be finite and nonnegative."
        raise RoutingDomainError(message)


def _check_parameters(coefficient_k: float, exponent_m: float) -> None:
    _check_nonnegative_finite(coefficient_k, "Storage coefficient k")
    if not math.isfinite(exponent_m) or exponent_m <= 0.0:
        message = "Storage exponent m must be finite and positive."
        raise RoutingDomainError(message)


def _storage_term(discharge: float, coefficient_k: float, exponent_m: float) -> float:
    try:
        value = coefficient_k * discharge**exponent_m
    except OverflowError as exc:
        message = "The storage-discharge relation overflowed."
        raise RoutingDomainError(message) from exc
    if not math.isfinite(value):
        message = "The storage-discharge relation returned a non-finite value."
        raise RoutingDomainError(message)
    return value


def _residual(outflow: float, *, coefficient_k: float, exponent_m: float, half_step: float, target: float) -> float:
    return _storage_term(outflow, coefficient_k, exponent_m) + half_step * outflow - target


def _bracket_upper_bound(
    *,
    coefficient_k: float,
    exponent_m: float,
    half_step: float,
    target: float,
    previous_outflow: float,
    previous_inflow: float,
    current_inflow: float,
) -> float:
    upper = max(1.0, previous_outflow, previous_inflow, current_inflow)
    for _ in range(64):
        residual = _residual(
            upper, coefficient_k=coefficient_k, exponent_m=exponent_m, half_step=half_step, target=target
        )
        if not math.isfinite(residual):
            message = "Non-finite residual while bracketing a routed discharge."
            raise RoutingDomainError(message)
        if residual >= 0.0:
            return upper
        upper *= 2.0
    message = "Unable to bracket a nonnegative routed discharge."
    raise RoutingDomainError(message)


def _nonlinear_root(
    *,
    coefficient_k: float,
    exponent_m: float,
    half_step: float,
    target: float,
    previous_outflow: float,
    previous_inflow: float,
    current_inflow: float,
) -> float:
    """Solve the monotone storage-continuity residual by bracketed false position.

    Illinois endpoint damping avoids the well-known false-position stagnation.
    The algorithm and its strict tolerance are *not* claimed to reproduce RORB's
    historical iteration stopping/convergence decisions.
    """
    lower = 0.0
    f_lower = -target
    upper = _bracket_upper_bound(
        coefficient_k=coefficient_k,
        exponent_m=exponent_m,
        half_step=half_step,
        target=target,
        previous_outflow=previous_outflow,
        previous_inflow=previous_inflow,
        current_inflow=current_inflow,
    )
    f_upper = _residual(
        upper, coefficient_k=coefficient_k, exponent_m=exponent_m, half_step=half_step, target=target
    )
    side = 0
    tolerance = 1e-12 * max(1.0, abs(target))
    for _ in range(256):
        candidate = (lower * f_upper - upper * f_lower) / (f_upper - f_lower)
        if not lower < candidate < upper:
            candidate = 0.5 * (lower + upper)
        residual = _residual(
            candidate, coefficient_k=coefficient_k, exponent_m=exponent_m, half_step=half_step, target=target
        )
        if abs(residual) <= tolerance:
            return candidate
        if residual < 0.0:
            lower, f_lower = candidate, residual
            if side == -1:
                f_upper *= 0.5
            side = -1
        else:
            upper, f_upper = candidate, residual
            if side == 1:
                f_lower *= 0.5
            side = 1
    message = "Nonlinear reach routing did not converge within the iteration limit."
    raise RoutingDomainError(message)


def _next_outflow(
    *,
    previous_inflow: float,
    current_inflow: float,
    previous_outflow: float,
    coefficient_k: float,
    exponent_m: float,
    half_step: float,
) -> float:
    target = _storage_term(previous_outflow, coefficient_k, exponent_m) + half_step * (
        previous_inflow + current_inflow - previous_outflow
    )
    if not math.isfinite(target) or target < 0.0:
        message = "The timestep produces an invalid negative/non-finite routing target; reduce the timestep."
        raise RoutingDomainError(message)
    if target == 0.0:
        return 0.0
    if exponent_m == 1.0:
        return target / (coefficient_k + half_step)
    return _nonlinear_root(
        coefficient_k=coefficient_k,
        exponent_m=exponent_m,
        half_step=half_step,
        target=target,
        previous_outflow=previous_outflow,
        previous_inflow=previous_inflow,
        current_inflow=current_inflow,
    )


def route_reach(
    inflow_m3_s: Sequence[float],
    *,
    coefficient_k: float,
    exponent_m: float,
    time_step_hours: float,
) -> tuple[float, ...]:
    """Route one prescribed hydrograph with trapezoidal storage continuity.

    The time grid is uniform, and RORB's documented convention Qout[0] = Qin[0]
    is used. A zero-storage reach passes the complete input through unchanged.

    This solves the *documented* relationship, but the exact RORB time-step,
    convergence and reporting conventions still require native acceptance.
    """
    _check_parameters(coefficient_k, exponent_m)
    if not math.isfinite(time_step_hours) or time_step_hours <= 0.0:
        message = "Timestep must be finite and positive, in hours."
        raise RoutingDomainError(message)
    if len(inflow_m3_s) == 0:
        message = "At least one inflow ordinate is required."
        raise RoutingDomainError(message)
    for index, value in enumerate(inflow_m3_s):
        _check_nonnegative_finite(value, f"Inflow ordinate {index}")
    if coefficient_k == 0.0:
        return tuple(inflow_m3_s)
    half_step = 0.5 * time_step_hours
    output = [inflow_m3_s[0]]
    for previous_inflow, current_inflow in pairwise(inflow_m3_s):
        output.append(
            _next_outflow(
                previous_inflow=previous_inflow,
                current_inflow=current_inflow,
                previous_outflow=output[-1],
                coefficient_k=coefficient_k,
                exponent_m=exponent_m,
                half_step=half_step,
            )
        )
    return tuple(output)
