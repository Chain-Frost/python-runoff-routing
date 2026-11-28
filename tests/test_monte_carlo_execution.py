"""#149: stream/checkpoint/replay explicit MC samples without drawing or new solvers."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import time
import tracemalloc
from dataclasses import replace
from decimal import ROUND_DOWN, ROUND_HALF_EVEN, ROUND_UP, Decimal, Inexact, localcontext
from fractions import Fraction
from pathlib import Path
from typing import cast

import pytest

from runoff_routing.arr_patterns import PatternSet, parse_pattern_csv, read_pattern_file
from runoff_routing.engine_types import EngineSelection
from runoff_routing.monte_carlo_effective import (
    EffectiveMCEvent,
    MCAllocation,
    MCInputError,
    MCPopulation,
    MCRequestHeader,
    encode_jsonl_line,
    is_contained_mc_source,
    materialise_arr_sample,
    preparation_model_sha256,
    read_header,
    validate_effective_request,
    write_effective_request,
)
from runoff_routing.monte_carlo_execution import (
    MCRunError,
    execute_mc_request,
    main,
    replay_mc_event,
    summarise_ledger,
)
from runoff_routing.project_batch import ProjectEvent, run_project_events
from runoff_routing.project_json import EmbeddedRun, Project, SourceFile, write_project
from runoff_routing.rorb_model import RunModel, from_json

ROOT = Path(__file__).parents[1]
EXAMPLES = ROOT / "examples"
SOURCE_PATTERNS = EXAMPLES / "arr-design-synthetic-patterns.csv"
MODEL = EXAMPLES / "synthetic-run.json"
CMD = EngineSelection.for_engine("python-cmd")


def _source_model() -> RunModel:
    model = from_json(MODEL.read_text(encoding="utf-8"))
    assert isinstance(model, RunModel)
    return model


def _input(
    directory: Path,
    *,
    count: int = 2,
    bad: bool = False,
    extension: bool = False,
    b_ids: bool = False,
) -> tuple[Path, Path, list[EffectiveMCEvent]]:
    model = _source_model()
    project = directory / "project.json"
    write_project(project, Project("mc_synthetic", "explicit", EmbeddedRun(model), engine=CMD))
    source = directory / "patterns.csv"
    source.write_bytes(SOURCE_PATTERNS.read_bytes())
    patterns = read_pattern_file(source, kind="point")
    events: list[EffectiveMCEvent] = []
    for index in range(count):
        item = materialise_arr_sample(
            model=model,
            pattern_set=patterns,
            pattern_source_order=1 + index % 2,
            sample_id=f"mc:0123456789abcdef:h1:{index:08d}" if b_ids else f"sample-{index + 1}",
            scenario_id="base",
            stratum_id="h1",
            stratum_mass=Decimal(1),
            stratum_size=count,
            rainfall_aep_percent=Decimal(2),
            gross_depth_mm=Decimal(20 + index),
            bom_source_sha256=hashlib.sha256(b"synthetic_B_sampled_IFD").hexdigest(),
            arf_region="South-West Western Australia",
            storm_initial_loss_mm=Decimal(6),
            preburst_depth_mm=Decimal(1),
            preburst_policy="subtract_reject",
            dry_tail_min=120,
        )
        events.append(item)
    if bad:
        record = events[0]
        assert record.event.storm is not None
        assert record.event.losses is not None
        events[0] = replace(
            record,
            event=ProjectEvent(
                record.sample_id,
                storm={**record.event.storm, "start_increment": 100},
                losses=record.event.losses,
            ),
        )
    header = MCRequestHeader(
        plan_sha256=hashlib.sha256(b"extended" if extension else b"initial").hexdigest(),
        policy_id="monte-carlo-statistics/1" if b_ids else "authored_control_v1",
        source_files=(SourceFile("patterns.csv", hashlib.sha256(source.read_bytes()).hexdigest()),),
        populations=(MCPopulation("base", 60, Decimal(1)),),
        event_count=count,
        preparation_model_sha256=preparation_model_sha256(model),
    )
    request = directory / "effective.jsonl"
    write_effective_request(request, header, events)
    return project, request, events


def _rows(ledger: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in ledger.read_text(encoding="utf-8").splitlines()]


def test_header_rejects_undeclared_zero_count_population_allocation() -> None:
    valid = MCRequestHeader(
        plan_sha256=hashlib.sha256(b"allocation-scope").hexdigest(),
        policy_id="authored_control_v1",
        source_files=(),
        populations=(MCPopulation("base", 60, Decimal("0.75")),),
        event_count=2,
        preparation_model_sha256=hashlib.sha256(b"model").hexdigest(),
        strata=(
            MCAllocation("base", 60, "h1", Decimal("0.5"), 2),
            MCAllocation("base", 60, "h2", Decimal("0.25"), 0),
        ),
    )
    assert valid.strata[1].planned_samples == 0

    with pytest.raises(MCInputError, match="undeclared scenario/duration"):
        replace(
            valid,
            strata=(
                MCAllocation("base", 60, "h1", Decimal("0.5"), 2),
                MCAllocation("other", 60, "h2", Decimal("0.25"), 0),
            ),
        )


def test_effective_request_rejects_symlinked_parent_source_escape(tmp_path: Path) -> None:
    inside = tmp_path / "inside"
    inside.mkdir()
    _, request, events = _input(inside, count=1)
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "patterns.csv").write_bytes((inside / "patterns.csv").read_bytes())
    alias = inside / "alias"
    try:
        alias.symlink_to(outside, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("Directory symlink creation unavailable on this filesystem")

    assert not is_contained_mc_source(alias / "patterns.csv", inside)
    original_header = read_header(request)
    new_source = SourceFile("alias/patterns.csv", hashlib.sha256((outside / "patterns.csv").read_bytes()).hexdigest())
    forged_header = replace(original_header, source_files=(new_source,))
    attempted = inside / "forged.jsonl"
    with pytest.raises(MCInputError, match="outside request directory"):
        write_effective_request(attempted, forged_header, events)
    assert not attempted.exists()

    original = request.read_bytes().splitlines(keepends=True)
    request.write_bytes(encode_jsonl_line(forged_header.to_dict()) + b"".join(original[1:]))
    with pytest.raises(MCInputError, match="outside request directory"):
        validate_effective_request(request)


def test_areal_mc_pattern_must_match_arr2019_size_bin() -> None:
    model = _source_model()
    original = model.catchment.subareas
    initial_area = sum((item.area_km2 for item in original), Decimal(0))
    first = replace(original[0], area_km2=original[0].area_km2 + Decimal(1000) - initial_area)
    model = replace(model, catchment=replace(model.catchment, subareas=(first, *original[1:])))

    def areal_source(bin_label: str, aep_band: str = "rare") -> PatternSet:
        header = "EventID,Duration,TimeStep,Region,Area,AEP,Increments"
        row = f"A1,60,30,SyntheticPoint,{bin_label},{aep_band},10,90"
        contents = f"{header}\n{row}\n"
        return parse_pattern_csv(contents.encode("utf-8"), kind="areal")

    def materialise(patterns: PatternSet) -> EffectiveMCEvent:
        return materialise_arr_sample(
            model=model,
            pattern_set=patterns,
            pattern_source_order=1,
            tp_bin_id="rare",
            sample_id="areal-review",
            scenario_id="base",
            stratum_id="h1",
            stratum_mass=Decimal(1),
            stratum_size=1,
            rainfall_aep_percent=Decimal(2),
            gross_depth_mm=Decimal(20),
            bom_source_sha256=hashlib.sha256(b"synthetic_bom").hexdigest(),
            arf_region="South-West Western Australia",
            storm_initial_loss_mm=Decimal(1),
            preburst_depth_mm=Decimal(0),
            preburst_policy="none",
            dry_tail_min=60,
        )

    with pytest.raises(MCInputError, match="areal temporal-pattern area bin"):
        materialise(areal_source("100"))
    accepted = materialise(areal_source("1000"))
    assert accepted.tp_area_bin == "1000"
    assert accepted.tp_aep_band == "rare"
    with pytest.raises(MCInputError, match="source AEP category"):
        materialise(areal_source("1000", "frequent"))


def test_materialise_once_and_replay_matches_existing_event_runner(tmp_path: Path) -> None:
    project, request, events = _input(tmp_path)
    _, digest = validate_effective_request(request)
    assert len(digest) == 64
    sample = events[0]
    assert sample.event.storm is not None
    assert sample.event.losses is not None
    with localcontext() as ctx:
        ctx.prec = 28
        expected_areal_depth = sum(
            (
                sample.gross_depth_mm * Decimal(value) / 100 * sample.arf_factor
                for value in cast("list[str]", sample.event.storm["percentages"])
            ),
            Decimal(0),
        )
    assert sample.event.storm["depths_mm"] == [str(expected_areal_depth)]
    assert sample.event.losses["initial_loss_mm"] == "5"
    direct = run_project_events(project, (sample.event,), selection=CMD).outcomes[0]
    ledger = tmp_path / "ledger.jsonl"
    report = execute_mc_request(project, request, ledger)
    assert report.complete
    site_records = cast("list[dict[str, object]]", _rows(ledger)[1]["sites"])
    assert site_records[0]["peak_m3_s"] == max(direct.hydrographs[0].discharge_m3_s)
    assert _rows(ledger)[1]["tp_source_kind"] == "point"
    assert _rows(ledger)[1]["tp_aep_band"] == "rare"
    assert _rows(ledger)[1]["original_tp_id"] == "0001"
    prefix = tmp_path / "selected"
    replayed = replay_mc_event(project, request, ledger, sample.sample_id, prefix, selection=CMD)
    assert replayed.outcomes[0].model_sha256 == direct.model_sha256
    assert replayed.outcomes[0].hydrographs == direct.hydrographs
    assert replayed.outcomes[0].physical_time_hours == direct.physical_time_hours
    assert (tmp_path / "selected.json").is_file()
    assert (tmp_path / "selected.csv").is_file()
    assert (tmp_path / "selected.txt").is_file()


def test_effective_materialisation_is_independent_of_decimal_context(tmp_path: Path) -> None:
    model = _source_model()
    source = tmp_path / "patterns.csv"
    source.write_bytes(SOURCE_PATTERNS.read_bytes())
    patterns = read_pattern_file(source, kind="point")
    requests: list[dict[str, object]] = []
    # Include directed rounding and traps: setting prec alone is insufficient.
    scenarios = (
        (12, ROUND_HALF_EVEN, False),
        (28, ROUND_DOWN, False),
        (80, ROUND_UP, False),
        (12, ROUND_DOWN, True),
        (80, ROUND_UP, True),
    )
    for precision, rounding, trap_inexact in scenarios:
        with localcontext() as ctx:
            ctx.prec = precision
            ctx.rounding = rounding
            ctx.traps[Inexact] = trap_inexact
            event = materialise_arr_sample(
                model=model,
                pattern_set=patterns,
                pattern_source_order=1,
                sample_id="sample-context",
                scenario_id="base",
                stratum_id="h1",
                stratum_mass=Decimal("0.123456789012345678901234567890"),
                stratum_size=3,
                rainfall_aep_percent=Decimal("2.12345678901234567890123456789"),
                gross_depth_mm=Decimal("20.12345678901234567890123456789012345"),
                bom_source_sha256=hashlib.sha256(b"synthetic_B_sampled_IFD").hexdigest(),
                arf_region="South-West Western Australia",
                storm_initial_loss_mm=Decimal("6.12345678901234567890"),
                preburst_depth_mm=Decimal("1.11111111111111111111"),
                preburst_policy="subtract_reject",
                dry_tail_min=120,
            )
            requests.append(event.to_dict())
    assert all(request == requests[0] for request in requests[1:])


def test_saved_effective_request_validation_is_independent_of_rounding_and_traps(tmp_path: Path) -> None:
    _project, request, _events = _input(tmp_path, count=3, b_ids=True)
    expected, digest = validate_effective_request(request)
    for rounding in (ROUND_DOWN, ROUND_UP):
        with localcontext() as ctx:
            ctx.prec = 12
            ctx.rounding = rounding
            ctx.traps[Inexact] = True
            checked, current_digest = validate_effective_request(request)
        assert checked == expected
        assert current_digest == digest


def test_probability_mass_accounting_ignores_callers_decimal_context() -> None:
    with localcontext() as ctx:
        ctx.prec = 8
        ctx.rounding = ROUND_UP
        ctx.traps[Inexact] = True
        with pytest.raises(MCInputError, match="probability mass must equal one"):
            MCPopulation("base", 60, Decimal("0.5"), Decimal("0.25"), Decimal("0.250000000000000000000000000001"))
        header = MCRequestHeader(
            plan_sha256=hashlib.sha256(b"high-precision-plan").hexdigest(),
            policy_id="authored_control_v1",
            source_files=(),
            populations=(MCPopulation("base", 60, Decimal("0.123456789012345678901234567890")),),
            event_count=2,
            preparation_model_sha256=hashlib.sha256(b"analytic-only-model").hexdigest(),
            strata=(
                MCAllocation("base", 60, "h1", Decimal("0.061728394506172839450617283945"), 1),
                MCAllocation("base", 60, "h2", Decimal("0.061728394506172839450617283945"), 1),
            ),
        )
        assert header.event_count == 2


def test_b_plan_colon_sample_id_is_preserved_and_engine_id_is_stable(tmp_path: Path) -> None:
    project, request, events = _input(tmp_path, b_ids=True)
    sample = events[0]
    assert sample.sample_id.startswith("mc:")
    assert sample.event.event_id == "mc-" + hashlib.sha256(sample.sample_id.encode("utf-8")).hexdigest()
    assert sample.event.event_id != sample.sample_id
    ledger = tmp_path / "b-ledger.jsonl"
    summary = execute_mc_request(project, request, ledger)
    assert summary.complete
    rows = _rows(ledger)
    assert rows[0]["policy_id"] == "monte-carlo-statistics/1"
    assert rows[1]["sample_id"] == sample.sample_id
    assert rows[1]["event_id"] == sample.event.event_id
    replay = replay_mc_event(project, request, ledger, sample.sample_id, tmp_path / "b-replay")
    assert replay.outcomes[0].event_id == sample.event.event_id


def test_resume_exact_prefix_without_rerouting_or_weight_change(tmp_path: Path) -> None:
    project, request, _ = _input(tmp_path, count=3)
    ledger = tmp_path / "ledger.jsonl"
    original = execute_mc_request(project, request, ledger)
    assert original.complete
    original_lines = ledger.read_bytes().splitlines(keepends=True)
    ledger.write_bytes(b"".join(original_lines[:2]))
    resumed = execute_mc_request(project, request, ledger, resume=True)
    assert resumed.complete
    assert ledger.read_bytes() == b"".join(original_lines)
    with pytest.raises(MCRunError, match="already exists"):
        execute_mc_request(project, request, ledger)
    assert summarise_ledger(ledger, request, _rows(ledger)[0]).complete


def test_changed_request_or_engine_rejected_even_with_same_sample_id(tmp_path: Path) -> None:
    project, request, _ = _input(tmp_path)
    ledger = tmp_path / "ledger.jsonl"
    assert execute_mc_request(project, request, ledger).complete
    data = request.read_bytes()
    request.write_bytes(data.replace(b'"policy_id":"authored_control_v1"', b'"policy_id":"modified_control_v1"'))
    with pytest.raises(MCRunError, match="different plan/policy/source/engine/code"):
        execute_mc_request(project, request, ledger, resume=True)
    request.write_bytes(data)
    with pytest.raises(MCRunError, match="only explicitly selected python-cmd"):
        execute_mc_request(project, request, tmp_path / "python.jsonl", selection=EngineSelection.for_engine("python"))
    assert not (tmp_path / "python.jsonl").exists()


def test_positive_weight_failure_never_disappears_or_becomes_zero(tmp_path: Path) -> None:
    project, request, events = _input(tmp_path, bad=True)
    ledger = tmp_path / "failures.jsonl"
    summary = execute_mc_request(project, request, ledger)
    assert not summary.complete
    rows = _rows(ledger)
    assert len(rows) == 3
    assert rows[1]["sample_id"] == events[0].sample_id
    assert rows[1]["probability_weight"] == "0.5"
    assert rows[1]["status"] != "computed_unvalidated"
    assert rows[1]["sites"] == []
    assert rows[2]["status"] == "computed_unvalidated"
    assert main(["inspect", str(project), str(request), str(ledger)]) == 2
    with pytest.raises(MCRunError, match="successfully checkpointed"):
        replay_mc_event(project, request, ledger, events[0].sample_id, tmp_path / "invalid")


def test_duplicate_samples_missing_strata_and_double_transform_rejected(tmp_path: Path) -> None:
    project, request, events = _input(tmp_path)
    del project
    raw = request.read_bytes()
    assert events[0].event.storm is not None
    assert events[0].event.losses is not None
    modified = ProjectEvent(
        events[0].sample_id,
        storm={**events[0].event.storm, "depths_mm": [str(events[0].gross_depth_mm)]},
        losses=events[0].event.losses,
    )
    with pytest.raises(MCInputError, match="ARF exactly once"):
        replace(events[0], event=modified)
    parts = raw.splitlines(keepends=True)
    request.write_bytes(parts[0] + parts[1] + parts[1])
    with pytest.raises(MCInputError, match="Duplicate sample"):
        validate_effective_request(request)
    request.write_bytes(parts[0] + parts[1])
    with pytest.raises(MCInputError, match="event count differs"):
        validate_effective_request(request)


def test_adopted_v1_does_not_silently_accept_experimental_preburst_clamp(tmp_path: Path) -> None:
    _, request, events = _input(tmp_path, count=1, b_ids=True)
    header = read_header(request)
    experimental = replace(events[0], loss_policy="subtract_clamp")
    output = tmp_path / "unreviewed-clamp.jsonl"
    with pytest.raises(MCInputError, match="Experimental preburst clamp"):
        write_effective_request(output, header, (experimental,))
    assert not output.exists()


def test_truncated_checkpoint_rejected_and_unfinished_not_complete(tmp_path: Path) -> None:
    project, request, _ = _input(tmp_path)
    ledger = tmp_path / "ledger.jsonl"
    assert execute_mc_request(project, request, ledger).complete
    parts = ledger.read_bytes().splitlines(keepends=True)
    ledger.write_bytes(parts[0] + parts[1])
    assert not summarise_ledger(ledger, request, _rows(ledger)[0]).complete
    ledger.write_bytes(parts[0] + parts[1] + parts[2][:-1])
    with pytest.raises(MCInputError, match="end with newline"):
        execute_mc_request(project, request, ledger, resume=True)


def test_ledger_numerical_corruption_fails_hash_chain_and_external_receipt(tmp_path: Path) -> None:
    project, request, events = _input(tmp_path)
    ledger = tmp_path / "tamper.jsonl"
    receipt = execute_mc_request(project, request, ledger)
    assert receipt.complete
    assert receipt.ledger_sha256 == hashlib.sha256(ledger.read_bytes()).hexdigest()
    assert summarise_ledger(ledger, request, _rows(ledger)[0], expected_ledger_sha256=receipt.ledger_sha256).complete

    rows = _rows(ledger)
    sites = cast("list[dict[str, object]]", rows[1]["sites"])
    sites[0]["peak_m3_s"] = 999999.0
    ledger.write_text(
        "".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in rows),
        encoding="utf-8",
    )
    with pytest.raises(MCRunError, match="checksum/chain mismatch"):
        execute_mc_request(project, request, ledger, resume=True)
    with pytest.raises(MCRunError, match="checksum/chain mismatch"):
        replay_mc_event(project, request, ledger, events[0].sample_id, tmp_path / "no-false-replay")
    assert not (tmp_path / "no-false-replay.json").exists()

    # A checksum chain is not a signature; a separately pinned complete-file
    # SHA-256 still detects a malicious rehash of the modified numerical row.
    previous = hashlib.sha256(
        (json.dumps(rows[0], sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    ).hexdigest()
    for row in rows[1:]:
        row["previous_record_sha256"] = previous
        row.pop("record_sha256")
        previous = hashlib.sha256(
            (json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
        ).hexdigest()
        row["record_sha256"] = previous
    ledger.write_text(
        "".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in rows),
        encoding="utf-8",
    )
    with pytest.raises(MCRunError, match="independently pinned"):
        summarise_ledger(ledger, request, _rows(ledger)[0], expected_ledger_sha256=receipt.ledger_sha256)


def test_zero_rainfall_is_valid_zero_peak_not_missing(tmp_path: Path) -> None:
    project, _request, events = _input(tmp_path)
    rainless = events[0]
    assert rainless.event.storm is not None
    assert rainless.event.losses is not None
    zero = replace(
        rainless,
        gross_depth_mm=Decimal(0),
        event=ProjectEvent(
            rainless.event.event_id,
            storm={**rainless.event.storm, "depths_mm": ["0"]},
            losses=rainless.event.losses,
        ),
    )
    header = MCRequestHeader(
        plan_sha256=hashlib.sha256(b"zero").hexdigest(),
        policy_id="authored_control_v1",
        source_files=(
            SourceFile("patterns.csv", hashlib.sha256((tmp_path / "patterns.csv").read_bytes()).hexdigest()),
        ),
        populations=(MCPopulation("base", 60, Decimal(1)),),
        event_count=1,
        preparation_model_sha256=preparation_model_sha256(_source_model()),
    )
    zero_request = tmp_path / "zero-effective.jsonl"
    # Preserve complete allocation after removing the second sample.
    zero = replace(zero, stratum_size=1, probability_weight=Decimal(1))
    write_effective_request(zero_request, header, (zero,))
    ledger = tmp_path / "zero-ledger.jsonl"
    summary = execute_mc_request(project, zero_request, ledger)
    assert summary.complete
    assert summary.zero_peak_events == 1
    sites = cast("list[dict[str, object]]", _rows(ledger)[1]["sites"])
    assert sites[0]["peak_m3_s"] == 0


def test_engine_selection_and_simple_cli(tmp_path: Path) -> None:
    project, request, _ = _input(tmp_path, count=1)
    ledger = tmp_path / "cli.jsonl"
    assert main(["validate", str(request)]) == 0
    assert main(["run", str(project), str(request), str(ledger), "--engine", "python-cmd"]) == 0
    assert main(["run", str(project), str(request), str(ledger)]) == 2
    assert main(["run", str(project), str(request), str(ledger), "--resume"]) == 0
    assert main(["replay", str(project), str(request), str(ledger), "sample-1", str(tmp_path / "cli-replay")]) == 0


def test_bounded_64_event_streaming_memory_receipt(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    project, request, _events = _input(tmp_path, count=64)
    ledger = tmp_path / "bounded-ledger.jsonl"
    tracemalloc.start()
    started = time.perf_counter()
    try:
        outcome = execute_mc_request(project, request, ledger)
        elapsed = time.perf_counter() - started
        _current, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    with capsys.disabled():
        print(
            f"MC149 bounded 64-event receipt: elapsed_s={elapsed:.6f}, "
            f"python_traced_peak_bytes={peak}, ledger_bytes={ledger.stat().st_size}",
            flush=True,
        )
    assert outcome.complete
    assert len(_rows(ledger)) == 65
    assert peak < 64 * 1024 * 1024
    assert ledger.stat().st_size < 512 * 1024


def test_conditional_research_uses_verified_ledger(tmp_path: Path) -> None:
    """Use two authored deterministic events, not the stochastic sampler or a physical model."""
    project, template, events = _input(tmp_path)
    request = tmp_path / "conditional-request.jsonl"
    header = replace(
        read_header(template),
        policy_id="monte-carlo-statistics/1",
        populations=(MCPopulation("base", 60, Decimal("0.49"), Decimal("0.01"), Decimal("0.50")),),
        strata=(MCAllocation("base", 60, "h1", Decimal("0.49"), 2),),
    )
    write_effective_request(
        request,
        header,
        (replace(event, stratum_mass=Decimal("0.49"), probability_weight=Decimal("0.245")) for event in events),
    )
    ledger = tmp_path / "conditional-ledger.jsonl"
    assert execute_mc_request(project, request, ledger).complete
    spec = importlib.util.spec_from_file_location(
        "mc_conditional_research", ROOT / "repo-scripts" / "mc_conditional_research.py"
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    records = _rows(ledger)[1:]
    first = cast("list[dict[str, object]]", records[0]["sites"])[0]
    site_id = cast("str", first["print_id"])
    peaks = [
        Fraction(cast("int | float", cast("list[dict[str, object]]", row["sites"])[0]["peak_m3_s"])) for row in records
    ]
    project_pin = module.Artifact(project, hashlib.sha256(project.read_bytes()).hexdigest())
    request_pin = module.Artifact(request, hashlib.sha256(request.read_bytes()).hexdigest())
    ledger_bytes = ledger.read_bytes()
    ledger_pin = module.Artifact(ledger, hashlib.sha256(ledger_bytes).hexdigest())
    curve = module.read_verified_cohort(project_pin, request_pin, ledger_pin, site_id=site_id)
    assert curve.quantile(Fraction(1, 100)) == (max(peaks), max(peaks))
    assert curve.unknown_mass == 0
    prefix = tmp_path / "conditional-prefix.jsonl"
    prefix.write_bytes(b"".join(ledger_bytes.splitlines(keepends=True)[:2]))
    prefix_pin = module.Artifact(prefix, hashlib.sha256(prefix.read_bytes()).hexdigest())
    partial = module.read_verified_cohort(project_pin, request_pin, prefix_pin, site_id=site_id)
    assert partial.unknown_mass == Fraction(49, 200)
    assert partial.quantile(Fraction(1, 100)) == (peaks[0], None)
    with pytest.raises(ValueError, match="digest mismatch"):
        module.read_verified_cohort(project_pin, request_pin, module.Artifact(ledger, "0" * 64), site_id=site_id)
    assert ledger.read_bytes() == ledger_bytes
