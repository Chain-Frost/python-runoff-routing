# S2 isolated reach-routing reference prototype

| Field | Value |
| --- | --- |
| Status | Active — synthetic prototype; native equivalence blocked |
| Owner | Unassigned |
| Created / updated | 2026-11-10 |
| Next review | 2026-11-17 |
| Baseline | main at 4498f7f466eb34a35d5eecf35844aa5bd4d7dcf7 |
| Branch | feat/s2-reach-reference-kernel |
| Tracking | [S2 issue #4](https://github.com/Chain-Frost/python-runoff-routing/issues/4) |

## Scope and design

This intentionally standalone S2 slice adds pure numerical reach-routing functions. It can be developed without taking ownership of S0 reference evidence (#2/PR #12) or S1 legacy-format parsing (#3/PR #13). It does not implement the full S2 single-storm calculation and does not claim RORB compatibility.

The mathematical model follows the documented RORB Version 6 manual (January 2010, sections 2.2.1 and 2.2.5): storage S = 3600 * k * Q^m in m³, k = kc * kr, trapezoidal continuity between prescribed inflow/outflow ordinates and Qout[0] = Qin[0]. A caller provides the combined k; the future parser/model must calculate and verify kr/dav correctly. Time steps are hours, hydrograph values are m³/s.

The m=1 case is solved analytically; m != 1 uses bracketed false position with Illinois endpoint damping and a strict numerical residual tolerance. This gives a mathematically checked reference implementation, **not an exact reproduction of RORB's Regula Falsi iteration count, stopping tolerance, timestep behavior or native rounding**. If a coarse timestep produces a negative/non-finite routing target, the prototype raises an explicit domain error instead of silently clipping. RORB's actual behavior remains to be characterised.

This module performs no rainfall-loss conversion, catchment network traversal, event sampling, IO, logging, CLI processing, calibration, or special storage. It is not imported by existing S0/S1 code and adds no dependencies.

## Checks and limitations

- Local Linux / Python 3.13.5: 21 focused synthetic pytest cases passed (including four exponent variations, nine invalid-input parameter sets, conservation and manufactured-solution tests). Python compilation passed. These are mathematical/synthetic checks only.
- Windows / Python 3.14, pinned Ruff 0.16.6, strict Pyright, wheel-build/installed-wheel acceptance and native RORB comparisons are NOT RUN / NOT ACCEPTED for this branch.
- No evidence that this solver matches the exact native RORB time stepping, linear Muskingum representation, handling of very long increments, convergence tolerance or printed output.
- No RORB executables, manuals, source model files or private datasets added. No merge, release or publication authorised.

## Completion and next action

This *slice* can be reviewed only after target Windows quality and installed-wheel checks. **Issue #4 remains open** until complete single-storm results, loss/routing conventions and full hydrographs pass against named native references.

Next: after S1 input-model contracts stabilise, build an adapter that computes k = kc * kr with validated dav and routes real model reaches; compare each timestep against the pinned RORB_CMD/RORBwin cases from S0. Record disagreements without changing tolerance after observing the results. Later add network traversal and loss calculations as separate reviewed slices. Preserve this readable reference kernel when considering Numba acceleration.

Do not rework the S0 runner, S1 inspectors, GitHub CI settings or repository visibility in this workpack.

## Subsequent S2 computational slice (2026-11-11)

A bounded Python-only single-storm computation, fixture input adapter, independent linear-storage oracle and offline reference comparator were subsequently added to this PR. See [S2 offline development](2026-11-11-s2-offline-development.md). The historical 21-test statement above describes the **original reach-only commit**, not the later combined branch. S2 numerical equivalence remains unaccepted; do not treat the expanded functionality as closing issue #4.
