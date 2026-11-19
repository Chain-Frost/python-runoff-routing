"""Ordered source membership geometry and odd/even p53 weighted-distance rule."""

from dataclasses import dataclass
from fractions import Fraction

from .models import Event
from .precision import UnsupportedNumericPath, add53, div53, fraction, mul53, store_rational


@dataclass(frozen=True, slots=True)
class ReachGeometry:
    """Coefficient values for a reach in original encounter order."""

    reach_id: int
    length_km: float
    relative_delay: float
    coefficient: float
    coefficient_seconds: float


@dataclass(frozen=True, slots=True)
class Geometry:
    """Whole-event mean and reach coefficients from stored input geometry."""

    distances: tuple[float, ...]
    total_area: float
    weighted_total: float
    mean_distance: float
    reaches: tuple[ReachGeometry, ...]


def _source_distances(event: Event) -> tuple[list[float], list[float]]:
    """Compute C11-C13 geometry without changing the control evaluation order."""
    distances = [0.0] * event.source_count
    active: set[int] | None = None
    branches: list[set[int]] = []
    reach_lengths: list[float] = []
    source = 0
    for control in event.controls:
        code = control.code
        if code == 2 and active is None:
            message = "code-2 source needs an existing running hydrograph"
            raise UnsupportedNumericPath(message)
        if code in (1, 2):
            if active is None:
                active = set()
            active.add(source)
            source += 1
        elif code == 3:
            active = _active_sources(active)
            branches.append(active.copy())
            active = None
        elif code == 4:
            active = _active_sources(active)
            active.update(branches.pop())
        if code in (1, 2, 5):
            active = _active_sources(active)
            length = control.length.stored
            reach_lengths.append(length)
            for index in sorted(active):
                distances[index] = store_rational(add53(fraction(distances[index]), fraction(length)))
    return distances, reach_lengths


def compute_geometry(event: Event) -> Geometry:  # noqa: C901 -- bounded zero terminal copy guard
    """Compute stored coefficients in the original arithmetic order."""
    distances, reach_lengths = _source_distances(event)
    if not all(x > 0 for x in distances):
        message = "nonpositive source-to-outlet distance"
        raise UnsupportedNumericPath(message)
    area_total = 0.0
    for area in event.areas:
        area_total = store_rational(add53(fraction(area_total), fraction(area.stored)))
    if area_total <= 0:
        message = "nonpositive total area after store"
        raise UnsupportedNumericPath(message)
    even = event.source_count - (event.source_count % 2)
    weighted = Fraction()
    for index in range(even):
        weighted = add53(weighted, mul53(fraction(event.areas[index].stored), fraction(distances[index])))
    weighted_store = store_rational(weighted)
    if even < event.source_count:
        last_product = mul53(fraction(event.areas[-1].stored), fraction(distances[-1]))
        weighted_store = store_rational(add53(fraction(weighted_store), last_product))
    mean = store_rational(div53(fraction(weighted_store), fraction(area_total)))
    if mean <= 0:
        message = "nonpositive stored mean source distance"
        raise UnsupportedNumericPath(message)
    inverse = div53(Fraction(1), fraction(mean))
    reaches: list[ReachGeometry] = []
    for reach_id, length in enumerate(reach_lengths, 1):
        relative = store_rational(mul53(fraction(length), inverse))
        coefficient = store_rational(mul53(fraction(event.kc.stored), fraction(relative)))
        seconds = store_rational(mul53(fraction(coefficient), Fraction(3600)))
        if length == 0.0:
            if relative != 0.0 or coefficient != 0.0 or seconds != 0.0:
                message = f"reach {reach_id}: zero-length coefficient mismatch"
                raise UnsupportedNumericPath(message)
        elif min(relative, coefficient, seconds) <= 0:
            message = f"reach {reach_id}: positive coefficient underflow"
            raise UnsupportedNumericPath(message)
        reaches.append(ReachGeometry(reach_id, length, relative, coefficient, seconds))
    return Geometry(tuple(distances), area_total, weighted_store, mean, tuple(reaches))


def _active_sources(active: set[int] | None) -> set[int]:
    if active is None:
        message = "geometry requires an active source branch"
        raise UnsupportedNumericPath(message)
    return active
