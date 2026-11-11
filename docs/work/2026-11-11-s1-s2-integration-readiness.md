# S1/S2 integration readiness — Handoff C (blocked; preparatory slice)

**Status:** BLOCKED, not an integrated parser/solver. **Date:** 2026-11-11. **Owner:** Unassigned.

**Authoritative assignment:** https://github.com/Chain-Frost/runoff-routing-investigations/blob/docs/2026-11-11-s1-s2-agent-handoffs/docs/work/2026-11-11-s1-s2-integration-handoff.md

The investigations repository and its raw native corpus are private; the Python source repository is public. Do not transfer raw cases, per-event outputs, absolute private paths, native executables or hashes of private material into this branch.

## Exact current upstream revisions

| Owner | Draft PR / head | Base | Current capability | Gate |
| --- | --- | --- | --- | --- |
| S0 | [#12](https://github.com/Chain-Frost/python-runoff-routing/pull/12), `0d964e81c2f992c0097a8a4d7c16455abe327cd8` | main | Source evidence harness, offline reference comparison | Native acceptance still open; S0 must remain untouched |
| S1 | [#13](https://github.com/Chain-Frost/python-runoff-routing/pull/13), `06081dd645eebecb6ec273259e129adaa80b960f` | S0 #12, parent `07a54f931c441f3363b572ecc2a1dd0df3a79464` | CMD V2 single-burst .par `ParameterModel`, source line/hash diagnostics, partial .out inspection | **No RunModel, .catg/.stm reader, versioned JSON or canonical writers**; unreviewed draft |
| S2 | [#14](https://github.com/Chain-Frost/python-runoff-routing/pull/14), `78d94926172c40ff11ccd4a3bc4c8b028cf5b689` | main | `calculate_storm`, local `Catchment/Control/Storm/Losses`, `legacy_inputs.py` narrow fixture adapter and offline comparator | No agreed S1 input mapping or accepted RORB numerical parity; draft |
| Preparation | This branch | main `4498f7f466eb34a35d5eecf35844aa5bd4d7dcf7` | Pure, independently testable Decimal-to-float guard and integration checklist | Blocked before real adapter |

Both S1 and S2 have **no submitted reviews** at this snapshot. No upstream branches were rebased, merged, cherry-picked, modified or released by this work.

## Required upstream handoffs

1. **S1 owner** must publish and review a source-independent typed `RunModel` with source identities, ordered controls, subareas, ISA/pluviograph/depth mapping and explicit print-site identities. Implement characterised S1 .catg/.stm grammars, versioned JSON and canonical .par/.catg/.stm serializers with parse-after-write semantic round trips. Original-byte preservation must be separate from canonical export. Unsupported/non-representable features must reject.
2. **S2 owner** must document admitted solver features and unresolved numerical hypotheses against its current head. Current assumptions include at-end-of-bin rainfall inflow, initial-loss/continuing-loss bin crossing and nonlinear stopping. Peak proximity does not accept full-ordinate parity.
3. **Integrator**, only after the S1 contract is agreed, must pin current S1/S2 heads, map S1 typed records to S2 types through one adapter and remove duplicated fixture grammars only after tests establish migration equivalence. Do **not** create another S1-like parser or let S2 read raw input text directly.

## Future adapter contract (not an API implemented here)

- Validate *parse*, *numerical execution* and *native parity* as independent gates. Input recognised by S1 does not imply it can be computed by S2. Fail closed before calculation for unknown control codes, storage, FIT, imperviousness, external/lateral inflows, GUI .par, multiple bursts or other unsupported numerical features.
- Preserve original RORB control order, source/area/depth/ISA mapping and subarea identities. S2 supports control 1/3/4/5/7; the imported 0 is a terminator, not a routed operation. Do not silently reorder, merge ISAs or infer hydrograph-to-print-location associations from positional `HydNNN` labels. No invented print-site identities.
- Admit only a one-ISA, one-burst, fully pervious, natural-reach, explicit DESIGN storm subset, and S1 CMD loss model **1** if it is proven semantically IL/CL. S1 loss model 2 is ambiguous and must reject for computation. S2 currently has one `kc/m`, a single `Losses` object and a uniform storm pattern.
- S1 values are `Decimal`. The new pure `decimal_to_solver_float(value, field=..., units=..., constraint=...)` primitive rejects nonfinite values, binary64 overflow, underflow-to-zero and out-of-domain values. It performs no unit conversion, never handles integer codes/IDs, and is **not** a `RunModel` adapter. The future adapter must supply each field's correct source units and error-to-source diagnostic mapping. Expected units include mm, mm/h, km, km2, hours and dimensionless kc/m; outputs are m3/s. IEEE-754 rounding is not proof of native parity.
- A future `run_model(model)` must be side-effect-free, return typed results and diagnostics, and include trustworthy print-location identities only where established. Preserve the S1 raw input hashes and line metadata, and native original time/increment tokens without shifting any axis. Use a thin Windows-friendly wrapper with exclusive no-clobber report/CSV output, not a new parser or generic plugin system.
- Distinguish `invalid_source`, `parsed`, `unsupported_execution`, `calculated_unvalidated`, `compared_unaccepted` and `incomplete_evidence`. Neither a skipped private test nor a missing corpus constitutes a green parity result.

## Capability matrix at this revision

| Dialect / feature | S1 parse | S1 canonical write | S2 isolated calculation | Integrated end-to-end | Parity accepted |
| --- | --- | --- | --- | --- | --- |
| CMD V2 single-burst .par | Limited typed inspection | No | Manual parameter setup only | No | No |
| GUI .par / multi-burst CMD | No | No | No | No | No |
| RORB_GE .catg, codes 1/3/4/5/7 | No | No | Fixture-only S2 parser | No | No |
| Explicit DESIGN .stm, fully pervious, one ISA | No | No | Fixture-only S2 parser | No | No |
| Other .cat/.dat/.stm dialects | No | No | No | No | No |
| Versioned JSON RunModel | No | No | No | No | No |
| Single .out HydNNN table | Partial only, print identities unverified | N/A | Separate cached comparator | No trusted identity join | No |
| Storage, FIT, GUI imperviousness, code 2/6, multiple ISAs | No runnable typed model | No | Unsupported/reject | No | No |

**No versioned JSON example is published as runnable** because S1 has not defined its format. Generating a speculative config would undermine the authoritative type contract.

## Integration acceptance plan (after readiness gate)

1. Re-read upstream PR heads; review S1 `RunModel` and canonical writer APIs. Assert `read → typed model → JSON → typed model → canonical .par/.catg/.stm → read` semantic equality for characterised fixtures. Reject unrepresentable features rather than dropping them.
2. Implement the single typed adapter to S2 `Catchment/Control/Storm/Losses`, preserve command and ISA order, invoke `calculate_storm` and return typed print identities and structured source diagnostics. Test fail-closed unsupported constructs **before** a solver call.
3. Exercise supported `read → calculate → offline compare` via S2's comparator, retaining raw CMD tokens; run private corpus strictly outside this repository and record unsupported/incomplete separately. Do not claim tolerance acceptance from near-equal peaks.
4. Run focused synthetic, parser/writer/source, offline and installed-wheel tests separately. Target Windows/Python **3.14**, pinned Ruff **0.16.6**, strict Pyright and installed-wheel import outside checkout. Do not execute RORB or start native capture from the integration test suite.
5. Produce reviewed API example and supported versioned JSON sample **after** S1 settles the format. Keep issues [#3](https://github.com/Chain-Frost/python-runoff-routing/issues/3) and [#4](https://github.com/Chain-Frost/python-runoff-routing/issues/4) open until their separate acceptance gates pass.

## Dependency and conflict/merge plan

This preparatory branch is based directly on **main**, not on any unmerged implementation. It does not contain S1 or S2 source and must not be presented as the final integration PR.

Recommended review/merge order, **subject to explicit separate approval**: S0 #12 → stacked S1 #13 → independently based S2 #14 (review and resolve conflicts) → completed integration PR. Alternatively agree a pinned integration stack with reviewed parents. Never perform a blind rebase while an upstream branch is being edited and never force-push. After the parents are agreed, re-evaluate this preparation against the combined tree, then retire/mark `legacy_inputs.py` a compatibility shim only after migration tests; do not change S0 capture machinery or workflows.

## Evidence for this preparatory PR

- **PASS, supplementary only:** 19 synthetic unit tests on Linux/CPython 3.13.5; compilation succeeded. No native executables or private data accessed.
- **NOT RUN:** Ruff 0.16.6, strict Pyright, Windows/Python 3.14, whole-repository tests, installed wheel, parser/serializer round trips (S1 contract absent), offline private corpus and numeric parity.
- **Next action:** Wait for an agreed S1 typed-model/serializer revision. Re-read all three PR heads and then implement the actual end-to-end adapter. This preparatory PR must remain draft and is not accepted Handoff C completion.
