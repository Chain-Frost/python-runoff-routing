# S5 — Versioned offline multi-case native regression

**Status:** diagnostic implementation under review; **no native numerical equivalence accepted**. This is an S5 extension of [JSON project execution](PROJECT_JSON.md) and the [SHA-pinned CMD reviewer](S5_RECORDED_NATIVE_REVIEW.md). Tracking: [#7](https://github.com/Chain-Frost/python-runoff-routing/issues/7), [#44](https://github.com/Chain-Frost/python-runoff-routing/issues/44), [#51](https://github.com/Chain-Frost/python-runoff-routing/issues/51).

## Contract and boundaries

A regression suite reuses the existing S5 `load_project`/typed S1 `RunModel`, S0 `verify_manifest`, S1 `inspect_output`, S2 `run_model` and predeclared S2 printed-precision/volume reviewers. There is **no second solver**, no native RORB execution, no ARR rainfall-generation adapter and no change to fixed golden values or tolerances.

Each declared case is enumerated **exactly once**. The suite has independent statuses for source verification, software computation, frozen print-budget comparison and native numerical acceptance. `computed/pass` is strictly a *printed-ordinate diagnostic*, not a declaration of RORB compatibility. All records set `native_numerical_acceptance=unassessed`. Per-case classifications:

| Classification | Meaning |
| --- | --- |
| `computed/pass` | Valid pinned source and S0 output, supported Python run, all mapped ordinates within the **existing** strict half-print-unit budget |
| `computed/fail` | Same checks computed, but **at least one printed ordinate** fails the original frozen budget |
| `unsupported` | Recognised but unsupported numerical, engine or rainfall profile (for example, RORBwin or unprocessed ARR forcing) |
| `incomplete` | Missing declared project/reference, source file, incomplete native capture or insufficient print coverage |
| `invalid` | Malformed schema, tampering, mismatched fingerprints, ambiguous mappings, contradictory source/engine evidence |

`source_verification` is `verified` only after the complete S0/project checks pass. An unsupported/invalid case is never silently omitted. CLI exit 0 requires **all** declared cases to be `computed/pass`; exit 1 means any fail/unsupported/incomplete/invalid classification, while exit 2 means a suite-level schema, usage or output I/O error. A zero exit does **not** accept S2 numerical compatibility.

## Suite schema v1

The suite JSON is a small **separate** file; the referenced project JSONs retain their existing S5 schema. All paths are portable, slash-separated, relative to the suite file's directory; source records must be SHA-256-pinned. Each native engine SHA-256 is its executable fingerprint from the S0 manifest. Replace all example strings below with actual lowercase SHA-256 values; they are not digests.

```json
{
  "format": "python-runoff-routing-offline-regression",
  "schema_version": 1,
  "suite_id": "reviewed-cmd-events",
  "cases": [
    {
      "case_id": "reviewed-event-01",
      "project": {
        "path": "projects/event-01.json",
        "sha256": "<64 lowercase hex characters>"
      },
      "native": {
        "manifest": {
          "path": "reference/event-01/manifest.json",
          "sha256": "<64 lowercase hex characters>"
        },
        "engine_executable_sha256": "<64 lowercase hex characters>",
        "print_mapping": [
          {"model_print_id": "print_1", "native_column_id": "Hyd001"}
        ]
      }
    }
  ]
}
```

`project` and/or `native` may be `null` for a **declared incomplete case**; this records work outstanding rather than inventing results. Duplicate IDs, unknown fields, unsafe Windows names, duplicate mappings and ambiguous native column reuse are rejected. Reference column coverage must be complete and one-to-one with the typed model's print sites and S0 declared columns; it is never inferred from filename, column order or description.

**Print-site evidence:** the `model_print_id` to `HydNNN` association in this schema is **caller asserted**. Checking that the two names exist and have complete one-to-one coverage does not independently verify the physical location. `mapping_evidence=caller_asserted` must remain in all records until separate, documented source proof exists.

## CLI and Python API

Use a unique output filename on each run, and do not write a report into the source or reference directories. Example on the installed Python 3.14 environment:

```powershell
py -3.14 -m runoff_routing.project_regression ".local/s5/suite.json" ".local/s5/results-001.json" ".local/s5/samples-001.csv"
```

No program launch, network access or fixture regeneration is performed by this command. The optional CSV is long-form, preserving native `Inc` and `Time` **verbatim** next to *independently indexed* Python ordinates. No 0-based/1-based conversion, phase shift or time-alignment selection occurs.

```python
from pathlib import Path
from runoff_routing.project_regression import run_suite, write_suite_results

report = run_suite(Path(".local/s5/suite.json"))
write_suite_results(
    Path(".local/s5/results-002.json"),
    report,
    details_csv=Path(".local/s5/samples-002.csv"),
)
assert len(report.cases) == sum(1 for _ in report.cases)
```

The results JSON is source-derived and immutable once written. It retains suite/project/typed-model/manifest/native-output/executable hashes, source hashes, effective settings, computational control-vector order, raw CMD increment and time tokens, per-site mapping identity and its evidence state, all-ordinate counts, first and maximum errors, native and model peak **indices** and magnitudes, and model/native physical-horizon trapezoid integrals. The CSV retains all original native discharge tokens and Python outputs. Each print budget is the existing S2 source-print-resolution rule; it is not refitted.

### Native reported volume

For a uniquely identified **single-column** retained `.out` table, the S1 output reader can attach a single pre-table printed `Volume,m³` token. Its exact printed text, native-inclusive sum, physical trapezoid and independently assessed print-precision interval consistency are reported **separately**. A missing, repeated, ambiguous, or multi-column volume is `unavailable`, not zero or an inferred value. This statistic is not a catchment water-balance proof. Rainfall-excess and physical water-balance comparisons remain **unassessed** until source/time semantics are independently characterised.

## Printed native timestep precision

For the characterised CMD 6.44 1-based report, the immutable S0 effective
timestep is checked **exactly** against the S1 source storm before reviewing
the output table. A separately printed native header can round that exact
value: an original 0.125-hour step may display as 0.12 or 0.13 hours.
The reviewer accepts a header only within **half of its last displayed
decimal place** and independently checks **every raw Inc/Time value** against
`Inc * exact_source_timestep` using that time token's own displayed
precision. Both endpoints of a half-unit rounding tie are admitted; no
time-label shift, resampling, source change, user-tuned tolerance or discharge
budget change is permitted. Mismatched clocks still fail closed, and all
original tokens are retained in the diagnostic.

This specifically addresses the **one invalid timestep-header classification**
in the prior private 65-case replay. The corrected source head has **not** yet
been replayed against the private 65-case corpus; no 36/36 computed result
is claimed for it. Independently approved physical print mappings and S2
native numerical acceptance remain outstanding.

## Profile and acceptance limits

The retained native-review adapter currently supports file-backed `legacy-rorb` projects, pinned RORB_CMD manifest and executable identity, one verified S0 `.out` table, one-burst/one-ISA pervious IL/CL DESIGN storms and characterised 1-based CMD labels. RORBwin captures, unsupported topologies or profiles and unprocessed ARR2016/2026 assets fail closed. Original `.par` paths are retained but not followed. TOML remains deferred.

The **previously verified** five-subarea CMD replay was **11/201 within frozen print precision**, first failure at sample index 11, max absolute difference **0.22707848694007993 m³/s**. Earlier private 65-case work identified **36 computed numerical failures** and **29 otherwise unsupported/uncomputed**; they are prior evidence, **not** a new S5 suite run. Private original case bytes, `FILE_INDEX.json`, original output and manifest hashes remain exclusively in `runoff-routing-investigations` or local ignored folders. An offline-only private replay must be executed from a private, separately checked-out corpus with explicit print mappings, without copying fixture bytes into this public repository.

### Verification requirements

Public synthetic tests cover source/hash tampering, missing references, incompatible GUI profiles, ambiguous mappings, incomplete captures, native 1-based clocks, frozen numerical failures, raw-volume provenance, no-clobber reports and full per-case disposition. Validate with `py -3.14 repo-scripts/check_local.py`, `py -3.14 -m build`, and an **out-of-tree installed wheel** on Windows/Python 3.14; record exact results rather than inferring Windows success from non-Windows tests. The pre-existing Windows quality workflow is permitted. **S2 #4 and S5 #7 remain open**, regardless of software-test outcomes.
