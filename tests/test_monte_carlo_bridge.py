"""#149: B/C execution-boundary adapters, using the existing authored public sources.

The production B/C modules remain on their separate staging PRs. These tests
exercise the E contract without copying their sampler or estimator algorithms.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterator
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

import pytest

from runoff_routing import monte_carlo_bridge
from runoff_routing.arr_patterns import read_pattern_file
from runoff_routing.bom_ifd import BoMIFD
from runoff_routing.monte_carlo_bridge import prepare_saved_sample_plan
from runoff_routing.monte_carlo_effective import (
    MCAllocation,
    MCPopulation,
    MCRequestHeader,
    iter_effective_events,
    materialise_arr_sample,
    preparation_model_sha256,
    validate_effective_request,
    write_effective_request,
)
from runoff_routing.monte_carlo_execution import execute_mc_request
from runoff_routing.project_json import EmbeddedRun, Project, SourceFile, write_project
from runoff_routing.rorb_model import RunModel, from_json

ROOT = Path(__file__).parents[1]
EXAMPLES = ROOT / "examples"


def _model() -> RunModel:
    model = from_json((EXAMPLES / "synthetic-run.json").read_text(encoding="utf-8"))
    assert isinstance(model, RunModel)
    return model


def test_explicit_zero_count_stratum_is_preserved_in_header_and_verification(tmp_path: Path) -> None:
    pattern = tmp_path / "patterns.csv"
    pattern.write_bytes((EXAMPLES / "arr-design-synthetic-patterns.csv").read_bytes())
    model = _model()

    event = materialise_arr_sample(
        model=model,
        pattern_set=read_pattern_file(pattern, kind="point"),
        pattern_source_order=1,
        sample_id="control-1",
        scenario_id="control",
        stratum_id="h1",
        stratum_mass=Decimal("0.6"),
        stratum_size=1,
        rainfall_aep_percent=Decimal(2),
        gross_depth_mm=Decimal(20),
        bom_source_sha256=hashlib.sha256(b"authored-draw").hexdigest(),
        arf_region="South-West Western Australia",
        storm_initial_loss_mm=Decimal(6),
        preburst_depth_mm=Decimal(0),
        preburst_policy="none",
        dry_tail_min=120,
    )
    header = MCRequestHeader(
        hashlib.sha256(b"bounded-plan").hexdigest(),
        "authored-analytic/1",
        (SourceFile("patterns.csv", hashlib.sha256(pattern.read_bytes()).hexdigest()),),
        (MCPopulation("control", 60, Decimal(1), Decimal(0), Decimal(0)),),
        1,
        preparation_model_sha256(model),
        (
            MCAllocation("control", 60, "h1", Decimal("0.6"), 1),
            MCAllocation("control", 60, "h2", Decimal("0.4"), 0),
        ),
    )
    request = tmp_path / "effective.jsonl"
    write_effective_request(request, header, (event,))
    stored, _ = validate_effective_request(request)
    assert stored.strata == header.strata
    assert stored.populations[0].rare_unmodelled_mass == 0
    assert len(tuple(iter_effective_events(request))) == 1


def test_stored_b_record_materialises_without_a_new_draw(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    project = tmp_path / "project.json"
    write_project(project, Project("mc_bridge_control", "explicit", EmbeddedRun(_model())))
    pattern = tmp_path / "patterns.csv"
    pattern.write_bytes((EXAMPLES / "arr-design-synthetic-patterns.csv").read_bytes())
    ifd = tmp_path / "ifd.csv"
    ifd.write_bytes((EXAMPLES / "arr-design-synthetic-ifd.csv").read_bytes())
    sample = SimpleNamespace(
        plan_id=hashlib.sha256(b"original-plan").hexdigest(),
        sample_id="mc:abcde123456:h1:00000000",
        scenario_id="control",
        duration_min=60,
        stratum_id="h1",
        aep_fraction=Decimal("0.02"),
        event_probability_weight=Decimal("0.49"),
        gross_ifd_depth_mm=Decimal(20),
        tp_bin_id="rare",
        tp_event_id="0001",
        tp_source_order=1,
        storm_initial_loss_mm=Decimal(6),
    )
    spec: dict[str, object] = {
        "policy": {"id": "monte-carlo-statistics/1", "version": "1", "status": "reviewed"},
        "scenario_id": "control",
        "duration_min": 60,
        "sources": {
            "ifd": hashlib.sha256(ifd.read_bytes()).hexdigest(),
            "temporal_patterns": hashlib.sha256(pattern.read_bytes()).hexdigest(),
        },
        "strata": [{"id": "h1", "aep_lower": "0.01", "aep_upper": "0.5", "probability_mass": "0.49", "count": 1}],
        "ifd": {},
        "fixed_parameters": [
            {"name": "kc", "value": "0.5", "unit": "model"},
            {"name": "m", "value": "1", "unit": "dimensionless"},
        ],
        "arf_policy": "catchment-wide-once-after-sampling-by-event-owner",
        "preburst_policy": "storm-IL-before-one-time-preburst-adjustment-by-event-owner",
    }
    domain = {
        "modelled_mass": "0.49",
        "lower_unmodelled_mass": "0.01",
        "upper_unmodelled_mass": "0.5",
    }

    class FakeB:
        def read_sample_plan(self, _path: Path) -> SimpleNamespace:
            return SimpleNamespace(
                plan_id=sample.plan_id,
                population_id=hashlib.sha256(b"synthetic-population").hexdigest(),
                parent_plan_id=None,
                spec=lambda: spec,
                to_dict=lambda: {"domain": domain},
            )

        def iter_saved_sample_records(self, _path: Path, _plan: SimpleNamespace) -> Iterator[SimpleNamespace]:
            return iter((sample,))

        def ifd_from_bom(self, _source: BoMIFD | None, _duration: int) -> dict[str, object]:
            return {"interpolation": "z_linear_depth_v1", "points": [{"aep": "0.02", "depth_mm": "20"}]}

    spec["ifd"] = FakeB().ifd_from_bom(None, 60)
    monkeypatch.setattr(monte_carlo_bridge, "_sample_api", FakeB)
    request = tmp_path / "prepared.jsonl"
    header = prepare_saved_sample_plan(
        project,
        tmp_path / "b.plan.json",
        tmp_path / "b.samples.jsonl",
        request,
        ifd_path=ifd,
        patterns_path=pattern,
        arf_region="South-West Western Australia",
        dry_tail_min=120,
    )
    assert header.plan_sha256 == sample.plan_id
    assert header.populations[0].rare_unmodelled_mass == Decimal("0.01")
    assert header.populations[0].frequent_unmodelled_mass == Decimal("0.5")
    prepared = next(iter_effective_events(request))
    assert prepared.sample_id == sample.sample_id
    assert prepared.event.event_id.startswith("mc-")
    assert prepared.tp_bin_id == sample.tp_bin_id
    assert prepared.original_tp_id == sample.tp_event_id
    assert prepared.tp_aep_band == "rare"
    assert prepared.preburst_depth_mm == 0
    ledger = tmp_path / "results.jsonl"
    result = execute_mc_request(project, request, ledger)
    assert result.complete
    assert json.loads(ledger.read_text().splitlines()[1])["status"] == "computed_unvalidated"
