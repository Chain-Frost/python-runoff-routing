# Native RORB reporting statistics versus physical-horizon volumes

Status: proposed read-only compatibility helper, **not** accepted solver parity.

The retained RORB_CMD 6.44 / RORBwin 6.52 offline investigations indicate that native reported volumes can use an inclusive full-weight sum over all printed flow samples, rather than trapezoidal integration over the physical sample-index horizon. The two statistics must not share an ambiguous output field.

Given samples q[0] through q[N] at h hours:

- Native inclusive-sample-sum candidate = 3600 h sum(q[0] through q[N]).
- Physical-horizon trapezoid = 3600 h [(q[0] + q[N])/2 + sum(q[1] through q[N-1])].
- Difference = 1800 h [q[0] + q[N]], due solely to endpoint weights.

For 21 constant samples at 2 m3/s and h=0.5 h, the inclusive statistic is 75,600 m3 and the ten-hour physical-horizon integral is 72,000 m3. Both calculations are valid for differently named conventions; neither alone validates mass balance.

## Pure numerical API

The standalone function review_volume_conventions in runoff_routing.native_reporting accepts original printed discharge strings, timestep hours, an explicit version-qualified profile label, optional unmodified native time tokens, and an optional native reported-volume token. It returns a frozen VolumeConventionReview including:

- Raw native time strings **without any shift**, and a separate zero-based sample-index elapsed grid.
- Original native scalar and the two independently calculated candidate volumes.
- Inclusive-sum versus physical-horizon endpoint-weight difference.
- Individual half-last-printed-unit uncertainties for discharge-derived integrals and the reported native scalar.
- Boolean interval-consistency assessments, or None when no reported scalar was supplied. Consistency does **not** prove an internal algorithm or engine identity.

At least two finite nonnegative discharge samples are required. Original file bytes, executable fingerprints, print-site identities and effective settings remain the responsibility of the pinned S0/S1 evidence manifest.

## Supported interpretation and integration boundary

This helper computes statistics; it does not modify the routing kernel, fix native timing or accept RORB numerical parity.

The inclusive-sum observation applies to the tested native builds/cases, not universally. A discrepancy should be described as a metric-definition difference before alleging a physical mass-balance error.

S2's existing trapezoidal flux-integral and reach-storage balance calculations remain separate. The active S1/S2 integration PR #23 is owned by another agent: its author may consume this helper **after review and reconciliation**, without changing numerical tolerances or confusing the three concepts.

Validation: 12 synthetic tests and Python compilation passed locally on Linux/Python 3.13.5. Windows/Python 3.14, pinned Ruff, strict Pyright, whole-suite, installed-wheel and private-corpus replay remain outstanding. No native RORB was run and no proprietary data committed.

Related: [regression contract](REGRESSION.md), [S2 stage #4](https://github.com/Chain-Frost/python-runoff-routing/issues/4).
