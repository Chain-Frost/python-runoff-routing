# Issue #148 — analytical convergence study and handoff (15 November 2026)

Owner's bounded scope: only isolated convergence research and synthetic analytical controls. Do not edit A/B/C/E production types, deterministic numerical engines, other agents' branches, fixed CMD regression corpus or the single CMD feature matrix.

- **Deliverables:** `repo-scripts/mc_convergence_research.py` (opt-in cost-capped research generator, exact reference, independent seeds and conservative frequency/tail controls), `repo-scripts/plot_mc_convergence.py` (standard-library SVG plots), `tests/test_mc_convergence_research.py` (seven synthetic/statistical tests), research report and retained compact stage receipts in `docs/research/issue148/`.
- **Executed locally:** Linux, Python 3.13.5, `pytest` 7 passed; five complete study stages and small 77k-event preflight; no native/CMD routing, hosted CI, independent reviewer, wheel, Ruff/Pyright executable or product numerical validation was run in this scope. The research scripts are not shipped as `runoff_routing` package modules.
- **Result:** for the defined two-site/two-duration synthetic population and 24-output whole-run, the 5% study tolerance passed 2/100 independent confirmation runs at 1,000 events/duration and 5/100 at 2,500. Exact one-sided 95% upper bounds on those success probabilities are 0.062 and 0.102, below the provisional 0.95 criterion. Do not generalise to real catchments or another policy.
- **Provenance:** stage-separated SHA256 seeds, pinned scripts, parameter manifest, analytically exact reference, raw per-replication quantiles/envelopes, exact-binomial pass bounds, bootstrap SD diagnostics, critical-duration frequencies, complete mass and event-budget/wall/memory accounting. No unapproved native data were exported.
- **Scientific limitations:** not ARR/RORBwin frequency compatibility, not a hydrologic model or `python-cmd` acceptance, not a production count threshold. Missing-tail bounds are explicitly unresolved; reference for real models requires independent high-precision simulation with its own uncertainty.
- **Next action:** after #145/#146/#147/#149 stabilise their interfaces and site/engine qualification, an independent reviewer under #150 audits the analytic methods and the bounded real-catchment pilot/confirmation. Link this report from the final `docs/MONTE_CARLO.md` owner (the document is concurrently owned by #145 and initially introduced in draft PR #151). Keep parent #9 open.

See [full methods and results](../research/MONTE_CARLO_CONVERGENCE.md) and [scope #148](https://github.com/Chain-Frost/python-runoff-routing/issues/148).

## Addendum — positive-control confirmation and independent review

- The first five historical stages and seven-test initial handoff above remain accurately attributed to their original source revisions. **Subsequent** work adds two tests (now **nine locally passing** on Linux/Python 3.13.5), and an opt-in sixth stage without altering the original five raw receipts or silently relabelling their script SHA.
- A deliberately constructed *low-variability but nondegenerate* second synthetic population was independently stage-seeded for 100 confirmations at each of 250, 500 and 1,000 evaluations **per duration**, retaining 7,200 complete 24-output rows, exact analytic references, the manifest and one-sided binomial intervals. Under the proposed 1% relative / 0.002 synthetic absolute and 95%-reliability criterion, pass counts are **72/100 (inadequate), 96/100 (unresolved) and 100/100 (adequate only for this specified synthetic population)**; the 1,000-event one-sided lower bound is 0.970. Exploratory response selection is disclosed and prevents generalisation to an unbiased hydrological catchment population.
- The new simulation-time script SHA is `7f46c621229c19b9ed3efdd68be04a853941d8fe40139d42ee490007949d035f`; the stage used **350,000** synthetic evaluations, **7.309 seconds**, 4.11 MiB traced peak, Linux/Python 3.13.5. Six analytical stages total **2,625,000** synthetic evaluations. This is not a native launch, a `python-cmd` throughput receipt or a real flood-AEP result.
- **F/#150 independent scientific review has now completed both parts** of the synthetic research on PR #168: 14,160 original rows/590 variant-replication groups and the new 7,200 rows/300 independent replication groups, including independent Clopper–Pearson limits and separate reference integration. Both reviews report **no concrete statistical discrepancy**. A passed synthetic review does not qualify real-catchment or current-build native behaviour.
- Previous [Windows/Python 3.13 CI #43728288716](https://github.com/Chain-Frost/python-runoff-routing/actions/runs/43728288716) completed successfully on earlier source/staging merge `0846201`. New research additions were corrected for pinned Ruff formatting and strict Pyright at later heads; [current follow-up CI #43732400389](https://github.com/Chain-Frost/python-runoff-routing/actions/runs/43732400389) passed strict local quality on `253379a`, with source CMD/wheel checks not yet complete at this record. This is GitHub CI evidence, not locally executed Windows checks.
- **Remaining full issue #148 gate:** conduct a bounded named physical-site catchment study *through the qualified common B→E→C execution/result path* after #145/#146/#147/#149 policy/contracts integrate, with separate independent high-precision references, uncertainty, failed/missing/tail mass and engine profile. The F/#150 native comparison and engineering acceptance are distinct; do not claim either here. Keep #148/#9 open and PR #168 in Monte Carlo staging.


## 16 November 2026 — confidence-limit correction

A subsequent focused branch repairs large-n binomial upper-tail numerical underflow in
\`repo-scripts/mc_convergence_research.py\`, keeping exact one-sided Clopper–Pearson
inversion and historical research receipts. Eleven focused local tests passed Linux /
Python 3.13.5, including independent 1,000,000-replication binomial/CP reference values
and archived original/synthetic-positive first-run replay. Research-only SciPy beta
quantiles independently checked 11 count configurations up to 10,000,000
replications (not a runtime dependency); the largest bound differences were
approximately 1e-12. Source/wheel CI and reviewed PR status are independent.

A named real-catchment convergence acceptance is still not run: the #149
materialisation/execution adapter remains unmerged; B/C source modules alone do
not establish a qualified B→E→C flow-frequency result. See the main report
for explicit preflight requirements. Do not relabel prior synthetic results
as actual hydrological convergence.


## 16 November 2026 — optional research SciPy and current study gate

High-count `binomial_upper_tail` uses optional research-only
`scipy.special.betainc` for n >= 1,000,000 if installed, avoiding
large-n `lgamma` cancellation. Regular dev/product installation remains
dependency-free; the logarithmic recurrence remains as fallback.

All B/C/E code is now staged under #151, but a fully qualified
catchment-specific convergence study has not been run. The public
example IFD/catchment is synthetic; v1 1%-50% rainfall support leaves
51% unmodelled mass. Do not infer full-domain adequacy or native parity.
