"""Bridge #146's canonical persisted draws into #149 explicit, replayable events.

No stochastic law, IFD interpolation, numerical engine, or alternate sample
schema is implemented here. The #146 package module is loaded only when the
staged sampling implementation is installed.
"""

from __future__ import annotations

import importlib
import json
from collections.abc import Iterable, Iterator, Mapping
from decimal import Decimal, localcontext
from pathlib import Path
from typing import Never, Protocol, cast

from .arr_patterns import PatternKind, read_pattern_file
from .bom_ifd import BoMIFD, read_bom_ifd_csv
from .monte_carlo_effective import (
    MC_SAMPLE_DECIMAL_CONTEXT,
    EffectiveMCEvent,
    MCAllocation,
    MCInputError,
    MCPopulation,
    MCRequestHeader,
    materialise_arr_sample,
    preparation_model_sha256,
    sha256_file,
    write_effective_request,
)
from .project_json import SourceFile, load_project
from .rorb_model import RunModel

MAX_SPEC_BYTES = 2 * 1024 * 1024
_ADOPTED_ARF = "catchment-wide-once-after-sampling-by-event-owner"
_ADOPTED_PREBURST = "storm-IL-before-one-time-preburst-adjustment-by-event-owner"


class SamplePlanView(Protocol):
    plan_id: str
    population_id: str
    parent_plan_id: str | None

    def spec(self) -> dict[str, object]: ...

    def to_dict(self) -> dict[str, object]: ...


class SavedSampleView(Protocol):
    plan_id: str
    sample_id: str
    scenario_id: str
    duration_min: int
    stratum_id: str
    aep_fraction: Decimal
    event_probability_weight: Decimal
    gross_ifd_depth_mm: Decimal
    tp_bin_id: str
    tp_event_id: str
    tp_source_order: int
    storm_initial_loss_mm: Decimal


class _PlanFactory(Protocol):
    def create(self, spec: dict[str, object]) -> SamplePlanView: ...


class _SampleApi(Protocol):
    SamplePlan: _PlanFactory

    def write_sample_plan(self, prefix: Path, plan: SamplePlanView) -> tuple[Path, Path]: ...

    def read_sample_plan(self, path: Path) -> SamplePlanView: ...

    def iter_saved_sample_records(
        self, path: Path, plan: SamplePlanView, *, require_complete: bool = True
    ) -> Iterator[SavedSampleView]: ...

    def ifd_from_bom(self, source: BoMIFD, duration_min: int) -> dict[str, object]: ...


def _fail(message: str) -> Never:
    raise MCInputError(message)


def _sample_api() -> _SampleApi:
    try:
        module = importlib.import_module("runoff_routing.monte_carlo_plan")
    except ModuleNotFoundError as exc:
        message = "The #146 sample-plan package must be staged/installed before plan creation or preparation"
        raise MCInputError(message) from exc
    return cast("_SampleApi", module)


def _obj(raw: object, label: str) -> dict[str, object]:
    if not isinstance(raw, dict):
        _fail(f"{label} must be an object from the accepted #146 plan")
    return cast("dict[str, object]", raw)


def _list(raw: object, label: str) -> list[object]:
    if not isinstance(raw, list):
        _fail(f"{label} must be an ordered list from the accepted #146 plan")
    return cast("list[object]", raw)


def _text(raw: object, label: str) -> str:
    if not isinstance(raw, str) or not raw or raw != raw.strip() or any(ord(c) < 32 for c in raw):
        _fail(f"Invalid plan field {label}")
    return raw


def _decimal(raw: object, label: str) -> Decimal:
    if not isinstance(raw, str):
        _fail(f"Plan {label} must preserve an exact decimal string")
    try:
        value = Decimal(raw)
    except ArithmeticError as exc:
        message = f"Invalid plan decimal for {label}"
        raise MCInputError(message) from exc
    if not value.is_finite():
        _fail(f"Nonfinite plan decimal {label}")
    return value


def _pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            _fail(f"Duplicate sample-plan config key: {key}")
        result[key] = value
    return result


def _bad_constant(value: str) -> Never:
    _fail(f"Nonstandard sample-plan JSON constant: {value}")


def create_saved_sample_plan(spec_path: Path, prefix: Path) -> tuple[Path, Path]:
    """CLI/API entry point into B's single canonical plan factory and writer."""
    if spec_path.stat().st_size > MAX_SPEC_BYTES:
        _fail("Sample-plan config exceeds 2 MiB")
    content = spec_path.read_bytes()
    if not content or len(content) > MAX_SPEC_BYTES:
        _fail("Empty or oversized sample-plan config")
    try:
        raw: object = json.loads(content.decode("utf-8-sig"), object_pairs_hook=_pairs, parse_constant=_bad_constant)
    except (UnicodeError, TypeError, ValueError) as exc:
        message = "Malformed sample-plan JSON"
        raise MCInputError(message) from exc
    plan = _sample_api().SamplePlan.create(_obj(raw, "sample-plan spec"))
    return _sample_api().write_sample_plan(prefix, plan)


def _source_files(spec: dict[str, object], request_path: Path, paths: Mapping[str, Path]) -> tuple[SourceFile, ...]:
    hashed = _obj(spec["sources"], "sources")
    if set(paths) != set(hashed):
        _fail("All and only original plan source roles must have explicit file paths")
    parent = request_path.absolute().parent
    result: list[SourceFile] = []
    for role, stored in hashed.items():
        path = paths[role].absolute()
        if path.is_symlink() or not path.is_file() or sha256_file(path) != stored:
            _fail(f"Original #146 source hash does not match supplied {role} bytes")
        try:
            relative = path.relative_to(parent).as_posix()
        except ValueError:
            _fail("Original source files must be within the effective-request directory")
        result.append(SourceFile(relative, _text(stored, f"sources.{role}")))
    return tuple(result)


def _check_fixed(spec: dict[str, object], model: RunModel) -> None:
    parameters = model.parameters
    if (
        not parameters.lumped_kc
        or len(parameters.routing) != 1
        or parameters.num_isa != 1
        or parameters.loss_model != 1
        or len(parameters.losses) != 1
    ):
        _fail("First MC subset requires one fixed lumped kc/m and pervious IL/CL")
    routing = parameters.routing[0]
    fixed = {
        "kc": routing.kc,
        "m": routing.m,
        "continuing": parameters.losses[0].continuing,
    }
    for item in _list(spec["fixed_parameters"], "fixed_parameters"):
        entry = _obj(item, "fixed parameter")
        name = _text(entry["name"], "fixed parameter name")
        if name not in fixed or _decimal(entry["value"], name) != fixed[name]:
            _fail("Plan-fixed routing/loss parameter differs from the selected project")


def _allocations(spec: dict[str, object]) -> tuple[MCAllocation, ...]:
    scenario = _text(spec["scenario_id"], "scenario_id")
    duration = cast("int", spec["duration_min"])
    result: list[MCAllocation] = []
    for item in _list(spec["strata"], "strata"):
        entry = _obj(item, "stratum")
        result.append(
            MCAllocation(
                scenario,
                duration,
                _text(entry["id"], "stratum ID"),
                _decimal(entry["probability_mass"], "stratum probability mass"),
                cast("int", entry["count"]),
            )
        )
    return tuple(result)


def _policy_id(spec: dict[str, object]) -> str:
    policy = _obj(spec["policy"], "policy")
    name = _text(policy["id"], "policy ID")
    version = _text(policy["version"], "policy version")
    return name if name.endswith(f"/{version}") else f"{name}/{version}"


def _check_depth_source(api: _SampleApi, spec: dict[str, object], ifd_path: Path) -> None:
    duration = cast("int", spec["duration_min"])
    bom = read_bom_ifd_csv(ifd_path)
    candidate = api.ifd_from_bom(bom, duration)
    ifd = _obj(spec["ifd"], "IFD")
    if ifd.get("interpolation") != "z_linear_depth_v1" or candidate["points"] != ifd.get("points"):
        _fail("Plan IFD anchors are not the source-backed #146 z-linear BoM depth table")


def _materialised(
    records: Iterable[SavedSampleView],
    *,
    model: RunModel,
    patterns_path: Path,
    pattern_kind: str,
    strata: tuple[MCAllocation, ...],
    bom_sha256: str,
    arf_region: str,
    dry_tail_min: int,
) -> Iterator[EffectiveMCEvent]:
    if pattern_kind not in {"point", "areal"}:
        _fail("Unexpected pattern source kind")
    patterns = read_pattern_file(patterns_path, kind=cast("PatternKind", pattern_kind))
    allocation = {item.stratum_id: item for item in strata}
    for record in records:
        planned = allocation.get(record.stratum_id)
        if planned is None or record.plan_id == "" or record.event_probability_weight <= 0:
            _fail("Sample belongs to an unknown or unallocated plan stratum")
        if (
            record.scenario_id != planned.scenario_id
            or record.duration_min != planned.duration_min
            or planned.planned_samples <= 0
        ):
            _fail("Sample scenario/duration/stratum allocation differs from its plan")
        with localcontext(MC_SAMPLE_DECIMAL_CONTEXT):
            aep_percent = record.aep_fraction * 100
        event = materialise_arr_sample(
            model=model,
            pattern_set=patterns,
            pattern_source_order=record.tp_source_order,
            expected_original_tp_id=record.tp_event_id,
            tp_bin_id=record.tp_bin_id,
            sample_id=record.sample_id,
            scenario_id=record.scenario_id,
            stratum_id=record.stratum_id,
            stratum_mass=planned.probability_mass,
            stratum_size=planned.planned_samples,
            rainfall_aep_percent=aep_percent,
            gross_depth_mm=record.gross_ifd_depth_mm,
            bom_source_sha256=bom_sha256,
            arf_region=arf_region,
            storm_initial_loss_mm=record.storm_initial_loss_mm,
            preburst_depth_mm=Decimal(0),
            preburst_policy="none",
            dry_tail_min=dry_tail_min,
        )
        if event.probability_weight != record.event_probability_weight:
            _fail("The submitted B sample has a stale weight from a different plan revision")
        yield event


def prepare_saved_sample_plan(
    project_path: Path,
    plan_path: Path,
    samples_path: Path,
    request_path: Path,
    *,
    ifd_path: Path,
    patterns_path: Path,
    arf_region: str,
    dry_tail_min: int,
    loss_source_path: Path | None = None,
) -> MCRequestHeader:
    """Validate B's saved plan/draws without RNG, then emit exact effective events."""
    api = _sample_api()
    plan = api.read_sample_plan(plan_path)
    spec = plan.spec()
    if spec["arf_policy"] != _ADOPTED_ARF or spec["preburst_policy"] != _ADOPTED_PREBURST:
        _fail("Unrecognised plan ARF or storm/burst loss preparation policy")
    # Use one source-model snapshot to check plan-fixed kc/m, derive ARF
    # and bind the prepared request to the routed computational model.
    model = load_project(project_path).run
    _check_fixed(spec, model)
    _check_depth_source(api, spec, ifd_path)
    original_paths: dict[str, Path] = {"ifd": ifd_path, "temporal_patterns": patterns_path}
    if loss_source_path is not None:
        original_paths["initial_loss"] = loss_source_path
    sources = _source_files(spec, request_path, original_paths)
    allocations = _allocations(spec)
    manifest = _obj(plan.to_dict()["domain"], "sampling domain")
    modelled = _decimal(manifest["modelled_mass"], "modelled mass")
    lower = _decimal(manifest["lower_unmodelled_mass"], "rare unmodelled mass")
    upper = _decimal(manifest["upper_unmodelled_mass"], "frequent unmodelled mass")
    scenario = _text(spec["scenario_id"], "scenario")
    duration = cast("int", spec["duration_min"])
    event_count = sum(item.planned_samples for item in allocations)
    if not event_count:
        _fail("This execution boundary needs at least one planned sample; zero-allocation mass remains explicit")
    header = MCRequestHeader(
        plan_sha256=plan.plan_id,
        policy_id=_policy_id(spec),
        source_files=sources,
        populations=(MCPopulation(scenario, duration, modelled, lower, upper),),
        event_count=event_count,
        preparation_model_sha256=preparation_model_sha256(model),
        strata=allocations,
        sample_population_id=plan.population_id,
        parent_plan_sha256=plan.parent_plan_id,
    )
    with localcontext(MC_SAMPLE_DECIMAL_CONTEXT):
        area_km2 = sum((s.area_km2 for s in model.catchment.subareas), Decimal(0))
    kind = "point" if area_km2 < 75 else "areal"
    records = api.iter_saved_sample_records(samples_path, plan)
    events = _materialised(
        records,
        model=model,
        patterns_path=patterns_path,
        pattern_kind=kind,
        strata=allocations,
        bom_sha256=cast("str", _obj(spec["sources"], "sources")["ifd"]),
        arf_region=arf_region,
        dry_tail_min=dry_tail_min,
    )
    write_effective_request(request_path, header, events)
    return header
