# S6: Optional PyTUFLOW 1.3.0 ARR source interoperability

**Review date:** 14 November 2026. **Tracking:** [#63](https://github.com/Chain-Frost/python-runoff-routing/issues/63); parent [#8](https://github.com/Chain-Frost/python-runoff-routing/issues/8).

**Source identity.** [PyTUFLOW 1.3.0](https://pypi.org/project/pytuflow/1.3.0/) was released 5 November 2026. Its release wheel SHA-256 is 8984c48104af418e24f086580e9176189c416ccc8ccd4eb77ad6aebda88ded50; no PyPI provenance attestation was provided. Git [release/1.3.0](https://github.com/TUFLOW-Support/PyTuflow/tree/release/1.3.0) points to 1a9459ddec9fb14e339cbfcd5413a701b6ab1ac9. This must not be confused with later master source. PyTUFLOW is [MIT licensed](https://github.com/TUFLOW-Support/PyTuflow/blob/release/1.3.0/LICENSE.txt); no upstream code or original BoM/ARR archives have been copied.

## Reuse versus independent implementation

| Capability | Pinned PyTUFLOW 1.3.0 | RORB preparation decision |
| --- | --- | --- |
| ARR2026 baseline selection | ArrApiResponse.ifd_table(1990/2030) returns recommended RecIFD baselines | Optional independent accessor cross-check only. ARRDocument preserves native, current and historical datasets, exact raw bytes, hash, axes, units, absent/unprocessed layers. |
| IFD arithmetic | Normal JSON floating-point and float/pandas processing can lose original decimal digits | Keep Decimal as-exported IFDs. Identify any float-roundtrip difference; never substitute a rounded value. |
| Historical BoM CSV | Current upstream ARR engine reads recommended IFDs through Data Hub, not historical BoM CSV | Retain BoMIFD source, issuance, AEP_PERCENT/EY/AEP_ONE_IN/ARI_YEARS identity and no implicit frequency conversion. |
| Point temporal patterns | parse_point_tp_csv converts EventID to int, increments to float and assigns cycling TP ordinal | Preserve original EventID string, leading zeros, source order and Decimal vector; never substitute ordinal IDs. |
| Areal temporal patterns | parse_areal_tp_csv expects missing AEP column and parses numeric area bins | Keep explicit absent or present AEP, original area-bin string, original member hash; report unsupported upstream AEP-bearing shape. |
| ZIP files | Upstream URL downloader selects first name containing increments and does not provide a source-safe offline ZIP auditor | Retain strict local ZIP validation and all member hashes. Probe feeds each validated increments CSV to upstream parser; URL-download/first-member behaviour is *not* validated. |
| TP selection | TemporalPatternSet.patterns can use point patterns when areal is absent; return count need not be ten; accepts EY, AEP and 1-in-N in its band function | Keep exact 10-member ARR2019 regional source selection; missing/partial areal members fail closed. ARR2026 TP selection is not automatically accepted. |
| ARF, preburst, IL/CL, climate | Upstream follows its own TUFLOW 2026/baseline/interpolation policies | Preserve once-only independent legacy operations and separate experimental RORBwin 6.52 loss; no policy transfer or implicit double application. |
| Event output | PyTUFLOW writes TUFLOW events, not RORBwin .par/.stm and engine-specific source-excess clocks | Do not add a RORB adapter; generated-input/native and routed-hydrograph acceptance remain distinct. |

## Explicit offline probe

The new standard-library-only runoff_routing.pytuflow_arr_audit module is not imported by the normal solver, does not download, edit source files or write output files. In a separately selected disposable Windows/Python 3.14 environment, install the exact third-party wheel and dependencies, verify its wheel SHA-256, then run:

~~~powershell
py -3.14 -m pip install "pytuflow==1.3.0"
py -3.14 -m runoff_routing.pytuflow_arr_audit --arr-json C:\offline\arr2026.json --point-patterns C:\offline\point_Increments.csv --areal-patterns C:\offline\areal_Increments.zip
~~~

Inputs are original local, rights-cleared or synthetic files only. The command demands PyTUFLOW version 1.3.0; invokes only ArrApiResponse.ifd_table, parse_point_tp_csv and parse_areal_tp_csv; emits JSON to stdout containing source SHA-256, dataset order, baseline and units, ID and area/frequency labels, member hashes, mismatch counts and up to ten examples. Failure to read/validate sources fails closed. No ARR API, networking, storm generation, RORB executable, pandas interpolation or solver dispatch is invoked by this probe. Multiple validated ZIP increments files are compared individually rather than claiming parity with upstream's first-member downloader.

## Evidence and missing gates

- Synthetic local-audit functions and strict source regressions cover recommended baseline matrices, native baseline being unexposed by the upstream accessor, leading-zero IDs, Decimal/float discrepancies, optional areal AEP, missing 0/1/9-member areal sets and unsupported inferred AEP mapping.
- Existing tests continue to own source SHA mismatches, frequency definitions, repeated ARF/preburst/loss and source identity. No historical or 2026 method is reinterpreted by this work.
- **Actual PyTUFLOW 1.3.0 import on Windows/Python 3.14: NOT RUN.** Python >=3.9 metadata is not compatibility evidence.
- **Authentic pinned-wheel offline ARR2026 and point/areal ZIP comparison: NOT RUN.** Static upstream source review and mock-shaped synthetic tests are not PyTUFLOW runtime equivalence evidence.
- **Generated RORBwin input, excess-ordinate, S2 routed numerical and ARR2026 policy parity: NOT ASSESSED.** Issue #8 remains open.

This is an independently reviewable source-validation slice. See [work record](work/2026-11-14-s6-pytuflow-interoperability.md) and [S6 matrix](ARR_S6_INTEGRATION.md).
