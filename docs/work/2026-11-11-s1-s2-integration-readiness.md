# S1/S2 integration readiness and dependency register

**Snapshot date:** 2026-11-11. **Status:** S0/S1 implementation merged; S1 canonical native acceptance, S2 numerical parity and integrated private/native acceptance **open**. This is a *status and gate register*, not proof that either routing engine profile is matched or that a release is authorised. **Owner:** Unassigned; independent branch authors retain control of outstanding implementation branches. **Review:** On the next bounded validation session.

The objective is to implement RORB procedures in Python, using pinned RORB executables as the computational source of truth. Confirm effective inputs and preserve separate RORB_CMD and RORBwin version profiles. This project is publicly visible; private source data and evidence stay outside it.

## Verified PR map at this snapshot

| Work | PR / source head | Disposition | Independent acceptance |
| --- | --- | --- | --- |
| Planning and owner reference policy | #11, #24 | Merged | Documentation/scaffold only |
| Reference capture S0 | [#12](https://github.com/Chain-Frost/python-runoff-routing/pull/12), merged `f9f51ad` | Merged implementation | [S0 #2](https://github.com/Chain-Frost/python-runoff-routing/issues/2) open; CMD 6.44 and limited GUI 6.52 evidence |
| CMD .par/.out inspection S1 | [#13](https://github.com/Chain-Frost/python-runoff-routing/pull/13), merged `17d134b` | Merged implementation | S1 #3 open; subset inspector only |
| Typed model/canonical S1 | [#19](https://github.com/Chain-Frost/python-runoff-routing/pull/19), merged `be8832e` | Merged implementation | S1 #3 open; native canonical acceptance not proven |
| Native code-7 line fix | [#25](https://github.com/Chain-Frost/python-runoff-routing/pull/25), merged `3575fb5` | Merged implementation | Corrected canonical files not rerun through CMD |
| Worked-example inventory and warnings | [#15](https://github.com/Chain-Frost/python-runoff-routing/pull/15), [#17](https://github.com/Chain-Frost/python-runoff-routing/pull/17) | Merged documentation | No numerical acceptance |
| S2 single-storm kernel | [#14](https://github.com/Chain-Frost/python-runoff-routing/pull/14), `78d9492` | **Draft / unmerged** | [S2 #4](https://github.com/Chain-Frost/python-runoff-routing/issues/4) parity unsatisfied |
| Printed-ordinate and linear-balance audit | [#18](https://github.com/Chain-Frost/python-runoff-routing/pull/18), `53021ff`, stacked on #14 | **Draft / unmerged** | Strict native model comparisons unresolved |
| Selected S2 quality/transport repairs | [#21](https://github.com/Chain-Frost/python-runoff-routing/pull/21), `947a9aa`, stacked on #18 | **Draft / unmerged** | Revalidate two added tests; 36 private computed cases exceed precision budget |
| Duplicate transport repair | [#22](https://github.com/Chain-Frost/python-runoff-routing/pull/22) | **Closed, superseded by #21** | Useful transport tests retained on #21 |
| Typed S1+S2 integration | [#23](https://github.com/Chain-Frost/python-runoff-routing/pull/23), `4450475` at snapshot | **Draft / unmerged** | Needs selected #21 and #25 reconciled, updated Windows and private native checks |
| This readiness register | [#20](https://github.com/Chain-Frost/python-runoff-routing/pull/20) | Documentation refresh | Not an integration acceptance |

The heads above are a dated record, not a lease: fetch remote heads again before any edit or merge. No automated scheduling is implied.

## Integration contract and reuse

- Reuse the merged S1 `RunModel`, `ParameterSet`, `CatchmentModel`, `StormModel`, `rorb_codec.to_s2_payload`, source-aware `.par/.catg/.stm` parsers, canonical writers and schema-1 JSON. Preserve computational control order, area/rainfall/ISA identities, original bytes, source spans and diagnostic print IDs.
- Reuse S2's pure `calculate_storm`, reach-storage kernel and frozen `assess_printed_parity`/linear-balance audit. Keep the solver and file/capture adapters separate; no generic parallel parser or second RORB process runner.
- The #23 `integration.run_model` bridge already exists with typed results, no-clobber CSV/JSON, explicit `parity_status=unassessed`, stable S1 print IDs and a checked Decimal-to-float boundary. That work includes an S2 #18 integration merge, **not** the newer selected #21 strict-quality/transport repairs or the native code-7 #25 update. The active #23 author should reconcile these without overwriting concurrent work.
- Reject unsupported or uncharacterised features **before** numerical computation: GUI .par, FIT, multiple ISA/bursts, storage, imperviousness, uncharacterised controls, other rainfall/loss semantics or speculative print-site mappings. The supported minimum is a restricted single-burst, one-ISA, pervious DESIGN profile. Parsing success, mathematical execution and native parity are different statuses.
- Native CMD 6.44 consumed the old canonical code-7 print-location line incorrectly. #25 fixes the Python physical-record layout, but a new **native replay** against the corrected complete .catg/.stm/.par is required. Original-byte preservation and a Python round trip alone do not prove RORB accepts the exported file.

## Evidence and numerical gate

- **S1:** merged-head Windows/Python 3.14.10 quality checks passed on #13 (64 tests), #19 (98 tests) and #25 (101 tests), with Ruff 0.16.6, strict Pyright, wheel builds and isolated installed-wheel import. The quality workflow is an already owner-approved single Windows lane, not permission to add more automation.
- **S0:** fingerprinted CMD 6.44 and user-operated GUI 6.52 baseline had 301 exactly matching outlet **values in row order** but different printed increment/time labels. This is a single baseline-specific reporting observation, not general cross-engine parity or a validated universal time shift.
- **S2 #21:** a Windows/Python 3.14.6 report from earlier head `17102b8` records Ruff, Pyright, 104 synthetic tests and private installed-wheel replay. At amended `947a9aa` two tests from #22 are added; the previous quality result is **not** a check of this newer head. The private campaign records 941 indexed files, four additional linear checks and 65 outcomes: 36 compared, 25 unreviewed, 3 expected failures and 1 incomplete reference. All **36 computed whole-catchment cases exceed the frozen printed-precision budget**. This is evidence of a compatibility blocker, not evidence for loosening the tolerance.
- Six manufactured nonlinear kernel controls passed, but pinned native endpoint/stopping and source time/phase conventions remain unresolved. The private raw corpus is not copied into this public repo. The current implementation is *executable but unvalidated* for RORB parity.

## Outstanding graph and concrete gates

```text
main: #11, #24, #15, #17, #12, #13, #19, #25  [merged code/docs]
  |
  +-- #14 S2 kernel [draft] -- #18 diagnostics [draft] -- #21 selected quality [draft]
  |                                                 `-- #22 closed/superseded
  |
  +-- #23 S1+S2 integration [draft; uses S1 + #18, pending #21/#25 reconciliation]

#20: this documentation-only status register; not solver acceptance
```

1. **S0 #2:** audit the profile-specific time labels, effective GUI settings and reference provenance for additional permission-cleared cases, retaining raw report/CSV identities. Do not close on the single 301-row match.
2. **S1 #3:** re-execute the repaired canonical code-7 output with actual fingerprinted CMD 6.44 and verify complete file acceptance, effective input echo and source-folder write isolation. Extend only approved dialect fixtures.
3. **S2 #4:** characterise the native nonlinear step/Regula-Falsi stopping and source rainfall phase with bounded, preapproved native probes; compare every ordinate under the *existing* precision budget. Keep #14/#18/#21 draft until their acceptance criteria and exact-head Windows/wheel gates are met.
4. **Integration #23:** coordinate with its active branch owner; merge the chosen #21 behavior and #25 code-7 fixes without duplicating S1 grammar or S2 kernel; run exact-head Windows/Python 3.14, source and isolated-wheel tests plus authorized private corpus comparison. If those gates do not establish native parity, retain the draft and `parity_status=unassessed`.
5. **Operational boundary:** no force-push, release, PyPI upload, visibility change, new workflows, or automatic closure of numerical issues. This register does not authorise a native simulation or a private data upload.

## Change and validation history

Updated 2026-11-11 during the owner-authorised PR cleanup to replace obsolete pre-integration statements and superseded SHA/status claims. Documentation-only changes require repository Markdown link/hygiene checks, not numerical simulations. The source/installed-wheel and native checks quoted above belong to their named source revisions, **not** automatically to this document or an unreviewed combined S2/integration head.
