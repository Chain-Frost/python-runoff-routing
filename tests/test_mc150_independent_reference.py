"""Independent exact-rational synthetic controls for MC qualification (#150).

This does not import or validate the implementation under development. The controls
are designed for independent comparison with #146/#147/#149 after their contracts land.
"""

from __future__ import annotations

import json
from fractions import Fraction
from pathlib import Path
from typing import Literal, NotRequired, TypedDict, cast

import pytest


class Event(TypedDict):
    sample_id: str
    status: Literal["valid", "failed", "missing"]
    q_m3s: str | None


class Stratum(TypedDict):
    stratum_id: str
    mass: str
    events: list[Event]


class Threshold(TypedDict):
    threshold_m3s: str
    gt_lower: str
    gt_upper: str
    equal_mass: str


class StepQuantile(TypedDict):
    upper_tail_probability: str
    quantile_m3s: str


class Population(TypedDict):
    case_id: str
    strata: list[Stratum]
    unmodelled_tails: dict[str, str]
    threshold_checks: list[Threshold]
    step_quantiles: NotRequired[list[StepQuantile]]


class Extension(TypedDict):
    original_revision: str
    extended_revision: str
    original_strata: list[Stratum]
    extended_strata: list[Stratum]
    threshold_m3s: str
    original_exceedance: str
    extended_exceedance: str
    original_a1_weight: str
    extended_a1_weight: str


class DurationRow(TypedDict):
    site_id: str
    duration_minutes: int
    at_aep: dict[str, str]


class EnvelopeCheck(TypedDict):
    site_id: str
    aep: str
    max_q_m3s: str
    critical_duration_minutes: int


class DurationEnvelope(TypedDict):
    input_type: str
    durations: list[DurationRow]
    expected: list[EnvelopeCheck]


class Reference(TypedDict):
    schema_version: str
    evidence_kind: str
    exceedance_convention: str
    interpolation_status: str
    cases: list[Population]
    plan_extension: Extension
    duration_envelope: DurationEnvelope


REFERENCE_FILE = (
    Path(__file__).absolute().parent / "fixtures" / "monte-carlo-qualification-v1" / "analytic-controls.json"
)
REFERENCE = cast("Reference", json.loads(REFERENCE_FILE.read_text(encoding="utf-8")))


def _weighted_events(strata: list[Stratum]) -> list[tuple[Event, Fraction]]:
    """Compute independent exact weights without using production samplers or estimators."""
    weighted: list[tuple[Event, Fraction]] = []
    seen: set[str] = set()
    for stratum in strata:
        mass = Fraction(stratum["mass"])
        assert 0 < mass <= 1
        assert stratum["events"]
        weight = mass / len(stratum["events"])
        for event in stratum["events"]:
            assert event["sample_id"] not in seen
            seen.add(event["sample_id"])
            if event["status"] == "valid":
                assert event["q_m3s"] is not None
                assert Fraction(event["q_m3s"]) >= 0
            else:
                assert event["status"] in ("failed", "missing")
                assert event["q_m3s"] is None
            weighted.append((event, weight))
    return weighted


def _strict_exceedance_bounds(
    weighted: list[tuple[Event, Fraction]], threshold: Fraction, unmodelled: Fraction
) -> tuple[Fraction, Fraction, Fraction]:
    definite = sum(
        (
            weight
            for event, weight in weighted
            if event["status"] == "valid" and Fraction(event["q_m3s"] or "0") > threshold
        ),
        Fraction(),
    )
    unknown = sum((weight for event, weight in weighted if event["status"] != "valid"), unmodelled)
    equals = sum(
        (
            weight
            for event, weight in weighted
            if event["status"] == "valid" and Fraction(event["q_m3s"] or "0") == threshold
        ),
        Fraction(),
    )
    return definite, definite + unknown, equals


def test_reference_identity_and_hand_derived_exceedance_bounds() -> None:
    assert REFERENCE["schema_version"] == "mc150-analytic-reference-v1"
    assert REFERENCE["evidence_kind"].endswith("not_native")
    assert REFERENCE["exceedance_convention"] == "P(Q > threshold)"
    assert len(REFERENCE["cases"]) == 3
    for case in REFERENCE["cases"]:
        weighted = _weighted_events(case["strata"])
        tails = sum((Fraction(value) for value in case["unmodelled_tails"].values()), Fraction())
        assert all(Fraction(value) >= 0 for value in case["unmodelled_tails"].values())
        assert sum((weight for _, weight in weighted), tails) == 1
        for check in case["threshold_checks"]:
            observed = _strict_exceedance_bounds(weighted, Fraction(check["threshold_m3s"]), tails)
            expected = Fraction(check["gt_lower"]), Fraction(check["gt_upper"]), Fraction(check["equal_mass"])
            assert observed == expected, (case["case_id"], check, observed)


def test_step_inverse_is_only_a_declared_analytic_example() -> None:
    """A production interpolation convention remains owned by #145/#147."""
    population = REFERENCE["cases"][0]
    weighted = _weighted_events(population["strata"])
    assert all(event["status"] == "valid" for event, _ in weighted)
    values = sorted({Fraction(event["q_m3s"] or "0") for event, _ in weighted})
    for check in population.get("step_quantiles", []):
        aep = Fraction(check["upper_tail_probability"])
        nonexceedance = 1 - aep
        first = next(
            q
            for q in values
            if sum((weight for event, weight in weighted if Fraction(event["q_m3s"] or "0") <= q), Fraction())
            >= nonexceedance
        )
        assert first == Fraction(check["quantile_m3s"])


def test_zero_is_valid_but_failure_and_unmodelled_tails_are_not() -> None:
    cases = {case["case_id"]: case for case in REFERENCE["cases"]}
    unequal = _weighted_events(cases["Q01-unequal-strata-zero-and-ties"]["strata"])
    assert sum((weight for event, weight in unequal if event["q_m3s"] == "0"), Fraction()) == Fraction(1, 4)
    assert sum((weight for _, weight in unequal), Fraction()) == 1
    assert Fraction(2, 5) != Fraction(1, 2)  # Five pooled events would give the wrong P(Q>10).

    incomplete = _weighted_events(cases["Q02-failure-missing-are-not-dry"]["strata"])
    status_mass = {
        status: sum((weight for event, weight in incomplete if event["status"] == status), Fraction())
        for status in ("valid", "failed", "missing")
    }
    assert status_mass == {"valid": Fraction(5, 8), "failed": Fraction(1, 4), "missing": Fraction(1, 8)}
    assert status_mass["valid"] != 1  # Not a complete frequency curve, even though all valid Q are finite.

    tails = cases["Q03-unmodelled-probability-tails"]["unmodelled_tails"]
    assert sum((Fraction(value) for value in tails.values()), Fraction()) == Fraction(1, 2)


def test_plan_extension_preserves_draws_but_reweights_existing_samples() -> None:
    extension = REFERENCE["plan_extension"]
    original = _weighted_events(extension["original_strata"])
    extended = _weighted_events(extension["extended_strata"])
    old = {event["sample_id"]: (event["q_m3s"], weight) for event, weight in original}
    new = {event["sample_id"]: (event["q_m3s"], weight) for event, weight in extended}
    assert extension["original_revision"] != extension["extended_revision"]
    assert all(new[sample_id][0] == peak for sample_id, (peak, _) in old.items())
    assert old["a1"][1] == Fraction(extension["original_a1_weight"]) == Fraction(1, 10)
    assert new["a1"][1] == Fraction(extension["extended_a1_weight"]) == Fraction(1, 20)
    assert old["b1"][1] == new["b1"][1] == Fraction(2, 5)
    threshold = Fraction(extension["threshold_m3s"])
    before = _strict_exceedance_bounds(original, threshold, Fraction())
    after = _strict_exceedance_bounds(extended, threshold, Fraction())
    assert before[0] == before[1] == Fraction(extension["original_exceedance"]) == Fraction(1, 2)
    assert after[0] == after[1] == Fraction(extension["extended_exceedance"]) == Fraction(9, 20)


@pytest.mark.parametrize("aep", ["1/20", "1/100"])
def test_duration_envelope_is_site_specific_and_never_pools_samples(aep: str) -> None:
    envelope = REFERENCE["duration_envelope"]
    rows = [row for row in envelope["durations"] if aep in row["at_aep"]]
    expected_rows = [row for row in envelope["expected"] if row["aep"] == aep]
    assert len(rows) == 4
    assert len(expected_rows) == 2
    for expected in expected_rows:
        matches = [row for row in rows if row["site_id"] == expected["site_id"]]
        critical = max(matches, key=lambda row: Fraction(row["at_aep"][aep]))
        assert Fraction(critical["at_aep"][aep]) == Fraction(expected["max_q_m3s"])
        assert critical["duration_minutes"] == expected["critical_duration_minutes"]
