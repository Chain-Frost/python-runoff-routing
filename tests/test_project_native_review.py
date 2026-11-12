"""S5-P2 source-pinned native CMD diagnostics; entirely synthetic evidence."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

import pytest

from runoff_routing.integration import canonical_run_bytes, read_run_json, run_model
from runoff_routing.project_json import LegacyRunFiles, Project, ProjectError, SourceFile, main, write_project
from runoff_routing.project_native_review import review_project_native_capture, write_native_review_json
from runoff_routing.rorb_inspect import inspect_file

ROOT = Path(__file__).absolute().parents[1]
ENGINE_SHA = "a" * 64


def _synthetic_case(tmp_path: Path) -> tuple[Path, Path, str]:
    """Write an S0-shaped, source-verified manufactured fixture (not RORB output)."""
    model = read_run_json((ROOT / "examples/synthetic-run.json").read_text(encoding="utf-8"))
    project_folder = tmp_path / "Historic RORB Project"
    evidence = tmp_path / "retained S0 evidence"
    project_folder.mkdir()
    evidence.mkdir()
    raw_par, raw_catg, raw_stm = canonical_run_bytes(model)
    sources: list[SourceFile] = []
    for name, contents in (("run.par", raw_par), ("catchment.catg", raw_catg), ("event.stm", raw_stm)):
        (project_folder / name).write_bytes(contents)
        (evidence / name).write_bytes(contents)
        sources.append(SourceFile(name, hashlib.sha256(contents).hexdigest()))
    project = project_folder / "project.json"
    write_project(
        project,
        Project(
            "historic-synthetic",
            "legacy-rorb",
            LegacyRunFiles(sources[0], sources[1], sources[2]),
        ),
    )

    calculated = run_model(model)
    depths = calculated.prints[0].discharge_m3_s
    native_times = [f"{(index + 1) * calculated.numerical.dt_hours:.2f}" for index in range(len(depths))]
    rows = "\n".join(f"{index + 1} {native_times[index]} {flow:.4f}" for index, flow in enumerate(depths))
    text = (
        "RORBWin Output File\n"
        "Program version 6.44 synthetic\n"
        "Time increment (hours)= 0.50\n"
        f"Duration of calculations: {model.storm.calculation_increments}\n"
        "Inc Time Hyd001\n"
        f"{rows}\n"
        "End of synthetic hydrograph\n"
    )
    output = evidence / "historic.out"
    output.write_text(text, encoding="utf-8")
    inspection = inspect_file(output)
    assert inspection.hydrographs is not None
    assert inspection.status == "partial"
    assert inspection.hydrographs.rows[0].increment == 1
    assert inspection.hydrographs.rows[-1].increment == model.storm.calculation_increments + 1

    def stamp(path: Path) -> dict[str, str | int]:
        raw = path.read_bytes()
        return {"sha256": hashlib.sha256(raw).hexdigest(), "size_bytes": len(raw)}

    manifest: dict[str, Any] = {
        "schema_version": 1,
        "case_id": "synthetic-legacy",
        "engine": {
            "kind": "RORB_CMD",
            "observed_version": "6.44",
            "executable": {"sha256": ENGINE_SHA, "size_bytes": 123},
        },
        "effective_settings": {
            "timestep_hours": str(model.storm.timestep_hours),
            "cmd_writer": {
                "kc": str(model.parameters.routing[0].kc),
                "m": str(model.parameters.routing[0].m),
                "initial_loss_mm": str(model.parameters.losses[0].initial_loss_mm),
                "continuing": str(model.parameters.losses[0].continuing),
                "loss_model": 1,
                "num_isa": 1,
                "num_bursts": 1,
            },
        },
        "requested_print_locations": {"Hyd001": "synthetic explicitly mapped print_1"},
        "provenance_gaps": [],
        "expected_steps": len(depths),
        "hydrograph_check": {
            "columns": ["Inc", "Time", "Hyd001"],
            "rows": len(depths),
            "raw_time_labels": native_times,
        },
        "diagnostics": {"errors": [], "warnings": []},
        "outcome": "success",
        "inputs": {
            "parameters": {"path": "run.par", **stamp(evidence / "run.par"), "generated": True},
            "catchment": {"staged": "catchment.catg", "source_fingerprint": stamp(evidence / "catchment.catg")},
            "storm": {"staged": "event.stm", "source_fingerprint": stamp(evidence / "event.stm")},
        },
        "outputs": [{"path": "historic.out", **stamp(output)}],
    }
    target = evidence / "manifest.json"
    contents = json.dumps(manifest, indent=2, sort_keys=True).encode("utf-8")
    target.write_bytes(contents)
    return project, target, hashlib.sha256(contents).hexdigest()


def _mutate_manifest(manifest: Path, change: str) -> str:
    content: dict[str, Any] = json.loads(manifest.read_text(encoding="utf-8"))
    if change == "source":
        content["inputs"]["catchment"]["source_fingerprint"]["sha256"] = "f" * 64
    elif change == "effective":
        content["effective_settings"]["cmd_writer"]["m"] = "0.85"
    elif change == "horizon":
        content["expected_steps"] = 5
    elif change == "time":
        content["hydrograph_check"]["raw_time_labels"][0] = "0.00"
    elif change == "column":
        content["requested_print_locations"] = {"Hyd999": "elsewhere"}
    elif change == "engine":
        content["engine"]["kind"] = "RORBwin"
    elif change == "incomplete":
        content["outcome"] = "captured_unverified"
    elif change == "warnings":
        content["diagnostics"]["warnings"] = ["synthetic warning"]
    else:
        content["provenance_gaps"] = ["unverified source"]
    bytes_out = json.dumps(content, indent=2, sort_keys=True).encode("utf-8")
    manifest.write_bytes(bytes_out)
    return hashlib.sha256(bytes_out).hexdigest()


def test_s0_manifest_and_raw_cmd_output_are_reviewed_without_claiming_parity(tmp_path: Path) -> None:
    project, manifest, digest = _synthetic_case(tmp_path)
    result = review_project_native_capture(
        project,
        manifest,
        manifest_sha256=digest,
        engine_executable_sha256=ENGINE_SHA,
        model_print_id="print_1",
        native_column_id="Hyd001",
    )
    assert result.project_id == "historic-synthetic"
    assert result.case_id == "synthetic-legacy"
    assert result.manifest_sha256 == digest
    assert result.engine_executable_sha256 == ENGINE_SHA
    assert result.mapping_evidence == "caller_asserted"
    assert result.raw_increment_tokens == tuple(str(i) for i in range(1, 7))
    assert result.raw_time_tokens[0] == "0.50"
    assert result.raw_time_tokens[-1] == "3.00"
    assert result.printed.model_print_id == "print_1"
    assert result.printed.native_column_id == "Hyd001"
    assert result.printed.printed_discharge_parity.within_print_budget
    assert result.printed.native_reporting.sample_count == 6
    assert result.printed.native_reporting.physical_trapezoid_m3 >= 0
    assert result.printed.numerical_acceptance == "unassessed"
    assert result.numerical_acceptance == "unassessed"
    report = json.loads(result.to_json())
    assert report["review_status"] == "source_verified_diagnostic"
    assert report["printed"]["native_reporting"]["raw_native_time_tokens"][0] == "0.50"
    assert report["native_output_sha256"] == hashlib.sha256((manifest.parent / "historic.out").read_bytes()).hexdigest()


def test_native_review_is_read_only_and_no_clobber(tmp_path: Path) -> None:
    project, manifest, digest = _synthetic_case(tmp_path)
    before = (project.read_bytes(), manifest.read_bytes(), (manifest.parent / "historic.out").read_bytes())
    result = review_project_native_capture(
        project,
        manifest,
        manifest_sha256=digest,
        engine_executable_sha256=ENGINE_SHA,
        model_print_id="print_1",
        native_column_id="Hyd001",
    )
    target = tmp_path / "diagnostic.json"
    write_native_review_json(target, result)
    assert target.read_bytes().endswith(b"\n")
    with pytest.raises(FileExistsError):
        write_native_review_json(target, result)
    assert before == (project.read_bytes(), manifest.read_bytes(), (manifest.parent / "historic.out").read_bytes())


@pytest.mark.parametrize(
    ("changed", "message"),
    [
        ("source", "catchment"),
        ("effective", "m does not match"),
        ("horizon", "expected steps"),
        ("time", "time labels"),
        ("column", "native column"),
        ("engine", "RORB_CMD"),
        ("incomplete", "not a completed"),
        ("warnings", "errors or warnings"),
        ("gaps", "provenance gaps"),
    ],
)
def test_native_manifest_inconsistency_rejected(tmp_path: Path, changed: str, message: str) -> None:
    project, manifest, _ = _synthetic_case(tmp_path)
    new_sha = _mutate_manifest(manifest, changed)
    with pytest.raises(ProjectError, match=message):
        review_project_native_capture(
            project,
            manifest,
            manifest_sha256=new_sha,
            engine_executable_sha256=ENGINE_SHA,
            model_print_id="print_1",
            native_column_id="Hyd001",
        )


def test_manifest_hash_and_engine_hash_must_be_pinned(tmp_path: Path) -> None:
    project, manifest, digest = _synthetic_case(tmp_path)
    with pytest.raises(ProjectError, match="SHA-256"):
        review_project_native_capture(
            project,
            manifest,
            manifest_sha256="0" * 64,
            engine_executable_sha256=ENGINE_SHA,
            model_print_id="print_1",
            native_column_id="Hyd001",
        )
    with pytest.raises(ProjectError, match="executable"):
        review_project_native_capture(
            project,
            manifest,
            manifest_sha256=digest,
            engine_executable_sha256="f" * 64,
            model_print_id="print_1",
            native_column_id="Hyd001",
        )


def test_native_report_corruption_rejected_by_s0_manifest(tmp_path: Path) -> None:
    project, manifest, digest = _synthetic_case(tmp_path)
    with (manifest.parent / "historic.out").open("ab") as stream:
        stream.write(b"\nchanged")
    with pytest.raises(ProjectError, match="invalid or changed evidence"):
        review_project_native_capture(
            project,
            manifest,
            manifest_sha256=digest,
            engine_executable_sha256=ENGINE_SHA,
            model_print_id="print_1",
            native_column_id="Hyd001",
        )


def test_missing_or_unmapped_print_id_is_rejected(tmp_path: Path) -> None:
    project, manifest, digest = _synthetic_case(tmp_path)
    with pytest.raises(ProjectError, match="print mapping"):
        review_project_native_capture(
            project,
            manifest,
            manifest_sha256=digest,
            engine_executable_sha256=ENGINE_SHA,
            model_print_id="missing",
            native_column_id="Hyd001",
        )


def test_native_review_does_not_launch_reference_binary(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def prohibited(*_args: object, **_kwargs: object) -> None:
        pytest.fail("Native engine execution prohibited")

    monkeypatch.setattr(subprocess, "run", prohibited)
    project, manifest, digest = _synthetic_case(tmp_path)
    report = review_project_native_capture(
        project,
        manifest,
        manifest_sha256=digest,
        engine_executable_sha256=ENGINE_SHA,
        model_print_id="print_1",
        native_column_id="Hyd001",
    )
    assert report.review_status == "source_verified_diagnostic"


def test_project_native_cli_is_no_clobber_and_reports_explicit_unassessed_status(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    project, manifest, digest = _synthetic_case(tmp_path)
    target = tmp_path / "native-review.json"
    args = [
        "review-native",
        str(project),
        str(manifest),
        digest,
        ENGINE_SHA,
        "print_1",
        "Hyd001",
        str(target),
    ]
    assert main(args) == 0
    receipt = json.loads(capsys.readouterr().out)
    assert receipt["review_status"] == "source_verified_diagnostic"
    assert receipt["numerical_acceptance"] == "unassessed"
    assert receipt["printed_within_budget"] is True
    assert json.loads(target.read_text(encoding="utf-8"))["mapping_evidence"] == "caller_asserted"
    assert main(args) == 2
    assert "failed" in capsys.readouterr().err.lower()


def test_native_review_rejects_zero_based_cmd_row_identity(tmp_path: Path) -> None:
    project, manifest, _ = _synthetic_case(tmp_path)
    output = manifest.parent / "historic.out"
    before = output.read_text(encoding="utf-8")
    lines = before.splitlines()
    start = lines.index("Inc Time Hyd001") + 1
    for index in range(6):
        row = lines[start + index].split()
        row[0] = str(index)
        lines[start + index] = " ".join(row)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    data: dict[str, Any] = json.loads(manifest.read_text(encoding="utf-8"))
    raw = output.read_bytes()
    data["outputs"][0]["sha256"] = hashlib.sha256(raw).hexdigest()
    data["outputs"][0]["size_bytes"] = len(raw)
    manifest_bytes = json.dumps(data, indent=2, sort_keys=True).encode("utf-8")
    manifest.write_bytes(manifest_bytes)
    with pytest.raises(ProjectError, match="1-based sequence"):
        review_project_native_capture(
            project,
            manifest,
            manifest_sha256=hashlib.sha256(manifest_bytes).hexdigest(),
            engine_executable_sha256=ENGINE_SHA,
            model_print_id="print_1",
            native_column_id="Hyd001",
        )
