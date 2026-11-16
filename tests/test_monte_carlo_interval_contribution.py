"""Independent analytic controls for ARR interval audits and conditional sampling diagnostics.

All peak arrays are NEW authored synthetic examples. The historical RORBwin
5x5 pilot is an execution/format receipt, NOT a statistical validation case.
"""

from __future__ import annotations

import math

import pytest

from runoff_routing.monte_carlo_frequency import (
    CurvePopulation,
    FrequencyCurve,
    FrequencyInputError,
    FrequencyScope,
    PeakRecord,
    StratumWeight,
    UnmodelledTails,
    build_frequency_curve,
)
from runoff_routing.monte_carlo_frequency_bridge import format_selected_aep_table


def _curve(
    peaks: tuple[float, ...],
    *,
    site: str = "print_1",
    missing_index: int | None = None,
    tails: UnmodelledTails | None = None,
) -> FrequencyCurve:
    scope = FrequencyScope("plan-187", "independent", "v1", "synthetic", 1440, site)
    tails = tails if tails is not None else UnmodelledTails()
    mass = (1 - tails.total) / len(peaks)
    allocations = tuple(StratumWeight(f"interval-{i}", mass, 1) for i in range(len(peaks)))
    records = tuple(
        PeakRecord(
            scope,
            f"interval-{i}",
            f"sample-{i}",
            mass,
            "missing" if i == missing_index else "valid",
            None if i == missing_index else peak,
            None if i == missing_index else f"event-{i}",
            None if i == missing_index else f"input-{i}",
        )
        for i, peak in enumerate(peaks)
    )
    return build_frequency_curve(CurvePopulation(scope, allocations, tails), records)


def test_tpt_contributions_use_strict_exceedance_without_a_native_flag() -> None:
    curve = _curve((10.0, 20.0, 30.0, 40.0, 50.0))
    estimate = curve.estimate(0.4)
    assert estimate.peak_m3_s == 30.0
    audit = estimate.interval_probability_audit
    assert audit is not None
    assert audit.method == "arr-total-probability-strict-interval-contributions-v1"
    assert audit.known_strict_exceedance_probability == pytest.approx(0.4)
    assert audit.maximum_stratum_id == "interval-3"
    assert audit.maximum_stratum_share_of_known_exceedance == pytest.approx(0.5)
    assert [row.exceeding_samples for row in audit.strata] == [0, 0, 0, 1, 1]
    assert [row.strict_exceedance_probability_mass for row in audit.strata] == pytest.approx([0, 0, 0, 0.2, 0.2])
    # The concentrated interval contribution is DESCRIPTIVE, never a RORB *.
    assert estimate.native_interval_warning == "not_assessed"
    assert curve.exceedance(30.0).known_exceedance_probability == pytest.approx(0.4)


def test_5x5_adversarial_synthetic_concentration_is_not_native_parity() -> None:
    scope = FrequencyScope("plan-5x5", "independent", "v1", "synthetic", 1440, "print_1")
    population = CurvePopulation(scope, tuple(StratumWeight(f"h{i}", 0.2, 5) for i in range(5)))
    # Authored zero/positive pattern, not copied from the RORBwin output.
    peaks = (
        (0, 0, 0, 0, 0),
        (0, 0, 0, 0, 0),
        (0, 0, 10, 15, 25),
        (40, 45, 50, 55, 60),
        (80, 85, 90, 95, 100),
    )
    rows = tuple(
        PeakRecord(scope, f"h{h}", f"s{h}-{j}", 0.04, "valid", float(q), f"e{h}-{j}", f"i{h}-{j}")
        for h, group in enumerate(peaks)
        for j, q in enumerate(group)
    )
    curve = build_frequency_curve(population, rows)
    estimate = curve.estimate(0.5)
    audit = estimate.interval_probability_audit
    assert audit is not None
    assert audit.maximum_stratum_share_of_known_exceedance is not None
    assert audit.maximum_stratum_share_of_known_exceedance >= 1 / 3
    # Contributing fractions cannot be used to reproduce native reliability stars.
    assert estimate.native_interval_warning == "not_assessed"
    diagnostic = estimate.scientific_sampling_diagnostic
    assert diagnostic is not None
    assert diagnostic.status == "review"
    assert diagnostic.simultaneous_absolute_aep_margin == pytest.approx(math.sqrt(math.log(200) / 10))


def test_zero_atom_and_two_physical_sites_are_distinct() -> None:
    upstream = _curve((10.0, 20.0, 30.0, 40.0, 50.0), site="upstream")
    downstream = _curve((0.0, 0.0, 0.0, 0.0, 0.0), site="downstream")
    up = upstream.estimate(0.4)
    down = downstream.estimate(0.4)
    assert up.peak_m3_s == 30.0
    assert down.peak_m3_s == 0.0
    assert down.status == "zero_atom"
    assert down.interval_probability_audit is not None
    assert down.interval_probability_audit.known_strict_exceedance_probability == 0.0
    assert down.interval_probability_audit.maximum_stratum_id is None
    assert downstream.exceedance(0).known_exceedance_probability == 0
    assert up.native_interval_warning == down.native_interval_warning == "not_assessed"


def test_uniform_dkw_bound_is_simultaneous_and_uses_declared_screen() -> None:
    n = 1000
    scope = FrequencyScope("plan-1000", "independent", "v1", "synthetic", 60, "print_1")
    population = CurvePopulation(scope, (StratumWeight("h", 1.0, n),))
    rows = tuple(PeakRecord(scope, "h", f"s{i}", 1 / n, "valid", float(i), f"e{i}", f"i{i}") for i in range(n))
    curve = build_frequency_curve(population, rows)
    expected = math.sqrt(math.log(40) / 2000)
    loose = curve.estimate(0.5)
    strict = curve.estimate(0.1)
    assert loose.scientific_sampling_diagnostic is not None
    assert strict.scientific_sampling_diagnostic is not None
    assert loose.scientific_sampling_diagnostic.simultaneous_absolute_aep_margin == pytest.approx(expected)
    assert loose.scientific_sampling_diagnostic.status == "below_screen"
    assert loose.scientific_sampling_diagnostic.margin_relative_to_target_aep == pytest.approx(2 * expected)
    assert strict.scientific_sampling_diagnostic.status == "review"
    assert strict.scientific_sampling_diagnostic.margin_relative_to_target_aep == pytest.approx(10 * expected)
    assert loose.scientific_sampling_diagnostic.maximum_single_sample_probability_weight == pytest.approx(0.001)
    assert strict.scientific_sampling_diagnostic.native_equivalence == "not_assessed"
    assert strict.scientific_sampling_diagnostic.independent_seed_convergence == "not_assessed"
    assert strict.scientific_sampling_diagnostic.boundary_sensitivity == "not_assessed"
    assert (
        curve.estimate(0.5, confidence_level=0.95, relative_aep_screen=0.05).scientific_sampling_diagnostic is not None
    )
    lower = curve.estimate(0.5, confidence_level=0.95, relative_aep_screen=0.05)
    assert lower.scientific_sampling_diagnostic is not None
    assert lower.scientific_sampling_diagnostic.status == "review"


def test_missing_positive_weight_or_rainfall_tail_fails_closed() -> None:
    for curve in (
        _curve((10.0, 20.0, 30.0, 40.0, 50.0), missing_index=0),
        _curve((10.0, 20.0, 30.0, 40.0, 50.0), tails=UnmodelledTails(0.1)),
    ):
        estimate = curve.estimate(0.4)
        assert estimate.status == "incomplete"
        assert estimate.peak_m3_s is None
        assert estimate.interval_probability_audit is None
        assert estimate.native_interval_warning == "not_assessed"
        assert estimate.scientific_sampling_diagnostic is not None
        assert estimate.scientific_sampling_diagnostic.status == "not_assessed"
        assert estimate.scientific_sampling_diagnostic.simultaneous_absolute_aep_margin is None


@pytest.mark.parametrize(
    ("confidence", "screen"),
    [(0.0, 0.2), (1.0, 0.2), (math.nan, 0.2), (0.95, 0.0), (0.95, math.inf), (0.95, -0.2)],
)
def test_unqualified_scientific_parameters_rejected(confidence: float, screen: float) -> None:
    curve = _curve((10.0, 20.0, 30.0))
    with pytest.raises(FrequencyInputError):
        curve.estimate(0.5, confidence_level=confidence, relative_aep_screen=screen)


def test_selected_aep_table_marks_scientific_review_not_native_asterisk() -> None:
    curve = _curve((10.0, 20.0, 30.0, 40.0, 50.0))
    targets = (0.99, 0.4)
    estimates: list[dict[str, object]] = [
        {
            "status": item.status,
            "peak_m3_s": item.peak_m3_s,
            "native_interval_warning": item.native_interval_warning,
            "scientific_sampling_diagnostic": {"status": item.scientific_sampling_diagnostic.status},
        }
        for item in (curve.estimate(0.99), curve.estimate(0.4))
        if item.scientific_sampling_diagnostic is not None
    ]
    lines, flagged = format_selected_aep_table("print_01", targets, estimates)
    assert flagged
    assert "AEP(1inY)" in lines[1]
    assert "Peak print_01" in lines[1]
    assert "1.01" in lines[2]
    assert "10.00!" in lines[2]
    assert "2.5" in lines[3]
    assert "30.00!" in lines[3]
    assert "*" not in lines[2] + lines[3]
    assert "native *" in lines[0]
    assert any("NOT ASSESSED" in line for line in lines)


def test_incomplete_aep_table_prints_na_without_any_warning_symbol() -> None:
    curve = _curve((10.0, 20.0, 30.0, 40.0, 50.0), missing_index=0)
    item = curve.estimate(0.4)
    assert item.scientific_sampling_diagnostic is not None
    lines, flagged = format_selected_aep_table(
        "print_01",
        (0.4,),
        [
            {
                "status": item.status,
                "peak_m3_s": item.peak_m3_s,
                "native_interval_warning": "not_assessed",
                "scientific_sampling_diagnostic": {"status": "not_assessed"},
            }
        ],
    )
    assert not flagged
    assert "N/A" in lines[2]
    assert "!" not in lines[2]
    assert "*" not in lines[2]
    assert any("unresolved probability mass" in line for line in lines)
