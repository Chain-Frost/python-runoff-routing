"""Verify printed interval timing, page selection, depth and the actual BC data CSV."""

from __future__ import annotations

import csv
import io
from decimal import Decimal
from itertools import pairwise
from pathlib import Path

import pytest

from runoff_routing.rorb_readers.readers import read_rorb_bytes, read_rorb_file
from runoff_routing.tuflow_rainfall import (
    RainfallExportError,
    RainfallKind,
    build_tuflow_rainfall,
    export_tuflow_rainfall,
    main,
)

_GROSS = "Rainfall, mm, in time inc. following time shown"
_EXCESS = "Rainfall-excess, mm, in time inc. following time shown"
_PREFIX = (
    "RORBWin Output File\nProgram version 6.52\nVector file : synthetic.catg\n"
    "Time increment (hours)= 0.125\nRainfall times: 0 3\n"
)
_HEADER = " Time Sub-\n Catch Area\n Incs ment "
_GROSS_PAGES = (
    f"{_GROSS}\n{_HEADER}A B\n\n"
    "0 2.00 3.00 1.25\n1 0.00 0.00 0.00\n2 4.00 1.25 5.50\n\n"
    "Tot. 6.00 4.25 6.75\nPluvi. ref. no. 1 2\n\n"
    f"{_HEADER}Q\n\n0 2.00 2.5\n1 0.00 0.0\n2 4.00 7.5\n\nTot. 6.00 10.0\n"
)
_EXCESS_PAGE = (
    f"{_EXCESS}\n{_HEADER}A B Q\n\n"
    "0 1.00 1.50 0.50 1.0\n1 0.00 0.00 0.00 0.0\n2 0.00 0.00 0.00 0.0\n\n"
    "Tot. 1.00 1.50 0.50 1.0\n"
)
_REPORT = _PREFIX + _GROSS_PAGES + _EXCESS_PAGE + "\nRouting results:\n"
_COLUMNS = ("Subarea_A_mm", "Subarea_B_mm", "Subarea_Q_mm", "Catchment_mm")
_EXPECTED = (
    "Time_hours,Subarea_A_mm,Subarea_B_mm,Subarea_Q_mm,Catchment_mm\n"
    "0.000,0,0,0,0\n"
    "0.125,3.00,1.25,2.5,2.00\n"
    "0.250,0.00,0.00,0.0,0.00\n"
    "0.375,1.25,5.50,7.5,4.00\n"
    "0.500,0,0,0,0\n"
)


def test_gross_multicolumn_csv_and_stepped_depth_conservation(tmp_path: Path) -> None:
    source = tmp_path / "rain.out"
    original = _REPORT.encode()
    source.write_bytes(original)
    output = tmp_path / "rain.csv"
    boundary = export_tuflow_rainfall(source, output, kind="gross", columns=_COLUMNS)
    assert boundary.section == "rainfall_1"
    assert boundary.clock_basis == "reported"
    assert boundary.reported_step_hours == boundary.step_hours == Decimal("0.125")
    assert boundary.start_increment == 0
    assert boundary.finish_increment == 3
    assert boundary.trailing_zero_added
    assert boundary.totals_mm == tuple(map(Decimal, ("4.25", "6.75", "10.0", "6.00")))
    assert boundary.reported_totals_mm == boundary.totals_mm
    assert output.read_bytes() == _EXPECTED.encode()
    assert source.read_bytes() == original
    # Independent BC-data consumer: each noninitial depth belongs to the previous interval.
    rows = list(csv.DictReader(io.StringIO(output.read_text(encoding="utf-8"))))
    for column, expected in zip(_COLUMNS, boundary.totals_mm, strict=True):
        applied = Decimal(0)
        for earlier, later in pairwise(rows):
            dt = Decimal(later["Time_hours"]) - Decimal(earlier["Time_hours"])
            rate = Decimal(later[column]) / dt
            applied += rate * dt
        assert applied == expected
    with pytest.raises(FileExistsError):
        export_tuflow_rainfall(source, output, kind="excess", columns=_COLUMNS)
    assert output.read_bytes() == _EXPECTED.encode()


def test_excess_is_not_gross_and_existing_dry_end_needs_no_padding() -> None:
    document = read_rorb_bytes(_REPORT.encode())
    assert document.section("rainfall_1").columns[-2:] == ["Subarea_A_mm", "Subarea_B_mm"]
    assert document.section("rainfall_1_page_2").columns[-1] == "Subarea_Q_mm"
    boundary = build_tuflow_rainfall(document, kind="excess", columns=("Subarea_A_mm",))
    assert boundary.section == "rainfall_2"
    assert boundary.totals_mm == (Decimal("1.50"),)
    assert not boundary.trailing_zero_added
    assert boundary.to_csv() == "Time_hours,Subarea_A_mm\n0.000,0\n0.125,1.50\n0.250,0.00\n0.375,0.00\n"
    with pytest.raises(RainfallExportError, match="does not identify"):
        build_tuflow_rainfall(document, kind="excess", columns=_COLUMNS, section=1)


def test_repeated_section_requires_explicit_selection() -> None:
    document = read_rorb_bytes((_PREFIX + _GROSS_PAGES + _GROSS_PAGES + "\nRouting results:\n").encode())
    with pytest.raises(RainfallExportError, match="explicitly select"):
        build_tuflow_rainfall(document, kind="gross", columns=_COLUMNS)
    boundary = build_tuflow_rainfall(document, kind="gross", columns=_COLUMNS, section=2)
    assert boundary.section == "rainfall_2"
    assert boundary.to_csv() == _EXPECTED


def test_nonzero_declared_start_preserved_without_clock_reset() -> None:
    report = (
        _PREFIX.replace("0 3", "2 4") + f"{_GROSS}\n{_HEADER}A\n\n2 3 2.5\n3 4 3.5\n\nTot. 7 6.0\nRouting results:\n"
    )
    boundary = build_tuflow_rainfall(read_rorb_bytes(report.encode()), kind="gross", columns=("Subarea_A_mm",))
    assert boundary.to_csv() == "Time_hours,Subarea_A_mm\n0.250,0\n0.375,2.5\n0.500,3.5\n0.625,0\n"


@pytest.mark.parametrize(
    ("original", "replacement", "message"),
    [
        ("following time shown", "before time shown", "Unsupported interval timing"),
        ("Rainfall times: 0 3", "Rainfall times: 0 4", "Incomplete or invalid rainfall interval"),
        ("Rainfall times: 0 3", "Rainfall times: 0 3\nRainfall times: 0 3", "complete declared rainfall horizon"),
        (
            "Time increment (hours)= 0.125",
            "Time increment (hours)= 0.125\nTime increment (hours)= 0.25",
            "structurally valid",
        ),
        ("Time increment (hours)= 0.125", "Time increment (hours)= 0", "structurally valid"),
        ("0 2.00 3.00 1.25", "0 2.00 *** 1.25", "structurally valid"),
        ("0 2.00 3.00 1.25", "0 2.00 -3.00 1.25", "nonnegative finite decimals"),
        ("\n1 0.00 0.00 0.00\n", "\n\n", "Missing complete rainfall page"),
        ("2 4.00 1.25 5.50", "3 4.00 1.25 5.50", "structurally valid"),
        ("Tot. 6.00 4.25 6.75", "Tot. 6.00 4.25", "Missing complete rainfall page"),
        ("Tot. 6.00 10.0", "Tot. 6.00 malformed", "Missing complete rainfall page"),
        ("Incs ment Q", "Incs ment A", "Ambiguous repeated rainfall column"),
        ("0 2.00 2.5", "0 3.00 2.5", "Conflicting repeated catchment rainfall"),
        ("Incs ment Q", "Incs other Q", "Missing complete rainfall page"),
        ("2 4.00 7.5", "2 4.00", "structurally valid"),
    ],
)
def test_bad_or_unidentified_report_refuses_without_creating_output(
    tmp_path: Path, original: str, replacement: str, message: str
) -> None:
    assert original in _REPORT
    source = tmp_path / "bad.out"
    source.write_text(_REPORT.replace(original, replacement), encoding="utf-8")
    output = tmp_path / "bad.csv"
    with pytest.raises(RainfallExportError, match=message):
        export_tuflow_rainfall(source, output, kind="gross", columns=_COLUMNS)
    assert not output.exists()


def test_rounded_step_with_cumulative_clock_drift_refuses() -> None:
    report = _REPORT + "\nHydrograph summary\nInc Time Hyd0001\n0 0.00 0\n1 0.12 0\n2 0.24 0\n3 0.36 0\n\n"
    with pytest.raises(RainfallExportError, match="cumulative OUT clock"):
        build_tuflow_rainfall(read_rorb_bytes(report.encode()), kind="gross", columns=_COLUMNS)


@pytest.mark.parametrize("columns", [(), ("Hyd001",), ("Subarea_A_mm", "Subarea_A_mm"), ("Subarea_Z_mm",)])
def test_unknown_ambiguous_or_discharge_column_refuses(columns: tuple[str, ...]) -> None:
    with pytest.raises(RainfallExportError, match=r"Select at least one unique|Unknown rainfall column"):
        build_tuflow_rainfall(read_rorb_bytes(_REPORT.encode()), kind="gross", columns=columns)


def test_cli_requires_selection_and_writes_literal_csv(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    source = tmp_path / "rain.out"
    source.write_text(_REPORT, encoding="utf-8")
    output = tmp_path / "rain.csv"
    args = [str(source), str(output), "--kind", "gross"]
    with pytest.raises(SystemExit) as missing:
        main(args)
    assert missing.value.code == 2
    assert not output.exists()
    for column in _COLUMNS:
        args.extend(("--column", column))
    assert main(args) == 0
    assert output.read_bytes() == _EXPECTED.encode()
    assert "Subarea_Q_mm: printed increments 10.0 mm" in capsys.readouterr().out


def test_source_and_destination_protection(tmp_path: Path) -> None:
    source = tmp_path / "report.csv"
    original = _REPORT.encode()
    source.write_bytes(original)
    with pytest.raises(FileExistsError):
        export_tuflow_rainfall(source, source, kind="gross", columns=_COLUMNS)
    assert source.read_bytes() == original
    with pytest.raises(RainfallExportError, match="csv extension"):
        export_tuflow_rainfall(source, tmp_path / "report.out", kind="gross", columns=_COLUMNS)
    assert not (tmp_path / "report.out").exists()


def test_explicit_timestep_needs_complete_clock() -> None:
    with pytest.raises(RainfallExportError, match="requires a complete OUT clock"):
        build_tuflow_rainfall(
            read_rorb_bytes(_REPORT.encode()), kind="gross", columns=_COLUMNS, exact_step_hours=Decimal("0.125")
        )


def test_cli_caller_verified_exact_timestep(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    report = _REPORT.replace("0.125", "0.12") + (
        "\nDuration of calculations: 3\nHydrograph summary\nInc Time Hyd0001\n0 0.00 0\n"
        "1 0.12 0\n2 0.25 0\n3 0.38 0\n\n"
    )
    source = tmp_path / "rounded.out"
    source.write_text(report, encoding="utf-8")
    output = tmp_path / "rain.csv"
    args = [str(source), str(output), "--kind", "gross", "--column", "Subarea_A_mm"]
    with pytest.raises(SystemExit) as default_refused:
        main(args)
    assert default_refused.value.code == 2
    assert not output.exists()
    assert main([*args, "--exact-step-hours", "0.125"]) == 0
    assert output.read_text(encoding="utf-8") == (
        "Time_hours,Subarea_A_mm\n0.000,0\n0.125,3.00\n0.250,0.00\n0.375,1.25\n0.500,0\n"
    )
    assert "Timestep: 0.125 h (caller_exact); report: 0.12 h" in capsys.readouterr().out


def _five_minute_report(header: str, *, weighted: bool, footer: str) -> str:
    """Artificial shape from the native-layout report; no unpublished source depths copied."""
    depths = ("11.6", "0.0", *("10.0",) * 8, "5.0", "8.4")
    records = [
        f"{i} {depth} {Decimal(depth):.0f} {Decimal(depth):.0f}" if weighted else f"{i} {depth}"
        for i, depth in enumerate(depths)
    ]
    times = [f"{i} {Decimal(i) / 12:.2f} 0.0" for i in range(201)]
    return "\n".join(
        (
            _PREFIX.replace("0.125", "0.08").replace("0 3", "0 12").rstrip(),
            _GROSS,
            header,
            "",
            *records,
            "",
            footer,
            "",
            "Routing results:",
            "Duration of calculations: 200",
            "Hydrograph summary",
            "Inc Time Hyd0001",
            *times,
            "",
            "",
        )
    )


@pytest.mark.parametrize("header", ["Time\nCatch\nIncs ment", "Time Catch\nIncs ment", "Time\nCatch\nincs ment"])
def test_uniform_catchment_only_compact_total(header: str) -> None:
    report = _five_minute_report(header, weighted=False, footer="Tot.105.0")
    document = read_rorb_bytes(report.encode())
    assert document.section("rainfall_1").columns == ["line", "Inc", "Catchment_mm"]
    with pytest.raises(RainfallExportError, match="cumulative OUT clock"):
        build_tuflow_rainfall(document, kind="gross", columns=("Catchment_mm",))
    result = build_tuflow_rainfall(
        document, kind="gross", columns=("Catchment_mm",), exact_step_hours=Decimal("0.08333333333")
    )
    assert result.totals_mm == result.reported_totals_mm == (Decimal("105.0"),)
    assert result.rows[1].time_hours == Decimal("0.08333333333")
    assert result.rows[1].depths_mm == (Decimal("11.6"),)
    assert result.rows[2].depths_mm == (Decimal("0.0"),)
    assert result.rows[12].time_hours == Decimal("0.99999999996")
    assert result.rows[12].depths_mm == (Decimal("8.4"),)
    assert result.rows[-1].time_hours == Decimal("1.08333333329")
    assert result.rows[-1].depths_mm == (Decimal(0),)
    with pytest.raises(RainfallExportError, match="Unknown rainfall column"):
        build_tuflow_rainfall(
            document, kind="gross", columns=("Subarea_A_mm",), exact_step_hours=Decimal("0.08333333333")
        )


@pytest.mark.parametrize("footer", ["Tot.105.0 105 105", "Tot. 105.0 105 105"])
def test_weighted_report_compact_or_spaced_total(footer: str) -> None:
    report = _five_minute_report(_HEADER + "A B", weighted=True, footer=footer)
    result = build_tuflow_rainfall(
        read_rorb_bytes(report.encode()),
        kind="gross",
        columns=("Catchment_mm", "Subarea_A_mm", "Subarea_B_mm"),
        exact_step_hours=Decimal("0.08333333333"),
    )
    assert result.totals_mm == result.reported_totals_mm == (Decimal("105.0"), Decimal(105), Decimal(105))
    assert result.rows[1].depths_mm == (Decimal("11.6"), Decimal(12), Decimal(12))
    assert result.rows[12].depths_mm == (Decimal("8.4"), Decimal(8), Decimal(8))


@pytest.mark.parametrize(
    ("header", "footer"),
    [
        ("Time\nUnknown\nIncs ment", "Tot.105.0"),
        ("Time\nCatch\nIncs ment", "Tot.105.0 105"),
        ("Time\nCatch\nIncs ment", "Tot.invalid"),
        ("Time\nCatch\nIncs ment", "Tot.-105.0"),
    ],
)
def test_uniform_report_rejects_unidentified_header_or_total(header: str, footer: str) -> None:
    report = _five_minute_report(header, weighted=False, footer=footer)
    with pytest.raises(RainfallExportError, match="Missing complete rainfall page"):
        build_tuflow_rainfall(
            read_rorb_bytes(report.encode()),
            kind="gross",
            columns=("Catchment_mm",),
            exact_step_hours=Decimal("0.08333333333"),
        )


_ROOT = Path(__file__).absolute().parents[1]
_CMD = (
    _ROOT
    / "tests/fixtures/regression-v1/native-cmd/objects"
    / "00ffce5b02f4972c3db08a9d4811b25320af513f9073f1373daa901f0d40c8d9.out"
)
_645 = _ROOT / ".local/reader-test-data/RORB/6.45-490-event-reader-example/RORB_14141_ aep10_du12hourtp1.out"
_652 = _ROOT / ".local/reader-test-data/RORB/12hr-areal-example/Fig6_7_ aep0p2EY_du12hourtp1.out"


@pytest.mark.parametrize(
    ("path", "column", "kind", "count", "first", "last", "total", "reported"),
    [
        (_CMD, "Subarea_A_mm", "gross", 72, "0", "4", "69", "69"),
        (_CMD, "Catchment_mm", "excess", 72, "0.0", "3.4", "58.5", "58.3"),
        (_645, "Subarea_Q_mm", "gross", 24, "2", "4", "92", "93"),
        (_645, "Subarea_X_mm", "excess", 24, "0", "0", "4", "4"),
        (_652, "Subarea_A_mm", "gross", 72, "0", "3", "47", "51"),
        (_652, "Catchment_mm", "excess", 72, "0.0", "1.7", "22.2", "22.1"),
    ],
)
def test_retained_report_printed_depths(
    path: Path, column: str, kind: RainfallKind, count: int, first: str, last: str, total: str, reported: str
) -> None:
    if path != _CMD and not path.is_file():
        pytest.skip("Pinned public RORBWin reader fixture checkout unavailable")
    result = build_tuflow_rainfall(read_rorb_file(path), kind=kind, columns=(column,))
    assert result.start_increment == 0
    assert result.finish_increment == count
    assert result.rows[0].time_hours == 0
    assert result.rows[0].depths_mm == (Decimal(0),)
    assert result.rows[1].time_hours == Decimal("0.50")
    assert result.rows[1].depths_mm == (Decimal(first),)
    assert result.rows[count].time_hours == Decimal("0.50") * count
    assert result.rows[count].depths_mm == (Decimal(last),)
    assert result.totals_mm == (Decimal(total),)
    assert result.reported_totals_mm == (Decimal(reported),)
    assert len(result.rows) == count + 1 + int(Decimal(last) != 0)
    assert result.rows[-1].depths_mm == (Decimal(0),)


@pytest.mark.parametrize(
    ("name", "count", "first", "last", "total"),
    [
        ("437bd8d073280c9f2a5939d01b560c8c606f0df2c0dab26bdab37812a412b166", 5, 3, 7, 13),
        ("1507a183b2b21247d217184026f60d20de434d191c84da61dc82726f57048450", 96, 1, 1, 96),
    ],
)
def test_original_rounded_clock_requires_explicit_source_step(
    name: str, count: int, first: int, last: int, total: int
) -> None:
    document = read_rorb_file(_CMD.with_name(f"{name}.out"))
    assert document.sha256 == name
    with pytest.raises(RainfallExportError, match="cumulative OUT clock"):
        build_tuflow_rainfall(document, kind="gross", columns=("Subarea_A_mm",))
    with pytest.raises(RainfallExportError, match="printed timestep resolution"):
        build_tuflow_rainfall(document, kind="gross", columns=("Subarea_A_mm",), exact_step_hours=Decimal("0.13"))
    with pytest.raises(RainfallExportError, match="cumulative OUT clock"):
        build_tuflow_rainfall(document, kind="gross", columns=("Subarea_A_mm",), exact_step_hours=Decimal("0.124"))
    # The existing public register binds each original report to a 0.125 h source STM.
    result = build_tuflow_rainfall(document, kind="gross", columns=("Subarea_A_mm",), exact_step_hours=Decimal("0.125"))
    assert result.reported_step_hours == Decimal("0.12")
    assert result.step_hours == Decimal("0.125")
    assert result.clock_basis == "caller_exact"
    assert result.finish_increment == count
    assert result.rows[1].time_hours == Decimal("0.125")
    assert result.rows[1].depths_mm == (Decimal(first),)
    assert result.rows[count].time_hours == Decimal("0.125") * count
    assert result.rows[count].depths_mm == (Decimal(last),)
    assert result.totals_mm == (Decimal(total),)
    assert result.rows[-1].time_hours == Decimal("0.125") * (count + 1)
    assert result.rows[-1].depths_mm == (Decimal(0),)
