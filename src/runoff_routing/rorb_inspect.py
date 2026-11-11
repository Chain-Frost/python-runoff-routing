"""Read-only RORB inspect/validate dispatcher; never launches a native executable."""

from __future__ import annotations

from pathlib import Path

from .rorb_codec import FormatProblem, parse_catg, parse_design_stm
from .rorb_documents import Diagnostic, Inspection, RorbSource, SourceField
from .rorb_model import CatchmentModel
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
    if suffix in {".catg", ".stm"}:
        try:
            payload = path.read_bytes()
            parsed = parse_catg(payload) if suffix == ".catg" else parse_design_stm(payload)
        except FormatProblem as exc:
            return Inspection(
                suffix.removeprefix("."),
                "unsupported" if exc.status == "unsupported" else "invalid",
                source,
                (Diagnostic(exc.code, str(exc), "unsupported" if exc.status == "unsupported" else "error", exc.line),),
            )
        if source.sha256 != parsed.source.sha256:
            notes = (Diagnostic("source_changed", "Source file changed between read and parse", "error"),)
            return Inspection(suffix.removeprefix("."), "invalid", source, notes)
        fields = tuple(
            SourceField(item.line, item.field, item.source_text, source.lines[item.line - 1])
            for item in parsed.source_map
        )
        notes = (Diagnostic("execution_unverified", "Parsed syntax is not native or S2 numerical approval", "warning"),)
        if isinstance(parsed.model, CatchmentModel):
            return Inspection("rorb_ge_002", "parsed", source, notes, fields, catchment=parsed.model)
        return Inspection("design_explicit", "parsed", source, notes, fields, storm=parsed.model)
    if suffix in {".cat", ".dat"}:
        return Inspection(
            suffix.removeprefix("."),
            "unsupported",
            source,
            (Diagnostic("fixture_required", "Combined/text grammar is not characterised", "unsupported"),),
        )
    return Inspection(
        "unknown",
        "unsupported",
        source,
        (Diagnostic("unknown_extension", "File type is not a supported RORB inspection format", "unsupported"),),
    )
