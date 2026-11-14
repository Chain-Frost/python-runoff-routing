"""Synthetic PyTUFLOW boundary checks; do not require or mock an upstream runtime pass."""

from __future__ import annotations

import hashlib
import json
from decimal import Decimal
from pathlib import Path
from typing import Any, cast

import pytest

from runoff_routing.arr_data import ARRFormatError
from runoff_routing.arr_import import parse_arr_json
from runoff_routing.arr_patterns import parse_pattern_csv
from runoff_routing.arr_selection import select_arr2019_ensemble
from runoff_routing.pytuflow_arr_audit import compare_ifd_tables, compare_pattern_rows

FIXTURES = Path(__file__).absolute().parent / "fixtures" / "arr"


class _SyntheticResponse:
    """Documented accessor shape only; does not pretend to execute PyTUFLOW."""

    def __init__(self, raw: bytes) -> None:
        doc = cast("dict[str, Any]", json.loads(raw.decode("utf-8-sig")))
        self.tables = cast("dict[str, object]", doc["layers"]["RecIFD"])

    def ifd_table(self, year: int) -> dict[str, object]:
        name = {1990: "Default Historical (1961-1990) Baseline", 2030: "Default Current (2030) Baseline"}[year]
        value = self.tables[name]
        assert isinstance(value, dict)
        return cast("dict[str, object]", value)


def test_ifd_matching_baselines_preserves_native_and_hash() -> None:
    raw = (FIXTURES / "2026v1-minimal.json").read_bytes()
    result = compare_ifd_tables(parse_arr_json(raw), _SyntheticResponse(raw))
    assert result["source_sha256"] == hashlib.sha256(raw).hexdigest()
    assert result["native_dataset_not_exposed_by_pytuflow_ifd_table"] == ["Default Native Baseline"]
    assert json.dumps(result).count("source_numeric_match") == 2


def test_ifd_float_roundtrip_discrepancy_is_explicit() -> None:
    raw = (FIXTURES / "2026v1-minimal.json").read_bytes().replace(b"9.60", b"9.6000000000000000001")
    result = compare_ifd_tables(parse_arr_json(raw), _SyntheticResponse(raw))
    assert result["source_sha256"] == hashlib.sha256(raw).hexdigest()
    assert "source_numeric_difference" in json.dumps(result)
    assert "9.6000000000000000001" in json.dumps(result)


def test_point_leading_zero_id_and_decimal_increments_are_not_normalised() -> None:
    raw = (
        b"EventID,Duration,TimeStep,Region,AEP,Increments\n"
        b"0007,60,30,SYNTHETIC,rare,0.1234567890123456789,99.8765432109876543211\n"
    )
    source = parse_pattern_csv(raw, kind="point")
    rows: list[dict[str, object]] = [
        {
            "event_id": 7,
            "duration": 60,
            "timestep": 30.0,
            "region": "SYNTHETIC",
            "aep_band": "rare",
            "increments": [float("0.1234567890123456789"), float("99.8765432109876543211")],
        }
    ]
    result = compare_pattern_rows(source, rows)
    assert source.source_sha256 == hashlib.sha256(raw).hexdigest()
    assert result["status"] == "source_difference"
    assert "0007" in json.dumps(result)
    assert "increment 0" in json.dumps(result)


@pytest.mark.parametrize("count", [0, 1, 9])
def test_missing_areal_members_never_fall_back_to_point(count: int) -> None:
    rows = ["EventID,Duration,TimeStep,Region,Area,Increments"]
    rows.extend(f"{i:04d},60,30,SYNTHETIC,100,25,75" for i in range(count))
    if count == 0:
        rows.append("9999,120,60,SYNTHETIC,100,25,75")
    source = parse_pattern_csv(("\n".join(rows) + "\n").encode(), kind="areal")
    with pytest.raises(ARRFormatError, match="Expected 10"):
        select_arr2019_ensemble(
            source,
            catchment_area_km2=Decimal(100),
            duration_min=60,
            aep_percent=Decimal(1),
            region="SYNTHETIC",
        )


def test_areal_missing_aep_stays_missing() -> None:
    raw = b"EventID,Duration,TimeStep,Region,Area,Increments\n0001,60,30,SYNTHETIC,100,50,50\n"
    source = parse_pattern_csv(raw, kind="areal")
    assert source.patterns[0].aep_band is None
    result = compare_pattern_rows(
        source,
        [{"event_id": 1, "duration": 60, "timestep": 30.0, "region": "SYNTHETIC", "area": 100, "increments": [50.0, 50.0]}],
    )
    assert result["status"] == "source_difference"


def test_uncharacterised_ey_ari_aep_substitution_is_not_implicit() -> None:
    source = parse_pattern_csv(
        b"EventID,Duration,TimeStep,Region,AEP,Increments\n1,60,30,SYNTHETIC,rare,50,50\n",
        kind="point",
    )
    for aep in (Decimal("0.5"), Decimal("63.2")):
        with pytest.raises(ARRFormatError, match="frequency selection"):
            select_arr2019_ensemble(
                source, catchment_area_km2=Decimal(30), duration_min=60, aep_percent=aep, region="SYNTHETIC"
            )
