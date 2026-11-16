# Issue #9: Monte Carlo scope and statistical research plan

- Status: planning delivered for review; no Monte Carlo implementation, simulation-budget result or native qualification.
- Reviewed: 15 November 2026.
- Parent: [#9](https://github.com/Chain-Frost/python-runoff-routing/issues/9); roadmap [#1](https://github.com/Chain-Frost/python-runoff-routing/issues/1).
- Inspected public baseline: `0675d75b05dba7728b389fdd8af743060b4469b2`, merged deterministic design-rainfall PR #136.
- Implementation owners: unassigned until an agent accepts a scoped issue.
- Branch: `docs/issue9-monte-carlo-scopes-20261115`.

## Reason for the change

The owner requested bounded work scopes, a determination of whether current RORBwin GUI/Ghidra inspection is needed, an assessment of available distribution documentation, a Python study of simulation-count stability, and durable documentation of the adopted statistical basis.

The existing event/batch workflow is sufficiently developed for independent sampling and statistics work. Its deterministic source preparation does not implement arbitrary-probability interpolation, stochastic loss/TP selection or weighted flood-frequency analysis. The existing private research and supplied manuals/release notes should be reused; they are not an executed native MC qualification.

## Delivered planning

- [#145](https://github.com/Chain-Frost/python-runoff-routing/issues/145): statistical basis, distributions, probability conventions and evidence gaps.
- [#146](https://github.com/Chain-Frost/python-runoff-routing/issues/146): persisted sample plans, probability/depth interpolation and reproducible sampler.
- [#147](https://github.com/Chain-Frost/python-runoff-routing/issues/147): weighted frequency curves, completeness and representative-event rules.
- [#148](https://github.com/Chain-Frost/python-runoff-routing/issues/148): simulation-budget/convergence research and bounded variance-reduction comparison.
- [#149](https://github.com/Chain-Frost/python-runoff-routing/issues/149): prepared event execution, text/API integration, compact persistence and resume.
- [#150](https://github.com/Chain-Frost/python-runoff-routing/issues/150): bounded native observation and independent statistical/native qualification.

Each issue includes its own handoff prompt, acceptance criteria, dependencies and ownership boundary. [MONTE_CARLO.md](../MONTE_CARLO.md) is the enduring initial method note; the existing source register and documentation indexes provide navigation.

## Review and checks

Independent planning reviews covered statistical correctness, repository readiness/ownership and published-source claims. Corrections incorporated:

1. Give probability-to-depth interpolation to the sampler owner; the event adapter consumes its result and materialises the storm.
2. Extending a plan preserves eligible earlier draws/IDs but revises the plan and all affected stratum weights. Require full reaggregation, rejecting mixed weights.
3. Define adequacy using error tolerance plus required whole-run pass probability/confidence; 30 independent trials are screening, not a 95%-reliability proof.
4. Keep new unapproved raw native captures local outside Git until separate applicable custody/publication approval exists.
5. State median storm-IL scaling, fixed initial spatial pattern, and explicit preburst/ARF transformations.

Validation is limited to issue cross-links, repository-relative links and factual-claim/source review. No numerical tests, source/wheel calculations, convergence experiment, native launch or Ghidra inspection was performed for this documentation-only change. Existing numerical/reference/CI policies are unchanged.

## Remaining decisions and next action

Start #145's adopted-method review and #148's analytical study design. Schema and exact weighted analytical controls can proceed alongside them; complete catchment-specific research after the relevant sampler/result/adapter interfaces and event-policy qualification.

No universal sample count, native RNG match, current native IL coefficient table, interpolation/tail rule or statistical tolerance is adopted by this planning PR. Full CMD #5, design-rainfall #8/#137, future RORBwin PAR #144 and advanced feature gates retain their independent status. Keep #9 and its implementation/qualification children open.
