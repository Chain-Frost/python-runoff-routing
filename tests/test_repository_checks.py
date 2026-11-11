"""Exercise the extracted Markdown-link checker without any model execution."""

import runpy
from collections.abc import Callable
from pathlib import Path
from typing import cast

CHECKS = runpy.run_path(str(Path(__file__).absolute().parents[1] / "repo-scripts" / "check_repository.py"))
MARKDOWN_ERRORS = cast("Callable[[Path, str], list[str]]", CHECKS["markdown_errors"])


def test_local_markdown_links_and_anchors(tmp_path: Path) -> None:
    document = tmp_path / "README.md"
    (tmp_path / "local guide.md").write_text("# Local guide\n", encoding="utf-8")
    document.write_text("[Guide](local%20guide.md#local-guide) [Here](#local)\n", encoding="utf-8")
    assert MARKDOWN_ERRORS(document, "README.md") == []


def test_missing_link_is_reported(tmp_path: Path) -> None:
    document = tmp_path / "README.md"
    document.write_text("[Missing](missing.md)\n", encoding="utf-8")
    assert MARKDOWN_ERRORS(document, "README.md") == ["Broken relative link in README.md: missing.md"]


def test_external_links_are_not_fetched(tmp_path: Path) -> None:
    document = tmp_path / "README.md"
    document.write_text("[Site](https://example.invalid/) [Mail](mailto:review@example.invalid)\n", encoding="utf-8")
    assert MARKDOWN_ERRORS(document, "README.md") == []


def test_only_owner_approved_quality_workflow_is_allowed() -> None:
    assert CHECKS["ALLOWED_WORKFLOWS"] == {".github/workflows/quality.yml"}
