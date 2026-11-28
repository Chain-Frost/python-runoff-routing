"""Section-aware reading of observed standard RORB output, without rewriting time or rainfall."""

import re
from dataclasses import dataclass
from decimal import Decimal
from typing import Literal

from .reader_types import Record, RorbDocument, Section, exact_number, integer, number, validate_series
from .result_readers import read_sites, report_metadata


@dataclass(frozen=True, slots=True)
class HydrographSiteColumn:
    """Canonical site ID, raw legend token and printed column with optional physical name."""

    site_id: str
    column: str
    physical_name: str | None
    description: str
    site_record_line: int
    site_id_token: str


def _hyd_ordinal(token: str) -> int:
    match = re.fullmatch(r"Hyd(\d+)", token)
    if match is None or int(match[1]) == 0:
        msg = f"Invalid printed hydrograph identifier {token!r}"
        raise ValueError(msg)
    return int(match[1])


def _bind_site_columns(  # noqa: C901 -- strict physical identity and missing-data guards
    document: RorbDocument, *, table_name: str = "hydrographs_1", allow_unnamed: bool = False
) -> tuple[HydrographSiteColumn, ...]:
    """Match Hyd ordinals without guessing physical names or table positions.

    Unnamed sites reject by default. Explicit allow_unnamed is for numerical
    source-token comparison only: the resulting physical_name is None and
    physical identity remains unverified. Source tokens are unchanged.
    """
    # Scalar interpretation is independent of a complete numeric table and
    # physical-site legend. Preserve scalar-specific failures for consumers to
    # diagnose instead of hiding them behind an unrelated site-binding error.
    scalar_errors = {"reported_scalar_value", "reported_scalar_values", "reported_scalar_layout"}
    if document.kind != "standard_output" or any(
        issue.severity == "error" and issue.code not in scalar_errors for issue in document.diagnostics
    ):
        msg = "Only a structurally valid parsed standard output can bind physical sites"
        raise ValueError(msg)
    if document.metadata.get("hydrograph_summary_count") != 1:
        msg = "Exactly one hydrograph summary is required for physical binding"
        raise ValueError(msg)
    try:
        sites = document.section("sites")
        table = document.section(table_name)
    except StopIteration as exc:
        msg = "Missing physical site descriptions or hydrograph table"
        raise ValueError(msg) from exc
    if not sites.valid or not sites.rows or not table.valid or not table.rows:
        msg = "Incomplete or invalid physical sites or hydrograph samples"
        raise ValueError(msg)

    identified: dict[int, HydrographSiteColumn] = {}
    physical_names: set[str] = set()
    for site in sites.rows:
        site_id = site["id"]
        site_id_token = site.get("id_token")
        description = site["description"]
        name = site["name"]
        role = site["role"]
        if not isinstance(site_id, str) or not isinstance(site_id_token, str) or not isinstance(description, str):
            msg = "Invalid physical site description"
            raise ValueError(msg)  # noqa: TRY004 -- retain the documented ValueError for invalid site records
        raw_name = name if role is not None else description
        if (
            isinstance(raw_name, str)
            and raw_name.strip()
            and re.fullmatch(r"(?:calculated|observed)?\s*hydrograph\s*[:,]?", raw_name, re.IGNORECASE) is None
        ):
            physical_name: str | None = raw_name
        elif allow_unnamed:
            physical_name = None
        else:
            msg = "Native physical print location is unnamed"
            raise ValueError(msg)
        ordinal = _hyd_ordinal(site_id)
        if ordinal in identified or (physical_name is not None and physical_name.casefold() in physical_names):
            msg = "Ambiguous physical site names or identifiers"
            raise ValueError(msg)
        identified[ordinal] = HydrographSiteColumn(
            site_id, "", physical_name, description, int(str(site["line"])), site_id_token
        )
        if physical_name is not None:
            physical_names.add(physical_name.casefold())

    matched: list[HydrographSiteColumn] = []
    printed_ordinals: set[int] = set()
    for column in table.columns[3:]:
        ordinal = _hyd_ordinal(column)
        if ordinal in printed_ordinals:
            msg = "Duplicate hydrograph column ordinal with alternate zero padding"
            raise ValueError(msg)
        printed_ordinals.add(ordinal)
        site = identified.get(ordinal)
        if site is None:
            msg = f"Hydrograph column {column} has no matching physical site"
            raise ValueError(msg)
        matched.append(
            HydrographSiteColumn(
                site.site_id, column, site.physical_name, site.description, site.site_record_line, site.site_id_token
            )
        )
    if len(matched) != len(identified):
        msg = "Physical site list differs from the hydrograph table"
        raise ValueError(msg)
    return tuple(matched)


CmdDiagnosticQuantity = Literal[
    "subarea_upstream_flow",
    "rainfall_excess_flow",
    "reach_downstream_flow",
    "reach_upstream_flow",
    "calculated_flow",
]


@dataclass(frozen=True, slots=True)
class CmdDiagnosticColumn:
    """Report-local flow identity, not a verified model print or physical node."""

    site_id: str
    column: str
    description: str
    site_record_line: int
    site_id_token: str
    quantity_kind: CmdDiagnosticQuantity
    units: Literal["m3/s"] = "m3/s"


# Only the retained CMD 6.44 Figure 6.7 code-11 legend is characterised.
# Do not generalise to another subarea, reach, print mode or native profile.
_CMD_DIAGNOSTIC_LAYOUT: dict[int, tuple[str, CmdDiagnosticQuantity]] = {
    1: ("Sub-area inflow point, sub-area A - Upstream", "subarea_upstream_flow"),
    2: ("Sub-area inflow point, sub-area A - Rain ex.", "rainfall_excess_flow"),
    3: ("Normal storage, reach no. 0 1 - Downstream", "reach_downstream_flow"),
    4: ("Normal storage, reach no. 0 1 - Upstream", "reach_upstream_flow"),
    5: ("Calculated hydrograph,", "calculated_flow"),
}


def _has_cmd_diagnostic_legend(document: RorbDocument) -> bool:
    """Detect the diagnostic family, even if a member of its legend is malformed."""
    return any(
        str(row.get("description")).startswith("Sub-area inflow point, sub-area ")
        or (
            document.metadata.get("program_version") == "6.44"
            and str(row.get("description")).startswith("Normal storage, reach no.")
        )
        for section in document.sections
        if section.name == "sites"
        for row in section.rows
    )


def bind_output_site_columns(
    document: RorbDocument, *, table_name: str = "hydrographs_1", allow_unnamed: bool = False
) -> tuple[HydrographSiteColumn, ...]:
    """Bind ordinary physical output sites; never promote diagnostic flow identities."""
    if _has_cmd_diagnostic_legend(document):
        msg = "CMD diagnostic columns cannot be bound as ordinary physical print sites"
        raise ValueError(msg)
    return _bind_site_columns(document, table_name=table_name, allow_unnamed=allow_unnamed)


def _check_cmd_diagnostic_units(document: RorbDocument) -> None:
    """Require the retained three discharge-summary groups, without binding their scalars."""
    try:
        scalars = document.section("reported_scalars")
    except StopIteration as exc:
        msg = "Missing CMD diagnostic discharge summary groups"
        raise ValueError(msg) from exc
    peaks = [row for row in scalars.rows if row["family"] == "Peak discharge"]
    if (
        not scalars.valid
        or tuple(row["ordinal"] for row in peaks) != (1, 2, 1, 2, 1)
        or any(row["unit"] != "m³/s" for row in peaks)
    ):
        msg = "CMD diagnostic discharge units or summary group counts are unsupported"
        raise ValueError(msg)


def bind_cmd_diagnostic_columns(document: RorbDocument) -> tuple[CmdDiagnosticColumn, ...]:
    """Bind only the observed five-column report legend; never establish model or native parity.

    The banner and legend do not prove source control 11 or executable identity.
    Preserve the report's actual column order, raw IDs and source lines.
    """
    if document.metadata.get("program_version") != "6.44":
        msg = "CMD diagnostic output requires the characterised 6.44 report layout"
        raise ValueError(msg)
    sites = _bind_site_columns(document, allow_unnamed=True)
    if {_hyd_ordinal(site.site_id) for site in sites} != set(_CMD_DIAGNOSTIC_LAYOUT):
        msg = "Unsupported CMD diagnostic legend or column population"
        raise ValueError(msg)
    table = document.section("hydrographs_1")
    step = document.metadata.get("time_increment_raw")
    if (
        table.completeness != "reported_increment_count"
        or table.increment_origin != 1
        or not isinstance(step, str)
        or table.source_decimal(0, "Time") != exact_number(step)
    ):
        msg = "CMD diagnostic output requires a complete one-based report clock"
        raise ValueError(msg)
    _check_cmd_diagnostic_units(document)

    result: list[CmdDiagnosticColumn] = []
    for site in sites:
        description, kind = _CMD_DIAGNOSTIC_LAYOUT[_hyd_ordinal(site.site_id)]
        if " ".join(site.description.split()) != description:
            msg = f"Unsupported CMD diagnostic legend for {site.column}: {site.description}"
            raise ValueError(msg)
        if any(table.source_decimal(index, site.column) < 0 for index in range(len(table.rows))):
            msg = f"Unsupported negative CMD diagnostic flow in {site.column}"
            raise ValueError(msg)
        result.append(
            CmdDiagnosticColumn(
                site.site_id, site.column, site.description, site.site_record_line, site.site_id_token, kind
            )
        )
    return tuple(result)


def _record_cmd_diagnostic_columns(document: RorbDocument) -> None:
    """Expose report-local typed identities through the canonical JSON/CSV section views."""
    if not _has_cmd_diagnostic_legend(document):
        return
    document.issue(
        "cmd_diagnostic_report",
        "CMD diagnostic flows are not ordinary physical print sites; model binding remains unverified.",
    )
    section = Section(
        "cmd_diagnostic_sites",
        ["line", "id", "id_token", "column", "description", "quantity_kind", "units", "physical_site_verified"],
    )
    document.sections.append(section)
    try:
        columns = bind_cmd_diagnostic_columns(document)
    except ValueError as exc:
        section.valid = False
        document.issue("cmd_diagnostic_binding", str(exc))
        return
    for item in columns:
        section.rows.append(
            {
                "line": item.site_record_line,
                "id": item.site_id,
                "id_token": item.site_id_token,
                "column": item.column,
                "description": item.description,
                "quantity_kind": item.quantity_kind,
                "units": item.units,
                "physical_site_verified": False,
            }
        )
        section.source_tokens.append(
            {"id_token": item.site_id_token, "column": item.column, "description": item.description}
        )
    section.completeness = "observed_legend_binding"


def _numeric_table(doc: RorbDocument, start: int, columns: list[str], name: str) -> Section:
    table = Section(name, ["line", *columns])
    doc.sections.append(table)
    for i in range(start, len(doc.lines)):
        line = doc.lines[i]
        tokens = line.split()
        if not tokens:
            if table.rows:
                break
            continue
        if tokens[0] in {"Tot.", "Total", "End"} or tokens[0].startswith("Tot.") or line.strip().startswith("End of "):
            table.completeness = "terminated"
            break
        # A textual footer may end a table, but numeric-looking bad records must fail.
        if not re.match(r"^[\d+.*-]", tokens[0]) and table.rows:
            doc.issue("table_boundary", f"Unrecognized end of {name}; retained in raw text.", i + 1, error=True)
            table.valid = False
            break
        try:
            if len(tokens) != len(columns):
                msg = "Numeric record width differs from header."
                raise ValueError(msg)  # noqa: TRY301 -- caught locally to preserve the original row diagnostic
            row: Record = {"line": i + 1, columns[0]: integer(tokens[0])}
            row.update({c: number(v) for c, v in zip(columns[1:], tokens[1:], strict=True)})
            table.rows.append(row)
            table.source_tokens.append(dict(zip(columns, tokens, strict=True)))
        except ValueError as exc:
            table.valid = False
            doc.issue("output_record", f"{name}: {exc}", i + 1, error=True)
    return table


def _source_decimal(token: str) -> Decimal:
    """Read an already-validated numeric source token without binary rounding."""
    return Decimal(token.replace("D", "E").replace("d", "e"))


def _printed_resolution(value: Decimal) -> Decimal:
    """Return the resolution implied by the source's printed decimal places."""
    return Decimal(1).scaleb(int(value.as_tuple().exponent))


def _validate_reported_time_increment(doc: RorbDocument, table: Section, step_token: str) -> None:
    """Check the reported step using exact source decimals and printed rounding bounds."""
    step = _source_decimal(step_token)
    step_resolution = _printed_resolution(step)
    for previous, current in zip(table.rows, table.rows[1:], strict=False):
        previous_line = int(str(previous["line"]))
        current_line = int(str(current["line"]))
        previous_time = _source_decimal(doc.lines[previous_line - 1].split()[1])
        current_time = _source_decimal(doc.lines[current_line - 1].split()[1])
        tolerance = min(
            step / 2,
            (_printed_resolution(previous_time) + _printed_resolution(current_time) + step_resolution) / 2,
        )
        observed = current_time - previous_time
        if abs(observed - step) > tolerance:
            doc.issue(
                "time_increment_mismatch",
                f"{table.name}: observed {observed:g} h between rows, expected {step:g} h.",
                current_line,
                error=True,
            )
            table.valid = False


def _reported_scalars(doc: RorbDocument) -> None:
    """Collect generic reported scalar lexemes, not interpreted print-site bindings."""
    section = Section("reported_scalars", ["line", "family", "unit", "token", "character", "ordinal"])
    doc.sections.append(section)
    families = ("Peak discharge,", "Time to peak,", "Volume,")
    for index, line in enumerate(doc.lines):
        if not line.lstrip().startswith(families):
            continue
        match = re.match(r"^\s*(Peak discharge|Time to peak|Volume),(\S+)\s+", line)
        if match is None:
            doc.issue("reported_scalar_layout", "Scalar unit/value layout is unsupported.", index + 1, error=True)
            section.valid = False
            continue
        family, unit = match[1], match[2]
        values = list(re.finditer(r"\S+", line[match.end() :]))
        if not values:
            doc.issue("reported_scalar_values", "No reported scalar values.", index + 1, error=True)
            section.valid = False
        for ordinal, item in enumerate(values, 1):
            token = item[0]
            try:
                exact_number(token)
            except ValueError as exc:
                # Keep the invalid original token: generic source evidence must
                # never silently lose a failed scalar row.
                doc.issue("reported_scalar_value", str(exc), index + 1, error=True)
                section.valid = False
            section.rows.append(
                {
                    "line": index + 1,
                    "family": family,
                    "unit": unit,
                    "token": token,
                    "character": match.end() + item.start() + 1,
                    "ordinal": ordinal,
                }
            )
            section.source_tokens.append({"value": token})
    section.completeness = "observed_scalar_lines"


def _rainfall_header_start(doc: RorbDocument, index: int) -> int | None:
    """Recognise the observed catchment/subarea and uniform catchment header forms."""
    labels = doc.lines[index].split()
    if labels in (["Incs", "ment"], ["incs", "ment"]):
        if index >= 1 and doc.lines[index - 1].split() == ["Time", "Catch"]:
            return index - 1
        if index >= 2 and doc.lines[index - 2].split() == ["Time"] and doc.lines[index - 1].split() == ["Catch"]:
            return index - 2
        return None
    if (
        labels[:2] == ["Incs", "ment"]
        and len(labels) > 2
        and index >= 2
        and doc.lines[index - 2].split() == ["Time", "Sub-"]
        and doc.lines[index - 1].split() == ["Catch", "Area"]
    ):
        return index - 2
    return None


def _rainfall_columns(doc: RorbDocument, index: int) -> list[str] | None:
    labels = doc.lines[index].split()
    if len(labels) == 2:
        return ["Inc", "Catchment_mm"] if _rainfall_header_start(doc, index) is not None else None
    if labels[:2] != ["Incs", "ment"]:
        return None
    areas = labels[2:]
    if any(re.fullmatch(r"[A-Za-z]+", a) is None for a in areas) or len(set(areas)) != len(areas):
        return None
    return ["Inc", "Catchment_mm", *[f"Subarea_{a}_mm" for a in areas]]


def _next_nonblank(doc: RorbDocument, index: int) -> int:
    while index < len(doc.lines) and not doc.lines[index].strip():
        index += 1
    return index


def _rainfall_page_end(doc: RorbDocument, table: Section) -> int | None:
    """Bind the printed total separately from interval tokens and find the next page."""
    if not table.valid or not table.rows:
        return None
    index = _next_nonblank(doc, int(str(table.rows[-1]["line"])))
    if index >= len(doc.lines):
        return None
    footer = doc.lines[index].strip()
    if not footer.startswith("Tot."):
        return None
    # RORB may fill the catchment field completely, e.g. Tot.105.0.
    tokens = footer.removeprefix("Tot.").split()
    if len(tokens) != len(table.columns) - 2:
        return None
    try:
        if any(number(token) < 0 for token in tokens):
            return None
    except ValueError:
        return None
    for column, token in zip(table.columns[2:], tokens, strict=True):
        doc.metadata[f"{table.name}_reported_total_{column}"] = token
    doc.metadata[f"{table.name}_total_line"] = index + 1
    index = _next_nonblank(doc, index + 1)
    if index < len(doc.lines) and doc.lines[index].split()[:3] == ["Pluvi.", "ref.", "no."]:
        index = _next_nonblank(doc, index + 1)
    return index


def _read_rainfall_table(doc: RorbDocument, header: int, name: str) -> Section | None:
    columns = _rainfall_columns(doc, header)
    if columns is None:
        return None
    table = _numeric_table(doc, header + 1, columns, name)
    if table.rows:
        validate_series(doc, table, "Inc")
    return table


def _read_rainfall_pages(doc: RorbDocument, index: int, name: str) -> None:
    """Retain existing numbered first pages; add separately named continuation pages."""
    doc.metadata[f"{name}_meaning"] = doc.lines[index].strip()
    candidates = [
        j
        for j in range(index + 1, min(index + 7, len(doc.lines)))
        if doc.lines[j].split()[:2] == ["Incs", "ment"] or doc.lines[j].split() == ["incs", "ment"]
    ]
    table = _read_rainfall_table(doc, candidates[0], name) if len(candidates) == 1 else None
    if table is None:
        doc.issue("unsupported_rainfall", "Rainfall header layout unsupported; raw block preserved.", index + 1)
        return
    header = candidates[0]
    if _rainfall_header_start(doc, header) != _next_nonblank(doc, index + 1):
        return
    pages = 1
    while True:
        boundary = _rainfall_page_end(doc, table)
        if boundary is None or boundary >= len(doc.lines):
            return
        next_line = doc.lines[boundary].strip()
        if next_line.startswith(("Rainfall, mm, in time inc.", "Rainfall-excess, mm, in time inc.")) or (
            next_line == "Routing results:"
        ):
            doc.metadata[f"{name}_page_count"] = pages
            return
        header = boundary + 2
        if len(table.columns) <= 3 or header >= len(doc.lines) or _rainfall_header_start(doc, header) != boundary:
            return
        pages += 1
        next_table = _read_rainfall_table(doc, header, f"{name}_page_{pages}")
        if next_table is None or len(next_table.columns) <= 3:
            return
        table = next_table


def _record_rainfall_clock(doc: RorbDocument) -> None:
    """Admit only a unique global printed rainfall horizon and time increment."""
    times = [line.strip() for line in doc.lines if line.lstrip().startswith("Rainfall times:")]
    steps = [line for line in doc.lines if line.lstrip().startswith("Time increment (hours)")]
    if len(times) != 1 or len(steps) != 1:
        return
    match = re.fullmatch(r"Rainfall times:\s*(\d+)\s+(\d+)", times[0])
    if match is not None and isinstance(doc.metadata.get("time_increment_raw"), str):
        doc.metadata["rainfall_start_increment"] = int(match[1])
        doc.metadata["rainfall_finish_increment"] = int(match[2])


def read_output(doc: RorbDocument) -> None:  # noqa: C901 - preserve ordered format state and diagnostic scope
    """Read named hydrographs and supported rainfall tables; retain all other source lines."""
    report_metadata(doc)
    _reported_scalars(doc)
    doc.metadata["hydrograph_summary_count"] = sum(line.strip() == "Hydrograph summary" for line in doc.lines)
    doc.metadata["engine_identity"] = "unverified_from_report_banner"
    sites = read_sites(doc, "Site", "Hyd")
    messages = Section("reported_messages", ["line", "text"])
    doc.sections.append(messages)
    timestep: float | None = None
    timestep_text: str | None = None
    expected_last: int | None = None
    hydrograph_count = 0
    hydrograph_summaries: list[Section] = []
    rainfall_count = 0
    for i, line in enumerate(doc.lines):
        if re.search(r"\b(?:warning|error)\b", line, re.IGNORECASE):
            messages.rows.append({"line": i + 1, "text": line})
        match = re.fullmatch(r"\s*Time increment \(hours\)\s*=\s*(\S+)\s*", line)
        if match:
            try:
                value = number(match[1])
                if value <= 0 or (timestep is not None and timestep != value):
                    msg = "Invalid or conflicting time increment."
                    raise ValueError(msg)  # noqa: TRY301 -- caught locally to preserve the original report diagnostic
                timestep = value
                timestep_text = match[1]
                doc.metadata["time_increment_hours"] = timestep
                doc.metadata["time_increment_raw"] = match[1]
            except ValueError as exc:
                doc.issue("time_increment", str(exc), i + 1, error=True)
        match = re.fullmatch(r"\s*Duration of calculations:\s*(\d+)\s*", line)
        if match:
            value = int(match[1])
            if expected_last is not None and value != expected_last:
                doc.issue("calculation_duration", "Conflicting calculation durations.", i + 1, error=True)
            expected_last = value
            doc.metadata["reported_duration_increments"] = value
            doc.metadata["reported_duration_raw"] = match[1]
        tokens = line.split()
        if tokens[:2] == ["Inc", "Time"]:
            hydrograph_count += 1
            if (
                len(tokens) < 3
                or len(set(tokens)) != len(tokens)
                or any(re.fullmatch(r"Hyd\d+", t) is None for t in tokens[2:])
            ):
                doc.issue("output_header", "Unsupported hydrograph summary header.", i + 1, error=True)
                continue
            table = _numeric_table(doc, i + 1, tokens, f"hydrographs_{hydrograph_count}")
            hydrograph_summaries.append(table)
            validate_series(doc, table, "Time")
            ordinals = [int(token[3:]) for token in tokens[2:]]
            if 0 in ordinals or len(set(ordinals)) != len(ordinals):
                doc.issue(
                    "hydrograph_column_ambiguous",
                    "Repeated or zero Hyd ordinal with alternate zero padding.",
                    i + 1,
                    error=True,
                )
                table.valid = False
            normalized = {f"Hyd{value:04d}" for value in ordinals}
            if normalized != {r["id"] for r in sites.rows}:
                # A table's numeric validity is independent of physical
                # print-site interpretation. The latter remains unresolved.
                doc.issue(
                    "site_mapping",
                    "Printed Hyd labels lack a complete independently verified site mapping.",
                    i + 1,
                )
            if table.rows:
                # Observed RORBWin summaries use 0..N; retained CMD 6.44
                # summaries use 1..N+1. Neither source clock is shifted.
                origin = int(str(table.rows[0]["Inc"]))
                table.increment_origin = origin
                doc.metadata[f"{table.name}_increment_origin"] = origin
                if origin not in (0, 1):
                    doc.issue(
                        "increment_origin",
                        "Only characterised increment origins 0 and 1 are supported.",
                        i + 1,
                        error=True,
                    )
                    table.valid = False
            if expected_last is not None and table.rows:
                origin = table.increment_origin
                if (
                    origin is None
                    or origin not in (0, 1)
                    or table.rows[-1]["Inc"] != expected_last + origin
                    or len(table.rows) != expected_last + 1
                ):
                    doc.issue(
                        "incomplete_hydrograph",
                        "Rows do not cover the reported calculation increments.",
                        i + 1,
                        error=True,
                    )
                    table.valid = False
                else:
                    table.completeness = "reported_increment_count"
            else:
                doc.issue("completion_unverified", "No calculation count to verify hydrograph completion.", i + 1)
        if line.strip().startswith(("Rainfall, mm, in time inc.", "Rainfall-excess, mm, in time inc.")):
            rainfall_count += 1
            _read_rainfall_pages(doc, i, f"rainfall_{rainfall_count}")
    _record_rainfall_clock(doc)
    if timestep_text is not None:
        for table in hydrograph_summaries:
            _validate_reported_time_increment(doc, table, timestep_text)
    if hydrograph_count == 0:
        doc.issue(
            "no_hydrograph_summary", "No supported numeric hydrograph summary; output detail or run mode may differ."
        )
    if hydrograph_count == 0 and "Vector file" not in doc.metadata and "Storm file" not in doc.metadata:
        doc.issue(
            "output_structure",
            "Output signature lacks corroborating version and report sections.",
            error=True,
        )
    if hydrograph_count > 1:
        doc.issue(
            "multiple_summaries",
            "Multiple summaries retained separately; site/parameter scope requires review.",
            error=True,
        )
    doc.metadata["hydrograph_time_unit"] = "hours"
    _record_cmd_diagnostic_columns(doc)
    doc.issue(
        "uninterpreted_sections",
        "Routing instructions, other input/output sections and unsupported tables remain in raw text.",
    )
