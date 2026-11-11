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
    encoding: str = "utf-8-sig"


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


def _is_positive_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _is_valid_aep(value: object) -> bool:
    return isinstance(value, Decimal) and value.is_finite() and 0 < value <= 100


def _is_valid_depth(value: object) -> bool:
    return isinstance(value, Decimal) and value.is_finite() and value >= 0


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
        if not _is_positive_int(duration):
            msg = f"Invalid IFD duration: {duration!r}"
            raise ARRFormatError(msg)
    for aep in table.aep_percent:
        if not _is_valid_aep(aep):
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
            if not _is_valid_depth(depth):
                msg = f"Nonfinite or negative IFD depth in {table.name} row {number}"
                raise ARRFormatError(msg)


@dataclass(frozen=True, slots=True)
class LegacyStormLoss:
    """Original ARR2016 storm (not burst) IL/CL, with explicit missing -50 sentinel."""

    initial_loss_mm: Decimal | None
    continuing_loss_mm_per_hour: Decimal | None
    raw_id: str | None
    metadata: tuple[tuple[str, str], ...]
    raw_fields: tuple[tuple[str, str], ...]

    def __post_init__(self) -> None:
        for value in (self.initial_loss_mm, self.continuing_loss_mm_per_hour):
            if value is not None and not _is_valid_depth(value):
                msg = "Invalid legacy storm loss"
                raise ARRFormatError(msg)


@dataclass(frozen=True, slots=True)
class LegacyARF:
    """Raw historical coefficients: not an applied areal-reduction factor."""

    zone: str
    coefficients: tuple[tuple[str, Decimal], ...]
    metadata: tuple[tuple[str, str], ...]
    raw_fields: tuple[tuple[str, str], ...]

    def __post_init__(self) -> None:
        keys = tuple(key for key, _ in self.coefficients)
        if not self.zone or keys != tuple("abcdefghi"):
            msg = "Invalid legacy ARF zone/coefficients"
            raise ARRFormatError(msg)
        if any(not isinstance(value, Decimal) or not value.is_finite() for _, value in self.coefficients):
            msg = "Invalid nonfinite legacy ARF coefficient"
            raise ARRFormatError(msg)


@dataclass(frozen=True, slots=True)
class LegacyTPRegion:
    """TP regional identifier only; source increments remain a separate data product."""

    kind: Literal["point", "areal"]
    code: str
    label: str
    intersection_fraction: Decimal | None
    metadata: tuple[tuple[str, str], ...]
    raw_fields: tuple[tuple[str, str], ...]

    def __post_init__(self) -> None:
        if not self.code or not self.label or self.kind not in {"point", "areal"}:
            msg = "Invalid legacy temporal-pattern region identity"
            raise ARRFormatError(msg)
        if self.intersection_fraction is not None and not (Decimal(0) <= self.intersection_fraction <= 1):
            msg = "Invalid temporal-pattern intersection fraction"
            raise ARRFormatError(msg)


@dataclass(frozen=True, slots=True)
class LegacyPreburst:
    """Legacy depth and ratio are separately retained; ratios may legitimately exceed 1."""

    percentile: Literal[10, 25, 50, 75, 90]
    source_tag: str
    durations_min: tuple[int, ...]
    aep_percent: tuple[Decimal, ...]
    depths_mm: tuple[tuple[Decimal, ...], ...]
    ratios: tuple[tuple[Decimal, ...], ...]
    metadata: tuple[tuple[str, str], ...]

    def __post_init__(self) -> None:
        if not self.durations_min or len(self.durations_min) > MAX_DURATION_COUNT:
            msg = "Legacy preburst duration axis is empty/unbounded"
            raise ARRFormatError(msg)
        if not self.aep_percent or len(self.aep_percent) > MAX_AEP_COUNT:
            msg = "Legacy preburst probability axis is empty/unbounded"
            raise ARRFormatError(msg)
        if len(set(self.durations_min)) != len(self.durations_min) or any(
            not _is_positive_int(duration) for duration in self.durations_min
        ):
            msg = "Legacy preburst durations invalid or duplicated"
            raise ARRFormatError(msg)
        if len(set(self.aep_percent)) != len(self.aep_percent) or any(
            not _is_valid_aep(aep) for aep in self.aep_percent
        ):
            msg = "Legacy preburst AEP percentages invalid or duplicated"
            raise ARRFormatError(msg)
        if len(self.depths_mm) != len(self.durations_min) or len(self.ratios) != len(self.durations_min):
            msg = "Legacy preburst row count mismatch"
            raise ARRFormatError(msg)
        for depths, ratios in zip(self.depths_mm, self.ratios, strict=True):
            if len(depths) != len(self.aep_percent) or len(ratios) != len(self.aep_percent):
                msg = "Legacy preburst column count mismatch"
                raise ARRFormatError(msg)
            if any(not _is_valid_depth(value) for value in (*depths, *ratios)):
                msg = "Legacy preburst depth/ratio must be finite and nonnegative"
                raise ARRFormatError(msg)


@dataclass(frozen=True, slots=True)
class LegacyRawSection:
    """Recognised legacy marker whose numeric meaning has not yet been implemented."""

    tag: str
    body_lines: tuple[str, ...]
    metadata: tuple[tuple[str, str], ...]


@dataclass(frozen=True, slots=True)
class ARRDocument:
    """An offline validated document, including all original source bytes."""

    source: DataHubSource
    location: QueryLocation
    ifd_datasets: tuple[IFDDataset, ...]
    absent_layers: tuple[str, ...]
    unprocessed_layers: tuple[str, ...]
    raw_bytes: bytes
    capability: Literal["ifd_validated", "location_only", "legacy_layers_validated"] = "ifd_validated"
    legacy_losses: LegacyStormLoss | None = None
    legacy_arf: LegacyARF | None = None
    legacy_tp_regions: tuple[LegacyTPRegion, ...] = ()
    legacy_preburst: tuple[LegacyPreburst, ...] = ()
    legacy_unprocessed: tuple[LegacyRawSection, ...] = ()

    def __post_init__(self) -> None:
        if len(self.ifd_datasets) > MAX_IFD_TABLES:
            msg = "Too many IFD datasets"
            raise ARRFormatError(msg)
        if self.source.byte_length != len(self.raw_bytes):
            msg = "ARR raw bytes do not match source metadata"
            raise ARRFormatError(msg)
        if not self.ifd_datasets and self.capability == "ifd_validated":
            msg = "Document with no validated IFD cannot declare ifd_validated"
            raise ARRFormatError(msg)
        has_legacy = bool(self.legacy_losses or self.legacy_arf or self.legacy_tp_regions or self.legacy_preburst)
        if self.capability == "legacy_layers_validated" and (not has_legacy or self.ifd_datasets):
            msg = "Legacy capability requires legacy layers and cannot include IFD tables"
            raise ARRFormatError(msg)
