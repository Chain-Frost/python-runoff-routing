"""Public CMD adapter and pure numerical controls; never launch RORB or load private fixtures."""

from __future__ import annotations

import json
import math
from dataclasses import replace
from decimal import Decimal
from fractions import Fraction
from pathlib import Path
from typing import cast

import pytest

from runoff_routing._cmd644.geometry import ReachGeometry
from runoff_routing._cmd644.power import bounded_power
from runoff_routing._cmd644.precision import direct_binary32, internal_store, store
from runoff_routing._cmd644.preparation import prepare
from runoff_routing._cmd644.routing import route_reach
from runoff_routing.cmd_engine import CMD_PROFILE, CmdBoundaryError, adapt_event
from runoff_routing.engine_execution import run_engine_project
from runoff_routing.engine_types import EngineSelection, EngineStatus
from runoff_routing.integration import canonical_run_bytes, parse_run_bytes
from runoff_routing.project_json import EmbeddedRun, Project, load_project, write_project
from runoff_routing.rorb_model import (
    CatchmentModel,
    ControlStep,
    PrintLocation,
    Reach,
    RunModel,
    SubArea,
    from_json,
    to_json,
)

EXAMPLE = Path(__file__).parents[1] / "examples" / "synthetic-run.json"


def _model() -> RunModel:
    value = from_json(EXAMPLE.read_text(encoding="utf-8"))
    assert isinstance(value, RunModel)
    return value


def _project(directory: Path, model: RunModel, *, cmd_stored: bool = False) -> Path:
    project = directory / "event.json"
    chosen = EngineSelection.for_engine("python-cmd") if cmd_stored else EngineSelection()
    write_project(project, Project("cmd_example", "explicit", EmbeddedRun(model), engine=chosen))
    return project


def test_single_source_typed_event_preserves_decimal_and_order(tmp_path: Path) -> None:
    project = _project(tmp_path, _model())
    event = adapt_event(load_project(project))
    assert event.event_id == "cmd_example"
    assert event.h.lexeme == "0.5"
    assert event.depths[0].lexeme == "20.0"
    assert tuple(item.code for item in event.controls) == (1, 7)
    assert len(event.weights) == 2
    assert event.weights[0].stored == 60.0
    assert event.n == 5
    assert event.impervious[0].stored == 0.0


def _mode_two_model(*, initial: str = "5", coefficient: str = "0.5") -> RunModel:
    model = _model()
    loss = replace(
        model.parameters.losses[0],
        initial_loss_mm=Decimal(initial),
        continuing=Decimal(coefficient),
    )
    return replace(model, parameters=replace(model.parameters, loss_model=2, losses=(loss,)))


def test_mode_two_round_trip_and_source_level_proportional_excess(tmp_path: Path) -> None:
    model = _mode_two_model()
    assert parse_run_bytes(*canonical_run_bytes(model)).model == model
    source = _project(tmp_path, model, cmd_stored=True)
    event = adapt_event(load_project(source))
    assert event.loss_model == 2
    assert event.cl.lexeme == "0.5"
    prepared = prepare(event)
    assert prepared.rain[0] == (12.0, 8.0)
    assert prepared.after_initial[0] == (7.0, 8.0)
    assert prepared.excess[0] == (3.5, 4.0)
    assert prepared.crossings[0].bin_one_based == 1
    expected_volume = float(model.catchment.subareas[0].area_km2) * sum(prepared.excess[0]) * 1000
    assert sum(prepared.hydrographs[0][1:]) * prepared.seconds == pytest.approx(expected_volume, abs=0.02)

    result = run_engine_project(source)
    assert result.status == "computed_unvalidated"
    assert result.native_parity_status == "not_assessed"
    assert result.native_raw_increment_tokens == ()
    assert result.requested_print_ids == ("print_1",)
    assert len(result.hydrographs[0].discharge_m3_s) == len(result.physical_time_hours) == 6
    assert result.python_diagnostics is not None
    assert result.python_diagnostics["loss_model"] == 2
    assert result.python_diagnostics["runoff_coefficient_stored"] == 0.5
    assert result.python_diagnostics["continuing_loss_mm_h_stored"] is None
    assert result.python_diagnostics["source_rainfall_excess_mm_stored"] == ((3.5, 4.0),)

    # The same numeric 0.5 has different units and meaning in IL/CL mode 1.
    mode_one = replace(model, parameters=replace(model.parameters, loss_model=1))
    other_dir = tmp_path / "mode1"
    other_dir.mkdir()
    mode_one_source = _project(other_dir, mode_one, cmd_stored=True)
    assert prepare(adapt_event(load_project(mode_one_source))).excess[0] == (6.75, 7.75)
    mode_one_result = run_engine_project(mode_one_source)
    assert mode_one_result.status == "computed_unvalidated"
    assert mode_one_result.hydrographs != result.hydrographs


@pytest.mark.parametrize(
    ("initial", "coefficient", "expected"),
    [
        ("12", "0.5", (0.0, 4.0)),
        ("5", "0", (0.0, 0.0)),
        ("5", "1", (7.0, 8.0)),
        ("30", "0.7", (0.0, 0.0)),
    ],
)
def test_mode_two_equality_zero_and_coefficient_boundaries(
    tmp_path: Path, initial: str, coefficient: str, expected: tuple[float, float]
) -> None:
    model = _mode_two_model(initial=initial, coefficient=coefficient)
    source = _project(tmp_path, model, cmd_stored=True)
    event = adapt_event(load_project(source))
    assert prepare(event).excess[0] == expected
    outcome = run_engine_project(source)
    assert outcome.status == "computed_unvalidated"
    assert len(outcome.hydrographs[0].discharge_m3_s) == 6


@pytest.mark.parametrize("exponent", ["1", "0.8"])
def test_zero_length_terminal_code5_copies_positive_flow_at_two_physical_prints(tmp_path: Path, exponent: str) -> None:
    """Python source/installed-wheel smoke, not a new native acceptance case."""
    original = _model()
    catchment = original.catchment
    terminal = Reach("reach_2", Decimal(0), "terminal zero-length code 5")
    model = replace(
        original,
        parameters=replace(
            original.parameters,
            routing=(replace(original.parameters.routing[0], m=Decimal(exponent)),),
        ),
        catchment=replace(
            catchment,
            reaches=(*catchment.reaches, terminal),
            controls=(
                catchment.controls[0],
                catchment.controls[-1],
                ControlStep(5, reach_id=terminal.identifier),
                ControlStep(7, print_id="print_2"),
            ),
            print_locations=(*catchment.print_locations, PrintLocation("print_2", "terminal output")),
        ),
    )
    assert from_json(to_json(model)) == model
    path = _project(tmp_path, model, cmd_stored=True)
    for engine in ("python-cmd", "python"):
        result = run_engine_project(path, selection=EngineSelection.for_engine(engine))
        assert result.status == "computed_unvalidated", result.diagnostics
        assert result.requested_print_ids == ("print_1", "print_2")
        assert len(result.hydrographs) == 2
        first, terminal_print = (record.discharge_m3_s for record in result.hydrographs)
        assert first == terminal_print
        assert any(value > 0 for value in terminal_print)
        assert result.native_parity_status == "not_assessed"
        if engine == "python-cmd":
            assert result.python_diagnostics is not None
            reaches = cast("list[dict[str, object]]", result.python_diagnostics["reaches"])
            assert len(reaches) == 2
            assert reaches[-1]["zero_length_terminal_copy"] is True
            assert reaches[-1]["coefficient_hours_stored"] == 0.0
            assert reaches[-1]["S_m3_stored"] == (0.0,) * len(terminal_print)
            assert reaches[-1]["Q_m3_s_stored"] == first


def test_typed_model_rejects_nonterminal_zero_length_reach() -> None:
    original = _model()
    catchment = original.catchment
    terminal = Reach("reach_2", Decimal(0))
    with pytest.raises(ValueError, match="terminal code 5"):
        replace(
            catchment,
            reaches=(*catchment.reaches, terminal),
            controls=(
                catchment.controls[0],
                ControlStep(5, reach_id=terminal.identifier),
                catchment.controls[-1],
                ControlStep(7, print_id="print_2"),
            ),
            print_locations=(*catchment.print_locations, PrintLocation("print_2")),
        )


def test_mode_two_dry_event_and_no_crossing(tmp_path: Path) -> None:
    model = _mode_two_model(initial="0")
    model = replace(model, storm=replace(model.storm, depths_mm=(Decimal(0),)))
    source = _project(tmp_path, model, cmd_stored=True)
    event = adapt_event(load_project(source))
    prepared = prepare(event)
    assert prepared.crossings[0].bin_one_based is None
    assert prepared.excess[0] == (0.0, 0.0)
    assert set(prepared.hydrographs[0]) == {0.0}
    outcome = run_engine_project(source)
    assert outcome.status == "computed_unvalidated"
    assert set(outcome.hydrographs[0].discharge_m3_s) == {0.0}


def test_mode_two_rejects_nonfractional_coefficient_before_calculation() -> None:
    # The typed S1 boundary now rejects an impossible coefficient before
    # project persistence or computational adapter execution.
    with pytest.raises(ValueError, match="Runoff coefficient"):
        _mode_two_model(coefficient="1.01")


def test_public_cmd_runs_full_horizon_without_native_or_fallback(tmp_path: Path) -> None:
    source = _project(tmp_path, _model(), cmd_stored=True)
    cmd = run_engine_project(source)
    engineering = run_engine_project(source, selection=EngineSelection.for_engine("python"))
    assert cmd.status == engineering.status == "computed_unvalidated"
    assert cmd.effective_selection.engine == "python-cmd"
    assert engineering.effective_selection.engine == "python"
    assert cmd.stored_selection.engine == "python-cmd"
    assert cmd.native_parity_status == "not_assessed"
    assert cmd.native_executable_sha256 is None
    assert len(cmd.hydrographs) == len(engineering.hydrographs) == 1
    assert len(cmd.hydrographs[0].discharge_m3_s) == 6
    assert cmd.physical_time_hours == ("0.0", "0.5", "1.0", "1.5", "2.0", "2.5")
    assert cmd.hydrographs[0].print_id == "print_1"
    assert cmd.python_diagnostics is not None
    assert cmd.python_diagnostics["cmd_profile"] == CMD_PROFILE
    assert cmd.python_diagnostics["native_parity"] == "not_assessed_for_this_public_source_or_wheel"
    assert math.isclose(cmd.hydrographs[0].discharge_m3_s[1], 4.0555556, abs_tol=0.001)


def test_repeated_runs_are_isolated_and_source_changes_output(tmp_path: Path) -> None:
    root = tmp_path / "a"
    root.mkdir()
    source = _project(root, _model())
    choice = EngineSelection.for_engine("python-cmd")
    first = run_engine_project(source, selection=choice)
    second = run_engine_project(source, selection=choice)
    assert first.hydrographs == second.hydrographs
    model = _model()
    storm = replace(model.storm, depths_mm=(Decimal("30.0"),))
    root2 = tmp_path / "b"
    root2.mkdir()
    other = _project(root2, replace(model, storm=storm))
    altered = run_engine_project(other, selection=choice)
    assert altered.status == "computed_unvalidated"
    assert altered.hydrographs != first.hydrographs


def test_future_profile_never_falls_back(tmp_path: Path) -> None:
    source = _project(tmp_path, _model())
    outcome = run_engine_project(source, selection=EngineSelection.for_engine("python-cmd", "cmd-6.45"))
    assert outcome.status == "unavailable_engine"
    assert outcome.diagnostics[0].code == "cmd_profile"
    assert outcome.hydrographs == ()


def test_nonlumped_profile_rejected_before_output(tmp_path: Path) -> None:
    model = _model()
    changed = replace(model, parameters=replace(model.parameters, lumped_kc=False))
    project = _project(tmp_path, changed)
    result = run_engine_project(project, selection=EngineSelection.for_engine("python-cmd"))
    assert result.status == "unsupported_feature"
    assert result.diagnostics[0].code == "cmd_parameters"
    assert not result.hydrographs


def test_two_code_seven_prints_without_intervening_reach_return_identical_full_outlets(tmp_path: Path) -> None:
    model = _model()
    catchment = model.catchment
    controls = (
        catchment.controls[0],
        ControlStep(7, print_id="internal", label="Interior"),
        catchment.controls[1],
    )
    extended = replace(
        catchment,
        controls=controls,
        print_locations=(PrintLocation("internal"), *catchment.print_locations),
    )
    project = _project(tmp_path, replace(model, catchment=extended))
    result = run_engine_project(project, selection=EngineSelection.for_engine("python-cmd"))
    assert result.status == "computed_unvalidated"
    assert tuple(item.print_id for item in result.hydrographs) == ("internal", "print_1")
    assert len(result.hydrographs[0].discharge_m3_s) == 6
    assert result.hydrographs[0].discharge_m3_s == result.hydrographs[1].discharge_m3_s


def test_delayed_rainfall_preserves_full_horizon(tmp_path: Path) -> None:
    model = _model()
    storm = replace(model.storm, start_increment=2)
    project = _project(tmp_path, replace(model, storm=storm))
    event = adapt_event(load_project(project))
    assert tuple(value.stored for value in event.weights[:2]) == (0.0, 0.0)
    result = run_engine_project(project, selection=EngineSelection.for_engine("python-cmd"))
    assert result.status == "computed_unvalidated"
    assert len(result.hydrographs[0].discharge_m3_s) == 6
    assert result.hydrographs[0].discharge_m3_s[:3] == (0.0, 0.0, 0.0)


def test_stored_binary32_core_separates_linear_and_nonlinear() -> None:
    geometry = ReachGeometry(1, 1.0, 1.0, 1.0, 3600.0)
    linear = route_reach((0.0, 1.0, 0.0, 0.0), geometry, 900, (1,), exponent=1.0, hours=0.25)
    assert linear.is_linear
    assert not linear.steps
    assert linear.q[1] == store(0.25 / 2.25)
    nonlinear = route_reach((0.0, 1.0, 0.0), geometry, 900, (1,), exponent=store(0.8), hours=0.25)
    assert not nonlinear.is_linear
    assert nonlinear.steps
    assert nonlinear.q[0] == 0


@pytest.mark.parametrize(("numerator", "expected"), [(1, 0), (3, 2), (5, 2)])
def test_exact_subnormal_rounding(numerator: int, expected: int) -> None:
    assert direct_binary32(Fraction(numerator, 2**150)) == Fraction(expected, 2**149)


@pytest.mark.parametrize("exponent", range(1, 8))
def test_integer_power_stores_at_each_step(exponent: int) -> None:
    base = store(1.2345)
    actual = base
    for _ in range(1, exponent):
        actual = internal_store(actual * base)
    assert bounded_power(base, float(exponent)) == actual


def test_no_reference_fallback_or_output_substitution(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    project = _project(tmp_path, _model())

    def interrupt(*_args: object, **_kwargs: object) -> None:
        status: EngineStatus = "numerical_error"
        raise CmdBoundaryError(status, "forced_computation_failure", "Forced fresh calculation failure")

    monkeypatch.setattr("runoff_routing.cmd_engine.execute", interrupt)
    outcome = run_engine_project(project, selection=EngineSelection.for_engine("python-cmd"))
    assert outcome.status == "numerical_error"
    assert outcome.diagnostics[0].code == "forced_computation_failure"
    assert outcome.hydrographs == ()


def test_result_json_has_actual_source_identity_and_diagnostics(tmp_path: Path) -> None:
    project = _project(tmp_path, _model())
    outcome = run_engine_project(project, selection=EngineSelection.for_engine("python-cmd"))
    data = json.loads(outcome.to_json())
    assert data["model_sha256"] == data["python_diagnostics"]["model_input_sha256"]
    assert data["effective_selection"]["numerical_profile"] == "cmd-6.44"
    assert len(data["python_diagnostics"]["reaches"][0]["Q_m3_s_stored"]) == 6
    assert data["native_raw_time_tokens"] == []


@pytest.mark.parametrize("magnitude", ["1e-400", "1e-330", "1e-325"])
def test_cmd_rejects_decimal_underflow_without_emulating_zero_exponent(tmp_path: Path, magnitude: str) -> None:
    """A positive Decimal that binary64 loses cannot silently select the m=0 branch."""
    model = _model()
    value = Decimal(magnitude)
    assert value > 0
    assert float(value) == 0
    routing = replace(model.parameters.routing[0], m=value)
    parameters = replace(model.parameters, routing=(routing,))
    altered = replace(model, parameters=parameters)
    project = _project(tmp_path, altered, cmd_stored=True)
    outcome = run_engine_project(project)
    assert outcome.status == "unsupported_feature"
    assert outcome.hydrographs == ()
    assert len(outcome.diagnostics) == 1
    assert outcome.diagnostics[0].code == "cmd_input_representation"
    assert "underflows binary64" in outcome.diagnostics[0].message


def test_cmd_preserves_exact_zero_operand_boundary(tmp_path: Path) -> None:
    """An actual zero is valid and must not be mistaken for underflow."""
    event = adapt_event(load_project(_project(tmp_path, _model())))
    assert event.impervious[0].lexeme == "0"
    assert event.impervious[0].stored == 0.0


def test_public_typed_domain_rejects_zero_exponent() -> None:
    model = _model()
    with pytest.raises(ValueError, match="m must be"):
        replace(model.parameters.routing[0], m=Decimal(0))


def test_two_source_branches_preserve_original_order_and_complete_outlet(tmp_path: Path) -> None:
    """A save/restore confluence must consume every source and reach exactly once."""

    model = _model()
    catchment = CatchmentModel(
        "Two source synthetic",
        (SubArea("first", Decimal(1)), SubArea("second", Decimal(2))),
        (
            Reach("first_reach", Decimal(1)),
            Reach("second_reach", Decimal("1.5")),
            Reach("outlet_reach", Decimal("0.5")),
        ),
        (
            ControlStep(1, subarea_id="first", reach_id="first_reach"),
            ControlStep(3),
            ControlStep(1, subarea_id="second", reach_id="second_reach"),
            ControlStep(4),
            ControlStep(5, reach_id="outlet_reach"),
            ControlStep(7, print_id="joined"),
        ),
        (PrintLocation("joined", "Both sources"),),
    )
    storm = replace(
        model.storm,
        subarea_ids=("first", "second"),
        depths_mm=(Decimal("20.0"), Decimal("30.0")),
    )
    source = _project(tmp_path, replace(model, catchment=catchment, storm=storm))
    event = adapt_event(load_project(source))
    assert tuple(step.code for step in event.controls) == (1, 3, 1, 4, 5, 7)
    assert tuple(item.lexeme for item in event.depths) == ("20.0", "30.0")
    outcome = run_engine_project(source, selection=EngineSelection.for_engine("python-cmd"))
    assert outcome.status == "computed_unvalidated"
    assert len(outcome.hydrographs) == 1
    assert outcome.hydrographs[0].print_id == "joined"
    assert len(outcome.hydrographs[0].discharge_m3_s) == 6
    assert outcome.python_diagnostics is not None
    assert outcome.python_diagnostics["ordered_source_ids"] == ("first", "second")
    assert outcome.python_diagnostics["ordered_reach_ids"] == (
        "first_reach",
        "second_reach",
        "outlet_reach",
    )
    reaches = cast("list[dict[str, object]]", outcome.python_diagnostics["reaches"])
    assert len(reaches) == 3
    members = cast("tuple[int, ...]", reaches[-1]["source_membership_one_based"])
    assert set(members) == {1, 2}
