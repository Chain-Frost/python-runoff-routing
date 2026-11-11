# S2: offline single-storm computational slice

**State:** Prototype implemented, numerical parity unaccepted. **Target:** Windows / Python 3.14.  **Date:** 2026-11-11.

This slice extends [the standalone reach kernel](2026-11-10-s2-reach-kernel.md) without adding a dependency on native executables or the unmerged S0/S1 branches.

## Implemented

- Pure discrete natural-reach routing from the original S2 kernel and a separately derived exact continuous linear-storage reference, with stepwise trapezoidal balance and initial/final storage.
- Pure DESIGN storm computation for a precisely bounded subset: one fully pervious ISA, uniform explicit temporal pattern, initial/continuing losses, `kc` and `m`, natural reaches, source/stack/confluence/route/print controls `1/3/4/5/7`, area-weighted `dav`, and multiple print points with a final complete outlet. Control `0` terminates the imported vector. Source flow is placed at the ending sample of each rainfall bin.
- Strict fixture adapters for the matching RORB_GE `.catg` control vector and explicit `.stm` grammar. Unrecognised reach types, impervious inputs, special storage, codes `2/6`, external inflows, multiple ISAs, FIT mode, and unknown storms fail explicitly. These narrow adapters do not replace S1's intended general parsers.
- Offline comparison against a separately authorised, **private** corpus with input/manifest/output SHA-256 checks, sample-by-sample Decimal printed-value comparison, raw native increment/time labels, native and predicted peaks/indices, RMS and maximum discharge error, outlet integrals and optional per-ordinate CSV/JSON. No corpus contents are committed or bundled in the public repository.

## Scientific status

The independent continuous linear storage solution assumes linearly interpolated inflow; the discrete reference solves the trapezoidal recurrence. They are distinct mathematical references at finite time increments. The IL/CL bin-crossing, source phase, legacy nonlinear stopping, time-offset and native volume conventions remain compatibility hypotheses.

The retained native corpus includes whole-catchment output, not prescribed individual-reach inflow and storage. Matching a whole-catchment peak does not establish full-ordinate or reach-level parity. The offline comparator deliberately reports measured differences and **does not apply an after-the-fact passing tolerance**. Profiles unsupported by the narrow input adapter are not accepted by default; unchanged input hashes alone are not numerical validation.

## Local validation

- Linux/Python 3.13.5 synthetic-only tests for the new computations, parser rejection, offline comparator and storage audit: 50 passed. No RORB invoked. Basic compilation was checked.
- Exploratory independent cross-checks, using three complete CMD hydrographs read from the owner's separately authorised private corpus, showed identical peak sample indices and peak differences within 0.06%. Individual ordinate differences exceed the output rounding resolution; these checks are not native parity acceptance and are not golden baselines.
- Windows/Python 3.14, pinned Ruff 0.16.6, strict Pyright, installed-wheel validation and Python-vs-full-private-corpus execution: **NOT RUN** in the authoring environment. Do not report these gates as passed.

## How to compare without RORB

Keep the private investigations checkout alongside the source checkout; never copy its `tests/fixtures/rorb/native-corpus/` into the public repository. After installing the Python package, set `CORPUS_ROOT` and `CASE_IDS` in `repo-scripts/s2_compare_corpus.py` and run the script. It prints machine-readable summaries. Import `compare_corpus_case` to access all exact raw output tokens or `to_csv()` for complete row-level diagnostics.

## Next gate

On Windows/Python 3.14, run the full source-quality/wheel checks and the offline comparator on all characterised CMD cases. Record every unsupported and discrepant case, including complete hydrographs and timing/volume deltas, without adjusting tolerances. Obtain a separately observed, controlled single-reach input/outflow and storage reference before accepting the root-finding and phase conventions. Only then broaden the one-ISA parser and remaining control codes.

**Keep PR #14 draft and issue #4 open**; do not merge, publish the corpus or release a package on the basis of this prototype.
