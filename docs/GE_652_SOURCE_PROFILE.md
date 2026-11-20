# Read-only RORB_GE 6.52 graphical source profile

This is an evidence-gathering facility for [original CATG admission issue #197](https://github.com/Chain-Frost/python-runoff-routing/issues/197), not a RORB_GE 6.52 reader, numerical port or native validation.

**Important distinction:** A RORBwin 6.52 output banner identifies the program producing an output report. It does *not* establish that the source CATG header is `RORB_GE 6.52`. A graphical catchment file may retain an earlier GE dialect or the `RORB_GE 002` export scaffold. Do not infer the CATG dialect from a `.out` file.

## Local source inspection

From the public checkout, with the project dependencies installed:

```powershell
python repo-scripts/rorb_inspect.py "D:\Private\Models\catchment.catg" --ge-profile
```

The command prints deterministic, read-only JSON and does not write any file or run RORB. A zero exit status means that one version marker and one graphical end marker were found in the correct order; it **does not** mean the source is admitted, complete, executable or native-equivalent. Missing or duplicate markers return a nonzero status and an aggregate diagnostic.

The profile records only:

- declared graphical version, version/end-marker counts and marker order;
- known graphical section types, declared record counts where recognisable, and histograms of token widths;
- whether the numerical tail begins with exactly `0`, exactly `1`, another record or nothing, plus a noncomment record count;
- source byte length, newline family and fixed structural diagnostic codes.

The JSON omits original bytes, paths, title, catchment/reach/node names, source labels, coordinates, rainfall, numerical operands and unrecognised custom section names. Unknown section headings are recorded as `other_section`. **Source SHA-256 is omitted by default**. To include it in locally retained provenance only, explicitly select `--ge-profile-sha256` alongside `--ge-profile`. Review any output before sharing externally; a file size or fingerprint may itself identify a private source.

For multiple local CATGs, call the same pure API without uploading the originals:

```python
import json
from pathlib import Path

from runoff_routing.rorb_ge_profile import profile_graphical_catg

root = Path(r"D:\Private\Models")
profiles = []
for path in sorted(root.rglob("*.catg")):
    result = profile_graphical_catg(path.read_bytes())
    if result.declared_ge_version == "6.52":
        profiles.append(json.loads(result.to_json()))
print(json.dumps(profiles, indent=2))
```

This output is structural only and carries no mapping to the original project files. Keep any file-to-profile mapping and original source hashes in private custody, not in the public repository.

## Qualification boundary

- `parse_catg` continues to **reject RORB_GE 6.52** as `ge_652_unqualified`. The typed computational model, source editor and selected engines remain unchanged. The CLI profile cannot bypass the parser.
- The published tests mutate only an already approved **2,913-byte RORB_GE 6.45** public fixture to create a **synthetic 6.52 header**. These tests qualify the profiler, not actual 6.52 source grammar.
- An original GE 6.52 CATG with its full graphical and computational records, securely inspected locally, is required to identify actual differences in section order, node annotations, background-image metadata, print sites and control/reach modes. Any implementation must preserve the exact computational vector; no network-topology inference from drawing is authorised.
- Recognised-but-unsupported storage sections, control codes 8 / 7.1 / 7.2, multiple physical print/excess modes, saved RORBwin PAR, embedded rainfall filtering and spatially varied preparation retain their own explicit gates under #5/#91/#144/#8. Do not coerce unsupported inputs to a recognised subset.
- Native numerical qualification also requires matched original effective inputs, physical sites, native profile and full hydrographs; a header inspection or synthetic source change is not a routing pass.

See [the five-set existing-project receipt](work/2026-11-19-anonymised-site-e-validation.md), [current compatibility contract](COMPATIBILITY.md) and [the single CMD feature matrix](CMD_FEATURE_MATRIX.md).
