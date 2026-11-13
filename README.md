# Python runoff routing

Public, in-development Python implementation of RORB procedures. Existing RORB_CMD and RORBwin executables remain the computational source of truth for separately fingerprinted effective-input profiles.

**Status (2026-11-14):** S0 native-reference capture, S1 typed parsing, bounded S2 Python-only kernel/integration and S5 JSON project execution plus a SHA-pinned CMD diagnostic are merged. The S5 multi-case offline regression extension is a draft. The existing 201-ordinate CMD check **fails** strict numerical parity (11/201 within the fixed print budget). No numerical stage, ensemble, Monte Carlo or production solver is accepted.

The first usable milestone reads existing RORB inputs and reproduces supported single-storm calculations. RORB_CMD and RORBwin are separate reference engines, not interchangeable ground truth. Production calculations will run in Python, without launching RORB for every event.

## Start here

- [Implementation plan](docs/IMPLEMENTATION_PLAN.md): scope, stage gates and linked workpacks.
- [Compatibility contract](docs/COMPATIBILITY.md): file dialects, GUI/CMD differences and numerical conventions.
- [Regression contract](docs/REGRESSION.md): reference capture, acceptance and performance evidence.
- [S5 offline multi-case regression](docs/S5_OFFLINE_REGRESSION.md): source-pinned CMD diagnostics, statuses and CLI usage.
- [Development guide](docs/DEVELOPMENT.md): Windows setup and local-only checks.
- [Work register](docs/work/README.md) and [documentation index](docs/README.md).

## Local development

Windows with Python 3.14 is the acceptance environment. Use the normal Python installation; no virtual environment is required by this project.

```powershell
py -3.14 -m pip install -e ".[dev]"
py -3.14 repo-scripts/check_local.py
```

Alternatively double-click `check_local.cmd`. Build validation at package milestones uses `py -3.14 -m build`; install the resulting wheel and test from outside the checkout.

Main contains S0 evidence capture, S1 typed source-preserving subset parsers for CMD .par, RORB_GE .catg and DESIGN .stm, an unvalidated Python S2 reference and S5 JSON execution/diagnostics. Local scripts include `repo-scripts/rorb_reference.py` and `repo-scripts/rorb_inspect.py`; they are not accepted as a full routing solver. See the [live dependency and acceptance register](docs/work/2026-11-11-s1-s2-integration-readiness.md).

## Development and publication controls

The pre-existing, owner-approved single-lane Windows/Python 3.14 quality workflow `.github/workflows/quality.yml` runs non-native checks. It cannot prove numerical equivalence. No additional hosted automation, release jobs or package publication are authorised.

Do not commit RORB executables, manuals, unapproved samples, client models or generated outputs. Keep local reference material under ignored `.local/`. A future licence and package publication need separate owner approval; the repository is already public. This project is not represented as endorsed by RORB's authors or custodians.
