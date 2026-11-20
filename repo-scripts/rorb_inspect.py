"""Inspect existing RORB input files or canonical native results, without running RORB."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from runoff_routing.rorb_ge_profile import profile_graphical_catg
from runoff_routing.rorb_inspect import inspect_file
from runoff_routing.rorb_report_views import inspect_report, report_csv, report_json


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path)
    parser.add_argument(
        "--report", action="store_true", help="Inspect canonical .out, batch.out or RORB hydrograph CSV"
    )
    parser.add_argument(
        "--ge-profile",
        action="store_true",
        help="Redacted graphical CATG envelope and record shapes only; never imports or executes 6.52",
    )
    parser.add_argument(
        "--ge-profile-sha256",
        action="store_true",
        help="Opt in to including the local source fingerprint; requires --ge-profile",
    )
    parser.add_argument("--section", help="Show one canonical report section (preserving source row order)")
    parser.add_argument("--format", choices=("json", "csv"), default="json", help="Canonical report view; default json")
    parser.add_argument("--offset", type=int, default=0, help="First zero-based section row, default 0")
    parser.add_argument("--limit", type=int, default=100, help="Maximum returned section rows (0..10000)")
    args = parser.parse_args(argv)
    if args.report and args.ge_profile:
        parser.error("--report and --ge-profile cannot be combined")
    if args.ge_profile_sha256 and not args.ge_profile:
        parser.error("--ge-profile-sha256 requires --ge-profile")
    if not args.report and (args.section is not None or args.format != "json" or args.offset or args.limit != 100):
        parser.error("--section, --format, --offset and --limit require --report")
    if args.ge_profile and args.path.suffix.lower() not in {".cat", ".catg"}:
        parser.error("--ge-profile accepts .cat or .catg only")
    if args.report and args.format == "csv" and args.section is None:
        parser.error("--format csv requires --section")
    try:
        if args.ge_profile:
            # A successful profile is not a successful CATG import or run.
            result = profile_graphical_catg(args.path.read_bytes(), include_sha256=args.ge_profile_sha256)
            print(result.to_json())
            return 0 if result.envelope == "bounded" else 1
        if args.report:
            document = inspect_report(args.path)
            if args.format == "csv" and args.section is not None:
                result = report_csv(document, args.section, offset=args.offset, limit=args.limit)
            else:
                result = report_json(document, section=args.section, offset=args.offset, limit=args.limit)
            print(result, end="")
            selected_valid = (
                next((item.valid for item in document.sections if item.name == args.section), False)
                if args.section is not None
                else True
            )
            return 0 if document.status in ("ok", "partial") and selected_valid else 1
        result = inspect_file(args.path)
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(result.to_json())
    return 0 if result.status in ("parsed", "partial") else 1


if __name__ == "__main__":
    raise SystemExit(main())
