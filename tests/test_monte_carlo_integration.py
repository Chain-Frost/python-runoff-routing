"""Integrated S7 #146 → #149 → #147 CLI contract on authored public source bytes.

This exercises the real B/C implementations on the staged integration branch.
Incomplete rainfall tails are retained: successful routing is not a
full-domain flood-frequency estimate or RORBwin native parity.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from dataclasses import replace
from decimal import Decimal, localcontext
from pathlib import Path
from typing import cast

import pytest

from runoff_routing import monte_carlo_execution as mc_execution
from runoff_routing.bom_ifd import read_bom_ifd_csv
from runoff_routing.monte_carlo_bridge import prepare_saved_sample_plan
from runoff_routing.monte_carlo_effective import iter_effective_events, validate_effective_request
from runoff_routing.monte_carlo_execution import MCRunError, execute_mc_request, extend_mc_execution, main
from runoff_routing.monte_carlo_plan import ifd_from_bom, read_sample_plan, write_sample_plan
from runoff_routing.project_batch import run_project_events
from runoff_routing.project_json import EmbeddedRun, Project, load_project, write_project
from runoff_routing.rorb_model import RunModel, from_json

EXAMPLES = Path(__file__).parents[1] / "examples"


def _fixture(root: Path) -> tuple[Path, Path, Path, Path]:
    project = root / "project.json"
    model = from_json((EXAMPLES / "synthetic-run.json").read_text(encoding="utf-8"))
    assert isinstance(model, RunModel)
    write_project(project, Project("integrated_mc", "explicit", EmbeddedRun(model)))
    ifd = root / "ifd.csv"
    patterns = root / "patterns.csv"
    ifd.write_bytes((EXAMPLES / "arr-design-synthetic-ifd.csv").read_bytes())
    patterns.write_bytes((EXAMPLES / "arr-design-synthetic-patterns.csv").read_bytes())
    spec: dict[str, object] = {
        "schema_version": 1,
        "policy": {"id": "monte-carlo-statistics", "version": "1", "status": "reviewed"},
        "scenario_id": "synthetic",
        "duration_min": 60,
        "sources": {
            "ifd": hashlib.sha256(ifd.read_bytes()).hexdigest(),
            "temporal_patterns": hashlib.sha256(patterns.read_bytes()).hexdigest(),
        },
        "rng": {
            "algorithm": "hmac-sha256-53-v1",
            "derivation": "canonical-json-domain-separated-v1",
            "root_seed": 42,
        },
        "within_stratum": "uniform_aep_mass_v1",
        "strata": [
            {"id": "h1", "aep_lower": "0.01", "aep_upper": "0.02", "probability_mass": "0.01", "count": 2},
        ],
        "ifd": ifd_from_bom(read_bom_ifd_csv(ifd), 60),
        "tp_bins": [
            {
                "id": "rare",
                "aep_lower": "0.01",
                "aep_upper": "0.02",
                "choices": [
                    {"event_id": "0001", "source_order": 1, "probability": "0.5"},
                    {"event_id": "0002", "source_order": 2, "probability": "0.5"},
                ],
            },
        ],
        "loss": {"mode": "fixed_storm_il", "storm_il_mm": "1"},
        "fixed_parameters": [
            {"name": "kc", "value": "0.5", "unit": "RORB_coefficient"},
            {"name": "m", "value": "1", "unit": "dimensionless"},
            {"name": "continuing", "value": "0.1", "unit": "mm/h"},
        ],
        "arf_policy": "catchment-wide-once-after-sampling-by-event-owner",
        "preburst_policy": "storm-IL-before-one-time-preburst-adjustment-by-event-owner",
        "joint_policy": "conditional-tp-on-aep__independent-storm-il-v1",
    }
    config = root / "spec.json"
    config.write_text(json.dumps(spec) + "\n", encoding="utf-8")
    return project, config, ifd, patterns


def test_saved_b_to_e_request_is_decimal_context_independent(tmp_path: Path) -> None:
    project, config, ifd, patterns = _fixture(tmp_path)
    prefix = tmp_path / "context-study"
    assert main(["plan", str(config), str(prefix)]) == 0
    outputs: list[bytes] = []
    for precision in (12, 28, 80):
        request = tmp_path / f"context-{precision}.jsonl"
        with localcontext() as ctx:
            ctx.prec = precision
            prepare_saved_sample_plan(
                project,
                prefix.with_suffix(".plan.json"),
                prefix.with_suffix(".samples.jsonl"),
                request,
                ifd_path=ifd,
                patterns_path=patterns,
                arf_region="South-West Western Australia",
                dry_tail_min=120,
            )
        outputs.append(request.read_bytes())
    assert outputs[0] == outputs[1] == outputs[2]


@pytest.mark.parametrize("model_change", ["routing_kc", "catchment_area"])
def test_changed_model_cannot_execute_saved_b_draws(tmp_path: Path, model_change: str) -> None:
    project, config, ifd, patterns = _fixture(tmp_path)
    prefix = tmp_path / "model-identity"
    assert main(["plan", str(config), str(prefix)]) == 0
    request = tmp_path / "model-effective.jsonl"
    prepare_saved_sample_plan(
        project,
        prefix.with_suffix(".plan.json"),
        prefix.with_suffix(".samples.jsonl"),
        request,
        ifd_path=ifd,
        patterns_path=patterns,
        arf_region="South-West Western Australia",
        dry_tail_min=120,
    )
    source = load_project(project)
    model = source.run
    if model_change == "routing_kc":
        params = replace(model.parameters, routing=(replace(model.parameters.routing[0], kc=Decimal(5)),))
        changed = replace(model, parameters=params)
    else:
        areas = model.catchment.subareas
        changed_areas = (replace(areas[0], area_km2=areas[0].area_km2 + 1), *areas[1:])
        changed = replace(model, catchment=replace(model.catchment, subareas=changed_areas))
    project.unlink()
    write_project(project, replace(source.project, model_source=EmbeddedRun(changed)))
    ledger = tmp_path / "rejected.jsonl"
    with pytest.raises(MCRunError, match="prepared for a different source model"):
        execute_mc_request(project, request, ledger)
    assert not ledger.exists()


def test_routes_validated_model_snapshot_when_project_changes_at_checkpoint(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project, config, ifd, patterns = _fixture(tmp_path)
    prefix = tmp_path / "snapshot"
    assert main(["plan", str(config), str(prefix)]) == 0
    request = tmp_path / "snapshot-effective.jsonl"
    prepare_saved_sample_plan(
        project,
        prefix.with_suffix(".plan.json"),
        prefix.with_suffix(".samples.jsonl"),
        request,
        ifd_path=ifd,
        patterns_path=patterns,
        arf_region="South-West Western Australia",
        dry_tail_min=120,
    )
    baseline = tmp_path / "snapshot-baseline.jsonl"
    assert execute_mc_request(project, request, baseline).complete

    original_new_ledger = cast("Callable[[Path, dict[str, object]], str]", vars(mc_execution)["_new_ledger"])

    def mutate_after_identity_check(path: Path, header: dict[str, object]) -> str:
        previous = original_new_ledger(path, header)
        loaded = load_project(project)
        params = loaded.run.parameters
        modified = replace(loaded.run, parameters=replace(params, routing=(replace(params.routing[0], kc=Decimal(5)),)))
        project.unlink()
        write_project(project, replace(loaded.project, model_source=EmbeddedRun(modified)))
        return previous

    raced = tmp_path / "snapshot-raced.jsonl"
    with monkeypatch.context() as patch:
        patch.setattr(mc_execution, "_new_ledger", mutate_after_identity_check)
        assert execute_mc_request(project, request, raced).complete
    # Every routed event came from the originally validated source snapshot,
    # not the changed project file reopened by the common event runner.
    assert raced.read_bytes() == baseline.read_bytes()
    with pytest.raises(MCRunError, match="prepared for a different source model"):
        execute_mc_request(project, request, tmp_path / "snapshot-new-run.jsonl")


def test_real_b_to_e_to_c_cli_and_representative_replay(tmp_path: Path) -> None:
    project, config, ifd, patterns = _fixture(tmp_path)
    prefix = tmp_path / "study"
    request = tmp_path / "effective.jsonl"
    ledger = tmp_path / "computed.jsonl"
    report = tmp_path / "frequency"
    assert main(["plan", str(config), str(prefix)]) == 0
    assert (
        main(
            [
                "prepare",
                str(project),
                str(tmp_path / "study.plan.json"),
                str(tmp_path / "study.samples.jsonl"),
                str(request),
                "--ifd",
                str(ifd),
                "--patterns",
                str(patterns),
                "--arf-region",
                "South-West Western Australia",
                "--dry-tail-min",
                "120",
            ]
        )
        == 0
    )
    header, _ = validate_effective_request(request)
    assert header.event_count == 2
    assert header.strata[0].planned_samples == 2
    assert header.populations[0].rare_unmodelled_mass == Decimal("0.01")
    assert header.populations[0].frequent_unmodelled_mass == Decimal("0.98")
    events = tuple(iter_effective_events(request))
    assert len(events) == 2
    assert all(item.tp_aep_band == "rare" and item.tp_bin_id == "rare" for item in events)
    assert all(item.event.event_id.startswith("mc-") for item in events)

    assert main(["run", str(project), str(request), str(ledger), "--engine", "python-cmd"]) == 0
    assert main(["run", str(project), str(request), str(ledger), "--resume"]) == 0
    for event in events:
        direct = run_project_events(project, (event.event,)).outcomes[0]
        assert direct.status == "computed_unvalidated"
    assert (
        main(
            [
                "frequency",
                str(project),
                str(request),
                str(ledger),
                str(report),
                "--aep",
                "0.01",
                "--confidence-level",
                "0.9",
                "--relative-aep-screen",
                "0.1",
            ]
        )
        == 2
    )
    body = json.loads((tmp_path / "frequency.json").read_text(encoding="utf-8"))
    assert body["point_results_complete"] is False
    assert body["native_rorbwin_interval_warning"] == "not_assessed"
    assert cast("dict[str, object]", body["scientific_sampling_policy"])["confidence_level"] == 0.9
    assert cast("dict[str, object]", body["scientific_sampling_policy"])["relative_aep_screen"] == 0.1
    scopes = cast("list[dict[str, object]]", body["frequency_scopes"])
    assert len(scopes) == 1
    assert scopes[0]["physical_site_id"] == "print_1"
    targets = cast("list[dict[str, object]]", scopes[0]["targets"])
    assert targets[0]["status"] == "incomplete"
    assert targets[0]["peak_m3_s"] is None
    assert targets[0]["aep_1_in_y"] == 100
    assert targets[0]["row_number"] == 1
    assert targets[0]["native_interval_warning"] == "not_assessed"
    assert targets[0]["interval_probability_audit"] is None
    assert cast("dict[str, object]", targets[0]["scientific_sampling_diagnostic"])["status"] == "not_assessed"
    assert "AEP(1inY)" in (tmp_path / "frequency.txt").read_text(encoding="utf-8")
    assert "N/A" in (tmp_path / "frequency.txt").read_text(encoding="utf-8")
    assert (tmp_path / "frequency.csv").is_file()
    first = events[0]
    assert main(["replay", str(project), str(request), str(ledger), first.sample_id, str(tmp_path / "selected")]) == 0
    replayed = json.loads((tmp_path / "selected.json").read_text(encoding="utf-8"))
    outcomes = cast("list[dict[str, object]]", replayed["outcomes"])
    assert outcomes[0]["event_id"] == first.event.event_id


def test_extended_plan_reuses_identical_computations_with_new_stratum_weights(tmp_path: Path) -> None:
    project, config, ifd, patterns = _fixture(tmp_path)
    assert main(["plan", str(config), str(tmp_path / "initial")]) == 0
    old_plan_path = tmp_path / "initial.plan.json"
    old_samples_path = tmp_path / "initial.samples.jsonl"
    old_request = tmp_path / "original-effective.jsonl"
    old_ledger = tmp_path / "original-ledger.jsonl"
    prepare_saved_sample_plan(
        project,
        old_plan_path,
        old_samples_path,
        old_request,
        ifd_path=ifd,
        patterns_path=patterns,
        arf_region="South-West Western Australia",
        dry_tail_min=120,
    )
    assert execute_mc_request(project, old_request, old_ledger).complete

    old_plan = read_sample_plan(old_plan_path)
    new_plan = old_plan.extend({"h1": 4})
    assert new_plan.parent_plan_id == old_plan.plan_id
    new_plan_path, new_samples_path = write_sample_plan(tmp_path / "extended", new_plan)
    new_request = tmp_path / "extended-effective.jsonl"
    prepare_saved_sample_plan(
        project,
        new_plan_path,
        new_samples_path,
        new_request,
        ifd_path=ifd,
        patterns_path=patterns,
        arf_region="South-West Western Australia",
        dry_tail_min=120,
    )
    assert (
        main(
            ["extend", str(project), str(old_request), str(old_ledger), str(new_request), str(tmp_path / "reuse.jsonl")]
        )
        == 0
    )
    reused = (tmp_path / "reuse.jsonl").read_bytes()
    assert len(reused.splitlines()) == 5
    old_samples = tuple(iter_effective_events(old_request))
    new_samples = tuple(iter_effective_events(new_request))
    assert [s.sample_id for s in old_samples] == [s.sample_id for s in new_samples[:2]]
    assert all(s.probability_weight == Decimal("0.0025") for s in new_samples)
    assert all(s.probability_weight == Decimal("0.005") for s in old_samples)
    assert execute_mc_request(project, new_request, tmp_path / "fresh.jsonl").complete
    assert reused == (tmp_path / "fresh.jsonl").read_bytes()
    assert (tmp_path / "original-ledger.jsonl").is_file()

    with pytest.raises(MCRunError, match="parent"):
        extend_mc_execution(project, old_request, old_ledger, old_request, tmp_path / "not-an-extension.jsonl")
    assert not (tmp_path / "not-an-extension.jsonl").exists()
