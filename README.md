# Python runoff routing

Private development of an independent Python rainfall-runoff routing engine.

**Status: planning and repository scaffolding only. No parser, solver, ensemble or Monte Carlo implementation is validated.**

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

The package currently contains only its namespace. The planned inspect/validate/run/compare commands do not exist yet.

## Private bootstrap

No GitHub Actions workflow, release automation or package-upload job is supplied. Local checks remain required. This repository policy is separate from GitHub's repository-level Actions switch; see the development guide for the owner setting.

Do not commit RORB executables, manuals, unapproved samples, client models or generated outputs. Keep local reference material under ignored `.local/`. A future licence, public visibility and publication require an explicit owner decision. This project is not represented as endorsed by RORB's authors or custodians.
