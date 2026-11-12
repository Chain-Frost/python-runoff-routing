# Work register

| Work front | Status | Owner | Updated | Next review | Next action |
| --- | --- | --- | --- | --- | --- |
| [Computational reference guidance](2026-11-11-computational-reference-guidance.md) | Owner wording applied | Local agent | 2026-11-11 | Next procedure investigation | Implement Python procedures and verify against pinned RORB computations. |
| [S0 native validation](2026-11-11-s0-native.md) | Partial native evidence; stage open | Unassigned | 2026-11-11 | On acceptance review | Confirm time conventions and remaining profile/provenance gaps under [#2](https://github.com/Chain-Frost/python-runoff-routing/issues/2). |
| [S0 evidence capture](2026-11-10-s0-capture.md) | Implemented; acceptance open | Unassigned | 2026-11-11 | On acceptance review | Validate retained CMD/GUI evidence and capture completeness before closing S0. |
| [S1 CMD parameter/output inspection](2026-11-10-s1-inspection.md) | Implemented subset; Windows checks previously passed, acceptance open | Unassigned | 2026-11-11 | On parser review | Verify .catg/.stm source identities and native print-site/time mapping under [#3](https://github.com/Chain-Frost/python-runoff-routing/issues/3). |
| [S1 typed parser / canonical files](2026-11-11-s1-bidirectional.md) | Implemented subset; native canonical acceptance open | Unassigned | 2026-11-11 | On parser review | Single corrected #25 CMD 6.44 case now passed private replay; next validate #28 distinct physical vs graphical code-7 print labels. |
| [S1 optional RORB_GE GIS authoring](2026-11-11-s1-ge-authoring.md) | Bounded CMD 6.44 and Python3.14 OGR checks passed; editor scope deferred | Unassigned | 2026-11-11 | When revisiting GIS | Prioritise S2/rainfall; GUI editor/field fidelity and QGIS packaging are not accepted. |
| [S1/S2 integration readiness](2026-11-11-s1-s2-integration-readiness.md) | S1 merged; S2 parity and integration acceptance open | Unassigned | 2026-11-11 | On S2 reconciliation | Revalidate S2 #21, reconcile selected fixes into #23, retain explicit no-parity status. |
| [S1/S2 Python integration](2026-11-11-s1-s2-integration.md) | Draft PR #23; CI/source checks after latest sync required, numerical parity open | Integration owner | 2026-11-11 | On CI/private corpus review | Validate exact head after S1 code-7 and S1-backed CP1252 source integration; no native acceptance inferred. |
| [RORB GUI/CMD behavior audit](2026-11-11-rorb-forensics.md) | Planned | Unassigned | 2026-11-11 | On evidence capture | Start isolated Windows GUI/CMD observations under [#16](https://github.com/Chain-Frost/python-runoff-routing/issues/16). |
| [Private bootstrap](2026-11-09-bootstrap.md) | Scaffold merged (#11); stage gates open | Unassigned | 2026-11-11 | On stage validation | Validate S0 native capture and retain the separate numerical gates; no release is implied. |

[Implementation plan](../IMPLEMENTATION_PLAN.md) links all stage issues. S0-S7 remain unaccepted; S8 is deferred. Issue status and this register do not mean an agent is currently running. Review dates do not schedule background work.
- [S1/S2 post-merge reconciliation](2026-11-11-s1-s2-postmerge-reconciliation.md): source-safe code-7 label distinction and selected S2 test coverage; numerical acceptance open.
