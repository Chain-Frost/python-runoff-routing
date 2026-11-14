"""Safe offline ARR point/areal temporal-pattern increment CSV and ZIP readers."""

from __future__ import annotations

import csv
import hashlib
import io
import re
import stat
import zipfile
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Literal, Never

from runoff_routing.arr_data import ARRFormatError

MAX_PATTERN_CSV_BYTES = 8 * 1024 * 1024
MAX_PATTERN_ZIP_BYTES = 32 * 1024 * 1024
MAX_ARCHIVE_ENTRIES = 128
MAX_ARCHIVE_UNCOMPRESSED_BYTES = 32 * 1024 * 1024
MAX_PATTERN_ROWS = 12000
MAX_PATTERN_INCREMENTS = 512
PatternKind = Literal["point", "areal"]
_HEADER_POINT = ("eventid", "duration", "timestep", "region", "aep", "increments")
_HEADER_AREAL = ("eventid", "duration", "timestep", "region", "area", "aep", "increments")
_HEADER_AREAL_NO_AEP = ("eventid", "duration", "timestep", "region", "area", "increments")
_BANDS = {"frequent", "intermediate", "rare", "very rare"}


def _invalid(message: str) -> Never:
    raise ARRFormatError(message)


def _number(value: str, *, field: str) -> Decimal:
    try:
        number = Decimal(value.strip())
    except InvalidOperation as exc:
        msg = f"Invalid {field}: {value!r}"
        raise ARRFormatError(msg) from exc
    if not number.is_finite() or number < 0 or number.adjusted() > 1000:
        _invalid(f"Nonfinite, negative or unsupported {field}: {value!r}")
    return number


def _positive_int(value: str, *, field: str) -> int:
    number = _number(value, field=field)
    if not number or number != number.to_integral_value() or number > 10080:
        _invalid(f"{field} requires positive whole minutes: {value!r}")
    return int(number)


@dataclass(frozen=True, slots=True)
class Pattern:
    """One original event in source order, without RORB pattern renumbering."""

    event_id: str
    duration_min: int
    timestep_min: int
    region: str
    aep_band: str | None
    increments_percent: tuple[Decimal, ...]
    area_bin: str | None = None

    def __post_init__(self) -> None:
        if not self.event_id or not self.region:
            _invalid("ARR temporal pattern event/region identity is empty")
        if self.aep_band is not None and self.aep_band not in _BANDS:
            _invalid("Unknown ARR temporal-pattern AEP bin")
        if self.duration_min <= 0 or self.timestep_min <= 0:
            _invalid("Temporal-pattern durations and timestep must be positive")
        if self.duration_min % self.timestep_min:
            _invalid("Temporal-pattern duration must be divisible by timestep")
        if not self.increments_percent or len(self.increments_percent) > MAX_PATTERN_INCREMENTS:
            _invalid("Temporal-pattern increment count missing or unbounded")
        if len(self.increments_percent) != self.duration_min // self.timestep_min:
            _invalid("Temporal-pattern increment count differs from duration/timestep")
        if any(not n.is_finite() or n < 0 or n > 100 for n in self.increments_percent):
            _invalid("Invalid ARR temporal-pattern increment percentage")
        if self.area_bin is not None and not self.area_bin.strip():
            _invalid("Empty ARR areal temporal-pattern bin")


@dataclass(frozen=True, slots=True)
class PatternSource:
    """Each CSV source hash is independently traceable, even within a ZIP archive."""

    locator: str
    sha256: str
    byte_length: int


@dataclass(frozen=True, slots=True)
class PatternSet:
    """One ordered collection of ARR temporal patterns; source ZIP/CSV bytes preserved."""

    kind: PatternKind
    source_sha256: str
    raw_bytes: bytes
    source_locator: str | None
    members: tuple[PatternSource, ...]
    patterns: tuple[Pattern, ...]
    rounding_budget_percent: Decimal

    def __post_init__(self) -> None:
        if hashlib.sha256(self.raw_bytes).hexdigest() != self.source_sha256:
            _invalid("ARR pattern source SHA-256 mismatch")
        if not self.patterns or len(self.patterns) > MAX_PATTERN_ROWS:
            _invalid("ARR temporal-pattern set is empty or excessive")
        if (
            not self.rounding_budget_percent.is_finite()
            or self.rounding_budget_percent < 0
            or self.rounding_budget_percent > Decimal("0.5")
        ):
            _invalid("ARR temporal pattern rounding budget must be between 0 and 0.5 percentage points")
        ids = [(p.event_id, p.duration_min, p.aep_band, p.area_bin, p.region) for p in self.patterns]
        if len(ids) != len(set(ids)):
            _invalid("Duplicate temporal-pattern event ID in the same bin, duration and region")
        for event in self.patterns:
            if self.kind == "point" and (event.area_bin is not None or event.aep_band is None):
                _invalid("Point temporal patterns require an AEP bin and must not have an areal bin")
            if self.kind == "areal" and event.area_bin is None:
                _invalid("Areal temporal patterns require the source area bin")
            if abs(sum(event.increments_percent) - Decimal(100)) > self.rounding_budget_percent:
                _invalid(f"Temporal-pattern percentages do not sum to 100 within declared budget: {event.event_id}")


def _decode_csv(raw: bytes, encoding: str) -> list[list[str]]:
    if not raw or len(raw) > MAX_PATTERN_CSV_BYTES:
        _invalid("Temporal-pattern CSV is empty or exceeds limit")
    if encoding not in {"utf-8-sig", "cp1252"}:
        _invalid("Temporal-pattern CSV encoding must be UTF-8 or explicit cp1252")
    try:
        source = raw.decode(encoding)
    except UnicodeDecodeError as exc:
        msg = f"Temporal-pattern CSV cannot decode as {encoding}"
        raise ARRFormatError(msg) from exc
    try:
        return list(csv.reader(io.StringIO(source, newline=""), strict=True))
    except csv.Error as exc:
        msg = "Malformed quoted temporal-pattern CSV"
        raise ARRFormatError(msg) from exc


def _csv_patterns(raw: bytes, *, kind: PatternKind, encoding: str) -> tuple[Pattern, ...]:
    rows = _decode_csv(raw, encoding)
    if not rows or len(rows) > MAX_PATTERN_ROWS + 1:
        _invalid("Missing/oversized ARR temporal-pattern CSV")
    header = tuple(part.strip().lower().replace(" ", "") for part in rows[0])
    supported = (_HEADER_AREAL, _HEADER_AREAL_NO_AEP) if kind == "areal" else (_HEADER_POINT,)
    expected = next(
        (
            candidate
            for candidate in supported
            if header[: len(candidate)] == candidate and not any(header[len(candidate) :])
        ),
        None,
    )
    if expected is None:
        _invalid("Unrecognised ARR temporal-pattern CSV column order / area-bin layout")
    increments_index = len(expected) - 1
    patterns: list[Pattern] = []
    for index, row in enumerate(rows[1:], start=2):
        if not any(cell.strip() for cell in row):
            _invalid(f"Blank row inside temporal-pattern CSV at line {index}")
        if len(row) <= increments_index or not all(row[i].strip() for i in range(increments_index)):
            _invalid(f"Missing temporal-pattern metadata at line {index}")
        duration_min = _positive_int(row[1], field="Duration")
        timestep_min = _positive_int(row[2], field="TimeStep")
        band: str | None = None if expected == _HEADER_AREAL_NO_AEP else row[increments_index - 1].strip().lower()
        if band is not None and band not in _BANDS:
            _invalid(f"Unknown ARR AEP bin at line {index}: {band!r}")
        increment_cells = row[increments_index:]
        if not increment_cells or not increment_cells[0].strip():
            _invalid(f"Missing first temporal-pattern increment at line {index}")
        while increment_cells and not increment_cells[-1].strip():
            increment_cells.pop()
        if any(not cell.strip() for cell in increment_cells):
            _invalid(f"Missing interior temporal-pattern increment at line {index}")
        increments = tuple(_number(x, field="increment") for x in increment_cells)
        patterns.append(
            Pattern(
                event_id=row[0].strip(),
                duration_min=duration_min,
                timestep_min=timestep_min,
                region=row[3].strip(),
                aep_band=band,
                increments_percent=increments,
                area_bin=row[4].strip() if kind == "areal" else None,
            )
        )
    return tuple(patterns)


def parse_pattern_csv(
    raw: bytes,
    *,
    kind: PatternKind,
    locator: str | None = None,
    encoding: str = "utf-8-sig",
    rounding_budget_percent: Decimal = Decimal(0),
) -> PatternSet:
    """Import a single ARR Increments.csv (point or areal explicitly selected)."""
    patterns = _csv_patterns(raw, kind=kind, encoding=encoding)
    return PatternSet(
        kind=kind,
        source_sha256=hashlib.sha256(raw).hexdigest(),
        raw_bytes=raw,
        source_locator=locator,
        members=(PatternSource(locator or "<bytes>", hashlib.sha256(raw).hexdigest(), len(raw)),),
        patterns=patterns,
        rounding_budget_percent=rounding_budget_percent,
    )


def _safe_zip_name(name: str) -> None:
    if (
        not name
        or name.startswith(("/", "\\"))
        or "\\" in name
        or "\x00" in name
        or re.match(r"^[A-Za-z]:", name)
        or any(segment in {"", ".", ".."} for segment in name.split("/"))
    ):
        _invalid(f"Unsafe temporal-pattern ZIP member name: {name!r}")


def _zip_infos(archive: zipfile.ZipFile) -> tuple[zipfile.ZipInfo, ...]:
    infos = tuple(archive.infolist())
    if not infos or len(infos) > MAX_ARCHIVE_ENTRIES:
        _invalid("Temporal-pattern ZIP entry count missing/excessive")
    total = 0
    seen: set[str] = set()
    for info in infos:
        # ZipInfo.filename normalises backslashes on Windows; orig_filename
        # retains the unmodified central-directory entry for security checks.
        raw_name = info.orig_filename
        _safe_zip_name(raw_name.rstrip("/") if info.is_dir() else raw_name)
        key = raw_name.casefold()
        if key in seen:
            _invalid(f"Duplicate temporal-pattern archive member {info.filename!r}")
        seen.add(key)
        if stat.S_ISLNK(info.external_attr >> 16) or info.flag_bits & 0x1:
            _invalid("Links and encrypted files are prohibited in ARR temporal-pattern ZIP")
        if info.is_dir():
            continue
        if info.file_size > MAX_PATTERN_CSV_BYTES:
            _invalid("Temporal-pattern ZIP member exceeds 8 MiB")
        if info.file_size > 1024 and info.file_size > 200 * max(1, info.compress_size):
            _invalid("Temporal-pattern ZIP member has unsafe compression ratio")
        total += info.file_size
        if total > MAX_ARCHIVE_UNCOMPRESSED_BYTES:
            _invalid("Temporal-pattern ZIP uncompressed total exceeds 32 MiB")
    return infos


def parse_pattern_zip(
    raw: bytes,
    *,
    kind: PatternKind,
    locator: str | None = None,
    encoding: str = "utf-8-sig",
    rounding_budget_percent: Decimal = Decimal(0),
) -> PatternSet:
    """Read source-order *Increments.csv members, never extracting archive files to disk."""
    if not raw or len(raw) > MAX_PATTERN_ZIP_BYTES:
        _invalid("ARR temporal-pattern ZIP exceeds 32 MiB or is empty")
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            infos = _zip_infos(archive)
            patterns: list[Pattern] = []
            sources: list[PatternSource] = []
            for info in infos:
                if info.is_dir() or not info.filename.lower().endswith("increments.csv"):
                    continue
                payload = archive.read(info)
                sources.append(PatternSource(info.filename, hashlib.sha256(payload).hexdigest(), len(payload)))
                patterns.extend(_csv_patterns(payload, kind=kind, encoding=encoding))
    except (zipfile.BadZipFile, RuntimeError, EOFError, OSError) as exc:
        msg = "Invalid or unsupported ARR temporal-pattern ZIP archive"
        raise ARRFormatError(msg) from exc
    if not sources:
        _invalid("ARR temporal-pattern ZIP has no *Increments.csv members")
    return PatternSet(
        kind=kind,
        source_sha256=hashlib.sha256(raw).hexdigest(),
        raw_bytes=raw,
        source_locator=locator,
        members=tuple(sources),
        patterns=tuple(patterns),
        rounding_budget_percent=rounding_budget_percent,
    )


def read_pattern_file(
    path: Path,
    *,
    kind: PatternKind,
    encoding: str = "utf-8-sig",
    rounding_budget_percent: Decimal = Decimal(0),
) -> PatternSet:
    """Read local ARR CSV or ZIP with strict size bounds and no extraction/network activity."""
    limit = MAX_PATTERN_ZIP_BYTES if path.suffix.lower() == ".zip" else MAX_PATTERN_CSV_BYTES
    with path.open("rb") as stream:
        raw = stream.read(limit + 1)
    locator = str(path.absolute())
    if path.suffix.lower() == ".zip":
        return parse_pattern_zip(
            raw, kind=kind, locator=locator, encoding=encoding, rounding_budget_percent=rounding_budget_percent
        )
    if path.suffix.lower() == ".csv":
        return parse_pattern_csv(
            raw, kind=kind, locator=locator, encoding=encoding, rounding_budget_percent=rounding_budget_percent
        )
    _invalid("ARR temporal patterns must be supplied as CSV or ZIP")
