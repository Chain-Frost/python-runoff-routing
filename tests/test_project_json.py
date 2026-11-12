"""S5-P0 JSON project boundary tests; all model and rainfall values are synthetic."""

from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from decimal import Decimal
from pathlib import Path

import pytest

from runoff_routing.project_json import (
    EmbeddedRun,
    ExternalAsset,
    LegacyRunFiles,
    Project,
    ProjectError,
    SourceFile,
    compare_project_files,
    export_run_json,
    import_rorb_project,
    load_project,
    main,
    project_from_json,
    project_to_json,
    write_project,
)
from runoff_routing.rorb_codec import serialize_catg, serialize_cmd_par, serialize_design_stm
from runoff_routing.rorb_model import (
    CatchmentModel,
    ControlStep,
    LossValue,
    ParameterSet,
    PrintLocation,
    Reach,
    RoutingValue,
    RunModel,
    StormModel,
    SubArea,
    from_json,
)


def _run() -> RunModel:
    return RunModel(
        ParameterSet(
            "OTHER-PATH-NEVER-FOLLOW.catg",
            "OTHER-STORM-NEVER-FOLLOW.stm",
            True,
            3,
            1,
            1,
            1,
            (RoutingValue(1, Decimal(1), Decimal("0.8")),),
            (LossValue(1, 1, Decimal(2), Decimal("0.5")),),
        ),
        CatchmentModel(
            "Example project",
            (SubArea("area_1", Decimal(2), "A"),),
            (Reach("reach_1", Decimal(3), "Reach 1 Sub-area A"),),
            (
                ControlStep(1, "area_1", "reach_1", label="Reach 1 Sub-area A"),
                ControlStep(7, print_id="print_1", label="Outlet"),
            ),
            (PrintLocation("print_1", "Outlet"),),
        ),
        StormModel(
            "Example storm",
            Decimal("0.5"),
            10,
            0,
            (Decimal(25), Decimal(75)),
            (Decimal(10),),
            ("area_1",),
        ),
    )


def _legacy_sources(root: Path) -> tuple[Path, Path, Path]:
    folder = root / "input models"
    folder.mkdir(parents=True)
    run = _run()
    paths = (folder / "parameters.par", folder / "catchment.catg", folder / "storm.stm")
    for path, contents in zip(
        paths,
        (serialize_cmd_par(run.parameters), serialize_catg(run.catchment), serialize_design_stm(run.storm)),
        strict=True,
    ):
        path.write_bytes(contents)
    return paths


def _inline() -> Project:
    return Project("case-one", "explicit", EmbeddedRun(_run()))


def test_inline_json_roundtrip_reuses_exact_s1_typed_model() -> None:
    project = _inline()
    encoded = project_to_json(project)
    assert project_from_json(encoded) == project
    assert project_from_json(encoded).model_source == EmbeddedRun(_run())
    assert '"schema_version": 1' in encoded
    assert '"rainfall_profile": "explicit"' in encoded


def test_legacy_import_equivalence_and_no_implicit_par_path_following(tmp_path: Path) -> None:
    files = _legacy_sources(tmp_path)
    target = tmp_path / "hydrology project.json"
    project = import_rorb_project(
        target,
        identifier="case-one",
        rainfall_profile="legacy-rorb",
        parameters=files[0],
        catchment=files[1],
        storm=files[2],
    )
    assert isinstance(project.model_source, LegacyRunFiles)
    original = tuple(path.read_bytes() for path in files)
    write_project(target, project)
    loaded = load_project(target)
    assert loaded.run == _run()
    assert loaded.validation_status == "structural_only"
    assert len(loaded.file_hashes) == 3
    assert tuple(path.read_bytes() for path in files) == original
    assert loaded.original_json_bytes == target.read_bytes()
    assert "\\" not in project.model_source.parameters.path


def test_external_arr_is_hash_verified_but_not_interpreted(tmp_path: Path) -> None:
    root = tmp_path / "Project With Spaces"
    root.mkdir()
    path = root / "rainfall 2026.json"
    raw = b'{"datahub_version":"2026v1"}\n'
    path.write_bytes(raw)
    asset = ExternalAsset(
        "rain2026",
        "rainfall",
        "arr_2026v1",
        SourceFile(path.name, hashlib.sha256(raw).hexdigest()),
    )
    project = replace(_inline(), rainfall_profile="arr-2026v1", assets=(asset,))
    target = root / "project.json"
    write_project(target, project)
    loaded = load_project(target)
    assert loaded.project.rainfall_profile == "arr-2026v1"
    assert loaded.run == _run()
    assert path.read_bytes() == raw
    path.write_bytes(raw + b"changed")
    with pytest.raises(ProjectError, match="SHA-256"):
        load_project(target)


@pytest.mark.parametrize(
    "path",
    [
        "../escape.json",
        "folder/../escape.json",
        "/etc/passwd",
        r"C:\Windows\win.ini",
        r"\\server\share\model.dat",
        "C:relative.txt",
        "a//file.json",
        "a/./file.json",
        r"a\b.csv",
    ],
)
def test_unsafe_relative_references_rejected(path: str) -> None:
    with pytest.raises(ProjectError, match="Unsafe"):
        SourceFile(path, "0" * 64)


@pytest.mark.parametrize(
    "alteration",
    ["version", "format", "missing", "unknown", "profile", "assets", "source", "nonfinite", "wrong_units"],
)
def test_json_schema_rejects_malformed_or_unsupported_values(alteration: str) -> None:
    data = json.loads(project_to_json(_inline()))
    if alteration == "version":
        data["schema_version"] = 2
    elif alteration == "format":
        data["format"] = "unrelated"
    elif alteration == "missing":
        del data["rainfall_profile"]
    elif alteration == "unknown":
        data["toml"] = True
    elif alteration == "profile":
        data["rainfall_profile"] = "auto"
    elif alteration == "assets":
        data["external_assets"] = {"bad": "not a list"}
    elif alteration == "source":
        data["model_source"]["kind"] = "future-unsupported"
    elif alteration == "nonfinite":
        data["model_source"]["run"]["model"]["parameters"]["routing"][0]["kc"] = "NaN"
    else:
        data["model_source"]["run"]["units"]["area"] = "m2"
    with pytest.raises(ProjectError):
        project_from_json(json.dumps(data))


def test_duplicate_keys_and_nonstandard_json_constants_rejected() -> None:
    text = project_to_json(_inline())
    duplicated = text.replace('"schema_version": 1,', '"schema_version": 1, "schema_version": 1,')
    with pytest.raises(ProjectError, match="Duplicate"):
        project_from_json(duplicated)
    with pytest.raises(ProjectError, match="Nonstandard"):
        project_from_json(text.replace('"schema_version": 1', '"schema_version": NaN'))


def test_invalid_assets_and_duplicate_ids_rejected() -> None:
    source = SourceFile("data/a.csv", "a" * 64)
    asset = ExternalAsset("data1", "reference", "arr_2026v1", source)
    with pytest.raises(ProjectError, match="Duplicate"):
        replace(_inline(), assets=(asset, asset))
    data = json.loads(project_to_json(replace(_inline(), assets=(asset,))))
    data["external_assets"][0]["role"] = "unexpected"
    with pytest.raises(ProjectError, match="role"):
        project_from_json(json.dumps(data))


def test_file_corruption_rejected_without_changing_evidence(tmp_path: Path) -> None:
    paths = _legacy_sources(tmp_path)
    project = import_rorb_project(
        tmp_path / "project.json",
        identifier="case-one",
        rainfall_profile="legacy-rorb",
        parameters=paths[0],
        catchment=paths[1],
        storm=paths[2],
    )
    write_project(tmp_path / "project.json", project)
    paths[1].write_bytes(paths[1].read_bytes() + b"bad")
    with pytest.raises(ProjectError, match="SHA-256"):
        load_project(tmp_path / "project.json")


def test_symlink_escape_rejected(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_text("something", encoding="utf-8")
    link = project_root / "external.txt"
    try:
        link.symlink_to(outside)
    except OSError, NotImplementedError:
        pytest.skip("File symlinks unavailable on this filesystem")
    asset = ExternalAsset(
        "outside",
        "reference",
        "other",
        SourceFile("external.txt", hashlib.sha256(b"something").hexdigest()),
    )
    write_project(project_root / "project.json", replace(_inline(), assets=(asset,)))
    with pytest.raises(ProjectError, match="escapes"):
        load_project(project_root / "project.json")


def test_unicode_paths_and_exclusive_create(tmp_path: Path) -> None:
    root = tmp_path / "test ünicode"
    root.mkdir()
    target = root / "模型 project.json"
    write_project(target, _inline())
    with pytest.raises(FileExistsError):
        write_project(target, _inline())
    assert load_project(target).project.identifier == "case-one"


def test_import_cannot_reach_outside_project_root(tmp_path: Path) -> None:
    project_root = tmp_path / "case"
    project_root.mkdir()
    par, catg, stm = _legacy_sources(tmp_path)
    with pytest.raises(ProjectError, match="inside the project"):
        import_rorb_project(
            project_root / "project.json",
            identifier="case-one",
            rainfall_profile="legacy-rorb",
            parameters=par,
            catchment=catg,
            storm=stm,
        )


def test_cli_validate_inspect_and_bad_usage(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = tmp_path / "project.json"
    write_project(path, _inline())
    assert main(["validate", str(path)]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["status"] == "structural_only"
    assert data["numerical_parity"] == "not_assessed"
    assert data["subareas"] == 1
    assert main(["inspect", str(path)]) == 0
    assert main(["unknown", str(path)]) == 2


def test_cli_import_rorb_writes_fingerprinted_project(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    par, catg, stm = _legacy_sources(tmp_path)
    target = tmp_path / "case.json"
    args = ["import-rorb", "id1", "legacy-rorb", str(par), str(catg), str(stm), str(target)]
    assert main(args) == 0
    assert load_project(target).run == _run()
    capsys.readouterr()
    assert main(args) == 2


def test_original_rorb_files_and_embedded_json_have_exact_typed_model_identity(tmp_path: Path) -> None:
    par, catg, stm = _legacy_sources(tmp_path)
    legacy_path = tmp_path / "historic project.json"
    legacy_project = import_rorb_project(
        legacy_path,
        identifier="historic-model",
        rainfall_profile="legacy-rorb",
        parameters=par,
        catchment=catg,
        storm=stm,
    )
    write_project(legacy_path, legacy_project)
    embedded_path = tmp_path / "converted model.json"
    write_project(embedded_path, Project("comparison-target", "legacy-rorb", EmbeddedRun(_run())))
    comparison = compare_project_files(legacy_path, embedded_path)
    assert comparison.left_source_kind == "rorb-files"
    assert comparison.right_source_kind == "embedded-run"
    assert comparison.model_equal
    assert comparison.rainfall_profile_equal
    assert comparison.external_assets_equal
    assert comparison.configuration_equal
    assert comparison.first_differences == ()
    assert comparison.numerical_parity == "not_assessed"
    assert json.loads(comparison.to_json())["configuration_equal"] is True


def test_compare_reports_exact_rorb_model_field_changes_without_fitting_tolerances(tmp_path: Path) -> None:
    before = tmp_path / "before.json"
    after = tmp_path / "after.json"
    write_project(before, _inline())
    run = _run()
    routing = replace(run.parameters.routing[0], m=Decimal("0.9"))
    changed_parameters = replace(run.parameters, routing=(routing,))
    write_project(after, Project("after", "explicit", EmbeddedRun(replace(run, parameters=changed_parameters))))
    result = compare_project_files(before, after)
    assert not result.model_equal
    assert result.rainfall_profile_equal
    assert not result.configuration_equal
    assert "run.model.parameters.routing[0].m" in result.first_differences
    assert result.numerical_parity == "not_assessed"


def test_same_model_with_different_rainfall_profiles_is_not_interchangeable(tmp_path: Path) -> None:
    legacy, modern = tmp_path / "legacy.json", tmp_path / "modern.json"
    write_project(legacy, Project("legacy", "legacy-rorb", EmbeddedRun(_run())))
    write_project(modern, Project("modern", "arr-2026v1", EmbeddedRun(_run())))
    result = compare_project_files(legacy, modern)
    assert result.model_equal
    assert not result.rainfall_profile_equal
    assert not result.configuration_equal
    assert result.first_differences == ("rainfall_profile",)


def test_external_asset_provenance_can_disagree_even_with_identical_run_model(tmp_path: Path) -> None:
    first = tmp_path / "2016 rainfall.json"
    second = tmp_path / "2026 rainfall.json"
    first.write_bytes(b"historic")
    second.write_bytes(b"modern")
    asset_a = ExternalAsset(
        "rain",
        "rainfall",
        "legacy_2016",
        SourceFile(first.name, hashlib.sha256(first.read_bytes()).hexdigest()),
    )
    asset_b = ExternalAsset(
        "rain",
        "rainfall",
        "arr_2026v1",
        SourceFile(second.name, hashlib.sha256(second.read_bytes()).hexdigest()),
    )
    left = tmp_path / "first.json"
    right = tmp_path / "second.json"
    write_project(left, replace(_inline(), assets=(asset_a,)))
    write_project(right, replace(_inline(), assets=(asset_b,)))
    result = compare_project_files(left, right)
    assert result.model_equal
    assert result.rainfall_profile_equal
    assert not result.external_assets_equal
    assert not result.configuration_equal
    assert any(path.startswith("external_assets[0]") for path in result.first_differences)


def test_export_s1_run_json_is_readable_and_does_not_clobber_or_claim_parity(tmp_path: Path) -> None:
    source = tmp_path / "project.json"
    destination = tmp_path / "run.json"
    write_project(source, _inline())
    before = source.read_bytes()
    digest = export_run_json(source, destination)
    assert digest == hashlib.sha256(destination.read_bytes()).hexdigest()
    assert from_json(destination.read_text(encoding="utf-8")) == _run()
    assert b"rainfall_profile" not in destination.read_bytes()
    assert source.read_bytes() == before
    with pytest.raises(FileExistsError):
        export_run_json(source, destination)


def test_compare_and_export_command_exit_codes_and_json_reports(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    first, other, export = tmp_path / "a.json", tmp_path / "b.json", tmp_path / "run.json"
    write_project(first, _inline())
    write_project(other, replace(_inline(), rainfall_profile="legacy-rorb"))
    assert main(["compare", str(first), str(first)]) == 0
    passed = json.loads(capsys.readouterr().out)
    assert passed["configuration_equal"]
    assert passed["numerical_parity"] == "not_assessed"
    assert main(["compare", str(first), str(other)]) == 1
    mismatch = json.loads(capsys.readouterr().out)
    assert not mismatch["rainfall_profile_equal"]
    assert "rainfall_profile" in mismatch["first_differences"]
    assert main(["export-run", str(first), str(export)]) == 0
    receipt = json.loads(capsys.readouterr().out)
    assert receipt["status"] == "written"
    assert receipt["numerical_parity"] == "not_assessed"
    assert from_json(export.read_text(encoding="utf-8")) == _run()
    assert main(["export-run", str(first), str(export)]) == 2


def test_compare_and_export_fail_closed_on_bad_input_hash(tmp_path: Path) -> None:
    par, catg, stm = _legacy_sources(tmp_path)
    source = tmp_path / "legacy.json"
    write_project(
        source,
        import_rorb_project(
            source,
            identifier="historical",
            rainfall_profile="legacy-rorb",
            parameters=par,
            catchment=catg,
            storm=stm,
        ),
    )
    catg.write_bytes(catg.read_bytes() + b"invalid source changed")
    with pytest.raises(ProjectError, match="SHA-256"):
        compare_project_files(source, source)
    with pytest.raises(ProjectError, match="SHA-256"):
        export_run_json(source, tmp_path / "should_not_exist.json")
    assert not (tmp_path / "should_not_exist.json").exists()



@pytest.mark.parametrize(
    "path",
    ["CON", "nul.txt", "AUX.ifd", "com1.csv", "LPT9", "COM³.dat", "folder/data.", "folder/data "],
)
def test_unportable_windows_device_and_trailing_dot_names_rejected(path: str) -> None:
    with pytest.raises(ProjectError, match="Unsafe"):
        SourceFile(path, "0" * 64)


def test_identical_external_content_relocated_within_project_is_semantically_equal(tmp_path: Path) -> None:
    origin = tmp_path / "before"
    moved = tmp_path / "after"
    origin.mkdir()
    moved.mkdir()
    source = b"same synthetic rainfall metadata"
    for folder, name in ((origin, "2016-source.txt"), (moved, "historic file.txt")):
        (folder / name).write_bytes(source)
    digest = hashlib.sha256(source).hexdigest()
    left_asset = ExternalAsset("ifd", "rainfall", "legacy_arr2016", SourceFile("2016-source.txt", digest))
    right_asset = ExternalAsset("ifd", "rainfall", "legacy_arr2016", SourceFile("historic file.txt", digest))
    left = origin / "project.json"
    right = moved / "project.json"
    write_project(left, replace(_inline(), assets=(left_asset,)))
    write_project(right, replace(_inline(), assets=(right_asset,)))
    result = compare_project_files(left, right)
    assert result.model_equal
    assert result.external_assets_equal
    assert not result.external_asset_paths_equal
    assert result.configuration_equal
    assert result.first_differences == ()
    assert result.numerical_parity == "not_assessed"
