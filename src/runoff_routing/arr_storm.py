"""Explicit raw hyetographs from *already selected* IFD depths and ARR patterns.

Not an ARR method implementation: no event selection, ARF, climate change, preburst,
losses, temporal filtering, RORB serialization, or hydrological acceptance.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Literal

from runoff_routing.arr_data import ARRDocument, ARRFormatError, IFDDataset
from runoff_routing.arr_patterns import Pattern, PatternSet
from runoff_routing.bom_ifd import BoMIFD, BoMProbability


@dataclass(frozen=True, slots=True)
class RawHyetograph:
    """Gross rainfall depths (mm) per increment, no hydrologic adjustments."""

    duration_min: int
    timestep_min: int
    pattern_event_id: str
    pattern_region: str
    pattern_aep_band: str
    pattern_area_bin: str | None
    source_label: str
    source_sha256: str
    pattern_source_sha256: str
    probability_label: str
    source_rainfall_depth_mm: Decimal
    increments_mm: tuple[Decimal, ...]
    end_times_min: tuple[int, ...]
    total_mm: Decimal
    operations: tuple[str, ...]
    hydrological_acceptance: Literal["not_assessed"] = "not_assessed"


def _match_pattern(patterns: PatternSet, pattern: Pattern, *, duration_min: int) -> None:
    if pattern not in patterns.patterns:
        msg = "Temporal pattern does not belong to supplied source set"
        raise ARRFormatError(msg)
    if pattern.duration_min != duration_min:
        msg = "IFD event duration does not match temporal-pattern duration"
        raise ARRFormatError(msg)
    if sum(pattern.increments_percent) != Decimal(100):
        msg = "Explicit storm generation requires exactly 100% temporal increments; no silent normalisation"
        raise ARRFormatError(msg)


def _make_storm(
    *,
    pattern_set: PatternSet,
    pattern: Pattern,
    depth: Decimal,
    source_label: str,
    source_sha256: str,
    probability_label: str,
    operations: tuple[str, ...],
) -> RawHyetograph:
    _match_pattern(pattern_set, pattern, duration_min=pattern.duration_min)
    if not depth.is_finite() or depth < 0:
        msg = "Raw storm depth must be finite and nonnegative"
        raise ARRFormatError(msg)
    depths = tuple(depth * fraction / Decimal(100) for fraction in pattern.increments_percent)
    return RawHyetograph(
        duration_min=pattern.duration_min,
        timestep_min=pattern.timestep_min,
        pattern_event_id=pattern.event_id,
        pattern_region=pattern.region,
        pattern_aep_band=pattern.aep_band,
        pattern_area_bin=pattern.area_bin,
        source_label=source_label,
        source_sha256=source_sha256,
        pattern_source_sha256=pattern_set.source_sha256,
        probability_label=probability_label,
        source_rainfall_depth_mm=depth,
        increments_mm=depths,
        end_times_min=tuple(range(pattern.timestep_min, pattern.duration_min + 1, pattern.timestep_min)),
        total_mm=sum(depths, Decimal(0)),
        operations=operations,
    )


def storm_from_bom(
    source: BoMIFD,
    probability: BoMProbability,
    pattern_set: PatternSet,
    pattern: Pattern,
    *,
    convert_intensity: bool = False,
) -> RawHyetograph:
    """Select an exact BoM duration/probability and emit a *gross* event only."""
    _match_pattern(pattern_set, pattern, duration_min=pattern.duration_min)
    depth = source.depth_mm_at(pattern.duration_min, probability, convert_intensity=convert_intensity)
    return _make_storm(
        pattern_set=pattern_set,
        pattern=pattern,
        depth=depth,
        source_label="BoM 2016 IFD (raw gross rainfall)",
        source_sha256=source.sha256,
        probability_label=probability.label,
        operations=(
            "EXACT_IFD_DURATION_AND_PROBABILITY",
            "CONVERT_MM_PER_H_TO_MM_EXPLICIT" if source.rainfall_unit == "mm/h" else "DEPTH_MM_AS_EXPORTED",
            "PATTERN_PERCENT_DISTRIBUTION_ONLY",
            "NO_ARF_NO_CLIMATE_ADJUSTMENT_NO_LOSSES_NO_PREBURST",
        ),
    )


def storm_from_arr_2026(
    document: ARRDocument,
    dataset: IFDDataset,
    probability_aep_percent: Decimal,
    pattern_set: PatternSet,
    pattern: Pattern,
) -> RawHyetograph:
    """Apply only raw 2026 IFD depth and a manually selected pattern; no scenario adjustment."""
    if dataset not in document.ifd_datasets:
        msg = "ARR IFD dataset does not belong to the supplied source document"
        raise ARRFormatError(msg)
    if dataset.scenario_ssp is not None or dataset.scenario_year is not None:
        msg = "Climate-adjusted ARR datasets require a separately reviewed selection policy"
        raise ARRFormatError(msg)
    try:
        i = dataset.durations_min.index(pattern.duration_min)
        j = dataset.aep_percent.index(probability_aep_percent)
    except ValueError as exc:
        msg = "Exact ARR duration/AEP percentage missing; no implicit interpolation"
        raise ARRFormatError(msg) from exc
    return _make_storm(
        pattern_set=pattern_set,
        pattern=pattern,
        depth=dataset.depths_mm[i][j],
        source_label=dataset.name,
        source_sha256=document.source.sha256,
        probability_label=f"{probability_aep_percent}% AEP",
        operations=(
            "EXACT_IFD_DURATION_AND_AEP_PERCENT",
            "DATA_HUB_BASELINE_AS_EXPORTED",
            "PATTERN_PERCENT_DISTRIBUTION_ONLY",
            "NO_ARF_NO_CLIMATE_ADJUSTMENT_NO_LOSSES_NO_PREBURST",
        ),
    )
