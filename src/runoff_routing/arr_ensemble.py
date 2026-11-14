"""Auditable source-order ARR2019 ten-event rainfall ensembles.

This is an explicit-input preparation adapter, not a representative-event rule,
ARR2026 policy, RORB storm-file writer or native-equivalence claim.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Literal

from runoff_routing.arr_arf import AreaAdjustedHyetograph, ARFResult, apply_arr2019_arf_to_bom_storm
from runoff_routing.arr_data import ARRFormatError
from runoff_routing.arr_patterns import PatternSet
from runoff_routing.arr_selection import TP_SELECTION_POLICY, TemporalPatternSelection, select_arr2019_ensemble
from runoff_routing.arr_storm import RawHyetograph, storm_from_bom
from runoff_routing.bom_ifd import BoMIFD, BoMProbability

ENSEMBLE_LEDGER_VERSION = "arr2019-explicit-ensemble-v1"


@dataclass(frozen=True, slots=True)
class ExplicitARR2019Ensemble:
    """All ten original events, optionally with one already calculated ARF."""

    selection: TemporalPatternSelection
    bom_source_sha256: str
    probability_label: str
    gross_storms: tuple[RawHyetograph, ...]
    areal_storms: tuple[AreaAdjustedHyetograph, ...] | None
    operations: tuple[str, ...]
    hydrological_acceptance: Literal["not_assessed"] = "not_assessed"

    def __post_init__(self) -> None:
        if (
            self.selection.policy_version != TP_SELECTION_POLICY
            or len(self.gross_storms) != 10
            or tuple(storm.pattern_event_id for storm in self.gross_storms) != self.selection.event_ids
        ):
            msg = "ARR2019 ensemble must retain exactly ten selected events in original source order"
            raise ARRFormatError(msg)
        if any(
            storm.source_sha256 != self.bom_source_sha256
            or storm.pattern_source_sha256 != self.selection.source_sha256
            or storm.probability_label != self.probability_label
            for storm in self.gross_storms
        ):
            msg = "ARR2019 ensemble storm/source identity mismatch"
            raise ARRFormatError(msg)
        if self.areal_storms is not None and (
            len(self.areal_storms) != 10
            or any(
                adjusted.gross != gross
                for gross, adjusted in zip(self.gross_storms, self.areal_storms, strict=True)
            )
        ):
            msg = "ARR2019 areal storms must retain the corresponding original gross events"
            raise ARRFormatError(msg)

    @property
    def event_ids(self) -> tuple[str, ...]:
        """Exact original IDs, not engine-generated event ordinals."""
        return self.selection.event_ids


def build_explicit_arr2019_ensemble(
    bom: BoMIFD,
    probability: BoMProbability,
    pattern_source: PatternSet,
    selection: TemporalPatternSelection,
    *,
    arf: ARFResult | None = None,
) -> ExplicitARR2019Ensemble:
    """Generate all ten source-order gross storms, optionally applying an explicit ARF once.

    The caller must already have selected the regional source, catchment area,
    AEP, duration, and (if desired) coefficient profile. No event is ranked,
    dropped, adjusted for loss/preburst, filtered or routed.
    """
    if probability.kind != "AEP_PERCENT" or probability.value != selection.aep_percent:
        msg = "ARR2019 ensemble requires an exactly matching BoM percentage AEP, not EY/ARI/one-in-N"
        raise ARRFormatError(msg)
    if probability not in bom.probabilities:
        msg = "Selected BoM probability does not belong to supplied source bytes"
        raise ARRFormatError(msg)
    if selection.source_sha256 != pattern_source.source_sha256:
        msg = "ARR2019 temporal-pattern selection and original source SHA-256 differ"
        raise ARRFormatError(msg)
    expected = select_arr2019_ensemble(
        pattern_source,
        catchment_area_km2=selection.catchment_area_km2,
        duration_min=selection.duration_min,
        aep_percent=selection.aep_percent,
        region=selection.region,
    )
    if selection != expected:
        msg = "ARR2019 temporal-pattern selection differs from exact source-order policy result"
        raise ARRFormatError(msg)
    if arf is not None and (
        arf.area_km2 != selection.catchment_area_km2
        or arf.duration_min != selection.duration_min
        or arf.aep_percent != selection.aep_percent
    ):
        msg = "ARR2019 ARF area, duration and AEP must match the selected ensemble"
        raise ARRFormatError(msg)
    gross = tuple(storm_from_bom(bom, probability, pattern_source, event) for event in selection.patterns)
    areal = None if arf is None else tuple(apply_arr2019_arf_to_bom_storm(storm, arf) for storm in gross)
    return ExplicitARR2019Ensemble(
        selection=selection,
        bom_source_sha256=bom.sha256,
        probability_label=probability.label,
        gross_storms=gross,
        areal_storms=areal,
        operations=(
            "EXACT_SOURCE_ORDER_TEN_EVENT_IDS",
            "EXPLICIT_BOM_AEP_PERCENT_AND_DURATION",
            "EXPLICIT_ARR2019_ARF_ONCE" if arf is not None else "NO_ARF",
            "NO_REPRESENTATIVE_EVENT_NO_LOSSES_NO_PREBURST_NO_EMBEDDED_BURST_NO_ROUTING",
        ),
    )


def explicit_ensemble_inventory_json(ensemble: ExplicitARR2019Ensemble) -> str:
    """Emit every exact Decimal increment as a string, without output rounding or I/O."""
    events: list[dict[str, object]] = []
    for ordinal, storm in enumerate(ensemble.gross_storms, start=1):
        adjusted = None if ensemble.areal_storms is None else ensemble.areal_storms[ordinal - 1]
        events.append(
            {
                "source_order_ordinal_1_based": ordinal,
                "source_event_id": storm.pattern_event_id,
                "timestep_min": storm.timestep_min,
                "end_times_min": list(storm.end_times_min),
                "gross_increments_mm": [str(value) for value in storm.increments_mm],
                "gross_total_mm": str(storm.total_mm),
                "areal_increments_mm": (
                    None if adjusted is None else [str(value) for value in adjusted.increments_mm]
                ),
                "areal_total_mm": None if adjusted is None else str(adjusted.total_mm),
            }
        )
    selection = ensemble.selection
    arf = None if ensemble.areal_storms is None else ensemble.areal_storms[0].arf
    payload: dict[str, object] = {
        "schema_version": ENSEMBLE_LEDGER_VERSION,
        "hydrological_acceptance": ensemble.hydrological_acceptance,
        "representative_event": None,
        "selection": {
            "policy_version": selection.policy_version,
            "area_km2": str(selection.catchment_area_km2),
            "duration_min": selection.duration_min,
            "aep_percent": str(selection.aep_percent),
            "region": selection.region,
            "source_kind": selection.source_kind,
            "area_bin": selection.area_bin,
            "aep_band": selection.aep_band,
            "expected_count": selection.expected_count,
        },
        "sources": {
            "bom_sha256": ensemble.bom_source_sha256,
            "bom_probability_label": ensemble.probability_label,
            "temporal_pattern_sha256": selection.source_sha256,
        },
        "arf": (
            None
            if arf is None
            else {
                "policy_version": arf.policy_version,
                "factor": str(arf.factor),
                "region": arf.region,
                "coefficient_origin": arf.coefficient_origin,
                "coefficient_source_sha256": arf.coefficient_source_sha256,
                "method_steps": list(arf.method_steps),
            }
        ),
        "operations": list(ensemble.operations),
        "events": events,
    }
    return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
