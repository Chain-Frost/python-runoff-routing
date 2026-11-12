"""ARR2019 Book 2 regional ARF equations with explicit policy and coefficient provenance.

Independent of the RORB engine and ARR2026 climate/loss methods. Source parameters
are always identified; all inputs and results retain Decimal representation.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Literal

from runoff_routing.arr_data import ARRDocument, ARRFormatError
from runoff_routing.arr_storm import RawHyetograph

ARF_POLICY_VERSION = "ARR2019_BOOK2_V4_1_2_4_1_TO_2_4_4"
CoefficientOrigin = Literal["arr2019_book2_table_2_4_2", "legacy_datahub"]
NegativePolicy = Literal["reject", "floor_zero"]

# Published ARR2019 Book 2 v4.1 table 2.4.2, retaining its displayed precision.
# Note: the 2020 Tony Ladson R gist has Inland Arid g=-0.129; Book 2 has +0.129.
# The independently developed ryan-tools script uses +0.129, correctly.
_PUBLISHED_PARAMETERS: dict[str, tuple[str, ...]] = {
    "East Coast North": ("0.327", "0.241", "0.448", "0.36", "0.00096", "0.48", "-0.21", "0.012", "-0.0013"),
    "Semi-arid Inland Queensland": ("0.159", "0.283", "0.25", "0.308", "7.3E-07", "1", "0.039", "0", "0"),
    "Tasmania": ("0.0605", "0.347", "0.2", "0.283", "0.00076", "0.347", "0.0877", "0.012", "-0.00033"),
    "South-West Western Australia": (
        "0.183",
        "0.259",
        "0.271",
        "0.33",
        "3.85E-06",
        "0.41",
        "0.55",
        "0.00817",
        "-0.00045",
    ),
    "Central New South Wales": ("0.265", "0.241", "0.505", "0.321", "0.00056", "0.414", "-0.021", "0.015", "-0.00033"),
    "South-East Coast": ("0.06", "0.361", "0", "0.317", "8.11E-05", "0.651", "0", "0", "0"),
    "Southern Semi-arid": ("0.254", "0.247", "0.403", "0.351", "0.0013", "0.302", "0.058", "0", "0"),
    "Southern Temperate": ("0.158", "0.276", "0.372", "0.315", "0.000141", "0.41", "0.15", "0.01", "-0.0027"),
    "Northern Coastal": ("0.326", "0.223", "0.442", "0.323", "0.0013", "0.58", "-0.374", "0.013", "-0.0015"),
    "Inland Arid": ("0.297", "0.234", "0.449", "0.344", "0.00142", "0.216", "0.129", "0", "0"),
}


@dataclass(frozen=True, slots=True)
class ARFCoefficients:
    """Nine ARR long-duration coefficients from one explicitly identified source."""

    region: str
    values: tuple[Decimal, Decimal, Decimal, Decimal, Decimal, Decimal, Decimal, Decimal, Decimal]
    origin: CoefficientOrigin
    source_sha256: str | None = None

    def __post_init__(self) -> None:
        if not self.region.strip() or len(self.values) != 9 or any(not v.is_finite() for v in self.values):
            msg = "ARR ARF coefficients require a region and nine finite values"
            raise ARRFormatError(msg)
        if self.origin == "legacy_datahub" and not self.source_sha256:
            msg = "Data Hub coefficients require their original ARR export SHA-256"
            raise ARRFormatError(msg)


def published_coefficients(region: str) -> ARFCoefficients:
    """Retrieve *exact* published regional coefficients, not inferred from TP region."""
    raw = _PUBLISHED_PARAMETERS.get(region)
    if raw is None:
        msg = f"Unknown ARR2019 ARF region {region!r}; use a published full region name"
        raise ARRFormatError(msg)
    values = (
        Decimal(raw[0]),
        Decimal(raw[1]),
        Decimal(raw[2]),
        Decimal(raw[3]),
        Decimal(raw[4]),
        Decimal(raw[5]),
        Decimal(raw[6]),
        Decimal(raw[7]),
        Decimal(raw[8]),
    )
    return ARFCoefficients(region, values, "arr2019_book2_table_2_4_2")


def legacy_datahub_coefficients(document: ARRDocument) -> ARFCoefficients:
    """Preserve original source parameters independently of the published default."""
    arf = document.legacy_arf
    if arf is None:
        msg = "ARR Data Hub document has no parsed legacy ARF coefficients"
        raise ARRFormatError(msg)
    values = tuple(value for _, value in arf.coefficients)
    return ARFCoefficients(
        arf.zone,
        (values[0], values[1], values[2], values[3], values[4], values[5], values[6], values[7], values[8]),
        "legacy_datahub",
        document.source.sha256,
    )


@dataclass(frozen=True, slots=True)
class ARFResult:
    """One applicable factor and a traceable description of its method."""

    area_km2: Decimal
    duration_min: int
    aep_percent: Decimal
    factor: Decimal
    region: str | None
    coefficient_origin: CoefficientOrigin | None
    coefficient_source_sha256: str | None
    method_steps: tuple[str, ...]
    policy_version: str = ARF_POLICY_VERSION

    def __post_init__(self) -> None:
        if not self.factor.is_finite() or not 0 <= self.factor <= 1:
            msg = "ARF calculation result must be a finite dimensionless factor between zero and one"
            raise ARRFormatError(msg)
        if self.policy_version != ARF_POLICY_VERSION:
            msg = "Unrecognised ARR ARF calculation policy version"
            raise ARRFormatError(msg)


@dataclass(frozen=True, slots=True)
class AreaAdjustedHyetograph:
    """Separate adjusted result: gross source cannot be confused with areal rainfall."""

    gross: RawHyetograph
    arf: ARFResult
    increments_mm: tuple[Decimal, ...]
    total_mm: Decimal
    operations: tuple[str, ...]
    hydrological_acceptance: Literal["not_assessed"] = "not_assessed"


def _clamp(value: Decimal, policy: NegativePolicy, steps: list[str]) -> Decimal:
    if not value.is_finite():
        msg = "Nonfinite ARR ARF calculation"
        raise ARRFormatError(msg)
    if value < 0:
        if policy == "reject":
            msg = "Negative ARF outside physical bounds; explicitly select floor_zero if reviewed"
            raise ARRFormatError(msg)
        steps.append("NEGATIVE_ARF_EXPLICIT_FLOOR_ZERO")
        return Decimal(0)
    return min(Decimal(1), value)


def _short(area: Decimal, duration: Decimal, aep_frac: Decimal) -> Decimal:
    probability_term = Decimal("0.3") + aep_frac.log10()
    return min(
        Decimal(1),
        Decimal(1)
        - Decimal("0.287")
        * (area ** Decimal("0.265") - Decimal("0.439") * duration.log10())
        * duration ** Decimal("-0.36")
        + Decimal("0.00226") * area ** Decimal("0.226") * duration ** Decimal("0.125") * probability_term
        + Decimal("0.0141")
        * area ** Decimal("0.213")
        * Decimal(10) ** (Decimal("-0.021") * (duration - 180) ** 2 / 1440)
        * probability_term,
    )


def _long(area: Decimal, duration: Decimal, aep_frac: Decimal, coeffs: ARFCoefficients) -> Decimal:
    a, b, c, d, e, f, g, h, i = coeffs.values
    probability_term = Decimal("0.3") + aep_frac.log10()
    return min(
        Decimal(1),
        Decimal(1)
        - a * (area**b - c * duration.log10()) * duration**-d
        + e * area**f * duration**g * probability_term
        + h * Decimal(10) ** (i * area * duration / 1440) * probability_term,
    )


def _interpolate_area(area: Decimal, at_ten: Decimal) -> Decimal:
    return Decimal(1) - Decimal("0.6614") * (1 - at_ten) * (area ** Decimal("0.4") - 1)


def _validate_arf_inputs(
    area: Decimal,
    duration_min: int,
    aep_percent: Decimal,
    coefficients: ARFCoefficients | None,
    *,
    allow_short_extrapolation: bool,
    allow_rare_aep_extension: bool,
    negative_policy: NegativePolicy,
) -> None:
    if not area.is_finite() or not 0 < area <= 30000:
        msg = "ARR ARF catchment area must be in (0, 30000] km2"
        raise ARRFormatError(msg)
    if isinstance(duration_min, bool) or not 1 <= duration_min <= 10080:
        msg = "ARR ARF duration must be 1..10080 whole minutes"
        raise ARRFormatError(msg)
    if not aep_percent.is_finite() or not 0 < aep_percent <= 50:
        msg = "ARR ARF requires an AEP percentage, not EY/ARI; maximum is 50%"
        raise ARRFormatError(msg)
    if aep_percent < (Decimal("0.05") if allow_rare_aep_extension else Decimal(1)):
        msg = "ARR ARF AEP extrapolation below 1% requires an explicit reviewed opt-in (minimum 0.05%)"
        raise ARRFormatError(msg)
    if duration_min < 30 and not allow_short_extrapolation:
        msg = "ARR ARF durations below 30 minutes require explicit extrapolation opt-in"
        raise ARRFormatError(msg)
    if area > 1000 and duration_min <= 720:
        msg = "ARR short-duration ARF equation is inapplicable for catchment area > 1000 km2"
        raise ARRFormatError(msg)
    if negative_policy not in {"reject", "floor_zero"}:
        msg = "Unknown ARR ARF negative-value policy"
        raise ARRFormatError(msg)
    if area > 1 and duration_min > 720 and coefficients is None:
        msg = "Long/interpolated ARR ARF requires explicitly selected regional coefficients"
        raise ARRFormatError(msg)


def _evaluate_arf(
    area: Decimal,
    duration_min: int,
    aep_percent: Decimal,
    coefficients: ARFCoefficients | None,
    negative_policy: NegativePolicy,
    steps: list[str],
) -> Decimal:
    if area <= 1:
        steps.append("SMALL_AREA_UNITY")
        return Decimal(1)
    duration = Decimal(duration_min)
    aep_fraction = aep_percent / 100
    evaluation_area = max(area, Decimal(10))
    if duration_min <= 720:
        result = _clamp(_short(evaluation_area, duration, aep_fraction), negative_policy, steps)
        steps.append("SHORT_DURATION_EQ_2_4_1")
    elif duration_min >= 1440:
        if coefficients is None:
            msg = "Required ARR regional coefficients missing"
            raise ARRFormatError(msg)
        result = _clamp(_long(evaluation_area, duration, aep_fraction, coefficients), negative_policy, steps)
        steps.append("LONG_DURATION_EQ_2_4_2")
    else:
        if coefficients is None:
            msg = "Required ARR regional coefficients missing"
            raise ARRFormatError(msg)
        short = _clamp(_short(evaluation_area, Decimal(720), aep_fraction), negative_policy, steps)
        long = _clamp(_long(evaluation_area, Decimal(1440), aep_fraction, coefficients), negative_policy, steps)
        result = short + (long - short) * (duration - 720) / 720
        steps.append("DURATION_LINEAR_INTERPOLATION_EQ_2_4_3")
        if area > 1000:
            steps.append("SHORT_ENDPOINT_EXTRAPOLATION_GT_1000_KM2_AS_ARR2019_RECOMMENDS")
    if area < 10:
        result = _interpolate_area(area, result)
        steps.append("SMALL_AREA_INTERPOLATION_EQ_2_4_4")
    return _clamp(result, negative_policy, steps)


def calculate_arr2019_arf(
    *,
    catchment_area_km2: Decimal,
    duration_min: int,
    aep_percent: Decimal,
    coefficients: ARFCoefficients | None = None,
    allow_short_extrapolation: bool = False,
    allow_rare_aep_extension: bool = False,
    negative_policy: NegativePolicy = "reject",
) -> ARFResult:
    """ARR2019 equations 2.4.1-2.4.4, with explicit applicable method boundaries.

    Durations below 30 minutes and AEP below 1% are outside the derived
    range and require explicit method flags (ARR recommends up to 0.05%).
    """
    area = catchment_area_km2
    _validate_arf_inputs(
        area,
        duration_min,
        aep_percent,
        coefficients,
        allow_short_extrapolation=allow_short_extrapolation,
        allow_rare_aep_extension=allow_rare_aep_extension,
        negative_policy=negative_policy,
    )
    steps: list[str] = []
    if duration_min < 30:
        steps.append("DURATION_LT_30_MIN_EXTRAPOLATION_OPT_IN")
    if aep_percent < 1:
        steps.append("AEP_LT_1_PERCENT_EXTENSION_OPT_IN")
    try:
        factor = _evaluate_arf(area, duration_min, aep_percent, coefficients, negative_policy, steps)
    except (InvalidOperation, OverflowError, ValueError) as exc:
        msg = "Unrepresentable ARR ARF equation result"
        raise ARRFormatError(msg) from exc
    return ARFResult(
        area_km2=area,
        duration_min=duration_min,
        aep_percent=aep_percent,
        factor=factor,
        region=None if coefficients is None else coefficients.region,
        coefficient_origin=None if coefficients is None else coefficients.origin,
        coefficient_source_sha256=None if coefficients is None else coefficients.source_sha256,
        method_steps=tuple(steps),
    )


def apply_arr2019_arf_to_bom_storm(gross: RawHyetograph, calculation: ARFResult) -> AreaAdjustedHyetograph:
    """Apply one factor to a selected *BoM gross* storm; reject other source types.

    The return type differs from RawHyetograph to prevent accidental second use.
    """
    if gross.source_label != "BoM 2016 IFD (raw gross rainfall)":
        msg = "ARF application requires an unadjusted gross BoM source, not a Data Hub-adjusted IFD"
        raise ARRFormatError(msg)
    if gross.duration_min != calculation.duration_min:
        msg = "ARF and source storm duration differ"
        raise ARRFormatError(msg)
    label = gross.probability_label.strip()
    if not label.endswith("%"):
        msg = "ARF application requires a BoM percentage AEP; EY/ARI and one-in-N not accepted"
        raise ARRFormatError(msg)
    try:
        supplied_aep = Decimal(label[:-1])
    except InvalidOperation as exc:
        msg = "Unparseable BoM AEP percentage for ARF application"
        raise ARRFormatError(msg) from exc
    if supplied_aep != calculation.aep_percent:
        msg = "ARF and BoM storm AEP percentages differ"
        raise ARRFormatError(msg)
    depths = tuple(x * calculation.factor for x in gross.increments_mm)
    return AreaAdjustedHyetograph(
        gross=gross,
        arf=calculation,
        increments_mm=depths,
        total_mm=sum(depths, Decimal(0)),
        operations=(*gross.operations, *calculation.method_steps, "ARF_APPLIED_ONCE_TO_GROSS_BOM_RAINFALL"),
    )
