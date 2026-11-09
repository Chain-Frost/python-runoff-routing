"""Run inexpensive local quality gates without launching reference engines."""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).absolute().parents[1]
COMMANDS: tuple[tuple[str, ...], ...] = (
    ("repo-scripts/check_repository.py",),
    ("-m", "ruff", "check", "--no-fix", "."),
    ("-m", "ruff", "format", "--check", "."),
    ("-m", "pyright"),
    ("-m", "pytest", "-m", "not native and not benchmark"),
)


def main() -> int:
    if sys.version_info < (3, 14):
        print("Python 3.14 or newer is required for this check suite.", file=sys.stderr)
        return 2
    for arguments in COMMANDS:
        print(f"Checking: {sys.executable} {' '.join(arguments)}", flush=True)
        # Only the current interpreter and the fixed command table are executed; no shell.
        result = subprocess.run(  # noqa: S603 -- reviewed fixed commands, no external command text
            [sys.executable, *arguments], cwd=ROOT, check=False
        )
        if result.returncode:
            return result.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
