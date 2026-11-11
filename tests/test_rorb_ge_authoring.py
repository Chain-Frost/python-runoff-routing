"""Synthetic PyROMB-inspired RORB_GE authoring checks; never launch native RORB."""

from __future__ import annotations

import subprocess
from dataclasses import replace
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from runoff_routing import rorb_ge_gis
from runoff_routing.rorb_codec import parse_catg, serialize_catg, write_new
from runoff_routing.rorb_ge_authoring import (
    GeDrawing,
    GeNode,
    GeReach,
    Point,
    serialize_catg_with_drawing,
)
from runoff_routing.rorb_ge_gis import drawing_from_layers
from runoff_routing.rorb_model import CatchmentModel, ControlStep, PrintLocation, Reach, SubArea


def _model() -> CatchmentModel:
    return CatchmentModel(
        "SYNTHETIC GIS AUTHORING",
        (SubArea("area_1", Decimal(1), "A"), SubArea("area_2", Decimal(1), "B")),
        (
            Reach("reach_1", Decimal(5), "Reach 1 Sub-area A"),
            Reach("reach_2", Decimal(4), "Reach 2 Sub-area B"),
            Reach("reach_3", Decimal("2.5"), "Reach 3"),
        ),
        (
            ControlStep(1, "area_1", "reach_1", label="Reach 1 Sub-area A"),
            ControlStep(3, label="Store"),
            ControlStep(1, "area_2", "reach_2", label="Reach 2 Sub-area B"),
            ControlStep(4, label="Join"),
            ControlStep(5, reach_id="reach_3", label="Reach 3"),
            ControlStep(7, print_id="print_1", label="Outlet"),
        ),
        (PrintLocation("print_1", "Outlet"),),
    )


def _drawing() -> GeDrawing:
    return GeDrawing(
        (
            GeNode("A", 0, 0, "area_1", display_label="A"),
            GeNode("JOIN", 5000, 0),
            GeNode("B", 5000, 4000, "area_2", display_label="B"),
            GeNode("OUT", 7500, 0, outlet=True),
        ),
        (
            GeReach("reach_1", ((0, 0), (5000, 0))),
            GeReach("reach_2", ((5000, 0), (5000, 4000))),  # reversed digitisation must work
            GeReach("reach_3", ((5000, 0), (7500, 0))),
        ),
        "EPSG:28350",
        "m",
    )


def test_graphical_catg_preserves_computational_bytes_and_roundtrips() -> None:
    model = _model()
    data = serialize_catg_with_drawing(model, _drawing())
    parsed = parse_catg(data)
    marker = b"C END RORB_GE\n"
    assert parsed.model == model
    assert data.split(marker, maxsplit=1)[1] == serialize_catg(model).split(marker, maxsplit=1)[1]
    assert b"C #NODES\nC      4\n" in data
    assert b"C #REACHES\nC      3\n" in data
    assert b"7\nOutlet\n0\n" in data
    assert [step.code for step in parsed.model.controls] == [1, 3, 1, 4, 5, 7]
    assert b"RORB_GE 002" in data
    assert b"RORB_GE 6.45" not in data


def test_flat_extent_and_multi_vertex_reaches() -> None:
    model = _model()
    nodes = (
        GeNode("A", 0, 0, "area_1"),
        GeNode("B", 9000, 0, "area_2"),
        GeNode("JOIN", 5000, 0),
        GeNode("OUT", 7500, 0, outlet=True),
    )
    reaches = (
        GeReach("reach_1", ((0, 0), (2500, 0), (5000, 0))),
        GeReach("reach_2", ((9000, 0), (5000, 0))),
        GeReach("reach_3", ((5000, 0), (7500, 0))),
    )
    data = serialize_catg_with_drawing(model, GeDrawing(nodes, reaches, "EPSG:28350", "m"))
    assert parse_catg(data).model == model


@pytest.mark.parametrize(
    ("replacement", "message"),
    [
        ({"outlet": False}, "one graphical outlet"),
        ({"x_m": float("nan")}, "finite"),
        ({"display_label": "a" * 29}, "28-character"),
    ],
)
def test_invalid_outlet_node_fail_closed(replacement: dict[str, Any], message: str) -> None:
    original = _drawing()
    if "x_m" in replacement or "display_label" in replacement:
        with pytest.raises(ValueError, match=message):
            replace(original.nodes[-1], **replacement)
    else:
        changed = replace(original.nodes[-1], **replacement)
        with pytest.raises(ValueError, match=message):
            serialize_catg_with_drawing(_model(), replace(original, nodes=(*original.nodes[:-1], changed)))


def test_wrong_topology_is_not_silently_reordered() -> None:
    original = _drawing()
    links = (*original.reaches[:2], GeReach("reach_3", ((0, 0), (2500, 0))))
    with pytest.raises(ValueError, match=r"tree|Parallel|matches|not downstream|source|length"):
        serialize_catg_with_drawing(_model(), replace(original, reaches=links))
    swapped = (
        original.reaches[1],
        original.reaches[0],
        original.reaches[2],
    )
    assert parse_catg(serialize_catg_with_drawing(_model(), replace(original, reaches=swapped))).model == _model()


def test_geometry_and_source_identity_rejection() -> None:
    original = _drawing()
    with pytest.raises(ValueError, match="globally unique"):
        serialize_catg_with_drawing(
            _model(), replace(original, nodes=(replace(original.nodes[0], identifier="JOIN"), *original.nodes[1:]))
        )
    short_reach = replace(original.reaches[0], vertices_m=((0, 0), (4990, 0)))
    with pytest.raises(ValueError, match="length differs"):
        serialize_catg_with_drawing(_model(), replace(original, reaches=(short_reach, *original.reaches[1:])))
    shifted_reach = replace(original.reaches[0], vertices_m=((0.1, 0), (5000, 0)))
    with pytest.raises(ValueError, match="matches 0 nodes"):
        serialize_catg_with_drawing(_model(), replace(original, reaches=(shifted_reach, *original.reaches[1:])))
    with pytest.raises(ValueError, match="source IDs"):
        serialize_catg_with_drawing(
            _model(), replace(original, nodes=(replace(original.nodes[0], subarea_id=None), *original.nodes[1:]))
        )


def test_malformed_and_unsupported_drawing_rejected() -> None:
    drawing = _drawing()
    with pytest.raises(ValueError, match="projected CRS"):
        replace(drawing, crs="EPSG:4326")
    with pytest.raises(ValueError, match="finite"):
        replace(drawing, endpoint_tolerance_m=float("inf"))
    with pytest.raises(ValueError, match="zero geometric"):
        GeReach("reach_X", ((0, 0), (0, 0)))
    extra = PrintLocation("print_2", "Another")
    augmented = replace(
        _model(),
        print_locations=(*_model().print_locations, extra),
        controls=(*_model().controls, ControlStep(7, print_id="print_2", label="Another")),
    )
    with pytest.raises(ValueError, match="single final"):
        serialize_catg_with_drawing(augmented, drawing)


def test_drawing_writer_no_file_or_native_side_effects(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def prohibit(*_args: object, **_kwargs: object) -> None:
        pytest.fail("A source writer cannot launch RORB")

    monkeypatch.setattr(subprocess, "run", prohibit)
    original = serialize_catg(_model())
    output = tmp_path / "authored.catg"
    write_new(output, serialize_catg_with_drawing(_model(), _drawing()))
    with pytest.raises(FileExistsError):
        write_new(output, b"clobber")
    assert parse_catg(output.read_bytes()).model == parse_catg(original).model


class _Layer:
    """Minimal PyROMB VectorLayer-shaped synthetic layer."""

    def __init__(self, records: list[tuple[list[Point], dict[str, object]]]) -> None:
        self.data = records

    def geometry(self, index: int) -> list[Point]:
        return self.data[index][0]

    def record(self, index: int) -> dict[str, object]:
        return self.data[index][1]

    def __len__(self) -> int:
        return len(self.data)


class _Shape:
    """Minimal rectangle-only fake for testing the optional OGR boundary."""

    def __init__(self, shape_kind: int) -> None:
        self.kind = shape_kind
        self.coords: list[Point] = []

    def AddPoint_2D(self, x: float, y: float) -> None:  # noqa: N802 -- exact external OGR naming convention
        self.coords.append((x, y))

    def AddGeometry(self, other: _Shape) -> None:  # noqa: N802 -- exact external OGR naming convention
        self.coords = other.coords

    def IsEmpty(self) -> bool:  # noqa: N802 -- exact external OGR naming convention
        return not self.coords

    def IsValid(self) -> bool:  # noqa: N802 -- exact external OGR naming convention
        return bool(self.coords)

    def GetArea(self) -> float:  # noqa: N802 -- exact external OGR naming convention
        return (max(x for x, _y in self.coords) - min(x for x, _y in self.coords)) * (
            max(y for _x, y in self.coords) - min(y for _x, y in self.coords)
        )

    def Contains(self, other: _Shape) -> bool:  # noqa: N802 -- exact external OGR naming convention
        x, y = other.coords[0]
        return min(point[0] for point in self.coords) < x < max(point[0] for point in self.coords) and min(
            point[1] for point in self.coords
        ) < y < max(point[1] for point in self.coords)


class _FakeOgr:
    wkbLinearRing = 1  # noqa: N815 -- faithful OGR test double
    wkbPolygon = 2  # noqa: N815 -- faithful OGR test double
    wkbPoint = 3  # noqa: N815 -- faithful OGR test double

    def Geometry(self, kind: int) -> _Shape:  # noqa: N802 -- exact external OGR naming convention
        return _Shape(kind)


def _layers() -> tuple[_Layer, _Layer, _Layer, _Layer]:
    centroids = _Layer(
        [
            ([(0, 0)], {"id": "area_1", "fi": 0}),
            ([(5000, 4000)], {"id": "area_2", "fi": 0}),
        ]
    )
    basins = _Layer(
        [
            ([(-500, -500), (500, -500), (500, 500), (-500, 500), (-500, -500)], {}),
            ([(4500, 3500), (5500, 3500), (5500, 4500), (4500, 4500), (4500, 3500)], {}),
        ]
    )
    confluences = _Layer(
        [
            ([(5000, 0)], {"id": "JOIN", "out": 0}),
            ([(7500, 0)], {"id": "OUT", "out": 1}),
        ]
    )
    reaches = _Layer(
        [
            ([(0, 0), (5000, 0)], {"id": "reach_1", "t": 1, "s": 0}),
            ([(5000, 4000), (5000, 0)], {"id": "reach_2", "t": 1, "s": 0}),
            ([(5000, 0), (7500, 0)], {"id": "reach_3", "t": 1, "s": 0}),
        ]
    )
    return centroids, basins, confluences, reaches


def test_optional_ogr_layer_adapter_preserves_model(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(rorb_ge_gis, "_ogr", _FakeOgr)
    layers = _layers()
    drawing = drawing_from_layers(_model(), *layers, projected_crs="EPSG:28350")
    assert parse_catg(serialize_catg_with_drawing(_model(), drawing)).model == _model()
    assert drawing.nodes[0].outlet is False
    assert drawing.nodes[1].outlet is True


def test_optional_ogr_rejects_bad_basins(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(rorb_ge_gis, "_ogr", _FakeOgr)
    centroids, basins, confluences, reaches = _layers()
    misplaced = _Layer([([(500, 0)], centroids.data[0][1]), centroids.data[1]])
    with pytest.raises(ValueError, match="strictly inside"):
        drawing_from_layers(_model(), misplaced, basins, confluences, reaches, projected_crs="EPSG:28350")
    repeated = _Layer([basins.data[0], basins.data[0]])
    with pytest.raises(ValueError, match=r"already assigned|Unassigned|strictly inside"):
        drawing_from_layers(_model(), centroids, repeated, confluences, reaches, projected_crs="EPSG:28350")
    ring_with_hole = _Layer(
        [
            (basins.data[0][0] + [(10, 10), (20, 10), (10, 10)], {}),
            basins.data[1],
        ]
    )
    with pytest.raises(ValueError, match="holes or multipart"):
        drawing_from_layers(_model(), centroids, ring_with_hole, confluences, reaches, projected_crs="EPSG:28350")


@pytest.mark.parametrize("bad", ["negative_slope", "unknown_reach", "missing_field", "nonzero_fi", "null_field"])
def test_gis_attribute_checks(monkeypatch: pytest.MonkeyPatch, bad: str) -> None:
    monkeypatch.setattr(rorb_ge_gis, "_ogr", _FakeOgr)
    centroids, basins, confluences, reaches = _layers()
    if bad == "negative_slope":
        reaches.data[0][1]["s"] = -1
    elif bad == "unknown_reach":
        reaches.data[0][1]["id"] = "unmapped"
    elif bad == "missing_field":
        del reaches.data[0][1]["s"]
    elif bad == "nonzero_fi":
        centroids.data[0][1]["fi"] = 0.1
    else:
        centroids.data[0][1]["fi"] = None
    with pytest.raises((TypeError, ValueError), match="feature"):
        drawing_from_layers(_model(), centroids, basins, confluences, reaches, projected_crs="EPSG:28350")


def test_qgis_null_variant_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    class _QgisNull:
        def isNull(self) -> bool:  # noqa: N802 -- QGIS 3 QVariant protocol
            return True

    monkeypatch.setattr(rorb_ge_gis, "_ogr", _FakeOgr)
    centroids, basins, confluences, reaches = _layers()
    confluences.data[1][1]["out"] = _QgisNull()
    with pytest.raises(ValueError, match="empty required field"):
        drawing_from_layers(_model(), centroids, basins, confluences, reaches, projected_crs="EPSG:28350")


def test_optional_gdal_is_not_imported_for_pure_writer(monkeypatch: pytest.MonkeyPatch) -> None:
    def missing() -> None:
        message = "Simulated missing GDAL"
        raise RuntimeError(message)

    monkeypatch.setattr(rorb_ge_gis, "_ogr", missing)
    assert parse_catg(serialize_catg_with_drawing(_model(), _drawing())).model == _model()
    with pytest.raises(RuntimeError, match="Simulated missing GDAL"):
        drawing_from_layers(_model(), *_layers(), projected_crs="EPSG:28350")
