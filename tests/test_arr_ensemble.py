"""Synthetic source-order S6 event-ledger tests; no native hydrology claim."""

from __future__ import annotations

import json
from dataclasses import FrozenInstanceError, replace
from decimal import Decimal

import pytest

from runoff_routing.arr_arf import calculate_arr2019_arf
from runoff_routing.arr_data import ARRFormatError
from runoff_routing.arr_ensemble import (
    ENSEMBLE_LEDGER_VERSION,
    build_explicit_arr2019_ensemble,
    explicit_ensemble_inventory_json,
)
from runoff_routing.arr_patterns import PatternSet, parse_pattern_csv
from runoff_routing.arr_selection import TemporalPatternSelection, select_arr2019_ensemble
from runoff_routing.bom_ifd import BoMIFD, parse_bom_ifd_csv

REGION = "SYNTHETIC REGION"


def _bom(*, probability: str = "1%") -> BoMIFD:
    return parse_bom_ifd_csv(
        (
            "Copyright Commonwealth of Australia 2016\n"
            "IFD Design Rainfall Depth (mm)\n"
            "Requested coordinate:,Latitude,-30.000,Longitude,150.100\n"
            f"Duration,Duration in min,{probability},2%\n"
            "1 hour,60,100,110\n"
        ).encode()
    )


def _patterns(*, areal: bool = False, last_percent: str = "40") -> PatternSet:
    head = (
        "EventID,Duration,TimeStep,Region,Area,Increments"
        if areal
        else "EventID,Duration,TimeStep,Region,AEP,Increments"
    )
    rows = [head]
    for ordinal in range(1, 11):
        field = "100" if areal else "rare"
        rows.append(f"{ordinal:04d},60,15,{REGION},{field},10,20,30,{last_percent}")
    return parse_pattern_csv(
        ("\n".join(rows) + "\n").encode(),
        kind="areal" if areal else "point",
        rounding_budget_percent=Decimal("0.05") if last_percent != "40" else Decimal(0),
    )


def _selection(patterns: PatternSet, *, areal: bool = False) -> TemporalPatternSelection:
    return select_arr2019_ensemble(
        patterns,
        catchment_area_km2=Decimal(100 if areal else 50),
        duration_min=60,
        aep_percent=Decimal(1),
        region=REGION,
    )


def test_all_ten_original_event_ids_and_exact_gross_ordinates_retained() -> None:
    bom = _bom()
    patterns = _patterns()
    selection = _selection(patterns)
    ensemble = build_explicit_arr2019_ensemble(bom, bom.probability("1%"), patterns, selection)
    assert ensemble.event_ids == tuple(f"{ordinal:04d}" for ordinal in range(1, 11))
    assert all(
        storm.increments_mm == (Decimal(10), Decimal(20), Decimal(30), Decimal(40))
        for storm in ensemble.gross_storms
    )
    assert all(storm.end_times_min == (15, 30, 45, 60) for storm in ensemble.gross_storms)
    assert ensemble.areal_storms is None
    assert ensemble.hydrological_acceptance == "not_assessed"
    record = json.loads(explicit_ensemble_inventory_json(ensemble))
    assert record["schema_version"] == ENSEMBLE_LEDGER_VERSION
    assert record["representative_event"] is None
    assert record["sources"]["bom_sha256"] == bom.sha256
    assert record["sources"]["temporal_pattern_sha256"] == patterns.source_sha256
    assert len(record["events"]) == 10
    assert record["events"][0]["source_order_ordinal_1_based"] == 1
    assert record["events"][0]["source_event_id"] == "0001"
    assert record["events"][0]["gross_increments_mm"] == ["10", "20", "30", "40"]
    assert record["events"][0]["areal_increments_mm"] is None
    assert record["operations"][-1] == "NO_REPRESENTATIVE_EVENT_NO_LOSSES_NO_PREBURST_NO_EMBEDDED_BURST_NO_ROUTING"
    attribute = "probability_label"
    with pytest.raises(FrozenInstanceError):
        setattr(ensemble, attribute, "2%")


def test_areal_source_keeps_missing_aep_and_applies_explicit_arf_once() -> None:
    bom = _bom()
    patterns = _patterns(areal=True)
    selection = _selection(patterns, areal=True)
    arf = calculate_arr2019_arf(
        catchment_area_km2=Decimal(100), duration_min=60, aep_percent=Decimal(1)
    )
    ensemble = build_explicit_arr2019_ensemble(bom, bom.probability("1%"), patterns, selection, arf=arf)
    assert ensemble.selection.aep_band is None
    assert ensemble.areal_storms is not None
    assert len(ensemble.areal_storms) == 10
    assert all(item.gross.pattern_event_id == f"{i:04d}" for i, item in enumerate(ensemble.areal_storms, 1))
    assert all(item.total_mm == sum(item.increments_mm) for item in ensemble.areal_storms)
    assert all(item.total_mm == item.gross.total_mm * arf.factor for item in ensemble.areal_storms)
    record = json.loads(explicit_ensemble_inventory_json(ensemble))
    assert record["selection"]["aep_band"] is None
    assert record["selection"]["area_bin"] == "100"
    assert record["arf"]["factor"] == str(arf.factor)
    assert record["events"][9]["source_event_id"] == "0010"
    assert record["events"][0]["areal_total_mm"] == str(ensemble.areal_storms[0].total_mm)


def test_source_and_selection_order_cannot_be_swapped_or_forged() -> None:
    bom = _bom()
    patterns = _patterns()
    selection = _selection(patterns)
    alternate = parse_pattern_csv(
        patterns.raw_bytes.replace(b"0001", b"0099", 1), kind="point"
    )
    with pytest.raises(ARRFormatError, match="SHA-256"):
        build_explicit_arr2019_ensemble(bom, bom.probability("1%"), alternate, selection)
    with pytest.raises(ARRFormatError, match="source-order policy"):
        build_explicit_arr2019_ensemble(
            bom, bom.probability("1%"), patterns, replace(selection, patterns=tuple(reversed(selection.patterns)))
        )
    with pytest.raises(ARRFormatError, match="source order"):
        replace(
            build_explicit_arr2019_ensemble(bom, bom.probability("1%"), patterns, selection),
            gross_storms=tuple(reversed(build_explicit_arr2019_ensemble(
                bom, bom.probability("1%"), patterns, selection
            ).gross_storms)),
        )


def test_probability_and_arf_mismatch_fail_without_hidden_conversion() -> None:
    bom = _bom()
    patterns = _patterns()
    selection = _selection(patterns)
    with pytest.raises(ARRFormatError, match="matching BoM percentage AEP"):
        build_explicit_arr2019_ensemble(bom, bom.probability("2%"), patterns, selection)
    with pytest.raises(ARRFormatError, match="does not belong"):
        build_explicit_arr2019_ensemble(_bom(probability="5%"), bom.probability("1%"), patterns, selection)
    arf = calculate_arr2019_arf(catchment_area_km2=Decimal(100), duration_min=60, aep_percent=Decimal(1))
    with pytest.raises(ARRFormatError, match="ARF area"):
        build_explicit_arr2019_ensemble(bom, bom.probability("1%"), patterns, selection, arf=arf)
    with pytest.raises(ARRFormatError, match="ARF area"):
        build_explicit_arr2019_ensemble(
            bom, bom.probability("1%"), patterns, selection, arf=replace(arf, duration_min=120)
        )


def test_near_100_percent_pattern_is_not_silently_normalised() -> None:
    bom = _bom()
    patterns = _patterns(last_percent="39.99")
    selection = _selection(patterns)
    with pytest.raises(ARRFormatError, match="exactly 100%"):
        build_explicit_arr2019_ensemble(bom, bom.probability("1%"), patterns, selection)
