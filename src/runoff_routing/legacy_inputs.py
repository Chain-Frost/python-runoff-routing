"""Strict fixture-oriented RORB_GE control vector and DESIGN storm readers.

This adapter recognises only the uniform, natural-reach, fully pervious,
explicit single-pattern subset. It does not replace S1's general source
inspection and does not infer unknown old-format fields.
"""

import math
import re
from typing import cast

from runoff_routing.single_storm import Catchment, Control, ControlCode, Storm


class LegacyInputError(ValueError):
    """The source is malformed or outside the characterised fixture subset."""


def _tokens(text: str) -> tuple[str, ...]:
    return tuple(token for token in re.split(r"[\s,]+", text.strip()) if token)


def _numbers(text: str) -> tuple[float, ...]:
    try:
        values = tuple(float(value.replace("D", "E").replace("d", "E")) for value in _tokens(text))
    except ValueError as exc:
        message = "Unexpected non-numeric field in a legacy data record."
        raise LegacyInputError(message) from exc
    if not all(math.isfinite(value) for value in values):
        message = "Non-finite legacy numeric field."
        raise LegacyInputError(message)
    return values


def _payload_lines(text: str) -> tuple[str, ...]:
    return tuple(
        line.strip()
        for line in text.splitlines()
        if line.strip() and not line.lstrip().startswith("C ") and line.strip() != "C"
    )


def _take_terminated(lines: tuple[str, ...], start: int) -> tuple[tuple[float, ...], int]:
    output: list[float] = []
    for index in range(start, len(lines)):
        values = _numbers(lines[index])
        for position, number in enumerate(values):
            if number == -99.0:
                if position != len(values) - 1 or not output:
                    message = "Malformed or empty -99-terminated data sequence."
                    raise LegacyInputError(message)
                return tuple(output), index + 1
            output.append(number)
    message = "Missing -99 terminator."
    raise LegacyInputError(message)


def parse_control_vector(text: str) -> Catchment:
    """Read RORB_GE embedded natural-channel stack commands and subarea areas.

    Spatial nodes and drawing coordinates are ignored; they are not source
    authority for the routing calculation. Only the post-END control vector
    and explicit areas are interpreted. Other storage/reach/input features
    must be rejected before calculating.
    """
    lines = text.splitlines()
    if sum(line.strip() == "C END RORB_GE" for line in lines) != 1:
        message = "Expected exactly one RORB_GE completion marker."
        raise LegacyInputError(message)
    boundary = next(i for i, line in enumerate(lines) if line.strip() == "C END RORB_GE")
    remaining = [
        line.strip()
        for line in lines[boundary + 1 :]
        if line.strip() and not line.lstrip().startswith("C ") and line.strip() != "C"
    ]
    if len(remaining) < 4 or remaining[0] != "1":
        message = "Only RORB_GE natural reach type 1 is supported."
        raise LegacyInputError(message)
    controls: list[Control] = []
    command_end: int | None = None
    for index, line in enumerate(remaining[1:], start=1):
        code, length = _control_record(line)
        if code == 0:
            command_end = index + 1
            break
        controls.append(Control(cast("ControlCode", code), length))
    if command_end is None or not controls:
        message = "Missing final zero control or empty control vector."
        raise LegacyInputError(message)
    areas, index = _take_terminated(tuple(remaining), command_end)
    if index >= len(remaining) or not _pervious_flag(remaining[index]):
        message = "Only explicitly all-pervious RORB_GE sources are supported."
        raise LegacyInputError(message)
    if any(line.strip() for line in remaining[index + 1 :]):
        message = "Unexpected data after the pervious-area flag."
        raise LegacyInputError(message)
    return Catchment(tuple(controls), areas)


def parse_explicit_design_storm(text: str) -> Storm:
    """Read the characterised single-ISA DESIGN pattern and per-area depths."""
    lines = _payload_lines(text)
    try:
        marker = lines.index("DESIGN")
    except ValueError as exc:
        message = "Only explicit DESIGN storms are supported."
        raise LegacyInputError(message) from exc
    if marker + 4 >= len(lines):
        message = "Incomplete DESIGN storm records."
        raise LegacyInputError(message)
    metadata = _numbers(lines[marker + 1])
    if len(metadata) != 6 or metadata[2:] != (1, 1, 1, -99):
        message = "Only one pluviograph, ISA and storm burst are characterised."
        raise LegacyInputError(message)
    dt, horizon = metadata[:2]
    if dt <= 0 or not horizon.is_integer() or horizon <= 0:
        message = "Invalid timestep or calculation horizon."
        raise LegacyInputError(message)
    timing = _numbers(lines[marker + 2])
    if len(timing) != 2 or timing[0] != 0 or not timing[1].is_integer() or timing[1] <= 0:
        message = "Only rainfall starting at interval zero is supported."
        raise LegacyInputError(message)
    if lines[marker + 3].strip().casefold() != "temporal pattern (% of depth)":
        message = "Missing explicit temporal-pattern marker."
        raise LegacyInputError(message)
    percentages, next_line = _take_terminated(lines, marker + 4)
    if len(percentages) != int(timing[1]):
        message = "Temporal pattern count does not match the header."
        raise LegacyInputError(message)
    if next_line >= len(lines):
        message = "Missing subarea rainfall depths."
        raise LegacyInputError(message)
    depths, end = _take_terminated(lines, next_line)
    if end != len(lines):
        message = "Unexpected trailing storm records."
        raise LegacyInputError(message)
    return Storm(dt, int(horizon), percentages, depths)


def _pervious_flag(text: str) -> bool:
    fields = text.split(",", maxsplit=2)
    if len(fields) == 3 and fields[2].strip() != "No impervious areas in system":
        return False
    return _numbers(",".join(fields[:2])) == (0.0, -99.0)


def _control_record(line: str) -> tuple[int, float]:
    fields = _tokens(line.split(",", maxsplit=3)[0])
    if len(fields) != 1 or not fields[0].isascii() or not fields[0].isdecimal():
        message = "Invalid RORB control-code field."
        raise LegacyInputError(message)
    code = int(fields[0])
    if code not in {0, 1, 3, 4, 5, 7}:
        message = f"Uncharacterised control code {code}."
        raise LegacyInputError(message)
    length = 0.0
    if code in {1, 5}:
        numeric = _numbers(",".join(line.split(",")[:3]))
        if len(numeric) != 3 or numeric[2] != -99.0:
            message = "Expected natural reach length followed by -99."
            raise LegacyInputError(message)
        length = numeric[1]
    return code, length
