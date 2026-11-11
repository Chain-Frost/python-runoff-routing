# Local Windows agent handoff — RORB behavior and bug archaeology

**Assigned work:** [audit issue #16](https://github.com/Chain-Frost/python-runoff-routing/issues/16).

**Start:** Check latest main and open branches. Create a new, independent topic branch or worktree (suggested name: audit/rorb-gui-cmd-forensics) without modifying S0 PR #12, stacked S1 PR #13, S2 PR #14 or documentation PR #15. No agent is automatically assigned merely because this handoff exists.

**Read before doing anything:** AGENTS.md, docs/DEVELOPMENT.md, docs/COMPATIBILITY.md, docs/REGRESSION.md, [audit and warning policy](../BEHAVIOUR_AND_WARNINGS.md), the issue, and the S0/S1 work records on their own branches. The source repo currently reports public visibility; do not make any sensitive content available publicly.

## Mission

Help build an open, performant and auditable Python replacement by discovering both **observable and latent** RORBwin/RORB_CMD bugs, distinguishing deliberate legacy behavior from mistakes, and preserving full legacy file import/export interoperability. The goal is to understand consequences and produce reproducible evidence to support user warnings when the new implementation deliberately behaves more correctly than historical RORB.

Do **not** begin with a wholesale decompilation or write a competing hydrological solver.

## A. Establish reproducible provenance and isolated workspace

1. Inventory locally installed RORBwin.exe, RORB_CMD.exe, related runtimes and legitimate sample models. Record SHA-256, observed executable version/banner, installed file inventory, OS, timezone/locale, and input path semantics. Distinguish actual versions from the documentation's historical 6.31/6.52 claims.
2. Create a local scratch tree outside production folders, e.g. an ignored .local/forensics folder with independent input copies, outputs, logs, GUI-state evidence, file/registry traces and per-case manifest. Use read-only originals and verify original hashes before and after.
3. Read and reuse PR #12's reference-capture schema and command rather than inventing a second native runner. Run one known permitted/isolated native case first. Do not run dozens of cases before confirming all output locations and write behavior.

## B. Test GUI entry and persistence, not just output numbers

For each GUI hypothesis, collect a **five-state record**:

- value the engineer deliberately entered / selected;
- value the GUI displays, including whether a dependent control is enabled;
- value saved to .par, .catg, .stm or generated supporting file;
- value shown after closing/reopening or creating a new catchment;
- value demonstrably applied in the native calculation (echoes, generated storms, raw result differences, or an explicit unknown if not observable).

Start with controlled **Cancel / Apply / Save / reopen / new model** sequences and change only one factor at a time. Compare GUI and CMD only where their execution capabilities and inputs are genuinely equivalent. Capture GUI settings and raw files before and after; record screenshots only if permitted and scrub user/project details.

User reports that there are known user-facing RORB GUI input bugs. Do not guess those bugs. Keep a finding field for user-supplied steps and integrate additional confirmed reports when provided.

## C. Probe known release-note anomalies

Use the v6.52 release notes to select controlled, independent cases for:

- GUI selection persistence of constant versus varying losses;
- varying IL/CL with AEP and duration; wrong indexing;
- preburst ARF double application and PMP-related ARF handling;
- off-by-one report/CSV time labels;
- wrong ensemble/Monte Carlo representative temporal pattern selection;
- CMD code-11 rainfall-excess outputs;
- stale ARR data references after Cancel/new model;
- computational changes when only graphical/editor coordinates should change.

Each probe must specify exact engine hash/version, a single changed input, complete input/effective-output evidence and a possible falsifying observation. A historical bug fix is NOT proof that today's executable has the bug.

## D. Discover bugs not documented in manuals

Design **bounded automated tests and invariants**:

- Metamorphic: independent run order, reload/save idempotence, identical effective values entered in different UI sequences, same data through GUI and CMD where supported, numerical conservation, zero inflow and rainfall.
- Boundary: timestep length, horizon, maximum increments, loss-factor boundaries, small/large coefficients, m around 1, zero/negative/nonfinite values, duplicate IDs, D-format exponents, column and field widths, missing -99 sentinels, multiple bursts/ISAs and version-specific unsupported cases.
- File handling: path spaces/Unicode/UNC, changing working directory, relative external references, file name collisions, output placement, output overwritten or silently reused.
- Latent defect hypotheses: stale in-memory arrays between GUI runs, unseen default changes, mis-indexed ISA or rainfall patterns, hidden row limits, silent truncation, incorrect fixed-field offsets, state leakage between multiple simulations.

For errors, record a minimal reproducer and whether it is a GUI input, file reading, hydrological algorithm, numerical precision or reporting defect. A statistical difference or crash alone is insufficient to identify cause.

Use Process Monitor on short permission-cleared cases to trace native file/registry reads/writes and a reproducible source-directory write audit. Save filtered trace summaries and raw traces locally, not in the public repo.

## E. Legacy file interoperability / CatchmentSIM workflow

The [CatchmentSIM RORB help](https://csse.com.au/csim_online_help/rorb.html) states that exported .catg files may not contain executable RORB control code until opened and saved in RORB GE; and that GE Rescale can lose real-world coordinates.

Test this workflow with a permitted catchment and retain before/after byte hashes, parsed numeric/control records, node identifiers, coordinate reference intent and output print locations. Separate:

1. Byte-perfect read/write of an unchanged source file.
2. Semantic edit/export and subsequent successful re-import into GUI/CMD.
3. RORB GE regeneration of computation codes and graphical/real-world coordinate preservation.
4. Numerical parity for the same effective catchment and explicit storm.

Build a dialect inventory for .cat/.catg/.dat/.stm, RORBwin saved .par, RORB_CMD V2 .par, .out, batch.out and later .pat/.ifd/.mc. Recognize incomplete/GUI-only files as such, not automatically malformed. Fail closed on unknown numerical records; preserve comments and metadata without inventing missing control codes.

Do not implement S1 parser internals or alter input semantics without coordinating with its existing PR #13 author.

## F. Selective binary analysis — explicit legal gate

First perform read-only PE header/runtime/symbol/import/format/error-string inspection on authorized local copies (no binary modification, protections bypass, unapproved upload or code extraction). Record possible internal routines and, for each, a behavioral question that can be checked by controlled execution.

If that is insufficient, propose a **narrowed question for targeted disassembly** (example: how a documented nonlinear routing convergence exit is selected, or why a GUI input selection is ignored). Decompilation/disassembly is outside the scope authorized by this workpack. **Do not proceed** until rights/legal scope, licensing and repo instructions are explicitly reviewed and amended where applicable. Do not include disassembly/decompiled source in Python implementation PRs; record independently verifiable behavior instead.

The audit is not a legal clearance.

## G. Findings and warnings

Create a versioned machine-readable finding register (e.g. JSON with schema version) and readable summary. Minimum fields: finding ID, area, hypothesis/confirmed/intentional/disproved status, exact engine version/hash, reproducible steps, raw input/output checksums, GUI entered/displayed/saved/reopened/effective states, invariant/specification, numerical significance, severity, independent corroboration, affected versions/conditions and Python treatment.

For a demonstrated legacy defect, propose a stable diagnostic ID and clear user message:

- The old RORB build would have interpreted/generated X.
- This implementation uses Y, because of documented or independently verified reason Z.
- The affected location/parameters and potential result difference are supplied.
- The user can select a verified compatibility profile or accept the corrected calculation, where available.

Do not assert a version bug or numerical improvement from a single source's disagreement; record uncertainty explicitly. Never retroactively loosen regression tolerances to manufacture agreement.

## H. First-tranche acceptance, delivery and coordination

Aim for an **auditable investigation**, not a fixed quota of confirmed bugs:

- One executable/profile inventory with hashes and separately identified GUI/CMD builds.
- At least **three** distinct, minimized defect hypotheses systematically investigated; each clearly confirmed, disproved or unresolved.
- At least **two** GUI entered/displayed/saved/reloaded/effective-state probes.
- A permitted single-case Process Monitor trace with actual file-write location checks.
- A CatchmentSIM/GE-style .catg round-trip characterization **where the necessary input/tools are available**; otherwise a concrete fixture request and no unsupported claim.
- A versioned finding register, at least one **draft** warning example, documented file-compatibility levels and a prioritized follow-up list.
- Windows Python 3.14 quality checks on any new code (pinned Ruff, strict Pyright, focused pytest); no proprietary data in Git. Keep user cases private and artifacts auditably hashed.
- Report exact source branch/commit, native execution count, input/output integrity, evidence local paths (redacted in public PR), passed/failed/not-run checks and one next action.

**Delivery:** create a draft PR tied to #16, update the dedicated status record, and comment on S0/S1/S2 issues with findings relevant to their work. Do not merge, release, change visibility or enable new workflows. Native validation of S0 remains its own acceptance gate; this workpack does not close #2/#3/#4.

**If blocked:** deliver tested black-box/file-preservation probes, the finding register schema, exact missing evidence and the highest-value focused next experiment. Do not invent results or claim work occurred.
