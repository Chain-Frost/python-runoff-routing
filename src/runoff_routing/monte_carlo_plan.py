"""Pure, explicitly configured Monte Carlo samples; no routing or native-RORB claims.

The sampler implements the versioned project method in issue #145; native scientific
qualification remains independent of software correctness.
All probabilities are annual exceedance *fractions*; all stored numbers are decimal strings.
"""

from __future__ import annotations

import hashlib
import hmac
import json
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from decimal import ROUND_HALF_EVEN, Context, Decimal, InvalidOperation, localcontext
from itertools import pairwise
from math import isfinite
from pathlib import Path
from statistics import NormalDist
from typing import TYPE_CHECKING, Never, cast

PLAN_FORMAT = "python-runoff-routing-mc-sample-plan"
SCHEMA_VERSION = 1
RNG_ALGORITHM = "hmac-sha256-53-v1"
RNG_DERIVATION = "canonical-json-domain-separated-v1"
# Explicit v1 choice: conditional TP on sampled AEP, loss independent of rainfall.
# Other conditional loss laws require a new reviewed and implemented profile.
JOINT_POLICY = "conditional-tp-on-aep__independent-storm-il-v1"
MAX_SAMPLES = 1_000_000
MAX_STRATA = 1000

if TYPE_CHECKING:
    from runoff_routing.arr_data import IFDDataset
    from runoff_routing.bom_ifd import BoMIFD
# Pinned computation policy: isolated from callers' Decimal precision, rounding,
# traps and exponent limits. localcontext() must never inherit caller settings.
_SAMPLER_CONTEXT = Context(prec=60, rounding=ROUND_HALF_EVEN)
_MAX_MANIFEST_BYTES = 2 * 1024 * 1024
_MAX_SAMPLE_LINE_BYTES = 16 * 1024
_DIGEST_LENGTH = 64


class SamplePlanError(ValueError):
    """Invalid sampling configuration, persisted plan or sample ledger."""


def _fail(message: str) -> Never:
    raise SamplePlanError(message)


def _obj(value: object, label: str) -> dict[str, object]:
    if not isinstance(value, dict):
        _fail(f"{label} must be a JSON object with string keys")
    candidate = cast("dict[object, object]", value)
    if any(not isinstance(key, str) for key in candidate):
        _fail(f"{label} must be a JSON object with string keys")
    return cast("dict[str, object]", value)


def _list(value: object, label: str) -> list[object]:
    if not isinstance(value, list):
        _fail(f"{label} must be a JSON array")
    return cast("list[object]", value)


def _keys(obj: dict[str, object], required: set[str], label: str, optional: set[str] | None = None) -> None:
    extra = set(obj).difference(required | (optional or set()))
    missing = required.difference(obj)
    if extra or missing:
        _fail(f"{label} has unexpected/missing keys: {sorted(extra)!r} / {sorted(missing)!r}")


def _name(value: object, label: str) -> str:
    if (
        not isinstance(value, str)
        or not 1 <= len(value) <= 128
        or value != value.strip()
        or any(ord(c) < 32 for c in value)
    ):
        _fail(f"{label} requires nonempty trimmed text without control characters")
    return value


def _decimal(value: object, label: str, *, minimum: Decimal = Decimal(0)) -> Decimal:
    if not isinstance(value, str):
        _fail(f"{label} must be a decimal string, not a JSON number")
    try:
        number = Decimal(value)
    except InvalidOperation:
        _fail(f"{label} must be a valid decimal")
    if not number.is_finite() or number < minimum or number.adjusted() > 300 or len(number.as_tuple().digits) > 60:
        _fail(f"{label} must be finite and within supported range")
    return number


def _prob(value: object, label: str) -> Decimal:
    number = _decimal(value, label)
    if number > 1:
        _fail(f"{label} exceeds one; use AEP fraction, not percent")
    return number


def _int(value: object, label: str, minimum: int, maximum: int) -> int:
    if type(value) is not int or not minimum <= value <= maximum:
        _fail(f"{label} requires an integer in {minimum}..{maximum}")
    return value


def _digest(value: object, label: str) -> str:
    if not isinstance(value, str) or len(value) != _DIGEST_LENGTH or any(c not in "0123456789abcdef" for c in value):
        _fail(f"{label} must be a lowercase SHA-256 hexadecimal digest")
    return value


def _json(value: object) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False)


def _sha(value: object) -> str:
    return hashlib.sha256(_json(value).encode("utf-8")).hexdigest()


def _no_duplicates(pairs: list[tuple[str, object]]) -> dict[str, object]:
    values: dict[str, object] = {}
    for key, value in pairs:
        if key in values:
            _fail(f"Duplicate JSON key: {key}")
        values[key] = value
    return values


def _reject_constant(value: str) -> Never:
    _fail(f"Nonstandard JSON constant: {value}")


def _decode(content: str) -> object:
    try:
        return json.loads(content, object_pairs_hook=_no_duplicates, parse_constant=_reject_constant)
    except (ValueError, TypeError):
        _fail("Invalid sample plan JSON")


def _normal_z(p: Decimal) -> Decimal:
    """Finite standard-normal nonexceedance coordinate, with explicit numeric domain."""
    if not 0 < p < 1:
        _fail("AEP probability must be strictly interior for normal-coordinate interpolation")
    with localcontext(_SAMPLER_CONTEXT):
        q = float(Decimal(1) - p)
    if not 0 < q < 1:
        _fail("Source AEP is outside representable normal-coordinate probability support")
    return Decimal(str(NormalDist().inv_cdf(q)))


def _check_spec(spec: dict[str, object]) -> None:
    """Validate a pinned numerical policy before deriving a plan or any draw."""
    _keys(
        spec,
        {
            "schema_version",
            "policy",
            "scenario_id",
            "duration_min",
            "sources",
            "rng",
            "strata",
            "ifd",
            "tp_bins",
            "loss",
            "fixed_parameters",
            "arf_policy",
            "preburst_policy",
            "joint_policy",
            "within_stratum",
        },
        "spec",
    )
    if spec["schema_version"] != SCHEMA_VERSION or type(spec["schema_version"]) is not int:
        _fail("Unsupported Monte Carlo sample-plan schema")
    policy = _obj(spec["policy"], "policy")
    _keys(policy, {"id", "version", "status"}, "policy")
    _name(policy["id"], "policy.id")
    _name(policy["version"], "policy.version")
    if policy["status"] not in {"provisional", "reviewed"}:
        _fail("policy.status must be provisional or reviewed")
    if policy["status"] == "reviewed" and (policy["id"], policy["version"]) != ("monte-carlo-statistics", "1"):
        _fail("Only the adopted monte-carlo-statistics/1 method may declare a reviewed project policy")
    _name(spec["scenario_id"], "scenario_id")
    _int(spec["duration_min"], "duration_min", 1, 10080)
    for key in ("arf_policy", "preburst_policy"):
        _name(spec[key], key)
    if spec["joint_policy"] != JOINT_POLICY:
        _fail("Unsupported joint_policy: explicit independent storm loss with AEP-conditional TP is required")
    if spec["within_stratum"] != "uniform_aep_mass_v1":
        _fail("Only explicit uniform-AEP-mass conditional sampling is implemented")
    sources = _check_sources_and_rng(spec)
    strata = _check_strata(spec)
    _check_ifd(spec, strata)
    _check_temporal_patterns(spec, strata)
    _check_loss(spec, sources)
    _check_fixed_parameters(spec)


def _check_sources_and_rng(spec: dict[str, object]) -> dict[str, object]:
    sources = _obj(spec["sources"], "sources")
    if not {"ifd", "temporal_patterns"}.issubset(sources):
        _fail("An original IFD and temporal-pattern source SHA-256 are required")
    for role, source_sha in sources.items():
        _name(role, "source role")
        _digest(source_sha, f"sources.{role}")
    rng = _obj(spec["rng"], "rng")
    _keys(rng, {"algorithm", "derivation", "root_seed"}, "rng")
    if rng["algorithm"] != RNG_ALGORITHM or rng["derivation"] != RNG_DERIVATION:
        _fail("Unsupported RNG algorithm or stream derivation")
    _int(rng["root_seed"], "rng.root_seed", 0, 2**64 - 1)
    return sources


def _check_strata(spec: dict[str, object]) -> list[object]:
    strata = _list(spec["strata"], "strata")
    if not 1 <= len(strata) <= MAX_STRATA:
        _fail("A bounded, nonempty set of rainfall strata is required")
    ids: set[str] = set()
    previous: Decimal | None = None
    allocated = 0
    for index, value in enumerate(strata):
        item = _obj(value, f"strata[{index}]")
        _keys(item, {"id", "aep_lower", "aep_upper", "probability_mass", "count"}, "stratum")
        stratum_id = _name(item["id"], "stratum.id")
        if ":" in stratum_id or stratum_id in ids:
            _fail("Stratum IDs must be unique and cannot contain ':'")
        ids.add(stratum_id)
        lo = _prob(item["aep_lower"], "stratum.aep_lower")
        hi = _prob(item["aep_upper"], "stratum.aep_upper")
        if not lo < hi or hi == 1 or (previous is not None and previous != lo):
            _fail("Strata must be ascending, disjoint and contiguous; interior gaps/overlap are invalid")
        with localcontext(_SAMPLER_CONTEXT):
            width = hi - lo
        if _prob(item["probability_mass"], "stratum.probability_mass") != width:
            _fail("Stratum mass must equal its AEP interval width")
        allocated += _int(item["count"], "stratum.count", 0, MAX_SAMPLES)
        previous = hi
    if allocated > MAX_SAMPLES:
        _fail("Sample allocation exceeds bounded-plan limit")
    return strata


def _check_ifd(spec: dict[str, object], strata: list[object]) -> None:
    ifd = _obj(spec["ifd"], "ifd")
    _keys(ifd, {"source_id", "interpolation", "points"}, "ifd")
    _name(ifd["source_id"], "ifd.source_id")
    if ifd["interpolation"] != "z_linear_depth_v1":
        _fail("Unsupported IFD interpolation; no silent interpolation/extrapolation")
    points = _list(ifd["points"], "ifd.points")
    if not 2 <= len(points) <= 128:
        _fail("IFD interpolation needs 2..128 source cells")
    previous_p: Decimal | None = None
    previous_depth: Decimal | None = None
    for value in points:
        point = _obj(value, "ifd point")
        _keys(point, {"aep", "depth_mm"}, "ifd point")
        p = _prob(point["aep"], "ifd.aep")
        depth = _decimal(point["depth_mm"], "ifd.depth_mm")
        if p == 0 or p == 1 or (previous_p is not None and p <= previous_p):
            _fail("IFD AEP must increase strictly and stay inside (0,1)")
        if previous_depth is not None and depth > previous_depth:
            _fail("IFD rainfall depth must not increase with AEP")
        _normal_z(p)
        previous_p, previous_depth = p, depth
    if _prob(_obj(strata[0], "stratum")["aep_lower"], "stratum.aep_lower") < _prob(
        _obj(points[0], "IFD")["aep"], "ifd.aep"
    ) or _prob(_obj(strata[-1], "stratum")["aep_upper"], "stratum.aep_upper") > _prob(
        _obj(points[-1], "IFD")["aep"], "ifd.aep"
    ):
        _fail("Modelled AEP strata exceed measured IFD support; tail extrapolation is forbidden")


def _check_tp_choices(choices: list[object]) -> None:
    if not 1 <= len(choices) <= 4096:
        _fail("Eligible TP population must be nonempty and bounded")
    total = Decimal(0)
    event_ids: set[str] = set()
    orders: set[int] = set()
    for choice in choices:
        member = _obj(choice, "TP member")
        _keys(member, {"event_id", "source_order", "probability"}, "TP member")
        event_id = _name(member["event_id"], "TP source EventID")
        if event_id in event_ids:
            _fail("Duplicate TP EventID in conditional population")
        event_ids.add(event_id)
        source_order = _int(member["source_order"], "TP source order", 1, 1_000_000)
        if source_order in orders:
            _fail("Duplicate TP source order in conditional population")
        orders.add(source_order)
        weight = _prob(member["probability"], "TP conditional probability")
        with localcontext(_SAMPLER_CONTEXT):
            total += weight
    if total != 1:
        _fail("TP conditional probabilities must sum to exactly one")


def _check_temporal_patterns(spec: dict[str, object], strata: list[object]) -> None:
    bins = _list(spec["tp_bins"], "tp_bins")
    if not 1 <= len(bins) <= 128:
        _fail("Temporal-pattern bins must be nonempty and bounded")
    expected_lo = _prob(_obj(strata[0], "stratum")["aep_lower"], "stratum.aep_lower")
    bin_ids: set[str] = set()
    for index, value in enumerate(bins):
        band = _obj(value, f"tp_bins[{index}]")
        _keys(band, {"id", "aep_lower", "aep_upper", "choices"}, "tp bin")
        bin_id = _name(band["id"], "tp bin ID")
        if bin_id in bin_ids:
            _fail("Duplicate temporal-pattern conditional-bin identity")
        bin_ids.add(bin_id)
        lo = _prob(band["aep_lower"], "TP bin lower")
        hi = _prob(band["aep_upper"], "TP bin upper")
        if lo != expected_lo or hi <= lo:
            _fail("TP conditional bins must cover all modelled rainfall AEP values without gaps/overlap")
        expected_lo = hi
        _check_tp_choices(_list(band["choices"], "tp choices"))
    if expected_lo != _prob(_obj(strata[-1], "stratum")["aep_upper"], "stratum.aep_upper"):
        _fail("TP bins do not cover the entire rainfall probability domain")


def _check_loss(spec: dict[str, object], sources: dict[str, object]) -> None:
    loss = _obj(spec["loss"], "loss")
    mode = loss.get("mode")
    if mode == "fixed_storm_il":
        _keys(loss, {"mode", "storm_il_mm"}, "loss")
        _decimal(loss["storm_il_mm"], "fixed storm IL")
        return
    if mode == "empirical_scaled_storm_il":
        _check_empirical_loss(loss, sources)
        return
    _fail("Loss mode must be explicitly fixed or source-specified empirical storm IL")


def _check_empirical_loss(loss: dict[str, object], sources: dict[str, object]) -> None:
    _keys(loss, {"mode", "source_id", "median_storm_il_mm", "cdf_quantiles"}, "loss")
    if "initial_loss" not in sources:
        _fail("Empirical loss sampling requires a hashed initial_loss source")
    _name(loss["source_id"], "loss.source_id")
    _decimal(loss["median_storm_il_mm"], "median storm IL")
    quantiles = _list(loss["cdf_quantiles"], "loss.cdf_quantiles")
    if not 2 <= len(quantiles) <= 4096:
        _fail("Empirical loss CDF needs 2..4096 points")
    prev_u: Decimal | None = None
    prev_ratio: Decimal | None = None
    table: list[tuple[Decimal, Decimal]] = []
    for item in quantiles:
        point = _obj(item, "loss quantile")
        _keys(point, {"nonexceedance", "ratio_to_median"}, "loss quantile")
        u = _prob(point["nonexceedance"], "loss nonexceedance probability")
        ratio = _decimal(point["ratio_to_median"], "loss median multiplier")
        if prev_u is not None and (u <= prev_u or ratio < cast("Decimal", prev_ratio)):
            _fail("Loss inverse CDF must be monotone with increasing nonexceedance probability")
        prev_u, prev_ratio = u, ratio
        table.append((u, ratio))
    if table[0][0] != 0 or table[-1][0] != 1:
        _fail("Empirical loss inverse table must cover CDF endpoints zero and one")
    if _linear_table(Decimal("0.5"), table) != 1:
        _fail("Standardised empirical loss inverse must have median factor one")


def _check_fixed_parameters(spec: dict[str, object]) -> None:
    fixed = _list(spec["fixed_parameters"], "fixed_parameters")
    if len(fixed) > 64:
        _fail("Too many fixed parameters")
    fixed_names: set[str] = set()
    for value in fixed:
        item = _obj(value, "fixed parameter")
        _keys(item, {"name", "value", "unit"}, "fixed parameter")
        key = _name(item["name"], "fixed parameter name")
        if key in fixed_names:
            _fail("Duplicate fixed parameter")
        fixed_names.add(key)
        _decimal(item["value"], "fixed parameter value", minimum=Decimal("-1e100"))
        _name(item["unit"], "fixed parameter unit")


def ifd_from_bom(source: BoMIFD, duration_min: int) -> dict[str, object]:
    """Bridge the existing source-preserving BoM reader; never convert EY/ARI implicitly.

    The caller must record ``source.sha256`` under the plan's ``sources.ifd``.
    Intensity (mm/h) is deliberately unsupported until a named conversion policy
    is selected: the table must already contain source depth in mm.
    """
    if source.rainfall_unit != "mm":
        _fail("BoM IFD input must be source depth in mm, not intensity in mm/h")
    if duration_min not in source.durations_min:
        _fail("Selected duration is not present in the original BoM IFD source")
    points: list[dict[str, str]] = []
    for probability in source.probabilities:
        if probability.kind == "AEP_PERCENT":
            with localcontext(_SAMPLER_CONTEXT):
                aep_fraction = probability.value / Decimal(100)
            points.append({"aep": str(aep_fraction), "depth_mm": str(source.depth_mm_at(duration_min, probability))})
    points.sort(key=lambda p: Decimal(p["aep"]))
    if len(points) < 2:
        _fail("Source BoM IFD needs two explicit percentage-AEP points; no EY/ARI conversion")
    return {"source_id": source.label or "BoM IFD source", "interpolation": "z_linear_depth_v1", "points": points}


def ifd_from_arr(table: IFDDataset, duration_min: int) -> dict[str, object]:
    """Bridge the existing ARR table; caller pins original Data Hub source hash."""
    if table.probability_unit != "AEP_PERCENT" or table.depth_unit != "mm":
        _fail("ARR IFD requires original percentage AEP and millimetre depth")
    try:
        index = table.durations_min.index(duration_min)
    except ValueError:
        _fail("Requested duration absent from ARR source table")
    with localcontext(_SAMPLER_CONTEXT):
        points = [
            {"aep": str(aep / Decimal(100)), "depth_mm": str(depth)}
            for aep, depth in zip(table.aep_percent, table.depths_mm[index], strict=True)
        ]
    points.sort(key=lambda p: Decimal(p["aep"]))
    return {"source_id": table.name, "interpolation": "z_linear_depth_v1", "points": points}


def _population_spec(spec: dict[str, object]) -> dict[str, object]:
    result = cast("dict[str, object]", _decode(_json(spec)))
    for item in _list(result["strata"], "strata"):
        _obj(item, "stratum").pop("count")
    return result


def _domain(spec: dict[str, object]) -> dict[str, str]:
    strata = _list(spec["strata"], "strata")
    lo = _prob(_obj(strata[0], "stratum")["aep_lower"], "stratum.aep_lower")
    hi = _prob(_obj(strata[-1], "stratum")["aep_upper"], "stratum.aep_upper")
    with localcontext(_SAMPLER_CONTEXT):
        unallocated = sum(
            (
                _prob(item["probability_mass"], "stratum.mass")
                for item in (_obj(row, "stratum") for row in strata)
                if item["count"] == 0
            ),
            Decimal(0),
        )
        return {
            "convention": "AEP_FRACTION",
            "endpoint_rule": "[lower,upper); final upper closed; inverse draws strictly interior",
            "modelled_mass": str(hi - lo),
            "unallocated_stratum_mass": str(unallocated),
            "allocated_stratum_mass": str(hi - lo - unallocated),
            "lower_unmodelled_mass": str(lo),
            "upper_unmodelled_mass": str(1 - hi),
        }


@dataclass(frozen=True, slots=True)
class SamplePlan:
    """Immutable, canonical plan configuration plus stable and revision identities."""

    _spec_json: str
    population_id: str
    plan_id: str
    parent_plan_id: str | None = None

    @classmethod
    def create(cls, spec: dict[str, object], *, parent_plan_id: str | None = None) -> SamplePlan:
        # Serialize/reparse: detached copies cannot mutate a frozen plan's identity.
        cloned = _obj(_decode(_json(spec)), "spec")
        _check_spec(cloned)
        if parent_plan_id is not None:
            _digest(parent_plan_id, "parent_plan_id")
        return cls(_json(cloned), _sha(_population_spec(cloned)), _sha(cloned), parent_plan_id)

    @classmethod
    def from_dict(cls, raw: object) -> SamplePlan:
        value = _obj(raw, "sample plan")
        _keys(
            value,
            {"format", "schema_version", "spec", "plan_id", "population_id", "parent_plan_id", "domain"},
            "sample plan",
        )
        if value["format"] != PLAN_FORMAT or value["schema_version"] != SCHEMA_VERSION:
            _fail("Unexpected persisted sample-plan format/version")
        parent = value["parent_plan_id"]
        if parent is not None and not isinstance(parent, str):
            _fail("parent_plan_id must be null or a SHA-256 digest")
        plan = cls.create(_obj(value["spec"], "spec"), parent_plan_id=parent)
        if plan.plan_id != value["plan_id"] or plan.population_id != value["population_id"]:
            _fail("Sample-plan revision/population hash mismatch")
        if _domain(plan.spec()) != value["domain"]:
            _fail("Sample-plan modelled/tail probability mass mismatch")
        return plan

    def spec(self) -> dict[str, object]:
        """Return a detached, validated configuration dictionary."""
        return _obj(_decode(self._spec_json), "spec")

    def to_dict(self) -> dict[str, object]:
        spec = self.spec()
        return {
            "format": PLAN_FORMAT,
            "schema_version": SCHEMA_VERSION,
            "spec": spec,
            "domain": _domain(spec),
            "plan_id": self.plan_id,
            "population_id": self.population_id,
            "parent_plan_id": self.parent_plan_id,
        }

    def extend(self, counts: dict[str, int]) -> SamplePlan:
        """Create a new immutable plan revision, retaining old sample IDs and draws."""
        spec = self.spec()
        strata = _list(spec["strata"], "strata")
        old_ids = {_obj(row, "stratum")["id"] for row in strata}
        if set(counts) != old_ids:
            _fail("Extension requires the complete existing stratum allocation")
        increased = False
        for row in strata:
            item = _obj(row, "stratum")
            old = _int(item["count"], "count", 0, MAX_SAMPLES)
            new = _int(counts[cast("str", item["id"])], "new count", old, MAX_SAMPLES)
            increased |= new > old
            item["count"] = new
        if not increased:
            _fail("An extension must increase at least one stratum count")
        return SamplePlan.create(spec, parent_plan_id=self.plan_id)


def _draw(
    seed: int,
    plan: SamplePlan,
    spec: dict[str, object],
    stratum: dict[str, object],
    index: int,
    purpose: str,
) -> Decimal:
    """Adopted HMAC-SHA256/53-v1 stream: identity is independent of allocation and scheduling."""
    payload = {
        "namespace": "python-runoff-routing/mc-sampler",
        "version": 1,
        "population_id": plan.population_id,
        "policy": spec["policy"],
        "sources": spec["sources"],
        "scenario_id": spec["scenario_id"],
        "duration_min": spec["duration_min"],
        "stratum_id": stratum["id"],
        "aep_lower": stratum["aep_lower"],
        "aep_upper": stratum["aep_upper"],
        "index": index,
        "purpose": purpose,
    }
    digest = hmac.new(seed.to_bytes(8, "big"), _json(payload).encode("utf-8"), hashlib.sha256).digest()
    bits = int.from_bytes(digest[:8], "big") >> 11
    with localcontext(_SAMPLER_CONTEXT):
        return Decimal(2 * bits + 1) / Decimal(2**54)


def _linear_table(x: Decimal, points: list[tuple[Decimal, Decimal]], *, descending: bool = False) -> Decimal:
    if x < points[0][0] or x > points[-1][0]:
        _fail("Requested probability is outside explicit table support; no extrapolation")
    for (x0, y0), (x1, y1) in pairwise(points):
        if x <= x1:
            with localcontext(_SAMPLER_CONTEXT):
                result = y0 + (x - x0) * (y1 - y0) / (x1 - x0)
            if result < 0 or (descending and result > y0):
                _fail("Invalid interpolated table value")
            return result
    return points[-1][1]


def _ifd_depth(p: Decimal, ifd: dict[str, object]) -> Decimal:
    """Z-linear *source depth* interpolation; never infer source AEP/EY conversions."""
    points = [
        (_prob(pt["aep"], "IFD aep"), _decimal(pt["depth_mm"], "IFD depth"))
        for pt in (_obj(x, "IFD point") for x in _list(ifd["points"], "ifd.points"))
    ]
    if p < points[0][0] or p > points[-1][0]:
        _fail("Requested probability is outside explicit IFD support; no extrapolation")
    for (p0, d0), (p1, d1) in pairwise(points):
        if p == p0:
            return d0
        if p == p1:
            return d1
        if p0 < p < p1:
            # z = inverse standard-normal CDF at rainfall *nonexceedance* 1-p.
            # The Normal coordinate does not assert normally distributed rainfall depth.
            z = _normal_z(p)
            z0 = _normal_z(p0)
            z1 = _normal_z(p1)
            with localcontext(_SAMPLER_CONTEXT):
                result = d0 + (d1 - d0) * (z - z0) / (z1 - z0)
            if result < 0:
                _fail("Negative IFD depth after z interpolation")
            return result
    _fail("No IFD bracket for a valid sampled probability")


def interpolate_ifd_depth(plan: SamplePlan, aep_fraction: Decimal) -> Decimal:
    """Adopted z-linear source depth interpolation, with exact anchors and no extrapolation."""
    if not aep_fraction.is_finite() or not 0 <= aep_fraction <= 1:
        _fail("AEP must be a finite fraction in [0,1]")
    return _ifd_depth(aep_fraction, _obj(plan.spec()["ifd"], "IFD"))


def _loss_value(u: Decimal, loss: dict[str, object]) -> tuple[Decimal | None, Decimal]:
    if loss["mode"] == "fixed_storm_il":
        return None, _decimal(loss["storm_il_mm"], "storm IL")
    quantiles = [
        (
            _prob(pt["nonexceedance"], "loss CDF"),
            _decimal(pt["ratio_to_median"], "loss ratio"),
        )
        for pt in (_obj(x, "loss quantile") for x in _list(loss["cdf_quantiles"], "loss quantiles"))
    ]
    ratio = _linear_table(u, quantiles)
    with localcontext(_SAMPLER_CONTEXT):
        mm = ratio * _decimal(loss["median_storm_il_mm"], "median storm IL")
    return ratio, mm


def inverse_storm_loss(plan: SamplePlan, nonexceedance: Decimal) -> tuple[Decimal | None, Decimal]:
    """Evaluate an explicitly source-identified loss inverse table or fixed storm IL."""
    if not nonexceedance.is_finite() or not 0 <= nonexceedance <= 1:
        _fail("Loss nonexceedance input must lie in [0,1]")
    return _loss_value(nonexceedance, _obj(plan.spec()["loss"], "loss"))


def _tp_selection(p: Decimal, u: Decimal, bins: list[object]) -> tuple[str, str, int]:
    for item in bins:
        band = _obj(item, "TP band")
        lo = _prob(band["aep_lower"], "TP lower")
        hi = _prob(band["aep_upper"], "TP upper")
        if lo <= p < hi or (p == hi and item is bins[-1]):
            cumulative = Decimal(0)
            for choice in _list(band["choices"], "TP choices"):
                member = _obj(choice, "TP choice")
                with localcontext(_SAMPLER_CONTEXT):
                    cumulative += _prob(member["probability"], "TP probability")
                if u < cumulative:
                    return (
                        _name(band["id"], "TP bin"),
                        _name(member["event_id"], "TP EventID"),
                        _int(member["source_order"], "TP order", 1, 1_000_000),
                    )
    _fail("No eligible TP could be selected; no missing-pattern substitution")


def select_temporal_pattern(plan: SamplePlan, aep_fraction: Decimal, uniform: Decimal) -> tuple[str, str, int]:
    """Select original TP EventID, with [lower, upper) bands and last upper inclusive."""
    if not aep_fraction.is_finite() or not uniform.is_finite() or not 0 <= uniform < 1:
        _fail("Invalid temporal-pattern selection inputs")
    return _tp_selection(aep_fraction, uniform, _list(plan.spec()["tp_bins"], "TP bins"))


@dataclass(frozen=True, slots=True)
class SampleRecord:
    """All effective B-stage draws required for replay, without any hydrograph."""

    plan_id: str
    sample_id: str
    stratum_id: str
    index: int
    scenario_id: str
    duration_min: int
    aep_fraction: Decimal
    event_probability_weight: Decimal
    gross_ifd_depth_mm: Decimal
    tp_bin_id: str
    tp_event_id: str
    tp_source_order: int
    tp_uniform: Decimal
    loss_uniform: Decimal | None
    storm_il_ratio_to_median: Decimal | None
    storm_initial_loss_mm: Decimal

    def to_dict(self) -> dict[str, object]:
        return {
            "plan_id": self.plan_id,
            "sample_id": self.sample_id,
            "stratum_id": self.stratum_id,
            "index": self.index,
            "scenario_id": self.scenario_id,
            "duration_min": self.duration_min,
            "aep_fraction": str(self.aep_fraction),
            "event_probability_weight": str(self.event_probability_weight),
            "gross_ifd_depth_mm": str(self.gross_ifd_depth_mm),
            "tp_bin_id": self.tp_bin_id,
            "tp_event_id": self.tp_event_id,
            "tp_source_order": self.tp_source_order,
            "tp_uniform": str(self.tp_uniform),
            "loss_uniform": None if self.loss_uniform is None else str(self.loss_uniform),
            "storm_il_ratio_to_median": None
            if self.storm_il_ratio_to_median is None
            else str(self.storm_il_ratio_to_median),
            "storm_initial_loss_mm": str(self.storm_initial_loss_mm),
        }

    @classmethod
    def from_dict(cls, value: object) -> SampleRecord:
        obj = _obj(value, "sample record")
        _keys(obj, set(cls.__dataclass_fields__), "sample record")
        nullable = ("loss_uniform", "storm_il_ratio_to_median")
        return cls(
            plan_id=_digest(obj["plan_id"], "sample.plan_id"),
            sample_id=_name(obj["sample_id"], "sample.sample_id"),
            stratum_id=_name(obj["stratum_id"], "sample.stratum_id"),
            index=_int(obj["index"], "sample.index", 0, MAX_SAMPLES),
            scenario_id=_name(obj["scenario_id"], "sample.scenario_id"),
            duration_min=_int(obj["duration_min"], "sample.duration_min", 1, 10080),
            aep_fraction=_prob(obj["aep_fraction"], "sample.aep_fraction"),
            event_probability_weight=_prob(obj["event_probability_weight"], "sample.event_probability_weight"),
            gross_ifd_depth_mm=_decimal(obj["gross_ifd_depth_mm"], "sample.gross_ifd_depth_mm"),
            tp_bin_id=_name(obj["tp_bin_id"], "sample.tp_bin_id"),
            tp_event_id=_name(obj["tp_event_id"], "sample.tp_event_id"),
            tp_source_order=_int(obj["tp_source_order"], "sample.tp_source_order", 1, 1_000_000),
            tp_uniform=_prob(obj["tp_uniform"], "sample.tp_uniform"),
            loss_uniform=None if obj[nullable[0]] is None else _prob(obj[nullable[0]], "sample.loss_uniform"),
            storm_il_ratio_to_median=None
            if obj[nullable[1]] is None
            else _decimal(obj[nullable[1]], "sample.storm_il_ratio_to_median"),
            storm_initial_loss_mm=_decimal(obj["storm_initial_loss_mm"], "sample.storm_initial_loss_mm"),
        )


def _sample_id(plan: SamplePlan, stratum_id: str, index: int) -> str:
    # Full 256-bit logical identity keeps even 128-character stratum IDs in bounds.
    # It excludes plan revision/allocation but includes every population/source choice.
    return f"mc:{_sha({'version': 1, 'population_id': plan.population_id, 'stratum_id': stratum_id, 'index': index})}"


def iter_stratum_samples(
    plan: SamplePlan, stratum_id: str, *, start: int = 0, stop: int | None = None
) -> Iterator[SampleRecord]:
    """Reproducibly yield an arbitrary chunk of one stratum, independent of traversal."""
    spec = plan.spec()
    rows = [_obj(item, "stratum") for item in _list(spec["strata"], "strata")]
    matches = [row for row in rows if row["id"] == stratum_id]
    if len(matches) != 1:
        _fail("Unknown stratum ID")
    row = matches[0]
    count = _int(row["count"], "count", 0, MAX_SAMPLES)
    if count == 0:
        if start != 0 or stop not in {0, None}:
            _fail("Cannot draw from a zero-allocation stratum")
        return
    end = count if stop is None else _int(stop, "stop", 0, count)
    _int(start, "start", 0, end)
    lo = _prob(row["aep_lower"], "stratum lower")
    mass = _prob(row["probability_mass"], "stratum mass")
    with localcontext(_SAMPLER_CONTEXT):
        weight = mass / count
    bins = _list(spec["tp_bins"], "TP bins")
    ifd = _obj(spec["ifd"], "IFD")
    loss = _obj(spec["loss"], "loss")
    seed = _int(_obj(spec["rng"], "rng")["root_seed"], "root seed", 0, 2**64 - 1)
    for index in range(start, end):
        sample_id = _sample_id(plan, stratum_id, index)
        with localcontext(_SAMPLER_CONTEXT):
            aep = lo + mass * _draw(seed, plan, spec, row, index, "rainfall")
        tp_u = _draw(seed, plan, spec, row, index, "tp")
        tp_bin_id, event_id, source_order = _tp_selection(aep, tp_u, bins)
        loss_u = _draw(seed, plan, spec, row, index, "loss") if loss["mode"] == "empirical_scaled_storm_il" else None
        ratio, storm_il = _loss_value(loss_u if loss_u is not None else Decimal("0.5"), loss)
        yield SampleRecord(
            plan_id=plan.plan_id,
            sample_id=sample_id,
            stratum_id=stratum_id,
            index=index,
            scenario_id=_name(spec["scenario_id"], "scenario"),
            duration_min=_int(spec["duration_min"], "duration", 1, 10080),
            aep_fraction=aep,
            event_probability_weight=weight,
            gross_ifd_depth_mm=_ifd_depth(aep, ifd),
            tp_bin_id=tp_bin_id,
            tp_event_id=event_id,
            tp_source_order=source_order,
            tp_uniform=tp_u,
            loss_uniform=loss_u,
            storm_il_ratio_to_median=ratio,
            storm_initial_loss_mm=storm_il,
        )


def iter_plan_samples(plan: SamplePlan) -> Iterator[SampleRecord]:
    """Canonical order only; callers can instead use disjoint arbitrary chunks."""
    for row in _list(plan.spec()["strata"], "strata"):
        yield from iter_stratum_samples(plan, cast("str", _obj(row, "stratum")["id"]))


def _validate_sample_identity(
    plan: SamplePlan, spec: dict[str, object], sample: SampleRecord, row: dict[str, object], count: int
) -> None:
    with localcontext(_SAMPLER_CONTEXT):
        expected_weight = _prob(row["probability_mass"], "mass") / count
    lo = _prob(row["aep_lower"], "lower")
    hi = _prob(row["aep_upper"], "upper")
    if (
        sample.plan_id != plan.plan_id
        or sample.sample_id != _sample_id(plan, sample.stratum_id, sample.index)
        or sample.scenario_id != spec["scenario_id"]
        or sample.duration_min != spec["duration_min"]
        or sample.event_probability_weight != expected_weight
        or not lo < sample.aep_fraction < hi
    ):
        _fail("Sample provenance, identity, AEP or plan-revision weight mismatch")
    if sample.gross_ifd_depth_mm != _ifd_depth(sample.aep_fraction, _obj(spec["ifd"], "IFD")):
        _fail("Sample source-interpolated depth changed")


def _validate_sample_tp_and_loss(spec: dict[str, object], sample: SampleRecord) -> None:
    if not 0 < sample.tp_uniform < 1:
        _fail("Invalid temporal-pattern inverse draw")
    tp_id, event_id, source_order = _tp_selection(
        sample.aep_fraction, sample.tp_uniform, _list(spec["tp_bins"], "TP bins")
    )
    if (tp_id, event_id, source_order) != (sample.tp_bin_id, sample.tp_event_id, sample.tp_source_order):
        _fail("Sample selected an unavailable/incorrect conditional temporal pattern")
    loss = _obj(spec["loss"], "loss")
    if loss["mode"] == "empirical_scaled_storm_il":
        if sample.loss_uniform is None or not 0 < sample.loss_uniform < 1:
            _fail("Missing/invalid empirical loss primitive")
        ratio, mm = _loss_value(sample.loss_uniform, loss)
    else:
        if sample.loss_uniform is not None:
            _fail("Fixed storm loss cannot have a stochastic loss draw")
        ratio, mm = _loss_value(Decimal("0.5"), loss)
    if sample.storm_initial_loss_mm != mm or sample.storm_il_ratio_to_median != ratio:
        _fail("Sample storm initial-loss interpretation/value mismatch")


def iter_validated_samples(
    plan: SamplePlan, records: Iterable[SampleRecord], *, require_complete: bool = True
) -> Iterator[SampleRecord]:
    """Validate unordered explicit samples without invoking the RNG."""
    spec = plan.spec()
    strata = {_name(r["id"], "stratum ID"): r for r in (_obj(x, "stratum") for x in _list(spec["strata"], "strata"))}
    seen: set[tuple[str, int]] = set()
    for sample in records:
        row = strata.get(sample.stratum_id)
        if row is None:
            _fail("Sample refers to an unknown stratum")
        count = _int(row["count"], "count", 0, MAX_SAMPLES)
        if not 0 <= sample.index < count or (sample.stratum_id, sample.index) in seen:
            _fail("Duplicate or out-of-allocation sample index")
        seen.add((sample.stratum_id, sample.index))
        _validate_sample_identity(plan, spec, sample, row, count)
        _validate_sample_tp_and_loss(spec, sample)
        yield sample
    if require_complete and len(seen) != sum(_int(r["count"], "count", 0, MAX_SAMPLES) for r in strata.values()):
        _fail("Incomplete sample ledger: positive-weight planned records are missing")


def validate_sample_records(
    plan: SamplePlan, records: Iterable[SampleRecord], *, require_complete: bool = True
) -> None:
    """Check every sample and total allocated weight without invoking any RNG."""
    for _ in iter_validated_samples(plan, records, require_complete=require_complete):
        pass


def write_sample_plan(prefix: Path, plan: SamplePlan) -> tuple[Path, Path]:
    """Write inspectable JSON manifest and bounded JSONL sample rows; no overwrite."""
    manifest = prefix.with_suffix(".plan.json")
    ledger = prefix.with_suffix(".samples.jsonl")
    if manifest.exists() or ledger.exists():
        _fail("Sample-plan path already exists; do not overwrite an immutable revision")
    # The reader's bound applies to exact encoded bytes. Reject before either
    # file is created; writing an unreadable immutable plan is not permitted.
    manifest_content = json.dumps(plan.to_dict(), indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    if len(manifest_content.encode("utf-8")) > _MAX_MANIFEST_BYTES:
        _fail("Sample-plan manifest exceeds size limit; no files created")
    with manifest.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(manifest_content)
    created_ledger = False
    try:
        with ledger.open("x", encoding="utf-8", newline="\n") as handle:
            created_ledger = True
            for record in iter_plan_samples(plan):
                handle.write(_json(record.to_dict()) + "\n")
    except Exception:
        # Never unlink a ledger that another writer created while this pair was being opened.
        if created_ledger:
            ledger.unlink(missing_ok=True)
        manifest.unlink(missing_ok=True)
        raise
    return manifest, ledger


def read_sample_plan(path: Path) -> SamplePlan:
    if path.stat().st_size > _MAX_MANIFEST_BYTES:
        _fail("Sample-plan manifest exceeds size limit")
    return SamplePlan.from_dict(_decode(path.read_text(encoding="utf-8")))


def iter_saved_sample_records(path: Path, plan: SamplePlan, *, require_complete: bool = True) -> Iterator[SampleRecord]:
    """Bounded streaming ledger verification and replay without sampling again."""

    def _records() -> Iterator[SampleRecord]:
        with path.open("r", encoding="utf-8") as handle:
            for i in range(MAX_SAMPLES + 1):
                # Bound per-line memory before parsing; never read an unbounded arbitrary input line.
                line = handle.readline(_MAX_SAMPLE_LINE_BYTES + 1)
                if not line:
                    return
                if len(line.encode("utf-8")) > _MAX_SAMPLE_LINE_BYTES or not line.endswith("\n"):
                    _fail("Sample row exceeds maximum size or is unterminated")
                if i >= MAX_SAMPLES:
                    _fail("Sample ledger exceeds bounded-plan limit")
                yield SampleRecord.from_dict(_decode(line))

    yield from iter_validated_samples(plan, _records(), require_complete=require_complete)


def read_sample_records(path: Path, plan: SamplePlan, *, require_complete: bool = True) -> list[SampleRecord]:
    """Convenience for bounded small studies; use iter_saved_sample_records for large studies."""
    return list(iter_saved_sample_records(path, plan, require_complete=require_complete))


def normal_coordinate_strata(z_edges: tuple[float, ...], counts: tuple[int, ...]) -> list[dict[str, object]]:
    """Convert increasing nonexceedance-normal z bin edges to ascending AEP strata.

    Returned order is rare-to-frequent in increasing AEP, reversing input z-bin
    counts to preserve each bin's allocation and its true nonuniform p mass.
    """
    if len(z_edges) < 2 or len(counts) != len(z_edges) - 1 or any(not isfinite(z) for z in z_edges):
        _fail("Finite normal-coordinate edges require one sample count per stratum")
    if any(a >= b for a, b in pairwise(z_edges)):
        _fail("Normal-coordinate strata must be strictly increasing")
    probability_edges = [Decimal(str(1 - NormalDist().cdf(z))) for z in reversed(z_edges)]
    if any(a >= b or a <= 0 or b >= 1 for a, b in pairwise(probability_edges)):
        _fail("Normal-coordinate CDF endpoints must be distinct strictly interior AEP fractions")
    allocations = reversed(counts)
    with localcontext(_SAMPLER_CONTEXT):
        return [
            {"id": f"h{i:04d}", "aep_lower": str(a), "aep_upper": str(b), "probability_mass": str(b - a), "count": n}
            for i, (a, b, n) in enumerate(zip(probability_edges[:-1], probability_edges[1:], allocations, strict=True))
        ]
