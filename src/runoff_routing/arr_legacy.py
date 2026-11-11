"""Explicit ARR2016-era Data Hub TXT profile; inputs only, never event generation."""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from typing import Literal, Never

from runoff_routing.arr_data import (
    ARRDocument,
    ARRFormatError,
    DataHubSource,
    LegacyARF,
    LegacyPreburst,
    LegacyRawSection,
    LegacyStormLoss,
    LegacyTPRegion,
    QueryLocation,
)

# These describe historical TXT section markers, not a current ARR/IFD method.
_LEGACY_SECTION_TAGS = frozenset(
    {
        "RIVREG",
        "LONGARF",
        "LOSSES",
        "TP",
        "ATP",
        "BOMIFD",
        "PREBURST",
        "PREBURST10",
        "PREBURST25",
        "PREBURST75",
        "PREBURST90",
        "CCF",
        "BASEFLOW",
    }
)
_PREBURST_PERCENTILES: dict[str, Literal[10, 25, 50, 75, 90]] = {
    "PREBURST": 50,
    "PREBURST10": 10,
    "PREBURST25": 25,
    "PREBURST75": 75,
    "PREBURST90": 90,
}
_DURATION = re.compile(r"^(\d+)\s*\(\s*\d+(?:\.\d+)?\s*\)$")
_DEPTH_RATIO = re.compile(r"^([^()]+?)\s*\(\s*([^()]+)\s*\)$")


def _error(message: str) -> Never:
    raise ARRFormatError(message)


def _decimal(value: str, path: str, *, nonnegative: bool = True) -> Decimal:
    try:
        number = Decimal(value.strip())
    except InvalidOperation:
        _error(f"Invalid legacy decimal at {path}: {value!r}")
    if not number.is_finite() or number.adjusted() > 1000 or (nonnegative and number < 0):
        _error(f"Nonfinite or out-of-range legacy decimal at {path}: {value!r}")
    return number


def _pairs(lines: list[str], context: str) -> tuple[tuple[str, str], ...]:
    result: list[tuple[str, str]] = []
    seen: set[str] = set()
    for line in lines:
        if not line.strip():
            continue
        if "," not in line:
            # Long 'Note' entries occasionally wrap in printed/exported copies.
            if context.endswith("metadata") and result and result[-1][0].lower() == "note":
                key, prior = result[-1]
                result[-1] = (key, f"{prior} {line.strip()}")
                continue
            _error(f"Malformed legacy {context} field: {line!r}")
        key, value = (item.strip() for item in line.split(",", 1))
        if not key or key.casefold() in seen:
            _error(f"Empty/duplicate legacy {context} field: {key!r}")
        seen.add(key.casefold())
        result.append((key, value))
    return tuple(result)


def _select(fields: tuple[tuple[str, str], ...], key: str) -> str | None:
    return next((value for name, value in fields if name.casefold() == key.casefold()), None)


def _require(fields: tuple[tuple[str, str], ...], key: str, context: str) -> str:
    result = _select(fields, key)
    if result is None or not result:
        _error(f"Missing {context} field {key!r}")
    return result


def _only(fields: tuple[tuple[str, str], ...], allowed: set[str], context: str) -> None:
    unexpected = {key for key, _ in fields if key.casefold() not in allowed}
    if unexpected:
        _error(f"Uncharacterised legacy {context} fields: {sorted(unexpected)}")


def _location(lines: list[str]) -> QueryLocation:
    pairs = _pairs(lines, "INPUTDATA")
    _only(pairs, {"latitude", "longitude", "centroid_used"}, "INPUTDATA")
    latitude = _decimal(_require(pairs, "Latitude", "INPUTDATA"), "Latitude", nonnegative=False)
    longitude = _decimal(_require(pairs, "Longitude", "INPUTDATA"), "Longitude", nonnegative=False)
    if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
        _error("Legacy input latitude/longitude outside EPSG:4326 bounds")
    return QueryLocation(latitude, longitude, _select(pairs, "Centroid_Used"), raw_fields=pairs)


def _block(lines: list[str], tag: str) -> tuple[list[str], tuple[tuple[str, str], ...]]:
    meta = f"[{tag}_META]"
    if lines.count(meta) > 1:
        _error(f"Duplicate legacy {tag} metadata marker")
    if meta in lines:
        boundary = lines.index(meta)
        content, metadata = lines[:boundary], _pairs(lines[boundary + 1 :], f"{tag} metadata")
    else:
        content, metadata = lines, ()
    if any(line.startswith("[") for line in content):
        _error(f"Unexpected bracket marker inside legacy {tag}")
    return content, metadata


def _loss(fields: tuple[tuple[str, str], ...], metadata: tuple[tuple[str, str], ...]) -> LegacyStormLoss:
    _only(fields, {"id", "storm initial losses (mm)", "storm continuing losses (mm/h)"}, "LOSSES")
    il = _decimal(_require(fields, "Storm Initial Losses (mm)", "LOSSES"), "LOSSES IL", nonnegative=False)
    cl = _decimal(_require(fields, "Storm Continuing Losses (mm/h)", "LOSSES"), "LOSSES CL", nonnegative=False)
    if (il < 0 and il != -50) or (cl < 0 and cl != -50):
        _error("Negative legacy storm loss other than -50 missing-data sentinel")
    return LegacyStormLoss(
        None if il == -50 else il, None if cl == -50 else cl, _select(fields, "ID"), metadata, fields
    )


def _arf(fields: tuple[tuple[str, str], ...], metadata: tuple[tuple[str, str], ...]) -> LegacyARF:
    expected = tuple("abcdefghi")
    _only(fields, {"zone", *expected}, "LONGARF")
    zone = _require(fields, "Zone", "LONGARF")
    coeff = tuple(
        (key, _decimal(_require(fields, key, "LONGARF"), f"ARF.{key}", nonnegative=False)) for key in expected
    )
    return LegacyARF(zone, coeff, metadata, fields)


def _tp(fields: tuple[tuple[str, str], ...], metadata: tuple[tuple[str, str], ...], tag: str) -> LegacyTPRegion:
    _only(fields, {"code", "label", "arealabel", "per_intersect"}, tag)
    code = _require(fields, "code", tag)
    label_key = "Label" if tag == "TP" else "arealabel"
    label = _require(fields, label_key, tag)
    if tag == "TP" and _select(fields, "arealabel") is not None:
        _error("Areal label in legacy point TP section")
    if tag == "ATP" and _select(fields, "Label") is not None:
        _error("Point label in legacy areal TP section")
    intersection = _select(fields, "per_intersect")
    fraction = _decimal(intersection, f"{tag}.per_intersect") if intersection is not None else None
    if fraction is not None and fraction > 1:
        _error("Legacy TP per_intersect exceeds fraction 1")
    return LegacyTPRegion("point" if tag == "TP" else "areal", code, label, fraction, metadata, fields)


def _trim_row(line: str) -> list[str]:
    parts = [part.strip() for part in line.split(",")]
    if parts and not parts[-1]:
        parts.pop()
    if not parts or any(not part for part in parts):
        _error("Empty legacy preburst cell or duration")
    return parts


def _axes_and_rows(
    lines: list[str], tag: str
) -> tuple[tuple[int, ...], tuple[Decimal, ...], tuple[tuple[Decimal, ...], ...], tuple[tuple[Decimal, ...], ...]]:
    if len(lines) < 2:
        _error(f"Empty legacy {tag} table")
    header = _trim_row(lines[0])
    if header[0] != r"min (h)\AEP(%)":
        _error(f"Unknown legacy {tag} AEP/duration axis units")
    aeps = tuple(_decimal(value, f"{tag}.AEP") for value in header[1:])
    if not aeps or any(not (0 < aep <= 100) for aep in aeps) or len(set(aeps)) != len(aeps):
        _error(f"Empty/duplicate/invalid legacy {tag} AEP percentages")
    durations: list[int] = []
    depths: list[tuple[Decimal, ...]] = []
    ratios: list[tuple[Decimal, ...]] = []
    for raw_line in lines[1:]:
        cells = _trim_row(raw_line)
        match = _DURATION.fullmatch(cells[0])
        if match is None or int(match[1]) <= 0:
            _error(f"Invalid legacy {tag} duration {cells[0]!r}")
        if len(cells) != len(aeps) + 1:
            _error(f"Legacy {tag} column count mismatch at {cells[0]}")
        durations.append(int(match[1]))
        values = [_DEPTH_RATIO.fullmatch(value) for value in cells[1:]]
        if any(value is None for value in values):
            _error(f"Legacy {tag} expects explicit depth (ratio) cells")
        parsed = [value for value in values if value is not None]
        depths.append(tuple(_decimal(value[1], f"{tag}.depth") for value in parsed))
        ratios.append(tuple(_decimal(value[2], f"{tag}.ratio") for value in parsed))
    if len(set(durations)) != len(durations) or len(durations) > 1024 or len(aeps) > 128:
        _error(f"Duplicate or unbounded legacy {tag} duration/AEP axis")
    return tuple(durations), aeps, tuple(depths), tuple(ratios)


def _collect_sections(payload: list[str]) -> dict[str, list[str]]:
    """Section scanner: reject unknown bracket markers but ignore display headings."""
    sections: dict[str, list[str]] = {}
    cursor = 0
    while cursor < len(payload):
        line = payload[cursor]
        if not line or not line.startswith("["):
            if "," in line:
                _error(f"Legacy field outside a marked section: {line!r}")
            cursor += 1
            continue
        if not line.endswith("]"):
            _error(f"Malformed legacy marker {line!r}")
        tag = line[1:-1]
        if tag != "INPUTDATA" and tag not in _LEGACY_SECTION_TAGS:
            _error(f"Unknown legacy section marker {line}")
        if tag in sections:
            _error(f"Duplicate legacy section [{tag}]")
        terminator = f"[END_{tag}]"
        try:
            end = payload.index(terminator, cursor + 1)
        except ValueError:
            _error(f"Missing legacy section terminator {terminator}")
        sections[tag] = payload[cursor + 1 : end]
        cursor = end + 1
    return sections


def parse_legacy_sections(
    raw: bytes, payload: list[str], *, source: DataHubSource, embedded_patterns: bool
) -> ARRDocument:
    """Validate source-era layers without supplying an IFD, RORB storm or loss policy."""
    sections = _collect_sections(payload)
    if "INPUTDATA" not in sections:
        _error("Missing legacy INPUTDATA section")
    location = _location(sections.pop("INPUTDATA"))
    losses: LegacyStormLoss | None = None
    arf: LegacyARF | None = None
    regions: list[LegacyTPRegion] = []
    preburst: list[LegacyPreburst] = []
    others: list[LegacyRawSection] = []
    for tag, lines in sections.items():
        content, metadata = _block(lines, tag)
        if tag == "LOSSES":
            losses = _loss(_pairs(content, tag), metadata)
        elif tag == "LONGARF":
            arf = _arf(_pairs(content, tag), metadata)
        elif tag in {"TP", "ATP"}:
            regions.append(_tp(_pairs(content, tag), metadata, tag))
        elif tag in _PREBURST_PERCENTILES:
            durations, aeps, depths, ratios = _axes_and_rows([line for line in content if line], tag)
            preburst.append(LegacyPreburst(_PREBURST_PERCENTILES[tag], tag, durations, aeps, depths, ratios, metadata))
        else:
            # A known layer is not necessarily a safely interpretable numeric dataset.
            others.append(LegacyRawSection(tag, tuple(content), metadata))
    validated = bool(losses or arf or regions or preburst)
    return ARRDocument(
        source=source,
        location=location,
        ifd_datasets=(),
        absent_layers=("RecIFD",),
        unprocessed_layers=tuple(item.tag for item in others) + (("EmbeddedPatterns",) if embedded_patterns else ()),
        raw_bytes=raw,
        capability="legacy_layers_validated" if validated else "location_only",
        legacy_losses=losses,
        legacy_arf=arf,
        legacy_tp_regions=tuple(regions),
        legacy_preburst=tuple(preburst),
        legacy_unprocessed=tuple(others),
    )
