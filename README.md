# Python runoff routing

Public, in-development Python implementation of selected RORB rainfall-runoff procedures. RORB_CMD and RORBwin are separately fingerprinted native reference engines; they are **not** interchangeable or required for normal Python execution.

## Current status (14 November 2026)

The public `main` branch contains S0 reference-capture tools, restricted S1 typed RORB input/output readers, an integrated S2 Python-only single-storm routing implementation ([#23](https://github.com/Chain-Frost/python-runoff-routing/pull/23)), and S5 JSON project import, execution and read-only native diagnostics ([#47](https://github.com/Chain-Frost/python-runoff-routing/pull/47), [#52](https://github.com/Chain-Frost/python-runoff-routing/pull/52)). **Implementation and synthetic-test success do not establish native numerical equivalence.** The exact-wheel S5 CMD diagnostic verified its sources but **failed** frozen S2 printed parity: 11/201 ordinates within budget; first mismatch at index 11; maximum error 0.22707848694007993 m³/s.

S6 ARR Data Hub source intake [#38](https://github.com/Chain-Frost/python-runoff-routing/pull/38), BoM IFD/temporal patterns [#48](https://github.com/Chain-Frost/python-runoff-routing/pull/48), ARR2019 ARFs/selection [#49](https://github.com/Chain-Frost/python-runoff-routing/pull/49) and explicit preburst/loss preparation [#50](https://github.com/Chain-Frost/python-runoff-routing/pull/50) have **merged as bounded Python source/method slices**. The **explicitly selected, experimental** RORBwin 6.52 full-increment loss profile [#54](https://github.com/Chain-Frost/python-runoff-routing/pull/54) is also **merged as code**, without changing the default ARR loss method or solver. Evidence-only R0/R1 and N1–N4 investigations [#56](https://github.com/Chain-Frost/python-runoff-routing/pull/56), [#64](https://github.com/Chain-Frost/python-runoff-routing/pull/64) and [#68](https://github.com/Chain-Frost/python-runoff-routing/pull/68) have also merged. N4 confirms native coefficient sensitivity, but R1 and N4 strict excess comparisons and the seven R2–R7 precision residuals remain failed. Coastal and further S6 precision experimentation are deferred until the Python routing engine is working and numerically validated; all S6 native/routed acceptance gates remain open. S2 native routing parity is the current engineering priority. S2 and full S5/S6 native acceptance remain open, and no production-compatible solver, ensemble or Monte Carlo claim is made. See the [current S0–S8 capability/acceptance matrix](docs/STATUS.md), [active next actions](docs/work/README.md), [compatibility contract](docs/COMPATIBILITY.md) and [regression contract](docs/REGRESSION.md).

## Supported entry points on main

- The source-aware S1 model and restricted `.par` / `.catg` / DESIGN `.stm` subset are documented in [S1/S2 integration](docs/S1_S2_INTEGRATION.md). Unsupported or uncharacterised legacy features fail closed.
- `runoff_routing.integration.read_run_json` and `run_model` calculate a supported, already-supplied storm in Python; calculated results are **unvalidated against native routing**.
- `python -m runoff_routing.project_json` provides `validate`, `inspect`, `import-rorb`, `compare`, `export-run`, `run`, `compare-runs` and `review-native`. The last command reviews an existing SHA-pinned CMD capture; it does **not** launch RORB. See [JSON project usage](docs/PROJECT_JSON.md) and [native review limitations](docs/S5_RECORDED_NATIVE_REVIEW.md).
- `repo-scripts/rorb_inspect.py` and `repo-scripts/rorb_reference.py` are developer scripts, not a general accepted native-compatible routing CLI. No `[project.scripts]` console entry point is configured.

## Development and smoke example

Windows / CPython 3.14 is the acceptance environment. The project does not require a virtual environment, although using one is supported.

~~~powershell
py -3.14 -m pip install -e ".[dev]"
py -3.14 repo-scripts/check_local.py
~~~

A source-controlled synthetic example can be calculated without starting RORB:

~~~python
from pathlib import Path
from runoff_routing.integration import read_run_json, run_model

model = read_run_json(Path("examples/synthetic-run.json").read_text(encoding="utf-8"))
result = run_model(model)
print(result.to_csv())
~~~

Run the example from the checkout root after installing the package. This checks Python execution, **not** native parity. For package milestones, `py -3.14 -m build` builds a wheel; verify the installed import from outside the checkout. `check_local.cmd` is the Windows wrapper. The approved [Windows quality workflow](.github/workflows/quality.yml) performs non-native checks only.

## Navigation and data controls

- [Documentation index](docs/README.md), [S6 detailed capability and native gates](docs/ARR_S6_INTEGRATION.md), [implementation roadmap](docs/IMPLEMENTATION_PLAN.md), [development guide](docs/DEVELOPMENT.md), [source register](docs/SOURCES.md).
- Preserve original effective inputs, native clock labels, engine identities and frozen tolerances. Public code uses the strict mathematical reference backend. A separate **private, opt-in experimental CMD-compatible** mode is under investigation and is neither merged here nor numerically accepted.
- Do not commit private raw captures, local paths, native executables, manuals, client models or unapproved input datasets. Keep unapproved local material in ignored `.local/`. TOML, publication and releases remain deferred and require separate owner decisions. This project is not endorsed by RORB's authors or custodians.
