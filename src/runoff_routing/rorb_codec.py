"""Evidence-limited RORB_CMD, RORB_GE and DESIGN parse/serialise boundaries.

Parse functions are pure and preserve original source bytes. Canonical emitters
operate only on validated typed models and never promise native compatibility.
"""

from __future__ import annotations

import hashlib
import math
import re
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
    PrintLocation,
    Reach,
    RoutingValue,
    RunModel,
    StormModel,
    SubArea,
)
from .rorb_par import inspect_cmd_parameters

Dialect = Literal["cmd_v2", "rorb_ge_002", "design_explicit"]
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


def _graphical(lines: tuple[str, ...]) -> tuple[int, tuple[str, ...]]:
    """Validate marker/known nonzero storage features; never infer computational order from nodes."""
    versions = [
        (index, line.strip()) for index, line in enumerate(lines) if re.fullmatch(r"C RORB_GE \d+", line.strip())
    ]
    boundaries = [index for index, line in enumerate(lines) if line.strip() == "C END RORB_GE"]
    if len(versions) != 1 or versions[0][1] != "C RORB_GE 002":
        message = "Only a single RORB_GE 002 graphical header is characterised"
        raise _problem(message, unsupported=True)
    if len(boundaries) != 1 or versions[0][0] >= boundaries[0]:
        message = "Missing or repeated RORB_GE completion marker"
        raise _problem(message)
    end = boundaries[0]
    header = lines[: end + 1]
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


def parse_catg(data: bytes) -> ParsedDocument[CatchmentModel]:  # noqa: C901 -- ordered control vector states
    """Read RORB_GE 002's embedded explicit natural-reach stack vector."""
    source = SourceDocument.from_bytes(data)
    lines = source.lines
    if not lines:
        message = "Empty RORB_GE catchment"
        raise _problem(message)
    end, graphics = _graphical(lines)
    records = _raw_records(lines, end + 1)
    if not records:
        message = "Missing RORB_GE computation records"
        raise _problem(message)
    if records[0][1] != "1":
        message = "Only natural reach-type header 1 is supported"
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
        if code not in (1, 3, 4, 5, 7):
            message = f"Uncharacterised numerical control code {code}"
            raise _problem(message, line_no, unsupported=True)
        parts = [part.strip() for part in raw.split(",", maxsplit=3)]
        label = ""
        if code in (1, 5):
            if len(parts) < 3 or _number(parts[2], line_no) != -99:
                message = "Natural reach needs code, positive length, -99"
                raise _problem(message, line_no)
            length = _number(parts[1], line_no)
            if length <= 0:
                message = "Natural reach length must be positive"
                raise _problem(message, line_no)
            label = parts[3] if len(parts) == 4 else ""
            reach_id = f"reach_{len(reaches) + 1}"
            reaches.append(Reach(reach_id, length, label))
            if code == 1:
                area_id = f"area_{len(names) + 1}"
                match = _AREA_NAME.search(label)
                names.append(match[1] if match is not None else "")
                controls.append(ControlStep(1, area_id, reach_id, None, label))
            else:
                controls.append(ControlStep(5, None, reach_id, None, label))
            spans.append(SourceSpan(f"reach_{len(reaches)}", line_no, parts[1]))
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
                if physical_label.strip() == "0" and not any(value == "0" for _, value in records[cursor + 2 :]):
                    message = "Code 7 consumed the final zero control as its missing location"
                    raise _problem(message, line_no + 1)
                if physical_label.strip():
                    if _is_comment(physical_label):
                        message = "Comment-prefixed print locations are not characterised"
                        raise _problem(message, line_no + 1, unsupported=True)
                    if cursor + 1 >= len(records) or records[cursor + 1][0] != line_no + 1:
                        message = "Code 7 print location must immediately follow its control"
                        raise _problem(message, line_no + 1)
                    label = physical_label.strip()
                    cursor += 1
                else:
                    label = ""
                print_id = f"print_{len(prints) + 1}"
                prints.append(PrintLocation(print_id, label))
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
    flag = [token.strip() for token in impervious.split(",", maxsplit=2)]
    if len(flag) < 2 or _number(flag[1], impervious_line) != -99:
        message = "Expected impervious flag followed by -99"
        raise _problem(message, impervious_line)
    if _number(flag[0], impervious_line) != 0:
        message = "Impervious fractions require a different model dialect"
        raise _problem(message, impervious_line, unsupported=True)
    if next_index + 1 != len(records):
        message = "Trailing catchment data after impervious sentinel"
        raise _problem(message, records[next_index + 1][0])
    if len(areas) != len(names):
        message = f"Subarea count {len(areas)} differs from source controls {len(names)}"
        raise _problem(message)
    try:
        model = CatchmentModel(
            lines[0].strip(),
            tuple(SubArea(f"area_{index + 1}", area, names[index]) for index, area in enumerate(areas)),
            tuple(reaches),
            tuple(controls),
            tuple(prints),
        )
    except ValueError as exc:
        raise _problem(str(exc)) from exc
    return ParsedDocument("rorb_ge_002", source, model, tuple(spans), graphics)


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
    if marker.casefold() != "temporal pattern (% of depth)":
        message = "Missing temporal pattern marker"
        raise _problem(message, marker_line)
    percentages, next_index, percent_spans = _terminated(records, 3, "temporal_percent")
    if len(percentages) != count:
        message = "Temporal pattern length does not match the declared rainfall-bin count"
        raise _problem(message, timing_line)
    depths, final_index, depth_spans = _terminated(records, next_index, "rainfall_depth_mm")
    if final_index != len(records):
        message = "Trailing records after the DESIGN rainfall depths"
        raise _problem(message, records[final_index][0])
    try:
        model = StormModel(
            lines[0].strip(),
            dt,
            horizon,
            start,
            percentages,
            depths,
            tuple(f"area_{index + 1}" for index in range(len(depths))),
        )
    except ValueError as exc:
        raise _problem(str(exc)) from exc
    spans = (
        SourceSpan("timestep_hours", header_line, header_fields[0]),
        SourceSpan("calculation_increments", header_line, header_fields[1]),
        SourceSpan("start_increment", timing_line, timing_fields[0]),
        *percent_spans,
        *depth_spans,
    )
    return ParsedDocument("design_explicit", source, model, spans)


def parse_bytes(
    data: bytes, suffix: str
) -> ParsedDocument[ParameterSet] | ParsedDocument[CatchmentModel] | ParsedDocument[StormModel]:
    """Content parser; suffix is only a declared dialect selection."""
    extension = suffix.lower().lstrip(".")
    if extension == "par":
        return parse_cmd_par(data)
    if extension == "catg":
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


def serialize_catg(model: CatchmentModel) -> bytes:
    """Canonical computation vector with an *empty* drawing scaffold, not a native-verified redraw."""
    model.__post_init__()
    _canonical_ids(model)
    lines = [
        _safe_label(model.title),
        "C RORB_GE 002",
        "C #NODES",
        "C 0",
        "C #REACHES",
        "C 0",
        "C #STORAGES",
        "C 0",
        "C #INFLOW/OUTFLOW",
        "C 0",
        "C END RORB_GE",
        "1",
    ]
    reaches = {reach.identifier: reach for reach in model.reaches}
    for step in model.controls:
        label = _safe_label(step.label)
        if step.code in (1, 5):
            if step.reach_id is None:
                message = "Missing reach identity"
                raise ValueError(message)
            lines.append(f"{step.code}, {reaches[step.reach_id].length_km}, -99, {label}")
        elif step.code == 7:
            # The native code 7 label is a separate character record.
            lines.extend(("7", label))
        else:
            lines.append(f"{step.code}, {label}")
    lines.extend(
        [
            "0",
            "C Sub Area Data",
            ", ".join([*(str(item.area_km2) for item in model.subareas), "-99"]),
            "C Impervious Fraction Data",
            "0, -99",
            "",
        ]
    )
    return "\n".join(lines).encode("utf-8")


def serialize_design_stm(model: StormModel) -> bytes:
    """Explicit DESIGN pattern; percentages/depths remain Decimal tokens."""
    model.__post_init__()
    _canonical_ids(model)
    lines = [
        _safe_label(model.title),
        "DESIGN",
        f"{model.timestep_hours},{model.calculation_increments},1,1,1,-99",
        f"{model.start_increment},{len(model.percentages)}",
        "Temporal pattern (% of depth)",
        ", ".join([*(str(item) for item in model.percentages), "-99"]),
        "C Sub-area rainfall depths",
        ", ".join([*(str(item) for item in model.depths_mm), "-99"]),
        "",
    ]
    return "\n".join(lines).encode("utf-8")


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
    if parameters.num_isa != 1 or parameters.loss_model != 1 or not parameters.lumped_kc:
        message = "S2 adapter only accepts one-ISA, lumped, pervious IL/CL inputs"
        raise ValueError(message)
    if storm.start_increment != 0:
        message = "S2 adapter needs rainfall starting in the first increment"
        raise ValueError(message)
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
        _as_float(parameters.losses[0].continuing),
        _as_float(parameters.routing[0].kc),
        _as_float(parameters.routing[0].m),
    )
