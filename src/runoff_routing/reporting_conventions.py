"""Compare native reported sample-sum volume with physical-horizon integration.

The result is a reporting-convention diagnostic, not a routing or mass-balance
acceptance test. Original printed tokens and native clocks are never rewritten.
No files, native executables or numerical routing kernels are used.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from itertools import pairwise


@dataclass(frozen=True, slots=True)
class VolumeConventionAudit:
    """Explicit, separate sample-sum and physical-horizon statistics."""

    sample_count: int
    timestep_hours: Decimal
    inclusive_sample_sum_m3: Decimal
    physical_trapezoid_m3: Decimal
    endpoint_weight_difference_m3: Decimal
    sample_sum_printing_bound_m3: Decimal
    trapezoid_printing_bound_m3: Decimal
    reported_native_volume_m3: Decimal | None
    reported_native_half_unit_m3: Decimal | None
    sample_sum_consistent_with_report: bool | None
    trapezoid_consistent_with_report: bool | None
    sample_index_centroid_hours: Decimal | None
    sample_index_elapsed_hours: tuple[Decimal, ...]
    raw_native_time_tokens: tuple[str, ...] | None


def _printed_token(token: str, *, label: str) -> tuple[Decimal, Decimal]:
    """Parse exact decimal text and its own half-last-place print unit."""
    if not isinstance(token, str) or not token or token != token.strip() or "_" in token:
        message = f"{label} must be one unmodified numeric print token"
        raise ValueError(message)
    try:
        value = Decimal(token)
    except InvalidOperation as exc:
        message = f"{label} is not a decimal print token"
        raise ValueError(message) from exc
    if not value.is_finite() or value < 0:
        message = f"{label} must be finite and nonnegative"
        raise ValueError(message)
    exponent = value.as_tuple().exponent
    if not isinstance(exponent, int):
        message = f"{label} does not have a finite print resolution"
        raise TypeError(message)
    try:
        half_unit = Decimal(5).scaleb(exponent - 1)
    except InvalidOperation as exc:
        message = f"{label} has an unrepresentable print resolution"
        raise ValueError(message) from exc
    return value, half_unit


def _overlaps_print_intervals(
    candidate: Decimal, candidate_bound: Decimal, reported: Decimal, reported_bound: Decimal
) -> bool:
    """Use two independent print resolutions, never a tuned flow tolerance."""
    return candidate - candidate_bound <= reported + reported_bound and reported - reported_bound <= (
        candidate + candidate_bound
    )


def audit_volume_conventions(
    discharge_tokens: Sequence[str],
    *,
    timestep_hours: Decimal,
    native_reported_volume_text: str | None = None,
    raw_native_time_tokens: Sequence[str] | None = None,
) -> VolumeConventionAudit:
    """Audit distinct native summary and physical-horizon volume candidates.

    Inclusive sample-sum: 3600*h*sum(q[0..N]).
    Physical horizon: 3600*h*sum((q[i]+q[i+1])/2).

    Only source print precision is propagated. A consistency result supports
    or excludes a *reporting* hypothesis for this series, never native solver
    equivalence, hydrological mass balance or the interpretation of raw times.
    """
    if not isinstance(timestep_hours, Decimal) or not timestep_hours.is_finite() or timestep_hours <= 0:
        message = "Timestep must be a positive finite Decimal number of hours"
        raise ValueError(message)
    tokens = tuple(discharge_tokens)
    if not tokens:
        message = "At least one printed discharge sample is required"
        raise ValueError(message)
    parsed = tuple(_printed_token(token, label=f"Discharge sample {index}") for index, token in enumerate(tokens))
    values = tuple(value for value, _ in parsed)
    uncertainties = tuple(bound for _, bound in parsed)
    raw_times = tuple(raw_native_time_tokens) if raw_native_time_tokens is not None else None
    if raw_times is not None and (len(raw_times) != len(values) or any(not value for value in raw_times)):
        message = "Raw native time labels must be present for every discharge sample"
        raise ValueError(message)

    factor = Decimal(3600) * timestep_hours
    inclusive = factor * sum(values, Decimal(0))
    trapezoid = factor * sum(((before + after) / 2 for before, after in pairwise(values)), Decimal(0))
    inclusive_bound = factor * sum(uncertainties, Decimal(0))
    trapezoid_bound = factor * sum(
        ((before + after) / 2 for before, after in pairwise(uncertainties)), Decimal(0)
    )
    reported = reported_bound = None
    sample_sum_consistent = trapezoid_consistent = None
    if native_reported_volume_text is not None:
        reported, reported_bound = _printed_token(native_reported_volume_text, label="Native volume")
        sample_sum_consistent = _overlaps_print_intervals(inclusive, inclusive_bound, reported, reported_bound)
        trapezoid_consistent = _overlaps_print_intervals(trapezoid, trapezoid_bound, reported, reported_bound)

    elapsed = tuple(timestep_hours * index for index in range(len(values)))
    total = sum(values, Decimal(0))
    centroid: Decimal | None = None
    if total:
        centroid = sum((time * flow for time, flow in zip(elapsed, values, strict=True)), Decimal(0)) / total
    return VolumeConventionAudit(
        sample_count=len(values),
        timestep_hours=timestep_hours,
        inclusive_sample_sum_m3=inclusive,
        physical_trapezoid_m3=trapezoid,
        endpoint_weight_difference_m3=inclusive - trapezoid,
        sample_sum_printing_bound_m3=inclusive_bound,
        trapezoid_printing_bound_m3=trapezoid_bound,
        reported_native_volume_m3=reported,
        reported_native_half_unit_m3=reported_bound,
        sample_sum_consistent_with_report=sample_sum_consistent,
        trapezoid_consistent_with_report=trapezoid_consistent,
        sample_index_centroid_hours=centroid,
        sample_index_elapsed_hours=elapsed,
        raw_native_time_tokens=raw_times,
    )
