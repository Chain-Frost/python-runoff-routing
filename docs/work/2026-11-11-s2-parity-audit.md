# S2 offline printed-precision and balance audit

**Status:** source-only diagnostics, numerical compatibility remains unaccepted. **Date:** 2026-11-11.
**Stack:** this work is based on S2 draft PR #14, without modifying its author branch.

## What this adds

- Pure `assess_printed_parity` checks **every native discharge token** against half of its individual printed last-place unit. It reports first out-of-budget index, peak indices, maximum/RMS and scaled errors, a near-zero diagnostic, independent trapezoidal outlet integrals and their printing uncertainty. No retiming or peak-only acceptance.
- `audit_printed_linear_balance` uses *independently known prescribed inflow* and the existing `audit_reach_balance` (not a solver internal residual) to inspect printed downstream samples. It exposes every step's inflow/outflow flux, inferred storage change, closure residual and propagated print-precision bound, plus the initial/final storage and global closure. Initial storage is treated as exactly known only when the native first output equals the prescribed initial value. The sign convention is storage change + outflow - inflow.
- Source-level synthetic tests cover two grids for the same triangle, repeatability, nonzero equilibrium, near-zero tokens, malformed data, and material mismatch despite matching peak index.

## Fixed budgets and interpretation

For printed discharge `q`, let `e(q)` be **one half of the last printed unit**, based on its raw Decimal token. Strict printed parity requires `abs(Q_python - q) <= e(q)` at **all** samples. This is a precision budget, not a general hydrological tolerance. It is not retrospectively relaxed after observing a mismatch.

For a **linear k** with exact externally prescribed inflow, the step-balance rounding bound is

`3600 * [(k + h/2) * e_out[n] + abs(k - h/2) * e_out[n-1]]`.

The global bound is the trapezoid outflow integral uncertainty plus `3600*k*(e_out[0] + e_out[-1])`. When the pinned initial output exactly matches independently prescribed initial flow, its uncertainty is zero. This makes the full-horizon bound slightly tighter than the conservative 1.98 m³ original experimental budget; it does not increase an allowance to fit measured errors.

These bounds assume **linear storage m=1** and a prescribed, verified input. Do not apply this printed-balance policy to nonlinear storage, unobserved internal inflows, whole-catchment outlets, native volume reports or unverified input phase. `Qout[0]=Qin[0]` remains unchanged.

The exact continuous piecewise-linear ODE remains a distinct comparison; it is *not* substituted for the finite-step trapezoidal kernel. A smaller native time step is not automatically more correct. A pass of a rounding hypothesis does **not** establish an accepted engine profile.

## Local validation and next gate

A Linux / Python 3.13.5 supplemental check exercised 13 synthetic test cases against a locally reconstructed linear recurrence and independent audit shim: 13 passed. A real source checkout on Windows / Python 3.14, Ruff 0.16.6, strict Pyright, wheel build, installed-wheel out-of-tree test, full S2 affected suite and **full private corpus** are still **NOT RUN** in this environment. This status must not be promoted to numerical acceptance.

A separate **private** read-only campaign driver imports this public API and the existing S2 `compare_corpus_case` to inventory the 65 catalogue cases and inspect the four supplemental linear cases, retaining full CSV/JSON under ignored local output. No private files are bundled here; the private campaign and its review must be executed in an owner-authorised checkout.

Next: run that campaign with a real Windows/Python 3.14 installed source branch, check all statuses/hashes, then investigate the already observed strict nonlinear one-reach discrepancy with a manufactured single-step and constant-flow control. Keep S2 issue #4 and PR #14 draft; no merge, release, hosted workflow or native execution.

## Offline adapter repair, 2026-11-11

Source base 53021ff. Added strict UTF-8/BOM then CP1252 decoding for legacy inputs and recognised the documented all-pervious flag annotation. No numerical kernel or tolerance changes. Windows Python 3.14.6: 98 tests passed; build and isolated installed-wheel campaign completed. Existing full-suite static gates remain failing (24 Ruff findings before final edits; 8 Pyright findings), so this is not acceptance-ready.

Private runner base 50790dc also corrected its six-line prescribed-inflow grammar. Installed wheel: 941 indexed files verified; four supplemental linear checks pass; all 65 catalogue records retained: 36 compared, 25 skipped-unreviewed, 3 expected-failure, 1 invalid incomplete reference. Comparisons remain exploratory and numerical acceptance open. Full private output retained under ignored .local/s2-adapter-repair-wheel in the investigations audit checkout.

Next: review full ordinate mismatches and isolated nonlinear storage; repair static findings before integration or merge.

## Quality gates and nonlinear controls, 2026-11-11

The follow-up batch fixes all observed static findings without weakening Ruff families or Pyright. Validation, stack execution and reference record checks are split into focused functions; the strict reach algorithm and numerical tolerances are unchanged. Tests use the public storm result for average distance instead of a private helper.

Windows Python 3.14.6: repository hygiene, Ruff 0.16.6 lint/format, strict Pyright (0 errors) and 104 tests passed. Six manufactured nonlinear checks cover exact Q1=1 endpoints and nonzero equilibrium at 0.5/0.25/0.125 h. Seven private cached nonlinear tests passed against this source, reproducing the original strict mismatch and independent bisection agreement.

Build and installed-wheel campaign rerun passed execution: 941 indexed files; four supplemental linear passes; 65 catalogue outcomes (36 compared, 25 skipped-unreviewed, 3 expected-failure, 1 invalid). All 36 computed cases fail the printed-precision hypothesis. Complete JSON and all 41 CSV files are byte/structure identical to the preceding adapter-repair run. Private output: ignored .local/s2-quality-wheel in the audit checkout. This confirms the refactor did not alter computed evidence.

S1 PR #19 at f356ec5 has a successful hosted Windows check. S2 native compatibility remains open. Next: obtain explicit opt-in for bounded manufactured native nonlinear probes before inferring a legacy stopping profile; preserve strict kernel and fixed tolerances meanwhile.

## Overlap reconciliation: PR #21 versus #22 (2026-11-11)

PR #21 is the selected S2 adapter/strict-quality implementation. The overlapping PR #22 only addressed legacy text transport and the all-pervious annotation. PR #21's strict UTF-8/BOM/CP1252 decoder and exact all-pervious annotation handling are retained; unknown and nonzero impervious flags still reject. RORB v6 manual Table 5-2 permits the known inline annotation after the numeric flag. PR #22's two additional regression scenarios (annotated nonzero rejection and fingerprint-verified CP1252 whole-case comparison) have been added here. The separate #22 implementation is superseded; do not combine competing decoders or change routing formulas/tolerances.

The 104-test Windows/Python 3.14 quality and installed-wheel evidence cited above applies to the preceding `17102b8` head. The two newly imported tests require exact-head revalidation before treating this revised head as quality checked. Their addition does not establish CMD or GUI numerical parity, and S2 issue #4 remains open.

## Nonlinear printed-storage audit (follow-up, 2026-11-11)

A separate stacked, draft source slice adds `audit_printed_nonlinear_balance` without changing the strict `route_reach` kernel or any native tolerance. For independently pinned prescribed inflow, it calls the existing independent timestep balance audit and bounds the uncertainty from raw printed downstream ordinates: each `Q` lies in `[max(0, Q-e), Q+e]` where `e` is half the original printed last unit. The nonlinear storage uncertainty at one sample is `3600*k*max((Q+e)**m-Q**m, Q**m-max(0,Q-e)**m)`. A step's conservative bound sums both endpoint storage uncertainties and `1800*h*(e_prev+e_next)` for trapezoidal outflow. The global bound uses only first/last storage uncertainty and the output-integral rounding allowance. This is not a fitted native convergence tolerance; it remains valid when `m < 1` and `Q=0` without differentiating a singular slope.

Public synthetic tests check manufactured exact first endpoints, deliberately perturbed printed results, zero/near-zero storage, constant equilibrium, invalid inputs and nonanticipation: future prescribed inflow must not alter a strict past-timestep calculation. A standalone Python 3.13 diagnostic shim exercised 12 focused mathematical cases, but **not** an installed source wheel; source-tree Ruff, Pyright, Windows/Python 3.14, full-suite and private corpus remain **NOT RUN** for this follow-up. Do not mark S2 numeric acceptance from this diagnostic, and do not use it to claim native physical mass balance or to infer an RORBwin profile. The native CMD single-reach differences and future-peak dependence remain unresolved.
