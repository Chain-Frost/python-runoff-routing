# Independent Monte Carlo B/C integration control — issue #150

**Date:** 16 November 2026. **Branch:** test/issue150-bc-independent-qualification-20261116. **Parent:** #150 and #9. **Base:** 0596c706d72630955885ce91fa362a890e1630b3, the Monte Carlo staging branch under draft #151 (not main).

This is a **bounded independent software qualification** of the already-staged #146 sampled-event contract and #147 weighted frequency API, distinct from any native RORBwin or flood-engineering acceptance. It adds a single executable test to the existing #150 fixture module, not a sampler/runner/estimator/comparator or second public reference catalogue.

The test takes six actual, deterministic, versioned #146 draws, including their stable sample IDs and precisely weighted original strata (2 × 0.05 and 4 × 0.075) and explicit 0.6 missing probability-domain mass. It supplies **separately authored physical-output response values**, including an intentionally **failed positive-weight 0.05** sample and a **valid zero-flow 0.075** sample, to the actual #147 C public API for two different physical sites.

The independently derived expected controls are:

| Invariant | Expected |
| --- | --- |
| Two distinct sites | No cross-site pooling |
| Valid total mass | 0.35 |
| Failed mass | 0.05, not zero or dropped |
| Unmodelled frequent/rare rainfall mass | 0.5 / 0.1; total 0.6 |
| Total unresolved mass | 0.65 |
| Valid zero-peak mass | 0.075 |
| Strict P(Q > 0) for both sites | 0.275 |
| Strict P(Q > 10), upstream | 0.15 |
| Strict P(Q > 10), downstream | 0.225 |
| Upper logical P(Q > 10) bound | 0.8 upstream, 0.875 downstream |
| Flood AEP point and representative | **Incomplete/unavailable** despite successful synthetic draws |

The response table is **synthetic**, not native RORBwin or even a \`python-cmd\` run. Exact B source/TP identity and C full probability mass do not prove the separate #149 effective preparation, routing, persisted-ledger integrity, replay or native compatibility. E's draft PR #161 has its own source tests and one B→E→C CLI test; F must independently review any final integrated source/wheel receipt before upgrading the software acceptance claim.

**Qualification workflow:** run existing repository Windows/Python 3.13 CI at the actual PR head; inspect Ruff, strict Pyright, exact full source tests, source original-CMD regression, isolated installed-wheel checks and original-CMD wheel regression. Report zero unexpected F skips. An earlier PR #163 receipt preceded the #146 integration, so its four skipped B-consumer tests **must not** be called B acceptance. No Windows RORBwin executable has been launched in this task.

**Still open under #150:** F1–F6 current-build native MC observations, separately matched source/effective-input and routed results, real-catchment independent-seed convergence and defensible engineering acceptance including unmodelled probability tails. Keep #150 and #9 open and #151 staging unmerged to main merely on the strength of this control.
