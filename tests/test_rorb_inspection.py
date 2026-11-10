"""Synthetic, read-only RORB input/output inspection contracts (no native engine)."""

from __future__ import annotations

import hashlib
import json
import subprocess
from collections.abc import Callable
from decimal import Decimal
from pathlib import Path

import pytest

from runoff_routing.reference import Parameters, render_par
from runoff_routing.rorb_inspect import inspect_file


def _write(tmp_path: Path, data: str, name: str = "case.par", *, crlf: bool = False) -> Path:
    path = tmp_path / name
    path.write_bytes(data.replace("\n", "\r\n").encode("utf-8") if crlf else data.encode("utf-8"))
    return path


def _cmd(*, lumped: bool = True, model: int = 1, extra: str = "", bursts: int = 1) -> str:
    lines = [
        "# BEGIN",
        "Cat file :first.catg",
        "Stm file :TP03.stm",
        f"Lumped kc:{'T' if lumped else 'F'}",
        "Verbosity:3",
        f"Lossmodel:{model}",
        "Num ISA  :2",
        "ISA 1    :12,0.8",
    ]
    if not lumped:
        lines.append("ISA 2    :25,1")
    lines.extend([f"Num burst:{bursts}", "ISA 1    :20,2", "ISA 2    :11,3", *([extra] if extra else []), "# END"])
    return "\n".join(lines) + "\n"


def _out(rows: str = "0 0.000 0 0\n1 0.333 12 10\n2 0.667 0 0\n") -> str:
    return (
        "RORBWin Output File\nProgram version 6.45\n"
        "Time increment (hours)= 3.33D-1\nDuration of calculations: 2\n"
        "Site Description\n01 Calculated hydrograph, outlet\n"
        "Inc Time Hyd0001 Hyd0002\n" + rows + "End of hydrograph\n"
    )


@pytest.mark.parametrize("lumped", [True, False])
def test_cmd_read_preserves_raw_bytes_and_isa_order(tmp_path: Path, lumped: bool) -> None:
    source = _write(tmp_path, _cmd(lumped=lumped), crlf=True)
    before = source.read_bytes()
    doc = inspect_file(source)
    assert doc.status == "parsed"
    assert doc.source.sha256 == hashlib.sha256(before).hexdigest()
    assert doc.source.encoding == "utf-8-sig"
    assert source.read_bytes() == before
    assert doc.parameters is not None
    assert doc.parameters.catchment_reference == "first.catg"
    assert doc.parameters.storm_reference == "TP03.stm"
    assert doc.parameters.num_isa == 2
    assert doc.parameters.num_bursts == 1
    assert [p.isa for p in doc.parameters.routing] == ([1] if lumped else [1, 2])
    assert [p.isa for p in doc.parameters.losses] == [1, 2]
    assert doc.parameters.losses[1].initial_loss_mm == Decimal(11)
    assert doc.fields[0].line == 2
    assert doc.fields[-1].raw.startswith("ISA 2")
    assert not any(d.severity == "error" for d in doc.diagnostics)
    assert json.loads(doc.to_json())["source"]["sha256"] == doc.source.sha256


def test_par_generated_by_s0_writer_round_trips(tmp_path: Path) -> None:
    params = Parameters.from_mapping(
        {"kc": "15", "m": "0.8", "initial_loss_mm": "20", "continuing": "2", "loss_model": 1}
    )
    path = tmp_path / "native.par"
    path.write_bytes(render_par(Path("model.catg"), Path("rain.stm"), params))
    doc = inspect_file(path)
    assert doc.parameters is not None
    assert doc.parameters.routing[0].kc == params.kc
    assert doc.parameters.losses[0].continuing == params.continuing
    assert doc.parameters.loss_model == 1
    assert doc.status == "parsed"


def test_fortran_exponent_and_loss_flag_two(tmp_path: Path) -> None:
    text = _cmd(model=2).replace("12,0.8", "1.2D1,8d-1")
    doc = inspect_file(_write(tmp_path, text))
    assert doc.parameters is not None
    assert doc.parameters.routing[0].kc == Decimal(12)
    assert doc.parameters.routing[0].m == Decimal("0.8")
    assert any(d.code == "loss_2_unverified" for d in doc.diagnostics)


def _replace(old: str, new: str) -> Callable[[str], str]:
    """Explicitly typed synthetic file mutation, without lambda inference gaps."""
    def apply(text: str) -> str:
        return text.replace(old, new)
    return apply


@pytest.mark.parametrize(
    ("mutation", "expected_status"),
    [
        (_replace("# BEGIN", "saved GUI settings"), "unsupported"),
        (_replace("# END", "# WRONG"), "invalid"),
        (_replace("Num burst:1", "Num burst:2"), "unsupported"),
        (_replace("Lossmodel:1", "Lossmodel:4"), "unsupported"),
        (_replace("Num ISA  :2", "Num ISA  :3"), "invalid"),
        (_replace("ISA 2    :11,3", "ISA 1    :11,3"), "invalid"),
        (_replace("12,0.8", "-12,0.8"), "invalid"),
        (_replace("12,0.8", "nan,0.8"), "invalid"),
        (_replace("ISA 2    :11,3", "ISA 2    :11"), "invalid"),
        (_replace("# END", "EXTRA\n# END"), "unsupported"),
        (_replace("Stm file :TP03.stm", "Stm file :"), "invalid"),
    ],
)
def test_parameter_fail_closed(tmp_path: Path, mutation: Callable[[str], str], expected_status: str) -> None:
    doc = inspect_file(_write(tmp_path, mutation(_cmd())))
    assert doc.status == expected_status
    assert doc.parameters is None
    assert doc.diagnostics


def test_out_keeps_raw_times_and_columns(tmp_path: Path) -> None:
    source = _write(tmp_path, _out(), "run.out")
    doc = inspect_file(source)
    assert doc.status == "partial"
    assert doc.hydrographs is not None
    assert doc.hydrographs.columns == ("Hyd0001", "Hyd0002")
    assert [r.raw_time for r in doc.hydrographs.rows] == ["0.000", "0.333", "0.667"]
    assert [r.increment for r in doc.hydrographs.rows] == [0, 1, 2]
    assert [r.values[0] for r in doc.hydrographs.rows] == [0, 12, 0]
    assert doc.hydrographs.time_increment_hours == Decimal("0.333")
    assert doc.hydrographs.reported_duration_increments == 2
    assert any(d.code == "print_identity_unverified" for d in doc.diagnostics)


@pytest.mark.parametrize(
    "rows",
    [
        "0 0 0 0\n1 0.333 ******** 1\n2 0.667 0 0\n",
        "0 0 0 0\n1 0.333 NaN 1\n2 0.667 0 0\n",
        "0 0 0 0\n1 0.333 1\n2 0.667 0 0\n",
        "0 0 0 0\n2 0.333 1 1\n3 0.667 0 0\n",
        "0 0 0 0\n1 0.200 1 1\n2 0.667 0 0\n",
        "0 0 0 0\n1 0.333 1 1\n",
        "0 0 0 0\n1 0.333 1 1\n2 0.333 0 0\n",
    ],
)
def test_report_malformed_is_not_valid_prefix(tmp_path: Path, rows: str) -> None:
    doc = inspect_file(_write(tmp_path, _out(rows), "bad.out"))
    assert doc.status == "invalid"
    assert doc.hydrographs is None


def test_output_never_infers_completion_or_time_axis(tmp_path: Path) -> None:
    text = _out().replace("Duration of calculations: 2\n", "").replace("Time increment (hours)= 3.33D-1\n", "")
    doc = inspect_file(_write(tmp_path, text, "unverified.out"))
    assert doc.status == "partial"
    assert {d.code for d in doc.diagnostics} >= {"completion_unverified", "timestep_unverified"}


def test_duplicate_output_labels_rejected(tmp_path: Path) -> None:
    text = _out().replace("Hyd0002", "Hyd0001")
    assert inspect_file(_write(tmp_path, text, "bad.out")).status == "invalid"


@pytest.mark.parametrize("extension", ["cat", "catg", "dat", "stm"])
def test_uncharacterised_file_types_not_claimed_supported(tmp_path: Path, extension: str) -> None:
    doc = inspect_file(_write(tmp_path, "native model data", f"model.{extension}"))
    assert doc.status == "unsupported"
    assert doc.parameters is None
    assert doc.hydrographs is None


def test_read_only_inspector_cannot_launch_native_process(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def prohibited(*_args: object, **_kwargs: object) -> None:
        pytest.fail("Inspecting cached files must never execute native programs")

    monkeypatch.setattr(subprocess, "run", prohibited)
    assert inspect_file(_write(tmp_path, _cmd())).status == "parsed"
    assert inspect_file(_write(tmp_path, _out(), "ref.out")).status == "partial"
