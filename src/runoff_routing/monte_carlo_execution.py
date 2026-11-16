"""Resumable Monte Carlo execution through the existing prepared #119 event iterator.

Sampling, probability-to-depth conversion and frequency interpolation are owned by
#146 and #147. This implementation stores no full batch of Q arrays in memory.
The JSONL execution request is an immutable boundary, not a second sample plan.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sqlite3
import sys
import tempfile
from collections import Counter
from collections.abc import Iterator
from contextlib import closing
from dataclasses import dataclass
from decimal import Decimal
from itertools import islice
from pathlib import Path
from typing import cast

from .engine_provenance import identify_implementation, verify_installed_wheel
from .engine_types import EngineOutcome, EngineSelection
from .monte_carlo_bridge import create_saved_sample_plan, prepare_saved_sample_plan
from .monte_carlo_effective import (
    MAX_LINE_BYTES,
    EffectiveMCEvent,
    MCRequestHeader,
    encode_jsonl_line,
    iter_effective_events,
    parse_jsonl_line,
    preparation_model_sha256,
    read_header,
    sha256_file,
    validate_effective_request,
)
from .monte_carlo_frequency_bridge import write_mc_frequency
from .project_batch import (
    ProjectBatchReport,
    ProjectEvent,
    iter_project_events,
    run_project_events,
    write_batch_results,
)
from .project_json import LoadedProject, load_project

LEDGER_FORMAT = "python-runoff-routing-mc-event-ledger"
LEDGER_VERSION = 3
_STATUS_OK = "computed_unvalidated"
_LEDGER_ROW_KEYS = {
    "sample_id",
    "event_id",
    "original_tp_id",
    "original_tp_order",
    "tp_source_kind",
    "tp_aep_band",
    "tp_area_bin",
    "tp_region",
    "tp_bin_id",
    "loss_policy",
    "rainfall_aep_percent",
    "arf_factor",
    "previous_record_sha256",
    "record_sha256",
    "scenario_id",
    "duration_min",
    "stratum_id",
    "probability_weight",
    "effective_event_sha256",
    "effective_model_sha256",
    "status",
    "diagnostics",
    "requested_print_ids",
    "sites",
}


class MCRunError(ValueError):
    """A stale checkpoint, unsupported engine or invalid model/ledger."""


@dataclass(frozen=True, slots=True)
class MCRunSummary:
    expected: int
    recorded: int
    status_counts: dict[str, int]
    zero_peak_events: int
    ledger_sha256: str

    @property
    def complete(self) -> bool:
        return self.recorded == self.expected and self.status_counts == {_STATUS_OK: self.expected}

    def to_text(self) -> str:
        return (
            f"MC events: {self.recorded}/{self.expected} checkpointed\n"
            f"Statuses: {json.dumps(self.status_counts, sort_keys=True)}\n"
            f"All-site zero-peak successful events: {self.zero_peak_events}\n"
            f"Ledger SHA-256 (pin externally for authenticity): {self.ledger_sha256}\n"
            f"Software execution complete: {str(self.complete).lower()}\n"
            "Flood-frequency estimate: requires #147 full-plan adapter. Native/statistical parity: not assessed.\n"
        )


def _project_subset(loaded: LoadedProject) -> None:
    run = loaded.run
    if (
        run.parameters.num_isa != 1
        or run.parameters.loss_model != 1
        or len(run.parameters.losses) != 1
        or run.parameters.num_bursts != 1
        or run.storm.pattern_basis != "percent_of_depth"
        or run.storm.preburst_bins
        or any(subarea.impervious_fraction != 0 for subarea in run.catchment.subareas)
        or len(run.storm.subarea_ids) != len(run.catchment.subareas)
        or any(asset.role != "reference" for asset in loaded.project.assets)
        or loaded.project.rainfall_profile not in ("explicit", "legacy-rorb")
    ):
        message = "MC execution currently requires a fully pervious, single-ISA, IL/CL explicit-storm project"
        raise MCRunError(message)


def _fixed_parameters(record: EffectiveMCEvent, loaded: LoadedProject) -> None:
    losses = record.event.losses
    storm = record.event.storm
    if losses is None or storm is None:
        message = "Explicit storm and losses required"
        raise MCRunError(message)
    if Decimal(cast("str", losses["continuing"])) != loaded.run.parameters.losses[0].continuing or len(
        cast("list[object]", storm["depths_mm"])
    ) != len(loaded.run.storm.subarea_ids):
        message = "MC subset fixes continuing loss and pervious subarea source population"
        raise MCRunError(message)


def _header(
    project: LoadedProject,
    input_sha256: str,
    *,
    selection: EngineSelection,
    wheel_artifact: Path | None,
    request_path: Path,
) -> dict[str, object]:
    if selection.engine != "python-cmd" or selection.numerical_profile != "cmd-6.44":
        message = "Current MC routing supports only explicitly selected python-cmd/cmd-6.44"
        raise MCRunError(message)
    identity = identify_implementation()
    wheel_sha256 = verify_installed_wheel(wheel_artifact) if wheel_artifact is not None else None
    header = read_header(request_path)
    if header.preparation_model_sha256 != preparation_model_sha256(project.run):
        message = "MC effective request was prepared for a different source model; reprepare before routing"
        raise MCRunError(message)
    return {
        "format": LEDGER_FORMAT,
        "schema_version": LEDGER_VERSION,
        "request_sha256": input_sha256,
        "plan_sha256": header.plan_sha256,
        "preparation_model_sha256": header.preparation_model_sha256,
        "sample_population_id": header.sample_population_id,
        "parent_plan_sha256": header.parent_plan_sha256,
        "policy_id": header.policy_id,
        "source_files": [{"path": f.path, "sha256": f.sha256} for f in header.source_files],
        "populations": [p.to_dict() for p in header.populations],
        "expected_event_count": header.event_count,
        "project_sha256": hashlib.sha256(project.original_json_bytes).hexdigest(),
        "project_file_hashes": [list(pair) for pair in project.file_hashes],
        "engine": selection.engine,
        "numerical_profile": selection.numerical_profile,
        "implementation_revision": identity.revision,
        "package_version": identity.package_version,
        "wheel_sha256": wheel_sha256,
    }


def _event_row(event: EffectiveMCEvent, result: EngineOutcome) -> dict[str, object]:
    sites: list[dict[str, object]] = []
    status = result.status
    diagnostics = [{"code": item.code, "message": item.message} for item in result.diagnostics]
    if status == _STATUS_OK:
        if (
            not result.requested_print_ids
            or len(result.hydrographs) != len(result.requested_print_ids)
            or {item.print_id for item in result.hydrographs} != set(result.requested_print_ids)
        ):
            status = "incomplete_output"
            diagnostics.append({"code": "mc_missing_site", "message": "Missing or duplicate requested output site"})
        for graph in result.hydrographs:
            ordinates = graph.discharge_m3_s
            if (
                not ordinates
                or len(ordinates) != len(result.physical_time_hours)
                or not all(math.isfinite(value) and value >= 0 for value in ordinates)
            ):
                status = "incomplete_output"
                diagnostics.append({"code": "mc_nonfinite_peak", "message": "Unusable discharge series"})
                break
            peak = max(ordinates)
            index = ordinates.index(peak)
            sites.append(
                {
                    "print_id": graph.print_id,
                    "label": graph.label,
                    "peak_m3_s": peak,
                    "peak_index": index,
                    "peak_time_hours": (
                        result.physical_time_hours[index] if index < len(result.physical_time_hours) else None
                    ),
                }
            )
        if status != _STATUS_OK:
            sites = []
    return {
        "sample_id": event.sample_id,
        "event_id": event.event.event_id,
        "original_tp_id": event.original_tp_id,
        "original_tp_order": event.original_tp_order,
        "tp_source_kind": event.tp_source_kind,
        "tp_aep_band": event.tp_aep_band,
        "tp_area_bin": event.tp_area_bin,
        "tp_region": event.tp_region,
        "tp_bin_id": event.tp_bin_id,
        "loss_policy": event.loss_policy,
        "rainfall_aep_percent": str(event.rainfall_aep_percent),
        "arf_factor": str(event.arf_factor),
        "scenario_id": event.scenario_id,
        "duration_min": event.duration_min,
        "stratum_id": event.stratum_id,
        "probability_weight": str(event.probability_weight),
        "effective_event_sha256": event.digest(),
        "effective_model_sha256": result.model_sha256,
        "status": status,
        "diagnostics": diagnostics,
        "requested_print_ids": list(result.requested_print_ids),
        "sites": sites,
    }


def _seal_record(record: dict[str, object], previous: str) -> dict[str, object]:
    """Hash all result fields and the previous row; not a digital signature."""
    payload = {**record, "previous_record_sha256": previous}
    checksum = hashlib.sha256(encode_jsonl_line(payload)).hexdigest()
    return {**payload, "record_sha256": checksum}


def _verify_record_checksum(record: dict[str, object], previous: str, ordinal: int) -> str:
    claimed = record.get("record_sha256")
    payload = {key: value for key, value in record.items() if key != "record_sha256"}
    calculated = hashlib.sha256(encode_jsonl_line(payload)).hexdigest()
    if record.get("previous_record_sha256") != previous or claimed != calculated:
        message = f"MC ledger checksum/chain mismatch at record {ordinal}"
        raise MCRunError(message)
    return calculated


def _read_ledger(path: Path) -> Iterator[dict[str, object]]:
    with path.open("rb") as stream:
        first = stream.readline(MAX_LINE_BYTES + 1)
        if not first:
            message = "Empty MC ledger"
            raise MCRunError(message)
        raw_header = parse_jsonl_line(first)
        if not isinstance(raw_header, dict):
            message = "Invalid MC ledger header"
            raise MCRunError(message)
        yield cast("dict[str, object]", raw_header)
        for ordinal, raw in enumerate(iter(lambda: stream.readline(MAX_LINE_BYTES + 1), b""), start=1):
            parsed = parse_jsonl_line(raw)
            if not isinstance(parsed, dict):
                message = f"Invalid ledger event record at row {ordinal}"
                raise MCRunError(message)
            row = cast("dict[str, object]", parsed)
            if set(row) != _LEDGER_ROW_KEYS:
                message = f"Invalid ledger event record at row {ordinal}"
                raise MCRunError(message)
            yield row


def _existing_prefix(path: Path, expected: dict[str, object], request_path: Path) -> tuple[int, str]:
    """Only an unchanged complete-prefix checkpoint may be resumed.

    A new extended plan revision changes the request SHA and weights. It must
    use a new ledger and reaggregate under all of the new weights.
    """
    recorded = _read_ledger(path)
    actual_header = next(recorded)
    if actual_header != expected:
        message = "MC checkpoint belongs to a different plan/policy/source/engine/code revision"
        raise MCRunError(message)
    count = 0
    previous = hashlib.sha256(encode_jsonl_line(expected)).hexdigest()
    effective = iter_effective_events(request_path)
    for row in recorded:
        previous = _verify_record_checksum(row, previous, count + 1)
        candidate = next(effective, None)
        if candidate is None:
            message = "Ledger contains more events than the request"
            raise MCRunError(message)
        if (
            row["sample_id"] != candidate.sample_id
            or row["event_id"] != candidate.event.event_id
            or row["original_tp_id"] != candidate.original_tp_id
            or row["original_tp_order"] != candidate.original_tp_order
            or row["tp_source_kind"] != candidate.tp_source_kind
            or row["tp_aep_band"] != candidate.tp_aep_band
            or row["tp_area_bin"] != candidate.tp_area_bin
            or row["tp_region"] != candidate.tp_region
            or row["tp_bin_id"] != candidate.tp_bin_id
            or row["loss_policy"] != candidate.loss_policy
            or row["rainfall_aep_percent"] != str(candidate.rainfall_aep_percent)
            or row["arf_factor"] != str(candidate.arf_factor)
            or row["scenario_id"] != candidate.scenario_id
            or row["duration_min"] != candidate.duration_min
            or row["stratum_id"] != candidate.stratum_id
            or row["probability_weight"] != str(candidate.probability_weight)
            or row["effective_event_sha256"] != candidate.digest()
        ):
            message = f"Mixed or reordered checkpoint at event {count + 1}"
            raise MCRunError(message)
        count += 1
    return count, previous


def _new_ledger(path: Path, header: dict[str, object]) -> str:
    if path.exists() or path.is_symlink():
        message = "MC ledger already exists; specify --resume for an unchanged plan"
        raise MCRunError(message)
    with path.open("xb") as stream:
        stream.write(encode_jsonl_line(header))
        stream.flush()
        os.fsync(stream.fileno())
    return hashlib.sha256(encode_jsonl_line(header)).hexdigest()


def _append_ledger(path: Path, record: dict[str, object], previous: str) -> str:
    sealed = _seal_record(record, previous)
    encoded = encode_jsonl_line(sealed)
    if len(encoded) > MAX_LINE_BYTES:
        message = "Compact MC ledger record exceeds bounded line length"
        raise MCRunError(message)
    with path.open("ab") as stream:
        stream.write(encoded)
        stream.flush()
        os.fsync(stream.fileno())
    return cast("str", sealed["record_sha256"])


def summarise_ledger(
    path: Path,
    request_path: Path,
    expected: dict[str, object],
    *,
    expected_ledger_sha256: str | None = None,
) -> MCRunSummary:
    """Count all planned success/zero/failure states; never call partial a curve."""
    completed, _ = _existing_prefix(path, expected, request_path)
    ledger_digest = sha256_file(path)
    if expected_ledger_sha256 is not None and ledger_digest != expected_ledger_sha256:
        message = "MC ledger differs from the independently pinned original SHA-256"
        raise MCRunError(message)
    counts: Counter[str] = Counter()
    zeros = 0
    rows = _read_ledger(path)
    next(rows)
    for record in rows:
        status = record["status"]
        if not isinstance(status, str):
            message = "Invalid MC ledger status"
            raise MCRunError(message)
        counts[status] += 1
        sites = record["sites"]
        if not isinstance(sites, list):
            message = "Invalid MC ledger site collection"
            raise MCRunError(message)
        sites_list = cast("list[object]", sites)
        if (
            status == _STATUS_OK
            and sites_list
            and all(
                isinstance(site, dict) and cast("dict[str, object]", site).get("peak_m3_s") == 0 for site in sites_list
            )
        ):
            zeros += 1
    return MCRunSummary(
        int(cast("int", expected["expected_event_count"])),
        completed,
        dict(sorted(counts.items())),
        zeros,
        ledger_digest,
    )


def execute_mc_request(
    project_path: Path,
    request_path: Path,
    ledger_path: Path,
    *,
    resume: bool = False,
    selection: EngineSelection | None = None,
    wheel_artifact: Path | None = None,
) -> MCRunSummary:
    """Checkpoint each completed event, streaming the existing runner and prepared geometry.

    No full routed hydrographs persist in the compact ledger. Use replay_mc_event
    for a selected complete event's unchanged full ordinary batch output.
    """
    _, request_hash = validate_effective_request(request_path)
    loaded = load_project(project_path)
    _project_subset(loaded)
    for planned in iter_effective_events(request_path):
        _fixed_parameters(planned, loaded)
    selected = loaded.project.engine if selection is None else selection
    header = _header(loaded, request_hash, selection=selected, wheel_artifact=wheel_artifact, request_path=request_path)
    if ledger_path.is_symlink():
        message = "MC ledger symlinks are not accepted"
        raise MCRunError(message)
    if resume:
        completed, previous = _existing_prefix(ledger_path, header, request_path)
    else:
        previous = _new_ledger(ledger_path, header)
        completed = 0
    remaining = islice(iter_effective_events(request_path), completed, None)
    # Two bounded iterators over the same immutable request are intentional:
    # iter_project_events consumes its own source once, maintaining one geometry
    # cache across the whole remaining batch, while the outer stream retains
    # the weight/identity corresponding to each reported EngineOutcome.
    model_events = (record.event for record in islice(iter_effective_events(request_path), completed, None))
    outcomes = iter_project_events(
        project_path,
        model_events,
        selection=selected,
        selection_source="api_override",
        wheel_artifact=wheel_artifact,
        _loaded_project=loaded,
    )
    for record, outcome in zip(remaining, outcomes, strict=True):
        _fixed_parameters(record, loaded)
        if outcome.event_id != record.event.event_id:
            message = "Existing runner returned an outcome with a different event ID"
            raise MCRunError(message)
        previous = _append_ledger(ledger_path, _event_row(record, outcome), previous)
    if sha256_file(request_path) != request_hash:
        message = "MC request changed during execution; checkpoint is not reusable"
        raise MCRunError(message)
    return summarise_ledger(ledger_path, request_path, header)


def iter_verified_mc_results(
    project_path: Path,
    request_path: Path,
    ledger_path: Path,
    *,
    selection: EngineSelection | None = None,
    wheel_artifact: Path | None = None,
) -> Iterator[dict[str, object]]:
    """Yield hash-checked results, including incomplete positive-weight events."""
    _, request_sha = validate_effective_request(request_path)
    loaded = load_project(project_path)
    _project_subset(loaded)
    selected = loaded.project.engine if selection is None else selection
    header = _header(loaded, request_sha, selection=selected, wheel_artifact=wheel_artifact, request_path=request_path)
    _existing_prefix(ledger_path, header, request_path)
    before = sha256_file(ledger_path)
    rows = _read_ledger(ledger_path)
    next(rows)
    yield from rows
    if sha256_file(ledger_path) != before:
        message = "MC ledger changed during verified frequency processing"
        raise MCRunError(message)


def replay_mc_event(
    project_path: Path,
    request_path: Path,
    ledger_path: Path,
    sample_id: str,
    output_prefix: Path,
    *,
    selection: EngineSelection | None = None,
    wheel_artifact: Path | None = None,
) -> ProjectBatchReport:
    """Replay an actual retained effective event with the original selected engine."""
    _, request_hash = validate_effective_request(request_path)
    loaded = load_project(project_path)
    _project_subset(loaded)
    selected = loaded.project.engine if selection is None else selection
    expected = _header(
        loaded, request_hash, selection=selected, wheel_artifact=wheel_artifact, request_path=request_path
    )
    _existing_prefix(ledger_path, expected, request_path)
    match: EffectiveMCEvent | None = None
    for item in iter_effective_events(request_path):
        if item.sample_id == sample_id:
            match = item
            break
    if match is None:
        message = f"Sample {sample_id!r} absent from explicit request"
        raise MCRunError(message)
    rows = _read_ledger(ledger_path)
    next(rows)
    recorded = next((row for row in rows if row["sample_id"] == sample_id), None)
    if recorded is None or recorded["status"] != _STATUS_OK:
        message = "Representative-event replay requires a successfully checkpointed actual sample"
        raise MCRunError(message)
    _fixed_parameters(match, loaded)
    report = run_project_events(
        project_path,
        (match.event,),
        selection=selected,
        wheel_artifact=wheel_artifact,
        _loaded_project=loaded,
    )
    outcome = report.outcomes[0]
    replayed = _event_row(match, outcome)
    for key in ("effective_event_sha256", "effective_model_sha256", "status", "sites"):
        if replayed[key] != recorded[key]:
            message = f"MC representative replay diverged from checkpoint: {key}"
            raise MCRunError(message)
    write_batch_results(output_prefix, report)
    return report


def _check_extended_plan(old: MCRequestHeader, new: MCRequestHeader) -> None:
    """Only an explicitly linked immutable B extension can reuse old computations."""
    if (
        old.sample_population_id is None
        or old.sample_population_id != new.sample_population_id
        or new.parent_plan_sha256 != old.plan_sha256
        or old.plan_sha256 == new.plan_sha256
        or old.policy_id != new.policy_id
        or old.preparation_model_sha256 != new.preparation_model_sha256
        or old.source_files != new.source_files
        or old.populations != new.populations
        or not old.strata
        or not new.strata
    ):
        message = "Plan extension requires an identical source/policy/population and explicit parent revision"
        raise MCRunError(message)
    prior = {(s.scenario_id, s.duration_min, s.stratum_id): s for s in old.strata}
    current = {(s.scenario_id, s.duration_min, s.stratum_id): s for s in new.strata}
    if prior.keys() != current.keys():
        message = "Extended plan changed its original rainfall strata"
        raise MCRunError(message)
    if any(
        current[key].probability_mass != row.probability_mass or current[key].planned_samples < row.planned_samples
        for key, row in prior.items()
    ) or not any(current[key].planned_samples > row.planned_samples for key, row in prior.items()):
        message = "Plan extension must increase allocations while preserving each stratum probability mass"
        raise MCRunError(message)


def _index_prior_results(db: sqlite3.Connection, request: Path, ledger: Path) -> None:
    """Index only small scalar records on temporary disk, not in-process hydrographs."""
    db.execute(
        "CREATE TABLE cached (sample_id TEXT PRIMARY KEY, input_id TEXT NOT NULL,"
        " outcome_json TEXT NOT NULL, seen INTEGER NOT NULL DEFAULT 0)"
    )
    samples = iter_effective_events(request)
    records = _read_ledger(ledger)
    next(records)
    for result in records:
        sample = next(samples, None)
        if sample is None or result["sample_id"] != sample.sample_id:
            message = "Prior result/sample identity changed after validating the original ledger"
            raise MCRunError(message)
        db.execute(
            "INSERT INTO cached (sample_id, input_id, outcome_json) VALUES (?, ?, ?)",
            (
                sample.sample_id,
                sample.computation_digest(),
                json.dumps(result, sort_keys=True, separators=(",", ":"), allow_nan=False),
            ),
        )
    db.commit()


def _verify_reusable_samples(db: sqlite3.Connection, request: Path) -> None:
    """Reject any changed earlier effective rainfall, loss, TP or source inputs."""
    for sample in iter_effective_events(request):
        old = db.execute("SELECT input_id FROM cached WHERE sample_id = ?", (sample.sample_id,)).fetchone()
        if old is None:
            continue
        if old[0] != sample.computation_digest():
            message = "Previously computed sample differs in the extended plan's effective inputs"
            raise MCRunError(message)
        db.execute("UPDATE cached SET seen = 1 WHERE sample_id = ?", (sample.sample_id,))
    result = db.execute("SELECT COUNT(*) FROM cached WHERE seen = 0").fetchone()
    if result is None or result[0] != 0:
        message = "New plan omits a previously computed logical sample"
        raise MCRunError(message)


def _uncached_events(db: sqlite3.Connection, request: Path) -> Iterator[ProjectEvent]:
    for sample in iter_effective_events(request):
        if db.execute("SELECT 1 FROM cached WHERE sample_id = ?", (sample.sample_id,)).fetchone() is None:
            yield sample.event


def _reweight_cached_record(raw_json: str, new: EffectiveMCEvent) -> dict[str, object]:
    """Carry identical computations forward but discard all prior-plan weight and checksum fields."""
    parsed: object = json.loads(raw_json)
    if not isinstance(parsed, dict):
        message = "Stored prior scalar record is not a JSON object"
        raise MCRunError(message)
    result = cast("dict[str, object]", parsed)
    result.pop("previous_record_sha256", None)
    result.pop("record_sha256", None)
    result["probability_weight"] = str(new.probability_weight)
    result["effective_event_sha256"] = new.digest()
    return result


def extend_mc_execution(
    project_path: Path,
    old_request_path: Path,
    old_ledger_path: Path,
    new_request_path: Path,
    new_ledger_path: Path,
    *,
    selection: EngineSelection | None = None,
    wheel_artifact: Path | None = None,
) -> MCRunSummary:
    """Reuse an exact unchanged B sample under an explicit extended plan revision.

    Prior scalar peaks are disk-indexed; all event weights are recalculated
    under the new allocation. Never modify or reinterpret the old ledger.
    """
    old_plan, old_digest = validate_effective_request(old_request_path)
    new_plan, new_digest = validate_effective_request(new_request_path)
    _check_extended_plan(old_plan, new_plan)
    if new_ledger_path.exists() or new_ledger_path.is_symlink():
        message = "The extended checkpoint destination already exists"
        raise MCRunError(message)
    loaded = load_project(project_path)
    _project_subset(loaded)
    selected = loaded.project.engine if selection is None else selection
    old_header = _header(
        loaded, old_digest, selection=selected, wheel_artifact=wheel_artifact, request_path=old_request_path
    )
    new_header = _header(
        loaded, new_digest, selection=selected, wheel_artifact=wheel_artifact, request_path=new_request_path
    )
    _existing_prefix(old_ledger_path, old_header, old_request_path)
    old_ledger_hash = sha256_file(old_ledger_path)
    with (
        tempfile.TemporaryDirectory(prefix="mc149-extend-") as folder,
        closing(sqlite3.connect(Path(folder) / "reused-results.sqlite3")) as db,
    ):
        _index_prior_results(db, old_request_path, old_ledger_path)
        _verify_reusable_samples(db, new_request_path)
        for event in iter_effective_events(new_request_path):
            _fixed_parameters(event, loaded)
        previous = _new_ledger(new_ledger_path, new_header)
        outcomes = iter_project_events(
            project_path,
            _uncached_events(db, new_request_path),
            selection=selected,
            wheel_artifact=wheel_artifact,
            _loaded_project=loaded,
        )
        for event in iter_effective_events(new_request_path):
            matched = db.execute("SELECT outcome_json FROM cached WHERE sample_id = ?", (event.sample_id,)).fetchone()
            if matched is None:
                routed = next(outcomes)
                if routed.event_id != event.event.event_id:
                    message = "New event runner output is not the selected effective sample"
                    raise MCRunError(message)
                row = _event_row(event, routed)
            else:
                row = _reweight_cached_record(cast("str", matched[0]), event)
            previous = _append_ledger(new_ledger_path, row, previous)
    if (
        sha256_file(old_ledger_path) != old_ledger_hash
        or sha256_file(old_request_path) != old_digest
        or sha256_file(new_request_path) != new_digest
    ):
        message = "Original/extended source or ledger changed during plan extension"
        raise MCRunError(message)
    return summarise_ledger(new_ledger_path, new_request_path, new_header)


def _preparation_cli_action(options: argparse.Namespace) -> int | None:
    """Text-mode B plan and E materialisation use exactly one sampler and source profile."""
    if options.command == "plan":
        paths = create_saved_sample_plan(options.spec, options.output_prefix)
        print(f"Created immutable B sample-plan files: {paths[0]}, {paths[1]}")
        return 0
    if options.command == "prepare":
        header = prepare_saved_sample_plan(
            options.project,
            options.plan,
            options.samples,
            options.request,
            ifd_path=options.ifd,
            patterns_path=options.patterns,
            arf_region=options.arf_region,
            dry_tail_min=options.dry_tail_min,
            loss_source_path=options.loss_source,
        )
        print(f"Prepared {header.event_count} exact B samples without new randomness: {options.request}")
        return 0
    if options.command == "extend":
        if options.numerical_profile is not None and options.engine is None:
            message = "--numerical-profile requires --engine"
            raise MCRunError(message)
        selected = (
            EngineSelection.for_engine(options.engine, options.numerical_profile)
            if options.engine is not None
            else None
        )
        result = extend_mc_execution(
            options.project,
            options.old_request,
            options.old_ledger,
            options.new_request,
            options.new_ledger,
            selection=selected,
            wheel_artifact=options.wheel_artifact,
        )
        print(result.to_text(), end="")
        return 0 if result.complete else 2
    if options.command == "validate":
        header, digest = validate_effective_request(options.request)
        print(f"Valid effective request: {header.event_count} samples; SHA-256 {digest}")
        return 0
    return None


def main(argv: list[str] | None = None) -> int:
    """Explicit-event MC CLI: validate, stream, resume, inspect and deterministic replay."""
    parser = argparse.ArgumentParser(prog="python -m runoff_routing.monte_carlo_execution")
    commands = parser.add_subparsers(dest="command", required=True)
    create = commands.add_parser("plan", help="create B's immutable sample plan from a JSON spec")
    create.add_argument("spec", type=Path)
    create.add_argument("output_prefix", type=Path)
    prepare = commands.add_parser("prepare", help="materialise stored #146 draws into ready #119 events")
    prepare.add_argument("project", type=Path)
    prepare.add_argument("plan", type=Path)
    prepare.add_argument("samples", type=Path)
    prepare.add_argument("request", type=Path)
    prepare.add_argument("--ifd", type=Path, required=True)
    prepare.add_argument("--patterns", type=Path, required=True)
    prepare.add_argument("--arf-region", required=True)
    prepare.add_argument("--dry-tail-min", type=int, default=0)
    prepare.add_argument("--loss-source", type=Path)
    validate = commands.add_parser("validate", help="verify all effective events and original source hashes")
    validate.add_argument("request", type=Path)
    run = commands.add_parser("run", help="run or resume an exact effective request")
    run.add_argument("project", type=Path)
    run.add_argument("request", type=Path)
    run.add_argument("ledger", type=Path)
    run.add_argument("--resume", action="store_true")
    replay = commands.add_parser("replay", help="re-execute one checkpointed representative event")
    replay.add_argument("project", type=Path)
    replay.add_argument("request", type=Path)
    replay.add_argument("ledger", type=Path)
    replay.add_argument("sample_id")
    replay.add_argument("output_prefix", type=Path)
    extension = commands.add_parser("extend", help="reuse unchanged event computations under a new B plan revision")
    extension.add_argument("project", type=Path)
    extension.add_argument("old_request", type=Path)
    extension.add_argument("old_ledger", type=Path)
    extension.add_argument("new_request", type=Path)
    extension.add_argument("new_ledger", type=Path)
    frequency = commands.add_parser("frequency", help="delegate exact weighted curves to #147")
    frequency.add_argument("project", type=Path)
    frequency.add_argument("request", type=Path)
    frequency.add_argument("ledger", type=Path)
    frequency.add_argument("output_prefix", type=Path)
    frequency.add_argument("--aep", type=float, required=True, action="append")
    frequency.add_argument("--confidence-level", type=float, default=0.95)
    frequency.add_argument("--relative-aep-screen", type=float, default=0.2)
    inspect = commands.add_parser("inspect", help="report checkpoint completeness without a frequency estimate")
    inspect.add_argument("project", type=Path)
    inspect.add_argument("request", type=Path)
    inspect.add_argument("ledger", type=Path)
    inspect.add_argument("--expected-ledger-sha256", help="independently stored ledger file SHA-256")
    for sub in (run, replay, inspect, frequency, extension):
        sub.add_argument("--engine", choices=("python", "python-cmd", "rorb-cmd"))
        sub.add_argument("--numerical-profile")
        sub.add_argument("--wheel-artifact", type=Path)
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return exc.code if isinstance(exc.code, int) else 2
    try:
        early = _preparation_cli_action(args)
        if early is not None:
            return early
        if args.numerical_profile is not None and args.engine is None:
            message = "--numerical-profile requires --engine"
            raise MCRunError(message)
        selected = EngineSelection.for_engine(args.engine, args.numerical_profile) if args.engine is not None else None
        if args.command == "run":
            report = execute_mc_request(
                args.project,
                args.request,
                args.ledger,
                resume=args.resume,
                selection=selected,
                wheel_artifact=args.wheel_artifact,
            )
            print(report.to_text(), end="")
            return 0 if report.complete else 2
        if args.command == "frequency":
            result = write_mc_frequency(
                args.project,
                args.request,
                args.ledger,
                args.output_prefix,
                target_aeps=tuple(args.aep),
                selection=selected,
                wheel_artifact=args.wheel_artifact,
                read_rows=iter_verified_mc_results,
                confidence_level=args.confidence_level,
                relative_aep_screen=args.relative_aep_screen,
            )
            print(f"Weighted frequency: {result.scopes} physical populations; complete={result.point_results_complete}")
            return 0 if result.point_results_complete else 2
        if args.command == "replay":
            report = replay_mc_event(
                args.project,
                args.request,
                args.ledger,
                args.sample_id,
                args.output_prefix,
                selection=selected,
                wheel_artifact=args.wheel_artifact,
            )
            print(report.to_text(), end="")
            return 0 if report.succeeded else 2
        _, digest = validate_effective_request(args.request)
        loaded = load_project(args.project)
        _project_subset(loaded)
        selected = loaded.project.engine if selected is None else selected
        expected = _header(
            loaded, digest, selection=selected, wheel_artifact=args.wheel_artifact, request_path=args.request
        )
        result = summarise_ledger(
            args.ledger, args.request, expected, expected_ledger_sha256=args.expected_ledger_sha256
        )
        print(result.to_text(), end="")
    except (OSError, ValueError, TypeError, ArithmeticError) as exc:
        print(f"MC execution failed: {exc}", file=sys.stderr)
        return 2
    else:
        return 0 if result.complete else 2


if __name__ == "__main__":
    raise SystemExit(main())
