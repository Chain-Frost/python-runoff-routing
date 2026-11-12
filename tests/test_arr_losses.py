"""Synthetic-only preburst/loss policies; no RORB executable or hydrological parity."""

from dataclasses import FrozenInstanceError, replace
from typing import Literal
from decimal import Decimal
from pathlib import Path

import pytest

from runoff_routing.arr_data import ARRFormatError
from runoff_routing.arr_import import parse_arr_txt
from runoff_routing.arr_losses import (
    LOSS_POLICY_VERSION,
    LossMethod,
    PreburstLossSelection,
    calculate_burst_only_excess,
    prepend_explicit_preburst,
    select_legacy_preburst_loss,
)
from runoff_routing.arr_storm import RawHyetograph

FIXTURES = Path(__file__).absolute().parent / "fixtures" / "arr"


def _document() -> bytes:
    return (FIXTURES / "2016-era-synthetic.txt").read_bytes()


def _selection(*, method: LossMethod = "burst_only_reduced_il") -> PreburstLossSelection:
    document = parse_arr_txt(_document(), legacy_profile="arr2016")
    return select_legacy_preburst_loss(
        document, duration_min=60, aep_percent=Decimal(1), percentile=50, method=method
    )


def _event(*, aep: str = "1%", duration_min: int = 60, label: str = "BoM 2016 IFD (raw gross rainfall)") -> RawHyetograph:
    return RawHyetograph(
        duration_min=duration_min,
        timestep_min=30,
        pattern_event_id="synthetic-101",
        pattern_region="Synthetic only",
        pattern_aep_band="rare",
        pattern_area_bin=None,
        source_label=label,
        source_sha256="synthetic-bom-sha256",
        pattern_source_sha256="synthetic-tp-sha256",
        probability_label=aep,
        source_rainfall_depth_mm=Decimal(100),
        increments_mm=(Decimal(10), Decimal(90)),
        end_times_min=(30, 60),
        total_mm=Decimal(100),
        operations=("DEPTH_MM_AS_EXPORTED",),
    )


def test_median_preburst_selected_by_exact_duration_and_aep() -> None:
    result = _selection()
    assert result.policy_version == LOSS_POLICY_VERSION
    assert result.method == "burst_only_reduced_il"
    assert result.source_profile == "arr2016_txt"
    assert result.preburst_percentile == 50
    assert result.source_preburst_tag == "PREBURST"
    assert result.preburst_depth_mm == Decimal("7.00")
    assert result.preburst_ratio == Decimal("1.020")
    assert result.storm_initial_loss_mm == Decimal("21.0")
    assert result.continuing_loss_mm_per_hour == Decimal("2.00")
    assert result.burst_initial_loss_mm == Decimal("14.00")
    assert result.preburst_above_storm_il_mm == 0
    assert result.source_sha256
    assert ("Version", "2018_v1") in result.source_preburst_metadata
    assert ("Version", "2016_v1") in result.source_loss_metadata
    with pytest.raises(FrozenInstanceError):
        setattr(result, "burst_initial_loss_mm", Decimal(0))


@pytest.mark.parametrize("percentile", [10, 25, 50, 75, 90])
def test_all_preburst_percentiles_have_distinct_source_identity(
    percentile: Literal[10, 25, 50, 75, 90],
) -> None:
    doc = parse_arr_txt(_document(), legacy_profile="arr2016")
    result = select_legacy_preburst_loss(doc, duration_min=60, aep_percent=Decimal(50), percentile=percentile)
    assert result.source_preburst_tag == ("PREBURST" if percentile == 50 else f"PREBURST{percentile}")
    assert result.preburst_percentile == percentile


@pytest.mark.parametrize(
    ("duration", "aep"),
    [(90, Decimal(1)), (60, Decimal(2)), (1440, Decimal(1)), (0, Decimal(1)), (60, Decimal("NaN"))],
)
def test_missing_or_invalid_exact_axis_fails_closed(duration: int, aep: Decimal) -> None:
    doc = parse_arr_txt(_document(), legacy_profile="arr2016")
    with pytest.raises(ARRFormatError, match="missing|duration|AEP"):
        select_legacy_preburst_loss(doc, duration_min=duration, aep_percent=aep)


def test_excess_preburst_requires_operator_review_and_never_negative_il() -> None:
    old = b"60 (1.0),2.0 (0.010),7.00 (1.020),"
    new = b"60 (1.0),2.0 (0.010),40.00 (1.020),"
    changed = _document().replace(old, new, 1)
    doc = parse_arr_txt(changed, legacy_profile="arr2016")
    with pytest.raises(ARRFormatError, match="Preburst exceeds"):
        select_legacy_preburst_loss(doc, duration_min=60, aep_percent=Decimal(1))
    result = select_legacy_preburst_loss(
        doc, duration_min=60, aep_percent=Decimal(1), excess_policy="clamp_burst_il_to_zero"
    )
    assert result.preburst_depth_mm == 40
    assert result.preburst_above_storm_il_mm == 19
    assert result.burst_initial_loss_mm == 0
    assert any("CLAMPED_EXPLICITLY" in step for step in result.operations)
    explicit = select_legacy_preburst_loss(doc, duration_min=60, aep_percent=Decimal(1), method="explicit_preburst")
    assert explicit.burst_initial_loss_mm is None
    assert explicit.storm_initial_loss_mm == 21
    assert explicit.preburst_depth_mm == 40


def test_missing_storm_loss_sentinel_does_not_default_zero() -> None:
    changed = _document().replace(b"Storm Initial Losses (mm),21.0", b"Storm Initial Losses (mm),-50")
    doc = parse_arr_txt(changed, legacy_profile="arr2016")
    with pytest.raises(ARRFormatError, match="required"):
        select_legacy_preburst_loss(doc, duration_min=60, aep_percent=Decimal(1))


def test_legacy_only_does_not_accept_modern_arr_without_conversion() -> None:
    modern = parse_arr_txt((FIXTURES / "2026v1-minimal.txt").read_bytes())
    with pytest.raises(ARRFormatError, match="legacy ARR2016"):
        select_legacy_preburst_loss(modern, duration_min=60, aep_percent=Decimal(1))


def test_burst_only_loss_arithmetic_has_exact_water_balance() -> None:
    selection = _selection()
    event = _event()
    result = calculate_burst_only_excess(event, selection)
    assert result.applied_initial_loss_mm == 14
    assert result.excess_increments_mm[0] == 0
    assert result.excess_increments_mm[1] > 85
    assert result.applied_continuing_loss_mm > 0
    assert result.rainfall_total_mm == 100
    assert result.excess_total_mm + result.applied_initial_loss_mm + result.applied_continuing_loss_mm == 100
    assert result.hydrological_acceptance == "not_assessed"
    assert "NO_RORBWIN_LOSS_ENGINE_OR_RUNOFF_PARITY" in result.operations


def test_wet_dry_partial_step_loss_accounting() -> None:
    selection = _selection()
    event = replace(_event(), increments_mm=(Decimal(0), Decimal(100)), total_mm=Decimal(100))
    result = calculate_burst_only_excess(event, selection)
    assert result.applied_initial_loss_mm == 14
    assert result.applied_continuing_loss_mm == Decimal("0.86")
    assert result.excess_increments_mm == (Decimal(0), Decimal("85.14"))
    assert sum(result.excess_increments_mm) + result.applied_initial_loss_mm + result.applied_continuing_loss_mm == 100


def test_explicit_preburst_never_silently_uses_burst_only_losses() -> None:
    selection = _selection(method="explicit_preburst")
    assert selection.burst_initial_loss_mm is None
    with pytest.raises(ARRFormatError, match="cannot consume explicit-preburst"):
        calculate_burst_only_excess(_event(), selection)
    added = prepend_explicit_preburst(
        _event(), selection, percentages=(Decimal(25), Decimal(75)), declared_profile_id="synthetic-example"
    )
    assert added.preburst_increments_mm == (Decimal("1.75"), Decimal("5.25"))
    assert added.preburst_end_times_min == (-30, 0)
    assert added.combined_gross_increments_mm == (Decimal("1.75"), Decimal("5.25"), 10, 90)
    assert added.combined_gross_total_mm == 107
    assert added.hydrological_acceptance == "not_assessed"
    assert "NO_RORBWIN_PREBURST_PROFILE_PARITY_CLAIM" in added.operations


@pytest.mark.parametrize(
    "percentages",
    [(), (Decimal(50),), (Decimal(-1), Decimal(101)), (Decimal("NaN"), Decimal(100)), (Decimal(0), Decimal(101))],
)
def test_missing_malformed_preburst_profile_rejected(percentages: tuple[Decimal, ...]) -> None:
    with pytest.raises(ARRFormatError, match="empty|total|Invalid"):
        prepend_explicit_preburst(
            _event(), _selection(method="explicit_preburst"), percentages=percentages, declared_profile_id="test"
        )


@pytest.mark.parametrize("aep", ["2%", "2EY", "1 in 100", "NaN%", "garbled"])
def test_ensemble_probability_mismatch_rejected(aep: str) -> None:
    with pytest.raises(ARRFormatError, match="AEP|percentage|Unparseable"):
        calculate_burst_only_excess(_event(aep=aep), _selection())


def test_duration_and_source_type_mismatch_fail() -> None:
    with pytest.raises(ARRFormatError, match="duration"):
        calculate_burst_only_excess(_event(duration_min=120), _selection())
    with pytest.raises(ARRFormatError, match="BoM IFD"):
        calculate_burst_only_excess(_event(label="ARR 2026 current-adjusted"), _selection())


def test_no_implicit_preburst_pattern_or_hidden_source_identity() -> None:
    with pytest.raises(ARRFormatError, match="source ID"):
        prepend_explicit_preburst(
            _event(), _selection(method="explicit_preburst"), percentages=(Decimal(100),), declared_profile_id=""
        )
    assert _selection().source_sha256 == parse_arr_txt(_document(), legacy_profile="arr2016").source.sha256


def test_exact_bom_arr_requested_coordinates_and_raw_hash_are_verified() -> None:
    from runoff_routing.arr_losses import verify_legacy_bom_source_point
    from runoff_routing.bom_ifd import parse_bom_ifd_csv

    raw = (
        b"Copyright Commonwealth of Australia 2016\n"
        b"IFD Design Rainfall Depth (mm)\n"
        b"Requested coordinate:,Latitude,-30.00500,Longitude,150.100\n"
        b"Duration,Duration in min,1%\n"
        b"1 hour,60,100\n"
    )
    bom = parse_bom_ifd_csv(raw)
    event = replace(_event(), source_sha256=bom.sha256)
    selection = _selection()
    agreement = verify_legacy_bom_source_point(bom, selection, event)
    assert (agreement.requested_latitude, agreement.requested_longitude) == (Decimal("-30.00500"), Decimal("150.100"))
    assert agreement.datahub_sha256 == selection.source_sha256
    assert agreement.bom_sha256 == bom.sha256

    with pytest.raises(ARRFormatError, match="source bytes"):
        verify_legacy_bom_source_point(bom, selection, _event())
    with pytest.raises(ARRFormatError, match="requested points differ"):
        verify_legacy_bom_source_point(replace(bom, latitude=Decimal("-30.1")), selection, event)
    with pytest.raises(ARRFormatError, match="coordinates are missing"):
        verify_legacy_bom_source_point(replace(bom, latitude=None), selection, event)


def test_source_increments_and_total_must_agree() -> None:
    event = replace(_event(), total_mm=Decimal(99))
    with pytest.raises(ARRFormatError, match="totals disagree"):
        calculate_burst_only_excess(event, _selection())


def test_complete_storm_separates_preburst_and_burst_without_double_reduction() -> None:
    from runoff_routing.arr_losses import calculate_complete_storm_excess

    selection = _selection(method="explicit_preburst")
    event = _event()
    full = prepend_explicit_preburst(
        event, selection, percentages=(Decimal(25), Decimal(75)), declared_profile_id="synthetic-two-step"
    )
    result = calculate_complete_storm_excess(full)
    assert result.end_times_min == (-30, 0, 30, 60)
    assert result.excess_increments_mm[:3] == (0, 0, 0)
    assert result.preburst_excess_total_mm == 0
    assert result.excess_total_mm == result.burst_excess_total_mm
    assert result.applied_initial_loss_mm == 21
    assert result.rainfall_total_mm == 107
    assert result.rainfall_total_mm == (
        result.applied_initial_loss_mm + result.applied_continuing_loss_mm + result.excess_total_mm
    )
    assert result.hydrological_acceptance == "not_assessed"
    # Preburst entirely consumed by IL; same burst excess is expected for this
    # *particular synthetic* example only, not universal RORBwin parity.
    burst_only = calculate_burst_only_excess(event, _selection())
    assert result.excess_increments_mm[2:] == burst_only.excess_increments_mm


def test_complete_storm_preburst_can_produce_excess_and_cannot_reuse_burst_il() -> None:
    from runoff_routing.arr_losses import calculate_complete_storm_excess

    doc = parse_arr_txt(
        _document().replace(b"Storm Initial Losses (mm),21.0", b"Storm Initial Losses (mm),2.0"),
        legacy_profile="arr2016",
    )
    selection = select_legacy_preburst_loss(
        doc, duration_min=60, aep_percent=Decimal(1), method="explicit_preburst"
    )
    event = _event()
    full = prepend_explicit_preburst(
        event, selection, percentages=(Decimal(50), Decimal(50)), declared_profile_id="synthetic-two-step"
    )
    excess = calculate_complete_storm_excess(full)
    assert excess.preburst_excess_total_mm > 0
    assert excess.excess_total_mm == sum(excess.excess_increments_mm)
    with pytest.raises(ARRFormatError, match="cannot consume explicit-preburst"):
        calculate_burst_only_excess(event, selection)


def test_ratio_preburst_on_arf_adjusted_rainfall_preserves_original_depth() -> None:
    from runoff_routing.arr_arf import calculate_arr2019_arf, published_coefficients, apply_arr2019_arf_to_bom_storm
    from runoff_routing.arr_losses import derive_preburst_from_areal_rainfall

    gross = _event()
    calculation = calculate_arr2019_arf(
        catchment_area_km2=Decimal(100),
        duration_min=60,
        aep_percent=Decimal(1),
        coefficients=published_coefficients("South-West Western Australia"),
    )
    area = apply_arr2019_arf_to_bom_storm(gross, calculation)
    doc = parse_arr_txt(_document().replace(b"7.00 (1.020)", b"7.00 (0.050)"), legacy_profile="arr2016")
    before = select_legacy_preburst_loss(doc, duration_min=60, aep_percent=Decimal(1))
    after = derive_preburst_from_areal_rainfall(before, area)
    assert after.depth_basis == "ratio_x_areal_reduced_design_depth"
    assert after.source_preburst_depth_mm == before.preburst_depth_mm == Decimal("7.00")
    assert after.preburst_depth_mm == before.preburst_ratio * area.total_mm
    assert after.rainfall_basis_total_mm == area.total_mm
    assert after.burst_initial_loss_mm == max(Decimal(0), before.storm_initial_loss_mm - after.preburst_depth_mm)
    assert "RORBWIN_V6_52_METHOD_HYPOTHESIS_NOT_NUMERICALLY_ACCEPTED" in after.operations
    with pytest.raises(ARRFormatError, match="double application"):
        derive_preburst_from_areal_rainfall(after, area)


def test_ratio_preburst_rejects_nonadjusted_rainfall_and_unreviewed_excess() -> None:
    from runoff_routing.arr_arf import calculate_arr2019_arf, published_coefficients, apply_arr2019_arf_to_bom_storm
    from runoff_routing.arr_losses import derive_preburst_from_areal_rainfall

    gross = _event()
    selection = _selection()
    from typing import cast
    from runoff_routing.arr_arf import AreaAdjustedHyetograph
    with pytest.raises(ARRFormatError, match="once-ARF-adjusted"):
        derive_preburst_from_areal_rainfall(selection, cast(AreaAdjustedHyetograph, gross))
    calc = calculate_arr2019_arf(
        catchment_area_km2=Decimal(100), duration_min=60, aep_percent=Decimal(1),
        coefficients=published_coefficients("South-West Western Australia"),
    )
    areal = apply_arr2019_arf_to_bom_storm(gross, calc)
    modified = replace(selection, preburst_ratio=Decimal(2))
    with pytest.raises(ARRFormatError, match="exceeds storm IL"):
        derive_preburst_from_areal_rainfall(modified, areal)
    clamped = replace(modified, excess_policy="clamp_burst_il_to_zero")
    derived = derive_preburst_from_areal_rainfall(clamped, areal)
    assert derived.burst_initial_loss_mm == 0
    assert derived.preburst_above_storm_il_mm > 0
