"""Evidence-limited RORB_CMD, RORB_GE and DESIGN parse/serialise boundaries.

Parse functions are pure and preserve original source bytes. Canonical emitters
operate only on validated typed models and never promise native compatibility.
"""

from __future__ import annotations

import hashlib
import importlib
import math
import re
from collections.abc import Callable
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Literal, cast

from .rorb_documents import RorbSource, decimal_number
from .rorb_model import (
    CatchmentModel,
    ControlCode,
    ControlStep,
    LossValue,
    ParameterSet,
    PatternBasis,
    PrintLocation,
    Reach,
    RoutingValue,
    RunModel,
    StormModel,
    SubArea,
)
from .rorb_par import inspect_cmd_parameters

Dialect = Literal[
    "cmd_v2", "rorb_ge_002", "rorb_ge_645", "design_explicit", "design_relative_weights", "design_preburst_combined"
]
Status = Literal["invalid", "unsupported"]
_NUMBER = re.compile(r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eEdD][+-]?[0-9]+)?\Z")
_AREA_NAME = re.compile(r"Sub-area\s+(\S+)", re.IGNORECASE)


class RorbFormatError(ValueError):
    """A source error with a stable unsupported/invalid distinction."""

    def __init__(self, status: Status, code: str, message: str, line: int | None = None) -> None:
        super().__init__(message)
        self.status = status
        self.code = code
        self.line = line


FormatProblem = RorbFormatError


@dataclass(frozen=True, slots=True)
class SourceSpan:
    """One-based source location and original semantic token."""

    field: str
    line: int
    source_text: str


@dataclass(frozen=True, slots=True)
class SourceDocument:
    """Source identity, including exact encoding, line endings and comments."""

    data: bytes
    encoding: str
    newline: Literal["lf", "crlf", "cr", "mixed", "none"]
    sha256: str
    lines: tuple[str, ...]

    @classmethod
    def from_bytes(cls, data: bytes) -> SourceDocument:
        try:
            content = data.decode("utf-8-sig")
            encoding = "utf-8-sig"
        except UnicodeDecodeError:
            try:
                content = data.decode("cp1252")
            except UnicodeDecodeError as exc:
                message = "Undecodable RORB source bytes"
                status: Status = "invalid"
                code = "source_encoding"
                raise RorbFormatError(status, code, message) from exc
            encoding = "cp1252"
        crlf = b"\r\n" in data
        bare_lf = b"\n" in data.replace(b"\r\n", b"")
        cr = b"\r" in data.replace(b"\r\n", b"")
        styles = sum((crlf, bare_lf, cr))
        if styles > 1:
            newline = "mixed"
        elif crlf:
            newline = "crlf"
        elif bare_lf:
            newline = "lf"
        elif cr:
            newline = "cr"
        else:
            newline = "none"
        return cls(data, encoding, newline, hashlib.sha256(data).hexdigest(), tuple(content.splitlines()))


@dataclass(frozen=True, slots=True)
class ParsedDocument[T]:
    """An untouched parsed source and its immutable, syntax-independent model."""

    dialect: Dialect
    source: SourceDocument
    model: T
    source_map: tuple[SourceSpan, ...]
    graphical_metadata: tuple[str, ...] = ()


def original_bytes[T](parsed: ParsedDocument[T], *, current_model: T | None = None) -> bytes:
    """Original-byte mode: reject a changed model rather than silently discard edits."""
    if current_model is not None and current_model != parsed.model:
        message = "Original-byte export cannot represent edits; choose canonical export"
        raise ValueError(message)
    return parsed.source.data


def _problem(message: str, line: int | None = None, *, unsupported: bool = False) -> FormatProblem:
    return FormatProblem(
        "unsupported" if unsupported else "invalid",
        "unsupported_construct" if unsupported else "malformed_record",
        message,
        line,
    )


def _number(token: str, line: int) -> Decimal:
    clean = token.strip()
    if _NUMBER.fullmatch(clean) is None:
        message = f"Invalid numeric token {token!r}"
        raise _problem(message, line)
    try:
        return decimal_number(clean)
    except ValueError as exc:
        raise _problem(str(exc), line) from exc


def _integer(token: str, line: int, *, minimum: int = 0, maximum: int = 1_000_000) -> int:
    value = _number(token, line)
    if value != value.to_integral_value() or not minimum <= value <= maximum:
        message = f"Expected integer in [{minimum}, {maximum}]: {token!r}"
        raise _problem(message, line)
    return int(value)


def _raw_records(lines: tuple[str, ...], start: int) -> list[tuple[int, str]]:
    return [
        (index + 1, line.strip())
        for index, line in enumerate(lines[start:], start=start)
        if line.strip() and not _is_comment(line)
    ]


def _is_comment(line: str) -> bool:
    stripped = line.lstrip()
    return stripped == "C" or stripped.startswith(("C ", "C\t"))


def _csv(line: str, location: int) -> list[str]:
    tokens = [token.strip() for token in line.split(",")]
    if tokens and not tokens[-1]:
        tokens.pop()
    if not tokens or any(not token for token in tokens):
        message = "Missing or empty comma-separated numeric field"
        raise _problem(message, location)
    return tokens


def _terminated(
    records: list[tuple[int, str]], start: int, category: str
) -> tuple[tuple[Decimal, ...], int, tuple[SourceSpan, ...]]:
    """Read a complete sentinel-delimited sequence without absorbing following records."""
    values: list[Decimal] = []
    spans: list[SourceSpan] = []
    for index in range(start, len(records)):
        line, raw = records[index]
        tokens = _csv(raw, line)
        for token_index, token in enumerate(tokens):
            value = _number(token, line)
            if value == -99:
                if not values or token_index != len(tokens) - 1:
                    message = f"Malformed -99 terminator in {category}"
                    raise _problem(message, line)
                return tuple(values), index + 1, tuple(spans)
            if value < 0:
                message = f"Negative {category} value"
                raise _problem(message, line)
            if len(values) >= 100_000:
                message = f"Excessive {category} sequence length"
                raise _problem(message, line)
            values.append(value)
            spans.append(SourceSpan(category, line, token))
    message = f"Missing -99 terminator in {category}"
    raise _problem(message)


def parse_cmd_par(data: bytes) -> ParsedDocument[ParameterSet]:
    """Reuse S1's fixed-column CMD V2 inspector without accepting GUI .par."""
    source = SourceDocument.from_bytes(data)
    view = RorbSource(Path("<source.par>"), source.sha256, len(data), source.encoding, source.lines)
    inspection = inspect_cmd_parameters(view)
    if inspection.parameters is None:
        issue = inspection.diagnostics[0]
        raise FormatProblem(
            "unsupported" if inspection.status == "unsupported" else "invalid", issue.code, issue.message, issue.line
        )
    original = inspection.parameters
    try:
        model = ParameterSet(
            original.catchment_reference,
            original.storm_reference,
            original.lumped_kc,
            original.verbosity,
            original.loss_model,
            original.num_isa,
            original.num_bursts,
            tuple(RoutingValue(item.isa, item.kc, item.m) for item in original.routing),
            tuple(LossValue(item.isa, item.burst, item.initial_loss_mm, item.continuing) for item in original.losses),
        )
    except ValueError as exc:
        raise _problem(str(exc)) from exc
    spans = tuple(SourceSpan(field.label.strip(), field.line, field.value) for field in inspection.fields)
    return ParsedDocument("cmd_v2", source, model, spans)


_GRAPHICAL_645_SECTIONS = (
    "#FILE COMMENTS",
    "#SUB-AREA AREA COMMENTS",
    "#IMPERVIOUS FRACTION COMMENTS",
    "#BACKGROUND IMAGE",
    "#NODES",
    "#REACHES",
    "#STORAGES",
    "#INFLOW/OUTFLOW",
)


def _validate_graphical_645(header: tuple[str, ...]) -> None:
    """Recognise the original 6.45 *header only*; no numerical source inference."""
    markers = tuple(line.strip()[2:] for line in header if line.strip().startswith("C #"))
    if len(markers) != len(_GRAPHICAL_645_SECTIONS) or set(markers) != set(_GRAPHICAL_645_SECTIONS):
        message = "Unknown, missing or repeated RORB_GE 6.45 graphical section"
        raise _problem(message, unsupported=True)
    for section in _GRAPHICAL_645_SECTIONS[:3]:
        indices = [index for index, line in enumerate(header) if line.strip() == f"C {section}"]
        if len(indices) != 1 or indices[0] + 1 >= len(header):
            message = f"Missing graphical {section} count"
            raise _problem(message)
        location = indices[0] + 1
        record = header[location].strip()
        if not record.startswith("C "):
            message = f"Malformed graphical {section} count"
            raise _problem(message, location + 1)
        if _integer(record[2:].strip(), location + 1) != 0:
            message = f"Graphical {section} content is not characterised"
            raise _problem(message, location + 1, unsupported=True)
    index = next(i for i, line in enumerate(header) if line.strip() == "C #BACKGROUND IMAGE")
    # The original 6.45 source has C T F; the optional image flag C T T
    # belongs to the graphical section, not the computational control vector.
    # Do not silently consume an unknown asset record or other flag set.
    if index + 1 >= len(header) or re.fullmatch(r"C\s+T\s+[FT]", header[index + 1].strip()) is None:
        message = "Uncharacterised RORB_GE 6.45 background-image flags"
        raise _problem(message, index + 2, unsupported=True)
    next_section = next((i for i in range(index + 2, len(header)) if header[i].strip().startswith("C #")), len(header))
    if any(line.strip() not in ("", "C") for line in header[index + 2 : next_section]):
        message = "Background-image asset payload is not characterised"
        raise _problem(message, index + 3, unsupported=True)


def _graphical(lines: tuple[str, ...]) -> tuple[int, tuple[str, ...]]:
    """Validate known graphical sections, never infer computational order from nodes."""
    versions = [
        (index, line.strip())
        for index, line in enumerate(lines)
        if re.fullmatch(r"C RORB_GE \d+(?:\.\d+)?", line.strip())
    ]
    boundaries = [index for index, line in enumerate(lines) if line.strip() == "C END RORB_GE"]
    if len(versions) != 1 or versions[0][1] not in ("C RORB_GE 002", "C RORB_GE 6.45"):
        message = "Only one RORB_GE 002 or original 6.45 graphical header is characterised"
        raise _problem(message, unsupported=True)
    if len(boundaries) != 1 or versions[0][0] >= boundaries[0]:
        message = "Missing or repeated RORB_GE completion marker"
        raise _problem(message)
    end = boundaries[0]
    header = lines[: end + 1]
    if versions[0][1] == "C RORB_GE 6.45":
        _validate_graphical_645(header)
    for section in ("#NODES", "#REACHES", "#STORAGES", "#INFLOW/OUTFLOW"):
        markers = [index for index, line in enumerate(header) if line.strip() == f"C {section}"]
        if len(markers) != 1 or markers[0] + 1 >= len(header):
            message = f"Missing or repeated graphical {section} section"
            raise _problem(message)
        count_line = header[markers[0] + 1].strip()
        if not count_line.startswith("C "):
            message = f"Malformed graphical {section} count"
            raise _problem(message, markers[0] + 2)
        count = _integer(count_line[2:].strip(), markers[0] + 2, maximum=100_000)
        if count > 0 and section in ("#STORAGES", "#INFLOW/OUTFLOW"):
            message = f"Graphical {section} feature is not characterised"
            raise _problem(message, markers[0] + 2, unsupported=True)
    return end, header


def _graphic_entity_rows(
    header: tuple[str, ...], section: str, *, columns: int
) -> tuple[tuple[int, tuple[str, ...]], ...]:
    """Read only the original 6.45 node/reach *header* records, not a topology."""
    marker = next((i for i, line in enumerate(header) if line.strip() == f"C {section}"), None)
    if marker is None:
        message = f"Missing graphical {section} section"
        raise _problem(message)
    count = _integer(header[marker + 1].strip()[2:].strip(), marker + 2)
    end = next(
        (i for i in range(marker + 2, len(header)) if header[i].strip().startswith("C #")),
        len(header) - 1,
    )
    rows: list[tuple[int, tuple[str, ...]]] = []
    for i in range(marker + 2, end):
        line = header[i].strip()
        if not line or line == "C":
            continue
        tokens = tuple(line.split())
        # Reach geometry has separate single-coordinate continuation lines;
        # these are retained raw but do not represent another reach.
        if section == "#REACHES" and len(tokens) == 2 and tokens[0] == "C":
            _number(tokens[1], i + 1)
            continue
        if len(tokens) < columns or tokens[0] != "C":
            message = f"Uncharacterised {section} graphical record"
            raise _problem(message, i + 1, unsupported=True)
        _integer(tokens[1], i + 1, minimum=1)
        rows.append((i + 1, tokens))
    if len(rows) != count or tuple(_integer(tokens[1], line, minimum=1) for line, tokens in rows) != tuple(
        range(1, count + 1)
    ):
        message = f"RORB_GE 6.45 {section} count or graphical IDs are inconsistent"
        raise _problem(message)
    return tuple(rows)


def _validate_645_print_flags(header: tuple[str, ...]) -> tuple[SourceSpan, ...]:
    """Recognise PR16's fixed *ordinary-export* print/excess settings only."""
    nodes = _graphic_entity_rows(header, "#NODES", columns=14)
    reaches = _graphic_entity_rows(header, "#REACHES", columns=12)
    if not nodes or not reaches:
        message = "RORB_GE 6.45 requires graphical nodes and reaches"
        raise _problem(message)
    spans: list[SourceSpan] = []
    outlets = 0
    for line, tokens in nodes:
        _number(tokens[2], line)
        _number(tokens[3], line)
        _number(tokens[-5], line)
        fi = _number(tokens[-4], line)
        if not Decimal(0) <= fi <= Decimal(1):
            message = "Graphical node impervious fraction must be between zero and one"
            raise _problem(message, line)
        native_print = _integer(tokens[-3], line, maximum=999)
        excess = _integer(tokens[-2], line, maximum=999)
        _integer(tokens[-1], line, maximum=999)
        end_flag = _integer(tokens[6], line, maximum=1)
        if excess != 0 or native_print not in (0, 70) or (native_print == 70) != (end_flag == 1):
            message = "Only PR16 single-outlet graphical print 70 and zero excess are characterised"
            raise _problem(message, line, unsupported=True)
        outlets += native_print == 70
        spans.append(SourceSpan("graphical_node_id", line, tokens[1]))
    if outlets != 1:
        message = "PR16 graphical header requires exactly one outlet print 70"
        raise _problem(message, unsupported=True)
    for line, tokens in reaches:
        # Upstream ordinary writer sets reach translation, reach print and
        # comment to zero; other flag values need output/feature review.
        translation = _integer(tokens[-7], line)
        native_print = _integer(tokens[-5], line)
        if translation != 0 or native_print != 0:
            message = "Graphical reach translations/additional prints are outside PR16 export"
            raise _problem(message, line, unsupported=True)
        spans.append(SourceSpan("graphical_reach_id", line, tokens[1]))
    return tuple(spans)


def parse_catg(data: bytes) -> ParsedDocument[CatchmentModel]:  # noqa: C901 -- ordered control vector states
    """Read RORB_GE 002's embedded explicit natural-reach stack vector."""
    source = SourceDocument.from_bytes(data)
    lines = source.lines
    if not lines:
        message = "Empty RORB_GE catchment"
        raise _problem(message)
    end, graphics = _graphical(lines)
    explicit_types = any(line.strip() == "C RORB_GE 6.45" for line in graphics)
    graphical_spans = _validate_645_print_flags(graphics) if explicit_types else ()
    records = _raw_records(lines, end + 1)
    if not records:
        message = "Missing RORB_GE computation records"
        raise _problem(message)
    if records[0][1] != ("0" if explicit_types else "1"):
        message = "Unsupported reach mode for the declared graphical dialect"
        raise _problem(message, records[0][0], unsupported=True)
    controls: list[ControlStep] = []
    reaches: list[Reach] = []
    names: list[str] = []
    prints: list[PrintLocation] = []
    spans: list[SourceSpan] = []
    end_index: int | None = None
    cursor = 1
    while cursor < len(records):
        line_no, raw = records[cursor]
        code_token = raw.split(",", maxsplit=1)[0].strip()
        code = _integer(code_token, line_no, minimum=0)
        if code == 0:
            if raw != "0":
                message = "The terminating zero control must be a complete record"
                raise _problem(message, line_no)
            end_index = cursor + 1
            break
        if code not in ((1, 2, 3, 4, 5, 7) if explicit_types else (1, 3, 4, 5, 7)):
            message = f"Uncharacterised numerical control code {code}"
            raise _problem(message, line_no, unsupported=True)
        parts = [part.strip() for part in raw.split(",", maxsplit=4 if explicit_types else 3)]
        label = ""
        if code in (1, 2, 5):
            if explicit_types:
                if len(parts) < 4:
                    message = "Explicit reach needs code, type, length and -99"
                    raise _problem(message, line_no)
                reach_type = _integer(parts[1], line_no, minimum=1, maximum=4)
                if reach_type in (2, 3):
                    # The pinned PyRomb writer emits a separate slope for
                    # these enums, but CMD 6.44 calculation is not qualified.
                    if len(parts) != 5 or _number(parts[4], line_no) != -99:
                        message = "Unlined/lined reach needs code, type, length, slope and -99"
                        raise _problem(message, line_no)
                    _number(parts[2], line_no)
                    _number(parts[3], line_no)
                    message = f"Reach type {reach_type} requires independent numerical qualification"
                    raise _problem(message, line_no, unsupported=True)
                if reach_type == 4:
                    if len(parts) != 4 or _number(parts[3], line_no) != -99:
                        message = "Drowned reach needs code, type, length and -99"
                        raise _problem(message, line_no)
                    message = "Reach type 4 requires independent numerical qualification"
                    raise _problem(message, line_no, unsupported=True)
                if len(parts) != 4 or _number(parts[3], line_no) != -99:
                    message = "Explicit natural reach must terminate with -99"
                    raise _problem(message, line_no)
                length_token = parts[2]
            else:
                if len(parts) < 3 or _number(parts[2], line_no) != -99:
                    message = "Natural reach needs code, positive length, -99"
                    raise _problem(message, line_no)
                length_token = parts[1]
                label = parts[3] if len(parts) == 4 else ""
            length = _number(length_token, line_no)
            if length < 0:
                message = "Natural reach length must be nonnegative"
                raise _problem(message, line_no)
            reach_id = f"reach_{len(reaches) + 1}"
            reaches.append(Reach(reach_id, length, label))
            if code in (1, 2):
                area_id = f"area_{len(names) + 1}"
                match = _AREA_NAME.search(label)
                names.append(match[1] if match is not None else "")
                controls.append(ControlStep(cast("ControlCode", code), area_id, reach_id, None, label))
            else:
                controls.append(ControlStep(5, None, reach_id, None, label))
            spans.append(SourceSpan(f"reach_{len(reaches)}", line_no, length_token))
        else:
            if len(parts) > 2:
                message = "Stack/print controls accept no numeric operands"
                raise _problem(message, line_no)
            label = parts[1] if len(parts) == 2 else ""
            if code == 7:
                # Item 3.1 is the NEXT PHYSICAL record, not the text
                # following a comma on the control line.
                if line_no >= len(lines):
                    message = "Code 7 is missing its physical print-location record"
                    raise _problem(message, line_no)
                physical_label = lines[line_no]
                if physical_label.strip() == "0":
                    message = "Code 7 requires a location record distinct from the zero control terminator"
                    raise _problem(message, line_no + 1)
                if physical_label.strip():
                    if _is_comment(physical_label):
                        message = "Comment-prefixed print locations are not characterised"
                        raise _problem(message, line_no + 1, unsupported=True)
                    if cursor + 1 >= len(records) or records[cursor + 1][0] != line_no + 1:
                        message = "Code 7 print location must immediately follow its control"
                        raise _problem(message, line_no + 1)
                    native_location = physical_label.strip()
                    cursor += 1
                else:
                    native_location = ""
                print_id = f"print_{len(prints) + 1}"
                prints.append(PrintLocation(print_id, native_location))
                # Inline annotation and the physical native record are distinct.
                controls.append(ControlStep(7, None, None, print_id, label))
                spans.append(SourceSpan("print_location", line_no + 1, physical_label))
            else:
                controls.append(ControlStep(cast("ControlCode", code), None, None, None, label))
        spans.append(SourceSpan("control", line_no, code_token))
        cursor += 1
    if end_index is None:
        message = "Missing zero control vector terminator"
        raise _problem(message)
    areas, next_index, area_spans = _terminated(records, end_index, "subarea_area_km2")
    spans.extend(area_spans)
    if next_index >= len(records):
        message = "Missing explicit impervious-data sentinel"
        raise _problem(message)
    impervious_line, impervious = records[next_index]
    flag = _csv(impervious, impervious_line)
    if explicit_types and len(flag) == 1 and _number(flag[0], impervious_line) == 1:
        fractions, after_fractions, fraction_spans = _terminated(records, next_index + 1, "impervious_fraction")
        if len(fractions) != len(areas) or any(value > 1 for value in fractions):
            message = "Impervious fraction table must have one value in [0,1] for every original source"
            raise _problem(message, impervious_line)
        spans.extend(fraction_spans)
        final_index = after_fractions
    else:
        if len(flag) < 2 or _number(flag[1], impervious_line) != -99:
            message = "Expected zero impervious flag followed by -99"
            raise _problem(message, impervious_line)
        if _number(flag[0], impervious_line) != 0:
            message = "Uncharacterised impervious table flag"
            raise _problem(message, impervious_line, unsupported=True)
        fractions = (Decimal(0),) * len(areas)
        final_index = next_index + 1
    if final_index != len(records):
        message = "Trailing catchment data after impervious sentinel"
        raise _problem(message, records[final_index][0])
    if len(areas) != len(names):
        message = f"Subarea count {len(areas)} differs from source controls {len(names)}"
        raise _problem(message)
    try:
        model = CatchmentModel(
            lines[0].strip(),
            tuple(
                SubArea(f"area_{index + 1}", area, names[index], fractions[index]) for index, area in enumerate(areas)
            ),
            tuple(reaches),
            tuple(controls),
            tuple(prints),
            reach_mode="explicit_reach_types" if explicit_types else "implicit_natural",
        )
    except ValueError as exc:
        raise _problem(str(exc)) from exc
    dialect: Dialect = "rorb_ge_645" if explicit_types else "rorb_ge_002"
    return ParsedDocument(dialect, source, model, (*graphical_spans, *spans), graphics)


def _original_combined_preburst(
    lines: tuple[str, ...], dt: Decimal, percentages: tuple[Decimal, ...], depths: tuple[Decimal, ...]
) -> tuple[int, tuple[SourceSpan, ...]]:
    """Admit only generator-evidenced pre-burst + 100% burst, not arbitrary >100%."""
    annotations: list[SourceSpan] = []
    values: list[Decimal] = []
    labels = ("Storm duration", "ARF*BurDepth(mm)", "Pre-burst depth(mm)")
    for label in labels:
        matches = [
            (line_number, raw.split(":", 1)[1].strip())
            for line_number, raw in enumerate(lines, 1)
            if re.fullmatch(r"C\s+" + re.escape(label) + r"\s*:.*", raw.strip(), re.IGNORECASE)
        ]
        if len(matches) != 1:
            message = f"Nonunit percent pattern lacks unique {label} source evidence"
            raise _problem(message, unsupported=True)
        line_number, lexeme = matches[0]
        if label == "Storm duration":
            duration = re.fullmatch(r"([^ ]+)\s+hour(?:s)?", lexeme, re.IGNORECASE)
            if duration is None:
                message = "Only original hour-based design-burst duration is characterised"
                raise _problem(message, line_number, unsupported=True)
            lexeme = duration.group(1)
        values.append(_number(lexeme, line_number))
        annotations.append(SourceSpan("preburst_" + label.lower().replace(" ", "_"), line_number, lexeme))
    duration_h, burst_depth, preburst_depth = values
    if dt <= 0 or duration_h <= 0 or duration_h / dt != (duration_h / dt).to_integral_value():
        message = "Original design-burst duration is not an exact positive count of storm increments"
        raise _problem(message, unsupported=True)
    burst_bins = int(duration_h / dt)
    split = len(percentages) - burst_bins
    if split < 1 or burst_bins < 1 or not depths or len(set(depths)) != 1:
        message = "Combined pre-burst timing or uniform rainfall depths are not characterised"
        raise _problem(message, unsupported=True)
    prefix = sum(percentages[:split], Decimal(0))
    suffix = sum(percentages[split:], Decimal(0))
    total = prefix + suffix
    if prefix <= 0 or abs(suffix - Decimal(100)) > Decimal("0.05") or total <= 0:
        message = "Combined storm must have a positive pre-burst and an independent 100% design burst"
        raise _problem(message, unsupported=True)
    depth = depths[0]
    if (
        preburst_depth <= 0
        or burst_depth <= 0
        or abs(depth - (preburst_depth + burst_depth)) > Decimal("0.01")
        or abs(depth * prefix / total - preburst_depth) > Decimal("0.01")
        or abs(depth * suffix / total - burst_depth) > Decimal("0.01")
    ):
        message = "Original pre-burst/burst depths do not reconcile with the recorded nonunit pattern"
        raise _problem(message, unsupported=True)
    return split, tuple(annotations)


def parse_design_stm(data: bytes) -> ParsedDocument[StormModel]:  # noqa: C901 -- distinct DESIGN input contracts
    """Strict explicit single-burst DESIGN storm reader, preserving percentages and depth tokens."""
    source = SourceDocument.from_bytes(data)
    lines = source.lines
    if len(lines) < 4 or lines[1].strip() != "DESIGN":
        message = "Only title followed by an explicit DESIGN storm is supported"
        raise _problem(message, unsupported=True)
    records = _raw_records(lines, 2)
    if len(records) < 4:
        message = "Missing explicit DESIGN storm records"
        raise _problem(message)
    header_line, header = records[0]
    header_fields = _csv(header, header_line)
    if len(header_fields) != 6:
        message = "Expected six DESIGN metadata values"
        raise _problem(message, header_line)
    dt = _number(header_fields[0], header_line)
    horizon = _integer(header_fields[1], header_line, minimum=1)
    flags = tuple(_integer(token, header_line, minimum=-99) for token in header_fields[2:])
    if flags != (1, 1, 1, -99):
        message = "Multiple pluviographs, ISAs or bursts not characterised"
        raise _problem(message, header_line, unsupported=True)
    timing_line, timing = records[1]
    timing_fields = _csv(timing, timing_line)
    if len(timing_fields) != 2:
        message = "Expected start increment and rainfall-bin count"
        raise _problem(message, timing_line)
    start = _integer(timing_fields[0], timing_line)
    count = _integer(timing_fields[1], timing_line, minimum=1)
    if start != 0:
        message = "Nonzero burst start requires a different storm convention"
        raise _problem(message, timing_line, unsupported=True)
    marker_line, marker = records[2]
    if marker.casefold() not in ("temporal pattern (% of depth)", "temporal weights"):
        message = "Missing supported temporal pattern marker"
        raise _problem(message, marker_line)
    relative_weights = marker.casefold() == "temporal weights"
    # Preserve original weights and the distinct denominator convention.
    percentages, next_index, percent_spans = _terminated(
        records, 3, "temporal_weight" if relative_weights else "temporal_percent"
    )
    if len(percentages) != count:
        message = "Temporal pattern length does not match the declared rainfall-bin count"
        raise _problem(message, timing_line)
    depths, final_index, depth_spans = _terminated(records, next_index, "rainfall_depth_mm")
    if final_index != len(records):
        message = "Trailing records after the DESIGN rainfall depths"
        raise _problem(message, records[final_index][0])
    basis = PatternBasis.RELATIVE_WEIGHTS if relative_weights else PatternBasis.PERCENT_OF_DEPTH
    preburst_bins = 0
    preburst_spans: tuple[SourceSpan, ...] = ()
    if not relative_weights and abs(sum(percentages, Decimal(0)) - Decimal(100)) > Decimal("0.05"):
        # Source annotations must independently prove the split. A nonunit
        # pattern without its original pre-burst+burst identity is rejected.
        preburst_bins, preburst_spans = _original_combined_preburst(lines, dt, percentages, depths)
        basis = PatternBasis.COMBINED_PREBURST_PERCENT
    try:
        model = StormModel(
            lines[0].strip(),
            dt,
            horizon,
            start,
            percentages,
            depths,
            tuple(f"area_{index + 1}" for index in range(len(depths))),
            pattern_basis=basis,
            preburst_bins=preburst_bins,
        )
    except ValueError as exc:
        raise _problem(str(exc)) from exc
    spans = (
        SourceSpan("timestep_hours", header_line, header_fields[0]),
        SourceSpan("calculation_increments", header_line, header_fields[1]),
        SourceSpan("start_increment", timing_line, timing_fields[0]),
        *preburst_spans,
        *percent_spans,
        *depth_spans,
    )
    dialect: Dialect = (
        "design_relative_weights"
        if relative_weights
        else "design_preburst_combined"
        if preburst_bins
        else "design_explicit"
    )
    return ParsedDocument(dialect, source, model, spans)


def parse_bytes(
    data: bytes, suffix: str
) -> ParsedDocument[ParameterSet] | ParsedDocument[CatchmentModel] | ParsedDocument[StormModel]:
    """Content parser; suffix is only a declared dialect selection."""
    extension = suffix.lower().lstrip(".")
    if extension == "par":
        return parse_cmd_par(data)
    if extension == "catg" or (extension == "cat" and b"C RORB_GE " in data[:1024]):
        return parse_catg(data)
    if extension == "stm":
        return parse_design_stm(data)
    message = f"Uncharacterised RORB input dialect: {extension}"
    raise _problem(message, unsupported=True)


def read_file(path: Path) -> ParsedDocument[ParameterSet] | ParsedDocument[CatchmentModel] | ParsedDocument[StormModel]:
    """Opt-in, read-only filesystem adapter. References in a .par are never followed."""
    return parse_bytes(path.read_bytes(), path.suffix)


def _safe_label(label: str) -> str:
    if any(char in label for char in (",", "\n", "\r", "\x00")):
        message = "Canonical labels cannot contain commas or record delimiters"
        raise ValueError(message)
    if label.strip() != label:
        message = "Canonical labels cannot start or end with whitespace"
        raise ValueError(message)
    return label


def _canonical_ids(model: CatchmentModel | StormModel) -> None:
    if isinstance(model, CatchmentModel):
        collections = (
            (tuple(item.identifier for item in model.subareas), "area_"),
            (tuple(item.identifier for item in model.reaches), "reach_"),
            (tuple(item.identifier for item in model.print_locations), "print_"),
        )
    else:
        collections = ((model.subarea_ids, "area_"),)
    for ids, prefix in collections:
        if ids != tuple(f"{prefix}{index + 1}" for index in range(len(ids))):
            message = "Legacy format cannot represent arbitrary object IDs; use stable ordinal IDs"
            raise ValueError(message)


def serialize_cmd_par(model: ParameterSet) -> bytes:
    """Canonical CMD V2; all field labels have the documented fixed ten-column prefix."""
    model.__post_init__()
    if any("\t" in name or name != name.strip() for name in (model.catchment_reference, model.storm_reference)):
        message = "Canonical CMD references cannot contain tabs or surrounding spaces"
        raise ValueError(message)
    lines = [
        "# BEGIN",
        f"Cat file :{model.catchment_reference}",
        f"Stm file :{model.storm_reference}",
        f"Lumped kc:{'T' if model.lumped_kc else 'F'}",
        f"Verbosity:{model.verbosity}",
        f"Lossmodel:{model.loss_model}",
        f"Num ISA  :{model.num_isa}",
    ]
    lines.extend(f"ISA {item.isa:<5}:{item.kc},{item.m}" for item in model.routing)
    lines.append(f"Num burst:{model.num_bursts}")
    lines.extend(f"ISA {item.isa:<5}:{item.initial_loss_mm},{item.continuing}" for item in model.losses)
    return ("\n".join([*lines, "# END", ""])).encode("utf-8")


class CatgWriterLossError(ValueError):
    """The PyRomb representation would not round-trip all typed CATG semantics."""


# The writer's public ordered-record API is deliberately loaded only on export.
# Ordinary source parsing and routing never import PyRomb or its GIS dependencies.
_GraphNode = tuple[int, str, float, float, int, bool, bool, Decimal, Decimal]
_GraphReach = tuple[int, str, int, int, float, float, Decimal]


def render_catg_with_graphics(
    model: CatchmentModel,
    *,
    node_records: tuple[_GraphNode, ...] = (),
    reach_records: tuple[_GraphReach, ...] = (),
) -> bytes:
    """Adapt validated ordered model records to the pinned PyRomb renderer."""
    model.__post_init__()
    _canonical_ids(model)
    try:
        writer = importlib.import_module("pyromb.models.rorb")
    except ImportError as exc:
        message = "PyRomb CATG writing requires the pinned optional dependency: install .[catg]"
        raise ValueError(message) from exc
    control_factory = cast("Callable[[int, Decimal | None, str, str], object]", writer.OrderedControl)
    node_factory = cast("Callable[..., object]", writer.OrderedNode)
    reach_factory = cast("Callable[..., object]", writer.OrderedReach)
    render = cast("Callable[..., str]", writer.render_ordered_catg)
    reaches = {reach.identifier: reach.length_km for reach in model.reaches}
    locations = {point.identifier: point.label for point in model.print_locations}
    ordered = tuple(
        control_factory(
            int(step.code),
            reaches[step.reach_id] if step.reach_id is not None else None,
            step.label,
            locations[step.print_id] if step.print_id is not None else "",
        )
        for step in model.controls
    )
    nodes = tuple(node_factory(*record) for record in node_records)
    graphics_reaches = tuple(reach_factory(*record) for record in reach_records)
    output = render(
        model.title,
        ordered,
        tuple(area.area_km2 for area in model.subareas),
        tuple(area.impervious_fraction for area in model.subareas),
        explicit_reach_types=model.reach_mode == "explicit_reach_types",
        nodes=nodes,
        reaches=graphics_reaches,
    ).encode("utf-8")
    try:
        restored = parse_catg(output).model
    except RorbFormatError as exc:
        message = f"PyRomb CATG cannot be reparsed as a supported model ({exc.status}): {exc}"
        raise ValueError(message) from exc
    if restored != model:
        message = "PyRomb CATG export would lose source order, labels, physical lengths or output intent"
        raise CatgWriterLossError(message)
    return output


def serialize_catg(model: CatchmentModel) -> bytes:
    """Emit a checked CATG through PyRomb; use original_bytes() for unchanged sources.

    Explicit-reach RORB_GE 6.45 needs validated graphical data supplied through
    serialize_catg_with_drawing(). No local CATG formatter or fallback exists.
    """
    return render_catg_with_graphics(model)


def serialize_design_stm(model: StormModel) -> bytes:
    """Export supported DESIGN records, keeping generator history distinct."""
    model.__post_init__()
    _canonical_ids(model)
    annotations: list[str] = []
    if model.pattern_basis == "combined_preburst_percent":
        if len(set(model.depths_mm)) != 1:
            message = "Combined pre-burst DESIGN export currently requires uniform source depths"
            raise ValueError(message)
        total = sum(model.percentages, Decimal(0))
        prefix = sum(model.percentages[: model.preburst_bins], Decimal(0))
        suffix = sum(model.percentages[model.preburst_bins :], Decimal(0))
        duration = model.timestep_hours * (len(model.percentages) - model.preburst_bins)
        depth = model.depths_mm[0]
        preburst_depth, burst_depth = depth * prefix / total, depth * suffix / total
        if duration <= 0 or preburst_depth <= 0 or burst_depth <= 0:
            message = "Combined pre-burst annotation quantities must be positive"
            raise ValueError(message)
        # Required by the source reader for a nonunit 100%-burst-plus-preburst
        # pattern. These are new calculations, not copied generator provenance.
        annotations = [
            "C Export annotation: derived from typed combined storm; not original generator metadata",
            f"C Storm duration: {duration} hours",
            f"C ARF*BurDepth(mm): {burst_depth}",
            f"C Pre-burst depth(mm): {preburst_depth}",
        ]
    lines = [
        _safe_label(model.title),
        "DESIGN",
        *annotations,
        f"{model.timestep_hours},{model.calculation_increments},1,1,1,-99",
        f"{model.start_increment},{len(model.percentages)}",
        "Temporal weights" if model.pattern_basis == "relative_weights" else "Temporal pattern (% of depth)",
        ", ".join([*(str(item) for item in model.percentages), "-99"]),
        "C Sub-area rainfall depths",
        ", ".join([*(str(item) for item in model.depths_mm), "-99"]),
        "",
    ]
    result = "\n".join(lines).encode("utf-8")
    if parse_design_stm(result).model != model:
        message = "DESIGN export would alter the typed storm model"
        raise ValueError(message)
    return result


def write_new(path: Path, data: bytes) -> None:
    """No-clobber explicit output adapter. Never follows source references."""
    with path.open("xb") as stream:
        stream.write(data)


@dataclass(frozen=True, slots=True)
class S2Payload:
    """Temporary numerical boundary; not a native-parity or solver acceptance statement."""

    controls: tuple[tuple[int, float], ...]
    areas_km2: tuple[float, ...]
    timestep_hours: float
    calculation_increments: int
    percentages: tuple[float, ...]
    depths_mm: tuple[float, ...]
    initial_loss_mm: float
    continuing_loss_mm_h: float
    kc: float
    m: float
    runoff_coefficient: float | None = None
    impervious_fractions: tuple[float, ...] = ()
    pattern_basis: PatternBasis = PatternBasis.PERCENT_OF_DEPTH


def _as_float(value: Decimal) -> float:
    number = float(value)
    if not math.isfinite(number):
        message = "Decimal boundary value cannot be represented as a finite float"
        raise ValueError(message)
    if value != 0 and number == 0.0:
        message = "Nonzero Decimal boundary value underflowed to zero"
        raise ValueError(message)
    return number


def to_s2_payload(model: RunModel) -> S2Payload:
    """Convert only the explicitly supported S2 single-storm subset, without importing S2."""
    parameters, catchment, storm = model.parameters, model.catchment, model.storm
    if parameters.num_isa != 1 or parameters.loss_model not in (1, 2) or not parameters.lumped_kc:
        message = "S2 adapter only accepts one-ISA, lumped, pervious IL/CL or IL/RoC inputs"
        raise ValueError(message)
    if parameters.loss_model == 2 and not 0 <= parameters.losses[0].continuing <= 1:
        message = "Runoff coefficient for IL/RoC must be a fraction in [0, 1]"
        raise ValueError(message)
    if storm.start_increment != 0:
        message = "S2 adapter needs rainfall starting in the first increment"
        raise ValueError(message)
    basis = PatternBasis(storm.pattern_basis)
    if basis not in ("percent_of_depth", "relative_weights"):
        message = "S2 cannot represent combined preburst/burst patterns with a single denominator"
        raise ValueError(message)
    if catchment.reach_mode not in ("implicit_natural", "explicit_reach_types"):
        message = "S2 accepts only characterised natural-reach computation modes"
        raise ValueError(message)
    # S1 recognises the imported explicit graphical mode only for validated
    # natural reach type 1. It rejects other reach modes before this boundary.
    lengths = {item.identifier: item.length_km for item in catchment.reaches}
    steps = tuple(
        (step.code, _as_float(lengths[step.reach_id]) if step.reach_id is not None else 0.0)
        for step in catchment.controls
    )
    return S2Payload(
        steps,
        tuple(_as_float(item.area_km2) for item in catchment.subareas),
        _as_float(storm.timestep_hours),
        storm.calculation_increments,
        tuple(_as_float(value) for value in storm.percentages),
        tuple(_as_float(value) for value in storm.depths_mm),
        _as_float(parameters.losses[0].initial_loss_mm),
        _as_float(parameters.losses[0].continuing) if parameters.loss_model == 1 else 0.0,
        _as_float(parameters.routing[0].kc),
        _as_float(parameters.routing[0].m),
        _as_float(parameters.losses[0].continuing) if parameters.loss_model == 2 else None,
        tuple(_as_float(area.impervious_fraction) for area in catchment.subareas),
        basis,
    )
