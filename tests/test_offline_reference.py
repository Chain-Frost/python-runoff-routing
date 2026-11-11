"""Offline comparison fixture is synthetic; no private data is distributed."""

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from runoff_routing.offline_reference import CorpusError, compare_corpus_case, decode_legacy_source
from runoff_routing.rorb_codec import RorbFormatError, SourceDocument

CAT = """SYNTHETIC CATCHMENT
C RORB_GE 002
C #NODES
C 0
C #REACHES
C 0
C #STORAGES
C 0
C #INFLOW/OUTFLOW
C 0
C END RORB_GE
1
1, 2.0, -99
7
OUTLET
0
C Areas
10.0, -99
C Impervious
0, -99
"""
STM = """Sample
DESIGN
1.0, 3, 1, 1, 1, -99
0, 2
Temporal pattern (% of depth)
50.0,50.0,-99
C rainfall depths
3.6, -99
"""
PAR = "# BEGIN\n# END\n"
HYDRO = {
    "tables": [
        {
            "columns": ["Inc", "Time", "Hyd001"],
            "rows": [["1", "1.00", "0.000"], ["2", "2.00", "5.000"], ["3", "3.00", "5.000"], ["4", "4.00", "0.000"]],
        }
    ]
}


def _write_case(root: Path) -> None:
    root.mkdir()
    inputs: list[dict[str, Any]] = []
    for identity, filename, contents in (
        ("catchment", "model.catg", CAT.encode()),
        ("storm", "storm.stm", STM.encode()),
        ("parameters", "reference.par", PAR.encode()),
    ):
        (root / filename).write_bytes(contents)
        inputs.append(
            {
                "identity": identity,
                "path": filename,
                "fingerprint": {"sha256": hashlib.sha256(contents).hexdigest(), "size_bytes": len(contents)},
            }
        )
    manifest = b"{}\n"
    (root / "manifest.json").write_bytes(manifest)
    raw_hydro = json.dumps(HYDRO).encode()
    (root / "hydrographs.json").write_bytes(raw_hydro)
    (root / "FILE_INDEX.json").write_text(
        json.dumps(
            {
                "files": {
                    "hydrographs.json": {"sha256": hashlib.sha256(raw_hydro).hexdigest(), "size_bytes": len(raw_hydro)}
                }
            }
        ),
        encoding="utf-8",
    )
    record: dict[str, Any] = {
        "schema_version": 1,
        "cases": [
            {
                "case_id": "synthetic",
                "capture_outcome": "success",
                "manifest": "manifest.json",
                "manifest_fingerprint": {"sha256": hashlib.sha256(manifest).hexdigest(), "size_bytes": len(manifest)},
                "hydrographs": "hydrographs.json",
                "inputs": inputs,
                "engine": {"kind": "RORB_CMD", "executable": {"sha256": "example-only"}},
                "effective_settings": {
                    "timestep_hours": "1",
                    "cmd_writer": {
                        "kc": "0",
                        "m": "1",
                        "initial_loss_mm": "0",
                        "continuing": "0",
                        "loss_model": 1,
                        "num_isa": 1,
                        "num_bursts": 1,
                    },
                },
            }
        ],
    }
    (root / "catalogue.json").write_text(json.dumps(record), encoding="utf-8")


@pytest.mark.parametrize(
    ("raw", "expected", "encoding"),
    [
        (b"\xef\xbb\xbfSource\r\n", "Source\r\n", "utf-8-sig"),
        ("Süd".encode("utf-8"), "Süd", "utf-8-sig"),
        (b"Legacy \x96 name\r\n", "Legacy – name\r\n", "cp1252"),
        (b"", "", "utf-8-sig"),
    ],
)
def test_legacy_text_decoder_uses_s1_source_encoding(raw: bytes, expected: str, encoding: str) -> None:
    source = SourceDocument.from_bytes(raw)
    assert source.data == raw
    assert source.encoding == encoding
    assert source.sha256 == hashlib.sha256(raw).hexdigest()
    assert decode_legacy_source(raw) == expected


def test_legacy_text_decoder_rejects_invalid_cp1252() -> None:
    with pytest.raises(RorbFormatError, match="Undecodable RORB source bytes") as error:
        decode_legacy_source(b"\x81")
    assert error.value.status == "invalid"
    assert error.value.code == "source_encoding"


def test_exact_synthetic_offline_comparison(tmp_path: Path) -> None:
    _write_case(tmp_path / "corpus")
    result = compare_corpus_case(tmp_path / "corpus", "synthetic")
    assert result.status == "compared"
    assert result.exact_printed_matches == 4
    assert result.max_absolute_error_m3_s == 0.0
    assert result.first_native_time_token == "1.00"  # noqa: S105 -- recorded native clock label
    assert result.last_native_time_token == "4.00"  # noqa: S105 -- recorded native clock label
    assert result.native_peak_time_token == "2.00"  # noqa: S105 -- recorded native clock label
    assert result.predicted_peak_elapsed_hours == 1.0
    assert result.nominal_rainfall_excess_volume_m3 == 36_000.0
    assert result.predicted_peak_index == 1
    assert result.sample_count == 4
    assert result.to_json(include_ordinates=True).count('"row"') == 4
    assert result.reference_integral_m3 == 36000.0
    assert result.to_csv().splitlines()[0] == (
        "sample_index,native_increment,native_time,native_discharge_token,predicted_m3_s,signed_error_m3_s"
    )
    assert len(result.to_csv().splitlines()) == 5


def test_modified_corpus_input_is_rejected(tmp_path: Path) -> None:
    root = tmp_path / "corpus"
    _write_case(root)
    (root / "storm.stm").write_text(STM + "extra", encoding="utf-8")
    with pytest.raises(CorpusError, match="fingerprint"):
        compare_corpus_case(root, "synthetic")


def test_corrupt_reference_hydrograph_is_rejected(tmp_path: Path) -> None:
    root = tmp_path / "corpus"
    _write_case(root)
    (root / "hydrographs.json").write_text("{}", encoding="utf-8")
    with pytest.raises(CorpusError, match="fingerprint"):
        compare_corpus_case(root, "synthetic")


def test_cp1252_original_corpus_source_is_accepted(tmp_path: Path) -> None:
    root = tmp_path / "corpus"
    _write_case(root)
    encoded = CAT.replace("SYNTHETIC CATCHMENT", "Café catchment").encode("cp1252")
    (root / "model.catg").write_bytes(encoded)
    catalogue = json.loads((root / "catalogue.json").read_text(encoding="utf-8"))
    item = next(record for record in catalogue["cases"][0]["inputs"] if record["identity"] == "catchment")
    item["fingerprint"] = {"sha256": hashlib.sha256(encoded).hexdigest(), "size_bytes": len(encoded)}
    (root / "catalogue.json").write_text(json.dumps(catalogue), encoding="utf-8")
    report = compare_corpus_case(root, "synthetic")
    assert report.status == "compared"
    assert report.exact_printed_matches == 4
    assert (root / "model.catg").read_bytes() == encoded


def test_gui_reference_is_not_misused(tmp_path: Path) -> None:
    root = tmp_path / "corpus"
    _write_case(root)
    catalog = json.loads((root / "catalogue.json").read_text())
    catalog["cases"][0]["engine"]["kind"] = "RORBwin"
    (root / "catalogue.json").write_text(json.dumps(catalog), encoding="utf-8")
    report = compare_corpus_case(root, "synthetic")
    assert report.status == "unsupported"
    assert report.exact_printed_matches is None
