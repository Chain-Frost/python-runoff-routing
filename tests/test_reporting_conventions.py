"""Pure reporting-convention checks, independent of RORB engine execution."""

from __future__ import annotations

from decimal import Decimal

import pytest

from runoff_routing.reporting_conventions import audit_volume_conventions


def test_native_inclusive_sample_sum_differs_from_physical_horizon() -> None:
    result = audit_volume_conventions(
        ["2.0000"] * 21, timestep_hours=Decimal("0.5"), native_reported_volume_token="7.56E+04"
    )
    assert result.sample_count == 21
    assert result.inclusive_sample_sum_m3 == Decimal("75600")
    assert result.physical_trapezoid_m3 == Decimal("72000")
    assert result.endpoint_weight_difference_m3 == Decimal("3600")
    assert result.sample_sum_printing_bound_m3 == Decimal("1.89")
    assert result.trapezoid_printing_bound_m3 == Decimal("1.8")
    assert result.reported_native_half_unit_m3 == Decimal("50")
    assert result.sample_sum_consistent_with_report is True
    assert result.trapezoid_consistent_with_report is False
    assert result.sample_index_centroid_hours == Decimal("5.0")


@pytest.mark.parametrize(
    ("dt", "count", "expected_sum"),
    [
        ("0.5", 21, "75600"),
        ("0.25", 41, "73800"),
        ("0.125", 81, "72900"),
    ],
)
def test_native_volume_candidate_counts_all_samples(dt: str, count: int, expected_sum: str) -> None:
    result = audit_volume_conventions(["2.0000"] * count, timestep_hours=Decimal(dt))
    assert result.inclusive_sample_sum_m3 == Decimal(expected_sum)
    assert result.physical_trapezoid_m3 == Decimal("72000")
    assert result.endpoint_weight_difference_m3 == Decimal(expected_sum) - Decimal("72000")
    assert result.sample_sum_consistent_with_report is None
    assert result.trapezoid_consistent_with_report is None


def test_manufactured_single_step_separates_summary_from_balance() -> None:
    audit = audit_volume_conventions(
        ["0.0000", "1.0001"], timestep_hours=Decimal("0.5"), native_reported_volume_token="1.80E+03"
    )
    assert audit.inclusive_sample_sum_m3 == Decimal("1800.18")
    assert audit.physical_trapezoid_m3 == Decimal("900.09")
    assert audit.endpoint_weight_difference_m3 == Decimal("900.09")
    assert audit.sample_sum_printing_bound_m3 == Decimal("0.18")
    assert audit.trapezoid_printing_bound_m3 == Decimal("0.09")
    assert audit.reported_native_half_unit_m3 == Decimal("5")
    assert audit.sample_sum_consistent_with_report is True
    assert audit.trapezoid_consistent_with_report is False


def test_native_raw_times_are_preserved_without_shift() -> None:
    result = audit_volume_conventions(
        ["0.0000", "1.0000", "0.0000"],
        timestep_hours=Decimal("0.5"),
        raw_native_time_tokens=["0.50", "1.00", "1.50"],
    )
    assert result.raw_native_time_tokens == ("0.50", "1.00", "1.50")
    assert result.sample_index_elapsed_hours == (Decimal(0), Decimal("0.5"), Decimal("1.0"))
    assert result.sample_index_centroid_hours == Decimal("0.5")


def test_zero_discharge_has_no_centroid_and_is_not_a_reported_parity_pass() -> None:
    result = audit_volume_conventions(
        ["0.0000", "0.0000"],
        timestep_hours=Decimal("0.5"),
        native_reported_volume_token="0.00",
    )
    assert result.inclusive_sample_sum_m3 == result.physical_trapezoid_m3 == Decimal(0)
    assert result.sample_index_centroid_hours is None
    assert result.sample_sum_consistent_with_report is True
    assert result.trapezoid_consistent_with_report is True


def test_one_sample_is_a_zero_duration_physical_horizon() -> None:
    result = audit_volume_conventions(["2.0000"], timestep_hours=Decimal("0.5"))
    assert result.inclusive_sample_sum_m3 == Decimal("3600")
    assert result.physical_trapezoid_m3 == Decimal(0)
    assert result.endpoint_weight_difference_m3 == Decimal("3600")
    assert result.trapezoid_printing_bound_m3 == Decimal(0)
    assert result.sample_index_centroid_hours == Decimal(0)


@pytest.mark.parametrize(
    "token",
    ["", " ", " 1.0", "1.0 ", "NaN", "Infinity", "-Inf", "-0.01", "word", "1_0", "1,234", "1D0"],
)
def test_invalid_native_discharge_tokens_fail_closed(token: str) -> None:
    with pytest.raises(ValueError, match="Discharge sample"):
        audit_volume_conventions([token], timestep_hours=Decimal("0.5"))


@pytest.mark.parametrize("timestep", [Decimal(0), Decimal(-1), Decimal("NaN"), Decimal("Infinity"), Decimal("-Infinity")])
def test_invalid_timestep_fails_closed(timestep: Decimal) -> None:
    with pytest.raises(ValueError, match="Timestep"):
        audit_volume_conventions(["0.0000"], timestep_hours=timestep)


def test_ambiguous_reported_precision_is_not_forced_to_one_convention() -> None:
    result = audit_volume_conventions(
        ["0.0000", "0.0000"], timestep_hours=Decimal("0.5"), native_reported_volume_token="0"
    )
    assert result.sample_sum_consistent_with_report is True
    assert result.trapezoid_consistent_with_report is True


@pytest.mark.parametrize("native", ["-1", "NaN", "abc", ""])
def test_bad_native_summary_volume_rejected(native: str) -> None:
    with pytest.raises(ValueError, match="Native volume"):
        audit_volume_conventions(
            ["1.0000"], timestep_hours=Decimal("0.5"), native_reported_volume_token=native
        )


@pytest.mark.parametrize("times", [[], ["0.00"], ["0.00", ""]])
def test_incomplete_native_time_labels_rejected(times: list[str]) -> None:
    with pytest.raises(ValueError, match="Raw native time labels"):
        audit_volume_conventions(
            ["1.0000", "2.0000"], timestep_hours=Decimal("0.5"), raw_native_time_tokens=times
        )


def test_native_volume_conventions_do_not_depend_on_raw_label_offsets() -> None:
    discharge = ["0.0000", "2.0000", "1.0000"]
    cmd = audit_volume_conventions(
        discharge, timestep_hours=Decimal("0.5"), raw_native_time_tokens=["0.50", "1.00", "1.50"]
    )
    gui = audit_volume_conventions(
        discharge, timestep_hours=Decimal("0.5"), raw_native_time_tokens=["0.00", "0.50", "1.00"]
    )
    assert cmd.inclusive_sample_sum_m3 == gui.inclusive_sample_sum_m3
    assert cmd.physical_trapezoid_m3 == gui.physical_trapezoid_m3
    assert cmd.raw_native_time_tokens != gui.raw_native_time_tokens
    assert cmd.sample_index_elapsed_hours == gui.sample_index_elapsed_hours


def test_invalid_print_unit_does_not_elevate_reporting_hypothesis_to_parity() -> None:
    result = audit_volume_conventions(
        ["0.0000", "0.0000"], timestep_hours=Decimal("0.5"), native_reported_volume_token="0.00"
    )
    assert result.sample_sum_consistent_with_report is True
    assert result.trapezoid_consistent_with_report is True
    assert not hasattr(result, "numerical_parity_accepted")
