"""Source-independent controls for fixed paired-cohort research decisions."""

from __future__ import annotations

import hashlib
import importlib.util
import sys
from collections.abc import Iterator
from decimal import Decimal
from fractions import Fraction
from itertools import combinations_with_replacement, product
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import Any, cast

import pytest


def _research() -> ModuleType:
    path = Path(__file__).parents[1] / "repo-scripts" / "mc_conditional_research.py"
    spec = importlib.util.spec_from_file_location("mc_conditional_research", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _identity(number: int) -> str:
    return f"{number:064x}"


def _allocation() -> dict[str, tuple[Decimal, int]]:
    return {"a": (Decimal(".20"), 2), "b": (Decimal(".29"), 2)}


def _rows(prefix: str) -> list[dict[str, object]]:
    return [
        {
            "sample_id": f"{prefix}-{index}",
            "stratum_id": "a" if index < 2 else "b",
            "scenario_id": "study",
            "duration_min": 1440,
            "status": "computed_unvalidated",
            "sites": [{"print_id": "P01", "peak_m3_s": peak}, {"print_id": "P02", "peak_m3_s": 99 - peak}],
        }
        for index, peak in enumerate((0, 20, 10, 10))
    ]


def _scope(mc: ModuleType) -> object:
    return mc.CohortScope(
        _identity(1000),
        _identity(1001),
        "study",
        1440,
        ("P01", "P02"),
        tuple((key, mass, count) for key, (mass, count) in _allocation().items()),
    )


def _pair(mc: ModuleType, number: int, rows: list[dict[str, object]]) -> object:
    first = mc.conditional_curve(_allocation(), rows, scenario="study", duration=1440, site_id="P01")
    second = mc.conditional_curve(_allocation(), rows, scenario="study", duration=1440, site_id="P02")
    return mc.PairedCohort(
        _identity(number), _identity(number + 100), _identity(number + 200), _scope(mc), (first, second)
    )


def test_pooled_curves_match_direct_full_allocation() -> None:
    mc = _research()
    rows_a, rows_b = _rows("a"), _rows("b")[:3]
    pair_a, pair_b = _pair(mc, 1, rows_a), _pair(mc, 2, rows_b)
    pooled = mc.pool_paired_cohorts(_scope(mc), (_identity(1), _identity(2)), [pair_a, pair_b])
    plan = {key: (mass, count * 2) for key, (mass, count) in _allocation().items()}
    for site, curve in zip(("P01", "P02"), pooled, strict=True):
        direct = mc.conditional_curve(plan, rows_a + rows_b, scenario="study", duration=1440, site_id=site)
        assert curve == direct
        assert curve.unknown_mass == Fraction(29, 400)


def test_unstarted_cohort_stays_in_both_planned_denominators() -> None:
    mc = _research()
    first, second = mc.pool_paired_cohorts(_scope(mc), (_identity(1), _identity(2)), [_pair(mc, 1, _rows("a"))])
    for curve in (first, second):
        assert curve.planned_count == 8
        assert curve.unknown_mass == Fraction(49, 200)
        assert curve.status_counts == {"valid": 4, "unrecorded": 4}
        assert curve.quantile(Fraction(1, 100))[1] is None
    assert first.cdf(Fraction(0)) == (Fraction(5, 49), Fraction(59, 98))
    assert second.cdf(Fraction(0)) == (0, Fraction(1, 2))
    wholly_unknown = mc.pool_paired_cohorts(_scope(mc), (_identity(1), _identity(2)), [])
    assert all(curve.unknown_mass == Fraction(49, 100) for curve in wholly_unknown)


def test_pooled_scope_and_artifact_identity_rejected() -> None:
    mc = _research()
    a = cast("Any", _pair(mc, 1, _rows("a")))
    b = cast("Any", _pair(mc, 2, _rows("b")))
    ids = (_identity(1), _identity(2))
    with pytest.raises(ValueError, match="Duplicate or unplanned"):
        mc.pool_paired_cohorts(_scope(mc), ids, [a, a])
    with pytest.raises(ValueError, match="distinct preassigned"):
        mc.pool_paired_cohorts(_scope(mc), (ids[0], ids[0]), [])
    with pytest.raises(ValueError, match="Duplicate cohort artifact"):
        mc.pool_paired_cohorts(_scope(mc), ids, [a, b._replace(request_sha256=a.request_sha256)])
    with pytest.raises(ValueError, match="Duplicate cohort artifact"):
        mc.pool_paired_cohorts(_scope(mc), ids, [a, b._replace(ledger_sha256=a.ledger_sha256)])
    for scope in (
        b.scope._replace(site_ids=("P02", "P01")),
        b.scope._replace(allocations=(("a", Decimal(".21"), 2), ("b", Decimal(".28"), 2))),
        b.scope._replace(wheel_sha256=_identity(1002)),
    ):
        with pytest.raises(ValueError, match="Mismatched paired cohort"):
            mc.pool_paired_cohorts(_scope(mc), ids, [a, b._replace(scope=scope)])
    corrupted = b.curves[0]._replace(unknown_mass=Fraction(1, 10))
    with pytest.raises(ValueError, match="Inconsistent curve mass"):
        mc.pool_paired_cohorts(_scope(mc), ids, [a, b._replace(curves=(corrupted, b.curves[1]))])


def test_pooled_reader_failure_propagates_without_partial_result() -> None:
    mc = _research()

    def records() -> Iterator[object]:
        yield _pair(mc, 1, _rows("a"))
        message = "late verification failure"
        raise ValueError(message)

    with pytest.raises(ValueError, match="late verification failure"):
        mc.pool_paired_cohorts(_scope(mc), (_identity(1), _identity(2)), records())


def test_rectangle_classifier_exhaustive_integer_controls() -> None:
    mc = _research()
    intervals = tuple(combinations_with_replacement(range(5), 2))
    for (lo, hi), (ref_lo, ref_hi), margin in product(intervals, intervals, range(4)):
        passes = [abs(a - b) <= margin for a, b in product(range(lo, hi + 1), range(ref_lo, ref_hi + 1))]
        expected = "definite_pass" if all(passes) else "definite_fail" if not any(passes) else "unresolved"
        comparison = mc.ComponentComparison(
            (Fraction(lo), Fraction(hi)), (Fraction(ref_lo), Fraction(ref_hi)), Fraction(margin)
        )
        assert mc.classify_component(comparison) == expected


def test_rectangle_unbounded_and_exact_boundary() -> None:
    mc = _research()
    comparison = mc.ComponentComparison((Fraction(0), None), (Fraction(10), Fraction(10)), Fraction(1))
    assert mc.classify_component(comparison) == "unresolved"
    assert mc.classify_component(comparison._replace(observed=(Fraction(12), None))) == "definite_fail"
    assert mc.classify_component(comparison._replace(observed=(Fraction(11), None))) == "unresolved"
    at_margin = comparison._replace(observed=(Fraction(11), Fraction(11)))
    assert mc.classify_component(at_margin) == "definite_pass"
    near = Fraction(11) + Fraction(1, 10**20)
    assert mc.classify_component(at_margin._replace(observed=(near, near))) == "definite_fail"
    with pytest.raises(ValueError, match="exact fractions"):
        mc.classify_component(at_margin._replace(observed=(11.0, Fraction(11))))
    with pytest.raises(ValueError, match="Invalid nonnegative"):
        mc.classify_component(at_margin._replace(observed=(Fraction(2), Fraction(1))))
    with pytest.raises(ValueError, match="exact fraction"):
        mc.classify_component(at_margin._replace(margin=1.0))


def test_whole_run_requires_both_sites_and_all_frozen_components() -> None:
    mc = _research()
    success = mc.ComponentComparison((Fraction(1), Fraction(1)), (Fraction(1), Fraction(1)), Fraction(0))
    unknown = success._replace(observed=(Fraction(0), None))
    failure = success._replace(observed=(Fraction(2), Fraction(2)))
    components = ("P01:peak", "P02:peak")
    assert mc.classify_whole_run(components, dict.fromkeys(components, success)) == "definite_pass"
    assert mc.classify_whole_run(components, {components[0]: success, components[1]: unknown}) == "unresolved"
    assert mc.classify_whole_run(components, {components[0]: unknown, components[1]: failure}) == "definite_fail"
    with pytest.raises(ValueError, match="exact frozen"):
        mc.classify_whole_run(components, {components[0]: success})


def test_fixed_confirmation_counts_keep_all_300_planned_slots() -> None:
    mc = _research()
    ids = tuple(_identity(i) for i in range(300))
    assert mc.confirmation_decision(ids, dict.fromkeys(ids[:294], "definite_pass")) == (294, 300, 6, "adequate")
    assert mc.confirmation_decision(ids, dict.fromkeys(ids[:293], "definite_pass")) == (293, 300, 7, "unresolved")
    assert mc.confirmation_decision(ids, dict.fromkeys(ids[:25], "definite_fail")) == (0, 275, 275, "inadequate")
    assert mc.confirmation_decision(ids, dict.fromkeys(ids[:24], "definite_fail")) == (0, 276, 276, "unresolved")
    assert mc.confirmation_decision(ids, {}) == (0, 300, 300, "unresolved")
    with pytest.raises(ValueError, match="fixed family"):
        mc.confirmation_decision(ids[:-1], {})
    with pytest.raises(ValueError, match="fixed family"):
        mc.confirmation_decision(ids, {_identity(300): "definite_pass"})
    with pytest.raises(ValueError, match="Invalid confirmation"):
        mc.confirmation_decision(ids, {ids[0]: "adequate"})


def test_paired_adapter_reuses_verified_reader_and_exact_scope(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Exercise adapter wiring only, with an authored header/reader double, no routing."""
    mc = _research()
    artifacts: list[Any] = []
    for name in ("project", "request", "ledger", "wheel"):
        path = tmp_path / name
        path.write_text(name, encoding="utf-8")
        artifacts.append(mc.Artifact(path, hashlib.sha256(path.read_bytes()).hexdigest()))
    project, request, ledger, wheel = artifacts
    header = SimpleNamespace(
        plan_sha256=_identity(42),
        populations=(SimpleNamespace(scenario_id="study", duration_min=1440),),
        strata=tuple(
            SimpleNamespace(stratum_id=key, probability_mass=mass, planned_samples=count)
            for key, (mass, count) in _allocation().items()
        ),
    )
    effective = ModuleType("runoff_routing.monte_carlo_effective")

    def read_header(path: Path) -> SimpleNamespace:
        assert path == request.path
        return header

    def sha256_file(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    monkeypatch.setattr(effective, "read_header", read_header, raising=False)
    monkeypatch.setattr(effective, "sha256_file", sha256_file, raising=False)
    monkeypatch.setitem(sys.modules, effective.__name__, effective)
    calls: list[str] = []

    def verified_reader(
        project_pin: object, request_pin: object, ledger_pin: object, *, site_id: str, wheel: object
    ) -> object:
        assert (project_pin, request_pin, ledger_pin) == (project, request, ledger)
        assert wheel == artifacts[3]
        calls.append(site_id)
        return mc.conditional_curve(_allocation(), _rows("paired"), scenario="study", duration=1440, site_id=site_id)

    monkeypatch.setattr(mc, "read_verified_cohort", verified_reader)
    pair = mc.read_verified_pair(project, request, ledger, site_ids=("P01", "P02"), wheel=wheel)
    assert calls == ["P01", "P02"]
    assert pair.plan_sha256 == _identity(42)
    assert pair.scope.project_sha256 == project.sha256
    assert pair.scope.wheel_sha256 == wheel.sha256
    assert pair.curves[0].cdf(Fraction(0))[0] > 0
    assert pair.curves[1].cdf(Fraction(0)) == (0, 0)
    assert mc.pool_paired_cohorts(pair.scope, (pair.plan_sha256,), [pair]) == pair.curves
    before = len(calls)
    with pytest.raises(ValueError, match="digest mismatch"):
        mc.read_verified_pair(project, request._replace(sha256="0" * 64), ledger, site_ids=("P01", "P02"), wheel=wheel)
    assert len(calls) == before

    def failed_second_reader(
        project_pin: object, request_pin: object, ledger_pin: object, *, site_id: str, wheel: object
    ) -> object:
        if site_id == "P02":
            message = "second site verification failed"
            raise ValueError(message)
        return verified_reader(project_pin, request_pin, ledger_pin, site_id=site_id, wheel=wheel)

    monkeypatch.setattr(mc, "read_verified_cohort", failed_second_reader)
    with pytest.raises(ValueError, match="second site verification failed"):
        mc.read_verified_pair(project, request, ledger, site_ids=("P01", "P02"), wheel=wheel)
    assert ledger.path.read_bytes() == b"ledger"
