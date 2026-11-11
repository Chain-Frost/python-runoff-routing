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
    except (OSError, NotImplementedError):
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
