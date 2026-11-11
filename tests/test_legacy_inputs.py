"""Compatibility shim regression: supported S1 grammar is authoritative."""

import pytest

from runoff_routing.legacy_inputs import (
    LegacyInputError,
    parse_control_bytes,
    parse_control_vector,
    parse_explicit_design_storm,
    parse_explicit_design_storm_bytes,
)
from runoff_routing.rorb_codec import parse_catg, parse_design_stm
from runoff_routing.single_storm import Control

CONTROL = """HEADER
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
1, 2.0, -99, first source
3
1, 3.0, -99, second source
4
5, 1.0, -99, downstream reach
7
PRINT
0
C Sub Area Data
1.0, 3.0, -99
C Impervious Fraction Data
0, -99
"""
STORM = """Sample
DESIGN
C storm data
0.5, 10, 1, 1, 1, -99
0, 2
Temporal pattern (% of depth)
20.0, 80.0, -99.00
C depth
10.0, 20.0, -99.00
"""


def test_control_sample_order_and_lengths() -> None:
    model = parse_control_vector(CONTROL)
    assert model.controls == (Control(1, 2), Control(3), Control(1, 3), Control(4), Control(5, 1), Control(7))
    assert model.areas_km2 == (1, 3)
    assert len(parse_catg(CONTROL.encode()).model.controls) == len(model.controls)


def test_original_bytes_accept_cp1252_and_annotated_pervious_data() -> None:
    coded = CONTROL.replace("7\nPRINT\n", "7\nCafé\n").replace("0, -99\n", "0, -99, No impervious areas\n")
    assert parse_control_bytes(coded.encode("cp1252")) == parse_control_vector(CONTROL)
    storm = STORM.replace("Sample", "Café rainfall")
    assert parse_explicit_design_storm_bytes(storm.encode("cp1252")) == parse_explicit_design_storm(STORM)


def test_explicit_design_storm() -> None:
    storm = parse_explicit_design_storm(STORM)
    assert storm.timestep_hours == 0.5
    assert storm.calculation_increments == 10
    assert storm.percentages == (20, 80)
    assert storm.depths_mm == (10, 20)
    assert len(parse_design_stm(STORM.encode()).model.percentages) == len(storm.percentages)


@pytest.mark.parametrize(
    "source",
    [
        CONTROL.replace("C END RORB_GE", "C END"),
        CONTROL.replace("1\n1, 2.0", "2\n1, 2.0"),
        CONTROL.replace("5, 1.0", "2, 1.0"),
        CONTROL.replace("1.0, 3.0, -99", "1.0, 3.0"),
        CONTROL.replace("0, -99", "1, -99"),
        CONTROL.replace("1, 3.0", "1, nan"),
        CONTROL.replace("C #STORAGES\nC 0", "C #STORAGES\nC 1"),
    ],
)
def test_unsupported_catchment_fails(source: str) -> None:
    with pytest.raises(LegacyInputError):
        parse_control_vector(source)


@pytest.mark.parametrize(
    "source",
    [
        STORM.replace("DESIGN", "FIT"),
        STORM.replace("0, 2", "0, 3"),
        STORM.replace("1, 1, 1, -99", "2, 1, 1, -99"),
        STORM.replace("10.0, 20.0, -99.00", "10.0, bad, -99.00"),
        STORM.replace("20.0, 80.0, -99.00", "20.0, 80.0"),
    ],
)
def test_unsupported_storm_fails(source: str) -> None:
    with pytest.raises(LegacyInputError):
        parse_explicit_design_storm(source)
