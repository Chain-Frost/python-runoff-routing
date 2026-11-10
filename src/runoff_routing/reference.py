"""Local, opt-in RORB reference capture; no hydrological computation or implicit execution."""

from __future__ import annotations

import hashlib
import json
import math
import platform
import re
import shutil
import subprocess
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Literal
from uuid import uuid4

SCHEMA_VERSION = 1
Outcome = Literal[
    "captured_unverified",
    "success",
    "zero_runoff",
    "missing_output",
    "incomplete_output",
    "native_error",
    "nonzero_exit",
    "launch_failed",
    "timeout",
    "input_mutated",
    "inventory_failed",
]
ERROR_LINE = re.compile(r"^\s*(?:error\b|fatal\b|aborted\b|failed\b|unable to\b)", re.IGNORECASE)
WARNING_LINE = re.compile(r"^\s*warning\b", re.IGNORECASE)


@dataclass(frozen=True, slots=True)
class Parameters:
    """Limited writer from ryan-tools PR #145; one ISA and one rainfall burst only."""

    kc: Decimal
    m: Decimal
    initial_loss_mm: Decimal
    continuing: Decimal
    loss_model: Literal[1, 2]

    @classmethod
    def from_mapping(cls, raw: dict[str, Any]) -> Parameters:
        try:
            values = (Decimal(str(raw[key])) for key in ("kc", "m", "initial_loss_mm", "continuing"))
            kc, m, initial_loss, continuing = values
        except (KeyError, InvalidOperation) as exc:
            message = "Parameters require numeric kc, m, initial_loss_mm and continuing"
            raise ValueError(message) from exc
        flag = raw.get("loss_model")
        if type(flag) is not int or flag not in (1, 2):
            message = "Only loss_model 1 (IL/CL) or 2 (IL/ROC) is supported"
            raise ValueError(message)
        if any(not value.is_finite() for value in (kc, m, initial_loss, continuing)):
            message = "Parameters must be finite"
            raise ValueError(message)
        if kc <= 0 or m <= 0 or initial_loss < 0 or continuing < 0:
            message = "kc and m must be positive; losses must be nonnegative"
            raise ValueError(message)
        return cls(kc, m, initial_loss, continuing, flag)

    def as_effective(self) -> dict[str, str | int]:
        return {
            "kc": str(self.kc),
            "m": str(self.m),
            "initial_loss_mm": str(self.initial_loss_mm),
            "continuing": str(self.continuing),
            "continuing_unit": "mm/h" if self.loss_model == 1 else "runoff_coefficient",
            "loss_model": self.loss_model,
            "loss_interpretation": "IL/CL" if self.loss_model == 1 else "IL/runoff coefficient",
            "num_isa": 1,
            "num_bursts": 1,
        }


def render_par(catchment: Path, storm: Path, params: Parameters) -> bytes:
    """Adapt the pinned ryan-tools render_par, pointing ONLY at staged input paths."""
    for path in (catchment, storm):
        if "\n" in str(path) or "\r" in str(path):
            message = "Input path contains a parameter-file delimiter"
            raise ValueError(message)
    text = "\n".join(
        (
            "# BEGIN",
            f"Cat file :{catchment}",
            f"Stm file :{storm}",
            "Lumped kc:T",
            "Verbosity:3",
            f"Lossmodel:{params.loss_model}",
            "Num ISA  :1",
            f"ISA 1    :{params.kc},{params.m}",
            "Num burst:1",
            f"ISA 1    :{params.initial_loss_mm},{params.continuing}",
            "# END",
            "",
        )
    )
    return text.encode("utf-8")


def fingerprint(path: Path) -> dict[str, str | int]:
    """Record original bytes in chunks without interpreting file encodings."""
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return {"sha256": digest.hexdigest(), "size_bytes": path.stat().st_size}


def _load(spec_file: Path) -> dict[str, Any]:
    raw: Any = json.loads(spec_file.read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or raw.get("schema_version") != SCHEMA_VERSION:
        message = f"Expected capture spec schema_version={SCHEMA_VERSION}"
        raise ValueError(message)
    if not isinstance(raw.get("case_id"), str) or not re.fullmatch(r"[A-Za-z0-9][\w.-]{0,79}", raw["case_id"]):
        message = "case_id must be 1-80 safe characters"
        raise ValueError(message)
    if raw.get("engine_kind") not in ("RORB_CMD", "RORBwin"):
        message = "engine_kind must be RORB_CMD or RORBwin"
        raise ValueError(message)
    required = ("provenance", "effective_settings", "requested_print_locations", "expected_steps")
    if any(key not in raw for key in required):
        message = f"Missing required capture spec fields: {required}"
        raise ValueError(message)
    if not isinstance(raw["provenance"], dict) or not isinstance(raw["effective_settings"], dict):
        message = "provenance and effective_settings must be objects"
        raise TypeError(message)
    prints = raw["requested_print_locations"]
    if (
        not isinstance(prints, dict)
        or not prints
        or any(
            not isinstance(key, str) or not re.fullmatch(r"Hyd\d+", key) or not isinstance(value, str) or not value
            for key, value in prints.items()
        )
    ):
        message = "requested_print_locations must map HydNNN column IDs to actual location identities"
        raise ValueError(message)
    count = raw["expected_steps"]
    if count is not None and (type(count) is not int or count <= 0):
        message = "expected_steps must be a positive integer or null (unverified horizon)"
        raise ValueError(message)
    return raw


def _path(spec_file: Path, raw: str) -> Path:
    if not raw or "\n" in raw or "\r" in raw:
        message = "Invalid path in reference capture spec"
        raise ValueError(message)
    value = Path(raw).expanduser()
    return (value if value.is_absolute() else spec_file.absolute().parent / value).absolute()


def _file(spec_file: Path, raw: object) -> Path:
    if not isinstance(raw, str):
        message = "Input and executable paths must be strings"
        raise TypeError(message)
    path = _path(spec_file, raw)
    if path.is_symlink() or not path.is_file():
        message = f"Reference file is missing or not a regular file: {raw}"
        raise FileNotFoundError(message)
    return path


def _copy(source: Path, target: Path) -> dict[str, str | int]:
    """Stage an independent byte copy; the source is never opened for writing."""
    if target.exists() or target.is_symlink():
        message = f"Refusing to overwrite capture evidence: {target.name}"
        raise FileExistsError(message)
    shutil.copyfile(source, target, follow_symlinks=False)
    original = fingerprint(source)
    if fingerprint(target) != original:
        message = f"Staged input differs from its source: {target.name}"
        raise ValueError(message)
    return original


def _record(path: Path, root: Path) -> dict[str, str | int]:
    return {"path": path.relative_to(root).as_posix(), **fingerprint(path)}


def _files(root: Path, excluded: set[Path]) -> list[dict[str, str | int]]:
    all_paths = list(root.rglob("*"))
    if any(path.is_symlink() for path in all_paths):
        message = "Native outputs must not be symlinks"
        raise ValueError(message)
    paths = sorted(path for path in all_paths if path.is_file() and path not in excluded)
    return [_record(path, root) for path in paths]


def _check_report(  # noqa: C901 -- explicit diagnostics for all malformed native-table states
    path: Path, expected_prints: dict[str, str], expected_steps: int | None
) -> tuple[Outcome, dict[str, Any]]:
    """Conservative cached table check; a non-characterised format is NOT native parity."""
    headers: list[tuple[int, list[str]]] = []
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    for index, line in enumerate(lines):
        names = line.split()
        if len(names) >= 3 and names[:2] == ["Inc", "Time"]:
            headers.append((index, names))
    if len(headers) != 1:
        return "incomplete_output", {"reason": f"Expected one Inc/Time table; found {len(headers)}"}
    index, names = headers[0]
    if len(names) != len(set(names)) or set(names[2:]) != set(expected_prints):
        return "incomplete_output", {
            "reason": "Printed hydrograph columns differ from requested print identities",
            "columns": names,
        }
    readings: list[list[float]] = []
    time_labels: list[str] = []
    for line in lines[index + 1 :]:
        cells = line.split()
        if not cells:
            if readings:
                break
            continue
        try:
            float(cells[0])
        except ValueError:
            if readings:
                break
            continue
        if len(cells) != len(names):
            return "incomplete_output", {"reason": "Truncated/extra hydrograph row", "rows": len(readings)}
        try:
            values = [float(cell) for cell in cells]
        except ValueError:
            return "incomplete_output", {"reason": "Invalid numeric hydrograph row", "rows": len(readings)}
        if not all(math.isfinite(value) for value in values):
            return "incomplete_output", {"reason": "Non-finite hydrograph value", "rows": len(readings)}
        if readings and (values[0] <= readings[-1][0] or values[1] <= readings[-1][1]):
            return "incomplete_output", {"reason": "Time/increment did not advance", "rows": len(readings)}
        readings.append(values)
        time_labels.append(cells[1])
    summary: dict[str, Any] = {"columns": names, "rows": len(readings), "raw_time_labels": time_labels}
    if not readings or (expected_steps is not None and len(readings) != expected_steps):
        summary["reason"] = "Empty/incomplete hydrograph table or unexpected horizon"
        return "incomplete_output", summary
    if expected_steps is None:
        summary["reason"] = "Expected timestep count not supplied: cannot establish completeness"
        return "captured_unverified", summary
    if all(value == 0 for row in readings for value in row[2:]):
        return "zero_runoff", summary
    return "success", summary


def _diagnostics(paths: list[Path]) -> dict[str, list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    for path in paths:
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            if ERROR_LINE.match(line):
                errors.append(f"{path.name}: {line[:300]}")
            if WARNING_LINE.match(line):
                warnings.append(f"{path.name}: {line[:300]}")
    return {"errors": errors, "warnings": warnings}


def _metadata_gaps(spec: dict[str, Any]) -> list[str]:
    """A readable hydrograph is not a complete provenance record."""
    gaps: list[str] = [field for field in ("observed_banner", "observed_version") if not spec.get(field)]
    provenance = spec["provenance"]
    gaps.extend(f"provenance.{field}" for field in ("source", "redistribution") if not provenance.get(field))
    generator = spec.get("generator")
    if not isinstance(generator, dict) or any(not generator.get(key) for key in ("name", "revision", "event_to_file")):
        gaps.append("generator name/revision/event_to_file")
    gaps.extend(
        f"effective_settings.{field}"
        for field in ("timestep_hours", "horizon", "isa_mapping", "burst_mapping")
        if spec["effective_settings"].get(field) in (None, "", [])
    )
    if spec["expected_steps"] is None:
        gaps.append("expected_steps")
    if spec.get("parameters", {}).get("loss_model") == 2:
        gaps.append("loss_model_2_native_semantics_unverified")
    return gaps


def _manifest_base(spec: dict[str, Any], executable: Path, root: Path) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "case_id": spec["case_id"],
        "engine": {
            "kind": spec["engine_kind"],
            "executable": fingerprint(executable),
            "observed_banner": spec.get("observed_banner"),
            "observed_version": spec.get("observed_version"),
            "documentation_version": spec.get("documentation_version"),
        },
        "provenance": spec["provenance"],
        "generator": spec.get("generator"),
        "effective_settings": spec["effective_settings"],
        "requested_print_locations": spec["requested_print_locations"],
        "provenance_gaps": _metadata_gaps(spec),
        "expected_steps": spec["expected_steps"],
        "environment": {
            "os": platform.system(),
            "release": platform.release(),
            "python": platform.python_version(),
            "machine": platform.machine(),
        },
        "capture": {
            "utc_started": datetime.now(UTC).isoformat(),
            "working_directory": ".",
            "local_isolation": "exclusive case directory; staged input copies; no source writes requested",
            "relative_root": root.name,
        },
        "inputs": {},
        "outputs": [],
        "diagnostics": {"errors": [], "warnings": []},
        "outcome": "captured_unverified",
    }


def _persist(root: Path, manifest: dict[str, Any]) -> Path:
    target = root / "manifest.json"
    with target.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(manifest, stream, indent=2, ensure_ascii=False)
        stream.write("\n")
    return target


def _new_root(parent: Path, case_id: str) -> Path:
    if parent.is_symlink():
        message = "Capture output parent must not be a symlink"
        raise ValueError(message)
    parent.mkdir(parents=True, exist_ok=True)
    root = parent / f"{case_id}_{datetime.now(UTC).strftime('%Y%m%dT%H%M%S')}_{uuid4().hex[:12]}"
    root.mkdir(exist_ok=False)
    return root


def capture_cmd(  # noqa: C901 -- single-case subprocess/evidence lifecycle, no nested process launching
    spec_file: Path, parent: Path, *, execute: bool = False
) -> Path | None:
    """Validate by default. Only execute=True may launch a native process."""
    spec = _load(spec_file)
    if spec["engine_kind"] != "RORB_CMD":
        message = "Automatic execution is supported only for RORB_CMD"
        raise ValueError(message)
    executable = _file(spec_file, spec.get("executable"))
    catchment = _file(spec_file, spec.get("catchment"))
    storm = _file(spec_file, spec.get("storm"))
    if catchment.suffix.lower() != ".catg" or storm.suffix.lower() != ".stm":
        message = "Initial CMD writer only accepts .catg plus .stm (one ISA, one burst)"
        raise ValueError(message)
    params_raw = spec.get("parameters")
    if not isinstance(params_raw, dict):
        message = "parameters must be an object for the limited CMD writer"
        raise TypeError(message)
    allowed = {"kc", "m", "initial_loss_mm", "continuing", "loss_model"}
    if set(params_raw) != allowed:
        message = "CMD writer requires exactly kc, m, initial_loss_mm, continuing and loss_model"
        raise ValueError(message)
    if spec["effective_settings"].get("isa_mapping") != [1] or spec["effective_settings"].get("burst_mapping") != [1]:
        message = "CMD writer supports only one explicit ISA and one explicit burst mapping ([1])"
        raise ValueError(message)
    params = Parameters.from_mapping(params_raw)
    timeout = spec.get("timeout_seconds", 1800)
    if isinstance(timeout, bool) or not isinstance(timeout, (float, int)) or not math.isfinite(timeout) or timeout <= 0:
        message = "timeout_seconds must be a positive finite number"
        raise ValueError(message)
    if spec.get("gui_effective_settings") is not None:
        message = "GUI settings cannot be applied to a CMD execution"
        raise ValueError(message)
    if not execute:
        return None
    root = _new_root(parent.absolute(), spec["case_id"])
    manifest = _manifest_base(spec, executable, root)
    manifest["effective_settings"] = {**spec["effective_settings"], "cmd_writer": params.as_effective()}
    staged_catchment = root / f"catchment{catchment.suffix.lower()}"
    staged_storm = root / "storm.stm"
    originals = {"catchment": catchment, "storm": storm}
    original_hashes = {key: fingerprint(path) for key, path in originals.items()}
    manifest["inputs"] = {
        "catchment": {"source_fingerprint": _copy(catchment, staged_catchment), "staged": staged_catchment.name},
        "storm": {"source_fingerprint": _copy(storm, staged_storm), "staged": staged_storm.name},
    }
    par = root / "reference.par"
    par.write_bytes(render_par(staged_catchment.absolute(), staged_storm.absolute(), params))
    manifest["inputs"]["parameters"] = {"generated": True, **_record(par, root)}
    manifest["capture"]["argv"] = ["<fingerprinted RORB_CMD executable>", par.name]
    excluded = {staged_catchment, staged_storm, par, root / "manifest.json"}
    started = time.monotonic()
    outcome: Outcome = "captured_unverified"
    stdout = b""
    stderr = b""
    return_code: int | None = None
    try:
        # A user-specified executable is fingerprinted and is never obtained from PATH or a shell.
        result = subprocess.run(  # noqa: S603 -- explicit native opt-in, fixed argument list, no shell
            [str(executable), par.name], cwd=root, check=False, capture_output=True, timeout=timeout
        )
        stdout, stderr, return_code = result.stdout, result.stderr, result.returncode
        if return_code != 0:
            outcome = "nonzero_exit"
    except subprocess.TimeoutExpired as exc:
        outcome = "timeout"
        stdout = exc.stdout or b""
        stderr = exc.stderr or b""
    except OSError as exc:
        outcome = "launch_failed"
        stderr = f"{type(exc).__name__}: {exc}".encode("utf-8", errors="replace")
    finally:
        manifest["capture"]["elapsed_seconds"] = time.monotonic() - started
        manifest["capture"]["timeout_seconds"] = timeout
        manifest["capture"]["return_code"] = return_code
        (root / "stdout.bin").write_bytes(stdout)
        (root / "stderr.bin").write_bytes(stderr)
        for name in ("stdout.bin", "stderr.bin"):
            manifest["capture"][name] = _record(root / name, root)
        excluded.update({root / "stdout.bin", root / "stderr.bin"})
        try:
            manifest["outputs"] = _files(root, excluded)
            reports = [
                root / str(record["path"])
                for record in manifest["outputs"]
                if str(record["path"]).lower().endswith(".out")
            ]
            logs = [
                root / str(record["path"])
                for record in manifest["outputs"]
                if str(record["path"]).lower().endswith(".log")
            ]
            diagnostics = _diagnostics([root / "stdout.bin", root / "stderr.bin", *reports, *logs])
            manifest["diagnostics"] = diagnostics
            if outcome == "captured_unverified":
                if diagnostics["errors"]:
                    outcome = "native_error"
                elif not reports:
                    outcome = "missing_output"
                elif len(reports) > 1:
                    outcome = "incomplete_output"
                else:
                    outcome, manifest["hydrograph_check"] = _check_report(
                        reports[0], spec["requested_print_locations"], spec["expected_steps"]
                    )
                if (diagnostics["warnings"] or manifest["provenance_gaps"]) and outcome in ("success", "zero_runoff"):
                    outcome = "captured_unverified"
        except (OSError, ValueError) as exc:
            manifest["diagnostics"]["errors"].append(f"Evidence inventory/inspection: {type(exc).__name__}: {exc}")
            outcome = "inventory_failed"
        try:
            if any(fingerprint(path) != original_hashes[key] for key, path in originals.items()):
                outcome = "input_mutated"
            if (
                fingerprint(staged_catchment) != original_hashes["catchment"]
                or fingerprint(staged_storm) != original_hashes["storm"]
            ):
                outcome = "input_mutated"
        except OSError as exc:
            outcome = "input_mutated"
            manifest["diagnostics"]["errors"].append(f"Source/staged input inaccessible after run: {exc}")
        manifest["outcome"] = outcome
        _persist(root, manifest)
    return root / "manifest.json"


def archive_reference(spec_file: Path, parent: Path) -> Path:
    """Cache supplied GUI/CMD evidence WITHOUT launching either executable."""
    spec = _load(spec_file)
    executable = _file(spec_file, spec.get("executable"))
    raw_inputs = spec.get("inputs")
    raw_outputs = spec.get("outputs")
    if not isinstance(raw_inputs, dict) or not raw_inputs or not isinstance(raw_outputs, dict) or not raw_outputs:
        message = "Archive requires nonempty inputs and outputs mappings"
        raise ValueError(message)
    if spec["engine_kind"] == "RORBwin" and not isinstance(spec.get("gui_effective_settings"), dict):
        message = "RORBwin archive requires explicit gui_effective_settings"
        raise ValueError(message)
    files = {
        "inputs": {name: _file(spec_file, path) for name, path in raw_inputs.items()},
        "outputs": {name: _file(spec_file, path) for name, path in raw_outputs.items()},
    }
    if any(
        not isinstance(name, str) or not re.fullmatch(r"[A-Za-z0-9_.-]+", name)
        for group in files.values()
        for name in group
    ):
        message = "Archive file identifiers must be safe single path components"
        raise ValueError(message)
    root = _new_root(parent.absolute(), spec["case_id"])
    manifest = _manifest_base(spec, executable, root)
    if spec["engine_kind"] == "RORBwin":
        manifest["effective_settings"]["gui"] = spec["gui_effective_settings"]
    manifest["capture"]["mode"] = "manual_archive_no_execution"
    manifest["capture"]["elapsed_seconds"] = None
    manifest["capture"]["return_code"] = None
    manifest["capture"]["argv"] = None
    manifest["inputs"] = {}
    for category, entries in files.items():
        (root / category).mkdir()
        for key, path in entries.items():
            destination = root / category / key
            metadata = _copy(path, destination)
            record = {"identity": key, **_record(destination, root), "source_fingerprint": metadata}
            if category == "inputs":
                manifest["inputs"][key] = record
            else:
                manifest["outputs"].append(record)
    manifest["outcome"] = "captured_unverified"
    return _persist(root, manifest)


def verify_manifest(manifest_path: Path) -> list[str]:
    """Offline, read-only audit of all staged inputs and retained outputs."""
    manifest: Any = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict) or manifest.get("schema_version") != SCHEMA_VERSION:
        message = "Unrecognised capture manifest schema"
        raise ValueError(message)
    root = manifest_path.absolute().parent
    discrepancies: list[str] = []
    entries = [*manifest.get("outputs", []), *manifest.get("inputs", {}).values()]
    entries.extend(
        manifest["capture"][key] for key in ("stdout.bin", "stderr.bin") if key in manifest.get("capture", {})
    )
    for entry in entries:
        if not isinstance(entry, dict):
            discrepancies.append("Non-object evidence record")
            continue
        name = entry.get("path") or entry.get("staged")
        if not isinstance(name, str):
            discrepancies.append("Missing evidence path")
            continue
        relative = Path(name)
        if relative.is_absolute() or ".." in relative.parts:
            discrepancies.append(f"Unsafe evidence locator: {name}")
            continue
        path = root / relative
        if not path.is_file() or path.is_symlink():
            discrepancies.append(f"Evidence missing or symlinked: {name}")
            continue
        expected = entry.get("source_fingerprint", entry)
        if fingerprint(path) != {key: expected[key] for key in ("sha256", "size_bytes")}:
            discrepancies.append(f"Evidence hash mismatch: {name}")
    return discrepancies
