"""Unit-labelled, fail-closed Decimal-to-float conversion for future S1/S2 adapters.

This primitive does not parse RORB records, perform unit conversion, or declare
any input computationally supported. An eventual RunModel adapter must select
and validate each field's units and execution capability before calling S2.
"""

import math
from decimal import Decimal
from typing import Literal

type ValueConstraint = Literal["any", "nonnegative", "positive"]


class NormalizationError(ValueError):
    """An input Decimal cannot safely be supplied to a float-based solver."""


def decimal_to_solver_float(
    value: Decimal,
    *,
    field: str,
    units: str,
    constraint: ValueConstraint = "any",
) -> float:
    """Convert a finite Decimal without overflow, underflow-to-zero or hidden sign changes.

    Units are a required diagnostic annotation, *not* an implicit conversion.
    Finite representable values use ordinary IEEE-754 rounding; this does not
    establish equivalence to native RORB arithmetic. Integer flags and IDs
    must stay integral and must never pass through this function.
    """
    if not field.strip() or not units.strip():
        message = "Field name and expected units must be supplied."
        raise ValueError(message)
    if constraint not in {"any", "nonnegative", "positive"}:
        message = f"Unknown numeric constraint: {constraint!r}."
        raise ValueError(message)
    if not isinstance(value, Decimal):
        message = f"{field} [{units}]: expected Decimal, not {type(value).__name__}."
        raise TypeError(message)
    context = f"{field} [{units}]"
    if not value.is_finite():
        message = f"{context}: value must be finite."
        raise NormalizationError(message)
    if (constraint == "nonnegative" and value < 0) or (constraint == "positive" and value <= 0):
        message = f"{context}: value must be {constraint}."
        raise NormalizationError(message)
    result = float(value)
    if not math.isfinite(result):
        message = f"{context}: conversion overflowed binary64."
        raise NormalizationError(message)
    if value != 0 and result == 0:
        message = f"{context}: conversion underflowed nonzero input to zero."
        raise NormalizationError(message)
    return 0.0 if result == 0 else result
