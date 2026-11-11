"""Synthetic capture-contract tests; these never execute RORB_CMD or RORBwin."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from runoff_routing import reference
from runoff_routing.reference import Parameters, archive_reference, capture_cmd, render_par, verify_manifest
from runoff_routing.reference_compare import Tolerance, compare_cached


def _spec(tmp_path: Path, *, loss_model: int = 1, expected_steps: int | None = 2) -> Path:
    (tmp_path / "catchment.catg").write_bytes(b"original catchment\r\n")
    (tmp_path / "rain.stm").write_bytes(b"original storm\r\n")
    (tmp_path / "RORB_CMD.exe").write_bytes(b"fake binary - do NOT execute")
    spec = {
        "schema_version": 1,
        "case_id": "sample-TP01",
        "engine_kind": "RORB_CMD",
        "executable": "RORB_CMD.exe",
        "observed_banner": "synthetic test banner",
        "observed_version": "synthetic-test-build",
        "documentation_version": "6.31 mentioned in guide, not verified binary version",
        "catchment": "catchment.catg",
        "storm": "rain.stm",
        "parameters": {
            "kc": "15",
            "m": "0.8",
            "initial_loss_mm": "20",
            "continuing": "0.5" if loss_model == 2 else "2",
            "loss_model": loss_model,
        },
        "timeout_seconds": 5,
        "provenance": {"source": "synthetic", "redistribution": "tests only"},
        "generator": {"name": "test ensemble exporter", "revision": "synthetic", "event_to_file": "sample-TP01"},
        "effective_settings": {"timestep_hours": "1", "horizon": "2", "isa_mapping": [1], "burst_mapping": [1]},
        "requested_print_locations": {"Hyd001": "verified outlet number 7", "Hyd002": "verified other location"},
        "expected_steps": expected_steps,
    }
    spec_path = tmp_path / "spec.json"
    spec_path.write_text(json.dumps(spec), encoding="utf-8")
    return spec_path


def _read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _mock_execution(
    monkeypatch: pytest.MonkeyPatch,
    *,
    report: str | None = None,
    stderr: bytes = b"",
    status: int = 0,
    log: str = "",
) -> None:
    if report is None:
        report = "Inc Time Hyd001 Hyd002\n1 0 1 2\n2 1 3 4\nEnd\n"

    def fake_run(*args: object, **kwargs: object) -> subprocess.CompletedProcess[bytes]:
        del args
        root = kwargs["cwd"]
        assert isinstance(root, Path)
        assert root.is_dir()
        par = root / "reference.par"
        contents = par.read_text()
        assert str(root / "catchment.catg") in contents
        assert str(root / "storm.stm") in contents
        if report:
            (root / "native.out").write_text(report)
        if log:
            (root / "native.log").write_text(log)
        return subprocess.CompletedProcess(["mock"], status, b"mock stdout\r\n", stderr)

    monkeypatch.setattr(subprocess, "run", fake_run)


def test_one_isa_one_burst_renderer_and_ambiguous_loss_flag(tmp_path: Path) -> None:
    parameters = Parameters.from_mapping(
        {"kc": 15, "m": "0.8", "initial_loss_mm": 20, "continuing": "0.5", "loss_model": 2}
    )
    par = render_par(tmp_path / "a.catg", tmp_path / "b.stm", parameters)
    assert b"Lossmodel:2" in par
    assert b"ISA 1    :15,0.8" in par
    assert b"ISA 1    :20,0.5" in par
    assert parameters.as_effective()["continuing_unit"] == "runoff_coefficient"
    with pytest.raises(ValueError, match="Only loss_model"):
        Parameters.from_mapping({"kc": 15, "m": 0.8, "initial_loss_mm": 20, "continuing": 2, "loss_model": 3})
    with pytest.raises(ValueError, match="finite"):
        Parameters.from_mapping({"kc": "NaN", "m": 0.8, "initial_loss_mm": 20, "continuing": 2, "loss_model": 1})


@pytest.mark.parametrize("coefficient", ["0", "0.5", "1"])
def test_valid_runoff_coefficient_bounds(coefficient: str) -> None:
    parameters = Parameters.from_mapping(
        {"kc": 10, "m": 0.8, "initial_loss_mm": 20, "continuing": coefficient, "loss_model": 2}
    )
    assert str(parameters.continuing) == coefficient


def test_invalid_example_coefficient_rejected_before_capture(tmp_path: Path) -> None:
    spec_path = _spec(tmp_path, loss_model=2)
    spec = _read(spec_path)
    spec["parameters"]["continuing"] = "2"
    spec_path.write_text(json.dumps(spec))
    captures = tmp_path / "captures"
    with pytest.raises(ValueError, match="Runoff coefficient"):
        capture_cmd(spec_path, captures, execute=True)
    assert not captures.exists()


def test_preflight_never_launches_or_writes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    spec_path = _spec(tmp_path)

    def fail(*args: object, **kwargs: object) -> None:
        del args, kwargs
        pytest.fail("Implicit reference executable launch")

    monkeypatch.setattr(subprocess, "run", fail)
    output = tmp_path / "captures"
    assert capture_cmd(spec_path, output) is None
    assert not output.exists()


def test_cmd_capture_preserves_inputs_and_manifest(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    spec = _spec(tmp_path)
    orig = (tmp_path / "catchment.catg").read_bytes(), (tmp_path / "rain.stm").read_bytes()
    _mock_execution(monkeypatch)
    manifest_file = capture_cmd(spec, tmp_path / "captures", execute=True)
    assert manifest_file is not None
    manifest = _read(manifest_file)
    assert manifest["outcome"] == "success"
    assert manifest["engine"]["observed_version"] == "synthetic-test-build"
    assert manifest["engine"]["documentation_version"].startswith("6.31")
    assert manifest["inputs"]["parameters"]["generated"]
    assert manifest["hydrograph_check"]["rows"] == 2
    assert manifest["capture"]["return_code"] == 0
    assert manifest["capture"]["stdout.bin"]["sha256"]
    assert verify_manifest(manifest_file) == []
    assert orig == ((tmp_path / "catchment.catg").read_bytes(), (tmp_path / "rain.stm").read_bytes())
    assert sorted(p.name for p in manifest_file.parent.iterdir()) == [
        "catchment.catg",
        "manifest.json",
        "native.out",
        "reference.par",
        "stderr.bin",
        "stdout.bin",
        "storm.stm",
    ]


@pytest.mark.parametrize(
    ("report", "stderr", "code", "log", "expected"),
    [
        ("", b"", 0, "", "missing_output"),
        ("Inc Time Hyd001 Hyd002\n1 0 0 0\n2 1 0 0\n", b"", 0, "", "zero_runoff"),
        ("Inc Time Hyd001 Hyd002\n1 0 1 2\n", b"", 0, "", "incomplete_output"),
        ("Inc Time Hyd001 Hyd002\n1 0 1 2\n2 1 nan 5\n", b"", 0, "", "incomplete_output"),
        ("", b"Fatal: Native calculation aborted", 0, "", "native_error"),
        ("", b"", 7, "", "nonzero_exit"),
        ("Inc Time Hyd001 Hyd002\n1 0 1 2\n2 1 4 3\n", b"", 0, "Error: unstable routing", "native_error"),
        ("Inc Time Hyd001 Hyd002\n1 0 1 2\n2 1 4 3\n", b"", 0, "Warning: check run", "captured_unverified"),
    ],
)
def test_outcomes_are_distinct(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, report: str, stderr: bytes, code: int, log: str, expected: str
) -> None:
    _mock_execution(monkeypatch, report=report, stderr=stderr, status=code, log=log)
    manifest = capture_cmd(_spec(tmp_path), tmp_path / "captures", execute=True)
    assert manifest is not None
    assert _read(manifest)["outcome"] == expected
    assert verify_manifest(manifest) == []


def test_timeout_retains_partial_streams(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def timeout(*args: object, **kwargs: object) -> None:
        del args, kwargs
        raise subprocess.TimeoutExpired(["mock"], 5, output=b"partial stdout", stderr=b"partial stderr")

    monkeypatch.setattr(subprocess, "run", timeout)
    manifest_path = capture_cmd(_spec(tmp_path), tmp_path / "captures", execute=True)
    assert manifest_path is not None
    assert _read(manifest_path)["outcome"] == "timeout"
    assert (manifest_path.parent / "stdout.bin").read_bytes() == b"partial stdout"
    assert (manifest_path.parent / "stderr.bin").read_bytes() == b"partial stderr"


def test_executable_permission_denial_retained(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def denied(*args: object, **kwargs: object) -> None:
        del args, kwargs
        raise PermissionError(13, "WinError 5 permission denied")

    monkeypatch.setattr(subprocess, "run", denied)
    manifest = capture_cmd(_spec(tmp_path), tmp_path / "captures", execute=True)
    assert manifest is not None
    assert _read(manifest)["outcome"] == "launch_failed"
    assert b"permission denied" in (manifest.parent / "stderr.bin").read_bytes()


def test_unknown_horizon_is_not_accepted(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _mock_execution(monkeypatch)
    manifest = capture_cmd(_spec(tmp_path, expected_steps=None), tmp_path / "captures", execute=True)
    assert manifest is not None
    assert _read(manifest)["outcome"] == "captured_unverified"


def test_archive_gui_offline_and_detect_tampering(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    spec_path = _spec(tmp_path)
    spec = _read(spec_path)
    (tmp_path / "RORBwin.exe").write_bytes(b"different native reference binary")
    (tmp_path / "saved.par").write_bytes(b"saved GUI settings")
    (tmp_path / "gui.out").write_bytes(b"original GUI report")
    spec.update(
        {
            "engine_kind": "RORBwin",
            "executable": "RORBwin.exe",
            "inputs": {"catchment": "catchment.catg", "storm": "rain.stm", "configuration": "saved.par"},
            "outputs": {"gui.out": "gui.out"},
            "gui_effective_settings": {"loss_method": "verified manually", "timestep": 0.25},
        }
    )
    spec_path.write_text(json.dumps(spec))

    def deny(*args: object, **kwargs: object) -> None:
        del args, kwargs
        pytest.fail("Manual archiving must never invoke native processes")

    monkeypatch.setattr(subprocess, "run", deny)
    manifest_path = archive_reference(spec_path, tmp_path / "archives")
    data = _read(manifest_path)
    assert data["engine"]["kind"] == "RORBwin"
    assert data["effective_settings"]["gui"]["loss_method"] == "verified manually"
    assert data["outcome"] == "captured_unverified"
    assert verify_manifest(manifest_path) == []
    (manifest_path.parent / "outputs" / "gui.out").write_bytes(b"tampered")
    assert "Evidence hash mismatch" in verify_manifest(manifest_path)[0]


def test_cached_same_profile_comparison_and_timing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    spec = _spec(tmp_path)
    _mock_execution(monkeypatch)
    first = capture_cmd(spec, tmp_path / "captures", execute=True)
    second = capture_cmd(spec, tmp_path / "captures", execute=True)
    assert first is not None
    assert second is not None
    policy = Tolerance("test-exact", 0, 0)
    assert compare_cached(first, second, policy).status == "pass"
    (second.parent / "native.out").write_text("Inc Time Hyd001 Hyd002\n1 0 1 2\n2 1.5 3 4\nEnd\n")
    # A modified original reference file must fail integrity before numerical comparison.
    assert compare_cached(first, second, policy).status == "invalid_evidence"
    with pytest.raises(ValueError, match="finite"):
        Tolerance("bad", float("nan"), 0)


def test_no_linux_or_synthetic_run_is_native_acceptance(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _mock_execution(monkeypatch)
    spec = _spec(tmp_path)
    result = capture_cmd(spec, tmp_path / "captures", execute=True)
    assert result is not None
    record = _read(result)
    assert (
        record["environment"]["python"] == f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    )
    assert record["engine"]["observed_version"] == "synthetic-test-build"


def test_unknown_build_and_loss_two_are_not_claimed_verified(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _mock_execution(monkeypatch)
    spec_path = _spec(tmp_path, loss_model=2)
    spec = _read(spec_path)
    spec["observed_banner"] = None
    spec_path.write_text(json.dumps(spec))
    manifest = capture_cmd(spec_path, tmp_path / "captures", execute=True)
    assert manifest is not None
    data = _read(manifest)
    assert data["outcome"] == "captured_unverified"
    assert "observed_banner" in data["provenance_gaps"]
    assert "loss_model_2_native_semantics_unverified" in data["provenance_gaps"]
    assert data["hydrograph_check"]["rows"] == 2


def test_unsupported_multi_isa_rejected_before_side_effects(tmp_path: Path) -> None:
    spec_path = _spec(tmp_path)
    spec = _read(spec_path)
    spec["effective_settings"]["isa_mapping"] = [1, 2]
    spec_path.write_text(json.dumps(spec))
    target = tmp_path / "captures"
    with pytest.raises(ValueError, match="one explicit ISA"):
        capture_cmd(spec_path, target, execute=True)
    assert not target.exists()


def test_evidence_inventory_error_preserves_manifest(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:

    _mock_execution(monkeypatch)

    def deny_inventory(root: Path, excluded: set[Path]) -> list[dict[str, str | int]]:
        del root, excluded
        raise PermissionError(13, "Unable to enumerate native directory")

    monkeypatch.setattr(reference, "_files", deny_inventory)
    manifest = capture_cmd(_spec(tmp_path), tmp_path / "captures", execute=True)
    assert manifest is not None
    record = _read(manifest)
    assert record["outcome"] == "inventory_failed"
    assert "Unable to enumerate" in record["diagnostics"]["errors"][0]
    assert (manifest.parent / "stdout.bin").read_bytes().startswith(b"mock stdout")
