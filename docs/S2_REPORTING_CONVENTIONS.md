# S2 native report-volume conventions versus physical-horizon integration

**Status:** independent reporting diagnostic, **not** numerical RORB compatibility acceptance.
The strict [S2 integration](https://github.com/Chain-Frost/python-runoff-routing/pull/23),
[regression contract](REGRESSION.md) and original raw time labels remain unchanged.

## What is being compared

For raw printed discharge samples `q[0]..q[N]` and sample spacing `h` hours, two
mathematically different statistics are kept explicitly:

- **Candidate native summary:** `3600*h*sum(q[0..N])`, inclusive full-weight
  sample sum including both endpoints.
- **Physical horizon:** `3600*h*(q[0]/2 + sum(q[1..N-1]) + q[N]/2)`,
  the trapezoidal integral over `N*h` hours.
- Their difference is exactly `1800*h*(q[0]+q[N])`. It is an **endpoint
  weighting difference**, not a timestep shift or flow-routing discrepancy.
- The printed sample-index centroid is `sum(i*h*q[i])/sum(q)`; this is a
  discrete statistic, **not necessarily a continuous-time volume centroid**.
  It is undefined for entirely zero discharge.
- Original native time tokens are preserved untouched, separately from
  `i*h` sample-index elapsed time. CMD 6.44 and GUI 6.52 can print different
  time labels for the same series, so neither is silently retimed.

[Retained offline source-phase/volume investigation](https://github.com/Chain-Frost/runoff-routing-investigations/blob/main/docs/work/2026-11-11-source-phase-volume.md)
reports 116 native summary volumes consistent with the inclusive sample-sum
candidate within the raw summary/source printed resolutions; 26 exclude the
physical-horizon trapezoid. Those findings are **bounded to the observed profiles**
and are not a promise about every future RORB build or mode.

## Pure API example

```python
from decimal import Decimal

from runoff_routing.reporting_conventions import audit_volume_conventions

audit = audit_volume_conventions(
    ["0.0000", "1.0001"],
    timestep_hours=Decimal("0.5"),
    native_reported_volume_token="1.80E+03",
    raw_native_time_tokens=["0.50", "1.00"],
)
assert audit.inclusive_sample_sum_m3 == Decimal("1800.18")
assert audit.physical_trapezoid_m3 == Decimal("900.09")
assert audit.sample_sum_consistent_with_report is True
assert audit.trapezoid_consistent_with_report is False
assert audit.raw_native_time_tokens == ("0.50", "1.00")
assert audit.sample_index_elapsed_hours == (Decimal(0), Decimal("0.5"))
```

The input is **raw source print text**, not rounded Python floats. Both the
discharge samples and optional native reported scalar carry independent
half-of-last-printed-unit intervals. Each consistency verdict means only that
the two **reporting uncertainty intervals overlap**. If both overlap, both
are reported as consistent; no preferred hypothesis is forced. Without a
native reported value, both consistency verdicts are `None`.

The routine does not read any files, infer RORB engine identity, execute
RORB, calculate inflow/excess, compare predicted versus observed discharge,
check conservation, or generate a tolerance policy. A passing volume-report
hypothesis **does not** make a failed S2 full-ordinate parity case pass.
Physical-horizon integration remains the appropriate separately labelled
quantity when auditing storage continuity over a physical interval.

## Testing and next integration

The public synthetic suite covers constant nonzero endpoints at 0.5/0.25/0.125 h,
manufactured single-step 1.80E+03 native summary, zero and single-sample
cases, individual raw print resolutions, raw CMD/GUI time-label distinctions,
malformed/non-finite tokens and scientific-notation native summary intervals.
No proprietary case data are transferred to the public repo.

**Next:** the integration/reporting owner may expose the two separately named
volumes in a future explicit native-comparison report. Do not silently replace
`PrintedParity.native_integral_m3`, which represents the physical-horizon
trapezoid, or relabel source raw times. Keep S2 issue #4 open pending the
outstanding strict full-ordinate routing discrepancies and separately authorised
native causal probes.
