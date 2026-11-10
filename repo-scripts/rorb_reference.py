"""Local reference evidence tool; native launches require an explicit --execute flag."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

from runoff_routing.reference import archive_reference, capture_cmd, verify_manifest
from runoff_routing.reference_compare import Tolerance, compare_cached


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="operation", required=True)
    cmd = sub.add_parser("cmd", help="Preflight (default) or explicitly execute RORB_CMD")
    cmd.add_argument("spec", type=Path)
    cmd.add_argument("--output", type=Path, default=Path(".local/rorb-reference"))
    cmd.add_argument("--execute", action="store_true", help="Explicit native execution consent")
    archive = sub.add_parser("archive", help="Hash/copy manually collected GUI or CMD evidence; no launches")
    archive.add_argument("spec", type=Path)
    archive.add_argument("--output", type=Path, default=Path(".local/rorb-reference"))
    audit = sub.add_parser("audit", help="Check cached evidence without launching a reference engine")
    audit.add_argument("manifest", type=Path)
    compare = sub.add_parser("compare", help="Compare two verified cached runs from the same engine profile")
    compare.add_argument("left", type=Path)
    compare.add_argument("right", type=Path)
    compare.add_argument("--policy-id", required=True)
    compare.add_argument("--absolute", type=float, required=True)
    compare.add_argument("--relative", type=float, required=True)
    compare.add_argument("--near-zero-floor", type=float, default=0.0)
    args = parser.parse_args(argv)
    try:
        if args.operation == "cmd":
            manifest = capture_cmd(args.spec, args.output, execute=args.execute)
            print(manifest or "Preflight passed; no process launched and no capture files written")
            return 0
        if args.operation == "archive":
            print(archive_reference(args.spec, args.output))
            return 0
        if args.operation == "audit":
            problems = verify_manifest(args.manifest)
            print(json.dumps({"valid": not problems, "discrepancies": problems}, indent=2))
            return int(bool(problems))
        policy = Tolerance(args.policy_id, args.absolute, args.relative, args.near_zero_floor)
        result = compare_cached(args.left, args.right, policy)
        print(json.dumps(asdict(result), indent=2))
    except (OSError, KeyError, ValueError, TypeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    else:
        return 0 if result.status == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
