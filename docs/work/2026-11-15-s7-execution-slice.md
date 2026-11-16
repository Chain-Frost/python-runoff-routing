# Issue #149 bounded Monte Carlo execution — 15 November 2026

Baseline: main 0675d75b05dba7728b389fdd8af743060b4469b2.
Branch: feat/mc149-streamed-execution-20261115.
Ownership: S7 E only. Interface proposals posted to issues #146 and #147.

## Implementation

- An explicit, immutable effective-event JSONL boundary around the
  existing #119 project iterator. No second sampler, solver, native
  executable, rainfall depth interpolation or statistical quantile method.
- Source-hash, plan/policy and stratum weight/total mass validation;
  no double ARR ARF or preburst adjustment.
- One prepared-model iterator per execution/resume, compact per-event
  physical-site peaks and typed failures in a resumable JSONL ledger.
- Stale/mixed plan, revised engine code, changed source, duplicate and
  truncated checkpoint safeguards; only an exact source-plan prefix resumes.
- Selective representative-event replay into the ordinary batch
  JSON/CSV/text full hydrograph output using saved effective inputs.

## Evidence status and handoff

Synthetic checks cover direct-runner equivalence, once-only ARF/preburst,
CLI/replay, exact-prefix resume, stale inputs, invalid plan probabilities
and positive-weight failure accounting. Source/wheel quality and
independent review require exact checked revision receipts before
software acceptance. No new native observations or hydrological
acceptance claims were made.

End-to-end B-created persisted plan, C-weighted frequency CLI, an
explicit audited extended-plan computation-reuse/reweighting workflow,
and measured throughput/memory receipt remain pending. These must
not be represented as existing functionality merely because the
bounded execution adapter is present.

## 16 November follow-up — independent #150 review findings

- Review F flagged unauthenticated output-peak mutation and a misleading
  native TP-kind interpretation. Ledger schema v2 now checksum-chains the
  numerical result, physical-site/time evidence and effective-event ID.
  An optional separately retained file SHA-256 verifies against a trusted
  external receipt; a self-checksum alone does **not** establish
  authenticity. A positive result still requires selected full-event replay.
- Documented the strict <75-km2 point/areal choice as **our narrower
  project limitation**, not a required RORBwin restriction. Retain the
  real source TP area/AEP category/region plus B's conditional-bin ID.
  Versioned clamp is rejected under the adopted baseline policy.
- Added regression checks for tampered numeric results, external pinned
  hash mismatch and zero-flow mass. Source/full-wheel quality must be
  attached to the exact new PR revision, not inherited from prior head.
- The earlier exact-head Windows software/source/wheel CI
  [43727500931](https://github.com/Chain-Frost/python-runoff-routing/actions/runs/43727500931)
  **passed** on `6570268430b6d88b4d5a7984e55df43a99adbfdc`.

## B/C integration and explicit extension — 16 November 2026

- B #146 and C #147 are now merged into the separate #151 integration
  branch, and this E PR is based on that exact staging lineage.
- Added actual B plan creation/roundtrip via CLI and B-sampled BoM z-linear
  gross depths, original temporal-pattern identities, one-time published
  ARR ARF and fixed single-ISA IL/CL materialisation. A source-backed
  end-to-end test calls B/E/C on the public synthetic fixtures.
- Added a C-owned strict weighted frequency CLI/report adapter, preserving
  positive-weight failure, zero-flow, unallocated stratum and both tail masses.
  Missing tail mass returns incomplete, not a fabricated flood-frequency AEP.
- Added explicit B plan extension into a new immutable checkpoint with
  parent/population/source checks, full retained effective-sample comparison,
  temporary disk-indexed scalar reuse, recomputed full stratum weights
  and fresh route execution for new events. Tests compare reused and entirely
  rerouted extended ledgers byte-for-byte.
- The Windows quality run on pre-extension combined head
  `16acb03ca149275701446ec13f161ae509d0b9c8` reached **1182 passed / 1 failed**;
  the single failure exposed a nonassociative Decimal sum-vs-product audit
  defect on large synthetic gross depths. The validator now checks exactly
  the maintained #136 increment-distribute, once-ARF, sum operation order.
  This does not relax input or routing tolerances.
- New code still requires an exact-head full Ruff/Pyright/pytest/source
  CMD/installed-wheel CI receipt and proportionate independent #150 review
  before stage merge. Scientific/native compatibility remains pending.

## 16 November E integration-review hardening

- Corrected ambient Decimal-context dependence in source AEP-to-percent
  conversion, effective ARR ARF/rainfall materialisation, source TP
  percentages, probability mass checks and sampled storm/burst IL.
  Existing #136 ARF arithmetic remains pinned to Decimal precision 28;
  B's sampled AEP/stratum arithmetic is pinned to precision 60.
- Added differential tests at caller precisions 12/28/80 and a low-precision
  probability-mass guard, including a complete saved B-to-E text-file
  preparation comparison. Fractional-hour timesteps are accepted only if
  they agree with the integer source duration within 1e-12 minute.
- Reconciled B/C staging integration and corrected malformed literal
  backslash-n paragraphs and the actual effective schema v2 in the E guide.
- Previous exact-head Windows source/installed-wheel job
  [43749746930](https://github.com/Chain-Frost/python-runoff-routing/actions/runs/43749746930)
  passed at `609cf3c5faef47919a90a587e843e3cf08769bfb`. This review-hardening
  revision needs its own CI and proportionate independent review before
  staged merge; it adds no new RORBwin/native scientific acceptance.

## 16 November P2 independent review — exact-context safety

- Independent Codex review of `51e8fbb` identified that `localcontext()`
  with precision alone inherits caller-selected rounding and decimal traps.
  This was a real remaining failure for otherwise unchanged saved requests
  under ROUND_DOWN/ROUND_UP and enabled Inexact trapping.
- Replaced every E-owned ambient Decimal context for source materialisation,
  ARF/burst IL, derived AEP percentage and probability/weight checks with
  explicit `Context` templates. The 28-digit ARR and 60-digit B-derived
  contexts now pin ROUND_HALF_EVEN and standard traps, insulated from the
  caller's current Decimal context.
- Expanded direct E materialisation and saved-request-validation regressions
  to exercise ROUND_DOWN/ROUND_UP and Inexact traps as well as precision.
  These correct the E boundary without altering B's underlying stochastic
  probability law, C's quantile method or the solver.
- Exact-head source, installed-wheel and independent re-review must pass
  before staging #151 merge. Earlier CI and source review remain historical
  evidence, not approval of this further code change.

## 16 November P2 independent review — bind source model before routing

- New exact-head Codex review at `a158e0d` found a real
  **prepare/run model-drift** vulnerability: changing the project's
  fixed kc after preparing B samples allowed a software-complete E
  ledger with a different peak, while ARF could also become stale
  when catchment area changed.
- Effective request schema **v3** now requires
  `preparation_model_sha256`, calculated from the canonical complete
  source `RunModel` serialisation on the *same in-memory model snapshot*
  used for fixed-parameter checking and one-time storm/ARF
  materialisation. Execution compares this against the selected
  project's resolved model before creating or resuming a ledger.
  Its sealed ledger schema advances to **v3** and retains the same
  integrity chain, now with this preparation-model identity.
- A deliberate original model change to either kc or catchment area
  must produce an error without a routed result/ledger; tests cover
  both. Extension also requires identical preparation-model identity.
- Old v2 effective requests/ledgers lack this binding, so they cannot
  be silently promoted: re-prepare immutable B plan draws against
  original sources and run a new v3 ledger. Statistical/native F
  qualifications remain separate from software acceptability.
- Exact-head quality, source CMD regression, isolated installed-wheel
  tests and independent review still determine staging merge readiness.

## 16 November independent follow-up — prevent validation/run model race

- Codex at `b720303` found that the verified E model was not necessarily
  the model routed: `iter_project_events()` separately reloaded the source
  when the event iterator began. A project or source modified immediately
  after the checkpoint was opened could be routed under the old source
  fingerprint.
- Reused the *same validated `LoadedProject` snapshot* for python-cmd
  batch iteration, representative replay and new extended-plan event
  routing by adding a narrow internal-only optional argument to the
  existing shared event runner and materialising no duplicate solver.
  Native rorb-cmd explicitly rejects snapshot-only execution.
- An integration regression mutates project kc immediately after
  `_new_ledger()`. The resulting checkpoint must byte-match a completed
  reference execution of the verified original model, and a subsequent
  run against the altered source must fail before ledger creation.
- The new execution flow holds one immutable source snapshot per run,
  preserving prepared geometry caching and preventing a model read
  between validated provenance and numerical routing.
- Re-review and fresh exact-head source/wheel quality checks remain
  mandatory before merging E into staging #151.
