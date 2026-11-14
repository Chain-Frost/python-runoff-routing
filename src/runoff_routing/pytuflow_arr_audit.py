"""Explicit, offline PyTUFLOW 1.3.0 ARR source audit; never selected by RORB execution.

Importing this module needs only the standard library. The explicitly invoked CLI
imports PyTUFLOW and uses its local source APIs; no downloads or native runs.
"""

from __future__ import annotations

import argparse
import importlib
import io
import json
import sys
import zipfile
from collections.abc import Callable
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Protocol, cast

from runoff_routing.arr_data import ARRDocument, ARRFormatError, IFDDataset
from runoff_routing.arr_import import parse_arr_json
from runoff_routing.arr_patterns import Pattern, PatternKind, PatternSet, read_pattern_file

PYTUFLOW_VERSION = "1.3.0"
PYTUFLOW_TAG_COMMIT = "1a9459ddec9fb14e339cbfcd5413a701b6ab1ac9"
PYTUFLOW_WHEEL_SHA256 = "8984c48104af418e24f086580e9176189c416ccc8ccd4eb77ad6aebda88ded50"
MAX_ARR_BYTES = 8 * 1024 * 1024
MAX_DIFF_SAMPLES = 10


class _RecIFDResponse(Protocol):
    def ifd_table(self, year: int) -> dict[str, object]:
        """Return PyTUFLOW's recommended original RecIFD table for a baseline year."""


class _PatternFrame(Protocol):
    def to_dict(self, orient: str) -> list[dict[str, object]]:
        """Return PyTUFLOW's parsed CSV rows."""


def _sequence(value: object, field: str) -> list[object]:
    if not isinstance(value, list):
        msg = f"PyTUFLOW {field} must be a list"
        raise TypeError(msg)
    return cast("list[object]", value)


def _decimal(value: object, field: str) -> Decimal:
    if isinstance(value, bool) or value is None:
        msg = f"PyTUFLOW {field} is not numeric"
        raise ValueError(msg)
    try:
        number = Decimal(str(value))
    except InvalidOperation as exc:
        msg = f"PyTUFLOW {field} is not numeric"
        raise ValueError(msg) from exc
    if not number.is_finite():
        msg = f"PyTUFLOW {field} is nonfinite"
        raise ValueError(msg)
    return number


@dataclass(slots=True)
class _Differences:
    """Bounded examples with a complete mismatch count."""

    count: int = 0
    examples: list[str] = field(default_factory=list)

    def add(self, message: str) -> None:
        """Record every mismatch but cap potentially large report examples."""
        self.count += 1
        if len(self.examples) < MAX_DIFF_SAMPLES:
            self.examples.append(message)


def _ifd_differences(public: IFDDataset, upstream: dict[str, object]) -> _Differences:
    """Compare original IFD axes, shape and individual values without interpolation."""
    differences = _Differences()
    durations = tuple(_decimal(value, "duration") for value in _sequence(upstream.get("index"), "index"))
    probabilities = tuple(_decimal(value, "AEP") for value in _sequence(upstream.get("columns"), "columns"))
    depths = tuple(
        tuple(_decimal(value, "depth") for value in _sequence(row, "depth row"))
        for row in _sequence(upstream.get("data"), "data")
    )
    if durations != tuple(Decimal(value) for value in public.durations_min):
        differences.add("duration axis differs")
    if probabilities != public.aep_percent:
        differences.add("AEP axis differs")
    if len(depths) != len(public.depths_mm):
        differences.add("depth row count differs")
    for i, (observed_row, source_row) in enumerate(zip(depths, public.depths_mm, strict=False)):
        if len(observed_row) != len(source_row):
            differences.add(f"depth row {i} column count differs")
        for j, (observed, original) in enumerate(zip(observed_row, source_row, strict=False)):
            if observed != original:
                differences.add(f"depth[{i}][{j}]: original={original} upstream={observed}")
    return differences


def compare_ifd_tables(document: ARRDocument, response: _RecIFDResponse) -> dict[str, object]:
    """Audit recommended 1990/2030 IFD source without selecting a RORB baseline."""
    comparisons: list[dict[str, object]] = []
    for year, baseline in ((1990, "historical_1961_1990"), (2030, "current_2030")):
        public = next((dataset for dataset in document.ifd_datasets if dataset.baseline == baseline), None)
        if public is None:
            comparisons.append({"baseline": baseline, "status": "not_in_original_source"})
            continue
        differences = _ifd_differences(public, response.ifd_table(year))
        comparisons.append(
            {
                "baseline": baseline,
                "dataset": public.name,
                "duration_unit": public.duration_unit,
                "probability_unit": public.probability_unit,
                "depth_unit": public.depth_unit,
                "status": "source_numeric_match" if differences.count == 0 else "source_numeric_difference",
                "difference_count": differences.count,
                "examples": differences.examples,
            }
        )
    return {
        "kind": "ARR2026_RecIFD",
        "source_sha256": document.source.sha256,
        "source_byte_length": document.source.byte_length,
        "datahub_version": document.source.datahub_version,
        "original_dataset_order": [table.name for table in document.ifd_datasets],
        "native_dataset_not_exposed_by_pytuflow_ifd_table": [
            table.name for table in document.ifd_datasets if table.baseline == "native"
        ],
        "absent_layers": list(document.absent_layers),
        "unprocessed_layers": list(document.unprocessed_layers),
        "comparisons": comparisons,
        "policy": "source_values_only_no_interpolation_or_climate_adjustment",
    }


def _compare_pattern_row(
    original: Pattern, row: dict[str, object], kind: PatternKind, number: int, differences: _Differences
) -> None:
    """Compare numeric coordinates numerically but identifiers exactly as strings."""
    if _decimal(row.get("duration"), "duration") != Decimal(original.duration_min):
        differences.add(f"pattern {number}: duration differs")
    if _decimal(row.get("timestep"), "timestep") != Decimal(original.timestep_min):
        differences.add(f"pattern {number}: timestep differs")
    for label, source_value in (("event_id", original.event_id), ("region", original.region)):
        observed = str(row.get(label, "<missing>"))
        if observed != source_value:
            differences.add(f"pattern {number} {label}: original={source_value!r} upstream={observed!r}")
    if kind == "point":
        if row.get("aep_band") != original.aep_band:
            differences.add(f"pattern {number}: point AEP band differs")
    else:
        if str(row.get("area", "<missing>")) != original.area_bin:
            differences.add(f"pattern {number}: areal bin differs")
        if original.aep_band is not None:
            differences.add(f"pattern {number}: source areal AEP={original.aep_band} not in upstream CSV API")
    increments = _sequence(row.get("increments"), "increments")
    if len(increments) != len(original.increments_percent):
        differences.add(f"pattern {number}: increment count differs")
    for i, (source_value, observed_value) in enumerate(zip(original.increments_percent, increments, strict=False)):
        observed = _decimal(observed_value, "increment")
        if observed != source_value:
            differences.add(f"pattern {number} increment {i}: original={source_value} upstream={observed}")


def compare_pattern_rows(source: PatternSet, upstream_rows: list[dict[str, object]]) -> dict[str, object]:
    """Retain original IDs, missing fields and full-precision increments."""
    differences = _Differences()
    if len(source.patterns) != len(upstream_rows):
        differences.add(f"pattern count original={len(source.patterns)} upstream={len(upstream_rows)}")
    for i, (original, row) in enumerate(zip(source.patterns, upstream_rows, strict=False)):
        _compare_pattern_row(original, row, source.kind, i, differences)
    return {
        "kind": f"{source.kind}_TP_Increments",
        "source_sha256": source.source_sha256,
        "source_byte_length": len(source.raw_bytes),
        "source_member_sha256": [item.sha256 for item in source.members],
        "source_member_names": [item.locator for item in source.members],
        "original_pattern_count": len(source.patterns),
        "upstream_pattern_count": len(upstream_rows),
        "original_ids": [pattern.event_id for pattern in source.patterns],
        "original_area_bins": sorted({pattern.area_bin for pattern in source.patterns if pattern.area_bin is not None}),
        "original_aep_bands": sorted({pattern.aep_band for pattern in source.patterns if pattern.aep_band is not None}),
        "increment_unit": "percent",
        "status": "source_numeric_and_identity_match" if differences.count == 0 else "source_difference",
        "difference_count": differences.count,
        "examples": differences.examples,
        "policy": "source_rows_only_no_tuflow_fallback_or_RORB_selection",
    }


def _read_arr_bytes(path: Path) -> bytes:
    with path.open("rb") as stream:
        raw = stream.read(MAX_ARR_BYTES + 1)
    if not raw or len(raw) > MAX_ARR_BYTES:
        msg = "ARR JSON is empty or exceeds 8 MiB"
        raise ARRFormatError(msg)
    return raw


def _pattern_csv_texts(source: PatternSet, *, zipped: bool) -> list[str]:
    if not zipped:
        return [source.raw_bytes.decode("utf-8-sig")]
    with zipfile.ZipFile(io.BytesIO(source.raw_bytes)) as archive:
        return [archive.read(member.locator).decode("utf-8-sig") for member in source.members]


def _load_upstream() -> tuple[
    Callable[[dict[str, object]], _RecIFDResponse], Callable[[str], _PatternFrame], Callable[[str], _PatternFrame]
]:
    package = importlib.import_module("pytuflow")
    version = getattr(package, "__version__", None)
    if version != PYTUFLOW_VERSION:
        msg = f"Expected PyTUFLOW {PYTUFLOW_VERSION}; found {version!r}"
        raise ValueError(msg)
    api = importlib.import_module("pytuflow.arr.api_client")
    tp = importlib.import_module("pytuflow.arr.temporal_patterns")
    return (
        cast("Callable[[dict[str, object]], _RecIFDResponse]", api.ArrApiResponse),
        cast("Callable[[str], _PatternFrame]", tp.parse_point_tp_csv),
        cast("Callable[[str], _PatternFrame]", tp.parse_areal_tp_csv),
    )


def _audit_ifd(path: Path, factory: Callable[[dict[str, object]], _RecIFDResponse]) -> dict[str, object]:
    """Compare one original, bounded ARR JSON response."""
    raw = _read_arr_bytes(path)
    document = parse_arr_json(raw, locator=str(path.absolute()))
    decoded = cast("dict[str, object]", json.loads(raw.decode("utf-8-sig")))
    return compare_ifd_tables(document, factory(decoded))


def _audit_patterns(path: Path, kind: PatternKind, parse_csv: Callable[[str], _PatternFrame]) -> dict[str, object]:
    """Compare the original validated CSV or every validated ZIP increments member."""
    source = read_pattern_file(path, kind=kind)
    rows: list[dict[str, object]] = []
    for csv_text in _pattern_csv_texts(source, zipped=path.suffix.lower() == ".zip"):
        try:
            rows.extend(parse_csv(csv_text).to_dict("records"))
        except (ValueError, TypeError, KeyError, IndexError) as exc:
            return {
                "kind": f"{kind}_TP_Increments",
                "source_sha256": source.source_sha256,
                "source_member_sha256": [member.sha256 for member in source.members],
                "status": "upstream_csv_parser_rejected",
                "reason": f"{type(exc).__name__}: {exc}",
            }
    result = compare_pattern_rows(source, rows)
    if len(source.members) > 1:
        result["zip_semantics"] = (
            "Each validated Increments.csv member compared independently; PyTUFLOW URL downloader "
            "takes only the first matching ZIP member, so URL/ZIP semantics are not established."
        )
    return result


def main() -> int:
    """Explicit source-only CLI; stdout is JSON and no file is written."""
    parser = argparse.ArgumentParser(description="Compare pinned PyTUFLOW 1.3.0 ARR sources, offline")
    parser.add_argument("--arr-json", type=Path)
    parser.add_argument("--point-patterns", type=Path, help="Original point Increments.csv or ZIP")
    parser.add_argument("--areal-patterns", type=Path, help="Original areal Increments.csv or ZIP")
    args = parser.parse_args()
    if not any((args.arr_json, args.point_patterns, args.areal_patterns)):
        parser.error("Provide at least one offline source file")
    try:
        ifd_factory, point_parser, areal_parser = _load_upstream()
    except (ImportError, OSError, AttributeError, ValueError) as exc:
        print(f"Optional PyTUFLOW 1.3.0 import check failed: {exc}", file=sys.stderr)
        return 2
    results: list[dict[str, object]] = []
    try:
        if args.arr_json is not None:
            results.append(_audit_ifd(args.arr_json, ifd_factory))
        sources: tuple[tuple[Path | None, PatternKind, Callable[[str], _PatternFrame]], ...] = (
            (args.point_patterns, "point", point_parser),
            (args.areal_patterns, "areal", areal_parser),
        )
        for path, kind, upstream_parser in sources:
            if path is not None:
                results.append(_audit_patterns(path, kind, upstream_parser))
    except (OSError, UnicodeError, ARRFormatError, ValueError, KeyError, TypeError) as exc:
        print(f"Source comparison failed closed: {exc}", file=sys.stderr)
        return 2
    report = {
        "schema_version": 1,
        "scope": "offline_source_only_not_native_acceptance",
        "pytuflow_version": PYTUFLOW_VERSION,
        "pytuflow_source_tag_commit": PYTUFLOW_TAG_COMMIT,
        "pytuflow_wheel_sha256_reference": PYTUFLOW_WHEEL_SHA256,
        "results": results,
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
