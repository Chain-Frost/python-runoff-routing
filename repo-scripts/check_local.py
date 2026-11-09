"""Run inexpensive local quality gates without launching reference engines."""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).absolute().parents[1]
COMMANDS: tuple[tuple[str, ...], ...] = (
    ("repo-scripts/check_repository.py",),
    ("-m", "ruff", "check", "."),
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
        result = subprocess.run([sys.executable, *arguments], cwd=ROOT, check=False)
        if result.returncode:
            return result.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
