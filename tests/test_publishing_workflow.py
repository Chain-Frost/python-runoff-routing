"""Protect the selected-release workflow and the retired first-project preflight."""

import re
from pathlib import Path

WORKFLOW = Path(__file__).absolute().parents[1] / ".github" / "workflows" / "publish.yml"


def test_publisher_requires_manual_current_main_and_successful_quality() -> None:
    source = WORKFLOW.read_text(encoding="utf-8")
    assert "workflow_dispatch:" in source
    assert "workflow_run:" not in source
    assert "\n  push:" not in source
    assert "\n  pull_request:" not in source
    assert "PYPI_ONE_SHOT_ENABLED" not in source
    assert "PYPI_PUBLISH_ENABLED" not in source
    assert "inputs." not in source
    assert "github.event_name == 'workflow_dispatch'" in source
    assert "github.ref == 'refs/heads/main'" in source
    assert "github.run_attempt == 1" in source
    assert ".head_sha == $sha" in source
    assert '.event == "push"' in source
    assert '.path == ".github/workflows/quality.yml"' in source
    assert "windows-python-versions (3.11)" in source
    assert "windows-python-versions (3.14)" in source
    assert "windows-python-313" in source
    assert 'ZoneInfo("Australia/Perth")' in source
    assert "auto_release_version.py next" in source
    assert "auto_release_version.py stamp" in source


def test_publisher_permissions_and_protected_upload() -> None:
    source = WORKFLOW.read_text(encoding="utf-8")
    build, after_build = source.split("\n  tag:\n", 1)
    tag, after_tag = after_build.split("\n  publish:\n", 1)
    publish, release = after_tag.split("\n  release:\n", 1)
    assert source.count("id-token: write") == 1
    assert "id-token: write" in publish
    assert "environment:\n      name: pypi" in publish
    assert "actions/checkout@" not in publish
    assert "pip install" not in publish
    assert "contents: write" not in build
    assert "contents: write" not in publish
    assert "contents: write" in tag
    assert "contents: write" in release
    assert "actions: write" not in source
    assert "digest-mismatch: error" in publish
    assert "skip-existing: 'false'" in publish
    assert "needs: [build, tag]" in publish
    assert "createRef" in tag
    assert "createRelease" not in tag
    assert "createRelease" in release
    assert "needs: [build, publish]" in release
    assert "needs.publish.result == 'success'" in release
    assert "calendar_parts(version) <= calendar_parts(released)" in publish


def test_missing_unprotected_environment_blocks_publication() -> None:
    source = WORKFLOW.read_text(encoding="utf-8")
    assert source.count("environments/pypi") == 4
    assert source.count('reviewer.login == "Chain-Frost"') == 2
    assert source.count(".can_admins_bypass == false") == 2
    assert source.count("deployment_branch_policy.custom_branch_policies == true") == 2
    assert source.count("deployment_branch_policy.protected_branches == false") == 2
    assert source.count("deployment-branch-policies?per_page=100") == 2
    assert source.count(".total_count == 1") == 2
    assert source.count("(.branch_policies | length) == 1") == 2
    assert source.count('.branch_policies[0].name == "main"') == 2
    assert source.count('.branch_policies[0].type == "branch"') == 2
    assert source.count("actions: read") == 2


def test_release_checks_exact_artifacts_and_installed_apis() -> None:
    source = WORKFLOW.read_text(encoding="utf-8")
    assert "check_release.py --tag=" in source
    assert "twine check --strict" in source
    assert "-r requirements-catg.txt -e '.[dev]'" in source
    assert 'pip install "${files[0]}"' in source
    assert 'pip install "${files[0]}[mcp,dev,research]"' in source
    assert '-m pip install -r "$GITHUB_WORKSPACE/requirements-catg.txt"' in source
    assert "from runoff_routing.rorb_readers.output_reader import bind_output_site_columns" in source
    assert "runoff_routing.tuflow_rainfall --help" in source
    assert "from ryan_library" not in source
    assert "verify_installed_wheel" in source
    assert "cmp " in source


def test_all_actions_expressions_are_closed() -> None:
    """Reject unclosed and surplus braces in privileged workflow expressions."""
    expression = re.compile(r"\$\{\{[^{}]+\}\}")
    for line in WORKFLOW.read_text(encoding="utf-8").splitlines():
        if "${{" not in line:
            continue
        without_expressions = expression.sub("", line)
        assert "${{" not in without_expressions, f"Unclosed GitHub expression: {line}"
        assert "{" not in without_expressions, f"Stray GitHub expression brace: {line}"
        assert "}" not in without_expressions, f"Stray GitHub expression brace: {line}"


def test_activation_requires_read_only_live_configuration_preflight() -> None:
    quality = WORKFLOW.with_name("quality.yml").read_text(encoding="utf-8")
    preflight = quality.split("  release-configuration:\n", 1)[1].split("  windows-python-313:\n", 1)[0]
    assert "github.event.pull_request.number == 220" in preflight
    assert "github.event.pull_request.head.repo.full_name == github.repository" in preflight
    assert "vars.PYPI_ONE_SHOT_ENABLED" in preflight
    assert "id-token:" not in preflight
    assert "actions: write" not in preflight
    assert "contents: write" not in preflight
    assert "actions: read" in preflight
    assert "environment:" not in preflight
    assert "deployment-branch-policies?per_page=100" in preflight
    assert "gh api" in preflight
    aggregate = quality.split("  windows-python-313:\n", 1)[1]
    assert "needs: [windows-python-versions, release-configuration]" in aggregate
    assert "$env:CONFIG_RESULT -ne 'success'" in aggregate
    assert "$env:CONFIG_RESULT -ne 'skipped'" in aggregate
