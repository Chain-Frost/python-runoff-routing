"""Small field-binding/comparison helpers for #53, not a suite runner or solver.

Reuse the existing public output inspector for hydrograph rows. Scalar selectors
are pinned to the retained CMD report dialect, preserving all original tokens.
"""

import math
from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from fractions import Fraction
from typing import Literal

from ryan_library.functions.RORB.output_reader import bind_output_site_columns
from ryan_library.functions.RORB.reader_types import RorbDocument

from runoff_routing.rorb_documents import HydrographReport, RorbSource
from runoff_routing.rorb_out import checked_canonical_report

Status = Literal["pass", "fail", "incomplete"]


@dataclass(frozen=True, slots=True)
class ScalarField:
    """Original lexeme and exact one-based report selector."""

    token: str
    line: int
    character: int
    ordinal: int
    unit: str


@dataclass(frozen=True, slots=True)
class SiteMetrics:
    """Reported column and raw legend text; physical print identity is unverified."""

    column: str
    label: str
    peak: ScalarField | None
    peak_time: ScalarField | None
    volume: ScalarField | None


@dataclass(frozen=True, slots=True)
class PeakComparison:
    """Native reporting results; exact hidden-state ties remain a distinct gate."""

    magnitude: Status
    time: Status
    time_reason: str
    candidate_tied_indices: tuple[int, ...]
    candidate_peak: Fraction
    candidate_elapsed_hours: Fraction | None


def token_interval(token: str) -> tuple[Fraction, Fraction]:
    """Original inclusive half-last-unit interval, clipped at physical zero."""
    if not token or token != token.strip() or "_" in token:
        message = "Scalar must retain one complete original numeric token"
        raise ValueError(message)
    try:
        value = Decimal(token.replace("D", "E").replace("d", "e"))
    except InvalidOperation as exc:
        message = "Invalid scalar token"
        raise ValueError(message) from exc
    if not value.is_finite() or value < 0:
        message = "Scalar must be finite and nonnegative"
        raise ValueError(message)
    exponent = value.as_tuple().exponent
    if not isinstance(exponent, int):
        message = "Scalar has no finite decimal precision"
        raise TypeError(message)
    half = Fraction(Decimal(5).scaleb(exponent - 1))
    centre = Fraction(value)
    return max(Fraction(0), centre - half), centre + half


def _scalars(document: RorbDocument, prefix: str, unit: str) -> tuple[ScalarField, ...]:
    """Bind the exact canonical scalar records to the frozen CMD unit profile."""
    family, separator, expected_unit = prefix.partition(",")
    if not separator:
        message = "Scalar binding requires an explicit source unit"
        raise ValueError(message)
    section = document.section("reported_scalars")
    fields: list[ScalarField] = []
    for row in section.rows:
        if row["family"] != family:
            continue
        if row["unit"] != expected_unit:
            message = "Native scalar unit/scale differs from the selected reporting profile"
            raise ValueError(message)
        token = str(row["token"])
        token_interval(token)
        fields.append(
            ScalarField(
                token,
                int(str(row["line"])),
                int(str(row["character"])),
                int(str(row["ordinal"])),
                unit,
            )
        )
    if not section.valid:
        message = "Reported scalar section contains invalid source records"
        raise ValueError(message)
    return tuple(fields)


def _site_scalars(fields: tuple[ScalarField, ...], count: int) -> tuple[ScalarField | None, ...]:
    if not fields:
        return (None,) * count
    if len(fields) != count:
        message = "Ambiguous partial or duplicate native scalar population"
        raise ValueError(message)
    return fields


def bind_report_metrics(source: RorbSource, report: HydrographReport) -> tuple[SiteMetrics, ...]:
    """Bind source-scoped ordinal/scalar records, not verified physical print sites."""
    document = checked_canonical_report(source)
    if document.kind != "standard_output":
        message = "Canonical report is not a supported native output"
        raise ValueError(message)
    if document.metadata.get("hydrograph_summary_count") != 1:
        message = "Exactly one native hydrograph-summary legend is required"
        raise ValueError(message)
    hydrographs = [s for s in document.sections if s.name.startswith("hydrographs_")]
    if len(hydrographs) != 1 or not hydrographs[0].valid or tuple(hydrographs[0].columns[3:]) != report.columns:
        message = "Canonical hydrograph scope differs from the selected report"
        raise ValueError(message)
    if len(hydrographs[0].rows) != len(report.rows) or any(
        hydrographs[0].source_tokens[i]["Time"] != item.raw_time for i, item in enumerate(report.rows)
    ):
        message = "Canonical report tokens differ from the selected hydrograph"
        raise ValueError(message)
    # The canonical shared reader owns the sole numeric Hyd-ordinal grammar.
    # This consumes its source-preserving physical legend/column association
    # rather than reformatting HydNNN identifiers with a second local parser.
    # CMD original reports routinely omit the location name for their one
    # printed hydrograph. Preserve its numeric ordinal for source-derived
    # scalar comparisons without claiming a verified physical print identity.
    # The canonical reader remains strict by default in physical-site contexts.
    mapped = bind_output_site_columns(document, allow_unnamed=True)
    if len(mapped) != 1 and any(site.physical_name is None for site in mapped):
        message = "Multiple unnamed physical sites cannot be bound to scalar comparison"
        raise ValueError(message)
    if tuple(site.column for site in mapped) != report.columns:
        message = "Native physical site binding differs from the actual table columns"
        raise ValueError(message)

    count = len(report.columns)
    peaks = _site_scalars(_scalars(document, "Peak discharge,m³/s", "m3/s"), count)
    times = _site_scalars(_scalars(document, "Time to peak,h", "h"), count)
    volumes = _site_scalars(_scalars(document, "Volume,m³", "m3"), count)
    if any(value is not None for value in (*peaks, *times, *volumes)) and tuple(
        site.site_id for site in mapped
    ) != tuple(row["id"] for row in document.section("sites").rows):
        # Printed scalar ordinals have no separately verified site IDs. A
        # reordered hydrograph header is safe for Q identity but must not
        # silently remap peaks, times or volumes by list position.
        message = "Native scalar ordinals cannot be bound to reordered physical sites"
        raise ValueError(message)
    return tuple(
        SiteMetrics(site.column, site.description, peak, time, volume)
        for site, peak, time, volume in zip(mapped, peaks, times, volumes, strict=True)
    )


def _flows(values: Sequence[float]) -> tuple[Fraction, ...]:
    if not values or any(not math.isfinite(value) or value < 0 for value in values):
        message = "Complete finite nonnegative candidate flows are required"
        raise ValueError(message)
    return tuple(Fraction(value) for value in values)


def compare_peak(values: Sequence[float], timestep_hours: Fraction, binding: SiteMetrics) -> PeakComparison:
    """Compare a unique nonzero maximum; never choose a hidden native tie rule."""
    if timestep_hours <= 0:
        message = "Positive actual timestep required"
        raise ValueError(message)
    flows = _flows(values)
    peak = max(flows)
    ties = tuple(i for i, flow in enumerate(flows) if flow == peak)
    magnitude: Status = "incomplete"
    if binding.peak is not None:
        lower, upper = token_interval(binding.peak.token)
        magnitude = "pass" if lower <= peak <= upper else "fail"
    if peak == 0:
        return PeakComparison(magnitude, "incomplete", "zero_flow_time_undefined", ties, peak, None)
    if len(ties) != 1:
        return PeakComparison(magnitude, "incomplete", "native_tie_policy_unresolved", ties, peak, None)
    elapsed = ties[0] * timestep_hours
    if binding.peak_time is None:
        return PeakComparison(magnitude, "incomplete", "native_peak_time_scalar_absent", ties, peak, elapsed)
    lower, upper = token_interval(binding.peak_time.token)
    time: Status = "pass" if lower <= elapsed <= upper else "fail"
    return PeakComparison(magnitude, time, "unique_nonzero_candidate_peak", ties, peak, elapsed)


def compare_reported_volume(values: Sequence[float], duration_seconds: Fraction, binding: SiteMetrics) -> Status:
    """Compare only the frozen native inclusive sum, never physical closure."""
    if duration_seconds <= 0:
        message = "Positive actual duration required"
        raise ValueError(message)
    flows = _flows(values)
    if binding.volume is None:
        return "incomplete"
    value = duration_seconds * sum(flows, start=Fraction(0))
    lower, upper = token_interval(binding.volume.token)
    return "pass" if lower <= value <= upper else "fail"
