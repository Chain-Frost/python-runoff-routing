"""Check tracked/candidate files and relative Markdown links; never run native models."""

import re
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).absolute().parents[1]
FORBIDDEN_SUFFIXES = {".exe", ".dll", ".whl", ".pyc", ".pdf"}
LINK = re.compile(r"\[[^\]]*\]\(([^)]+)\)")


def markdown_errors(path: Path, name: str) -> list[str]:
    """Return missing local link targets without fetching external URLs."""
    errors: list[str] = []
    for target in LINK.findall(path.read_text(encoding="utf-8")):
        if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", target) or target.startswith("#"):
            continue
        relative = unquote(target.split("#", 1)[0])
        if relative and not (path.parent / relative).exists():
            errors.append(f"Broken relative link in {name}: {target}")
    return errors


def main() -> int:
    git_executable = shutil.which("git")
    if git_executable is None:
        print("Git is required for repository checks.", file=sys.stderr)
        return 2
    # Resolve the executable once, pass fixed Git arguments, and never invoke a shell.
    result = subprocess.run(  # noqa: S603 -- resolved Git executable with fixed read-only arguments
        [git_executable, "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
        cwd=ROOT,
        capture_output=True,
        check=True,
    )
    paths = sorted(set(result.stdout.decode("utf-8").split("\0")) - {""})
    errors: list[str] = []
    for name in paths:
        path = ROOT / name
        if name.startswith((".github/workflows/", ".local/", "results/", "reports/", "dist/", "build/")):
            errors.append(f"Disallowed tracked/candidate path: {name}")
        if path.suffix.lower() in FORBIDDEN_SUFFIXES:
            errors.append(f"Reference/binary artifact must remain outside Git: {name}")
        if not path.is_file():
            continue
        if path.stat().st_size > 1_000_000:
            errors.append(f"File exceeds the 1 MB bootstrap review limit: {name}")
        if path.suffix.lower() == ".md":
            errors.extend(markdown_errors(path, name))
    for error in errors:
        print(error, file=sys.stderr)
    print(f"Repository checks: {len(paths)} files, {len(errors)} errors.")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
