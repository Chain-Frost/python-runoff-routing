# S6 — explicit ten-event rainfall ledger (2026-11-14)

**Owner:** S6. **Status:** proposed standalone opt-in implementation on a draft branch; native/hydrological acceptance open.

**Tracking:** [#8](https://github.com/Chain-Frost/python-runoff-routing/issues/8). **Branch:** `feat/s6-explicit-ensemble-ledger-20261114`.

## Scope

Build one audited, deterministic **ten-member** ARR2019 source-order gross rainfall bundle by composing the already merged temporal-pattern selector, BoM source and raw-storm generator. Optionally apply an explicitly supplied, source-labelled ARR2019 ARF once to every gross storm. Provide a pure JSON ledger of all increment values, time labels and original IDs to support future independently controlled native comparisons.

This is a small independent addition, not a rewrite of existing P0–P3, RORBwin 6.52 loss experiments or the N4 coefficient-sensitivity protocol. Source bytes, native evidence, existing default loss/routing, tolerances, golden data, CI/workflow and public release state are untouched.

## Evidence boundaries

- Exact AEP percentage only; rejects implicit EY/ARI/one-in-N conversion and cross-source patterns.
- Recomputes the source selection to reject reordered/missing patterns; no representative index is assumed.
- Keeps the original event ID separate from its 1-based **source-order** position and exact `Decimal` rainfall vectors; no rounding in JSON.
- Explicit ARF must match area/duration/AEP, and produces distinct adjusted types while retaining gross inputs.
- Tests use fabricated BoM and temporal-pattern sources; none is an accepted native or authentic site result.

**Quality state:** check the pull request's exact-head Windows/Python 3.14 Ruff, Pyright, full tests, wheel import and repository checker before merge. No local Windows/Python 3.14 or installed RORBwin execution is available in this environment. Even successful CI would validate source/software only.

## Next action

Review the opt-in ledger API and exact-head synthetic gate, then use the locally retained original EventID-9091 source and the independent native N4/R0–R7 work to compare **all input increments** under a frozen engine profile. Do not infer numerical acceptance, choose representative hydrographs or change the original 0.0000018 mm excess tolerance.
