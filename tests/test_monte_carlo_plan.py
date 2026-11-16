"""Analytic and serialisation controls for provisional explicit Monte Carlo sample plans."""

from __future__ import annotations

import copy
import hashlib
import hmac
import json
from collections.abc import Callable
from dataclasses import replace
from decimal import ROUND_DOWN, Decimal, Inexact, localcontext
from pathlib import Path
from typing import Any, cast

import pytest

import runoff_routing.monte_carlo_plan as module
from runoff_routing.monte_carlo_plan import (
    SamplePlan,
    SamplePlanError,
    interpolate_ifd_depth,
    inverse_storm_loss,
    iter_plan_samples,
    iter_saved_sample_records,
    iter_stratum_samples,
    normal_coordinate_strata,
    read_sample_plan,
    read_sample_records,
    select_temporal_pattern,
    validate_sample_records,
    write_sample_plan,
)


def _sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _spec(*, seed: int = 12, loss: str = "empirical_scaled_storm_il") -> dict[str, Any]:
    return {
        "schema_version": 1,
        "policy": {"id": "synthetic-analytic-control", "version": "1", "status": "provisional"},
        "scenario_id": "control-no-climate-uplift",
        "duration_min": 60,
        "sources": {
            "ifd": _sha(b"synthetic source IFD data"),
            "temporal_patterns": _sha(b"synthetic source temporal patterns"),
            "initial_loss": _sha(b"synthetic source CDF"),
        },
        "rng": {
            "algorithm": "hmac-sha256-53-v1",
            "derivation": "canonical-json-domain-separated-v1",
            "root_seed": seed,
        },
        "within_stratum": "uniform_aep_mass_v1",
        "strata": [
            {"id": "h1", "aep_lower": "0.1", "aep_upper": "0.2", "probability_mass": "0.1", "count": 2},
            {"id": "h2", "aep_lower": "0.2", "aep_upper": "0.7", "probability_mass": "0.5", "count": 4},
        ],
        "ifd": {
            "source_id": "exact BoM source labels",
            "interpolation": "z_linear_depth_v1",
            "points": [
                {"aep": "0.05", "depth_mm": "100"},
                {"aep": "0.20", "depth_mm": "80"},
                {"aep": "0.70", "depth_mm": "40"},
            ],
        },
        "tp_bins": [
            {
                "id": "rare",
                "aep_lower": "0.1",
                "aep_upper": "0.2",
                "choices": [
                    {"event_id": "0001", "source_order": 7, "probability": "0.3"},
                    {"event_id": "0101", "source_order": 19, "probability": "0.7"},
                ],
            },
            {
                "id": "frequent",
                "aep_lower": "0.2",
                "aep_upper": "0.7",
                "choices": [{"event_id": "0201", "source_order": 10, "probability": "1"}],
            },
        ],
        "loss": (
            {"mode": "fixed_storm_il", "storm_il_mm": "20"}
            if loss == "fixed_storm_il"
            else {
                "mode": "empirical_scaled_storm_il",
                "source_id": "synthetic inverse CDF",
                "median_storm_il_mm": "20",
                "cdf_quantiles": [
                    {"nonexceedance": "0", "ratio_to_median": "0.2"},
                    {"nonexceedance": "0.5", "ratio_to_median": "1"},
                    {"nonexceedance": "1", "ratio_to_median": "2"},
                ],
            }
        ),
        "fixed_parameters": [
            {"name": "kc", "value": "2.6", "unit": "model"},
            {"name": "m", "value": "0.8", "unit": "dimensionless"},
        ],
        "arf_policy": "catchment-wide-once-after-sampling-by-event-owner",
        "preburst_policy": "storm-IL-before-one-time-preburst-adjustment-by-event-owner",
        "joint_policy": "conditional-tp-on-aep__independent-storm-il-v1",
    }


def test_mass_and_sample_weights_are_exact_and_no_tail_renormalisation() -> None:
    plan = SamplePlan.create(_spec())
    rows = list(iter_plan_samples(plan))
    assert len(rows) == 6
    assert [x.event_probability_weight for x in rows] == [Decimal("0.05")] * 2 + [Decimal("0.125")] * 4
    assert sum((x.event_probability_weight for x in rows), Decimal(0)) == Decimal("0.6")
    assert plan.to_dict()["domain"] == {
        "convention": "AEP_FRACTION",
        "endpoint_rule": "[lower,upper); final upper closed; inverse draws strictly interior",
        "modelled_mass": "0.6",
        "unallocated_stratum_mass": "0",
        "allocated_stratum_mass": "0.6",
        "lower_unmodelled_mass": "0.1",
        "upper_unmodelled_mass": "0.3",
    }
    validate_sample_records(plan, rows)


def test_inverse_table_direction_median_and_ifd_interpolation() -> None:
    plan = SamplePlan.create(_spec())
    assert interpolate_ifd_depth(plan, Decimal("0.2")) == Decimal(80)
    assert abs(interpolate_ifd_depth(plan, Decimal("0.45")) - Decimal("59.0351833368")) < Decimal("0.0000000001")
    assert interpolate_ifd_depth(plan, Decimal("0.7")) == Decimal(40)
    assert inverse_storm_loss(plan, Decimal("0.0")) == (Decimal("0.2"), Decimal("4.0"))
    assert inverse_storm_loss(plan, Decimal("0.25")) == (Decimal("0.60"), Decimal("12.00"))
    assert inverse_storm_loss(plan, Decimal("0.5")) == (Decimal(1), Decimal(20))
    assert inverse_storm_loss(plan, Decimal(1)) == (Decimal(2), Decimal(40))
    with pytest.raises(SamplePlanError, match="extrapolation"):
        interpolate_ifd_depth(plan, Decimal("0.9"))


def test_exact_conditional_tp_bin_edges_and_original_source_ids() -> None:
    plan = SamplePlan.create(_spec())
    assert select_temporal_pattern(plan, Decimal("0.199999"), Decimal("0.2999")) == ("rare", "0001", 7)
    assert select_temporal_pattern(plan, Decimal("0.199999"), Decimal("0.3")) == ("rare", "0101", 19)
    assert select_temporal_pattern(plan, Decimal("0.2"), Decimal("0.0")) == ("frequent", "0201", 10)
    assert select_temporal_pattern(plan, Decimal("0.7"), Decimal("0.5")) == ("frequent", "0201", 10)
    with pytest.raises(SamplePlanError, match="No eligible TP"):
        select_temporal_pattern(plan, Decimal("0.75"), Decimal("0.5"))
    rows = list(iter_plan_samples(plan))
    assert {row.tp_event_id for row in rows[:2]} <= {"0001", "0101"}
    assert {row.tp_event_id for row in rows[2:]} == {"0201"}


def test_plan_roundtrip_and_explicit_replay_never_redraws(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    plan = SamplePlan.create(_spec())
    paths = write_sample_plan(tmp_path / "run1", plan)
    loaded = read_sample_plan(paths[0])
    assert loaded == plan
    expected = list(iter_plan_samples(plan))

    def _unexpected_draw(*_args: object) -> Decimal:
        pytest.fail("RNG called during persisted replay")

    monkeypatch.setattr(module, "_draw", _unexpected_draw)
    replay = read_sample_records(paths[1], loaded)
    assert replay == expected
    assert [x.to_dict() for x in replay] == [x.to_dict() for x in expected]
    with pytest.raises(SamplePlanError, match="already exists"):
        write_sample_plan(tmp_path / "run1", loaded)


def test_reordered_and_chunked_draws_are_identical() -> None:
    plan = SamplePlan.create(_spec())
    expected = list(iter_plan_samples(plan))
    chunks = [
        *iter_stratum_samples(plan, "h2", start=2),
        *iter_stratum_samples(plan, "h1", start=1),
        *iter_stratum_samples(plan, "h2", start=0, stop=2),
        *iter_stratum_samples(plan, "h1", start=0, stop=1),
    ]
    validate_sample_records(plan, chunks)
    assert {x.sample_id: x for x in chunks} == {x.sample_id: x for x in expected}


def test_extension_preserves_logical_draws_and_reweights_all_old_records() -> None:
    plan = SamplePlan.create(_spec())
    extended = plan.extend({"h1": 4, "h2": 8})
    full = copy.deepcopy(_spec())
    full["strata"][0]["count"] = 4
    full["strata"][1]["count"] = 8
    fresh = SamplePlan.create(full)
    assert extended.parent_plan_id == plan.plan_id
    assert extended.plan_id == fresh.plan_id
    assert extended.population_id == plan.population_id == fresh.population_id
    assert [x.to_dict() for x in iter_plan_samples(extended)] == [x.to_dict() for x in iter_plan_samples(fresh)]
    prior = list(iter_plan_samples(plan))
    later = list(iter_plan_samples(extended))
    lookup = {(x.stratum_id, x.index): x for x in later}
    for old in prior:
        new = lookup[(old.stratum_id, old.index)]
        assert new == replace(old, plan_id=extended.plan_id, event_probability_weight=old.event_probability_weight / 2)
    with pytest.raises(SamplePlanError, match="revision weight mismatch"):
        validate_sample_records(extended, prior)
    validate_sample_records(extended, later)


def test_seed_changes_draws_but_not_fixed_policy() -> None:
    a = SamplePlan.create(_spec(seed=1))
    b = SamplePlan.create(_spec(seed=2))
    assert a.plan_id != b.plan_id
    assert a.population_id != b.population_id
    a_rows, b_rows = list(iter_plan_samples(a)), list(iter_plan_samples(b))
    assert a_rows[0].aep_fraction != b_rows[0].aep_fraction
    assert [(r.stratum_id, r.index, r.event_probability_weight) for r in a_rows] == [
        (r.stratum_id, r.index, r.event_probability_weight) for r in b_rows
    ]


def test_fixed_losses_are_distinct_from_stochastic_loss_draws() -> None:
    spec = _spec(loss="fixed_storm_il")
    plan = SamplePlan.create(spec)
    rows = list(iter_plan_samples(plan))
    assert all(r.storm_initial_loss_mm == 20 and r.storm_il_ratio_to_median is None for r in rows)
    assert all(r.loss_uniform is None for r in rows)
    with pytest.raises(SamplePlanError, match="Fixed storm loss"):
        validate_sample_records(plan, [replace(rows[0], loss_uniform=Decimal("0.5"))], require_complete=False)


@pytest.mark.parametrize(
    ("path", "replacement", "message"),
    [
        (("strata", 1, "aep_lower"), "0.21", "gaps/overlap"),
        (("strata", 0, "probability_mass"), "0.099", "mass"),
        (("strata", 0, "count"), -1, "count"),
        (("strata", 0, "count"), True, "count"),
        (("strata", 0, "count"), 1000001, "count"),
        (("ifd", "points", 1, "depth_mm"), "NaN", "finite"),
        (("ifd", "points", 1, "depth_mm"), "200", "depth"),
        (("tp_bins", 0, "choices", 0, "probability"), "0.8", "sum"),
        (("tp_bins", 1, "aep_lower"), "0.3", "gaps/overlap"),
        (("loss", "cdf_quantiles", 1, "ratio_to_median"), "0.1", "monotone"),
        (("loss", "cdf_quantiles", 1, "ratio_to_median"), "1.5", "median factor"),
        (("loss", "cdf_quantiles", 0, "nonexceedance"), "0.1", "endpoints"),
        (("rng", "algorithm"), "MT19937", "Unsupported RNG"),
        (("sources", "ifd"), "wrong", "SHA-256"),
        (("ifd", "points", -1, "aep"), "0.6", "IFD support"),
        (("policy", "status"), "unknown", "policy.status"),
        (("joint_policy",), "loss-conditionally-correlated-with-rainfall-v1", "Unsupported joint_policy"),
    ],
)
def test_invalid_config_is_rejected(path: tuple[str | int, ...], replacement: object, message: str) -> None:
    spec = _spec()
    target: Any = spec
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = replacement
    with pytest.raises(SamplePlanError, match=message):
        SamplePlan.create(spec)


def test_corrupt_plan_and_ledger_are_rejected(tmp_path: Path) -> None:
    plan = SamplePlan.create(_spec())
    manifest, ledger = write_sample_plan(tmp_path / "s", plan)
    raw = json.loads(manifest.read_text())
    raw["domain"]["upper_unmodelled_mass"] = "0"
    with pytest.raises(SamplePlanError, match="mass mismatch"):
        SamplePlan.from_dict(raw)
    raw = json.loads(manifest.read_text())
    raw["spec"]["strata"][0]["count"] = 3
    with pytest.raises(SamplePlanError, match="hash mismatch"):
        SamplePlan.from_dict(raw)
    lines = ledger.read_text().splitlines()
    lines.pop()
    ledger.write_text("\n".join(lines) + "\n")
    with pytest.raises(SamplePlanError, match="Incomplete"):
        read_sample_records(ledger, plan)
    lines.append(lines[0])
    ledger.write_text("\n".join(lines) + "\n")
    with pytest.raises(SamplePlanError, match="Duplicate"):
        read_sample_records(ledger, plan)


def test_normal_coordinate_boundaries_are_probability_weights_not_normal_depth_draws() -> None:
    strata = normal_coordinate_strata((-1.0, 0.0, 1.0), (5, 7))
    assert len(strata) == 2
    assert strata[0]["aep_upper"] == "0.5"
    assert Decimal(str(strata[0]["probability_mass"])) + Decimal(str(strata[1]["probability_mass"])) == (
        Decimal(str(strata[1]["aep_upper"])) - Decimal(str(strata[0]["aep_lower"]))
    )
    with pytest.raises(SamplePlanError, match="strictly increasing"):
        normal_coordinate_strata((0.0, -1.0), (10,))


def test_duplicated_json_keys_and_nonfinite_constants_cannot_be_loaded(tmp_path: Path) -> None:
    manifest = tmp_path / "bad.plan.json"
    manifest.write_text('{"format":"x","format":"y"}')
    with pytest.raises(SamplePlanError, match="Invalid sample plan JSON"):
        read_sample_plan(manifest)
    manifest.write_text('{"x":NaN}')
    with pytest.raises(SamplePlanError, match="Invalid sample plan JSON"):
        read_sample_plan(manifest)


def test_streamed_saved_samples_validate_without_buffering(tmp_path: Path) -> None:
    plan = SamplePlan.create(_spec())
    _, ledger = write_sample_plan(tmp_path / "stream", plan)
    assert [item.sample_id for item in iter_saved_sample_records(ledger, plan)] == [
        item.sample_id for item in iter_plan_samples(plan)
    ]


def test_145_z_linear_rainfall_depth_is_not_linear_in_aep() -> None:
    spec = _spec()
    spec["ifd"]["points"] = [
        {"aep": "0.1", "depth_mm": "100"},
        {"aep": "0.5", "depth_mm": "50"},
    ]
    spec["strata"] = [{"id": "h1", "aep_lower": "0.1", "aep_upper": "0.5", "probability_mass": "0.4", "count": 8}]
    spec["tp_bins"] = [
        {
            "id": "frequent",
            "aep_lower": "0.1",
            "aep_upper": "0.5",
            "choices": [{"event_id": "0001", "source_order": 1, "probability": "1"}],
        }
    ]
    plan = SamplePlan.create(spec)
    # Independent normal-quantile calculation: 50 + 50 * Phi^-1(0.7) / Phi^-1(0.9).
    assert abs(interpolate_ifd_depth(plan, Decimal("0.3")) - Decimal("70.45959471342826")) < Decimal("0.000001")
    assert interpolate_ifd_depth(plan, Decimal("0.1")) == 100
    assert interpolate_ifd_depth(plan, Decimal("0.5")) == 50


def test_zero_allocation_is_explicit_missing_interior_mass_and_can_be_extended() -> None:
    spec = _spec()
    spec["strata"][1]["count"] = 0
    original = SamplePlan.create(spec)
    original_domain = cast("dict[str, str]", original.to_dict()["domain"])
    assert original_domain["unallocated_stratum_mass"] == "0.5"
    assert original_domain["allocated_stratum_mass"] == "0.1"
    assert len(list(iter_plan_samples(original))) == 2
    assert list(iter_stratum_samples(original, "h2")) == []
    validate_sample_records(original, list(iter_plan_samples(original)))
    extended = original.extend({"h1": 2, "h2": 4})
    assert extended.population_id == original.population_id
    assert extended.plan_id != original.plan_id
    extended_domain = cast("dict[str, str]", extended.to_dict()["domain"])
    assert extended_domain["unallocated_stratum_mass"] == "0"
    old = list(iter_plan_samples(original))
    full = list(iter_plan_samples(extended))
    assert [x.sample_id for x in old] == [x.sample_id for x in full[:2]]
    assert [x.aep_fraction for x in old] == [x.aep_fraction for x in full[:2]]
    with pytest.raises(SamplePlanError, match="revision weight mismatch"):
        validate_sample_records(extended, old, require_complete=False)


def test_hmac_53bit_rng_uses_canonical_message_and_root_key() -> None:
    spec = _spec(seed=1234)
    plan = SamplePlan.create(spec)
    row = spec["strata"][0]
    message = {
        "namespace": "python-runoff-routing/mc-sampler",
        "version": 1,
        "population_id": plan.population_id,
        "policy": spec["policy"],
        "sources": spec["sources"],
        "scenario_id": spec["scenario_id"],
        "duration_min": spec["duration_min"],
        "stratum_id": row["id"],
        "aep_lower": row["aep_lower"],
        "aep_upper": row["aep_upper"],
        "index": 0,
        "purpose": "rainfall",
    }
    raw = json.dumps(message, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    digest = hmac.digest((1234).to_bytes(8, "big"), raw, "sha256")
    assert digest.hex() == "7ec4c19b07ce55a19cf1c9f16fab828a4c1fed5802d6a49b746263f39fa9fed5"
    with localcontext() as context:
        context.prec = 60
        unit = Decimal((int.from_bytes(digest[:8], "big") >> 11) * 2 + 1) / Decimal(2**54)
        expected_p = Decimal("0.1") + Decimal("0.1") * unit
    assert next(iter_plan_samples(plan)).aep_fraction == expected_p


def test_source_changes_and_unsupported_extreme_probability_are_rejected() -> None:
    first = SamplePlan.create(_spec())
    spec = _spec()
    spec["sources"]["ifd"] = _sha(b"new source revision")
    changed = SamplePlan.create(spec)
    assert first.population_id != changed.population_id
    assert next(iter_plan_samples(first)).aep_fraction != next(iter_plan_samples(changed)).aep_fraction
    spec = _spec()
    spec["ifd"]["points"][0]["aep"] = "1e-50"
    with pytest.raises(SamplePlanError, match="representable normal-coordinate"):
        SamplePlan.create(spec)


def test_zero_weight_tp_never_selected_and_duplicate_source_order_rejected() -> None:
    spec = _spec()
    spec["tp_bins"][0]["choices"][0]["probability"] = "0"
    spec["tp_bins"][0]["choices"][1]["probability"] = "1"
    plan = SamplePlan.create(spec)
    assert select_temporal_pattern(plan, Decimal("0.15"), Decimal("0.00001"))[1] == "0101"
    spec["tp_bins"][0]["choices"][1]["source_order"] = 7
    with pytest.raises(SamplePlanError, match="Duplicate TP source order"):
        SamplePlan.create(spec)


def test_ledger_rejects_oversize_unterminated_rows(tmp_path: Path) -> None:
    plan = SamplePlan.create(_spec())
    path = tmp_path / "bad.samples.jsonl"
    path.write_text("x" * 20_000)
    with pytest.raises(SamplePlanError, match="row exceeds maximum size"):
        read_sample_records(path, plan)
    path.write_text("{}")
    with pytest.raises(SamplePlanError, match="unterminated"):
        read_sample_records(path, plan)


def test_reviewed_policy_status_requires_adopted_project_method() -> None:
    spec = _spec()
    spec["policy"]["status"] = "reviewed"
    with pytest.raises(SamplePlanError, match="Only the adopted"):
        SamplePlan.create(spec)
    spec["policy"] = {"id": "monte-carlo-statistics", "version": "1", "status": "reviewed"}
    plan = SamplePlan.create(spec)
    assert plan.spec()["joint_policy"] == module.JOINT_POLICY
    approved_policy = cast("dict[str, object]", plan.spec()["policy"])
    assert approved_policy["status"] == "reviewed"


def test_loss_independence_is_explicit_not_implicitly_inferred() -> None:
    spec = _spec()
    spec["joint_policy"] = "conditional-loss-from-rainfall-v1"
    with pytest.raises(SamplePlanError, match="Unsupported joint_policy"):
        SamplePlan.create(spec)
    spec["joint_policy"] = module.JOINT_POLICY
    plan = SamplePlan.create(spec)
    first = next(iter_plan_samples(plan))
    assert first.loss_uniform is not None
    assert first.tp_uniform is not None
    assert 0 < first.loss_uniform < 1
    assert 0 < first.tp_uniform < 1


def test_max_length_stratum_ids_remain_replayable_and_source_specific() -> None:
    spec = _spec()
    spec["strata"][0]["id"] = "x" * 128
    plan = SamplePlan.create(spec)
    records = list(iter_plan_samples(plan))
    assert records[0].stratum_id == "x" * 128
    assert len(records[0].sample_id) == 67
    assert records[0].sample_id.startswith("mc:")
    validate_sample_records(plan, records)
    assert type(records[0]).from_dict(records[0].to_dict()) == records[0]
    spec["sources"]["ifd"] = _sha(b"changed input")
    changed = SamplePlan.create(spec)
    assert next(iter_plan_samples(changed)).sample_id != records[0].sample_id


def test_145_published_hmac_three_purpose_vectors() -> None:
    """Independent #145 byte-level stream receipt; no native RNG parity claim."""
    plan = replace(SamplePlan.create(_spec()), population_id="0" * 64)
    spec: dict[str, object] = {
        "policy": {"id": "monte-carlo-statistics", "version": "1", "status": "reviewed"},
        "sources": {"ifd": "1" * 64, "temporal_patterns": "2" * 64},
        "scenario_id": "synthetic",
        "duration_min": 60,
    }
    row: dict[str, object] = {"id": "bin0", "aep_lower": "0.1", "aep_upper": "0.5"}
    with localcontext() as context:
        context.prec = 60
        expected = {
            "rainfall": Decimal(7152193880365849) / Decimal(18014398509481984),
            "tp": Decimal(7325063005905719) / Decimal(18014398509481984),
            "loss": Decimal(7249325353445475) / Decimal(18014398509481984),
        }
    # Resolve the private pure kernel only in this byte-level contract test.
    draw = cast(
        "Callable[[int, SamplePlan, dict[str, object], dict[str, object], int, str], Decimal]",
        vars(module)["_draw"],
    )
    for purpose, unit in expected.items():
        assert draw(42, plan, spec, row, 0, purpose) == unit


def test_decimal_context_does_not_change_plan_draws_or_replay(tmp_path: Path) -> None:
    """Changing caller Decimal settings cannot alter plan hashes, effective draws or replay."""
    spec = _spec()
    reference = SamplePlan.create(spec)
    reference_manifest = reference.to_dict()
    reference_samples = [record.to_dict() for record in iter_plan_samples(reference)]
    reference_depth = interpolate_ifd_depth(reference, Decimal("0.45"))
    reference_loss = inverse_storm_loss(reference, Decimal("0.3"))
    reference_bins = normal_coordinate_strata((-0.84, 0.0, 0.84), (2, 3))
    with localcontext() as ctx:
        ctx.prec = 5
        ctx.rounding = ROUND_DOWN
        ctx.Emin = -9
        ctx.Emax = 9
        ctx.traps[Inexact] = True
        plan = SamplePlan.create(spec)
        assert plan == reference
        assert plan.to_dict() == reference_manifest
        assert [record.to_dict() for record in iter_plan_samples(plan)] == reference_samples
        assert interpolate_ifd_depth(plan, Decimal("0.45")) == reference_depth
        assert inverse_storm_loss(plan, Decimal("0.3")) == reference_loss
        assert normal_coordinate_strata((-0.84, 0.0, 0.84), (2, 3)) == reference_bins
        manifest, ledger = write_sample_plan(tmp_path / "fixed-context", plan)
        assert read_sample_plan(manifest) == reference
        assert [record.to_dict() for record in read_sample_records(ledger, plan)] == reference_samples


def test_manifest_size_preflight_uses_encoded_bytes_and_leaves_no_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    spec = _spec()
    spec["scenario_id"] = "Unicode-café-雨"
    plan = SamplePlan.create(spec)
    content = (json.dumps(plan.to_dict(), indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")
    assert len(content) > len(content.decode("utf-8"))
    monkeypatch.setattr(module, "_MAX_MANIFEST_BYTES", len(content) - 1)
    rejected_prefix = tmp_path / "too-large"
    with pytest.raises(SamplePlanError, match="manifest exceeds size limit"):
        write_sample_plan(rejected_prefix, plan)
    assert not rejected_prefix.with_suffix(".plan.json").exists()
    assert not rejected_prefix.with_suffix(".samples.jsonl").exists()
    monkeypatch.setattr(module, "_MAX_MANIFEST_BYTES", len(content))
    accepted_prefix = tmp_path / "exact-boundary"
    manifest, ledger = write_sample_plan(accepted_prefix, plan)
    assert manifest.stat().st_size == len(content)
    assert read_sample_plan(manifest) == plan
    assert len(read_sample_records(ledger, plan)) == 6
