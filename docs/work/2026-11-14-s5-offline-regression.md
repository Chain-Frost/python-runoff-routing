# S5 — multi-case offline native regression suite

**Updated:** 2026-11-14. **Owner:** S5 implementation branch. **Branch:** `feat/s5-offline-regression-suite-20261114` from main `e00e34d8`. **Status:** draft public work, not merged or accepted. **Review:** on the draft PR/Windows quality and private replay.

## Scope and dependency use

Extend S5 JSON project execution and S0/S1/S2 native diagnostics, without second parser/solver. A versioned multi-event source-pinned JSON suite classifies every declared case `computed/pass`, `computed/fail`, `unsupported`, `incomplete` or `invalid`. Source verification, Python computation, original printed parity and native acceptance are independent statuses.

S0 `verify_manifest` and exact native executable/manifest/output hashes, S1 typed model and native output inspector, S2 `run_model`, frozen printed-precision parity and independent native-inclusive versus physical-trapezoid volume audits remain authoritative. Call one computation per supported project, not one per print column. Retain control-vector order, raw CMD 1-based increment/time tokens, peak magnitude/index and full-horizon integrals; no phase shift, tolerance fitting, rainfall-excess invention or ARR generation. Print-point maps are **caller asserted**, not independently location verified.

The S1 output parser captures the original native `Volume,m³` string only for a unique single-column report; absence/ambiguity remains unavailable. A printed-volume consistency check is reporting evidence only, not a hydrological balance or solver-acceptance gate.

## Previous real-native evidence — unchanged

The separately verified five-subarea RORB_CMD capture used 201 authentic output ordinates. **11/201 match the frozen printed allowance**; first failure index **11**, maximum absolute error **0.22707848694007993 m³/s**. Windows/installed-wheel offline source checks passed in the earlier S5-P2 work, but numerical compatibility failed. Earlier private 65-case work recorded **36 computed numerical failures** and **29 unsupported/uncomputed profiles**. The current suite has **not** independently re-executed that 65-case campaign, and no private bytes were copied to the public repo.

## Quality evidence and outstanding gates

- **PASS** on exact implementation head `6e97f74d90bcfcdab770c663777875bc84c4e510`: [Windows quality run #43505358206](https://github.com/Chain-Frost/python-runoff-routing/actions/runs/43505358206), **Python 3.14.10**; repository hygiene **108 files, 0 errors**; **Ruff 0.16.6 lint/format PASS**; strict **Pyright 0 errors/0 warnings**; **390 public synthetic tests PASS**; production wheel **built** and **installed/imported outside checkout**. This is software validation only, not native numerical acceptance.
- Private 65-case suite: **NOT RUN** against this branch/installed wheel in the present environment; requires isolated private Windows source access, explicitly asserted print mappings and original corpus hash/index audit.
- Native process launches: **NONE authorised or attempted** in this task. Original tolerances, goldens, ARR inputs, compatibility profiles and strict S2 backend unchanged.
- Native numerical acceptance: **unassessed**, while the known CMD failure remains **FAIL**. S2 [#4](https://github.com/Chain-Frost/python-runoff-routing/issues/4) and S5 [#7](https://github.com/Chain-Frost/python-runoff-routing/issues/7) stay open.

**Next action:** independently review the draft PR and perform the **offline-only private 65-case read-only replay** against the exact installed wheel, then publish **sanitised classifications only**. Keep original S0 S1 clocks and frozen print budgets.

## Private Windows corpus handoff — offline only

1. Use an isolated checkout of `Chain-Frost/runoff-routing-investigations` and the public PR's **built/installed wheel**. Ensure imports resolve to installed site-packages outside the public source checkout; do not call RORB_CMD or RORBwin.
2. Before calculations, verify every entry in `tests/fixtures/rorb/native-corpus/FILE_INDEX.json` against its original `sha256` and `size_bytes`, and independently verify the 65 `catalogue.json` case manifests and input fingerprints. Reuse the existing private `repo-scripts/s2_offline_campaign.py` hash/index audit; do not change the original catalogue, source manifests, original native outputs or tolerances.
3. Stage only the necessary **verified byte copies** into a newly created, ignored `.local/s5-offline-<unique-run-id>` folder, with a separate schema-1 file-backed JSON `Project` per supported original CMD case. Construct a versioned S5 suite manifest with **all 65 declared case IDs**; set missing or nonrepresentable project/native entries to `null` so they are explicitly `incomplete`. Do not forge a usable S1 project for captured GUI/ARR profiles.
4. Supply each `print_1`→`HydNNN` mapping in an independently reviewed private mapping register. A manually entered or single-site positional mapping remains `caller_asserted` and must not be described as independently verified. Reject ambiguous mappings.
5. Run `py -3.14 -m runoff_routing.project_regression <suite.json> <new-results.json> <new-ordinates.csv>` from an installed-wheel environment. Verify 65 output classifications, frozen print budget, complete native sample horizons, unchanged raw CMD times, manifest/output/engine SHA-256 and physical volume differences. Compare with earlier 36 computed failures/29 other or uncomputed cases; any changed distribution requires a separately explained cause.
6. Retain case-level private hashes and full CSVs in ignored local storage; report only sanitized classifications and quality metadata in the public PR. Never commit private corpus bytes, publish raw native files, run a native engine, or promote a passing diagnostic to S2/S5 numerical acceptance.

## Follow-up: local Windows installed-wheel replay, 2026-11-14

**Diagnostic replay executed; acceptance incomplete.** Public source revision
`734b665de395aa1afc0890b4f0b7c545d4e84d96` was checked out separately and built into a wheel
with SHA-256 `a7fd01834cd1f3e1fdbf0b50fd6e165aac7c9455446ff674e91e963d59c78649`.
Windows 10 / Python **3.14.6** used a fresh virtual environment and isolated-mode Python;
imports resolved to that environment's installed `site-packages`, outside the public source checkout.
This local interpreter differs from hosted CI's Python 3.14.10.

The isolated private checkout was `56f1eec`. All **1,026 FILE_INDEX entries** verified before and after
execution, and all 65 catalogue manifest/input fingerprints were independently rechecked using the
existing private audit functions. Original corpus, manifests, outputs and tolerances were unchanged.
Private staged byte copies, the suite, mapping register, full JSON and ordinate CSV remain ignored/local.

The new S5 suite declared all **65** cases and returned **35 computed/fail, 1 invalid, 29 incomplete**;
there were **zero computed passes**. The 29 incomplete entries have no representable project in this
adapter and retain their original private dispositions: 25 unreviewed, 3 expected native failures and
1 incomplete/invalid capture. These are adapter dispositions, not newly invalidated native inputs.

The difference from the historical 36 computed failures is explained: one original storm/effective
input uses **0.125 hours**, while its native output header prints **0.12 hours**. The new reviewer
requires exact header/input timestep equality and rejects that case before computation. No timestep,
tolerance or original native time token was changed to bypass this guard. Review of printed timestep
precision is a separate follow-up.

Re-executing the existing private campaign API against the **same installed public wheel** reproduced
**36 compared strict numerical failures, 25 unreviewed, 3 expected failures and 1 invalid/incomplete**.
All four separately retained narrow linear controls passed their existing precision/balance checks.
The original baseline remains **11/201**, first mismatch index **11**, maximum absolute error
**0.22707848694007993 m3/s**.

For the 36 representable projects, source code-7 labels and native code-7 echoes agree. This cross-check
does **not** independently establish physical print-location identity or the Hyd-column association:
all mappings remain **caller_asserted**, including blank-label single-site cases. The requested
independently reviewed physical mapping acceptance gate therefore remains **outstanding**.

No new native process was launched. No numerical acceptance, merge, release, publication, golden
update or tolerance adjustment occurred. Earlier NOT RUN statements above describe the original PR
handoff, superseded only by this explicitly limited diagnostic replay.

**Next action:** independently review physical print mappings and assess the rounded native timestep
header guard, then rerun the affected exact-wheel suite. S2 #4 and S5 #7 remain open.

## Independent follow-up — native reported-timestep precision

A narrowly scoped successor branch `fix/s5-native-printed-timestep-20261114`
guards the known 0.125-hour source / 0.12-hour printed-header discrepancy
without loosening numerical discharge budgets or altering source effective
settings. It checks the printed header at half-last-place resolution and
requires **every original CMD Inc/Time token** to represent
`Inc * exact_source_timestep` within that token's own printed resolution.
A disagreement beyond either printed allowance fails closed. Synthetic
tests cover both rounding ties, a false-header-precision case and a
hash-consistent but inconsistent native raw-clock case.

This is a **candidate source correction**, not evidence of a new private
installed-wheel replay or numerical acceptance. The previous 35 computed
failures, one rejected header and 29 incomplete classifications remain
historical facts from the earlier wheel. Before acceptance, run exact-head
Windows/Python 3.14 non-native quality and repeat a read-only private
65-case replay with independently reviewed print mappings; retain any
unexpected difference as a failure pending independent explanation.

## Current-head independent Windows offline replay

**Updated:** 2026-11-14. **Owner:** local validation agent.
**Selected implementation:** `b23f7338f276460b35514ba2f438150044454039` (PR #58 after #66).
**Delivery branch:** `audit/s5-current-corpus-20261114`; documentation only.

Windows **10.0.19045**, Python **3.14.6**, package **0.0.0.dev0**. Built wheel SHA-256:
`4e967b7d29d7889f6da5b5afbc7faa08fbbcfa367fb3e3cb4a1600c3d47ac238`.
A fresh private virtual environment outside the public checkout imported installed
`env/Lib/site-packages/runoff_routing/__init__.py`, using isolated-mode Python.

All **1,026** indexed original files passed byte-size/SHA-256 verification before and after replay;
all **65** catalogue manifest/input fingerprints passed the existing independent private audit.
Every original case ID appears exactly once. The installed-wheel API and CLI returned
**36 computed/fail, 29 incomplete, zero computed/pass, zero unsupported and zero invalid**.
CLI exit **1** correctly reports failed/incomplete diagnostics. The 29 incomplete projects retain
**25 unreviewed GUI profiles, three expected native failures and one incomplete native capture**;
these are coverage limitations, not passing comparisons or newly invalidated original inputs.

The same wheel's existing private campaign reproduced **36 compared failures** and the same
29 other dispositions; **all 16,836 predictions and original native discharge/increment/time tokens
matched exactly** between APIs. Four separately retained linear controls passed. The sole change
from the earlier S5 replay is one rounded-timestep-header rejection becoming a computed failure
after #66. No numerical computation, source timestep, frozen allowance or golden was changed.
The original baseline still matches **11/201**, first failure **11**, maximum absolute error
**0.22707848694007993 m3/s**. Private reports retain all 65 rows, engine/executable identities,
effective inputs, source/control order, peak differences and separate volume diagnostics.

Quality on the selected implementation: repository hygiene **108 files/0 errors**;
**Ruff 0.16.6** lint and format pass (**98 files**); strict **Pyright 1.1.414**
**0 errors/0 warnings**; source and fresh installed-wheel runs each **393 passed, one skipped**
with **pytest 9.1.1**. The skip is Windows file-symlink creation unavailable, so that environment
gate remains unexecuted. **Eight private campaign contract tests passed**. Build frontend
**1.6.1**, isolated setuptools **84.2.1**. The first default-interpreter test invocation hit six
collection errors through an older global editable checkout; explicitly selecting this source
for source tests, then separately testing the clean installed wheel, removed that contamination.
Existing synthetic negatives passed; an installed-wheel duplicate-case probe also rejected the
duplicate and retained the incomplete entry. Complete corpus membership was checked independently
against the catalogue; schema v1 does not itself know an external expected-case registry.

All **36** computed print mappings remain **caller asserted**. Source/native code-7 echo agreement
does not prove independent physical location or Hyd-column identity. Rainfall-excess and water
balance remain unassessed without independent source/time semantics. Native numerical equivalence
remains **unaccepted**. No RORB process was launched or original evidence modified.

**Review recommendation:** ready for software review with these explicit limitations; not ready
for numerical acceptance. PR #58 currently conflicts with main; its exact head has no hosted check
attached. #66's successful Windows run is on another commit with the same tree, not exact-head CI.
Resolve integration separately and repeat affected checks. Independently establish physical print
mapping, address the 29 coverage gaps and investigate the 36 numerical failures. S2 #4 and S5 #7
remain open. No merge, release, publication, new automation or native execution is authorised.

### Refreshed PR head after concurrent main reconciliation

The PR owner advanced #58 during final publication checks. The preceding `b23f7338` evidence is
retained as an earlier snapshot; its conflict/hosted-status observations are superseded here.
**Final selected public revision: `8d6b1b8c60d2920fe163fa20e27aac08685aabd3`.**
An isolated checkout, newly built wheel and another fresh out-of-tree virtual environment were used.
**Wheel SHA-256: `2f6a104665e3a27c8691e0e51667a6928157ab46a7e4d529a42fc30b530208c3`.**
Windows/Python/tool versions remain as above. Installed imports resolve to the new environment's
`env/Lib/site-packages/runoff_routing/__init__.py`, using isolated-mode Python.

Exact refreshed-head checks: hygiene **147 files/0 errors**; Ruff **0.16.6** lint/format pass
(**133 files**); strict Pyright **0 errors/0 warnings**; source and installed-wheel tests each
**670 passed, one skipped** (same unavailable Windows file symlink); eight private contracts pass.
[Exact-head hosted Windows quality](https://github.com/Chain-Frost/python-runoff-routing/actions/runs/43551785615)
also passed. The refreshed PR is **mergeable** at this check, without any merge by this validation task.

The full corpus was independently re-audited and replayed with the new installed wheel:
**36 computed/fail, 29 incomplete; zero pass/unsupported/invalid**. All **1,026** indexed files
verified again before and after. All **16,836** shared predictions and original tokens reproduce the
fresh prior API; the complete S5 result JSON and ordinate CSV are **byte-identical** to the preceding
implementation snapshot. Thus the concurrent main reconciliation introduced no observed numerical
or classification change. Across computed cases **1,498/16,836** ordinates meet the unchanged budget;
maximum absolute error **0.3574415134574167 m3/s**. All 36 peak indices agree, while ordinate, peak
magnitude and volume diagnostics remain independently reported. All 36 unique single-column native
reported volumes are retained separately from inclusive sums and physical trapezoids.

The 65-row private table and full per-case reports are retained in the private investigations
branch `audit/s5-current-65-20261114`, under `docs/evidence/s5-refreshed-65-20261114/`.
Full CSVs, staged verified copies and both earlier replay packets remain ignored/private.
Ready for software review, with the same mapping, coverage, numerical and symlink limitations;
no RORB numerical equivalence or stage closure is implied. Next action: independent mapping and
coverage review, followed by a selected numerical discrepancy investigation.
