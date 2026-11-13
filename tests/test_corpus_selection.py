"""Offline batch case selection covers all original corpus outcomes.

No private fixtures or native executables are used.
"""

from __future__ import annotations

import runpy
from collections.abc import Callable
from pathlib import Path
from typing import cast

import pytest


def _choose() -> Callable[[dict[str, object]], tuple[str, ...]]:
    script = Path(__file__).absolute().parents[1] / "repo-scripts" / "s2_compare_corpus.py"
    namespace = runpy.run_path(str(script), run_name="offline_selection_test")
    helper: object = namespace["select_case_ids"]
    assert callable(helper)
    return cast("Callable[[dict[str, object]], tuple[str, ...]]", helper)


def _catalogue() -> dict[str, object]:
    return {
        "schema_version": 1,
        "cases": [
            {"case_id": "computed-cmd", "engine": {"kind": "RORB_CMD"}, "capture_outcome": "success"},
            {"case_id": "unverified-gui", "engine": {"kind": "RORBwin"}, "capture_outcome": "captured_unverified"},
            {"case_id": "native-failure", "engine": {"kind": "RORB_CMD"}, "capture_outcome": "native_error"},
            {"case_id": "incomplete", "engine": {"kind": "RORB_CMD"}, "capture_outcome": "incomplete_output"},
        ],
    }


def test_default_selection_keeps_all_engine_profiles_and_outcomes() -> None:
    assert _choose()(_catalogue()) == ("computed-cmd", "unverified-gui", "native-failure", "incomplete")


@pytest.mark.parametrize(
    "corruption",
    ["version", "missing", "empty", "duplicate", "missing_id", "empty_id"],
)
def test_corpus_selection_rejects_invalid_inventory(corruption: str) -> None:
    record = _catalogue()
    if corruption == "version":
        record["schema_version"] = 2
    elif corruption == "missing":
        record.pop("cases")
    elif corruption == "empty":
        record["cases"] = []
    elif corruption == "duplicate":
        record["cases"] = [{"case_id": "same"}, {"case_id": "same"}]
    elif corruption == "missing_id":
        record["cases"] = [{"engine": {"kind": "RORB_CMD"}}]
    else:
        record["cases"] = [{"case_id": ""}]
    with pytest.raises((TypeError, ValueError), match=r"catalogue|case_id|case"):
        _choose()(record)
