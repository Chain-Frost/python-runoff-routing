"""Typed S1/S2 reporting review without native execution or silent time alignment."""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from decimal import Decimal
from typing import Literal

from runoff_routing.integration import RunInputError, RunResult, assess_recorded_print
from runoff_routing.parity_metrics import PrintedParity
from runoff_routing.reporting_conventions import VolumeConventionAudit, audit_volume_conventions


def _json_decimal(value: object) -> str:
    if isinstance(value, Decimal):
        return str(value)
    message = f"Unexpected non-JSON audit value: {type(value).__name__}"
    raise TypeError(message)


@dataclass(frozen=True, slots=True)
class RecordedPrintReview:
    """Print identity, independent parity and volume audits, without declaring acceptance."""

    model_print_id: str
    model_print_label: str
    native_column_id: str
    engine_profile: str
    printed_discharge_parity: PrintedParity
    native_reporting: VolumeConventionAudit
    numerical_acceptance: Literal["unassessed"] = "unassessed"

    def to_json(self) -> str:
        """Serialize Decimal results as exact strings; preserve original native labels."""
        return json.dumps(asdict(self), default=_json_decimal, indent=2, sort_keys=True, allow_nan=False) + "\n"


def review_recorded_print(
    result: RunResult,
    native_discharge_tokens: Sequence[str],
    *,
    model_print_id: str,
    native_column_id: str,
    engine_profile: str,
    raw_native_time_tokens: Sequence[str],
    native_reported_volume_text: str | None = None,
) -> RecordedPrintReview:
    """Review a caller-verified native print mapping against a typed S1/S2 calculation.

    Both matching native print IDs and exact engine provenance must be independently
    verified before use; this API cannot establish either from a report alone.

    Printed-discharge parity uses the existing frozen half-print-unit policy.
    Native inclusive-sum and physical-horizon volumes remain separate statistics.
    Raw native time tokens are retained, not shifted to match model elapsed time.
    No success here marks hydrological numerical acceptance.
    """
    if not engine_profile.strip():
        message = "An explicit, version-qualified engine profile must be supplied"
        error = RunInputError("invalid", "engine_profile", message)
        raise error
    if not native_column_id.strip():
        message = "An explicit native hydrograph column identity must be supplied"
        error = RunInputError("invalid", "native_column_id", message)
        raise error
    matching = tuple(item for item in result.prints if item.print_id == model_print_id)
    if len(matching) != 1:
        message = f"The model print ID {model_print_id!r} does not identify exactly one calculated site"
        error = RunInputError("invalid", "print_identity", message)
        raise error
    native_tokens = tuple(native_discharge_tokens)
    native_times = tuple(raw_native_time_tokens)
    if len(native_tokens) != len(matching[0].discharge_m3_s):
        message = "Native and model printed discharge sample counts differ"
        error = RunInputError("invalid", "print_count", message)
        raise error
    if len(native_times) != len(native_tokens):
        message = "Native time labels and discharge sample counts differ"
        error = RunInputError("invalid", "native_time_count", message)
        raise error
    if any(not time for time in native_times):
        message = "Raw native time labels cannot be empty"
        error = RunInputError("invalid", "native_time_label", message)
        raise error

    parity = assess_recorded_print(result, native_tokens, print_id=model_print_id)
    reporting = audit_volume_conventions(
        native_tokens,
        timestep_hours=Decimal(str(result.numerical.dt_hours)),
        native_reported_volume_text=native_reported_volume_text,
        raw_native_time_tokens=native_times,
    )
    return RecordedPrintReview(
        model_print_id=model_print_id,
        model_print_label=matching[0].label,
        native_column_id=native_column_id,
        engine_profile=engine_profile,
        printed_discharge_parity=parity,
        native_reporting=reporting,
    )
