"""Pure weighted Monte Carlo peak-frequency analysis (issue #147).

Consumes explicit completed/failed samples and their *planned* stratum mass.
No random draws, routing, source-file I/O, hydrograph invention or native claim.
"""

from __future__ import annotations

import math
from collections import Counter, defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from fractions import Fraction
from typing import Literal, Never

PeakStatus = Literal["valid", "failed", "missing", "unsupported"]
QuantileStatus = Literal["estimated", "zero_atom", "incomplete"]
ScientificScreenStatus = Literal["review", "below_screen", "not_assessed"]
METHOD_PROFILE = "monte-carlo-statistics/1:weighted-step-inverse-v1"
INTERVAL_AUDIT_METHOD = "arr-total-probability-strict-interval-contributions-v1"
SCIENTIFIC_SCREEN_METHOD = "conditional-stratum-dkw-uniform-bonferroni-v1"
DEFAULT_SAMPLING_CONFIDENCE = 0.95
DEFAULT_RELATIVE_AEP_SCREEN = 0.2
_MASS_ROUNDOFF = 1e-12  # Input binary floating-point summation tolerance, never an engineering error band.


class FrequencyInputError(ValueError):
    """Inconsistent plan, probability allocation or peak-result ledger."""


def _fail(message: str) -> Never:
    raise FrequencyInputError(message)


def _identifier(value: object, label: str) -> None:
    if not isinstance(value, str) or not value or value != value.strip() or any(ord(c) < 32 for c in value):
        _fail(f"{label} must be nonempty, trimmed text without controls")


def _probability(value: object, label: str) -> None:
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
        or not 0 <= value <= 1
    ):
        _fail(f"{label} must be a finite probability in [0, 1]")


def _finite_real(value: object) -> bool:
    """Accept finite non-boolean Python real-valued API inputs."""
    return not isinstance(value, bool) and isinstance(value, (int, float)) and math.isfinite(value)


@dataclass(frozen=True, slots=True)
class FrequencyScope:
    """One immutable sample plan, scenario, storm duration and physical site."""

    plan_id: str
    policy_id: str
    policy_version: str
    scenario_id: str
    duration_minutes: int
    output_site_id: str

    def __post_init__(self) -> None:
        _identifier(self.plan_id, "plan_id")
        _identifier(self.policy_id, "policy_id")
        _identifier(self.policy_version, "policy_version")
        _identifier(self.scenario_id, "scenario_id")
        _identifier(self.output_site_id, "output_site_id")
        if type(self.duration_minutes) is not int or self.duration_minutes <= 0:
            _fail("duration_minutes must be a positive integer")


@dataclass(frozen=True, slots=True)
class StratumWeight:
    """Original conditional-draw allocation, not a reweighted retained-result count."""

    stratum_id: str
    probability_mass: float
    planned_samples: int

    def __post_init__(self) -> None:
        _identifier(self.stratum_id, "stratum_id")
        _probability(self.probability_mass, "stratum probability mass")
        if type(self.planned_samples) is not int or self.planned_samples < 0:
            _fail("planned_samples must be a nonnegative integer")


@dataclass(frozen=True, slots=True)
class UnmodelledTails:
    """Explicit residual rainfall-domain mass; no extrapolated flow assumptions."""

    lower_rainfall_mass: float = 0.0
    upper_rainfall_mass: float = 0.0
    other_mass: float = 0.0

    def __post_init__(self) -> None:
        _probability(self.lower_rainfall_mass, "lower rainfall tail")
        _probability(self.upper_rainfall_mass, "upper rainfall tail")
        _probability(self.other_mass, "other unmodelled mass")

    @property
    def total(self) -> float:
        return math.fsum((self.lower_rainfall_mass, self.upper_rainfall_mass, self.other_mass))


@dataclass(frozen=True, slots=True)
class CurvePopulation:
    """Read-only aggregate view of B's *full* persisted plan, not a second plan schema."""

    scope: FrequencyScope
    strata: tuple[StratumWeight, ...]
    tails: UnmodelledTails = UnmodelledTails()

    def __post_init__(self) -> None:
        if not self.strata:
            _fail("A frequency population needs its complete strata allocation")
        names = [entry.stratum_id for entry in self.strata]
        if len(names) != len(set(names)):
            _fail("Duplicate stratum identifiers")
        mass = math.fsum((*[item.probability_mass for item in self.strata], self.tails.total))
        if not math.isclose(mass, 1.0, rel_tol=0.0, abs_tol=_MASS_ROUNDOFF):
            _fail("Strata and explicitly declared unmodelled tails must sum to one")


@dataclass(frozen=True, slots=True)
class PeakRecord:
    """One sample/site ledger row; E maps the original engine status explicitly.

    For a valid row, event_id and effective_input_id identify an actual replayable
    simulation, not an interpolated or averaged hydrograph. Engine acceptance
    is intentionally NOT implied by `valid`.
    """

    scope: FrequencyScope
    stratum_id: str
    sample_id: str
    event_probability_weight: float
    status: PeakStatus
    peak_m3_s: float | None = None
    event_id: str | None = None
    effective_input_id: str | None = None

    def __post_init__(self) -> None:
        _identifier(self.stratum_id, "stratum_id")
        _identifier(self.sample_id, "sample_id")
        _probability(self.event_probability_weight, "event probability weight")
        if self.status not in ("valid", "failed", "missing", "unsupported"):
            _fail("Unrecognised peak-result status")
        if self.event_id is not None:
            _identifier(self.event_id, "event_id")
        if self.effective_input_id is not None:
            _identifier(self.effective_input_id, "effective_input_id")
        # Reporting groups are binary64 floats. A larger Python integer can
        # round to a DIFFERENT attained peak and detach its probability mass
        # from the exact inverse. Reject it rather than mis-select a quantile.
        if isinstance(self.peak_m3_s, int) and abs(self.peak_m3_s) > (1 << 53):
            _fail("Unrepresentable integer peak exceeds the exact binary64 range")
        if self.status == "valid":
            if (
                self.event_id is None
                or self.effective_input_id is None
                or self.peak_m3_s is None
                or not _finite_real(self.peak_m3_s)
                or self.peak_m3_s < 0
            ):
                _fail("Valid peaks require finite nonnegative flow and replayable event/input IDs")
        elif self.peak_m3_s is not None:
            _fail("Failed/missing/unsupported rows must not carry an accepted peak")


@dataclass(frozen=True, slots=True)
class StratumAccounting:
    stratum_id: str
    probability_mass: float
    planned_samples: int
    observed_samples: int
    valid_zero_samples: int
    valid_positive_samples: int
    failed_samples: int
    explicit_missing_samples: int
    absent_samples: int
    unsupported_samples: int
    sample_probability_weight: float | None


@dataclass(frozen=True, slots=True)
class ProbabilityCoverage:
    """Absolute probability masses, not conditional on successful computations."""

    valid_mass: float
    zero_mass: float
    positive_mass: float
    failed_mass: float
    missing_mass: float
    unsupported_mass: float
    unallocated_stratum_mass: float
    tails: UnmodelledTails

    @property
    def unresolved_mass(self) -> float:
        return math.fsum(
            (
                self.failed_mass,
                self.missing_mass,
                self.unsupported_mass,
                self.unallocated_stratum_mass,
                self.tails.total,
            )
        )

    @property
    def complete(self) -> bool:
        return self.unresolved_mass == 0.0


@dataclass(frozen=True, slots=True)
class WeightedPeak:
    record: PeakRecord
    weight: float


@dataclass(frozen=True, slots=True)
class PeakGroup:
    """One attained peak and its absolute probability mass (exact ties combined)."""

    peak_m3_s: float
    probability_mass: float
    cumulative_mass: float


@dataclass(frozen=True, slots=True)
class ExceedanceBounds:
    threshold_m3_s: float
    known_exceedance_probability: float
    lower_probability: float
    upper_probability: float
    unresolved_probability_mass: float
    boundary_strata_known_exceedance_probability: float
    boundary_strata_share_of_known_exceedance: float | None


@dataclass(frozen=True, slots=True)
class RepresentativeEvent:
    sample_id: str
    event_id: str
    effective_input_id: str
    stratum_id: str
    realised_peak_m3_s: float
    target_peak_m3_s: float
    signed_mismatch_m3_s: float
    absolute_mismatch_m3_s: float


@dataclass(frozen=True, slots=True)
class IntervalContribution:
    """An ARR Total Probability Theorem component at a *strict* peak threshold."""

    stratum_id: str
    exceeding_samples: int
    strict_exceedance_probability_mass: float


@dataclass(frozen=True, slots=True)
class IntervalContributionAudit:
    """Descriptive conditional exceedance contributions, NOT a reliability test."""

    known_strict_exceedance_probability: float
    maximum_stratum_id: str | None
    maximum_stratum_share_of_known_exceedance: float | None
    strata: tuple[IntervalContribution, ...]
    method: str = INTERVAL_AUDIT_METHOD
    native_equivalence: Literal["not_assessed"] = "not_assessed"


@dataclass(frozen=True, slots=True)
class ScientificSamplingDiagnostic:
    """Conservative uniform-in-q probability screen; NOT a flood-quantile confidence interval."""

    status: ScientificScreenStatus
    confidence_level: float
    relative_aep_screen: float
    simultaneous_absolute_aep_margin: float | None
    margin_relative_to_target_aep: float | None
    maximum_single_sample_probability_weight: float | None
    maximum_sample_weight_relative_to_target_aep: float | None
    reason: str
    method: str = SCIENTIFIC_SCREEN_METHOD
    assumptions: str = "iid_within_each_rainfall_stratum_conditional_on_fixed_project_distribution"
    independent_seed_convergence: Literal["not_assessed"] = "not_assessed"
    boundary_sensitivity: Literal["not_assessed"] = "not_assessed"
    native_equivalence: Literal["not_assessed"] = "not_assessed"


@dataclass(frozen=True, slots=True)
class QuantileEstimate:
    aep: float
    status: QuantileStatus
    peak_m3_s: float | None
    lower_bound_m3_s: float | None
    upper_bound_m3_s: float | None
    representative: RepresentativeEvent | None
    boundary_strata_known_exceedance_probability: float | None
    boundary_strata_share_of_known_exceedance: float | None
    at_observed_support_edge: bool
    method: str = METHOD_PROFILE
    software_qualification: Literal["provisional"] = "provisional"
    statistical_qualification: Literal["not_assessed"] = "not_assessed"
    native_equivalence: Literal["not_assessed"] = "not_assessed"
    interval_probability_audit: IntervalContributionAudit | None = None
    scientific_sampling_diagnostic: ScientificSamplingDiagnostic | None = None
    native_interval_warning: Literal["not_assessed"] = "not_assessed"


@dataclass(frozen=True, slots=True)
class FrequencyCurve:
    scope: FrequencyScope
    accounting: tuple[StratumAccounting, ...]
    coverage: ProbabilityCoverage
    groups: tuple[PeakGroup, ...]
    positive_weight_observations: tuple[WeightedPeak, ...]
    method: str = METHOD_PROFILE

    def exceedance(self, threshold_m3_s: float) -> ExceedanceBounds:
        """Absolute strict S(q) and unresolved/boundary-stratum contributions."""
        if not _finite_real(threshold_m3_s):
            _fail("Exceedance threshold must be finite")
        if threshold_m3_s < 0:
            active = self.positive_weight_observations
            known = self.coverage.valid_mass
            lower, upper = 1.0, 1.0  # All unsupported/unknown flow is also nonnegative.
        else:
            active = tuple(
                item
                for item in self.positive_weight_observations
                if item.record.peak_m3_s is not None and item.record.peak_m3_s > threshold_m3_s
            )
            known = math.fsum(item.weight for item in active)
            lower, upper = known, min(1.0, math.fsum((known, self.coverage.unresolved_mass)))
        boundary_ids = {self.accounting[0].stratum_id, self.accounting[-1].stratum_id}
        boundary = math.fsum(item.weight for item in active if item.record.stratum_id in boundary_ids)
        return ExceedanceBounds(
            threshold_m3_s,
            known,
            lower,
            upper,
            self.coverage.unresolved_mass,
            boundary,
            boundary / known if known else None,
        )

    def _interval_probability_audit(self, peak: float) -> IntervalContributionAudit:
        """Break the strict ARR/TPT survival probability into original rainfall strata."""
        counts: Counter[str] = Counter(
            item.record.stratum_id
            for item in self.positive_weight_observations
            if item.record.peak_m3_s is not None and item.record.peak_m3_s > peak
        )
        parts: list[tuple[str, Fraction, int]] = []
        for allocation in self.accounting:
            count = counts[allocation.stratum_id]
            mass = (
                Fraction(str(allocation.probability_mass)) * count / allocation.planned_samples
                if allocation.planned_samples > 0
                else Fraction(0)
            )
            parts.append((allocation.stratum_id, mass, count))
        total = sum((part[1] for part in parts), Fraction(0))
        largest = max(parts, key=lambda part: part[1]) if total > 0 else None
        return IntervalContributionAudit(
            float(total),
            largest[0] if largest is not None else None,
            float(largest[1] / total) if largest is not None else None,
            tuple(IntervalContribution(name, count, float(mass)) for name, mass, count in parts),
        )

    def _scientific_sampling_screen(
        self, aep: float, confidence_level: float, relative_aep_screen: float
    ) -> ScientificSamplingDiagnostic:
        """Simultaneous stratified DKW bound; independent iid draws WITHIN strata required.

        Union-bound the conditional DKW inequalities across positive-weight
        intervals. Weighted summation bounds the supremum of the full CDF
        error over all Q, including data-selected quantiles. Not a flow
        quantile interval or evidence of correctness of the hydrological model.
        """
        if not self.coverage.complete:
            return ScientificSamplingDiagnostic(
                "not_assessed",
                confidence_level,
                relative_aep_screen,
                None,
                None,
                None,
                None,
                "unresolved_probability_mass",
            )
        active = tuple(item for item in self.accounting if item.probability_mass > 0)
        if not active or any(item.planned_samples <= 0 for item in active):
            return ScientificSamplingDiagnostic(
                "not_assessed", confidence_level, relative_aep_screen, None, None, None, None, "unallocated_stratum"
            )
        log_term = math.log(2 * len(active) / (1 - confidence_level))
        bound = min(
            1.0,
            math.fsum(
                item.probability_mass * min(1.0, math.sqrt(log_term / (2 * item.planned_samples))) for item in active
            ),
        )
        resolution = max(item.probability_mass / item.planned_samples for item in active)
        relative = bound / aep
        relative_resolution = resolution / aep
        status: ScientificScreenStatus = "review" if relative > relative_aep_screen else "below_screen"
        # Very small positive AEPs can overflow the relative display ratio.
        # The absolute probability bound remains finite and authoritative.
        return ScientificSamplingDiagnostic(
            status,
            confidence_level,
            relative_aep_screen,
            bound,
            relative if math.isfinite(relative) else None,
            resolution,
            relative_resolution if math.isfinite(relative_resolution) else None,
            "conditional_iid_sampling_assumption_not_independently_qualified",
        )

    def estimate(
        self,
        aep: float,
        *,
        confidence_level: float = DEFAULT_SAMPLING_CONFIDENCE,
        relative_aep_screen: float = DEFAULT_RELATIVE_AEP_SCREEN,
    ) -> QuantileEstimate:
        """Adopted #145 weighted noninterpolating generalized inverse on attained peaks.

        This is an empirical *finite-ledger* estimate. Unresolved mass returns
        nonnegative-support bounds, never a renormalised conditional quantile.
        No IID confidence interval or smooth/extrapolated quantile is implied.
        """
        _probability(aep, "AEP")
        _probability(confidence_level, "sampling confidence level")
        if not 0 < confidence_level < 1:
            _fail("sampling confidence level must be strictly between 0 and 1")
        if not _finite_real(relative_aep_screen) or relative_aep_screen <= 0:
            _fail("relative AEP screen must be a finite positive number")
        if not 0 < aep < 1:
            _fail("AEP must be strictly inside (0, 1)")
        # Convert the public decimal probability values into exact rationals.
        # Binary float 1.0 - aep and cumulatively summed w_h/n_h can disagree
        # at the very same step boundary, selecting an adjacent WRONG peak.
        nonexceedance = Fraction(1) - Fraction(str(aep))
        steps = _exact_cumulative_steps(self)
        if not self.coverage.complete:
            unresolved = _exact_unresolved_mass(self.accounting, self.coverage.tails)
            lower, upper = _incomplete_bounds(steps, nonexceedance, unresolved)
            return QuantileEstimate(
                aep,
                "incomplete",
                None,
                lower,
                upper,
                None,
                None,
                None,
                False,
                scientific_sampling_diagnostic=self._scientific_sampling_screen(
                    aep, confidence_level, relative_aep_screen
                ),
            )
        if not self.groups:
            _fail("Complete populations must contain positive-weight observed peaks")
        peak = _inverse_step(steps, nonexceedance)
        if peak is None:
            # A complete plan can sum to one only within the documented
            # 1e-12 float-input mass tolerance. Return its last *attained*
            # peak rather than inventing any higher flow or missing tail.
            peak = self.groups[-1].peak_m3_s
        at_edge = peak in (self.groups[0].peak_m3_s, self.groups[-1].peak_m3_s)
        return self._result(
            aep, peak, "zero_atom" if peak == 0 else "estimated", at_edge, confidence_level, relative_aep_screen
        )

    def _result(
        self,
        aep: float,
        peak: float,
        status: QuantileStatus,
        at_edge: bool,
        confidence_level: float,
        relative_aep_screen: float,
    ) -> QuantileEstimate:
        selected = min(
            self.positive_weight_observations,
            key=lambda item: (
                abs(float(item.record.peak_m3_s or 0) - peak),
                item.record.sample_id,
                item.record.event_id or "",
            ),
        ).record
        actual = float(selected.peak_m3_s or 0)
        representative = RepresentativeEvent(
            selected.sample_id,
            selected.event_id or "",
            selected.effective_input_id or "",
            selected.stratum_id,
            actual,
            peak,
            actual - peak,
            abs(actual - peak),
        )
        evidence = self.exceedance(peak)
        return QuantileEstimate(
            aep,
            status,
            peak,
            None,
            None,
            representative,
            evidence.boundary_strata_known_exceedance_probability,
            evidence.boundary_strata_share_of_known_exceedance,
            at_edge,
            interval_probability_audit=self._interval_probability_audit(peak),
            scientific_sampling_diagnostic=self._scientific_sampling_screen(aep, confidence_level, relative_aep_screen),
        )


def _exact_cumulative_steps(curve: FrequencyCurve) -> tuple[tuple[float, Fraction], ...]:
    """Recreate exact planned w_h/n_h masses; group counts before inversion.

    The float API's shortest-roundtrip decimal strings represent plan inputs.
    Group probabilities in public output may remain rounded for display.
    """
    units = {
        row.stratum_id: Fraction(str(row.probability_mass)) / row.planned_samples
        for row in curve.accounting
        if row.planned_samples > 0 and row.probability_mass > 0
    }
    counts: dict[float, Counter[str]] = defaultdict(Counter)
    for item in curve.positive_weight_observations:
        peak = item.record.peak_m3_s
        if peak is None:
            _fail("Valid weighted observation has no peak")
        counts[peak][item.record.stratum_id] += 1

    cumulative = Fraction(0)
    steps: list[tuple[float, Fraction]] = []
    for group in curve.groups:
        cumulative += sum(
            (units[stratum] * count for stratum, count in counts[group.peak_m3_s].items()),
            Fraction(0),
        )
        steps.append((group.peak_m3_s, cumulative))
    return tuple(steps)


def _exact_unresolved_mass(accounting: tuple[StratumAccounting, ...], tails: UnmodelledTails) -> Fraction:
    """Keep all failed/missing/unsupported/unallocated/tail probability on its original scale."""
    unresolved = sum(
        (Fraction(str(value)) for value in (tails.lower_rainfall_mass, tails.upper_rainfall_mass, tails.other_mass)),
        Fraction(0),
    )
    for row in accounting:
        mass = Fraction(str(row.probability_mass))
        if row.planned_samples == 0:
            unresolved += mass
        else:
            missing = row.failed_samples + row.explicit_missing_samples + row.absent_samples + row.unsupported_samples
            unresolved += mass * missing / row.planned_samples
    return unresolved


def _inverse_step(steps: tuple[tuple[float, Fraction], ...], probability: Fraction) -> float | None:
    if probability <= 0:
        return 0.0
    for peak, cumulative in steps:
        if cumulative >= probability:
            return peak
    return None


def _incomplete_bounds(
    steps: tuple[tuple[float, Fraction], ...], nonexceedance: Fraction, unresolved: Fraction
) -> tuple[float | None, float | None]:
    """All unknown nonnegative peaks at zero versus infinity; exact step selection."""
    lower = 0.0 if nonexceedance <= unresolved else _inverse_step(steps, nonexceedance - unresolved)
    upper = _inverse_step(steps, nonexceedance)
    return lower, upper


def _planned_records(population: CurvePopulation, records: Iterable[PeakRecord]) -> dict[str, list[PeakRecord]]:
    """Validate the complete current plan revision before calculating weights."""
    strata = {entry.stratum_id: entry for entry in population.strata}
    by_stratum: dict[str, list[PeakRecord]] = defaultdict(list)
    seen_samples: set[str] = set()
    seen_events: set[str] = set()
    for record in records:
        if record.scope != population.scope:
            _fail("Mismatched plan, policy, scenario, duration or physical output-site identity")
        if record.stratum_id not in strata:
            _fail("Peak refers to a stratum outside the immutable plan")
        if record.sample_id in seen_samples:
            _fail("Duplicate sample identifier in the same curve")
        seen_samples.add(record.sample_id)
        if record.event_id is not None:
            if record.event_id in seen_events:
                _fail("Duplicate event identifier in the same curve")
            seen_events.add(record.event_id)
        entry = strata[record.stratum_id]
        expected = entry.probability_mass / entry.planned_samples if entry.planned_samples else None
        if expected is None or not math.isclose(record.event_probability_weight, expected, rel_tol=1e-12, abs_tol=0.0):
            _fail("Stale or mixed plan-revision event weights; reaggregate using the complete current plan")
        by_stratum[record.stratum_id].append(record)
    return by_stratum


def _account_observations(
    population: CurvePopulation, by_stratum: dict[str, list[PeakRecord]]
) -> tuple[tuple[StratumAccounting, ...], list[WeightedPeak], ProbabilityCoverage]:
    """Retain planned denominators, zero outcomes and every unresolved mass."""
    accounting: list[StratumAccounting] = []
    weighted: list[WeightedPeak] = []
    failed: list[float] = []
    missing: list[float] = []
    unsupported: list[float] = []
    unallocated: list[float] = []
    for stratum in population.strata:
        entries = by_stratum[stratum.stratum_id]
        n = stratum.planned_samples
        if len(entries) > n:
            _fail("More observed samples than the planned stratum allocation")
        unit = stratum.probability_mass / n if n else None
        if unit is None:
            unallocated.append(stratum.probability_mass)
        counts = {
            status: sum(item.status == status for item in entries)
            for status in ("valid", "failed", "missing", "unsupported")
        }
        absent = n - len(entries)
        valid = tuple(item for item in entries if item.status == "valid")
        valid_zeros = sum(item.peak_m3_s == 0 for item in valid)
        valid_positive = len(valid) - valid_zeros
        if unit is not None:
            weighted.extend(WeightedPeak(item, unit) for item in valid if unit > 0)
            failed.append(counts["failed"] * unit)
            missing.append((counts["missing"] + absent) * unit)
            unsupported.append(counts["unsupported"] * unit)
        accounting.append(
            StratumAccounting(
                stratum.stratum_id,
                stratum.probability_mass,
                n,
                len(entries),
                valid_zeros,
                valid_positive,
                counts["failed"],
                counts["missing"],
                absent,
                counts["unsupported"],
                unit,
            )
        )
    zero_mass = math.fsum(item.weight for item in weighted if item.record.peak_m3_s == 0)
    coverage = ProbabilityCoverage(
        math.fsum(item.weight for item in weighted),
        zero_mass,
        math.fsum(item.weight for item in weighted if item.record.peak_m3_s != 0),
        math.fsum(failed),
        math.fsum(missing),
        math.fsum(unsupported),
        math.fsum(unallocated),
        population.tails,
    )
    return tuple(accounting), weighted, coverage


def _group_peaks(weighted: list[WeightedPeak]) -> tuple[PeakGroup, ...]:
    """Merge exact numeric ties while retaining the original individual samples."""
    weighted.sort(key=lambda item: (float(item.record.peak_m3_s or 0), item.record.sample_id))
    groups: list[PeakGroup] = []
    total = 0.0
    position = 0
    while position < len(weighted):
        peak = float(weighted[position].record.peak_m3_s or 0)
        end = position + 1
        while end < len(weighted) and weighted[end].record.peak_m3_s == peak:
            end += 1
        mass = math.fsum(item.weight for item in weighted[position:end])
        new_total = math.fsum((total, mass))
        groups.append(PeakGroup(peak, mass, new_total))
        total = new_total
        position = end
    return tuple(groups)


def build_frequency_curve(population: CurvePopulation, records: Iterable[PeakRecord]) -> FrequencyCurve:
    """Aggregate exactly the planned samples for ONE scope, ignoring input ordering."""
    by_stratum = _planned_records(population, records)
    accounting, weighted, coverage = _account_observations(population, by_stratum)
    return FrequencyCurve(population.scope, accounting, coverage, _group_peaks(weighted), tuple(weighted))


def build_frequency_curves(
    populations: Iterable[CurvePopulation], records: Iterable[PeakRecord]
) -> tuple[FrequencyCurve, ...]:
    """Build site/duration/scenario curves first; never pool these populations."""
    by_scope: dict[FrequencyScope, CurvePopulation] = {}
    for population in populations:
        if population.scope in by_scope:
            _fail("Duplicate curve population scope")
        by_scope[population.scope] = population
    ledger: dict[FrequencyScope, list[PeakRecord]] = defaultdict(list)
    for record in records:
        if record.scope not in by_scope:
            _fail("A peak ledger row has no matching planned population")
        ledger[record.scope].append(record)
    return tuple(
        build_frequency_curve(population, ledger[scope])
        for scope, population in sorted(
            by_scope.items(),
            key=lambda entry: (
                entry[0].scenario_id,
                entry[0].output_site_id,
                entry[0].duration_minutes,
                entry[0].plan_id,
            ),
        )
    )


@dataclass(frozen=True, slots=True)
class DurationEnvelope:
    scenario_id: str
    policy_id: str
    policy_version: str
    output_site_id: str
    aep: float
    status: QuantileStatus
    peak_m3_s: float | None
    critical_duration_minutes: int | None
    representative: RepresentativeEvent | None
    lower_bound_m3_s: float | None
    upper_bound_m3_s: float | None
    margin_to_second_m3_s: float | None
    tied_critical_durations_minutes: tuple[int, ...]
    duration_estimates: tuple[tuple[int, QuantileEstimate], ...]
    software_qualification: Literal["provisional"] = "provisional"
    statistical_qualification: Literal["not_assessed"] = "not_assessed"
    native_equivalence: Literal["not_assessed"] = "not_assessed"


def duration_envelope(curves: Iterable[FrequencyCurve], aep: float) -> DurationEnvelope:
    """Maximum of separate duration quantiles; requested order breaks exact ties."""
    source = tuple(curves)
    if not source:
        _fail("Duration envelope needs at least one curve")
    first = source[0].scope
    if any(
        item.scope.scenario_id != first.scenario_id
        or item.scope.policy_id != first.policy_id
        or item.scope.policy_version != first.policy_version
        or item.scope.output_site_id != first.output_site_id
        for item in source
    ):
        _fail("Duration envelope must not combine different scenarios, policies or sites")
    if len({item.scope.duration_minutes for item in source}) != len(source):
        _fail("Duplicate duration in duration envelope")
    estimates = tuple((curve.scope.duration_minutes, curve.estimate(aep)) for curve in source)
    available = [(duration, estimate) for duration, estimate in estimates if estimate.peak_m3_s is not None]
    if len(available) != len(estimates):
        state: QuantileStatus = "incomplete"
        lower_candidates = [
            item.peak_m3_s if item.peak_m3_s is not None else item.lower_bound_m3_s for _, item in estimates
        ]
        upper_candidates = [
            item.peak_m3_s if item.peak_m3_s is not None else item.upper_bound_m3_s for _, item in estimates
        ]
        lower_values = [value for value in lower_candidates if value is not None]
        upper_values = [value for value in upper_candidates if value is not None]
        lower = max(lower_values) if len(lower_values) == len(lower_candidates) else None
        upper = max(upper_values) if len(upper_values) == len(upper_candidates) else None
        return DurationEnvelope(
            first.scenario_id,
            first.policy_id,
            first.policy_version,
            first.output_site_id,
            aep,
            state,
            None,
            None,
            None,
            lower,
            upper,
            None,
            (),
            estimates,
        )
    ranked = sorted(enumerate(available), key=lambda pair: (-float(pair[1][1].peak_m3_s or 0), pair[0]))
    selected_duration, selected = ranked[0][1]
    selected_peak = float(selected.peak_m3_s or 0)
    runner_up = float(ranked[1][1][1].peak_m3_s or 0) if len(ranked) > 1 else None
    tied = tuple(duration for duration, item in available if item.peak_m3_s == selected_peak)
    return DurationEnvelope(
        first.scenario_id,
        first.policy_id,
        first.policy_version,
        first.output_site_id,
        aep,
        selected.status,
        selected_peak,
        selected_duration,
        selected.representative,
        None,
        None,
        selected_peak - runner_up if runner_up is not None else None,
        tied,
        estimates,
    )
