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
from runoff_routing.project_regression import FORMAT, run_suite, write_suite_results
from runoff_routing.project_regression import main as regression_main
from runoff_routing.rorb_inspect import inspect_file

ROOT = Path(__file__).absolute().parents[1]
ENGINE_SHA = "a" * 64


def _synthetic_case(
    tmp_path: Path, *, effective_timestep: str = "0.5", printed_timestep: str = "0.50"
) -> tuple[Path, Path, str]:
    """Write an S0-shaped, source-verified manufactured fixture (not RORB output)."""
    model_json = (ROOT / "examples/synthetic-run.json").read_text(encoding="utf-8")
    model_document: dict[str, Any] = json.loads(model_json)
    model_document["model"]["storm"]["timestep_hours"] = effective_timestep
    model = read_run_json(json.dumps(model_document))
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
        f"Time increment (hours)= {printed_timestep}\n"
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


# S5 multi-case offline diagnostics use manufactured evidence only (no native programs).
def _suite_case(project: Path | None, manifest: Path | None, *, engine_hash: str = ENGINE_SHA) -> dict[str, Any]:
    def entry(path: Path) -> dict[str, str]:
        return {
            "path": path.relative_to(path.parents[2]).as_posix(),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }

    return {
        "case_id": "case-one",
        "project": entry(project) if project is not None else None,
        "native": {
            "manifest": entry(manifest),
            "engine_executable_sha256": engine_hash,
            "print_mapping": [{"model_print_id": "print_1", "native_column_id": "Hyd001"}],
        }
        if manifest is not None
        else None,
    }


def _suite_file(tmp_path: Path, entries: list[dict[str, Any]]) -> Path:
    target = tmp_path / "suite.json"
    target.write_text(
        json.dumps({"format": FORMAT, "schema_version": 1, "suite_id": "synthetic-suite", "cases": entries}),
        encoding="utf-8",
    )
    return target


def _restamp_native(manifest: Path, *, flow: str | None = None, reported_volume: str | None = None) -> None:
    original: dict[str, Any] = json.loads(manifest.read_text(encoding="utf-8"))
    output = manifest.parent / "historic.out"
    content = output.read_text(encoding="utf-8")
    if flow is not None:
        original_row = next(line for line in content.splitlines() if line.startswith("1 0.50 "))
        content = content.replace(original_row, f"1 0.50 {flow}")
    if reported_volume is not None:
        content = content.replace("Inc Time Hyd001", f"Volume,m³  {reported_volume}\nInc Time Hyd001")
    output.write_text(content, encoding="utf-8")
    original["outputs"][0]["size_bytes"] = len(output.read_bytes())
    original["outputs"][0]["sha256"] = hashlib.sha256(output.read_bytes()).hexdigest()
    manifest.write_text(json.dumps(original, indent=2, sort_keys=True), encoding="utf-8")


def test_offline_suite_classifies_every_case_with_source_and_numerics_separate(tmp_path: Path) -> None:
    first_root = tmp_path / "first"
    second_root = tmp_path / "second"
    third_root = tmp_path / "third"
    first_root.mkdir()
    second_root.mkdir()
    third_root.mkdir()
    passing_project, passing_manifest, _ = _synthetic_case(first_root)
    failing_project, failing_manifest, _ = _synthetic_case(second_root)
    unsupported_project, unsupported_manifest, _ = _synthetic_case(third_root)
    _restamp_native(failing_manifest, flow="999.0000")
    tampered_manifest: dict[str, Any] = json.loads(unsupported_manifest.read_text(encoding="utf-8"))
    tampered_manifest["engine"]["kind"] = "RORBwin"
    unsupported_manifest.write_text(json.dumps(tampered_manifest), encoding="utf-8")
    one = _suite_case(passing_project, passing_manifest)
    two = _suite_case(failing_project, failing_manifest)
    three = _suite_case(unsupported_project, unsupported_manifest)
    four = _suite_case(passing_project, None)
    five = _suite_case(passing_project, passing_manifest)
    six = _suite_case(passing_project, passing_manifest)
    two["case_id"] = "case-two"
    three["case_id"] = "case-three"
    four["case_id"] = "case-four"
    five["case_id"] = "case-five"
    six["case_id"] = "case-six"
    five["project"]["sha256"] = "0" * 64
    six["native"]["print_mapping"].append({"model_print_id": "print_1", "native_column_id": "Hyd002"})
    suite = _suite_file(tmp_path, [one, two, three, four, five, six])
    result = run_suite(suite)
    assert len(result.cases) == 6
    assert [case.classification for case in result.cases] == [
        "computed/pass",
        "computed/fail",
        "unsupported",
        "incomplete",
        "invalid",
        "invalid",
    ]
    assert result.cases[0].source_verification == "verified"
    assert result.cases[0].execution_status == "computed_unvalidated"
    assert result.cases[1].source_verification == "verified"
    assert result.cases[1].native_print_budget == "outside"
    assert result.cases[0].reviews[0].raw_increment_tokens == ("1", "2", "3", "4", "5", "6")
    assert result.cases[0].reviews[0].raw_time_tokens[0] == "0.50"
    assert result.cases[0].reviews[0].mapping_evidence == "caller_asserted"
    report = json.loads(result.to_json())
    assert report["native_numerical_acceptance"] == "unassessed"
    assert report["counts"]["computed/fail"] == 1
    assert report["counts"]["invalid"] == 2
    assert report["cases"][0]["prints"][0]["printed"]["samples"] == 6
    assert report["cases"][0]["control_vector_order"]
    assert report["cases"][0]["effective_settings"]
    assert result.to_csv().count("case-one,computed/pass") == 6
    assert result.to_csv().count("case-two,computed/fail") == 6


def test_offline_suite_preserves_verified_native_reported_volume_without_gate_inference(tmp_path: Path) -> None:
    root = tmp_path / "single"
    root.mkdir()
    project, manifest, _ = _synthetic_case(root)
    _restamp_native(manifest, reported_volume="1.23E+04")
    suite = _suite_file(tmp_path, [_suite_case(project, manifest)])
    result = run_suite(suite)
    assert result.cases[0].classification == "computed/pass"
    audit = result.cases[0].reviews[0].printed.native_reporting
    assert str(audit.reported_native_volume_m3) == "1.23E+4"
    assert audit.raw_native_time_tokens is not None
    assert result.cases[0].reviews[0].native_volume_source == "unique_single_column_out"
    assert (
        json.loads(result.to_json())["cases"][0]["prints"][0]["reporting"]["native_reported_volume_token"]
        == result.cases[0].reviews[0].native_reported_volume_text
    )


def test_offline_suite_handles_incomplete_capture_and_unavailable_file(tmp_path: Path) -> None:
    root = tmp_path / "case"
    root.mkdir()
    project, manifest, _ = _synthetic_case(root)
    native: dict[str, Any] = json.loads(manifest.read_text(encoding="utf-8"))
    native["outcome"] = "incomplete_output"
    manifest.write_text(json.dumps(native), encoding="utf-8")
    case = _suite_case(project, manifest)
    missing = _suite_case(project, manifest)
    missing["case_id"] = "missing-case"
    missing["native"]["manifest"]["path"] = "absent/manifest.json"
    suite = _suite_file(tmp_path, [case, missing])
    assert [item.classification for item in run_suite(suite).cases] == ["incomplete", "incomplete"]


def test_offline_suite_tampering_unknown_keys_and_unmodified_inputs(tmp_path: Path) -> None:
    root = tmp_path / "case"
    root.mkdir()
    project, manifest, _ = _synthetic_case(root)
    originals = (project.read_bytes(), manifest.read_bytes(), (manifest.parent / "historic.out").read_bytes())
    suite = _suite_file(tmp_path, [_suite_case(project, manifest)])
    output, csv_file = tmp_path / "summary.json", tmp_path / "samples.csv"
    result = run_suite(suite)
    write_suite_results(output, result, details_csv=csv_file)
    assert output.exists()
    assert csv_file.exists()
    with pytest.raises(FileExistsError):
        write_suite_results(tmp_path / "another.json", result, details_csv=csv_file)
    assert not (tmp_path / "another.json").exists()
    assert originals == (project.read_bytes(), manifest.read_bytes(), (manifest.parent / "historic.out").read_bytes())
    assert regression_main([str(suite), str(tmp_path / "once.json")]) == 0
    assert regression_main([str(suite), str(tmp_path / "once.json")]) == 2
    case = _suite_case(project, manifest)
    case["native"]["unknown_option"] = "do-not-guess"
    suite.write_text(
        json.dumps({"format": FORMAT, "schema_version": 1, "suite_id": "synthetic-suite", "cases": [case]}),
        encoding="utf-8",
    )
    assert run_suite(suite).cases[0].classification == "invalid"
    suite.write_text('{"format":"' + FORMAT + '","format":"' + FORMAT + '"}', encoding="utf-8")
    with pytest.raises(ProjectError, match="Duplicate"):
        run_suite(suite)


@pytest.mark.parametrize("printed_timestep", ["0.12", "0.13"])
def test_native_rounded_timestep_remains_source_verified(tmp_path: Path, printed_timestep: str) -> None:
    """A 0.125-hour source can be displayed to two decimals without losing its identity."""
    root = tmp_path / "case"
    root.mkdir()
    project, manifest, digest = _synthetic_case(root, effective_timestep="0.125", printed_timestep=printed_timestep)
    checked = review_project_native_capture(
        project,
        manifest,
        manifest_sha256=digest,
        engine_executable_sha256=ENGINE_SHA,
        model_print_id="print_1",
        native_column_id="Hyd001",
    )
    assert checked.raw_time_tokens[0] == "0.12"
    assert checked.raw_time_tokens[-1] == "0.75"
    assert checked.mapping_evidence == "caller_asserted"
    assert checked.numerical_acceptance == "unassessed"
    suite = _suite_file(tmp_path, [_suite_case(project, manifest)])
    outcome = run_suite(suite).cases[0]
    assert outcome.classification == "computed/pass"
    assert outcome.source_verification == "verified"
    assert outcome.execution_status == "computed_unvalidated"


def test_native_timestep_discrepancy_outside_header_precision_rejected(tmp_path: Path) -> None:
    project, manifest, digest = _synthetic_case(tmp_path, effective_timestep="0.125", printed_timestep="0.122")
    with pytest.raises(ProjectError, match="beyond its printed precision"):
        review_project_native_capture(
            project,
            manifest,
            manifest_sha256=digest,
            engine_executable_sha256=ENGINE_SHA,
            model_print_id="print_1",
            native_column_id="Hyd001",
        )


def test_native_raw_clock_must_match_exact_source_timestep(tmp_path: Path) -> None:
    project, manifest, _ = _synthetic_case(tmp_path, effective_timestep="0.125", printed_timestep="0.12")
    output = manifest.parent / "historic.out"
    text = output.read_text(encoding="utf-8")
    assert "1 0.12 " in text
    output.write_text(text.replace("1 0.12 ", "1 0.14 ", 1), encoding="utf-8")
    capture: dict[str, Any] = json.loads(manifest.read_text(encoding="utf-8"))
    output_bytes = output.read_bytes()
    capture["outputs"][0]["sha256"] = hashlib.sha256(output_bytes).hexdigest()
    capture["outputs"][0]["size_bytes"] = len(output_bytes)
    capture["hydrograph_check"]["raw_time_labels"][0] = "0.14"
    revised = json.dumps(capture, sort_keys=True, indent=2).encode("utf-8")
    manifest.write_bytes(revised)
    with pytest.raises(ProjectError, match="raw time labels differ"):
        review_project_native_capture(
            project,
            manifest,
            manifest_sha256=hashlib.sha256(revised).hexdigest(),
            engine_executable_sha256=ENGINE_SHA,
            model_print_id="print_1",
            native_column_id="Hyd001",
        )


def test_offline_suite_rejects_unmapped_actual_native_column(tmp_path: Path) -> None:
    """An extra native column must not disappear from a passing suite decision."""
    root = tmp_path / "extra-column"
    root.mkdir()
    project, manifest, _ = _synthetic_case(root)
    output = manifest.parent / "historic.out"
    lines = output.read_text(encoding="utf-8").splitlines()
    header = lines.index("Inc Time Hyd001")
    lines[header] = "Inc Time Hyd001 Hyd002"
    for index in range(header + 1, header + 7):
        assert len(lines[index].split()) == 3
        lines[index] += " 999999.0000"
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    data: dict[str, Any] = json.loads(manifest.read_text(encoding="utf-8"))
    original = output.read_bytes()
    data["outputs"][0]["sha256"] = hashlib.sha256(original).hexdigest()
    data["outputs"][0]["size_bytes"] = len(original)
    data["hydrograph_check"]["columns"] = ["Inc", "Time", "Hyd001", "Hyd002"]
    manifest.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")

    outcome = run_suite(_suite_file(tmp_path, [_suite_case(project, manifest)])).cases[0]
    assert outcome.classification == "invalid"
    assert outcome.execution_status == "not_computed"
    assert outcome.source_verification == "failed"
    assert "column coverage" in (outcome.reason or "")


def test_offline_suite_preserves_recognised_unsupported_rorb_dialect(tmp_path: Path) -> None:
    """Supported source verification must not relabel an unsupported dialect invalid."""
    root = tmp_path / "impervious"
    root.mkdir()
    project, manifest, _ = _synthetic_case(root)
    catchment = project.parent / "catchment.catg"
    content = catchment.read_text(encoding="utf-8")
    marker = "C Impervious Fraction Data\n0, -99"
    assert content.count(marker) == 1
    catchment.write_text(content.replace(marker, "C Impervious Fraction Data\n2, -99"), encoding="utf-8")
    assert inspect_file(catchment).status == "unsupported"

    document: dict[str, Any] = json.loads(project.read_text(encoding="utf-8"))
    document["model_source"]["catchment"]["sha256"] = hashlib.sha256(catchment.read_bytes()).hexdigest()
    project.write_text(json.dumps(document, indent=2, sort_keys=True), encoding="utf-8")

    outcome = run_suite(_suite_file(tmp_path, [_suite_case(project, manifest)])).cases[0]
    assert outcome.classification == "unsupported"
    assert outcome.source_verification == "not_verified"
    assert outcome.execution_status == "not_computed"
    assert "Impervious fractions" in (outcome.reason or "")
