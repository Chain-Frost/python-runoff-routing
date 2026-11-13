# Optional GIS authoring of RORB_GE catchments (S1)

**Status:** limited RORB_GE 002 *source-authoring* contract; a two-file, 21-ordinate
RORB_CMD 6.44 profile passed bounded native replay (see [acceptance report](work/2026-11-11-pr29-native-acceptance.md)).
RORB_GE graphical-editor opening/display and general RORBwin compatibility are **not** validated.
The existing source-aware
[bidirectional parser](RORB_BIDIRECTIONAL.md) and its computational ordering remain authoritative.

## Provenance and code reuse

This implementation selectively adapts the input validation, OGR containment,
topology preflight and graphics conventions from
[PyROMB PR #16](https://github.com/norman-tom/pyromb/pull/16),
fork head `a323d5709f7ce14c6adf46f01e0224b60668340c` and
the upstream writer `src/pyromb/models/rorb.py`. Those projects use the MIT
licence (Copyright © 2022 Tom Norman); see the retained
[licence notice](third_party/PYROMB_LICENSE.txt).
The PR #16 validation is **not present on PyROMB main** at the time of review.
It reports 242 Windows/QGIS/OGR tests passed; its writer and traversal blobs are
unchanged from upstream main, so these results alone do not certify native
RORB file acceptance.

No PyROMB dependency, GDAL runtime, NumPy, pandas or Matplotlib are required
for the source-level or direct-geometry writer. GDAL/OGR is loaded only when
calling the *optional* `drawing_from_layers` GIS boundary under QGIS/OSGeo4W.
No QGIS or GDAL packages are downloaded or installed automatically.

## Pure authoring from an existing typed model

```python
from runoff_routing.rorb_codec import parse_catg, write_new
from runoff_routing.rorb_ge_authoring import (
    GeDrawing,
    GeNode,
    GeReach,
    serialize_catg_with_drawing,
)

# Use an already inspected / authored CatchmentModel. Do not generate a new
# computational vector from graphical coordinate ordering.
model = parse_catg(original_catg_bytes).model

# Each graphical node/subarea/reach must have a stable, explicit identity.
# This illustration must be replaced by the *real* checked GIS geometry.
drawing = GeDrawing(
    nodes=(
        GeNode("A", 0.0, 0.0, "area_1", display_label="A"),
        GeNode("OUT", 5000.0, 0.0, outlet=True),
    ),
    reaches=(GeReach("reach_1", ((0.0, 0.0), (5000.0, 0.0))),),
    crs="EPSG:28350",
    unit="m",
)
data = serialize_catg_with_drawing(model, drawing)
write_new(output_path, data)  # exclusive create: no overwrite
```

The example is schematic: `model` must have exactly one matching 5 km reach,
one `area_1` source and a final outlet print for this drawing to pass. The
writer does not claim that arbitrary data passed into this example are valid.

This writer validates unique node/reach IDs, finite XY, snapped endpoints,
an unambiguous connected outlet-rooted tree, source/reach mappings, GIS length
against the exact computational reach length, and the original 1/3/4/5/7 stack
order against the actual confluence locations. Reversed line digitisation is
supported. It uses the **existing canonical computational-vector writer**,
including [the native-evidence code-7 physical print-location fix
#25](https://github.com/Chain-Frost/python-runoff-routing/pull/25), rather than
creating another RORB grammar.

**Native print-label compatibility boundary:** The original two-file CMD 6.44
acceptance used a bare `7` control followed by the physical print-location
line. The integrated S1 parser also preserves a distinct optional graphical
annotation on the code-7 control record. If `ControlStep.label` is nonempty,
the writer emits `7, annotation` followed by `PrintLocation.label` on the
next physical line. This annotated form retains typed/JSON round-trip semantics
but **has not received a native CMD replay**. To emit the previously accepted
bare-code-7 variant, the caller must *explicitly* provide an empty
`ControlStep.label` while retaining the separate physical
`PrintLocation.label`; the serializer will not silently drop the annotation.

It emits nonempty GE 002 node/reach drawing blocks using PyROMB-informed legacy
field formatting with an aspect-preserving layout. Control-code, subarea and
reach order are not changed. The drawing includes one graphical midpoint per
reach, not a lossless copy of the original GIS polyline. Preserve source GIS
geometries separately. It rejects source areas and reach lengths which cannot
be represented to three decimal places in the target graphical fields, rather
than silently rounding source model metadata.

## Optional PyROMB-style GIS layers

```python
from runoff_routing.rorb_ge_gis import drawing_from_layers
from runoff_routing.rorb_ge_authoring import serialize_catg_with_drawing

# PyROMB-compatible layer interface:
#   len(layer), layer.record(i)["id"], layer.geometry(i) -> list[(x, y)]
# The actual source CRS must be verified in QGIS before this call.
drawing = drawing_from_layers(
    model,
    centroids,
    basin_polygons,
    confluences,
    reaches,
    projected_crs="EPSG:28350",
    endpoint_tolerance_m=0.000001,
)
output_bytes = serialize_catg_with_drawing(model, drawing)
```

For this first tranche, the existing typed model's `area_1`, `reach_1`
identities must be supplied explicitly in the GIS layers. Centroid `fi`
must be zero; reach `t` must be 1 and `s` finite/nonnegative; confluence
`out` must be 0 or 1, with exactly one outlet. No automatic ID matching
by names, nearest polygon-centre, topology repair or geometry rewriting occurs.

OGR requires one centroid strictly inside each valid single-part, single-ring
basin polygon, rejects holes and extra parts *when the layer interface exposes
them*, and confirms area agreement within 0.0000005 km². This flat XY layer
interface **cannot independently verify source CRS, geometry type or missing
ring/part metadata discarded upstream**. The caller must validate those source
properties and metre units in QGIS; specifying `projected_crs` is a declaration,
not a coordinate transformation or source CRS inspection.

## Deliberate exclusions and gates

- Initial writer accepts only GE 002 with natural reaches, all-pervious areas,
  no storage/diversion, one final outlet print. No mixed `.dat`, FIT,
  multi-burst, fractional codes or full GUI 6.45 support.
- Tree-only GIS preprocessing does **not** disqualify existing RORB
  computational models containing diversions, rejoining routes or storage;
  those models simply cannot be authored through this optional adapter yet.
- No RORB native executable or private fixtures are bundled or launched.
  Synthetic parser round-tripping does not establish native acceptability.
- The bounded [CMD 6.44 acceptance report](work/2026-11-11-pr29-native-acceptance.md)
  documents two diagnostic-free executions, byte-identical computational records,
  exact 21-ordinate/printed-time agreement and verified physical code-7 identity.
  A genuine Python 3.14 OGR source/wheel adapter check also passed; separate QGIS
  provider checks used its Python 3.12 runtime (below this package's >=3.14 requirement).
- **Not established:** GUI/editor load/save and graphical field/display fidelity,
  supported Python 3.14 QGIS package operation, broader catchment/format support or
  hydrological numerical equivalence. These are deferred; no further GUI/GIS work
  is required for the present computational priority. S1 issue #3 stays open.
