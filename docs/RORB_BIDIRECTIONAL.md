# S1 bidirectional RORB input boundary

**Status:** limited executable parser/serializer contract, not native or numerical acceptance. See [issue #3](https://github.com/Chain-Frost/python-runoff-routing/issues/3), [inspection](S1-INSPECTION.md), [compatibility](COMPATIBILITY.md) and [regression](REGRESSION.md).

## Pure API and identity

- `rorb_codec.parse_cmd_par(bytes)`, `parse_catg(bytes)`, `parse_design_stm(bytes)` produce `ParsedDocument[T]` with frozen, slot-based typed domain data, original source bytes/hash/encoding/newline, field-level one-based token spans and, for RORB_GE, the untouched graphical source block. These pure functions do not read a path or call native software.
- `rorb_codec.original_bytes(parsed, current_model=...)` returns **exact original bytes**. Supplying an edited model raises `ValueError`; original-byte mode must not silently discard changes.
- `serialize_cmd_par(ParameterSet)`, `serialize_catg(CatchmentModel)`, `serialize_design_stm(StormModel)` create deterministic UTF-8/LF canonical files. They accept **models**, not edited source wrappers. Each generated file is parsed by the same parser. Canonical RORB_GE creates an **empty drawing scaffold**: it deliberately does not reproduce or regenerate graphical node coordinates. Native acceptance of that scaffold remains unverified.
- `read_file(Path)` reads only its named source (it never dereferences the CMD references). `write_new(Path, bytes)` opens in exclusive-create mode and refuses to overwrite any existing file.
- `rorb_model.RunModel` holds three independently parsed or authored models; it rejects depth/area-order and ISA/burst count mismatches. `rorb_model.to_dict/from_dict` and `to_json/from_json` retain typed domain contents using **schema_version=1**, exact explicit units and Decimal **strings**; input RORB files are no longer required after model construction.
- `rorb_codec.to_s2_payload(run)` is a **narrow reviewed float boundary** for the currently understood one-ISA lumped IL/CL, all-pervious S2 subset. It does not import the separate S2 branch, calculate flow or claim numerical parity. S2 should adapt this boundary when its source branch is integrated; do not fork another authoritative parser.

All model classes are frozen and slot-based. Values at file and JSON boundaries are `Decimal`; conversion to finite `float` is explicit only at the provisional S2 adapter. Identifiers `area_1`, `reach_1` and `print_1` are deterministic **computational ordinal IDs**. Human text labels and the original graphical drawing are separate metadata. The catchment vector and storm depths stay in source order.

## Example: RORB files → Python → JSON → Python → RORB files

```python
from pathlib import Path

from runoff_routing.rorb_codec import (
    original_bytes,
    parse_catg,
    parse_cmd_par,
    parse_design_stm,
    serialize_catg,
    serialize_cmd_par,
    serialize_design_stm,
    write_new,
)
from runoff_routing.rorb_model import RunModel, from_json, to_json

folder = Path(r"C:\models")
par = parse_cmd_par((folder / "reference.par").read_bytes())
catchment = parse_catg((folder / "catchment.catg").read_bytes())
storm = parse_design_stm((folder / "storm.stm").read_bytes())
assert original_bytes(catchment) == (folder / "catchment.catg").read_bytes()

run = RunModel(par.model, catchment.model, storm.model)
interchange = to_json(run)  # can be stored, transported, reviewed, edited
restored = from_json(interchange)
assert isinstance(restored, RunModel)

output = folder / "canonical"  # create this directory explicitly
write_new(output / "reference.par", serialize_cmd_par(restored.parameters))
write_new(output / "catchment.catg", serialize_catg(restored.catchment))
write_new(output / "storm.stm", serialize_design_stm(restored.storm))
```

Canonical output loses the original comments, whitespace, line endings and RORB_GE coordinates **by design**; those remain only in the original source document. Canonical filenames/paths are not rewritten to point to a new directory automatically. The caller must choose safe reference paths and review native compatibility before running the generated files. The serializer rejects arbitrary object IDs (RORB uses ordinal ordering) and labels containing a record delimiter rather than quietly changing them.

## Initial capability matrix

| Feature | Read | Typed JSON | Canonical write | Native/S2 approval |
| --- | --- | --- | --- | --- |
| CMD V2 `.par`, one explicit burst, 1–N ISA entries, lumped or per-ISA routing, loss flag 1/2 | Supported | Supported | Supported | **Neither**; CMD loss flag 2 especially requires native probing |
| CMD `.par` arbitrary bursts or uncharacterised codes | **Unsupported** | Not represented | **Unsupported** | No |
| GUI/RORBwin saved `.par` | **Unsupported**, distinct dialect | Not represented | **Unsupported** | No |
| RORB_GE 002 `.catg`, explicit stack codes 1/3/4/5/7, natural reaches, all-pervious areas, zero special storage/inflow | Supported | Supported | **Computational subset only** with empty drawing | Numerical S2 subset may use explicit float adapter; no native parity |
| RORB_GE 002 special storages, diversions, impervious fractions or uncharacterised controls | **Unsupported** | Not represented | **Unsupported** | No |
| Explicit DESIGN `.stm`, one pluviograph, ISA, burst and source-order subarea depths | Supported | Supported | Supported | No native temporal alignment/rainfall-generation claim |
| FIT, multi-pluviograph, multiple burst/start/dialect storms | **Unsupported** | Not represented | **Unsupported** | No |
| Text `.cat`, mixed `.dat`, manual FIT/hydrograph sources | **Unsupported** | Not represented | **Unsupported** | No |
| Retained single-table `.out` | Separate read-only partial inspection | No input-domain model | No | Completion/print identity unverified |

**Unsupported** is reserved for recognised but uncharacterised numerical constructs/dialects. **Invalid** is used for contradictory counts, truncated records, bad token delimiters, duplicate computational identities, invalid stack operations, non-finite numbers, missing -99 markers and trailing data. `FormatProblem.status`, `.code` and `.line` provide machine-readable diagnostics. Syntax acceptance does **not** mean RORB will accept the generated file, or that S2 can execute the model.

## Tests and private evidence

- Ordinary public synthetic tests cover original-byte preservation (including CRLF and cp1252), canonical/JSON round trips, CMD Windows path spelling, Fortran-D numeric tokens, units, stack validation, unsupported/invalid classification, no-clobber and the S2-only float conversion boundary.
- The user-approved **private** [investigations corpus](https://github.com/Chain-Frost/runoff-routing-investigations/tree/audit/rorb-gui-cmd-forensics/tests/fixtures/rorb/native-corpus) is **not** copied into this public repository. Its independent opt-in regression is `repo-scripts/check_private_parser_corpus.py`. It fingerprints every indexed private file before and after a read-only replay, loads the reviewed baseline `.catg/.stm/.par`, checks a deliberately truncated storm and unknown control, and checks JSON identity. It is **not** part of hosted CI. A full corpus regression must separately characterise each dialect/feature before asserting coverage.
- Quality gate: Windows/Python 3.14, Ruff 0.16.6, strict Pyright, full synthetic tests and build/installed-wheel import outside the checkout. Native or private fixture execution is not a permitted hosted CI step.

## S2 integration handoff

Keep `single_storm.py` on its independent [S2 draft PR #14](https://github.com/Chain-Frost/python-runoff-routing/pull/14). When ready to stack or merge, replace S2's `legacy_inputs.py` reading with the S1 `RunModel` / `to_s2_payload` mapping; construct S2's temporary `Control`, `Catchment`, `Storm`, `Losses` from that payload. Retain S2 control-code and source phase validation, compare every ordinate against the separately frozen evidence contract, and **do not** reinterpret multiple ISAs, FIT, split hydrographs, graphical coordinates or source-timing convention automatically. Preserve PR #12/#13/#14 and the private evidence; link [S1 issue #3](https://github.com/Chain-Frost/python-runoff-routing/issues/3) without closing it.
