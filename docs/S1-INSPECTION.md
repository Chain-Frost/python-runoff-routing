# S1 read-only RORB inspection (with bidirectional input subset)

[Issue #3](https://github.com/Chain-Frost/python-runoff-routing/issues/3) is a staged parser/model task. The initial CMD/.out inspector remains supported. A limited `.catg`/`.stm` bidirectional parser is now documented in [S1 input model](RORB_BIDIRECTIONAL.md); neither is an accepted native solver or hydrological compatibility claim.

## Usage

After installing the package on Windows/Python 3.14:

```powershell
py -3.14 repo-scripts/rorb_inspect.py .local\models\reference.par
py -3.14 repo-scripts/rorb_inspect.py .local\captures\run.out
```

The command prints JSON diagnostics and a byte fingerprint. Exit 0 means a supported *inspection* (`parsed` CMD parameter subset, or `partial` retained output), 1 means `unsupported`/`invalid`, and 2 means read/decoding failure. It never starts RORB, follows external references, writes a modified source, updates expected outputs or infers an executable version.

## Accepted **syntax**, not native behaviour

- RORB_CMD V2 `.par`, with exact `# BEGIN`/`# END`, column-11 data, catchment and storm references, lumped flag, verbosity, explicit loss model 1 or 2, ISA count and source-order routing/loss pairs. All ISA loss records are retained even when routing uses one lumped kc/m pair. The single-burst subset is parsed into typed, source-independent parameter records; GUI `.par`, unknown flags and multiple-burst variants return `unsupported`.
- Retained `.out` with one `Inc Time HydNNN` table. Preserve printed time tokens, row/increment order and columns; validate finite values, contiguous increments, positive time order and printed time-step rounding where metadata is present. Check a reported calculation duration when available. A returned `partial` is intentional: print locations, native behaviour and completeness without duration remain unverified.
- RORB_GE 002 `.catg` natural-reach, fully-pervious, codes 1/3/4/5/7 and single explicit DESIGN `.stm` now return `parsed` with independent typed source models, exact source fingerprints and source spans. These **limited** grammars have separate canonical writers and JSON interchange; inspect-file status still does not authorise numerical execution.
- Text `.cat`, mixed `.dat`, GUI `.par`, FIT, multi-burst, special storages and uncharacterised numerical features explicitly return `unsupported`.

Every inspection retains the original line text, source path and SHA-256. Parameter records and output rows have one-based line numbers. Original `.par` numerical tokens use `Decimal` (including Fortran `D` notation), not float-based flag comparisons; a CMD loss-model flag of 2 generates a specific provenance warning because the guide/example conflict needs native probing.

## Source reuse and known exclusions

Interpretation is based on the user-owned [ryan-tools PR #233](https://github.com/Chain-Frost/ryan-tools/pull/233), revision `c5811226bd97343eda7002d5a89513f7b0c5b019` (especially its conservative `parameter_reader.py`/`output_reader.py`), and the separate [S0 capture](REFERENCE_CAPTURE.md). The code is a focused, standalone adaptation; neither PyHMA nor pandas nor the MCP server is imported. Existing ryan-tools native/private-data acceptance is not transferred.

**Known limitations:** general catchment/control dialects beyond the explicit RORB_GE subset; graph and gauge mapping; equivalent combined `.dat`; `.catg` variants; multi-burst CMD; GUI saved settings; rainfall/excess code 11; multiple output summaries; native time labels, site identities and cross-engine parity. These remain issue #3 or later-stage work and must not be silently ignored during a solver run.

## Validation and next input

Synthetic tests validate the documented single-burst layout, lumped/unlumped ISA ordering, `D` exponents, CRLF, malformed/truncated records, unsupported signatures, raw tokens, time-grid rounding and read-only behaviour. They are **not** S1 numerical acceptance. Extend from evidence-backed `.cat`, `.dat` and additional `.catg`/`.stm` samples, and validate against named native profiles before claiming generality.
