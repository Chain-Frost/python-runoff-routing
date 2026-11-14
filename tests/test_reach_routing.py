"""Analytic and independent synthetic checks, not RORB equivalence fixtures."""

import math

import pytest

from runoff_routing.reach_routing import RoutingDomainError, route_reach, storage_volume


def test_zero_storage_is_identity() -> None:
    inflow = (0.0, 10.0, 3.0, 0.0)
    assert route_reach(inflow, coefficient_k=0.0, exponent_m=0.8, time_step_hours=0.25) == inflow


def test_constant_inflow_is_in_equilibrium() -> None:
    inflow = (3.0,) * 8
    assert route_reach(inflow, coefficient_k=1.5, exponent_m=0.8, time_step_hours=0.1) == pytest.approx(inflow)


def test_initial_outflow_equals_initial_inflow() -> None:
    inflow = (2.0, 8.0, 0.0)
    routed = route_reach(inflow, coefficient_k=1.0, exponent_m=1.0, time_step_hours=0.5)
    assert routed[0] == inflow[0]


def test_linear_reach_matches_analytical_recurrence() -> None:
    routed = route_reach((0.0, 10.0, 0.0), coefficient_k=1.0, exponent_m=1.0, time_step_hours=0.5)
    assert routed == pytest.approx((0.0, 2.0, 3.2))


def test_nonlinear_manufactured_solution() -> None:
    routed = route_reach((0.0, 3.0), coefficient_k=1.0, exponent_m=0.8, time_step_hours=1.0)
    assert routed == pytest.approx((0.0, 1.0), rel=1e-11)


@pytest.mark.parametrize("exponent", [0.6, 0.8, 1.0, 1.25])
def test_stepwise_continuity_is_independent_of_solver(exponent: float) -> None:
    input_values = (0.0, 2.0, 7.0, 3.0, 1.0, 0.0, 0.0, 0.0)
    k = 1.5
    dt_hours = 0.1
    out = route_reach(input_values, coefficient_k=k, exponent_m=exponent, time_step_hours=dt_hours)
    for index in range(1, len(out)):
        delta_storage = storage_volume(out[index], coefficient_k=k, exponent_m=exponent) - storage_volume(
            out[index - 1], coefficient_k=k, exponent_m=exponent
        )
        average_net_flow = (
            0.5 * 3600.0 * dt_hours * (input_values[index - 1] + input_values[index] - out[index - 1] - out[index])
        )
        assert delta_storage == pytest.approx(average_net_flow, rel=1e-9, abs=1e-7)
        assert out[index] >= 0.0


def test_linear_long_step_fails_instead_of_clipping_negative_flow() -> None:
    with pytest.raises(RoutingDomainError, match="negative/non-finite"):
        route_reach((1.0, 0.0, 0.0), coefficient_k=1.0, exponent_m=1.0, time_step_hours=10.0)


@pytest.mark.parametrize(
    ("inflow", "k", "m", "dt"),
    [
        ((), 1.0, 0.8, 0.1),
        ((-1.0,), 1.0, 0.8, 0.1),
        ((math.nan,), 1.0, 0.8, 0.1),
        ((math.inf,), 1.0, 0.8, 0.1),
        ((1.0,), -1.0, 0.8, 0.1),
        ((1.0,), 1.0, 0.0, 0.1),
        ((1.0,), 1.0, math.inf, 0.1),
        ((1.0,), 1.0, 0.8, 0.0),
        ((1.0,), 1.0, 0.8, math.nan),
    ],
)
def test_invalid_inputs_fail_explicitly(inflow: tuple[float, ...], k: float, m: float, dt: float) -> None:
    with pytest.raises(RoutingDomainError):
        route_reach(inflow, coefficient_k=k, exponent_m=m, time_step_hours=dt)


def test_storage_uses_documented_units() -> None:
    assert storage_volume(2.0, coefficient_k=1.0, exponent_m=1.0) == 7200.0


def test_storage_overflow_fails_explicitly() -> None:
    with pytest.raises(RoutingDomainError, match="overflowed"):
        storage_volume(1e200, coefficient_k=1.0, exponent_m=2.0)


@pytest.mark.parametrize("dt_hours", [0.5, 0.25, 0.125])
def test_manufactured_nonlinear_endpoint_matches_independent_continuity(dt_hours: float) -> None:
    # Set Q[0]=I[0]=0, Q[1]=1 and k=1, so continuity fixes I[1]=2/dt+1.
    actual = route_reach((0.0, 2.0 / dt_hours + 1.0), coefficient_k=1.0, exponent_m=0.8, time_step_hours=dt_hours)
    assert actual == pytest.approx((0.0, 1.0), abs=1e-11)


@pytest.mark.parametrize("dt_hours", [0.5, 0.25, 0.125])
def test_manufactured_nonlinear_equilibrium_is_unchanged(dt_hours: float) -> None:
    actual = route_reach((2.0,) * 21, coefficient_k=1.0, exponent_m=0.8, time_step_hours=dt_hours)
    assert actual == pytest.approx((2.0,) * 21, abs=1e-10)
