"""Opt-in, read-only S1 private-corpus regression; never writes/copies fixtures.

Run: py -3.14 repo-scripts/check_private_parser_corpus.py [local-corpus-directory]
The corpus remains in the private investigations checkout and is not a CI input.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any, cast

from runoff_routing.rorb_codec import FormatProblem, original_bytes, parse_catg, parse_cmd_par, parse_design_stm
from runoff_routing.rorb_model import RunModel, from_json, to_json


def _index_audit(root: Path) -> int:
    raw: object = json.loads((root / "FILE_INDEX.json").read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        message = "Private corpus index must be a JSON object"
        raise TypeError(message)
    index = cast("dict[str, Any]", raw)
    entries = cast("dict[str, dict[str, Any]]", index["files"])
    for name, expected in entries.items():
        path = root / name
        data = path.read_bytes()
        if len(data) != expected["size_bytes"] or hashlib.sha256(data).hexdigest() != expected["sha256"]:
            message = f"Private corpus evidence changed or missing: {name}"
            raise ValueError(message)
    return len(entries)


def _inputs(root: Path, case_name: str) -> dict[str, Path]:
    raw: object = json.loads((root / "catalogue.json").read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        message = "Private corpus catalogue must be an object"
        raise TypeError(message)
    catalogue = cast("dict[str, Any]", raw)
    matches = [item for item in catalogue["cases"] if item["case_id"] == case_name]
    if len(matches) != 1:
        message = f"Expected exactly one case in private catalogue: {case_name}"
        raise ValueError(message)
    return {item["identity"]: root / item["path"] for item in matches[0]["inputs"]}


def _run(root: Path) -> None:  # noqa: C901 -- ordered immutable evidence audits
    count = _index_audit(root)
    files = _inputs(root, "review-design-baseline")
    catg = parse_catg(files["catchment"].read_bytes())
    stm = parse_design_stm(files["storm"].read_bytes())
    par = parse_cmd_par(files["parameters"].read_bytes())
    for item in (catg, stm, par):
        if hashlib.sha256(original_bytes(item)).hexdigest() != item.source.sha256:
            message = "Unchanged original-source mode failed"
            raise ValueError(message)
    run = RunModel(par.model, catg.model, stm.model)
    if from_json(to_json(run)) != run:
        message = "Private baseline JSON model did not round-trip"
        raise ValueError(message)
    if len(run.catchment.subareas) != 5 or len(run.storm.percentages) != 24:
        message = "Private baseline source counts differ from original evidence"
        raise ValueError(message)
    broken = _inputs(root, "failure-truncated-storm")
    try:
        parse_design_stm(broken["storm"].read_bytes())
    except FormatProblem as exc:
        if exc.status != "invalid":
            message = f"Truncated storm classified as {exc.status}, expected invalid"
            raise ValueError(message) from exc
    else:
        message = "Truncated private storm was accepted"
        raise ValueError(message)
    invalid = _inputs(root, "failure-invalid-code")
    try:
        parse_catg(invalid["catchment"].read_bytes())
    except FormatProblem as exc:
        if exc.status != "unsupported":
            message = f"Unknown control classified as {exc.status}, expected unsupported"
            raise ValueError(message) from exc
    else:
        message = "Uncharacterised private control code was accepted"
        raise ValueError(message)
    if _index_audit(root) != count:
        message = "Private corpus index changed during read-only regression"
        raise ValueError(message)
    print(f"PASS: {count} unchanged private evidence files; baseline, failure and typed JSON")


if __name__ == "__main__":
    if len(sys.argv) > 2:
        message = "Accepts zero or one explicit private corpus directory"
        raise ValueError(message)
    default = (
        Path(__file__).absolute().parents[2]
        / "runoff-routing-investigations"
        / "tests"
        / "fixtures"
        / "rorb"
        / "native-corpus"
    )
    _run(Path(sys.argv[1]) if len(sys.argv) == 2 else default)
