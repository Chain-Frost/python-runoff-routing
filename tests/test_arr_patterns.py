"""Synthetic ARR pattern parsing and intentionally gross rainfall disaggregation."""

from __future__ import annotations

import hashlib
import io
import stat
import zipfile
from dataclasses import FrozenInstanceError
from decimal import Decimal
from pathlib import Path

import pytest

from runoff_routing.arr_data import ARRFormatError
from runoff_routing.arr_import import parse_arr_json
from runoff_routing.arr_patterns import parse_pattern_csv, parse_pattern_zip, read_pattern_file
from runoff_routing.arr_storm import storm_from_arr_2026, storm_from_bom
from runoff_routing.bom_ifd import parse_bom_ifd_csv


def _point_csv(*, event_id: str = "0004", duration: int = 1440, timestep: int = 360) -> bytes:
    return (
        "EventID,Duration,TimeStep,Region,AEP,Increments\r\n"
        f"{event_id},{duration},{timestep},SYNTHETIC_REGION,intermediate,10,20,30,40\r\n"
    ).encode()


def _areal_csv() -> bytes:
    return (
        b"EventID,Duration,TimeStep,Region,Area,AEP,Increments\r\n"
        b"7,60,15,SYNTHETIC_REGION,100-200,frequent,25,25,25,25\r\n"
    )


def _bom() -> bytes:
    return (
        b"Synthetic BoM example, NOT a real BoM export\n"
        b"IFD Design Rainfall Depth (mm)\n"
        b"Issued:,12 November 2026\n"
        b"Location Label:,SYNTHETIC EXAMPLE ONLY\n"
        b"Requested coordinate:,Latitude,-33.5,Longitude,115.25\n"
        b"Nearest grid cell:,Latitude,33.5125 (S),Longitude,115.2375 (E)\n"
        b",,Annual Exceedance Probability (AEP)\n"
        b"Duration,Duration in min,50%,1%\n"
        b"24 hour,1440,30.0,45.5\n"
    )


def _archive(members: list[tuple[str, bytes]]) -> bytes:
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in members:
            archive.writestr(name, data)
    return stream.getvalue()


def test_point_pattern_exact_identity_and_percentages() -> None:
    raw = _point_csv()
    result = parse_pattern_csv(raw, kind="point", locator="synthetic-point.csv")
    assert result.kind == "point"
    assert result.source_sha256 == hashlib.sha256(raw).hexdigest()
    assert result.raw_bytes == raw
    assert result.members[0].byte_length == len(raw)
    pattern = result.patterns[0]
    assert pattern.event_id == "0004"  # Original ID, not a numeric ordinal.
    assert pattern.aep_band == "intermediate"
    assert pattern.region == "SYNTHETIC_REGION"
    assert pattern.duration_min == 1440
    assert pattern.timestep_min == 360
    assert pattern.increments_percent == tuple(Decimal(x) for x in (10, 20, 30, 40))
    with pytest.raises(FrozenInstanceError):
        pattern.event_id = "replacement"  # pyright: ignore[reportAttributeAccessIssue] -- frozen runtime test


def test_areal_bin_is_explicit_and_not_converted_to_area() -> None:
    result = parse_pattern_csv(_areal_csv(), kind="areal")
    assert result.patterns[0].area_bin == "100-200"
    with pytest.raises(ARRFormatError, match="column order"):
        parse_pattern_csv(_areal_csv(), kind="point")
    with pytest.raises(ARRFormatError, match="column order"):
        parse_pattern_csv(_point_csv(), kind="areal")


def test_point_zip_preserves_order_and_member_hashes() -> None:
    first = _point_csv(event_id="0004")
    second = _point_csv(event_id="0230")
    raw = _archive([("west_Increments.csv", first), ("subdirectory/east_Increments.csv", second)])
    result = parse_pattern_zip(raw, kind="point", locator="TP.zip")
    assert result.source_sha256 == hashlib.sha256(raw).hexdigest()
    assert result.raw_bytes == raw
    assert [source.locator for source in result.members] == [
        "west_Increments.csv",
        "subdirectory/east_Increments.csv",
    ]
    assert result.members[0].sha256 == hashlib.sha256(first).hexdigest()
    assert [pattern.event_id for pattern in result.patterns] == ["0004", "0230"]


def test_csv_file_reader_is_read_only(tmp_path: Path) -> None:
    path = tmp_path / "SYNTHETIC_Increments.csv"
    raw = _point_csv()
    path.write_bytes(raw)
    assert read_pattern_file(path, kind="point").raw_bytes == raw
    assert path.read_bytes() == raw


@pytest.mark.parametrize(
    ("old", "new", "message"),
    [
        ("intermediate", "unknown", "AEP bin"),
        ("10,20,30,40", "10,20,30", "increment count"),
        ("10,20,30,40", "10,20,30,-1", "negative"),
        ("10,20,30,40", "10,20,30,NaN", "Nonfinite"),
        ("10,20,30,40", "10,20,30,45", "sum"),
        ("10,20,30,40", "10,,20,30,40", "interior"),
        ("1440,360", "1440,400", "divisible"),
        ("1440,360", "1440,240", "increment count"),
        ("0004", "", "metadata"),
    ],
)
def test_invalid_pattern_csv(old: str, new: str, message: str) -> None:
    with pytest.raises(ARRFormatError, match=message):
        parse_pattern_csv(_point_csv().replace(old.encode(), new.encode()), kind="point")


def test_duplicate_pattern_identity_is_not_renumbered() -> None:
    duplicate = _point_csv() + b"0004,1440,360,SYNTHETIC_REGION,intermediate,10,20,30,40\r\n"
    with pytest.raises(ARRFormatError, match="Duplicate"):
        parse_pattern_csv(duplicate, kind="point")


def test_declared_rounding_budget_and_strict_storm_balance() -> None:
    raw = _point_csv().replace(b"10,20,30,40", b"10,20,30,39.98")
    with pytest.raises(ARRFormatError, match="sum"):
        parse_pattern_csv(raw, kind="point")
    accepted = parse_pattern_csv(raw, kind="point", rounding_budget_percent=Decimal("0.02"))
    assert accepted.patterns[0].increments_percent[-1] == Decimal("39.98")
    with pytest.raises(ARRFormatError, match="rounding budget"):
        parse_pattern_csv(_point_csv(), kind="point", rounding_budget_percent=Decimal("NaN"))


@pytest.mark.parametrize(
    "name",
    [
        "../outside_Increments.csv",
        r"C:\outside_Increments.csv",
        "/root_Increments.csv",
        "./ok_Increments.csv",
        "dir//bad_Increments.csv",
        "dir\\bad_Increments.csv",
    ],
)
def test_zip_rejects_unsafe_member_paths(name: str) -> None:
    # ZipInfo normalises backslash separators on Windows before writing. Patch the
    # same-length stored names in both ZIP headers so the parser sees hostile bytes.
    safe_name = name.replace("\\", "_")
    raw = _archive([(safe_name, _point_csv())])
    if safe_name != name:
        stored_name = safe_name.encode()
        assert raw.count(stored_name) == 2
        raw = raw.replace(stored_name, name.encode())
    with pytest.raises(ARRFormatError, match="Unsafe"):
        parse_pattern_zip(raw, kind="point")


def test_zip_rejects_duplicate_casefolded_names() -> None:
    raw = _archive([("A_Increments.csv", _point_csv()), ("a_increments.csv", _point_csv(event_id="50"))])
    with pytest.raises(ARRFormatError, match="Duplicate"):
        parse_pattern_zip(raw, kind="point")


def test_zip_rejects_symlink_and_oversized_uncompressed_member() -> None:
    raw = io.BytesIO()
    with zipfile.ZipFile(raw, "w") as archive:
        link = zipfile.ZipInfo("link_Increments.csv")
        link.create_system = 3
        link.external_attr = (stat.S_IFLNK | 0o777) << 16
        archive.writestr(link, _point_csv())
    with pytest.raises(ARRFormatError, match="Links"):
        parse_pattern_zip(raw.getvalue(), kind="point")
    bomb = _archive([("huge_Increments.csv", b"a" * (8 * 1024 * 1024 + 1))])
    with pytest.raises(ARRFormatError, match="exceeds"):
        parse_pattern_zip(bomb, kind="point")


def test_zip_rejects_invalid_archive() -> None:
    with pytest.raises(ARRFormatError, match="ZIP"):
        parse_pattern_zip(b"bad zip", kind="point")
    with pytest.raises(ARRFormatError, match=r"no \*Increments"):
        parse_pattern_zip(_archive([("readme.txt", b"safe")]), kind="point")


def test_gross_storm_from_exact_bom_value_and_selected_pattern() -> None:
    bom = parse_bom_ifd_csv(_bom())
    patterns = parse_pattern_csv(_point_csv(), kind="point")
    event = storm_from_bom(bom, bom.probability("1%"), patterns, patterns.patterns[0])
    assert event.source_sha256 == bom.sha256
    assert event.pattern_source_sha256 == patterns.source_sha256
    assert event.pattern_event_id == "0004"
    assert event.probability_label == "1%"
    assert event.increments_mm == (Decimal("4.55"), Decimal("9.1"), Decimal("13.65"), Decimal("18.2"))
    assert event.end_times_min == (360, 720, 1080, 1440)
    assert event.total_mm == Decimal("45.5")
    assert event.hydrological_acceptance == "not_assessed"
    assert "NO_ARF_NO_CLIMATE_ADJUSTMENT_NO_LOSSES_NO_PREBURST" in event.operations


def test_gross_storm_rejects_mismatched_duration_and_no_unspecified_conversion() -> None:
    bom = parse_bom_ifd_csv(_bom())
    patterns = parse_pattern_csv(_point_csv(), kind="point")
    wrong_pattern = parse_pattern_csv(_point_csv(event_id="wrong", duration=60, timestep=15), kind="point")
    with pytest.raises(ARRFormatError, match="Exact BoM duration"):
        storm_from_bom(bom, bom.probability("1%"), wrong_pattern, wrong_pattern.patterns[0])
    with pytest.raises(ARRFormatError, match="does not belong"):
        storm_from_bom(bom, bom.probability("1%"), patterns, wrong_pattern.patterns[0])


def test_gross_storm_from_arr2026_uses_exact_current_table_only() -> None:
    fixture = Path(__file__).absolute().parent / "fixtures" / "arr" / "2026v1-minimal.json"
    document = parse_arr_json(fixture.read_bytes())
    patterns = parse_pattern_csv(
        b"EventID,Duration,TimeStep,Region,AEP,Increments\nsynthetic,60,15,SYNTHETIC,frequent,25,25,25,25\n",
        kind="point",
    )
    event = storm_from_arr_2026(document, document.ifd_datasets[0], Decimal("1.0"), patterns, patterns.patterns[0])
    assert event.total_mm == Decimal("70.000")
    assert event.increments_mm == (Decimal("17.50000"),) * 4
    assert event.source_label == document.ifd_datasets[0].name
    assert event.hydrological_acceptance == "not_assessed"
