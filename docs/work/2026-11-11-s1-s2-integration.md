# Handoff C — S1 typed model / S2 numerical prototype integration

**Current status (2026-11-12):** The Python-only implementation was merged into public `main` via [PR #23](https://github.com/Chain-Frost/python-runoff-routing/pull/23) as `a558c0ce9679949cf15ef5be024d8f4b0a7637f6`. Previous draft-state wording below records historical development. **Native numerical S2 parity remains unaccepted:** four linear supplemental profiles pass, while all 36 computed CMD whole-catchment cases fail frozen printed precision. [Current merge and validation record](2026-11-12-s1-s2-implementation-merge.md). Stage issues #3/#4 remain open.

**State:** implementation in draft; S1 code-7 changes reconciled; all scientific acceptance gates open. **Date:** 2026-11-11. **Owner branch:** `feat/s1-s2-integration-owner-20261111`.

## Upstream dependency map

- S0 #12 (`feat/s0-reference-capture`): original reference capture and provenance; no changes in this work.
- S1 inspection #13 (`feat/s1-cmd-inspection-ci`) based on S0; S1 typed source model #19 (`feat/s1-bidirectional-parser`) based on #13. Selected S1 parent: `f356ec51a470ae1ab9e6919d7c4e5744674a3b38` at integration creation.
- S2 routing #14 (`feat/s2-reach-reference-kernel`) based on `main`; S2 all-ordinate comparator #18 (`feat/s2-printed-ordinate-audit-20261111`) based on #14. Selected S2 parent: `53021ff23ccb4ee46ddf9a528775b14220d7051e`.
- Integration merge `7774213161ff73f684a830f03d6743c273d74eb8` has both parent heads, with S1 tree plus S2-only computation, comparator, documentation and synthetic tests. No force-update, native raw corpus, native executable or parent PR modifications.

The S1 `RunModel` / schema-1 JSON and S1 parsers/writers are authoritative, and its `to_s2_payload` is the sole source Decimal-to-float boundary. S2 temporary `Catchment`, `Control`, `Storm`, `Losses` are only calculation DTOs. New `integration.run_model` provides preflight feature/numerical checks, ordered typed print results, no implicit native `HydNNN` mapping, JSON/CSV and no-clobber output adapters. The legacy S2 text parsing surface is now only a shim over S1, not an independent parser.

## Separate tests and unaccepted evidence

- S1 source/serialization/JSON tests: public synthetic, no private fixtures.
- S2 reach, storm and full-ordinate comparison tests: public synthetic, no native launch.
- Integration tests: source -> typed -> JSON -> canonical -> source, float boundary fail-closed, print identities, result/CSV and no-clobber. Synthetic-only.
- Private corpus and real CMD time/print mapping: must be executed separately on authorised Windows machine, with full hashes and explicit *unsupported / incomplete / discrepancy* accounting. A missing corpus never counts as a pass.

## Open design gates

- Whole-catchment peak resemblance does not establish raw-ordinate numerical parity.
- Per-event native phase, time increments, output column identity, exact loss crossing, RORB nonlinear root stopping and other control codes remain unverified.
- Canonical `.catg` graphical scaffold is computational-only and not native-verified.
- Multiple ISA, impervious, FIT, storages and GUI `.par` are not made runnable by this PR.
- Keep #3 and #4 open; PR remains draft. No merges, releases, workflow-permission changes or native executables.

See [integration API, sample and feature matrix](../S1_S2_INTEGRATION.md) for the cold-start contract and staged merge order.

## Exact-head public validation (2026-11-11)

- Integration source/solver commit: `9e57ce29f93fa17634169d4d5a452a59e97dc44a`.
- Hosted Windows quality [workflow run 43037231240](https://github.com/Chain-Frost/python-runoff-routing/actions/runs/43037231240): **passed** on Windows/Python **3.14.10**.
- Repository hygiene: **67 files, 0 errors**.
- Pinned Ruff **0.16.6** lint: **passed**; Ruff format: **58 files already formatted**.
- Strict Pyright **1.1.414**: **0 errors, 0 warnings**.
- Non-native, non-benchmark public pytest: **193 passed**, including the typed S1 parser/writer, S2 solver and comparison, S1-backed legacy shim and new integration round-trip tests.
- `python -m build --wheel`: **passed**; install and import of the wheel outside the checkout: **passed**.
- Separate authorised **private full-corpus** offline comparisons: **NOT RUN** for this integration branch. Native RORB launches: **NOT RUN**. Full numerical parity: **NOT ACCEPTED**.
- This PR is intentionally draft. The documentation-only follow-on commit does not upgrade the scientific acceptance state.

## S1 upstream reconciliation (2026-11-11)

S0 #12, S1 inspection #13, S1 typed API #19 and corrected native code-7 writer #25 are merged to `main`. The integration draft merges the current `main` tree (preserving all newer capture, parser, tests and policy changes) with the S2/integration-only files. Its public synthetic `.catg` fixtures now use code 7 followed by a separate physical print-location record. S2 #14/#18 and overlapping transport correction #21 remain independent and subject to review; the rejected duplicate #22 does not supply an authoritative parser. Exact-head Windows quality and private evidence must be verified separately. No numerical stage or RORB native serialization is accepted by this reconciliation.

## S1-backed offline source transport

The retained offline S2 comparator passes SHA-256-verified original `.catg` and `.stm` bytes through the S1 grammar via the compatibility adapter. This preserves legacy CP1252 input support, avoids a duplicate parser, and retains original evidence hashes. Public synthetic regressions include CP1252 catchment/storm text and an annotated all-pervious sentinel. These are input-transport checks, not a private-corpus replay or numerical acceptance; overlapping S2 #21 must be reconciled independently before merging.

## Implementation merge outcome (2026-11-12)

The reviewed head `55aac4f51db1f994239b3c052598a1cc09787599` passed Windows/Python 3.14.10 Ruff 0.16.6, strict Pyright and 247 synthetic tests, with successful out-of-tree wheel import. The final private installed-wheel campaign verified 1,026 indexed files and classified 65 originals (36 computed CMD failures against fixed print precision, 25 unreviewed, three expected failures, one incomplete reference); the four limited linear profiles passed. All 16,836 integrated Python predicted ordinates matched the retained Python comparator and the prior numerical CSVs were unchanged. The only historical report difference was three S1 failure-message strings. These are software regression findings, **not** acceptance of native RORB equivalence.

The repository allows squash merges only; the implementation was merged as `a558c0ce9679949cf15ef5be024d8f4b0a7637f6`, without a release, native run, private fixture transfer, tolerance change or golden replacement. The dependent pure nonlinear diagnostic remains a separate unaccepted draft [PR #41](https://github.com/Chain-Frost/python-runoff-routing/pull/41). S1 issue #3, S2 issue #4 and annotated code-7 native execution acceptance are outstanding.
