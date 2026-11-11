# Agent handoff — S6-P0 independent ARR 2026v1 rainfall intake

**Assignment:** separate rainfall/data-agent; can start now while S1/S2 agents work. **Issue:** [S6-P0 #33](https://github.com/Chain-Frost/python-runoff-routing/issues/33), subordinate to [S6 #8](https://github.com/Chain-Frost/python-runoff-routing/issues/8). **Prepared:** 2026-11-11. **Owner:** unassigned until an agent picks up the work. **Primary contract:** [ARR 2026 input formats](../ARR_2026_INPUT_CONTRACT.md).

## Copy-ready execution prompt

> Implement S6-P0, independent ARR rainfall-data ingestion, from [the handoff](https://github.com/Chain-Frost/python-runoff-routing/blob/docs/2026-11-11-s6-arr-2026-agent-handoff/docs/work/2026-11-11-s6-arr-2026-agent-handoff.md) and [issue #33](https://github.com/Chain-Frost/python-runoff-routing/issues/33).
>
> Read \`AGENTS.md\`, \`docs/DEVELOPMENT.md\`, \`docs/COMPATIBILITY.md\`, \`docs/REGRESSION.md\`, \`docs/work/README.md\`, \`docs/ARR_2026_INPUT_CONTRACT.md\` and the selected issue. Fetch live \`main\` and check for competing work before editing. Use an isolated worktree and create a **new topic branch based on main** (not an S1/S2 branch). Keep changes limited to an independent rainfall data module, synthetic tests and documentation; no changes to existing S1 \`rorb_model\`/\`rorb_codec\`, S2 numerical kernels or reference runners.
>
> Review the official 21 August 2026 Data Hub change and its real public \`2026v1\` JSON/TXT export. Start with strict versioned **offline ingestion/validation** of IFD tables including source/hash, jurisdiction, default/native/current/historical baselines, durations/AEP axes, dataset identity and optional climate-adjusted products. Treat \`All=1\` missing optional datasets as expected; don't invent fields. Use \`Decimal\` and explicit units. Add conservative support for a narrow documented legacy TXT subset; unknown fields/dialects and unsafe conversions must fail clearly, not be guessed.
>
> Deliver a draft standalone PR with an explicit \`parse/validate\` API, original source evidence/provenance, a capability matrix, quality tests (Windows/Python 3.14, Ruff 0.16.6, strict Pyright, installed wheel), a source-versioned sample fixture/spec and a record of unsupported features. Use synthetic data in public tests and read-only opt-in raw external snapshots. No RORB runs, rainfall design-method or numerical parity claims, climate double counting, new hosted automation, package release, merge, force push or public raw/client data.

## Workpack boundaries and dependencies

| Work front | Allowed now | Defer |
| --- | --- | --- |
| S6-P0 / agent | ARR 2026v1 JSON/TXT ingestion and validation, IFD dataset inventory, typed raw source/provenance, synthetic tests | RORB routing or changing S1/S2 model/solver contracts |
| S6-P1 / follow-up | Temporal-pattern ZIP/CSV ingestion; point vs areal bins; safe archives; source ID/proportion validation | Generating routed result acceptance |
| S6-P2 / follow-up | Climate scenarios and IFD/loss/preburst/ARF method policy with documented baseline | Assuming a universal jurisdiction/default policy |
| S6-P3 / follow-up | Explicit storm generation and bridge to S2, RORB and TUFLOW outputs | Claims of equivalence before independent inputs/outputs verify |
| S1/S2 agents | RORB file compatibility, calculations and offline native parity | Implementing a second ARR parser or selecting climate methodology by accident |

## Source observations important for correctness

**Official live JSON** (2026v1) exposes \`datahub_version\`, \`input_data\`, \`layers.RecIFD\` tables with \`index/columns/data\`, \`layers.PointTP.url\`, \`layers.ArealTP.url\`, \`layers.ARFParams\` and \`layers.NewStormLosses\`. Official TXT starts with \`Data Hub Version,2026v1\` and \`[STARTTXT]\`. These are concrete initial fixtures, not a complete declared schema.

**Critical migration issues:** \`Default IFD\` may be a region-specific dataset or envelope; native/historical/current IFD are different baselines, not interchangeable values. Source IFD output uses three significant figures. Preburst ratio/depth and adjusted-loss baseline are separate quantities. SSP/year and already-adjusted rainfall products require explicit policy to prevent double adjustment. Outlet coordinates and representative centroid can affect jurisdiction layers. Don't assume \`Select All\` includes all climate products. Distinguish live production features from the development-server changelog.

**Compare externally** to TUFLOW's new QGIS ARR 2026.2.0 implementation only for independent method checks. Do not vendor plugin code or infer that TUFLOW's default settings are universally correct.

## Inputs and acceptance

- Official live [Data Hub changelog](https://data.arr-software.org/changelog) and [API/usage guide](https://data.arr-software.org/about).
- Live public [JSON example](https://data.arr-software.org/?lon_coord=152.648&lat_coord=-29.573&type=json&All=1), [TXT example](https://data.arr-software.org/?lon_coord=152.648&lat_coord=-29.573&type=text&All=1), and [TUFLOW tool reference](https://wiki.tuflow.com/QGIS_ARR_to_TUFLOW).
- First PR should demonstrate \`JSON -> typed immutable source -> validated IFD set -> JSON/CSV inventory report\` with no hydrologic calculation. Include source SHA-256 and explicit version/units/semantic tags.
- Edge cases: no optional layers; multiple dataset baselines; inconsistent table dimensions; out-of-range or nonsensical AEP labels; missing or old version; huge inputs; Unicode; original bytes intact; deterministic reporting; no-clobber output.
- Code must target Windows/Python 3.14 with no legacy typing imports, pinned Ruff and strict Pyright. Normal unit tests must never make network requests or launch native programs.
- Do not merge any source PR, close #8, claim rainfall-method compliance or publish a package. Record exact head, test counts, limitations and next follow-up. Stop at first-slice boundary.

## Result to report to owner

Provide the new draft PR URL, head SHA, schema/version inventory supported, tested source cases, exact local/CI quality results, one example of a normalised IFD record, and the remaining unknown or method-dependent layers. Distinguish **readable, parsed, validated, processed and hydrologically accepted**.
