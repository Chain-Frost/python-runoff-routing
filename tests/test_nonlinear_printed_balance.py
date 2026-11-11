"""Public synthetic-only nonlinear storage and nonanticipation diagnostics."""

import math

import pytest
from runoff_routing.parity_metrics import audit_printed_nonlinear_balance
from runoff_routing.reach_routing import RoutingDomainError, route_reach


@pytest.mark.parametrize("dt", [0.5, 0.25, 0.125])
def test_exact_nonlinear_manufactured_endpoint_is_within_print_budget(dt: float) -> None:
    qin1 = 1.0 + 2.0 / dt
    balance = audit_printed_nonlinear_balance(
        (0.0, qin1),
        ("0.0000", f"{qin1:.4f}"),
        ("0.0000", "1.0000"),
        coefficient_k=1.0,
        exponent_m=0.8,
        dt_hours=dt,
    )
    assert balance.exponent_m == 0.8
    assert balance.first_outside_step_budget_index is None
    assert balance.steps_within_budget
    assert balance.closure_within_budget
    assert balance.initial_inferred_storage_m3 == 0.0
    assert balance.steps[0].end_index == 1


@pytest.mark.parametrize("dt", [0.5, 0.25, 0.125])
def test_material_synthetic_nonlinear_mismatch_exceeds_print_budget(dt: float) -> None:
    qin1 = 1.0 + 2.0 / dt
    balance = audit_printed_nonlinear_balance(
        (0.0, qin1),
        ("0.0000", f"{qin1:.4f}"),
        ("0.0000", "1.0030"),
        coefficient_k=1.0,
        exponent_m=0.8,
        dt_hours=dt,
    )
    assert not balance.steps_within_budget
    assert not balance.closure_within_budget
    assert balance.first_outside_step_budget_index == 1
    assert balance.max_step_residual_m3 > balance.max_step_printing_bound_m3
    assert balance.steps[0].closure_residual_m3 > balance.steps[0].print_rounding_bound_m3


def test_nonzero_equilibrium_balance_is_exact() -> None:
    report = audit_printed_nonlinear_balance(
        (2.0,) * 21,
        ("2.0000",) * 21,
        ("2.0000",) * 21,
        coefficient_k=1.0,
        exponent_m=0.8,
        dt_hours=0.5,
    )
    assert report.steps_within_budget and report.closure_within_budget
    assert report.closure_residual_m3 == 0.0
    assert report.initial_inferred_storage_m3 == report.final_inferred_storage_m3
    assert report.inflow_integral_m3 == report.outflow_integral_m3


def test_printed_zero_has_finite_sublinear_storage_bound() -> None:
    report = audit_printed_nonlinear_balance(
        (0.0, 0.0),
        ("0.0000", "0.0000"),
        ("0.0000", "0.0000"),
        coefficient_k=1.0,
        exponent_m=0.5,
        dt_hours=0.5,
    )
    assert math.isfinite(report.max_step_printing_bound_m3)
    assert report.max_step_printing_bound_m3 > 0.0
    assert report.steps_within_budget


@pytest.mark.parametrize("later", [(5.0, 0.0, 0.0), (100.0, 0.0, 0.0), (0.0, 100.0, 0.0)])
def test_strict_nonlinear_solver_is_causal(later: tuple[float, ...]) -> None:
    short = route_reach((0.0, 5.0), coefficient_k=1.0, exponent_m=0.8, time_step_hours=0.5)
    long = route_reach((0.0, 5.0, *later), coefficient_k=1.0, exponent_m=0.8, time_step_hours=0.5)
    assert long[:2] == short
    assert long[1] == pytest.approx(1.0, abs=1e-11)


def test_nonlinear_printed_balance_rejects_unsupported_parameters() -> None:
    with pytest.raises(RoutingDomainError, match="exponent"):
        audit_printed_nonlinear_balance(
            (0.0, 5.0),
            ("0.0000", "5.0000"),
            ("0.0000", "1.0000"),
            coefficient_k=1.0,
            exponent_m=0.0,
            dt_hours=0.5,
        )
    with pytest.raises(ValueError, match="Prescribed inflow"):
        audit_printed_nonlinear_balance(
            (0.0, 5.0),
            ("0.0000", "4.9990"),
            ("0.0000", "1.0000"),
            coefficient_k=1.0,
            exponent_m=0.8,
            dt_hours=0.5,
        )
