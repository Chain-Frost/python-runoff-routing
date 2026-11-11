"""Offline comparison against an owner-supplied private numerical corpus.

The numerical source package has no dependency on the corpus, private paths,
RORB executables or proprietary source files. All file I/O stays in this
comparison adapter; the source solver remains pure.
"""

import csv
import hashlib
import io
import json
import math
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any, Literal

from runoff_routing.legacy_inputs import parse_control_vector, parse_explicit_design_storm
from runoff_routing.single_storm import Losses, calculate_storm

Status = Literal["compared", "unsupported", "invalid"]


@dataclass(frozen=True, slots=True)
class OrdinateDifference:
    """Complete row-wise difference, without rounding the expected token."""

    row: int
    raw_increment: str
    raw_time: str
    expected_token: str
    predicted_m3_s: float
    signed_difference_m3_s: float


@dataclass(frozen=True, slots=True)
class OfflineComparison:
    """Numerical comparison, NOT acceptance of the compatibility profile."""

    case_id: str
    status: Status
    reason: str
    engine_kind: str | None = None
    engine_sha256: str | None = None
    source_manifest_sha256: str | None = None
    printed_column: str | None = None
    dt_hours: float | None = None
    nominal_start_time_hours: float = 0.0
    first_native_time_token: str | None = None
    last_native_time_token: str | None = None
    native_peak_time_token: str | None = None
    predicted_peak_elapsed_hours: float | None = None
    sample_count: int | None = None
    exact_printed_matches: int | None = None
    max_absolute_error_m3_s: float | None = None
    rms_error_m3_s: float | None = None
    predicted_peak_m3_s: float | None = None
    reference_peak_m3_s: float | None = None
    predicted_peak_index: int | None = None
    reference_peak_index: int | None = None
    predicted_integral_m3: float | None = None
    reference_integral_m3: float | None = None
    average_distance_km: float | None = None
    nominal_rainfall_excess_volume_m3: float | None = None
    differences: tuple[OrdinateDifference, ...] = ()

    def to_csv(self) -> str:
        """Complete, row-ordered comparison data without native-time modification."""
        buffer = io.StringIO(newline="")
        writer = csv.writer(buffer, lineterminator="\n")
        writer.writerow(("sample_index", "native_increment", "native_time", "native_discharge_token",
                         "predicted_m3_s", "signed_error_m3_s"))
        for row in self.differences:
            writer.writerow((row.row, row.raw_increment, row.raw_time, row.expected_token,
                             row.predicted_m3_s, row.signed_difference_m3_s))
        return buffer.getvalue()

    def to_json(self, *, include_ordinates: bool = False) -> str:
        """Deterministic report; full differences available for audited comparisons."""
        data = asdict(self)
        if not include_ordinates:
            data.pop("differences")
        return json.dumps(data, indent=2, sort_keys=True, allow_nan=False)


class CorpusError(ValueError):
    """Missing, corrupted or structurally inconsistent offline corpus evidence."""


def _safe_relative(root: Path, locator: str) -> Path:
    path = Path(locator)
    if not locator or path.is_absolute() or path.anchor or any(part in {"..", "."} for part in path.parts):
        message = "Corpus locator is not a safe relative path."
        raise CorpusError(message)
    return root / path


def _read_verified(root: Path, record: Mapping[str, Any]) -> bytes:
    relative = record.get("path")
    fingerprint = record.get("fingerprint")
    if not isinstance(relative, str) or not isinstance(fingerprint, dict):
        message = "Missing input locator or SHA-256 fingerprint."
        raise CorpusError(message)
    data = _safe_relative(root, relative).read_bytes()
    if len(data) != fingerprint.get("size_bytes") or hashlib.sha256(data).hexdigest() != fingerprint.get("sha256"):
        message = f"Corpus input fingerprint does not match: {relative}."
        raise CorpusError(message)
    return data


def _integral(samples: Sequence[float], dt_hours: float) -> float:
    return 3600.0 * dt_hours * math.fsum(0.5 * (a + b) for a, b in zip(samples, samples[1:], strict=False))


def _compare_rows(
    rows: list[list[str]], predicted: tuple[float, ...], *, case_id: str, settings: Mapping[str, Any],
    column: str, engine: Mapping[str, Any], manifest_sha: str, dav: float, excess_volume: float,
) -> OfflineComparison:
    if len(rows) != len(predicted) or any(len(row) != 3 for row in rows):
        message = "Native row count/width does not match the predicted single print location."
        raise CorpusError(message)
    if not rows:
        message = "An empty native hydrograph is not a valid numerical reference."
        raise CorpusError(message)
    dt = float(settings["timestep_hours"])
    if not math.isfinite(dt) or dt <= 0:
        message = "Invalid reference timestep."
        raise CorpusError(message)
    differences: list[OrdinateDifference] = []
    expected: list[float] = []
    exact_matches = 0
    for index, (row, model) in enumerate(zip(rows, predicted, strict=True)):
        try:
            native = Decimal(row[2])
            increment = int(row[0])
            printed_time = Decimal(row[1])
        except (ValueError, ArithmeticError) as exc:
            message = "Non-numeric raw reference record."
            raise CorpusError(message) from exc
        if not native.is_finite() or native < 0 or not printed_time.is_finite():
            message = "Native hydrograph contains non-finite/negative reference tokens."
            raise CorpusError(message)
        if increment != index + 1:
            message = "Unexpected CMD increment sequence."
            raise CorpusError(message)
        if index and printed_time <= Decimal(rows[index - 1][1]):
            message = "Non-increasing native time labels."
            raise CorpusError(message)
        if not math.isfinite(model) or model < 0:
            message = "Predicted hydrograph contains invalid values."
            raise CorpusError(message)
        try:
            printed_model = Decimal(str(model)).quantize(Decimal(1).scaleb(native.as_tuple().exponent))
        except ArithmeticError as exc:
            message = "Cannot quantize predicted discharge to printed resolution."
            raise CorpusError(message) from exc
        exact_matches += printed_model == native
        expected.append(float(native))
        differences.append(OrdinateDifference(index, row[0], row[1], row[2], model, model - float(native)))
    return OfflineComparison(
        case_id=case_id,
        status="compared",
        reason="Comparison only; numeric parity and native time/flux conventions not accepted.",
        engine_kind=str(engine["kind"]),
        engine_sha256=str(engine["executable"]["sha256"]),
        source_manifest_sha256=manifest_sha,
        printed_column=column,
        dt_hours=dt,
        first_native_time_token=rows[0][1],
        last_native_time_token=rows[-1][1],
        native_peak_time_token=rows[expected.index(max(expected))][1],
        predicted_peak_elapsed_hours=predicted.index(max(predicted)) * dt,
        sample_count=len(rows),
        exact_printed_matches=exact_matches,
        max_absolute_error_m3_s=max(abs(row.signed_difference_m3_s) for row in differences),
        rms_error_m3_s=math.sqrt(math.fsum(row.signed_difference_m3_s**2 for row in differences) / len(rows)),
        predicted_peak_m3_s=max(predicted),
        reference_peak_m3_s=max(expected),
        predicted_peak_index=predicted.index(max(predicted)),
        reference_peak_index=expected.index(max(expected)),
        predicted_integral_m3=_integral(predicted, dt),
        reference_integral_m3=_integral(expected, dt),
        average_distance_km=dav,
        nominal_rainfall_excess_volume_m3=excess_volume,
        differences=tuple(differences),
    )


def compare_corpus_case(corpus_root: Path, case_id: str) -> OfflineComparison:
    """Compare an eligible CMD case from the private offline corpus.

    Validates the recorded input and manifest checksums before computing.
    GUI, multi-table, invalid and uncharacterised profiles are unsupported,
    not interpreted as a passing result. No RORB executable is launched.
    """
    root = corpus_root.absolute()
    catalogue = json.loads((root / "catalogue.json").read_text(encoding="utf-8"))
    if catalogue.get("schema_version") != 1:
        message = "Unsupported offline corpus catalogue schema."
        raise CorpusError(message)
    cases = [case for case in catalogue.get("cases", ()) if case.get("case_id") == case_id]
    if len(cases) != 1:
        message = "Case identifier missing or ambiguous."
        raise CorpusError(message)
    case = cases[0]
    engine = case.get("engine", {})
    engine_kind = engine.get("kind")
    if engine_kind != "RORB_CMD":
        return OfflineComparison(case_id, "unsupported", "GUI profile is not a CMD calculation fixture.")
    if case.get("capture_outcome") != "success":
        return OfflineComparison(case_id, "unsupported", "Native reference capture was not successful.")
    settings = case.get("effective_settings", {})
    parameters = settings.get("cmd_writer", {})
    if parameters.get("loss_model") != 1 or parameters.get("num_isa") != 1 or parameters.get("num_bursts") != 1:
        return OfflineComparison(case_id, "unsupported", "Only one-ISA IL/CL single-burst DESIGN is supported.")
    manifest = case.get("manifest")
    manifest_fingerprint = case.get("manifest_fingerprint", {})
    if not isinstance(manifest, str) or not isinstance(manifest_fingerprint, dict):
        message = "Missing manifest path/fingerprint."
        raise CorpusError(message)
    manifest_bytes = _safe_relative(root, manifest).read_bytes()
    if (len(manifest_bytes) != manifest_fingerprint.get("size_bytes") or
            hashlib.sha256(manifest_bytes).hexdigest() != manifest_fingerprint.get("sha256")):
        message = "Manifest fingerprint changed."
        raise CorpusError(message)
    inputs = {item["identity"]: item for item in case.get("inputs", ())}
    if not {"catchment", "storm", "parameters"}.issubset(inputs):
        return OfflineComparison(case_id, "unsupported", "Missing catchment/storm/CMD parameter evidence.")
    raw_model = _read_verified(root, inputs["catchment"]).decode("utf-8-sig")
    raw_storm = _read_verified(root, inputs["storm"]).decode("utf-8-sig")
    _read_verified(root, inputs["parameters"])
    model = parse_control_vector(raw_model)
    storm = parse_explicit_design_storm(raw_storm)
    if str(storm.timestep_hours) != str(float(settings["timestep_hours"])):
        message = "Mismatch between stored storm and effective timestep."
        raise CorpusError(message)
    result = calculate_storm(
        model, storm,
        losses=Losses(float(parameters["initial_loss_mm"]), float(parameters["continuing"])),
        kc=float(parameters["kc"]), m=float(parameters["m"]),
    )
    index = json.loads((root / "FILE_INDEX.json").read_text(encoding="utf-8"))
    hydrograph_path = case["hydrographs"]
    entry = index.get("files", {}).get(hydrograph_path)
    if not isinstance(entry, dict):
        message = "Hydrograph missing from immutable corpus file index."
        raise CorpusError(message)
    raw_hydrograph = _read_verified(root, {"path": hydrograph_path, "fingerprint": entry})
    expected_record = json.loads(raw_hydrograph.decode("utf-8-sig"))
    tables = expected_record.get("tables", ())
    if len(tables) != 1 or len(result.outlets_m3_s) != 1 or tables[0].get("columns") != ["Inc", "Time", "Hyd001"]:
        return OfflineComparison(case_id, "unsupported", "Print-location identity/shape not characterised.")
    return _compare_rows(
        tables[0]["rows"], result.outlets_m3_s[0], case_id=case_id,
        settings=settings, column="Hyd001", engine=engine,
        manifest_sha=hashlib.sha256(manifest_bytes).hexdigest(), dav=result.average_distance_km,
        excess_volume=math.fsum(
            math.fsum(excess) * 1000.0 * area for excess, area in zip(
                result.rainfall_excess_mm, model.areas_km2, strict=True
            )
        ),
    )
