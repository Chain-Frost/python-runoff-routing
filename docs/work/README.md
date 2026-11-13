# Work register

- [S6 RORBwin local preflight](2026-11-13-s6-rorbwin-local-preflight.md): R0 native rainfall matched
  using an editor-saved 6.52 model; zero-loss excess ordinates matched, CSV timing open; R1–R7 **NOT RUN**.

| Work front | Status | Owner | Updated | Next review | Next action |
| --- | --- | --- | --- | --- | --- |
| [S6 local RORBwin 6.52 rainfall validation](2026-11-12-s6-rorbwin-local-validation-handoff.md) | Handoff prepared; no native comparison run | Unassigned (local Windows agent) | 2026-11-12 | On native evidence review | Fingerprint RORBwin and compare synthetic 100 km² rainfall, ARF, preburst and IL/CL vectors before routing; private evidence only. |
| [S6-P3 legacy preburst/loss policy](2026-11-12-s6-p3-preburst-loss.md) | Draft; original storm IL versus burst IL and explicit source ratio | Rainfall agent | 2026-11-12 | Windows quality and native comparison | Verify RORBwin v6.52 GSAM/Jordan defaults, source ratios, time-grid and IL/CL numerics before acceptance. |
| [S6-P2 temporal-pattern selection + ARF](2026-11-12-s6-p2-selection-arf.md) | Draft; source-only ARR2019 methods; depends on #48 | Rainfall agent | 2026-11-12 | Windows quality and method review | Confirm actual catchment area/ARF zone, validate event selection and RORBwin rainfall inputs; no stage acceptance. |
| [S6-P1 BoM IFD + TP intake](2026-11-12-s6-bom-tp-gross.md) | Draft, dependent on S6-P0 PR #38 | Independent rainfall agent | 2026-11-12 | Windows quality review | Verify offline BoM and TP input, gross rainfall, no hydrological parity claim. |
| [S6-P1 BoM IFD and ARR TP intake](2026-11-12-s6-bom-tp-gross.md) | Draft; real FLTwest ZIP replay passed structural validation | Rainfall agent | 2026-11-12 | After final-head CI and method review | Preserve missing areal AEP; verify 2026 variants and design-event selection before hydraulic acceptance (PR #48). |
| [S6-P0 ARR Data Hub intake](2026-11-11-s6-p0-implementation.md) | Draft source-only implementation | Independent rainfall agent | 2026-11-11 | After implementation CI review | Validate 2026v1 IFD JSON/TXT and provenance; do not infer ARR method acceptance [#33](https://github.com/Chain-Frost/python-runoff-routing/issues/33). |
| [Computational reference guidance](2026-11-11-computational-reference-guidance.md) | Owner wording applied | Local agent | 2026-11-11 | Next procedure investigation | Implement Python procedures and verify against pinned RORB computations. |
| [S0 native validation](2026-11-11-s0-native.md) | Partial native evidence; stage open | Unassigned | 2026-11-11 | On acceptance review | Confirm time conventions and remaining profile/provenance gaps under [#2](https://github.com/Chain-Frost/python-runoff-routing/issues/2). |
| [S0 evidence capture](2026-11-10-s0-capture.md) | Implemented; acceptance open | Unassigned | 2026-11-11 | On acceptance review | Validate retained CMD/GUI evidence and capture completeness before closing S0. |
| [S1 CMD parameter/output inspection](2026-11-10-s1-inspection.md) | Implemented subset; Windows checks previously passed, acceptance open | Unassigned | 2026-11-11 | On parser review | Verify .catg/.stm source identities and native print-site/time mapping under [#3](https://github.com/Chain-Frost/python-runoff-routing/issues/3). |
| [S1 typed parser / canonical files](2026-11-11-s1-bidirectional.md) | Implemented subset; native canonical acceptance open | Unassigned | 2026-11-11 | On parser review | Single corrected #25 CMD 6.44 case now passed private replay; next validate #28 distinct physical vs graphical code-7 print labels. |
| [S1/S2 integration readiness](2026-11-11-s1-s2-integration-readiness.md) | S1 merged; S2 parity and integration acceptance open | Unassigned | 2026-11-11 | On S2 reconciliation | Revalidate S2 #21, reconcile selected fixes into #23, retain explicit no-parity status. |
| [RORB GUI/CMD behavior audit](2026-11-11-rorb-forensics.md) | Planned | Unassigned | 2026-11-11 | On evidence capture | Start isolated Windows GUI/CMD observations under [#16](https://github.com/Chain-Frost/python-runoff-routing/issues/16). |
| [Private bootstrap](2026-11-09-bootstrap.md) | Scaffold merged (#11); stage gates open | Unassigned | 2026-11-11 | On stage validation | Validate S0 native capture and retain the separate numerical gates; no release is implied. |

[Implementation plan](../IMPLEMENTATION_PLAN.md) links all stage issues. S0-S7 remain unaccepted; S8 is deferred. Issue status and this register do not mean an agent is currently running. Review dates do not schedule background work.
