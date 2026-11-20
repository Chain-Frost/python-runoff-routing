"""Privacy-minimising read-only structural profile of unqualified RORB_GE CATG.

The output intentionally excludes model names, node/reach labels, coordinates,
paths, rainfall, numeric operands and original file contents. It does not
admit an input for execution, and must not be mistaken for a CATG parser.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import asdict, dataclass
from typing import Literal

from .rorb_codec import SourceDocument

_KNOWN_SECTIONS = frozenset(
    {
        "#FILE COMMENTS",
        "#SUB-AREA AREA COMMENTS",
        "#IMPERVIOUS FRACTION COMMENTS",
        "#BACKGROUND IMAGE",
        "#NODES",
        "#REACHES",
        "#STORAGES",
        "#INFLOW/OUTFLOW",
    }
)
_COUNTED_SECTIONS = _KNOWN_SECTIONS - {"#BACKGROUND IMAGE"}
_VERSION = re.compile(r"C\s+RORB_GE\s+([0-9]+(?:\.[0-9]+)?)\Z")
_SECTION = re.compile(r"C\s+(#.+)\Z")
_POSITIVE_OR_ZERO_INTEGER = re.compile(r"[0-9]+\Z")


@dataclass(frozen=True, slots=True)
class GeSectionShape:
    """Structural statistics only; record bodies and private labels are discarded."""

    section: str
    marker_line: int
    declared_count: int | None
    record_width_counts: tuple[tuple[int, int], ...]


@dataclass(frozen=True, slots=True)
class GeCatgProfile:
    """Observed graphical envelope, never an admitted computational model."""

    qualification: Literal["structure_only_unqualified"]
    envelope: Literal["bounded", "incomplete"]
    declared_ge_version: str | None
    version_marker_count: int
    end_marker_count: int
    sections: tuple[GeSectionShape, ...]
    tail_first_record: Literal["0", "1", "other", "missing"]
    tail_noncomment_record_count: int
    source_size_bytes: int
    source_newline: str
    source_sha256: str | None
    diagnostics: tuple[str, ...]

    def to_json(self) -> str:
        """Export only aggregate structure, never source lines or locations."""
        return json.dumps(asdict(self), indent=2, sort_keys=True)


def _shape(lines: tuple[str, ...], marker: str, start: int, stop: int) -> GeSectionShape:
    """Group widths without retaining any raw text or numerical operands."""
    widths: Counter[int] = Counter()
    declared_count: int | None = None
    for number in range(start + 1, stop):
        tokens = lines[number].strip().split()
        if not tokens or tokens[0] != "C" or len(tokens) == 1:
            continue
        width = len(tokens) - 1
        widths[width] += 1
        if (
            declared_count is None
            and number == start + 1
            and marker in _COUNTED_SECTIONS
            and width == 1
            and _POSITIVE_OR_ZERO_INTEGER.fullmatch(tokens[1]) is not None
        ):
            declared_count = int(tokens[1])
    return GeSectionShape(marker, start + 1, declared_count, tuple(sorted(widths.items())))


def profile_graphical_catg(data: bytes, *, include_sha256: bool = False) -> GeCatgProfile:
    """Summarise raw CATG graphical shapes without importing or running a model.

    Even when the source says RORB_GE 6.52, this method cannot establish its
    exact graphical grammar, numerical control validity or native equivalence.
    The optional source hash should be included only in locally retained
    provenance; the CLI omits it by default.
    """
    source = SourceDocument.from_bytes(data)
    lines = source.lines
    versions = [
        (index, found.group(1))
        for index, line in enumerate(lines)
        if (found := _VERSION.fullmatch(line.strip())) is not None
    ]
    endings = [index for index, line in enumerate(lines) if line.strip() == "C END RORB_GE"]
    diagnostics: list[str] = []
    if len(versions) != 1:
        diagnostics.append("missing_or_multiple_version_markers")
    if len(endings) != 1:
        diagnostics.append("missing_or_multiple_end_markers")

    end = endings[0] if len(endings) == 1 else len(lines)
    if len(versions) == 1 and versions[0][0] >= end:
        diagnostics.append("version_not_before_end_marker")
    markers: list[tuple[int, str]] = []
    for index in range(end):
        match = _SECTION.fullmatch(lines[index].strip())
        if match is None:
            continue
        name = match.group(1)
        # Unknown section names may contain client-supplied text. Redact.
        markers.append((index, name if name in _KNOWN_SECTIONS else "other_section"))
    sections = tuple(
        _shape(lines, name, position, markers[i + 1][0] if i + 1 < len(markers) else end)
        for i, (position, name) in enumerate(markers)
    )
    if any(s.section == "other_section" for s in sections):
        diagnostics.append("unknown_graphical_sections_present")
    tail = (
        [
            line.strip()
            for line in lines[end + 1 :]
            if line.strip() and not line.lstrip().startswith(("C ", "C\t")) and line.strip() != "C"
        ]
        if len(endings) == 1
        else []
    )
    first = tail[0] if tail else ""
    tail_kind: Literal["0", "1", "other", "missing"] = (
        "0" if first == "0" else "1" if first == "1" else "other" if first else "missing"
    )
    if not tail:
        diagnostics.append("no_computational_tail_observed")
    bounded = len(versions) == 1 and len(endings) == 1 and versions[0][0] < end
    return GeCatgProfile(
        "structure_only_unqualified",
        "bounded" if bounded else "incomplete",
        versions[0][1] if len(versions) == 1 else None,
        len(versions),
        len(endings),
        sections,
        tail_kind,
        len(tail),
        len(data),
        source.newline,
        source.sha256 if include_sha256 else None,
        tuple(diagnostics),
    )
