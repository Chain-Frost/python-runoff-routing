# S6 R5: native long-duration default preburst characterisation

**Status:** one R5 run completed; native defaults observed; Python default-pattern equivalence unimplemented.

**Owner:** Local Windows agent. **Updated:** 2026-11-14. **Review:** on selection of conditional R6/R7 cases.

**Source implementation baseline:** `b2c89eae7517d1117fd522f24a1897ab7622823d`.
**Branch:** `feat/s6-rorbwin-native-rainfall`; stage [#8](https://github.com/Chain-Frost/python-runoff-routing/issues/8), open.

After the [controlled crossing experiment](2026-11-14-s6-controlled-loss-kernel.md) characterised the
bounded loss rule, the owner's next recommended step was one separate default-pattern R5 run.
It did not substitute for the still-failing fine-precision excess checks or change any default Python method.

## Effective native setup

The experiment retained corrected R4's editor-saved **RORB_GE 6.52** model, **100 km²**, **24 h / 1% AEP**,
FLTwest areal **EventID 9091**, file ARF coefficients, IL **21 mm**, CL **2 mm/h**, and manual preburst
depth **5.4%**. No spatial rainfall, impervious area or embedded-burst filter was introduced.
The **Use default pre-burst patterns** checkbox was enabled; **Use ARR data hub pre-burst depths**
remained disabled. The inherited synthetic coefficient TXT is not a site loss/preburst export.

RORBwin selected **Inland Zone**, the as-loaded GSAM default. The GUI also offers Coastal Zone,
but it was not selected or tested. This is a recorded software default, **not** an independently
validated geographic zone for the illustrative Margaret River point.

The unchanged executable has SHA-256
`0ca65bcef548f26a5f9bceda6c99ed4f545a9498b61c93aa59a00400732d1aea`, computational banner **6.52,
updated 1 June 2023**. The model hash remains
`189bc5d27f9dddbbdf9d555fa3fb0b79137dd54c9c5d06f4f9a5b02c62b3dc09`.
The separate pre-run R5 protocol capped this experiment at **one** native calculation.

## Observations

| Item | Native observation |
| --- | --- |
| Default long-duration source | GSAM, Inland Zone |
| Default editor time increment at 24 h | **3 h** |
| Effective generated rainfall timestep | **1 h** |
| Generated preburst length | **21 hourly increments** |
| Design-burst length | **24 hourly increments** |
| Total forcing length | **45 increments** |
| Printed preburst depth | **6.58 mm** |
| Written burst / combined depth | **121.85 / 128.43 mm** |
| Native excess total after unit conversion | **64.2410964 mm** |

All 45 rainfall/excess positions and all **201** raw CSV records are retained. The initial record
and 155 trailing records are zero; the known excess-export labels remain one increment/one hour
above the separate native hydrograph labels. Native design-burst origin is hour **21**, unlike
corrected R4's hour **2**. Raw time labels and origins are preserved explicitly.

The preburst relative weights sum to **5.4**, with combined weight **105.4**, scaled to written
depth **128.43 mm** in the input-matched diagnostic. The reconstructed preburst is approximately
**6.57990512334 mm**. Raw default pattern tables/sequences remain private native evidence; they
were not copied into a Python GSAM/Jordan implementation.

Replaying the separate Decimal loss candidate on this native rainfall passes **43/45** cells at
the unchanged **0.0000018 mm** allowance. Steps **27/41** fail, maximum approximately
**0.00000190740038 mm**. They are strict expected failures in the cached native replay, not accepted
native parity. All 24 design-burst excess tokens equal corrected R4's corresponding tokens, while
the preburst shapes and origins differ. Both tested preburst totals are below the initial loss;
this observation does not establish pattern-independent behaviour generally.

## Scope and next action

An isolated eleven-file capture retains native inputs, outputs, GUI-saved parameters, the pre-run
protocol and hashes. Screenshots record default mode, zone and time increment; per-step diagnostics
retain both clocks. Prior R0–R4 evidence remains unchanged. Full source/wheel validation and replay
counts are in the [controlled loss work record](2026-11-14-s6-controlled-loss-kernel.md).

R5 is **characterised for this long-duration/default-zone case only**. It is not equivalent to the
Python user-defined 25/75 preburst profile, and **short-duration Jordan behaviour is NOT RUN**.
Conditional **R6/R7**, full native excess precision, and routed-flow acceptance remain open/unrun.
Next: select supported point/areal boundary and frequency/interpolation cases with explicit source
identities and effective native settings. PR #50 remains draft; no merge, release or stage closure.
