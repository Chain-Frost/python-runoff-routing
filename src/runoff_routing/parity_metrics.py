"""Printed-precision and independent step-balance audits for offline S2 evidence.

These audits do not validate a native engine, its time-label convention, or
rainfall-loss and network transport. No reference executable or files are read.
"""

import math
from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from runoff_routing.reach_analysis import audit_reach_balance
from runoff_routing.reach_routing import RoutingDomainError


@dataclass(frozen=True, slots=True)
class PrintedParity:
    """All-ordinate printed precision hypothesis, not engine acceptance."""

    sample_count: int
    within_print_budget: bool
    matching_samples: int
    first_outside_budget_index: int | None
    maximum_absolute_error_m3_s: float
    rms_error_m3_s: float
    maximum_scaled_error: float
    maximum_near_zero_absolute_error_m3_s: float
    predicted_peak_index: int
    native_peak_index: int
    predicted_peak_m3_s: float
    native_peak_m3_s: float
    predicted_integral_m3: float
    native_integral_m3: float
    integral_rounding_bound_m3: float


@dataclass(frozen=True, slots=True)
class PrintedLinearBalance:
    """Inferred storage and independently calculated printed-output flux residuals."""

    initial_inferred_storage_m3: float
    final_inferred_storage_m3: float
    inflow_integral_m3: float
    outflow_integral_m3: float
    closure_residual_m3: float
    closure_printing_bound_m3: float
    max_step_residual_m3: float
    max_step_printing_bound_m3: float
    first_outside_step_budget_index: int | None
    closure_within_budget: bool
    steps_within_budget: bool


def _valid_step(dt_hours: float) -> None:
    if not math.isfinite(dt_hours) or dt_hours <= 0:
        msg = "Printed-ordinate timestep must be finite and positive."
        raise RoutingDomainError(msg)


def _read_tokens(tokens: Sequence[str]) -> tuple[tuple[float, ...], tuple[float, ...]]:
    if not tokens:
        msg = "At least one printed discharge token is required."
        raise ValueError(msg)
    values: list[float] = []
    half_units: list[float] = []
    for index, token in enumerate(tokens):
        try:
            decimal = Decimal(token)
            if not decimal.is_finite():
                msg = f"Non-finite printed discharge at sample {index}."
                raise ValueError(msg)
            exponent = decimal.as_tuple().exponent
            if not isinstance(exponent, int):
                msg = f"Invalid printed resolution at sample {index}."
                raise ValueError(msg)
            half_unit = Decimal(5).scaleb(exponent - 1)
            value = float(decimal)
            unit = float(half_unit)
        except (InvalidOperation, OverflowError, ValueError) as exc:
            msg = f"Invalid printed discharge token at sample {index}."
            raise ValueError(msg) from exc
        if not decimal.is_finite() or not math.isfinite(value) or value < 0 or not math.isfinite(unit) or unit <= 0:
            msg = f"Non-finite or negative printed discharge at sample {index}."
            raise ValueError(msg)
        values.append(value)
        half_units.append(unit)
    return tuple(values), tuple(half_units)


def _integral(samples: Sequence[float], dt_hours: float) -> float:
    return 3600.0 * dt_hours * math.fsum(
        (left + right) * 0.5 for left, right in zip(samples, samples[1:], strict=False)
    )


def _integral_uncertainty(half_units: Sequence[float], dt_hours: float) -> float:
    if len(half_units) < 2:
        return 0.0
    return 3600.0 * dt_hours * math.fsum(
        (left + right) * 0.5 for left, right in zip(half_units, half_units[1:], strict=False)
    )


def assess_printed_parity(
    predicted_m3_s: Sequence[float], native_tokens: Sequence[str], *, dt_hours: float
) -> PrintedParity:
    """Check every sample against half its own printed last-place unit.

    This is a predeclared strict printing hypothesis, not a subsequently
    selected hydrological model tolerance. Near-zero scaled error uses the
    larger of observed magnitude and the individual half-print-unit.
    """
    _valid_step(dt_hours)
    native, half_units = _read_tokens(native_tokens)
    predictions = tuple(predicted_m3_s)
    if len(predictions) != len(native):
        msg = "Native and predicted sample counts differ."
        raise ValueError(msg)
    errors: list[float] = []
    within = 0
    first: int | None = None
    near_zero = 0.0
    maximum_scaled = 0.0
    for index, (predicted, reference, half_unit) in enumerate(
        zip(predictions, native, half_units, strict=True)
    ):
        if not math.isfinite(predicted) or predicted < 0:
            msg = f"Predicted discharge at sample {index} is invalid."
            raise ValueError(msg)
        error = abs(predicted - reference)
        errors.append(error)
        if abs(Decimal(str(predicted)) - Decimal(native_tokens[index])) <= Decimal(str(half_unit)):
            within += 1
        elif first is None:
            first = index
        maximum_scaled = max(maximum_scaled, error / max(reference, half_unit))
        if reference <= half_unit:
            near_zero = max(near_zero, error)
    peak_pred = max(predictions)
    peak_ref = max(native)
    return PrintedParity(
        sample_count=len(native),
        within_print_budget=first is None,
        matching_samples=within,
        first_outside_budget_index=first,
        maximum_absolute_error_m3_s=max(errors),
        rms_error_m3_s=math.sqrt(math.fsum(error * error for error in errors) / len(errors)),
        maximum_scaled_error=maximum_scaled,
        maximum_near_zero_absolute_error_m3_s=near_zero,
        predicted_peak_index=predictions.index(peak_pred),
        native_peak_index=native.index(peak_ref),
        predicted_peak_m3_s=peak_pred,
        native_peak_m3_s=peak_ref,
        predicted_integral_m3=_integral(predictions, dt_hours),
        native_integral_m3=_integral(native, dt_hours),
        integral_rounding_bound_m3=_integral_uncertainty(half_units, dt_hours),
    )


def audit_printed_linear_balance(
    prescribed_inflow_m3_s: Sequence[float], printed_inflow_tokens: Sequence[str],
    printed_outflow_tokens: Sequence[str], *, coefficient_k: float, dt_hours: float,
) -> PrintedLinearBalance:
    """Audit native printed linear reach balance using *known exact* forcing.

    Use only when prescribed inflow is independently pinned and is identical
    at printed precision. This uses no native internal storage observations:
    storage is inferred from S = 3600*k*Q. Printed downstream uncertainty
    is propagated through the discrete continuity equation, not guessed from
    the largest observed residual. Failing a bound is a numerical discrepancy.
    """
    _valid_step(dt_hours)
    if not math.isfinite(coefficient_k) or coefficient_k < 0:
        msg = "Combined k must be finite and nonnegative."
        raise RoutingDomainError(msg)
    upstream, upstream_eps = _read_tokens(printed_inflow_tokens)
    downstream, eps = _read_tokens(printed_outflow_tokens)
    if len(prescribed_inflow_m3_s) != len(upstream) or len(upstream) != len(downstream):
        msg = "The prescribed and printed sample grids must match."
        raise ValueError(msg)
    for index, (prescribed, printed, unit) in enumerate(
        zip(prescribed_inflow_m3_s, upstream, upstream_eps, strict=True)
    ):
        if not math.isfinite(prescribed) or prescribed < 0 or abs(prescribed - printed) > unit:
            msg = f"Prescribed inflow is not reproduced by the native upstream print at sample {index}."
            raise ValueError(msg)
    audit = audit_reach_balance(
        prescribed_inflow_m3_s, downstream, coefficient_k=coefficient_k, exponent_m=1.0,
        time_step_hours=dt_hours,
    )
    # The initial storage is exact when the printed first output equals the
    # independently prescribed initial flow (Qout[0] = Qin[0]).
    if Decimal(printed_outflow_tokens[0]) == Decimal(str(prescribed_inflow_m3_s[0])):
        eps = (0.0, *eps[1:])
    half_step = dt_hours * 0.5
    step_bounds = tuple(
        3600.0 * ((coefficient_k + half_step) * eps[index]
                  + abs(coefficient_k - half_step) * eps[index - 1])
        for index in range(1, len(eps))
    )
    outside = next(
        (step.end_index for step, bound in zip(audit.steps, step_bounds, strict=True)
         if abs(step.residual_m3) > bound + 1e-9), None
    )
    global_bound = _integral_uncertainty(eps, dt_hours) + 3600.0 * coefficient_k * (eps[0] + eps[-1])
    return PrintedLinearBalance(
        initial_inferred_storage_m3=audit.initial_storage_m3,
        final_inferred_storage_m3=audit.final_storage_m3,
        inflow_integral_m3=audit.integrated_inflow_m3,
        outflow_integral_m3=audit.integrated_outflow_m3,
        closure_residual_m3=audit.closure_residual_m3,
        closure_printing_bound_m3=global_bound,
        max_step_residual_m3=audit.maximum_step_residual_m3,
        max_step_printing_bound_m3=max(step_bounds, default=0.0),
        first_outside_step_budget_index=outside,
        closure_within_budget=abs(audit.closure_residual_m3) <= global_bound + 1e-9,
        steps_within_budget=outside is None,
    )
