"""Independent ARR2019 temporal-pattern selection tests with synthetic public fixtures."""

from __future__ import annotations

from decimal import Decimal

import pytest

from runoff_routing.arr_data import ARRFormatError
from runoff_routing.arr_patterns import PatternSet, parse_pattern_csv
from runoff_routing.arr_selection import TP_SELECTION_POLICY, select_arr2019_ensemble

REGION = "SYNTHETIC REGION"


def _point() -> PatternSet:
    rows = ["EventID,Duration,TimeStep,Region,AEP,Increments"]
    for band in ("frequent", "intermediate", "rare"):
        rows.extend(f"{band}{ordinal:02d},60,15,{REGION},{band},10,20,30,40" for ordinal in range(10))
    return parse_pattern_csv(("\n".join(rows) + "\n").encode(), kind="point")


def _areal(*, omit_aep: bool = True, count: int = 10, bin_label: str = "100") -> PatternSet:
    header = "EventID,Duration,TimeStep,Region,Area,Increments"
    if not omit_aep:
        header = "EventID,Duration,TimeStep,Region,Area,AEP,Increments"
    rows = [header]
    for ordinal in range(count):
        parts = [f"T{ordinal:03d}", "720", "180", REGION, bin_label]
        if not omit_aep:
            parts.append("rare")
        rows.append(",".join([*parts, "10", "20", "30", "40"]))
    return parse_pattern_csv(("\n".join(rows) + "\n").encode(), kind="areal")


@pytest.mark.parametrize(
    ("area", "expected_bin"),
    [
        ("0.1", None),
        ("74.999", None),
        ("75", "100"),
        ("139.999", "100"),
        ("140", "200"),
        ("299.999", "200"),
        ("300", "500"),
        ("699.999", "500"),
        ("700", "1000"),
        ("1599.999", "1000"),
        ("1600", "2500"),
        ("3499.999", "2500"),
        ("3500", "5000"),
        ("6999.999", "5000"),
        ("7000", "10000"),
        ("13999.999", "10000"),
        ("14000", "20000"),
        ("27999.999", "20000"),
        ("28000", "40000"),
        ("30000", "40000"),
    ],
)
def test_area_band_boundaries_fail_instead_of_using_nearest(area: str, expected_bin: str | None) -> None:
    if expected_bin is None:
        src = _point()
        duration = 60
    else:
        src = _areal(bin_label=expected_bin)
        duration = 720
    selection = select_arr2019_ensemble(
        src, catchment_area_km2=Decimal(area), duration_min=duration, aep_percent=Decimal(1), region=REGION
    )
    assert selection.area_bin == expected_bin
    assert selection.policy_version == TP_SELECTION_POLICY
    assert selection.source_kind == ("point" if expected_bin is None else "areal")
    assert len(selection.patterns) == 10


@pytest.mark.parametrize(
    ("aep", "band"),
    [
        ("50", "frequent"),
        ("20", "frequent"),
        ("10", "intermediate"),
        ("5", "intermediate"),
        ("2", "rare"),
        ("1", "rare"),
    ],
)
def test_exact_aep_band_and_source_order(aep: str, band: str) -> None:
    source = _point()
    selection = select_arr2019_ensemble(
        source,
        catchment_area_km2=Decimal(25),
        duration_min=60,
        aep_percent=Decimal(aep),
        region=REGION,
    )
    assert selection.source_sha256 == source.source_sha256
    assert selection.aep_band == band
    assert selection.event_ids == tuple(f"{band}{ordinal:02d}" for ordinal in range(10))
    assert all(pattern.aep_band == band for pattern in selection.patterns)


def test_missing_areal_aep_is_preserved_not_inferred() -> None:
    source = _areal()
    selected = select_arr2019_ensemble(
        source, catchment_area_km2=Decimal(100), duration_min=720, aep_percent=Decimal(1), region=REGION
    )
    assert selected.aep_band is None
    assert selected.event_ids == tuple(f"T{n:03d}" for n in range(10))


def test_present_areal_aep_must_match_requested_band() -> None:
    source = _areal(omit_aep=False)
    selected = select_arr2019_ensemble(
        source, catchment_area_km2=Decimal(100), duration_min=720, aep_percent=Decimal(2), region=REGION
    )
    assert selected.aep_band == "rare"
    with pytest.raises(ARRFormatError, match="Expected 10"):
        select_arr2019_ensemble(
            source, catchment_area_km2=Decimal(100), duration_min=720, aep_percent=Decimal(10), region=REGION
        )


def test_incomplete_ensemble_is_not_silently_filled() -> None:
    with pytest.raises(ARRFormatError, match="got 1"):
        select_arr2019_ensemble(
            _areal(count=1),
            catchment_area_km2=Decimal(100),
            duration_min=720,
            aep_percent=Decimal(1),
            region=REGION,
        )


@pytest.mark.parametrize("aep", [Decimal("63.2"), Decimal("0.5"), Decimal("0.2"), Decimal("NaN")])
def test_uncharacterised_aep_conversions_rejected(aep: Decimal) -> None:
    with pytest.raises(ARRFormatError, match=r"frequency selection|finite Decimal"):
        select_arr2019_ensemble(
            _point(), catchment_area_km2=Decimal(50), duration_min=60, aep_percent=aep, region=REGION
        )


@pytest.mark.parametrize("area", [Decimal(-1), Decimal(0), Decimal("NaN"), Decimal("Infinity")])
def test_impossible_areas_rejected(area: Decimal) -> None:
    with pytest.raises(ARRFormatError, match="positive finite"):
        select_arr2019_ensemble(
            _point(), catchment_area_km2=area, duration_min=60, aep_percent=Decimal(1), region=REGION
        )


def test_source_region_duration_and_kind_must_match() -> None:
    with pytest.raises(ARRFormatError, match="requires point"):
        select_arr2019_ensemble(
            _areal(), region=REGION, catchment_area_km2=Decimal(50), duration_min=60, aep_percent=Decimal(1)
        )
    with pytest.raises(ARRFormatError, match="requires areal"):
        select_arr2019_ensemble(
            _point(), region=REGION, catchment_area_km2=Decimal(75), duration_min=60, aep_percent=Decimal(1)
        )
    with pytest.raises(ARRFormatError, match="got 0"):
        select_arr2019_ensemble(
            _point(), region="OTHER REGION", catchment_area_km2=Decimal(50), duration_min=60, aep_percent=Decimal(1)
        )
    with pytest.raises(ARRFormatError, match="got 0"):
        select_arr2019_ensemble(
            _point(), region=REGION, catchment_area_km2=Decimal(50), duration_min=180, aep_percent=Decimal(1)
        )


@pytest.mark.parametrize("override", [0, 1, 9, 11, 20, True])
def test_expected_count_cannot_override_ten_member_policy(override: int) -> None:
    """Allowing expected_count=1 would otherwise accept a partial regional ensemble."""
    with pytest.raises(ARRFormatError, match="exactly ten"):
        select_arr2019_ensemble(
            _areal(count=1),
            catchment_area_km2=Decimal(100),
            duration_min=720,
            aep_percent=Decimal(1),
            region=REGION,
            expected_count=override,
        )


def test_selection_rejects_out_of_range_duration_even_when_source_is_valid() -> None:
    with pytest.raises(ARRFormatError, match=r"1\.\.10080"):
        select_arr2019_ensemble(
            _point(), catchment_area_km2=Decimal(50), duration_min=10081, aep_percent=Decimal(1), region=REGION
        )
