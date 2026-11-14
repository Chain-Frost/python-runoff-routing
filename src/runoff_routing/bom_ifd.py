"""Source-preserving offline BoM Design Rainfall System CSV intake.

BoM design-rainfall downloads are distinct from ARR Data Hub exports. The
published 2016 methodology may appear in files issued in later years.
"""

from __future__ import annotations

import csv
import hashlib
import io
import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Literal, Never

from runoff_routing.arr_data import ARRFormatError

MAX_BOM_CSV_BYTES = 8 * 1024 * 1024
MAX_BOM_ROWS = 1024
MAX_BOM_PROBABILITIES = 128

ProbabilityKind = Literal["AEP_PERCENT", "EY", "AEP_ONE_IN", "ARI_YEARS"]
RainfallUnit = Literal["mm", "mm/h"]
BoMTableKind = Literal["ifd", "all_design"]

_TABLE_TITLE = re.compile(
    r"(?i)^(?P<kind>IFD|All)\s+Design Rainfall\s+(?P<unit>Depth|Intensity)\s*\((?P<unit_tag>mm|mm/h)\)$"
)
_PROBABILITY = re.compile(
    r"(?i)^(?:(?P<ey>\d+(?:\.\d+)?)\s*EY|"
    r"(?P<aep>\d+(?:\.\d+)?)\s*%(?:\s*AEP)?|"
    r"1\s*(?:in|/|:)\s*(?P<one_in>\d+(?:\.\d+)?)(?:\s*AEP)?|"
    r"(?P<ari>\d+(?:\.\d+)?)\s*(?:year|yr)\s*ARI)\s*$"
)
_DURATION = re.compile(r"(?i)^(?P<number>\d+(?:\.\d+)?)\s*(?P<unit>min(?:ute)?s?|hours?|hrs?|days?|d|h|m)$")
_COORDINATE = re.compile(r"(?i)^(?P<number>\d+(?:\.\d+)?)\s*\(\s*(?P<hemisphere>[NSEW])\s*\)$")


def _invalid(message: str) -> Never:
    raise ARRFormatError(message)


def _decimal(token: str, field: str, *, positive: bool = False) -> Decimal:
    try:
        value = Decimal(token.strip())
    except InvalidOperation as exc:
        msg = f"Invalid decimal for {field}: {token!r}"
        raise ARRFormatError(msg) from exc
    if not value.is_finite() or value < 0 or (positive and value == 0) or value.adjusted() > 1000:
        _invalid(f"Invalid, negative or nonfinite {field}: {token!r}")
    return value


def _signed_decimal(token: str, field: str) -> Decimal:
    try:
        value = Decimal(token.strip())
    except InvalidOperation as exc:
        msg = f"Invalid signed coordinate {field}: {token!r}"
        raise ARRFormatError(msg) from exc
    if not value.is_finite():
        _invalid(f"Nonfinite {field} coordinate")
    return value


def _coordinate(token: str, *, longitude: bool) -> Decimal:
    matched = _COORDINATE.fullmatch(token.strip())
    if matched is None:
        _invalid(f"Unknown BoM nearest-grid coordinate {token!r}")
    hemisphere = matched.group("hemisphere").upper()
    if (longitude and hemisphere not in {"E", "W"}) or (not longitude and hemisphere not in {"N", "S"}):
        _invalid(f"Coordinate hemisphere does not match latitude/longitude: {token!r}")
    value = _decimal(matched.group("number"), "nearest grid coordinate")
    return -value if hemisphere in {"S", "W"} else value


@dataclass(frozen=True, slots=True)
class BoMProbability:
    """Original probability label plus explicit EY/AEP/rare/ARI semantics."""

    label: str
    kind: ProbabilityKind
    value: Decimal

    def __post_init__(self) -> None:
        if not self.label or not self.value.is_finite() or self.value <= 0:
            _invalid("Invalid BoM probability label/value")
        if self.kind == "AEP_PERCENT" and self.value > 100:
            _invalid("BoM AEP percentage exceeds 100")
        if self.kind == "AEP_ONE_IN" and self.value < 1:
            _invalid("BoM one-in-N denominator must be at least one")


@dataclass(frozen=True, slots=True)
class BoMIFD:
    """Immutable BoM 2016-methodology rainfall table with exact source bytes."""

    sha256: str
    raw_bytes: bytes
    locator: str | None
    issued: str | None
    label: str | None
    latitude: Decimal | None
    longitude: Decimal | None
    nearest_latitude: Decimal | None
    nearest_longitude: Decimal | None
    rainfall_unit: RainfallUnit
    table_kind: BoMTableKind
    probabilities: tuple[BoMProbability, ...]
    durations_min: tuple[int, ...]
    duration_labels: tuple[str, ...]
    values: tuple[tuple[Decimal, ...], ...]
    raw_preamble: tuple[tuple[str, ...], ...]
    source_system: str = "BoM Design Rainfall System (2016 methodology)"

    def __post_init__(self) -> None:
        _validate_bom_axes(self)
        _validate_bom_matrix(self)

    def probability(self, label: str) -> BoMProbability:
        """Select by the original label, not an inferred index or probability conversion."""
        matches = (item for item in self.probabilities if item.label == label)
        found = next(matches, None)
        if found is None:
            _invalid(f"BoM probability label {label!r} was not present")
        return found

    def value_at(self, duration_min: int, probability: BoMProbability) -> Decimal:
        """Require exact duration and probability identity; no interpolation."""
        try:
            i = self.durations_min.index(duration_min)
            j = self.probabilities.index(probability)
        except ValueError as exc:
            msg = "Exact BoM duration/probability not found; no implicit conversion or interpolation"
            raise ARRFormatError(msg) from exc
        return self.values[i][j]

    def depth_mm_at(
        self, duration_min: int, probability: BoMProbability, *, convert_intensity: bool = False
    ) -> Decimal:
        """Depth (mm) or *explicit* conversion of intensity in mm/h."""
        value = self.value_at(duration_min, probability)
        if self.rainfall_unit == "mm":
            return value
        if not convert_intensity:
            _invalid("BoM source is intensity (mm/h); pass convert_intensity=True explicitly")
        return value * Decimal(duration_min) / Decimal(60)


def _validate_bom_axes(source: BoMIFD) -> None:
    """Verify source identity and both row and probability axes."""
    if hashlib.sha256(source.raw_bytes).hexdigest() != source.sha256:
        _invalid("BoM source hash does not match original bytes")
    if not source.raw_bytes or len(source.raw_bytes) > MAX_BOM_CSV_BYTES:
        _invalid("BoM CSV source is empty or unbounded")
    if not source.probabilities or len(source.probabilities) > MAX_BOM_PROBABILITIES:
        _invalid("BoM probability axis is empty or unbounded")
    if not source.durations_min or len(source.durations_min) > MAX_BOM_ROWS:
        _invalid("BoM duration axis is empty or unbounded")
    if len({(item.kind, item.value) for item in source.probabilities}) != len(source.probabilities):
        _invalid("Duplicate BoM probability in export")
    if len(set(source.durations_min)) != len(source.durations_min) or any(t <= 0 for t in source.durations_min):
        _invalid("Duplicate or invalid BoM duration")
    if tuple(sorted(source.durations_min)) != source.durations_min:
        _invalid("BoM duration axis must be in ascending source order")


def _validate_bom_matrix(source: BoMIFD) -> None:
    """Validate depth matrix, labelled durations and WGS84 grid/point coordinates."""
    if len(source.duration_labels) != len(source.durations_min):
        _invalid("BoM duration label and numeric axis mismatch")
    if len(source.values) != len(source.durations_min) or any(
        len(row) != len(source.probabilities) for row in source.values
    ):
        _invalid("BoM rainfall matrix dimensions do not match axes")
    if any(not value.is_finite() or value < 0 for row in source.values for value in row):
        _invalid("BoM IFD values must be finite and nonnegative")
    geographic_bounds = (
        (source.latitude, 90),
        (source.longitude, 180),
        (source.nearest_latitude, 90),
        (source.nearest_longitude, 180),
    )
    for coord, limit in geographic_bounds:
        if coord is not None and (not coord.is_finite() or abs(coord) > limit):
            _invalid("BoM geographic coordinate outside valid bounds")


def _duration(label: str) -> int:
    matched = _DURATION.fullmatch(label.strip())
    if matched is None:
        _invalid(f"Unknown BoM human-readable duration {label!r}")
    number = _decimal(matched.group("number"), "duration", positive=True)
    unit = matched.group("unit").lower()
    multiplier = 1 if unit.startswith("min") or unit == "m" else 1440 if unit.startswith("day") or unit == "d" else 60
    minutes = number * multiplier
    if minutes != minutes.to_integral_value() or not (1 <= minutes <= 10080):
        _invalid(f"Nonintegral/out-of-range BoM duration {label!r}")
    return int(minutes)


def _parse_probability(token: str) -> BoMProbability:
    label = token.strip()
    match = _PROBABILITY.fullmatch(label)
    if match is None:
        _invalid(f"Unknown BoM probability label {token!r}; EY, AEP and ARI are not interchangeable")
    kinds: tuple[tuple[str, ProbabilityKind], ...] = (
        ("ey", "EY"),
        ("aep", "AEP_PERCENT"),
        ("one_in", "AEP_ONE_IN"),
        ("ari", "ARI_YEARS"),
    )
    for group, kind in kinds:
        value = match.group(group)
        if value is not None:
            return BoMProbability(label=label, kind=kind, value=_decimal(value, "probability", positive=True))
    _invalid(f"Unsupported BoM probability label {token!r}")


def _csv_rows(raw: bytes, encoding: str) -> list[list[str]]:
    if not raw or len(raw) > MAX_BOM_CSV_BYTES:
        _invalid("BoM CSV is empty or exceeds the 8 MiB limit")
    if encoding not in {"utf-8-sig", "cp1252"}:
        _invalid("BoM CSV requires UTF-8 or explicitly selected cp1252 encoding")
    try:
        decoded = raw.decode(encoding)
    except UnicodeDecodeError as exc:
        msg = f"BoM CSV cannot be decoded as {encoding}"
        raise ARRFormatError(msg) from exc
    try:
        rows = list(csv.reader(io.StringIO(decoded, newline=""), strict=True))
    except csv.Error as exc:
        msg = "Malformed BoM CSV quoting"
        raise ARRFormatError(msg) from exc
    if len(rows) > MAX_BOM_ROWS + 256:
        _invalid("BoM CSV row count exceeds limit")
    return rows


def _table_metadata(preamble: list[list[str]], explicit_unit: RainfallUnit | None) -> tuple[BoMTableKind, RainfallUnit]:
    titles = [match for row in preamble for cell in row if (match := _TABLE_TITLE.fullmatch(cell.strip())) is not None]
    if len(titles) != 1:
        _invalid("BoM CSV requires one recognised IFD/All Design Rainfall depth or intensity title")
    title = titles[0]
    kind: BoMTableKind = "all_design" if title.group("kind").lower() == "all" else "ifd"
    unit: RainfallUnit = "mm/h" if title.group("unit_tag").lower() == "mm/h" else "mm"
    if (unit == "mm") != (title.group("unit").lower() == "depth"):
        _invalid("BoM units and depth/intensity title contradict each other")
    if explicit_unit is not None and unit != explicit_unit:
        _invalid("Explicit BoM rainfall unit contradicts the CSV header")
    return kind, unit


def _metadata(
    preamble: list[list[str]],
) -> tuple[str | None, str | None, Decimal | None, Decimal | None, Decimal | None, Decimal | None]:
    issued: str | None = None
    label: str | None = None
    latitude: Decimal | None = None
    longitude: Decimal | None = None
    nearest_latitude: Decimal | None = None
    nearest_longitude: Decimal | None = None
    for row in preamble:
        if not row:
            continue
        key = row[0].strip().lower().rstrip(":")
        if key == "issued" and len(row) == 2:
            issued = row[1].strip()
        elif key == "location label" and len(row) == 2:
            label = row[1].strip()
        elif (
            key == "requested coordinate"
            and len(row) == 5
            and row[1].strip().lower() == "latitude"
            and row[3].strip().lower() == "longitude"
        ):
            latitude = _signed_decimal(row[2], "latitude")
            longitude = _signed_decimal(row[4], "longitude")
        elif (
            key == "nearest grid cell"
            and len(row) == 5
            and row[1].strip().lower() == "latitude"
            and row[3].strip().lower() == "longitude"
        ):
            nearest_latitude = _coordinate(row[2], longitude=False)
            nearest_longitude = _coordinate(row[4], longitude=True)
        elif key in {"requested coordinate", "nearest grid cell"}:
            _invalid(f"Malformed BoM {key} metadata row")
    return issued, label, latitude, longitude, nearest_latitude, nearest_longitude


def _header(rows: list[list[str]]) -> int:
    matches = [i for i, row in enumerate(rows) if len(row) >= 3 and row[:2] == ["Duration", "Duration in min"]]
    if len(matches) != 1:
        _invalid("BoM CSV requires one Duration,Duration in min,probabilities header")
    return matches[0]


def parse_bom_ifd_csv(
    raw: bytes,
    *,
    locator: str | None = None,
    encoding: str = "utf-8-sig",
    source_unit: RainfallUnit | None = None,
) -> BoMIFD:
    """Import a BoM Design Rainfall System depth/intensity CSV, offline and unmodified."""
    rows = _csv_rows(raw, encoding)
    header_index = _header(rows)
    preamble = rows[:header_index]
    table_kind, unit = _table_metadata(preamble, source_unit)
    header = rows[header_index]
    if any(not cell.strip() for cell in header[2:]):
        _invalid("Blank BoM probability column label")
    probabilities = tuple(_parse_probability(label) for label in header[2:])
    duration_labels: list[str] = []
    durations: list[int] = []
    values: list[tuple[Decimal, ...]] = []
    for i, row in enumerate(rows[header_index + 1 :], start=header_index + 2):
        if not any(cell.strip() for cell in row):
            if any(any(cell.strip() for cell in later) for later in rows[i:]):
                _invalid("Unexpected content after blank row in BoM matrix")
            break
        if len(row) != len(header):
            _invalid(f"Ragged BoM matrix at CSV row {i}")
        label = row[0].strip()
        duration = _duration(label)
        numeric_min = _decimal(row[1], "Duration in min", positive=True)
        if numeric_min != duration:
            _invalid(f"BoM duration mismatch at row {i}: {label!r} versus {row[1]!r} minutes")
        duration_labels.append(label)
        durations.append(duration)
        values.append(tuple(_decimal(value, f"BoM rainfall row {i}") for value in row[2:]))
    issued, label, lat, lon, nearest_lat, nearest_lon = _metadata(preamble)
    return BoMIFD(
        sha256=hashlib.sha256(raw).hexdigest(),
        raw_bytes=raw,
        locator=locator,
        issued=issued,
        label=label,
        latitude=lat,
        longitude=lon,
        nearest_latitude=nearest_lat,
        nearest_longitude=nearest_lon,
        rainfall_unit=unit,
        table_kind=table_kind,
        probabilities=probabilities,
        durations_min=tuple(durations),
        duration_labels=tuple(duration_labels),
        values=tuple(values),
        raw_preamble=tuple(tuple(row) for row in preamble),
    )


def read_bom_ifd_csv(path: Path, *, encoding: str = "utf-8-sig", source_unit: RainfallUnit | None = None) -> BoMIFD:
    """Read BoM CSV bytes without modifying them or making a network request."""
    with path.open("rb") as stream:
        raw = stream.read(MAX_BOM_CSV_BYTES + 1)
    return parse_bom_ifd_csv(raw, locator=str(path.absolute()), encoding=encoding, source_unit=source_unit)
