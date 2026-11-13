# Integrated S1/S2 native print and volume review

**Status:** review-only integration API, **not** accepted native numerical equivalence.

This additive integration uses the typed S1/S2 RunResult and the independent reporting_conventions audit. It never modifies the solver, the default RunResult JSON/CSV schema, the native parser or the recorded reference outputs.

## API

~~~python
from runoff_routing.integration_reporting import review_recorded_print

review = review_recorded_print(
    result,
    original_native_discharge_tokens,
    model_print_id="print_1",
    native_column_id="Hyd001",
    engine_profile="RORB_CMD 6.44, installed-executable SHA-256 verified separately",
    raw_native_time_tokens=original_native_time_tokens,
    native_reported_volume_text="7.56E+04",
)
payload = review.to_json()
~~~

This API requires a **caller-established** mapping between the model's physical print ID and an actual native output column. Native time labels are mandatory and preserved exactly; model elapsed time is separately calculated from the timestep and the zero-based sample index. A nonblank engine profile must be supplied, but executable SHA-256, effective settings and the print-location mapping still need independent S0 manifest verification.

The returned RecordedPrintReview combines:

- PrintedParity: existing full-ordinate strict printing comparison, peak sample indices and independently integrated physical-horizon fluxes. A passing printed parity result by itself does not establish native numerical equivalence.
- VolumeConventionAudit: historical inclusive sample-sum candidate, physical-horizon trapezoid, discrete sample-weighted centroid, the endpoint-weight difference, native summary volume when provided, and separate printing uncertainty bounds.
- Explicit model and native column identities, the externally supplied engine-profile description, and numerical_acceptance="unassessed".

The JSON representation retains all Decimal values as decimal **strings**. The original native time tokens and physical elapsed-time grid remain separate. No legacy-style time shifting or tolerance adjustment is applied.

## Ownership and acceptance

Based on the merged S1/S2 integration contract and the standalone reporting-convention implementation proposed by PR #40. This branch records a two-parent Git merge of current main and the original PR #40 head, retaining source ownership without rewriting either author branch. If PR #40 merges first, the additive integration changes can be reviewed independently.

The new API is **not** a native solver, does not parse a native report to discover the output site, does not infer historical version identity from the report, and does not automatically assert source/engine parity. It is a read-only connector for independently verified input tokens.

Tests use only the public synthetic RunModel fixture and no native executables or private evidence. Full private-corpus acceptance and true RORB numerical-equivalence review remain separate gates. No existing JSON/CSV outputs are changed by this PR.

References: [S2 reporting conventions](S2_REPORTING_CONVENTIONS.md), [S1/S2 integration](S1_S2_INTEGRATION.md), [regression contract](REGRESSION.md).
