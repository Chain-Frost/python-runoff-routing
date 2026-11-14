# Python runoff routing

Public, in-development Python implementation of RORB procedures. Existing RORB_CMD and RORBwin executables remain the computational source of truth for separately fingerprinted effective-input profiles.

**Status (2026-11-14):** S0/S1 source and capture foundations, Python-only S2 routing integration, S5 JSON project and native diagnostic infrastructure, and S6 rainfall preparation P0–P3 (**#38, #48, #49, #50**) are implemented and merged. The S6 APIs provide versioned ARR/BoM input, legacy temporal patterns, ARR2019 ARFs and explicit preburst/loss arithmetic; none establishes RORBwin method parity or engineering design acceptance. **S2 numerical parity fails** the frozen CMD comparison (11/201 ordinates within budget); S6 R1 strict excess and experimental RORBwin precision comparisons remain unaccepted. No numerical stage, ensemble/Monte Carlo or production solver is accepted.

The first usable milestone reads existing RORB inputs and reproduces supported single-storm calculations. RORB_CMD and RORBwin are separate reference engines, not interchangeable ground truth. Production calculations will run in Python, without launching RORB for every event.

## Start here

- [Implementation plan](docs/IMPLEMENTATION_PLAN.md): scope, stage gates and linked workpacks.
- [Compatibility contract](docs/COMPATIBILITY.md): file dialects, GUI/CMD differences and numerical conventions.
- [Regression contract](docs/REGRESSION.md): reference capture, acceptance and performance evidence.
- [Development guide](docs/DEVELOPMENT.md): Windows setup and local-only checks.
- [Work register](docs/work/README.md) and [documentation index](docs/README.md).

## Local development

Windows with Python 3.14 is the acceptance environment. Use the normal Python installation; no virtual environment is required by this project.

```powershell
py -3.14 -m pip install -e ".[dev]"
py -3.14 repo-scripts/check_local.py
```

Alternatively double-click `check_local.cmd`. Build validation at package milestones uses `py -3.14 -m build`; install the resulting wheel and test from outside the checkout.

Main contains S0 reference capture, S1 typed source-preserving RORB inputs, a bounded Python-only S2 routing/integration implementation, S5 JSON project execution and native diagnostics, and the S6 rainfall-source/preparation modules. Local reference scripts do not establish RORB numerical equivalence. See the [S6 capability and acceptance matrix](docs/ARR_S6_INTEGRATION.md) and [work register](docs/work/README.md) for implemented-versus-accepted scope.

## Development and publication controls

The pre-existing, owner-approved single-lane Windows/Python 3.14 quality workflow `.github/workflows/quality.yml` runs non-native checks. It cannot prove numerical equivalence. No additional hosted automation, release jobs or package publication are authorised.

Do not commit RORB executables, manuals, unapproved samples, client models or generated outputs. Keep local reference material under ignored `.local/`. A future licence and package publication need separate owner approval; the repository is already public. This project is not represented as endorsed by RORB's authors or custodians.
