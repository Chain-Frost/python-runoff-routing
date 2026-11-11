"""Compatibility-only S2 fixture API backed by the authoritative S1 grammar.

New callers should use :mod:`runoff_routing.integration` and typed RunModel.
No second .catg/.stm grammar is maintained here. Legacy text adapters reject
S1-unsupported formats rather than interpreting or silently dropping fields.
"""

from __future__ import annotations

import math
from decimal import Decimal

from .rorb_codec import FormatProblem, parse_catg, parse_design_stm
from .single_storm import Catchment, Control, Storm


class LegacyInputError(ValueError):
    """A legacy fixture cannot be represented by the supported S1 dialect."""


def _float(value: Decimal) -> float:
    number = float(value)
    if not math.isfinite(number) or (value > 0 and number == 0):
        message = "A source number underflows or overflows at the S2 float boundary"
        raise LegacyInputError(message)
    return number


def parse_control_bytes(data: bytes) -> Catchment:
    """Adapt original verified source bytes using only the S1 .catg parser."""
    try:
        model = parse_catg(data).model
    except FormatProblem as exc:
        message = f"S1 {exc.status} catchment: {exc}"
        raise LegacyInputError(message) from exc
    lengths = {reach.identifier: _float(reach.length_km) for reach in model.reaches}
    controls = tuple(
        Control(step.code, lengths[step.reach_id] if step.reach_id is not None else 0.0) for step in model.controls
    )
    return Catchment(controls, tuple(_float(area.area_km2) for area in model.subareas))


def parse_control_vector(text: str) -> Catchment:
    """Historical text fixture interface; byte-based sources should avoid decoding."""
    return parse_control_bytes(text.encode("utf-8"))


def parse_explicit_design_storm_bytes(data: bytes) -> Storm:
    """Adapt original verified source bytes using only the S1 .stm parser."""
    try:
        model = parse_design_stm(data).model
    except FormatProblem as exc:
        message = f"S1 {exc.status} DESIGN storm: {exc}"
        raise LegacyInputError(message) from exc
    return Storm(
        _float(model.timestep_hours),
        model.calculation_increments,
        tuple(_float(value) for value in model.percentages),
        tuple(_float(value) for value in model.depths_mm),
    )


def parse_explicit_design_storm(text: str) -> Storm:
    """Historical text fixture interface; byte-based sources should avoid decoding."""
    return parse_explicit_design_storm_bytes(text.encode("utf-8"))
