"""Synthetic tests of separate native and physical reporting statistics."""

from decimal import Decimal

import pytest

from runoff_routing.native_reporting import review_volume_conventions


def test_full_weight_sum_differs_from_physical_trapezoid() -> None:
    review = review_volume_conventions(
        ("2.0000",) * 21,
        timestep_hours="0.5",
        profile_id="CMD-6.44-example",
        reported_volume_text="75600",
        raw_native_time_tokens=tuple(f"{(index + 1) / 2:.2f}" for index in range(21)),
    )
    assert review.native_inclusive_sum_candidate_m3 == Decimal(75600)
    assert review.physical_horizon_trapezoid_m3 == Decimal(72000)
    assert review.extra_endpoint_weight_m3 == Decimal(3600)
    assert review.native_sum_consistent_with_report is True
    assert review.physical_integral_consistent_with_report is False
    assert review.sample_index_elapsed_hours[0] == 0
    assert review.sample_index_elapsed_hours[-1] == 10
    assert review.raw_native_time_tokens is not None
    assert review.raw_native_time_tokens[0] == "0.50"


def test_native_time_tokens_remain_untouched_across_profiles() -> None:
    cmd = review_volume_conventions(
        ("0.0000", "1.0000", "2.0000"),
        timestep_hours="0.5",
        profile_id="RORB_CMD-6.44",
        raw_native_time_tokens=("0.50", "1.00", "1.50"),
    )
    gui = review_volume_conventions(
        ("0.0000", "1.0000", "2.0000"),
        timestep_hours="0.5",
        profile_id="RORBwin-6.52",
        raw_native_time_tokens=("0.00", "0.50", "1.00"),
    )
    assert cmd.sample_index_elapsed_hours == gui.sample_index_elapsed_hours
    assert cmd.raw_native_time_tokens != gui.raw_native_time_tokens
    assert cmd.native_inclusive_sum_candidate_m3 == gui.native_inclusive_sum_candidate_m3
    assert cmd.native_reported_volume_m3 is None
    assert cmd.native_sum_consistent_with_report is None


def test_scientific_printed_precision_is_not_an_exact_scalar_assertion() -> None:
    review = review_volume_conventions(
        ("2.0000",) * 21,
        timestep_hours="0.5",
        profile_id="RORB-CMD-v6.44-pinned-build",
        reported_volume_text="7.56E+04",
    )
    assert review.native_report_printing_bound_m3 == 50
    assert review.native_sum_consistent_with_report is True
    assert review.physical_integral_consistent_with_report is False


def test_all_zero_hydrograph_keeps_both_volumes_zero() -> None:
    review = review_volume_conventions(
        ("0", "0", "0"), timestep_hours="1.0", profile_id="test", reported_volume_text="0"
    )
    assert review.native_inclusive_sum_candidate_m3 == 0
    assert review.physical_horizon_trapezoid_m3 == 0
    assert review.native_sum_consistent_with_report is True
    assert review.physical_integral_consistent_with_report is True


@pytest.mark.parametrize(
    ("values", "dt", "profile", "times", "error"),
    [
        (("1",), "0.5", "build", None, "At least two"),
        (("1", "2"), "0", "build", None, "strictly positive"),
        (("1", "2"), "NaN", "build", None, "Timestep"),
        (("1", "2"), "Infinity", "build", None, "Timestep"),
        (("1", "-2"), "0.5", "build", None, "Discharge"),
        (("1", "nan"), "0.5", "build", None, "Discharge"),
        (("1", "2"), "0.5", "", None, "profile"),
        (("1", "2"), "0.5", "build", ("0.5",), "time-token"),
    ],
)
def test_invalid_inputs_fail_closed(
    values: tuple[str, ...], dt: str, profile: str, times: tuple[str, ...] | None, error: str
) -> None:
    with pytest.raises(ValueError, match=error):
        review_volume_conventions(values, timestep_hours=dt, profile_id=profile, raw_native_time_tokens=times)
