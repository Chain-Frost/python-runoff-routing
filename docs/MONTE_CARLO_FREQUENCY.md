# Weighted Monte Carlo frequency results — adopted project step policy

**Owner:** [#147](https://github.com/Chain-Frost/python-runoff-routing/issues/147), under [#9](https://github.com/Chain-Frost/python-runoff-routing/issues/9). **Scientific basis:** [#145](https://github.com/Chain-Frost/python-runoff-routing/issues/145), project method **`monte-carlo-statistics/1`** in the staged [#151 method document](https://github.com/Chain-Frost/python-runoff-routing/pull/151) (not yet an accepted RORBwin 6.52 behaviour claim). The implementation identifies the statistical result profile as `monte-carlo-statistics/1:weighted-step-inverse-v1`. This is **the noninterpolating generalized inverse** adopted by #145, not a separate smooth/plotting-position profile. This document describes software semantics; no new rainfall distribution, stochastic execution engine, IID uncertainty estimator or native-equivalence claim is introduced.

## API and separation of ownership

`runoff_routing.monte_carlo_frequency` accepts an **immutable, complete sampling-plan allocation** and a compact site-peak ledger. It does not generate stochastic draws, route hydrology, interpret a native report, duplicate the persisted plan schema, write CLI/text files or construct an averaged hydrograph. [#146](https://github.com/Chain-Frost/python-runoff-routing/issues/146) owns the persisted plan and draws; [#149](https://github.com/Chain-Frost/python-runoff-routing/issues/149) maps those draws into existing engine outcomes and an effective-input manifest; C aggregates that ledger. [#148](https://github.com/Chain-Frost/python-runoff-routing/issues/148) owns convergence/replication and [#150](https://github.com/Chain-Frost/python-runoff-routing/issues/150) owns independent statistical/native verification.

`FrequencyScope(plan_id, policy_id, policy_version, scenario_id, duration_minutes, output_site_id)` identifies exactly one scenario, duration and **physical** printed output site for one immutable plan *revision*. The `plan_id` is B's revision identifier, distinct from B's extension-stable `population_id`; any change to the plan's per-stratum allocation produces a new revision. `CurvePopulation` carries that scope, every `StratumWeight(stratum_id, probability_mass, planned_samples)` in original reviewed stratification order, and explicit `UnmodelledTails(lower_rainfall_mass, upper_rainfall_mass, other_mass)`. **All** stratum masses plus tails must sum to one, subject only to `1e-12` absolute binary summation tolerance. Unknown or omitted probability mass is invalid input; it is not normalised away. An unallocated stratum has `planned_samples=0` and retains all its mass as unresolved.

Each `PeakRecord` carries `scope`, `stratum_id`, the original stable `sample_id`, **current revision's** `event_probability_weight`, the original routed `event_id`, `effective_input_id` and a nonnegative peak in `m³/s` only when valid. Results are normalised to `valid | failed | missing | unsupported` **without discarding** their original engine status and diagnostic provenance in E. An absent planned row is also a missing outcome. A successful zero peak is an explicit valid outcome, not a default for an error. Original TP `EventID`, source order, generated event ID and sample ID are separate identities. The caller must ensure `effective_input_id` resolves to the exact actual event and all storm/ARF/loss inputs; C deliberately does not recreate them. Failure records never carry an accepted Q.

A mixed scope/policy version/plan revision, duplicate sample/event identity for one site, unknown stratum, count beyond planned allocations, unexpected weight or invalid success/failure combination raises `FrequencyInputError`. On plan extension E must re-present earlier outcomes against the new full allocation **with recomputed weights**, not append old weighted rows and claim coverage. Multiple sites may share sample IDs because each site has a separate curve.

## Strict weighted exceedance and incomplete mass

For stratum `h` with probability mass `w_h` and **planned** conditional draw count `n_h > 0`, each draw retains `a_hi = w_h/n_h` even if missing. The estimated known strict survival at peak threshold `q` is

\[
S_{\rm known}(q)=\sum_{h:n_h>0}\sum_{i\in\mathrm{valid}(h)}\frac{w_h}{n_h}\,\mathbf{1}(Q_{hi}>q).
\]

The inequality is **`>`**, not `>=`. At `q=Q_i` a tied event is not an exceedance. The implementation uses the planned `n_h`, **never the surviving valid count**, and does not pool samples using equal global weights. `ProbabilityCoverage` reports separate total absolute masses for valid positive, valid zero, failed, missing explicit/absent, unsupported, unallocated strata and each named rainfall tail. `StratumAccounting` retains each planned and observed count and its original per-sample weight. `complete` means there is zero **positive** unresolved mass; zero-weight failed rows still appear in counts.

For any `q >= 0`, with unresolved mass `u`, the supplied logical finite-ledger interval is

\[
S_{\rm known}(q)\le S_{\rm full}(q)\le\min(1,S_{\rm known}(q)+u).
\]

These are **not** statistical confidence intervals; they assume only nonnegative possible flows. For negative `q`, every physical nonnegative flow (including an unresolved one) exceeds the threshold and the logical lower/upper bounds are both 1, while the unresolved **accounting** remains visible. Missing positive mass blocks an accepted full-population point quantile under v1 even if a partial bound is narrow. The module never equates a sparse zero-exceedance count to proof of a zero conditional tail risk.

The `exceedance(q)` result additionally reports the **known exceedance mass contributed by the first and last plan strata**, and that mass divided by known exceedance when the denominator is nonzero. One-stratum populations are counted once, not twice; a zero denominator yields an unavailable share. This is an explicit boundary-stratum contribution, **not** RORBwin's historical 20% warning or a universal accuracy acceptance rule. `estimate()` retains the corresponding boundary evidence at the selected attained peak and whether that peak lies at an empirical minimum or maximum.

## Adopted `monte-carlo-statistics/1` quantile inversion

For **complete probability-one** empirical mass, sort distinct nonnegative *attained* peaks. Aggregate exact ties into one `PeakGroup(Q_j, m_j, F_j)` with absolute mass `m_j` and cumulative nonexceedance mass `F_j`. At requested `AEP = α` strictly inside `(0,1)`, select the **first attained peak** with cumulative mass `F_j >= 1-α`:

\[
q_\alpha=\inf\{q\ge0:S(q)\le\alpha\}.
\]

This is a **discrete generalized inverse**, not midpoint plotting positions, linear/log interpolation or a smoothed frequency curve. No peak outside observed support and no rainfall-tail extrapolation are produced. A valid zero is a genuine atom; selecting it returns `zero_atom`. Exact tied positive peaks are a single cumulative step. The per-target software verdict is `estimated | zero_atom | incomplete` and the separate fields `software_qualification=provisional`, `statistical_qualification=not_assessed` and `native_equivalence=not_assessed` are not elevated by green software tests. A complete finite-ledger step quantile does **not** imply statistical convergence, flood-annual-maximum acceptance or RORBwin parity.

For an incomplete population at `a = 1-α`, let `u` be total unresolved absolute mass and `F_known` the **un-normalised** valid empirical step CDF. Conservative *finite-ledger*, nonnegative-support quantile bounds are

\[
q_{\mathrm{low}}=\begin{cases}0,&a\le u,\\F_{\mathrm{known}}^{-1}(a-u),&a>u,\end{cases}
\qquad q_{\mathrm{up}}=F_{\mathrm{known}}^{-1}(a).
\]

The upper bound is `None`/unbounded if the known cumulative mass cannot reach `a`; the lower can also be unavailable in otherwise inconsistent partial inputs. The point estimate and representative are **absent** whenever unresolved positive mass exists, even when bounds are finite. These bounds describe possible completions of the *planned finite ledger*, not Monte Carlo confidence or population-predictive intervals. There is no IID-quantile interval attached to stratified/dependent draws.

### Exact step-boundary arithmetic correction — 16 November 2026

The adopted `monte-carlo-statistics/1` probability policy is unchanged. The previous
implementation compared binary floating-point `1.0 - AEP` against repeatedly
accumulated `w_h/n_h`, which can select the **next higher attained peak** at an
exact boundary. For 10 equiprobable peaks 0–9 m³/s and AEP 0.1, the correct
noninterpolating value is 8 m³/s (cumulative 9/10), not 9 m³/s. For 20 equal
peaks and AEP 0.95, the correct value is the first, not the second peak.

The fixed decision path uses exact rational fractions of the original planned
stratum probabilities divided by their planned sample counts, aggregated at
tied peaks; AEP is reconstructed from the shortest round-trip decimal
representation of the public float input. Failed/missing/unsupported/unallocated
and tail mass uses the same exact planned scale for incomplete bounds. Float
`PeakGroup` and probability diagnostics remain unchanged for presentation, but
**never determine quantile rank**. No `isclose` tolerance is used to blur real
near-boundary differences, no unresolved mass is renormalised and no flow is
extrapolated. The special complete-population final-step fallback is limited
to original mass sums within the previously documented 1e-12 input roundoff,
and returns only the last *attained* peak.

A subsequent independent PR review identified that accepted Python integer peaks above 2**53 can round when converted to binary64 `PeakGroup.peak_m3_s`, losing their original group key and its probability mass. The public API now **rejects** integer peaks beyond the exactly representable binary64 integer range instead of silently selecting a different quantile. Float peaks remain valid; the response contract already reports binary64 values. This explicit rejection also avoids `math.isfinite` overflow for enormous integers.

New independent literal-rank regression cases cover 10/20 equal samples,
adjacent floating-point AEP values, unequal masses, and incomplete tail bounds.
This corrects software arithmetic, not native RORBwin or engineering acceptance.

## Duration envelopes and actual-event representatives

`build_frequency_curves` creates one curve per scenario/duration/physical site without pooling. `duration_envelope(curves, aep)` then takes the maximum of separately estimated duration quantiles; the **caller must pass curves in requested duration order**. Exact ties select the first **requested** duration and return all exactly tied durations in that same order. Near ties retain the exact numerical gap to the second-largest peak; there is no hidden tolerance. If any requested duration is incomplete, the envelope returns `incomplete`, **no critical-duration point** and only safe finite-ledger bounds where available. This max-of-quantiles is not the quantile of a cross-duration annual maximum without a separately accepted joint duration law.

At a complete attained quantile, the representative is the **actual successful** sample with minimum `|Q_sample-q_alpha|`, with ties resolved lexically by stable `sample_id`, then `event_id`. `RepresentativeEvent` retains the actual original sample/event IDs, stratum, effective-input manifest identity, target, realised peak, signed and absolute mismatch. In the adopted noninterpolating policy the target is attained so at least one representative has zero mismatch; the fields remain explicit to prevent an invented/averaged series being advertised as a replayable simulation. E can use the recorded manifest pointer to replay the underlying full hydrograph. The source original TP ID and loss/ARF values live in that manifest, not a second copy in this statistics module.

## Independent analytical controls

**A's adopted two-stratum mixture:** `w=(0.2,0.8)`, `n=(2,2)`, hence actual draw weights `(0.1,0.1,0.4,0.4)`. Peaks `(0,20,10,10)` m³/s yield **`S(0)=0.9`, `S(10)=0.1`, `S(20)=0`**. At `α=0.2`, `a=0.8` and the first group reaching that mass is peak **10 m³/s**; the representative is one of the actual 10 m³/s events, tie-broken by sample ID. If a 0.4-weight peak fails, `S_full(10)` is bounded **`[0.1, 0.5]`** and no full-population quantile is reported. These are literal authored expectations from the reviewed #145 specification, not software-generated reference results.

**Unequal additional control:** `w=(0.25,0.75)`, `n=(2,2)`, peaks `(10,20,30,40)` m³/s, per-draw weights `(0.125,0.125,0.375,0.375)`. Then **`S(20)=0.75`**, `S(30)=0.375`, and the weighted **`q_0.5=30`** m³/s since the first cumulative peak at/above 0.5 is 30 (cumulative 0.625). A globally unweighted quantile is not an admissible substitute. A separate 3-stratum control checks boundary contributions; tests cover nonnegative zeros, exact ties, affine monotone transforms, sparse extreme AEPs, failed/missing/unsupported and unallocated mass, explicit tails, input permutations and bad identity/revision/weight rejection. The tests check independent literal values, not outputs calculated by the same algorithm to construct fixtures.

## Acceptance boundary

- **Software:** focused source tests and exactly scoped installed-wheel checks must be associated with the published PR head. Ruff/Pyright and full repository tests are separate gates. The method is packaged as pure API; E owns the CLI/text result surface.
- **Statistical:** #145 adopted the public *project* probability and step-quantile rules; #148/#150 still own convergence, finite-sample uncertainty and independent research. No IID confidence estimator is provided here.
- **Native RORBwin equivalence:** **not assessed**, and cannot be inferred from hand-calculated tests. The published table/loss and effective native build remain F's obligations.
- **Engineering:** a finite rainfall support with unmodelled tails is not a complete flood AEP distribution. The code retains those tails and refuses false full-population point estimates.


## Stratified sampling diagnostics and native warning separation — 17 November 2026

**Issue #187:** The 2010 RORB manual's example (pp. 147–148) and a live
RORBwin 6.52 receipt show an asterisk legend involving rainfall-interval
contributions above 20%. **The native numerical rule is NOT established.**
The prior project implementation, which marked a peak when the largest
at-or-above-quantile interval contribution exceeded 20% of the total, was
**falsified** by the authentic 5×5 native output: at positive peaks only
three of the five rainfall divisions contribute at all, so it would
automatically mark all positive peaks despite several unstarred native
values. That method and its native-looking '*' markers are withdrawn.

### 1. Strict total-probability interval audit (not a warning)

ARR Book 4 v4.2 §4.3.3.3 Eq. (4.4.7) defines, for threshold \`q\`,
original interval probability mass \`w_h\` and conditional exceedance
probability \`p_h(q)\`:

\[
\widehat{S}(q)=\sum_h w_h\,\widehat p_h(q),\quad
\widehat p_h(q)=\frac{\#\{i:Q_{hi}>q\}}{n_h}.
\]

This code computes every strict \`Q>q\` stratum contribution from
**the originally planned** \`w_h/n_h\`, and records the interval identity,
exceedance count, absolute contribution, total strict probability and
maximum share (where the denominator is nonzero). This is descriptive
diagnostic evidence only. The maximum contributing share does **not**
directly measure statistical error, and never creates a native \`*\` or
\`!\` warning. The generalised-inverse quantile and separate existing
strict estimator remain unchanged.

### 2. Simultaneous conditional-sampling uncertainty screen

A separate, **conservative** mathematical bound describes sampling
uncertainty for the **fixed versioned stochastic flood surrogate**
*if all outputs for positive-mass strata are independent, identically
distributed conditional on their original rainfall stratum*. It does
**not** address catchment model, calibration, rainfall/loss distribution,
boundary/extrapolation or annual-max-flood assumptions.

For each positive-weight stratum, the finite-sample
Dvoretzky–Kiefer–Wolfowitz (DKW) inequality gives
\`P(sup_q |F_hat_h(q)-F_h(q)|>eps_h) <= 2 exp(-2 n_h eps_h^2)\`.
A union bound across \`H\` positive-weight strata at confidence \`1-delta\`
sets

\[
\varepsilon_h=\min\left(1,
\sqrt{\frac{\log(2H/\delta)}{2n_h}}\right),\qquad
\varepsilon=\min\left(1,\sum_h w_h\varepsilon_h\right).
\]

Thus, under those iid assumptions, a \`(1-delta)\` simultaneous
**absolute exceedance-probability error bound** is \`eps\` for
all fixed or *sample-selected* peak thresholds. It is **not** a
confidence bound on the *peak discharge quantile*, and is not
an independent-seed replication result.

The public method
\`conditional-stratum-dkw-uniform-bonferroni-v1\` defaults to
**95% conditional sampling confidence** and an explicitly
**project-selected 20% relative-AEP screening threshold**:
\`eps/target_AEP > 0.20\` produces \`scientific_sampling_diagnostic.status
= "review"\`; otherwise it is \`"below_screen"\`, **not "reliable"**.
Both parameters are configurable in Python and the CLI
(\`--confidence-level\`, \`--relative-aep-screen\`).
The JSON also reports the maximum original single-draw probability
weight \`max_h(w_h/n_h)\` and its ratio to the target AEP as a
sample-resolution diagnostic. Neither 20% nor 95% establishes
hydrological or numerical engineering acceptance.

**Illustration, not a hydrological result:** a hypothetical
five-stratum sample with \`n_h=5\` and \`w_h=0.2\` has
\`eps=sqrt(ln(200)/10)=0.727895...\` at 95% simultaneous confidence.
This high conservative probability error ceiling shows why **5×5 is
suitable only for execution/formatting tests** and cannot establish
extreme-tail stability. For one complete 1000-event equally weighted
stratum, the illustrative bound is \`sqrt(ln(40)/2000)=0.0429469...\`.
These are mathematical controls, not endorsements of a required
simulation count or real-catchment uncertainty.

If **any** positive-weight event is failed, missing or unsupported,
or if a probability-domain rainfall tail remains unmodelled,
the point flood AEP is \`N/A\` and sampling screen
\`"not_assessed"\`. Known finite-ledger logical bounds remain
in JSON, but are neither statistical confidence limits nor a basis
for rounding away omitted mass. For future sampling policies
without iid within-stratum draws, the DKW model must be replaced or
disabled; applying the bound to the native RORB 5×5 report is
**not supported**, since its stochastic dependence is unverified.

### 3. Native warning and boundary sensitivity remain separate

\`native_interval_warning="not_assessed"\` is always emitted until
the 6.52 native implementation and its rainfall-interval contributions
are independently characterised under #150 F6. No native \`*\`
asterisks are fabricated.

\`boundary_sensitivity="not_assessed"\` and
\`independent_seed_convergence="not_assessed"\` are retained
in the scientific diagnostic because no independently accepted
alternative endpoint extrapolations or replicated-run convergence
study is present. ARR §4.3.3.3 and Nathan & Weinmann (2013)
discuss conditional weighting and the special assumptions for first
and last rainfall intervals. Even an unflagged sampling screen
does not qualify a full-domain flood annual-max AEP or boundary
sensitivity. #148 owns a real-catchment independent-seed study.

### Report format and status

The existing frequency-group CSV remains unchanged. JSON selected-AEP
targets include the strict interval breakdown, sampling confidence,
uniform absolute/relative AEP bound, single-draw resolution and
**separate native-versus-scientific statuses**. Text includes:

- \`No.\`, \`AEP(1inY) = 1/AEP fraction\`, and physical output-site peak;
- \`!\` **only** when the conditional scientific sampling screen
  requests review, subject to its assumptions;
- \`N/A\` when positive probability mass is unresolved, with no point;
- an explicit statement that RORBwin's \`*\` is **not assessed**,
  and an absent \`!\` does **not** imply reliability.

**Sources:**
- [ARR Book 4 v4.2 §4.3.3.3](https://www.arr-software.org/pdfs/ARR_190514_Book4_V4.2.pdf)
- [Nathan & Weinmann (2013), worked stratified example and rainfall endpoint assumptions](https://arr.ga.gov.au/__data/assets/pdf_file/0017/40562/ARR_DiscussionPaper_MonteCarlo.pdf)
- [DKW finite-sample uniform CDF inequality](https://pbreheny.org/621/f12/notes/8-23.pdf)
- [HARC boundary discussion](https://harc.com.au/forums/topic/monte-carlo-simulation-summary-results/)

No raw native RORBwin artefacts are added to the public repository.
