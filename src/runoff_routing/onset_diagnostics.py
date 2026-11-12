"""Pure onset-relative audit of previously calculated and printed hydrographs.

This is *not* a numerical compatibility verdict or causal attribution. The
existing printed-precision evaluator is the only owner of mismatch thresholds.
Original native increment/time tokens remain verbatim and are never shifted.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal
from typing import Literal

from .offline_reference import OfflineComparison
from .parity_metrics import PrintedParity, assess_printed_parity

OnsetClass = Literal["within_print_budget", "at_onset", "next_sample", "later"]


@dataclass(frozen=True, slots=True)
class OnsetAudit:
    """First strict mismatch relative to *either* series' first nonzero sample."""

    case_id: str | None
    classification: OnsetClass
    first_native_nonzero_index: int | None
    first_predicted_nonzero_index: int | None
    first_any_nonzero_index: int | None
    first_outside_budget_index: int | None
    samples_from_onset: int | None
    first_mismatch_native_increment: str | None
    first_mismatch_native_time: str | None
    first_mismatch_native_discharge: str | None
    first_mismatch_predicted_m3_s: float | None
    first_mismatch_signed_error_m3_s: float | None
    printed_parity: PrintedParity


@dataclass(frozen=True, slots=True)
class OnsetCampaign:
    """Classification counts; passing source tests do not accept native parity."""

    total: int
    within_print_budget: int
    at_onset: int
    next_sample: int
    later: int


def _raw_labels(labels: Sequence[str] | None, count: int, name: str) -> tuple[str, ...] | None:
    if labels is None:
        return None
    result = tuple(labels)
    if len(result) != count or any(
        not isinstance(token, str) or not token or any(char in token for char in ("\x00", "\r", "\n"))
        for token in result
    ):
        message = f"{name} tokens must be nonempty original strings matching the sample grid"
        raise ValueError(message)
    return result


def audit_onset(
    predicted_m3_s: Sequence[float],
    native_discharge_tokens: Sequence[str],
    *,
    dt_hours: float,
    case_id: str | None = None,
    native_increment_tokens: Sequence[str] | None = None,
    native_time_tokens: Sequence[str] | None = None,
) -> OnsetAudit:
    """Describe *when* the first printed-budget failure occurs.

    A 0.0000 native sample and a tiny positive prediction can agree within
    its declared half-last-place print allowance, even though the prediction
    has a nonzero onset. This audit retains both onset indices and never
    substitutes an output-clock interpretation for the raw native labels.

    A mismatch on the first nonzero sample is not proof that rainfall, source
    timing or routing caused it. Independent source/individual-reach prints
    are required to attribute the first discrepancy to a computational stage.
    """
    if case_id is not None and (not case_id.strip() or case_id != case_id.strip()):
        message = "Case identifier must be nonempty without surrounding whitespace"
        raise ValueError(message)
    if (native_increment_tokens is None) != (native_time_tokens is None):
        message = "Native increment and time labels must be supplied together"
        raise ValueError(message)
    predicted = tuple(predicted_m3_s)
    tokens = tuple(native_discharge_tokens)
    parity = assess_printed_parity(predicted, tokens, dt_hours=dt_hours)
    increments = _raw_labels(native_increment_tokens, parity.sample_count, "Native increment")
    times = _raw_labels(native_time_tokens, parity.sample_count, "Native time")
    first_native = next((i for i, token in enumerate(tokens) if Decimal(token) > 0), None)
    first_predicted = next((i for i, value in enumerate(predicted) if value > 0), None)
    candidates = (i for i in (first_native, first_predicted) if i is not None)
    first_any = min(candidates, default=None)
    mismatch = parity.first_outside_budget_index
    if mismatch is None:
        classification: OnsetClass = "within_print_budget"
        offset: int | None = None
    else:
        if first_any is None or mismatch < first_any:
            message = "Nonzero discharge onset is inconsistent with the printed mismatch"
            raise ValueError(message)
        offset = mismatch - first_any
        if offset == 0:
            classification = "at_onset"
        elif offset == 1:
            classification = "next_sample"
        else:
            classification = "later"
    return OnsetAudit(
        case_id=case_id,
        classification=classification,
        first_native_nonzero_index=first_native,
        first_predicted_nonzero_index=first_predicted,
        first_any_nonzero_index=first_any,
        first_outside_budget_index=mismatch,
        samples_from_onset=offset,
        first_mismatch_native_increment=increments[mismatch]
        if increments is not None and mismatch is not None
        else None,
        first_mismatch_native_time=times[mismatch] if times is not None and mismatch is not None else None,
        first_mismatch_native_discharge=tokens[mismatch] if mismatch is not None else None,
        first_mismatch_predicted_m3_s=predicted[mismatch] if mismatch is not None else None,
        first_mismatch_signed_error_m3_s=(
            predicted[mismatch] - float(Decimal(tokens[mismatch])) if mismatch is not None else None
        ),
        printed_parity=parity,
    )


def audit_offline_comparison(comparison: OfflineComparison) -> OnsetAudit:
    """Adapt an already verified, complete CMD comparison; never read or rewrite files."""
    differences = comparison.differences
    if (
        comparison.status != "compared"
        or comparison.dt_hours is None
        or comparison.sample_count is None
        or not differences
        or comparison.sample_count != len(differences)
    ):
        message = "Onset audit requires a complete computed offline comparison"
        raise ValueError(message)
    if any(row.row != index for index, row in enumerate(differences)):
        message = "Offline comparison rows must preserve their original zero-based sample order"
        raise ValueError(message)
    return audit_onset(
        tuple(row.predicted_m3_s for row in differences),
        tuple(row.expected_token for row in differences),
        dt_hours=comparison.dt_hours,
        case_id=comparison.case_id,
        native_increment_tokens=tuple(row.raw_increment for row in differences),
        native_time_tokens=tuple(row.raw_time for row in differences),
    )


def summarize_onset_audits(audits: Sequence[OnsetAudit]) -> OnsetCampaign:
    """Aggregate complete comparisons; do not turn unsupported cases into passes."""
    records = tuple(audits)
    if not records:
        message = "At least one completed onset audit is required"
        raise ValueError(message)
    known_ids = [record.case_id for record in records if record.case_id is not None]
    if len(known_ids) != len(set(known_ids)):
        message = "Duplicate case identity in onset audit campaign"
        raise ValueError(message)
    counts = Counter(record.classification for record in records)
    return OnsetCampaign(
        total=len(records),
        within_print_budget=counts["within_print_budget"],
        at_onset=counts["at_onset"],
        next_sample=counts["next_sample"],
        later=counts["later"],
    )
