"""Protect the inert future-release proposal without activating a publisher."""

from pathlib import Path

ROOT = Path(__file__).absolute().parents[1]
TEMPLATE = ROOT / "packaging" / "pypi" / "publish.yml.in"


def test_future_release_is_inert_and_explicitly_selected() -> None:
    source = TEMPLATE.read_text(encoding="utf-8")
    assert not (ROOT / ".github" / "workflows" / "publish-selected.yml").exists()
    assert "workflow_dispatch:" in source
    assert "workflow_run:" not in source
    assert "source_sha:" in source
    assert "quality_run_id:" in source
    assert "release_tag:" in source
    assert "PYPI_ONE_SHOT_ENABLED" not in source
    assert "github.run_attempt == 1" in source
    assert "github.ref == 'refs/heads/main'" in source
    assert "vars.PYPI_PUBLISH_ENABLED == 'true'" in source


def test_future_release_qualifies_both_main_lanes_and_artifacts() -> None:
    source = TEMPLATE.read_text(encoding="utf-8")
    assert '.head_sha == $sha' in source
    assert '.event == "push"' in source
    assert '.path == ".github/workflows/quality.yml"' in source
    assert "windows-python-versions (3.11)" in source
    assert "windows-python-versions (3.14)" in source
    assert "windows-python-313" in source
    assert "auto_release_version.py stamp" in source
    assert "check_release.py --tag=" in source
    assert "twine check --strict" in source
    assert "[mcp,dev,research]" in source
    assert "runoff_routing.tuflow_rainfall --help" in source
    assert "cmp " in source


def test_future_upload_separates_build_and_oidc_and_fails_closed() -> None:
    source = TEMPLATE.read_text(encoding="utf-8")
    build, remainder = source.split("\n  publish:\n")
    upload, release = remainder.split("\n  release:\n")
    assert "id-token: write" not in build
    assert "environment:\n      name: pypi" in upload
    assert "id-token: write" in upload
    assert "actions/checkout@" not in upload
    assert "pip install" not in upload
    assert "digest-mismatch: error" in upload
    assert ".can_admins_bypass == false" in upload
    assert '.branch_policies[0].name == "main"' in upload
    assert 'version in project["releases"]' in upload
    assert "skip-existing: 'false'" in upload
    assert "id-token: write" not in release
    assert "needs.publish.result == 'success'" in release
