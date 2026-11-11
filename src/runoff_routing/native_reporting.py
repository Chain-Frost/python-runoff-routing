"""Distinguish legacy reported sample sums from physical-horizon integrals.

This is a pure numerical diagnostic, not an RORB executable or solver.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

SECONDS_PER_HOUR = Decimal(3600)


@dataclass(frozen=True, slots=True)
class VolumeConventionReview:
    """Preserve native printed tokens and both independently defined volumes."""

    profile_id: str
    raw_native_time_tokens: tuple[str, ...] | None
    sample_index_elapsed_hours: tuple[Decimal, ...]
    native_volume_token: str | None
    native_reported_volume_m3: Decimal | None
    native_inclusive_sum_candidate_m3: Decimal
    physical_horizon_trapezoid_m3: Decimal
    extra_endpoint_weight_m3: Decimal
    native_sum_printing_bound_m3: Decimal
    physical_integral_printing_bound_m3: Decimal
    native_report_printing_bound_m3: Decimal | None
    native_sum_consistent_with_report: bool | None
    physical_integral_consistent_with_report: bool | None


def _finite_nonnegative(token: str, label: str) -> Decimal:
    try:
        number = Decimal(token)
    except InvalidOperation as exc:
        message = f"{label} must be a valid Decimal numeric token."
        raise ValueError(message) from exc
    if not number.is_finite() or number < 0:
        message = f"{label} must be finite and nonnegative."
        raise ValueError(message)
    return number


def _half_print_unit(value: Decimal) -> Decimal:
    exponent = value.as_tuple().exponent
    if not isinstance(exponent, int):
        message = "A finite Decimal token must have an integral printed exponent."
        raise TypeError(message)
    return Decimal("0.5").scaleb(exponent)


def review_volume_conventions(
    native_discharge_tokens: Sequence[str],
    *,
    timestep_hours: str,
    profile_id: str,
    reported_volume_text: str | None = None,
    raw_native_time_tokens: Sequence[str] | None = None,
) -> VolumeConventionReview:
    """Audit independent sample-volume conventions using raw printed precision.

    Never reinterpret native time tokens or infer an engine version. Historical
    native full-weight sample sums are a version-specific candidate, not a
    universal volume rule or the physical-horizon flux integral.
    """
    if not profile_id.strip():
        message = "An explicit, version-qualified engine profile is required."
        raise ValueError(message)
    dt = _finite_nonnegative(timestep_hours, "Timestep")
    if dt == 0:
        message = "Timestep must be strictly positive."
        raise ValueError(message)
    if len(native_discharge_tokens) < 2:
        message = "At least two discharge samples are required to define a physical horizon."
        raise ValueError(message)
    if raw_native_time_tokens is not None and len(raw_native_time_tokens) != len(native_discharge_tokens):
        message = "Raw time-token count differs from discharge count."
        raise ValueError(message)

    values = tuple(
        _finite_nonnegative(token, f"Discharge sample {index}")
        for index, token in enumerate(native_discharge_tokens)
    )
    half_units = tuple(_half_print_unit(value) for value in values)
    middle_sum = sum(values[1:-1], Decimal(0))
    middle_error = sum(half_units[1:-1], Decimal(0))
    full_sum = sum(values, Decimal(0))
    full_error = sum(half_units, Decimal(0))
    native_candidate = SECONDS_PER_HOUR * dt * full_sum
    physical_integral = SECONDS_PER_HOUR * dt * (middle_sum + (values[0] + values[-1]) / 2)
    native_candidate_bound = SECONDS_PER_HOUR * dt * full_error
    physical_bound = SECONDS_PER_HOUR * dt * (middle_error + (half_units[0] + half_units[-1]) / 2)

    reported = None
    reported_bound = None
    native_consistent = None
    physical_consistent = None
    if reported_volume_text is not None:
        reported = _finite_nonnegative(reported_volume_text, "Native reported volume")
        reported_bound = _half_print_unit(reported)
        native_consistent = abs(reported - native_candidate) <= reported_bound + native_candidate_bound
        physical_consistent = abs(reported - physical_integral) <= reported_bound + physical_bound

    return VolumeConventionReview(
        profile_id=profile_id,
        raw_native_time_tokens=tuple(raw_native_time_tokens) if raw_native_time_tokens is not None else None,
        sample_index_elapsed_hours=tuple(index * dt for index in range(len(values))),
        native_volume_token=reported_volume_text,
        native_reported_volume_m3=reported,
        native_inclusive_sum_candidate_m3=native_candidate,
        physical_horizon_trapezoid_m3=physical_integral,
        extra_endpoint_weight_m3=native_candidate - physical_integral,
        native_sum_printing_bound_m3=native_candidate_bound,
        physical_integral_printing_bound_m3=physical_bound,
        native_report_printing_bound_m3=reported_bound,
        native_sum_consistent_with_report=native_consistent,
        physical_integral_consistent_with_report=physical_consistent,
    )
