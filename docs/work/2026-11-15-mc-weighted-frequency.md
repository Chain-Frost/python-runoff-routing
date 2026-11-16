# S7/C issue #147 — weighted frequency result implementation handoff

**Status:** adopted #145 v1 noninterpolating step policy implemented in review PR #167; #150 independently inspected the method and reported no statistical mismatch. The original Windows CI failed strict Pyright on one repeated optional representative lookup, corrected in this handoff. This PR is stacked onto the draft #151 Monte Carlo integration branch, **not main**; revalidation and staging merge remain separate steps. Software checks do not accept RORBwin or engineering flood-frequency parity. **Owner:** current #147 agent. **Scope:** pure result-layer API, no sampler, solver, source reader, parser, CLI, duplicate persisted-plan schema or native captures. **Basis:** GitHub `main` at branch creation `80af6e961b5e3b129498a4cb6bce791b482c87e7` (15 November 2026); #145 published its adopted `monte-carlo-statistics/1` project method through staged [PR #151](https://github.com/Chain-Frost/python-runoff-routing/pull/151), which remained outside `main` when reconciled. Project adoption is not current RORBwin native or engineering acceptance.

**Changed surface:** `src/runoff_routing/monte_carlo_frequency.py`, `tests/test_monte_carlo_frequency.py`, [method and independent controls](../MONTE_CARLO_FREQUENCY.md), and this record. No change to `python-cmd/cmd-6.44`, native comparator, deterministic event runner, recorded original references or CLI. The Python API deliberately accepts a read-only view of B's planned stratum masses/allocation and E's per-site result ledger.

**Local tests:** Python 3.13.5 on Linux, `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python -m pytest -q tests/test_monte_carlo_frequency.py`: **19 passed** (source-local focused suite). Assertions include literal unequal-weight arithmetic and adopted weighted noninterpolating step inverse, affine monotone transformation, zero-flow atom, tied simulated peaks, strict exceedance, incomplete/failed/missing/unsupported masses, bounds and tails, attained-support boundary cases, permuted ledgers, rejected duplicate/mixed revision identities and weights, multi-site duration isolation, near/exact ties and representative event replay IDs. Neither RORBwin nor RORB CMD was executed. Static Ruff/Pyright and exact full-source wheel/CI results must be added only when actually checked on the published head; the isolated local test package is not a full public checkout.

**Review dependencies:** #145 adopted `monte-carlo-statistics/1` with strict exceedance and noninterpolating generalized-inverse quantile; the software adopts that project rule without claiming native parity. #146 owns persisted plan revision, weights and draw identity; #149 owns the adapter from actual common-engine outcomes, effective-input manifest and CLI/text-file persistence; #148 owns independent-seed convergence/appropriate intervals; #150 owns independent statistical/native qualification. All remain separate; parent #9 stays open. Do not claim that a green unit suite qualifies return periods or a RORBwin native build.

**Installed-wheel software API gate:** The existing approved Windows quality workflow now executes `tests/test_monte_carlo_frequency.py` from the isolated wheel installation destination and outside the source checkout, alongside the existing source/installed checks; the destination import path is verified in that same workflow step. This does not add a new workflow or imply native acceptance. Exact-head CI outcome must be recorded separately when complete.

**Review and remaining gates (16 November 2026):** #150 PR #163 supplied a scientific-source review with no method findings, but reported strict Pyright failing at the prior C test line 357. The test now stores the optional representative once and asserts it is non-null before access; no estimator arithmetic or production signatures changed. The independent #150 literal-rational adapter checks require the C API in the same staging checkout; the B/E→C production event-ledger adapter, persisted report/CLI, independent-seed convergence and actual RORBwin comparisons remain owned by #149/#148/#150. Preserve `monte-carlo-statistics/1:weighted-step-inverse-v1` and do not claim midpoint interpolation. **Next action:** verify GitHub quality CI and exact-head isolated wheel on this staging-targeted branch; then merge #167 into #151 only. Keep parent #9 open.

## Follow-up correction — 16 November 2026

The previously staged PR #167 was found to have a **material quantile rank
defect**, despite passing its original tests: at exact CDF steps binary
accumulation can choose an adjacent higher realised flow. Hand-checked
10-sample AEP 0.1 should give 8, not 9 m³/s. An analogous 20-sample
AEP 0.95 case and incomplete-tail bounds are independently specified.
The focused correction uses exact rational planned stratum masses for
decision comparisons while retaining the original reporting API,
provenance, unmodelled tails and unchanged project method.

**Disposition:** correction PR against draft #151 staging (not main).
Exact source/wheel CI and a new independent #150 acceptance review
remain required on the corrected head. No native or engineering claims.

**Independent code-review correction:** Codex review of #181 at `5c7c6c5`
identified valid Python integers greater than 2**53 losing exact peak
group mass during float reporting. The follow-up explicitly rejects those
integer-valued peaks before grouping and tests the exact binary64
integer boundary and an enormous integer. This is a fail-closed input
boundary for a float-valued reporting API, not a change to solver
precision or hydrological acceptance. A fresh independent review of
the correction and exact-head CI is required.

