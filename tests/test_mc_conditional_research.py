"""Deterministic research-only controls; no routing or Monte Carlo execution."""

from __future__ import annotations

import importlib.util
from collections.abc import Iterator
from decimal import Decimal, localcontext
from fractions import Fraction
from pathlib import Path
from types import ModuleType

import pytest


def _research() -> ModuleType:
    path = Path(__file__).parents[1] / "repo-scripts" / "mc_conditional_research.py"
    spec = importlib.util.spec_from_file_location("mc_conditional_research", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _row(sample: str, stratum: str, peak: object, *, status: str = "computed_unvalidated") -> dict[str, object]:
    return {
        "sample_id": sample,
        "stratum_id": stratum,
        "scenario_id": "study",
        "duration_min": 1440,
        "status": status,
        "probability_weight": "0.0000001",  # Deliberately not the exact plan weight.
        "sites": [{"print_id": "P01", "peak_m3_s": peak}, {"print_id": "P02", "peak_m3_s": 99}],
    }


def _plan() -> dict[str, tuple[Decimal, int]]:
    return {"a": (Decimal("0.20"), 2), "b": (Decimal("0.29"), 2)}


def _rows() -> list[dict[str, object]]:
    return [_row("a1", "a", 0), _row("a2", "a", 20), _row("b1", "b", 10), _row("b2", "b", 10)]


def test_exact_unequal_weights_ties_and_strict_survival() -> None:
    mc = _research()
    curve = mc.conditional_curve(_plan(), _rows(), scenario="study", duration=1440, site_id="P01")
    assert curve.cdf(Fraction(0)) == (Fraction(100, 490),) * 2
    assert curve.cdf(Fraction(10)) == (Fraction(390, 490),) * 2
    assert curve.survival(Fraction(10)) == (Fraction(100, 490),) * 2
    assert curve.quantile(Fraction(1, 2)) == (10, 10)
    assert curve.quantile(Fraction(1, 100)) == (20, 20)
    assert curve.unknown_mass == 0
    assert curve.status_counts == {"valid": 4, "unrecorded": 0}


def test_missing_and_failed_draws_keep_original_denominator() -> None:
    mc = _research()
    rows = _rows()[:-1]
    curve = mc.conditional_curve(_plan(), rows, scenario="study", duration=1440, site_id="P01")
    assert curve.cdf(Fraction(0)) == (Fraction(100, 490), Fraction(245, 490))
    assert curve.cdf(Fraction(10)) == (Fraction(245, 490), Fraction(390, 490))
    assert curve.quantile(Fraction(1, 2)) == (0, 10)
    assert curve.quantile(Fraction(1, 100)) == (20, None)
    assert curve.status_counts == {"valid": 3, "unrecorded": 1}
    rows.append(_row("b2", "b", 0, status="numerical_error"))
    failed = mc.conditional_curve(_plan(), rows, scenario="study", duration=1440, site_id="P01")
    assert failed.known == curve.known
    assert failed.unknown_mass == Fraction(145, 1000)
    assert failed.status_counts == {"valid": 3, "numerical_error": 1, "unrecorded": 0}


def test_wholly_unstarted_not_zero() -> None:
    mc = _research()
    curve = mc.conditional_curve(_plan(), [], scenario="study", duration=1440, site_id="P01")
    assert curve.cdf(Fraction(0)) == (0, 1)
    assert curve.quantile(Fraction(1, 100)) == (0, None)
    assert curve.unknown_mass == Fraction(49, 100)
    assert curve.status_counts == {"unrecorded": 4}


def test_exact_decimal_boundary_not_float_roundtrip() -> None:
    mc = _research()
    plan = {"a": (Decimal("0.48509999999999999999"), 1), "b": (Decimal("0.00490000000000000001"), 1)}
    with localcontext() as context:
        context.prec = 3
        curve = mc.conditional_curve(
            plan, [_row("a1", "a", 0), _row("b1", "b", 1)], scenario="study", duration=1440, site_id="P01"
        )
    assert curve.quantile(Fraction(1, 100)) == (1, 1)
    assert float(plan["a"][0]) == 0.4851


@pytest.mark.parametrize("peak", [True, -1, float("inf"), float("nan"), "10", None])
def test_invalid_computed_peaks_rejected(peak: object) -> None:
    mc = _research()
    with pytest.raises(ValueError, match="site peak"):
        mc.conditional_curve(_plan(), [_row("a1", "a", peak)], scenario="study", duration=1440, site_id="P01")


def test_duplicate_unknown_and_overallocated_rows_rejected() -> None:
    mc = _research()
    for rows, reason in (
        ([_row("a1", "a", 0), _row("a1", "b", 0)], "Duplicate sample"),
        ([_row("x", "x", 0)], "undeclared stratum"),
        ([_row(str(i), "a", 0) for i in range(3)], "exceed planned"),
    ):
        with pytest.raises(ValueError, match=reason):
            mc.conditional_curve(_plan(), rows, scenario="study", duration=1440, site_id="P01")


def test_mixed_scope_and_duplicate_sites_rejected() -> None:
    mc = _research()
    row = _row("a1", "a", 0)
    row["duration_min"] = 60
    with pytest.raises(ValueError, match="Mixed scenario"):
        mc.conditional_curve(_plan(), [row], scenario="study", duration=1440, site_id="P01")
    row["duration_min"] = 1440
    row["sites"] = [{"print_id": "P01", "peak_m3_s": 1}] * 2
    with pytest.raises(ValueError, match="Ambiguous computed site"):
        mc.conditional_curve(_plan(), [row], scenario="study", duration=1440, site_id="P01")


def test_positive_allocations_and_exact_support_required() -> None:
    mc = _research()
    for plan, reason in (
        ({"a": (Decimal("0.49"), 0)}, "positive planned"),
        ({"a": (Decimal("0.50"), 1)}, "mass 0.49"),
    ):
        with pytest.raises(ValueError, match=reason):
            mc.conditional_curve(plan, [], scenario="study", duration=1440, site_id="P01")


def test_reader_exhausted_before_result_return() -> None:
    mc = _research()

    def invalid_at_end() -> Iterator[dict[str, object]]:
        yield _row("a1", "a", 0)
        message = "final digest mismatch"
        raise ValueError(message)

    with pytest.raises(ValueError, match="final digest mismatch"):
        mc.conditional_curve(_plan(), invalid_at_end(), scenario="study", duration=1440, site_id="P01")


def test_exact_conditional_queries_reject_float() -> None:
    mc = _research()
    plan = {"a": (Decimal("0.48509999999999999999"), 1), "b": (Decimal("0.00490000000000000001"), 1)}
    curve = mc.conditional_curve(
        plan, [_row("a1", "a", 0), _row("b1", "b", 1)], scenario="study", duration=1440, site_id="P01"
    )
    assert curve.quantile(Fraction(1, 100)) == (1, 1)
    with pytest.raises(ValueError, match="exact fraction"):
        curve.quantile(0.01)
    for threshold in (0.0, float("nan"), float("inf")):
        with pytest.raises(ValueError, match="exact fraction"):
            curve.cdf(threshold)
        with pytest.raises(ValueError, match="exact fraction"):
            curve.survival(threshold)
