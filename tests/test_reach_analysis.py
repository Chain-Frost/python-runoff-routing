"""Independent continuous linear reference and water-balance verification."""

import math
from itertools import pairwise

import pytest

from runoff_routing.reach_analysis import audit_reach_balance, linear_continuous_reference
from runoff_routing.reach_routing import RoutingDomainError, route_reach


def test_continuous_linear_ramp_exact_solution() -> None:
    # dQ/dt + Q = t, Q(0) = 0 has exact Q(t) = t - 1 + exp(-t).
    out = linear_continuous_reference((0.0, 1.0, 2.0), coefficient_k=1.0, time_step_hours=1.0)
    assert out == pytest.approx((0.0, math.exp(-1.0), 1.0 + math.exp(-2.0)), rel=1e-13)


def test_continuous_linear_constant_inflow_is_equilibrium() -> None:
    assert linear_continuous_reference((3.0,) * 6, coefficient_k=2.0, time_step_hours=0.25) == pytest.approx(
        (3.0,) * 6
    )


def test_continuous_linear_no_storage_is_identity() -> None:
    inflow = (0.0, 12.0, 5.0, 0.0)
    assert linear_continuous_reference(inflow, coefficient_k=0.0, time_step_hours=0.5) == inflow


def test_continuous_reference_extreme_ratios() -> None:
    values = (0.0, 1.0, 0.0)
    assert linear_continuous_reference(values, coefficient_k=1e-320, time_step_hours=1.0) == values
    nearly_static = linear_continuous_reference(values, coefficient_k=1e12, time_step_hours=1e-6)
    assert all(math.isfinite(v) and v >= 0 for v in nearly_static)
    assert nearly_static[1] == pytest.approx(5e-19, rel=1e-9)


def test_independent_continuous_and_discrete_solutions_differ_at_finite_step() -> None:
    inflow = (0.0, 1.0, 2.0)
    continuous = linear_continuous_reference(inflow, coefficient_k=1.0, time_step_hours=1.0)
    discrete = route_reach(inflow, coefficient_k=1.0, exponent_m=1.0, time_step_hours=1.0)
    assert continuous[1] == pytest.approx(math.exp(-1.0))
    assert discrete[1] == pytest.approx(1.0 / 3.0)
    assert continuous != pytest.approx(discrete, rel=1e-4)


def test_trapezoidal_solution_converges_to_continuous_solution_when_refined() -> None:
    dt = 0.01
    inflow = tuple(index * dt for index in range(101))
    continuous = linear_continuous_reference(inflow, coefficient_k=1.0, time_step_hours=dt)
    discrete = route_reach(inflow, coefficient_k=1.0, exponent_m=1.0, time_step_hours=dt)
    assert discrete[-1] == pytest.approx(continuous[-1], abs=1e-5)


@pytest.mark.parametrize("exponent", [0.6, 0.8, 1.0, 1.25])
def test_balance_all_steps_and_closure(exponent: float) -> None:
    inflow = (0.0, 3.0, 8.0, 4.0, 1.0, 0.0, 0.0)
    outflow = route_reach(inflow, coefficient_k=1.0, exponent_m=exponent, time_step_hours=0.1)
    audit = audit_reach_balance(inflow, outflow, coefficient_k=1.0, exponent_m=exponent, time_step_hours=0.1)
    assert len(audit.steps) == len(inflow) - 1
    assert audit.initial_storage_m3 == 0.0
    assert audit.closure_residual_m3 == pytest.approx(0.0, abs=1e-7)
    assert audit.maximum_step_residual_m3 == pytest.approx(0.0, abs=1e-7)
    assert all(step.end_index == i for i, step in enumerate(audit.steps, 1))
    assert audit.integrated_inflow_m3 == pytest.approx(
        0.5 * 3600 * 0.1 * sum(a + b for a, b in pairwise(inflow))
    )


def test_balance_detects_nonconserving_routing() -> None:
    inflow = (0.0, 2.0, 0.0)
    wrong_outflow = (0.0, 0.0, 0.0)
    audit = audit_reach_balance(inflow, wrong_outflow, coefficient_k=1.0, exponent_m=1.0, time_step_hours=0.1)
    assert audit.maximum_step_residual_m3 == pytest.approx(360.0)
    assert audit.closure_residual_m3 == pytest.approx(-720.0)


def test_balance_one_sample() -> None:
    audit = audit_reach_balance((5.0,), (5.0,), coefficient_k=2.0, exponent_m=1.0, time_step_hours=1.0)
    assert audit.steps == ()
    assert audit.initial_storage_m3 == audit.final_storage_m3 == 36000.0
    assert audit.integrated_inflow_m3 == audit.integrated_outflow_m3 == audit.closure_residual_m3 == 0.0


@pytest.mark.parametrize(
    ("inflow", "outflow", "k", "m", "dt"),
    [
        ((), (), 1.0, 1.0, 1.0),
        ((0.0,), (0.0, 1.0), 1.0, 1.0, 1.0),
        ((0.0,), (float("nan"),), 1.0, 1.0, 1.0),
        ((-1.0,), (0.0,), 1.0, 1.0, 1.0),
        ((0.0,), (0.0,), -1.0, 1.0, 1.0),
        ((0.0,), (0.0,), 1.0, 0.0, 1.0),
        ((0.0,), (0.0,), 1.0, 1.0, 0.0),
    ],
)
def test_balance_invalid_inputs_fail(
    inflow: tuple[float, ...], outflow: tuple[float, ...], k: float, m: float, dt: float
) -> None:
    with pytest.raises(RoutingDomainError):
        audit_reach_balance(inflow, outflow, coefficient_k=k, exponent_m=m, time_step_hours=dt)


def test_continuous_reference_rejects_invalid_parameters() -> None:
    with pytest.raises(RoutingDomainError):
        linear_continuous_reference((0.0, 1.0), coefficient_k=-1, time_step_hours=0.25)
    with pytest.raises(RoutingDomainError):
        linear_continuous_reference((0.0, 1.0), coefficient_k=1, time_step_hours=0)
    with pytest.raises(RoutingDomainError):
        linear_continuous_reference((0.0, float('inf')), coefficient_k=1, time_step_hours=1)
