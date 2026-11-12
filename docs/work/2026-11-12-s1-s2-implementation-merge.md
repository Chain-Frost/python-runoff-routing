# S1/S2 Python-only implementation merge — 2026-11-12

**Status:** implemented on public `main`; **S1/S2 numerical/native compatibility is not accepted**. Owner authorised an implementation-only merge and retention of separate stage gates.

## Revisions and merge

- Reviewed public [integration PR #23](https://github.com/Chain-Frost/python-runoff-routing/pull/23) at `55aac4f51db1f994239b3c052598a1cc09787599` on top of public main `b78cf56501507fbce086fbf2bf71b940fc6cbb4e`.
- [Windows quality run 43055005783](https://github.com/Chain-Frost/python-runoff-routing/actions/runs/43055005783) passed at that exact head: Windows Python 3.14.10, repository hygiene (84 files, zero errors), Ruff 0.16.6 lint/format, strict Pyright (zero errors/warnings), **247 public synthetic tests**, wheel build and external installed import.
- Merge-commit method was rejected because the repository permits only squash merges. **Implementation squash merge:** `a558c0ce9679949cf15ef5be024d8f4b0a7637f6`.
- Optional inline code-7 graphical annotation and the separate physical native print-location record remain distinct; S1 source bytes/encodings and typed identities are preserved. Python-only S2 solver and the original offline reference comparison are implemented, with unsupported features explicitly rejected.
- Repository auto-deletes merged head branches. To protect the live [nonlinear printed-balance child PR #41](https://github.com/Chain-Frost/python-runoff-routing/pull/41), it was retargeted to `main` first. A non-forced two-parent ancestry merge `df6eb34e638f32d01c0ee2787005544e70e81b09` references the integrated main as its second parent and retains the child source tree **byte-identically**. The resulting draft PR #41 diff contains only its unique three-file diagnostic/test addition; it is not merged or numerically accepted.

## Separate retained private offline evidence

A prior independently reported Windows installed-source-wheel replay used the complete **65-case private catalogue** and four supplemental prescribed-inflow linear profiles. It verified the **1,026-entry index** and retained source bytes without executing RORB or transferring private fixtures to this public repository.

| Class | Count | Interpretation |
| --- | ---: | --- |
| Limited linear profiles | 4 | Passed fixed experimental budgets |
| CMD catchment profiles computed | 36 | **All outside frozen full-ordinate printing budget** |
| Captured-unreviewed | 25 | Not promoted to numerical comparisons |
| Native expected-failure captures | 3 | Rejected with explicit diagnostics |
| Incomplete reference | 1 | Rejected; not treated as a zero-flow case |

All **16,836 integrated Python predicted discharge ordinates** matched the retained Python comparison. The common numerical CSV content did not change; three expected-failure diagnostic messages reflect S1's authoritative parser. Recorded CMD and RORBwin print-time labels remain separate. Neither numerical compatibility nor an historical root/whole-series algorithm is established by these tests.

## Acceptance and next work

**Open:** [S1 issue #3](https://github.com/Chain-Frost/python-runoff-routing/issues/3), [S2 issue #4](https://github.com/Chain-Frost/python-runoff-routing/issues/4), GUI/nonlinear legacy equivalence, annotated code-7 native acceptance, broad grammar/ISA/loss modes and other stage-specific gates. Any fitted tolerance or altered solver must undergo separate review; original pinned native goldens remain unchanged.

No native RORB launch, package publication, release, visibility change, force-push, golden replacement or private-data transfer was part of this merge. Independent source PRs #21/#27/#39/#40 and draft child #41 are not automatically accepted or merged; review their unique deltas before consolidation.
