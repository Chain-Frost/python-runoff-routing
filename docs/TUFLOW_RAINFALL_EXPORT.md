# RORB to TUFLOW rainfall boundary export

Convert one standard RORB OUT report using the canonical PyRORB reader, without running either solver.
The API and CLI explicitly select gross rainfall or rainfall excess, named printed columns,
and an unused output path. No ryan-tools, pandas, TUFLOW or native RORB installation is required.

## Usage

```sh
python -m runoff_routing.tuflow_rainfall report.out rainfall.csv --kind gross --column Subarea_A_mm --column Subarea_Q_mm
```

```python
from pathlib import Path
from runoff_routing.tuflow_rainfall import export_tuflow_rainfall

result = export_tuflow_rainfall(
    Path("report.out"),
    Path("rainfall.csv"),
    kind="gross",
    columns=("Subarea_A_mm", "Subarea_Q_mm"),
)
print(result.columns, result.totals_mm, result.reported_totals_mm)
```

Use `Catchment_mm` for the printed catchment series, or `Subarea_<label>_mm` for
an exact printed subarea label. Uniform direct-depth OUT reports may print only `Catchment_mm`;
no individual subarea columns or physical mapping are inferred. Repeat `--column` to select multiple columns in output order.
If the selected kind occurs more than once, inspect the canonical numbered sections and use
`--section N` (Python: `section=N`) for the intended `rainfall_N`. No implicit first-match
selection. `build_tuflow_rainfall(document, ...)` returns the same boundary without writing.
`--kind excess` explicitly selects rainfall-excess depths; never substitute it for gross rainfall,
or apply RORB losses again in TUFLOW when the intended input is already net of those losses.
The source report is read-only. The destination must have a CSV extension and an existing
parent directory; an existing file is not overwritten.

### Reports with rounded timestep labels

The default clock uses the printed timestep and checks it against available OUT time labels.
Some real reports print a rounded value (e.g. 0.12 h for a source STM specifying 0.125 h).
If the cumulative clock contradicts the printed step, default export refuses. If you have
independently established the exact timestep from the matching source STM or other reliable
source evidence, supply it explicitly:

```sh
python -m runoff_routing.tuflow_rainfall report.out rain.csv --kind gross --column Subarea_A_mm --exact-step-hours 0.125
```

Python equivalent: pass `exact_step_hours=Decimal("0.125")` (import Decimal from decimal).
The supplied step must be positive, within half the printed timestep's last digit, and
consistent with every printed hydrograph time label to half its last digit. A complete
canonical OUT hydrograph clock covering the rainfall horizon is required for this opt-in.
No approximate step is inferred, no embedded STM path is followed, and association with the
correct STM is the caller's responsibility. The API returns the reported and selected step
separately and records `clock_basis` as `reported` or `caller_exact`; the CLI prints both.

## Literal input and output contract

The [TUFLOW Classic/HPC 2026.3 manual, sections 8.4.3.1.1 and 8.5](https://docs.tuflow.com/classic-hpc/manual/2026.3/07-Boundaries-and-Initial-Conditions.html)
defines rainfall boundary data as metric incremental depth in mm with times in simulation hours,
and defines named CSV column selection in the BC database.
[Appendix A, Rainfall Boundaries](https://docs.tuflow.com/classic-hpc/manual/2026.3/80-AppendicesA-TCFCommands.html)
specifies the default STEPPED convention: depth at the second time is applied over the preceding interval.

The output has exactly one header and no provenance preamble, increment-index column, totals
row or rainfall intensity column. For example, two intervals of 0.125 hours with printed depths
3.00 and 1.25 mm are represented as follows:

```csv
Time_hours,Subarea_A_mm
0.000,0
0.125,3.00
0.250,1.25
0.375,0
```

In the BC database (adjust the Source path to suit the model), select the columns by name:

```csv
Name,Source,Column 1,Column 2
Rain_A,rainfall.csv,Time_hours,Subarea_A_mm
```

Use the corresponding `Rain_A` name in the `2d_rf` rainfall polygon or an appropriate global
rainfall boundary. Use metric units, `Rainfall Boundaries == STEPPED`, no time shift and
unit depth multiplier if the intended model clock and depths match the source. This is a BC data
CSV, not a grid rainfall index, rainfall control file, BC database generator or a discharge CSV.

The RORB heading must literally identify either `Rainfall, mm, in time inc. following time shown`
or `Rainfall-excess, mm, in time inc. following time shown`. For RORB increment i, the depth
covers the interval from i times the selected step to (i+1) times that step. Assign it to the
latter timestamp. The unique reported rainfall Start and Finish define the required
half-open increment sequence [Start, Finish). Do not use the hydrograph calculation duration
as the rainfall duration. Introduce one zero-depth anchor at Start times step; if the first
increment starts at zero and is wet, its depth goes to the end of that very first interval.
Preserve dry interior increments. If any selected series is wet at the last interval,
append a single dry interval of the same length after Finish. Otherwise keep the already-dry
last interval. A delayed Start is not shifted back to zero; rainfall is zero before the
initial anchor and after the final dry entry under the documented convention.

## Qualification and limits

The admitted format uses the three-line Time / Catch / Incs ment subarea header,
letter-only subarea labels, or the explicit uniform catchment-only Time/Catch and Incs ment
header. Both require contiguous interval records, each page's printed Tot. footer (including
compact `Tot.105.0`), an optional Pluvi. ref. no. line and an identified next rainfall
heading or Routing results boundary. A catchment-only page is not a continuation page. Continuation pages are represented separately under the same numbered section.
Repeated catchment values must agree between pages; repeated subarea identities are rejected.
Every selected section page must match the declared rainfall horizon. Unsupported layouts,
missing time information, malformed numbers, negative depths, incomplete intervals or invalid
canonical reports are refused. Hydrograph clock labels, when present, must corroborate
the selected timestep to their printed resolution. The converter cannot infer
an unprinted exact timestep or reconstruct unprinted rainfall precision. Its exact decimal
domain limits absolute decimal exponents and adjusted exponents to 30; time values must remain
distinct in floating-point representation. No arbitrary correction, interpolation or loss model
is performed.

Printed subarea interval depths may have much coarser precision than the source rainfall;
their sum can differ from the report's independently printed Tot. value. The result reports
both separately (in selected column order) and exports the interval sum unchanged.
It does not certify the physical model, rainfall weighting or polygon associations.
See the [work record](work/2026-11-28-issue249-tuflow-rainfall.md) for retained-source
comparisons and pending native TUFLOW consumption validation.
