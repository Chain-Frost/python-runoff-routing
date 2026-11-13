# PR #29 bounded native and GIS acceptance

- **Tested revision:** `a5aee07c8f84f23267f999322961d903c2b081aa`, unchanged throughout execution.
  [PR #29](https://github.com/Chain-Frost/python-runoff-routing/pull/29),
  [S1 issue #3](https://github.com/Chain-Frost/python-runoff-routing/issues/3).
- **Owner:** Local agent, under the owner's explicit bounded-campaign instruction.
  **Updated:** 2026-11-11 (Australia/Perth). **Next review:** Next owner acceptance review.
- **Branch:** `acceptance/pr29-native-a5aee07`, an isolated worktree. This report is a documentation
  follow-up; it does not change the tested PR head, implementation, tolerances or numerical status.
- **Status:** PASS for the two-case embedded computational-record CMD replay and bounded real-OGR
  adapter checks. QGIS source/provider checks pass as supplementary evidence; supported-package
  QGIS/Python 3.14 integration remains unverified. No numerical stage is accepted or closed.

## Frozen scope and native observations

The campaign froze a maximum of two CMD launches, zero GUI launches, a 15-second per-case timeout,
exact printed comparisons and no native repair/retry. Exactly two RORB_CMD calculations ran through
the existing S0 `capture_cmd(..., execute=True)` harness. Each used exclusive staged copies, binary
process streams, generated CMD parameters and an immutable audited manifest. No new native runner
or production numerical implementation was introduced.

One independently authored typed model defines two all-pervious 1 km2 sources, three natural reaches
(5, 4 and 2.5 km), source/store/source/join/route/final-print controls and one final outlet.
`serialize_catg` and `serialize_catg_with_drawing` generated canonical and nonempty graphical
RORB_GE 002 catchments. Their computational records after `C END RORB_GE` are byte-identical,
and both parse back to the same typed model. Graphical metadata contains four nodes and three reaches,
including a reversed-digitised branch. The graphical outlet label is deliberately different from
the physical code-7 location, **Physical outlet 29**.

Both cases use the same generated DESIGN storm bytes: h=0.5 h, 20 calculation increments,
two rainfall intervals (25%, 75%), and ordered subarea depths 20/30 mm. Parameters are kc=5,
m=0.8, IL=1 mm and CL=0.5 mm/h; one ISA, one burst, zero initial output.

The executable fingerprint before/after is the retained CMD 6.44 profile
`10999ca29f9516c6a7abd26df37cafd433a1cd4ae70d7ac61aa7213845c5ab6f`;
both actual reports identify version 6.44, updated 12 March 2019.

Both captures have exit zero, S0 outcome `success`, no provenance gaps, no error/warning diagnostics,
and complete finite tables. Independent checks verify effective routing/loss echoes, rainfall pattern,
source order/areas/depths, reach order/lengths, DESIGN mode and horizon. Native data checks, the print
control description and Hyd001's physical site identity all identify **Physical outlet 29**.
The graphical outlet label is not substituted for that physical location.

All **21 discharge ordinates and their raw increment/time tokens match exactly** between cases.
CMD labels remain Inc 1..21 and time 0.50..10.50 h, including the initial zero row; no shift or rounding
adjustment was applied. The full reports from the data-check section onward also match exactly.
Source modules, generated originals, staged catchments/storms and executable hashes are unchanged.

This proves bounded CMD acceptance of the paired files' embedded computational records. CMD treats
graphics as comments: this does **not** establish graphical field-width correctness, editor opening,
display/layout fidelity, GUI execution, all GE 002 variants or hydrological numerical equivalence.

## Genuine GIS boundary, kept separate

The approved small GeoPackage was independently created for this campaign, without project/client data.
EPSG:28350 projected metre layers contain two disjoint single-ring 1 km2 polygons, two source points,
two confluence/outlet points and three natural-reach lines. Basin feature order is deliberately opposite
to computational source order. The source datasource is opened read-only; negative controls operate on
in-memory feature copies, and its before/after byte hash is unchanged.

- **Target runtime:** Windows/Python 3.14.6 with genuine GDAL/OGR 3.13.3 and the GPKG driver.
  Both pinned-source and retained installed-wheel adapter imports pass. CRS, metre units, geometry types,
  validity, XY dimensionality, polygon rings/parts and feature counts are checked before exposing the flat
  layer protocol. The adapter matches actual OGR polygon containment/area, preserves explicit identities,
  and generates a round-trippable drawing with identical computational records.
- **QGIS provider:** QGIS 4.2.3 with its compatible OSGeo4W GDAL/OGR 3.13.3 and genuine `QgsVectorLayer`
  GPKG layers passes the same positive checks. Boundary centroid, mismatched basin area and actual NULL
  impervious-fraction controls are rejected in both OGR and QGIS feature paths. The private wrapper only
  exposes the adapter's documented feature/XY protocol after checking source metadata; no OGR test double
  or geometry repair is used. This runs in a separate headless `QgsApplication`, without altering a live project.
- **Compatibility limitation:** Installed QGIS uses Python **3.12.16**, below this package's declared
  `>=3.14` requirement. Its source-level provider execution is supplementary evidence, not a supported
  installed-QGIS package claim. A QGIS build using supported Python remains a separate acceptance gate.
  The Python 3.14 installed-wheel OGR check uses existing genuine system GIS bindings with its package
  import explicitly pinned to the fresh wheel installation; the package-only fresh venv stays dependency-free.

## Software quality, evidence and next action

At the pinned head, Windows/Python 3.14.6 local quality checks pass: Ruff 0.16.6 lint/format,
strict Pyright with zero errors/warnings, repository/link checks and **123 tests passed, zero skips**.
Build succeeds. The retained wheel installs into a fresh venv outside the checkout, passes `pip check`,
imports from that installation with `py.typed`, and reproduces all three generated input files byte-for-byte.
Installed-wheel parsing, both S0 manifest audits and preflight pass; no extra native launch occurs there.

Raw inputs, GeoPackage, typed model, complete reports/logs/process streams, specs, frozen plan,
reproduction scripts, source fingerprints, manifests, wheel, quality/build logs and GIS results remain
outside the public repository in the private local campaign bundle `pr29-native-a5aee07`.
Its separate SHA-256/size inventory retains every campaign payload; raw files, private paths and the
evidence hashes are not added here. The original corpus/goldens remain untouched.

Next action: review this named-profile evidence on PR #29. Keep S1 #3 and all numerical acceptance gates
open. Graphical-editor acceptance and supported-Python QGIS packaging need separately scoped work;
this campaign authorises no additional native runs. No merge, release, package upload or workflow change.
