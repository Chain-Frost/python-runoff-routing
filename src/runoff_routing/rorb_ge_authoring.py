"""Optional RORB_GE 002 drawing authoring for an existing typed catchment.

Topology checks and GE field layouts are adapted from PyROMB PR #16 (MIT,
Copyright 2022 Tom Norman; see docs/third_party/PYROMB_LICENSE.txt).
The computational vector comes from serialize_catg; drawing coordinates
never reconstruct or reorder the routing instructions.
"""

from __future__ import annotations

import math
from collections import deque
from dataclasses import dataclass
from decimal import Decimal
from itertools import pairwise
from typing import Literal

from .rorb_codec import parse_catg, serialize_catg
from .rorb_model import CatchmentModel

Point = tuple[float, float]
MetreUnit = Literal["m"]


def _finite(value: float, description: str) -> None:
    if not math.isfinite(value):
        message = f"{description} must be finite"
        raise ValueError(message)


def _name(value: str, description: str) -> None:
    if not value or value != value.strip() or any(ord(char) < 32 for char in value):
        message = f"{description} needs a nonempty single-line name"
        raise ValueError(message)


@dataclass(frozen=True, slots=True)
class GeNode:
    """One explicitly named node in a projected-metre GIS network."""

    identifier: str
    x_m: float
    y_m: float
    subarea_id: str | None = None
    outlet: bool = False
    display_label: str = ""

    def __post_init__(self) -> None:
        _name(self.identifier, "Node")
        _finite(self.x_m, "Node x")
        _finite(self.y_m, "Node y")
        if self.subarea_id is not None:
            _name(self.subarea_id, "Subarea")
        if self.outlet and self.subarea_id is not None:
            message = "A terminal outlet may not also be a source subarea"
            raise ValueError(message)
        if "\r" in self.display_label or "\n" in self.display_label or len(self.display_label) > 28:
            message = "Graphical labels must fit the 28-character GE 002 name field"
            raise ValueError(message)


@dataclass(frozen=True, slots=True)
class GeReach:
    """GIS geometry linked explicitly to a computational reach identifier."""

    identifier: str
    vertices_m: tuple[Point, ...]

    def __post_init__(self) -> None:
        _name(self.identifier, "Reach")
        if len(self.vertices_m) < 2:
            message = f"Reach {self.identifier!r} requires at least two vertices"
            raise ValueError(message)
        for i, vertex in enumerate(self.vertices_m):
            if len(vertex) != 2:
                message = f"Reach {self.identifier!r} vertex {i} requires XY coordinates"
                raise ValueError(message)
            _finite(vertex[0], f"Reach {self.identifier!r} vertex {i} x")
            _finite(vertex[1], f"Reach {self.identifier!r} vertex {i} y")
        if not any(start != end for start, end in pairwise(self.vertices_m)):
            message = f"Reach {self.identifier!r} has zero geometric length"
            raise ValueError(message)


@dataclass(frozen=True, slots=True)
class GeDrawing:
    """Optional graphical topology, not an authority for computational ordering."""

    nodes: tuple[GeNode, ...]
    reaches: tuple[GeReach, ...]
    crs: str
    unit: MetreUnit
    endpoint_tolerance_m: float = 0.000001

    def __post_init__(self) -> None:
        _name(self.crs, "Projected CRS")
        if self.unit != "m" or self.crs.upper() in {"EPSG:4326", "EPSG:4283", "EPSG:7844"}:
            message = "Drawing requires a projected CRS with coordinates measured in metres"
            raise ValueError(message)
        _finite(self.endpoint_tolerance_m, "Endpoint tolerance")
        if self.endpoint_tolerance_m < 0:
            message = "Endpoint tolerance must be nonnegative"
            raise ValueError(message)
        if len(self.nodes) < 2 or not self.reaches:
            message = "Graphical catchment needs at least two nodes and one reach"
            raise ValueError(message)


@dataclass(frozen=True, slots=True)
class _DirectedNetwork:
    """GIS direction rooted at the outlet and checked against the control vector."""

    downstream: dict[str, str | None]
    edge_nodes: dict[str, tuple[str, str]]


def _endpoint_index(point: Point, nodes: tuple[GeNode, ...], tolerance: float, reach: str) -> int:
    matches = [
        index for index, node in enumerate(nodes) if math.hypot(point[0] - node.x_m, point[1] - node.y_m) <= tolerance
    ]
    if len(matches) != 1:
        message = f"Reach {reach!r} endpoint {point} matches {len(matches)} nodes within {tolerance:g} m"
        raise ValueError(message)
    return matches[0]


def _network(drawing: GeDrawing) -> _DirectedNetwork:  # noqa: C901 -- validate complete tree preflight
    """Validate exact endpoint identity and one connected outlet-rooted tree."""
    nodes = drawing.nodes
    reaches = drawing.reaches
    identifiers = [*(node.identifier for node in nodes), *(reach.identifier for reach in reaches)]
    if len(set(identifiers)) != len(identifiers):
        message = "Graphical node/reach identifiers must be globally unique"
        raise ValueError(message)
    outlets = [i for i, node in enumerate(nodes) if node.outlet]
    if len(outlets) != 1:
        message = f"Expected one graphical outlet, found {len(outlets)}"
        raise ValueError(message)
    if len(reaches) != len(nodes) - 1:
        message = "Graphical topology must be a tree: reaches must equal nodes minus one"
        raise ValueError(message)
    adjacent: list[list[tuple[int, str]]] = [[] for _ in nodes]
    undirected: set[frozenset[int]] = set()
    for reach in reaches:
        source = _endpoint_index(reach.vertices_m[0], nodes, drawing.endpoint_tolerance_m, reach.identifier)
        target = _endpoint_index(reach.vertices_m[-1], nodes, drawing.endpoint_tolerance_m, reach.identifier)
        if source == target:
            message = f"Reach {reach.identifier!r} connects a node to itself"
            raise ValueError(message)
        edge = frozenset((source, target))
        if edge in undirected:
            message = f"Parallel reaches share the same endpoints: {reach.identifier!r}"
            raise ValueError(message)
        undirected.add(edge)
        adjacent[source].append((target, reach.identifier))
        adjacent[target].append((source, reach.identifier))
    root = outlets[0]
    parents: dict[int, tuple[int, str] | None] = {root: None}
    pending = deque([root])
    while pending:
        current = pending.popleft()
        for neighbour, reach_id in adjacent[current]:
            if neighbour not in parents:
                parents[neighbour] = (current, reach_id)
                pending.append(neighbour)
    if len(parents) != len(nodes):
        missing = sorted(node.identifier for i, node in enumerate(nodes) if i not in parents)
        message = f"Disconnected graphical nodes from outlet: {missing}"
        raise ValueError(message)
    downstream: dict[str, str | None] = {}
    edge_nodes: dict[str, tuple[str, str]] = {}
    for i, node in enumerate(nodes):
        parent = parents[i]
        downstream[node.identifier] = nodes[parent[0]].identifier if parent is not None else None
        if parent is not None:
            edge_nodes[parent[1]] = (node.identifier, nodes[parent[0]].identifier)
    return _DirectedNetwork(downstream, edge_nodes)


def _length_km(vertices: tuple[Point, ...]) -> float:
    return math.fsum(math.hypot(end[0] - start[0], end[1] - start[1]) for start, end in pairwise(vertices)) / 1000


def _matches_model(model: CatchmentModel, drawing: GeDrawing, network: _DirectedNetwork) -> str:  # noqa: C901 -- explicit stack/geometry consistency checks
    """Prove the exact computational vector is compatible with authored geometry."""
    expected_reaches = {reach.identifier: reach for reach in model.reaches}
    if set(network.edge_nodes) != set(expected_reaches):
        message = "Every computational reach must have exactly one GIS polyline"
        raise ValueError(message)
    area_nodes: dict[str, str] = {}
    for node in drawing.nodes:
        if node.subarea_id is not None:
            if node.subarea_id in area_nodes:
                message = f"Duplicate graphical source for {node.subarea_id!r}"
                raise ValueError(message)
            area_nodes[node.subarea_id] = node.identifier
    if set(area_nodes) != {area.identifier for area in model.subareas}:
        message = "Graphical source IDs do not match all computational subareas"
        raise ValueError(message)
    for reach in drawing.reaches:
        length = Decimal(str(_length_km(reach.vertices_m)))
        computational = expected_reaches[reach.identifier].length_km
        if abs(length - computational) > Decimal("0.0005"):
            message = f"GIS reach {reach.identifier!r} length differs from computational length (km)"
            raise ValueError(message)
    outlet = next(node.identifier for node in drawing.nodes if node.outlet)
    if len(model.print_locations) != 1 or model.controls[-1].code != 7:
        message = "Initial graphical authoring supports a single final outlet print location"
        raise ValueError(message)
    running: str | None = None
    stack: list[str] = []
    for control in model.controls:
        if control.code == 1:
            if control.reach_id is None or control.subarea_id is None:
                message = "Source control is missing an explicit reach or area identity"
                raise ValueError(message)
            upstream, downstream = network.edge_nodes[control.reach_id]
            if area_nodes[control.subarea_id] != upstream:
                message = f"Source {control.subarea_id!r} is not upstream of its own computational reach"
                raise ValueError(message)
            running = downstream
        elif control.code == 3:
            if running is None:
                message = "Cannot store an uninitialised node"
                raise ValueError(message)
            stack.append(running)
            running = None
        elif control.code == 4:
            if running is None or not stack or running != stack.pop():
                message = "Computed confluence does not coincide with GIS confluence"
                raise ValueError(message)
        elif control.code == 5:
            if running is None or control.reach_id is None:
                message = "Reach route must have a running GIS node and reach ID"
                raise ValueError(message)
            upstream, downstream = network.edge_nodes[control.reach_id]
            if upstream != running:
                message = f"Reach {control.reach_id!r} is not downstream of the running GIS node"
                raise ValueError(message)
            running = downstream
        elif control.code == 7 and running != outlet:
            message = "Final print control does not refer to the graphical outlet"
            raise ValueError(message)
    if stack or running != outlet:
        message = "Graphical computation leaves an unresolved branch or non-outlet flow"
        raise ValueError(message)
    return outlet


def _layout(nodes: tuple[GeNode, ...]) -> dict[str, Point]:
    """Adapt PyROMB normalisation without division by zero for flat extents."""
    min_x = min(node.x_m for node in nodes)
    min_y = min(node.y_m for node in nodes)
    range_x = max(node.x_m for node in nodes) - min_x
    range_y = max(node.y_m for node in nodes) - min_y
    scale = max(range_x, range_y)
    if scale <= 0 or not math.isfinite(scale):
        message = "Graphical coordinate extent is degenerate or nonfinite"
        raise ValueError(message)
    return {
        node.identifier: (
            2.5 + 90 * (node.x_m - min_x) / scale,
            2.5 + 90 * (node.y_m - min_y) / scale,
        )
        for node in nodes
    }


def _graphic_node(
    node: GeNode,
    index: int,
    downstream_number: int,
    area: Decimal | None,
    position: Point,
) -> str:
    """Render a legacy RORB_GE node record with fixed graphical columns."""
    drawn_area = Decimal(0) if area is None else area
    if drawn_area != drawn_area.quantize(Decimal("0.001")):
        message = "RORB_GE 002 node area field supports only three decimal places"
        raise ValueError(message)
    return (
        f"C{index:>7}{position[0]:>15.3f}{position[1]:>15.3f}{1.0:>15.3f}"
        f"{int(node.subarea_id is not None):>2d}{int(node.outlet):>2d}{downstream_number:>6d}"
        f" {node.display_label:<28}{float(drawn_area):>15.3f}{0.0:>15.3f}"
        f"{70 if node.outlet else 0:>3d}{0:>3d}"
    )


def _graphic_reach(
    identifier: str,
    number: int,
    upstream: int,
    downstream: int,
    distance_km: Decimal,
    midpoint: Point,
) -> tuple[str, str, str]:
    """Adapt PyROMB's RORB reach record and two midpoint ordinates."""
    if distance_km != distance_km.quantize(Decimal("0.001")):
        message = f"RORB_GE 002 reach {identifier!r} requires three-decimal kilometre length"
        raise ValueError(message)
    record = (
        f"C{number:>7}{(' ' + identifier):<9}{upstream:>18d}{downstream:>6d}"
        f"{0:>15d}{1:>2d}{0:>2d}{float(distance_km):>15.3f}{0.0:>15.3f}{1:>6d}{0:>3d}"
    )
    return record, f"C{midpoint[0]:>16.3f}", f"C{midpoint[1]:>16.3f}"


def _graphical_prefix(model: CatchmentModel, drawing: GeDrawing, network: _DirectedNetwork) -> str:
    positions = _layout(drawing.nodes)
    node_numbers = {node.identifier: number for number, node in enumerate(drawing.nodes, start=1)}
    area_by_id = {area.identifier: area.area_km2 for area in model.subareas}
    lines = [
        model.title,
        "C RORB_GE 002",
        "C ",
        f"C {model.title}",
        "C ",
        "C #FILE COMMENTS",
        "C   0",
        "C ",
        "C #SUB-AREA AREA COMMENTS",
        "C   0",
        "C ",
        "C #IMPERVIOUS FRACTION COMMENTS",
        "C   0",
        "C ",
        "C #BACKGROUND IMAGE",
        "C  T  F",
        "C ",
        "C #NODES",
        f"C{len(drawing.nodes):>7d}",
    ]
    for node in drawing.nodes:
        next_node = network.downstream[node.identifier]
        downstream_number = node_numbers[next_node] if next_node is not None else 0
        area = area_by_id[node.subarea_id] if node.subarea_id is not None else None
        lines.extend(
            [
                _graphic_node(node, node_numbers[node.identifier], downstream_number, area, positions[node.identifier]),
                "C ",
            ]
        )
    lines.extend(["C #REACHES", f"C{len(model.reaches):>7d}"])
    for number, reach in enumerate(model.reaches, start=1):
        upstream, downstream = network.edge_nodes[reach.identifier]
        point_a, point_b = positions[upstream], positions[downstream]
        midpoint = ((point_a[0] + point_b[0]) / 2, (point_a[1] + point_b[1]) / 2)
        lines.extend(
            _graphic_reach(
                reach.identifier,
                number,
                node_numbers[upstream],
                node_numbers[downstream],
                reach.length_km,
                midpoint,
            )
        )
    lines.extend(
        [
            "C ",
            "C #STORAGES",
            "C      0",
            "C ",
            "C #INFLOW/OUTFLOW",
            "C      0",
            "C ",
            "C END RORB_GE",
        ]
    )
    return "\n".join(lines) + "\n"


def serialize_catg_with_drawing(model: CatchmentModel, drawing: GeDrawing) -> bytes:
    """Write checked GE 002 metadata with the authoritative computational vector.

    This is syntactic/model round-trip validation, not native RORB compatibility.
    """
    model.__post_init__()
    network = _network(drawing)
    _matches_model(model, drawing, network)
    canonical = serialize_catg(model).decode("utf-8")
    marker = "C END RORB_GE\n"
    computation = canonical.partition(marker)[2]
    if not computation:
        message = "Canonical catchment writer omitted the computational vector"
        raise ValueError(message)
    data = (_graphical_prefix(model, drawing, network) + computation).encode("utf-8")
    if parse_catg(data).model != model:
        message = "Authored GE metadata unexpectedly modified the computational model"
        raise ValueError(message)
    return data
