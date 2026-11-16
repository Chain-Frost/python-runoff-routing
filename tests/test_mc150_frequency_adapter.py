"""External #150 acceptance cases against the eventual #147 production result API.

The module is deliberately absent from #150's independent base while #147 is
under separate review. Skips are an explicit *not-run* gate, never accepted
production verification. Once #147 integrates, these same cases must execute.
"""

from __future__ import annotations

import importlib
import importlib.util
import json
from collections.abc import Callable
from dataclasses import replace
from fractions import Fraction
from pathlib import Path
from typing import Any, Protocol, cast

import pytest

REFERENCE = Path(__file__).absolute().parent / "fixtures" / "monte-carlo-qualification-v1" / "analytic-controls.json"


class _FrequencyAPI(Protocol):
    FrequencyScope: Callable[..., Any]
    StratumWeight: Callable[..., Any]
    UnmodelledTails: Callable[..., Any]
    CurvePopulation: Callable[..., Any]
    PeakRecord: Callable[..., Any]
    FrequencyInputError: type[Exception]
    build_frequency_curve: Callable[..., Any]
    build_frequency_curves: Callable[..., Any]
    duration_envelope: Callable[..., Any]


def _frequency() -> _FrequencyAPI:
    if importlib.util.find_spec("runoff_routing.monte_carlo_frequency") is None:
        pytest.skip("#147 frequency API not integrated in this branch; production comparison not run")
    return cast("_FrequencyAPI", importlib.import_module("runoff_routing.monte_carlo_frequency"))


def _controls() -> dict[str, Any]:
    return json.loads(REFERENCE.read_text(encoding="utf-8"))


def _fraction(text: str) -> float:
    return float(Fraction(text))


def _population(
    api: _FrequencyAPI,
    data: dict[str, Any],
    *,
    plan: str = "external-fixture-v1",
    duration: int = 60,
    site: str = "outlet",
) -> tuple[Any, tuple[Any, ...]]:
    scope = api.FrequencyScope(plan, "mc150-independent", "1", "synthetic", duration, site)
    strata = tuple(
        api.StratumWeight(item["stratum_id"], _fraction(item["mass"]), len(item["events"])) for item in data["strata"]
    )
    tails = data["unmodelled_tails"]
    population = api.CurvePopulation(
        scope,
        strata,
        api.UnmodelledTails(
            lower_rainfall_mass=_fraction(tails.get("frequent", "0")),
            upper_rainfall_mass=_fraction(tails.get("rare", "0")),
        ),
    )
    records = tuple(
        api.PeakRecord(
            scope,
            stratum["stratum_id"],
            sample["sample_id"],
            _fraction(stratum["mass"]) / len(stratum["events"]),
            sample["status"],
            _fraction(sample["q_m3s"]) if sample["q_m3s"] is not None else None,
            f"native-independent-{sample['sample_id']}" if sample["status"] == "valid" else None,
            f"effective-input-{sample['sample_id']}" if sample["status"] == "valid" else None,
        )
        for stratum in data["strata"]
        for sample in stratum["events"]
    )
    return population, records


@pytest.mark.parametrize(
    "case_id",
    ["Q01-unequal-strata-zero-and-ties", "Q02-failure-missing-are-not-dry", "Q03-unmodelled-probability-tails"],
)
def test_independent_exact_exceedance_and_probability_bounds(case_id: str) -> None:
    api = _frequency()
    case = next(item for item in _controls()["cases"] if item["case_id"] == case_id)
    population, records = _population(api, case)
    curve = api.build_frequency_curve(population, records)
    for expected in case["threshold_checks"]:
        actual = curve.exceedance(_fraction(expected["threshold_m3s"]))
        assert actual.known_exceedance_probability == pytest.approx(_fraction(expected["gt_lower"]))
        assert actual.lower_probability == pytest.approx(_fraction(expected["gt_lower"]))
        assert actual.upper_probability == pytest.approx(_fraction(expected["gt_upper"]))
    total_missing = sum(_fraction(value) for value in case["unmodelled_tails"].values())
    if any(event["status"] != "valid" for stratum in case["strata"] for event in stratum["events"]):
        assert not curve.coverage.complete
        assert curve.estimate(0.2).status == "incomplete"
        assert curve.estimate(0.2).representative is None
    elif total_missing > 0:
        assert not curve.coverage.complete
        assert curve.estimate(0.2).status == "incomplete"
    else:
        assert curve.coverage.complete
        for check in case.get("step_quantiles", []):
            q = curve.estimate(_fraction(check["upper_tail_probability"]))
            assert q.peak_m3_s == pytest.approx(_fraction(check["quantile_m3s"]))
            assert q.representative is not None
            assert q.representative.realised_peak_m3_s == q.peak_m3_s


def test_plan_extension_uses_new_weights_for_old_sample_ids() -> None:
    api = _frequency()
    extension = _controls()["plan_extension"]
    old_case: dict[str, Any] = {"strata": extension["original_strata"], "unmodelled_tails": {}}
    new_case: dict[str, Any] = {"strata": extension["extended_strata"], "unmodelled_tails": {}}
    old_population, old_records = _population(api, old_case, plan=extension["original_revision"])
    new_population, new_records = _population(api, new_case, plan=extension["extended_revision"])
    assert {r.sample_id for r in old_records} <= {r.sample_id for r in new_records}
    old_curve = api.build_frequency_curve(old_population, old_records)
    new_curve = api.build_frequency_curve(new_population, new_records)
    assert old_curve.exceedance(6).known_exceedance_probability == pytest.approx(
        _fraction(extension["original_exceedance"])
    )
    assert new_curve.exceedance(6).known_exceedance_probability == pytest.approx(
        _fraction(extension["extended_exceedance"])
    )
    assert next(r.event_probability_weight for r in old_records if r.sample_id == "a1") == pytest.approx(0.1)
    assert next(r.event_probability_weight for r in new_records if r.sample_id == "a1") == pytest.approx(0.05)
    with pytest.raises(api.FrequencyInputError, match=r"Mismatched plan|Stale or mixed"):
        api.build_frequency_curve(new_population, old_records)


@pytest.mark.parametrize("aep", ["1/20", "1/100"])
def test_independent_two_site_two_duration_envelopes(aep: str) -> None:
    api = _frequency()
    control = _controls()["duration_envelope"]
    populations: list[Any] = []
    records: list[Any] = []
    for row in control["durations"]:
        site, duration = row["site_id"], row["duration_minutes"]
        q_05 = _fraction(row["at_aep"]["1/20"])
        q_01 = _fraction(row["at_aep"]["1/100"])
        assert 0 < q_05 <= q_01
        scope = api.FrequencyScope(f"plan-{site}-{duration}", "mc150", "1", "synthetic", duration, site)
        populations.append(api.CurvePopulation(scope, (api.StratumWeight("h", 1.0, 100),)))
        # The 95th ranked event has peak q_05, while the 99th is q_01.
        for i, peak in enumerate((q_05 - 10,) * 94 + (q_05,) * 4 + (q_01,) * 2):
            records.append(
                api.PeakRecord(
                    scope,
                    "h",
                    f"{site}-{duration}-{i:03d}",
                    0.01,
                    "valid",
                    peak,
                    f"event-{site}-{duration}-{i:03d}",
                    f"input-{site}-{duration}-{i:03d}",
                )
            )
    curves = api.build_frequency_curves(populations, reversed(records))
    target = _fraction(aep)
    assert len(curves) == 4
    for item in [row for row in control["expected"] if row["aep"] == aep]:
        site_curves = tuple(
            sorted(
                (curve for curve in curves if curve.scope.output_site_id == item["site_id"]),
                key=lambda curve: curve.scope.duration_minutes,
            )
        )
        assert len(site_curves) == 2
        envelope = api.duration_envelope(site_curves, target)
        assert envelope.status == "estimated"
        assert envelope.peak_m3_s == pytest.approx(_fraction(item["max_q_m3s"]))
        assert envelope.critical_duration_minutes == item["critical_duration_minutes"]
        assert envelope.representative is not None
        assert envelope.representative.effective_input_id.startswith("input-")


def test_incomplete_mass_and_mixed_policy_fail_closed() -> None:
    api = _frequency()
    case = next(item for item in _controls()["cases"] if item["case_id"] == "Q02-failure-missing-are-not-dry")
    population, records = _population(api, case)
    curve = api.build_frequency_curve(population, records)
    assert curve.coverage.valid_mass == pytest.approx(0.625)
    assert curve.coverage.failed_mass == pytest.approx(0.25)
    assert curve.coverage.missing_mass == pytest.approx(0.125)
    assert curve.coverage.unresolved_mass == pytest.approx(0.375)
    assert curve.estimate(0.5).status == "incomplete"
    with pytest.raises(api.FrequencyInputError, match="Mismatched plan"):
        api.build_frequency_curve(population, (replace(records[0], scope=replace(population.scope, plan_id="other")),))
    with pytest.raises(api.FrequencyInputError, match="Stale or mixed"):
        api.build_frequency_curve(population, (replace(records[0], event_probability_weight=0.5),))
