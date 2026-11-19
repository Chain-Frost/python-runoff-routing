"""Independent linear controls and existing typed CMD boundary checks for issue #92.

These controls are manufactured/analytical, not original CMD observations.
"""

from __future__ import annotations

import math
from dataclasses import replace
from decimal import Decimal
from pathlib import Path
from typing import cast

import pytest

from runoff_routing._cmd644.geometry import ReachGeometry
from runoff_routing._cmd644.precision import UnsupportedNumericPath, store
from runoff_routing._cmd644.routing import route_reach as route_cmd_reach
from runoff_routing.cmd_engine import adapt_event
from runoff_routing.engine_execution import run_engine_project
from runoff_routing.engine_types import EngineSelection
from runoff_routing.project_json import EmbeddedRun, Project, load_project, write_project
from runoff_routing.reach_routing import route_reach as route_default_reach
from runoff_routing.rorb_model import Reach, RoutingValue, RunModel, from_json

EXAMPLE = Path(__file__).parents[1] / "examples" / "synthetic-run.json"


def _model() -> RunModel:
    model = from_json(EXAMPLE.read_text(encoding="utf-8"))
    assert isinstance(model, RunModel)
    return model


def test_cmd_linear_m_one_has_complete_analytic_discrete_pulse() -> None:
    """For k=5h and h=0.5h, the linear reservoir ratio is 19/21."""
    geometry = ReachGeometry(1, 1.0, 1.0, 5.0, 18000.0)
    incoming = (0.0, 1.0, 0.0, 0.0)
    result = route_cmd_reach(incoming, geometry, 1800.0, (1,), exponent=1.0, hours=0.5)
    expected = (0.0, 1 / 21, 40 / 441, 760 / 9261)
    assert result.is_linear
    assert result.steps == ()
    assert len(result.q) == len(result.s) == len(incoming)
    assert result.q == pytest.approx(expected, rel=1e-6, abs=1e-8)
    assert result.s[1] == pytest.approx(result.q[1] * 18000, rel=1e-6)
    assert result.processed_peak == 1.0


def test_default_linear_m_one_has_independent_analytic_pulse() -> None:
    incoming = (0.0, 1.0, 0.0, 0.0)
    result = route_default_reach(incoming, coefficient_k=5.0, exponent_m=1.0, time_step_hours=0.5)
    assert result == pytest.approx((0.0, 1 / 21, 40 / 441, 760 / 9261), rel=1e-10, abs=1e-12)


@pytest.mark.parametrize("exponent", ["0.6", "1.2"])
def test_positive_nonunit_m_is_preserved_at_typed_cmd_boundary(tmp_path: Path, exponent: str) -> None:
    original = _model()
    routing = replace(original.parameters.routing[0], m=Decimal(exponent))
    model = replace(original, parameters=replace(original.parameters, routing=(routing,)))
    source = tmp_path / "event.json"
    write_project(source, Project("m_bound", "explicit", EmbeddedRun(model)))
    event = adapt_event(load_project(source))
    assert event.m.lexeme == exponent
    assert event.m.stored == store(float(exponent))
    # Typed source admission is distinct from executing and qualifying native CMD m>1.


@pytest.mark.parametrize("exponent", ["0.999", "1", "1.001"])
def test_positive_exponents_execute_complete_events_on_both_selected_engines(tmp_path: Path, exponent: str) -> None:
    """Synthetic event software check only; no original CMD boundary golden is inferred."""
    original = _model()
    routing = replace(original.parameters.routing[0], m=Decimal(exponent))
    model = replace(original, parameters=replace(original.parameters, routing=(routing,)))
    source = tmp_path / "positive-exponent.json"
    write_project(source, Project("m_positive_event", "explicit", EmbeddedRun(model)))

    for engine in ("python-cmd", "python"):
        result = run_engine_project(source, selection=EngineSelection.for_engine(engine))
        assert result.effective_selection.engine == engine
        assert result.status == "computed_unvalidated", result.diagnostics
        assert result.native_parity_status == "not_assessed"
        assert result.requested_print_ids == ("print_1",)
        assert len(result.hydrographs) == 1
        q = result.hydrographs[0].discharge_m3_s
        assert len(q) == model.storm.calculation_increments + 1
        assert len(result.physical_time_hours) == len(q)
        assert all(math.isfinite(value) and value >= 0 for value in q)
        assert result.native_raw_time_tokens == ()
        assert result.native_raw_increment_tokens == ()

        if engine == "python-cmd":
            assert result.python_diagnostics is not None
            reaches = cast("list[dict[str, object]]", result.python_diagnostics["reaches"])
            assert len(reaches) == 1
            assert reaches[0]["linear_routing"] is (exponent == "1")


def test_negative_reaches_still_rejected_by_s1_without_guessing_native_outcome() -> None:
    with pytest.raises(ValueError, match="nonnegative"):
        Reach("bad", Decimal(-1))


def test_zero_m_is_rejected_at_typed_domain_not_silently_routed() -> None:
    with pytest.raises(ValueError, match="positive"):
        RoutingValue(1, Decimal(5), Decimal(0))


def test_default_zero_storage_is_not_equivalent_to_zero_exponent() -> None:
    incoming = (0.0, 1.0, 0.5, 0.0)
    assert route_default_reach(incoming, coefficient_k=0.0, exponent_m=0.8, time_step_hours=0.5) == incoming
    assert all(math.isfinite(v) for v in incoming)


def test_cmd_routing_failure_is_explicit_and_never_returns_partial_q(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Manufactured convergence/error propagation; not a native CMD observation."""
    project = tmp_path / "event.json"
    write_project(project, Project("error_boundary", "explicit", EmbeddedRun(_model())))

    def fail_convergence(*_args: object, **_kwargs: object) -> None:
        message = "manufactured nonlinear convergence failure"
        raise UnsupportedNumericPath(message)

    monkeypatch.setattr("runoff_routing.cmd_engine.execute", fail_convergence)
    result = run_engine_project(project, selection=EngineSelection.for_engine("python-cmd"))
    assert result.effective_selection.engine == "python-cmd"
    assert result.status == "numerical_error"
    assert result.diagnostics[0].code == "cmd_arithmetic"
    assert "convergence failure" in result.diagnostics[0].message
    assert result.requested_print_ids == ("print_1",)
    assert result.hydrographs == ()
    assert result.physical_time_hours == ()
    assert result.native_raw_time_tokens == ()
