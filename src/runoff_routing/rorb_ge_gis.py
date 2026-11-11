"""Optional GDAL/OGR GIS input validation for the RORB_GE authoring boundary.

Adapted from PyROMB PR #16 at a323d5709f7c (MIT, Copyright 2022 Tom
Norman; see docs/third_party/PYROMB_LICENSE.txt). GDAL is loaded only
when the caller explicitly requests polygon/centroid matching.
"""

from __future__ import annotations

import importlib
import math
from decimal import Decimal
from typing import Protocol, SupportsFloat, cast

from .rorb_ge_authoring import GeDrawing, GeNode, GeReach, Point
from .rorb_model import CatchmentModel


class FeatureRecord(Protocol):
    """Attribute records returned by dictionaries or QGIS feature proxies."""

    def __getitem__(self, field: str, /) -> object: ...


class VectorLayer(Protocol):
    """The small PyROMB-compatible geometry and attribute interface."""

    def __len__(self) -> int: ...

    def record(self, index: int) -> FeatureRecord: ...

    def geometry(self, index: int) -> list[Point]: ...


class _OgrGeometry(Protocol):
    def AddPoint_2D(self, x: float, y: float) -> None: ...  # noqa: N802 -- exact external OGR naming convention

    def AddGeometry(self, geometry: _OgrGeometry) -> None: ...  # noqa: N802 -- exact external OGR naming convention

    def IsEmpty(self) -> bool: ...  # noqa: N802 -- exact external OGR naming convention

    def IsValid(self) -> bool: ...  # noqa: N802 -- exact external OGR naming convention

    def GetArea(self) -> float: ...  # noqa: N802 -- exact external OGR naming convention

    def Contains(self, geometry: _OgrGeometry) -> bool: ...  # noqa: N802 -- exact external OGR naming convention


class _OgrModule(Protocol):
    wkbLinearRing: int  # noqa: N815 -- exact GDAL constant
    wkbPolygon: int  # noqa: N815 -- exact GDAL constant
    wkbPoint: int  # noqa: N815 -- exact GDAL constant

    def Geometry(self, kind: int) -> _OgrGeometry: ...  # noqa: N802 -- exact external OGR naming convention


def _ogr() -> _OgrModule:
    try:
        module = importlib.import_module("osgeo.ogr")
    except ImportError as exc:
        message = "Optional GIS authoring requires GDAL/OGR in the QGIS/OSGeo4W environment"
        raise RuntimeError(message) from exc
    return cast("_OgrModule", module)


def _missing(value: object) -> bool:
    if value is None or (isinstance(value, str) and not value.strip()):
        return True
    null_check = getattr(value, "isNull", None)
    return bool(null_check()) if callable(null_check) else False


def _record(layer: VectorLayer, index: int, kind: str, required: tuple[str, ...]) -> FeatureRecord:
    record = layer.record(index)
    for field in required:
        try:
            value = record[field]
        except (KeyError, IndexError, TypeError) as exc:
            message = f"{kind} feature {index} is missing required field {field!r}"
            raise ValueError(message) from exc
        if _missing(value):
            message = f"{kind} feature {index} has empty required field {field!r}"
            raise ValueError(message)
    return record


def _number(value: object, kind: str, index: int, field: str) -> float:
    if isinstance(value, bool):
        message = f"{kind} feature {index}: {field!r} must be numeric"
        raise ValueError(message)
    try:
        result = float(cast("str | SupportsFloat", value))
    except (TypeError, ValueError, OverflowError) as exc:
        message = f"{kind} feature {index}: {field!r} must be numeric"
        raise ValueError(message) from exc
    if not math.isfinite(result):
        message = f"{kind} feature {index}: {field!r} must be finite"
        raise ValueError(message)
    return result


def _identifier(value: object, kind: str, index: int) -> str:
    if not isinstance(value, str):
        message = f"{kind} feature {index}: id must be a string"
        raise TypeError(message)
    if not value.strip() or value != value.strip():
        message = f"{kind} feature {index}: id must be nonempty without surrounding whitespace"
        raise ValueError(message)
    return value


def _binary(value: object, kind: str, index: int, field: str) -> bool:
    if isinstance(value, bool):
        return value
    if type(value) is not int or value not in (0, 1):
        message = f"{kind} feature {index}: {field!r} must be 0 or 1"
        raise ValueError(message)
    return bool(value)


def _point(layer: VectorLayer, index: int, kind: str) -> Point:
    points = layer.geometry(index)
    if len(points) != 1:
        message = f"{kind} feature {index} requires exactly one XY point"
        raise ValueError(message)
    x, y = points[0]
    if not math.isfinite(x) or not math.isfinite(y):
        message = f"{kind} feature {index} has non-finite XY coordinates"
        raise ValueError(message)
    return x, y


def _polygon(vertices: list[Point], ogr: _OgrModule, index: int) -> _OgrGeometry:
    """Port the PR #16 single exterior-ring validation without auto-repair."""
    if len(vertices) < 3 or any(len(point) != 2 or not all(math.isfinite(v) for v in point) for point in vertices):
        message = f"Basin feature {index} needs at least three valid XY coordinates"
        raise ValueError(message)
    origin = vertices[0]
    distinct: set[Point] = set()
    closed = False
    for vertex in vertices:
        distinct.add(vertex)
        if vertex == origin and len(distinct) >= 3:
            closed = True
        elif closed:
            message = f"Basin feature {index} has unsupported holes or multipart rings"
            raise ValueError(message)
    points = vertices if vertices[-1] == origin else [*vertices, origin]
    if len(set(points[:-1])) < 3:
        message = f"Basin feature {index} needs three distinct polygon vertices"
        raise ValueError(message)
    ring = ogr.Geometry(ogr.wkbLinearRing)
    for x, y in points:
        ring.AddPoint_2D(x, y)
    polygon = ogr.Geometry(ogr.wkbPolygon)
    polygon.AddGeometry(ring)
    if polygon.IsEmpty() or not polygon.IsValid() or not math.isfinite(polygon.GetArea()) or polygon.GetArea() <= 0:
        message = f"Basin feature {index} is invalid or has non-positive area"
        raise ValueError(message)
    return polygon


def _assigned_areas(
    centroids: VectorLayer, basins: VectorLayer, model: CatchmentModel, ogr: _OgrModule
) -> tuple[GeNode, ...]:
    if not len(centroids) or not len(basins):
        message = "Centroid and basin layers must both contain records"
        raise ValueError(message)
    polygons = [_polygon(basins.geometry(i), ogr, i) for i in range(len(basins))]
    assigned: set[int] = set()
    areas = {subarea.identifier: subarea for subarea in model.subareas}
    nodes: list[GeNode] = []
    for i in range(len(centroids)):
        record = _record(centroids, i, "Centroid", ("id", "fi"))
        identity = _identifier(record["id"], "Centroid", i)
        if identity not in areas:
            message = f"Centroid feature {i}: ID {identity!r} does not match a computational subarea"
            raise ValueError(message)
        if _number(record["fi"], "Centroid", i, "fi") != 0:
            message = f"Centroid feature {i}: nonzero impervious fraction is unsupported"
            raise ValueError(message)
        point = _point(centroids, i, "Centroid")
        observed = ogr.Geometry(ogr.wkbPoint)
        observed.AddPoint_2D(*point)
        matches = [j for j, polygon in enumerate(polygons) if polygon.Contains(observed)]
        if len(matches) != 1:
            message = f"Centroid {identity!r} must be strictly inside one basin polygon; matched {matches}"
            raise ValueError(message)
        if matches[0] in assigned:
            message = f"Basin polygon {matches[0]} is already assigned to another centroid"
            raise ValueError(message)
        assigned.add(matches[0])
        area_km2 = Decimal(str(polygons[matches[0]].GetArea() / 1_000_000))
        if abs(area_km2 - areas[identity].area_km2) > Decimal("0.0000005"):
            message = f"Centroid {identity!r} OGR area differs from its computational km2 area"
            raise ValueError(message)
        nodes.append(GeNode(identity, *point, identity, False, areas[identity].label))
    if len(assigned) != len(polygons):
        missing = sorted(set(range(len(polygons))) - assigned)
        message = f"Unassigned basin polygons: {missing}"
        raise ValueError(message)
    return tuple(nodes)


def drawing_from_layers(
    model: CatchmentModel,
    centroids: VectorLayer,
    basins: VectorLayer,
    confluences: VectorLayer,
    reaches: VectorLayer,
    *,
    projected_crs: str,
    endpoint_tolerance_m: float = 0.000001,
) -> GeDrawing:
    """Validate PyROMB-style layers and return optional drawing metadata.

    Source CRS and dimensionality must be verified by the caller. The input
    interface exposes flattened XY only; loss of source parts/rings/CRS
    cannot be detected once a QGIS adapter has discarded that information.
    """
    ogr = _ogr()
    area_nodes = _assigned_areas(centroids, basins, model, ogr)
    confluence_nodes: list[GeNode] = []
    for index in range(len(confluences)):
        record = _record(confluences, index, "Confluence", ("id", "out"))
        name = _identifier(record["id"], "Confluence", index)
        x, y = _point(confluences, index, "Confluence")
        outlet = _binary(record["out"], "Confluence", index, "out")
        confluence_nodes.append(GeNode(name, x, y, outlet=outlet))
    outlet_count = sum(node.outlet for node in confluence_nodes)
    if outlet_count != 1:
        message = f"Confluence layer requires exactly one outlet; found {outlet_count}"
        raise ValueError(message)
    model_reaches = {reach.identifier for reach in model.reaches}
    links: list[GeReach] = []
    for index in range(len(reaches)):
        record = _record(reaches, index, "Reach", ("id", "t", "s"))
        identifier = _identifier(record["id"], "Reach", index)
        if identifier not in model_reaches:
            message = f"Reach feature {index}: ID {identifier!r} is not a computational reach"
            raise ValueError(message)
        reach_type = _number(record["t"], "Reach", index, "t")
        if reach_type != 1:
            message = f"Reach feature {index}: only natural reach type 1 is supported"
            raise ValueError(message)
        slope = _number(record["s"], "Reach", index, "s")
        if slope < 0:
            message = f"Reach feature {index}: slope cannot be negative"
            raise ValueError(message)
        points = tuple(reaches.geometry(index))
        links.append(GeReach(identifier, points))
    return GeDrawing(
        (*confluence_nodes, *area_nodes),
        tuple(links),
        projected_crs,
        "m",
        endpoint_tolerance_m,
    )
