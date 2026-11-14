# Local agent handoff — S6 RORBwin 6.52 rainfall/preburst/loss comparison

**Prepared:** 2026-11-12  
**Work front:** S6 rainfall-method/native verification, following S6-P0–P3.  
**Status:** HANDOFF ONLY — no native RORBwin run, numerical acceptance, merge, release or issue closure is claimed.  
**Owner's illustrative case:** Margaret River IFD point, **synthetic 100 km²** catchment.  
**Primary project:** [Chain-Frost/python-runoff-routing](https://github.com/Chain-Frost/python-runoff-routing) — Windows workspace typically `E:\Github\python-runoff-routing` (verify actual path).

## Copy-ready instruction to the local Windows agent

> Take over **S6 RORBwin rainfall verification**, not S1/S2 solver development. Read `AGENTS.md`, `docs/DEVELOPMENT.md`, `docs/REGRESSION.md`, `docs/COMPATIBILITY.md`, `docs/ARR_BOM_TP_GROSS.md`, `docs/ARR_S6_P2_SELECTION_ARF.md`, `docs/ARR_S6_P3_PREBURST_LOSSES.md`, and this handoff. Fetch live GitHub heads; work in a fresh isolated worktree based on **PR #50's head**, retaining PR dependencies and concurrent branches. On the approved Windows computer, fingerprint the actual RORBwin executable and document its observed version; use its GUI only for a small, local, permission-cleared **100 km² synthetic catchment**. Start with 24-hour/1% AEP/FLTwest areal event **9091** and the supplied BoM IFD CSV. Independently capture effective rainfall, ARF, preburst and IL/CL settings, source bytes, and per-timestep generated rainfall/excess. Compare against the Python S6 outputs before any routing-flow comparisons. Include no secret/client data or third-party raw files in public Git. Record all differences, do not silently change tolerance or reference values, and do not merge/release/close S6. Submit reviewable changes and a local evidence manifest.

## Git state and boundaries

Four **open draft, stacked** PRs were verified on 2026-11-12 (re-fetch; this snapshot may age):

| Slice | PR | Branch and pinned head |
| --- | --- | --- |
| S6-P0 Data Hub intake (legacy/2026) | [#38](https://github.com/Chain-Frost/python-runoff-routing/pull/38) | `feat/s6-p0-arr-2026-offline-ifd` — `4f2ac3671e40ff8d70177cc4e1998f363c0d0c80` |
| S6-P1 BoM/TP/gross rainfall | [#48](https://github.com/Chain-Frost/python-runoff-routing/pull/48) | `feat/s6-p1-bom-ifd-temporal-patterns` — `43678397be1bb94a8045a2413bf9a35263b97b2f` |
| S6-P2 TP selection/ARR2019 ARF | [#49](https://github.com/Chain-Frost/python-runoff-routing/pull/49) | `feat/s6-p2-arr2019-arf-tp-selection` — `0231a64f0cf1cfc02c59a45d5baccd2b027987a5` |
| S6-P3 preburst/IL/CL | [#50](https://github.com/Chain-Frost/python-runoff-routing/pull/50) | `feat/s6-p3-preburst-loss-policy` — `1cfbcd1d8b06fa1c13e087b664c49f2e3abc45ef` |

`main` is **not** the source of all S6-P0–P3 features. Do not develop from `main` alone or copy files across branches. No S6 numerical stage has been accepted. Last known #50 [Windows CI](https://github.com/Chain-Frost/python-runoff-routing/actions/runs/43145563256): Python 3.14.10, Ruff 0.16.6, strict Pyright, **356 passed**, built and installed wheel. This is **non-native software-quality evidence** only.

Suggested safe worktree setup, with paths changed to suit the actual machine:

```powershell
$repo = 'E:\Github\python-runoff-routing'
git -C $repo fetch origin
# Check for a pre-existing worktree/branch first; preserve all current work.
git -C $repo worktree list
git -C $repo worktree add 'E:\Github\python-runoff-routing-s6-native' -b 'feat/s6-rorbwin-native-rainfall' 'origin/feat/s6-p3-preburst-loss-policy'
Set-Location 'E:\Github\python-runoff-routing-s6-native'
py -3.14 -m pip install -e '.[dev]'
py -3.14 -m pytest -q tests/test_arr_losses.py tests/test_arr_arf.py tests/test_arr_selection.py tests/test_arr_patterns.py tests/test_bom_ifd.py
py -3.14 repo-scripts/check_local.py
```

Never reset or delete existing local worktrees. If the proposed branch/path exists, select a different isolated name.

## Private inputs and immutable evidence

Copy originals to the new worktree's ignored `.local\s6-rorbwin-native\inputs\` **only if approved by the owner**. Do not commit or redistribute them. The original uploaded files are not automatically available under a Windows `E:` path; locate or copy them explicitly and verify byte hashes before use.

| Input | SHA-256 (original uploaded bytes) | Role |
| --- | --- | --- |
| `depths_margaret_river_ifds.csv` | `0ca11f66c2a1cb7e48e8bd6fc852f52dfa68014377c16301f5d57495c54864db` | BoM 2016-methodology IFD depth, issued 2026-11-11 |
| `depths_margaret_river_all_design.csv` | `7a739958861f82c26e37a568ebabc56fe1dfe16f442b891d7978d54e710a5197` | Cross-check only; contains EY/AEP/rare probability columns |
| `Areal_FLTwest.zip` | `61c60366f953669a9879c5e2c6619b3c420c3a3dceeb296fa41e91606b3c213f` | Areal patterns, area bin `100`; actual 24h event IDs `9091`–`9100` |
| `FLTwest.zip` | `0cd57da5e7dffd8f235b72d3e59c83ac1ab9f2e54f03e94201340e307ed83adb` | Point-pattern comparison and future boundary testing |

```powershell
Get-FileHash '.local\s6-rorbwin-native\inputs\depths_margaret_river_ifds.csv' -Algorithm SHA256
Get-FileHash '.local\s6-rorbwin-native\inputs\Areal_FLTwest.zip' -Algorithm SHA256
```

**Also required:** a locally authorised `RORBwin.exe`, its actual observed version/banner and SHA-256, plus **a small RORBwin-compatible synthetic catchment model containing 100 km² total contributing area**. Do not pretend the latitude/longitude themselves define catchment area. Do not decompile, modify, patch, distribute, or commit executables/manuals. RORBwin 6.52 **release notes** are documentary evidence, not proof that a particular binary is build 6.52.

There is currently **no authentic site-matched legacy ARR Data Hub TXT with actual Margaret River losses** in the verified S6 inputs. Initial loss/preburst numbers below are **fabricated by design**; enter them manually as test parameters. If a genuine legacy TXT is later acquired, retain it separately and never confuse the two sources.

## Fixed baseline — verify before comparing

| Variable | Fixed value / semantics |
| --- | --- |
| BoM requested point | latitude `-33.953684`, longitude `115.0735` (WGS84 degrees) |
| Fictional catchment area | `100 km²`; explicitly synthetic, **not** spatially delineated |
| IFD duration / AEP | `1440 min` (24 h); `1% AEP`, **not 1 EY** |
| BoM gross point depth | `129.000 mm` |
| ARR temporal-pattern source | `Areal_FLTwest.zip`, region CSV label `S-SW Flatlands (West)`, area bin `100` |
| Baseline event | original `EventID=9091`; `60 min` timestep, `24` design increments |
| Other patterns | IDs `9092`–`9100`; no claim `9091` is the representative hydrograph |
| ARF source | published ARR2019 Book 2, region `South-West Western Australia` (assumption for synthetic point) |
| ARF factor (Python) | `0.9446027708854816873275314719` |
| Area-adjusted 24-h burst | `121.8537574442271376652515599 mm` |
| Synthetic storm IL / CL | `21.0 mm` initial loss; `2.0 mm/h` continuing loss |
| Synthetic preburst | source depth `7.00 mm` **distinct from** source ratio `0.054` |
| Explicit ratio × area-adjusted design depth | `6.580102901988265433923584235 mm` |
| Reduced burst-only IL (hypothesis) | `14.41989709801173456607641576 mm` |
| User-defined preburst shape | **25%, 75%**, two 60-min increments, purely synthetic; **not** the GSAM/Jordan default |
| Experimental outputs for diagnosis | burst-only excess `64.27700696349762178833652042 mm`; complete-storm gross `128.4338603462154030991751441 mm`; both **NOT** reference RORBwin results |

Reference synthetic JSON: the previous conversation generated `margaret_river_100km2_s6_synthetic_replay.json`; verify or regenerate it locally rather than treating an arbitrary path as guaranteed. **Never** use these fabricated losses for an actual design catchment.

Relevant source APIs: `runoff_routing.bom_ifd.read_bom_ifd_csv`; `arr_patterns.read_pattern_file`; `arr_selection.select_arr2019_ensemble`; `arr_storm.storm_from_bom`; `arr_arf.calculate_arr2019_arf`, `published_coefficients`, `apply_arr2019_arf_to_bom_storm`; `arr_losses.select_legacy_preburst_loss`, `derive_preburst_from_areal_rainfall`, `calculate_burst_only_excess`, `prepend_explicit_preburst`, `calculate_complete_storm_excess`. The loss selection API requires an **explicitly characterised legacy TXT document**; for a synthetic replay, construct only a clearly labelled synthetic legacy fixture with exact point metadata. Do not let a production importer fabricate such a source.

## Native comparison campaign — execute locally only

1. **Preflight and inventory.** Confirm executable SHA-256, version/banner, GUI build, OS/Python versions, source hashes, file licences and model status. Read the **RORBwin 6.52 release-notes PDF** from a **permission-approved local copy** (see the source register at [docs/SOURCES.md](../SOURCES.md)); do not commit the PDF. Check that RORBwin can represent the synthetic 100 km² model and import or enter the required rainfall and TP data; record exact GUI settings/screenshots. If the GUI cannot export effective storm/rainfall data, record this limitation rather than inventing results.
2. **Control the model.** Start with a very small *pervious* 100 km² RORBwin catchment with explicit areas, gauges/subareas, reach/order and one print location. No impervious/DCIA/ICIA, spatial rainfall patterns, Monte Carlo, unrequested interpolation or extra losses. Confirm RORBwin's calculated total area is actually 100 km². Preserve the input/model file unchanged after capture.
3. **Generate source-side reference vectors.** Using PR #50's typed modules, export read-only CSV/JSON evidence for **all 24 raw and adjusted rainfall increments** for EventID 9091, the 24 end-time labels, source rainfall total, ARF, preburst increments and synthetic experimental loss increments. Preserve original Decimal strings and both SHA-256 values. Do **not** use these as native goldens.
4. **Single-event native A/B tests.** Use the **same** RORBwin temporal-pattern ID and event duration. Capture the saved effective inputs and raw/native outputs for each case below. If RORBwin emits the storm in a different timestep or applies a different default interpolation, record the original convention and do not silently shift/resample it.
5. **Only then** compare selected additional TP IDs, 12-h threshold/bins and optional RORBwin GSAM/Jordan defaults. Do not run an unbounded ensemble until the single-event observations are understood.

| Case | Controlled comparison | Required observation |
| --- | --- | --- |
| `R0` | 129 mm gross IFD, event 9091; **ARF off, preburst off, IL/CL zero** | 24 source rain increments, event ID, time axes and total |
| `R1` | ARF **on**, 100 km², 24h/1% and no losses/preburst | One application of ARF, 121.8537574 mm total, coefficients and output rounding |
| `R2` | ARF on; **IL 21 mm, CL 2 mm/h**, preburst off | Native rainfall excess by timestep; establish RORB's within-step IL/CL convention |
| `R3` | Burst-only reduced IL explicitly `14.419897... mm`, CL 2, preburst OFF | Native burst excess; compare experimental Python burst-only method **as a hypothesis**, not an accepted match |
| `R4` | RORBwin **Apply Pre-Burst ON**, manual ratio `0.054` and **user-defined** 25/75% preburst, original IL 21 and CL 2 | Source and effective preburst depth, 2 preburst steps, 24 burst steps, total rainfall and all excess cells; check ARF once |
| `R5` | Identical to `R4` but RORBwin **default** GSAM/Jordan profile where applicable | Record default region/zone, pattern, timestep and model area dependence; **do not compare to Python's 25/75% profile as equivalent** |
| `R6` (conditional) | 12h and area threshold boundary (e.g. 74.9/75/100 km²), fresh supported TP and IFD | Characterise point/areal and preburst-profile switching; use actual source patterns only |
| `R7` (conditional) | Requested AEP, interpolation and long-duration preburst limits | Document supported RORBwin behaviour, no guessed nearest-table substitutions |

RORBwin 6.52 notes say preburst is optionally applied, the default uses GSAM for long duration and Jordan et al. (2005) for short duration, and **at 12 h** the area threshold is 75 km²; preburst default timestep compatibility and the **60-entry** GUI editor matter. They also document a historical **double-ARF-to-preburst** defect that was fixed. Record the native executable build as part of every comparison; release notes alone do not establish which behaviour is present.

**Crucial distinction:** for `R4`, do not manually apply ARF to a preburst value that RORBwin has already treated as a percentage of areal rainfall. Record whether the software internally uses unadjusted/adjusted design depth as the preburst-ratio basis. If that cannot be observed, mark the basis **unresolved**, not accepted.

## Comparison and pass/fail gates

- Match the **effective** AEP/duration/area/TP ID, input depth, region, ARF mode, preburst mode, IL and CL before numeric time-series comparisons. A mismatch in these is an **input/configuration** mismatch, not proof of a solver defect.
- Compare **each rainfall ordinate**, each excess ordinate when exported, raw time label, sequence length, step index, sums, ARF, preburst duration/depth, IL/CL consumption and conservation. Do not assess only total rainfall or peak discharge. Keep original CSV/TXT precision and exact source order.
- Compare time-zero and end-time conventions explicitly. If the native GUI output prints rounded values, define and freeze a **source-precision-derived absolute + relative tolerance** before deciding acceptance. Do not choose a tolerance after observing a mismatch or silently normalise to 100%.
- Report separately: `recognized`, `parsed`, `validated`, `event_generated`, `native_rainfall_compared`, `native_rainfall_accepted`, `native_excess_accepted`, `routed_output_accepted`. For unrun/missing native evidence mark **NOT RUN**, never pass.
- Do not compare discharge hydrographs until effective rainfall, losses and timing are characterised. If routing comparison follows, use matching input graphs and preserve GUI/CMD profiles separately; no solver changes in this work front.

## Expected local deliverables

Under ignored `.local\s6-rorbwin-native\` retain a manifest and immutable evidence snapshots:

```text
inputs/                         original BoM and ARR ZIP, local synthetic model, approved executable locator (not EXE copy in Git)
native/R0/ ... native/R5/       native RORBwin save/export/log/screenshot captures, never edited
python/                        source/adjusted/excess per-step CSV + deterministic JSON of method ledger
reports/manifest.json          case ids; source names, hashes, licensing; engine/version/hash; settings and effective inputs
reports/matrix.csv             case, duration, AEP, TP ID, mode, pass/fail/unresolved/not-run, max |difference|
reports/mismatches.md          field/index/time-by-time diagnostics, grouped by input vs algorithm vs reporting
reports/acceptance.md          scope, tolerance, versions, result, limitations and next tests
```

For public Git, commit **only** source code, synthetic fixtures, non-sensitive manifest *schema*, tests and explanatory Markdown. Full native outputs and raw BOM/ARR archives are local/private until rights and redistribution are reviewed. Include a small copy-ready summary in the PR and selected issue #8; cite exact revisions and evidence locations without exposing private paths unnecessarily.

## Validation and stopping point

Run `py -3.14 repo-scripts/check_local.py`, `py -3.14 -m build --wheel` and installed-wheel smoke **outside checkout** if implementing code. Tests remain offline and native-free by default. Keep the existing `.github/workflows/quality.yml` unchanged; no new automation, cloud native runs, third-party redistribution, force push, merge, release or stage closure without owner approval.

**Completion of this handoff** means a local native comparison report (or an explicit documented blocker), not that S6 is accepted. If source inputs or a native build are unavailable, stop at a truthful incomplete manifest; do not invent native outputs. A reviewed match for one illustrative rainfall event never implies universal ARR2019/2026 compatibility or RORBwin routing parity.
