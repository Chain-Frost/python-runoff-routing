# S6 rainfall-preparation capability and acceptance matrix

**Reconciliation date:** 2026-11-14. **Status:** four draft implementation PRs, source and arithmetic validation only. Neither RORBwin compatibility nor design hydrology acceptance is claimed. Parent #8 and #33 remain open.

| Stage | Recognised and parsed | Source validation | Python event / arithmetic | Native effective-input acceptance | Routed acceptance |
| --- | --- | --- | --- | --- | --- |
| P0 #38 — ARR 2026v1 | `RecIFD` current 2030, historical 1961–1990, native baseline JSON/TXT; legacy ARR2016 TXT opt-in | Typed axes, decimal depths, WGS84, version, byte SHA-256; unknown layers preserved as unprocessed | No ARR2026 automatic generator or climate products | Not assessed | Not assessed |
| P1 #48 — BoM and patterns | BoM 2016-methodology CSV, explicit AEP/EY/ARI/one-in-N; ARR2016/2019 point/areal increment CSV/ZIP | Original bytes/member hashes, original IDs and ordering, duration grid, ZIP safety, absent areal AEP retained | Caller-selected gross increments only; no implicit normalisation | R0 24/24 zero-loss rainfall observed, not stage-wide acceptance | Not assessed |
| P2 #49 — ARR2019 ARF/selection | Source region, point/areal boundary, nine area bins and common AEP frequency bands | Exactly ten patterns required, original source order, published vs legacy Data Hub region coefficients distinct | Equations 2.4.1–2.4.4; explicit one-time ARF on raw BoM | R1 24/24 within printed-depth precision; strict excess FAIL | Not assessed |
| P3 #50 — legacy losses/preburst | Original ARR2016 TXT storm IL/CL and five preburst percentile depths/ratios | Original source hash, rainfall basis, missing -50, percentile, ratio/deduction consistency | Separate burst-only or caller-defined full preburst; experimental IL/CL mass balance | Unaccepted; experimental PR #54 separate with six strict residual failures | Not assessed |

## Source and method boundaries

- **ARR2026 is not ARR2019.** Parsing versioned default IFD baselines does not validate 2026v1 temporal-pattern, SSP, climate, ARF, preburst or jurisdictional loss methods.
- **BoM source date differs from methodology date.** Retain original issuance, coordinates, labels, units and bytes; AEP, EY, ARI and 1-in-N labels are not interchangeable.
- **Temporal patterns:** exact event IDs rather than ordinals, source order, region, area/frequency bin and all ten members are required. Missing areal AEP remains absent.
- **ARF coefficient audit:** Book 2, Tony Ladson's R gist and ryan-tools all have Inland Arid `g=+0.129`. For South-West WA, published `e=3.85E-06` differs from script `e=3.845E-06`; no averaging or fitting to native discrepancies.
- **Once-only preparation:** gross and areal rainfall are distinct types; source preburst depth remains separate from selected ratio times once-ARF-reduced rainfall, with source hash, basis and percentile. Burst-only reduced IL and complete-storm storm IL cannot be combined.
- **Independent code:** S6 modules do not depend on S1 models, S2 numerical kernels, third-party runtime libraries, network downloads or native engines.

## Separate acceptance gates

| Gate | Evidence | Status | Next proof |
| --- | --- | --- | --- |
| Source-data | Synthetic parser tests and local offline BoM/FLTwest replays, original hashes retained | Source-format only; exact-head CI required | Authenticated current ARR2026 optional exports and provenance |
| ARR2019 arithmetic | Decimal coefficients, independent published ARF example, source TP order and loss mass balance | Source/formula stage only | Independent effective-storm computations by frozen reference policy |
| RORBwin R0/R1 | R0 24/24 zero-loss rainfall exact; R1 24/24 printed rainfall consistent | **Unaccepted**: R1 strict excess FAIL | Characterise saved/reopened full-precision source, one-increment raw CSV label offset and step-16 residual without changing tolerances |
| RORBwin experimental losses | Separate PR #54 full-increment CL: 42/42 isolated controls, six cached strict precision residual failures | **Unaccepted**, not selected as default | Additional conditional controls, GSAM/Jordan profiles, remaining failures |
| Routed hydrograph | No accepted generated-storm routing campaign | **Not assessed** | Compare all ordinates only after effective-input parity |

## Not implemented or unaccepted

Automatic ARR2026 IFD/SSP selection and uplift; jurisdictional losses and preburst; ARR2026 temporal pattern methods; default RORBwin GSAM/Jordan profiles; catchment spatial region verification; spatial rainfall; embedded-burst filtering; RORB file output; automatic representative hydrograph selection. No end-to-end hydrological design certification.

See [P0](ARR_S6_P0.md), [P1](ARR_BOM_TP_GROSS.md), [P2](ARR_S6_P2_SELECTION_ARF.md), [P3](ARR_S6_P3_PREBURST_LOSSES.md), [reconciliation work record](work/2026-11-14-s6-reconciliation.md) and [separate native PR #54](https://github.com/Chain-Frost/python-runoff-routing/pull/54).
