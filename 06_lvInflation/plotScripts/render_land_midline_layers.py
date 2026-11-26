#!/usr/bin/env python3
"""Data layers of the ventricular mid-wall figures (manuscript Figs 15 and 16).

The published figures ``land_problem2_m3_combined_overlay.pdf`` (inflation,
Land et al. 2015 problem 2) and ``land_problem3_m3_combined_overlay.pdf``
(active contraction, problem 3) are Keynote composites made by P. Cardiff:
faint JPEG crops of the published Land et al. result figures behind the
vector data layer rendered by ``render_land_problem2_m3_combined.py`` /
``render_land_problem3_m3_midlines.py`` (HPC versions archived in
``paperData/0{6,7}_*/plotScripts`` and in
``figureStaging_2026-10-29/backup_scripts/land{2,3}``).

This script re-renders ONLY the data layer in the shared manuscript style
(embedded Helvetica, printed font sizes, shared mesh-level identities) while
keeping the page size and every panel rectangle, axis window, tick set,
marker stride and clipping IDENTICAL to the original layer, so that the
layer can be put back under the same Keynote transforms with
``composite_land_overlay.py`` and stays aligned with the faint reference
layers.  No numerical value is changed: x and z are read from
``midLineDeformed.txt`` (m) and converted to mm as before.

Font sizes are the printed sizes divided by the composite's scale
(0.783 for Fig 15, 0.788 for Fig 16): 8 pt ticks/legend and 9 pt axis
labels on the page.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

PT = 72.0
PAGE_WIDTH = 6.0 * PT
PAGE_HEIGHT = 7.2 * PT

# --- shared style (paper_figure_style.py values expressed at layer scale) ---
LAYER_SCALE = 0.783           # layer -> printed (Keynote 0.877 x LaTeX 0.892)
FONT = "STIXGeneral"
FONT_BOLD = "STIXGeneral-Bold"
# STIX as bundled with matplotlib: the family of the cas-sc text and mathematics
import matplotlib  # noqa: E402
_TTF = Path(matplotlib.get_data_path()) / "fonts" / "ttf"
pdfmetrics.registerFont(TTFont(FONT, str(_TTF / "STIXGeneral.ttf")))
pdfmetrics.registerFont(TTFont(FONT_BOLD, str(_TTF / "STIXGeneralBol.ttf")))
FONT_ITALIC = "STIXGeneral-Italic"     # mathematical variables (x, z), as $x$ in the text
pdfmetrics.registerFont(TTFont(FONT_ITALIC, str(_TTF / "STIXGeneralItalic.ttf")))

TICK_FONT_SIZE = round(8.0 / LAYER_SCALE, 1)      # 10.2 -> 8 pt printed
AXIS_FONT_SIZE = round(9.0 / LAYER_SCALE, 1)      # 11.5 -> 9 pt printed
PANEL_FONT_SIZE = round(9.0 / LAYER_SCALE, 1)
LEGEND_FONT_SIZE = TICK_FONT_SIZE
SERIES_LINE_WIDTH = round(0.8 / LAYER_SCALE, 2)   # 0.8 pt printed (paper_figure_style.LINE_WIDTH)
MARKER_LINE_WIDTH = round(0.75 / LAYER_SCALE, 2)  # 0.75 pt printed (MARKER_EDGE_WIDTH)
MARKER_SIZE = 2.9                                 # 4.5 pt markers printed
GRID_LINE_WIDTH = 0.6
FRAME_LINE_WIDTH = 1.0
INK = colors.HexColor("#111111")
GRID = colors.HexColor("#D6D6D6")
PANEL_GUIDE = colors.HexColor("#8A8A8A")


@dataclass(frozen=True)
class Series:
    mesh: str
    label: str
    colour: object
    marker: str


# Mesh-level identities (paper_figure_style.MESH_LEVEL_STYLES, Okabe-Ito)
SERIES = (
    Series("mesh1", "Mesh 1", colors.HexColor("#0072B2"), "circle"),
    Series("mesh2", "Mesh 2", colors.HexColor("#D55E00"), "square"),
    Series("mesh3", "Mesh 3", colors.HexColor("#009E73"), "triangle"),
)


@dataclass(frozen=True)
class Panel:
    label: str
    x_bounds: tuple[float, float]
    y_bounds: tuple[float, float]
    x_ticks: tuple[float, ...]
    y_ticks: tuple[float, ...]
    left: float
    bottom: float
    width: float
    height: float
    marker_stride: int
    y_fmt: str = "{:g}"            # tick-label format of the z axis
    x_fmt: str = "{:g}"
    label_dy: float | None = None  # panel label height above the frame (layer units)
    show_label: bool = True        # False: the LaTeX sub-caption gives (a), (b), (c)


# Geometry copied unchanged from the HPC scripts that produced the paper layers.
PROBLEMS = {
    2: dict(
        title="Land Problem 2: m = 2 mid-wall deformation",
        runs_subdir="midWallLines",
        panels=(
            Panel("(a)", (-13.5, 0.0), (-28.0, 5.0), (-10.0, -5.0, 0.0),
                  (-25.0, -20.0, -15.0, -10.0, -5.0, 0.0, 5.0), 142.0, 245.0, 106.4, 260.0, 8),
            Panel("(b)", (-5.0, 0.0), (-28.0, -25.0), (-5.0, -4.0, -3.0, -2.0, -1.0, 0.0),
                  (-28.0, -27.5, -27.0, -26.5, -26.0, -25.5, -25.0), 50.0, 42.0, 154.0, 154.0, 2),
            Panel("(c)", (-13.4, -12.4), (-9.0, -2.0), (-13.4, -13.2, -13.0, -12.8, -12.6, -12.4),
                  (-9.0, -8.0, -7.0, -6.0, -5.0, -4.0, -3.0, -2.0), 265.0, 42.0, 154.0, 154.0, 2),
        ),
    ),
    3: dict(
        title="Land Problem 3: m = 2 mid-wall deformation",
        runs_subdir="midWallLines",
        panels=(
            Panel("(a)", (-10.0, 0.0), (-20.0, 5.0), (-10.0, -5.0, 0.0),
                  (-20.0, -15.0, -10.0, -5.0, 0.0, 5.0), 142.0, 245.0, 104.0, 260.0, 8),
            Panel("(b)", (-2.0, 0.0), (-15.0, -13.0), (-2.0, -1.5, -1.0, -0.5, 0.0),
                  (-15.0, -14.5, -14.0, -13.5, -13.0), 50.0, 42.0, 154.0, 154.0, 2),
            # The paper layer had a single x tick (-8.5); the labels -8.75 and
            # -8.25 were added by hand in Keynote.  They are drawn natively here.
            Panel("(c)", (-8.75, -8.25), (-2.0, 2.0), (-8.75, -8.5, -8.25),
                  (-2.0, -1.0, 0.0, 1.0, 2.0), 265.0, 42.0, 154.0, 154.0, 2),
        ),
    ),
}


def read_midline(path: Path) -> list[tuple[float, float]]:
    """Read x and z from an OpenFOAM midline result (m) and convert to mm."""
    points: list[tuple[float, float]] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            fields = line.split()
            if len(fields) < 3:
                raise ValueError(f"Expected x y z in {path}:{line_number}")
            points.append((1.0e3 * float(fields[0]), 1.0e3 * float(fields[2])))
    if not points:
        raise ValueError(f"No midline points found in {path}")
    return points


def tx(panel: Panel, x: float) -> float:
    lo, hi = panel.x_bounds
    return panel.left + (x - lo) / (hi - lo) * panel.width


def ty(panel: Panel, z: float) -> float:
    lo, hi = panel.y_bounds
    return panel.bottom + (z - lo) / (hi - lo) * panel.height


def fmt(value: float, pattern: str = "{:g}") -> str:
    return pattern.format(value).replace("-", "−")


# --- compact layout (Fig 15, 12 Nov 2026) -----------------------------------
# (a) tall on the left; (b) top right and (c) bottom right; the top of (a) is
# level with the top of (b) and the bottom of (a) with the bottom of (c).
# (b) is the upper zoom (inflection region) and (c) the lower one (apex).
# Panels keep their index (0 full line, 1 apex, 2 inflection) because the
# compositor pairs index k with the k-th faint Land et al. layer.
# Geometry in printed points (the layer is placed at LAYER_SCALE), so every
# panel has the same 8 pt / 9 pt text.  (a) keeps equal x and z scales.
ZOOM_HIGHLIGHT = colors.HexColor("#CC79A7")   # Okabe-Ito reddish purple (not a mesh colour)
# zoom call-outs drawn in panel (a), data coordinates [mm]:
#   panel index -> (label centre, arrow start, arrow tip)
COMPACT_CALLOUTS = {
    2: {2: ((-7.9, -5.5), (-9.0, -5.5), (-12.25, -5.5)),     # (b): inflection box, label to its right
        1: ((-2.5, -20.6), (-2.5, -21.6), (-2.5, -24.85))},  # (c): apex box, label above it
    3: {2: ((-5.8, -1.2), (-6.6, -1.2), (-8.15, -1.2)),      # (b): inflection box, label to its right
        1: ((-1.0, -9.6), (-1.0, -10.4), (-1.0, -12.85))},   # (c): apex box, label above it
}


def tick_format(ticks) -> str:
    """Same number of decimals for every label of an axis (e.g. -13.4 ... -13.0 ... -12.4)."""
    decimals = 0
    for value in ticks:
        text = f"{value:g}"
        if "." in text:
            decimals = max(decimals, len(text.split(".")[1]))
    return f"{{:.{decimals}f}}"
# Each panel is cut into its own subfigure PDF (split_land_panels.py); gap_v leaves room for the
# sub-caption of (b) between (b) and (c), so that LaTeX can keep the panel edges aligned.
COMPACT_PRINTED = dict(left_margin=36.0, gap_h=50.0, right_margin=12.0, bottom_margin=30.0,
                       gap_v=60.0, top_margin=6.0, small=128.0)


def compact_layout(problem: int) -> dict:
    p = COMPACT_PRINTED
    old = PROBLEMS[problem]["panels"]
    a, b, c = old
    height_a = 2.0 * p["small"] + p["gap_v"]
    width_a = height_a * (a.x_bounds[1] - a.x_bounds[0]) / (a.y_bounds[1] - a.y_bounds[0])
    left_a = p["left_margin"]
    left_bc = left_a + width_a + p["gap_h"]
    bottom_c = p["bottom_margin"]
    bottom_b = bottom_c + p["small"] + p["gap_v"]
    s = 1.0 / LAYER_SCALE
    common = dict(label_dy=6.0 * s, show_label=False)
    def fmts(panel):
        return dict(x_fmt=tick_format(panel.x_ticks), y_fmt=tick_format(panel.y_ticks), **common)

    panels = (
        Panel("(a)", a.x_bounds, a.y_bounds, a.x_ticks, a.y_ticks,
              left_a * s, bottom_c * s, width_a * s, height_a * s, a.marker_stride, **fmts(a)),
        # apex zoom: lower right, labelled (c)
        Panel("(c)", b.x_bounds, b.y_bounds, b.x_ticks, b.y_ticks,
              left_bc * s, bottom_c * s, p["small"] * s, p["small"] * s, b.marker_stride, **fmts(b)),
        # inflection zoom: upper right, labelled (b)
        Panel("(b)", c.x_bounds, c.y_bounds, c.x_ticks, c.y_ticks,
              left_bc * s, bottom_b * s, p["small"] * s, p["small"] * s, c.marker_stride, **fmts(c)),
    )
    width = (left_bc + p["small"] + p["right_margin"]) * s
    height = (bottom_b + p["small"] + p["top_margin"]) * s
    return dict(panels=panels, page=(width, height), legend_in=0, callouts=COMPACT_CALLOUTS.get(problem, {}))


def draw_zoom_boxes(pdf, panels) -> None:
    """Zoom regions in panel (a): translucent coloured fill and a dashed coloured outline.

    An opaque white patch (slightly larger than the box) first hides what the
    faint Keynote raster has under the box: its JPEG crops carry dashed lines
    there that cannot be removed as objects.  The curves are drawn afterwards.
    """
    full = panels[0]
    pad = 1.2 / LAYER_SCALE
    for panel in panels[1:]:
        x0, x1 = (tx(full, value) for value in panel.x_bounds)
        y0, y1 = (ty(full, value) for value in panel.y_bounds)
        pdf.saveState()
        clip = pdf.beginPath()
        clip.rect(full.left, full.bottom, full.width, full.height)
        pdf.clipPath(clip, stroke=0, fill=0)
        pdf.setFillColor(colors.white)
        pdf.rect(x0 - pad, y0 - pad, x1 - x0 + 2 * pad, y1 - y0 + 2 * pad, stroke=0, fill=1)
        pdf.setFillColor(ZOOM_HIGHLIGHT)
        pdf.setFillAlpha(0.22)
        pdf.rect(x0, y0, x1 - x0, y1 - y0, stroke=0, fill=1)
        pdf.setFillAlpha(1.0)
        pdf.setStrokeColor(ZOOM_HIGHLIGHT)
        pdf.setLineWidth(0.8 / LAYER_SCALE)
        pdf.setDash(3.0 / LAYER_SCALE, 2.0 / LAYER_SCALE)
        pdf.rect(x0, y0, x1 - x0, y1 - y0, stroke=1, fill=0)
        pdf.restoreState()


def draw_zoom_callouts(pdf, panels, callouts) -> None:
    """Arrow from a bold panel label to its zoom box in panel (a)."""
    full = panels[0]
    head = 4.0 / LAYER_SCALE
    for index, ((lx, lz), (sx, sz), (ex, ez)) in callouts.items():
        x0, y0, x1, y1 = tx(full, sx), ty(full, sz), tx(full, ex), ty(full, ez)
        length = ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5
        ux, uy = (x1 - x0) / length, (y1 - y0) / length
        pdf.saveState()
        pdf.setStrokeColor(ZOOM_HIGHLIGHT)
        pdf.setFillColor(ZOOM_HIGHLIGHT)
        pdf.setLineWidth(0.9 / LAYER_SCALE)
        pdf.line(x0, y0, x1 - ux * head * 0.8, y1 - uy * head * 0.8)
        path = pdf.beginPath()
        path.moveTo(x1, y1)
        path.lineTo(x1 - ux * head - uy * head * 0.45, y1 - uy * head + ux * head * 0.45)
        path.lineTo(x1 - ux * head + uy * head * 0.45, y1 - uy * head - ux * head * 0.45)
        path.close()
        pdf.drawPath(path, stroke=0, fill=1)
        pdf.setFillColor(INK)
        pdf.setFont(FONT_BOLD, PANEL_FONT_SIZE)
        pdf.drawCentredString(tx(full, lx), ty(full, lz) - 0.36 * PANEL_FONT_SIZE, panels[index].label)
        pdf.restoreState()


def draw_marker(pdf, x, y, series: Series, size: float = MARKER_SIZE) -> None:
    pdf.setStrokeColor(series.colour)
    pdf.setFillColor(colors.white)
    pdf.setLineWidth(MARKER_LINE_WIDTH)
    if series.marker == "circle":
        pdf.circle(x, y, size, stroke=1, fill=1)
    elif series.marker == "square":
        pdf.rect(x - size, y - size, 2 * size, 2 * size, stroke=1, fill=1)
    else:
        path = pdf.beginPath()
        path.moveTo(x, y + size + 0.4)
        path.lineTo(x - size - 0.3, y - size)
        path.lineTo(x + size + 0.3, y - size)
        path.close()
        pdf.drawPath(path, stroke=1, fill=1)


def math_label(pdf, x: float, y: float, variable: str, rest: str) -> None:
    """Centred axis label: italic variable (STIX) followed by upright text, e.g. 'x [mm]'."""
    w_var = pdfmetrics.stringWidth(variable, FONT_ITALIC, AXIS_FONT_SIZE)
    w_rest = pdfmetrics.stringWidth(rest, FONT, AXIS_FONT_SIZE)
    x0 = x - 0.5 * (w_var + w_rest)
    pdf.setFillColor(INK)
    pdf.setFont(FONT_ITALIC, AXIS_FONT_SIZE)
    pdf.drawString(x0, y, variable)
    pdf.setFont(FONT, AXIS_FONT_SIZE)
    pdf.drawString(x0 + w_var, y, rest)


def draw_axes(pdf, panel: Panel) -> None:
    top = panel.bottom + panel.height
    right = panel.left + panel.width

    pdf.setStrokeColor(GRID)
    pdf.setLineWidth(GRID_LINE_WIDTH)
    pdf.setDash(1.0, 2.0)
    for value in panel.x_ticks:
        x = tx(panel, value)
        pdf.line(x, panel.bottom, x, top)
    for value in panel.y_ticks:
        y = ty(panel, value)
        pdf.line(panel.left, y, right, y)
    pdf.setDash()

    pdf.setStrokeColor(INK)
    pdf.setLineWidth(FRAME_LINE_WIDTH)
    pdf.rect(panel.left, panel.bottom, panel.width, panel.height, stroke=1, fill=0)
    tick = 3.0 / LAYER_SCALE * 0.8
    for value in panel.x_ticks:
        x = tx(panel, value)
        pdf.line(x, panel.bottom, x, panel.bottom - tick)
    for value in panel.y_ticks:
        y = ty(panel, value)
        pdf.line(panel.left, y, panel.left - tick, y)

    pdf.setFillColor(INK)
    pdf.setFont(FONT, TICK_FONT_SIZE)
    for value in panel.x_ticks:
        pdf.drawCentredString(tx(panel, value), panel.bottom - tick - 1.5 - 0.72 * TICK_FONT_SIZE,
                              fmt(value, panel.x_fmt))
    tick_width = max(pdfmetrics.stringWidth(fmt(v, panel.y_fmt), FONT, TICK_FONT_SIZE) for v in panel.y_ticks)
    for value in panel.y_ticks:
        pdf.drawRightString(panel.left - tick - 2.0, ty(panel, value) - 0.36 * TICK_FONT_SIZE,
                            fmt(value, panel.y_fmt))

    math_label(pdf, (panel.left + right) / 2.0, panel.bottom - 29.5, "x", " [mm]")
    pdf.saveState()
    # rotated label: glyphs extend ~0.72 em to the left of the baseline
    pdf.translate(panel.left - tick - 2.0 - tick_width - 6.0, (panel.bottom + top) / 2.0)
    pdf.rotate(90)
    math_label(pdf, 0.0, 0.0, "z", " [mm]")
    pdf.restoreState()

    if not panel.show_label:
        return
    if panel.label_dy is not None:
        label_y = top + panel.label_dy
    else:
        label_y = top + (2.0 if panel.label == "(a)" else 8.0)
    pdf.setFont(FONT_BOLD, PANEL_FONT_SIZE)
    pdf.drawString(panel.left - 28.0, label_y, panel.label)


def draw_series(pdf, panel: Panel, points, series: Series) -> None:
    mapped = [(tx(panel, x), ty(panel, z)) for x, z in points]
    pdf.saveState()
    clip = pdf.beginPath()
    clip.rect(panel.left, panel.bottom, panel.width, panel.height)
    pdf.clipPath(clip, stroke=0, fill=0)

    pdf.setStrokeColor(series.colour)
    pdf.setLineWidth(SERIES_LINE_WIDTH)
    path = pdf.beginPath()
    path.moveTo(*mapped[0])
    for point in mapped[1:]:
        path.lineTo(*point)
    pdf.drawPath(path, stroke=1, fill=0)

    visible_indices = [
        index
        for index, (x, z) in enumerate(points)
        if panel.x_bounds[0] <= x <= panel.x_bounds[1]
        and panel.y_bounds[0] <= z <= panel.y_bounds[1]
    ]
    selected = visible_indices[:: panel.marker_stride]
    if visible_indices and selected[-1] != visible_indices[-1]:
        selected.append(visible_indices[-1])
    for index in selected:
        draw_marker(pdf, *mapped[index], series)
    pdf.restoreState()


def legend_size() -> tuple[float, float]:
    row_height = 1.9 * LEGEND_FONT_SIZE
    text_width = max(pdfmetrics.stringWidth(item.label, FONT, LEGEND_FONT_SIZE) for item in SERIES)
    return 12.0 + 25.0 + 8.0 + text_width + 12.0, 12.0 + row_height * len(SERIES)


def draw_legend(pdf, x: float = 276.0, y: float = 356.0) -> None:
    row_height = 1.9 * LEGEND_FONT_SIZE
    sample_width = 25.0
    box_width, box_height = legend_size()

    # White opaque patch without a frame, as for every other legend of the
    # paper (paper_figure_style.legend); the HPC layer had a grey frame.
    pdf.setFillColor(colors.white)
    pdf.roundRect(x, y, box_width, box_height, 2.5, stroke=0, fill=1)

    row_y = y + box_height - 10.0 - 0.72 * LEGEND_FONT_SIZE
    pdf.setFont(FONT, LEGEND_FONT_SIZE)
    for series in SERIES:
        sample_y = row_y + 0.36 * LEGEND_FONT_SIZE
        pdf.setStrokeColor(series.colour)
        pdf.setLineWidth(SERIES_LINE_WIDTH)
        pdf.line(x + 9.0, sample_y, x + 9.0 + sample_width, sample_y)
        draw_marker(pdf, x + 9.0 + sample_width / 2.0, sample_y, series)
        pdf.setFillColor(INK)
        pdf.drawString(x + 9.0 + sample_width + 7.0, row_y, series.label)
        row_y -= row_height


def draw_magnification_guides(pdf, panels) -> None:
    full = panels[0]
    pdf.setStrokeColor(PANEL_GUIDE)
    pdf.setLineWidth(0.65)
    pdf.setDash(2.0, 1.8)
    for panel in panels[1:]:
        x0, x1 = (tx(full, value) for value in panel.x_bounds)
        y0, y1 = (ty(full, value) for value in panel.y_bounds)
        pdf.rect(x0, y0, x1 - x0, y1 - y0, stroke=1, fill=0)
    pdf.setDash()


def render(problem: int, data_dir: Path, output: Path, series_json: Path | None = None,
           layout: str = "keynote") -> Path:
    spec = PROBLEMS[problem]
    base = data_dir / spec["runs_subdir"] if spec["runs_subdir"] else data_dir
    datasets = {s.mesh: read_midline(base / s.mesh / "midLineDeformed.txt") for s in SERIES}
    if layout == "compact":
        compact = compact_layout(problem)
        panels, page = compact["panels"], compact["page"]
    else:
        panels, page = spec["panels"], (PAGE_WIDTH, PAGE_HEIGHT)

    output.parent.mkdir(parents=True, exist_ok=True)
    pdf = canvas.Canvas(str(output), pagesize=page, pageCompression=1,
                        initialFontName=FONT, initialFontSize=TICK_FONT_SIZE)
    pdf.setTitle(spec["title"])
    pdf.setSubject(f"Data layer ({layout} layout): full line, apical and inflection regions")
    pdf.setAuthor("solids4foam")
    for panel in panels:
        draw_axes(pdf, panel)
        if layout == "compact" and panel is panels[0]:
            draw_zoom_boxes(pdf, panels)        # under the curves
        for series in SERIES:
            draw_series(pdf, panel, datasets[series.mesh], series)
    if layout == "compact":
        draw_zoom_callouts(pdf, panels, compact["callouts"])
    else:
        draw_magnification_guides(pdf, panels)
    if layout == "compact":
        # inside panel (a), upper right (no data there)
        box_width, box_height = legend_size()
        a = panels[0]
        inset = 4.0 / LAYER_SCALE
        draw_legend(pdf, a.left + a.width - box_width - inset, a.bottom + a.height - box_height - inset)
    else:
        draw_legend(pdf)
    pdf.showPage()
    pdf.save()
    if series_json is not None:
        import json

        series_json.parent.mkdir(parents=True, exist_ok=True)
        series_json.write_text(json.dumps({
            f"land_problem{problem}_layer": {
                "series": {s.mesh: {"x": [p[0] for p in datasets[s.mesh]], "y": [p[1] for p in datasets[s.mesh]]}
                           for s in SERIES},
                "panels": [p.__dict__ for p in spec["panels"]],
            }
        }, indent=1))
    print(f"Wrote {output}")
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--problem", type=int, choices=(2, 3), required=True)
    parser.add_argument("--data-dir", type=Path, required=True,
                        help="directory containing midWallLines/mesh{1,2,3}/midLineDeformed.txt")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--dump-series", type=Path)
    parser.add_argument("--layout", choices=("keynote", "compact"), default="keynote",
                        help="keynote: original panel geometry; compact: (a) left, (b)/(c) stacked right")
    args = parser.parse_args()
    render(args.problem, args.data_dir, args.output, args.dump_series, args.layout)


if __name__ == "__main__":
    main()
