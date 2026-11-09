# Source register

Reviewed for planning on 2026-11-09. Source-derived statements are reference specifications or probe targets; implementation choices and acceptance policies are project decisions.

| ID | Source | Relevant scope and limitations |
| --- | --- | --- |
| R1 | User-supplied rorb_manual.pdf, RORB Version 6 User Manual, January 2010 | Sections 2.2/2.4 routing; 3.3/3.4 runoff/losses; chapter 5 file data; 6.1/6.10 ordering; chapter 8 Monte Carlo. Printed page labels differ from PDF indices. Historical, not a complete 6.52 specification. |
| R2 | User-supplied RORB_CMD-documentation_V2.pdf, one page | CMD parameter file, column-11 values, output/log behaviour; identifies a 6.31 base. Does not identify the actual supplied executable hash/version. |
| R3 | User-supplied RORBwin_v652_release-notes.pdf | Sections 1.4, 1.6-1.8: naming/CSV, ARR, MC extraction, impervious modes and fixes. Changes are cumulative from 6.30; do not assume every feature exists in CMD. |
| R4 | [HARC: direct/indirect impervious fractions in CMD](https://harc.com.au/forums/topic/directly-indirectly-connected-impervious-fractions-in-rorb-cmd/) and [HARC clarification](https://harc.com.au/forums/topic/apply-direct-and-indirect-impervious-fractions/) | Historical custodian statements distinguishing GUI/CMD surface-loss support; confirm against the selected binary. |
| R5 | User-supplied RORB_CMD_example.par, RORB_CMD.exe, RORBwin.exe and SampleData.zip | Candidate reference assets. The example loss-model/value combination needs probing. Binary fingerprints, archive inventory and native execution remain S0 work; no claim that they were executed in this bootstrap. |
| R6 | [HARC software page](https://harc.com.au/software/rorb/) | Custodian currently lists 6.52 and licensing/registration; a download version does not replace binary fingerprints. |
| G1 | [GitHub Actions billing](https://docs.github.com/en/actions/concepts/billing-and-usage) | Private usage has a plan allowance and additional billing; no account-specific allowance was inspected. |
| G2 | [GitHub repository Actions settings](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/enabling-features-for-your-repository/managing-github-actions-settings-for-a-repository) | Repository-level disable switch is distinct from having no workflow files. |
| T1 | Chain-Frost/ryan-tools AGENTS.md, docs/DEVELOPMENT_GUIDE.md and docs/WORK_TRACKING.md, inspected 2026-11-09 | Inspiration for local validation, Windows acceptance, path safety, batch pushes and handoffs; not wholesale adoption of that repository's architecture. |

Do not commit third-party binaries/manuals or assume sample redistribution rights. Keep bibliography/provenance and independently authored implementation separate. Review applicable permissions before copying source assets or publishing. This register is not legal advice or an assertion of endorsement.
