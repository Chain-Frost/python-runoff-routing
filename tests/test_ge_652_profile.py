"""Unqualified graphical 6.52 envelope profiling; no native tools or client data."""

from __future__ import annotations

import hashlib
import json
import runpy
from collections.abc import Callable
from pathlib import Path
from typing import cast

import pytest

from runoff_routing.rorb_codec import FormatProblem, parse_catg
from runoff_routing.rorb_ge_profile import profile_graphical_catg

_ROOT = Path(__file__).resolve().parents[1]
_FIXTURE = (
    _ROOT
    / "tests"
    / "fixtures"
    / "regression-v1"
    / "native-cmd"
    / "objects"
    / "2ad4663ddeaacdfd4bba4b199a29d3eed7bcb6d9f096ff62f6d9d107330bd247.catg"
)


def _synthetic_652() -> bytes:
    original = _FIXTURE.read_bytes()
    assert hashlib.sha256(original).hexdigest() == _FIXTURE.stem
    assert original.count(b"C RORB_GE 6.45") == 1
    return original.replace(b"C RORB_GE 6.45", b"C RORB_GE 6.52", 1)


def test_ge_652_profile_is_structure_only_and_parser_remains_fail_closed() -> None:
    source = _synthetic_652()
    shape = profile_graphical_catg(source)
    assert shape.qualification == "structure_only_unqualified"
    assert shape.envelope == "bounded"
    assert shape.declared_ge_version == "6.52"
    assert shape.version_marker_count == shape.end_marker_count == 1
    assert shape.source_newline == "crlf"
    assert shape.source_size_bytes == len(source)
    assert shape.source_sha256 is None
    assert shape.tail_first_record == "0"
    assert shape.tail_noncomment_record_count > 0
    counts = {item.section: item.declared_count for item in shape.sections}
    assert counts["#NODES"] == 8
    assert counts["#REACHES"] == 7
    assert counts["#STORAGES"] == counts["#INFLOW/OUTFLOW"] == 0
    assert all(record.section != "other_section" for record in shape.sections)
    assert shape.diagnostics == ()

    with pytest.raises(FormatProblem, match=r"6\.52 recognised but unqualified") as caught:
        parse_catg(source)
    assert caught.value.status == "unsupported"
    assert caught.value.code == "ge_652_unqualified"


def test_ge_652_profile_does_not_emit_custom_headings_paths_or_coordinates() -> None:
    source = _synthetic_652()
    confidential = b"C #CLIENT_NAME_PRIVATE_PATH\nC Customer XYZ, 123.4567, C:\\\\Internal\\\\Map.wmf\n"
    edited = source.replace(b"C #NODES", confidential + b"C #NODES", 1)
    assert edited != source
    shape = profile_graphical_catg(edited)
    payload = shape.to_json()
    assert "other_section" in payload
    assert "unknown_graphical_sections_present" in shape.diagnostics
    assert "CLIENT_NAME_PRIVATE_PATH" not in payload
    assert "Customer XYZ" not in payload
    assert "123.4567" not in payload
    assert "Map.wmf" not in payload
    assert '"source_sha256": null' in payload
    assert shape.source_size_bytes == len(edited)

    with_hash = profile_graphical_catg(edited, include_sha256=True)
    assert with_hash.source_sha256 == hashlib.sha256(edited).hexdigest()
    assert with_hash.to_json() != payload
    assert "Customer XYZ" not in with_hash.to_json()


@pytest.mark.parametrize(
    ("edit", "expected"),
    [
        (
            lambda raw: raw.replace(b"C END RORB_GE", b"C END RORB_GE\nC END RORB_GE", 1),
            "missing_or_multiple_end_markers",
        ),
        (
            lambda raw: raw.replace(b"C RORB_GE 6.52", b"C RORB_GE 6.52\nC RORB_GE 6.52", 1),
            "missing_or_multiple_version_markers",
        ),
        (lambda raw: raw.replace(b"C END RORB_GE", b"C END GRAPHICAL", 1), "missing_or_multiple_end_markers"),
    ],
)
def test_ge_652_profile_reports_envelope_gaps_without_claiming_input_acceptance(
    edit: Callable[[bytes], bytes], expected: str
) -> None:
    source = edit(_synthetic_652())
    shape = profile_graphical_catg(source)
    assert shape.envelope == "incomplete"
    assert expected in shape.diagnostics
    assert shape.qualification == "structure_only_unqualified"


def test_ge_652_profile_disambiguates_file_header_from_rorbwin_program_version() -> None:
    source = _synthetic_652().replace(b"C RORB_GE 6.52", b"C RORB_GE 002", 1)
    shape = profile_graphical_catg(source)
    assert shape.declared_ge_version == "002"
    assert shape.qualification == "structure_only_unqualified"
    assert shape.tail_first_record == "0"


def test_ge_652_read_only_cli_redacts_hash_unless_explicitly_requested(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = _synthetic_652()
    path = tmp_path / "sensitive-client-model.catg"
    path.write_bytes(source)
    before = path.read_bytes()
    namespace = runpy.run_path(str(_ROOT / "repo-scripts" / "rorb_inspect.py"))
    main = cast("Callable[[list[str]], int]", namespace["main"])

    assert main([str(path), "--ge-profile"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["declared_ge_version"] == "6.52"
    assert result["qualification"] == "structure_only_unqualified"
    assert result["source_sha256"] is None
    assert "sensitive-client-model" not in json.dumps(result)
    assert "b1" not in json.dumps(result)
    assert path.read_bytes() == before

    assert main([str(path), "--ge-profile", "--ge-profile-sha256"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["source_sha256"] == hashlib.sha256(source).hexdigest()
    assert path.read_bytes() == before
