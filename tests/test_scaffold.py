"""Scaffold checks only; these tests establish no hydrological equivalence."""

import tomllib
from pathlib import Path

ROOT = Path(__file__).absolute().parents[1]


def test_only_owner_approved_hosted_workflow() -> None:
    workflow_dir = ROOT / ".github" / "workflows"
    assert workflow_dir.is_dir()
    assert {path.name for path in workflow_dir.iterdir()} == {"quality.yml"}


def test_python_target_and_strict_typing() -> None:
    with (ROOT / "pyproject.toml").open("rb") as stream:
        config = tomllib.load(stream)
    assert config["project"]["requires-python"] == ">=3.14"
    assert config["tool"]["pyright"]["typeCheckingMode"] == "strict"


def test_namespace_is_present() -> None:
    assert (ROOT / "src" / "runoff_routing" / "__init__.py").is_file()
    assert (ROOT / "src" / "runoff_routing" / "py.typed").is_file()
