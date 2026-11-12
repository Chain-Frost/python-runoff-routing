# S2: first printed-precision discrepancy relative to runoff onset

**Status:** diagnostic only; not native numerical acceptance. Source stage [#4](https://github.com/Chain-Frost/python-runoff-routing/issues/4) stays open. This intentionally does not duplicate [nonlinear printed-storage balance #41](https://github.com/Chain-Frost/python-runoff-routing/pull/41), the [future-peak budget investigation](https://github.com/Chain-Frost/runoff-routing-investigations/pull/17), or [native-volume convention #40](https://github.com/Chain-Frost/python-runoff-routing/pull/40).

The new pure `runoff_routing.onset_diagnostics` module **reuses** `assess_printed_parity` and its pre-existing per-native-token half-last-place budget without selecting any new tolerance. It reports the first strictly discrepant sample relative to the first nonzero value in either the predicted or native series, plus both separate onset indices. The native raw increment and time tokens are optional but must be provided together; they are carried verbatim, **never** shifted onto the model-elapsed axis.

The output classes are `within_print_budget`, `at_onset`, `next_sample`, and `later`. Even `within_print_budget` is only a *printed-precision comparison*, not engine acceptance. A tiny positive predicted flow may be masked by a printed `0.0000` and is not automatically a failed ordinate. Source/individual-reach observations are still required to distinguish rainfall/excess construction, initial state, source placement, and routing from one another.

## API

```python
from runoff_routing.offline_reference import compare_corpus_case
from runoff_routing.onset_diagnostics import audit_offline_comparison

# Run only against a separately permission-cleared, read-only private corpus.
comparison = compare_corpus_case(corpus_root, "selected-case-id")
report = audit_offline_comparison(comparison)  # no native execution or I/O of its own
print(report.classification, report.first_outside_budget_index)
print(report.first_mismatch_native_increment, report.first_mismatch_native_time)
```

`audit_offline_comparison` rejects unsupported/incomplete records, missing time steps, row count changes, and reordered sample indices. Its `OnsetAudit` includes the complete unchanged `PrintedParity`, distinct native and Python onset indices, raw native first-mismatch tokens and signed difference. `summarize_onset_audits` reports category counts, rejecting duplicate named cases. No process starts, input/fixture files, manual content, native executables or private outputs enter the public source.

## Separate retained evidence (not committed here)

A new read-only **exploratory** analysis examined the 36 previously retained private CMD calculation-comparison CSVs, without rerunning RORB or changing the installed solver. It found the earliest discrepancy **at first nonzero flow in 35 cases**, and **one sample after first nonzero flow in one case**; none requires a later cumulative error before exceeding printed precision. This is a sample-index timing observation using the original printed discharge resolution, **not** a causal routing/source attribution. One near-onset case remains initially inside its original printed allowance. Its first-mismatch token and the rest of the original data remain private.

Other separately verified evidence: 15 linear/loss API cases have printed-precision agreement of independently projected excess/source/outlet calculations (without successful legacy file import); four isolated linear profiles pass. Full-catchment 36/36 failures, nonlinear finite-iteration/future-forcing dependence and native CMD/GUI clock differences remain unresolved.

**Next discrimination:** use independent, fingerprinted source hydrograph and upstream/downstream reach prints for the earliest failure interval. If the source prints already differ, classify that stage before routing. If independently matched source prints enter a reach and its output differs, investigate that reach's initialisation, `k`/storage and nonlinear stopping with separate mathematical balance versus native print budgets. Never infer source agreement solely from matching whole-catchment outlets or adjust the temporal axis to improve an error metric.
