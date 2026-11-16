"""Independent hand-calculated S7/C weighted-frequency controls; no native equivalence."""

from __future__ import annotations

import math
from dataclasses import replace
from typing import cast

import pytest

from runoff_routing.monte_carlo_frequency import (
    CurvePopulation,
    FrequencyInputError,
    FrequencyScope,
    PeakRecord,
    PeakStatus,
    StratumWeight,
    UnmodelledTails,
    build_frequency_curve,
    build_frequency_curves,
    duration_envelope,
)


def _scope(*, site: str = "site-A", duration: int = 60, scenario: str = "design") -> FrequencyScope:
    return FrequencyScope(f"plan-{duration}", "method-1", "v1", scenario, duration, site)


def _record(
    scope: FrequencyScope,
    stratum: str,
    sample: str,
    peak: float | None,
    *,
    status: PeakStatus = "valid",
    weight: float = 0.5,
) -> PeakRecord:
    return PeakRecord(
        scope,
        stratum,
        sample,
        weight,
        status,
        peak,
        f"event-{sample}" if status == "valid" else None,
        f"manifest-{sample}" if status == "valid" else None,
    )


def _four(*, scope: FrequencyScope | None = None) -> tuple[CurvePopulation, tuple[PeakRecord, ...]]:
    s = scope or _scope()
    # Manually enumerated: 0.25/2 = 0.125 for each h1 event;
    # 0.75/2 = 0.375 for each h2 event.
    p = CurvePopulation(s, (StratumWeight("h1", 0.25, 2), StratumWeight("h2", 0.75, 2)))
    return p, (
        _record(s, "h1", "a", 10, weight=0.125),
        _record(s, "h1", "b", 20, weight=0.125),
        _record(s, "h2", "c", 30, weight=0.375),
        _record(s, "h2", "d", 40, weight=0.375),
    )


def test_exact_unequal_weight_exceedance_and_adopted_step_inverse() -> None:
    population, records = _four()
    curve = build_frequency_curve(population, records)
    assert curve.coverage.valid_mass == 1
    assert curve.coverage.complete
    assert curve.exceedance(20).lower_probability == pytest.approx(0.75)  # strict: 20 does not exceed 20
    assert curve.exceedance(30).upper_probability == pytest.approx(0.375)
    assert curve.exceedance(0).lower_probability == 1
    assert curve.exceedance(40).upper_probability == 0
    assert curve.groups[2].cumulative_mass == pytest.approx(0.625)
    assert curve.groups[3].cumulative_mass == pytest.approx(1.0)
    q = curve.estimate(0.5)
    assert q.status == "estimated"
    # At F=0.5 the first attained peak with cumulative mass >= 0.5 is 30.
    assert q.peak_m3_s == 30
    assert q.representative is not None
    assert q.representative.sample_id == "c"
    assert q.representative.event_id == "event-c"
    assert q.representative.effective_input_id == "manifest-c"
    assert q.representative.signed_mismatch_m3_s == 0
    assert q.native_equivalence == "not_assessed"
    assert q.statistical_qualification == "not_assessed"


def test_affine_monotone_transform_preserves_analytical_quantiles() -> None:
    population, records = _four()
    basic = build_frequency_curve(population, records)
    transformed = tuple(replace(item, peak_m3_s=float(item.peak_m3_s or 0) * 2 + 3) for item in records)
    scaled = build_frequency_curve(population, transformed)
    for aep in (0.2, 0.3, 0.5, 0.8):
        q1 = basic.estimate(aep)
        q2 = scaled.estimate(aep)
        assert q1.status == q2.status
        if q1.peak_m3_s is not None:
            assert q2.peak_m3_s == pytest.approx(q1.peak_m3_s * 2 + 3)


def test_zero_flow_atom_ties_and_representative_ties() -> None:
    s = _scope()
    p = CurvePopulation(s, (StratumWeight("dry", 0.4, 2), StratumWeight("wet", 0.6, 2)))
    rows = (
        _record(s, "dry", "zero-b", 0, weight=0.2),
        _record(s, "wet", "wet-b", 20, weight=0.3),
        _record(s, "wet", "wet-a", 20, weight=0.3),
        _record(s, "dry", "zero-a", 0, weight=0.2),
    )
    curve = build_frequency_curve(p, rows)
    assert curve.coverage.zero_mass == pytest.approx(0.4)
    assert curve.exceedance(0).lower_probability == pytest.approx(0.6)
    assert curve.exceedance(20).lower_probability == 0
    assert curve.estimate(0.65).status == "zero_atom"  # 1-AEP = 0.35 < 0.4
    zero = curve.estimate(0.65)
    assert zero.peak_m3_s == 0
    assert zero.representative is not None
    assert zero.representative.sample_id == "zero-a"  # independent of input order
    middle = curve.estimate(0.45)  # F=0.55 selects attained 20, never interpolated 10.
    assert middle.peak_m3_s == 20
    assert middle.representative is not None
    assert middle.representative.sample_id == "wet-a"  # exact 20-peak tie, stable lexical ID
    assert build_frequency_curve(p, reversed(rows)).estimate(0.45) == middle


def test_noninterpolating_step_inverse_on_attained_support_and_endpoint_rejection() -> None:
    population, rows = _four()
    curve = build_frequency_curve(population, rows)
    assert curve.estimate(0.01).peak_m3_s == 40  # empirical maximum, not extrapolated
    assert curve.estimate(0.99).peak_m3_s == 10  # empirical minimum, not extrapolated
    assert curve.estimate(0.1875).peak_m3_s == 40  # exactly on highest midpoint
    assert curve.estimate(0.9375).peak_m3_s == 10  # exactly on lowest midpoint
    assert curve.estimate(0.1875).at_observed_support_edge
    assert not curve.estimate(0.5).at_observed_support_edge
    with pytest.raises(FrequencyInputError, match="strictly inside"):
        curve.estimate(0)
    with pytest.raises(FrequencyInputError, match="strictly inside"):
        curve.estimate(1)


def test_failed_missing_and_unmodelled_tails_remain_in_denominators() -> None:
    s = _scope()
    p = CurvePopulation(
        s,
        (StratumWeight("first", 0.4, 2), StratumWeight("second", 0.4, 2)),
        UnmodelledTails(upper_rainfall_mass=0.2),
    )
    rows = (
        _record(s, "first", "valid0", 0, weight=0.2),
        _record(s, "first", "failed", None, status="failed", weight=0.2),
        _record(s, "second", "valid20", 20, weight=0.2),
        # second planned draw is absent; it retains weight 0.2.
    )
    curve = build_frequency_curve(p, rows)
    coverage = curve.coverage
    assert coverage.valid_mass == pytest.approx(0.4)
    assert coverage.zero_mass == pytest.approx(0.2)
    assert coverage.failed_mass == pytest.approx(0.2)
    assert coverage.missing_mass == pytest.approx(0.2)
    assert coverage.tails.total == pytest.approx(0.2)
    assert coverage.unresolved_mass == pytest.approx(0.6)
    assert curve.accounting[1].absent_samples == 1
    assert curve.estimate(0.1).status == "incomplete"
    assert curve.estimate(0.1).peak_m3_s is None
    # Target F=0.9. Putting unknown 0.6 all at +inf gives no finite upper bound;
    # placing it all at zero moves F=0.9 into known observed Q=20.
    bound = curve.estimate(0.1)
    assert bound.lower_bound_m3_s == 20
    assert bound.upper_bound_m3_s is None
    bracket = curve.exceedance(0)
    assert bracket.lower_probability == pytest.approx(0.2)
    assert bracket.upper_probability == pytest.approx(0.8)


def test_unallocated_stratum_and_zero_weight_failures() -> None:
    s = _scope()
    p = CurvePopulation(
        s,
        (StratumWeight("allocated", 0.8, 1), StratumWeight("unallocated", 0.2, 0)),
    )
    curve = build_frequency_curve(p, (_record(s, "allocated", "live", 5, weight=0.8),))
    assert curve.coverage.unallocated_stratum_mass == pytest.approx(0.2)
    assert curve.coverage.missing_mass == 0
    assert curve.estimate(0.5).status == "incomplete"
    assert curve.exceedance(5).upper_probability == pytest.approx(0.2)

    zero_mass_population = CurvePopulation(
        s,
        (StratumWeight("allocated", 1, 1), StratumWeight("unused", 0, 1)),
    )
    with_zero_weight_failure = build_frequency_curve(
        zero_mass_population,
        (_record(s, "allocated", "live", 5, weight=1), _record(s, "unused", "fail", None, status="failed", weight=0)),
    )
    assert with_zero_weight_failure.coverage.complete
    assert with_zero_weight_failure.accounting[1].failed_samples == 1
    assert with_zero_weight_failure.estimate(0.5).peak_m3_s == 5


def test_incomplete_quantile_bounds_with_known_zero_and_positive_peaks() -> None:
    s = _scope()
    p = CurvePopulation(s, (StratumWeight("interior", 0.8, 2),), UnmodelledTails(0.2, 0))
    curve = build_frequency_curve(
        p,
        (
            _record(s, "interior", "dry", 0, weight=0.4),
            _record(s, "interior", "wet", 20, weight=0.4),
        ),
    )
    # F=0.1: all missing mass at zero OR at infinity still places target in zero atom.
    q = curve.estimate(0.9)
    assert q.status == "incomplete"
    assert q.lower_bound_m3_s == 0
    assert q.upper_bound_m3_s == 0
    assert q.representative is None
    # F=0.9: upper cannot be inferred because known mass only 0.8.
    q = curve.estimate(0.1)
    assert q.lower_bound_m3_s == 20
    assert q.upper_bound_m3_s is None


def test_incomplete_explicit_statuses_do_not_become_valid_zero() -> None:
    s = _scope()
    p = CurvePopulation(s, (StratumWeight("h", 1, 4),))
    rows = (
        _record(s, "h", "zero", 0, weight=0.25),
        _record(s, "h", "error", None, status="failed", weight=0.25),
        _record(s, "h", "unrun", None, status="missing", weight=0.25),
        _record(s, "h", "unsupported", None, status="unsupported", weight=0.25),
    )
    curve = build_frequency_curve(p, rows)
    assert curve.coverage.valid_mass == 0.25
    assert curve.coverage.failed_mass == 0.25
    assert curve.coverage.missing_mass == 0.25
    assert curve.coverage.unsupported_mass == 0.25
    assert curve.estimate(0.5).status == "incomplete"


def test_input_order_permutations_and_identity_validation() -> None:
    p, rows = _four()
    original = build_frequency_curve(p, rows)
    for ordering in (rows[::-1], (rows[2], rows[0], rows[3], rows[1])):
        current = build_frequency_curve(p, ordering)
        assert current.coverage == original.coverage
        assert current.groups == original.groups
        assert current.estimate(0.5) == original.estimate(0.5)
    with pytest.raises(FrequencyInputError, match="Duplicate sample"):
        build_frequency_curve(p, (*rows, rows[0]))
    with pytest.raises(FrequencyInputError, match="Duplicate event"):
        build_frequency_curve(p, (*rows[:3], replace(rows[3], event_id="event-a")))
    with pytest.raises(FrequencyInputError, match="Mismatched plan"):
        build_frequency_curve(p, (replace(rows[0], scope=replace(p.scope, plan_id="plan-new")),))
    with pytest.raises(FrequencyInputError, match="Mismatched plan"):
        build_frequency_curve(p, (replace(rows[0], scope=replace(p.scope, policy_id="method-new")),))
    with pytest.raises(FrequencyInputError, match="Stale or mixed"):
        build_frequency_curve(p, (replace(rows[0], event_probability_weight=0.25),))
    with pytest.raises(FrequencyInputError, match="More observed samples"):
        build_frequency_curve(p, (*rows, _record(p.scope, "h1", "extra", 50, weight=0.125)))
    with pytest.raises(FrequencyInputError, match="Duplicate stratum"):
        CurvePopulation(p.scope, (StratumWeight("h", 1, 2), StratumWeight("h", 0, 1)))
    with pytest.raises(FrequencyInputError, match="sum to one"):
        CurvePopulation(p.scope, (StratumWeight("h", 0.8, 2),))


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -1, True])
def test_bad_flow_rejected(value: float) -> None:
    with pytest.raises(FrequencyInputError, match="finite nonnegative"):
        _record(_scope(), "h", "s", value)


def test_missing_replay_identity_or_invalid_success_status_rejected() -> None:
    s = _scope()
    with pytest.raises(FrequencyInputError, match="replayable"):
        PeakRecord(s, "h", "s", 0.5, "valid", 5)
    with pytest.raises(FrequencyInputError, match="must not carry"):
        PeakRecord(s, "h", "s", 0.5, "failed", 5)
    with pytest.raises(FrequencyInputError, match="Unrecognised"):
        _record(s, "h", "s", None, status=cast(PeakStatus, "computed_unvalidated"))


def test_unrepresentable_integer_peak_rejected_before_quantile_grouping() -> None:
    scope = _scope()
    accepted = _record(scope, "h", "exact-boundary", 1 << 53, weight=1 / 3)
    assert accepted.peak_m3_s == float(1 << 53)
    with pytest.raises(FrequencyInputError, match="Unrepresentable integer peak"):
        _record(scope, "h", "unrepresentable", (1 << 53) + 1, weight=1 / 3)
    with pytest.raises(FrequencyInputError, match="Unrepresentable integer peak"):
        _record(scope, "h", "huge", 10**400, weight=1 / 3)


def test_multiple_physical_sites_and_durations_do_not_pool() -> None:
    s_a = _scope(site="downstream", duration=60)
    s_b = _scope(site="upstream", duration=60)
    s_c = _scope(site="downstream", duration=120)
    pops = tuple(CurvePopulation(s, (StratumWeight("h", 1, 2),)) for s in (s_a, s_b, s_c))
    records = tuple(
        _record(s, "h", f"{s.duration_minutes}-{s.output_site_id}-{number}", peak)
        for s, peaks in ((s_a, (10, 20)), (s_b, (1, 2)), (s_c, (20, 30)))
        for number, peak in enumerate(peaks)
    )
    curves = build_frequency_curves(pops, reversed(records))
    assert len(curves) == 3
    by_scope = {curve.scope: curve for curve in curves}
    assert by_scope[s_b].estimate(0.5).peak_m3_s == 1
    assert by_scope[s_a].estimate(0.5).peak_m3_s == 10
    assert by_scope[s_c].estimate(0.5).peak_m3_s == 20
    envelope = duration_envelope((by_scope[s_a], by_scope[s_c]), 0.5)
    assert envelope.peak_m3_s == 20
    assert envelope.critical_duration_minutes == 120
    assert envelope.margin_to_second_m3_s == pytest.approx(10)
    assert envelope.representative is not None
    assert envelope.representative.event_id.startswith("event-120-downstream")
    with pytest.raises(FrequencyInputError, match="scenarios, policies or sites"):
        duration_envelope((by_scope[s_a], by_scope[s_b]), 0.5)
    with pytest.raises(FrequencyInputError, match="Duplicate duration"):
        duration_envelope((by_scope[s_a], by_scope[s_a]), 0.5)


def test_exact_tie_chooses_requested_duration_order_and_near_tie_stays_numeric() -> None:
    def _curve(d: int, upper: float) -> tuple[CurvePopulation, tuple[PeakRecord, ...]]:
        s = _scope(duration=d)
        return CurvePopulation(s, (StratumWeight("h", 1, 2),)), (
            _record(s, "h", f"{d}-a", 10),
            _record(s, "h", f"{d}-b", upper),
        )

    p60, r60 = _curve(60, 30)
    p120, r120 = _curve(120, 30)
    p180, r180 = _curve(180, 30.00000002)
    tied = duration_envelope((build_frequency_curve(p120, r120), build_frequency_curve(p60, r60)), 0.2)
    assert tied.critical_duration_minutes == 120
    assert tied.tied_critical_durations_minutes == (120, 60)
    assert tied.margin_to_second_m3_s == 0
    near = duration_envelope((build_frequency_curve(p60, r60), build_frequency_curve(p180, r180)), 0.2)
    assert near.critical_duration_minutes == 180
    assert near.margin_to_second_m3_s == pytest.approx(2e-8)


def test_unqualified_duration_blocks_envelope_and_preserves_bounds() -> None:
    s1, s2 = _scope(duration=60), _scope(duration=120)
    p1 = CurvePopulation(s1, (StratumWeight("h", 1, 2),))
    p2 = CurvePopulation(s2, (StratumWeight("h", 1, 2),))
    good = build_frequency_curve(p1, (_record(s1, "h", "a", 10), _record(s1, "h", "b", 30)))
    bad = build_frequency_curve(p2, (_record(s2, "h", "a", 20),))  # absent 1/2
    env = duration_envelope((good, bad), 0.5)
    assert env.status == "incomplete"
    assert env.peak_m3_s is None
    assert env.representative is None
    assert env.critical_duration_minutes is None
    assert env.upper_bound_m3_s == 20  # finite bound from known observed mass


def test_adopted_a_two_stratum_zero_tie_exact_mixture() -> None:
    """Independent literal #145 example: masses .2/.8, peaks 0/20/10/10."""
    s = _scope()
    population = CurvePopulation(s, (StratumWeight("dry", 0.2, 2), StratumWeight("wet", 0.8, 2)))
    rows = (
        _record(s, "dry", "a", 0, weight=0.1),
        _record(s, "dry", "b", 20, weight=0.1),
        _record(s, "wet", "c", 10, weight=0.4),
        _record(s, "wet", "d", 10, weight=0.4),
    )
    curve = build_frequency_curve(population, rows)
    assert curve.exceedance(0).known_exceedance_probability == pytest.approx(0.9)
    assert curve.exceedance(10).known_exceedance_probability == pytest.approx(0.1)
    assert curve.exceedance(20).known_exceedance_probability == 0
    assert curve.estimate(0.2).peak_m3_s == 10
    representative = curve.estimate(0.2).representative
    assert representative is not None
    assert representative.sample_id == "c"
    failed = build_frequency_curve(
        population,
        (*rows[:3], replace(rows[3], status="failed", peak_m3_s=None, event_id=None, effective_input_id=None)),
    )
    assert failed.exceedance(10).lower_probability == pytest.approx(0.1)
    assert failed.exceedance(10).upper_probability == pytest.approx(0.5)
    assert failed.estimate(0.2).status == "incomplete"


def test_boundary_stratum_exceedance_contribution_without_native_warning() -> None:
    s = _scope()
    population = CurvePopulation(
        s, (StratumWeight("frequent", 0.2, 1), StratumWeight("middle", 0.6, 1), StratumWeight("rare", 0.2, 1))
    )
    curve = build_frequency_curve(
        population,
        (
            _record(s, "frequent", "a", 10, weight=0.2),
            _record(s, "middle", "b", 20, weight=0.6),
            _record(s, "rare", "c", 30, weight=0.2),
        ),
    )
    x = curve.exceedance(15)
    assert x.known_exceedance_probability == pytest.approx(0.8)
    assert x.boundary_strata_known_exceedance_probability == pytest.approx(0.2)
    assert x.boundary_strata_share_of_known_exceedance == pytest.approx(0.25)
    assert curve.estimate(0.3).peak_m3_s == 20
    assert curve.estimate(0.3).boundary_strata_known_exceedance_probability == pytest.approx(0.2)


@pytest.mark.parametrize(
    ("count", "aep", "expected"),
    [(10, 0.1, 8.0), (20, 0.95, 0.0), (20, 0.05, 18.0)],
)
def test_exact_step_boundary_quantiles_from_hand_computed_ranks(count: int, aep: float, expected: float) -> None:
    scope = _scope()
    population = CurvePopulation(scope, (StratumWeight("h", 1, count),))
    records = tuple(_record(scope, "h", f"draw-{index}", float(index), weight=1 / count) for index in range(count))
    curve = build_frequency_curve(population, records)
    estimate = curve.estimate(aep)
    assert estimate.peak_m3_s == expected
    assert estimate.representative is not None
    assert estimate.representative.realised_peak_m3_s == expected


def test_adjacent_aep_probabilities_do_not_share_a_spurious_epsilon_tolerance() -> None:
    scope = _scope()
    population = CurvePopulation(scope, (StratumWeight("h", 1, 10),))
    rows = tuple(_record(scope, "h", f"draw-{i}", float(i), weight=0.1) for i in range(10))
    curve = build_frequency_curve(population, rows)
    assert curve.estimate(math.nextafter(0.1, 0.0)).peak_m3_s == 9
    assert curve.estimate(0.1).peak_m3_s == 8
    assert curve.estimate(math.nextafter(0.1, 1.0)).peak_m3_s == 8


def test_unequal_probability_strata_use_original_rational_allocations_for_inversion() -> None:
    scope = _scope()
    population = CurvePopulation(scope, (StratumWeight("a", 0.3, 3), StratumWeight("b", 0.7, 7)))
    rows = tuple(
        _record(scope, "a" if index < 3 else "b", f"draw-{index}", float(index), weight=0.1) for index in range(10)
    )
    curve = build_frequency_curve(population, reversed(rows))
    assert curve.estimate(0.1).peak_m3_s == 8
    assert curve.estimate(0.9).peak_m3_s == 0


def test_incomplete_quantile_bounds_at_exact_rational_step_boundaries() -> None:
    scope = _scope()
    population = CurvePopulation(scope, (StratumWeight("modelled", 0.9, 9),), UnmodelledTails(lower_rainfall_mass=0.1))
    rows = tuple(_record(scope, "modelled", f"draw-{i}", float(i), weight=0.1) for i in range(9))
    curve = build_frequency_curve(population, rows)
    estimate = curve.estimate(0.2)
    assert estimate.status == "incomplete"
    assert estimate.peak_m3_s is None
    assert estimate.lower_bound_m3_s == 6  # F_known reaches 7/10 at Q=6.
    assert estimate.upper_bound_m3_s == 7  # F_known reaches 8/10 at Q=7.
    assert estimate.representative is None
