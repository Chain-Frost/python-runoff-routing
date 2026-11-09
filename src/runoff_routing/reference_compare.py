"""Read-only reference-to-reference checks; this is not solver acceptance."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from runoff_routing.reference import verify_manifest


@dataclass(frozen=True, slots=True)
class Tolerance:
    """Predeclared policy; never select thresholds from observed differences."""

    policy_id: str
    absolute: float
    relative: float
    near_zero_floor: float = 0.0

    def __post_init__(self) -> None:
        if not self.policy_id or any(
            not math.isfinite(value) or value < 0 for value in (self.absolute, self.relative, self.near_zero_floor)
        ):
            message = "Comparison tolerance must have an ID and finite nonnegative values"
            raise ValueError(message)


@dataclass(frozen=True, slots=True)
class Comparison:
    status: Literal["pass", "fail", "not_comparable", "invalid_evidence"]
    differences: tuple[str, ...]
    policy_id: str
    compared_points: int


def _report(root: Path, manifest: dict[str, Any]) -> Path:
    reports = [row["path"] for row in manifest["outputs"] if str(row["path"]).lower().endswith(".out")]
    if len(reports) != 1:
        message = "Comparison requires exactly one retained .out report per case"
        raise ValueError(message)
    return root / str(reports[0])


def _table(path: Path) -> tuple[list[str], list[list[str]], list[list[float]]]:
    text = path.read_text(encoding="utf-8", errors="replace").splitlines()
    headings = [i for i, line in enumerate(text) if line.split()[:2] == ["Inc", "Time"]]
    if len(headings) != 1:
        message = "Report does not contain exactly one Inc/Time table"
        raise ValueError(message)
    columns = text[headings[0]].split()
    if len(columns) < 3 or len(set(columns)) != len(columns):
        message = "Report has invalid or duplicate hydrograph identifiers"
        raise ValueError(message)
    rows: list[list[float]] = []
    raw_rows: list[list[str]] = []
    for line in text[headings[0] + 1 :]:
        tokens = line.split()
        if not tokens:
            if rows:
                break
            continue
        try:
            float(tokens[0])
        except ValueError:
            if rows:
                break
            continue
        if len(tokens) != len(columns):
            message = "Report contains a partial or extra hydrograph row"
            raise ValueError(message)
        try:
            values = [float(token) for token in tokens]
        except ValueError as exc:
            message = "Report contains a nonnumeric hydrograph row"
            raise ValueError(message) from exc
        if not all(map(math.isfinite, values)):
            message = "Report contains nonfinite values"
            raise ValueError(message)
        rows.append(values)
        raw_rows.append(tokens)
    if not rows:
        message = "Report contains no hydrograph rows"
        raise ValueError(message)
    return columns, raw_rows, rows


def _input_hashes(manifest: dict[str, Any]) -> dict[str, str]:
    return {
        key: str(value["source_fingerprint"]["sha256"])
        for key, value in manifest["inputs"].items()
        if key in ("catchment", "storm")
    }


def compare_cached(left_path: Path, right_path: Path, policy: Tolerance) -> Comparison:
    """Compare pinned same-profile cases, never launch either RORB executable."""
    problems = [*verify_manifest(left_path), *verify_manifest(right_path)]
    if problems:
        return Comparison("invalid_evidence", tuple(problems), policy.policy_id, 0)
    left: dict[str, Any] = json.loads(left_path.read_text(encoding="utf-8"))
    right: dict[str, Any] = json.loads(right_path.read_text(encoding="utf-8"))
    if (left["engine"] != right["engine"] or left["case_id"] != right["case_id"]):
        return Comparison("not_comparable", ("Engine identities or case IDs differ; GUI/CMD baselines stay separate",), policy.policy_id, 0)
    if (_input_hashes(left).keys() != {"catchment", "storm"} or _input_hashes(right).keys() != {"catchment", "storm"}):
        return Comparison("not_comparable", ("Catchment/storm source hashes are required",), policy.policy_id, 0)
    if left["effective_settings"] != right["effective_settings"] or _input_hashes(left) != _input_hashes(right):
        return Comparison("not_comparable", ("Effective settings or original catchment/storm hashes differ",), policy.policy_id, 0)
    if left["requested_print_locations"] != right["requested_print_locations"]:
        return Comparison("not_comparable", ("Requested print identities differ",), policy.policy_id, 0)
    if left["expected_steps"] is None or left["expected_steps"] != right["expected_steps"]:
        return Comparison("not_comparable", ("Unverified or mismatched expected timestep horizon",), policy.policy_id, 0)
    if left["outcome"] not in ("success", "zero_runoff") or right["outcome"] not in ("success", "zero_runoff"):
        return Comparison("not_comparable", ("One or both captures lack verified complete output",), policy.policy_id, 0)
    try:
        names_a, raw_a, a = _table(_report(left_path.parent, left))
        names_b, raw_b, b = _table(_report(right_path.parent, right))
    except (KeyError, ValueError) as exc:
        return Comparison("invalid_evidence", (str(exc),), policy.policy_id, 0)
    if names_a != names_b or len(a) != len(b) or len(a) != left["expected_steps"]:
        return Comparison("fail", ("Report columns or row counts differ",), policy.policy_id, 0)
    differences: list[str] = []
    compared = 0
    for index, (row_a, row_b) in enumerate(zip(a, b, strict=True), start=1):
        if raw_a[index - 1][:2] != raw_b[index - 1][:2]:
            differences.append(f"Row {index}: raw increment/time labels differ")
            continue
        for name, value_a, value_b in zip(names_a[2:], row_a[2:], row_b[2:], strict=True):
            compared += 1
            allowance = max(policy.absolute, policy.relative * max(abs(value_a), abs(value_b), policy.near_zero_floor))
            if abs(value_a - value_b) > allowance:
                differences.append(f"Row {index} {name}: {value_a} vs {value_b} (limit {allowance})")
    return Comparison("fail" if differences else "pass", tuple(differences), policy.policy_id, compared)
