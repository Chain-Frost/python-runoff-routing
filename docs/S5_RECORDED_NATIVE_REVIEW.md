# S5-P2: SHA-pinned native CMD reference review

**Status: read-only diagnostic only; numerical equivalence is unassessed.** Child of [S5 #7](https://github.com/Chain-Frost/python-runoff-routing/issues/7), [issue #51](https://github.com/Chain-Frost/python-runoff-routing/issues/51). Depends on the S5-P1 [PR #47](https://github.com/Chain-Frost/python-runoff-routing/pull/47), typed native [PR #45](https://github.com/Chain-Frost/python-runoff-routing/pull/45), and separate printed-volume [PR #40](https://github.com/Chain-Frost/python-runoff-routing/pull/40).

## Inputs and validation

Use a file-backed **legacy-rorb JSON project**, explicitly selected SHA-pinned S0 native capture manifest, independently pinned **RORB_CMD executable SHA-256**, and a caller-established model print ID versus native HydNNN column mapping. All original .catg/.stm project input hashes must match those in the S0 capture. The .par file embedded paths are never followed.

The adapter uses S0 verify_manifest, S1 RorbSource/inspect_output, and S1/S2 review_recorded_print. It confirms complete successful or zero-runoff outcome, no provenance gaps or warnings, native executable identity, effective kc/m/IL/CL, source/burst/ISA, timestep, sample count, native output hash, raw columns and raw time strings. Both local and staged files are read only.

**CMD increment convention:** actual RORB_CMD 6.44 reference output with 200 calculation increments has 201 rows numbered **1–201**, beginning at raw time **0.50 h**. The S1 inspector now recognises this without shifting source labels; it continues to support a previously characterised 0..N variant. This does not infer RORBwin compatibility.

## API

~~~python
from pathlib import Path
from runoff_routing.project_native_review import review_project_native_capture, write_native_review_json

review = review_project_native_capture(
    Path("project.json"),
    Path("evidence/manifest.json"),
    manifest_sha256="REPLACE_WITH_64_LOWERCASE_HEX",
    engine_executable_sha256="REPLACE_WITH_64_LOWERCASE_HEX",
    model_print_id="print_1",
    native_column_id="Hyd001",
)
write_native_review_json(Path("recorded-review.json"), review)
~~~

Equivalent command:

~~~text
python -m runoff_routing.project_json review-native <project.json> <manifest.json> <manifest-sha256> <engine-sha256> <print-id> <native-column> <review.json>
~~~

Hash placeholders must be replaced with reviewed actual SHA-256 values. The command never downloads inputs, starts RORB or changes native records.

## Interpretation

Outputs include project, model, manifest, output and executable hashes, original unshifted native increment/time tokens, explicitly mapped site labels, frozen full-ordinate PrintedParity and separate inclusive native sample-sum versus physical trapezoid volume candidates. A printed comparison can fail while the verified diagnostic completes normally.

All reports remain `source_verified_diagnostic`, `mapping_evidence=caller_asserted` and `numerical_acceptance=unassessed`. The source HydNNN name or S0 manifest description does not independently establish a computational print location. Full native approval requires separate reviewed source/engine/site identity, time and phase policy, and previously frozen numerical acceptance criteria.

**Scope:** RORB_CMD only; initial captured one-ISA/burst pervious DESIGN subset. RORBwin, ambiguous or incomplete reports, mismatched source bytes/settings, and unprocessed ARR rainfall fail closed. S6 owns ARR2016/2026 event preparation; TOML is deferred.

Tests use synthetic S0-shaped files only. Private benchmark output is not copied into the public repository or executed by CI.

## Software-quality verification

The first S5-P2 implementation head `9c36efe` passed [Windows/Python 3.14 quality run #43148310990](https://github.com/Chain-Frost/python-runoff-routing/actions/runs/43148310990), including strict Ruff/Pyright, 370 public synthetic tests, and an installed-wheel import. This is a **source-quality check only**: no private original CMD/GUI hydrographs or native executables ran on the hosted workflow.
