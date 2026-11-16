"""Versioned explicit-event project batches using the established selected-engine dispatcher.

A batch request is not another project schema. One SHA-verified schema-2 project
owns catchment, controls, source ordering, rainfall method and engine selection.
Each event derives a fresh immutable S1 run in memory; no project is rewritten.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import re
import sys
from collections import Counter
from collections.abc import Callable, Iterable, Iterator, Mapping
from dataclasses import asdict, dataclass, replace
from itertools import pairwise
from pathlib import Path
from typing import Any, cast

from .cmd_engine import CmdBoundaryError, PreparedCmdModel, prepare_cmd_model
from .engine_execution import (
    SelectionSource,
    attribute_engine_outcome,
    create_engine_outcome_base,
    execute_loaded_engine,
)
from .engine_types import EngineDiagnostic, EngineOutcome, EngineSelection, EngineStatus
from .integration import RunInputError, prepare_run_model
from .native_cmd import NativeConfiguration
from .project_json import (
    EmbeddedRun,
    LoadedProject,
    ProjectError,
    load_project,
)
from .rorb_model import (
    CatchmentModel,
    LossMode,
    ParameterSet,
    RoutingValue,
    RunModel,
    StormModel,
    edit_run_model,
    from_dict,
    to_dict,
    to_json,
)
from .single_storm import PreparedCatchment

REQUEST_FORMAT = "python-runoff-routing-explicit-events"
REQUEST_VERSION = 1
_INVALID_INPUT: EngineStatus = "invalid_input"
_UNSUPPORTED_FEATURE: EngineStatus = "unsupported_feature"
REPORT_FORMAT = "python-runoff-routing-event-results"
MAX_REQUEST_BYTES = 8 * 1024 * 1024
_EVENT_ID = re.compile(r"[A-Za-z][A-Za-z0-9_.-]{0,127}\Z")
_STORM_FIELDS = {
    "title",
    "timestep_hours",
    "calculation_increments",
    "start_increment",
    "percentages",
    "depths_mm",
}
_LOSS_FIELDS = {"initial_loss_mm", "continuing", "continuing_loss_mm_h", "runoff_coefficient"}
_ROUTING_FIELDS = {"kc", "m"}
_CSV_HEADER = (
    "event_index",
    "event_id",
    "status",
    "error_code",
    "error_message",
    "project_id",
    "project_sha256",
    "effective_model_sha256",
    "original_source_sha256_json",
    "stored_engine",
    "engine",
    "numerical_profile",
    "rainfall_profile",
    "source_kind",
    "timestep_hours",
    "calculation_increments",
    "print_id",
    "print_label",
    "native_column_id",
    "sample_index",
    "physical_time_hours",
    "native_increment_token",
    "native_time_token",
    "discharge_m3_s",
    "physical_trapezoidal_volume_m3",
    "native_inclusive_reported_volume_m3",
    "discharge_units",
    "volume_units",
    "clock_convention",
)


class BatchConfigError(ValueError):
    """Malformed whole-batch request or unsafe output configuration."""


class EventConfigError(ValueError):
    """A single invalid/unsupported event that must retain its own outcome."""

    def __init__(self, status: EngineStatus, code: str, message: str) -> None:
        super().__init__(message)
        self.status: EngineStatus = status
        self.code = code


@dataclass(frozen=True, slots=True)
class ProjectEvent:
    """Typed public API request; override mappings are read, not mutated."""

    event_id: str
    storm: Mapping[str, object] | None = None
    losses: Mapping[str, object] | None = None
    routing: Mapping[str, object] | None = None


@dataclass(frozen=True, slots=True)
class EffectiveModel:
    """Shared run/save/export event settings; source documents remain separate."""

    run: RunModel
    event_id: str | None
    edited_fields: tuple[str, ...]

    @property
    def override_label(self) -> str:
        return ",".join(self.edited_fields) if self.edited_fields else "none"


def _unique_pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    """Reject duplicate keys in the request, including nested event objects."""
    entries: dict[str, object] = {}
    for key, value in pairs:
        if key in entries:
            message = f"Duplicate JSON object key: {key}"
            raise BatchConfigError(message)
        entries[key] = value
    return entries


def _reject_nonfinite(value: str) -> None:
    message = f"Nonstandard JSON constant: {value}"
    raise BatchConfigError(message)


def load_event_request(path: Path) -> tuple[object, ...]:
    """Read a versioned text-file request, preserving malformed individual events.

    Top-level schema/duplicate-key failures invalidate the request. An invalid
    event remains a per-event result rather than vanishing during parsing.
    """
    if path.stat().st_size > MAX_REQUEST_BYTES:
        message = "Event request exceeds the 8 MiB limit"
        raise BatchConfigError(message)
    raw = path.read_bytes()
    if len(raw) > MAX_REQUEST_BYTES:
        message = "Event request changed or exceeds the 8 MiB limit"
        raise BatchConfigError(message)
    try:
        parsed: object = json.loads(
            raw.decode("utf-8-sig"), object_pairs_hook=_unique_pairs, parse_constant=_reject_nonfinite
        )
    except (UnicodeError, ValueError, TypeError) as exc:
        raise BatchConfigError(str(exc)) from exc
    if not isinstance(parsed, dict):
        message = "Event request must be a JSON object"
        raise BatchConfigError(message)
    request = cast("dict[str, object]", parsed)
    if set(request) != {"format", "schema_version", "events"}:
        message = "Event request requires exactly format, schema_version and events"
        raise BatchConfigError(message)
    if request["format"] != REQUEST_FORMAT or type(request["schema_version"]) is not int:
        message = "Unknown event-request format or schema version"
        raise BatchConfigError(message)
    if request["schema_version"] != REQUEST_VERSION:
        message = "Unsupported event-request schema version"
        raise BatchConfigError(message)
    events = request["events"]
    if not isinstance(events, list) or not events:
        message = "Event request needs a nonempty events array"
        raise BatchConfigError(message)
    return tuple(cast("list[object]", events))


def _request_fields(item: object) -> dict[str, object]:
    if isinstance(item, ProjectEvent):
        data: dict[str, object] = {"event_id": item.event_id}
        if item.storm is not None:
            data["storm"] = dict(item.storm)
        if item.losses is not None:
            data["losses"] = dict(item.losses)
        if item.routing is not None:
            data["routing"] = dict(item.routing)
        return data
    if not isinstance(item, dict):
        raise EventConfigError(_INVALID_INPUT, "event_record", "Event must be a JSON object")
    data = cast("dict[str, object]", item)
    if "storages" in data:
        raise EventConfigError(_UNSUPPORTED_FEATURE, "event_storages", "Event-level special storage is unsupported")
    if set(data) - {"event_id", "storm", "losses", "routing"}:
        raise EventConfigError(_INVALID_INPUT, "event_fields", "Unknown event fields")
    return data


def _identifier(item: object, ordinal: int) -> str:
    if isinstance(item, ProjectEvent):
        value: object = item.event_id
    elif isinstance(item, dict):
        value = cast("dict[str, object]", item).get("event_id")
    else:
        value = None
    if isinstance(value, str) and _EVENT_ID.fullmatch(value):
        return value
    return f"<request:{ordinal}>"


def _overlay(raw: object, allowed: set[str], label: str) -> dict[str, object]:
    if not isinstance(raw, dict):
        raise EventConfigError(_INVALID_INPUT, "event_overlay", f"{label} must be a JSON object")
    data = cast("dict[str, object]", raw)
    if set(data) - allowed:
        raise EventConfigError(_UNSUPPORTED_FEATURE, f"{label}_fields", f"Unsupported {label} override fields")
    # Alias normalization may pop() a loss field. Never mutate the caller's
    # raw event dictionary, including when replaying or exporting it twice.
    return dict(data)


def _derive_storm(original: StormModel, raw: object) -> StormModel:
    patch = _overlay(raw, _STORM_FIELDS, "storm")
    document = to_dict(original)
    body = cast("dict[str, Any]", document["model"])
    body.update(patch)
    restored = from_dict(document)
    if not isinstance(restored, StormModel):
        message = "Storm override did not produce an S1 storm"
        raise EventConfigError(_INVALID_INPUT, "storm_model", message)
    return restored


def _derive_parameters(original: ParameterSet, raw: object) -> ParameterSet:
    if len(original.losses) != 1:
        raise EventConfigError(
            _UNSUPPORTED_FEATURE, "loss_override_scope", "Only one-ISA explicit event losses can be overridden"
        )
    patch = _overlay(raw, _LOSS_FIELDS, "losses")
    named = {"continuing_loss_mm_h", "runoff_coefficient"} & patch.keys()
    if len(named) > 1 or ("continuing" in patch and named):
        raise EventConfigError(
            _INVALID_INPUT, "loss_fields", "Mutually exclusive continuing loss and runoff-coefficient fields"
        )
    if "continuing_loss_mm_h" in patch:
        if original.loss_model != LossMode.INITIAL_CONTINUING:
            raise EventConfigError(_INVALID_INPUT, "loss_mode", "continuing_loss_mm_h requires loss mode 1")
        patch["continuing"] = patch.pop("continuing_loss_mm_h")
    if "runoff_coefficient" in patch:
        if original.loss_model != LossMode.INITIAL_RUNOFF_COEFFICIENT:
            raise EventConfigError(_INVALID_INPUT, "loss_mode", "runoff_coefficient requires loss mode 2")
        patch["continuing"] = patch.pop("runoff_coefficient")
    document = to_dict(original)
    body = cast("dict[str, Any]", document["model"])
    losses = cast("list[dict[str, Any]]", body["losses"])
    losses[0].update(patch)
    restored = from_dict(document)
    if not isinstance(restored, ParameterSet):
        message = "Loss override did not produce S1 parameters"
        raise EventConfigError(_INVALID_INPUT, "loss_model", message)
    return restored


def _derive_routing(original: ParameterSet, raw: object) -> ParameterSet:
    """Change explicit lumped routing parameters without changing CATG source order."""
    if not original.lumped_kc or len(original.routing) != 1:
        raise EventConfigError(
            _UNSUPPORTED_FEATURE,
            "routing_override_scope",
            "Per-event routing parameter override requires a single lumped kc/m",
        )
    patch = _overlay(raw, _ROUTING_FIELDS, "routing")
    document = to_dict(original)
    body = cast("dict[str, Any]", document["model"])
    routing = cast("list[dict[str, Any]]", body["routing"])
    routing[0].update(patch)
    restored = from_dict(document)
    if not isinstance(restored, ParameterSet):
        message = "Routing override did not produce S1 parameters"
        raise EventConfigError(_INVALID_INPUT, "routing_model", message)
    return restored


def _validated_override[T](original: T, raw: object, converter: Callable[[T, object], T], code: str) -> T:
    """Retain typed per-event failure codes without obscuring unsupported fields."""
    try:
        return converter(original, raw)
    except EventConfigError:
        raise
    except (TypeError, ValueError, ArithmeticError) as exc:
        # Decimal Overflow/InvalidOperation from S1 validation is an event-local
        # invalid input, not a reason to discard the remaining batch.
        raise EventConfigError(_INVALID_INPUT, code, str(exc)) from exc


def _event_run(current: RunModel, fields: dict[str, object]) -> tuple[RunModel, tuple[str, ...]]:
    storm = current.storm
    parameters = current.parameters
    changed: list[str] = []
    if "storm" in fields:
        storm = _validated_override(storm, fields["storm"], _derive_storm, "storm_model")
        changed.append("storm")
    if "losses" in fields:
        parameters = _validated_override(parameters, fields["losses"], _derive_parameters, "loss_model")
        changed.append("losses")
    if "routing" in fields:
        parameters = _validated_override(parameters, fields["routing"], _derive_routing, "routing_model")
        changed.append("routing")
    try:
        return edit_run_model(current, parameters=parameters, storm=storm), tuple(changed)
    except (TypeError, ValueError, ArithmeticError) as exc:
        raise EventConfigError(_INVALID_INPUT, "event_model", str(exc)) from exc


def resolve_effective_model(
    base: RunModel,
    event: ProjectEvent | dict[str, object] | None = None,
) -> EffectiveModel:
    """Resolve one explicitly selected event using exactly the same validation for all consumers.

    The function does not read, write or mutate source files. Callers own source
    bindings, project persistence, native expressibility and engine selection.
    """
    if event is None:
        return EffectiveModel(base, None, ())
    identifier = _identifier(event, 1)
    if identifier.startswith("<request:"):
        raise EventConfigError(_INVALID_INPUT, "event_id", "Event ID must be a stable, nonempty ASCII identifier")
    fields = _request_fields(event)
    run, changed = _event_run(base, fields)
    return EffectiveModel(run, identifier, changed)


def _event_failure(base: EngineOutcome, status: EngineStatus, code: str, message: str) -> EngineOutcome:
    return replace(base, status=status, diagnostics=(EngineDiagnostic(code, message),))


def _event_preparation(
    loaded: LoadedProject,
    selection: EngineSelection,
    python_cache: dict[tuple[CatchmentModel, tuple[RoutingValue, ...]], PreparedCatchment],
    cmd_cache: dict[tuple[CatchmentModel, tuple[RoutingValue, ...]], PreparedCmdModel],
) -> tuple[PreparedCatchment | None, PreparedCmdModel | None]:
    """Reuse only fixed geometry/coefficients; never event state or hydrographs."""
    key = (loaded.run.catchment, loaded.run.parameters.routing)
    if selection.engine == "python":
        prepared = python_cache.get(key)
        if prepared is None:
            try:
                prepared = prepare_run_model(loaded.run)
            except RunInputError:
                return None, None  # The normal dispatcher retains its original typed rejection.
            python_cache[key] = prepared
        return prepared, None
    if selection.engine == "python-cmd":
        prepared_cmd = cmd_cache.get(key)
        if prepared_cmd is None:
            try:
                prepared_cmd = prepare_cmd_model(loaded)
            except CmdBoundaryError:
                return None, None  # An unsupported event does not poison the next input.
            cmd_cache[key] = prepared_cmd
        return None, prepared_cmd
    return None, None


def iter_project_events(
    project_path: Path,
    events: Iterable[object],
    *,
    selection: EngineSelection | None = None,
    selection_source: SelectionSource = "api_override",
    native_config: NativeConfiguration | None = None,
    wheel_artifact: Path | None = None,
    _loaded_project: LoadedProject | None = None,
) -> Iterator[EngineOutcome]:
    """Execute requested events in order, with one result per input and no file-per-event.

    Source hashes and package/wheel attribution are verified once. The typed
    project source is unchanged; every event has an independent immutable model
    and numerical calculation. No solver or native engine is substituted.

    _loaded_project is an internal-only trusted source snapshot for E's sealed
    MC requests; it must be validated and identified before entering this
    iterator, so routing cannot independently reopen a changed model.
    """
    loaded = load_project(project_path) if _loaded_project is None else _loaded_project
    effective = loaded.project.engine if selection is None else selection
    if _loaded_project is not None and effective.engine == "rorb-cmd":
        message = "An in-memory prepared project snapshot cannot be used for native rorb-cmd source files"
        raise BatchConfigError(message)
    if selection_source not in ("api_override", "cli_override"):
        message = "selection_source must be api_override or cli_override"
        raise BatchConfigError(message)
    source: SelectionSource = "project" if selection is None else selection_source
    attributed = attribute_engine_outcome(create_engine_outcome_base(loaded, effective, source), wheel_artifact)
    source_kind = "embedded-run" if isinstance(loaded.project.model_source, EmbeddedRun) else "rorb-files"
    python_cache: dict[tuple[CatchmentModel, tuple[RoutingValue, ...]], PreparedCatchment] = {}
    cmd_cache: dict[tuple[CatchmentModel, tuple[RoutingValue, ...]], PreparedCmdModel] = {}
    seen: set[str] = set()
    for ordinal, item in enumerate(events, start=1):
        identifier = _identifier(item, ordinal)
        event_base = replace(
            attributed,
            event_id=identifier,
            effective_inputs={**attributed.effective_inputs, "source_kind": source_kind, "event_overrides": "none"},
        )
        if identifier.startswith("<request:"):
            yield _event_failure(
                event_base, "invalid_input", "event_id", "Event ID must be a stable, nonempty ASCII identifier"
            )
            continue
        if identifier in seen:
            yield _event_failure(event_base, "invalid_input", "duplicate_event_id", "Duplicate event ID")
            continue
        seen.add(identifier)
        try:
            resolved = resolve_effective_model(loaded.run, cast("ProjectEvent | dict[str, object]", item))
            model, override = resolved.run, resolved.override_label
        except EventConfigError as exc:
            yield _event_failure(event_base, exc.status, exc.code, str(exc))
            continue
        effective_settings = {
            **event_base.effective_inputs,
            "timestep_hours": str(model.storm.timestep_hours),
            "calculation_increments": model.storm.calculation_increments,
            "loss_model": model.parameters.loss_model,
            "event_overrides": override,
            "source_kind": source_kind,
        }
        event_base = replace(
            event_base,
            model_sha256=hashlib.sha256(to_json(model).encode("utf-8")).hexdigest(),
            effective_inputs=effective_settings,
        )
        if attributed.diagnostics:
            yield replace(event_base, status=attributed.status)
            continue
        event_loaded = replace(loaded, run=model)
        prepared_python, prepared_cmd = _event_preparation(event_loaded, effective, python_cache, cmd_cache)
        yield execute_loaded_engine(
            event_loaded,
            event_base,
            project_path=project_path,
            native_config=native_config,
            prepared_python=prepared_python,
            prepared_cmd=prepared_cmd,
            materialize_native_event=effective.engine == "rorb-cmd" and override != "none",
        )


def _trapezoidal_volume(outcome: EngineOutcome, values: tuple[float, ...]) -> float | None:
    """Derived physical-time integral only; never call it CMD reported volume."""
    if len(values) < 2 or len(values) != len(outcome.physical_time_hours):
        return None
    try:
        times = tuple(float(value) for value in outcome.physical_time_hours)
    except ValueError:
        return None
    if not all(math.isfinite(value) for value in (*times, *values)):
        return None
    if any(b <= a for a, b in pairwise(times)):
        return None
    return 3600.0 * math.fsum(
        0.5 * (a + b) * (end - start)
        for a, b, start, end in zip(values[:-1], values[1:], times[:-1], times[1:], strict=True)
    )


@dataclass(frozen=True, slots=True)
class ProjectBatchReport:
    """Collected full outcomes; streaming API avoids retaining them if unnecessary."""

    outcomes: tuple[EngineOutcome, ...]

    @property
    def succeeded(self) -> bool:
        return bool(self.outcomes) and all(item.status == "computed_unvalidated" for item in self.outcomes)

    def to_json(self) -> str:
        payload = {
            "format": REPORT_FORMAT,
            "schema_version": REQUEST_VERSION,
            "requested_event_count": len(self.outcomes),
            "completed_event_count": sum(item.status == "computed_unvalidated" for item in self.outcomes),
            "status_counts": dict(sorted(Counter(item.status for item in self.outcomes).items())),
            "outcomes": [asdict(item) for item in self.outcomes],
            "volumes": [
                {
                    "event_id": item.event_id,
                    "print_id": graph.print_id,
                    "physical_trapezoidal_volume_m3": _trapezoidal_volume(item, graph.discharge_m3_s),
                    "native_inclusive_reported_volume_m3": None,
                }
                for item in self.outcomes
                for graph in item.hydrographs
            ],
        }
        return json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True, allow_nan=False) + "\n"

    def to_csv(self) -> str:
        buffer = io.StringIO(newline="")
        writer = csv.writer(buffer, lineterminator="\n")
        writer.writerow(_CSV_HEADER)
        for ordinal, outcome in enumerate(self.outcomes, start=1):
            error_code = outcome.diagnostics[0].code if outcome.diagnostics else ""
            error_message = outcome.diagnostics[0].message if outcome.diagnostics else ""
            common = (
                ordinal,
                outcome.event_id,
                outcome.status,
                error_code,
                error_message,
                outcome.project_id,
                outcome.project_sha256,
                outcome.model_sha256,
                json.dumps(outcome.source_file_hashes, ensure_ascii=False, separators=(",", ":")),
                outcome.stored_selection.engine,
                outcome.effective_selection.engine,
                outcome.effective_selection.numerical_profile,
                outcome.rainfall_profile,
                outcome.effective_inputs.get("source_kind", ""),
                outcome.effective_inputs["timestep_hours"],
                outcome.effective_inputs["calculation_increments"],
            )
            if not outcome.hydrographs:
                writer.writerow((*common, *("" for _ in range(len(_CSV_HEADER) - len(common)))))
                continue
            for graph in outcome.hydrographs:
                volume = _trapezoidal_volume(outcome, graph.discharge_m3_s)
                for index, discharge in enumerate(graph.discharge_m3_s):
                    hour = outcome.physical_time_hours[index] if index < len(outcome.physical_time_hours) else ""
                    inc = (
                        outcome.native_raw_increment_tokens[index]
                        if index < len(outcome.native_raw_increment_tokens)
                        else ""
                    )
                    raw_time = (
                        outcome.native_raw_time_tokens[index] if index < len(outcome.native_raw_time_tokens) else ""
                    )
                    writer.writerow(
                        (
                            *common,
                            graph.print_id,
                            graph.label,
                            graph.native_column_id or "",
                            index,
                            hour,
                            inc,
                            raw_time,
                            discharge,
                            volume if index == 0 else "",
                            "",
                            graph.units,
                            "m3",
                            outcome.native_clock_convention or "model_elapsed_from_zero",
                        )
                    )
        return buffer.getvalue()

    def to_text(self) -> str:
        counts = Counter(item.status for item in self.outcomes)
        header = ["Runoff routing: explicit event results"]
        if self.outcomes:
            first = self.outcomes[0]
            header.extend(
                (
                    f"Project: {first.project_id} ({first.project_sha256})",
                    f"Stored engine: {first.stored_selection.engine}/{first.stored_selection.numerical_profile}",
                    f"Effective engine: {first.effective_selection.engine}/{first.effective_selection.numerical_profile}",
                )
            )
        header.append(
            f"Requested: {len(self.outcomes)}  Computed: {counts['computed_unvalidated']}  "
            f"Other: {len(self.outcomes) - counts['computed_unvalidated']}"
        )
        for index, outcome in enumerate(self.outcomes, start=1):
            if len(self.outcomes) > 20 and outcome.status == "computed_unvalidated":
                continue
            reason = f" [{outcome.diagnostics[0].code}]" if outcome.diagnostics else ""
            header.append(f"{index}. {outcome.event_id}: {outcome.status}{reason}")
        header.append("Numerical/native parity: not assessed; physical trapezoidal volume is not CMD reported volume.")
        return "\n".join(header) + "\n"


def run_project_events(
    project_path: Path,
    events: Iterable[object],
    *,
    selection: EngineSelection | None = None,
    selection_source: SelectionSource = "api_override",
    native_config: NativeConfiguration | None = None,
    wheel_artifact: Path | None = None,
    _loaded_project: LoadedProject | None = None,
) -> ProjectBatchReport:
    """Materialise the streaming results; never hide failed/unsupported events."""
    outcomes = tuple(
        iter_project_events(
            project_path,
            events,
            selection=selection,
            selection_source=selection_source,
            native_config=native_config,
            wheel_artifact=wheel_artifact,
            _loaded_project=_loaded_project,
        )
    )
    if not outcomes:
        message = "An explicit batch must request at least one event"
        raise BatchConfigError(message)
    return ProjectBatchReport(outcomes)


def write_batch_results(prefix: Path, report: ProjectBatchReport) -> tuple[Path, Path, Path]:
    """Exclusive-create JSON, CSV and text. Roll back only files created here."""
    paths = (Path(f"{prefix}.json"), Path(f"{prefix}.csv"), Path(f"{prefix}.txt"))
    if len(set(paths)) != len(paths) or any(item.exists() or item.is_symlink() for item in paths):
        message = "One or more batch result destinations already exist"
        raise BatchConfigError(message)
    contents = (report.to_json(), report.to_csv(), report.to_text())
    created: list[Path] = []
    try:
        for path, content in zip(paths, contents, strict=True):
            with path.open("xb") as stream:
                created.append(path)
                stream.write(content.encode("utf-8"))
    except OSError:
        for path in created:
            path.unlink(missing_ok=True)
        raise
    return paths


def main(argv: list[str] | None = None) -> int:
    """CLI for selected-engine one-event or requested explicit-event batches."""
    parser = argparse.ArgumentParser(prog="python -m runoff_routing.project_batch")
    parser.add_argument("project", type=Path, help="validated versioned project JSON")
    parser.add_argument("output_prefix", type=Path, help="exclusive new .json/.csv/.txt report prefix")
    parser.add_argument("--events", type=Path, help="versioned JSON explicit-event request; default: stored event")
    parser.add_argument("--engine", choices=("python", "python-cmd", "rorb-cmd"))
    parser.add_argument("--numerical-profile")
    parser.add_argument("--native-config", type=Path)
    parser.add_argument("--wheel-artifact", type=Path)
    try:
        options = parser.parse_args(argv)
    except SystemExit as exc:
        return exc.code if isinstance(exc.code, int) else 2
    if options.engine is None and options.numerical_profile is not None:
        print("--numerical-profile requires an explicit --engine", file=sys.stderr)
        return 2
    prefix: Path = options.output_prefix
    output_paths = tuple(Path(f"{prefix}{suffix}") for suffix in (".json", ".csv", ".txt"))
    if any(path.exists() or path.is_symlink() for path in output_paths):
        print("Batch result destination already exists; no files overwritten", file=sys.stderr)
        return 2
    try:
        selected = (
            EngineSelection.for_engine(options.engine, options.numerical_profile)
            if options.engine is not None
            else None
        )
        native = NativeConfiguration.from_file(options.native_config) if options.native_config is not None else None
        requested = (
            load_event_request(options.events)
            if options.events is not None
            else (ProjectEvent(load_project(options.project).project.identifier),)
        )
        report = run_project_events(
            options.project,
            requested,
            selection=selected,
            selection_source="cli_override",
            native_config=native,
            wheel_artifact=options.wheel_artifact,
        )
        write_batch_results(prefix, report)
    except (BatchConfigError, ProjectError, OSError, ValueError, TypeError) as exc:
        print(f"Batch execution failed: {exc}", file=sys.stderr)
        return 2
    print(report.to_text(), end="")
    return 0 if report.succeeded else 2


if __name__ == "__main__":
    raise SystemExit(main())
