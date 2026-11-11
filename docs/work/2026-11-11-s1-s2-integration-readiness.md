# S1/S2 Handoff C integration — readiness and dependency contract

**2026-11-11 status: BLOCKED.** This is independent documentation and a conflict-free integration plan, **not** a working parser-to-solver bridge. The Handoff C start condition requires a *reviewed and stable* S1 typed API and canonical serializers. Those are now drafted in PR #19, but have **not** passed quality and review gates.

**Authoritative assignment:** https://github.com/Chain-Frost/runoff-routing-investigations/blob/docs/2026-11-11-s1-s2-agent-handoffs/docs/work/2026-11-11-s1-s2-integration-handoff.md

The investigations repo and native corpus are private while this Python repository is public. This preparation records no raw cases, machine paths, private artefacts or numerical case-level results.

## Current revision/owner map

| Role | Open PR and exact head | Base | State relevant to integration |
| --- | --- | --- | --- |
| S0 provenance | [#12](https://github.com/Chain-Frost/python-runoff-routing/pull/12): 0d964e81c2f992c0097a8a4d7c16455abe327cd8 | main | Draft; native acceptance separately open; do not touch |
| S1 inspection parent | [#13](https://github.com/Chain-Frost/python-runoff-routing/pull/13): 06081dd645eebecb6ec273259e129adaa80b960f | Stacked on S0 #12, parent 07a54f931c441f3363b572ecc2a1dd0df3a79464 | CMD single-burst .par ParameterModel and partial .out, no catchment/storm domain |
| **S1 bidirectional handoff A** | **[#19](https://github.com/Chain-Frost/python-runoff-routing/pull/19): 6403e8c6845bf4512720bba85e58f00fe6b720ec** | Stacked on S1 #13 | **RunModel, typed parameter/catchment/storm models, source-aware .catg/.stm/.par parsers, canonical serializers, JSON schema 1 and preliminary S2Payload exist. Draft, zero submitted reviews. Windows quality failed: 25 strict Pyright errors; wheel/build steps skipped.** |
| S2 computation parent | [#14](https://github.com/Chain-Frost/python-runoff-routing/pull/14): 78d94926172c40ff11ccd4a3bc4c8b028cf5b689 | main | Independent pure single-storm kernel, temporary Catchment/Control/Storm/Losses, legacy_inputs fixture readers, private offline comparison; unaccepted numeric equivalence |
| **S2 handoff B audit** | **[#18](https://github.com/Chain-Frost/python-runoff-routing/pull/18): 53021ff23ccb4ee46ddf9a528775b14220d7051e** | Stacked on S2 #14 | Printed-precision and linear balance diagnostics, 13 supplementary synthetic checks. Draft, no review; target quality and private comparison not accepted |
| This document | feat/s1-s2-integration-readiness, started at main 4498f7f466eb34a35d5eecf35844aa5bd4d7dcf7 | main | Readiness plan only, no duplicate model/grammar/numerical code |

**Newer PRs #19 and #18 are separate from parent PRs #13 and #14.** Handoff C may proceed after upstream agreement but must not assume that a draft branch with failing CI is a reviewed contract. Do not close issues #3 or #4.

## Actual S1 handoff A API (review required)

- `rorb_model.ParameterSet`, `CatchmentModel`, `StormModel`, `RunModel` are immutable source-independent domain objects. `RunModel` holds parameters/catchment/storm and validates ISA, burst and ordered subarea IDs.
- `rorb_codec.parse_cmd_par`, `parse_catg`, `parse_design_stm` produce source-aware `ParsedDocument` values; `serialize_cmd_par`, `serialize_catg`, `serialize_design_stm` provide supported-format canonical bytes. `original_bytes` is separate source-preservation mode; `write_new` is exclusive/no-clobber.
- `rorb_model.to_json/from_json` provide schema-1 interchange with Decimal strings. `docs/RORB_BIDIRECTIONAL.md` already provides a draft API example. A new speculative schema must **not** be created by the integration owner.
- `rorb_codec.to_s2_payload(RunModel)` already creates a restricted `S2Payload` with control code/reach length pairs, areas, storm values, losses, `kc`, and `m`. **Reuse or improve this existing single conversion boundary** after owner review; do not create another generic Decimal converter or duplicate .catg/.stm grammars.
- The current `S2Payload` omits print-site/source identifiers and source provenance; these must be retained in an integration result/diagnostic object without inventing associations. The current `_as_float` checks finite output, but not positive-Decimal underflow-to-zero and not field/expected unit context. These are review questions for S1, not permission to bypass its boundary. In particular, S1 `Reach.length_km` is positive Decimal while S2 accepts zero-length routing, so policy for representability and zero-length semantics needs explicit agreement.
- A canonical .catg writer using an empty graphical scaffold is **not** proof that native RORB accepts it. Preserve original source bytes/graphical information separately. Original print labels may not equal retained `HydNNN` output columns.

## Numerical adapter after upstream contract approval

Use S1 `RunModel` as the single authority. Construct S2 `Catchment(tuple(Control(code,length) ...), areas)`, `Storm(timestep,calculation_increments,percentages,depths)`, `Losses(initial,continuing)` and `calculate_storm(...,kc,m)` only after all execution capabilities are checked.

1. Preserve original computational control order exactly; do not treat trailing control 0 as a routed operation. Preserve subarea/area/depth/ISA identifiers; do not reorder by geometry, name or drawing order.
2. Initially accept only one ISA, one explicit DESIGN burst, loss flag 1 IL/CL, lumped kc/m, fully pervious source areas, uniform temporal percentages, natural reaches and S2 controls 1/3/4/5/7. Reject GUI .par, loss flag 2, multiple ISAs or bursts, FIT, external/lateral inflows, special storage, impervious fractions, unsupported controls or uncharacterised storms **before** any calculation.
3. Keep source decoding, parser diagnostics and format-specific token handling out of the numerical solver. Reject invalid/unsupported inputs differently from valid-but-unexecuted or executed-but-unvalidated inputs. Loss crossing, at-end-of-bin source phase, legacy nonlinear stopping, time labels and native volume conventions are unresolved S2 scientific hypotheses.
4. Export a pure `run_model(model)` with typed results and source-aware, machine-readable diagnostics; associate printed locations only through explicit stable S1 identities. No native process, file writes, time-axis adjustment or implicit `HydNNN` index matching.
5. Keep a thin Windows-friendly wrapper optional. Output JSON/report/CSV with exclusive creation by default. Reuse the S2 offline comparator only after native print-site and phase associations are established. Preserve raw increment and time strings.

## Capability matrix (unmerged heads; no Handoff C integration)

| Dialect / feature | S1 #19 parse | S1 #19 canonical serialize | S2 #14 isolated calculation | Integrated execute | Native numerical parity |
| --- | --- | --- | --- | --- | --- |
| CMD V2 .par single-burst subset | Draft yes | Draft yes | Manual setup only | **No** | No |
| RORB_GE 002 .catg natural/1,3,4,5,7 | Draft yes | Draft yes, empty graphic scaffold | Narrow legacy fixture parser | **No** | No |
| Explicit DESIGN .stm, one ISA/one burst | Draft yes | Draft yes | Narrow legacy fixture parser | **No** | No |
| Versioned JSON RunModel schema 1 | Draft yes | JSON draft yes | Separate S2 domain | **No** | No |
| Single cached .out HydNNN table | Partial read-only S1 inspector | Not applicable | S2 cached comparator | Print mapping unverified | No |
| GUI .par, .cat/.dat, FIT, unknown controls, storage, impervious, multi-burst | Unsupported / uncharacterised | Unsupported | Unsupported | No | No |

`Draft yes` means implementation exists at a particular unmerged revision, **not** that public CI/native equivalence or the shared API has been accepted.

## Integration validation plan

- Pin reviewed source heads before opening a *real* integration stack. Exercise `read → RunModel → to_json → from_json → canonical .par/.catg/.stm write → read` and semantic identity equality; preserve original bytes in the separate source-preservation path. Reject unrepresentable canonical features.
- Construct S2 from `to_s2_payload`; compare numeric results against equivalent direct S2 fixtures, verify control/area/ISA mapping and explicit print IDs, and assert unsupported features reject **before** `calculate_storm`.
- Retire or mark `legacy_inputs.py` a compatibility shim only after tests prove migration, not by moving the old grammar under a new module name.
- Run parser/writer/source and synthetic solver checks separately. Run the private offline corpus only from an approved **external** directory, reporting unsupported/incomplete cases separately from compared-but-unaccepted results, without writing data to the public source tree.
- Required target: Windows/Python 3.14, pinned Ruff 0.16.6, strict Pyright, full repository suite, wheel build and import outside checkout. Do not start RORB. Do not infer parity from peaks, an absent corpus or a skipped wheel check.

## Staged conflict and merge plan

No upstream branch is modified by this main-based readiness PR. **S0 #12 → stacked S1 #13 → stacked S1 #19 → S2 #14 → S2 #18 → final integration** is the provisional conceptual order, each step requiring its own owner approval, current-head review and deliberate conflict resolution. The S2 stack is independent from main; do not blind-rebase it during another agent's work. Integration may instead use an expressly agreed stack of pinned parents, with one documented dependency map. Do not force updates, merge, release, change workflows or close #3/#4 automatically.

## Current readiness validation and exact blocker

- **S1 #19 Windows quality run [43030412072](https://github.com/Chain-Frost/python-runoff-routing/actions/runs/43030412072): FAILED at head 6403e8c6845bf4512720bba85e58f00fe6b720ec.** Ruff lint/format passed; strict Pyright failed with **25 errors** in `check_private_parser_corpus.py`, `rorb_inspect.py`, `rorb_model.py` and `test_rorb_roundtrip.py`. Wheel build/import were skipped. No review submissions recorded.
- **S2 #18:** reported 13 supplementary synthetic diagnostic tests; Windows/Python 3.14, full private corpus and native parity remain unaccepted.
- **This document-only readiness branch:** no application code or tests changed, and no source test run is claimed. It cannot be treated as Handoff C completion.

**Next action:** S1 #19 owner resolves 25 strict typing findings, records full Windows/wheel checks and obtains an agreed reviewed typed model/serializer interface. Re-read fresh #19/#18 heads, then create a pinned stack and implement the single `run_model` adapter with tests.