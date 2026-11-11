"""Immutable RORB inspection results with original source identity and line provenance."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Literal

from .rorb_model import CatchmentModel, StormModel

Status = Literal["parsed", "partial", "unsupported", "invalid"]
Severity = Literal["warning", "error", "unsupported"]


@dataclass(frozen=True, slots=True)
class Diagnostic:
    """A machine-readable diagnostic tied to an original source line."""

    code: str
    message: str
    severity: Severity
    line: int | None = None


@dataclass(frozen=True, slots=True)
class RorbSource:
    """Read-only source, retaining original lines and an exact byte fingerprint."""

    path: Path
    sha256: str
    size_bytes: int
    encoding: str
    lines: tuple[str, ...]

    @classmethod
    def read(cls, path: Path) -> RorbSource:
        data = path.read_bytes()
        try:
            text = data.decode("utf-8-sig")
            encoding = "utf-8-sig"
        except UnicodeDecodeError:
            text = data.decode("cp1252")
            encoding = "cp1252"
        return cls(path.absolute(), hashlib.sha256(data).hexdigest(), len(data), encoding, tuple(text.splitlines()))


@dataclass(frozen=True, slots=True)
class SourceField:
    """Original record, with a stable one-based line reference."""

    line: int
    label: str
    value: str
    raw: str


@dataclass(frozen=True, slots=True)
class RoutingParameter:
    isa: int
    kc: Decimal
    m: Decimal
    line: int


@dataclass(frozen=True, slots=True)
class LossParameter:
    isa: int
    burst: int
    initial_loss_mm: Decimal
    continuing: Decimal
    line: int


@dataclass(frozen=True, slots=True)
class ParameterModel:
    """CMD-independent typed parameter values, not a runnable catchment model."""

    catchment_reference: str
    storm_reference: str
    lumped_kc: bool
    verbosity: int
    loss_model: Literal[1, 2]
    num_isa: int
    num_bursts: int
    routing: tuple[RoutingParameter, ...]
    losses: tuple[LossParameter, ...]


@dataclass(frozen=True, slots=True)
class HydrographRow:
    line: int
    increment: int
    time_hours: Decimal
    values: tuple[Decimal, ...]
    raw_time: str


@dataclass(frozen=True, slots=True)
class HydrographReport:
    """A single retained hydrograph table, without inferred print-point identities."""

    columns: tuple[str, ...]
    rows: tuple[HydrographRow, ...]
    time_increment_hours: Decimal | None
    reported_duration_increments: int | None


@dataclass(frozen=True, slots=True)
class Inspection:
    """Parsing status does not imply numerical support or native parity."""

    kind: str
    status: Status
    source: RorbSource
    diagnostics: tuple[Diagnostic, ...]
    fields: tuple[SourceField, ...] = ()
    parameters: ParameterModel | None = None
    hydrographs: HydrographReport | None = None
    catchment: CatchmentModel | None = None
    storm: StormModel | None = None

    def to_json(self) -> str:
        """Return deterministic machine-readable inspection diagnostics."""
        return json.dumps(asdict(self), indent=2, sort_keys=True, default=str)


def decimal_number(text: str) -> Decimal:
    """Parse a complete finite decimal or Fortran-D numeric token."""
    try:
        value = Decimal(text.replace("d", "E").replace("D", "E"))
    except InvalidOperation as exc:
        message = f"Invalid numeric value: {text!r}"
        raise ValueError(message) from exc
    if not value.is_finite():
        message = f"Non-finite numeric value: {text!r}"
        raise ValueError(message)
    return value


def positive_integer(text: str, minimum: int = 1) -> int:
    if not text.isascii() or not text.isdecimal() or not minimum <= int(text) <= 10_000:
        message = f"Expected integer in [{minimum}, 10000]: {text!r}"
        raise ValueError(message)
    return int(text)
