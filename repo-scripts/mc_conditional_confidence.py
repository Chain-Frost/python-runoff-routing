"""Candidate #148 weighted reference intervals; no physical inference or execution."""

from __future__ import annotations

from collections.abc import Iterable
from decimal import ROUND_CEILING, ROUND_FLOOR, Context, Decimal, localcontext
from fractions import Fraction
from math import isqrt
from typing import NamedTuple, Never

_STEPS = 56
_SCALE = 1 << 60


class ReferenceDesign(NamedTuple):
    """Fixed-grid, split-alpha latent-indicator design; not an adopted method."""

    grid_points: int
    alpha: Fraction
    squared_weights: Fraction
    max_weight: Fraction
    hoeffding_radius: Fraction
    kl_limit: Fraction


def _fail(message: str) -> Never:
    raise ValueError(message)


def _require_fraction(value: object, message: str) -> Fraction:
    if not isinstance(value, Fraction):
        _fail(message)
    return value


def _log_bounds(value: Fraction) -> tuple[Fraction, Fraction]:
    """Directed ratio enclosure and correctly rounded Decimal logarithms.

    Decimal.ln is correctly rounded to nearest; one adjacent representable
    number on either side encloses the exact result. All subsequent arithmetic
    on the endpoints uses Fraction. Reject out-of-context ratios.
    """
    if value <= 0:
        _fail("Expected positive logarithm argument")
    if value == 1:
        return Fraction(0), Fraction(0)
    with localcontext(Context(prec=50, Emin=-256, Emax=256)) as context:
        numerator, denominator = Decimal(value.numerator), Decimal(value.denominator)
        context.rounding = ROUND_FLOOR
        low = context.divide(numerator, denominator)
        context.rounding = ROUND_CEILING
        high = context.divide(numerator, denominator)
        if not 0 < low <= high or not high.is_finite():
            _fail("Ratio outside supported logarithm context")
        lo = Decimal(0) if low == 1 else context.next_minus(context.ln(low))
        hi = Decimal(0) if high == 1 else context.next_plus(context.ln(high))
        return Fraction(lo), Fraction(hi)


def _sqrt_upper(value: Fraction) -> Fraction:
    """Ceiling on a fixed dyadic lattice using only integer arithmetic."""
    scaled = value * _SCALE**2
    root = isqrt(scaled.numerator // scaled.denominator)
    if root * root * scaled.denominator < scaled.numerator:
        root += 1
    return Fraction(root, _SCALE)


def reference_design(strata: Iterable[tuple[Fraction, int]], *, grid_points: int, alpha: Fraction) -> ReferenceDesign:
    """Known conditional stratum masses and full positive pooled counts.

    Half alpha is reserved for each simultaneous two-sided construction.
    Grid points count the complete fixed family across all sites. Cross-output
    dependence is allowed; independence is required for the latent draws.
    """
    alpha = _require_fraction(alpha, "Invalid fixed-grid family or reference alpha")
    if type(grid_points) is not int or not 1 <= grid_points <= 256 or not 0 < alpha < 1:
        _fail("Invalid fixed-grid family or reference alpha")
    total = Fraction(0)
    squared = Fraction(0)
    largest = Fraction(0)
    draws = 0
    for raw_mass, count in strata:
        mass = _require_fraction(raw_mass, "Positive conditional masses and planned counts required")
        if not 0 < mass <= 1 or type(count) is not int or count <= 0:
            _fail("Positive conditional masses and planned counts required")
        total += mass
        draws += count
        squared += mass * mass / count
        largest = max(largest, mass / count)
    if total != 1 or draws > 1_000_000:
        _fail("Reference masses must sum exactly to one within the draw cap")
    _, log_upper = _log_bounds(4 * grid_points / alpha)
    return ReferenceDesign(
        grid_points, alpha, squared, largest, _sqrt_upper(squared * log_upper / 2), largest * log_upper
    )


def _kl_lower(observed: Fraction, mean: Fraction) -> Fraction:
    """Lower enclosure of Bernoulli relative entropy at an interior mean."""
    total = Fraction(0)
    for x, p in ((observed, mean), (1 - observed, 1 - mean)):
        if x:
            lower, _ = _log_bounds(x / p)
            total += x * lower
    return total


def _kl_outer(observed: Fraction, limit: Fraction, *, upper: bool) -> Fraction:
    """Return an outward endpoint using only certified rejected trial means."""
    rejected = Fraction(1 if upper else 0)
    retained = observed
    for _ in range(_STEPS):
        middle = (rejected + retained) / 2
        if middle in (0, 1):
            break
        if _kl_lower(observed, middle) > limit:
            rejected = middle
        else:
            retained = middle
    return rejected


def reference_interval(
    design: ReferenceDesign, observed_lower: Fraction, observed_upper: Fraction
) -> tuple[Fraction, Fraction]:
    """Enclose the latent reference CDF using observed pathwise endpoint bounds.

    Unknown draws must retain full planned weight. This does not assume that
    the observed endpoints are independent, does not verify the latent law,
    and never authorises simulation. The KL limit and Hoeffding radius were
    rounded upward; the inverted endpoints are rounded outward.
    """
    observed_lower = _require_fraction(observed_lower, "Observed CDF endpoints must be exact fractions")
    observed_upper = _require_fraction(observed_upper, "Observed CDF endpoints must be exact fractions")
    if not 0 <= observed_lower <= observed_upper <= 1:
        _fail("Invalid observed CDF enclosure")
    return (
        max(
            Fraction(0),
            observed_lower - design.hoeffding_radius,
            _kl_outer(observed_lower, design.kl_limit, upper=False),
        ),
        min(
            Fraction(1),
            observed_upper + design.hoeffding_radius,
            _kl_outer(observed_upper, design.kl_limit, upper=True),
        ),
    )


def reference_quantile(
    grid: tuple[tuple[Fraction, Fraction, Fraction], ...], exceedance: Fraction
) -> tuple[Fraction, Fraction | None]:
    """Conservative inverse of simultaneous CDF bounds on a fixed finite grid.

    Each row is (flow, lower CDF, upper CDF). Apply monotone tightening;
    a finite grid cannot establish an upper inverse without a crossing.
    """
    exceedance = _require_fraction(exceedance, "Conditional exceedance must be an exact fraction")
    if not grid or not 0 < exceedance < 1:
        _fail("Expected nonempty grid and interior conditional exceedance")
    previous = Fraction(-1)
    lower = Fraction(0)
    lowers: list[Fraction] = []
    for flow, lo, hi in grid:
        _require_fraction(flow, "Reference grid values must be exact fractions")
        _require_fraction(lo, "Reference grid values must be exact fractions")
        _require_fraction(hi, "Reference grid values must be exact fractions")
        if flow < 0 or flow <= previous or not 0 <= lo <= hi <= 1:
            _fail("Invalid ordered reference grid")
        previous = flow
        lower = max(lower, lo)
        lowers.append(lower)
    upper = Fraction(1)
    uppers: list[Fraction] = []
    for _, _, hi in reversed(grid):
        upper = min(upper, hi)
        uppers.append(upper)
    uppers.reverse()
    if any(lo > hi for lo, hi in zip(lowers, uppers, strict=True)):
        _fail("Inconsistent simultaneous monotone reference bounds")
    target = 1 - exceedance
    lower_flow = max((flow for (flow, _, _), hi in zip(grid, uppers, strict=True) if hi < target), default=Fraction(0))
    upper_flow = next((flow for (flow, _, _), lo in zip(grid, lowers, strict=True) if lo >= target), None)
    return lower_flow, upper_flow
