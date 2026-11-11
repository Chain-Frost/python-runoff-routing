# RORB GUI/CMD behavior and legacy interoperability audit

| Field | Value |
| --- | --- |
| Status | Planned |
| Owner | Unassigned |
| Created / updated | 2026-11-11 |
| Next review | 2026-11-25 |
| Baseline | main at 4498f7f466eb34a35d5eecf35844aa5bd4d7dcf7 |
| Delivery | New independent audit branch/PR (none implementing native audit yet) |
| Tracking | [Issue #16](https://github.com/Chain-Frost/python-runoff-routing/issues/16) |

## Outcome and boundaries

Characterise historical GUI/CMD/file/solver behavior, including latent defects. Specify user warnings and exact legacy-versus-corrected semantics. Establish robust CatchmentSIM/RORB GE-compatible source preservation and round-trip requirements. The investigation is **separate** from ongoing S0 [PR #12](https://github.com/Chain-Frost/python-runoff-routing/pull/12), S1 [PR #13](https://github.com/Chain-Frost/python-runoff-routing/pull/13), S2 [PR #14](https://github.com/Chain-Frost/python-runoff-routing/pull/14), and manual [PR #15](https://github.com/Chain-Frost/python-runoff-routing/pull/15).

No executable/disassembly/native traces have been inspected or generated as part of this planning work. The existing source manual's historical licence, the conditional Australian statutory interoperability exception and this workpack's scope do not preapprove decompilation or copying proprietary implementation details.

## Immediate next action

Assign a local Windows agent with the installed RORBwin and RORB_CMD builds. Give it [the detailed handoff](2026-11-11-rorb-forensics-handoff.md) and [warning/compatibility policy](../BEHAVIOUR_AND_WARNINGS.md). Start by identifying actual hashes/builds, verifying isolated native output paths, and tracing two GUI save/reload input sequences. Use prior validated S0 capture machinery; do not create a second runner.

## Acceptance criteria

Deliver reproducible version-qualified findings (including disproved hypotheses), raw-state evidence, a read-only runtime I/O trace, a GUI file-format preservation/round-trip assessment and a stable machine-readable warning register proposal. Identify unresolved questions and review boundaries. Run Windows/Python 3.14 quality checks on any newly written code; do not close related implementation stages from audit-only evidence.

## Validation and delivery

Planning documents only. External evidence reviewed: user-supplied RORB manual/CMD guide and v6.52 release notes, official CatchmentSIM export help, and official Australian Copyright Act text. Repository contents and open S0/S1/S2 PR status checked on 2026-11-11.

NOT RUN: native RORB, GUI input probes, ProcMon, Ruff, Pyright, pytest, package build. No binary, private input, code extracted from native program or numerical fixtures are committed. No merge, release or workflow changes.

## Progress

### 2026-11-11

Opened audit issue and wrote the first-tranche local-agent contract and warnings/source-interoperability specification. All actual native findings are pending the local agent's evidence capture. The target repository currently reports public visibility, so evidence must remain local until permissions and privacy are reviewed.
