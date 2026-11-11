"""Independent linear-storage oracle and discrete balance audits for S2.

The oracle assumes *linearly interpolated prescribed inflow between samples*.
It is not an oracle for rainfall bin timing, network routing, or native RORB output
labels. The balance audit uses trapezoidal fluxes, not a native report's volume
convention. Both routines are pure and do not run native programs.
"""

import math
from collections.abc import Sequence
from dataclasses import dataclass
from itertools import pairwise

from runoff_routing.reach_routing import RoutingDomainError, storage_volume


@dataclass(frozen=True, slots=True)
class ReachBalanceStep:
    """Trapezoidal continuity terms for one sample-to-sample interval."""

    end_index: int
    inflow_volume_m3: float
    outflow_volume_m3: float
    storage_change_m3: float
    residual_m3: float


@dataclass(frozen=True, slots=True)
class ReachBalance:
    """Reach storage and flux balance; no assertion of native mass-balance parity."""

    steps: tuple[ReachBalanceStep, ...]
    initial_storage_m3: float
    final_storage_m3: float
    integrated_inflow_m3: float
    integrated_outflow_m3: float
    closure_residual_m3: float
    maximum_step_residual_m3: float


def _validate_nonnegative(values: Sequence[float], name: str) -> None:
    if not values:
        message = f"{name} requires at least one ordinate."
        raise RoutingDomainError(message)
    for index, value in enumerate(values):
        if not math.isfinite(value) or value < 0.0:
            message = f"{name} ordinate {index} must be finite and nonnegative."
            raise RoutingDomainError(message)


def _validate_time_step(time_step_hours: float) -> None:
    if not math.isfinite(time_step_hours) or time_step_hours <= 0.0:
        message = "Timestep must be finite and positive, in hours."
        raise RoutingDomainError(message)


def linear_continuous_reference(
    inflow_m3_s: Sequence[float], *, coefficient_k: float, time_step_hours: float
) -> tuple[float, ...]:
    """Exact m=1 storage response to a piecewise-linearly interpolated inflow.

    k is the *combined* storage coefficient, in hours for m=1. At t=0 the
    prescribed initial condition is Qout[0] = Qin[0]. This solves
    k * dQout/dt + Qout = Qin(t); it is deliberately a distinct reference
    from the existing trapezoidal (discrete) ``route_reach`` method.
    """
    if not math.isfinite(coefficient_k) or coefficient_k < 0.0:
        message = "Storage coefficient k must be finite and nonnegative."
        raise RoutingDomainError(message)
    _validate_time_step(time_step_hours)
    _validate_nonnegative(inflow_m3_s, "Inflow")
    if coefficient_k == 0.0:
        return tuple(inflow_m3_s)

    ratio = time_step_hours / coefficient_k
    if math.isinf(ratio):
        decay = 0.0
        total_input_weight = 1.0
        ramp_weight = 1.0
    else:
        decay = math.exp(-ratio)
        total_input_weight = -math.expm1(-ratio)
        if ratio < 1e-4:
            # Avoid cancellation in 1 - (1 - exp(-ratio)) / ratio.
            ramp_weight = ratio * (0.5 + ratio * (-1.0 / 6.0 + ratio * (1.0 / 24.0 - ratio / 120.0)))
        else:
            ramp_weight = 1.0 + math.expm1(-ratio) / ratio
    output = [float(inflow_m3_s[0])]
    for previous_inflow, current_inflow in pairwise(inflow_m3_s):
        # Positive convex weights avoid cancellation of approximately equal
        # inflow/outflow values when dt/k is extremely small.
        next_outflow = (
            decay * output[-1]
            + (total_input_weight - ramp_weight) * previous_inflow
            + ramp_weight * current_inflow
        )
        if not math.isfinite(next_outflow) or next_outflow < 0.0:
            message = "Continuous linear-storage reference produced an invalid discharge."
            raise RoutingDomainError(message)
        output.append(next_outflow)
    return tuple(output)


def audit_reach_balance(
    inflow_m3_s: Sequence[float],
    outflow_m3_s: Sequence[float],
    *,
    coefficient_k: float,
    exponent_m: float,
    time_step_hours: float,
) -> ReachBalance:
    """Audit every step using trapezoidal fluxes and S=3600*k*Q**m.

    The first/last storage values are included explicitly; outlet integration
    alone is not the same as a closed catchment water balance. Native reported
    discharge integrals can use a different sampling/phase convention.
    """
    _validate_time_step(time_step_hours)
    _validate_nonnegative(inflow_m3_s, "Inflow")
    _validate_nonnegative(outflow_m3_s, "Outflow")
    if len(inflow_m3_s) != len(outflow_m3_s):
        message = "Inflow and outflow sample counts must match exactly."
        raise RoutingDomainError(message)

    storage = storage_volume(outflow_m3_s[0], coefficient_k=coefficient_k, exponent_m=exponent_m)
    initial_storage = storage
    step_seconds = 3600.0 * time_step_hours
    if not math.isfinite(step_seconds):
        message = "Timestep duration overflows seconds."
        raise RoutingDomainError(message)
    steps: list[ReachBalanceStep] = []
    for index, ((in0, in1), (out0, out1)) in enumerate(
        zip(pairwise(inflow_m3_s), pairwise(outflow_m3_s), strict=True), start=1
    ):
        incoming = step_seconds * (0.5 * in0 + 0.5 * in1)
        outgoing = step_seconds * (0.5 * out0 + 0.5 * out1)
        next_storage = storage_volume(out1, coefficient_k=coefficient_k, exponent_m=exponent_m)
        storage_change = next_storage - storage
        if not all(math.isfinite(v) for v in (incoming, outgoing, storage_change)):
            message = "Reach volume calculation overflowed."
            raise RoutingDomainError(message)
        residual = math.fsum((storage_change, outgoing, -incoming))
        steps.append(ReachBalanceStep(index, incoming, outgoing, storage_change, residual))
        storage = next_storage
    integrated_inflow = math.fsum(step.inflow_volume_m3 for step in steps)
    integrated_outflow = math.fsum(step.outflow_volume_m3 for step in steps)
    closure = math.fsum((storage - initial_storage, integrated_outflow, -integrated_inflow))
    if not all(math.isfinite(value) for value in (integrated_inflow, integrated_outflow, closure)):
        message = "Integrated reach volume is non-finite."
        raise RoutingDomainError(message)
    return ReachBalance(
        steps=tuple(steps),
        initial_storage_m3=initial_storage,
        final_storage_m3=storage,
        integrated_inflow_m3=integrated_inflow,
        integrated_outflow_m3=integrated_outflow,
        closure_residual_m3=closure,
        maximum_step_residual_m3=max((abs(step.residual_m3) for step in steps), default=0.0),
    )
