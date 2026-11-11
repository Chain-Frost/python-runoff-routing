"""S1 typed -> S2 calculation contract; synthetic inputs only, no native software."""

from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import replace
from decimal import Decimal
from pathlib import Path

import pytest

from runoff_routing.integration import (
    RunInputError,
    assess_recorded_print,
    canonical_run_bytes,
    parse_run_bytes,
    read_run_files,
    read_run_json,
    run_model,
    write_result_csv,
    write_result_json,
)
from runoff_routing.rorb_codec import (
    parse_catg,
    parse_cmd_par,
    parse_design_stm,
)
from runoff_routing.rorb_model import (
    CatchmentModel,
    ControlStep,
    LossValue,
    ParameterSet,
    PrintLocation,
    Reach,
    RoutingValue,
    RunModel,
    StormModel,
    SubArea,
    from_json,
    to_json,
)
from runoff_routing.single_storm import Catchment, Control, Losses, Storm, calculate_storm


def _run() -> RunModel:
    return RunModel(
        ParameterSet(
            "catchment.catg",
            "design.stm",
            True,
            3,
            1,
            1,
            1,
            (RoutingValue(1, Decimal("0.5"), Decimal(1)),),
            (LossValue(1, 1, Decimal(1), Decimal("0.1")),),
        ),
        CatchmentModel(
            "Synthetic catchment",
            (SubArea("area_1", Decimal("2.0"), "A"),),
            (Reach("reach_1", Decimal("3.0"), "Reach A Sub-area A"),),
            (
                ControlStep(1, "area_1", "reach_1", label="Reach A Sub-area A"),
                ControlStep(7, print_id="print_1", label="Print A"),
            ),
            (PrintLocation("print_1", "Print A"),),
        ),
        StormModel(
            "Synthetic storm",
            Decimal("0.5"),
            5,
            0,
            (Decimal(60), Decimal(40)),
            (Decimal("20.0"),),
            ("area_1",),
        ),
    )


def _files(run: RunModel) -> tuple[bytes, bytes, bytes]:
    return canonical_run_bytes(run)


def test_s1_to_s2_calculation_uses_the_same_kernel_and_explicit_print_identity() -> None:
    run = _run()
    actual = run_model(run)
    reference = calculate_storm(
        Catchment((Control(1, 3.0), Control(7)), (2.0,)),
        Storm(0.5, 5, (60.0, 40.0), (20.0,)),
        losses=Losses(1.0, 0.1),
        kc=0.5,
        m=1.0,
    )
    assert actual.numerical == reference
    assert actual.prints[0].print_id == "print_1"
    assert actual.prints[0].label == "Print A"
    assert actual.prints[0].discharge_m3_s == reference.outlets_m3_s[0]
    assert actual.parity_status == "unassessed"
    assert actual.output_time_convention == "model_elapsed_from_zero"


def test_original_files_json_canonical_files_read_then_calculate_roundtrip() -> None:
    run = _run()
    source_files = _files(run)
    parsed = parse_run_bytes(*source_files)
    assert parsed.model == run
    assert parsed.parameters.source.sha256 == hashlib.sha256(source_files[0]).hexdigest()
    assert parsed.catchment.source.data == source_files[1]
    assert parsed.storm.source.data == source_files[2]
    restored = read_run_json(to_json(parsed.model))
    assert restored == run
    converted = _files(restored)
    assert parse_cmd_par(converted[0]).model == run.parameters
    assert parse_catg(converted[1]).model == run.catchment
    assert parse_design_stm(converted[2]).model == run.storm
    assert run_model(restored) == run_model(parsed.model)



def test_canonical_rejects_unrepresentable_authored_labels() -> None:
    run = _run()
    altered = replace(
        run,
        catchment=replace(run.catchment, subareas=(replace(run.catchment.subareas[0], label="unserializable label"),)),
    )
    with pytest.raises(RunInputError, match="discard typed labels") as caught:
        canonical_run_bytes(altered)
    assert caught.value.code == "canonical_loss"


def test_run_file_adapter_reads_only_explicit_paths(tmp_path: Path) -> None:
    run = _run()
    par, catg, stm = _files(run)
    a, b, c = (tmp_path / name for name in ("one.par", "two.catg", "three.stm"))
    a.write_bytes(par)
    b.write_bytes(catg)
    c.write_bytes(stm)
    assert read_run_files(a, b, c).model == run


def test_print_order_for_multiple_print_locations_is_not_guessed() -> None:
    run = _run()
    catchment = CatchmentModel(
        "Two prints",
        run.catchment.subareas,
        (*run.catchment.reaches, Reach("reach_2", Decimal(1))),
        (
            ControlStep(1, "area_1", "reach_1"),
            ControlStep(7, print_id="print_1", label="Upstream"),
            ControlStep(5, reach_id="reach_2"),
            ControlStep(7, print_id="print_2", label="Downstream"),
        ),
        (PrintLocation("print_1", "Upstream"), PrintLocation("print_2", "Downstream")),
    )
    results = run_model(replace(run, catchment=catchment))
    assert [item.print_id for item in results.prints] == ["print_1", "print_2"]
    assert results.prints[0].discharge_m3_s != results.prints[1].discharge_m3_s


def test_loss_flag_two_rejected_at_execution_not_at_model_layer() -> None:
    run = _run()
    recognised = replace(run, parameters=replace(run.parameters, loss_model=2))
    with pytest.raises(RunInputError) as caught:
        run_model(recognised)
    assert caught.value.status == "unsupported"
    assert caught.value.code == "unsupported_s2_profile"


def test_start_increment_rejected_at_execution_not_at_model_layer() -> None:
    run = _run()
    model = replace(run, storm=replace(run.storm, start_increment=1))
    with pytest.raises(RunInputError, match="first increment"):
        run_model(model)


def test_underflow_and_overflow_fail_closed_at_float_boundary() -> None:
    run = _run()
    for value in (Decimal("1e-999"), Decimal("1e9999")):
        changed = replace(run, parameters=replace(run.parameters, routing=(RoutingValue(1, value, Decimal(1)),)))
        with pytest.raises(RunInputError) as caught:
            run_model(changed)
        assert caught.value.status == "unsupported"


def test_storm_precision_s1_accepts_but_s2_preflight_rejects() -> None:
    run = _run()
    altered = replace(run, storm=replace(run.storm, percentages=(Decimal(60), Decimal("40.03"))))
    with pytest.raises(RunInputError) as caught:
        run_model(altered)
    assert caught.value.code == "storm_precision"
    assert caught.value.role == "storm"


def test_parsing_failures_report_role_status_and_source_line() -> None:
    par, catg, stm = _files(_run())
    with pytest.raises(RunInputError) as caught:
        parse_run_bytes(par, catg.replace(b"7, Print A", b"11, Print A"), stm)
    assert caught.value.status == "unsupported"
    assert caught.value.role == "catchment"
    assert caught.value.line is not None
    with pytest.raises(RunInputError) as caught:
        parse_run_bytes(b"GUI configuration", catg, stm)
    assert caught.value.role == "parameters"


def test_partial_and_invalid_json_is_rejected_with_typed_diagnostics() -> None:
    run = _run()
    assert isinstance(from_json(to_json(run.parameters)), ParameterSet)
    with pytest.raises(RunInputError) as caught:
        read_run_json(to_json(run.parameters))
    assert caught.value.code == "incomplete_run"
    with pytest.raises(RunInputError) as caught:
        read_run_json(json.dumps({"schema_version": 999}))
    assert caught.value.code == "json_schema"


def test_offline_printed_comparator_is_explicit_and_does_not_declare_native_parity() -> None:
    result = run_model(_run())
    tokens = tuple(f"{value:.6f}" for value in result.prints[0].discharge_m3_s)
    audit = assess_recorded_print(result, tokens, print_id="print_1")
    assert audit.within_print_budget
    assert audit.sample_count == len(tokens)
    with pytest.raises(RunInputError, match="does not uniquely"):
        assess_recorded_print(result, tokens, print_id="Hyd001")
    with pytest.raises(ValueError, match="counts"):
        assess_recorded_print(result, tokens[1:], print_id="print_1")


def test_reports_are_machine_readable_no_clobber_and_contain_no_native_time_claim(tmp_path: Path) -> None:
    result = run_model(_run())
    json_target, csv_target = tmp_path / "run.json", tmp_path / "hydrographs.csv"
    write_result_json(json_target, result)
    write_result_csv(csv_target, result)
    report = json.loads(json_target.read_text(encoding="utf-8"))
    assert report["parity_status"] == "unassessed"
    assert report["output_time_convention"] == "model_elapsed_from_zero"
    csv_lines = csv_target.read_text(encoding="utf-8").splitlines()
    assert csv_lines[0] == "print_id,print_label,sample_index,model_elapsed_hours,discharge_m3_s"
    assert len(csv_lines) == 7
    with pytest.raises(FileExistsError):
        write_result_json(json_target, result)
    with pytest.raises(FileExistsError):
        write_result_csv(csv_target, result)


def test_pure_api_never_launches_native_engines(monkeypatch: pytest.MonkeyPatch) -> None:
    def no_subprocess(*_args: object, **_kwargs: object) -> None:
        pytest.fail("No external process should be launched")

    monkeypatch.setattr(subprocess, "run", no_subprocess)
    run = parse_run_bytes(*_files(_run())).model
    assert run_model(run).prints
