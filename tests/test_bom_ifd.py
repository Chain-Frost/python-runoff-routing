"""Synthetic BoM Design Rainfall CSV contract tests; no real BoM data checked in."""

from __future__ import annotations

import hashlib
from dataclasses import replace
from decimal import Decimal
from pathlib import Path

import pytest

from runoff_routing.arr_data import ARRFormatError
from runoff_routing.bom_ifd import BoMIFD, parse_bom_ifd_csv, read_bom_ifd_csv


def _csv(*, all_design: bool = False, unit: str = "mm") -> bytes:
    title = "All Design" if all_design else "IFD Design"
    dimension = "Depth" if unit == "mm" else "Intensity"
    columns = "12EY,0.5EY,63.2%,1 in 200" if all_design else "63.2%,50%,1%"
    first = "3.5,4.0,5.0,11.5" if all_design else "5.0,6.0,11.5"
    second = "8.0,9.0,10.0,18.5" if all_design else "10.0,12.0,18.5"
    third = "21.0,28.0,30.0,45.5" if all_design else "30.0,35.0,45.5"
    return (
        "Copyright Commonwealth of Australia 2016 Bureau of Meteorology\r\n"
        "\r\n"
        f"{title} Rainfall {dimension} ({unit})\r\n"
        "Issued:,12 November 2026\r\n"
        "Location Label:,SYNTHETIC EXAMPLE ONLY\r\n"
        "Requested coordinate:,Latitude,-33.5,Longitude,115.25\r\n"
        "Nearest grid cell:,Latitude,33.5125 (S),Longitude,115.2375 (E)\r\n"
        "\r\n"
        ",,Annual Exceedance Probability (AEP)\r\n"
        f"Duration,Duration in min,{columns}\r\n"
        f"1 min,1,{first}\r\n"
        f"1.5 hour,90.0,{second}\r\n"
        f"24 hour,1440,{third}\r\n"
    ).encode()


def test_standard_ifd_exact_durations_labels_and_bytes() -> None:
    raw = _csv()
    result = parse_bom_ifd_csv(raw, locator=r"D:\rainfall\design.csv")
    assert isinstance(result, BoMIFD)
    assert result.sha256 == hashlib.sha256(raw).hexdigest()
    assert result.raw_bytes == raw
    assert result.locator == r"D:\rainfall\design.csv"
    assert result.rainfall_unit == "mm"
    assert result.table_kind == "ifd"
    assert result.durations_min == (1, 90, 1440)
    assert result.duration_labels == ("1 min", "1.5 hour", "24 hour")
    assert result.issued == "12 November 2026"
    assert result.label == "SYNTHETIC EXAMPLE ONLY"
    assert result.latitude == Decimal("-33.5")
    assert result.longitude == Decimal("115.25")
    assert result.nearest_latitude == Decimal("-33.5125")
    assert result.nearest_longitude == Decimal("115.2375")
    assert [(x.label, x.kind) for x in result.probabilities] == [
        ("63.2%", "AEP_PERCENT"),
        ("50%", "AEP_PERCENT"),
        ("1%", "AEP_PERCENT"),
    ]
    assert result.value_at(1440, result.probability("1%")) == Decimal("45.5")


def test_all_design_probability_kinds_are_not_silently_converted() -> None:
    result = parse_bom_ifd_csv(_csv(all_design=True))
    assert result.table_kind == "all_design"
    assert [(p.kind, p.value) for p in result.probabilities] == [
        ("EY", Decimal(12)),
        ("EY", Decimal("0.5")),
        ("AEP_PERCENT", Decimal("63.2")),
        ("AEP_ONE_IN", Decimal(200)),
    ]
    assert result.value_at(90, result.probability("0.5EY")) == Decimal("9.0")
    assert result.value_at(90, result.probability("1 in 200")) == Decimal("18.5")
    with pytest.raises(ARRFormatError, match="not present"):
        result.probability("0.5%")


def test_intensity_is_not_implicitly_converted() -> None:
    result = parse_bom_ifd_csv(_csv(unit="mm/h"))
    p = result.probability("1%")
    with pytest.raises(ARRFormatError, match="convert_intensity=True"):
        result.depth_mm_at(90, p)
    assert result.depth_mm_at(90, p, convert_intensity=True) == Decimal("27.75")
    with pytest.raises(ARRFormatError, match="contradicts"):
        parse_bom_ifd_csv(_csv(unit="mm/h"), source_unit="mm")


@pytest.mark.parametrize(
    ("needle", "replacement", "message"),
    [
        ("24 hour,1440", "24 hour,1380", "duration mismatch"),
        ("1.5 hour,90.0", "1.5 hour,90.5", "duration mismatch"),
        ("24 hour,1440", "1.5 hour,90", "Duplicate"),
        ("63.2%,50%,1%", "63.2%,50%,50%", "Duplicate"),
        ("63.2%,50%,1%", "63.2%,50%,101%", "percentage exceeds"),
        ("5.0,6.0,11.5", "5.0,6.0", "Ragged"),
        ("5.0,6.0,11.5", "5.0,6.0,NaN", "nonfinite"),
        ("5.0,6.0,11.5", "5.0,6.0,-1", "negative"),
        ("IFD Design Rainfall Depth (mm)", "IFD Design Rainfall Depth (unknown)", "recognised"),
        ("Duration in min", "Duration in hr", "requires one"),
        ("1.5 hour,90.0", "1.5 hour,90.0,7,extra", "Ragged"),
        ("Latitude,-33.5", "Latitude,-93.5", "geographic coordinate"),
        ("115.2375 (E)", "115.2375 (S)", "hemisphere"),
    ],
)
def test_invalid_source_rejected(needle: str, replacement: str, message: str) -> None:
    with pytest.raises(ARRFormatError, match=message):
        parse_bom_ifd_csv(_csv().replace(needle.encode(), replacement.encode()))


def test_extended_duplicate_probability_rejected() -> None:
    raw = _csv(all_design=True).replace(b"0.5EY", b"12EY")
    with pytest.raises(ARRFormatError, match="Duplicate"):
        parse_bom_ifd_csv(raw)


def test_malformed_csv_and_source_sha_drift_rejected() -> None:
    with pytest.raises(ARRFormatError, match="quoting"):
        parse_bom_ifd_csv(_csv() + b'"unterminated')
    result = parse_bom_ifd_csv(_csv())
    with pytest.raises(ARRFormatError, match="hash"):
        replace(result, sha256="0" * 64)


def test_file_reader_is_read_only_and_preserves_path(tmp_path: Path) -> None:
    path = tmp_path / "synthétic-ifd.csv"
    payload = _csv()
    path.write_bytes(payload)
    result = read_bom_ifd_csv(path)
    assert result.raw_bytes == payload
    assert result.locator == str(path.absolute())
    assert path.read_bytes() == payload


def test_missing_probabilities_and_rows_are_invalid() -> None:
    with pytest.raises(ARRFormatError, match="axis is empty"):
        parse_bom_ifd_csv(_csv().split(b"1 min,1,")[0])
    with pytest.raises(ARRFormatError):
        parse_bom_ifd_csv(b"not a design rainfall CSV")
