"""Immutable, source-faithful ARR Data Hub inputs; no rainfall generation or routing."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Literal

SCHEMA_VERSION = 1
MAX_SOURCE_BYTES = 8 * 1024 * 1024
MAX_IFD_TABLES = 64
MAX_DURATION_COUNT = 1024
MAX_AEP_COUNT = 128

Baseline = Literal["current_2030", "historical_1961_1990", "native"]
ExportFormat = Literal["json", "txt"]


class ARRFormatError(ValueError):
    """Unsafe, malformed or not yet characterised ARR data."""


@dataclass(frozen=True, slots=True)
class DataHubSource:
    """The hash covers the original bytes, including BOM, whitespace and newlines."""

    export_format: ExportFormat
    datahub_version: str | None
    sha256: str
    byte_length: int
    locator: str | None = None
    captured_at: str | None = None
    compatibility_profile: str | None = None
    system: str = "ARR Data Hub"


@dataclass(frozen=True, slots=True)
class QueryLocation:
    """Input coordinates are geographic WGS84 degrees, never projected metres."""

    latitude: Decimal
    longitude: Decimal
    centroid_used: str | None
    outlet_latitude: Decimal | None = None
    outlet_longitude: Decimal | None = None
    raw_fields: tuple[tuple[str, str], ...] = ()
    crs: str = "EPSG:4326"


@dataclass(frozen=True, slots=True)
class IFDDataset:
    """As-exported depth matrix, ordered axes, and explicit table identity."""

    source_layer: str
    name: str
    baseline: Baseline
    durations_min: tuple[int, ...]
    aep_percent: tuple[Decimal, ...]
    depths_mm: tuple[tuple[Decimal, ...], ...]
    provider_datasets: str | None = None
    release_year: int | None = None
    scenario_ssp: str | None = None
    scenario_year: int | None = None
    raw_metadata: tuple[tuple[str, str], ...] = ()
    duration_unit: str = "min"
    probability_unit: str = "AEP_PERCENT"
    depth_unit: str = "mm"
    climate_policy: str = "AS_EXPORTED_NO_FURTHER_UPLIFT"

    def __post_init__(self) -> None:
        """Validate matrix rather than trusting a supposedly-typed constructor."""
        if not self.name:
            msg = "IFD dataset name must not be empty"
            raise ARRFormatError(msg)
        _validate_ifd_axes(self)
        _validate_ifd_depths(self)
        if self.scenario_ssp is not None or self.scenario_year is not None:
            msg = "Scenario IFDs require a separately reviewed ARR climate-product contract"
            raise ARRFormatError(msg)


def _validate_ifd_axes(table: IFDDataset) -> None:
    """Keep probability and duration checks separate from matrix shape validation."""
    if not table.durations_min or len(table.durations_min) > MAX_DURATION_COUNT:
        msg = "IFD durations must be nonempty and bounded"
        raise ARRFormatError(msg)
    if not table.aep_percent or len(table.aep_percent) > MAX_AEP_COUNT:
        msg = "IFD AEP axis must be nonempty and bounded"
        raise ARRFormatError(msg)
    if len(set(table.durations_min)) != len(table.durations_min):
        msg = f"Duplicate IFD durations in {table.name}"
        raise ARRFormatError(msg)
    if len(set(table.aep_percent)) != len(table.aep_percent):
        msg = f"Duplicate IFD AEP values in {table.name}"
        raise ARRFormatError(msg)
    for duration in table.durations_min:
        if not isinstance(duration, int) or isinstance(duration, bool) or duration <= 0:
            msg = f"Invalid IFD duration: {duration!r}"
            raise ARRFormatError(msg)
    for aep in table.aep_percent:
        if not isinstance(aep, Decimal) or not aep.is_finite() or not (0 < aep <= 100):
            msg = f"Invalid AEP percentage: {aep!r}"
            raise ARRFormatError(msg)


def _validate_ifd_depths(table: IFDDataset) -> None:
    """Protect row and column coordinates and finite/nonnegative source values."""
    if len(table.depths_mm) != len(table.durations_min):
        msg = f"IFD row count mismatch in {table.name}"
        raise ARRFormatError(msg)
    for number, row in enumerate(table.depths_mm, 1):
        if len(row) != len(table.aep_percent):
            msg = f"IFD column count mismatch in {table.name} row {number}"
            raise ARRFormatError(msg)
        for depth in row:
            if not isinstance(depth, Decimal) or not depth.is_finite() or depth < 0:
                msg = f"Nonfinite or negative IFD depth in {table.name} row {number}"
                raise ARRFormatError(msg)


@dataclass(frozen=True, slots=True)
class ARRDocument:
    """An offline validated document, including all original source bytes."""

    source: DataHubSource
    location: QueryLocation
    ifd_datasets: tuple[IFDDataset, ...]
    absent_layers: tuple[str, ...]
    unprocessed_layers: tuple[str, ...]
    raw_bytes: bytes
    capability: Literal["ifd_validated", "location_only"] = "ifd_validated"

    def __post_init__(self) -> None:
        if len(self.ifd_datasets) > MAX_IFD_TABLES:
            msg = "Too many IFD datasets"
            raise ARRFormatError(msg)
        if self.source.byte_length != len(self.raw_bytes):
            msg = "ARR raw bytes do not match source metadata"
            raise ARRFormatError(msg)
        if not self.ifd_datasets and self.capability != "location_only":
            msg = "Document with no validated IFD must use location_only status"
            raise ARRFormatError(msg)
