# Python runoff routing

Private development of an independent Python rainfall-runoff routing engine.

**Status: independent Python S2 single-storm computation is a draft prototype; it is not validated as a RORB-equivalent solver.**

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

The draft S2 branch includes a bounded computation API and an offline numerical comparison helper. A full RORB input/model adapter and validated general-purpose run/compare CLI are still outstanding.

## Private bootstrap

No GitHub Actions workflow, release automation or package-upload job is supplied. Local checks remain required. This repository policy is separate from GitHub's repository-level Actions switch; see the development guide for the owner setting.

Do not commit RORB executables, manuals, unapproved samples, client models or generated outputs. Keep local reference material under ignored `.local/`. A future licence, public visibility and publication require an explicit owner decision. This project is not represented as endorsed by RORB's authors or custodians.
