"""Synthetic onset classification and raw-token invariants; no native RORB runs."""

from __future__ import annotations

import math
from dataclasses import replace

import pytest

from runoff_routing.offline_reference import OfflineComparison, OrdinateDifference
from runoff_routing.onset_diagnostics import audit_offline_comparison, audit_onset, summarize_onset_audits


def test_first_mismatch_at_first_nonzero_and_native_clock_is_not_shifted() -> None:
    prediction = (0.0, 0.0, 1.02, 1.5)
    native = ("0.0000", "0.0000", "1.0000", "1.5000")
    result = audit_onset(
        prediction,
        native,
        dt_hours=0.5,
        case_id="synthetic-prefix",
        native_increment_tokens=("1", "2", "3", "4"),
        native_time_tokens=("0.50", "1.00", "1.50", "2.00"),
    )
    assert result.classification == "at_onset"
    assert result.first_native_nonzero_index == result.first_predicted_nonzero_index == 2
    assert result.first_any_nonzero_index == result.first_outside_budget_index == 2
    assert result.samples_from_onset == 0
    assert result.first_mismatch_native_increment == "3"
    assert result.first_mismatch_native_time == "1.50"
    assert result.first_mismatch_native_discharge == "1.0000"
    assert result.first_mismatch_predicted_m3_s == pytest.approx(1.02)
    assert result.first_mismatch_signed_error_m3_s == pytest.approx(0.02)
    assert not result.printed_parity.within_print_budget


def test_mismatch_one_after_onset_when_first_nonzero_is_within_printing_allowance() -> None:
    result = audit_onset(
        (0.0, 1.00004, 1.02),
        ("0.0000", "1.0000", "1.0000"),
        dt_hours=0.25,
    )
    assert result.classification == "next_sample"
    assert result.first_any_nonzero_index == 1
    assert result.first_outside_budget_index == 2
    assert result.samples_from_onset == 1
    assert result.first_mismatch_native_time is None


def test_later_mismatch_and_equal_native_gui_axes_remain_distinct() -> None:
    prediction = (0.0, 0.5, 1.0, 1.0, 1.1)
    printed = ("0.0000", "0.5000", "1.0000", "1.0000", "1.0000")
    cmd = audit_onset(
        prediction, printed, dt_hours=0.5,
        native_increment_tokens=("1", "2", "3", "4", "5"),
        native_time_tokens=("0.50", "1.00", "1.50", "2.00", "2.50"),
    )
    gui = audit_onset(
        prediction, printed, dt_hours=0.5,
        native_increment_tokens=("0", "1", "2", "3", "4"),
        native_time_tokens=("0.00", "0.50", "1.00", "1.50", "2.00"),
    )
    assert cmd.classification == gui.classification == "later"
    assert cmd.first_outside_budget_index == gui.first_outside_budget_index == 4
    assert cmd.samples_from_onset == gui.samples_from_onset == 3
    assert cmd.first_mismatch_native_time == "2.50"
    assert gui.first_mismatch_native_time == "2.00"


def test_zero_printing_and_tiny_positive_prediction_are_not_misclassified_as_parity_failures() -> None:
    zero = audit_onset((0.0, 0.0), ("0.000", "0.000"), dt_hours=0.5)
    assert zero.classification == "within_print_budget"
    assert zero.first_any_nonzero_index is None
    assert zero.first_outside_budget_index is None
    assert zero.first_mismatch_native_discharge is None

    small = audit_onset((0.00004, 0.0), ("0.0000", "0.0000"), dt_hours=0.5)
    assert small.classification == "within_print_budget"
    assert small.first_predicted_nonzero_index == 0
    assert small.first_native_nonzero_index is None
    assert small.first_mismatch_signed_error_m3_s is None


def test_native_might_be_nonzero_before_python_and_mismatch_is_first_visible_sample() -> None:
    result = audit_onset((0.0, 0.0, 1.0), ("0.0000", "0.5000", "1.0000"), dt_hours=1)
    assert result.classification == "at_onset"
    assert result.first_native_nonzero_index == 1
    assert result.first_predicted_nonzero_index == 2
    assert result.first_any_nonzero_index == 1
    assert result.first_mismatch_signed_error_m3_s == pytest.approx(-0.5)


def test_offline_adapter_checks_identity_and_preserves_original_native_tokens() -> None:
    rows = (
        OrdinateDifference(0, "1", "0.50", "0.0000", 0.0, 0.0),
        OrdinateDifference(1, "2", "1.00", "2.0000", 2.02, 0.02),
    )
    comparison = OfflineComparison("synthetic", "compared", "test fixture", dt_hours=0.5, sample_count=2, differences=rows)
    result = audit_offline_comparison(comparison)
    assert result.case_id == "synthetic"
    assert result.first_mismatch_native_time == "1.00"
    assert result.classification == "at_onset"
    with pytest.raises(ValueError, match="complete computed"):
        audit_offline_comparison(replace(comparison, status="unsupported"))
    with pytest.raises(ValueError, match="complete computed"):
        audit_offline_comparison(replace(comparison, sample_count=3))
    with pytest.raises(ValueError, match="zero-based"):
        audit_offline_comparison(replace(comparison, differences=(replace(rows[0], row=1), *rows[1:])))


def test_campaign_counts_and_duplicate_id_fail_closed() -> None:
    first = audit_onset((0, 2), ("0.0000", "1.0000"), dt_hours=0.5, case_id="case-a")
    second = audit_onset((0, 1.00001), ("0.0000", "1.0000"), dt_hours=0.5, case_id="case-b")
    summary = summarize_onset_audits((first, second))
    assert summary.total == 2
    assert summary.at_onset == 1
    assert summary.within_print_budget == 1
    assert summary.next_sample == summary.later == 0
    with pytest.raises(ValueError, match="Duplicate"):
        summarize_onset_audits((first, first))
    with pytest.raises(ValueError, match="At least one"):
        summarize_onset_audits(())


@pytest.mark.parametrize(
    ("prediction", "native"),
    [
        ((0.0,), ("0.0000", "0.0000")),
        ((math.nan,), ("0.0000",)),
        ((-1.0,), ("0.0000",)),
        ((0.0,), ("NaN",)),
        ((0.0,), ("-1.0",)),
        ((), ()),
    ],
)
def test_malformed_inputs_inherit_the_strict_parity_validation(
    prediction: tuple[float, ...], native: tuple[str, ...]
) -> None:
    with pytest.raises(ValueError, match=r"sample|discharge|printed"):
        audit_onset(prediction, native, dt_hours=0.5)


def test_native_clock_and_identifiers_do_not_accept_partial_or_malformed_provenance() -> None:
    with pytest.raises(ValueError, match="supplied together"):
        audit_onset((0.0,), ("0.000",), dt_hours=0.5, native_time_tokens=("0.50",))
    with pytest.raises(ValueError, match="matching the sample grid"):
        audit_onset((0.0, 0.0), ("0.000", "0.000"), dt_hours=0.5,
                    native_increment_tokens=("1",), native_time_tokens=("0.50", "1.00"))
    with pytest.raises(ValueError, match="nonempty original strings"):
        audit_onset((0.0,), ("0.000",), dt_hours=0.5,
                    native_increment_tokens=("\n",), native_time_tokens=("0.50",))
    with pytest.raises(ValueError, match="Case identifier"):
        audit_onset((0.0,), ("0.000",), dt_hours=0.5, case_id=" unsafe ")
