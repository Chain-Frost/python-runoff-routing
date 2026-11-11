"""Source preservation and typed/canonical RORB round trips (synthetic, no native tools)."""

from __future__ import annotations

import hashlib
import json
import subprocess
from collections.abc import Callable
from dataclasses import replace
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from runoff_routing.rorb_codec import (
    FormatProblem,
    original_bytes,
    parse_bytes,
    parse_catg,
    parse_cmd_par,
    parse_design_stm,
    read_file,
    serialize_catg,
    serialize_cmd_par,
    serialize_design_stm,
    to_s2_payload,
    write_new,
)
from runoff_routing.rorb_model import (
    CatchmentModel,
    ControlStep,
    LossValue,
    ParameterSet,
    RoutingValue,
    RunModel,
    SubArea,
    from_dict,
    from_json,
    to_dict,
    to_json,
)


def _catg() -> str:
    return (
        "SYNTHETIC CATCHMENT\n"
        "C RORB_GE 002\n"
        "C #NODES\nC 0\nC #REACHES\nC 0\nC #STORAGES\nC 0\n"
        "C #INFLOW/OUTFLOW\nC 0\nC END RORB_GE\n"
        "1\n"
        "1, 5.000, -99, Reach 1 Sub-area A\n"
        "3, Store hydrograph\n"
        "1, 4.000, -99, Reach 2 Sub-area B\n"
        "4, Join stored hydrograph\n"
        "5, 2.500, -99, Reach 3\n"
        "7, PRINT outlet\n"
        "0\n"
        "C Sub Area Data\n"
        "30.000, 20.000, -99\n"
        "C Impervious Fraction Data\n"
        "0, -99, No impervious area\n"
    )


def _stm() -> str:
    return (
        "SYNTHETIC DESIGN\n"
        "DESIGN\n"
        "C Example comment not a data record\n"
        "0.500D0,200,1,1,1,-99\n"
        "0, 2\n"
        "Temporal pattern (% of depth)\n"
        "60.0,\t40.0,-99.00\n"
        "C Sub-area rainfall depths\n"
        "100.00,90.0,-99\n"
    )


def _params() -> ParameterSet:
    return ParameterSet(
        "subfolder\\model.catg", r"C:\storms\design.stm", True, 3, 1, 1, 1,
        (RoutingValue(1, Decimal("12.0"), Decimal("0.8")),),
        (LossValue(1, 1, Decimal(24), Decimal("5.0")),),
    )


def _run() -> RunModel:
    return RunModel(_params(), parse_catg(_catg().encode()).model, parse_design_stm(_stm().encode()).model)


def test_catchment_unchanged_source_preserves_crlf_comments_and_sha256() -> None:
    raw = _catg().replace("\n", "\r\n").encode("cp1252")
    parsed = parse_catg(raw)
    assert original_bytes(parsed) == raw
    assert parsed.source.sha256 == hashlib.sha256(raw).hexdigest()
    assert parsed.source.newline == "crlf"
    assert parsed.graphical_metadata[0] == "SYNTHETIC CATCHMENT"
    assert [item.code for item in parsed.model.controls] == [1, 3, 1, 4, 5, 7]
    assert [item.identifier for item in parsed.model.subareas] == ["area_1", "area_2"]
    assert [item.label for item in parsed.model.subareas] == ["A", "B"]
    assert [item.length_km for item in parsed.model.reaches] == [Decimal(5), Decimal(4), Decimal("2.5")]
    assert any(span.field == "subarea_area_km2" and span.source_text == "30.000" for span in parsed.source_map)
    edited = replace(parsed.model, title="Changed title")
    with pytest.raises(ValueError, match="cannot represent edits"):
        original_bytes(parsed, current_model=edited)


def test_canonical_catg_roundtrip_and_custom_id_rejection() -> None:
    parsed = parse_catg(_catg().encode())
    exported = serialize_catg(parsed.model)
    updated = parse_catg(exported)
    assert updated.model == parsed.model
    assert b"C #NODES\nC 0" in exported
    assert updated.source.newline == "lf"
    custom = replace(parsed.model.subareas[0], identifier="custom")
    changed_control = replace(parsed.model.controls[0], subarea_id="custom")
    noncanonical = replace(
        parsed.model,
        subareas=(custom, *parsed.model.subareas[1:]),
        controls=(changed_control, *parsed.model.controls[1:]),
    )
    with pytest.raises(ValueError, match="ordinal IDs"):
        serialize_catg(noncanonical)


def test_explicit_storm_original_and_canonical_roundtrips() -> None:
    payload = _stm().encode("utf-8")
    parsed = parse_design_stm(payload)
    assert original_bytes(parsed) == payload
    assert parsed.model.timestep_hours == Decimal("0.5")
    assert parsed.model.percentages == (Decimal("60.0"), Decimal("40.0"))
    assert parsed.model.depths_mm == (Decimal("100.00"), Decimal("90.0"))
    assert len([field for field in parsed.source_map if field.field == "rainfall_depth_mm"]) == 2
    assert parse_design_stm(serialize_design_stm(parsed.model)).model == parsed.model


def test_cmd_par_canonical_and_original_bytes_and_paths() -> None:
    params = _params()
    output = serialize_cmd_par(params)
    assert b"Cat file :subfolder\\model.catg" in output
    assert b"Stm file :C:\\storms\\design.stm" in output
    parsed = parse_cmd_par(output.replace(b"\n", b"\r\n"))
    assert parsed.model == params
    assert original_bytes(parsed) == output.replace(b"\n", b"\r\n")
    assert parse_cmd_par(serialize_cmd_par(parsed.model)).model == params
    assert [item.line for item in parsed.source_map] == list(range(2, 11))


@pytest.mark.parametrize("model", [_params(), _run()])
def test_model_json_roundtrip_and_versioned_units(model: ParameterSet | RunModel) -> None:
    payload = to_dict(model)
    restored = from_dict(payload)
    assert restored == model
    assert from_json(to_json(model)) == model
    assert payload["schema_version"] == 1
    assert payload["units"]["area"] == "km2"
    assert isinstance(json.loads(to_json(model))["model"], dict)


def test_individual_catchment_and_storm_json_roundtrip() -> None:
    run = _run()
    for model in (run.catchment, run.storm):
        assert from_json(to_json(model)) == model


@pytest.mark.parametrize(
    "corruption",
    [
        lambda data: {**data, "schema_version": 2},
        lambda data: {**data, "units": {"area": "m2"}},
        lambda data: {**data, "unknown": "not permitted"},
        lambda data: {**data, "model": {**data["model"], "verbosity": True}},
        lambda data: {**data, "model": {**data["model"], "routing": [
            {"isa": 1, "kc": 12.5, "m": "0.8"}]}},
    ],
)
def test_invalid_json_is_not_coerced(corruption: Callable[[dict[str, Any]], dict[str, Any]]) -> None:
    edited = corruption(to_dict(_params()))
    with pytest.raises((TypeError, ValueError)):
        from_dict(edited)


@pytest.mark.parametrize(
    ("source", "extension", "status"),
    [
        (b"GUI saved profile", ".par", "unsupported"),
        (b"legacy combined file", ".dat", "unsupported"),
        (b"legacy text catchment", ".cat", "unsupported"),
        (_stm().replace("DESIGN", "FIT").encode(), ".stm", "unsupported"),
        (_stm().replace("200,1,1,1", "200,2,1,1").encode(), ".stm", "unsupported"),
        (_catg().replace("\n7, PRINT outlet", "\n11, PRINT outlet").encode(), ".catg", "unsupported"),
        (_catg().replace("C #STORAGES\nC 0", "C #STORAGES\nC 1").encode(), ".catg", "unsupported"),
        (_catg().replace("0, -99, No impervious area", "2, -99").encode(), ".catg", "unsupported"),
        (_stm().replace("100.00,90.0,-99", "100.00,90.0").encode(), ".stm", "invalid"),
        (_stm().replace("0, 2", "0, 3").encode(), ".stm", "invalid"),
        (_catg().replace("3, Store hydrograph", "4, Store hydrograph").encode(), ".catg", "invalid"),
        (_catg().replace("30.000, 20.000, -99", "30.000, -99").encode(), ".catg", "invalid"),
        (_catg().replace("7, PRINT outlet", "7, PRINT outlet\nEXTRA").encode(), ".catg", "invalid"),
        (_catg().replace("5, 2.500, -99, Reach 3", "5, 2.500, 100, Reach 3").encode(),
         ".catg", "invalid"),
        (_stm().replace("60.0,", "NaN,").encode(), ".stm", "invalid"),
        (_stm().replace("60.0,", "1_0.0,").encode(), ".stm", "invalid"),
        (_stm().replace("100.00,90.0,-99", "100.00,-99,90.0").encode(), ".stm", "invalid"),
    ],
)
def test_unrecognised_and_invalid_constructs_fail_explicitly(source: bytes, extension: str, status: str) -> None:
    with pytest.raises(FormatProblem) as caught:
        parse_bytes(source, extension)
    assert caught.value.status == status


def test_duplicate_json_identifiers_and_impossible_controls_rejected() -> None:
    model = _run().catchment
    with pytest.raises(ValueError, match="Duplicate"):
        replace(model, print_locations=(model.print_locations[0], model.print_locations[0]))
    with pytest.raises(ValueError, match=r"Unbalanced|Code 4|Code 3"):
        replace(model, controls=(ControlStep(4), *model.controls))
    with pytest.raises(ValueError, match="positive"):
        replace(model, subareas=(SubArea("area_1", Decimal(0)), *model.subareas[1:]))


def test_s2_boundary_converts_once_and_rejects_unverified_losses() -> None:
    run = _run()
    adapter = to_s2_payload(run)
    assert adapter.controls == ((1, 5.0), (3, 0.0), (1, 4.0), (4, 0.0), (5, 2.5), (7, 0.0))
    assert adapter.areas_km2 == (30.0, 20.0)
    assert adapter.kc == 12.0
    unsupported = replace(run, parameters=replace(run.parameters, loss_model=2))
    with pytest.raises(ValueError, match="IL/CL"):
        to_s2_payload(unsupported)


def test_file_adapters_are_read_only_and_no_clobber(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def prohibited(*_args: object, **_kwargs: object) -> None:
        pytest.fail("Parser must never start RORB")

    monkeypatch.setattr(subprocess, "run", prohibited)
    source = tmp_path / "source.catg"
    source.write_bytes(_catg().encode())
    before = source.read_bytes()
    assert isinstance(read_file(source).model, CatchmentModel)
    assert source.read_bytes() == before
    target = tmp_path / "canonical.catg"
    write_new(target, serialize_catg(parse_catg(before).model))
    assert parse_catg(target.read_bytes()).model == parse_catg(before).model
    with pytest.raises(FileExistsError):
        write_new(target, b"no overwriting")
    assert source.read_bytes() == before


def test_stable_model_outside_checkout_requires_no_source_file() -> None:
    payload = to_json(_run())
    assert isinstance(from_json(payload), RunModel)
    assert "original_bytes" not in payload


def test_cp1252_labels_preserve_original_encoding() -> None:
    raw = _catg().replace("PRINT outlet", "PRINT café").encode("cp1252")
    parsed = parse_catg(raw)
    assert parsed.source.encoding == "cp1252"
    assert parsed.model.print_locations[0].label == "PRINT café"
    assert original_bytes(parsed) == raw
