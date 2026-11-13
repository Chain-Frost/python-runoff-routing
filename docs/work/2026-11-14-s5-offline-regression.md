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

**Private 65-case S5 replay status in this record: NOT RUN.**
