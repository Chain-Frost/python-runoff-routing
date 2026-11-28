"""Export printed RORB interval depths as metric TUFLOW STEPPED rainfall boundaries."""

from __future__ import annotations

import argparse
import csv
import io
import re
from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal, DecimalException, Inexact, localcontext
from itertools import pairwise
from pathlib import Path
from typing import Literal

from .rorb_readers.reader_types import RorbDocument, Section, exact_number
from .rorb_readers.readers import read_rorb_file

RainfallKind = Literal["gross", "excess"]
_HEADINGS = {
    "gross": "Rainfall, mm, in time inc.",
    "excess": "Rainfall-excess, mm, in time inc.",
}
_TIME_COLUMN = "Time_hours"
_ZERO = Decimal(0)


class RainfallExportError(ValueError):
    """Malformed, unsupported or ambiguous rainfall source or output selection."""


@dataclass(frozen=True, slots=True)
class RainfallRow:
    """One TUFLOW timestamp and the depths ending at that time, in column order."""

    time_hours: Decimal
    depths_mm: tuple[Decimal, ...]


@dataclass(frozen=True, slots=True)
class RainfallBoundary:
    """A selected printed-depth boundary, not reconstructed unrounded rainfall."""

    source_sha256: str
    section: str
    kind: RainfallKind
    columns: tuple[str, ...]
    step_hours: Decimal
    reported_step_hours: Decimal
    clock_basis: Literal["reported", "caller_exact"]
    start_increment: int
    finish_increment: int
    rows: tuple[RainfallRow, ...]
    totals_mm: tuple[Decimal, ...]
    reported_totals_mm: tuple[Decimal, ...]
    trailing_zero_added: bool

    def to_csv(self) -> str:
        """Return a single-header, comma-delimited TUFLOW boundary data file."""
        stream = io.StringIO(newline="")
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow((_TIME_COLUMN, *self.columns))
        for row in self.rows:
            writer.writerow(format(value, "f") for value in (row.time_hours, *row.depths_mm))
        return stream.getvalue()


def _decimal(value: Decimal) -> Decimal:
    """Bound printed decimals to an exactly representable working domain."""
    exponent = value.as_tuple().exponent
    if not isinstance(exponent, int) or abs(exponent) > 30 or value.adjusted() > 30 or value < 0:
        msg = "Rainfall values must be nonnegative finite decimals within the supported precision"
        raise RainfallExportError(msg)
    return value


def _metadata_decimal(document: RorbDocument, key: str) -> Decimal:
    token = document.metadata.get(key)
    if not isinstance(token, str):
        msg = f"Missing printed decimal: {key}"
        raise RainfallExportError(msg)
    return _decimal(exact_number(token))


def _select_section(document: RorbDocument, kind: RainfallKind, section: int | None) -> str:
    if kind not in _HEADINGS:
        msg = "Explicitly select gross or excess rainfall"
        raise RainfallExportError(msg)
    candidates = [
        match[1]
        for key, value in document.metadata.items()
        if (match := re.fullmatch(r"(rainfall_[1-9]\d*)_meaning", key)) is not None
        and isinstance(value, str)
        and value.startswith(_HEADINGS[kind])
    ]
    if section is None:
        if len(candidates) != 1:
            msg = f"Expected one {kind} rainfall section; explicitly select an available section: {candidates}"
            raise RainfallExportError(msg)
        selected = candidates[0]
    else:
        selected = f"rainfall_{section}"
        if selected not in candidates:
            msg = f"{selected} does not identify the requested {kind} rainfall"
            raise RainfallExportError(msg)
    if document.metadata[f"{selected}_meaning"] != f"{_HEADINGS[kind]} following time shown":
        msg = f"Unsupported interval timing in {selected}"
        raise RainfallExportError(msg)
    return selected


def _half_resolution(value: Decimal) -> Decimal:
    exponent = value.as_tuple().exponent
    if not isinstance(exponent, int):
        msg = "Invalid printed rainfall or hydrograph time"
        raise RainfallExportError(msg)
    return Decimal(1).scaleb(exponent) / 2


def _clock(document: RorbDocument, exact_step_hours: Decimal | None) -> tuple[Decimal, Decimal, int, int]:
    reported = _metadata_decimal(document, "time_increment_raw")
    start = document.metadata.get("rainfall_start_increment")
    finish = document.metadata.get("rainfall_finish_increment")
    if reported <= 0 or not isinstance(start, int) or not isinstance(finish, int) or not 0 <= start < finish:
        msg = "Expected an unambiguous positive time increment and complete declared rainfall horizon"
        raise RainfallExportError(msg)
    step = reported if exact_step_hours is None else _decimal(exact_step_hours)
    if step <= 0 or abs(step - reported) > _half_resolution(reported):
        msg = "Exact timestep is inconsistent with the printed timestep resolution"
        raise RainfallExportError(msg)
    covered = _verify_printed_clock(document, step)
    if exact_step_hours is not None and covered < finish:
        msg = "An explicit exact timestep requires a complete OUT clock covering the rainfall horizon"
        raise RainfallExportError(msg)
    return step, reported, start, finish


def _verify_printed_clock(document: RorbDocument, step: Decimal) -> int:
    """Check each printed OUT clock label and return the complete corroborated horizon."""
    covered = 0
    for table in document.sections:
        if not table.name.startswith("hydrographs_"):
            continue
        for index, row in enumerate(table.rows):
            observed = _decimal(table.source_decimal(index, "Time"))
            increment = int(str(row["Inc"]))
            expected = step * increment
            if abs(expected - observed) > _half_resolution(observed):
                msg = "Rainfall timestep disagrees with the cumulative OUT clock"
                raise RainfallExportError(msg)
        if table.completeness == "reported_increment_count" and table.rows:
            covered = max(covered, int(str(table.rows[-1]["Inc"])))
    return covered


def _validate_page(page: Section, start: int, finish: int) -> None:
    if (
        not page.valid
        or len(page.rows) != finish - start
        or len(page.source_tokens) != len(page.rows)
        or page.columns[:3] != ["line", "Inc", "Catchment_mm"]
        or any(row["Inc"] != increment for increment, row in enumerate(page.rows, start))
    ):
        msg = f"Incomplete or invalid rainfall interval sequence in {page.name}"
        raise RainfallExportError(msg)


def _collect_columns(
    document: RorbDocument, name: str, start: int, finish: int
) -> tuple[dict[str, tuple[Decimal, ...]], dict[str, Decimal]]:
    page_count = document.metadata.get(f"{name}_page_count")
    if not isinstance(page_count, int) or page_count < 1:
        msg = f"Missing complete rainfall page/header/total boundary for {name}"
        raise RainfallExportError(msg)
    values: dict[str, tuple[Decimal, ...]] = {}
    reported: dict[str, Decimal] = {}
    seen: set[str] = set()
    for index in range(1, page_count + 1):
        page = document.section(name if index == 1 else f"{name}_page_{index}")
        _validate_page(page, start, finish)
        for column in page.columns[2:]:
            depths = tuple(_decimal(page.source_decimal(i, column)) for i in range(len(page.rows)))
            total = _metadata_decimal(document, f"{page.name}_reported_total_{column}")
            if column == "Catchment_mm" and column in values:
                if values[column] != depths or reported[column] != total:
                    msg = "Conflicting repeated catchment rainfall across pages"
                    raise RainfallExportError(msg)
                continue
            if column.casefold() in seen:
                msg = f"Ambiguous repeated rainfall column: {column}"
                raise RainfallExportError(msg)
            seen.add(column.casefold())
            values[column] = depths
            reported[column] = total
    return values, reported


def _boundary_rows(
    selected: tuple[tuple[Decimal, ...], ...], step: Decimal, start: int, finish: int
) -> tuple[tuple[RainfallRow, ...], bool]:
    zeros = (_ZERO,) * len(selected)
    rows = [RainfallRow(step * start, zeros)]
    rows.extend(
        RainfallRow(step * end, tuple(depths)) for end, depths in enumerate(zip(*selected, strict=True), start + 1)
    )
    trailing = any(rows[-1].depths_mm)
    if trailing:
        rows.append(RainfallRow(step * (finish + 1), zeros))
    if any(float(a.time_hours) >= float(b.time_hours) for a, b in pairwise(rows)):
        msg = "Rainfall clock cannot be represented as distinct floating-point timestamps"
        raise RainfallExportError(msg)
    return tuple(rows), trailing


def build_tuflow_rainfall(
    document: RorbDocument,
    *,
    kind: RainfallKind,
    columns: Sequence[str],
    section: int | None = None,
    exact_step_hours: Decimal | None = None,
) -> RainfallBoundary:
    """Build a metric STEPPED boundary from explicit canonical rainfall columns.

    A source increment i describes [i*step, (i+1)*step]. The exported depth is
    at its end time. No source depth is redistributed or reconstructed.
    An optional caller-supplied exact source step must agree with the printed
    timestep and the complete cumulative OUT clock; it is never inferred.
    """
    if document.kind != "standard_output" or document.status == "invalid":
        msg = "A structurally valid standard RORB report is required"
        raise RainfallExportError(msg)
    requested = tuple(columns)
    if not requested or len(set(requested)) != len(requested):
        msg = "Select at least one unique canonical rainfall column"
        raise RainfallExportError(msg)
    name = _select_section(document, kind, section)
    try:
        with localcontext() as context:
            context.prec = 100
            context.traps[Inexact] = True
            step, reported_step, start, finish = _clock(document, exact_step_hours)
            values, reported = _collect_columns(document, name, start, finish)
            if any(column not in values for column in requested):
                msg = f"Unknown rainfall column; available columns: {tuple(values)}"
                raise RainfallExportError(msg)
            selected = tuple(values[column] for column in requested)
            rows, trailing = _boundary_rows(selected, step, start, finish)
            totals = tuple(sum(depths, _ZERO) for depths in selected)
    except (DecimalException, StopIteration, KeyError) as exc:
        msg = "Invalid or unsupported canonical rainfall source tokens or clock"
        raise RainfallExportError(msg) from exc
    return RainfallBoundary(
        source_sha256=document.sha256,
        section=name,
        kind=kind,
        columns=requested,
        step_hours=step,
        reported_step_hours=reported_step,
        clock_basis="reported" if exact_step_hours is None else "caller_exact",
        start_increment=start,
        finish_increment=finish,
        rows=rows,
        totals_mm=totals,
        reported_totals_mm=tuple(reported[column] for column in requested),
        trailing_zero_added=trailing,
    )


def export_tuflow_rainfall(
    source: Path,
    output: Path,
    *,
    kind: RainfallKind,
    columns: Sequence[str],
    section: int | None = None,
    exact_step_hours: Decimal | None = None,
) -> RainfallBoundary:
    """Convert one report to a new CSV; refuse to overwrite any existing file."""
    if output.suffix.lower() != ".csv":
        msg = "TUFLOW boundary data output must have a .csv extension"
        raise RainfallExportError(msg)
    result = build_tuflow_rainfall(
        read_rorb_file(source), kind=kind, columns=columns, section=section, exact_step_hours=exact_step_hours
    )
    payload = result.to_csv()
    with output.open("x", encoding="utf-8", newline="") as stream:
        stream.write(payload)
    return result


def main(argv: Sequence[str] | None = None) -> int:
    """Explicit single-report CLI; no RORB or TUFLOW process is launched."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Standard RORB .out report")
    parser.add_argument("output", type=Path, help="New TUFLOW rainfall boundary .csv")
    parser.add_argument("--kind", required=True, choices=("gross", "excess"))
    parser.add_argument("--column", required=True, action="append", help="Catchment_mm or Subarea_<label>_mm; repeat")
    parser.add_argument("--section", type=int, help="Number in canonical rainfall_N if the kind is ambiguous")
    parser.add_argument(
        "--exact-step-hours",
        type=exact_number,
        help="Caller-verified exact source timestep; requires corroboration by the complete printed OUT clock",
    )
    args = parser.parse_args(argv)
    try:
        result = export_tuflow_rainfall(
            args.source,
            args.output,
            kind=args.kind,
            columns=args.column,
            section=args.section,
            exact_step_hours=args.exact_step_hours,
        )
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    print(f"{result.kind} {result.section}; source SHA-256 {result.source_sha256}")
    print(f"Timestep: {result.step_hours:f} h ({result.clock_basis}); report: {result.reported_step_hours:f} h")
    for column, total, reported in zip(result.columns, result.totals_mm, result.reported_totals_mm, strict=True):
        print(f"{column}: printed increments {total:f} mm; printed report total {reported:f} mm")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
