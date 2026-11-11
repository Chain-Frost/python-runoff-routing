"""Synthetic-only ARR 2026 import contracts; no network or native engine."""

import csv
import hashlib
import io
import json
from dataclasses import FrozenInstanceError, replace
from decimal import Decimal
from pathlib import Path
from collections.abc import Callable
from typing import Any, cast

import pytest

from runoff_routing.arr_data import MAX_SOURCE_BYTES, ARRFormatError, IFDDataset
from runoff_routing.arr_import import parse_arr_json, parse_arr_txt, read_arr_file
from runoff_routing.arr_report import inventory_csv, inventory_dict, inventory_json, write_new

FIXTURES = Path(__file__).absolute().parent / "fixtures" / "arr"


def _raw(name: str = "2026v1-minimal.json") -> bytes:
    return (FIXTURES / name).read_bytes()


def _json() -> dict[str, Any]:
    return cast("dict[str, Any]", json.loads(_raw()))


def _modify(callback: Callable[[dict[str, Any]], object]) -> bytes:
    doc = _json()
    callback(doc)
    return json.dumps(doc).encode("utf-8")


def test_json_baselines_and_exact_source_bytes_and_decimal_precision() -> None:
    raw = b"\xef\xbb\xbf" + _raw().replace(b"\n", b"\r\n")
    parsed = parse_arr_json(raw, locator="owner-supplied/synthetic.json", captured_at="2026-11-11")
    assert parsed.raw_bytes == raw
    assert parsed.source.sha256 == hashlib.sha256(raw).hexdigest()
    assert parsed.source.byte_length == len(raw)
    assert parsed.source.locator == "owner-supplied/synthetic.json"
    assert parsed.source.datahub_version == "2026v1"
    assert parsed.source.captured_at == "2026-11-11"
    assert parsed.location.latitude == Decimal("-30.000")
    assert parsed.location.longitude == Decimal("150.000")
    assert parsed.location.crs == "EPSG:4326"
    assert [table.baseline for table in parsed.ifd_datasets] == [
        "current_2030",
        "historical_1961_1990",
        "native",
    ]
    current = parsed.ifd_datasets[0]
    assert current.durations_min == (5, 60)
    assert current.aep_percent == (Decimal("63.2"), Decimal("1.0"))
    assert current.depths_mm == ((Decimal("9.60"), Decimal("30.0")), (Decimal("15.0"), Decimal("70.000")))
    assert current.release_year is None  # No release metadata in live 2026v1 JSON RecIFD shape.
    assert current.climate_policy == "AS_EXPORTED_NO_FURTHER_UPLIFT"
    assert parsed.unprocessed_layers == ("PointTP",)
    assert parsed.absent_layers == ()


def test_json_inventory_deterministic_and_source_order() -> None:
    doc = parse_arr_json(_raw())
    expected = inventory_json(doc)
    assert inventory_json(doc) == expected
    output = json.loads(expected)
    assert output["schema_version"] == 1
    assert output["capability"] == "ifd_validated"
    assert output["ifd_datasets"][0]["depths_mm"][0] == ["9.60", "30.0"]
    assert output["ifd_datasets"][0]["units"]["probability"] == "AEP_PERCENT"
    assert [item["baseline"] for item in output["ifd_datasets"]] == [
        "current_2030",
        "historical_1961_1990",
        "native",
    ]
    assert inventory_dict(doc)["source"] == output["source"]
    reader = csv.DictReader(io.StringIO(inventory_csv(doc)))
    rows = list(reader)
    assert len(rows) == 12
    assert (rows[0]["duration_min"], rows[0]["aep_percent"], rows[0]["depth_mm"]) == (
        "5",
        "63.2",
        "9.60",
    )
    assert rows[4]["baseline"] == "historical_1961_1990"
    assert rows[-1]["baseline"] == "native"


def test_missing_optional_ifd_is_explicit_absence() -> None:
    raw = _modify(lambda obj: obj["layers"].pop("RecIFD"))
    doc = parse_arr_json(raw)
    assert doc.capability == "location_only"
    assert doc.ifd_datasets == ()
    assert doc.absent_layers == ("RecIFD",)
    assert "PointTP" in doc.unprocessed_layers


def test_empty_ifd_layer_is_not_fake_rainfall_validation() -> None:
    raw = _modify(lambda obj: obj["layers"].update({"RecIFD": {}}))
    doc = parse_arr_json(raw)
    assert doc.capability == "location_only"
    assert doc.absent_layers == ()


def test_other_layers_remain_unprocessed_not_discarded_or_adjusted() -> None:
    raw = _modify(lambda obj: obj["layers"].update({"CCAdjIFDDatasets": {"unknown": 6}}))
    doc = parse_arr_json(raw)
    assert doc.unprocessed_layers == ("PointTP", "CCAdjIFDDatasets")
    assert doc.ifd_datasets[0].scenario_ssp is None
    assert doc.ifd_datasets[0].scenario_year is None


@pytest.mark.parametrize(
    ("changed", "message"),
    [
        (lambda obj: obj.update({"datahub_version": "2019v1"}), "version"),
        (lambda obj: obj.pop("datahub_version"), "version"),
        (lambda obj: obj["layers"].update({"RecIFD": None}), "RecIFD"),
        (lambda obj: obj["layers"]["RecIFD"]["Default Native Baseline"].update({"index": []}), "durations"),
        (lambda obj: obj["layers"]["RecIFD"]["Default Native Baseline"].update({"columns": []}), "AEP"),
        (lambda obj: obj["layers"]["RecIFD"]["Default Native Baseline"].update({"index": [5, 5]}), "Duplicate"),
        (lambda obj: obj["layers"]["RecIFD"]["Default Native Baseline"].update({"columns": [1, 1.0]}), "Duplicate"),
        (lambda obj: obj["layers"]["RecIFD"]["Default Native Baseline"].update({"columns": [0, 1]}), "AEP"),
        (lambda obj: obj["layers"]["RecIFD"]["Default Native Baseline"].update({"columns": [101, 1]}), "AEP"),
        (lambda obj: obj["layers"]["RecIFD"]["Default Native Baseline"].update({"columns": ["2EY", 1]}), "decimal"),
        (lambda obj: obj["layers"]["RecIFD"]["Default Native Baseline"].update({"index": [5.5, 60]}), "Duration"),
        (lambda obj: obj["layers"]["RecIFD"]["Default Native Baseline"].update({"data": [[0, 1]]}), "row count"),
        (lambda obj: obj["layers"]["RecIFD"]["Default Native Baseline"].update({"data": [[0], [1]]}), "column count"),
        (lambda obj: obj["layers"]["RecIFD"]["Default Native Baseline"].update({"data": [[-2, 3], [1, 2]]}), "negative"),
        (lambda obj: obj["layers"]["RecIFD"]["Default Native Baseline"].update({"data": [[True, 3], [1, 2]]}), "Boolean"),
        (lambda obj: obj["layers"]["RecIFD"]["Default Native Baseline"].update({"data": [["10", 3], [1, 2]]}), "decimal"),
        (lambda obj: obj["layers"]["RecIFD"]["Default Native Baseline"].update({"extra": 1}), "exactly"),
        (lambda obj: obj["input_data"].update({"Latitude": 91}), "bounds"),
        (lambda obj: obj["input_data"].update({"Outlet Latitude": -25}), "outlet"),
    ],
)
def test_invalid_json_models_fail_closed(changed: Callable[[dict[str, Any]], object], message: str) -> None:
    with pytest.raises(ARRFormatError, match=message):
        parse_arr_json(_modify(changed))


def test_unknown_baseline_does_not_assume_climate_or_ifd_dataset_identity() -> None:
    obj = _json()
    table = obj["layers"]["RecIFD"].pop("Default Native Baseline")
    obj["layers"]["RecIFD"]["SSP5-8.5 (2090) adjusted"] = table
    with pytest.raises(ARRFormatError, match="Unrecognised RecIFD baseline"):
        parse_arr_json(json.dumps(obj).encode())


def test_duplicate_json_object_keys_rejected_before_data_loss() -> None:
    raw = _raw().replace(b'"datahub_version": "2026v1",', b'"datahub_version": "2026v1", "datahub_version": "2019v1",')
    with pytest.raises(ARRFormatError, match="Duplicate JSON key"):
        parse_arr_json(raw)


def test_nonfinite_json_literals_and_extreme_exponents_rejected() -> None:
    raw = _raw().replace(b"9.60", b"NaN", 1)
    with pytest.raises(ARRFormatError, match="Nonfinite"):
        parse_arr_json(raw)
    raw = _raw().replace(b"9.60", b"1e99999999", 1)
    with pytest.raises(ARRFormatError, match="Nonfinite|finite"):
        parse_arr_json(raw)


def test_bad_utf8_and_oversized_input_rejected() -> None:
    with pytest.raises(ARRFormatError, match="UTF-8"):
        parse_arr_json(b"\xff" + _raw())
    with pytest.raises(ARRFormatError, match="8 MiB"):
        parse_arr_json(b" " * (MAX_SOURCE_BYTES + 1))


def test_txt_ifd_sections_and_explicit_release_metadata() -> None:
    parsed = parse_arr_txt(_raw("2026v1-minimal.txt"))
    assert parsed.source.datahub_version == "2026v1"
    assert len(parsed.ifd_datasets) == 2
    assert parsed.ifd_datasets[0].release_year == 2026
    assert parsed.ifd_datasets[0].provider_datasets == "Synthetic IFD (2026)"
    assert parsed.ifd_datasets[0].raw_metadata[1] == ("Note", "Illustrative values only, not for design")
    assert parsed.ifd_datasets[0].depths_mm[1][1] == Decimal("70.000")
    assert "TP" in parsed.unprocessed_layers
    assert parsed.absent_layers == ()


def test_txt_and_json_ifd_values_match_for_illustrative_common_axes() -> None:
    text = parse_arr_txt(_raw("2026v1-minimal.txt"))
    data = parse_arr_json(_raw())
    for old, new in zip(text.ifd_datasets, data.ifd_datasets, strict=False):
        assert old.name == new.name
        assert old.durations_min == new.durations_min
        assert old.aep_percent == new.aep_percent
        assert old.depths_mm == new.depths_mm


def test_txt_bad_table_shape_and_section_marker_fail_closed() -> None:
    text = _raw("2026v1-minimal.txt")
    with pytest.raises(ARRFormatError, match="column count"):
        parse_arr_txt(text.replace(b"5 (0.08),9.60,30.0", b"5 (0.08),9.60"))
    with pytest.raises(ARRFormatError, match="terminator"):
        parse_arr_txt(text.replace(b"[END_RECCURRENTBASELINE]", b"[END_OTHER]"))
    with pytest.raises(ARRFormatError, match="axis units"):
        parse_arr_txt(text.replace(b"min (h)\\AEP(%)", b"min (h)\\ARI(yrs)"))
    with pytest.raises(ARRFormatError, match="Duplicate"):
        parse_arr_txt(text.replace(b"63.2,1.0", b"1.0,1.0"))


def test_txt_unknown_ifd_variant_is_not_silently_ignored() -> None:
    text = _raw("2026v1-minimal.txt").replace(b"[RECIFD]", b"[RECIFD_OTHER]").replace(
        b"[END_RECIFD]", b"[END_RECIFD_OTHER]"
    )
    with pytest.raises(ARRFormatError, match="Unknown RECIFD"):
        parse_arr_txt(text)


def test_legacy_txt_requires_explicit_profile_and_is_location_only() -> None:
    raw = _raw("2019v1-input-only.txt")
    with pytest.raises(ARRFormatError, match="explicit legacy profile"):
        parse_arr_txt(raw)
    parsed = parse_arr_txt(raw, legacy_profile="2019v1")
    assert parsed.source.datahub_version is None
    assert parsed.source.compatibility_profile == "2019v1_input_only"
    assert parsed.location.latitude == Decimal("-31.0")
    assert parsed.capability == "location_only"
    assert parsed.ifd_datasets == ()
    with pytest.raises(ARRFormatError, match="Legacy profile"):
        parse_arr_txt(_raw("2026v1-minimal.txt"), legacy_profile="2019v1")


def test_legacy_unknown_sections_fail_explicitly() -> None:
    raw = _raw("2019v1-input-only.txt").replace(b"[ENDTXT]", b"[RECIFD]\n[END_RECIFD]\n[ENDTXT]")
    with pytest.raises(ARRFormatError, match="not characterised"):
        parse_arr_txt(raw, legacy_profile="2019v1")


def test_txt_unrecognised_versions_not_downgraded() -> None:
    with pytest.raises(ARRFormatError, match="version"):
        parse_arr_txt(_raw("2026v1-minimal.txt").replace(b"2026v1", b"2030v1"))
    with pytest.raises(ARRFormatError, match="version"):
        parse_arr_txt(_raw("2019v1-input-only.txt"), legacy_profile="2018v1")


def test_source_is_immutable_and_no_clobber_writes(tmp_path: Path) -> None:
    source = tmp_path / "synthetic-\u6d4b\u8bd5.json"
    source.write_bytes(_raw())
    before = source.read_bytes()
    parsed = read_arr_file(source)
    assert parsed.raw_bytes == before
    assert source.read_bytes() == before
    with pytest.raises(FrozenInstanceError):
        setattr(parsed.source, "sha256", "tampered")
    with pytest.raises(ARRFormatError, match="row count"):
        replace(parsed.ifd_datasets[0], depths_mm=((Decimal(1),),))
    target = tmp_path / "inventory.json"
    write_new(target, inventory_json(parsed))
    assert json.loads(target.read_text(encoding="utf-8"))["source"]["sha256"] == parsed.source.sha256
    with pytest.raises(FileExistsError):
        write_new(target, "would overwrite")
    with pytest.raises(FileExistsError):
        write_new(source, "would overwrite source")
    assert source.read_bytes() == before


def test_unsupported_zip_is_not_implicitly_opened(tmp_path: Path) -> None:
    archive = tmp_path / "temporal_patterns.zip"
    archive.write_bytes(b"fake zip")
    with pytest.raises(ARRFormatError, match="ZIP and CSV"):
        read_arr_file(archive)


def test_json_rejects_legacy_profile_at_read_boundary(tmp_path: Path) -> None:
    source = tmp_path / "2026.json"
    source.write_bytes(_raw())
    with pytest.raises(ARRFormatError, match="Legacy TXT profile"):
        read_arr_file(source, legacy_profile="2019v1")


def test_derived_ifd_cannot_be_given_arbitrary_scenario_metadata() -> None:
    table = parse_arr_json(_raw()).ifd_datasets[0]
    with pytest.raises(ARRFormatError, match="Scenario IFDs"):
        replace(table, scenario_ssp="SSP5", scenario_year=2090)
    assert isinstance(table, IFDDataset)
