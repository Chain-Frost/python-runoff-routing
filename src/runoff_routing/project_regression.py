"""Read-only, hash-pinned, multi-case S5 native regression diagnostics.

This is a suite runner, not a second solver, RORB launcher, rainfall generator,
or acceptance gate. Every declared case has an explicit disposition.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, cast

from .project_json import LegacyRunFiles, LoadedProject, ProjectError, SourceFile, load_project
from .project_native_review import NativeProjectReview, review_project_native_captures

FORMAT = "python-runoff-routing-offline-regression"
VERSION = 1
MAX_SUITE_BYTES = 2 * 1024 * 1024
HASH = re.compile(r"[a-f0-9]{64}\Z")
IDENTIFIER = re.compile(r"[A-Za-z][A-Za-z0-9_.-]{0,127}\Z")
COLUMN = re.compile(r"Hyd\d+\Z")
Classification = Literal["computed/pass", "computed/fail", "unsupported", "incomplete", "invalid"]
SourceStatus = Literal["verified", "failed", "not_verified"]
ExecutionStatus = Literal["computed_unvalidated", "not_computed"]


@dataclass(frozen=True, slots=True)
class PrintMapping:
    """A declared association, NEVER independently verified by this schema."""

    model_print_id: str
    native_column_id: str


@dataclass(frozen=True, slots=True)
class NativeReference:
    manifest: SourceFile
    engine_executable_sha256: str
    print_mapping: tuple[PrintMapping, ...]


@dataclass(frozen=True, slots=True)
class CaseSpec:
    identifier: str
    project: SourceFile | None
    native: NativeReference | None


@dataclass(frozen=True, slots=True)
class RegressionSuite:
    identifier: str
    sha256: str
    path: Path
    cases: tuple[object, ...]


@dataclass(frozen=True, slots=True)
class CaseOutcome:
    """Distinct source, computation and diagnostic budgets; acceptance is never implied."""

    case_id: str
    classification: Classification
    source_verification: SourceStatus
    execution_status: ExecutionStatus
    native_print_budget: Literal["within", "outside", "not_assessed"]
    reason: str | None = None
    project_sha256: str | None = None
    model_sha256: str | None = None
    engine_profile: str | None = None
    engine_executable_sha256: str | None = None
    manifest_sha256: str | None = None
    native_output_sha256: str | None = None
    source_file_hashes: tuple[tuple[str, str], ...] = ()
    control_vector_order: tuple[tuple[int, str | None, str | None, str | None], ...] = ()
    effective_settings: dict[str, object] | None = None
    reviews: tuple[NativeProjectReview, ...] = ()

    def as_json(self) -> dict[str, object]:
        """Full identity and clocks with compact per-print diagnostics, not a second parity calculation."""
        reports: list[dict[str, object]] = []
        for item in self.reviews:
            parity = item.printed.printed_discharge_parity
            volume = item.printed.native_reporting
            reports.append(
                {
                    "model_print_id": item.model_print_id,
                    "model_print_label": item.printed.model_print_label,
                    "native_column_id": item.native_column_id,
                    "print_mapping_evidence": item.mapping_evidence,
                    "raw_increment_tokens": item.raw_increment_tokens,
                    "raw_time_tokens": item.raw_time_tokens,
                    "printed": {
                        "samples": parity.sample_count,
                        "matching_samples": parity.matching_samples,
                        "within_frozen_print_budget": parity.within_print_budget,
                        "first_outside_budget_index": parity.first_outside_budget_index,
                        "max_absolute_error_m3_s": parity.maximum_absolute_error_m3_s,
                        "predicted_peak_index": parity.predicted_peak_index,
                        "native_peak_index": parity.native_peak_index,
                        "predicted_peak_m3_s": parity.predicted_peak_m3_s,
                        "native_peak_m3_s": parity.native_peak_m3_s,
                        "predicted_physical_trapezoid_m3": parity.predicted_integral_m3,
                        "native_physical_trapezoid_m3": parity.native_integral_m3,
                        "integral_rounding_bound_m3": parity.integral_rounding_bound_m3,
                    },
                    "reporting": {
                        "native_reported_volume_token": item.native_reported_volume_text,
                        "native_reported_volume_m3": str(volume.reported_native_volume_m3)
                        if volume.reported_native_volume_m3 is not None
                        else None,
                        "native_inclusive_sample_sum_m3": str(volume.inclusive_sample_sum_m3),
                        "native_physical_trapezoid_m3": str(volume.physical_trapezoid_m3),
                        "native_volume_matches_inclusive_sum": volume.sample_sum_consistent_with_report,
                        "native_volume_matches_trapezoid": volume.trapezoid_consistent_with_report,
                        "volume_provenance": item.native_volume_source,
                    },
                }
            )
        return {
            "case_id": self.case_id,
            "classification": self.classification,
            "source_verification": self.source_verification,
            "execution_status": self.execution_status,
            "native_print_budget": self.native_print_budget,
            "native_numerical_acceptance": "unassessed",
            "reason": self.reason,
            "project_sha256": self.project_sha256,
            "model_sha256": self.model_sha256,
            "manifest_sha256": self.manifest_sha256,
            "native_output_sha256": self.native_output_sha256,
            "engine_profile": self.engine_profile,
            "engine_executable_sha256": self.engine_executable_sha256,
            "source_file_hashes": self.source_file_hashes,
            "control_vector_order": self.control_vector_order,
            "effective_settings": self.effective_settings,
            "prints": reports,
        }


@dataclass(frozen=True, slots=True)
class SuiteOutcome:
    suite_id: str
    suite_sha256: str
    cases: tuple[CaseOutcome, ...]

    def to_json(self) -> str:
        counts = Counter(case.classification for case in self.cases)
        report = {
            "format": FORMAT + "-result",
            "schema_version": VERSION,
            "suite_id": self.suite_id,
            "suite_sha256": self.suite_sha256,
            "case_count": len(self.cases),
            "counts": {
                name: counts[name]
                for name in ("computed/pass", "computed/fail", "unsupported", "incomplete", "invalid")
            },
            "native_numerical_acceptance": "unassessed",
            "cases": [case.as_json() for case in self.cases],
        }
        return json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n"

    def to_csv(self) -> str:
        """Optional per-ordinate table; raw native clocks are never mapped to model elapsed time."""
        buffer = io.StringIO(newline="")
        writer = csv.writer(buffer, lineterminator="\n")
        writer.writerow(
            (
                "case_id",
                "classification",
                "model_print_id",
                "native_column_id",
                "sample_index",
                "raw_native_increment",
                "raw_native_time",
                "native_discharge_token",
                "python_discharge_m3_s",
            )
        )
        for case in self.cases:
            for review in case.reviews:
                for index, (inc, time, native, predicted) in enumerate(
                    zip(
                        review.raw_increment_tokens,
                        review.raw_time_tokens,
                        review.raw_discharge_tokens,
                        review.predicted_discharge_m3_s,
                        strict=True,
                    )
                ):
                    writer.writerow(
                        (
                            case.case_id,
                            case.classification,
                            review.model_print_id,
                            review.native_column_id,
                            index,
                            inc,
                            time,
                            native,
                            predicted,
                        )
                    )
        return buffer.getvalue()

    @property
    def all_within_print_budget(self) -> bool:
        return bool(self.cases) and all(case.classification == "computed/pass" for case in self.cases)


def _object(raw: object, expected: set[str], label: str) -> dict[str, object]:
    data = cast("dict[str, object]", raw) if isinstance(raw, dict) else {}
    if set(data) != expected:
        message = f"{label} expects exactly {sorted(expected)}"
        raise ProjectError(message)
    return data


def _string(raw: object, label: str) -> str:
    if not isinstance(raw, str) or not raw:
        message = f"{label} must be a nonempty string"
        raise ProjectError(message)
    return raw


def _sha(raw: object, label: str) -> str:
    value = _string(raw, label)
    if HASH.fullmatch(value) is None:
        message = f"{label} must be a lowercase SHA-256"
        raise ProjectError(message)
    return value


def _source(raw: object) -> SourceFile:
    item = _object(raw, {"path", "sha256"}, "Source locator")
    return SourceFile(_string(item["path"], "Source path"), _sha(item["sha256"], "Source hash"))


def _parse_case(raw: object) -> CaseSpec:
    item = _object(raw, {"case_id", "project", "native"}, "Regression case")
    identifier = _string(item["case_id"], "Case ID")
    if IDENTIFIER.fullmatch(identifier) is None:
        message = "Case ID is not a stable ASCII identifier"
        raise ProjectError(message)
    project = None if item["project"] is None else _source(item["project"])
    native = None
    if item["native"] is not None:
        n = _object(item["native"], {"manifest", "engine_executable_sha256", "print_mapping"}, "Native ref")
        raw_mappings = n["print_mapping"]
        if not isinstance(raw_mappings, list):
            message = "Native print_mapping must be an array"
            raise ProjectError(message)
        mappings: list[PrintMapping] = []
        for entry in cast("list[object]", raw_mappings):
            e = _object(entry, {"model_print_id", "native_column_id"}, "Print mapping")
            model_id = _string(e["model_print_id"], "Model print ID")
            column = _string(e["native_column_id"], "Native column ID")
            if COLUMN.fullmatch(column) is None:
                message = "Native column must be HydNNN"
                raise ProjectError(message)
            mappings.append(PrintMapping(model_id, column))
        if len({entry.model_print_id for entry in mappings}) != len(mappings) or len(
            {entry.native_column_id for entry in mappings}
        ) != len(mappings):
            message = "Ambiguous or duplicate print mapping"
            raise ProjectError(message)
        native = NativeReference(
            _source(n["manifest"]), _sha(n["engine_executable_sha256"], "Native executable"), tuple(mappings)
        )
    return CaseSpec(identifier, project, native)


def _unique_pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    data: dict[str, object] = {}
    for key, value in pairs:
        if key in data:
            message = f"Duplicate regression JSON field: {key}"
            raise ProjectError(message)
        data[key] = value
    return data


def _reject_nonfinite(value: str) -> None:
    message = f"Invalid non-JSON numeric constant: {value}"
    raise ProjectError(message)


def load_suite(path: Path) -> RegressionSuite:
    """Read one bounded versioned manifest; per-case errors stay independently reportable."""
    if path.stat().st_size > MAX_SUITE_BYTES:
        message = "Regression manifest exceeds 2 MiB"
        raise ProjectError(message)
    raw = path.read_bytes()
    try:
        decoded: object = json.loads(
            raw.decode("utf-8"), object_pairs_hook=_unique_pairs, parse_constant=_reject_nonfinite
        )
    except (UnicodeError, ValueError) as exc:
        message = f"Invalid regression manifest JSON: {exc}"
        raise ProjectError(message) from exc
    data = _object(decoded, {"format", "schema_version", "suite_id", "cases"}, "Regression suite")
    if data["format"] != FORMAT or type(data["schema_version"]) is not int or data["schema_version"] != VERSION:
        message = "Unknown regression manifest format or schema version"
        raise ProjectError(message)
    identifier = _string(data["suite_id"], "Suite ID")
    if IDENTIFIER.fullmatch(identifier) is None:
        message = "Suite ID must be stable ASCII"
        raise ProjectError(message)
    cases = data["cases"]
    if not isinstance(cases, list) or not cases:
        message = "Regression suite must contain at least one case"
        raise ProjectError(message)
    return RegressionSuite(identifier, hashlib.sha256(raw).hexdigest(), path, tuple(cast("list[object]", cases)))


class _CaseError(Exception):
    def __init__(self, classification: Literal["unsupported", "incomplete", "invalid"], message: str) -> None:
        super().__init__(message)
        self.classification: Literal["unsupported", "incomplete", "invalid"] = classification

    @classmethod
    def unsupported(cls, message: str) -> _CaseError:
        return cls("unsupported", message)

    @classmethod
    def incomplete(cls, message: str) -> _CaseError:
        return cls("incomplete", message)

    @classmethod
    def invalid(cls, message: str) -> _CaseError:
        return cls("invalid", message)


def _verified_file(root: Path, reference: SourceFile) -> Path:
    """Use project-relative portable paths, verifying physical containment and exact bytes."""
    candidate = root / reference.path
    try:
        path = candidate.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        message = f"Missing source {reference.path}: {exc}"
        raise _CaseError.incomplete(message) from exc
    if not path.is_relative_to(root) or not path.is_file():
        message = f"Unsafe source locator: {reference.path}"
        raise _CaseError.invalid(message)
    if path.stat().st_size > 64 * 1024 * 1024:
        message = f"Source exceeds review limit: {reference.path}"
        raise _CaseError.invalid(message)
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != reference.sha256:
        message = f"Source hash mismatch: {reference.path}"
        raise _CaseError.invalid(message)
    return path


def _outcome(
    case_id: str, category: Classification, reason: str, *, source_status: SourceStatus = "not_verified"
) -> CaseOutcome:
    return CaseOutcome(case_id, category, source_status, "not_computed", "not_assessed", reason)


def _preflight_native(loaded: LoadedProject, manifest_path: Path, native_spec: NativeReference) -> None:
    """Separate unsupported profiles, captured incompleteness and invalid print identity."""
    if loaded.project.rainfall_profile == "arr-2026v1" or (
        loaded.project.rainfall_profile != "legacy-rorb" or not isinstance(loaded.project.model_source, LegacyRunFiles)
    ):
        message = "Offline CMD review requires file-backed legacy-rorb forcing"
        raise _CaseError.unsupported(message)
    if any(asset.role != "reference" for asset in loaded.project.assets):
        message = "Unprocessed external rainfall/curve input"
        raise _CaseError.unsupported(message)
    try:
        manifest_raw: object = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (UnicodeError, ValueError) as exc:
        message = f"Malformed native capture manifest: {exc}"
        raise _CaseError.invalid(message) from exc
    if not isinstance(manifest_raw, dict):
        message = "Native capture manifest must be an object"
        raise _CaseError.invalid(message)
    native = cast("dict[str, object]", manifest_raw)
    engine = native.get("engine")
    engine_kind = cast("dict[str, object]", engine).get("kind") if isinstance(engine, dict) else None
    if engine_kind not in {"RORB_CMD", "RORBwin"}:
        message = "Unrecognised or missing native engine profile"
        raise _CaseError.invalid(message)
    if engine_kind != "RORB_CMD":
        message = "Only RORB_CMD retained output is characterised"
        raise _CaseError.unsupported(message)
    outcome = native.get("outcome")
    if isinstance(outcome, str) and outcome in {"incomplete_output", "missing_output", "captured_unverified"}:
        message = f"Native capture outcome is {outcome}"
        raise _CaseError.incomplete(message)
    if outcome != "success" and outcome != "zero_runoff":
        message = f"Native capture outcome is not a valid calculation: {outcome}"
        raise _CaseError.invalid(message)
    requested = native.get("requested_print_locations")
    requested_columns: set[str] = set(cast("dict[str, object]", requested)) if isinstance(requested, dict) else set()
    actual_columns = {mapping.native_column_id for mapping in native_spec.print_mapping}
    expected_model = {entry.identifier for entry in loaded.run.catchment.print_locations}
    mapped_model = {mapping.model_print_id for mapping in native_spec.print_mapping}
    if not isinstance(requested, dict) or actual_columns != requested_columns or mapped_model != expected_model:
        message = "Ambiguous or incomplete print-location mapping coverage"
        raise _CaseError.invalid(message)


def _run_case(spec: CaseSpec, root: Path) -> CaseOutcome:
    if spec.project is None or spec.native is None:
        message = "Project or retained native reference is not supplied"
        raise _CaseError.incomplete(message)
    if not spec.native.print_mapping:
        message = "Native reference has no print mappings"
        raise _CaseError.incomplete(message)
    project = _verified_file(root, spec.project)
    manifest_path = _verified_file(root, spec.native.manifest)
    try:
        loaded = load_project(project)
    except (ProjectError, ValueError) as exc:
        message = f"Project cannot be verified: {exc}"
        raise _CaseError.invalid(message) from exc
    _preflight_native(loaded, manifest_path, spec.native)
    try:
        reviews = review_project_native_captures(
            project,
            manifest_path,
            manifest_sha256=spec.native.manifest.sha256,
            engine_executable_sha256=spec.native.engine_executable_sha256,
            print_mappings=tuple((m.model_print_id, m.native_column_id) for m in spec.native.print_mapping),
        )
    except ProjectError as exc:
        reason = str(exc)
        if "Unsupported" in reason or "only supports" in reason or "not supported" in reason:
            raise _CaseError.unsupported(reason) from exc
        if "hydrograph" in reason.lower() or "horizon" in reason.lower() or "report" in reason.lower():
            raise _CaseError.incomplete(reason) from exc
        raise _CaseError.invalid(reason) from exc
    if not reviews:
        message = "Native comparison returned no print locations"
        raise _CaseError.invalid(message)
    first = reviews[0]
    passing = all(r.printed.printed_discharge_parity.within_print_budget for r in reviews)
    return CaseOutcome(
        spec.identifier,
        "computed/pass" if passing else "computed/fail",
        "verified",
        "computed_unvalidated",
        "within" if passing else "outside",
        project_sha256=first.project_sha256,
        model_sha256=first.model_sha256,
        engine_profile=first.engine_profile,
        engine_executable_sha256=first.engine_executable_sha256,
        manifest_sha256=first.manifest_sha256,
        native_output_sha256=first.native_output_sha256,
        source_file_hashes=first.source_file_hashes,
        control_vector_order=first.control_vector_order,
        effective_settings=first.effective_settings,
        reviews=reviews,
    )


def run_suite(path: Path) -> SuiteOutcome:
    """Classify each case exactly once; unsupported/incomplete cases cannot silently disappear."""
    suite = load_suite(path)
    root = path.absolute().parent.resolve(strict=True)
    cases: list[CaseOutcome] = []
    used_ids: set[str] = set()
    for index, raw in enumerate(suite.cases, start=1):
        fallback = f"case-{index}"
        raw_record: dict[str, object] = cast("dict[str, object]", raw) if isinstance(raw, dict) else {}
        identifier = raw_record.get("case_id")
        name = identifier if isinstance(identifier, str) and IDENTIFIER.fullmatch(identifier) else fallback
        if name in used_ids:
            cases.append(_outcome(name, "invalid", "Duplicate case ID"))
            continue
        used_ids.add(name)
        try:
            spec = _parse_case(raw_record if isinstance(raw, dict) else None)
            cases.append(_run_case(spec, root))
        except _CaseError as exc:
            source_status: SourceStatus = "failed" if exc.classification == "invalid" else "not_verified"
            cases.append(_outcome(name, exc.classification, str(exc), source_status=source_status))
        except (ProjectError, OSError, TypeError, ValueError) as exc:
            cases.append(_outcome(name, "invalid", str(exc), source_status="failed"))
    return SuiteOutcome(suite.identifier, suite.sha256, tuple(cases))


def write_suite_results(report: Path, outcome: SuiteOutcome, *, details_csv: Path | None = None) -> None:
    """Exclusive-create outputs; reject existing targets before writing either file."""
    targets = (report,) if details_csv is None else (report, details_csv)
    if len({path.absolute() for path in targets}) != len(targets) or any(path.exists() for path in targets):
        message = "Regression output paths must be distinct, new files"
        raise FileExistsError(message)
    json_text = outcome.to_json()
    csv_text = outcome.to_csv() if details_csv is not None else None
    with report.open("xb") as stream:
        stream.write(json_text.encode("utf-8"))
    if details_csv is not None and csv_text is not None:
        with details_csv.open("xb") as stream:
            stream.write(csv_text.encode("utf-8"))


def main(argv: list[str] | None = None) -> int:
    """python -m runoff_routing.project_regression <suite.json> <results.json> [details.csv]."""
    args = sys.argv[1:] if argv is None else argv
    if len(args) not in (2, 3):
        print(
            "Usage: python -m runoff_routing.project_regression <suite.json> <results.json> [details.csv]",
            file=sys.stderr,
        )
        return 2
    try:
        result = run_suite(Path(args[0]))
        write_suite_results(Path(args[1]), result, details_csv=Path(args[2]) if len(args) == 3 else None)
    except (ProjectError, OSError, ValueError) as exc:
        print(f"Regression suite failed: {exc}", file=sys.stderr)
        return 2
    print(
        json.dumps(
            {
                "suite_id": result.suite_id,
                "case_count": len(result.cases),
                "classifications": [case.classification for case in result.cases],
                "native_numerical_acceptance": "unassessed",
            },
            sort_keys=True,
        )
    )
    return 0 if result.all_within_print_budget else 1


if __name__ == "__main__":
    raise SystemExit(main())
