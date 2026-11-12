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
