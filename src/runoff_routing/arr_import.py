"""Strict offline ARR Data Hub JSON and TXT intake; never downloads referenced files."""

from __future__ import annotations

import hashlib
import json
import re
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import cast

from runoff_routing.arr_data import (
    MAX_SOURCE_BYTES,
    ARRDocument,
    ARRFormatError,
    Baseline,
    DataHubSource,
    ExportFormat,
    IFDDataset,
    QueryLocation,
)

BASELINES: dict[str, Baseline] = {
    "Default Current (2030) Baseline": "current_2030",
    "Default Historical (1961-1990) Baseline": "historical_1961_1990",
    "Default Native Baseline": "native",
}
TXT_TABLE_MARKERS = {
    "Default Current (2030) Baseline": "RECCURRENTBASELINE",
    "Default Historical (1961-1990) Baseline": "RECHISTORICALBASELINE",
    "Default Native Baseline": "RECNATIVEBASELINE",
}
_DURATION_TXT = re.compile(r"^(\d+)\s+\((?:\d+(?:\.\d+)?)\)$")
_RELEASE_YEAR = re.compile(r"^[^,;+()]+ \((19\d\d|20\d\d)\)$")


def _problem(message: str) -> ARRFormatError:
    return ARRFormatError(message)


def _readable(raw: bytes) -> str:
    if not raw or len(raw) > MAX_SOURCE_BYTES:
        raise _problem("ARR input is empty or exceeds the 8 MiB offline intake limit")
    try:
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise _problem("ARR input must be UTF-8 (optional UTF-8 BOM)") from exc


def _unique_pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise _problem(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def _bad_constant(token: str) -> None:
    raise _problem(f"Nonfinite JSON constant: {token}")


def _object(value: object, path: str) -> dict[str, object]:
    if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
        raise _problem(f"Expected JSON object at {path}")
    return cast("dict[str, object]", value)


def _array(value: object, path: str) -> list[object]:
    if not isinstance(value, list):
        raise _problem(f"Expected JSON array at {path}")
    return cast("list[object]", value)


def _number(value: object, path: str, *, from_text: bool = False) -> Decimal:
    if isinstance(value, bool):
        raise _problem(f"Boolean is not a number at {path}")
    if isinstance(value, int | Decimal) or (from_text and isinstance(value, str)):
        try:
            number = Decimal(str(value))
        except InvalidOperation as exc:
            raise _problem(f"Invalid decimal at {path}") from exc
        if number.is_finite() and -1000 <= number.adjusted() <= 1000:
            return number
    raise _problem(f"Expected a finite decimal at {path}")


def _duration(value: object, path: str) -> int:
    number = _number(value, path)
    if number <= 0 or number != number.to_integral_value():
        raise _problem(f"Duration must be a positive whole number of minutes at {path}")
    return int(number)


def _location(fields: dict[str, object], *, from_text: bool = False) -> QueryLocation:
    try:
        lat = _number(fields["Latitude"], "input_data.Latitude", from_text=from_text)
        lon = _number(fields["Longitude"], "input_data.Longitude", from_text=from_text)
    except KeyError as exc:
        raise _problem(f"Missing ARR input coordinate {exc.args[0]}") from exc
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        raise _problem("ARR geographic input coordinates out of WGS84 bounds")
    centroid_value = fields.get("Centroid_Used")
    if centroid_value is not None and not isinstance(centroid_value, str):
        raise _problem("Centroid_Used must be a text label")
    outlet_lat = fields.get("Outlet Latitude")
    outlet_lon = fields.get("Outlet Longitude")
    if (outlet_lat is None) != (outlet_lon is None):
        raise _problem("ARR outlet requires both latitude and longitude")
    outlet_latitude = _number(outlet_lat, "Outlet Latitude", from_text=from_text) if outlet_lat is not None else None
    outlet_longitude = _number(outlet_lon, "Outlet Longitude", from_text=from_text) if outlet_lon is not None else None
    if outlet_latitude is not None and not (-90 <= outlet_latitude <= 90):
        raise _problem("ARR outlet latitude outside WGS84 bounds")
    if outlet_longitude is not None and not (-180 <= outlet_longitude <= 180):
        raise _problem("ARR outlet longitude outside WGS84 bounds")
    return QueryLocation(
        latitude=lat,
        longitude=lon,
        centroid_used=centroid_value,
        outlet_latitude=outlet_latitude,
        outlet_longitude=outlet_longitude,
        raw_fields=tuple((key, str(value)) for key, value in fields.items()),
    )


def _make_source(
    raw: bytes,
    fmt: ExportFormat,
    version: str | None,
    locator: str | None,
    captured_at: str | None,
    compatibility_profile: str | None = None,
) -> DataHubSource:
    return DataHubSource(fmt, version, hashlib.sha256(raw).hexdigest(), len(raw), locator, captured_at, compatibility_profile)


def _ifd_table(
    name: str,
    durations: tuple[int, ...],
    aeps: tuple[Decimal, ...],
    depths: tuple[tuple[Decimal, ...], ...],
    *,
    metadata: tuple[tuple[str, str], ...] = (),
) -> IFDDataset:
    baseline = BASELINES.get(name)
    if baseline is None:
        raise _problem(f"Unrecognised RecIFD baseline {name!r}; refuse to infer a scenario")
    datasets = next((value for key, value in metadata if key == "Datasets"), None)
    # A release year is only recorded when a single source dataset explicitly names it.
    match = _RELEASE_YEAR.fullmatch(datasets) if datasets else None
    year = match.group(1) if match else None
    return IFDDataset(
        source_layer="RecIFD",
        name=name,
        baseline=baseline,
        durations_min=durations,
        aep_percent=aeps,
        depths_mm=depths,
        provider_datasets=datasets,
        release_year=int(year) if year is not None else None,
        raw_metadata=metadata,
    )


def _json_table(name: str, value: object) -> IFDDataset:
    table = _object(value, f"RecIFD.{name}")
    if set(table) != {"index", "columns", "data"}:
        raise _problem(f"RecIFD.{name}: expected exactly index, columns, data")
    durations = tuple(_duration(v, f"{name}.index") for v in _array(table["index"], "index"))
    aeps = tuple(_number(v, f"{name}.columns") for v in _array(table["columns"], "columns"))
    rows = _array(table["data"], f"{name}.data")
    depths = tuple(
        tuple(_number(v, f"{name}.data[{i}]") for v in _array(row, f"{name}.data[{i}]"))
        for i, row in enumerate(rows)
    )
    return _ifd_table(name, durations, aeps, depths)


def parse_arr_json(
    raw: bytes, *, locator: str | None = None, captured_at: str | None = None
) -> ARRDocument:
    """Parse ARR 2026v1 RecIFD only, retaining original bytes and skipped layer names."""
    text = _readable(raw)
    try:
        decoded = cast(
            "object", json.loads(text, parse_float=Decimal, object_pairs_hook=_unique_pairs, parse_constant=_bad_constant)
        )
    except (json.JSONDecodeError, UnicodeError, RecursionError) as exc:
        raise _problem("Malformed ARR JSON") from exc
    root = _object(decoded, "root")
    version = root.get("datahub_version")
    if version != "2026v1":
        raise _problem(f"Unsupported ARR JSON Data Hub version: {version!r}")
    location = _location(_object(root.get("input_data"), "input_data"))
    layers = _object(root.get("layers"), "layers")
    ifd_tables = _object(layers["RecIFD"], "layers.RecIFD") if "RecIFD" in layers else {}
    if len(ifd_tables) > 64:
        raise _problem("Too many RecIFD tables")
    datasets = tuple(_json_table(name, value) for name, value in ifd_tables.items())
    return ARRDocument(
        source=_make_source(raw, "json", "2026v1", locator, captured_at),
        location=location,
        ifd_datasets=datasets,
        absent_layers=("RecIFD",) if "RecIFD" not in layers else (),
        unprocessed_layers=tuple(key for key in layers if key != "RecIFD"),
        raw_bytes=raw,
        capability="ifd_validated" if datasets else "location_only",
    )


def _marked(lines: list[str], opening: str, closing: str, *, required: bool) -> list[str] | None:
    if lines.count(opening) == 0 and lines.count(closing) == 0 and not required:
        return None
    if lines.count(opening) != 1 or lines.count(closing) != 1:
        raise _problem(f"Expected exactly one {opening}/{closing} section")
    start, end = lines.index(opening), lines.index(closing)
    if start >= end:
        raise _problem(f"Misordered ARR section {opening}")
    return lines[start + 1 : end]


def _input_section(lines: list[str], *, legacy: bool) -> QueryLocation:
    content = _marked(lines, "[INPUTDATA]", "[END_INPUTDATA]", required=True)
    if content is None:
        raise _problem("Missing INPUTDATA section")
    fields: dict[str, object] = {}
    for line in content:
        if not line.strip():
            continue
        if "," not in line or line.startswith("["):
            raise _problem(f"Malformed INPUTDATA field {line!r}")
        key, value = line.split(",", 1)
        if key in fields:
            raise _problem(f"Duplicate INPUTDATA key {key}")
        if legacy and key not in {"Latitude", "Longitude", "Centroid_Used"}:
            raise _problem(f"Unsupported legacy INPUTDATA field {key}")
        fields[key] = value
    return _location(fields, from_text=True)


def _txt_duration(value: str) -> int:
    match = _DURATION_TXT.fullmatch(value.strip())
    if match is None:
        raise _problem(f"Unsupported TXT duration/hour label {value!r}")
    return _duration(int(match.group(1)), "TXT duration")


def _txt_ifd_table(name: str, section: list[str]) -> IFDDataset:
    marker = TXT_TABLE_MARKERS[name]
    if len(section) < 4 or section[0] != f"[{marker}]" or section[-1] != f"[END_{marker}]":
        raise _problem(f"Invalid TXT baseline section for {name}")
    if section[1].split(",", 1)[0] != r"min (h)\AEP(%)":
        raise _problem(f"Unknown TXT IFD axis units in {name}")
    header = section[1].split(",")
    aeps = tuple(_number(part, f"{name}.AEP", from_text=True) for part in header[1:])
    meta_marker = f"[{marker}_META]"
    if section.count(meta_marker) != 1:
        raise _problem(f"Missing or duplicate IFD metadata marker in {name}")
    split = section.index(meta_marker)
    rows: list[tuple[Decimal, ...]] = []
    durations: list[int] = []
    for line in section[2:split]:
        parts = line.split(",")
        durations.append(_txt_duration(parts[0]))
        rows.append(tuple(_number(v, f"{name}.depth", from_text=True) for v in parts[1:]))
    metadata: list[tuple[str, str]] = []
    for line in section[split + 1 : -1]:
        if "," not in line or line.startswith("["):
            raise _problem(f"Invalid IFD metadata in {name}")
        key, value = line.split(",", 1)
        metadata.append((key, value))
    return _ifd_table(name, tuple(durations), aeps, tuple(rows), metadata=tuple(metadata))


def _txt_recifd(lines: list[str]) -> tuple[IFDDataset, ...]:
    content = _marked(lines, "[RECIFD]", "[END_RECIFD]", required=False)
    if content is None:
        return ()
    compact = [line.strip() for line in content if line.strip()]
    result: list[IFDDataset] = []
    cursor = 0
    while cursor < len(compact):
        name = compact[cursor]
        marker = TXT_TABLE_MARKERS.get(name)
        if marker is None:
            raise _problem(f"Unrecognised RecIFD TXT heading {name!r}")
        end_tag = f"[END_{marker}]"
        try:
            end = compact.index(end_tag, cursor + 1)
        except ValueError as exc:
            raise _problem(f"Missing RecIFD TXT terminator {end_tag}") from exc
        result.append(_txt_ifd_table(name, compact[cursor + 1 : end + 1]))
        cursor = end + 1
    if len({table.name for table in result}) != len(result):
        raise _problem("Duplicate RecIFD TXT baseline")
    return tuple(result)


def parse_arr_txt(
    raw: bytes,
    *,
    locator: str | None = None,
    captured_at: str | None = None,
    legacy_profile: str | None = None,
) -> ARRDocument:
    """Read 2026v1 IFD TXT or opt-in location-only legacy 2019 TXT profile."""
    lines = [line.strip() for line in _readable(raw).splitlines()]
    if not lines or not lines[0].startswith("Results - ARR Data Hub"):
        raise _problem("Unrecognised ARR TXT header")
    payload = _marked(lines, "[STARTTXT]", "[ENDTXT]", required=True)
    if payload is None:
        raise _problem("Missing STARTTXT section")
    start_pos, end_pos = lines.index("[STARTTXT]"), lines.index("[ENDTXT]")
    if any(line for line in lines[end_pos + 1 :]):
        raise _problem("Trailing content after ENDTXT")
    version_lines = [line for line in lines[1:start_pos] if line.startswith("Data Hub Version,")]
    if len(version_lines) > 1:
        raise _problem("Ambiguous TXT Data Hub version")
    version = version_lines[0].split(",", 1)[1] if version_lines else None
    if version == "2026v1":
        if legacy_profile is not None:
            raise _problem("Legacy profile cannot reinterpret ARR 2026v1 TXT")
    elif legacy_profile == "2019v1" and version in (None, "2019v1"):
        pass  # Unversioned original remains unversioned; profile is recorded separately.
    else:
        raise _problem(f"Unsupported/undeclared ARR TXT version {version!r}; explicit legacy profile required")
    is_legacy = legacy_profile == "2019v1"
    location = _input_section(payload, legacy=is_legacy)
    if is_legacy:
        allowed = {"[STARTTXT]", "[ENDTXT]", "[INPUTDATA]", "[END_INPUTDATA]"}
        other = {line for line in payload if line.startswith("[") and line.endswith("]")} - allowed
        if other:
            raise _problem(f"Legacy TXT sections not characterised: {sorted(other)}")
        datasets: tuple[IFDDataset, ...] = ()
    else:
        if any(line.startswith("[RECIFD_") for line in payload):
            raise _problem("Unknown RECIFD TXT variant requires a reviewed format contract")
        datasets = _txt_recifd(payload)
    recognised = {"STARTTXT", "INPUTDATA", "RECIFD", *TXT_TABLE_MARKERS.values()}
    unprocessed = tuple(
        marker
        for line in payload
        if line.startswith("[")
        and line.endswith("]")
        and not line.startswith("[END_")
        and not line.endswith("_META]")
        if (marker := line[1:-1]) not in recognised
    )
    return ARRDocument(
        source=_make_source(raw, "txt", version, locator, captured_at, "2019v1_input_only" if is_legacy else None),
        location=location,
        ifd_datasets=datasets,
        absent_layers=("RecIFD",) if "[RECIFD]" not in payload else (),
        unprocessed_layers=unprocessed,
        raw_bytes=raw,
        capability="ifd_validated" if datasets else "location_only",
    )


def read_arr_file(
    path: Path,
    *,
    locator: str | None = None,
    captured_at: str | None = None,
    legacy_profile: str | None = None,
) -> ARRDocument:
    """Read at most 8 MiB from a local file; preserve exact bytes and path spelling."""
    with path.open("rb") as stream:
        raw = stream.read(MAX_SOURCE_BYTES + 1)
    if len(raw) > MAX_SOURCE_BYTES:
        raise _problem("ARR file exceeds 8 MiB offline intake limit")
    source_locator = locator if locator is not None else str(path.absolute())
    if path.suffix.lower() == ".json":
        if legacy_profile is not None:
            raise _problem("Legacy TXT profile is not valid for JSON")
        return parse_arr_json(raw, locator=source_locator, captured_at=captured_at)
    if path.suffix.lower() in {".txt", ".text"}:
        return parse_arr_txt(raw, locator=source_locator, captured_at=captured_at, legacy_profile=legacy_profile)
    raise _problem(f"Unsupported ARR file extension {path.suffix!r}; ZIP and CSV are later workpacks")
