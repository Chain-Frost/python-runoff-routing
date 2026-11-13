# Typed native reporting integration

| Field | Value |
| --- | --- |
| Status | Draft implementation, no native numerical acceptance |
| Updated | 2026-11-12 |
| Owner | Unassigned |
| Base | Current main plus reviewed PR #40 reporting helper |
| Tracking | [S2 issue #4](https://github.com/Chain-Frost/python-runoff-routing/issues/4) |
| Next action | Exact-head Windows/Python 3.14 quality tests, then private-corpus review |

## Scope

Add integration_reporting.RecordedPrintReview and review_recorded_print without changing the existing S1/S2 solver, parser, time shifting policy, printed-precision tolerance or default report schema. Require explicit model/native print-site mapping, engine profile and original raw native time tokens. Return both strict all-ordinate printed comparison and separate native volume-statistic candidate versus physically integrated flow. Keep native numerical acceptance unassessed.

The implementation is a distinct branch based on the latest merged S1/S2 main and the original PR #40 reporting source, with two-parent merge provenance. Neither owner branch was changed.

## Evidence

The original PR #40 reported successful pinned Ruff 0.16.6 / strict Pyright / 158-test Windows quality and installed-wheel import. That is evidence for its own branch, not for this combined branch.

The integration tests are synthetic and no reference executables, private model files or raw proprietary output are committed. Report exact-head Windows CI separately; do not reclassify previously failed nonlinear native cases or accept a new reporting convention universally.

## Stop boundary

No change to nonlinear stopping criteria, source grammar, rainfall losses, root-finding, water-balance tolerances or RORB_Cmd/GUi profiles. Do not merge the paired reporting PRs or publish a package without separate review.
# Owner-requested dependency and installed-wheel review, 2026-11-13

Original #45 head `4fc1efd80f92a42626ca4f4c8281ec11c007e9a4` was reviewed with the
unchanged reporting module from #40. The owner-requested #40 merge completed first
at `925bdae8dbb5d286e84261db1cebef80f1d9f132`; this branch includes that main revision.
Only documentation indexes required conflict resolution. No runtime implementation,
numeric tolerance or reference input changed during this review.

Windows/Python 3.14.6: full repository checks 94 files / zero errors, Ruff 0.16.6
lint/format (84 files), strict Pyright zero errors/warnings, 310 non-native tests
passing without skips. A fresh wheel was installed in its own environment and
exercised outside the checkout with source PYTHONPATH unset.

The complete owner-approved 65-case offline catalogue was covered: 36 computed
strict comparisons remain numerical failures, 29 are explicitly unsupported.
All 36 computed cases also passed through the actual installed integrated review
API, preserving model/native print identities, complete raw time/flow tokens and
`numerical_acceptance="unassessed"`. Its model discharges exactly equal the
independent offline comparison's complete predictions. All 863 indexed corpus
files were hash/size checked before and after. Unsupported profiles stay unsupported.

The separate private #27 installed reporting verifier also passed unchanged:
36 reports, 30 CMD / six GUI, 116 inclusive-sum consistent columns and 26
trapezoid exclusions, with its 40-entry evidence index unchanged. These establish
reporting integration and regression preservation, not native numerical equivalence.
No RORB launch belongs to these reporting checks. Hosted exact-head checks and
the delivered/merged revision are recorded in the PR conversation; S1/S2 remain open.
