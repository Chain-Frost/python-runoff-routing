"""Synthetic-only precision contracts: private capture bytes are never distributed."""

import math

import pytest
from runoff_routing.parity_metrics import assess_printed_parity, audit_printed_linear_balance
from runoff_routing.reach_routing import route_reach


def _triangle(dt: float) -> tuple[float, ...]:
    steps = round(10.0 / dt)
    return tuple(max(0.0, 10.0 - 20.0 * abs(index * dt - 0.5)) for index in range(steps + 1))


@pytest.mark.parametrize("dt", [0.5, 0.25])
def test_linear_triangle_full_print_precision_and_balance(dt: float) -> None:
    inflow = _triangle(dt)
    predicted = route_reach(inflow, coefficient_k=1.0, exponent_m=1.0, time_step_hours=dt)
    inflow_tokens = tuple(f"{value:.4f}" for value in inflow)
    printed = tuple(f"{value:.4f}" for value in predicted)
    precision = assess_printed_parity(predicted, printed, dt_hours=dt)
    balance = audit_printed_linear_balance(inflow, inflow_tokens, printed, coefficient_k=1.0, dt_hours=dt)
    assert precision.sample_count == len(inflow)
    assert precision.within_print_budget
    assert precision.matching_samples == len(inflow)
    assert precision.first_outside_budget_index is None
    assert precision.predicted_peak_index == (2 if dt == 0.5 else 3)
    assert abs(precision.native_integral_m3 - precision.predicted_integral_m3) <= precision.integral_rounding_bound_m3
    assert balance.steps_within_budget
    assert balance.closure_within_budget
    assert len(balance.steps) == len(inflow) - 1
    assert balance.steps[0].end_index == 1
    assert all(step.within_print_budget for step in balance.steps)
    assert balance.max_step_printing_bound_m3 == pytest.approx(0.36)
    # Exact prescribed initial state permits a tighter bound than the
    # prewritten conservative 1.98 m³ allowance.
    assert balance.closure_printing_bound_m3 == pytest.approx(1.935 if dt == 0.5 else 1.9575)
    assert balance.closure_printing_bound_m3 <= 1.98
    assert balance.inflow_integral_m3 == pytest.approx(18_000)


def test_nonzero_initial_equilibrium_and_repeat_determinism() -> None:
    inflow = (2.0,) * 21
    predicted = route_reach(inflow, coefficient_k=1.0, exponent_m=1.0, time_step_hours=0.5)
    assert predicted == route_reach(inflow, coefficient_k=1.0, exponent_m=1.0, time_step_hours=0.5)
    assert predicted == inflow
    native = ("2.0000",) * len(inflow)
    report = assess_printed_parity(predicted, native, dt_hours=0.5)
    assert report.within_print_budget
    audit = audit_printed_linear_balance(inflow, native, native, coefficient_k=1.0, dt_hours=0.5)
    assert audit.initial_inferred_storage_m3 == audit.final_inferred_storage_m3 == 7200.0
    assert audit.inflow_integral_m3 == audit.outflow_integral_m3 == 72000.0
    assert audit.closure_residual_m3 == audit.max_step_residual_m3 == 0.0


def test_outside_print_budget_does_not_get_relaxed_for_peak_match() -> None:
    data = (0.0, 2.0, 3.2, 1.92)
    native = ("0.0000", "2.0000", "3.2000", "1.9162")
    result = assess_printed_parity(data, native, dt_hours=0.5)
    assert not result.within_print_budget
    assert result.matching_samples == 3
    assert result.first_outside_budget_index == 3
    assert result.predicted_peak_index == result.native_peak_index == 2
    assert result.maximum_absolute_error_m3_s == pytest.approx(0.0038)


def test_per_token_resolution_and_near_zero_scale() -> None:
    data = (0.00004, 1.049, 1.06)
    tokens = ("0.0000", "1.0", "1.06")
    report = assess_printed_parity(data, tokens, dt_hours=1)
    assert report.within_print_budget
    assert report.maximum_near_zero_absolute_error_m3_s == pytest.approx(0.00004)
    assert report.maximum_scaled_error >= 0.8


def test_balance_detects_nonconserving_native_table() -> None:
    incoming = (0.0, 10.0, 0.0, 0.0)
    outgoing = ("0.0000", "2.0000", "3.2000", "1.9160")
    balance = audit_printed_linear_balance(
        incoming, ("0.0000", "10.0000", "0.0000", "0.0000"),
        outgoing, coefficient_k=1.0, dt_hours=0.5,
    )
    assert not balance.steps_within_budget
    assert balance.first_outside_step_budget_index == 3
    assert not balance.steps[2].within_print_budget
    assert balance.steps[2].closure_residual_m3 != 0


@pytest.mark.parametrize(
    ("prediction", "tokens", "dt"),
    [
        ((), (), 0.5),
        ((1.0,), ("1.000", "2.000"), 0.5),
        ((math.nan,), ("0.000",), 0.5),
        ((0.0,), ("NaN",), 0.5),
        ((0.0,), ("-1.0",), 0.5),
        ((0.0,), ("0.0",), 0.0),
    ],
)
def test_invalid_precision_inputs_fail(prediction: tuple[float, ...], tokens: tuple[str, ...], dt: float) -> None:
    with pytest.raises(ValueError):
        assess_printed_parity(prediction, tokens, dt_hours=dt)


def test_printed_upstream_requires_matching_prescribed_inflow() -> None:
    with pytest.raises(ValueError, match="Prescribed inflow"):
        audit_printed_linear_balance(
            (0.0, 5.0), ("0.0000", "4.9990"), ("0.0000", "1.0000"),
            coefficient_k=1.0, dt_hours=0.5,
        )
