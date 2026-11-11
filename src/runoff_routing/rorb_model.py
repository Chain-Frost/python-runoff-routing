"""Immutable, source-independent RORB input models and versioned JSON interchange.

The models describe source semantics, not permission to execute a native engine.
All file-boundary numbers are Decimal; no implicit float conversion occurs here.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, Literal, cast

SCHEMA_VERSION = 1
ControlCode = Literal[1, 3, 4, 5, 7]


def _finite(value: Decimal, label: str, *, positive: bool = False) -> None:
    if type(value) is not Decimal or not value.is_finite() or value < 0 or (positive and value == 0):
        message = f"{label} must be a finite {'positive' if positive else 'nonnegative'} Decimal"
        raise ValueError(message)


def _identity(value: str, label: str) -> None:
    if not value or value.strip() != value or any(ord(char) < 32 for char in value):
        message = f"{label} must be a nonempty, unambiguous identifier"
        raise ValueError(message)


def _distinct(values: tuple[str, ...], label: str) -> None:
    if len(values) != len(set(values)):
        message = f"Duplicate {label} identifier"
        raise ValueError(message)


@dataclass(frozen=True, slots=True)
class RoutingValue:
    isa: int
    kc: Decimal
    m: Decimal

    def __post_init__(self) -> None:
        if type(self.isa) is not int or self.isa < 1:
            message = "Routing ISA must be a positive integer"
            raise ValueError(message)
        _finite(self.kc, "kc", positive=True)
        _finite(self.m, "m", positive=True)


@dataclass(frozen=True, slots=True)
class LossValue:
    isa: int
    burst: int
    initial_loss_mm: Decimal
    continuing: Decimal

    def __post_init__(self) -> None:
        if type(self.isa) is not int or self.isa < 1 or type(self.burst) is not int or self.burst < 1:
            message = "Loss ISA and burst must be positive integers"
            raise ValueError(message)
        _finite(self.initial_loss_mm, "initial loss")
        _finite(self.continuing, "continuing loss/coefficient")


@dataclass(frozen=True, slots=True)
class ParameterSet:
    """Documented CMD parameter values; path spellings are references, not dereferenced paths."""

    catchment_reference: str
    storm_reference: str
    lumped_kc: bool
    verbosity: int
    loss_model: Literal[1, 2]
    num_isa: int
    num_bursts: int
    routing: tuple[RoutingValue, ...]
    losses: tuple[LossValue, ...]

    def __post_init__(self) -> None:
        for reference in (self.catchment_reference, self.storm_reference):
            if not reference.strip() or "\r" in reference or "\n" in reference or "\x00" in reference:
                message = "Parameter file reference is empty or contains control characters"
                raise ValueError(message)
        if type(self.lumped_kc) is not bool or type(self.verbosity) is not int or self.verbosity not in (1, 2, 3):
            message = "Invalid CMD lumped flag or verbosity"
            raise ValueError(message)
        if self.loss_model not in (1, 2) or type(self.loss_model) is not int:
            message = "Unsupported CMD loss model"
            raise ValueError(message)
        if type(self.num_isa) is not int or not 1 <= self.num_isa <= 10_000 or self.num_bursts != 1:
            message = "Only a positive ISA count and one explicit burst are characterised"
            raise ValueError(message)
        routing_ids = tuple(item.isa for item in self.routing)
        expected_routing = (1,) if self.lumped_kc else tuple(range(1, self.num_isa + 1))
        if routing_ids != expected_routing:
            message = "Routing ISA identifiers/order do not match CMD count and lumping flag"
            raise ValueError(message)
        if tuple((item.burst, item.isa) for item in self.losses) != tuple(
            (1, index) for index in range(1, self.num_isa + 1)
        ):
            message = "Loss ISA/burst identifiers/order do not match CMD headers"
            raise ValueError(message)


@dataclass(frozen=True, slots=True)
class SubArea:
    identifier: str
    area_km2: Decimal
    label: str = ""

    def __post_init__(self) -> None:
        _identity(self.identifier, "Subarea")
        _finite(self.area_km2, "subarea area", positive=True)


@dataclass(frozen=True, slots=True)
class Reach:
    identifier: str
    length_km: Decimal
    label: str = ""

    def __post_init__(self) -> None:
        _identity(self.identifier, "Reach")
        _finite(self.length_km, "natural reach length", positive=True)


@dataclass(frozen=True, slots=True)
class Storage:
    """Reserved explicit identity; nonempty storage sets are not in the initial writer."""

    identifier: str
    kind: str

    def __post_init__(self) -> None:
        _identity(self.identifier, "Storage")
        _identity(self.kind, "Storage kind")


@dataclass(frozen=True, slots=True)
class PrintLocation:
    identifier: str
    label: str = ""

    def __post_init__(self) -> None:
        _identity(self.identifier, "Print location")


@dataclass(frozen=True, slots=True)
class ControlStep:
    code: ControlCode
    subarea_id: str | None = None
    reach_id: str | None = None
    print_id: str | None = None
    label: str = ""


@dataclass(frozen=True, slots=True)
class CatchmentModel:
    """Explicit computational order, independent of RORB_GE drawing geometry."""

    title: str
    subareas: tuple[SubArea, ...]
    reaches: tuple[Reach, ...]
    controls: tuple[ControlStep, ...]
    print_locations: tuple[PrintLocation, ...]
    storages: tuple[Storage, ...] = ()

    def __post_init__(self) -> None:
        validate_catchment(self)


def validate_catchment(model: CatchmentModel) -> None:  # noqa: C901 -- explicit stack-machine validation
    """Validate the supported stack machine and one-to-one source/reach identity order."""
    if not model.title.strip() or not model.subareas or not model.reaches or not model.controls:
        message = "Catchment requires a title, subareas, reaches and controls"
        raise ValueError(message)
    if model.storages:
        message = "Special storages are not supported by the characterised catchment subset"
        raise ValueError(message)
    _distinct(tuple(area.identifier for area in model.subareas), "subarea")
    _distinct(tuple(reach.identifier for reach in model.reaches), "reach")
    _distinct(tuple(point.identifier for point in model.print_locations), "print")
    areas = tuple(area.identifier for area in model.subareas)
    reaches = tuple(reach.identifier for reach in model.reaches)
    prints = tuple(point.identifier for point in model.print_locations)
    area_cursor = reach_cursor = print_cursor = 0
    running: set[str] | None = None
    stack: list[set[str]] = []
    for step in model.controls:
        if step.code == 1:
            if (
                area_cursor >= len(areas)
                or reach_cursor >= len(reaches)
                or step.subarea_id != areas[area_cursor]
                or step.reach_id != reaches[reach_cursor]
                or step.print_id is not None
            ):
                message = "Code 1 must consume the next subarea and reach exactly once"
                raise ValueError(message)
            if running is not None and not stack:
                message = "New subarea would overwrite an unstored running hydrograph"
                raise ValueError(message)
            running = {areas[area_cursor]}
            area_cursor += 1
            reach_cursor += 1
        elif step.code == 5:
            if (
                running is None
                or reach_cursor >= len(reaches)
                or step.reach_id != reaches[reach_cursor]
                or step.subarea_id is not None
                or step.print_id is not None
            ):
                message = "Code 5 requires a running hydrograph and the next reach"
                raise ValueError(message)
            reach_cursor += 1
        elif step.code == 3:
            if running is None or step.reach_id is not None or step.subarea_id is not None or step.print_id is not None:
                message = "Code 3 requires a running hydrograph without additional operands"
                raise ValueError(message)
            stack.append(set(running))
        elif step.code == 4:
            if (
                running is None
                or not stack
                or any(value is not None for value in (step.reach_id, step.subarea_id, step.print_id))
            ):
                message = "Code 4 requires a stored and a running hydrograph"
                raise ValueError(message)
            stored = stack.pop()
            if stored & running:
                message = "Confluence would count a subarea more than once"
                raise ValueError(message)
            running = stored | running
        elif step.code == 7:
            if (
                running is None
                or print_cursor >= len(prints)
                or step.print_id != prints[print_cursor]
                or step.reach_id is not None
                or step.subarea_id is not None
            ):
                message = "Code 7 must reference the next explicit print location"
                raise ValueError(message)
            print_cursor += 1
        else:
            message = f"Unsupported control code {step.code}"
            raise ValueError(message)
    if (
        stack
        or running != set(areas)
        or area_cursor != len(areas)
        or reach_cursor != len(reaches)
        or print_cursor != len(prints)
        or not prints
        or model.controls[-1].code != 7
    ):
        message = "Unbalanced catchment vector or missing final complete outlet print"
        raise ValueError(message)


@dataclass(frozen=True, slots=True)
class StormModel:
    """Explicit DESIGN pattern: source-order depth mapping is not a spatial join."""

    title: str
    timestep_hours: Decimal
    calculation_increments: int
    start_increment: int
    percentages: tuple[Decimal, ...]
    depths_mm: tuple[Decimal, ...]
    subarea_ids: tuple[str, ...]
    pluviograph_count: int = 1
    isa_count: int = 1
    burst_count: int = 1

    def __post_init__(self) -> None:
        validate_storm(self)


def validate_storm(model: StormModel) -> None:
    if not model.title.strip():
        message = "Storm title is required"
        raise ValueError(message)
    _finite(model.timestep_hours, "storm timestep", positive=True)
    if (
        type(model.calculation_increments) is not int
        or type(model.start_increment) is not int
        or model.start_increment < 0
        or model.calculation_increments < model.start_increment + len(model.percentages)
        or model.calculation_increments > 1_000_000
    ):
        message = "Storm horizon must cover all defined rainfall intervals"
        raise ValueError(message)
    if (model.pluviograph_count, model.isa_count, model.burst_count) != (1, 1, 1):
        message = "Only one explicit DESIGN pluviograph, ISA and burst is characterised"
        raise ValueError(message)
    if not model.percentages or not model.depths_mm or len(model.depths_mm) != len(model.subarea_ids):
        message = "Storm needs a pattern and one depth per ordered subarea"
        raise ValueError(message)
    _distinct(model.subarea_ids, "storm subarea")
    for name in model.subarea_ids:
        _identity(name, "Storm subarea")
    for value in model.percentages:
        _finite(value, "temporal pattern percentage")
    if abs(sum(model.percentages, Decimal(0)) - Decimal(100)) > Decimal("0.05"):
        message = "Temporal pattern percentages must total 100 within recorded precision"
        raise ValueError(message)
    for depth in model.depths_mm:
        _finite(depth, "storm rainfall depth")


@dataclass(frozen=True, slots=True)
class RunModel:
    """Cross-document domain model; still not verified for numerical execution."""

    parameters: ParameterSet
    catchment: CatchmentModel
    storm: StormModel

    def __post_init__(self) -> None:
        if self.parameters.num_isa != self.storm.isa_count or self.parameters.num_bursts != self.storm.burst_count:
            message = "Parameter ISA/burst counts differ from explicit storm mappings"
            raise ValueError(message)
        if tuple(item.identifier for item in self.catchment.subareas) != self.storm.subarea_ids:
            message = "Storm depth source order/IDs differ from catchment subarea order"
            raise ValueError(message)


RorbModel = ParameterSet | CatchmentModel | StormModel | RunModel


def _units(kind: str, loss_model: int = 1) -> dict[str, str]:
    common = {"area": "km2", "reach_length": "km", "time": "hour", "rainfall_depth": "mm"}
    if kind in ("parameters", "run"):
        common.update(
            {
                "kc": "RORB_coefficient",
                "m": "dimensionless",
                "initial_loss": "mm",
                "continuing": "mm/hour" if loss_model == 1 else "runoff_coefficient",
            }
        )
    if kind in ("storm", "run"):
        common["temporal_pattern"] = "percent"
    return common


def _parameter_data(model: ParameterSet) -> dict[str, Any]:
    return {
        "catchment_reference": model.catchment_reference,
        "storm_reference": model.storm_reference,
        "lumped_kc": model.lumped_kc,
        "verbosity": model.verbosity,
        "loss_model": model.loss_model,
        "num_isa": model.num_isa,
        "num_bursts": model.num_bursts,
        "routing": [{"isa": item.isa, "kc": str(item.kc), "m": str(item.m)} for item in model.routing],
        "losses": [
            {
                "isa": item.isa,
                "burst": item.burst,
                "initial_loss_mm": str(item.initial_loss_mm),
                "continuing": str(item.continuing),
            }
            for item in model.losses
        ],
    }


def _catchment_data(model: CatchmentModel) -> dict[str, Any]:
    return {
        "title": model.title,
        "subareas": [
            {"identifier": item.identifier, "area_km2": str(item.area_km2), "label": item.label}
            for item in model.subareas
        ],
        "reaches": [
            {"identifier": item.identifier, "length_km": str(item.length_km), "label": item.label}
            for item in model.reaches
        ],
        "controls": [
            {
                "code": item.code,
                "subarea_id": item.subarea_id,
                "reach_id": item.reach_id,
                "print_id": item.print_id,
                "label": item.label,
            }
            for item in model.controls
        ],
        "print_locations": [{"identifier": item.identifier, "label": item.label} for item in model.print_locations],
        "storages": [{"identifier": item.identifier, "kind": item.kind} for item in model.storages],
    }


def _storm_data(model: StormModel) -> dict[str, Any]:
    return {
        "title": model.title,
        "timestep_hours": str(model.timestep_hours),
        "calculation_increments": model.calculation_increments,
        "start_increment": model.start_increment,
        "percentages": [str(value) for value in model.percentages],
        "depths_mm": [str(value) for value in model.depths_mm],
        "subarea_ids": list(model.subarea_ids),
        "pluviograph_count": model.pluviograph_count,
        "isa_count": model.isa_count,
        "burst_count": model.burst_count,
    }


def to_dict(model: RorbModel) -> dict[str, Any]:
    """Stable, explicitly versioned JSON-compatible data. Decimals are strings."""
    if isinstance(model, RunModel):
        kind = "run"
        body = {
            "parameters": _parameter_data(model.parameters),
            "catchment": _catchment_data(model.catchment),
            "storm": _storm_data(model.storm),
        }
        loss_model = model.parameters.loss_model
    elif isinstance(model, ParameterSet):
        kind, body, loss_model = "parameters", _parameter_data(model), model.loss_model
    elif isinstance(model, CatchmentModel):
        kind, body, loss_model = "catchment", _catchment_data(model), 1
    else:
        kind, body, loss_model = "storm", _storm_data(model), 1
    return {"schema_version": SCHEMA_VERSION, "kind": kind, "units": _units(kind, loss_model), "model": body}


def to_json(model: RorbModel) -> str:
    return json.dumps(to_dict(model), ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n"


def _object(raw: object, names: set[str]) -> dict[str, object]:
    if not isinstance(raw, dict):
        message = "Expected JSON object"
        raise TypeError(message)
    record = cast("dict[str, object]", raw)
    if set(record) != names:
        message = f"Expected exact JSON object fields: {sorted(names)}"
        raise ValueError(message)
    return record


def _items(raw: object) -> list[object]:
    if not isinstance(raw, list):
        message = "Expected JSON array"
        raise TypeError(message)
    return cast("list[object]", raw)


def _string(value: object) -> str:
    if not isinstance(value, str):
        message = "Expected JSON string"
        raise TypeError(message)
    return value


def _field_str(record: dict[str, object], key: str) -> str:
    return _string(record[key])


def _optional_str(record: dict[str, object], key: str) -> str | None:
    raw = record[key]
    return None if raw is None else _string(raw)


def _integer_field(record: dict[str, object], key: str) -> int:
    value = record[key]
    if type(value) is not int:
        message = f"Expected integer for {key}"
        raise TypeError(message)
    return value


def _bool_field(record: dict[str, object], key: str) -> bool:
    value = record[key]
    if type(value) is not bool:
        message = f"Expected boolean for {key}"
        raise TypeError(message)
    return value


def _decimal(raw: object) -> Decimal:
    if not isinstance(raw, str):
        message = "JSON numeric values must be decimal strings"
        raise TypeError(message)
    if re.fullmatch(r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eEdD][+-]?[0-9]+)?", raw) is None:
        message = "Invalid decimal string in JSON"
        raise ValueError(message)
    try:
        result = Decimal(raw.replace("D", "E").replace("d", "E"))
    except InvalidOperation as exc:
        message = "Invalid decimal string in JSON"
        raise ValueError(message) from exc
    if not result.is_finite():
        message = "Non-finite decimal string in JSON"
        raise ValueError(message)
    return result


def _routing(raw: object) -> RoutingValue:
    record = _object(raw, {"isa", "kc", "m"})
    return RoutingValue(_integer_field(record, "isa"), _decimal(record["kc"]), _decimal(record["m"]))


def _loss(raw: object) -> LossValue:
    record = _object(raw, {"isa", "burst", "initial_loss_mm", "continuing"})
    return LossValue(
        _integer_field(record, "isa"),
        _integer_field(record, "burst"),
        _decimal(record["initial_loss_mm"]),
        _decimal(record["continuing"]),
    )


def _params(raw: object) -> ParameterSet:
    record = _object(
        raw,
        {
            "catchment_reference",
            "storm_reference",
            "lumped_kc",
            "verbosity",
            "loss_model",
            "num_isa",
            "num_bursts",
            "routing",
            "losses",
        },
    )
    loss_model = _integer_field(record, "loss_model")
    if loss_model not in (1, 2):
        message = "Unsupported CMD loss model"
        raise ValueError(message)
    recognised_loss: Literal[1, 2] = 1 if loss_model == 1 else 2
    return ParameterSet(
        _field_str(record, "catchment_reference"),
        _field_str(record, "storm_reference"),
        _bool_field(record, "lumped_kc"),
        _integer_field(record, "verbosity"),
        recognised_loss,
        _integer_field(record, "num_isa"),
        _integer_field(record, "num_bursts"),
        tuple(_routing(item) for item in _items(record["routing"])),
        tuple(_loss(item) for item in _items(record["losses"])),
    )


def _subarea(raw: object) -> SubArea:
    record = _object(raw, {"identifier", "area_km2", "label"})
    return SubArea(_field_str(record, "identifier"), _decimal(record["area_km2"]), _field_str(record, "label"))


def _reach(raw: object) -> Reach:
    record = _object(raw, {"identifier", "length_km", "label"})
    return Reach(_field_str(record, "identifier"), _decimal(record["length_km"]), _field_str(record, "label"))


def _control(raw: object) -> ControlStep:
    record = _object(raw, {"code", "subarea_id", "reach_id", "print_id", "label"})
    code = _integer_field(record, "code")
    if code not in (1, 3, 4, 5, 7):
        message = "Unrecognised RORB computational control code"
        raise ValueError(message)
    return ControlStep(
        code,
        _optional_str(record, "subarea_id"),
        _optional_str(record, "reach_id"),
        _optional_str(record, "print_id"),
        _field_str(record, "label"),
    )


def _print_location(raw: object) -> PrintLocation:
    record = _object(raw, {"identifier", "label"})
    return PrintLocation(_field_str(record, "identifier"), _field_str(record, "label"))


def _storage(raw: object) -> Storage:
    record = _object(raw, {"identifier", "kind"})
    return Storage(_field_str(record, "identifier"), _field_str(record, "kind"))


def _catchment(raw: object) -> CatchmentModel:
    record = _object(raw, {"title", "subareas", "reaches", "controls", "print_locations", "storages"})
    return CatchmentModel(
        _field_str(record, "title"),
        tuple(_subarea(item) for item in _items(record["subareas"])),
        tuple(_reach(item) for item in _items(record["reaches"])),
        tuple(_control(item) for item in _items(record["controls"])),
        tuple(_print_location(item) for item in _items(record["print_locations"])),
        tuple(_storage(item) for item in _items(record["storages"])),
    )


def _storm(raw: object) -> StormModel:
    record = _object(
        raw,
        {
            "title",
            "timestep_hours",
            "calculation_increments",
            "start_increment",
            "percentages",
            "depths_mm",
            "subarea_ids",
            "pluviograph_count",
            "isa_count",
            "burst_count",
        },
    )
    return StormModel(
        _field_str(record, "title"),
        _decimal(record["timestep_hours"]),
        _integer_field(record, "calculation_increments"),
        _integer_field(record, "start_increment"),
        tuple(_decimal(item) for item in _items(record["percentages"])),
        tuple(_decimal(item) for item in _items(record["depths_mm"])),
        tuple(_string(item) for item in _items(record["subarea_ids"])),
        _integer_field(record, "pluviograph_count"),
        _integer_field(record, "isa_count"),
        _integer_field(record, "burst_count"),
    )


def from_dict(raw: dict[str, Any]) -> RorbModel:
    """Reject unknown schema fields/units instead of constructing a partial model."""
    data = _object(raw, {"schema_version", "kind", "units", "model"})
    if type(data["schema_version"]) is not int or data["schema_version"] != SCHEMA_VERSION:
        message = "Unknown RORB JSON schema version"
        raise ValueError(message)
    kind = _field_str(data, "kind")
    if kind not in ("parameters", "catchment", "storm", "run"):
        message = "Unknown RORB JSON model kind"
        raise ValueError(message)
    body = data["model"]
    if kind == "parameters":
        model: RorbModel = _params(body)
    elif kind == "catchment":
        model = _catchment(body)
    elif kind == "storm":
        model = _storm(body)
    else:
        d = _object(body, {"parameters", "catchment", "storm"})
        model = RunModel(_params(d["parameters"]), _catchment(d["catchment"]), _storm(d["storm"]))
    loss_model = (
        model.parameters.loss_model
        if isinstance(model, RunModel)
        else (model.loss_model if isinstance(model, ParameterSet) else 1)
    )
    if data["units"] != _units(kind, loss_model):
        message = "RORB JSON units do not match the explicit model unit contract"
        raise ValueError(message)
    return model


def from_json(text: str) -> RorbModel:
    """Load only an explicit interchange schema; JSON cannot silently carry NaN."""

    def reject_constant(value: str) -> None:
        message = f"Nonstandard JSON constant: {value}"
        raise ValueError(message)

    decoded: object = json.loads(text, parse_constant=reject_constant)
    if not isinstance(decoded, dict):
        message = "RORB JSON root must be an object"
        raise TypeError(message)
    return from_dict(cast("dict[str, Any]", decoded))
