# RORB manual worked examples: local reference inputs

**Status:** Inventory and hashes checked against the user-supplied manual and ZIP on 2026-11-11. These examples are **not executed or accepted as native numerical regression goldens**.

## Source identity

- RORB Version 6 User Manual, Chapter 10, PDF pages 116–160 (printed pages 105–149). It documents four worked examples. Its Section 6.11 presents a graphical-editor example.
- User-supplied SampleData.zip, SHA-256: **4f58e2dd50fce15868d14eda24383529d1f18d472aed00422fbde0b4a3466c6a**.
- A curated local-only bundle contains 19 input members, a README and a JSON file manifest with exact per-file SHA-256. The bundle was created in the user conversation, not committed to Git.
- Original ZIP also contains melbourne.dat (32,424,927 bytes) and Fig6_7.wmf (1,166,998 bytes), excluded from the compact bundle; both remain in the original ZIP.

## Manual-to-file index

| Manual reference (PDF pages) | Original archive basenames | Intended regression coverage |
| --- | --- | --- |
| §6.11, graphical-editor introductory case (86–91) | Fig6_7.catg | S1: graphical catchment dialect, node metadata and computation-order preservation; not a complete storm |
| §10.2.1, Werribee FIT (117–122) | werfit.dat | S1/S2/S3: combined file and prescribed input/observed hydrographs, natural reach routing; FIT semantics differ from the minimum DESIGN solver |
| §10.2.2, Werribee DESIGN (123–127) | werdes.dat | S3: overbank flow formulas, diversion, parallel routes and branch rejoining |
| §10.3.1, Thomson FIT (128–137) | tomfit.cat, tomnov71.stm | S1/S3: separate catchment/storm, subareas, gauged rainfall, baseflow and interstation areas |
| §10.3.2, Thomson DESIGN (137–140) | tomdes.cat, tomdes.dat, tr48h.dat | S1/S3: reservoir routing and drowned reaches; do not assume these variants are interchangeable |
| §10.3.3, Thomson batch (140–144) | tomdes.cat, melbourne.ifd and generated storms | S6: historical rainfall generation/critical duration; generated native storm and output files are not in the archive |
| §10.4.1, South Creek FIT (145–150) | sckfit.cat, sckfit.dat, sckmar56.stm | S1/S3: two bursts, multiple pluviographs, varying loss factors and confluences |
| §10.4.2, South Creek DESIGN (150–155) | sckdes.cat, sckdes.dat, sckdes2.cat, sckbas.cat | S3/S6: urbanisation, impervious areas, lined/unlined reaches and basins |
| §10.5, Monte Carlo (155–160) | melbourne_mc.pat, melbourne.ifd, Thomson models | S7: historical stochastic temporal patterns; no event-level random draws or accepted Monte Carlo outputs |
| Legacy rainfall location support | ifd_aust.map, ifd_melb.map | S6: historical location data, not basic solver inputs |

## Do not equate manual printouts with archive outputs

1. **Werribee FIT simulation duration differs:** the printed input on PDF page 117 contains **2,28,-99**; distributed werfit.dat contains **2,50,-99**. This changes the calculation horizon and expected output count.
2. **Werribee DESIGN print controls differ:** the manual's printed input on PDF page 123 includes an upstream print operation and other output labels not identical to the distributed werdes.dat control vector. Track them as distinct versions.
3. **Version-dependent outputs:** the manual's Monte Carlo output example reports RORBWin 6.00; v6.52 release notes document later changes. Do not infer the installed RORB_CMD build from either document.
4. **Stage coverage:** the majority of worked examples exercise FIT, multiple bursts, multi-ISA, special storages or code variants not supported by the planned S2 one-ISA DESIGN minimum. They are valuable parser fixtures but not automatically runnable using the initial reference-capture writer.
5. **No validated native results are supplied:** the archive contains source inputs, IFD and temporal-pattern information, but not executable fingerprinted native reference runs with complete raw output, effective parameters, logs and print-site mapping.

## Safe local workflow

- Keep the original archive byte-for-byte and verify its SHA-256. Extract into ignored .local/rorb-manual-examples (or another dedicated, isolated local folder).
- Do not copy sample contents into this public repository before checking applicable permissions and data provenance. Do not commit RORB executables, manuals, figures or proprietary run outputs.
- Use [S0 reference capture](REFERENCE_CAPTURE.md) only with a **verified supported** model. The initial CMD writer accepts one ISA/one burst/lumped kc/m and separate .catg/.stm, so most manual examples need other native/manual execution and cannot be passed to the writer without extension.
- Use these inputs now for S1 parsing and byte-preservation tests, distinguishing combined .dat from separate catchment/storm files and retaining original control-vector order.
- Produce new native goldens from the actual installed GUI/CMD builds in isolated working folders. Keep GUI and CMD result profiles separate. Accept complete hydrographs only after effective settings, exact inputs, engine hashes, timestep and output-site identities are verified.
- Use melbourne_mc.pat for later historical Monte Carlo compatibility only; no Monte Carlo distribution/replay agreement is demonstrated by possessing this file.

**Acceptance:** file inventory confirmed; hydrological numerical equivalence, version matching and native RORB execution **not tested**. See [regression contract](REGRESSION.md), [compatibility contract](COMPATIBILITY.md) and issues [S0 #2](https://github.com/Chain-Frost/python-runoff-routing/issues/2), [S1 #3](https://github.com/Chain-Frost/python-runoff-routing/issues/3), [S2 #4](https://github.com/Chain-Frost/python-runoff-routing/issues/4).
