"""Experimental RORBwin 6.52 full-increment continuing-loss candidate.

Controlled native observations support the crossing rule for a bounded pervious
IL/CL profile. Decimal arithmetic here is a readable semantic candidate, not a
claim of native floating-point, CSV precision, timing or universal equivalence.
The existing ARR loss method does not select this profile automatically.
"""

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Literal

RORBWIN_652_LOSS_PROFILE = "rorbwin_6_52_full_increment_cl_experimental_v1"


@dataclass(frozen=True, slots=True)
class RORBwin652Excess:
    """Per-step loss accounting under the explicitly selected candidate rule."""

    timestep_min: int
    initial_loss_mm: Decimal
    continuing_loss_mm_per_hour: Decimal
    rainfall_increments_mm: tuple[Decimal, ...]
    initial_loss_increments_mm: tuple[Decimal, ...]
    continuing_loss_increments_mm: tuple[Decimal, ...]
    excess_increments_mm: tuple[Decimal, ...]
    profile_id: Literal["rorbwin_6_52_full_increment_cl_experimental_v1"] = field(
        default=RORBWIN_652_LOSS_PROFILE, init=False
    )
    native_parity: Literal["not_accepted"] = field(default="not_accepted", init=False)


def calculate_rorbwin_652_excess(
    rainfall_increments_mm: tuple[Decimal, ...],
    *,
    timestep_min: int,
    initial_loss_mm: Decimal,
    continuing_loss_mm_per_hour: Decimal,
) -> RORBwin652Excess:
    """Consume IL first, then cap a full timestep's CL by remaining rainfall.

    Dry steps neither consume losses nor reset IL. A step that exhausts IL
    receives the full CL capacity, without prorating for the IL-consuming
    fraction. Inputs are already effective rainfall depths in computational
    order; this function applies no ARF, preburst, rounding or time-label shift.
    """
    if isinstance(timestep_min, bool) or timestep_min <= 0:
        msg = "Candidate loss calculation requires a positive whole-minute timestep"
        raise ValueError(msg)
    if not rainfall_increments_mm:
        msg = "Candidate loss calculation requires rainfall increments"
        raise ValueError(msg)
    values = (*rainfall_increments_mm, initial_loss_mm, continuing_loss_mm_per_hour)
    if any(not value.is_finite() or value < 0 for value in values):
        msg = "Candidate rainfall and loss values must be finite and nonnegative"
        raise ValueError(msg)

    remaining_initial = initial_loss_mm
    continuing_capacity = continuing_loss_mm_per_hour * Decimal(timestep_min) / 60
    initial_losses: list[Decimal] = []
    continuing_losses: list[Decimal] = []
    excess: list[Decimal] = []
    for rainfall in rainfall_increments_mm:
        initial = min(remaining_initial, rainfall)
        remaining_initial -= initial
        after_initial = rainfall - initial
        continuing = min(after_initial, continuing_capacity)
        initial_losses.append(initial)
        continuing_losses.append(continuing)
        excess.append(after_initial - continuing)

    return RORBwin652Excess(
        timestep_min=timestep_min,
        initial_loss_mm=initial_loss_mm,
        continuing_loss_mm_per_hour=continuing_loss_mm_per_hour,
        rainfall_increments_mm=rainfall_increments_mm,
        initial_loss_increments_mm=tuple(initial_losses),
        continuing_loss_increments_mm=tuple(continuing_losses),
        excess_increments_mm=tuple(excess),
    )
