"""Protect the strict local lint policy without claiming that Ruff itself was executed."""

import tomllib
from pathlib import Path

ROOT = Path(__file__).absolute().parents[1]


def test_ruff_version_is_pinned_consistently() -> None:
    with (ROOT / "pyproject.toml").open("rb") as stream:
        project = tomllib.load(stream)
    with (ROOT / "ruff.toml").open("rb") as stream:
        ruff = tomllib.load(stream)
    assert ruff["required-version"] == "==0.16.6"
    assert "ruff==0.16.6" in project["project"]["optional-dependencies"]["dev"]
    assert "ruff" not in project["tool"]
    assert ruff["target-version"] == "py314"
    assert ruff["line-length"] == 120


def test_broad_rule_families_remain_enabled() -> None:
    with (ROOT / "ruff.toml").open("rb") as stream:
        ruff = tomllib.load(stream)
    expected = {
        "E",
        "W",
        "F",
        "B",
        "PLE",
        "PLW",
        "RUF",
        "UP",
        "FURB",
        "FLY",
        "SLOT",
        "ANN",
        "I",
        "ICN",
        "INP",
        "A",
        "ARG",
        "BLE",
        "C4",
        "C90",
        "EM",
        "ERA",
        "ISC",
        "N",
        "PERF",
        "PIE",
        "PLC",
        "RET",
        "RSE",
        "SIM",
        "SLF",
        "TRY",
        "G",
        "LOG",
        "S",
        "EXE",
        "PTH",
        "T10",
        "YTT",
        "NPY",
        "PD",
        "PT",
    }
    assert expected <= set(ruff["lint"]["select"])
    assert set(ruff["lint"]["ignore"]) == {"E111", "E114", "E117", "ISC001", "E501"}
    assert ruff["lint"]["mccabe"]["max-complexity"] == 10
    assert ruff["lint"]["per-file-ignores"] == {
        "tests/**/*.py": ["INP001", "S101"],
        "repo-scripts/**/*.py": ["INP001"],
    }


def test_linting_is_stable_and_non_mutating_by_default() -> None:
    with (ROOT / "ruff.toml").open("rb") as stream:
        ruff = tomllib.load(stream)
    assert ruff["preview"] is False
    assert ruff["fix"] is False
    assert ruff["unsafe-fixes"] is False
    assert ruff["force-exclude"] is True
    assert "tests" not in ruff["extend-exclude"]
    assert "tests/fixtures" not in ruff["extend-exclude"]
