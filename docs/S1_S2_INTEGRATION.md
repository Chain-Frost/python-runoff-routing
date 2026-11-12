# S1–S2 Python-only integration

**Status: implementation merged to `main` in [PR #23](https://github.com/Chain-Frost/python-runoff-routing/pull/23), NOT an accepted RORB-compatible numerical implementation.** This document covers the code behind [S1 #19](https://github.com/Chain-Frost/python-runoff-routing/pull/19) and [S2 #14](https://github.com/Chain-Frost/python-runoff-routing/pull/14)/[#18](https://github.com/Chain-Frost/python-runoff-routing/pull/18). Keep [issue #3](https://github.com/Chain-Frost/python-runoff-routing/issues/3) and [issue #4](https://github.com/Chain-Frost/python-runoff-routing/issues/4) open.

## Supported API, source provenance and no-clobber outputs

S1 `RunModel` is the sole input-domain authority; its numbers are `Decimal` and its order-preserving area, reach, control and print identities are explicit. `integration.run_model` delegates numerical conversion to **S1's** `rorb_codec.to_s2_payload`, validates that the resulting floats are usable, constructs the temporary S2 classes without introducing a new parser and runs S2's `calculate_storm` without external processes. Results return the named print locations **in S1 control order**, full source/excess series and `parity_status="unassessed"`. Model elapsed time is `index * timestep_hours`, **not** an interpretation of the native `.out` increment or clock tokens.

```python
from pathlib import Path

from runoff_routing.integration import (
    canonical_run_bytes,
    parse_run_bytes,
    read_run_json,
    run_model,
    write_result_csv,
    write_result_json,
)
from runoff_routing.rorb_codec import (
    parse_catg,
    parse_cmd_par,
    parse_design_stm,
    write_new,
)
from runoff_routing.rorb_model import RunModel, to_json

source = Path(r"C:\RORB\inputs")
parsed = parse_run_bytes(
    (source / "example.par").read_bytes(),
    (source / "example.catg").read_bytes(),
    (source / "example.stm").read_bytes(),
)
result = run_model(parsed.model)  # never starts RORB
write_result_json(source / "python-report.json", result)  # exclusive create
write_result_csv(source / "python-hydrographs.csv", result)

json_run = to_json(parsed.model)
restored = read_run_json(json_run)
par, catg, stm = canonical_run_bytes(restored)
assert (
    RunModel(
        parse_cmd_par(par).model,
        parse_catg(catg).model,
        parse_design_stm(stm).model,
    )
    == restored
)
write_new(source / "canonical.par", par)
write_new(source / "canonical.catg", catg)
write_new(source / "canonical.stm", stm)
```

For a standalone, fully typed JSON input, use [`examples/synthetic-run.json`](../examples/synthetic-run.json):

```python
from pathlib import Path
from runoff_routing.integration import read_run_json, run_model

model = read_run_json(Path("examples/synthetic-run.json").read_text(encoding="utf-8"))
print(run_model(model).to_csv())
```

Callers must name the three input files explicitly. The `.par` file references are recorded as input fields and **never followed** by these APIs. `ParsedRun` retains each complete S1 `ParsedDocument` (original exact bytes, SHA-256, encoding, newline and source map). `RunInputError.diagnostic` separates `invalid` from `unsupported` and includes the input role and a one-based line for parser problems; execution failures do not invent a source line. Canonical RORB_GE output uses S1's empty drawing scaffold and **does not** claim to reconstruct RORBwin graphical metadata. All writes use exclusive-create mode. If writing more than one output, a failure on a later file does not roll back a previously written file.

Use `integration.assess_recorded_print(result, native_tokens, print_id="print_1")` to apply S2's strict *all-ordinate printed precision* audit to an explicitly identified calculated print location. The caller must independently establish the native print column mapping, source/input fingerprints and phase/time-label correspondence. This is an **offline comparison only**, not automatic parity acceptance; do not align series by shifting time, assume a `HydNNN` association, or reinterpret RORB input flags.

The old `legacy_inputs.parse_control_vector`/`parse_explicit_design_storm` interfaces remain only for old S2 fixture and batch-comparator callers. They now delegate syntax recognition to the authoritative S1 parsers and then adapt to the old S2 classes; no second `.catg`/`.stm` field grammar should be maintained. The old private-corpus comparator continues validating retained hashes and native row tokens. It now passes original fingerprint-verified `.catg`/`.stm` bytes to S1 through the compatibility shim rather than decoding as UTF-8 first; S1 retains its UTF-8/BOM or CP1252 source-encoding contract. Its legacy CMD settings extraction and profile provenance remain separately reviewable and are **not** a complete typed run-model acceptance path.

## Capability and acceptance matrix

`Yes` under *compute* means **only** this prototype calculates a finite series for that subset. `No` under *parity* means not proven against native RORB printed ordinates.

| Dialect or feature | S1 parse | Canonical serialize | S2 calculate | Native parity accepted |
|---|---|---|---|---|
| CMD V2 `.par`, 1 burst, loss flag 1, 1 ISA, lumped `kc/m` | Yes | Yes | Yes when paired with matching supported catchment/storm | **No** |
| CMD V2 `.par`, 1–N ISA, loss flag 2, non-lumped routing | Bounded S1 support | Bounded S1 support | **No** (fail closed) | **No** |
| GUI/RORBwin `.par` or arbitrary multi-burst CMD | **No** | **No** | **No** | **No** |
| RORB_GE 002 `.catg`, all-pervious natural reaches, control codes 1/3/4/5/7 | Yes | Yes; empty graphical scaffold only | Yes with validated one-ISA model | **No** |
| `.catg` special storage, impervious, external inflows, uncharacterised control | **No** | **No** | **No** | **No** |
| `.stm` explicit DESIGN, one pluviograph/ISA/burst, start 0 | Yes | Yes | Yes; tighter S2 percent-sum and finite-float gate | **No** |
| FIT, multiple rainfall bursts, nonzero start | **No** or unsupported at S2 gate | **No** for uncharacterised source | **No** | **No** |
| Schema-1 typed JSON (`kind=run`, Decimal strings, explicit units) | Yes | Yes | Yes for the same supported subset | **No** |
| `.cat`, `.dat`, other unknown native inputs | **No** | **No** | **No** | **No** |
| Native single-table `.out` | S1 partial read-only inspection | Not an input writer | No; optional explicit-token comparison only | **No** |

*Parsed* and *runnable* are deliberately separate states. Reject impossible source order, arbitrary IDs in canonical legacy output, float underflow/overflow, unmatched control/print counts and unknown features. The S2 loss-bin crossing, source phase, nonlinear reach solution, `kc/kr` conventions, native time labels and print-location associations remain scientifically unverified.

## Validation and integration merge plan

Public synthetic tests are separate from the private investigations corpus. Run on **Windows / CPython 3.14** with the repository's pinned `ruff==0.16.6`, strict Pyright and installed-wheel smoke test:

```powershell
python -m pip install -e ".[dev]"
python repo-scripts/check_local.py
python -m build --wheel
```

Use the existing Windows `quality.yml` on the draft integration PR. Run private owner-authorised comparisons **locally** only using `repo-scripts/s2_compare_corpus.py` and the corpus fingerprint contract; **never** commit private raw source files, native executable binaries, machine-local paths or reports. A missing corpus means **not run**, not a pass. The native executable is never started by these test APIs.

**Proposed merge sequence and conflict resolution:**

1. Complete and separately review S0 [#12](https://github.com/Chain-Frost/python-runoff-routing/pull/12) before accepting S1 inspection [#13](https://github.com/Chain-Frost/python-runoff-routing/pull/13), then typed/codec S1 [#19](https://github.com/Chain-Frost/python-runoff-routing/pull/19).
2. Independently review S2 routing [#14](https://github.com/Chain-Frost/python-runoff-routing/pull/14), followed by printed-ordinate audit [#18](https://github.com/Chain-Frost/python-runoff-routing/pull/18). Keep their validation obligations separate and use their existing branches, not an unrelated S1 rebasing operation.
3. Integration includes an explicit **two-parent merge commit** (S1 and S2 heads), then integration-only commits. Once both parent lines are merged to `main`, update the integration PR target/branch with a non-forced merge/reconciliation; resolve `README.md`, `docs/README.md` and `docs/work/README.md` by keeping both work histories and explicit links. Keep duplicate old fixture parser excluded from domain authority.
4. Run exact-head Windows 3.14 quality, build/wheel import, public integration tests, then separate private offline replay. Only then request independent numerical/domain review. No issue closure, package publication, native launches or automatic merge from this draft integration branch.

This integration does **not** change S0 reference-capture machinery, hosted workflow permissions or the original S1/S2 PR branches.


## Post-merge reconciliation (2026-11-11)

The already-merged S1 code-7 fix #25 reads the native location from the **physical line following** control 7. This reconciliation preserves two independent labels: the optional inline `ControlStep.label` graphical annotation and `PrintLocation.label` on the following physical line. Typed JSON and canonical reparse retain both; `RunResult` reports the physical label. The bare `7` emitter was tested with CMD 6.44 (201 rows); the optional annotated `7, ...` form remains **native-unverified** and must not inherit that acceptance.

The #21 CP1252 and annotated all-pervious transport fixes already exist in #23's byte-preserving S1 parser adapters, so no duplicate decoder or S2 grammar was imported. Unique independent nonlinear manufactured/equilibrium tests and nonzero annotated impervious rejection were ported. Kernels, loss/phase rules and strict printing budgets were not changed. The previous private 65-case S2 outcomes were **36 discrepant, 25 unreviewed, three expected failures and one incomplete**; they are *not* tests of this installed wheel. See [post-merge record](work/2026-11-11-s1-s2-postmerge-reconciliation.md). Keep #3/#4 open.
