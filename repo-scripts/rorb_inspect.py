"""Inspect an existing RORB report or parameter file without launching any native program."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from runoff_routing.rorb_inspect import inspect_file


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path)
    args = parser.parse_args(argv)
    try:
        result = inspect_file(args.path)
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(result.to_json())
    return 0 if result.status in ("parsed", "partial") else 1


if __name__ == "__main__":
    raise SystemExit(main())
