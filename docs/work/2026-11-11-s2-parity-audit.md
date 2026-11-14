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

## Additive integrated nonlinear printed-storage diagnostic (draft)

Selected independently authored source: [S2 PR #27](https://github.com/Chain-Frost/python-runoff-routing/pull/27), `4cc9eec` (itself on the older #21 stack). This follow-up applies **only** its nonlinear printed-uncertainty diagnostics and 12 public manufactured/nonanticipation tests onto the current S1/S2 [integration #23](https://github.com/Chain-Frost/python-runoff-routing/pull/23). The S1 parser and source-decoder APIs remain authoritative; no parallel legacy parser or older S2 kernel is reintroduced.

`audit_printed_nonlinear_balance` is restricted to independently prescribed, matched inflow and original raw printed discharge tokens. It propagates half-last-place uncertainty through the full nonnegative nonlinear storage interval, including `Q=0` for `m<1`, and reports per-step and full-series residual-budget status. These are **printing-only** bounds around the documented trapezoidal continuity equation, not a fitted RORB nonlinear stopping budget or an observed native storage state. The public strict `route_reach` kernel, tolerance policies, reference inputs and output time labels are unchanged. The synthetic nonanticipation test remains explicitly inconsistent with the observed native future-forcing dependence; this is a diagnostic, not an attempt to make the strict solver match RORB.

This stacked PR requires exact-head Windows Python 3.14 pinned Ruff, strict Pyright, all public tests, installed wheel, and separately authorised private offline application to one-reach prescribed-inflow evidence. No native launch, private data transfer, issue closure or merge is implied by green CI. S2 #4 remains open.

## Half-print-unit boundary review (2026-11-12)

An exact-head automated code review of the integrated diagnostic found that binary float subtraction could reject a prescribed upstream value exactly **one half of a native printed last-place unit** from its recorded raw token. The accepted example is input 1.23445 against the four-decimal native token 1.2344; the excluded example 1.2344500001 remains outside the same original boundary. Both prescribed-inflow checks (linear and nonlinear) now reuse the existing Decimal-token comparison semantics of `assess_printed_parity` through a single helper, with four synthetic regression instances. This is an input-validation correction only: no prescribed flow interpretation, physical residual, storage law, solver iteration, tolerance magnitude, profile acceptance or native evidence was changed.

The revised exact head requires new Windows/Python 3.14 Ruff/format, strict Pyright, full pytest and installed-wheel verification before source merge. The private installed-wheel 65-case replay of this additive diagnostic is not performed by the public hosted checks. Numerical S2 issue #4 stays open.
