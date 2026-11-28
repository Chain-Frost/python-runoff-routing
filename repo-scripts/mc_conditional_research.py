"""Read-only #148 conditional research aggregation; not the production flood estimator."""

from __future__ import annotations

import math
from bisect import bisect_left, bisect_right
from collections.abc import Iterable, Mapping
from decimal import Decimal
from fractions import Fraction
from itertools import accumulate, pairwise
from pathlib import Path
from typing import Literal, NamedTuple, Never, cast

DOMAIN = Fraction(49, 100)
MAX_DRAWS = 1_000_000
UNKNOWN_STATUSES = {
    "unsupported_feature",
    "unavailable_engine",
    "invalid_input",
    "numerical_error",
    "incomplete_output",
    "native_execution_failed",
}


class Artifact(NamedTuple):
    """Externally pinned immutable artifact, not a self-authenticating hash."""

    path: Path
    sha256: str


class ConditionalCurve(NamedTuple):
    """Logical finite-ledger bounds, not population confidence intervals."""

    known: tuple[tuple[Fraction, Fraction], ...]
    cumulative: tuple[Fraction, ...]
    unknown_mass: Fraction
    status_counts: dict[str, int]
    planned_count: int

    def cdf(self, threshold: Fraction) -> tuple[Fraction, Fraction]:
        """Conditional CDF bounds at a finite nonnegative flow threshold."""
        threshold = _require_fraction(threshold, "CDF threshold must be an exact fraction")
        if threshold < 0:
            _fail("Expected a nonnegative threshold")
        index = bisect_right(self.known, (threshold, DOMAIN))
        observed = self.cumulative[index - 1] if index else Fraction(0)
        return observed / DOMAIN, (observed + self.unknown_mass) / DOMAIN

    def survival(self, threshold: Fraction) -> tuple[Fraction, Fraction]:
        """Strict exceedance, including ties and exact zero."""
        lower, upper = self.cdf(threshold)
        return 1 - upper, 1 - lower

    def quantile(self, exceedance: Fraction) -> tuple[Fraction, Fraction | None]:
        """Attained inverse bounds; None means no finite upper bound."""
        exceedance = _require_fraction(exceedance, "Conditional exceedance must be an exact fraction")
        if not 0 < exceedance < 1:
            _fail("Conditional response exceedance must be inside (0,1)")
        target = DOMAIN * (1 - exceedance)
        lower = Fraction(0) if self.unknown_mass >= target else self._inverse(target - self.unknown_mass)
        if lower is None:
            _fail("Inconsistent conditional ledger mass")
        return lower, self._inverse(target)

    def _inverse(self, target: Fraction) -> Fraction | None:
        index = bisect_left(self.cumulative, target)
        return self.known[index][0] if index < len(self.known) else None


def _fail(message: str) -> Never:
    raise ValueError(message)


def _require_fraction(value: object, message: str) -> Fraction:
    if not isinstance(value, Fraction):
        _fail(message)
    return value


def _allocations(allocations: Mapping[str, tuple[Decimal, int]]) -> dict[str, tuple[Fraction, int]]:
    result: dict[str, tuple[Fraction, int]] = {}
    for key, (mass, count) in allocations.items():
        if not key or not mass.is_finite() or not 0 < mass <= 1:
            _fail("Invalid stratum identity or mass")
        if type(count) is not int or not 0 < count <= MAX_DRAWS:
            _fail("Every positive-mass stratum needs a bounded positive planned allocation")
        result[key] = (Fraction(mass), count)
    if sum((mass for mass, _ in result.values()), Fraction(0)) != DOMAIN:
        _fail("Expected exact restricted rainfall mass 0.49")
    if sum(count for _, count in result.values()) > MAX_DRAWS:
        _fail("Planned draw cap exceeded")
    return result


def _site_peak(row: dict[str, object], site_id: str) -> tuple[str, Fraction | None]:
    status = row.get("status")
    if not isinstance(status, str):
        _fail("Missing verified result status")
    if status in UNKNOWN_STATUSES:
        return status, None
    if status != "computed_unvalidated":
        _fail("Unexpected verified result status")
    return _computed_peak(row, site_id)


def _computed_peak(row: dict[str, object], site_id: str) -> tuple[str, Fraction | None]:
    sites = row.get("sites")
    if not isinstance(sites, list):
        _fail("Missing computed site list")
    matches: list[dict[str, object]] = []
    for site in cast("list[object]", sites):
        if not isinstance(site, dict):
            _fail("Malformed computed site record")
        entry = cast("dict[str, object]", site)
        if entry.get("print_id") == site_id:
            matches.append(entry)
    if not matches:
        return "missing_site", None
    if len(matches) != 1:
        _fail("Ambiguous computed site identity")
    return "valid", _peak(matches[0].get("peak_m3_s"))


def _peak(peak: object) -> Fraction:
    if not isinstance(peak, (int, float)) or isinstance(peak, bool) or peak < 0:
        _fail("Invalid computed site peak")
    if isinstance(peak, float) and not math.isfinite(peak):
        _fail("Nonfinite computed site peak")
    return Fraction(peak)


def _row_identity(row: dict[str, object], scenario: str, duration: int) -> tuple[str, str]:
    if row.get("scenario_id") != scenario or row.get("duration_min") != duration:
        _fail("Mixed scenario or duration in conditional cohort")
    sample, stratum = row.get("sample_id"), row.get("stratum_id")
    if not isinstance(sample, str) or not sample or not isinstance(stratum, str) or not stratum:
        _fail("Missing verified sample or stratum identity")
    return sample, stratum


def conditional_curve(
    allocations: Mapping[str, tuple[Decimal, int]],
    rows: Iterable[dict[str, object]],
    *,
    scenario: str,
    duration: int,
    site_id: str,
) -> ConditionalCurve:
    """Consume a FULL verified prefix; use exact allocation masses, never rounded row weights.

    Caller must establish the row identities against the immutable plan. Empty rows
    represent a wholly unknown planned cohort, not evidence of zero discharge.
    Bounds assume a defined nonnegative latent response, not a scientific admission.
    """
    if not scenario or not site_id or type(duration) is not int or duration <= 0:
        _fail("Invalid cohort scope")
    planned = _allocations(allocations)
    total = sum(count for _, count in planned.values())
    seen: set[str] = set()
    counts: dict[str, int] = dict.fromkeys(planned, 0)
    statuses: dict[str, int] = {}
    groups: dict[Fraction, Fraction] = {}
    for row in rows:
        sample, stratum = _row_identity(row, scenario, duration)
        if sample in seen or stratum not in planned:
            _fail("Duplicate sample or undeclared stratum")
        seen.add(sample)
        mass, count = planned[stratum]
        counts[stratum] += 1
        if counts[stratum] > count:
            _fail("Recorded rows exceed planned allocation")
        status, peak = _site_peak(row, site_id)
        statuses[status] = statuses.get(status, 0) + 1
        if peak is not None:
            groups[peak] = groups.get(peak, Fraction(0)) + mass / count
    statuses["unrecorded"] = total - len(seen)
    known = tuple(sorted(groups.items()))
    cumulative = tuple(accumulate(mass for _, mass in known))
    unknown = DOMAIN - (cumulative[-1] if cumulative else Fraction(0))
    return ConditionalCurve(known, cumulative, unknown, statuses, total)


def read_verified_cohort(
    project: Artifact,
    request: Artifact,
    ledger: Artifact,
    *,
    site_id: str,
    wheel: Artifact | None = None,
) -> ConditionalCurve:
    """Read one already-recorded Python CMD cohort; never execute or write anything.

    Pins must come from external immutable custody. An entirely unstarted cohort
    has no verified ledger; use the pure kernel only after plan admission.
    """
    # Keep standalone mathematical controls usable without the product installed.
    from runoff_routing.monte_carlo_effective import read_header, sha256_file  # noqa: PLC0415
    from runoff_routing.monte_carlo_execution import iter_verified_mc_results  # noqa: PLC0415
    from runoff_routing.project_json import load_project  # noqa: PLC0415

    artifacts = (project, request, ledger) if wheel is None else (project, request, ledger, wheel)

    def verify() -> None:
        for artifact in artifacts:
            if sha256_file(artifact.path) != artifact.sha256:
                _fail("Externally pinned artifact digest mismatch")

    verify()
    header = read_header(request.path)
    if len(header.populations) != 1 or not header.strata or header.policy_id != "monte-carlo-statistics/1":
        _fail("Expected one explicit v1 scenario/duration population")
    pop = header.populations[0]
    if (pop.modelled_mass, pop.rare_unmodelled_mass, pop.frequent_unmodelled_mass) != (
        Decimal("0.49"),
        Decimal("0.01"),
        Decimal("0.50"),
    ):
        _fail("Expected fixed restricted support and explicit excluded tails")
    loaded = load_project(project.path)
    engine = loaded.project.engine
    if (engine.engine, engine.numerical_profile) != ("python-cmd", "cmd-6.44"):
        _fail("Expected stored Python CMD profile")
    sites = tuple(item.identifier for item in loaded.run.catchment.print_locations)
    if sites.count(site_id) != 1:
        _fail("Unknown or ambiguous project print ID")
    allocations = {item.stratum_id: (item.probability_mass, item.planned_samples) for item in header.strata}
    if len(allocations) != len(header.strata):
        _fail("Duplicate header stratum identity")
    rows = iter_verified_mc_results(
        project.path, request.path, ledger.path, wheel_artifact=None if wheel is None else wheel.path
    )
    curve = conditional_curve(allocations, rows, scenario=pop.scenario_id, duration=pop.duration_min, site_id=site_id)
    verify()
    return curve


class CohortScope(NamedTuple):
    """Common externally admitted scope for equal-allocation paired cohorts."""

    project_sha256: str
    wheel_sha256: str
    scenario: str
    duration: int
    site_ids: tuple[str, str]
    allocations: tuple[tuple[str, Decimal, int], ...]


class PairedCohort(NamedTuple):
    """Two marginals from the same pinned, verified event prefix."""

    plan_sha256: str
    request_sha256: str
    ledger_sha256: str
    scope: CohortScope
    curves: tuple[ConditionalCurve, ConditionalCurve]


def _check_digest(value: str) -> None:
    if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        _fail("Expected a canonical SHA-256 identity")


def _check_plan_ids(plan_ids: tuple[str, ...]) -> None:
    if not plan_ids or len(set(plan_ids)) != len(plan_ids):
        _fail("Expected distinct preassigned plan identities")
    for identity in plan_ids:
        _check_digest(identity)


def _scope_count(scope: CohortScope) -> int:
    _check_digest(scope.project_sha256)
    _check_digest(scope.wheel_sha256)
    if not scope.scenario or type(scope.duration) is not int or scope.duration <= 0:
        _fail("Invalid paired cohort scope")
    if len(scope.site_ids) != 2 or len(set(scope.site_ids)) != 2 or not all(scope.site_ids):
        _fail("Expected two distinct paired print IDs")
    allocations = {key: (mass, count) for key, mass, count in scope.allocations}
    if len(allocations) != len(scope.allocations):
        _fail("Duplicate paired cohort stratum")
    return sum(count for _, count in _allocations(allocations).values())


def read_verified_pair(
    project: Artifact,
    request: Artifact,
    ledger: Artifact,
    *,
    site_ids: tuple[str, str],
    wheel: Artifact,
) -> PairedCohort:
    """Read both sites from one immutable prefix using the existing verified reader.

    The two passes deliberately avoid caching a full ledger in memory. The
    caller must independently pin artifacts and establish preassigned plan/root
    membership, source law, and feature eligibility. No execution is performed.
    """
    # Keep standalone research controls usable without the product installed.
    from runoff_routing.monte_carlo_effective import read_header, sha256_file  # noqa: PLC0415

    if sha256_file(request.path) != request.sha256:
        _fail("Externally pinned artifact digest mismatch")
    header = read_header(request.path)
    if len(header.populations) != 1:
        _fail("Expected one explicit paired cohort population")
    pop = header.populations[0]
    allocations = tuple(sorted((a.stratum_id, a.probability_mass, a.planned_samples) for a in header.strata))
    scope = CohortScope(project.sha256, wheel.sha256, pop.scenario_id, pop.duration_min, site_ids, allocations)
    _scope_count(scope)
    _check_digest(header.plan_sha256)
    first = read_verified_cohort(project, request, ledger, site_id=site_ids[0], wheel=wheel)
    second = read_verified_cohort(project, request, ledger, site_id=site_ids[1], wheel=wheel)
    if sha256_file(request.path) != request.sha256:
        _fail("Externally pinned artifact digest mismatch")
    return PairedCohort(header.plan_sha256, request.sha256, ledger.sha256, scope, (first, second))


def _check_curve(curve: ConditionalCurve, planned_count: int) -> None:
    if curve.planned_count != planned_count or sum(curve.status_counts.values()) != planned_count:
        _fail("Curve status counts do not match the planned cohort")
    if any(type(count) is not int or count < 0 for count in curve.status_counts.values()):
        _fail("Invalid curve status counts")
    for peak, mass in curve.known:
        _require_fraction(peak, "Curve peak must be an exact fraction")
        _require_fraction(mass, "Curve mass must be an exact fraction")
        if peak < 0 or not 0 < mass <= DOMAIN:
            _fail("Invalid curve group")
    if any(left[0] >= right[0] for left, right in pairwise(curve.known)):
        _fail("Curve peak keys must be strictly increasing")
    cumulative = tuple(accumulate(mass for _, mass in curve.known))
    _require_fraction(curve.unknown_mass, "Unknown mass must be an exact fraction")
    known_total = cumulative[-1] if cumulative else Fraction(0)
    if curve.cumulative != cumulative or curve.unknown_mass != DOMAIN - known_total:
        _fail("Inconsistent curve mass accounting")
    if not 0 <= curve.unknown_mass <= DOMAIN:
        _fail("Invalid curve unknown mass")


def _pool_site(
    curves: Iterable[ConditionalCurve],
    planned_cohorts: int,
    draws_per_cohort: int,
) -> ConditionalCurve:
    groups: dict[Fraction, Fraction] = {}
    statuses: dict[str, int] = {}
    observed = 0
    for curve in curves:
        _check_curve(curve, draws_per_cohort)
        observed += 1
        for peak, mass in curve.known:
            groups[peak] = groups.get(peak, Fraction(0)) + mass
        for status, count in curve.status_counts.items():
            statuses[status] = statuses.get(status, 0) + count
    missing = (planned_cohorts - observed) * draws_per_cohort
    statuses["unrecorded"] = statuses.get("unrecorded", 0) + missing
    known = tuple((peak, mass / planned_cohorts) for peak, mass in sorted(groups.items()))
    cumulative = tuple(accumulate(mass for _, mass in known))
    unknown = DOMAIN - (cumulative[-1] if cumulative else Fraction(0))
    return ConditionalCurve(known, cumulative, unknown, statuses, planned_cohorts * draws_per_cohort)


def pool_paired_cohorts(
    scope: CohortScope,
    planned_plan_ids: tuple[str, ...],
    observed: Iterable[PairedCohort],
) -> tuple[ConditionalCurve, ConditionalCurve]:
    """Pool equal-stratum-count cohorts using all preassigned slots, including absences.

    Only verified pairs in the same exact scope may be supplied. The plan IDs
    must come from an independently admitted stage manifest; equal scope and
    distinct hashes alone do not prove identical source laws or independent roots.
    """
    _check_plan_ids(planned_plan_ids)
    count = _scope_count(scope)
    if count * len(planned_plan_ids) > MAX_DRAWS:
        _fail("Pooled planned draw cap exceeded")
    expected = set(planned_plan_ids)
    seen: set[str] = set()
    requests: set[str] = set()
    ledgers: set[str] = set()
    pairs: list[PairedCohort] = []
    for pair in observed:
        if pair.plan_sha256 not in expected or pair.plan_sha256 in seen:
            _fail("Duplicate or unplanned cohort identity")
        if pair.scope != scope or len(pair.curves) != 2:
            _fail("Mismatched paired cohort scope or allocation")
        _check_digest(pair.request_sha256)
        _check_digest(pair.ledger_sha256)
        if pair.request_sha256 in requests or pair.ledger_sha256 in ledgers:
            _fail("Duplicate cohort artifact identity")
        seen.add(pair.plan_sha256)
        requests.add(pair.request_sha256)
        ledgers.add(pair.ledger_sha256)
        pairs.append(pair)
    return (
        _pool_site((pair.curves[0] for pair in pairs), len(planned_plan_ids), count),
        _pool_site((pair.curves[1] for pair in pairs), len(planned_plan_ids), count),
    )


Interval = tuple[Fraction, Fraction | None]
ComponentStatus = Literal["definite_pass", "definite_fail", "unresolved"]
ReliabilityStatus = Literal["adequate", "inadequate", "unresolved"]


class ComponentComparison(NamedTuple):
    """One fixed component, with None denoting an unbounded upper endpoint."""

    observed: Interval
    reference: Interval
    margin: Fraction


def _check_interval(interval: Interval) -> None:
    lower, upper = interval
    _require_fraction(lower, "Interval endpoints must be exact fractions")
    if upper is not None:
        _require_fraction(upper, "Interval endpoints must be exact fractions")
    if lower < 0 or (upper is not None and upper < lower):
        _fail("Invalid nonnegative component enclosure")


def classify_component(comparison: ComponentComparison) -> ComponentStatus:
    """Classify all admissible observed/reference pairs, with inclusive margin."""
    observed, reference, margin = comparison
    _check_interval(observed)
    _check_interval(reference)
    _require_fraction(margin, "Margin must be an exact fraction")
    if margin < 0:
        _fail("Invalid negative component margin")
    lower, upper = observed
    ref_lower, ref_upper = reference
    if (upper is not None and upper + margin < ref_lower) or (ref_upper is not None and ref_upper + margin < lower):
        return "definite_fail"
    if upper is not None and ref_upper is not None and upper <= ref_lower + margin and ref_upper <= lower + margin:
        return "definite_pass"
    return "unresolved"


def classify_whole_run(
    expected_components: tuple[str, ...],
    comparisons: Mapping[str, ComponentComparison],
) -> ComponentStatus:
    """Use the complete frozen paired-output vector, never silently omit components."""
    if (
        not 1 <= len(expected_components) <= 14
        or not all(expected_components)
        or len(set(expected_components)) != len(expected_components)
        or set(comparisons) != set(expected_components)
    ):
        _fail("Expected the exact frozen component family")
    statuses = tuple(classify_component(comparisons[key]) for key in expected_components)
    if "definite_fail" in statuses:
        return "definite_fail"
    return "definite_pass" if all(status == "definite_pass" for status in statuses) else "unresolved"


class ReliabilityDecision(NamedTuple):
    """Fixed 300-cohort count decision, not a population or source admission."""

    definite_passes: int
    possible_passes: int
    unresolved: int
    status: ReliabilityStatus


def confirmation_decision(
    planned_plan_ids: tuple[str, ...],
    outcomes: Mapping[str, ComponentStatus],
) -> ReliabilityDecision:
    """Exact predeclared CP critical counts: n=300, target .95, alpha=.015 each tail.

    The caller must verify the frozen reference coverage construction and
    latent iid cohort law. Missing planned outcomes remain possible passes;
    do not use this function for sequential stopping or a different design.
    """
    _check_plan_ids(planned_plan_ids)
    if len(planned_plan_ids) != 300 or set(outcomes) - set(planned_plan_ids):
        _fail("Expected the fixed family of 300 preassigned confirmations")
    if any(status not in {"definite_pass", "definite_fail", "unresolved"} for status in outcomes.values()):
        _fail("Invalid confirmation outcome")
    definite = sum(status == "definite_pass" for status in outcomes.values())
    possible = 300 - sum(status == "definite_fail" for status in outcomes.values())
    status: ReliabilityStatus = "adequate" if definite >= 294 else "inadequate" if possible <= 275 else "unresolved"
    return ReliabilityDecision(definite, possible, possible - definite, status)
