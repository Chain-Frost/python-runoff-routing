"""Small offline analytical checks for the optional issue #148 research harness."""

from __future__ import annotations

import csv
import importlib.util
import json
import math
import sys
from pathlib import Path
from types import ModuleType

import pytest


def _research() -> ModuleType:
    path = Path(__file__).parents[1] / "repo-scripts" / "mc_convergence_research.py"
    if not path.exists():  # For local independent authoring outside the repository.
        path = Path(__file__).with_name("mc_convergence_research.py")
    spec = importlib.util.spec_from_file_location("mc_convergence_research", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_exact_integral_and_positive_atom() -> None:
    mc = _research()
    response = mc.Response(1.0, 0.0, 0.0, 1.0)
    assert mc.exact_survival(response, 0.0) == pytest.approx(0.5)
    assert mc.exact_survival(response, 0.5) == pytest.approx(0.125)
    assert mc.exact_quantile(response, 0.125) == pytest.approx(0.5, abs=1e-12)
    assert mc.exact_quantile(response, 0.6) == 0.0
    assert mc.exact_survival(response, 0.5, lower_u=0.0, upper_u=0.4) == 0.0


def test_weighted_inverse_and_missing_probability() -> None:
    mc = _research()
    peaks = [(0.0, 0.6), (10.0, 0.4)]
    assert mc.weighted_quantile(peaks, 0.1) == 10
    assert mc.weighted_quantile(peaks, 0.5) == 0
    assert mc.weighted_quantile(list(reversed(peaks)), 0.1) == 10
    with pytest.raises(ValueError, match="missing probability mass"):
        mc.weighted_quantile([(0.0, 0.6), (10.0, 0.3)], 0.1)
    with pytest.raises(ValueError, match="failed"):
        mc.weighted_quantile([(float("nan"), 1.0)], 0.1)


def test_exact_one_sided_lower_confidence_and_independent_reps() -> None:
    mc = _research()
    assert mc.lower_confidence_bound(0, 30) == 0.0
    assert mc.lower_confidence_bound(30, 30) == pytest.approx(0.05 ** (1 / 30), abs=1e-12)
    assert mc.lower_confidence_bound(30, 30) < 0.95
    assert mc.lower_confidence_bound(100, 100) > 0.95
    assert mc.upper_confidence_bound(2, 100) < 0.1
    assert mc.upper_confidence_bound(100, 100) == 1.0
    assert mc.sd_bootstrap_interval([1.0, 2.0, 5.0, 7.0], "fixed") == mc.sd_bootstrap_interval(
        [1.0, 2.0, 5.0, 7.0], "fixed"
    )
    assert 0.0 < mc.lower_confidence_bound(50, 100) < 0.5


def test_missing_tail_bounds_do_not_normalise_or_invent_upper_quantiles() -> None:
    mc = _research()
    response = mc.RESPONSES["near_tie"]["short"]
    lower, upper = mc.endpoint_quantile_bounds(response, 0.05)
    assert upper is not None
    truth = mc.exact_quantile(response, 0.05)
    assert lower <= truth <= upper
    _, sparse_upper = mc.endpoint_quantile_bounds(response, 0.02)
    assert sparse_upper is None


def test_complete_unequal_strata_and_exact_finite_tp() -> None:
    mc = _research()
    edges = mc.strata_edges(5)
    assert edges[0] == 0
    assert edges[-1] == 1
    assert edges[1] - edges[0] != pytest.approx(edges[3] - edges[2])
    for method in ("random_tp", "paired_tp"):
        peaks = mc.trial_peaks(root=9, stage="test", replication=0, duration="short", strata=5, n=4, tp_method=method)
        assert set(peaks) == {"zero_atom", "near_tie"}
        assert all(len(values) == 20 for values in peaks.values())
        for values in peaks.values():
            assert sum(weight for _, weight in values) == pytest.approx(1.0)
    first = mc.trial_peaks(root=9, stage="test", replication=0, duration="short", strata=5, n=4, tp_method="random_tp")
    repeat = mc.trial_peaks(root=9, stage="test", replication=0, duration="short", strata=5, n=4, tp_method="random_tp")
    changed = mc.trial_peaks(
        root=9, stage="test", replication=1, duration="short", strata=5, n=4, tp_method="random_tp"
    )
    assert first == repeat
    assert first != changed


def test_envelope_uses_each_duration_and_all_sites() -> None:
    mc = _research()
    rows = mc.one_trial(
        root=7, stage="test", replication=0, strata=5, n=4, tp_method="random_tp", quantile_method="rank"
    )
    assert len(rows) == 2 * 4 * 3
    for site in mc.RESPONSES:
        for aep in mc.AEPS:
            subset = {row["duration"]: row for row in rows if row["site"] == site and row["aep"] == aep}
            assert subset["envelope"]["estimate"] == max(subset[d]["estimate"] for d in mc.DURATIONS)
            assert subset["envelope"]["exact"] == max(subset[d]["exact"] for d in mc.DURATIONS)
            assert subset["envelope"]["critical_duration"] in mc.DURATIONS
            assert subset["envelope"]["zero_probability"] is None


def test_smoke_writes_immutable_replay_receipts(tmp_path: Path) -> None:
    mc = _research()
    output = tmp_path / "smoke"
    mc.run("smoke", output, root=123, replications=2, max_evaluations=80, max_wall_seconds=30, opt_in=False)
    manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    summary = json.loads((output / "summary.json").read_text(encoding="utf-8"))
    assert manifest["total_evaluations"] == 80
    assert (output / "endpoint_sensitivity.json").exists()
    assert len(summary["metrics"]) == 24
    assert summary["whole_run"][0]["replications"] == 2
    with pytest.raises(FileExistsError):
        mc.run("smoke", output, root=123, replications=2, max_evaluations=80, max_wall_seconds=30, opt_in=False)
    with pytest.raises(ValueError, match="require --opt-in"):
        mc.run(
            "pilot",
            tmp_path / "pilot",
            root=123,
            replications=2,
            max_evaluations=77000,
            max_wall_seconds=30,
            opt_in=False,
        )
    with pytest.raises(ValueError, match="exceeds"):
        mc.run(
            "smoke",
            tmp_path / "over-budget",
            root=123,
            replications=2,
            max_evaluations=79,
            max_wall_seconds=30,
            opt_in=False,
        )


def test_archived_negative_and_positive_confirmation_first_run_replays() -> None:
    """Original receipts retain their historical SHA, not today's source SHA."""
    mc = _research()
    repo_data = Path(__file__).parents[1] / "docs" / "research" / "issue148"
    local_data = Path(__file__).parent
    for stage, directory in (
        ("confirmation", "confirmation"),
        ("stable-independent-confirmation", "stable_confirmation"),
    ):
        receipt = repo_data / directory if repo_data.is_dir() else local_data / f"receipt-{stage}"
        if not receipt.exists():
            receipt = local_data / f"receipt-{directory}"
        if not receipt.exists() and stage == "stable-independent-confirmation":
            receipt = local_data / "receipt-stable-independent-confirmation"
        manifest = json.loads((receipt / "manifest.json").read_text(encoding="utf-8"))
        assert manifest["stage"] == stage
        first_variant = mc.STAGE_VARIANTS[stage][0]
        strata, count, tp, method = first_variant
        expected = mc.one_trial(
            root=manifest["root_seed"],
            stage=stage,
            replication=0,
            strata=strata,
            n=count,
            tp_method=tp,
            quantile_method=method,
            responses=mc.response_population(stage),
        )
        with (receipt / "raw.csv").open(newline="", encoding="utf-8") as stream:
            first = next(csv.DictReader(stream))
        assert first["site"] == expected[0]["site"]
        assert float(first["estimate"]) == pytest.approx(expected[0]["estimate"])
        assert float(first["exact"]) == pytest.approx(expected[0]["exact"])
        assert manifest["total_evaluations"] > 0


def test_stable_population_positive_result_is_non_degenerate() -> None:
    mc = _research()
    assert mc.RESPONSES != mc.STABLE_RESPONSES
    for site in mc.STABLE_RESPONSES.values():
        for response in site.values():
            assert response.slope > 0.0
            assert response.tp_bump > 0.0
            assert response.loss_width > 0.0
    rows = mc.one_trial(
        root=mc.ROOT_SEED,
        stage="stable-independent-confirmation",
        replication=0,
        strata=50,
        n=20,
        tp_method="random_tp",
        quantile_method="rank",
        responses=mc.STABLE_RESPONSES,
    )
    assert len(rows) == 24
    assert all(row["exact"] > 0 for row in rows)
    assert mc.lower_confidence_bound(100, 100) > 0.95
    assert mc.lower_confidence_bound(96, 100) < 0.95


def test_large_replication_confidence_limits_do_not_underflow() -> None:
    """Independent binomial reference values for a million trial replications."""
    mc = _research()
    assert mc.binomial_upper_tail(500000, 1_000_000, 0.5) == pytest.approx(0.5003989421806654, abs=2e-9)
    assert mc.binomial_upper_tail(500100, 1_000_000, 0.5) == pytest.approx(0.4211313785258083, abs=2e-9)
    assert mc.binomial_upper_tail(950000, 1_000_000, 0.95) == pytest.approx(0.5011898042280432, abs=2e-9)
    lower = mc.lower_confidence_bound(500000, 1_000_000)
    upper = mc.upper_confidence_bound(500000, 1_000_000)
    assert lower == pytest.approx(0.4991770739498, abs=1e-9)
    assert upper == pytest.approx(0.5008229260504, abs=1e-9)
    assert mc.binomial_upper_tail(500000, 1_000_000, lower) == pytest.approx(0.05, abs=2e-8)
    assert mc.binomial_upper_tail(500001, 1_000_000, upper) == pytest.approx(0.95, abs=2e-8)
    assert mc.lower_confidence_bound(1_000_000, 1_000_000) == pytest.approx(
        math.exp(math.log(0.05) / 1_000_000), abs=1e-14
    )
    assert mc.upper_confidence_bound(0, 1_000_000) == pytest.approx(-math.expm1(math.log(0.05) / 1_000_000), abs=1e-14)
    assert mc.lower_confidence_bound(1, 1_000_000) == pytest.approx(
        -math.expm1(math.log1p(-0.05) / 1_000_000), abs=1e-11
    )
    for count in (1_000, 100_000, 1_000_000):
        assert mc.lower_confidence_bound(count, count) <= 1.0
        assert mc.upper_confidence_bound(0, count) >= 0.0


def test_binomial_tail_extreme_values_are_finite() -> None:
    mc = _research()
    assert mc.binomial_upper_tail(0, 1_000_000, 0.5) == 1.0
    assert mc.binomial_upper_tail(1, 1_000_000, 0.0) == 0.0
    assert mc.binomial_upper_tail(1_000_000, 1_000_000, 1.0) == 1.0
    assert mc.binomial_upper_tail(1, 1_000_000, 1e-6) == pytest.approx(0.632120742768355, abs=1e-11)
    with pytest.raises(ValueError, match="invalid binomial"):
        mc.binomial_upper_tail(5, 4, 0.3)
    with pytest.raises(ValueError, match="invalid binomial"):
        mc.binomial_upper_tail(1, 4, float("nan"))
    with pytest.raises(ValueError, match="invalid confidence"):
        mc.upper_confidence_bound(2, 1)


def test_optional_scipy_binomial_backend(monkeypatch: pytest.MonkeyPatch) -> None:
    """The research-only high-count path uses SciPy when installed."""
    mc = _research()
    calls: list[tuple[float, float, float]] = []

    class _Special:
        def betainc(self, a: float, b: float, p: float) -> float:
            calls.append((a, b, p))
            return 0.375

    original = mc.importlib.import_module

    def fake_import(module: str) -> object:
        return _Special() if module == "scipy.special" else original(module)

    monkeypatch.setattr(mc.importlib, "import_module", fake_import)
    assert mc.binomial_upper_tail(500_000, 1_000_000, 0.5) == 0.375
    assert calls == [(500_000, 500_001, 0.5)]
