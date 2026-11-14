"""Independent rectangular-storm expectations for an opt-in experimental rule."""

from dataclasses import FrozenInstanceError
from decimal import Decimal
from pathlib import Path

import pytest

from runoff_routing.arr_import import parse_arr_txt
from runoff_routing.arr_losses import calculate_burst_only_excess, select_legacy_preburst_loss
from runoff_routing.arr_storm import RawHyetograph
from runoff_routing.rorbwin_losses import RORBWIN_652_LOSS_PROFILE, calculate_rorbwin_652_excess

RAIN = tuple(Decimal(value) for value in (10, 10, 10, 0, 10, 0))


@pytest.mark.parametrize(
    ("initial", "continuing", "minutes", "expected"),
    [
        (19, 0, 60, (0, 1, 10, 0, 10, 0)),
        (20, 0, 60, (0, 0, 10, 0, 10, 0)),
        (21, 0, 60, (0, 0, 9, 0, 10, 0)),
        (19, 2, 60, (0, 0, 8, 0, 8, 0)),
        (20, 2, 60, (0, 0, 8, 0, 8, 0)),
        (21, 2, 60, (0, 0, 7, 0, 8, 0)),
        (19, 2, 30, (0, 0, 9, 0, 9, 0)),
    ],
)
def test_controlled_crossings_and_dry_gap(
    initial: int, continuing: int, minutes: int, expected: tuple[int, ...]
) -> None:
    result = calculate_rorbwin_652_excess(
        RAIN,
        timestep_min=minutes,
        initial_loss_mm=Decimal(initial),
        continuing_loss_mm_per_hour=Decimal(continuing),
    )
    assert result.excess_increments_mm == tuple(Decimal(value) for value in expected)
    assert result.profile_id == RORBWIN_652_LOSS_PROFILE
    assert result.native_parity == "not_accepted"
    assert sum(result.initial_loss_increments_mm) == initial
    for rain, il, cl, excess in zip(
        result.rainfall_increments_mm,
        result.initial_loss_increments_mm,
        result.continuing_loss_increments_mm,
        result.excess_increments_mm,
        strict=True,
    ):
        assert rain == il + cl + excess
        assert il >= 0
        assert cl >= 0
        assert excess >= 0
    assert result.initial_loss_increments_mm[3] == result.continuing_loss_increments_mm[3] == 0


def test_existing_arr_loss_method_remains_partial_timestep() -> None:
    fixture = Path(__file__).absolute().parent / "fixtures" / "arr" / "2016-era-synthetic.txt"
    document = parse_arr_txt(fixture.read_bytes(), legacy_profile="arr2016")
    selection = select_legacy_preburst_loss(document, duration_min=60, aep_percent=Decimal(1))
    event = RawHyetograph(
        duration_min=60,
        timestep_min=30,
        pattern_event_id="synthetic-crossing",
        pattern_region="Synthetic only",
        pattern_aep_band="rare",
        pattern_area_bin=None,
        source_label="BoM 2016 IFD (raw gross rainfall)",
        source_sha256="synthetic-source",
        pattern_source_sha256="synthetic-pattern",
        probability_label="1%",
        source_rainfall_depth_mm=Decimal(100),
        increments_mm=(Decimal(10), Decimal(90)),
        end_times_min=(30, 60),
        total_mm=Decimal(100),
        operations=("SYNTHETIC_TEST_ONLY",),
    )
    reference = calculate_burst_only_excess(event, selection)
    candidate = calculate_rorbwin_652_excess(
        event.increments_mm,
        timestep_min=30,
        initial_loss_mm=Decimal(14),
        continuing_loss_mm_per_hour=Decimal(2),
    )
    assert candidate.excess_increments_mm == (Decimal(0), Decimal(85))
    assert reference.excess_increments_mm[1] > candidate.excess_increments_mm[1]
    assert "SEQUENTIAL_IL_THEN_CL_WITHIN_STEP_CONSTANT_RAIN_RATE" in reference.operations


@pytest.mark.parametrize("initial", ["-1", "NaN", "Infinity"])
def test_invalid_initial_loss_rejects(initial: str) -> None:
    with pytest.raises(ValueError, match="finite and nonnegative"):
        calculate_rorbwin_652_excess(
            RAIN, timestep_min=60, initial_loss_mm=Decimal(initial), continuing_loss_mm_per_hour=Decimal(2)
        )


@pytest.mark.parametrize("rain", [(), (Decimal(-1),), (Decimal("NaN"),)])
def test_empty_or_invalid_rainfall_rejects(rain: tuple[Decimal, ...]) -> None:
    with pytest.raises(ValueError, match=r"rainfall increments|finite and nonnegative"):
        calculate_rorbwin_652_excess(
            rain, timestep_min=60, initial_loss_mm=Decimal(0), continuing_loss_mm_per_hour=Decimal(2)
        )


@pytest.mark.parametrize("minutes", [0, -1, True])
def test_invalid_timestep_rejects(minutes: int) -> None:
    with pytest.raises(ValueError, match="whole-minute timestep"):
        calculate_rorbwin_652_excess(
            RAIN, timestep_min=minutes, initial_loss_mm=Decimal(0), continuing_loss_mm_per_hour=Decimal(2)
        )


def test_result_is_immutable() -> None:
    result = calculate_rorbwin_652_excess(
        RAIN, timestep_min=60, initial_loss_mm=Decimal(100), continuing_loss_mm_per_hour=Decimal(2)
    )
    assert result.excess_increments_mm == (Decimal(0),) * 6
    assert sum(result.initial_loss_increments_mm) == 40
    assert sum(result.continuing_loss_increments_mm) == 0
    field_name = "profile_id"
    with pytest.raises(FrozenInstanceError):
        setattr(result, field_name, "other")


@pytest.mark.parametrize("continuing", ["-1", "NaN", "Infinity"])
def test_invalid_continuing_loss_rejects(continuing: str) -> None:
    with pytest.raises(ValueError, match="finite and nonnegative"):
        calculate_rorbwin_652_excess(
            RAIN, timestep_min=60, initial_loss_mm=Decimal(0), continuing_loss_mm_per_hour=Decimal(continuing)
        )
