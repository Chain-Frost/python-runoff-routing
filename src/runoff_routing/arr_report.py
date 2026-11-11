"""Deterministic, non-hydrological ARR IFD inventory exports."""

from __future__ import annotations

import csv
import io
import json
from pathlib import Path

from runoff_routing.arr_data import ARRDocument, IFDDataset, SCHEMA_VERSION


def _dataset_dict(table: IFDDataset) -> dict[str, object]:
    return {
        "source_layer": table.source_layer,
        "name": table.name,
        "baseline": table.baseline,
        "provider_datasets": table.provider_datasets,
        "release_year": table.release_year,
        "scenario_ssp": table.scenario_ssp,
        "scenario_year": table.scenario_year,
        "units": {
            "duration": table.duration_unit,
            "probability": table.probability_unit,
            "rainfall_depth": table.depth_unit,
        },
        "climate_policy": table.climate_policy,
        "durations_min": list(table.durations_min),
        "aep_percent": [str(value) for value in table.aep_percent],
        "depths_mm": [[str(value) for value in row] for row in table.depths_mm],
        "raw_metadata": [list(item) for item in table.raw_metadata],
    }


def inventory_dict(document: ARRDocument) -> dict[str, object]:
    """Preserve source precision as decimal strings; no invented climate provenance."""
    source = document.source
    point = document.location
    return {
        "schema_version": SCHEMA_VERSION,
        "capability": document.capability,
        "source": {
            "system": source.system,
            "export_format": source.export_format,
            "datahub_version": source.datahub_version,
            "compatibility_profile": source.compatibility_profile,
            "sha256": source.sha256,
            "byte_length": source.byte_length,
            "locator": source.locator,
            "captured_at": source.captured_at,
        },
        "location": {
            "latitude": str(point.latitude),
            "longitude": str(point.longitude),
            "centroid_used": point.centroid_used,
            "outlet_latitude": str(point.outlet_latitude) if point.outlet_latitude is not None else None,
            "outlet_longitude": str(point.outlet_longitude) if point.outlet_longitude is not None else None,
            "crs": point.crs,
            "raw_fields": [list(item) for item in point.raw_fields],
        },
        "absent_layers": list(document.absent_layers),
        "unprocessed_layers": list(document.unprocessed_layers),
        "ifd_datasets": [_dataset_dict(table) for table in document.ifd_datasets],
    }


def inventory_json(document: ARRDocument) -> str:
    """Export an inventory with explicit status; not an ARR or RORB design file."""
    return json.dumps(inventory_dict(document), indent=2, ensure_ascii=False) + "\n"


def inventory_csv(document: ARRDocument) -> str:
    """One retained value per dataset/duration/AEP cell, in source order."""
    output = io.StringIO(newline="")
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(
        (
            "source_sha256",
            "datahub_version",
            "source_layer",
            "dataset_name",
            "baseline",
            "provider_datasets",
            "release_year",
            "duration_min",
            "aep_percent",
            "depth_mm",
        )
    )
    for table in document.ifd_datasets:
        for duration, row in zip(table.durations_min, table.depths_mm, strict=True):
            for aep, depth in zip(table.aep_percent, row, strict=True):
                writer.writerow(
                    (
                        document.source.sha256,
                        document.source.datahub_version,
                        table.source_layer,
                        table.name,
                        table.baseline,
                        table.provider_datasets or "",
                        table.release_year if table.release_year is not None else "",
                        duration,
                        str(aep),
                        str(depth),
                    )
                )
    return output.getvalue()


def write_new(path: Path, content: str) -> None:
    """Create a new report without overwriting any existing file, including source."""
    with path.open("xb") as stream:
        stream.write(content.encode("utf-8"))
