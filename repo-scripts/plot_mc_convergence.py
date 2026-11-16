"""Render scientific SVG figures from retained #148 summary JSON; standard library only.

Example: python repo-scripts/plot_mc_convergence.py research/.../pilot/summary.json --output research/.../figures
"""

from __future__ import annotations

import argparse
import json
import math
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

WIDTH, HEIGHT = 760, 470
LEFT, RIGHT, TOP, BOTTOM = 105, 38, 65, 75


def _svg_child(parent: ET.Element, tag: str, **attributes: str) -> ET.Element:
    """Create SVG children using an explicit ElementTree attribute mapping."""
    return ET.SubElement(parent, tag, attributes)


def _svg_plot(
    title: str,
    ylabel: str,
    curves: list[tuple[str, str, list[tuple[float, float]]]],
    *,
    ymax: float,
    reference_y: float | None = None,
) -> str:
    if ymax <= 0:
        message = "y limit must be positive"
        raise ValueError(message)
    svg = ET.Element(
        "svg",
        {
            "xmlns": "http://www.w3.org/2000/svg",
            "width": str(WIDTH),
            "height": str(HEIGHT),
            "viewBox": f"0 0 {WIDTH} {HEIGHT}",
            "role": "img",
            "aria-label": title,
        },
    )
    _svg_child(svg, "title").text = title
    _svg_child(svg, "rect", x="0", y="0", width=str(WIDTH), height=str(HEIGHT), fill="white")
    plot_width, plot_height = WIDTH - LEFT - RIGHT, HEIGHT - TOP - BOTTOM

    def xy(x: float, y: float) -> tuple[float, float]:
        return LEFT + (math.log10(x) - math.log10(250)) / (math.log10(10000) - math.log10(250)) * plot_width, TOP + (
            1 - y / ymax
        ) * plot_height

    for tick in (0, ymax / 4, ymax / 2, 3 * ymax / 4, ymax):
        y = xy(250, tick)[1]
        _svg_child(
            svg,
            "line",
            x1=str(LEFT),
            y1=f"{y:.2f}",
            x2=str(WIDTH - RIGHT),
            y2=f"{y:.2f}",
            stroke="#dddddd",
            **{"stroke-width": "1"},
        )
        _svg_child(
            svg, "text", x=str(LEFT - 12), y=f"{y + 5:.2f}", **{"text-anchor": "end", "font-size": "13"}
        ).text = f"{tick:.3f}"
    for tick in (250, 500, 1000, 2500, 5000, 10000):
        x, _ = xy(tick, 0)
        _svg_child(svg, "line", x1=f"{x:.2f}", y1=str(TOP), x2=f"{x:.2f}", y2=str(HEIGHT - BOTTOM), stroke="#eeeeee")
        _svg_child(
            svg, "text", x=f"{x:.2f}", y=str(HEIGHT - BOTTOM + 25), **{"text-anchor": "middle", "font-size": "12"}
        ).text = f"{tick:,}"
    if reference_y is not None:
        y = xy(250, reference_y)[1]
        _svg_child(
            svg,
            "line",
            x1=str(LEFT),
            y1=f"{y:.2f}",
            x2=str(WIDTH - RIGHT),
            y2=f"{y:.2f}",
            stroke="#777777",
            **{"stroke-dasharray": "7,4", "stroke-width": "2"},
        )
    for index, (label, color, points) in enumerate(curves):
        ordered = sorted(points)
        _svg_child(
            svg,
            "polyline",
            points=" ".join(f"{xy(x, y)[0]:.1f},{xy(x, y)[1]:.1f}" for x, y in ordered),
            fill="none",
            stroke=color,
            **{"stroke-width": "2.3"},
        )
        for x, y in ordered:
            xx, yy = xy(x, y)
            _svg_child(svg, "circle", cx=f"{xx:.2f}", cy=f"{yy:.2f}", r="4", fill=color)
        lx = LEFT + index * 200
        _svg_child(svg, "line", x1=str(lx), y1="43", x2=str(lx + 23), y2="43", stroke=color, **{"stroke-width": "3"})
        _svg_child(svg, "text", x=str(lx + 28), y="48", **{"font-size": "13"}).text = label
    _svg_child(svg, "text", x=str(WIDTH / 2), y="25", **{"text-anchor": "middle", "font-size": "18"}).text = title
    _svg_child(
        svg, "text", x=str(WIDTH / 2), y=str(HEIGHT - 13), **{"text-anchor": "middle", "font-size": "14"}
    ).text = "Event evaluations per duration / independent run (log scale)"
    _svg_child(
        svg,
        "text",
        x="23",
        y=str(HEIGHT / 2),
        transform=f"rotate(-90 23 {HEIGHT / 2})",
        **{"text-anchor": "middle", "font-size": "14"},
    ).text = ylabel
    return ET.tostring(svg, encoding="unicode", xml_declaration=True) + "\n"


def render(summary: dict[str, Any], output: Path) -> None:
    """Plot between-run SD and joint 24-output pass probability, not SE of a mean."""
    curves: list[tuple[str, str, list[tuple[float, float]]]] = []
    specs = (("zero_atom", 0.05, "Zero-atom, 5% AEP", "#205A91"), ("near_tie", 0.02, "Near-tie, 2% AEP", "#B44E32"))
    for site, aep, label, color in specs:
        points = [
            (float(item["variant"].split("-")[1][1:]) * 50, float(item["sd_single_run"]))
            for item in summary["metrics"]
            if item["site"] == site
            and item["duration"] == "envelope"
            and item["aep"] == aep
            and item["variant"].startswith("h50-")
        ]
        curves.append((label, color, points))
    if not all(points for _, _, points in curves):
        message = "the retained pilot data for both envelope curves are required"
        raise ValueError(message)
    ymax = max(y for _, _, points in curves for _, y in points) * 1.15
    output.mkdir(parents=True, exist_ok=True)
    (output / "single_run_sd.svg").write_text(
        _svg_plot(
            "Independent-run dispersion, analytic reference",
            "Between-run SD (synthetic response units)",
            curves,
            ymax=ymax,
        ),
        encoding="utf-8",
    )
    bands = (("0.01", "1% band", "#205A91"), ("0.02", "2% band", "#A56623"), ("0.05", "5% band", "#25834C"))
    pass_curves = [
        (
            label,
            color,
            [
                (float(item["evaluations_per_run"] / 2), float(item["pass_rate_by_band"][band]))
                for item in summary["whole_run"]
                if item["variant"].startswith("h50-")
            ],
        )
        for band, label, color in bands
    ]
    (output / "whole_run_pass.svg").write_text(
        _svg_plot(
            "Whole-run pass rates (30 pilots per budget)",
            "Fraction of runs passing all 24 estimates",
            pass_curves,
            ymax=1.0,
            reference_y=0.95,
        ),
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("summary", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    render(json.loads(args.summary.read_text(encoding="utf-8")), args.output)


if __name__ == "__main__":
    main()
