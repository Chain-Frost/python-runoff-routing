"""Prospective metric comparator controls; no native program or private data."""

import hashlib
import math
from dataclasses import replace
from fractions import Fraction
from pathlib import Path

import pytest

from runoff_routing.regression_metrics import (
    ScalarField,
    SiteMetrics,
    bind_report_metrics,
    compare_peak,
    compare_reported_volume,
    token_interval,
)
from runoff_routing.rorb_documents import RorbSource
from runoff_routing.rorb_out import inspect_output


def binding() -> SiteMetrics:
    return SiteMetrics(
        "Hyd001",
        "Synthetic outlet",
        ScalarField("1.", 1, 1, 1, "m3/s"),
        ScalarField("0.50", 2, 1, 1, "h"),
        ScalarField("2.70E+03", 3, 1, 1, "m3"),
    )


def test_original_peak_interval_is_inclusive() -> None:
    assert compare_peak((0.0, 1.5), Fraction(1, 2), binding()).magnitude == "pass"
    assert compare_peak((0.0, math.nextafter(1.5, 2.0)), Fraction(1, 2), binding()).magnitude == "fail"


def test_original_time_is_sample_index_not_raw_row_label() -> None:
    actual = compare_peak((0.0, 1.5), Fraction(1, 2), binding())
    assert actual.time == "pass"
    assert actual.candidate_elapsed_hours == Fraction(1, 2)
    shifted = replace(binding(), peak_time=ScalarField("1.00", 2, 1, 1, "h"))
    assert compare_peak((0.0, 1.5), Fraction(1, 2), shifted).time == "fail"


def test_zero_peak_does_not_acquire_physical_time_acceptance() -> None:
    zero = replace(binding(), peak=ScalarField("0.000", 1, 1, 1, "m3/s"))
    actual = compare_peak((0.0, 0.0), Fraction(1, 2), zero)
    assert actual.magnitude == "pass"
    assert actual.time == "incomplete"
    assert actual.time_reason == "zero_flow_time_undefined"


def test_exact_ties_are_not_silently_given_first_or_last_policy() -> None:
    actual = compare_peak((0.0, 1.5, 1.5), Fraction(1, 2), binding())
    assert actual.time == "incomplete"
    assert actual.candidate_tied_indices == (1, 2)


def test_report_volume_uses_both_endpoints_at_full_weight() -> None:
    assert compare_reported_volume((0.0, 1.5), Fraction(1800), binding()) == "pass"
    physical = replace(binding(), volume=ScalarField("1.35E+03", 3, 1, 1, "m3"))
    assert compare_reported_volume((0.0, 1.5), Fraction(1800), physical) == "fail"


@pytest.mark.parametrize("token", ["NaN", "Inf", "-1", "1_000", " 1.0", "1.0 ", ""])
def test_invalid_summary_tokens_are_rejected(token: str) -> None:
    with pytest.raises(ValueError, match=r"Scalar|Invalid scalar"):
        token_interval(token)


def source(extra: str = "", *, legend: str = "01", peak: str = "1.500") -> RorbSource:
    text = (
        "Time increment (hours)= 0.50\nDuration of calculations: 2\n"
        f"Peak discharge,m³/s {peak}\nTime to peak,h 0.50\nVolume,m³ 2.70E+03\n{extra}"
        f"Hydrograph summary\nSite Description\n{legend} Synthetic outlet\n"
        "Inc Time Hyd001\n1 0.50 0.000\n2 1.00 1.500\n3 1.50 0.000\n"
    )
    raw = text.encode()
    return RorbSource(
        Path("synthetic.out").absolute(), hashlib.sha256(raw).hexdigest(), len(raw), "utf-8", tuple(text.splitlines())
    )


def test_scalar_selectors_retain_original_token_and_location() -> None:
    original = source()
    report = inspect_output(original).hydrographs
    assert report is not None
    actual = bind_report_metrics(original, report)[0]
    assert actual.column == "Hyd001"
    assert actual.peak is not None
    field = actual.peak
    assert original.lines[field.line - 1][field.character - 1 :].split()[0] == field.token


def test_duplicate_scalar_fields_do_not_disappear() -> None:
    original = source("Peak discharge,m³/s 1.500\n")
    report = inspect_output(original).hydrographs
    assert report is not None
    with pytest.raises(ValueError, match="duplicate native scalar"):
        bind_report_metrics(original, report)


def test_wrong_site_legend_does_not_bind_by_position_alone() -> None:
    original = source(legend="02")
    report = inspect_output(original).hydrographs
    assert report is not None
    with pytest.raises(ValueError, match="no matching physical site"):
        bind_report_metrics(original, report)


def test_nonfinite_peak_summary_rejected_even_with_valid_table() -> None:
    original = source(peak="NaN")
    report = inspect_output(original).hydrographs
    assert report is not None
    with pytest.raises(ValueError, match="finite and nonnegative"):
        bind_report_metrics(original, report)


def _source_from_text(text: str) -> RorbSource:
    raw = text.encode("utf-8")
    return RorbSource(
        Path("physical-sites.out").absolute(),
        hashlib.sha256(raw).hexdigest(),
        len(raw),
        "utf-8",
        tuple(text.splitlines()),
    )


def test_canonical_physical_binding_accepts_zero_padding_without_changing_scalar_scope() -> None:
    base = source()
    raw = "\n".join(base.lines).replace("Inc Time Hyd001", "Inc Time Hyd0001") + "\n"
    original = _source_from_text(raw)
    report = inspect_output(original).hydrographs
    assert report is not None
    matched = bind_report_metrics(original, report)
    assert len(matched) == 1
    assert matched[0].column == "Hyd0001"
    assert matched[0].label == "Synthetic outlet"
    assert matched[0].peak is not None
    assert matched[0].peak.token == base.lines[2].split()[-1]


def test_reordered_hyd_columns_bind_only_named_sites_when_scalars_are_absent() -> None:
    text = (
        "RORBWin Output File\nProgram version 6.44\n"
        "Time increment (hours)= 0.50\nDuration of calculations: 2\n"
        "Hydrograph summary\nSite Description\n"
        "01 Calculated hydrograph, Upstream\n"
        "02 Calculated hydrograph, Downstream\n"
        "Inc Time Hyd002 Hyd001\n"
        "1 0.50 0.000 0.000\n2 1.00 1.500 1.000\n3 1.50 0.000 0.000\n"
    )
    original = _source_from_text(text)
    report = inspect_output(original).hydrographs
    assert report is not None
    matched = bind_report_metrics(original, report)
    assert [(item.column, item.label) for item in matched] == [
        ("Hyd002", "Calculated hydrograph, Downstream"),
        ("Hyd001", "Calculated hydrograph, Upstream"),
    ]
    assert all(item.peak is None and item.peak_time is None and item.volume is None for item in matched)


def test_reordered_hyd_columns_reject_unqualified_scalar_ordinal_association() -> None:
    text = (
        "RORBWin Output File\nProgram version 6.44\n"
        "Time increment (hours)= 0.50\nDuration of calculations: 2\n"
        "Peak discharge,m³/s 1.500 1.000\n"
        "Hydrograph summary\nSite Description\n"
        "01 Calculated hydrograph, Upstream\n"
        "02 Calculated hydrograph, Downstream\n"
        "Inc Time Hyd002 Hyd001\n"
        "1 0.50 0.000 0.000\n2 1.00 1.500 1.000\n3 1.50 0.000 0.000\n"
    )
    original = _source_from_text(text)
    report = inspect_output(original).hydrographs
    assert report is not None
    with pytest.raises(ValueError, match="scalar ordinals cannot be bound"):
        bind_report_metrics(original, report)


def test_unnamed_single_site_retains_numeric_scalars_but_not_physical_name() -> None:
    base = source()
    raw = "\n".join(base.lines).replace("01 Synthetic outlet", "01 Calculated hydrograph,") + "\n"
    original = _source_from_text(raw)
    report = inspect_output(original).hydrographs
    assert report is not None

    # The source-derived single-terminal CMD scalar is still comparable;
    # the raw legend gives no physical print label or verification.
    fields = bind_report_metrics(original, report)
    assert len(fields) == 1
    assert fields[0].column == "Hyd001"
    assert fields[0].label == "Calculated hydrograph,"
    assert fields[0].peak is not None
    assert fields[0].peak.token == base.lines[2].split()[-1]


def test_missing_volume_does_not_block_peak_comparison() -> None:
    actual = replace(binding(), volume=None)
    assert compare_reported_volume((0.0, 1.5), Fraction(1800), actual) == "incomplete"
    assert compare_peak((0.0, 1.5), Fraction(1, 2), actual).magnitude == "pass"


def test_missing_peak_scalar_does_not_turn_into_zero_reference() -> None:
    actual = compare_peak((0.0, 1.5), Fraction(1, 2), replace(binding(), peak=None))
    assert actual.magnitude == "incomplete"
    assert actual.time == "pass"
