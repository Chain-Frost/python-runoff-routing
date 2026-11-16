# F/#150: independent analytical reference controls

This folder contains **author-created synthetic probability examples**, not
original RORBwin observations, design-rainfall fixtures or a second production
reference catalogue. Source of truth for native CMD routing remains the existing
public regression dataset and its comparator. The [qualification work record](../../../docs/work/2026-11-15-mc150-independent-qualification.md)
identifies the separately required MC evidence gates.

`analytic-controls.json` uses rational strings (`"3/4"`, `"10"`) so the expected
mass, peaks and exceedances are exact. The independently calculated checks are
run by `tests/test_mc150_independent_reference.py` with Python `Fraction` and no
imports from production MC code. A subsequent F integration must **feed these
same cases into the implemented #146 sampler/#147 aggregator** and separately
verify output; this initial self-check is not that integration test.

## Hand calculations

1. **Q01 — unequal strata, ties and valid zero.** The dry stratum has mass
   1/4 split between two zero-flow events, each 1/8. The wet stratum has
   mass 3/4 split between peaks 10, 20 and 20 m³/s, each 1/4. At threshold
   10, strict exceedance is `1/4 + 1/4 = 1/2`; naively pooling five
   unweighted events gives `2/5`, which is wrong. At threshold 0 it is 3/4,
   and the mass at 0 is a **valid 1/4**, not a failure. Equal-to-threshold
   mass at 20 is 1/2. The example's *step* inverse thresholds for upper-tail
   probabilities 3/4, 1/2 and 1/4 are 0, 10 and 20 respectively. This is
   **not an adopted production interpolation rule**.
2. **Q02 — positive-weight failure and absent result.** The west stratum's
   two events each weigh 1/4 (one valid 5, one failed); the east stratum's
   four each weigh 1/8 (valid 0, 2 and 8, one missing). Known valid mass is
   5/8, failed mass 1/4 and missing mass 1/8. At threshold 4, the known
   strict exceedance is `1/4 + 1/8 = 3/8`; its possible total is bounded
   by `[3/8, 3/4]` because unresolved mass is 3/8. Neither a zero imputation
   nor renormalising valid events yields an accepted curve.
3. **Q03 — unmodelled probability tails.** Two complete *interior* events
   have weight 1/4 each and peaks 1 and 3. The frequent/rare unmodelled
   tails retain mass 1/5 and 3/10. At threshold 2, observed exceedance
   1/4 can only be bounded by `[1/4, 3/4]` without a tail model. An
   interior-only percentile cannot be reported as a complete estimate.
4. **Plan extension.** An original stratum of mass 1/5 has two events with
   weights 1/10. Extending it to four events without changing the first
   two samples makes *all four* weights 1/20. The other stratum of mass
   4/5 remains two events of weight 2/5 each. At threshold 6 the original
   exceedance is 1/2; the extended exceedance is 9/20. Old and new
   plan revisions are distinct, even for unchanged sample IDs/draws.
5. **Duration/site envelope.** At 5% AEP, upstream's 60-minute event is
   critical (40 versus 35 m³/s), while downstream's 120-minute event is
   critical (80 versus 60). At 1% AEP the critical durations reverse:
   upstream 120 minutes (70 versus 50), downstream 60 minutes (90 versus
   85). No pooling across sites, durations or AEPs is valid.

## Future production comparison

The adopted sample-plan/result schema is owned by #145–#149. Once stable, F
should consume their *public API outputs*, preserving the native/source TP ID,
modelled probability support, original/effective values, and plan/engine/profile
identity. Match sample IDs, finite values, status, per-stratum weights and
per-physical-site/per-duration results against these controls; ensure the
aggregator rejects or qualifies incomplete tails and failed runs. Step-quantile
checks apply **only if** the adopted policy chooses the same inversion rule.

If a future contract cannot represent any of these facts, record a specific
qualification gap; do not silently change the fixture or tests to force a pass.
