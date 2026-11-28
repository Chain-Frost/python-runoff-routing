# 28 November 2026 — #148 conditional research implementation

Scope: source-independent work requested after the #243 synthetic evidence and #244
Python-only specification. Base `e80e56dbd1089874b527b98f9d1606532474c733`. This branch is separate from concurrent
#243/#244; #245 remains the only other-PC evidence-custody issue. No original private
data, physical M04 run, native execution, stochastic sampler invocation, new preflight,
adopted method, or production frequency/solver change. No scientific issue is closed.

## Exact read-only conditional ledger

[Research kernel](../../repo-scripts/mc_conditional_research.py) uses Decimal allocation
masses as exact rational numbers and each stratum's full planned count. It preserves
the restricted rainfall-coordinate denominator 0.49, ties, true zero, unknown mass,
strict survival and attained generalized inverse. It does not use rounded per-event
serialized weights, discard failures, renormalize the observed prefix or extrapolate
the 0.51 excluded domain. Unknown mass is a logical interval under a defined
nonnegative latent response, not an assumption of physical admissibility.

The adapter requires externally pinned immutable project, request, ledger and optional
wheel, one v1 Python CMD scenario/duration population with explicit original masses
0.49/0.01/0.50, unique requested project print ID, and the existing full verified
result iterator. It reads to exhaustion (including final integrity checks) and
rechecks pins before returning. Existing verification owns sample/engine/source
binding; this code is not another ledger parser or runner. External pins must be
obtained independently; matching a digest does not establish scientific custody.
The mathematical kernel alone cannot authenticate arbitrary rows.

## Candidate reference intervals

[Confidence kernel](../../repo-scripts/mc_conditional_confidence.py) implements the
#243 weighted Hoeffding/KL split-reference-alpha proposal for an independently frozen
family of K <= 256 CDF grid points across sites. For normalized stratum masses v_h and
positive counts n_h, S = sum(v_h^2/n_h), b = max(v_h/n_h). The Hoeffding radius is
sqrt(S log(4K/alpha)/2); the weighted Bernoulli KL limit is b log(4K/alpha).
Each family receives alpha/2; union over the grid and both directions retains
the requested reference error alpha. No assumption of independence between sites
or censored endpoint observations. Independence applies to the complete latent
weighted draws, which still requires separate admission.

For the weighted KL argument, convexity on each bounded indicator contribution
after scaling by b and concavity in the Bernoulli mean bound the product moment
generating function by that of a scaled Bernoulli with mean F. Invert this bound
in both directions. Decimal directed division and adjacent representable
correctly-rounded Decimal logarithms enclose the exact log, with subsequent rational
arithmetic. The square root is rounded upward by integer square root and the
56-step KL brackets return only certified exterior trial means. Intersect the
two valid reference enclosures; use observed lower and upper CDFs to preserve
pathwise censoring enclosures. Monotone tighten and invert a fixed finite grid
without inventing an upper quantile at an unresolved tail.

This is a candidate, not an adopted reference construction. Exact finite-distribution
checks support its numerical behavior; they are not a full independently reviewed
one-engine scientific qualification. Do not change tolerances, alpha or physical
execution budgets on the basis of this implementation.

## Verification and handoff

Linux CPython 3.13.5: 23 focused deterministic tests passed on the four exact
new source/test blobs in an isolated directory. The tests cover original Decimal
boundary preservation, unequal weights, ties, zero, missing/failed draws, duplicates,
invalid values, final reader failure, finite-distribution convolution, censoring,
rare-tail narrowing, zero/one and finite-grid inversion. No package install or
routing took place in this isolated environment. The four Git blob hashes match the
locally executed bytes. The appended real verified-ledger integration test uses
the repository's two-event authored deterministic fixture and tests prefix bounds,
external pin rejection and read-only behavior. It requires full repository CI and
has not been run locally. GitHub clone/network DNS is unavailable locally; Ruff,
strict Pyright, full CI and independent exact-head review remain required.

Next: complete actual reader integration/quality review, then agree and qualify
the exact one-engine study construction and independent oracles before activation.
Do not repeat the archived two-engine study. #245 remains sufficient for the
other-PC custody/validation/loss/rights scope; no new local evidence request.
`simulation_authorised=false` for physical admission; #148/#9 remain open.

## Bounded one-engine implementation qualification — 28 November 2026

The [predeclared development study](https://github.com/Chain-Frost/pyrorb/pull/246#issuecomment-7232426403)
completed all eight controls, 200 independent studies each, using the exact candidate
confidence implementation at commit `af5028181c5784116ea3df938f6c87bace0dc798`, kernel SHA-256
`a6d22b55edf1e3717dab21073895bbb8474fe8770f19e084ec51ea166d663b7d`.
This is a smaller author-run source-independent qualification, not the entire
previously proposed 1,000 studies/control scientific campaign. No scientific
reviewer acceptance/power threshold or physical protocol is adopted.

Executed [source](../research/issue148/one_engine_qualification/validation.py.txt)
SHA-256 `2e624c048af01b731da36c28df4a20639b6dc3d7315884280358b187517e5e01`,
and [exact JSON result](../research/issue148/one_engine_qualification/results.json)
SHA-256 `fc5a033646873901072aa21608606bb042f5e42de98c1116bd87c9d0953b6e5b`
retain the executed bytes. Git blob identities are respectively
`52311723dc23caf898b998fd31b8acac207c6e3b` and
`e16706dbfa2f37825f8696517febcc68c51ddd35`.
Linux CPython 3.13.5, NumPy 2.3.5, SciPy 1.17.0; 28.2290 seconds,
146,948 KiB peak RSS, 3,833,800 multinomial count vectors. Exit 0, one actual
execution, no adaptive enlargement or replacement. The separate launcher imposed
the declared 300-second wall limit, 2 GiB virtual-address limit, output-file limit
of 32 MiB and one-thread numerical-library settings. No product sampler, native
engine, private model, physical routing, or physical events.

### Results

Every row uses 200 synthetic studies. The full reference CDF family and
generalised-inverse/zero-atom region covered the exact finite-law target in every
study. The exact reliability oracle is available in six controls; in controls
3/4 only an independently certified upper bound on true reliability is used to
classify verdict correctness. Do not claim full joint reliability interval
coverage for those two controls.

| Control | Reliability truth or upper bound | Adequate | Inadequate | Unresolved |
| --- | ---: | ---: | ---: | ---: |
| 1 Constant | 1 (exact) | 200 | 0 | 0 |
| 2 Half-zero atom | .4933399574 (exact) | 0 | 200 | 0 |
| 3 Rare jumps and ties | <=.8731226024 | 0 | 198 | 2 |
| 4 Unequal strata and laws | <=.4482614666 | 0 | 200 | 0 |
| 5 Different constant scales | 1 (exact) | 200 | 0 | 0 |
| 6 Rare zero atom | .9999348442 (exact) | 200 | 0 | 0 |
| 7 Outcome-dependent censoring and caps | .4933399574 (exact) | 0 | 0 | 200 |
| 8 Near-half zero atom | .4933612099 (exact) | 0 | 200 | 0 |
| Total | Not pooled as a single law | 600 | 798 | 202 |

Zero observed false verdicts or latent observation/classification enclosure
violations; exact-oracle joint reliability coverage 1,200/1,200 where assessable.
The complete study preserves all missing weight; control 7 yields 0 definite and
300 possible confirmations in every study, hence unresolved rather than a false
success or failure. This supports the fail-closed numerical design without
establishing that 1,000 events suffice universally.

The six prespecified metrics use simultaneous empirical Clopper-Pearson endpoints
at .05/(2*8*6). For a control with 200/200 coverage the lower empirical limit is
.9629051153, below the nominal .98 reference target. For zero false verdicts
in 200 studies the upper limit is .0370948847. These finite results cannot
establish nominal reference coverage or arbitrarily low false-decision risk.
No empirical acceptance threshold was adopted. Numeric CP endpoint evaluations
are diagnostic; the decision rule uses the independently established exact
critical counts >=294 definite or <=275 possible out of 300. The original
two-engine #243 qualification is not rerun.

### Reproduction and current-head quality correction

For reproduction, copy the archived source verbatim into a scratch
`qualification/one_engine_validation.py` directory immediately below a scratch
root containing the historical kernel at `repo-scripts/mc_conditional_confidence.py`.
Use the exact historical kernel from `af5028181c5784116ea3df938f6c87bace0dc798`, the versions and caps above,
and a fresh output filename. Preserve the fixed seeds and laws. The JSON records
the executed source/kernel hashes; runtime fields naturally differ on another
host. This script is retained as historical research text, not a maintained
production entry point or ordinary CI workload.

The original CI run [46095215881](https://github.com/Chain-Frost/pyrorb/actions/runs/46095215881)
failed at Ruff formatting. After the formatter-only correction, run
[46098376632](https://github.com/Chain-Frost/pyrorb/actions/runs/46098376632)
passed repository checks and Ruff lint/format but stopped at four strict Pyright
unnecessary-isinstance diagnostics on typed Fraction guards. Retain all runtime
Fraction rejection through a small object-typed boundary helper; no mathematical
formula or valid-input behavior changes. Add explicit rejection checks for float
alpha, weights and both CDF endpoints. The same 23 focused isolated tests pass
on the locally checked corrected source and test blobs. The archived experiment
used the earlier exact kernel, not the later source hash; do not attribute the
historical result to a new binary. Fresh hosted quality and exact-head review are
required for the correction and evidence batch. Actual product reader integration
still needs the full repository test gate.

No physical/custody evidence changes, no further task for #245, no physical
admission, activation, merge or release. Independent scientific disposition,
actual source/manifest approval and any required larger qualification remain
separate. Keep #148/#9 open, `simulation_authorised=false`.
