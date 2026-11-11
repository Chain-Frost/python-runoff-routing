"""Versioned JSON projects backed by the existing immutable S1 RunModel.

External RORB/ARR files are hash verified but never altered or interpreted
through a second grammar. No numerical solver, RORB binary or network access.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path, PureWindowsPath
from typing import Any, Literal, cast

from .rorb_codec import FormatProblem, parse_catg, parse_cmd_par, parse_design_stm
from .rorb_model import RunModel, from_dict, to_dict, to_json

PROJECT_VERSION = 1
PROJECT_FORMAT = "python-runoff-routing-project"
MAX_SOURCE_BYTES = 64 * 1024 * 1024
_HASH = re.compile(r"[a-f0-9]{64}\Z")
_ID = re.compile(r"[A-Za-z][A-Za-z0-9_.-]{0,127}\Z")

RainfallProfile = Literal["explicit", "legacy-rorb", "arr-2026v1"]
AssetRole = Literal["rainfall", "temporal-pattern", "curve", "reference"]


class ProjectError(ValueError):
    """Invalid or unsupported project, never a numerical-parity verdict."""


def _identifier(value: str, label: str) -> None:
    if _ID.fullmatch(value) is None:
        message = f"{label} must be a stable ASCII identifier of at most 128 characters"
        raise ProjectError(message)


def _safe_relative(path: str) -> None:
    """Portable slash paths only; absolute/drive/UNC/traversal paths fail closed."""
    if (
        not path
        or len(path) > 1024
        or "\\" in path
        or ":" in path
        or PureWindowsPath(path).anchor
        or path.startswith("/")
        or any(part in {"", ".", ".."} for part in path.split("/"))
        or any(ord(char) < 32 or char in '<>"|?*' for char in path)
    ):
        message = f"Unsafe project-relative path: {path!r}"
        raise ProjectError(message)


@dataclass(frozen=True, slots=True)
class SourceFile:
    """Immutable, hash-pinned project-relative file reference."""

    path: str
    sha256: str

    def __post_init__(self) -> None:
        _safe_relative(self.path)
        if _HASH.fullmatch(self.sha256) is None:
            message = f"Expected lowercase SHA-256 for {self.path}"
            raise ProjectError(message)


@dataclass(frozen=True, slots=True)
class EmbeddedRun:
    """Embed the existing versioned S1 model without redefining it."""

    run: RunModel


@dataclass(frozen=True, slots=True)
class LegacyRunFiles:
    """Original RORB inputs; .par's embedded paths are never followed."""

    parameters: SourceFile
    catchment: SourceFile
    storm: SourceFile

    def __post_init__(self) -> None:
        for reference, suffix in (
            (self.parameters, ".par"),
            (self.catchment, ".catg"),
            (self.storm, ".stm"),
        ):
            if not reference.path.lower().endswith(suffix):
                message = f"Unsupported RORB source format: {reference.path}"
                raise ProjectError(message)


@dataclass(frozen=True, slots=True)
class ExternalAsset:
    """Provenance only: S6 decides the meaning of rainfall/curve bytes."""

    identifier: str
    role: AssetRole
    data_profile: str
    source: SourceFile

    def __post_init__(self) -> None:
        _identifier(self.identifier, "Asset ID")
        _identifier(self.data_profile, "Data profile")
        if self.role not in {"rainfall", "temporal-pattern", "curve", "reference"}:
            message = "Unrecognised external asset role"
            raise ProjectError(message)


@dataclass(frozen=True, slots=True)
class Project:
    """JSON-only boundary; method profile does not assert model equivalence."""

    identifier: str
    rainfall_profile: RainfallProfile
    model_source: EmbeddedRun | LegacyRunFiles
    assets: tuple[ExternalAsset, ...] = ()

    def __post_init__(self) -> None:
        _identifier(self.identifier, "Project ID")
        if self.rainfall_profile not in {"explicit", "legacy-rorb", "arr-2026v1"}:
            message = "Unknown rainfall-method profile"
            raise ProjectError(message)
        ids = tuple(asset.identifier for asset in self.assets)
        if len(set(ids)) != len(ids):
            message = "Duplicate external asset IDs"
            raise ProjectError(message)


@dataclass(frozen=True, slots=True)
class LoadedProject:
    """Validated S1 model and original provenance, no numerical-parity claim."""

    project: Project
    run: RunModel
    original_json_bytes: bytes
    file_hashes: tuple[tuple[str, str], ...]
    validation_status: Literal["structural_only"] = "structural_only"


def _object(raw: object, fields: set[str], label: str) -> dict[str, object]:
    if not isinstance(raw, dict):
        message = f"{label} must be a JSON object"
        raise ProjectError(message)
    data = cast("dict[str, object]", raw)
    if set(data) != fields:
        message = f"{label} expects exact fields: {sorted(fields)}"
        raise ProjectError(message)
    return data


def _string(raw: object, label: str) -> str:
    if not isinstance(raw, str):
        message = f"{label} must be a JSON string"
        raise ProjectError(message)
    return raw


def _source_file(raw: object) -> SourceFile:
    data = _object(raw, {"path", "sha256"}, "source file")
    return SourceFile(_string(data["path"], "Path"), _string(data["sha256"], "Hash"))


def _asset(raw: object) -> ExternalAsset:
    data = _object(raw, {"id", "role", "data_profile", "source"}, "external asset")
    role = _string(data["role"], "Asset role")
    if role not in {"rainfall", "temporal-pattern", "curve", "reference"}:
        message = f"Unsupported external asset role: {role}"
        raise ProjectError(message)
    return ExternalAsset(
        _string(data["id"], "Asset ID"),
        cast("AssetRole", role),
        _string(data["data_profile"], "Data profile"),
        _source_file(data["source"]),
    )


def _model_source(raw: object) -> EmbeddedRun | LegacyRunFiles:
    if not isinstance(raw, dict):
        message = "Model source must be a JSON object"
        raise ProjectError(message)
    source = cast("dict[str, object]", raw)
    kind = _string(source.get("kind"), "Model source kind")
    if kind == "embedded-run":
        data = _object(source, {"kind", "run"}, "embedded model")
        run_document = _object(data["run"], {"schema_version", "kind", "units", "model"}, "S1 run")
        try:
            model = from_dict(cast("dict[str, Any]", run_document))
        except (TypeError, ValueError) as exc:
            message = f"Invalid S1 embedded run: {exc}"
            raise ProjectError(message) from exc
        if not isinstance(model, RunModel):
            message = "Embedded S1 input must be a complete RunModel"
            raise ProjectError(message)
        return EmbeddedRun(model)
    if kind == "rorb-files":
        data = _object(source, {"kind", "parameters", "catchment", "storm"}, "RORB file source")
        return LegacyRunFiles(
            _source_file(data["parameters"]), _source_file(data["catchment"]), _source_file(data["storm"])
        )
    message = f"Unsupported model source kind: {kind}"
    raise ProjectError(message)


def _file_dict(source: SourceFile) -> dict[str, str]:
    return {"path": source.path, "sha256": source.sha256}


def project_to_dict(project: Project) -> dict[str, Any]:
    """Deterministic schema-1 representation, preserving S1's separate schema."""
    if isinstance(project.model_source, EmbeddedRun):
        source: dict[str, Any] = {"kind": "embedded-run", "run": to_dict(project.model_source.run)}
    else:
        files = project.model_source
        source = {
            "kind": "rorb-files",
            "parameters": _file_dict(files.parameters),
            "catchment": _file_dict(files.catchment),
            "storm": _file_dict(files.storm),
        }
    return {
        "format": PROJECT_FORMAT,
        "schema_version": PROJECT_VERSION,
        "project_id": project.identifier,
        "rainfall_profile": project.rainfall_profile,
        "model_source": source,
        "external_assets": [
            {
                "id": asset.identifier,
                "role": asset.role,
                "data_profile": asset.data_profile,
                "source": _file_dict(asset.source),
            }
            for asset in project.assets
        ],
    }


def project_to_json(project: Project) -> str:
    return json.dumps(project_to_dict(project), ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n"


def _unique_pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            message = f"Duplicate JSON object key: {key}"
            raise ProjectError(message)
        result[key] = value
    return result


def _reject_nonfinite(value: str) -> None:
    message = f"Nonstandard JSON constant: {value}"
    raise ProjectError(message)


def project_from_json(text: str) -> Project:
    """Fail closed for duplicate keys, unknown source formats and versions."""
    try:
        raw: object = json.loads(text, object_pairs_hook=_unique_pairs, parse_constant=_reject_nonfinite)
    except (TypeError, ValueError) as exc:
        raise ProjectError(str(exc)) from exc
    data = _object(
        raw,
        {"format", "schema_version", "project_id", "rainfall_profile", "model_source", "external_assets"},
        "project",
    )
    if data["format"] != PROJECT_FORMAT or type(data["schema_version"]) is not int or data["schema_version"] != 1:
        message = "Unsupported JSON project format or version"
        raise ProjectError(message)
    profile = _string(data["rainfall_profile"], "Rainfall profile")
    if profile not in {"explicit", "legacy-rorb", "arr-2026v1"}:
        message = f"Unknown rainfall-method profile: {profile}"
        raise ProjectError(message)
    items = data["external_assets"]
    if not isinstance(items, list):
        message = "External assets must be a JSON array"
        raise ProjectError(message)
    return Project(
        _string(data["project_id"], "Project ID"),
        cast("RainfallProfile", profile),
        _model_source(data["model_source"]),
        tuple(_asset(item) for item in cast("list[object]", items)),
    )


def _read_bounded(path: Path) -> bytes:
    try:
        if path.stat().st_size > MAX_SOURCE_BYTES:
            message = f"Source exceeds {MAX_SOURCE_BYTES} byte limit: {path}"
            raise ProjectError(message)
        contents = path.read_bytes()
    except OSError as exc:
        message = f"Cannot read project source: {path}"
        raise ProjectError(message) from exc
    if len(contents) > MAX_SOURCE_BYTES:
        message = f"Source changed or exceeds maximum size: {path}"
        raise ProjectError(message)
    return contents


def _source_bytes(directory: Path, reference: SourceFile) -> bytes:
    """Resolve symlinks deliberately for containment; retain source spelling."""
    base = directory.resolve(strict=True)
    try:
        physical = (directory / reference.path).resolve(strict=True)
    except OSError as exc:
        message = f"Missing project source: {reference.path}"
        raise ProjectError(message) from exc
    if not physical.is_relative_to(base):
        message = f"Source symlink escapes project directory: {reference.path}"
        raise ProjectError(message)
    raw = _read_bounded(physical)
    if hashlib.sha256(raw).hexdigest() != reference.sha256:
        message = f"Source SHA-256 mismatch: {reference.path}"
        raise ProjectError(message)
    return raw


def _resolve_run(directory: Path, source: EmbeddedRun | LegacyRunFiles) -> tuple[RunModel, tuple[SourceFile, ...]]:
    if isinstance(source, EmbeddedRun):
        return source.run, ()
    references = (source.parameters, source.catchment, source.storm)
    raw = tuple(_source_bytes(directory, item) for item in references)
    try:
        parameters = parse_cmd_par(raw[0]).model
        catchment = parse_catg(raw[1]).model
        storm = parse_design_stm(raw[2]).model
        run = RunModel(parameters, catchment, storm)
    except (FormatProblem, TypeError, ValueError) as exc:
        message = f"RORB source cannot form supported S1 RunModel: {exc}"
        raise ProjectError(message) from exc
    return run, references


def load_project(path: Path) -> LoadedProject:
    """Validate JSON and source hashes; no solver or external process."""
    source = _read_bounded(path)
    try:
        project = project_from_json(source.decode("utf-8-sig"))
    except UnicodeError as exc:
        message = "Project JSON must be valid UTF-8"
        raise ProjectError(message) from exc
    directory = path.absolute().parent
    run, references = _resolve_run(directory, project.model_source)
    all_files = (*references, *(asset.source for asset in project.assets))
    for asset in project.assets:
        _source_bytes(directory, asset.source)
    return LoadedProject(project, run, source, tuple((item.path, item.sha256) for item in all_files))


def write_project(path: Path, project: Project) -> None:
    """Never overwrite an original file."""
    with path.open("xb") as stream:
        stream.write(project_to_json(project).encode("utf-8"))


def import_rorb_project(
    target: Path,
    *,
    identifier: str,
    rainfall_profile: RainfallProfile,
    parameters: Path,
    catchment: Path,
    storm: Path,
) -> Project:
    """Create a manifest from three existing, unmodified RORB source files."""
    base = target.absolute().parent.resolve(strict=True)

    def pinned(path: Path) -> SourceFile:
        source = path.absolute()
        try:
            relative = source.relative_to(target.absolute().parent).as_posix()
        except ValueError as exc:
            message = "RORB files must be physically inside the project directory"
            raise ProjectError(message) from exc
        reference = SourceFile(relative, hashlib.sha256(_read_bounded(source)).hexdigest())
        _source_bytes(base, reference)
        return reference

    source = LegacyRunFiles(pinned(parameters), pinned(catchment), pinned(storm))
    project = Project(identifier, rainfall_profile, source)
    _resolve_run(base, source)
    return project


MAX_DIFFERENCE_PATHS = 24


@dataclass(frozen=True, slots=True)
class ProjectComparison:
    """Exact typed-model and project-method comparison, without solver execution."""

    left_project_id: str
    right_project_id: str
    left_source_kind: Literal["embedded-run", "rorb-files"]
    right_source_kind: Literal["embedded-run", "rorb-files"]
    model_equal: bool
    rainfall_profile_equal: bool
    external_assets_equal: bool
    configuration_equal: bool
    first_differences: tuple[str, ...]
    numerical_parity: Literal["not_assessed"] = "not_assessed"

    def to_json(self) -> str:
        """Stable machine-readable model comparison, not a native routing verdict."""
        return json.dumps(asdict(self), indent=2, sort_keys=True, allow_nan=False) + "\n"


def _first_differences(left: object, right: object, path: str, differences: list[str]) -> None:
    """Report bounded field-level mismatches without changing source order."""
    if len(differences) >= MAX_DIFFERENCE_PATHS or left == right:
        return
    if isinstance(left, dict) and isinstance(right, dict):
        first = cast("dict[str, object]", left)
        second = cast("dict[str, object]", right)
        for key in sorted(first.keys() | second.keys()):
            if len(differences) >= MAX_DIFFERENCE_PATHS:
                break
            label = f"{path}.{key}"
            if key not in first or key not in second:
                differences.append(label)
            else:
                _first_differences(first[key], second[key], label, differences)
    elif isinstance(left, list) and isinstance(right, list):
        first_items = cast("list[object]", left)
        second_items = cast("list[object]", right)
        if len(first_items) != len(second_items):
            differences.append(f"{path}.length")
        for index, (a, b) in enumerate(zip(first_items, second_items, strict=False)):
            if len(differences) >= MAX_DIFFERENCE_PATHS:
                break
            _first_differences(a, b, f"{path}[{index}]", differences)
    else:
        differences.append(path)


def _source_kind(source: EmbeddedRun | LegacyRunFiles) -> Literal["embedded-run", "rorb-files"]:
    return "embedded-run" if isinstance(source, EmbeddedRun) else "rorb-files"


def compare_project_files(left: Path, right: Path) -> ProjectComparison:
    """Compare two fully verified JSON projects using S1's typed model.

    Exact S1 model identity is not native hydrograph or rainfall-method parity.
    """
    a = load_project(left)
    b = load_project(right)
    model_equal = a.run == b.run
    profile_equal = a.project.rainfall_profile == b.project.rainfall_profile
    assets_equal = a.project.assets == b.project.assets
    differences: list[str] = []
    if not model_equal:
        _first_differences(to_dict(a.run), to_dict(b.run), "run", differences)
    if not profile_equal:
        differences.append("rainfall_profile")
    if not assets_equal:
        _first_differences(
            project_to_dict(a.project)["external_assets"],
            project_to_dict(b.project)["external_assets"],
            "external_assets",
            differences,
        )
    return ProjectComparison(
        a.project.identifier,
        b.project.identifier,
        _source_kind(a.project.model_source),
        _source_kind(b.project.model_source),
        model_equal,
        profile_equal,
        assets_equal,
        model_equal and profile_equal and assets_equal,
        tuple(differences[:MAX_DIFFERENCE_PATHS]),
    )


def export_run_json(project_path: Path, destination: Path) -> str:
    """Write verified S1 RunModel JSON; the project retains source provenance.

    The exported S1 model intentionally omits project rainfall-method and
    external source metadata. Returns the SHA-256 of the new JSON file.
    """
    model = load_project(project_path).run
    contents = to_json(model).encode("utf-8")
    with destination.open("xb") as stream:
        stream.write(contents)
    return hashlib.sha256(contents).hexdigest()


def _validated_profile(value: str) -> RainfallProfile:
    if value not in {"explicit", "legacy-rorb", "arr-2026v1"}:
        message = f"Unknown rainfall-method profile: {value}"
        raise ProjectError(message)
    return cast("RainfallProfile", value)


def main(argv: list[str] | None = None) -> int:
    """Small Windows-friendly CLI without argparse, native calls or side effects."""
    args = sys.argv[1:] if argv is None else argv
    try:
        if len(args) == 3 and args[0] == "compare":
            report = compare_project_files(Path(args[1]), Path(args[2]))
            print(report.to_json(), end="")
            return 0 if report.configuration_equal else 1
        if len(args) == 3 and args[0] == "export-run":
            source_path, destination_path = Path(args[1]), Path(args[2])
            fingerprint = export_run_json(source_path, destination_path)
            print(
                json.dumps(
                    {"status": "written", "sha256": fingerprint, "numerical_parity": "not_assessed"},
                    sort_keys=True,
                )
            )
            return 0
        if len(args) == 2 and args[0] in {"validate", "inspect"}:
            loaded = load_project(Path(args[1]))
            print(
                json.dumps(
                    {
                        "status": loaded.validation_status,
                        "project_id": loaded.project.identifier,
                        "rainfall_profile": loaded.project.rainfall_profile,
                        "source_files": len(loaded.file_hashes),
                        "subareas": len(loaded.run.catchment.subareas),
                        "print_locations": len(loaded.run.catchment.print_locations),
                        "numerical_parity": "not_assessed",
                    },
                    sort_keys=True,
                )
            )
            return 0
        if len(args) == 7 and args[0] == "import-rorb":
            _, identifier, profile, par, catg, stm, destination = args
            selected_profile = _validated_profile(profile)
            target = Path(destination)
            project = import_rorb_project(
                target,
                identifier=identifier,
                rainfall_profile=selected_profile,
                parameters=Path(par),
                catchment=Path(catg),
                storm=Path(stm),
            )
            write_project(target, project)
            print(json.dumps({"status": "written", "path": str(target)}, sort_keys=True))
            return 0
    except (ProjectError, OSError) as exc:
        print(f"Project validation failed: {exc}", file=sys.stderr)
        return 2
    print(
        "Usage: python -m runoff_routing.project_json (validate|inspect) <project.json> "
        "| import-rorb <id> <rainfall-profile> <par> <catg> <stm> <project.json> "
        "| export-run <project.json> <run.json> | compare <left.json> <right.json>",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
