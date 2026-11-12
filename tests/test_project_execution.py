"""S5 JSON project routing bridge, with synthetic inputs and no native execution."""

from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import replace
from decimal import Decimal
from pathlib import Path

import pytest

from runoff_routing.integration import canonical_run_bytes, run_model
from runoff_routing.project_execution import (
    compare_routed_projects,
    run_project,
    write_execution_json,
)
from runoff_routing.project_json import (
    EmbeddedRun,
    ExternalAsset,
    LegacyRunFiles,
    Project,
    ProjectError,
    SourceFile,
    main,
    write_project,
)
from runoff_routing.rorb_model import RunModel, from_json, to_json

EXAMPLE = Path(__file__).parents[1] / "examples" / "synthetic-run.json"


def _model() -> RunModel:
    restored = from_json(EXAMPLE.read_text(encoding="utf-8"))
    assert isinstance(restored, RunModel)
    return restored


def _embedded(root: Path, *, profile: str = "explicit") -> Path:
    path = root / "embedded.json"
    if profile == "explicit":
        selected = "explicit"
    elif profile == "legacy-rorb":
        selected = "legacy-rorb"
    else:
        selected = "arr-2026v1"
    write_project(path, Project("example", selected, EmbeddedRun(_model())))
    return path


def _legacy(root: Path) -> Path:
    model = _model()
    par, catg, stm = canonical_run_bytes(model)
    directory = root / "Original RORB files"
    directory.mkdir()
    references: list[SourceFile] = []
    for name, contents in (("run.par", par), ("catchment.catg", catg), ("event.stm", stm)):
        path = directory / name
        path.write_bytes(contents)
        references.append(SourceFile(f"Original RORB files/{name}", hashlib.sha256(contents).hexdigest()))
    manifest = root / "legacy.json"
    write_project(
        manifest,
        Project("imported-legacy", "legacy-rorb", LegacyRunFiles(references[0], references[1], references[2])),
    )
    return manifest


def test_execute_embedded_json_calls_existing_s2_reference_exactly(tmp_path: Path) -> None:
    source = _embedded(tmp_path)
    result = run_project(source)
    assert result.calculation == run_model(_model())
    assert result.calculation_status == "computed_unvalidated"
    assert result.native_parity_status == "not_assessed"
    assert result.calculation.parity_status == "unassessed"
    assert result.calculation.output_time_convention == "model_elapsed_from_zero"
    assert result.project_sha256 == hashlib.sha256(source.read_bytes()).hexdigest()
    assert result.model_sha256 == hashlib.sha256(to_json(_model()).encode("utf-8")).hexdigest()
    assert result.source_file_hashes == ()
    assert result.to_csv() == result.calculation.to_csv()
    serialized = json.loads(result.to_json())
    assert serialized["calculation_status"] == "computed_unvalidated"
    assert serialized["native_parity_status"] == "not_assessed"
    assert len(serialized["calculation"]["prints"][0]["discharge_m3_s"]) == 6


def test_file_backed_rorb_and_embedded_json_produce_identical_python_ordinates(tmp_path: Path) -> None:
    source = _legacy(tmp_path)
    embedded = tmp_path / "same-model.json"
    write_project(embedded, Project("same-computation", "legacy-rorb", EmbeddedRun(_model())))
    a, b = run_project(source), run_project(embedded)
    assert a.source_kind == "rorb-files"
    assert b.source_kind == "embedded-run"
    assert a.source_file_hashes
    assert not b.source_file_hashes
    assert a.calculation == b.calculation
    assert a.model_sha256 == b.model_sha256
    comparison = compare_routed_projects(source, embedded)
    assert comparison.identical
    assert comparison.same_typed_model
    assert comparison.same_external_assets
    assert comparison.same_print_locations
    assert comparison.same_computed_ordinates
    assert comparison.first_difference is None
    assert comparison.native_parity_status == "not_assessed"


def test_exact_python_output_differences_are_reported_without_tolerance(tmp_path: Path) -> None:
    original = tmp_path / "original.json"
    edited = tmp_path / "edited.json"
    model = _model()
    write_project(original, Project("original", "explicit", EmbeddedRun(model)))
    new_routing = replace(model.parameters.routing[0], kc=Decimal(2))
    new_parameters = replace(model.parameters, routing=(new_routing,))
    write_project(edited, Project("edited", "explicit", EmbeddedRun(replace(model, parameters=new_parameters))))
    result = compare_routed_projects(original, edited)
    assert not result.identical
    assert not result.same_typed_model
    assert not result.same_computed_ordinates
    assert result.same_print_locations
    assert result.first_difference is not None
    assert result.first_difference.startswith("print_location.print_1.sample[")
    assert result.comparison_status == "diagnostic_only"


def test_cross_method_arr_and_legacy_profiles_fail_closed(tmp_path: Path) -> None:
    original = _embedded(tmp_path)
    modern = tmp_path / "arr.json"
    write_project(modern, Project("modern", "arr-2026v1", EmbeddedRun(_model())))
    with pytest.raises(ProjectError, match="S6 event adapter"):
        run_project(modern)
    with pytest.raises(ProjectError, match="cross-method"):
        compare_routed_projects(original, modern)


def test_unprocessed_rainfall_asset_is_not_ignored_in_solver(tmp_path: Path) -> None:
    asset_path = tmp_path / "rainfall-data.json"
    asset_path.write_bytes(b'{"datahub_version":"2026v1"}')
    asset = ExternalAsset(
        "rain",
        "rainfall",
        "arr_2026v1",
        SourceFile(asset_path.name, hashlib.sha256(asset_path.read_bytes()).hexdigest()),
    )
    source = tmp_path / "project.json"
    write_project(source, Project("example", "legacy-rorb", EmbeddedRun(_model()), (asset,)))
    with pytest.raises(ProjectError, match="unprocessed"):
        run_project(source)


def test_reference_only_external_evidence_is_hash_verified(tmp_path: Path) -> None:
    asset_path = tmp_path / "evidence.bin"
    asset_path.write_bytes(b"synthetic-reference")
    asset = ExternalAsset(
        "reference",
        "reference",
        "synthetic",
        SourceFile(asset_path.name, hashlib.sha256(asset_path.read_bytes()).hexdigest()),
    )
    source = tmp_path / "project.json"
    write_project(source, Project("example", "explicit", EmbeddedRun(_model()), (asset,)))
    result = run_project(source)
    assert len(result.source_file_hashes) == 1
    assert result.calculation_status == "computed_unvalidated"
    asset_path.write_bytes(b"modified")
    with pytest.raises(ProjectError, match="SHA-256"):
        run_project(source)


def test_unsupported_s2_loss_mode_rejected_before_producing_output(tmp_path: Path) -> None:
    model = _model()
    unsupported = replace(model, parameters=replace(model.parameters, loss_model=2))
    source = tmp_path / "unsupported.json"
    write_project(source, Project("unsupported", "explicit", EmbeddedRun(unsupported)))
    target = tmp_path / "report.json"
    with pytest.raises(ProjectError, match="Unsupported S1/S2"):
        write_execution_json(target, run_project(source))
    assert not target.exists()


def test_write_execution_report_is_no_clobber_and_retains_provenance(tmp_path: Path) -> None:
    source = _embedded(tmp_path)
    target = tmp_path / "result.json"
    result = run_project(source)
    write_execution_json(target, result)
    saved = json.loads(target.read_text(encoding="utf-8"))
    assert saved["model_sha256"] == result.model_sha256
    assert saved["project_sha256"] == hashlib.sha256(source.read_bytes()).hexdigest()
    assert saved["native_parity_status"] == "not_assessed"
    with pytest.raises(FileExistsError):
        write_execution_json(target, result)


def test_compare_routed_print_locations_requires_explicit_identity(tmp_path: Path) -> None:
    a, b = tmp_path / "a.json", tmp_path / "b.json"
    run = _model()
    write_project(a, Project("original", "explicit", EmbeddedRun(run)))
    new_location = replace(run.catchment.print_locations[0], label="Different output location")
    new_catchment = replace(run.catchment, print_locations=(new_location,))
    write_project(b, Project("relabelled", "explicit", EmbeddedRun(replace(run, catchment=new_catchment))))
    result = compare_routed_projects(a, b)
    assert not result.same_print_locations
    assert not result.same_typed_model
    assert not result.identical
    assert result.first_difference == "print_location.print_1"


def test_run_and_compare_routed_cli_have_explicit_status_and_exit_codes(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    a = _embedded(tmp_path)
    b = tmp_path / "same.json"
    write_project(b, Project("other-id", "explicit", EmbeddedRun(_model())))
    target = tmp_path / "calculation.json"
    assert main(["run", str(a), str(target)]) == 0
    receipt = json.loads(capsys.readouterr().out)
    assert receipt["status"] == "computed_unvalidated"
    assert receipt["native_parity_status"] == "not_assessed"
    assert target.exists()
    assert main(["run", str(a), str(target)]) == 2
    capsys.readouterr()
    assert main(["compare-runs", str(a), str(b)]) == 0
    same = json.loads(capsys.readouterr().out)
    assert same["same_computed_ordinates"]
    assert same["native_parity_status"] == "not_assessed"
    modern = tmp_path / "modern.json"
    write_project(modern, Project("modern", "arr-2026v1", EmbeddedRun(_model())))
    assert main(["compare-runs", str(a), str(modern)]) == 2


def test_native_execution_is_never_called(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    def prohibited(*_args: object, **_kwargs: object) -> None:
        pytest.fail("S5 project execution must not launch RORB")

    monkeypatch.setattr(subprocess, "run", prohibited)
    result = run_project(_embedded(tmp_path))
    assert result.calculation.prints
