"""Explicit ARR2019 regional temporal-pattern ensemble selection, with source order retained.

This implements published size/frequency bins, not RORBwin pattern selection,
representative-event choice, storm filtering, or ARR2026-specific policy.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Literal

from runoff_routing.arr_data import ARRFormatError
from runoff_routing.arr_patterns import Pattern, PatternSet

TP_SELECTION_POLICY = "ARR2019_BOOK2_5_9_REGIONAL_V1"
# The lower bound of each band is inclusive. The next lower bound is exclusive.
_AREAL_BINS: tuple[tuple[int, str], ...] = (
    (75, "100"),
    (140, "200"),
    (300, "500"),
    (700, "1000"),
    (1600, "2500"),
    (3500, "5000"),
    (7000, "10000"),
    (14000, "20000"),
    (28000, "40000"),
)
# Exact design probabilities backed by standard regional ARR2019 ensemble practice.
_AEP_BINS: dict[Decimal, str] = {
    Decimal("50"): "frequent",
    Decimal("20"): "frequent",
    Decimal("10"): "intermediate",
    Decimal("5"): "intermediate",
    Decimal("2"): "rare",
    Decimal("1"): "rare",
}


@dataclass(frozen=True, slots=True)
class TemporalPatternSelection:
    """A traceable source-order ensemble, not a single selected design event."""

    policy_version: str
    catchment_area_km2: Decimal
    duration_min: int
    aep_percent: Decimal
    source_kind: Literal["point", "areal"]
    region: str
    source_sha256: str
    area_bin: str | None
    aep_band: str | None
    patterns: tuple[Pattern, ...]
    expected_count: int

    @property
    def event_ids(self) -> tuple[str, ...]:
        """Exact published IDs in source order, without ordinal substitution."""
        return tuple(pattern.event_id for pattern in self.patterns)


def _area_bin(area_km2: Decimal) -> str | None:
    if not area_km2.is_finite() or area_km2 <= 0:
        msg = "Catchment area must be a positive finite Decimal in km2"
        raise ARRFormatError(msg)
    if area_km2 < 75:
        return None
    return next(bin_label for lower, bin_label in reversed(_AREAL_BINS) if area_km2 >= lower)


def select_arr2019_ensemble(
    source: PatternSet,
    *,
    catchment_area_km2: Decimal,
    duration_min: int,
    aep_percent: Decimal,
    region: str,
    expected_count: int = 10,
) -> TemporalPatternSelection:
    """Filter one supplied regional archive using ARR2019 Table 2.5.9.

    No nearest-duration, nearest-frequency or nearest-area fallback is permitted.
    An areal CSV without an AEP field is selected by area and duration only;
    its missing frequency metadata is retained as None.
    """
    area_bin = _area_bin(catchment_area_km2)
    if not region or not region.strip():
        msg = "Temporal-pattern region must be explicitly supplied"
        raise ARRFormatError(msg)
    if isinstance(duration_min, bool) or duration_min <= 0:
        msg = "Design duration must be a positive integer number of minutes"
        raise ARRFormatError(msg)
    if not aep_percent.is_finite():
        msg = "AEP must be a finite Decimal percentage, not EY or ARI"
        raise ARRFormatError(msg)
    aep_band = _AEP_BINS.get(aep_percent)
    if aep_band is None:
        msg = f"ARR2019 temporal-pattern frequency selection is not characterised for {aep_percent}% AEP"
        raise ARRFormatError(msg)
    if isinstance(expected_count, bool) or not 1 <= expected_count <= 20:
        msg = "Expected ensemble count must be an integer from 1 to 20"
        raise ARRFormatError(msg)
    kind: Literal["point", "areal"] = "point" if area_bin is None else "areal"
    if source.kind != kind:
        msg = f"Catchment area {catchment_area_km2} km2 requires {kind} temporal patterns"
        raise ARRFormatError(msg)
    matched = tuple(
        p
        for p in source.patterns
        if p.region == region
        and p.duration_min == duration_min
        and p.area_bin == area_bin
        and (p.aep_band == aep_band if kind == "point" else p.aep_band in {None, aep_band})
    )
    if len(matched) != expected_count:
        msg = (
            f"Expected {expected_count} {kind} ARR2019 patterns, got {len(matched)} "
            f"for duration={duration_min}, AEP={aep_percent}%, area_bin={area_bin}, region={region!r}; "
            "no missing-event or alternative-bin substitution"
        )
        raise ARRFormatError(msg)
    if kind == "areal" and any(p.aep_band != matched[0].aep_band for p in matched):
        msg = "Mixed or missing areal AEP metadata within the selected ensemble"
        raise ARRFormatError(msg)
    return TemporalPatternSelection(
        policy_version=TP_SELECTION_POLICY,
        catchment_area_km2=catchment_area_km2,
        duration_min=duration_min,
        aep_percent=aep_percent,
        source_kind=kind,
        region=region,
        source_sha256=source.source_sha256,
        area_bin=area_bin,
        aep_band=matched[0].aep_band,
        patterns=matched,
        expected_count=expected_count,
    )
