# Regression and performance contract

## Evidence layers

1. Parser/model fixtures: structural expectations, malformed inputs and unsupported features.
2. Independent numerical checks: simple/analytic cases, conservation, loss bounds, nonnegative storage/flow and timestep sensitivity.
3. Cached native regression: original inputs and raw results from a pinned CMD or GUI build; no executable needed for routine replay.
4. Explicit native Windows acceptance: verify the capture/run adapter and source/installed-wheel calculations on the actual supported environment.
5. Ensemble and Monte Carlo acceptance: event-level parity first, then sampling/probability and aggregate behaviour.

These layers are complementary. A native engine is a compatibility oracle, not proof of hydrological correctness. Synthetic labels applied to one event are not independent native simulations.

## Capture contract for the friend's ensembles

Retain each catchment (.cat/.catg or combined .dat), storm (.stm), CMD .par, raw .out/.log and any available hydrograph CSV. Include the generator configuration/revision and event-to-file mapping, not just batch peak summaries. Original source bytes must remain unchanged. Runtime capture is explicit opt-in and uses isolated local directories; do not run reference binaries in ordinary tests.

Every case manifest must record:

- schema version, case ID, feature tags and provenance/redistribution status;
- engine kind, executable SHA-256, observed banner/version and operating environment;
- SHA-256/size and relative locator for each input and raw output;
- effective kc/m, loss-model semantics, loss values/units, burst/ISA mapping, timestep, horizon and print-location identities;
- GUI effective settings and saved/generated inputs when GUI execution is the reference;
- command/working-directory policy, exit status, diagnostics, outcome and elapsed-time measurement context;
- expected output locations, raw-to-canonical field/time mappings, tolerance-policy ID and known differences.

Absolute private paths and executables stay local. Keep small permission-cleared fixtures in tests/fixtures/rorb with byte-preserving attributes; keep bulky/private evidence under ignored .local and reference it through approved manifests. Do not claim the uploaded SampleData.zip covers a feature until its cases are inventoried and executed.

## Comparison gates

Require complete case and print-location coverage, exact IDs/counts and unmodified source hashes. Compare rainfall totals/excess, contributing areas and reach/ISA metadata before hydrographs. Compare every ordinate, peak magnitude, peak index/time, horizon, volume/centroid where supported, and independent water balance. Missing or duplicate columns, NaN/overflow, truncated records and unexpected warnings must not disappear during parsing.

Use reviewed absolute plus relative numeric tolerances, with a near-zero floor and output-rounding allowance. Derive acceptance budgets from native output precision, repeatability and routing conventions. Freeze each tolerance policy before accepting comparisons; do not choose a loose percentage after seeing a mismatch. Timing must match the characterised grid; any allowed conversion is explicit and version-aware. Test flat peaks with a documented tie policy.

Report pass, fail, unsupported and not-run separately. Missing native binaries/data must fail the requested native acceptance campaign or produce an explicitly incomplete result, never a green acceptance claim. Cached tests can run without binaries. A failed event cannot be removed from an ensemble or probability denominator without invalidating acceptance.

Golden changes require an explicit update operation, regenerated provenance and a reviewed diff. Ordinary tests must never update expected outputs. Run reference inputs before/after and verify hashes. Installed-wheel checks run outside the checkout and verify the imported module location.

## Performance protocol

Measure single-event cold end-to-end time separately from warm in-memory numerical time. For 1, 100, 1000 and 10000 identical explicit events, record model size, increments, requested outputs, repetitions, median/spread, hardware/OS, dependency versions, thread/worker settings, elapsed time and peak memory. Record JIT compilation independently if used. Compare serial and parallel results and reset all event state.

Repeated RORB_CMD launches include process startup and file I/O. Native RORBwin internal ensembles/Monte Carlo are a different baseline. Missing GUI timing is recorded as missing, not inferred. Benchmarking against a subprocess wrapper does not establish an advantage over compiled in-process RORB. Performance changes must retain the same accepted numerical corpus.

## Monte Carlo-specific gate

Persist the full sample plan with RNG algorithm/version, seed, event IDs, duration, probability strata/masses, sampled depth, loss draw and TP identity. Worker scheduling must not change draws. Different RNGs with the same seed do not constitute matched samples.

Validate weighted total probability, sampling bounds/tails, zero-runoff mass, frequency conversions, interpolation, per-duration curves and critical-duration rules using independently checkable cases. Never use unweighted percentiles for unequal-probability strata, pool unrelated durations or silently renormalise omitted tails. Separate exact deterministic replay from aggregate statistical agreement with GUI runs. Compare increasing sample sizes and independent seeds, and label sampling uncertainty separately from parameter/model uncertainty.

Representative hydrographs must identify the actual sampled event and selection rule. A representative at one print point is not necessarily representative at every other point. Do not imply that the published manual fully specifies every implementation detail; unresolved details remain open until probed or clarified.
