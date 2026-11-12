"""S5 read-only review of fingerprinted S0 CMD evidence against a JSON project.

Native engine execution, location mapping, source timing and numerical
acceptance are never inferred. S1/S2 own the printed-ordinate/volume audit.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Literal, cast

from .integration_reporting import RecordedPrintReview, review_recorded_print
from .project_execution import execute_loaded_project
from .project_json import LegacyRunFiles, ProjectError, load_project
from .reference import verify_manifest
from .rorb_documents import RorbSource
from .rorb_out import inspect_output
from .rorb_model import RunModel

_HASH = re.compile(r"[a-f0-9]{64}\Z")
_MAX_MANIFEST_BYTES = 2 * 1024 * 1024


@dataclass(frozen=True, slots=True)
class NativeProjectReview:
    """A verified reference diagnostic, not evidence of accepted numerical parity."""

    project_id: str
    case_id: str
    project_sha256: str
    model_sha256: str
    manifest_sha256: str
    native_output_sha256: str
    engine_profile: str
    engine_executable_sha256: str
    model_print_id: str
    native_column_id: str
    mapping_evidence: Literal["caller_asserted"]
    raw_increment_tokens: tuple[str, ...]
    raw_time_tokens: tuple[str, ...]
    printed: RecordedPrintReview
    review_status: Literal["source_verified_diagnostic"] = "source_verified_diagnostic"
    numerical_acceptance: Literal["unassessed"] = "unassessed"

    def to_json(self) -> str:
        """Retain original printed tokens and Decimal statistics exactly."""
        result = asdict(self)
        result["printed"] = json.loads(self.printed.to_json())
        return json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n"


def _record(raw: object, label: str) -> dict[str, object]:
    if not isinstance(raw, dict):
        message = f"{label} must be an object"
        raise ProjectError(message)
    return cast("dict[str, object]", raw)


def _string(raw: object, label: str) -> str:
    if not isinstance(raw, str) or not raw.strip():
        message = f"{label} must be a nonempty string"
        raise ProjectError(message)
    return raw


def _verified_manifest(path: Path, expected_sha256: str) -> tuple[dict[str, object], str]:
    if _HASH.fullmatch(expected_sha256) is None:
        message = "Expected a pinned 64-hex SHA-256 for the native S0 manifest"
        raise ProjectError(message)
    if path.stat().st_size > _MAX_MANIFEST_BYTES:
        message = "Native S0 manifest is too large for this adapter"
        raise ProjectError(message)
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected_sha256:
        message = "Native S0 manifest SHA-256 mismatch"
        raise ProjectError(message)
    try:
        decoded: object = json.loads(raw.decode("utf-8"))
    except (UnicodeError, ValueError) as exc:
        message = "Native S0 manifest must be valid UTF-8 JSON"
        raise ProjectError(message) from exc
    manifest = _record(decoded, "S0 manifest")
    if type(manifest.get("schema_version")) is not int or manifest["schema_version"] != 1:
        message = "Unknown S0 manifest schema version"
        raise ProjectError(message)
    try:
        problems = verify_manifest(path)
    except (TypeError, ValueError, KeyError) as exc:
        message = f"Native S0 manifest could not verify its source evidence: {exc}"
        raise ProjectError(message) from exc
    if problems:
        message = f"Native S0 manifest contains invalid or changed evidence: {problems[0]}"
        raise ProjectError(message)
    return manifest, expected_sha256


def _decimal(value: object, label: str) -> Decimal:
    if not isinstance(value, str):
        message = f"{label} must be an explicitly recorded decimal string"
        raise ProjectError(message)
    try:
        parsed = Decimal(value)
    except InvalidOperation as exc:
        message = f"{label} is not a decimal number"
        raise ProjectError(message) from exc
    if not parsed.is_finite():
        message = f"{label} must be finite"
        raise ProjectError(message)
    return parsed


def _check_capture_settings(manifest: dict[str, object], loaded_run: LegacyRunFiles, model: RunModel) -> None:
    """Hash source input records before trusting native effective settings."""
    inputs = _record(manifest.get("inputs"), "S0 inputs")
    for role, expected in (("catchment", loaded_run.catchment.sha256), ("storm", loaded_run.storm.sha256)):
        source = _record(inputs.get(role), f"S0 {role} input")
        fingerprint = _record(source.get("source_fingerprint"), f"S0 {role} source fingerprint")
        if fingerprint.get("sha256") != expected:
            message = f"Original {role} source SHA-256 differs from the captured native input"
            raise ProjectError(message)
    settings = _record(manifest.get("effective_settings"), "S0 effective settings")
    cmd = _record(settings.get("cmd_writer"), "S0 CMD parameters")
    if _decimal(settings.get("timestep_hours"), "Native timestep") != model.storm.timestep_hours:
        message = "Native effective timestep differs from S1 source"
        raise ProjectError(message)
    if not model.parameters.lumped_kc or model.parameters.num_isa != 1 or model.parameters.num_bursts != 1:
        message = "Only the one-ISA/burst, lumped-kc native CMD profile is characterised"
        raise ProjectError(message)
    if any(type(cmd.get(name)) is not int or cmd[name] != 1 for name in ("num_isa", "num_bursts", "loss_model")):
        message = "Native CMD loss/ISA/burst flags are inconsistent or unsupported"
        raise ProjectError(message)
    if model.parameters.loss_model != 1:
        message = "Native CMD comparison only supports explicit pervious IL/CL losses"
        raise ProjectError(message)
    routing = model.parameters.routing[0]
    losses = model.parameters.losses[0]
    for field, source_value in (
        ("kc", routing.kc),
        ("m", routing.m),
        ("initial_loss_mm", losses.initial_loss_mm),
        ("continuing", losses.continuing),
    ):
        if _decimal(cmd.get(field), f"Native {field}") != source_value:
            message = f"Native effective {field} does not match the S1 model"
            raise ProjectError(message)


def _checked_report(
    manifest: dict[str, object], manifest_path: Path, native_column_id: str, expected_rows: int
) -> tuple[RorbSource, tuple[str, ...], tuple[str, ...]]:
    """Reuse S1's single-table inspector, then recover the exact source tokens."""
    outputs = manifest.get("outputs")
    if not isinstance(outputs, list):
        message = "S0 manifest lacks retained output records"
        raise ProjectError(message)
    records = cast("list[object]", outputs)
    selected = tuple(
        _record(item, "S0 output")
        for item in records
        if isinstance(item, dict) and str(item.get("path", "")).lower().endswith(".out")
    )
    if len(selected) != 1:
        message = "S0 native review requires exactly one retained .out report"
        raise ProjectError(message)
    name = _string(selected[0].get("path"), "Native output path")
    relative = Path(name)
    if relative.is_absolute() or ".." in relative.parts or relative.name != name:
        message = "Native report path must be a direct contained evidence file"
        raise ProjectError(message)
    path = manifest_path.absolute().parent / relative
    if path.stat().st_size > 64 * 1024 * 1024:
        message = "Native report exceeds the bounded 64 MiB offline review limit"
        raise ProjectError(message)
    source = RorbSource.read(path)
    if source.sha256 != selected[0].get("sha256"):
        message = "Native output changed after manifest verification"
        raise ProjectError(message)
    inspection = inspect_output(source)
    if inspection.hydrographs is None:
        message = "S1 could not validate a complete native hydrograph table"
        raise ProjectError(message)
    report = inspection.hydrographs
    if native_column_id not in report.columns:
        message = f"Native printed column {native_column_id!r} is absent"
        raise ProjectError(message)
    if report.time_increment_hours is None or report.reported_duration_increments is None:
        message = "Native output lacks an independently reported timestep or duration"
        raise ProjectError(message)
    if len(report.rows) != expected_rows:
        message = "Native and S1 calculation horizons do not match"
        raise ProjectError(message)
    # This initial CMD profile is characterised by raw Inc labels 1..N.
    if any(row.increment != i for i, row in enumerate(report.rows, start=1)):
        message = "Native CMD raw increment labels are not the characterised 1-based sequence"
        raise ProjectError(message)
    position = report.columns.index(native_column_id) + 2
    raw_tokens = tuple(source.lines[row.line - 1].split()[position] for row in report.rows)
    increments = tuple(source.lines[row.line - 1].split()[0] for row in report.rows)
    return source, raw_tokens, increments


def review_project_native_capture(
    project_path: Path,
    manifest_path: Path,
    *,
    manifest_sha256: str,
    engine_executable_sha256: str,
    model_print_id: str,
    native_column_id: str,
) -> NativeProjectReview:
    """Compare a file-backed historic JSON project with a pinned CMD S0 capture.

    The caller must establish the native-column/print-site mapping externally;
    any printed parity is a diagnostic, never an accepted RORB-compatible solve.
    """
    loaded = load_project(project_path)
    if loaded.project.rainfall_profile != "legacy-rorb" or not isinstance(loaded.project.model_source, LegacyRunFiles):
        message = "Native S0 review requires a legacy-rorb project backed by original RORB source files"
        raise ProjectError(message)
    manifest, manifest_hash = _verified_manifest(manifest_path, manifest_sha256)
    if manifest.get("outcome") not in ("success", "zero_runoff"):
        message = "Native S0 capture is not a completed successful result"
        raise ProjectError(message)
    if manifest.get("provenance_gaps") != []:
        message = "Native capture contains unresolved provenance gaps"
        raise ProjectError(message)
    diagnostics = _record(manifest.get("diagnostics"), "S0 diagnostics")
    if diagnostics.get("errors") != [] or diagnostics.get("warnings") != []:
        message = "Native S0 capture has errors or warnings"
        raise ProjectError(message)
    engine = _record(manifest.get("engine"), "S0 engine")
    executable = _record(engine.get("executable"), "S0 executable")
    if engine.get("kind") != "RORB_CMD":
        message = "This S5 reference review supports pinned RORB_CMD profiles only, not RORBwin"
        raise ProjectError(message)
    if _HASH.fullmatch(engine_executable_sha256) is None or executable.get("sha256") != engine_executable_sha256:
        message = "Native executable SHA-256 was not pinned or does not match the capture"
        raise ProjectError(message)
    version = _string(engine.get("observed_version"), "Native executable version")
    profile = f"RORB_CMD {version} sha256={engine_executable_sha256}"
    _check_capture_settings(manifest, loaded.project.model_source, loaded.run)
    count = loaded.run.storm.calculation_increments + 1
    if type(manifest.get("expected_steps")) is not int or manifest["expected_steps"] != count:
        message = "Native S0 expected steps do not match the S1 storm horizon"
        raise ProjectError(message)
    requested = _record(manifest.get("requested_print_locations"), "S0 requested print locations")
    if native_column_id not in requested or not isinstance(requested[native_column_id], str):
        message = "No explicit native column identity in S0 capture manifest"
        raise ProjectError(message)
    source, tokens, increments = _checked_report(manifest, manifest_path, native_column_id, count)
    report = inspect_output(source).hydrographs
    if report is None:
        message = "Validated native output unexpectedly lacks hydrograph rows"
        raise ProjectError(message)
    if report.time_increment_hours != loaded.run.storm.timestep_hours:
        message = "Native output timestep differs from original S1 storm"
        raise ProjectError(message)
    checks = _record(manifest.get("hydrograph_check"), "S0 hydrograph check")
    if checks.get("rows") != count or checks.get("columns") != ["Inc", "Time", *report.columns]:
        message = "Native hydrograph table differs from the S0 capture check"
        raise ProjectError(message)
    times = tuple(item.raw_time for item in report.rows)
    if checks.get("raw_time_labels") != list(times):
        message = "Native raw time labels differ from the S0 capture manifest"
        raise ProjectError(message)
    result = execute_loaded_project(loaded)
    try:
        printed = review_recorded_print(
            result.calculation,
            tokens,
            model_print_id=model_print_id,
            native_column_id=native_column_id,
            engine_profile=profile,
            raw_native_time_tokens=times,
        )
    except (ValueError, ArithmeticError) as exc:
        message = f"Native printed review rejected evidence or print mapping: {exc}"
        raise ProjectError(message) from exc
    return NativeProjectReview(
        loaded.project.identifier,
        _string(manifest.get("case_id"), "Native case ID"),
        result.project_sha256,
        result.model_sha256,
        manifest_hash,
        source.sha256,
        profile,
        engine_executable_sha256,
        model_print_id,
        native_column_id,
        "caller_asserted",
        increments,
        times,
        printed,
    )


def write_native_review_json(path: Path, review: NativeProjectReview) -> None:
    """No-clobber native comparison report."""
    with path.open("xb") as stream:
        stream.write(review.to_json().encode("utf-8"))
