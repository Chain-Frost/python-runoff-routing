"""CLI/report adapter from #149's verified peak ledger to #147's weighted estimator.

The statistical method, tail accounting and quantile inversion belong solely
to #147. No estimator, sampler, routing engine or duplicate source reader lives
in this module. The C implementation is loaded when it reaches the staging root.
"""

from __future__ import annotations

import csv
import importlib
import json
import math
from collections.abc import Callable, Iterable, Iterator
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Never, Protocol, cast

from .engine_types import EngineSelection
from .monte_carlo_effective import MCAllocation, MCInputError, MCPopulation, read_header
from .project_json import load_project


class _VerifiedReader(Protocol):
    def __call__(
        self,
        project_path: Path,
        request_path: Path,
        ledger_path: Path,
        *,
        selection: EngineSelection | None = None,
        wheel_artifact: Path | None = None,
    ) -> Iterator[dict[str, object]]: ...


class _CSVWriter(Protocol):
    def writerow(self, row: Iterable[object], /) -> object: ...


class _CurveView(Protocol):
    coverage: object
    groups: tuple[object, ...]

    def estimate(self, aep: float, *, confidence_level: float, relative_aep_screen: float) -> object: ...


class _FrequencyApi(Protocol):
    FrequencyScope: Callable[[str, str, str, str, int, str], object]
    StratumWeight: Callable[[str, float, int], object]
    UnmodelledTails: Callable[[float, float, float], object]
    CurvePopulation: Callable[[object, tuple[object, ...], object], object]
    PeakRecord: Callable[..., object]

    def build_frequency_curve(self, population: object, records: Iterable[object]) -> _CurveView: ...


@dataclass(frozen=True, slots=True)
class MCWeightedResult:
    """Receipt for files written exclusively; no scientific acceptance claim."""

    paths: tuple[Path, Path, Path]
    scopes: int
    point_results_complete: bool


def _fail(message: str) -> Never:
    raise MCInputError(message)


def _frequency_api() -> _FrequencyApi:
    try:
        module = importlib.import_module("runoff_routing.monte_carlo_frequency")
    except ModuleNotFoundError as exc:
        message = "The #147 weighted frequency module must be staged/installed before this command"
        raise MCInputError(message) from exc
    return cast("_FrequencyApi", module)


def _policy_identity(identifier: str) -> tuple[str, str]:
    name, separator, version = identifier.rpartition("/")
    return (name, version) if separator else (identifier, "explicit-unversioned")


def _strata_for(population: MCPopulation, all_strata: tuple[MCAllocation, ...]) -> tuple[MCAllocation, ...]:
    return tuple(
        item
        for item in all_strata
        if (item.scenario_id, item.duration_min) == (population.scenario_id, population.duration_min)
    )


def _sample_records(
    ledger_rows: Iterable[dict[str, object]],
    *,
    scenario_id: str,
    duration_min: int,
    site_id: str,
    scope: object,
    api: _FrequencyApi,
) -> Iterator[object]:
    """Preserve every recorded success/failure; missing planned rows belong to C."""
    for row in ledger_rows:
        if row["scenario_id"] != scenario_id or row["duration_min"] != duration_min:
            continue
        status = cast("str", row["status"])
        sites = row["sites"]
        if not isinstance(sites, list):
            _fail("Missing physical site list in verified MC ledger")
        matches = [
            cast("dict[str, object]", item)
            for item in cast("list[object]", sites)
            if isinstance(item, dict) and cast("dict[str, object]", item).get("print_id") == site_id
        ]
        if status == "computed_unvalidated" and len(matches) == 1:
            peak = matches[0].get("peak_m3_s")
            if not isinstance(peak, (int, float)) or not math.isfinite(peak) or peak < 0:
                _fail("Verified ledger has an invalid computed physical-site peak")
            mapped, value = "valid", float(peak)
        elif status in {"unsupported_feature", "unavailable_engine"}:
            mapped, value = "unsupported", None
        elif status in ("incomplete_output", "computed_unvalidated"):
            mapped, value = "missing", None
        else:
            mapped, value = "failed", None
        yield api.PeakRecord(
            scope=scope,
            stratum_id=cast("str", row["stratum_id"]),
            sample_id=cast("str", row["sample_id"]),
            event_probability_weight=float(cast("str", row["probability_weight"])),
            status=mapped,
            peak_m3_s=value,
            event_id=cast("str", row["event_id"]),
            effective_input_id=cast("str", row["effective_event_sha256"]),
        )


def _curve_population(
    api: _FrequencyApi,
    header_plan_id: str,
    header_policy_id: str,
    population: MCPopulation,
    site_id: str,
    all_strata: tuple[MCAllocation, ...],
) -> tuple[object, object]:
    policy, version = _policy_identity(header_policy_id)
    scope = api.FrequencyScope(
        header_plan_id, policy, version, population.scenario_id, population.duration_min, site_id
    )
    weights = tuple(
        api.StratumWeight(item.stratum_id, float(item.probability_mass), item.planned_samples)
        for item in _strata_for(population, all_strata)
    )
    if not weights:
        _fail("A frequency population requires the full original #146 stratum allocation")
    rare = population.rare_unmodelled_mass
    frequent = population.frequent_unmodelled_mass
    if rare is None or frequent is None:
        # The original hand-authored E boundary may not distinguish tails.
        # It remains an explicitly unmodelled residual, not a zero-flow mass.
        other = max(0.0, 1.0 - float(population.modelled_mass))
        tails = api.UnmodelledTails(0.0, 0.0, other)
    else:
        tails = api.UnmodelledTails(float(frequent), float(rare), 0.0)
    return scope, api.CurvePopulation(scope, weights, tails)


def _validate_target_aeps(aeps: tuple[float, ...]) -> None:
    if not aeps or len(aeps) > 100:
        _fail("Provide 1..100 explicit target flood AEP fractions")
    if any(not math.isfinite(value) or not 0 < value < 1 for value in aeps) or len(set(aeps)) != len(aeps):
        _fail("Target flood AEPs must be unique fractions in (0,1), not percentages")


def format_selected_aep_table(
    site_id: str,
    targets: tuple[float, ...],
    estimates: list[dict[str, object]],
    *,
    confidence_level: float = 0.95,
    relative_aep_screen: float = 0.2,
) -> tuple[list[str], bool]:
    """One site's selected peaks; '!' is NOT RORBwin's unverified '*'."""
    lines = [
        (
            f"Peak flows for selected AEPs (! = conservative {confidence_level:.0%} conditional-iid "
            f"sampling AEP error > {relative_aep_screen:.0%} of target AEP; NOT RORBwin native *)"
        ),
        f"  No.      AEP(1inY)       Peak {site_id}",
    ]
    any_review = False
    for number, (aep, estimate) in enumerate(zip(targets, estimates, strict=True), start=1):
        diagnostic = estimate.get("scientific_sampling_diagnostic")
        review = isinstance(diagnostic, dict) and cast("dict[str, object]", diagnostic).get("status") == "review"
        any_review |= review
        value = estimate.get("peak_m3_s")
        peak_text = f"{float(value):.2f}{'!' if review else ''}" if isinstance(value, (float, int)) else "N/A"
        lines.append(f"{number:>5} {1 / aep:>14.4g} {peak_text:>20}")
    if any(estimate.get("status") == "incomplete" for estimate in estimates):
        lines.append("N/A = unresolved probability mass; no full-population point or uncertainty screen")
    lines.append("! = screening caution under stated iid assumptions; not a flood-flow confidence interval")
    lines.append("RORBwin 6.52 native interval warning (*) = NOT ASSESSED; no native stars are generated")
    lines.append("An absent ! is not engineering acceptance; independent-seed/boundary studies remain open")
    lines.append("")
    return lines, any_review


def _report(
    project: Path,
    request: Path,
    ledger: Path,
    targets: tuple[float, ...],
    *,
    selection: EngineSelection | None,
    wheel_artifact: Path | None,
    csv_writer: _CSVWriter,
    read_rows: _VerifiedReader,
    confidence_level: float,
    relative_aep_screen: float,
) -> tuple[dict[str, object], str, bool]:
    _validate_target_aeps(targets)
    if not math.isfinite(confidence_level) or not 0 < confidence_level < 1:
        _fail("sampling confidence level must be strictly between zero and one")
    if not math.isfinite(relative_aep_screen) or relative_aep_screen <= 0:
        _fail("relative AEP screen must be finite and positive")
    header = read_header(request)
    if not header.strata:
        _fail("Frequency output requires the complete explicit #146 allocation, including zero-count strata")
    loaded = load_project(project)
    sites = tuple(item.identifier for item in loaded.run.catchment.print_locations)
    if not sites:
        _fail("A frequency output needs at least one physical site in the existing model")
    api = _frequency_api()
    csv_writer.writerow(("plan_id", "scenario_id", "duration_min", "print_id", "peak_m3_s", "mass", "cumulative_mass"))
    summaries: list[dict[str, object]] = []
    text_lines: list[str] = []
    all_complete = True
    any_scientific_warning = False
    for population in header.populations:
        for site_id in sites:
            scope, planned = _curve_population(
                api, header.plan_sha256, header.policy_id, population, site_id, header.strata
            )
            rows = read_rows(project, request, ledger, selection=selection, wheel_artifact=wheel_artifact)
            relevant = _sample_records(
                rows,
                scenario_id=population.scenario_id,
                duration_min=population.duration_min,
                site_id=site_id,
                scope=scope,
                api=api,
            )
            curve = api.build_frequency_curve(planned, relevant)
            for group in curve.groups:
                body = asdict(cast("Any", group))
                csv_writer.writerow(
                    (
                        header.plan_sha256,
                        population.scenario_id,
                        population.duration_min,
                        site_id,
                        body["peak_m3_s"],
                        body["probability_mass"],
                        body["cumulative_mass"],
                    )
                )
            estimates = [
                cast(
                    "dict[str, object]",
                    asdict(
                        cast(
                            "Any",
                            curve.estimate(
                                aep, confidence_level=confidence_level, relative_aep_screen=relative_aep_screen
                            ),
                        )
                    ),
                )
                for aep in targets
            ]
            for number, (aep, estimate) in enumerate(zip(targets, estimates, strict=True), start=1):
                estimate["row_number"] = number
                estimate["aep_1_in_y"] = 1 / aep
            coverage = cast("dict[str, object]", asdict(cast("Any", curve.coverage)))
            good = (
                bool(coverage["complete"]) if "complete" in coverage else (cast("Any", curve.coverage).complete is True)
            )
            if any(item.get("status") not in {"estimated", "zero_atom"} for item in estimates):
                good = False
            all_complete &= good
            summaries.append(
                {
                    "plan_id": header.plan_sha256,
                    "scenario_id": population.scenario_id,
                    "duration_min": population.duration_min,
                    "physical_site_id": site_id,
                    "coverage": coverage,
                    "targets": estimates,
                    "software_result_complete": good,
                }
            )
            text_lines.append(
                f"{population.scenario_id} {population.duration_min} min {site_id}: "
                f"{'complete' if good else 'incomplete'}"
            )
            warning_lines, flagged_here = format_selected_aep_table(
                site_id, targets, estimates, confidence_level=confidence_level, relative_aep_screen=relative_aep_screen
            )
            text_lines.extend(warning_lines)
            summaries[-1]["has_scientific_sampling_warning"] = flagged_here
            any_scientific_warning |= flagged_here
    report: dict[str, object] = {
        "format": "python-runoff-routing-mc-frequency-summary",
        "schema_version": 1,
        "plan_sha256": header.plan_sha256,
        "statistical_policy_id": header.policy_id,
        "source_effective_request": str(request.absolute()),
        "source_ledger": str(ledger.absolute()),
        "target_aeps_fractions": list(targets),
        "frequency_scopes": summaries,
        "point_results_complete": all_complete,
        "has_scientific_sampling_warnings": any_scientific_warning,
        "scientific_sampling_policy": {
            "method": "conditional-stratum-dkw-uniform-bonferroni-v1",
            "confidence_level": confidence_level,
            "relative_aep_screen": relative_aep_screen,
            "assumption": "iid_within_rainfall_strata_and_fixed_project_population",
            "interpretation": "conservative_sampling_screen_not_engineering_acceptance",
        },
        "native_rorbwin_interval_warning": "not_assessed",
        "numerical_native_equivalence": "not_assessed",
        "statistical_convergence": "not_assessed",
    }
    return report, "\n".join(text_lines) + "\n", all_complete


def write_mc_frequency(
    project: Path,
    request: Path,
    ledger: Path,
    output_prefix: Path,
    *,
    target_aeps: tuple[float, ...],
    selection: EngineSelection | None = None,
    wheel_artifact: Path | None = None,
    read_rows: _VerifiedReader,
    confidence_level: float = 0.95,
    relative_aep_screen: float = 0.2,
) -> MCWeightedResult:
    """Use #147 for exact weighted frequency, write reports without clobbering."""
    paths = (
        Path(f"{output_prefix}.json"),
        Path(f"{output_prefix}.csv"),
        Path(f"{output_prefix}.txt"),
    )
    if any(path.exists() or path.is_symlink() for path in paths):
        _fail("Frequency report destination already exists; no overwrite allowed")
    created: list[Path] = []
    try:
        with paths[1].open("x", encoding="utf-8", newline="") as stream:
            created.append(paths[1])
            report, text_output, complete = _report(
                project,
                request,
                ledger,
                target_aeps,
                selection=selection,
                wheel_artifact=wheel_artifact,
                csv_writer=csv.writer(stream, lineterminator="\n"),
                read_rows=read_rows,
                confidence_level=confidence_level,
                relative_aep_screen=relative_aep_screen,
            )
        with paths[0].open("x", encoding="utf-8", newline="\n") as stream:
            created.append(paths[0])
            stream.write(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + "\n")
        with paths[2].open("x", encoding="utf-8", newline="\n") as stream:
            created.append(paths[2])
            stream.write(text_output)
    except (OSError, ValueError, TypeError):
        for path in created:
            path.unlink(missing_ok=True)
        raise
    return MCWeightedResult(paths, len(cast("list[object]", report["frequency_scopes"])), complete)
