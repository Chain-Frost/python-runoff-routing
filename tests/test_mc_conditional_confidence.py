"""Independent exact finite-distribution checks of the candidate reference method."""

from __future__ import annotations

import importlib.util
from decimal import localcontext
from fractions import Fraction
from pathlib import Path
from types import ModuleType

import pytest


def _research() -> ModuleType:
    path = Path(__file__).parents[1] / "repo-scripts" / "mc_conditional_confidence.py"
    spec = importlib.util.spec_from_file_location("mc_conditional_confidence", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _distribution(weights: tuple[int, ...], probabilities: tuple[int, ...]) -> dict[int, Fraction]:
    """Enumerate all weighted Bernoulli outcomes by exact convolution."""
    states = {0: Fraction(1)}
    for weight, numerator in zip(weights, probabilities, strict=True):
        p = Fraction(numerator, 100)
        updated: dict[int, Fraction] = {}
        for total, mass in states.items():
            updated[total] = updated.get(total, Fraction(0)) + mass * (1 - p)
            shifted = total + weight
            updated[shifted] = updated.get(shifted, Fraction(0)) + mass * p
        states = updated
    return states


@pytest.mark.parametrize(
    "probabilities", [(1, 2, 3, 4), (5, 40, 70, 95), (96, 97, 98, 99), (0, 0, 0, 0), (100, 100, 100, 100)]
)
def test_exact_heterogeneous_weighted_reference_coverage(probabilities: tuple[int, ...]) -> None:
    mc = _research()
    weights = (1, 2, 3, 4)
    total_weight = sum(weights)
    alpha = Fraction(1, 50)
    design = mc.reference_design([(Fraction(w, total_weight), 1) for w in weights], grid_points=1, alpha=alpha)
    mean = sum((Fraction(w * p, 100 * total_weight) for w, p in zip(weights, probabilities, strict=True)), Fraction(0))
    states = _distribution(weights, probabilities)
    assert sum(states.values()) == 1
    noncoverage = Fraction(0)
    for value, mass in states.items():
        observed = Fraction(value, total_weight)
        lower, upper = mc.reference_interval(design, observed, observed)
        # Deliberately outcome-dependent censoring: enclose a high or low result.
        coarsened = (
            (max(Fraction(0), observed - Fraction(1, 5)), observed)
            if observed >= mean
            else (observed, min(Fraction(1), observed + Fraction(1, 5)))
        )
        c_lower, c_upper = mc.reference_interval(design, *coarsened)
        assert 0 <= c_lower <= lower <= upper <= c_upper <= 1
        if not lower <= mean <= upper:
            noncoverage += mass
    assert noncoverage <= alpha


def test_rare_tail_narrower_at_fixed_family_and_weights() -> None:
    mc = _research()
    strata = [(Fraction(1, 50), 10000)] * 50
    with localcontext() as context:
        context.prec = 3
        design = mc.reference_design(strata, grid_points=256, alpha=Fraction(1, 50))
        lower, upper = mc.reference_interval(design, Fraction(99, 100), Fraction(99, 100))
    assert design.squared_weights == Fraction(1, 500000)
    assert design.max_weight == Fraction(1, 500000)
    assert lower < Fraction(99, 100) < upper
    assert upper - lower < Fraction(2, 1000)
    assert mc.reference_interval(design, Fraction(0), Fraction(1)) == (0, 1)
    assert mc.reference_interval(design, Fraction(0), Fraction(0))[0] == 0
    assert mc.reference_interval(design, Fraction(1), Fraction(1))[1] == 1


def test_invalid_design_or_observation_rejected() -> None:
    mc = _research()
    with pytest.raises(ValueError, match="sum exactly"):
        mc.reference_design([(Fraction(1, 2), 2)], grid_points=1, alpha=Fraction(1, 50))
    with pytest.raises(ValueError, match="Positive conditional"):
        mc.reference_design([(Fraction(1), 0)], grid_points=1, alpha=Fraction(1, 50))
    design = mc.reference_design([(Fraction(1), 10)], grid_points=1, alpha=Fraction(1, 50))
    with pytest.raises(ValueError, match="Invalid observed"):
        mc.reference_interval(design, Fraction(3, 4), Fraction(1, 4))
    with pytest.raises(ValueError, match="reference alpha"):
        mc.reference_design([(Fraction(1), 10)], grid_points=1, alpha=0.02)
    with pytest.raises(ValueError, match="Positive conditional"):
        mc.reference_design([(1.0, 10)], grid_points=1, alpha=Fraction(1, 50))
    with pytest.raises(ValueError, match="exact fractions"):
        mc.reference_interval(design, 0.0, Fraction(1))
    with pytest.raises(ValueError, match="exact fractions"):
        mc.reference_interval(design, Fraction(0), 1.0)


def test_finite_grid_inversion_zero_atom_tie_and_unbounded_tail() -> None:
    mc = _research()
    grid = (
        (Fraction(0), Fraction(95, 100), Fraction(95, 100)),
        (Fraction(1), Fraction(98, 100), Fraction(99, 100)),
        (Fraction(2), Fraction(98, 100), Fraction(1)),
    )
    assert mc.reference_quantile(grid, Fraction(5, 100)) == (0, 0)
    assert mc.reference_quantile(grid, Fraction(2, 100)) == (0, 1)
    assert mc.reference_quantile(grid, Fraction(1, 100)) == (0, None)
    exact = (*grid[:2], (Fraction(2), Fraction(99, 100), Fraction(1)))
    assert mc.reference_quantile(exact, Fraction(1, 100)) == (0, 2)


def test_monotone_tightening_and_inconsistent_grid() -> None:
    mc = _research()
    grid = (
        (Fraction(0), Fraction(1, 2), Fraction(3, 4)),
        (Fraction(1), Fraction(1, 4), Fraction(1, 2)),
    )
    assert mc.reference_quantile(grid, Fraction(1, 2)) == (0, 0)
    with pytest.raises(ValueError, match="Inconsistent"):
        mc.reference_quantile((grid[0], (Fraction(1), Fraction(1, 4), Fraction(2, 5))), Fraction(1, 2))


def test_exact_reference_quantile_query_and_grid_required() -> None:
    mc = _research()
    near = Fraction(99, 100) - Fraction(1, 10**20)
    grid = ((Fraction(0), near, near), (Fraction(1), Fraction(1), Fraction(1)))
    assert mc.reference_quantile(grid, Fraction(1, 100)) == (0, 1)
    # A binary64 target can make an exact CDF below 0.99 appear to cross.
    with pytest.raises(ValueError, match="exact fraction"):
        mc.reference_quantile(grid, 0.01)
    for invalid in (
        ((0.0, near, near),),
        ((Fraction(0), float(near), near),),
        ((Fraction(0), near, float(near)),),
    ):
        with pytest.raises(ValueError, match="exact fractions"):
            mc.reference_quantile(invalid, Fraction(1, 100))
