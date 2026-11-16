# Monte Carlo scientific method and work scopes

## Status and purpose

**Status — 17 November 2026:** The adopted project sampler, weighted frequency layer, prepared execution and selected-AEP reporting are implemented on **draft staging [PR #151](https://github.com/Chain-Frost/python-runoff-routing/pull/151)**. They are unreleased and do not establish RORBwin statistical equivalence. The owner-directed [RORB method and larger-sample comparison work packs](work/2026-11-17-issue9-rorb-statistical-method-scopes.md) reuse #150 for native evidence and #148 for the physical study, with new #189 sampling/preparation, #190 probability/results and #191 canonical comparison scopes. All changes remain on #151; do not merge main.

This document retains the adopted `monte-carlo-statistics/1` method and its source/decision distinctions. A verified native-compatible profile will have a separate identity; it must not reinterpret existing saved plans. Measured convergence and comparison results belong in linked dated research reports.

The product surface remains CLI, Python API and text files. Current development executes explicit events with `python-cmd/cmd-6.44`. The independent `python/engineering-v1` remains the intended future default. The sampling policy has its own identity, separate from the selected event engine.

## Original scoping baseline — 15 November 2026

The following describes the original pre-Monte-Carlo baseline; the current staged software status and follow-on work are above. The inspected baseline was main `0675d75b05dba7728b389fdd8af743060b4469b2`:

- [#119](https://github.com/Chain-Frost/python-runoff-routing/issues/119) supplies the common [explicit-event and batch contract](PROJECT_BATCH_MVP.md), including prepared geometry reuse and per-event outcomes.
- Merged [#136](https://github.com/Chain-Frost/python-runoff-routing/pull/136) supplies [deterministic design rainfall](ARR_DESIGN_BATCH.md). Its source readers, temporal-pattern, ARF and loss/preburst components are reusable.
- The existing deterministic design workflow accepts exact source AEPs of 50%, 20%, 10%, 5%, 2% and 1%. It does not implement arbitrary-AEP sampling/interpolation, probability-tail modelling, a Monte Carlo sampler or weighted frequency analysis.
- [#8](https://github.com/Chain-Frost/python-runoff-routing/issues/8) and [#137](https://github.com/Chain-Frost/python-runoff-routing/issues/137) retain rainfall preparation/qualification work. Full CMD [#5](https://github.com/Chain-Frost/python-runoff-routing/issues/5), advanced capabilities and future RORBwin PAR [#144](https://github.com/Chain-Frost/python-runoff-routing/issues/144) are separate.

Statistical design, analytic controls and the research harness can proceed now. Real-model conclusions require an explicit, qualified rainfall/loss policy and a supported event feature population. They do not require completion of every unrelated advanced capability.

## Primary sources and their limits

The [source register](SOURCES.md) identifies the supplied 2010 RORB manual (R1, chapter 8) and cumulative v6.52 release notes (R3). A historical manual, an advertised version and an observed executable are different evidence identities.

| Source | Relevant evidence | Limit |
| --- | --- | --- |
| [ARR Book 4 v4.2](https://www.arr-software.org/pdfs/ARR_190514_Book4_V4.2.pdf), chapter 4, sections 4.3.2–4.3.3 | Sampling, dependence, stratified probability estimation and indicative counts | General method guidance; not a complete specification of a particular RORBwin executable. |
| [Nathan and Weinmann, 2013](https://arr.ga.gov.au/__data/assets/pdf_file/0017/40562/ARR_DiscussionPaper_MonteCarlo.pdf), sections 3–5 and 7 | Worked probability treatment, losses, duration envelope and diagnostics | Historical discussion paper; distinguish its recommendations from later software behaviour. |
| [ARR Book 5 v4.2](https://www.arr-software.org/pdfs/ARR_190514_Book5_V4.2.pdf), chapter 3, section 3.6 and Table 5.3.13 | Empirical standardised loss distributions and dependence | Edition, probability direction, scale and corrections must be reconciled before adopting a numerical table. |
| [HARC v6.32 announcement](https://harc.com.au/forums/topic/rorbwin-version-6-32/) | Default MC initial-loss distribution changed; accompanying correction notes an error in the referenced ARR table | Does not identify the exact effective table or interpolation in the selected 6.52 binary. |
| [HARC temporal-pattern clarification](https://harc.com.au/forums/topic/selection-of-temporal-patterns/) | MC uses rainfall AEP categories; deterministic selection uses an explicit index | A dated implementation statement, not a new current-build observation. |
| [HARC pervious/impervious loss clarification](https://harc.com.au/forums/topic/monte-carlo-with-arr-2019-impervious-losses/) | Historical MC varied pervious losses and held impervious losses fixed | Do not apply a rural loss distribution indiscriminately to urban surfaces. |
| [HARC frequency-summary discussion](https://harc.com.au/forums/topic/monte-carlo-simulation-summary-results/) | Rainfall input must bracket target probabilities; boundary influence can make reported estimates unreliable | Exact boundary calculations and warning logic still require version-specific evidence. |
| [Dong and Nakayama, 2020](https://web.njit.edu/~marvin/papers/qtut-r2.pdf), sections 4–6 | Quantile error, stratified estimation, variance reduction and confidence intervals | Interval assumptions must match the sampling design and output distribution. |

The [HARC product page](https://harc.com.au/software/rorb/) listed 6.52 at this review. Existing retained source research should be reconciled before new observations; a previously proposed experiment is not an executed validation receipt. No manual or executable is added to the public repository.


## Adopted v1 scientific contract (#145)

**Status (adopted 15 November; implementation status refreshed 17 November 2026):** This section is the versioned **project method** `monte-carlo-statistics/1`, now implemented on draft #151. It supersedes tentative choices in the original scoping text below; it is not an admitted numerical RORBwin 6.52 distribution or an engineering-accepted flood-frequency estimate. “Project decision” identifies a deliberate algorithm choice rather than a proven RORBwin implementation. Source IDs refer to [SOURCES.md](SOURCES.md).

### Target population and dependencies

For each **one scenario, rainfall duration and physical output site**, estimate the distribution of an explicitly routed peak `Q` when the rainfall depth is sampled from a duration-specific *annual-maximum rainfall* distribution and initial loss/temporal pattern obey a declared joint law. This produces a joint-probability **design-event surrogate**; interpreting it as the annual maximum flood AEP requires extra accepted hydrological assumptions. An ensemble conditional on a fixed rainfall AEP is a different quantity. Duration combinations are treated separately; no probability law over rainfall duration is invented [MC1, MC2, R1 chapter 8].

The admitted **first subset** is a supported pervious, single-ISA, single-DESIGN-burst catchment with explicitly varying rainfall depth, a selected eligible temporal-pattern identity, and pervious *storm* initial loss. Continuing/proportional loss, `kc`/`m`, catchment geometry and spatial rainfall pattern are fixed; one approved catchment-wide ARF is derived for each sampled rainfall probability and applied **once**. Multiple physical print sites share event draws but retain their own results. Unsupported urban/impervious/multiple-ISA/storage modes, missing source members, unsupported engines and missing source distributions fail explicitly. Other owners retain [#114–#118](https://github.com/Chain-Frost/python-runoff-routing/issues/114), #8 and #5. R1 `8.1–8.2` supports the historical fixed/stochastic distinction; it does **not** establish current executable behaviour.

The v1 **joint model** is `f(p,L,T)=f_R(p)f(L|p)Pr(T|p,d,region,type)`. A project may select `f(L|p)=f_L` **only after explicitly approving loss/rainfall conditional independence**; no hidden/default correlation assumption. A source-supported conditional loss law supersedes this simplified population only under a new reviewed policy. TP eligibility remains conditioned on the sampled rainfall-AEP category. Distinguish (1) event-to-event variability modelled by the joint law, (2) uncertainty in model/distribution/calibration parameters *not* modelled by v1, and (3) finite Monte Carlo estimation error measured independently under #148. More samples do not resolve (2) [MC1, MC2].

### Distribution and transformation register

| Quantity | Units / range | v1 rule, source and evidence status |
| --- | --- | --- |
| Rainfall exceedance probability `p` | Fraction, `0<p<1` | **Stochastic** on the annual-maximum rainfall exceedance scale; `z=Phi^-1(1-p)` only sets a standard-normal **probability coordinate**, not a Normal rainfall-depth law [MC1, MC2, R1 `8.5`]. |
| Gross design depth `D_d(p)` | mm, finite `>=0` | **Derived** from exact, source-identified duration-specific IFD anchors by z-linear interpolation as specified below. No free depth draw, unsupported conversion or extrapolation. Interpolation is a *project decision*, native parity unknown. |
| Temporal pattern `T` | Exact source ID / finite population | **Stochastic** categorical sample from authentic region/duration/point-or-areal/AEP-bin-eligible members, with explicit probabilities. Original TP label, source order and internal sample ID differ. R3 `1.6` and MC5 describe historical conditional categories; selected native bin edges remain unknown. |
| Standardised pervious loss `L` | Dimensionless, finite `>=0` | **Stochastic** inverse of an accepted **empirical CDF** `F_L(x)=Pr(L<=x)` with a normalised median `L=1`. The source table/version/hash, direction, endpoints and interpolation are mandatory. R1 `8.3` has a historical *exceedance* table; MC3/MC4 describe a corrected later table **not yet admitted** as the current native default. No Normal/lognormal shortcut. |
| Catchment median storm IL `M_s` | mm `>=0` | **Fixed source parameter**; effective **storm** IL `IL_s=M_s*g_d(p)*L`. The adopted default deterministic AEP multiplier `g_d(p)=1`. Any non-constant multiplier requires a separate versioned, approved AEP-dependent policy **before** stochastic scaling (R1 `8.3` describes an older option). |
| Preburst depth and effective burst IL | mm `>=0` | **Derived**, never another independent draw. Supported v1 baseline `PB=0`. An explicitly approved `PB(p,d)` source/policy may instead use `IL_b=IL_s-PB` only when `PB<=IL_s`; by default **reject** negative effective burst loss. Do not silently clamp or subtract preburst twice. Full preburst *temporal* simulation is unsupported by v1 [#136]. |
| Continuing loss / proportional coefficient | IL/CL: mm/hour; proportional: model-specific dimensionless | **Fixed** as applicable in the supported source model. A different fixed loss mode requires its own recognised numerical profile. R1 `8.1–8.2`. |
| ARF | Factor `[0,1]` | **Derived**, not sampled independently: adopted area, duration, sampled `p` and pinned Book 2 regional coefficients via [existing ARF code](../src/runoff_routing/arr_arf.py); apply to raw BoM point depth once. Regional selection and original source hashes persist. No spatial randomisation. |
| Spatial rainfall pattern | Existing source units | **Fixed** per approved scenario (initially uniform once-ARF-adjusted rain on pervious subareas as #136); no random duration-specific pattern. |
| `kc`, `m` and all routing state | Existing S1 units | **Fixed**; independent engine `python-cmd/cmd-6.44` currently selected, `python/engineering-v1` optional intended future default. Sampler cannot call or modify the deterministic numerical kernels. |

**Empirical loss table rule.** Admit a table only with explicit `(F_L,x)` coordinate pairs (or original exceedance `e` with documented `F_L=1-e` conversion), monotonically increasing `F_L` and nondecreasing loss factors, factors `>=0`, original source identity and verified median `x(0.5)=1`. The v1 inverse linearly interpolates the **factor** between bracketing nonexceedance probabilities (not `log(x)` or z); repeated factor values are a legitimate discrete atom. An admissible full-distribution table covers `F_L=0` and `F_L=1` with documented finite-support endpoints or explicit atoms; otherwise no draw outside its published domain. Reject nonmonotone, unbounded, missing, unversioned, physically inadmissible or direction-ambiguous tables. **There is deliberately no built-in RORBwin 6.52 loss table** pending #150's source/erratum and emitted-input review. R1 Table 8-1 and the ARR Table 5.3.13 values must not be silently conflated or copied into an unversioned “RORB default”. A user-supplied, appropriately approved distribution can be sampled independently of exact native equivalence.

**Synthetic loss example (not a published/native table):** `F_L=(0,0.5,1)` with factors `(0,1,2)` gives inverse factor `1.5` for `u_L=0.75`. Median storm IL `20 mm` and `g_d(p)=1` produce `IL_s=30 mm`. An *approved* preburst depth of `6 mm` would give burst IL `24 mm` exactly **once**. If `PB>30 mm`, reject; independently validated experimental clamp policy is not part of v1.

### Probability coordinates, boundary rules, and depth interpolation

1. `p` means **AEP fraction** of annual maximum rainfall. `u_R=1-p` is nonexceedance. Rarer depths have smaller `p` and greater `z=Phi^-1(u_R)`. The use of `Phi` makes no rainfall Normality claim. Original BoM `AEP_PERCENT` labels/lexemes persist; v1 admits *only exact, reviewed AEP-labelled points* to its interpolation table. `ARI` (one-in-Y), `EY` and raw percentage-vs-fraction conversions are not performed implicitly. ``p=1/ARI`` is a conventional annual-probability interpretation; ``p=1-exp(-EY)`` additionally assumes Poisson event occurrence. Either requires a named, audited conversion policy before admission. R3 reports an EY conversion fix, so native conversion must be verified rather than assumed.
2. An admitted table defines a **finite** rainfall-probability interval `0<p_min<p_max<1` with valid duration-specific point depths and any required ARF law. Define `z_min=Phi^-1(1-p_max)` and `z_max=Phi^-1(1-p_min)`. For `H` equal z-width bins choose ``z_j=z_min+j(z_max-z_min)/H``, `p_j=1-Phi(z_j)`. Bin `h` is `p∈[p_{h+1},p_h)` (the final outer boundary may be closed), with actual **probability mass** ``w_h=p_h-p_{h+1}``. Mass comes from `p`, *not* equal z-width. Alternative partitions must carry explicit edges and masses; they are distinct policy choices.
3. **Within-bin decision:** draw an open-unit `V` and set ``p=p_{h+1}+w_h*V``. This is uniform on the correct **conditional probability measure**, not uniform in z or depth; boundary placement and within-bin law are separate decisions. The generated p is strictly internal. Sampling z uniformly inside a z-bin would be a **different conditional distribution**. R1/MC1 give normal-coordinate stratification; exact native within-bin behaviour is unresolved under F3.
4. For valid original IFD anchors `(p_a,D_a)` and `(p_b,D_b)` bracketing the draw, calculate ``D(p)=D_a+(D_b-D_a)(z(p)-z_a)/(z_b-z_a)``. The sampled depth is gross **mm**, nonnegative, finite, and monotone with z. Require source SHA/edition, strictly ordered nonduplicate p anchors and continuous sampled-probability coverage. Match exact anchors exactly. **Reject** source gaps, out-of-range probability/duration, unsupported/unknown unit, nonmonotonic depth or any tail extrapolation. No duration interpolation in v1. This is a project interpolation choice and does not establish RORBwin equivalence.
5. **ARR boundaries:** the currently maintained [ARF implementation](../src/runoff_routing/arr_arf.py) admits 1%–50% AEP without an explicit rare extension and requires durations `>=30 min` without a separate short-duration opt-in, subject to further area restrictions. The v1 MC profile does **not** enable the extrapolation flags. Consequently the currently supported IFD+ARF population is *finite*; its excluded **rare-tail probability** `p_min` and **frequent-tail probability** `1-p_max` are **unmodelled**. Do not assign zero runoff to either tail, extend the IFD by constant depth, extrapolate the ARF or claim that the resulting middle-domain curve is a complete flood AEP. Numerical completion of a modelled subset is separate from tail/engineering acceptance.

**Synthetic IFD control:** `D(50% AEP)=50 mm` and `D(10% AEP)=100 mm`. For `p=0.3`, z is approximately `0.5244`, and `z(0.1)≈1.2816`; z-linear interpolation gives `D(0.3)≈70.46 mm`. A synthetic separately calculated ARF `0.9` would reduce this to approximately `63.41 mm` **once**. These authored values are not valid BoM IFD or ARF acceptance fixtures.

### Temporal-pattern eligibility and categorical inverse

Do not infer a source AEP bin by nearest IFD row. Use exact source duration, region, point/areal form, area bin and approved `p` category edges. Define **increasing-p half-open category edges** `[lo,hi)` (final category includes its rightmost boundary). Each p belongs to exactly one accepted category. All genuine source member IDs in that category are retained; missing, duplicate, wrong-timestep or non-100%-sum members fail. Require explicit nonnegative member weights summing to 1, or an **explicit `equal-members` project choice** giving `1/k` for `k>0`. A categorical uniform draw selects the first cumulative probability greater than the draw; preserve source order and original TP ID independently of internal ordinals. No substitution from a different AEP category or deterministic selection index. R1 `8.4` historically allows nearest-ARI censoring, and R3 `1.6` documents ARR2016 bins; neither proves selected native cutoffs/weights for #150.

### Weighted results and missing-mass requirements (C)

For stratum h with reviewed probability mass `w_h` and `n_h>0` conditional samples, **each** planned event has probability weight ``a_hi=w_h/n_h``. For each fixed site/duration/scenario and a **complete** modelled population, the estimated strict exceedance is

``S(q)=sum_h sum_i a_hi 1(Q_hi>q)``.

Strict `>` (not `>=`) is the v1 choice; tied values are nonexceedances *at their own threshold*. A genuine zero-runoff run is a successful peak of zero with its full weight; failed, unexecuted or unsupported runs have no invented zero Q. All planned mass ``sum_h w_h=p_max-p_min`` must be accounted separately as positive-success, zero-success, failed/unsupported/unexecuted, and rare/frequent **unmodelled tails**. Never renormalise successful results to 1. For any q, the full-domain survival satisfies the conservative bounds ``S_known(q) <= S_full(q) <= min(1,S_known(q)+w_failed+w_unmodelled)``. Missing positive mass blocks a qualified point flood-AEP quantile unless a separately accepted threshold-specific bound is sufficient.

**Quantile decision:** on a **complete probability-one discrete estimate** use the noninterpolating generalized inverse ``q_alpha=inf{q>=0:S(q)<=alpha}`` over attained nonnegative peak values (including zero). If failed/tail mass makes the curve incomplete, output `incomplete` and available exceedance bounds, **not** a plausible extrapolated quantile. Smooth/interpolated quantile curves require a separately versioned and tested policy; they are not v1 and not native-equivalence assumptions. A zero exceedance count in a sparse stratum is not proof that its conditional exceedance probability is zero.

**Synthetic exact mixture:** two strata have `w=(0.2,0.8)` and `n=(2,2)`, hence event weights `(0.1,0.1,0.4,0.4)`. Peaks `(0,20,10,10)` give `S(0)=0.9`, `S(10)=0.1`, `S(20)=0` and `q_0.2=10`. The zero peak has valid probability 0.1. If one weight-0.4 event fails, `S_full(10)∈[0.1,0.5]`; marking it `0` or dividing by surviving mass would be wrong. These are hand-specified analytic tests for #147, not native observations.

**Durations:** estimate each site's curve for **each requested duration** independently. Only afterward report a *design-duration envelope* ``q_env(alpha,site)=max_d q_d(alpha,site)``, with duration ties broken by user-requested duration order then numerical value. Do not call it the probability quantile of the maximum of jointly dependent annual storms (`Pr(max_d Q_d>q)`), for which no cross-duration joint model was adopted. An incomplete requested duration makes the envelope incomplete; a lower-bound diagnostic may be reported but not promoted.

**Representative event:** choose the actual successful sample minimizing `|peak-q_alpha|` for a complete duration/site quantile, tie-breaking by stable lexical sample ID. Record selected sample/event, target, observed peak, signed mismatch, original TP and all effective storm/loss/ARF inputs. A quantile interpolation is **not** a physical hydrograph. This differs from R3's historically documented single-site peak/depth matching; exact native extraction remains #150. Report boundary-stratum contribution diagnostics without turning RORBwin's historical `20%` warning into an adopted universal quality threshold.

### Versioned minimal handoff to B/C/E (#146/#147/#149)

- **Plan owned by B:** `statistical_policy_id`, sampler schema/version, immutable source content hashes/editions, scenario/duration/catchment, valid p support, strata boundaries/masses/allocations, adopted empirical-loss source and median, permitted TP pools/weights/category edges, dependence and preburst/ARF rules, fixed model parameters, root RNG seed/algorithm, plan revision and canonical digest. A plan does not contain routed hydrographs.
- **Sample owned by B:** stable logical `sample_id`, stratum/local index, plan revision, exact planned `w_h/n_h`, sampled p, original raw probability label, gross interpolated depth, original source TP ID and ordinal, standardised IL draw, effective storm/burst IL and specified ARF policy/effective-factor slot, source/policy hashes and materialisable effective-input identity. Sample ID is *not* the user-facing original TP EventID or a native run number. B owns probability-to-depth interpolation; E must **not** reimplement it.
- **Ledger owned by E:** immutable plan revision/hash and logical sample ID plus exact engine/profile, effective prepared-event SHA, execution status, physical output-site IDs, peak/Q or **absent** value, routing/effective source identity and optional full-hydrograph replay pointer. Duplicate and incompatible/mixed plans are rejected. Only the existing #119 runner executes explicit events.
- **Statistics owned by C:** consume immutable planned weights and status-bearing ledger, output distinct duration/site/scenario curves, success/zero/failure/tail mass, strict-exceedance/step-inverse policy, unavailable/complete verdict, boundary diagnostics and selected *actual* sample ID. Reaggregation must not silently use a stale plan revision.

**RNG / replay choice (adopted v1 HMAC contract):** the sampler uses `hmac-sha256-53-v1` with derivation ID `canonical-json-domain-separated-v1`, matching the current #146 source implementation and the originally independently reviewed #145 algorithm. The unsigned **64-bit** root seed `0..2^64-1` is encoded in **eight big-endian bytes** as the HMAC-SHA256 key.

For each local draw the exact HMAC message is *UTF-8 canonical JSON*: sorted keys, compact separators, `ensure_ascii=False`, `allow_nan=False`. Required fields: `namespace="python-runoff-routing/mc-sampler"`, `version=1`, full immutable `population_id` (SHA-256 of the source/policy sampling spec excluding only stratum counts), `policy` object, `sources` object, `scenario_id`, `duration_min`, `stratum_id`, original string `aep_lower` and `aep_upper`, zero-based `index`, and distinct `purpose` (`rainfall`, `tp`, `loss`). The JSON object is serialized directly; do not add sample count, worker/chunk order, plan revision or wall-clock fields. From the high 53 bits `k` of the HMAC digest's first eight bytes derive open-uniform `U=(2k+1)/2^54`. Changed source/policy/stratum boundaries create a new population; allocation extension preserves prior logical IDs/draws but all affected sample weights must be recalculated. Persist effective values for RNG-free replay. This stream is reproducible; it is not proven identical to RORBwin.

**Fixed HMAC stream test vector (synthetic identity, not a valid full plan):** Use root seed `42`; `population_id` equal to **64 ASCII zeroes**; `policy={"id":"monte-carlo-statistics","version":"1","status":"reviewed"}`; `sources` object with `ifd` equal to **64 ASCII ones** and `temporal_patterns` equal to **64 ASCII twos**; `scenario_id="synthetic"`, `duration_min=60`, `stratum_id="bin0"`, `aep_lower="0.1"`, `aep_upper="0.5"`, `index=0`. The only variable is the draw `purpose`.

| Purpose | First 53 digest bits (`k`) | Exact `U=(2k+1)/2^54` |
| --- | ---: | --- |
| `rainfall` | `3576096940182924` | `7152193880365849/18014398509481984` |
| `tp` | `3662531502952859` | `7325063005905719/18014398509481984` |
| `loss` | `3624662676722737` | `7249325353445475/18014398509481984` |

The sampler owner must also pin a test vector based on a real, canonical **plan-derived** `population_id`. These vectors are software-stream controls, not native Monte Carlo results.
**Plan extension:** expanding an unchanged stratum preserves prior draws and IDs, but creates a **new immutable plan revision**. Recompute **every** weight in that stratum as `w_h/n_h(new)`, including old results; reaggregate all relevant existing computed events. Reject mixed old/new weights and duplicate outcomes. Replay existing samples from recorded effective inputs, independent of worker count, traversal order, chunking and selected deterministic engine. The execution layer must never sample inside a numerical solver.

**Testable controls:** source/gross-depth monotonicity and AEP/EY rejection, z-edge and p-uniform interval mass, empirical IL direction/median/endpoint/atom and out-of-support, TP category and conditional member identity, preburst excess rejection/one-ARF transformation, unchanged CL/`kc`/`m`, deterministic stream independence and extension reweighting, weighted/tied/zero/failure/tail analytical controls, incomplete duration envelope and representative replay. Independently review probability direction, total mass, dependence, tail policy and **estimand**. Use ordinary repository link/claim checks for this docs-only PR, not an unrelated numerical suite.

### Open version-specific scientific questions for #150

| ID | Smallest bounded check | Exact claim it blocks |
| --- | --- | --- |
| F1 | Reconcile ARR Book 5 v4.2/any erratum, HARC v6.32 correction and the selected executable's **effective emitted** pervious loss-factor table, probability direction, median scaling, interpolation and endpoints. | “RORBwin 6.52 default loss distribution is numerically reproduced.” |
| F2 | Recover source AEP bins, native edge ownership, point/areal pattern membership, weights and any optional nearest-ARI censoring using original sources and limited adjacent-bin native runs. | “Same TP identities/conditional law as native.” |
| F3 | Check actual rainfall-stratum edges, within-bin transform, arbitrary-p IFD interpolation, coverage and effective settings saved in/reloaded from GUI PAR. Inspect **emitted samples**, not screenshots alone. | “Same sampled rain probability/depth as current native.” |
| F4 | Trace actual AEP-dependent IL factor, storm-vs-burst loss, preburst, once-applied ARF and spatial pattern on selected emitted samples. | “Matched native effective hydrological inputs.” |
| F5 | Establish any exposed seed/RNG algorithm/stream/replay behaviour or mark **unobservable**, without prohibited decompilation/Ghidra. | “Exact native seeded stream parity.” |
| F6 | Bounded missing/failed/zero-runoff runs, boundary reliability flag, frequency inversion, duration selection, single-site representative matching and nonconvergent extraction behaviour; preserve source/version. | “Native warnings, curve interpolation and extraction parity.” |

**Evidence levels and review gates:** R1 is the **2010 historical manual**, R3 cumulative release notes describe changes since 6.30, HARC MC4 corrects a historical table reference, and MC6 describes real but **dated** boundary/extraction concerns; none is fresh executable evidence. The earlier **14-test handoff was proposed, not performed**. Finish (i) adopted specification/independent arithmetic review, (ii) B/C sample/weight source and wheel verification, (iii) E execution/persistence identity, (iv) #148 independent-seed precision/coverage, (v) #150 separate native-input and aggregate matching, (vi) engineering suitability and **full probability-tail** acceptance. No native observation, decompilation, new public manual or binary custody transfer occurs under #145. Keep #9 open.


## Supporting initial source/scope summary (non-normative)

The original #151 planning tables, research budget and dependencies remain below for historical context. In any conflict, the decisions in `monte-carlo-statistics/1` above control.

### Quantities and proposed initial subset

The initial method concerns event-to-event hydrological variability and its integration into flood-frequency estimates. Monte Carlo sampling error is a separate numerical uncertainty. Uncertainty in calibration parameters or the assumed distribution is a further layer; more samples do not remove it.

| Quantity | Proposed baseline treatment | Decision/evidence required |
| --- | --- | --- |
| Rainfall probability and depth | Stratified probability sampling, mapped through a depth-frequency relationship | Probability convention, range, within-bin draw, interpolation and tails. |
| Temporal pattern | Draw an identified member of the eligible discrete population | Conditional duration/AEP/region population, weights, edges and original source identity. |
| Pervious initial loss | Sample the adopted empirical standardised storm-loss relationship, scaled by the adopted catchment median storm initial loss | Exact table/version, exceedance direction, scale, endpoints and interpolation. |
| Preburst and effective burst loss | Explicit configured transformation under one adopted policy; no independent preburst draw | Storm versus burst loss, dependence and no double subtraction. |
| Continuing/proportional loss | Fixed for the initial scope unless the selected reference explicitly requires otherwise | A deterministic AEP adjustment, if adopted, is distinct from an independent stochastic draw. |
| Routing `kc` and `m` | Fixed | Parameter-uncertainty analysis is a separate model, not an implicit addition. |
| ARF | Derive from the adopted catchment-area, duration and sampled-probability policy | Apply ARF once; retain the existing catchment-wide treatment. |
| Spatial pattern | Fixed for the initial subset | Any stochastic spatial pattern requires a separately adopted source/dependence model. |
| Duration | Separate simulation and frequency result for each configured duration | An explicit envelope rule; no invented duration probability weights. |
| Impervious, multiple-ISA and advanced features | Outside the first pervious single-ISA population unless separately supported and qualified | Existing feature owners retain their scope. |

Uniform spacing on a standard-normal probability coordinate does not imply a Normal rainfall-depth distribution [ARR Book 4, section 4.3.3.3]. Uniform draws in depth, cumulative probability and transformed-normal coordinate are also different procedures. The within-bin rule must be specified, not inferred from how boundaries are spaced.

Marginal distributions alone do not define a joint distribution. Each independence assumption or conditional rule must be recorded. For example, temporal-pattern eligibility can depend on sampled rainfall probability; storm loss and preburst must not be combined using incompatible interpretations.

## Statistical estimand and weighting

For a fixed scenario, duration and output location, let stratum $h$ have rainfall probability mass $w_h$, with $n_h$ samples drawn from its adopted conditional distribution. Let $Q_{hi}$ be the resulting peak. For complete modelled strata:

$
\widehat S(q)=\widehat{\Pr}(Q>q)
=\sum_h w_h\,\frac{1}{n_h}\sum_{i=1}^{n_h}\mathbf 1(Q_{hi}>q).
$

Each sample therefore contributes weight $w_h/n_h$. Unequal rainfall-stratum probabilities cannot be replaced by an unweighted percentile of all event peaks. Invert the weighted curve using an explicit quantile, tie and interpolation rule. Calling its result a flood AEP additionally depends on the adopted rainfall-probability and event-model assumptions; a conditional ensemble at one rainfall AEP is a different estimand [Nathan and Weinmann, sections 4.3–4.4].

Complete accounting requires:

- Modelled interior strata plus explicit upper/lower-tail treatment. If the domain is incomplete, report the missing mass and supported bounds; do not renormalise it away.
- A valid zero-runoff event remains in the probability calculation.
- A failed event retains its planned identity and probability weight. Missing positive-weight results cannot disappear from the denominator or become valid zeros.
- A reported point estimate must meet the adopted completeness rule. Otherwise return incomplete/unavailable or justified bounds.
- Separate curves by physical site, duration and scenario. The duration envelope is formed afterward under the selected method; durations are not pooled as independent samples.
- Representative hydrographs identify actual sampled events and their effective inputs. Report the difference between the selected event peak and the target quantile. An interpolated quantile does not itself supply a simulated hydrograph.

Scope C must independently verify unequal-weight mixtures, monotone transformations, ties, zero-flow atoms, failures and tails. Sparse strata and zero observed exceedances must not be mistaken for proof of zero uncertainty.

## Reproducibility and execution contract

A sample plan must record policy/schema version, source hashes, probability support, stratum bounds/mass/allocation, duration/scenario, stable sample ID, selected TP source ID, primitive and effective values, fixed parameters, RNG algorithm/version and stream/seed derivation. Persisted effective values enable replay without sampling again. Resuming an unchanged plan differs from extending it. An extension may preserve earlier draws and logical IDs, but creates a new immutable plan revision and recomputes every affected stratum weight using its new sample count. Reject mixed old/new weights; extended-plan reaggregation must match a fresh full-plan calculation.

Keep the transformations explicit:

1. Generate the sample plan under the selected probability model.
2. Materialise exact rainfall and parameter values under the selected preparation policy. Scope B owns probability-to-depth/IFD interpolation; E consumes the sampled depth and owns explicit-storm/ARF/preburst materialisation.
3. Execute ordinary deterministic events through `ProjectEvent` and `iter_project_events`.
4. Associate results and statuses with their planned weights, then calculate frequency outputs.

The same materialised event can later be evaluated using another supported engine. That comparison changes the event engine, not the stochastic input population. Matching an integer seed across different RNG implementations does not establish matching draws.

Use prepared catchment geometry with fresh loss/routing state for each event. The current request-file array loader and materialised batch outcomes need a bounded adapter for large plans: stream or chunk plans/results, validate checkpoint identities and reject duplicate or mixed-policy resumes. Compact peak/result ledgers can support frequency calculations; full hydrographs may be retained selectively or replayed from saved events. No new GUI or general execution framework is needed.

The [rerunnable convergence research under #148](research/MONTE_CARLO_CONVERGENCE.md) includes both a high-variability counterexample for which 1,000 simulations are inadequate and a low-variability nondegenerate synthetic population where 1,000 meets a proposed whole-run precision criterion. This does not establish a universal minimum, RORBwin compatibility or real-catchment statistical acceptance.

## Research question: is 1,000 enough?

There is no accepted universal simulation count. ARR Book 4 section 4.3.3.3 gives indicative guidance of about 50 probability intervals and 50–200 simulations per interval, depending on input variability. This corresponds to 2,500–10,000 event evaluations per duration, not a guarantee and not proof of a current RORBwin default.

The proposed pilot below deliberately includes smaller budgets so the research can determine where 1,000 is adequate.

| Samples per stratum | Strata | Events per duration/scenario |
| ---: | ---: | ---: |
| 5 | 50 | 250 |
| 10 | 50 | 500 |
| 20 | 50 | 1,000 |
| 50 | 50 | 2,500 |
| 100 | 50 | 5,000 |
| 200 | 50 | 10,000 |

These are **proposed study settings**. Begin with a small timing pilot, then record the total event budget and wall-time cap before larger catchment runs. Extend only to resolve a remaining question. Count replications and durations explicitly; multiple output sites from one routed event do not multiply event evaluations.

Use approximately 30 independent replications to locate promising budgets, then independently confirm any proposed acceptance boundary. Measure variability of an individual production run, not merely the standard error of the average of all research runs.

For each site/AEP/duration and the final envelope, retain:

- Individual replication estimates, between-run SD/CV and run-to-run spread with its uncertainty.
- Error against analytical truth or an independently established higher-precision reference.
- Remaining reference uncertainty, failure/missing mass and probability-boundary diagnostics.
- Critical-duration selection frequency, including near-ties.
- Event evaluations, elapsed time and memory.

A high-count simulation is a reference estimate, not ground truth. Compare separate bin-allocation/refinement and rainfall-endpoint/interpolation sensitivity. Correct conditional sampling can be unbiased for any valid partition; any approximation error must be traced to the actual algorithm rather than assumed to arise from bin count alone.

Evaluate 1%, 2% and 5% relative precision bands with a declared absolute tolerance near zero. These are research options, **not ARR standards or adopted engineering tolerances**. Define whole-result success if claiming that all required outputs are stable, and quantify uncertainty in its observed success rate. Before labelling a budget adequate, declare the required pass probability and confidence level. An illustrative research target is at least 95% of independent runs passing, supported by a one-sided 95% lower confidence bound; this remains a proposed project choice. Alternatively report pass rates and uncertainty without an adopted adequacy verdict. Thirty pilot replications do not establish that reliability claim. Use predefined study stages and independent confirmation rather than repeatedly testing an ordinary confidence interval until it passes.

Variance reduction is a later research comparison: balanced treatment of finite TP populations, revised allocation, Latin hypercube or randomized quasi-Monte Carlo. Compare bias, uncertainty and cost under the same intended joint distribution. More resampling from ten patterns does not enlarge the underlying hydrological evidence base. Common random numbers can aid scenario comparisons; independent replications are still needed to assess between-run stability.

The existing performance target of 1,000 events under ten seconds is distinct from statistical sufficiency. No new performance claim or benchmark was produced by this scoping work.

## Native inspection and compatibility

A small, version-pinned observation of the existing RORBwin interface and emitted MC records is useful where a named question remains: loss-table values/interpolation, TP edges, effective preburst/ARF settings, exposed RNG controls, probability boundaries, failure handling or representative extraction. Capture the settings and actual effective inputs/outputs; screenshots alone do not prove semantics.

The [HARC extraction discussion](https://harc.com.au/forums/topic/extracting-mc-hydrographs/) describes a historical failure when a sampled routing run does not converge and recommends reconstructing individual events. It is a test lead, not proof that all selected-build scenarios share the defect.

No Ghidra/decompilation work is scheduled. Current [AGENTS.md](../AGENTS.md) prohibits decompilation. Documentation, retained evidence and ordinary controlled observations come first. An unresolved exact-stream or internal-rule question must name the claim it blocks and a proposed bounded follow-up; it need not block an explicitly specified independent sampler.

Preserve `cmd-6.44` and RORBwin profiles separately. Where effective native draws are recoverable, compare identical events. Otherwise evaluate aggregate statistical agreement with suitable uncertainty and label it accordingly. A routing difference must be resolved or isolated before attributing aggregate differences to the sampler.

Fresh native observations require a finite experiment plan under existing local permissions. Reuse retained private evidence under its existing permission. New unapproved raw captures, screenshots and traces remain local outside Git until the applicable separate custody/publication approval exists; this is not permission to expand raw evidence in the private repository. Public CMD-fixture approval does not automatically authorise RORBwin-data transfer.

## Work allocation and completion

| Scope | Tracker | Current disposition |
| --- | --- | --- |
| A — statistical specification | [#145](https://github.com/Chain-Frost/python-runoff-routing/issues/145) | Completed project-method specification; retain its identity. |
| B — persisted plans and sampler | [#146](https://github.com/Chain-Frost/python-runoff-routing/issues/146) | Completed staged software; new native-profile sampling/preparation is #189. |
| C — weighted frequency/results | [#147](https://github.com/Chain-Frost/python-runoff-routing/issues/147) | Completed project estimator; native probability/result-policy work is #190. |
| D — simulation-budget research | [#148](https://github.com/Chain-Frost/python-runoff-routing/issues/148) | Analytical studies completed; physical-catchment/native comparison and production stability remain open. |
| E — execution/CLI | [#149](https://github.com/Chain-Frost/python-runoff-routing/issues/149) | Completed staged execution; reuse it in #189/#191 without another runner. |
| F — native/statistical qualification | [#150](https://github.com/Chain-Frost/python-runoff-routing/issues/150) | Open: native method specification, bounded observations and independent final assessment. |
| Reporting | [#187](https://github.com/Chain-Frost/python-runoff-routing/issues/187) | Completed selected-AEP reporting; native warning remains not assessed. |
| Comparison adapter | [#191](https://github.com/Chain-Frost/python-runoff-routing/issues/191) | New canonical native-record and comparison interface; reuse ryan-tools. |

The [17 November work plan](work/2026-11-17-issue9-rorb-statistical-method-scopes.md) defines the current five packs, dependency order, conditional Ghidra decision and larger-sample experimental requirements.

The issue bodies contain the authoritative handoff prompts and acceptance criteria. This is not a second capability matrix. Keep [#9](https://github.com/Chain-Frost/python-runoff-routing/issues/9) open until the selected implementation, statistical, effective-input, native and reproducibility gates are supported by independent evidence. Software implementation and source documentation may finish earlier and must be labelled accordingly.
