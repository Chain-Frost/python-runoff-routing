"""ARR2019 ARF numerical reference and application safety, independent of RORB."""

from __future__ import annotations

import math
from decimal import Decimal
from pathlib import Path

import pytest

from runoff_routing.arr_arf import (
    ARF_POLICY_VERSION,
    apply_arr2019_arf_to_bom_storm,
    calculate_arr2019_arf,
    legacy_datahub_coefficients,
    published_coefficients,
)
from runoff_routing.arr_data import ARRFormatError
from runoff_routing.arr_import import parse_arr_txt
from runoff_routing.arr_patterns import parse_pattern_csv
from runoff_routing.arr_storm import storm_from_bom
from runoff_routing.bom_ifd import parse_bom_ifd_csv


def _arf(area: str, duration: int, aep: str = "1", region: str = "East Coast North") -> Decimal:
    return calculate_arr2019_arf(
        catchment_area_km2=Decimal(area),
        duration_min=duration,
        aep_percent=Decimal(aep),
        coefficients=published_coefficients(region),
    ).factor


def _independent_short(area: float, duration: float, aep_percent: float) -> float:
    p = 0.3 + math.log10(aep_percent / 100)
    raw = (
        1
        - 0.287 * (area**0.265 - 0.439 * math.log10(duration)) * duration**-0.36
        + 0.00226 * area**0.226 * duration**0.125 * p
        + 0.0141 * area**0.213 * 10 ** (-0.021 * (duration - 180) ** 2 / 1440) * p
    )
    return min(1, raw)


def _independent_long(area: float, duration: float, aep_percent: float, region: str) -> float:
    a, b, c, d, e, f, g, h, i = (float(x) for x in published_coefficients(region).values)
    p = 0.3 + math.log10(aep_percent / 100)
    return min(
        1,
        1
        - a * (area**b - c * math.log10(duration)) * duration**-d
        + e * area**f * duration**g * p
        + h * 10 ** (i * area * duration / 1440) * p,
    )


def test_published_coefficients_and_independent_reference_provenance() -> None:
    assert published_coefficients("Inland Arid").values[6] == Decimal("0.129")
    assert published_coefficients("South-West Western Australia").values[4] == Decimal("3.85E-06")
    with pytest.raises(ARRFormatError, match="Unknown ARR2019 ARF region"):
        published_coefficients("FLTwest")


def test_official_2019_book2_worked_example() -> None:
    result = calculate_arr2019_arf(
        catchment_area_km2=Decimal("245.07"),
        duration_min=1440,
        aep_percent=Decimal(1),
        coefficients=published_coefficients("East Coast North"),
    )
    assert result.policy_version == ARF_POLICY_VERSION
    assert abs(result.factor - Decimal("0.929")) < Decimal("0.0005")
    assert result.method_steps == ("LONG_DURATION_EQ_2_4_2",)
    assert result.coefficient_origin == "arr2019_book2_table_2_4_2"


@pytest.mark.parametrize("area", [10, 25, 100, 1000])
@pytest.mark.parametrize("duration", [30, 60, 180, 360, 720])
def test_short_duration_equation_against_independent_float_expression(area: int, duration: int) -> None:
    expected = _independent_short(area, duration, 1)
    # The analytical equation can yield negative values outside its physical bounds;
    # tests use only positive cases here (negative policy is checked separately).
    if expected < 0:
        with pytest.raises(ARRFormatError, match="Negative ARF"):
            _arf(str(area), duration)
    else:
        assert abs(float(_arf(str(area), duration)) - expected) < 1e-11


@pytest.mark.parametrize("area", [10, 100, 1000, 30000])
@pytest.mark.parametrize("duration", [1440, 2880, 10080])
def test_long_duration_equation_against_independent_float_expression(area: int, duration: int) -> None:
    expected = _independent_long(area, duration, 1, "South-West Western Australia")
    if expected < 0:
        with pytest.raises(ARRFormatError, match="Negative ARF"):
            _arf(str(area), duration, region="South-West Western Australia")
    else:
        assert abs(float(_arf(str(area), duration, region="South-West Western Australia")) - expected) < 1e-11


@pytest.mark.parametrize("area", [2, 5, 9])
@pytest.mark.parametrize("duration", [60, 720, 1080, 1440, 2880])
def test_small_area_interpolation_formula(area: int, duration: int) -> None:
    if duration <= 720 or duration >= 1440:
        endpoint = _arf("10", duration)
    else:
        endpoint = _arf("10", 720) + (_arf("10", 1440) - _arf("10", 720)) * Decimal("0.5")
    expected = 1 - 0.6614 * (1 - float(endpoint)) * (area**0.4 - 1)
    assert abs(float(_arf(str(area), duration)) - expected) < 1e-11


def test_duration_interpolation_and_large_area_annotation() -> None:
    start, end = _arf("100", 720), _arf("100", 1440)
    assert abs(_arf("100", 1080) - (start + end) / 2) < Decimal("1e-20")
    big = calculate_arr2019_arf(
        catchment_area_km2=Decimal(1500),
        duration_min=1080,
        aep_percent=Decimal(1),
        coefficients=published_coefficients("South-West Western Australia"),
    )
    assert "SHORT_ENDPOINT_EXTRAPOLATION_GT_1000_KM2_AS_ARR2019_RECOMMENDS" in big.method_steps


@pytest.mark.parametrize("area", ["0.01", "1"])
@pytest.mark.parametrize("duration", [60, 720, 1080, 1440, 10080])
def test_small_area_unity_for_all_duration_branches(area: str, duration: int) -> None:
    result = calculate_arr2019_arf(catchment_area_km2=Decimal(area), duration_min=duration, aep_percent=Decimal(1))
    assert result.factor == 1
    assert result.method_steps == ("SMALL_AREA_UNITY",)


def test_validity_gates_fail_closed() -> None:
    with pytest.raises(ARRFormatError, match=r"in \(0, 30000\]"):
        _arf("30001", 1440)
    with pytest.raises(ARRFormatError, match="inapplicable"):
        _arf("1001", 720)
    with pytest.raises(ARRFormatError, match="regional coefficients"):
        calculate_arr2019_arf(catchment_area_km2=Decimal(10), duration_min=1440, aep_percent=Decimal(1))
    with pytest.raises(ARRFormatError, match="below 30 minutes"):
        _arf("10", 5)
    with pytest.raises(ARRFormatError, match="requires an AEP percentage"):
        _arf("10", 60, aep="63.2")
    with pytest.raises(ARRFormatError, match="extrapolation below 1%"):
        _arf("10", 60, aep="0.5")
    with pytest.raises(ARRFormatError, match=r"in \(0, 30000\]"):
        _arf("NaN", 60)
    with pytest.raises(ARRFormatError, match="duration must be"):
        _arf("10", 10081)
    with pytest.raises(ARRFormatError, match="duration must be"):
        _arf("10", True)


def test_opt_in_extended_range_and_original_source_not_rounded() -> None:
    result = calculate_arr2019_arf(
        catchment_area_km2=Decimal(25),
        duration_min=15,
        aep_percent=Decimal("0.5"),
        allow_short_extrapolation=True,
        allow_rare_aep_extension=True,
    )
    assert 0 < result.factor < 1
    assert "DURATION_LT_30_MIN_EXTRAPOLATION_OPT_IN" in result.method_steps
    assert "AEP_LT_1_PERCENT_EXTENSION_OPT_IN" in result.method_steps
    assert result.region is None


def test_gross_bom_rainfall_is_arf_reduced_once() -> None:
    raw = b"IFD Design Rainfall Depth (mm)\nDuration,Duration in min,1%\n24 hour,1440,129\n"
    source = parse_bom_ifd_csv(raw)
    csv = b"EventID,Duration,TimeStep,Region,AEP,Increments\n0007,1440,360,TEST,rare,10,20,30,40\n"
    patterns = parse_pattern_csv(csv, kind="point")
    gross = storm_from_bom(source, source.probability("1%"), patterns, patterns.patterns[0])
    arf = calculate_arr2019_arf(
        catchment_area_km2=Decimal(50),
        duration_min=1440,
        aep_percent=Decimal(1),
        coefficients=published_coefficients("South-West Western Australia"),
    )
    adjusted = apply_arr2019_arf_to_bom_storm(gross, arf)
    assert gross.total_mm == 129
    assert adjusted.total_mm == Decimal(129) * arf.factor
    assert adjusted.increments_mm == tuple(x * arf.factor for x in gross.increments_mm)
    assert adjusted.operations[-1] == "ARF_APPLIED_ONCE_TO_GROSS_BOM_RAINFALL"
    assert adjusted.gross is gross  # Output keeps the unadjusted source separately.


def test_wrong_probability_and_duration_do_not_apply_arf() -> None:
    raw = b"IFD Design Rainfall Depth (mm)\nDuration,Duration in min,1%\n24 hour,1440,129\n"
    source = parse_bom_ifd_csv(raw)
    patterns = parse_pattern_csv(
        b"EventID,Duration,TimeStep,Region,AEP,Increments\n1,1440,720,X,rare,50,50\n", kind="point"
    )
    gross = storm_from_bom(source, source.probability("1%"), patterns, patterns.patterns[0])
    with pytest.raises(ARRFormatError, match="AEP percentages differ"):
        apply_arr2019_arf_to_bom_storm(
            gross, calculate_arr2019_arf(catchment_area_km2=Decimal(1), duration_min=1440, aep_percent=Decimal(2))
        )
    with pytest.raises(ARRFormatError, match="duration differ"):
        apply_arr2019_arf_to_bom_storm(
            gross, calculate_arr2019_arf(catchment_area_km2=Decimal(1), duration_min=720, aep_percent=Decimal(1))
        )


def test_legacy_datahub_arfs_keep_original_coefficient_precision_and_source_hash() -> None:
    """2016-era Data Hub coefficients are not automatically replaced by 2019 table values."""
    source = Path(__file__).absolute().parent / "fixtures" / "arr" / "2016-era-synthetic.txt"
    doc = parse_arr_txt(source.read_bytes(), legacy_profile="arr2016")
    params = legacy_datahub_coefficients(doc)
    assert params.region == "Invented Zone"
    assert params.source_sha256 == doc.source.sha256
    assert params.values[4] == Decimal("0.00012")
    assert params.values[8] == Decimal("-0.0003")
    assert params.origin == "legacy_datahub"
    result = calculate_arr2019_arf(
        catchment_area_km2=Decimal(100), duration_min=1440, aep_percent=Decimal(1), coefficients=params
    )
    assert result.coefficient_origin == "legacy_datahub"
    assert result.coefficient_source_sha256 == doc.source.sha256
