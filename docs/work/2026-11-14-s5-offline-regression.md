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

## Completed corrected-wheel 65-case replay — final S5 review status

**14 November 2026, updated after independent private validation.**
The earlier `NOT RUN` and `35 computed/fail + 1 invalid` statements above
remain **historical observations of earlier installed wheels**; they do not
describe the final corrected implementation. The separately retained
independent Windows/Python 3.14.6 campaign used exact source
`c7de1aba4969344f2e85ef0732aa45dee93201a9` and the installed wheel
SHA-256
`6f43d66e7fdb80faa1dc678a35c44dcdff2144eacacdba573d09d86331f94dd0`.

- All **65** original catalogue case IDs and manifest/input fingerprints
  were checked, as were all **1,026** indexed source files before/after.
- The S5 suite classified **36 computed/fail, 29 incomplete, 0 pass,
  0 invalid, 0 unsupported**. The 29 incomplete retain 25 unreviewed,
  three expected native-failure and one incomplete capture classifications.
- **1,498/16,836** ordinates were within the unchanged frozen budget.
  Maximum absolute error: **0.3574415134574167 m³/s**; all native and Python
  raw ordinate/time tokens and predictions matched the previous API exactly.
  Four narrow linear controls continued to pass.
- The one exact-source `0.125 h` / displayed `0.12 h` case transitioned
  from erroneously invalid to **computed/fail**. The strict S2 discharge
  budget was neither relaxed nor refitted.
- The original 201-row baseline remains **11/201** in budget, first
  failure **11**, maximum error **0.22707848694007993 m³/s**.
  **All 36** HydNNN associations remain caller asserted despite recorded
  code-7 labels. Rainfall/excess and native physical water-balance equivalence
  are not established.
- Original long-form rows, complete 65-case table and source hashes remain
  in the **private** investigations branch; no raw model inputs, path-specific
  evidence or native executables were published or launched.

The later PR #58 reconciliations through
`4fbfe7541f2154a5e7ade88e823690db0f6c8503`
modify documentation relative to the exact validated `c7de1aba` code,
not numerical Python source or the frozen acceptance evaluator.
[Exact-head public Windows quality #43552194119](https://github.com/Chain-Frost/python-runoff-routing/actions/runs/43552194119)
passed **692** non-native tests, pinned Ruff, strict Pyright and external
installed-wheel import. It is a source-quality check, **not** a new native
replay on that wheel.

**Next action:** independent **software review and owner-approved
implementation-only disposition** of draft PR #58. Keep S2 #4, S5 #7 and
S5-P2 #51 open for numerical and source/profile coverage; separately verify
physical print-site mapping, address 29 unrepresented/incomplete projects and
investigate the 36 failed hydrographs. No broader numerical acceptance,
new native execution, release, publication, licence change or tolerance edit.

## Independent software review corrections (unmerged candidate)

Three reproducible review findings were raised against PR #58 after the
65-case replay: a second native hydrograph column could be omitted from a
passing suite comparison; a recognised unsupported source dialect could
be classified as malformed/invalid; and an invalid printed volume could
escape the S1 inspector's structured error result.

The isolated follow-up candidate **does not change native evidence or numerical
calculation**. It requires source-verified complete native column coverage
before a computed/pass classification; propagates the source parser's typed
`unsupported` distinction through S5 project loading; and keeps optional
printed-volume validation inside S1's structured inspection error boundary.
Manufactured regression tests exercise all three cases. The candidate needs
exact-head Windows/Python 3.14 quality and independent review before integration.
No separate 65-case private replay or S2/S5 numerical acceptance is inferred
from these source/diagnostic corrections.
