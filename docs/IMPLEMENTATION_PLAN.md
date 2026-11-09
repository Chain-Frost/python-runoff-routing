# Staged implementation plan

Planning baseline: 2026-11-09. [Tracking issue](https://github.com/Chain-Frost/python-runoff-routing/issues/1).

## Objective and boundary

Build an independent Python calculation engine. Existing RORB files are the initial input contract and remain a permanent compatibility route. A new TOML/JSON format is added only after a stable internal model exists. GUI replacement, GIS editing and a complete historical feature clone are not prerequisites for a useful first solver.

Separate three questions: can the file be parsed; can its features be executed; have its calculations been validated against a named reference build? A model can pass the first and fail the second. Unsupported numerical features must never be dropped silently.

## Stage gates

| Stage | Workpack | Deliverable | Exit gate |
| --- | --- | --- | --- |
| S0 | [Foundations and reference evidence #2](https://github.com/Chain-Frost/python-runoff-routing/issues/2) | Local quality tools, engine profiles, immutable captures and comparison contract. | Windows reference identities, effective inputs, failure cases and retained output evidence are verified. Scaffolding alone is insufficient. |
| S1 | [RORB import #3](https://github.com/Chain-Frost/python-runoff-routing/issues/3) | Source-aware readers and a typed domain model; inspect/validate interfaces. | Supported files map correctly; malformed/unsupported cases fail clearly; original order and bytes remain intact. |
| S2 | [Single-storm MVP #4](https://github.com/Chain-Frost/python-runoff-routing/issues/4) | Readable deterministic solver, run/compare interfaces and CSV results. | Complete hydrographs, diagnostics and independent invariants pass for the declared subset. |
| S3 | [Deterministic extensions #5](https://github.com/Chain-Frost/python-runoff-routing/issues/5) | Losses/ISAs, reach variants, storage/I-O and GUI-specific features in separate slices. | Every enabled slice has parser, solver and native regression evidence. |
| S4 | [Ensembles and performance #6](https://github.com/Chain-Frost/python-runoff-routing/issues/6) | Prepared model reused across events; bounded batches and optional acceleration. | Event-by-event parity, no state leakage, reproducibility and measured runtime/memory. |
| S5 | [Native format #7](https://github.com/Chain-Frost/python-runoff-routing/issues/7) | Versioned TOML/JSON and external tables. | Both input routes produce equivalent domain models and results. |
| S6 | [ARR preparation #8](https://github.com/Chain-Frost/python-runoff-routing/issues/8) | Auditable design-storm generation, separate from routing. | Generated hyetographs/effective parameters agree before routed outputs are compared. |
| S7 | [Monte Carlo #9](https://github.com/Chain-Frost/python-runoff-routing/issues/9) | Persisted stratified sample plans and weighted frequency analysis. | Replay, probability invariants, convergence and separate native GUI statistical evidence. |
| S8 | [Optional completeness/readiness #10](https://github.com/Chain-Frost/python-runoff-routing/issues/10) | Selected legacy functions and a future publication review. | Explicit scope and owner approval; no publication is authorised by this plan. |

## First usable solver: S2

Support DESIGN calculations using one supplied rainfall burst, uniform rainfall, wholly pervious subareas, one ISA and one kc/m pair, initial/continuing loss, natural reaches and branched networks. The initial control-code subset is 0, 1, 2, 3, 4, 5 and 7. Cover linear m=1 and nonlinear routing, zero-delay reaches and multiple requested print points.

Read .cat/.catg plus .stm and CMD .par, and equivalent combined .dat inputs for this subset. A .catg variant is supported only when its structure is characterised by a fixture. GUI run-configuration .par files are a distinct dialect; recognising the extension does not establish interoperability.

Exclude FIT loss estimation, special storage, diversions, nonuniform rainfall, multiple bursts/ISAs, legacy impervious fractions, DCIA/ICIA, generated design rainfalls and Monte Carlo until their stages. Return a named unsupported-feature diagnostic rather than approximating them.

Implement S = 3600*k*Q^m and k = kc*kr using the documented relationships, then prove the discrete conventions: dav/kr, initial-loss crossing within an increment, rainfall-excess timing, initial conditions, iterative stopping and calculation horizon. Do not replace RORB's method with an arbitrary ODE integrator and call it equivalent. Sources: R1 sections 2.2, 3.3.4, 3.4 and Table 5-2 in the source register.

## Architecture

```text
RORB readers ------> source records + diagnostics --+
                                                   +--> typed model --> prepared execution plan
TOML/JSON reader (later) ---------------------------+                         |
                                                                              v
explicit event / ensemble / MC sample plan ------------------------> event solver
                                                                              |
                                                                              v
                                                                results + diagnostics
                                                                              |
                                                                              v
                                                         comparison / exports / frequency analysis
```

The source representation retains original ordering, locations and uninterpreted non-computational metadata. The domain model is not a new spelling of the RORB text format. The execution plan preserves all order-sensitive semantics. Kernels receive numerical values, not filenames or GUI objects. Start with small focused modules; do not create a plugin framework or empty pass-through layers.

Keep rainfall preprocessing and random sampling outside the event solver. Retain a readable reference backend after introducing an accelerated backend. Select NumPy/Numba or alternatives only when justified and verified on Windows/Python 3.14; no backend or speed claim is pre-approved.

## Work ordering and parallelism

S0 evidence capture and S1 parsing can overlap after the capture/schema contract is agreed. S2 acceptance waits for both. S3 is feature-by-feature, not an all-or-nothing rewrite: S4 can use an explicitly accepted subset without waiting for unused storage or GUI features. S5 depends on the domain model and can move earlier after S2. S6 depends on the features required by its selected storms; S7 depends on accepted event computation, batches and rainfall policies, not every legacy feature.

At most one owner edits a shared model/parser contract at a time. Parallel agents should own distinct workpacks or fixture collections and integrate through explicit dependencies. Every PR states accepted features, remaining exclusions and evidence. A passing scaffold suite never closes S0-S7.

## Deferred work

Automatic FIT/calibration, interactive special-storage design equivalents, uncommon I/O combinations, additional historical dialects and GIS/editor features require separately selected workpacks. Hosted CI, public visibility, redistribution/licensing choices and PyPI publication are independent owner decisions, not automatic consequences of a stage merge.
