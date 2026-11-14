"""Deterministic, non-hydrological ARR IFD inventory exports."""

from __future__ import annotations

import csv
import io
import json
from pathlib import Path

from runoff_routing.arr_data import SCHEMA_VERSION, ARRDocument, IFDDataset


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


def _metadata(values: tuple[tuple[str, str], ...]) -> list[list[str]]:
    return [list(pair) for pair in values]


def _legacy_dict(document: ARRDocument) -> dict[str, object]:
    """Do not promote historical ARR2016 data into a BOM IFD or a storm event."""
    loss = document.legacy_losses
    arf = document.legacy_arf
    return {
        "storm_losses": (
            {
                "initial_loss_mm": str(loss.initial_loss_mm) if loss.initial_loss_mm is not None else None,
                "continuing_loss_mm_per_hour": (
                    str(loss.continuing_loss_mm_per_hour) if loss.continuing_loss_mm_per_hour is not None else None
                ),
                "raw_id": loss.raw_id,
                "metadata": _metadata(loss.metadata),
                "raw_fields": _metadata(loss.raw_fields),
            }
            if loss is not None
            else None
        ),
        "arf_parameters": (
            {
                "zone": arf.zone,
                "coefficients": [[key, str(value)] for key, value in arf.coefficients],
                "metadata": _metadata(arf.metadata),
                "raw_fields": _metadata(arf.raw_fields),
                "applied": False,
            }
            if arf is not None
            else None
        ),
        "temporal_pattern_regions": [
            {
                "kind": region.kind,
                "code": region.code,
                "label": region.label,
                "intersection_fraction": (
                    str(region.intersection_fraction) if region.intersection_fraction is not None else None
                ),
                "metadata": _metadata(region.metadata),
                "increments_loaded": False,
            }
            for region in document.legacy_tp_regions
        ],
        "preburst_tables": [
            {
                "percentile": table.percentile,
                "source_tag": table.source_tag,
                "durations_min": list(table.durations_min),
                "aep_percent": [str(value) for value in table.aep_percent],
                "depths_mm": [[str(value) for value in row] for row in table.depths_mm],
                "ratios": [[str(value) for value in row] for row in table.ratios],
                "metadata": _metadata(table.metadata),
                "applied": False,
            }
            for table in document.legacy_preburst
        ],
        "recognised_unprocessed_sections": [
            {"tag": layer.tag, "body_lines": list(layer.body_lines), "metadata": _metadata(layer.metadata)}
            for layer in document.legacy_unprocessed
        ],
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
            "encoding": source.encoding,
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
        "legacy": _legacy_dict(document),
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


def legacy_preburst_csv(document: ARRDocument) -> str:
    """Report imported depth and ratio separately, without deriving/applying preburst."""
    output = io.StringIO(newline="")
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(("source_sha256", "layer", "percentile", "duration_min", "aep_percent", "depth_mm", "ratio"))
    for table in document.legacy_preburst:
        for duration, depths, ratios in zip(table.durations_min, table.depths_mm, table.ratios, strict=True):
            for aep, depth, ratio in zip(table.aep_percent, depths, ratios, strict=True):
                writer.writerow(
                    (
                        document.source.sha256,
                        table.source_tag,
                        table.percentile,
                        duration,
                        str(aep),
                        str(depth),
                        str(ratio),
                    )
                )
    return output.getvalue()


def write_new(path: Path, content: str) -> None:
    """Create a new report without overwriting any existing file, including source."""
    with path.open("xb") as stream:
        stream.write(content.encode("utf-8"))
