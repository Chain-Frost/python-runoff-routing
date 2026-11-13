"""Read retained Inc/Time hydrograph reports without inventing location or timing mappings."""

from __future__ import annotations

import re
from decimal import Decimal
from itertools import pairwise

from .rorb_documents import Diagnostic, HydrographReport, HydrographRow, Inspection, RorbSource, decimal_number

STEP = re.compile(r"\s*Time increment \(hours\)\s*=\s*(\S+)\s*", re.IGNORECASE)
DURATION = re.compile(r"\s*Duration of calculations:\s*(\d+)\s*", re.IGNORECASE)
HYDRO = re.compile(r"Hyd\d+", re.IGNORECASE)
VOLUME = re.compile(r"\s*Volume\s*,\s*m(?:³|3)\s+(\S+)\s*", re.IGNORECASE)
NUMERIC_START = re.compile(r"^[+-]?(?:\d|\.\d|\*|nan|inf)", re.IGNORECASE)


def _extract_metadata(source: RorbSource) -> tuple[Decimal | None, int | None]:
    timestep: Decimal | None = None
    duration: int | None = None
    for line in source.lines:
        if match := STEP.fullmatch(line):
            value = decimal_number(match[1])
            if value <= 0 or (timestep is not None and value != timestep):
                message = "Conflicting or nonpositive reported time increments"
                raise ValueError(message)
            timestep = value
        if match := DURATION.fullmatch(line):
            value = int(match[1])
            if duration is not None and value != duration:
                message = "Conflicting reported calculation durations"
                raise ValueError(message)
            duration = value
    return timestep, duration


def _read_rows(source: RorbSource, line_index: int, count: int) -> tuple[HydrographRow, ...]:
    rows: list[HydrographRow] = []
    for number, line in enumerate(source.lines[line_index + 1 :], start=line_index + 2):
        fields = line.split()
        if not fields:
            if rows:
                break
            continue
        if not NUMERIC_START.match(fields[0]):
            if rows:
                break
            continue
        if len(fields) != count or not fields[0].isascii() or not fields[0].isdecimal():
            message = f"Malformed hydrograph data record at line {number}"
            raise ValueError(message)
        increment = int(fields[0])
        time = decimal_number(fields[1])
        values = tuple(decimal_number(value) for value in fields[2:])
        if rows and (increment != rows[-1].increment + 1 or time <= rows[-1].time_hours):
            message = f"Noncontiguous increment or nonincreasing time at line {number}"
            raise ValueError(message)
        rows.append(HydrographRow(number, increment, time, values, fields[1]))
    if not rows:
        message = f"Empty hydrograph table following line {line_index + 1}"
        raise ValueError(message)
    return tuple(rows)


def _printed_resolution(value: Decimal) -> Decimal:
    return Decimal(1).scaleb(int(value.as_tuple().exponent))


def _validate_time(rows: tuple[HydrographRow, ...], timestep: Decimal | None) -> None:
    if timestep is None:
        return
    for previous, current in pairwise(rows):
        precision = (
            _printed_resolution(previous.time_hours)
            + _printed_resolution(current.time_hours)
            + _printed_resolution(timestep)
        ) / 2
        tolerance = min(timestep / 2, precision)
        if abs(current.time_hours - previous.time_hours - timestep) > tolerance:
            message = f"Reported time increment differs from values at line {current.line}"
            raise ValueError(message)


def _validate_duration(rows: tuple[HydrographRow, ...], duration: int | None) -> None:
    if duration is None:
        return
    # Retained RORB_CMD 6.44 reports number N+1 output rows as increments
    # 1..N+1 (their first raw time is h); other characterised reports use
    # 0..N. Never shift the source increments or time tokens to reconcile.
    first_last = (rows[0].increment, rows[-1].increment)
    if len(rows) != duration + 1 or first_last not in ((0, duration), (1, duration + 1)):
        message = "Report hydrograph rows do not cover the full calculation duration"
        raise ValueError(message)




def _reported_single_column_volume(source: RorbSource, header_index: int, columns: tuple[str, ...]) -> str | None:
    """Attribute a printed m³ volume only for one uniquely identified hydrograph column."""
    if len(columns) != 1:
        return None
    matches = [
        match[1]
        for line in source.lines[:header_index]
        if (match := VOLUME.fullmatch(line)) is not None
    ]
    if len(matches) != 1:
        return None
    value = decimal_number(matches[0])
    if not value.is_finite() or value < 0:
        message = "Invalid source-reported volume in m3"
        raise ValueError(message)
    return matches[0]


def inspect_output(source: RorbSource) -> Inspection:
    headers = [(index, line.split()) for index, line in enumerate(source.lines) if line.split()[:2] == ["Inc", "Time"]]
    if not headers:
        return Inspection(
            "output_report",
            "unsupported",
            source,
            (Diagnostic("no_supported_table", "No Inc Time HydNNN table", "unsupported"),),
        )
    if len(headers) != 1:
        return Inspection(
            "output_report",
            "invalid",
            source,
            (Diagnostic("ambiguous_tables", "Multiple hydrograph tables need separate identities", "error"),),
        )
    index, fields = headers[0]
    if len(fields) < 3 or len(set(fields)) != len(fields) or any(HYDRO.fullmatch(name) is None for name in fields[2:]):
        return Inspection(
            "output_report",
            "invalid",
            source,
            (Diagnostic("bad_table_header", "Duplicate or unrecognised hydrograph columns", "error", index + 1),),
        )
    try:
        timestep, duration = _extract_metadata(source)
        rows = _read_rows(source, index, len(fields))
        _validate_time(rows, timestep)
        _validate_duration(rows, duration)
    except ValueError as exc:
        return Inspection(
            "output_report", "invalid", source, (Diagnostic("output_record", str(exc), "error", index + 1),)
        )
    report = HydrographReport(
        tuple(fields[2:]), rows, timestep, duration, _reported_single_column_volume(source, index, tuple(fields[2:]))
    )
    notes = [
        Diagnostic("print_identity_unverified", "HydNNN labels do not establish native print locations", "warning")
    ]
    if duration is None:
        notes.append(
            Diagnostic(
                "completion_unverified", "No reported calculation duration; cannot verify completeness", "warning"
            )
        )
    if timestep is None:
        notes.append(Diagnostic("timestep_unverified", "No reported timestep; raw labels preserved", "warning"))
    return Inspection("output_report", "partial", source, tuple(notes), hydrographs=report)
