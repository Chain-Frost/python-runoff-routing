"""Deterministic S6 input-population and #119 dispatch contracts (synthetic only)."""

from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from decimal import Decimal
from pathlib import Path
from typing import Any, cast

import pytest

from runoff_routing.arr_design_batch import (
    DesignBatchResult,
    DesignConfigError,
    read_design_config,
    run_design_batch,
    write_design_outputs,
)
from runoff_routing.arr_result_summary import read_deterministic_results
from runoff_routing.engine_types import EngineSelection
from runoff_routing.project_batch import load_event_request, run_project_events
from runoff_routing.project_json import EmbeddedRun, Project, write_project
from runoff_routing.rorb_model import RunModel, from_json

EXAMPLES = Path(__file__).parents[1] / "examples"
IFD = EXAMPLES / "arr-design-synthetic-ifd.csv"
PATTERNS = EXAMPLES / "arr-design-synthetic-patterns.csv"
MODEL = EXAMPLES / "synthetic-run.json"
LEGACY = Path(__file__).parent / "fixtures" / "arr" / "2016-era-synthetic.txt"


def _audit(result: DesignBatchResult) -> dict[str, Any]:
    """Test-only nested JSON manifest view; preserve typed model interfaces."""
    return cast("dict[str, Any]", result.effective)


def _project(directory: Path) -> Path:
    run = from_json(MODEL.read_text(encoding="utf-8"))
    assert isinstance(run, RunModel)
    path = directory / "project.json"
    write_project(path, Project("arr_design_synthetic", "explicit", EmbeddedRun(run)))
    return path


def _config(directory: Path, *, ifd: Path = IFD, patterns: Path = PATTERNS) -> tuple[Path, dict[str, object]]:
    project = _project(directory)
    data: dict[str, object] = {
        "format": "python-runoff-routing-arr2019-design",
        "schema_version": 1,
        "project": str(project),
        "bom_ifd": str(ifd),
        "temporal_patterns": str(patterns),
        "pattern_kind": "point",
        "temporal_region": "SyntheticPoint",
        "arf_region": "South-West Western Australia",
        "catchment_area_km2": "2",
        "durations_min": [60, 120],
        "aep_labels": ["1%", "2%"],
        "dry_tail_min": 120,
        "engine": "python-cmd",
        "numerical_profile": "cmd-6.44",
        "loss": {"mode": "project_il_cl"},
    }
    path = directory / "design.json"
    path.write_text(json.dumps(data) + "\n", encoding="utf-8")
    return path, data


def _write_config(path: Path, data: dict[str, object]) -> None:
    path.write_text(json.dumps(data) + "\n", encoding="utf-8")


@pytest.mark.parametrize(
    ("gross", "total", "increments", "difference"),
    [
        ("12.034", "12.03", ["1.203", "10.827"], "-0.004"),
        ("12.035", "12.04", ["1.204", "10.836"], "0.005"),
        ("12.045", "12.04", ["1.204", "10.836"], "-0.005"),
    ],
)
def test_written_depth_profile_keeps_published_rainfall_and_prepared_input_distinct(
    tmp_path: Path, gross: str, total: str, increments: list[str], difference: str
) -> None:
    source = tmp_path / "source.csv"
    source.write_text(IFD.read_text().replace("1 hour,60,12,10", f"1 hour,60,{gross},10"), encoding="utf-8")
    config, data = _config(tmp_path, ifd=source)
    run = from_json(MODEL.read_text(encoding="utf-8"))
    assert isinstance(run, RunModel)
    # One square kilometre makes published ARF exactly one: the expected depth
    # and increments below are hand-calculable independent of ARF evaluation.
    catchment = replace(run.catchment, subareas=(replace(run.catchment.subareas[0], area_km2=Decimal(1)),))
    project = tmp_path / "unit-area.json"
    write_project(project, Project("unit_area", "explicit", EmbeddedRun(replace(run, catchment=catchment))))
    data.update(project=str(project), catchment_area_km2="1", durations_min=[60], aep_labels=["1%"])
    _write_config(config, data)
    published = run_design_batch(config)
    assert Decimal(_audit(published)["members"][0]["areal_total_mm"]) == Decimal(gross)
    data["rainfall_preparation"] = "published_arf_stm_2dp"
    _write_config(config, data)
    prepared = run_design_batch(config)
    assert prepared.succeeded
    member = _audit(prepared)["members"][0]
    assert Decimal(member["published_areal_total_mm"]) == Decimal(gross)
    assert member["areal_total_mm"] == total
    assert member["areal_increments_mm"] == increments
    assert Decimal(member["prepared_depth_minus_published_mm"]) == Decimal(difference)
    assert member["raw_pattern_percent"] == ["10", "90"]
    assert member["effective_storm"]["depths_mm"] == [total]
    assert member["native_arf_arithmetic_parity"] == "not_assessed"
    assert _audit(prepared)["method_profile"] == "arr2019-bom-published-arf-stm-2dp-burst-only-v1"
    assert _audit(prepared)["routed_native_reference_status"] == "not_assessed"
    write_design_outputs(tmp_path / "prepared", prepared)
    summary = read_deterministic_results(tmp_path / "prepared.effective.json", tmp_path / "prepared.json")
    assert summary.data["method_profile"] == _audit(prepared)["method_profile"]
    assert summary.data["source_files"] == _audit(prepared)["source_files"]


def test_written_depth_profile_does_not_silently_round_high_precision_patterns(tmp_path: Path) -> None:
    patterns = tmp_path / "patterns.csv"
    patterns.write_text(PATTERNS.read_text().replace("rare,10,90", "rare,10.001,89.999"), encoding="utf-8")
    config, data = _config(tmp_path, patterns=patterns)
    data.update(rainfall_preparation="published_arf_stm_2dp", durations_min=[60], aep_labels=["1%"])
    _write_config(config, data)
    result = run_design_batch(config)
    assert not result.succeeded
    assert _audit(result)["prepared_population"] == 0
    assert "0.01% resolution" in _audit(result)["cells"][0]["error"]


def test_unknown_rainfall_preparation_is_rejected(tmp_path: Path) -> None:
    config, data = _config(tmp_path)
    data["rainfall_preparation"] = "native-identical"
    _write_config(config, data)
    with pytest.raises(DesignConfigError, match="Unknown rainfall_preparation"):
        read_design_config(config)


def test_native_written_design_requires_explicit_native_configuration(tmp_path: Path) -> None:
    config, data = _config(tmp_path)
    data.update(engine="rorb-cmd", rainfall_preparation="published_arf_stm_2dp")
    _write_config(config, data)
    with pytest.raises(DesignConfigError, match="explicit native configuration"):
        run_design_batch(config)


def test_written_profile_does_not_admit_unqualified_preburst_conventions(tmp_path: Path) -> None:
    config, data = _config(tmp_path)
    data["rainfall_preparation"] = "published_arf_stm_2dp"
    data["loss"] = {
        "mode": "legacy_source_depth_burst_only",
        "arr_txt": str(LEGACY),
        "percentile": 50,
        "excess_policy": "reject",
    }
    _write_config(config, data)
    with pytest.raises(DesignConfigError, match="without preburst adjustment"):
        read_design_config(config)


def test_padded_bom_metadata_is_admitted_to_design_batch(tmp_path: Path) -> None:
    """Synthetic padded preamble must survive preparation without changing depth data."""
    raw = IFD.read_bytes()
    newline = b"\r\n" if b"\r\n" in raw else b"\n"
    for record in (
        b"Issued:,15 November 2026",
        b"Location Label:,SYNTHETIC EXAMPLE ONLY",
        b"Requested coordinate:,Latitude,-30.00500,Longitude,150.100",
        b"Nearest grid cell:,Latitude,30.00500 (S),Longitude,150.100 (E)",
    ):
        assert raw.count(record + newline) == 1
        raw = raw.replace(record + newline, record + b",," + newline, 1)

    source = tmp_path / "padded-ifd.csv"
    source.write_bytes(raw)
    config, data = _config(tmp_path, ifd=source)
    data["durations_min"] = [60]
    data["aep_labels"] = ["1%"]
    _write_config(config, data)

    result = run_design_batch(config)
    assert result.succeeded
    assert _audit(result)["expected_population"] == 10
    assert _audit(result)["prepared_population"] == 10
    assert _audit(result)["source_files"]["bom_ifd"]["sha256"] == hashlib.sha256(raw).hexdigest()
    members = cast("list[dict[str, object]]", _audit(result)["members"])
    assert len(members) == 10
    assert all(Decimal(str(item["raw_gross_total_mm"])) == Decimal(12) for item in members)
    assert all(item["execution_status"] == "computed_unvalidated" for item in members)
    assert source.read_bytes() == raw


def test_complete_duration_aep_tp_population_replays_through_common_api(tmp_path: Path) -> None:
    config, _ = _config(tmp_path)
    result = run_design_batch(config)
    assert result.succeeded
    assert _audit(result)["expected_population"] == 40
    assert _audit(result)["prepared_population"] == 40
    assert _audit(result)["input_population_complete"] is True
    assert all(item.status == "computed_unvalidated" for item in result.routed.outcomes)
    records = cast("list[dict[str, object]]", _audit(result)["members"])
    assert [record["original_tp_id"] for record in records[:10]] == [f"{value:04d}" for value in range(1, 11)]
    assert [record["source_order"] for record in records[:10]] == list(range(1, 11))
    assert [record["ensemble_order"] for record in records[:10]] == list(range(1, 11))
    assert [record["original_tp_id"] for record in records[20:30]] == [f"{value:04d}" for value in range(101, 111)]
    assert [item["status"] for item in _audit(result)["cells"]] == ["ready"] * 4
    assert len({outcome.event_id for outcome in result.routed.outcomes}) == 40
    assert _audit(result)["source_files"]["design_config"]["sha256"] == hashlib.sha256(config.read_bytes()).hexdigest()
    assert _audit(result)["generated_input_reference_status"] == "not_assessed"
    assert _audit(result)["critical_duration_rule"] == "not_selected_unverified"
    assert _audit(result)["representative_event_rule"] == "not_selected_unverified"

    sources = _audit(result)["source_files"]
    assert sources["bom_ifd"]["sha256"] == hashlib.sha256(IFD.read_bytes()).hexdigest()
    assert sources["temporal_patterns"]["sha256"] == hashlib.sha256(PATTERNS.read_bytes()).hexdigest()
    assert sources["temporal_patterns"]["members"][0]["sha256"] == hashlib.sha256(PATTERNS.read_bytes()).hexdigest()
    assert all(record["effective_losses"] is None for record in records)
    for record in records:
        assert Decimal(str(record["raw_gross_total_mm"])) == sum(
            (Decimal(value) for value in cast("list[str]", record["raw_gross_increments_mm"])), Decimal(0)
        )
        assert Decimal(str(record["areal_total_mm"])) == sum(
            (Decimal(value) for value in cast("list[str]", record["areal_increments_mm"])), Decimal(0)
        )
        assert record["arf_factor"] is not None
        storm = cast("dict[str, object]", record["effective_storm"])
        assert storm["depths_mm"] == [record["areal_total_mm"]]
        assert record["execution_status"] == "computed_unvalidated"
    paths = write_design_outputs(tmp_path / "design-results", result)
    assert len(paths) == 6
    request = load_event_request(tmp_path / "design-results.events.json")
    replay = run_project_events(tmp_path / "project.json", request, selection=EngineSelection.for_engine("python-cmd"))
    assert replay.succeeded
    assert [(a.event_id, a.model_sha256, a.hydrographs, a.physical_time_hours) for a in replay.outcomes] == [
        (a.event_id, a.model_sha256, a.hydrographs, a.physical_time_hours) for a in result.routed.outcomes
    ]
    assert json.loads((tmp_path / "design-results.json").read_text())["requested_event_count"] == 40
    assert "Computed: 40" in (tmp_path / "design-results.txt").read_text()
    assert "Input: 40/40" in (tmp_path / "design-results.summary.txt").read_text()
    before = tuple(path.read_bytes() for path in paths)
    with pytest.raises(DesignConfigError, match="already exist"):
        write_design_outputs(tmp_path / "design-results", result)
    assert before == tuple(path.read_bytes() for path in paths)


def test_missing_tenth_tp_is_incomplete_without_substitution(tmp_path: Path) -> None:
    source = tmp_path / "missing.csv"
    rows = PATTERNS.read_text(encoding="utf-8").splitlines()
    source.write_text("\n".join(line for line in rows if not line.startswith("0110,")) + "\n")
    config, _ = _config(tmp_path, patterns=source)
    result = run_design_batch(config)
    assert not result.succeeded
    assert _audit(result)["expected_population"] == 40
    assert _audit(result)["prepared_population"] == 20
    assert [cell["status"] for cell in _audit(result)["cells"]] == ["ready", "ready", "input_error", "input_error"]
    assert all(cell["expected_count"] == 10 for cell in _audit(result)["cells"])
    assert all(cell["ready_count"] == 0 for cell in _audit(result)["cells"][2:])
    assert _audit(result)["cells"][2]["unqualified_source_candidate_ids"] == [
        f"{value:04d}" for value in range(101, 110)
    ]
    assert _audit(result)["cells"][2]["unqualified_source_candidate_count"] == 9
    assert len(result.routed.outcomes) == 20
    assert all(outcome.status == "computed_unvalidated" for outcome in result.routed.outcomes)
    assert _audit(result)["status"] == "incomplete"
    write_design_outputs(tmp_path / "incomplete", result)
    assert "FAILED 120 min" in (tmp_path / "incomplete.summary.txt").read_text()
    assert (tmp_path / "incomplete.events.json").exists()


def test_source_label_does_not_convert_ey_to_aep(tmp_path: Path) -> None:
    config, data = _config(tmp_path)
    data["aep_labels"] = ["0.5EY"]
    _write_config(config, data)
    result = run_design_batch(config)
    assert not result.succeeded
    assert _audit(result)["expected_population"] == 20
    assert _audit(result)["prepared_population"] == 0
    assert len(result.routed.outcomes) == 0
    assert all(cell["status"] == "input_error" for cell in _audit(result)["cells"])
    assert all("not present" in cell["error"] for cell in _audit(result)["cells"])


@pytest.mark.parametrize(
    ("mode", "expected_source_il"),
    [
        ("legacy_source_depth_burst_only", "14.00"),
        ("legacy_ratio_areal_burst_only", None),
    ],
)
def test_legacy_burst_only_losses_applied_by_engine_once(
    tmp_path: Path, mode: str, expected_source_il: str | None
) -> None:
    config, data = _config(tmp_path)
    data["aep_labels"] = ["1%"]
    data["durations_min"] = [60]
    data["loss"] = {"mode": mode, "arr_txt": str(LEGACY), "percentile": 50, "excess_policy": "reject"}
    _write_config(config, data)
    result = run_design_batch(config)
    assert result.succeeded
    assert len(result.routed.outcomes) == 10
    for record in _audit(result)["members"]:
        applied = record["loss"]
        assert applied["preburst_source_depth_mm"] == "7.00"
        assert applied["storm_initial_loss_mm"] == "21.0"
        assert applied["continuing_loss_mm_per_hour"] == "2.00"
        if expected_source_il is not None:
            assert applied["burst_initial_loss_mm"] == expected_source_il
            assert applied["preburst_depth_basis"] == "as_exported_depth"
        else:
            assert applied["preburst_depth_basis"] == "ratio_x_areal_reduced_design_depth"
            assert applied["rainfall_basis_total_mm"] == record["areal_total_mm"]
        assert record["effective_losses"]["initial_loss_mm"] == applied["burst_initial_loss_mm"]
        assert record["engine_loss_application"] == "once_by_selected_engine"
    assert _audit(result)["source_files"]["legacy_arr"]["sha256"] == hashlib.sha256(LEGACY.read_bytes()).hexdigest()


@pytest.mark.parametrize(
    ("ratio", "should_succeed"),
    [("1.020", True), ("3.000", False)],
)
def test_ratio_excess_policy_checks_applied_depth_not_source_depth(
    tmp_path: Path, ratio: str, should_succeed: bool
) -> None:
    """Source preburst > storm IL is not itself a ratio-method failure."""
    source = tmp_path / "source-with-high-exported-depth.txt"
    fixture = LEGACY.read_text(encoding="utf-8")
    original = "60 (1.0),2.0 (0.010),7.00 (1.020),"
    assert fixture.count(original) == 1
    source.write_text(fixture.replace(original, f"60 (1.0),2.0 (0.010),30.00 ({ratio}),"), encoding="utf-8")
    config, data = _config(tmp_path)
    data["aep_labels"] = ["1%"]
    data["durations_min"] = [60]
    data["loss"] = {
        "mode": "legacy_ratio_areal_burst_only",
        "arr_txt": str(source),
        "percentile": 50,
        "excess_policy": "reject",
    }
    _write_config(config, data)
    result = run_design_batch(config)
    assert result.succeeded is should_succeed
    if should_succeed:
        assert len(result.routed.outcomes) == 10
        for record in _audit(result)["members"]:
            loss = record["loss"]
            assert loss["preburst_source_depth_mm"] == "30.00"
            assert Decimal(loss["preburst_applied_depth_mm"]) < Decimal(21)
            assert loss["preburst_depth_basis"] == "ratio_x_areal_reduced_design_depth"
            assert "BURST_IL_FROM_SELECTED_RATIO_DEPTH_ONCE" in loss["operations"]
            assert "PREBURST_EXCEEDS_IL_CLAMPED_EXPLICITLY_NO_EXCESS_STORM_RAINFALL" not in loss["operations"]
            assert record["execution_status"] == "computed_unvalidated"
    else:
        assert _audit(result)["input_population_complete"] is False
        assert _audit(result)["cells"][0]["status"] == "input_error"
        assert "Ratio-derived preburst exceeds storm IL" in _audit(result)["cells"][0]["error"]
        assert len(result.routed.outcomes) == 0


def test_exported_source_depth_over_il_still_rejects_source_depth_method(tmp_path: Path) -> None:
    config, data = _config(tmp_path)
    source = tmp_path / "excess-source.txt"
    source.write_text(
        LEGACY.read_text(encoding="utf-8").replace(
            "60 (1.0),2.0 (0.010),7.00 (1.020),",
            "60 (1.0),2.0 (0.010),30.00 (1.020),",
        ),
        encoding="utf-8",
    )
    data["aep_labels"] = ["1%"]
    data["durations_min"] = [60]
    data["loss"] = {
        "mode": "legacy_source_depth_burst_only",
        "arr_txt": str(source),
        "percentile": 50,
        "excess_policy": "reject",
    }
    _write_config(config, data)
    result = run_design_batch(config)
    assert result.succeeded is False
    assert "Preburst exceeds storm IL" in _audit(result)["cells"][0]["error"]


def test_unsafe_or_unsupported_config_rejected_before_execution(tmp_path: Path) -> None:
    config, data = _config(tmp_path)
    data["engine"] = "rorb-cmd"
    _write_config(config, data)
    with pytest.raises(DesignConfigError, match="native rorb-cmd"):
        read_design_config(config)
    data["engine"] = "python-cmd"
    data["durations_min"] = [60, 60]
    _write_config(config, data)
    with pytest.raises(DesignConfigError, match="Duplicate duration"):
        read_design_config(config)
    data["durations_min"] = [60]
    data["catchment_area_km2"] = "3"
    _write_config(config, data)
    with pytest.raises(DesignConfigError, match="sum of project subareas"):
        run_design_batch(config)


def test_missing_arf_or_time_grid_is_explicit_failure(tmp_path: Path) -> None:
    config, data = _config(tmp_path)
    data["dry_tail_min"] = 50
    _write_config(config, data)
    result = run_design_batch(config)
    assert not result.succeeded
    assert _audit(result)["prepared_population"] == 0
    assert all(cell["status"] == "input_error" for cell in _audit(result)["cells"])
    assert all("dry tail" in cell["error"] for cell in _audit(result)["cells"])
