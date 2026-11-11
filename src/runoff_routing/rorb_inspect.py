"""Read-only RORB inspect/validate dispatcher; never launches a native executable."""

from __future__ import annotations

from pathlib import Path

from .rorb_documents import Diagnostic, Inspection, RorbSource
from .rorb_out import inspect_output
from .rorb_par import inspect_cmd_parameters


def inspect_file(path: Path) -> Inspection:
    """Return structured diagnostics while preserving the original source file."""
    source = RorbSource.read(path)
    suffix = path.suffix.lower()
    if suffix == ".par":
        return inspect_cmd_parameters(source)
    if suffix == ".out":
        return inspect_output(source)
    if suffix in {".cat", ".catg", ".dat", ".stm"}:
        return Inspection(
            suffix.removeprefix("."),
            "unsupported",
            source,
            (
                Diagnostic(
                    "fixture_required", "Catchment/storm semantics require verified grammar fixtures", "unsupported"
                ),
            ),
        )
    return Inspection(
        "unknown",
        "unsupported",
        source,
        (Diagnostic("unknown_extension", "File type is not a supported RORB inspection format", "unsupported"),),
    )
