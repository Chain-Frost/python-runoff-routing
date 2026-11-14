"""ARR2016-era preburst and loss preparation with explicit, non-interchangeable policies.

No RORBwin preburst-pattern inference, RORB rainfall-excess parity, or routing.
Only caller-selected, versioned legacy Data Hub records are accepted.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from decimal import Decimal, InvalidOperation
from typing import Literal

from runoff_routing.arr_arf import AreaAdjustedHyetograph
from runoff_routing.arr_data import ARRDocument, ARRFormatError
from runoff_routing.arr_storm import RawHyetograph
from runoff_routing.bom_ifd import BoMIFD

LossMethod = Literal["burst_only_reduced_il", "explicit_preburst"]
ExcessPreburstPolicy = Literal["reject", "clamp_burst_il_to_zero"]
LOSS_POLICY_VERSION = "arr2019-legacy-loss-v2"
PreburstDepthBasis = Literal["as_exported_depth", "ratio_x_areal_reduced_design_depth"]
MAX_EXPLICIT_PREBURST_STEPS = 512


@dataclass(frozen=True, slots=True)
class PreburstLossSelection:
    """Exact legacy grid cell and storm loss, without inventing a design policy."""

    source_sha256: str
    source_profile: str
    requested_latitude: Decimal
    requested_longitude: Decimal
    duration_min: int
    aep_percent: Decimal
    preburst_percentile: int
    preburst_depth_mm: Decimal
    source_preburst_depth_mm: Decimal
    preburst_ratio: Decimal
    depth_basis: PreburstDepthBasis
    rainfall_basis_total_mm: Decimal | None
    storm_initial_loss_mm: Decimal
    continuing_loss_mm_per_hour: Decimal
    method: LossMethod
    excess_policy: ExcessPreburstPolicy
    burst_initial_loss_mm: Decimal | None
    preburst_above_storm_il_mm: Decimal
    source_preburst_tag: str
    source_preburst_metadata: tuple[tuple[str, str], ...]
    source_loss_metadata: tuple[tuple[str, str], ...]
    operations: tuple[str, ...]
    policy_version: str = LOSS_POLICY_VERSION
    hydrological_acceptance: Literal["not_assessed"] = "not_assessed"

    def __post_init__(self) -> None:
        if self.policy_version != LOSS_POLICY_VERSION:
            msg = "Unsupported ARR loss policy version"
            raise ARRFormatError(msg)
        numbers = (
            self.aep_percent,
            self.preburst_depth_mm,
            self.source_preburst_depth_mm,
            self.preburst_ratio,
            self.storm_initial_loss_mm,
            self.continuing_loss_mm_per_hour,
            self.preburst_above_storm_il_mm,
        )
        if not all(value.is_finite() and value >= 0 for value in numbers):
            msg = "Nonfinite or negative selected loss/preburst values"
            raise ARRFormatError(msg)
        if not (-90 <= self.requested_latitude <= 90 and -180 <= self.requested_longitude <= 180):
            msg = "ARR loss source coordinates must be within WGS84 bounds"
            raise ARRFormatError(msg)
        if not 0 < self.aep_percent <= 100 or self.duration_min <= 0:
            msg = "ARR loss selection requires valid duration and AEP"
            raise ARRFormatError(msg)
        if not self.source_sha256 or not self.source_profile or not self.operations:
            msg = "ARR loss selection requires source and method provenance"
            raise ARRFormatError(msg)
        _validate_preburst_depth_basis(self)
        _validate_selected_preburst_arithmetic(self)
        if self.burst_initial_loss_mm is not None and (
            not self.burst_initial_loss_mm.is_finite() or self.burst_initial_loss_mm < 0
        ):
            msg = "Invalid computed burst initial loss"
            raise ARRFormatError(msg)
        if (self.method == "explicit_preburst") != (self.burst_initial_loss_mm is None):
            msg = "Explicit preburst retains storm IL; burst-only requires burst IL"
            raise ARRFormatError(msg)


def _validate_selected_preburst_arithmetic(selection: PreburstLossSelection) -> None:
    """Reject forged/repeated preburst and burst IL arithmetic at construction."""
    if selection.preburst_percentile not in {10, 25, 50, 75, 90}:
        msg = "Unsupported legacy preburst percentile"
        raise ARRFormatError(msg)
    if selection.preburst_above_storm_il_mm != max(
        Decimal(0), selection.preburst_depth_mm - selection.storm_initial_loss_mm
    ):
        msg = "Selected preburst excess must equal preburst minus storm IL once"
        raise ARRFormatError(msg)
    if selection.burst_initial_loss_mm is not None and selection.burst_initial_loss_mm != max(
        Decimal(0), selection.storm_initial_loss_mm - selection.preburst_depth_mm
    ):
        msg = "Selected burst initial loss must equal storm IL minus preburst once"
        raise ARRFormatError(msg)


def _validate_preburst_depth_basis(selection: PreburstLossSelection) -> None:
    """Keep original and ratio-derived event depth provenance distinct."""
    if selection.depth_basis not in {"as_exported_depth", "ratio_x_areal_reduced_design_depth"}:
        msg = "Unsupported preburst depth basis"
        raise ARRFormatError(msg)
    if (selection.depth_basis == "as_exported_depth") != (selection.rainfall_basis_total_mm is None):
        msg = "Ratio-derived preburst must retain its rainfall depth basis"
        raise ARRFormatError(msg)
    if selection.rainfall_basis_total_mm is not None and (
        not selection.rainfall_basis_total_mm.is_finite() or selection.rainfall_basis_total_mm < 0
    ):
        msg = "Invalid preburst rainfall depth basis"
        raise ARRFormatError(msg)
    if selection.rainfall_basis_total_mm is not None and (
        selection.preburst_depth_mm != selection.preburst_ratio * selection.rainfall_basis_total_mm
    ):
        msg = "Ratio-derived preburst depth must equal ratio times its recorded rainfall basis"
        raise ARRFormatError(msg)


def _validate_loss_method(method: LossMethod, excess_policy: ExcessPreburstPolicy) -> None:
    """Explicitly distinguish method policy from the original Data Hub source."""
    if method not in {"burst_only_reduced_il", "explicit_preburst"}:
        msg = "Unrecognised preburst loss method"
        raise ARRFormatError(msg)
    if excess_policy not in {"reject", "clamp_burst_il_to_zero"}:
        msg = "Unrecognised excess-preburst policy"
        raise ARRFormatError(msg)


def select_legacy_preburst_loss(
    document: ARRDocument,
    *,
    duration_min: int,
    aep_percent: Decimal,
    percentile: Literal[10, 25, 50, 75, 90] = 50,
    method: LossMethod = "burst_only_reduced_il",
    excess_policy: ExcessPreburstPolicy = "reject",
) -> PreburstLossSelection:
    """Select *exact* legacy source cells, with no interpolation or automatic quantile choice.

    The burst-only method uses IL_b = max(0, IL_s - source_preburst_depth).
    Its clamp behaviour is not an assertion that the excess preburst is negligible.
    For explicit preburst, the source storm IL is retained and distribution is deferred.
    """
    if document.source.compatibility_profile != "arr2016_txt":
        msg = "Only an explicit legacy ARR2016 TXT profile supports this loss selection"
        raise ARRFormatError(msg)
    _validate_loss_method(method, excess_policy)
    if isinstance(duration_min, bool) or duration_min <= 0:
        msg = "Loss event duration must be whole positive minutes"
        raise ARRFormatError(msg)
    if not aep_percent.is_finite() or not 0 < aep_percent <= 100:
        msg = "Loss event AEP must be an explicit percentage"
        raise ARRFormatError(msg)
    losses = document.legacy_losses
    if losses is None or losses.initial_loss_mm is None or losses.continuing_loss_mm_per_hour is None:
        msg = "Legacy storm initial and continuing loss are both required; -50 means missing"
        raise ARRFormatError(msg)
    tables = [item for item in document.legacy_preburst if item.percentile == percentile]
    if len(tables) != 1:
        msg = "Exactly one requested legacy preburst percentile table is required"
        raise ARRFormatError(msg)
    table = tables[0]
    try:
        row = table.durations_min.index(duration_min)
        col = table.aep_percent.index(aep_percent)
    except ValueError as exc:
        msg = "Requested legacy preburst duration/AEP missing; no interpolation"
        raise ARRFormatError(msg) from exc
    depth = table.depths_mm[row][col]
    ratio = table.ratios[row][col]
    exceeded = max(Decimal(0), depth - losses.initial_loss_mm)
    steps = [
        "EXACT_LEGACY_PREBURST_DEPTH_AND_RATIO_AS_EXPORTED",
        "STORM_LOSSES_FROM_SAME_LEGACY_DATAHUB_SOURCE",
        f"EXPLICIT_PREBURST_PERCENTILE_{percentile}",
    ]
    burst_il: Decimal | None = None
    if method == "burst_only_reduced_il":
        if exceeded > 0 and excess_policy == "reject":
            msg = "Preburst exceeds storm IL; explicitly review residual-preburst/clamp policy"
            raise ARRFormatError(msg)
        burst_il = max(Decimal(0), losses.initial_loss_mm - depth)
        steps.append("BURST_IL_STORM_IL_MINUS_PREBURST_DEPTH")
        if exceeded:
            steps.append("PREBURST_EXCEEDS_IL_CLAMPED_EXPLICITLY_NO_EXCESS_STORM_RAINFALL")
        steps.append("BURST_ONLY_NOT_RORBWIN_PREBURST_METHOD")
    else:
        steps.append("EXPLICIT_PREBURST_REQUIRED_NO_AUTO_TEMPORAL_PROFILE")
        steps.append("ORIGINAL_STORM_IL_RETAINED_NOT_BURST_IL")
    return PreburstLossSelection(
        source_sha256=document.source.sha256,
        source_profile=document.source.compatibility_profile,
        requested_latitude=document.location.latitude,
        requested_longitude=document.location.longitude,
        duration_min=duration_min,
        aep_percent=aep_percent,
        preburst_percentile=percentile,
        preburst_depth_mm=depth,
        source_preburst_depth_mm=depth,
        preburst_ratio=ratio,
        depth_basis="as_exported_depth",
        rainfall_basis_total_mm=None,
        storm_initial_loss_mm=losses.initial_loss_mm,
        continuing_loss_mm_per_hour=losses.continuing_loss_mm_per_hour,
        method=method,
        excess_policy=excess_policy,
        burst_initial_loss_mm=burst_il,
        preburst_above_storm_il_mm=exceeded,
        source_preburst_tag=table.source_tag,
        source_preburst_metadata=table.metadata,
        source_loss_metadata=losses.metadata,
        operations=tuple(steps),
    )


def _require_areal_event(value: object) -> AreaAdjustedHyetograph:
    """Validate a dynamic API boundary without weakening typed call signatures."""
    if not isinstance(value, AreaAdjustedHyetograph):
        msg = "Ratio-to-rainfall mode requires a once-ARF-adjusted BoM event"
        raise ARRFormatError(msg)
    return value


def derive_preburst_from_areal_rainfall(
    selection: PreburstLossSelection,
    event: AreaAdjustedHyetograph,
) -> PreburstLossSelection:
    """Opt-in RORBwin-oriented ratio times *once* ARF-adjusted design depth.

    Preburst ratios are source data, not a second ARF. Never apply an ARF
    to the computed preburst depth. The exact RORBwin 6.52 event arithmetic
    remains an independently testable hypothesis, not established parity.
    """
    event = _require_areal_event(event)
    if selection.depth_basis != "as_exported_depth":
        msg = "Preburst rainfall ratio was already applied; double application prohibited"
        raise ARRFormatError(msg)
    _event_inputs(event, selection)
    if "ARF_APPLIED_ONCE_TO_GROSS_BOM_RAINFALL" not in event.operations:
        msg = "Areal rainfall must have a traceable once-only ARF operation"
        raise ARRFormatError(msg)
    depth = selection.preburst_ratio * event.total_mm
    exceeds = max(Decimal(0), depth - selection.storm_initial_loss_mm)
    if selection.method == "burst_only_reduced_il" and exceeds and selection.excess_policy == "reject":
        msg = "Ratio-derived preburst exceeds storm IL; select an explicit reviewed excess policy"
        raise ARRFormatError(msg)
    burst_il = (
        max(Decimal(0), selection.storm_initial_loss_mm - depth)
        if selection.method == "burst_only_reduced_il"
        else None
    )
    return replace(
        selection,
        preburst_depth_mm=depth,
        depth_basis="ratio_x_areal_reduced_design_depth",
        rainfall_basis_total_mm=event.total_mm,
        burst_initial_loss_mm=burst_il,
        preburst_above_storm_il_mm=exceeds,
        operations=(
            *selection.operations,
            "OVERRIDE_SOURCE_PREBURST_DEPTH_WITH_EXPLICIT_RATIO_TIMES_AREAL_DEPTH",
            "SOURCE_PREBURST_DEPTH_RETAINED_SEPARATELY",
            "DESIGN_ARF_ALREADY_APPLIED_ONCE_NO_ARF_ON_PREBURST",
            "RORBWIN_V6_52_METHOD_HYPOTHESIS_NOT_NUMERICALLY_ACCEPTED",
        ),
    )


@dataclass(frozen=True, slots=True)
class SourcePointAgreement:
    """Independent assertion that selected BoM/ARR requested points and bytes agree."""

    bom_sha256: str
    datahub_sha256: str
    requested_latitude: Decimal
    requested_longitude: Decimal
    method: Literal["exact_requested_wgs84_point"] = "exact_requested_wgs84_point"


def verify_legacy_bom_source_point(
    bom: BoMIFD,
    selection: PreburstLossSelection,
    event: RawHyetograph | AreaAdjustedHyetograph,
) -> SourcePointAgreement:
    """Reject mixing unrelated point exports; no inference of catchment polygon/area.

    Deliberately strict: spatially varying IFDs need a separate reviewed mapping.
    """
    original = event.gross if isinstance(event, AreaAdjustedHyetograph) else event
    if bom.sha256 != original.source_sha256:
        msg = "Rainfall event does not originate from the supplied BoM source bytes"
        raise ARRFormatError(msg)
    if bom.latitude is None or bom.longitude is None:
        msg = "BoM requested WGS84 coordinates are missing"
        raise ARRFormatError(msg)
    if (bom.latitude, bom.longitude) != (selection.requested_latitude, selection.requested_longitude):
        msg = "BoM and ARR Data Hub requested points differ; no implicit spatial matching"
        raise ARRFormatError(msg)
    return SourcePointAgreement(
        bom_sha256=bom.sha256,
        datahub_sha256=selection.source_sha256,
        requested_latitude=selection.requested_latitude,
        requested_longitude=selection.requested_longitude,
    )


@dataclass(frozen=True, slots=True)
class ExplicitPreburstRainfall:
    """Caller-supplied temporal profile, never described as the RORBwin default."""

    source: RawHyetograph | AreaAdjustedHyetograph
    loss_selection: PreburstLossSelection
    preburst_percentages: tuple[Decimal, ...]
    preburst_increments_mm: tuple[Decimal, ...]
    combined_gross_increments_mm: tuple[Decimal, ...]
    preburst_end_times_min: tuple[int, ...]
    combined_end_times_min: tuple[int, ...]
    combined_gross_total_mm: Decimal
    operations: tuple[str, ...]
    hydrological_acceptance: Literal["not_assessed"] = "not_assessed"


def _event_inputs(
    event: RawHyetograph | AreaAdjustedHyetograph, selection: PreburstLossSelection
) -> tuple[tuple[Decimal, ...], int]:
    gross = event.gross if isinstance(event, AreaAdjustedHyetograph) else event
    if gross.duration_min != selection.duration_min:
        msg = "Loss/preburst event duration does not match rainfall duration"
        raise ARRFormatError(msg)
    try:
        aep_label = gross.probability_label.strip()
        if not aep_label.endswith("%"):
            msg = "Loss/preburst AEP requires a percentage, not EY/ARI/one-in-N"
            raise ARRFormatError(msg)
        aep = Decimal(aep_label[:-1])
    except InvalidOperation as exc:
        msg = "Unparseable rainfall AEP for loss selection"
        raise ARRFormatError(msg) from exc
    if not aep.is_finite() or aep != selection.aep_percent:
        msg = "Loss/preburst AEP does not match rainfall AEP"
        raise ARRFormatError(msg)
    if gross.source_label != "BoM 2016 IFD (raw gross rainfall)":
        msg = "Legacy loss method requires unmodified BoM IFD source rainfall"
        raise ARRFormatError(msg)
    increments = event.increments_mm
    if gross.timestep_min <= 0 or gross.duration_min % gross.timestep_min != 0:
        msg = "Invalid rainfall timestep for loss preparation"
        raise ARRFormatError(msg)
    if len(increments) != gross.duration_min // gross.timestep_min:
        msg = "Rainfall timestep/increment mismatch"
        raise ARRFormatError(msg)
    if any(not value.is_finite() or value < 0 for value in increments):
        msg = "Invalid rainfall depth for loss preparation"
        raise ARRFormatError(msg)
    if sum(increments, Decimal(0)) != event.total_mm:
        msg = "Rainfall totals disagree with source increments"
        raise ARRFormatError(msg)
    return increments, gross.timestep_min


def prepend_explicit_preburst(
    event: RawHyetograph | AreaAdjustedHyetograph,
    selection: PreburstLossSelection,
    *,
    percentages: tuple[Decimal, ...],
    declared_profile_id: str,
) -> ExplicitPreburstRainfall:
    """Prepend a *declared* preburst series before the original design burst.

    No temporal-pattern or duration is selected automatically. The caller must
    identify the external pattern; this does not evaluate losses or route flow.
    """
    if selection.method != "explicit_preburst":
        msg = "Prepending preburst requires explicit_preburst policy"
        raise ARRFormatError(msg)
    increments, timestep_min = _event_inputs(event, selection)
    if not declared_profile_id.strip():
        msg = "An explicit preburst temporal-profile source ID is required"
        raise ARRFormatError(msg)
    if not 1 <= len(percentages) <= MAX_EXPLICIT_PREBURST_STEPS:
        msg = "Explicit preburst increment count is empty or excessive"
        raise ARRFormatError(msg)
    if any(not value.is_finite() or not 0 <= value <= 100 for value in percentages):
        msg = "Invalid explicit preburst increment percentage"
        raise ARRFormatError(msg)
    if sum(percentages, Decimal(0)) != 100:
        msg = "Explicit preburst percentages must total exactly 100; no rescaling"
        raise ARRFormatError(msg)
    preburst = tuple(selection.preburst_depth_mm * value / 100 for value in percentages)
    preburst_end_times = tuple(range(-timestep_min * (len(percentages) - 1), 1, timestep_min))
    burst_end_times = tuple(range(timestep_min, (len(increments) + 1) * timestep_min, timestep_min))
    return ExplicitPreburstRainfall(
        source=event,
        loss_selection=selection,
        preburst_percentages=percentages,
        preburst_increments_mm=preburst,
        combined_gross_increments_mm=(*preburst, *increments),
        preburst_end_times_min=preburst_end_times,
        combined_end_times_min=(*preburst_end_times, *burst_end_times),
        combined_gross_total_mm=sum(preburst, Decimal(0)) + sum(increments, Decimal(0)),
        operations=(
            *selection.operations,
            f"CALLER_PROVIDED_PREBURST_PROFILE_{declared_profile_id}",
            "PREBURST_TIMESTEPS_END_AT_DESIGN_BURST_START",
            "NO_RORBWIN_PREBURST_PROFILE_PARITY_CLAIM",
        ),
    )


@dataclass(frozen=True, slots=True)
class ExperimentalExcessRainfall:
    """Explicit sequential within-step IL/CL arithmetic, NOT RORB numerical parity."""

    source: RawHyetograph | AreaAdjustedHyetograph
    selection: PreburstLossSelection
    excess_increments_mm: tuple[Decimal, ...]
    applied_initial_loss_mm: Decimal
    applied_continuing_loss_mm: Decimal
    rainfall_total_mm: Decimal
    excess_total_mm: Decimal
    operations: tuple[str, ...]
    hydrological_acceptance: Literal["not_assessed"] = "not_assessed"


def calculate_burst_only_excess(
    event: RawHyetograph | AreaAdjustedHyetograph, selection: PreburstLossSelection
) -> ExperimentalExcessRainfall:
    """One auditable IL/CL rule, not a claim about RORBwin's time-step convention.

    Initial loss consumes the leading fraction of a wet increment. Remaining
    time in that increment incurs continuing loss at CL mm/h. Later wet
    increments incur CL for the full step; dry intervals have no losses.
    """
    if selection.method != "burst_only_reduced_il" or selection.burst_initial_loss_mm is None:
        msg = "Burst-only IL/CL calculation cannot consume explicit-preburst input"
        raise ARRFormatError(msg)
    increments, timestep_min = _event_inputs(event, selection)
    excess, total_initial, total_continuing = _sequential_il_cl(
        increments,
        initial_loss_mm=selection.burst_initial_loss_mm,
        continuing_loss_mm_per_hour=selection.continuing_loss_mm_per_hour,
        timestep_min=timestep_min,
    )
    return ExperimentalExcessRainfall(
        source=event,
        selection=selection,
        excess_increments_mm=excess,
        applied_initial_loss_mm=total_initial,
        applied_continuing_loss_mm=total_continuing,
        rainfall_total_mm=sum(increments, Decimal(0)),
        excess_total_mm=sum(excess, Decimal(0)),
        operations=(
            *selection.operations,
            "SEQUENTIAL_IL_THEN_CL_WITHIN_STEP_CONSTANT_RAIN_RATE",
            "NO_RORBWIN_LOSS_ENGINE_OR_RUNOFF_PARITY",
        ),
    )


def _sequential_il_cl(
    increments: tuple[Decimal, ...],
    *,
    initial_loss_mm: Decimal,
    continuing_loss_mm_per_hour: Decimal,
    timestep_min: int,
) -> tuple[tuple[Decimal, ...], Decimal, Decimal]:
    """Experimental IL/CL accounting, independent of source format and event selection."""
    if any(not n.is_finite() or n < 0 for n in (initial_loss_mm, continuing_loss_mm_per_hour)):
        msg = "Experimental IL/CL must be finite and nonnegative"
        raise ARRFormatError(msg)
    if timestep_min <= 0 or not increments or any(not n.is_finite() or n < 0 for n in increments):
        msg = "Experimental rainfall increments and timestep must be valid"
        raise ARRFormatError(msg)
    initial_remaining = initial_loss_mm
    continuing_capacity = continuing_loss_mm_per_hour * Decimal(timestep_min) / 60
    total_initial = Decimal(0)
    total_continuing = Decimal(0)
    excess: list[Decimal] = []
    for rainfall in increments:
        initially_lost = min(initial_remaining, rainfall)
        initial_remaining -= initially_lost
        total_initial += initially_lost
        after_initial = rainfall - initially_lost
        available_fraction = Decimal(0) if rainfall == 0 else after_initial / rainfall
        continuing_lost = min(after_initial, continuing_capacity * available_fraction)
        total_continuing += continuing_lost
        excess.append(after_initial - continuing_lost)
    return tuple(excess), total_initial, total_continuing


@dataclass(frozen=True, slots=True)
class ExperimentalCompleteStormExcess:
    """Sequential experimental storm IL/CL across caller-specified preburst and burst."""

    source: ExplicitPreburstRainfall
    end_times_min: tuple[int, ...]
    excess_increments_mm: tuple[Decimal, ...]
    applied_initial_loss_mm: Decimal
    applied_continuing_loss_mm: Decimal
    rainfall_total_mm: Decimal
    excess_total_mm: Decimal
    preburst_excess_total_mm: Decimal
    burst_excess_total_mm: Decimal
    operations: tuple[str, ...]
    hydrological_acceptance: Literal["not_assessed"] = "not_assessed"


def calculate_complete_storm_excess(storm: ExplicitPreburstRainfall) -> ExperimentalCompleteStormExcess:
    """Experimental IL/CL for a complete synthetic storm, never RORBwin parity.

    The original *storm* IL is applied from the start of the explicit preburst;
    burst-only IL reduction is expressly prohibited on the same rainfall series.
    """
    selection = storm.loss_selection
    if selection.method != "explicit_preburst" or selection.burst_initial_loss_mm is not None:
        msg = "Complete-storm loss requires unmodified storm IL and explicit-preburst method"
        raise ARRFormatError(msg)
    _, timestep_min = _event_inputs(storm.source, selection)
    increments = storm.combined_gross_increments_mm
    if (
        not storm.preburst_increments_mm
        or len(increments) != len(storm.combined_end_times_min)
        or len(increments) != len(storm.preburst_increments_mm) + len(storm.source.increments_mm)
    ):
        msg = "Inconsistent explicit preburst and burst timestep grid"
        raise ARRFormatError(msg)
    if sum(increments, Decimal(0)) != storm.combined_gross_total_mm:
        msg = "Complete-storm rainfall totals disagree"
        raise ARRFormatError(msg)
    excess, initial, continuing = _sequential_il_cl(
        increments,
        initial_loss_mm=selection.storm_initial_loss_mm,
        continuing_loss_mm_per_hour=selection.continuing_loss_mm_per_hour,
        timestep_min=timestep_min,
    )
    pre_count = len(storm.preburst_increments_mm)
    preburst_excess = sum(excess[:pre_count], Decimal(0))
    burst_excess = sum(excess[pre_count:], Decimal(0))
    return ExperimentalCompleteStormExcess(
        source=storm,
        end_times_min=storm.combined_end_times_min,
        excess_increments_mm=excess,
        applied_initial_loss_mm=initial,
        applied_continuing_loss_mm=continuing,
        rainfall_total_mm=sum(increments, Decimal(0)),
        excess_total_mm=sum(excess, Decimal(0)),
        preburst_excess_total_mm=preburst_excess,
        burst_excess_total_mm=burst_excess,
        operations=(
            *storm.operations,
            "STORM_IL_APPLIED_FROM_FIRST_PREBURST_INCREMENT",
            "SEQUENTIAL_IL_THEN_CL_WITHIN_STEP_CONSTANT_RAIN_RATE",
            "NO_RORBWIN_NUMERICAL_PARITY",
        ),
    )
