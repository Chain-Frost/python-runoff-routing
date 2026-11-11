"""Independent, synthetic numeric-boundary tests; not RORB solver acceptance."""

from decimal import Decimal
from typing import cast

import pytest

from runoff_routing.numeric_boundary import NormalizationError, ValueConstraint, decimal_to_solver_float


@pytest.mark.parametrize(
    ("value", "constraint", "expected"),
    [
        (Decimal("1.25"), "positive", 1.25),
        (Decimal("0"), "nonnegative", 0.0),
        (Decimal("-0"), "nonnegative", 0.0),
        (Decimal("-2.5"), "any", -2.5),
        (Decimal("1e-300"), "positive", 1e-300),
    ],
)
def test_supported_finite_values(value: Decimal, constraint: ValueConstraint, expected: float) -> None:
    assert decimal_to_solver_float(value, field="storm.initial_loss", units="mm", constraint=constraint) == expected


@pytest.mark.parametrize("value", [Decimal("NaN"), Decimal("Infinity"), Decimal("-Infinity")])
def test_rejects_nonfinite_input(value: Decimal) -> None:
    with pytest.raises(NormalizationError, match=r"storm\.initial_loss \[mm\]: value must be finite"):
        decimal_to_solver_float(value, field="storm.initial_loss", units="mm")


@pytest.mark.parametrize("value", [Decimal("1e10000"), Decimal("-1e10000")])
def test_rejects_overflow(value: Decimal) -> None:
    with pytest.raises(NormalizationError, match="overflowed binary64"):
        decimal_to_solver_float(value, field="reach_length", units="km")


@pytest.mark.parametrize("value", [Decimal("1e-10000"), Decimal("-1e-10000")])
def test_rejects_underflow_to_zero(value: Decimal) -> None:
    with pytest.raises(NormalizationError, match="underflowed nonzero input"):
        decimal_to_solver_float(value, field="reach_length", units="km")


@pytest.mark.parametrize(
    ("value", "constraint"),
    [
        (Decimal("-0.1"), "nonnegative"),
        (Decimal("-0.1"), "positive"),
        (Decimal("0"), "positive"),
    ],
)
def test_rejects_out_of_domain(value: Decimal, constraint: ValueConstraint) -> None:
    with pytest.raises(NormalizationError, match=f"must be {constraint}"):
        decimal_to_solver_float(value, field="area", units="km2", constraint=constraint)


def test_rejects_untyped_values() -> None:
    with pytest.raises(TypeError, match="expected Decimal"):
        decimal_to_solver_float(cast("Decimal", 1.25), field="loss", units="mm")


@pytest.mark.parametrize(("field", "units"), [("", "mm"), ("loss", "")])
def test_requires_explicit_field_and_units(field: str, units: str) -> None:
    with pytest.raises(ValueError, match="Field name and expected units"):
        decimal_to_solver_float(Decimal(1), field=field, units=units)


def test_rejects_unknown_constraint() -> None:
    with pytest.raises(ValueError, match="Unknown numeric constraint"):
        decimal_to_solver_float(Decimal(1), field="loss", units="mm", constraint=cast("ValueConstraint", "unknown"))
