"""The integrated native review preserves time, identity and separate volume semantics."""

from __future__ import annotations

import json
import subprocess
from decimal import Decimal
from pathlib import Path

import pytest

from runoff_routing.integration import RunInputError, read_run_json, run_model
from runoff_routing.integration_reporting import review_recorded_print

ROOT = Path(__file__).absolute().parents[1]


def _model_result():
    run = read_run_json((ROOT / "examples" / "synthetic-run.json").read_text(encoding="utf-8"))
    return run_model(run)


def _tokens_and_times() -> tuple[tuple[str, ...], tuple[str, ...]]:
    result = _model_result()
    flows = tuple(f"{value:.4f}" for value in result.prints[0].discharge_m3_s)
    times = tuple(f"{(index + 1) * result.numerical.dt_hours:.2f}" for index in range(len(flows)))
    return flows, times


def _review():
    result = _model_result()
    flows, times = _tokens_and_times()
    return review_recorded_print(
        result,
        flows,
        model_print_id="print_1",
        native_column_id="Hyd001",
        engine_profile="RORB_CMD 6.44 - synthetic identity only",
        raw_native_time_tokens=times,
    )


def test_native_print_identity_and_timing_are_not_inferred() -> None:
    audit = _review()
    result = _model_result()
    assert audit.model_print_id == "print_1"
    assert audit.native_column_id == "Hyd001"
    assert audit.model_print_label == result.prints[0].label
    assert audit.numerical_acceptance == "unassessed"
    assert audit.printed_discharge_parity.within_print_budget
    assert audit.native_reporting.raw_native_time_tokens is not None
    assert audit.native_reporting.raw_native_time_tokens[0] == "0.50"
    assert audit.native_reporting.sample_index_elapsed_hours[0] == 0
    assert audit.native_reporting.sample_count == len(result.prints[0].discharge_m3_s)


def test_physical_flux_and_native_sum_are_distinct_even_after_integration() -> None:
    audit = _review()
    native = audit.native_reporting
    assert native.inclusive_sample_sum_m3 - native.physical_trapezoid_m3 == native.endpoint_weight_difference_m3
    assert float(native.physical_trapezoid_m3) == pytest.approx(
        audit.printed_discharge_parity.native_integral_m3, rel=1e-12, abs=1e-8
    )
    assert native.sample_sum_consistent_with_report is None
    assert native.trapezoid_consistent_with_report is None


def test_native_report_statistic_can_be_compared_without_accepting_routing() -> None:
    result = _model_result()
    flows, times = _tokens_and_times()
    baseline = _review()
    reported_text = str(baseline.native_reporting.inclusive_sample_sum_m3)
    audit = review_recorded_print(
        result,
        flows,
        model_print_id="print_1",
        native_column_id="Hyd001",
        engine_profile="RORB_CMD 6.44 - synthetic identity only",
        raw_native_time_tokens=times,
        native_reported_volume_text=reported_text,
    )
    assert audit.native_reporting.sample_sum_consistent_with_report is True
    assert audit.numerical_acceptance == "unassessed"


def test_machine_readable_report_preserves_original_native_tokens() -> None:
    audit = _review()
    payload = json.loads(audit.to_json())
    assert payload["native_column_id"] == "Hyd001"
    assert payload["numerical_acceptance"] == "unassessed"
    assert payload["native_reporting"]["raw_native_time_tokens"][0] == "0.50"
    assert payload["native_reporting"]["sample_index_elapsed_hours"][0] == "0.0"
    assert Decimal(payload["native_reporting"]["inclusive_sample_sum_m3"]) == audit.native_reporting.inclusive_sample_sum_m3
    assert "reported_native_volume_m3" in payload["native_reporting"]


@pytest.mark.parametrize("changed", ["model", "column", "profile", "counts", "times", "empty_time"])
def test_missing_or_ambiguous_provenance_is_rejected(changed: str) -> None:
    result = _model_result()
    flows, times = _tokens_and_times()
    kwargs = {
        "model_print_id": "print_1",
        "native_column_id": "Hyd001",
        "engine_profile": "RORB_CMD 6.44 - synthetic identity only",
        "raw_native_time_tokens": times,
    }
    if changed == "model":
        kwargs["model_print_id"] = "unmapped"
    elif changed == "column":
        kwargs["native_column_id"] = ""
    elif changed == "profile":
        kwargs["engine_profile"] = ""
    elif changed == "counts":
        flows = flows[:-1]
    elif changed == "times":
        kwargs["raw_native_time_tokens"] = times[:-1]
    else:
        kwargs["raw_native_time_tokens"] = ("", *times[1:])
    with pytest.raises(RunInputError):
        review_recorded_print(result, flows, **kwargs)


def test_native_printed_flow_token_validation_fails_closed() -> None:
    result = _model_result()
    flows, times = _tokens_and_times()
    bad = (flows[0], "NaN", *flows[2:])
    with pytest.raises(ValueError, match="finite"):
        review_recorded_print(
            result,
            bad,
            model_print_id="print_1",
            native_column_id="Hyd001",
            engine_profile="RORB_CMD 6.44 - synthetic identity only",
            raw_native_time_tokens=times,
        )


def test_integrated_audit_never_launches_native_programs(monkeypatch: pytest.MonkeyPatch) -> None:
    def reject_subprocess(*_args: object, **_kwargs: object) -> None:
        pytest.fail("Native execution is prohibited in offline reporting review")

    monkeypatch.setattr(subprocess, "run", reject_subprocess)
    assert _review().numerical_acceptance == "unassessed"
