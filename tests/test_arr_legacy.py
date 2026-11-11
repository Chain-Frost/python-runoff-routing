"""Synthetic ARR2016-era TXT import, byte provenance and legacy/2026 boundaries."""

import csv
import hashlib
import io
import json
from dataclasses import FrozenInstanceError, replace
from decimal import Decimal
from pathlib import Path

import pytest

from runoff_routing.arr_data import ARRFormatError
from runoff_routing.arr_import import parse_arr_json, parse_arr_txt, read_arr_file
from runoff_routing.arr_report import inventory_json, legacy_preburst_csv

FIXTURES = Path(__file__).absolute().parent / "fixtures" / "arr"


def _sample() -> bytes:
    return (FIXTURES / "2016-era-synthetic.txt").read_bytes()


def test_legacy_requires_opt_in_and_retains_bytes() -> None:
    raw = b"\xef\xbb\xbf" + _sample().replace(b"\n", b"\r\n")
    with pytest.raises(ARRFormatError, match="explicit legacy profile"):
        parse_arr_txt(raw)
    doc = parse_arr_txt(raw, legacy_profile="arr2016", locator="test/legacy.txt")
    assert doc.source.datahub_version is None
    assert doc.source.compatibility_profile == "arr2016_txt"
    assert doc.source.sha256 == hashlib.sha256(raw).hexdigest()
    assert doc.raw_bytes == raw
    assert doc.location.latitude == Decimal("-30.00500")
    assert doc.location.longitude == Decimal("150.100")
    assert doc.capability == "legacy_layers_validated"
    assert doc.ifd_datasets == ()
    assert doc.absent_layers == ("RecIFD",)
    assert doc.unprocessed_layers == ("RIVREG", "BOMIFD", "CCF", "BASEFLOW")
    assert doc.legacy_losses is not None
    field_name = "initial_loss_mm"
    with pytest.raises(FrozenInstanceError):
        setattr(doc.legacy_losses, field_name, Decimal(1))


def test_legacy_losses_and_arf_are_typed_but_not_applied() -> None:
    doc = parse_arr_txt(_sample(), legacy_profile="arr2016")
    loss = doc.legacy_losses
    arf = doc.legacy_arf
    assert loss is not None
    assert arf is not None
    assert loss.initial_loss_mm == Decimal("21.0")
    assert loss.continuing_loss_mm_per_hour == Decimal("2.00")
    assert loss.raw_id == "31415.0"
    assert ("Version", "2016_v1") in loss.metadata
    assert arf.zone == "Invented Zone"
    assert len(arf.coefficients) == 9
    assert arf.coefficients[-1] == ("i", Decimal("-0.0003"))
    report = inventory_json(doc)
    assert '"applied": false' in report


def test_legacy_tp_ids_not_increments() -> None:
    doc = parse_arr_txt(_sample(), legacy_profile="arr2016")
    point, areal = doc.legacy_tp_regions
    assert (point.kind, point.code, point.label) == ("point", "DemoPoint", "Synthetic Point Region")
    assert (areal.kind, areal.code) == ("areal", "DemoAreal")
    assert areal.intersection_fraction == Decimal("0.80")
    report = json.loads(inventory_json(doc))
    assert report["legacy"]["temporal_pattern_regions"][0]["increments_loaded"] is False


def test_legacy_preburst_stores_depths_ratios_and_source_precision() -> None:
    doc = parse_arr_txt(_sample(), legacy_profile="arr2016")
    assert [table.percentile for table in doc.legacy_preburst] == [50, 10, 25, 75, 90]
    median = doc.legacy_preburst[0]
    assert median.durations_min == (60, 120)
    assert median.aep_percent == (Decimal(50), Decimal(1))
    assert median.depths_mm[0] == (Decimal("2.0"), Decimal("7.00"))
    assert median.ratios[0] == (Decimal("0.010"), Decimal("1.020"))
    assert median.metadata[-1] == ("Note", "Synthetic only, not design data")
    data = list(csv.DictReader(io.StringIO(legacy_preburst_csv(doc))))
    assert len(data) == 20
    assert (data[0]["depth_mm"], data[0]["ratio"]) == ("2.0", "0.010")
    assert data[1]["ratio"] == "1.020"  # Legacy ratio may exceed unity.
    assert len(json.loads(inventory_json(doc))["legacy"]["preburst_tables"]) == 5


def test_other_sections_remain_raw_and_do_not_invent_ifd() -> None:
    doc = parse_arr_txt(_sample(), legacy_profile="arr2016")
    layers = {section.tag: section for section in doc.legacy_unprocessed}
    assert layers["RIVREG"].body_lines[0] == "Division,Synthetic Basin"
    assert layers["BOMIFD"].body_lines == ("No data,No data found at this location!",)
    assert layers["CCF"].body_lines[0] == ",RCP 4.5,RCP 8.5"
    assert layers["BASEFLOW"].metadata == (("Version", "2016_v1"),)
    assert doc.ifd_datasets == ()


def test_legacy_2026_dialect_and_legacy_json_are_not_confused() -> None:
    new = (FIXTURES / "2026v1-minimal.txt").read_bytes()
    with pytest.raises(ARRFormatError, match="Legacy profile"):
        parse_arr_txt(new, legacy_profile="arr2016")
    as_json = (FIXTURES / "2026v1-minimal.json").read_bytes().replace(b"2026v1", b"2019v1")
    with pytest.raises(ARRFormatError, match="version"):
        parse_arr_json(as_json)
    forged = _sample().replace(b"[STARTTXT]", b"Data Hub Version,2026v1\n[STARTTXT]")
    with pytest.raises(ARRFormatError, match="Legacy profile"):
        parse_arr_txt(forged, legacy_profile="arr2016")


def test_negative50_loss_sentinel_is_missing_not_zero() -> None:
    raw = _sample().replace(b"Storm Initial Losses (mm),21.0", b"Storm Initial Losses (mm),-50")
    raw = raw.replace(b"Storm Continuing Losses (mm/h),2.00", b"Storm Continuing Losses (mm/h),-50")
    doc = parse_arr_txt(raw, legacy_profile="arr2016")
    loss = doc.legacy_losses
    assert loss is not None
    assert loss.initial_loss_mm is None
    assert loss.continuing_loss_mm_per_hour is None
    assert ("Storm Initial Losses (mm)", "-50") in loss.raw_fields
    assert json.loads(inventory_json(doc))["legacy"]["storm_losses"]["initial_loss_mm"] is None


@pytest.mark.parametrize("bad", ["-1", "-10.0", "NaN", "Infinity"])
def test_invalid_legacy_il_rejected(bad: str) -> None:
    modified = _sample().replace(b"Storm Initial Losses (mm),21.0", f"Storm Initial Losses (mm),{bad}".encode())
    with pytest.raises(ARRFormatError, match=r"Negative|Nonfinite"):
        parse_arr_txt(modified, legacy_profile="arr2016")


@pytest.mark.parametrize(
    ("before", "after", "message"),
    [
        ("[END_LOSSES]", "[END_LOSSES_WRONG]", "terminator"),
        ("[LONGARF]", "[NEWARF]", "Unknown legacy section"),
        ("[TP]", "[LOSSES]", "Duplicate legacy section"),
        ("a,0.06", "a,0.06\na,0.07", "duplicate"),
        ("f,0.65", "f,NaN", "Nonfinite"),
        ("code,DemoPoint", "code,", "Missing"),
        ("per_intersect,0.80", "per_intersect,1.1", "exceeds fraction"),
        ("60 (1.0),2.0 (0.010),7.00 (1.020),", "60 (1.0),2.0,7.00 (1.020),", "depth \\(ratio\\)"),
        ("60 (1.0),2.0 (0.010),7.00 (1.020),", "60 (1.0),2.0 (0.010),", "column count"),
        ("120 (2.0),0.1 (0.001),1.0 (0.200),", "60 (1.0),0.1 (0.001),1.0 (0.200),", "Duplicate"),
        (r"min (h)\AEP(%),50,1,", r"min (h)\ARI(yr),50,1,", "axis units"),
    ],
)
def test_corrupt_legacy_sections_fail_closed(before: str, after: str, message: str) -> None:
    raw = _sample().decode("utf-8")
    assert before in raw
    with pytest.raises(ARRFormatError, match=message):
        parse_arr_txt(raw.replace(before, after, 1).encode(), legacy_profile="arr2016")


def test_tuflow_embedded_patterns_are_inventoried_not_read_as_tps() -> None:
    embedded = _sample() + b"[STARTPATTERNS]\nEventID,Duration,AEP\n1,60,1\n"
    doc = parse_arr_txt(embedded, legacy_profile="arr2016")
    assert "EmbeddedPatterns" in doc.unprocessed_layers
    assert doc.raw_bytes == embedded
    with pytest.raises(ARRFormatError, match="Trailing content"):
        parse_arr_txt(_sample() + b"\nInjected,1\n", legacy_profile="arr2016")


def test_local_file_legacy_profile_and_existing_2019_profile(tmp_path: Path) -> None:
    path = tmp_path / "legacy café.txt"
    path.write_bytes(_sample())
    doc = read_arr_file(path, legacy_profile="arr2016")
    assert doc.source.locator == str(path.absolute())
    assert doc.raw_bytes == path.read_bytes()
    old = read_arr_file(FIXTURES / "2019v1-input-only.txt", legacy_profile="2019v1")
    assert old.source.compatibility_profile == "2019v1_input_only"
    assert old.capability == "location_only"


def test_cp1252_legacy_requires_explicit_encoding() -> None:
    raw = _sample().replace(b"Synthetic Point Region", "Région".encode("cp1252"))
    with pytest.raises(ARRFormatError, match="decodable"):
        parse_arr_txt(raw, legacy_profile="arr2016")
    doc = parse_arr_txt(raw, legacy_profile="arr2016", legacy_encoding="cp1252")
    assert doc.legacy_tp_regions[0].label == "Région"
    assert doc.source.encoding == "cp1252"
    assert doc.raw_bytes == raw
    assert json.loads(inventory_json(doc))["source"]["encoding"] == "cp1252"
    with pytest.raises(ARRFormatError, match="CP1252 requires"):
        parse_arr_txt(raw, legacy_encoding="cp1252")


def test_legacy_preburst_typed_model_rejects_invalid_direct_construction() -> None:
    doc = parse_arr_txt(_sample(), legacy_profile="arr2016")
    table = doc.legacy_preburst[0]
    with pytest.raises(ARRFormatError, match="row count"):
        replace(table, depths_mm=())
    with pytest.raises(ARRFormatError, match="ratio must be finite"):
        replace(table, ratios=((Decimal("NaN"), Decimal(0)), *table.ratios[1:]))
    with pytest.raises(ARRFormatError, match="duplicated"):
        replace(table, durations_min=(60, 60))


def test_legacy_text_outside_marked_section_is_rejected() -> None:
    text = _sample().replace(b"[LOSSES]", b"Stray,10\n[LOSSES]", 1)
    with pytest.raises(ARRFormatError, match="outside a marked section"):
        parse_arr_txt(text, legacy_profile="arr2016")


def test_cp1252_via_read_file(tmp_path: Path) -> None:
    path = tmp_path / "Région arr.txt"
    raw = _sample().replace(b"Synthetic Point Region", "Région".encode("cp1252"))
    path.write_bytes(raw)
    doc = read_arr_file(path, legacy_profile="arr2016", legacy_encoding="cp1252")
    assert doc.source.encoding == "cp1252"
    assert doc.source.sha256 == hashlib.sha256(raw).hexdigest()
