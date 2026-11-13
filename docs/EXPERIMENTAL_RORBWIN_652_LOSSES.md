# Experimental RORBwin 6.52 loss profile

`runoff_routing.rorbwin_losses` provides a separate opt-in, readable **Decimal** candidate for
pervious initial/continuing losses. It does not replace or change `arr_losses`' existing experimental
partial-timestep method. No existing event API selects this candidate automatically.

The profile ID is **`rorbwin_6_52_full_increment_cl_experimental_v1`**. It is **not accepted for full
native parity**. See the [controlled native investigation](work/2026-11-14-s6-controlled-loss-kernel.md)
for the executable identity, tested scope, precision residuals and time-label observations.

## Explicit API

```python
from decimal import Decimal

from runoff_routing.rorbwin_losses import calculate_rorbwin_652_excess

result = calculate_rorbwin_652_excess(
    tuple(Decimal(value) for value in (10, 10, 10, 0, 10, 0)),
    timestep_min=60,
    initial_loss_mm=Decimal(19),
    continuing_loss_mm_per_hour=Decimal(2),
)
assert result.excess_increments_mm == tuple(Decimal(value) for value in (0, 0, 8, 0, 8, 0))
assert result.native_parity == "not_accepted"
```

Inputs are finite nonnegative rainfall **increment depths in mm**, initial loss in **mm**, continuing
loss in **mm/h**, and a positive whole-minute timestep. Computational source order is retained.
Empty rainfall, nonfinite/negative values, zero/negative timesteps and Boolean timesteps reject.
The frozen result exposes rainfall, IL consumption, CL consumption and excess for every increment,
with the entered loss values and timestep. It does not mutate inputs, read files, route flow, round
values or change timestamps.

For each increment, consume remaining IL first, then consume up to a **full timestep's CL capacity**
from any remaining rainfall. Cap both losses by available rainfall. In particular, the IL-consuming
fraction of a crossing increment does **not** reduce that increment's CL capacity. Dry increments
consume no losses and do not reset the candidate's remaining IL.

The caller must supply already effective rainfall and the deliberately selected storm or burst IL.
This kernel performs no ARF, preburst generation, initial-loss reduction, source matching or default
policy selection. Do not subtract preburst twice. Impervious fractions, other loss models, changing
loss parameters and routing are outside this API.

## Bounded evidence and limitations

Seven controlled native runs cover IL below/at/above a 20 mm cumulative boundary, CL 0 and 2 mm/h,
and one 30-minute case. All **42** rainfall-length excess cells agree with the candidate under the
unchanged **0.0000018 mm** print allowance. These cases include zero-rainfall steps after IL is
exhausted; they do not exhaust all dry-gap, restart, multiple-burst or impervious behaviours.

Cached R2/R3/R4 replay on native written effective rainfall still fails four cells at that allowance:
R2/R3 step 11 and R4 steps 8/22. They remain strict expected failures in the explicit private replay;
they are **not** accepted native regressions. Public unit tests use independent synthetic analytic
expectations, without private rainfall archives or native execution.

The subsequent [R5 default-pattern observation](work/2026-11-14-s6-r5-default-preburst.md) adds two
input-matched precision failures at the same frozen allowance. It does not implement or validate
Python generation of the native default patterns.

Binary32 arithmetic-order hypotheses can reproduce those printed observations, but no one tested
order reproduces all retained R1–R4 controls. This Decimal semantic candidate deliberately introduces
no inferred native floating-point mode and does not claim bitwise equivalence.

Raw excess CSV labels differ by **one increment** in the observed 60- and 30-minute native exports.
That is 1 h and 0.5 h respectively. Original labels must be retained alongside any explicitly derived
sample-index/physical-time coordinates. This kernel has no time-label mapping; the observation is
not a universal parser correction or a declaration of complete native event acceptance.
