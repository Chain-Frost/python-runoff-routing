# RORB legacy-behavior audit and compatibility-warning contract

Status: proposed policy, not an implemented feature. Tracking: [independent audit issue #16](https://github.com/Chain-Frost/python-runoff-routing/issues/16). Related: [S0 #2](https://github.com/Chain-Frost/python-runoff-routing/issues/2), [S1 #3](https://github.com/Chain-Frost/python-runoff-routing/issues/3), [S2 #4](https://github.com/Chain-Frost/python-runoff-routing/issues/4).

## Purpose

Deliver a **faithful import and independently correct, transparent calculation system**, not an uncritical clone of legacy mistakes. Historical RORB may exhibit errors in the graphical entry layer, persisted settings, execution preprocessing, routing engine, or reporting. These boundaries must be tested separately.

The same input can have four different representations:

1. User-intended state: what the engineer selected and entered in RORBwin.
2. GUI displayed state: what the interface currently shows, including defaults, stale selections and dependent controls.
3. Persisted/transported state: contents of .cat, .catg, .dat, .stm, GUI .par, CMD .par and any generated effective data.
4. Executed state: settings/rainfall actually used by a named RORBwin/RORB_CMD executable and its reported results.

Do not infer layer 4 from layer 2, or layer 2 from a saved file. Instrument the transitions. In particular, changing a GUI field followed by Cancel, reopen or a new catchment may leave hidden state inconsistent with the visible field. A plausible-looking output does not prove the intended value was applied.

## Three distinct equivalence promises

| Contract | What is required | What is not implied |
| --- | --- | --- |
| Source preservation | Read and retain exact bytes, line endings, field tokens, source spans, ordering and unknown non-computational metadata; unchanged files can be emitted byte-for-byte. | Parser or numerical support. |
| Semantic round-trip | When edited, export files preserving documented computational meaning, stable IDs and control-vector ordering, graph topology, parameter mappings, GUI references and real-world coordinates; verify acceptance by the relevant legacy tool. | Byte-identical output after an intentional edit, or numerical identity with another RORB build. |
| Version-profile numerical parity | An identical, explicit effective model and time grid produces matching hydrographs, with reviewed tolerances, named engine hashes and traceable output locations. | Mathematical correctness, absence of native bugs, or equivalence across GUI and CMD. |

Record which of these contracts is supported for each dialect, engine version and feature. Do not silently skip unknown computational records.

### CatchmentSIM / RORB GE boundary

CatchmentSIM's [RORB export documentation](https://csse.com.au/csim_online_help/rorb.html) says its generated .catg may include graphical-editor data **without generated RORB computational code**, which RORB GE adds on opening and saving. It also warns that Rescale can discard real-world coordinates. Test and document separately:

- direct imported .catg representation;
- computation codes before and after GE save;
- changed/unchanged geometry and georeferencing after save and after Rescale;
- print-location and network ordering before/after;
- execution success and routed results using a controlled storm.

A GIS editor should not silently invent or regenerate numerical control codes without telling the user; equally, a strict importer should not reject valid pre-save graphical-only files as malformed if they are a recognized dialect.

## Legacy behavior versus improved behavior

Two explicit user-selectable concepts are proposed:

- **Legacy compatibility profile:** reproduce the specified, verified RORB build's behavior when necessary for an auditable migration or exact comparison. Keep quirks and exceptions **version-scoped**. Some defects may be unsuitable to reproduce, in which case explain the limitation rather than pretending parity.
- **Corrected / independently audited calculation profile:** implement documented physical/mathematical intent with validated numerical methods. Warn whenever this produces a **material** difference from a known legacy behavior affecting the supplied model.

Never use a single global "RORB mode" that assumes all RORBwin, CMD and historical releases behave identically. Declare unknown or ambiguous version cases explicitly; default to clear rejection for unsupported executable behavior.

A compatibility warning should identify **which old behavior**, **which engine/version**, **affected inputs**, **physical/numerical consequences**, **what was done instead**, **why** and **how to reproduce/compare**. Warning IDs must remain stable. Diagnostic severity should be error for ambiguity that prevents a defensible calculation; warning for accepted but materially changed model behavior; info for lossless cosmetic differences.

A warning must never claim a bug was present in the user's original run solely because a historical release note describes one.

### Example warning contract (illustrative; not a verified bug)

~~~json
{
  "id": "RORB-GUI-LOSS-STATE",
  "status": "hypothesis",
  "legacy_profile": {
    "engine": "RORBwin",
    "version_observed": null,
    "executable_sha256": null
  },
  "trigger": "GUI displayed loss policy differs from persisted/effective policy",
  "severity": "warning",
  "input_location": null,
  "legacy_effective_value": null,
  "new_effective_value": null,
  "explanation": "A retained GUI state must be verified rather than inferred.",
  "evidence_id": null,
  "reproduction_id": null,
  "recommendation": "Check the saved settings and re-run a pinned reference case."
}
~~~

This is a design example. Do not ship it as a factual warning until a version-pinned reproducer exists. Parameter-level differences and source locations should be emitted in machine-readable JSON as well as concise human-readable text.

## Versioned finding register

For each **suspected or confirmed** issue, retain:

- finding ID, short description and category (GUI entry / import / persistence / preprocessing / solver / reporting / numerical stability / output format);
- status: hypothesis, reproduced, corroborated, intentional/documented, version-dependent, disproved or unresolved;
- engine kind, installed executable hash, observed banner/build, OS, options and effective inputs;
- minimal authorized reproducer; source/input SHA-256; before/after GUI values and saved bytes; screenshots or screen-state records where permitted;
- exact expected invariant or specification; observed behavior; comparison with independently calculated references or another engine; full ordinate differences when applicable;
- severity, result consequence, affected parameter ranges and event/time-grid conditions;
- reproducibility evidence (test type and count, independent reruns, frozen expected output, unique event ID);
- intended Python behavior and warning/error policy;
- original evidence location, permissions, responsible reviewer, source of claim and remaining uncertainty.

Keep distinct **engine bug**, **UI/persistence bug**, **documented but surprising behavior**, **hydrological modeling assumption**, **incorrect source data**, **parser misunderstanding** and **unclassified divergence**. A bug is not confirmed merely by Python disagreeing with native RORB.

### Priority hypotheses from historical release notes

The supplied RORBwin v6.52 release notes describe fixes concerning CMD code-11 rainfall-excess hydrographs, timestep labels/CSV alignment, variable initial and continuing losses across AEP/duration, ARR pre-burst application and ARF double-application, GUI loss-policy persistence, temporal-pattern selection and Monte Carlo/ensemble representative selection. These are **test seeds**, not claims that the current user's installed executables still contain the defects. Capture a distinct build fingerprint for every probe.

## Systematic latent-defect discovery

Use more than known bug reproduction:

1. **State-machine testing:** changed GUI value, cancel, load new model, save, reopen, switch tabs, batch run; assert visible = persisted = effective when specified to be equivalent. Identify stale caches, defaulting, edit-order dependence and hidden state.
2. **Grammar and boundary tests:** small/large counts, missing terminators, decimal/Fortran numeric tokens, duplicate labels, early EOF, invalid flags, mixed line endings, coordinate ranges and maximum run increments. Never run destructive stress tests against client projects.
3. **Metamorphic properties:** identical run after reloading; identical event after prior unrelated run; different GUI entry order with equal effective settings; area/rainfall scaling with expected effect; zero rainfall, zero inflow, conservation, time-grid refinement, unchanged topological identities under purely graphical edits.
4. **Differential tests:** GUI vs CMD with explicit comparable settings, historical binaries where lawfully available, independent analytical cases and Python reference kernel. Differences require a cause classification rather than averaging or tuning tolerances after seeing results.
5. **Numerical stability:** non-finite/negative/near-zero values, long time steps, m close to 1, small storage, zero runoff, high flows, ties/plateaus, solver non-convergence, overflow and branch-order sensitivity.
6. **Targeted static inspection:** PE metadata, imports/exports, embedded error/format strings and compiler/runtime hints can suggest hidden features, branches and code paths; no automatic claim of a defect from a string or symbol alone. Use these hints to design observable tests.

Randomized or combinatorial probes must have bounded case counts, independent seeds, isolated scratch outputs and full audit manifests. A crash or no response must become a reproducible failure report, not a silently discarded run.

## Source and rights boundary

The user-supplied RORB v6 manual contains a licence that restricts modification/development of the licensed software. Australian Copyright Act section 47D provides a limited **conditional** interoperability exception; it is not a blanket licence for whole-program decompilation or copying implementation details: [legislation.gov.au](https://www.legislation.gov.au/C1968A00063/2026-04-02/2026-04-02/text/original/epub/OEBPS/document_1/document_1.html).

Under current [AGENTS.md](../AGENTS.md), **decompilation is prohibited**. This handoff authorizes **only** normal authorized execution, isolated black-box experiments, file/GUI observations, system-call tracing and read-only PE metadata/string inspection within applicable rights. For targeted disassembly or decompilation, first raise a written, narrowly scoped permission/legal-policy decision and update repository instructions if authorized. Do not circumvent protection mechanisms, patch RORB, upload binaries to third-party analyzers or commit binary-derived code, pseudo-code, disassembly, private strings or proprietary sample files.

The eventual independently authored Python code should derive from public mathematical specifications and separately reviewed behavioral tests, with traceable provenance. This project is public at the time of this document; avoid uploading sensitive working evidence.

## Dependencies and delivery

- S0 PR #12 owns native execution/capture and reference manifests: **reuse, do not fork a competing runner**.
- S1 PR #13 owns parser/typed model: deliver concrete syntax/round-trip contracts to it; do not overwrite its code.
- S2 PR #14 owns the mathematical reference kernel: send documented numerical hypotheses/fixtures; do not replace the solver from this audit workpack.
- Documentation PR #15 inventories historical manual inputs and source/version mismatches. Do not equate PDF printed values with unverified distributed samples.
- [Local-agent start prompt](work/2026-11-11-rorb-forensics-handoff.md) defines immediate execution and acceptance gates; [work record](work/2026-11-11-rorb-forensics.md) is the authoritative audit status.
