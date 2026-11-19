# PR coverage against real-project findings - 19 November 2026

The open PRs fix several specific implementation gaps, but do not resolve all groups in the [difference register](2026-11-19-difference-group-review.md). The reviewed `main` remains `9c2a87bafdf53f1b1eadc08cd7a1414387551176`, the numerical source used in the original audit. All five new implementation PRs remain draft and unmerged. The tested candidate is the cumulative stack at PR #205, not an installed release.

## Implemented coverage

| Finding | PR and reviewed head | Assessment |
| --- | --- | --- |
| Empty-padded BoM metadata rejected | [#201](https://github.com/Chain-Frost/python-runoff-routing/pull/201), `0f759212d39fcedd33944cf6941e8fe856db4b31` | Implements the narrow fix for #196. Accepts only empty trailing metadata cells, retains bytes/hash and matrix validation. Local original-source checks below confirm useful coverage. |
| Zero-length terminal natural reach | [#202](https://github.com/Chain-Frost/python-runoff-routing/pull/202), `55451b76912000647be95bdbc73cf0d3f4e11057` | Implements the narrow #199 terminal code-5 Q-copy case, diagnostics and guards against other zero-reach placements. The original authored native-probe CATG now parses locally. This is not general zero-length or storage support. |
| Hyd identifier zero padding | [#203](https://github.com/Chain-Frost/python-runoff-routing/pull/203), `23b60f0f8ca009335be95b57b95307f81e0bbe87`, with [ryan-tools #331](https://github.com/Chain-Frost/ryan-tools/pull/331), `0ab83025c28294ee7e9137375fa1b5a9261b94dc` | Upstream provides unique numeric-ordinal binding; downstream consumes it for reporting metrics and pins that exact dependency. Explicit rejection/qualification remains for ambiguous, unnamed or reordered scalar associations. This addresses #200, not missing historical physical labels. Upstream must be reviewed/merged before downstream integration. |
| Graphical background flags | [#204](https://github.com/Chain-Frost/python-runoff-routing/pull/204), `dbe2a98487703b0291c66011922b6106b4cd5894` | Admits `C T T` in the bounded 6.45 envelope without an asset payload. The eight actual project files blocked at this point use `C F F`, which remains rejected. Therefore it does not remove this observed project blocker. |
| Graphical structural validation | [#205](https://github.com/Chain-Frost/python-runoff-routing/pull/205), `d47a01b22708d51379d37870476ad68ce45d87f4` | Strengthens section ordering and complete coordinate-pair validation. Useful parser hardening, not admission of version 6.52, node annotations or multiple physical prints. |

The stack is #198  #201  #202  #203  #204  #205. These PRs target each other's branches, not main. A change at the tip includes earlier stack changes; merging or testing a child cannot be interpreted independently of its bases and pinned reader dependency.

## Fresh local admission checks

Windows Python 3.14.4, separate processes for the audited baseline and detached candidate checkout. These are parser/admission checks only, not fresh routing, rainfall reconstruction, wheel equivalence or native simulation acceptance. The earlier installed reader dependency suffices for these parser-only calls; this local check does not qualify the #203 reporting runtime.

| Check | Audited main | Cumulative PR #205 |
| --- | ---: | ---: |
| Original loose project CATGs parsed | 7 / 47 | 7 / 47 |
| Distinct available original IFD files referenced by first-four-set dependency inventory | 0 / 17 | 15 / 17 |
| Original authored terminal-zero CATG probe parsed | Rejected | Accepted |

All 17 checked IFD files originally stop at padded coordinate metadata. In the candidate, 15 parse directly without the former metadata workaround; two progress past padding and stop at `Duplicate BoM probability in export`. That is a separately exposed validation condition, not proof of another bug or a reason to drop a probability column silently. This 17-file check does not cover every rainfall source in all five sets or rerun generated storms.

The 40 remaining original CATG rejections are unchanged: eight background flag cases, three uncharacterised node records, one graphical physical-print restriction and 28 outside the bounded graphical-header support. Rejection categories reflect the first encountered parser gate; a fix at one gate may expose others. No original project file was modified.

## CI and evidence distinction

All five reviewed public PR heads have successful exact-head `windows-python-313` checks. The PR #205 Windows workflow additionally shows successful strict quality, fresh source CMD regression, diagnostic deviation, wheel build/import, CLI/full-report and fresh installed-wheel regression steps. These are hosted software/cached-reference checks, not new native executable runs or execution of private projects.

Upstream ryan-tools #331 has eight successful exact-head checks, including Policy, Hosted tests, Package, Ruff and both Python 3.13/3.14 public original-reader acceptance checks. This review inspected code/test diffs and current GitHub check records; it does not claim to have personally rerun those hosted suites.

## What these PRs do not fix

- Saved GUI PAR conditional interpretation and automatic recovery of full effective settings (#144). The resolved precision examples remain investigation results, not a newly implemented full PAR importer.
- Original `C F F` graphical flags, uncharacterised node records, 6.52 dialects and additional physical-print restrictions (#197).
- Storage, code 8, fractional controls 7.1/7.2 or other unqualified routing domains.
- Spatial rainfall, embedded filtering, combined preburst/uniform-depth semantics and multi-pluviograph/ISA/burst preparation (#8).
- Missing declared source files, ambiguous dependencies, absent hydrographs, changed historical labels, workbook/processed references or hidden historical settings.
- The small archive residuals retained in the native follow-up and additional group representative. No PR claims a qualified numerical correction for those cases, and tolerances/goldens remain unchanged.

PR #198 and private investigations PR #90 retain evidence rather than fix runtime behaviour. The separate Monte Carlo integration PR #151 is not a fix for these deterministic project-admission and rainfall-preparation groups. Older ryan-tools PR #118 concerns TUFLOW-rainfall-to-STM conversion timing, and #145 concerns calibration orchestration; neither implements the unsupported project-preparation features above. Previously merged rainfall and import work is already included in the tested main and therefore cannot be counted as a new fix for a failure observed on that same source.

This review does not merge, release, retarget or modify any implementation PR. Private admission receipts retain input hashes and detailed errors; public findings remain anonymised.

