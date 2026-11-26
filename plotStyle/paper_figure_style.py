#!/usr/bin/env python3
"""Shared publication style for the figures of the JFNK mixed-formulation paper.

Design rules (derived from the linear Cook's membrane figures, 26 Oct 2026,
`linearElastic/cooksMembrane/plotScripts/plot_paper.py`, and adjusted so that
the text is readable at the size printed in the cas-sc manuscript):

* Every figure is drawn at its printed size.  cas-sc has
  ``\\linewidth = 468.33 pt`` (6.48 in), body text 10 pt, captions 9 pt.  The
  font sizes below are therefore the printed sizes: legend, tick and
  annotation text is 8 pt (80 % of the body text), axis labels 9 pt.
* Font family STIX (STIXGeneral, the copy bundled with matplotlib), embedded
  as a subset (``pdf.fonttype 42``).  The manuscript class cas-sc loads the
  ``stix`` package, so tick labels, words and mathematics (``mathtext.fontset
  = "stix"``) match the text and equations of the paper.
* Full axes box, ticks outside on the bottom/left, a subtle dotted light-grey
  major grid drawn behind the data, white legend background without a frame.
* Line width 0.8 pt, open markers 4.5 pt with 0.75 pt edges (Elsevier
  minimum 0.5 pt).
* Method identities (colour, marker) are fixed across the paper, see
  :data:`METHOD_STYLES`.  Quantities that are not methods (pressure-scale
  sweeps, mesh families, mesh levels, error measures) use their own,
  separately documented encodings so that method colours are never reused
  for unrelated quantities.

Usage::

    import paper_figure_style as pfs
    pfs.apply_style()
    fig, ax = pfs.new_figure(width_fraction=0.49)
    ax.plot(x, y, **pfs.line_kwargs("coupled_m2"))
    pfs.style_axes(ax)
    pfs.legend(ax)
    pfs.save(fig, "figure.pdf")
"""

from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402

# ---------------------------------------------------------------------------
# Manuscript geometry (measured with a cas-sc probe document, TeX Live 2025)
# ---------------------------------------------------------------------------
LINEWIDTH_PT = 468.3324          # \linewidth = \textwidth = \columnwidth
TEX_PT_PER_IN = 72.27
LINEWIDTH_IN = LINEWIDTH_PT / TEX_PT_PER_IN   # 6.480 in
BODY_FONT_PT = 10.0
CAPTION_FONT_PT = 9.0

# Printed font sizes [pt]
FONT_SIZES = {
    "tick": 8.0,
    "label": 9.0,
    "legend": 8.0,
    "legend_title": 8.0,
    "annotation": 8.0,
    "title": 9.0,
    "panel_label": 9.0,
}

FONT_FAMILY = "STIXGeneral"


def stix_font_file(bold: bool = False) -> str:
    """Path of matplotlib's bundled STIXGeneral TrueType file (used by reportlab layers)."""
    name = "STIXGeneralBol.ttf" if bold else "STIXGeneral.ttf"
    return str(Path(matplotlib.get_data_path()) / "fonts" / "ttf" / name)

LINE_WIDTH = 0.8
MARKER_SIZE = 4.5
MARKER_EDGE_WIDTH = 0.75
REFERENCE_LINE_WIDTH = 0.8
GRID_COLOUR = "#D6D6D6"
INK = "#111111"


def fig_width(fraction: float) -> float:
    """Printed width [in] of a figure included at ``fraction * \\linewidth``."""
    return fraction * LINEWIDTH_IN


RC_PARAMS = {
    "font.family": "serif",
    "font.serif": [FONT_FAMILY],
    "font.size": FONT_SIZES["annotation"],
    "axes.labelsize": FONT_SIZES["label"],
    "axes.titlesize": FONT_SIZES["title"],
    "xtick.labelsize": FONT_SIZES["tick"],
    "ytick.labelsize": FONT_SIZES["tick"],
    "legend.fontsize": FONT_SIZES["legend"],
    "legend.title_fontsize": FONT_SIZES["legend_title"],
    "figure.titlesize": FONT_SIZES["title"],
    "mathtext.fontset": "stix",
    "mathtext.default": "it",
    "axes.unicode_minus": True,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "pdf.compression": 6,
    "axes.linewidth": 0.8,
    "axes.edgecolor": INK,
    "axes.labelcolor": INK,
    "axes.axisbelow": True,
    "axes.grid": True,
    "axes.grid.which": "major",
    "grid.color": GRID_COLOUR,
    "grid.linewidth": 0.5,
    "grid.linestyle": (0, (1.0, 2.0)),
    "xtick.direction": "out",
    "ytick.direction": "out",
    "xtick.major.size": 3.0,
    "ytick.major.size": 3.0,
    "xtick.minor.size": 1.8,
    "ytick.minor.size": 1.8,
    "xtick.major.width": 0.7,
    "ytick.major.width": 0.7,
    "xtick.minor.width": 0.5,
    "ytick.minor.width": 0.5,
    "xtick.color": INK,
    "ytick.color": INK,
    "xtick.top": False,
    "ytick.right": False,
    "lines.linewidth": LINE_WIDTH,
    "lines.markersize": MARKER_SIZE,
    "lines.markeredgewidth": MARKER_EDGE_WIDTH,
    "legend.frameon": True,
    "legend.framealpha": 1.0,
    "legend.edgecolor": "none",
    "legend.fancybox": False,
    "legend.borderpad": 0.3,
    "legend.labelspacing": 0.3,
    "legend.handlelength": 2.2,
    "legend.handletextpad": 0.6,
    "legend.borderaxespad": 0.4,
    "legend.columnspacing": 1.2,
    "figure.dpi": 100,
    "savefig.dpi": 300,
    "savefig.pad_inches": 0.01,
}


def apply_style() -> None:
    """Install the shared rcParams (idempotent)."""
    plt.rcParams.update(RC_PARAMS)


# ---------------------------------------------------------------------------
# Identity encodings
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class SeriesStyle:
    label: str
    colour: str
    marker: str
    linestyle: object = "-"
    filled: bool = False
    zorder: float = 3.0
    linewidth: float = LINE_WIDTH

    def kwargs(self, **overrides) -> dict:
        kw = {
            "color": self.colour,
            "marker": self.marker,
            "linestyle": self.linestyle,
            "linewidth": self.linewidth,
            "markersize": MARKER_SIZE,
            "markeredgewidth": MARKER_EDGE_WIDTH,
            "markeredgecolor": self.colour,
            "markerfacecolor": self.colour if self.filled else "none",
            "zorder": self.zorder,
            "label": self.label,
        }
        kw.update(overrides)
        return kw


# Pressure-stabilisation method identities.  Colours are the linear Cook's
# palette (plot_paper.py, 26 Oct 2026); the coupled m = 0 rose was darkened
# slightly (#D7AAAA -> #D08C8C) for legibility on white.  Markers separate the
# coupled members from each other and from the separately implemented
# JST-type / Laplacian / Rhie-Chow constructions, so the series remain
# distinguishable in greyscale and under colour-vision deficiency.
# Index convention (manuscript, 29 Oct 2026): m = laplacianPower, i.e.
# m = 0 Laplacian (order 2), m = 1 bi-Laplacian (order 4), m = 2 sixth order.
# Run and file names evenlap_m0/m1/m2 already use this zero-based index; the
# OLD manuscript labels "m = 1/2/3" referred to the same operators.
METHOD_STYLES: dict[str, SeriesStyle] = {
    "jst": SeriesStyle("JST-type", "#4C78A8", "s"),
    "laplacian": SeriesStyle("Laplacian", "#5B8E55", "o"),
    "rhiechow": SeriesStyle("Rhie–Chow", "#7B6AA8", "^"),
    "coupled_m0": SeriesStyle("Coupled $m = 0$", "#D08C8C", "x"),
    "coupled_m1": SeriesStyle("Coupled $m = 1$", "#B85C4B", "+"),
    "coupled_m2": SeriesStyle("Coupled $m = 2$", "#7A2738", "D"),
}
# Aliases used by the case/run naming (laplacianPower) and by the Fourier CSVs.
METHOD_ALIASES = {
    "evenlap_m0": "coupled_m0",
    "evenlap_m1": "coupled_m1",
    "evenlap_m2": "coupled_m2",
    "gen0": "coupled_m0",
    "gen1": "coupled_m1",
    "gen2": "coupled_m2",
    "JST": "jst",
    "RhieChow": "rhiechow",
}


def method_style(key: str) -> SeriesStyle:
    return METHOD_STYLES[METHOD_ALIASES.get(key, key)]


# Literature / benchmark references.  A single reference curve is black and
# dashed; when several references share a panel they get distinct greys,
# dash patterns and markers (in this order).
REFERENCE_STYLES: list[SeriesStyle] = [
    SeriesStyle("Reference", "#111111", "v", linestyle=(0, (5, 3)), zorder=2.5,
                linewidth=REFERENCE_LINE_WIDTH),
    SeriesStyle("Reference 2", "#5A5A5A", "s", linestyle=(0, (3, 2, 1, 2)), zorder=2.4,
                linewidth=REFERENCE_LINE_WIDTH),
    SeriesStyle("Reference 3", "#9B9B9B", "^", linestyle=(0, (1.5, 2)), zorder=2.3,
                linewidth=REFERENCE_LINE_WIDTH),
    SeriesStyle("Reference 4", "#3B3B3B", "o", linestyle=(0, (7, 2, 1, 2, 1, 2)), zorder=2.2,
                linewidth=REFERENCE_LINE_WIDTH),
]

# Pressure-coefficient sweep (linear Cook's Figs 8/18): an ORDERED quantity,
# so a sequential colour map (viridis, truncated to keep the light end
# readable).  Colours are NOT method colours; the marker in each panel is the
# marker of the method shown in that panel.
PRESSURE_SCALE_ORDER = ("0.01", "0.1", "1", "10", "100", "1000")
# One open marker per s_p^star value, the same in every panel of Figs 8/18
# (the method is named by the sub-caption).  Avoids the benchmark's "v".
PRESSURE_SCALE_MARKERS = {"0.01": "o", "0.1": "s", "1": "D", "10": "^", "100": "p", "1000": "*"}


def pressure_scale_colours() -> dict[str, str]:
    cmap = matplotlib.colormaps["viridis"]
    n = len(PRESSURE_SCALE_ORDER)
    positions = [0.04 + 0.84 * i / (n - 1) for i in range(n)]
    return {
        scale: matplotlib.colors.to_hex(cmap(pos))
        for scale, pos in zip(PRESSURE_SCALE_ORDER, positions)
    }


# Mesh families of the manufactured solution (Figs 3-5): Okabe-Ito colours,
# one marker per family.  The ERROR MEASURE is encoded by the marker fill and
# line style: cell-wise RMS = filled marker, solid line; maximum = open marker,
# dashed line.
MESH_FAMILY_STYLES: dict[str, SeriesStyle] = {
    "hex": SeriesStyle("Hexahedral", "#0072B2", "o"),
    "distHex": SeriesStyle("Distorted hexahedral", "#E69F00", "^"),
    "poly": SeriesStyle("Polyhedral", "#009E73", "s"),
}
ERROR_MEASURE_STYLES = {
    "rms": {"filled": True, "linestyle": "-", "label": "Cell-wise RMS"},
    "max": {"filled": False, "linestyle": (0, (4, 2)), "label": "Maximum"},
}

# Mesh levels of the ventricular benchmarks (Figs 15/16): Okabe-Ito.
MESH_LEVEL_STYLES: dict[str, SeriesStyle] = {
    "mesh1": SeriesStyle("Mesh 1", "#0072B2", "o"),
    "mesh2": SeriesStyle("Mesh 2", "#D55E00", "s"),
    "mesh3": SeriesStyle("Mesh 3", "#009E73", "^"),
}

# Heart-tissue-beam reference statistics (Fig 13): three horizontal lines,
# distinct colours AND dash patterns.
LAND_STAT_STYLES: dict[str, SeriesStyle] = {
    "max": SeriesStyle("Land et al. (2015): maximum", "#009E73", "None",
                       linestyle=(0, (6, 2, 1.5, 2)), zorder=2.2),
    "median": SeriesStyle("Land et al. (2015): median", "#333333", "None",
                          linestyle="-", zorder=2.2),
    "min": SeriesStyle("Land et al. (2015): minimum", "#0072B2", "None",
                       linestyle=(0, (5, 3)), zorder=2.2),
}


def line_kwargs(key: str, **overrides) -> dict:
    """Keyword arguments for ``ax.plot`` for a method identity."""
    return method_style(key).kwargs(**overrides)


def reference_kwargs(index: int = 0, **overrides) -> dict:
    return REFERENCE_STYLES[index].kwargs(**overrides)


# ---------------------------------------------------------------------------
# Figure helpers
# ---------------------------------------------------------------------------
def new_figure(width_fraction: float = 0.49, aspect: float = 0.70, *,
               height_in: float | None = None, nrows: int = 1, ncols: int = 1,
               **subplot_kw):
    """Create a figure of the printed width.

    ``aspect`` is height / width of the whole figure; ``height_in`` overrides
    it.  Uses constrained layout so that labels never clip.
    """
    apply_style()
    width = fig_width(width_fraction)
    height = height_in if height_in is not None else width * aspect
    fig, axes = plt.subplots(nrows, ncols, figsize=(width, height),
                             layout="constrained", **subplot_kw)
    fig.get_layout_engine().set(w_pad=0.03, h_pad=0.03, wspace=0.04, hspace=0.04)
    return fig, axes


# ---------------------------------------------------------------------------
# Subfigures: fixed axes box, legend band above the axes
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class SubfigureLayout:
    """Fixed geometry [in] of one subfigure PDF.

    All subfigures of a block share one layout, so their axes boxes have the
    same size and position and line up on the page.  ``legend_rows`` reserves
    a band above the axes; use the largest row count of the block so that
    the bands (and therefore the axes) stay aligned.
    """

    width_fraction: float = 0.49
    axes_height_in: float = 1.70
    left_in: float = 0.50
    right_in: float = 0.08
    bottom_in: float = 0.40
    top_in: float = 0.04
    legend_rows: int = 0
    legend_gap_in: float = 0.05
    legend_side: str = "top"        # "top": band above the axes; "right": column beside them
    legend_width_in: float = 0.0    # width of the right-hand legend column

    @property
    def width_in(self) -> float:
        return fig_width(self.width_fraction)

    @property
    def axes_width_in(self) -> float:
        side = self.legend_width_in + self.legend_gap_in if self.legend_side == "right" else 0.0
        return self.width_in - self.left_in - self.right_in - side

    @property
    def legend_band_in(self) -> float:
        if self.legend_side not in ("top", "bottom") or self.legend_rows <= 0:
            return 0.0
        fs = FONT_SIZES["legend"]
        rows = self.legend_rows * fs * (1.0 + RC_PARAMS["legend.labelspacing"])
        return (rows + 2.0 * RC_PARAMS["legend.borderpad"] * fs) / 72.0 + self.legend_gap_in

    @property
    def height_in(self) -> float:
        return self.bottom_in + self.axes_height_in + self.legend_band_in + self.top_in

    @property
    def axes_bottom_in(self) -> float:
        """Lower edge of the axes box; a bottom legend band sits under the x label."""
        return self.bottom_in + (self.legend_band_in if self.legend_side == "bottom" else 0.0)


def new_subfigure(layout: SubfigureLayout, **subplot_kw):
    """Figure of the printed size with one axes at the fixed box of ``layout``."""
    apply_style()
    fig = plt.figure(figsize=(layout.width_in, layout.height_in))
    rect = (layout.left_in / layout.width_in, layout.axes_bottom_in / layout.height_in,
            layout.axes_width_in / layout.width_in, layout.axes_height_in / layout.height_in)
    ax = fig.add_axes(rect, **subplot_kw)
    ax._pfs_layout = layout  # read by outside_legend
    return fig, ax


def outside_legend(ax, handles=None, *, ncols: int = 1, row_major: bool = True, **kwargs):
    """Legend in the band above the axes, spread over the axes width.

    Entries are read row by row (matplotlib fills columns first); empty
    slots of the last row are padded with invisible entries.
    """
    layout: SubfigureLayout = getattr(ax, "_pfs_layout")
    if handles is None:
        handles = [h for h in ax.get_lines() if not h.get_label().startswith("_")]
    handles = list(handles)
    if row_major and ncols > 1:
        nrows = -(-len(handles) // ncols)
        blank = Line2D([], [], linestyle="none", marker="none", label=" ")
        padded = handles + [blank] * (nrows * ncols - len(handles))
        handles = [padded[r * ncols + c] for c in range(ncols) for r in range(nrows)]
    gap = layout.legend_gap_in / layout.axes_height_in
    kwargs.setdefault("loc", "lower left")
    kwargs.setdefault("bbox_to_anchor", (0.0, 1.0 + gap, 1.0, 0.0))
    kwargs.setdefault("mode", "expand")
    kwargs.setdefault("borderaxespad", 0.0)
    kwargs.setdefault("frameon", False)
    return ax.legend(handles=handles, ncols=ncols, **kwargs)


def right_legends(ax, groups, *, group_gap_pt: float = 5.0, **kwargs):
    """Legends stacked top-down in the column right of the axes.

    ``groups`` is a list of ``(handles, title)``; ``title`` may be None.
    """
    layout: SubfigureLayout = getattr(ax, "_pfs_layout")
    fig = ax.figure
    x = 1.0 + layout.legend_gap_in / layout.axes_width_in
    y = 1.0
    kwargs.setdefault("frameon", False)
    kwargs.setdefault("borderaxespad", 0.0)
    kwargs.setdefault("borderpad", 0.0)
    legends = []
    for handles, title in groups:
        leg = ax.legend(handles=list(handles), title=title, loc="upper left",
                        bbox_to_anchor=(x, y), alignment="left", **kwargs)
        ax.add_artist(leg)
        fig.canvas.draw()
        box = leg.get_window_extent(fig.canvas.get_renderer()).transformed(ax.transAxes.inverted())
        y = box.y0 - group_gap_pt / 72.0 / layout.axes_height_in
        legends.append(leg)
    return legends


def bottom_legends(ax, groups, *, group_gap_pt: float = 14.0, **kwargs):
    """Legends side by side in the band under the x label, centred on the axes.

    ``groups`` is a list of ``(handles, title, ncols)``; ``title`` may be None.
    Each group's title is left-aligned above its entries.
    """
    layout: SubfigureLayout = getattr(ax, "_pfs_layout")
    fig = ax.figure
    y = -(layout.bottom_in - 0.0) / layout.axes_height_in
    kwargs.setdefault("frameon", False)
    kwargs.setdefault("borderaxespad", 0.0)
    kwargs.setdefault("borderpad", 0.0)
    legends = []
    for handles, title, ncols in groups:
        handles = list(handles)
        if ncols > 1:  # read row by row
            nrows = -(-len(handles) // ncols)
            blank = Line2D([], [], linestyle="none", marker="none", label=" ")
            padded = handles + [blank] * (nrows * ncols - len(handles))
            handles = [padded[r * ncols + c] for c in range(ncols) for r in range(nrows)]
        leg = ax.legend(handles=handles, title=title, ncols=ncols, loc="upper left",
                        bbox_to_anchor=(0.0, y), alignment="left", **kwargs)
        ax.add_artist(leg)
        legends.append(leg)
    # centre the row of groups under the axes box
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    to_axes = ax.transAxes.inverted()
    widths = [leg.get_window_extent(renderer).transformed(to_axes).width for leg in legends]
    gap = group_gap_pt / 72.0 / layout.axes_width_in
    x = 0.5 * (1.0 - sum(widths) - gap * (len(widths) - 1))
    for leg, width in zip(legends, widths):
        leg.set_bbox_to_anchor((x, y), transform=ax.transAxes)
        x += width + gap
    # untitled groups: first entry on the same row as the first entry of a titled group
    fig.canvas.draw()
    titled = [leg for leg, (_, title, _) in zip(legends, groups) if title]
    if titled:
        row_top = max(leg.get_texts()[0].get_window_extent(renderer).y1 for leg in titled)
        for leg, (_, title, _) in zip(legends, groups):
            if title:
                continue
            dy = row_top - leg.get_texts()[0].get_window_extent(renderer).y1
            anchor = leg.get_bbox_to_anchor().transformed(to_axes)
            leg.set_bbox_to_anchor((anchor.x0, anchor.y0 + dy / ax.bbox.height), transform=ax.transAxes)
    return legends


def keyed_legend(ax, reference_handles, value_handles, key: str, *, ncols: int = 3,
                 corner: tuple[float, float] = (0.985, 0.975), **kwargs):
    """Legend inside the axes, upper right: references on top, values in a grid below.

    Layout (as agreed for Figs 8/18)::

               ▽ Reference
        key    ○ v1   □ v2   ◇ v3
               △ v4   ⬠ v5   ★ v6

    ``key`` (e.g. ``$s_p^\\star$``) sits left of the value grid, centred on
    its rows.  Returns the artists (two legends and the key text); white
    backgrounds hide the grid behind them.  Values are read row by row.
    """
    fig = ax.figure
    renderer = fig.canvas.get_renderer()
    to_axes = ax.transAxes.inverted()
    fs = FONT_SIZES["legend"]
    style = dict(frameon=True, framealpha=1.0, edgecolor="none", facecolor="white", fancybox=False,
                 borderpad=0.15, borderaxespad=0.0)
    style.update(kwargs)
    values = list(value_handles)
    nrows = -(-len(values) // ncols)
    blank = Line2D([], [], linestyle="none", marker="none", label=" ")
    padded = values + [blank] * (nrows * ncols - len(values))
    values = [padded[r * ncols + c] for c in range(ncols) for r in range(nrows)]

    # reference row first, to know its height
    ref = ax.legend(handles=list(reference_handles), loc="upper right", bbox_to_anchor=corner, **style)
    ax.add_artist(ref)
    fig.canvas.draw()
    ref_box = ref.get_window_extent(renderer).transformed(to_axes)
    row_gap = RC_PARAMS["legend.labelspacing"] * fs / 72.0 / (ax.bbox.height / fig.dpi)
    grid = ax.legend(handles=values, ncols=ncols, loc="upper right",
                     bbox_to_anchor=(corner[0], ref_box.y0 - row_gap), **style)
    ax.add_artist(grid)
    fig.canvas.draw()
    grid_box = grid.get_window_extent(renderer).transformed(to_axes)
    # reference entry aligned with the first column of the grid
    ref.set_bbox_to_anchor((grid_box.x0 + ref_box.width, ref_box.y1), transform=ax.transAxes)
    key_gap = 2.0 / 72.0 / (ax.bbox.width / fig.dpi)
    key_text = ax.text(grid_box.x0 - key_gap, 0.5 * (grid_box.y0 + grid_box.y1), key,
                       transform=ax.transAxes, ha="right", va="center", fontsize=FONT_SIZES["label"],
                       color=INK, zorder=ref.get_zorder(),
                       bbox=dict(facecolor="white", edgecolor="none", pad=0.6))
    fig.canvas.draw()
    return [ref, grid, key_text]


def assert_artists_clear(fig, ax, artists, context: str = "") -> None:
    """Fail if any plotted point or segment lies under one of ``artists``."""
    hits = []
    for artist in artists:
        hits += legend_overlaps(fig, ax, artist)
    if hits:
        detail = ", ".join(f"{label} ({n})" for label, n in hits)
        raise RuntimeError(f"legend covers plotted data{' in ' + context if context else ''}: {detail}")


def check_subfigure(fig, ax, leg=None, context: str = "", *, tol_pt: float = 0.5) -> None:
    """Fail if a legend touches the axes box or any text is clipped by the page."""
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    tol = tol_pt * fig.dpi / 72.0
    where = f" in {context}" if context else ""
    legends = [] if leg is None else (list(leg) if isinstance(leg, (list, tuple)) else [leg])
    ab = ax.get_window_extent(renderer)
    for item in legends:
        lb = item.get_window_extent(renderer)
        if lb.x0 < ab.x1 - tol and lb.x1 > ab.x0 + tol and lb.y0 < ab.y1 - tol and lb.y1 > ab.y0 + tol:
            raise RuntimeError(f"legend overlaps the axes box{where}")
    from matplotlib.transforms import Bbox
    boxes = [fig.get_tightbbox(renderer)]  # inches
    boxes += [item.get_window_extent(renderer).transformed(fig.dpi_scale_trans.inverted()) for item in legends]
    tight = Bbox.union(boxes)
    w, h = fig.get_size_inches()
    t = tol_pt / 72.0
    if tight.x0 < -t or tight.y0 < -t or tight.x1 > w + t or tight.y1 > h + t:
        raise RuntimeError(f"content clipped by the page{where}: tight box {tight.bounds} vs page {w:.3f} x {h:.3f} in")


def axes_box_pt(fig, ax) -> list[float]:
    """Axes box [x0, y0, width, height] in pt from the lower-left page corner."""
    w, h = fig.get_size_inches()
    x0, y0, bw, bh = ax.get_position().bounds
    return [round(v, 2) for v in (x0 * w * 72.0, y0 * h * 72.0, bw * w * 72.0, bh * h * 72.0)]


def style_axes(ax, *, grid: bool = True, minor: bool = False) -> None:
    """Apply the common axes look (box, outside ticks, subtle grid)."""
    for side in ("top", "right", "bottom", "left"):
        ax.spines[side].set_visible(True)
        ax.spines[side].set_linewidth(plt.rcParams["axes.linewidth"])
    ax.tick_params(which="both", direction="out", top=False, right=False)
    ax.grid(grid, which="major")
    ax.grid(False, which="minor")
    if minor:
        ax.minorticks_on()
    ax.set_axisbelow(True)


def legend(target, *args, **kwargs):
    """Legend with the common formatting (white opaque patch, no frame)."""
    kwargs.setdefault("frameon", True)
    kwargs.setdefault("framealpha", 1.0)
    kwargs.setdefault("edgecolor", "none")
    kwargs.setdefault("fancybox", False)
    leg = target.legend(*args, **kwargs)
    leg.get_frame().set_linewidth(0.0)
    if leg.get_title():
        leg.get_title().set_fontsize(FONT_SIZES["legend_title"])
    return leg


def legend_overlaps(fig, ax, leg, *, samples: int = 24) -> list[tuple[str, int]]:
    """Return the plotted series whose points or segments lie under the legend.

    Every Line2D of ``ax`` is sampled (its data points plus ``samples``
    interior points per segment, in display space) and tested against the
    legend's window extent.  Used as an automatic QA check so that no legend
    hides data.
    """
    import numpy as np

    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    bbox = leg.get_window_extent(renderer)
    hits: list[tuple[str, int]] = []
    for line in ax.get_lines():
        xy = line.get_xydata()
        if len(xy) == 0:
            continue
        pts = ax.transData.transform(xy)
        if len(pts) > 1:
            t = np.linspace(0.0, 1.0, samples + 2)[1:-1][:, None]
            seg = pts[:-1][:, None, :] * (1 - t) + pts[1:][:, None, :] * t
            pts = np.vstack([pts, seg.reshape(-1, 2)])
        inside = (
            (pts[:, 0] >= bbox.x0) & (pts[:, 0] <= bbox.x1)
            & (pts[:, 1] >= bbox.y0) & (pts[:, 1] <= bbox.y1)
        )
        if inside.any():
            hits.append((line.get_label(), int(inside.sum())))
    return hits


def assert_legend_clear(fig, ax, leg, context: str = "") -> None:
    hits = legend_overlaps(fig, ax, leg)
    if hits:
        detail = ", ".join(f"{label} ({n})" for label, n in hits)
        raise RuntimeError(f"legend covers plotted data{' in ' + context if context else ''}: {detail}")


def legend_handle(style: SeriesStyle, **overrides) -> Line2D:
    """A proxy artist for a style (used for shared legends)."""
    kw = style.kwargs(**overrides)
    label = kw.pop("label")
    return Line2D([], [], label=label, **kw)


def panel_label(ax, text: str, *, loc: str = "left") -> None:
    """Bold panel label such as (a), only for figures where LaTeX does not add one."""
    ax.set_title(text, loc=loc, fontsize=FONT_SIZES["panel_label"],
                 fontweight="bold", pad=3)


def annotate(ax, text: str, xy, **kwargs):
    kwargs.setdefault("fontsize", FONT_SIZES["annotation"])
    kwargs.setdefault("color", INK)
    return ax.text(*xy, text, transform=kwargs.pop("transform", ax.transAxes), **kwargs)


# ---------------------------------------------------------------------------
# Numerical-content record (for the before/after verification)
# ---------------------------------------------------------------------------
_RECORDS: dict[str, dict] = {}


def record_series(figure: str, name: str, x, y, **meta) -> None:
    """Record the exact arrays handed to matplotlib for one plotted series."""
    entry = _RECORDS.setdefault(figure, {"series": {}, "axes": {}})
    entry["series"][name] = {"x": [float(v) for v in x], "y": [float(v) for v in y], **meta}


def record_axes(figure: str, ax) -> None:
    entry = _RECORDS.setdefault(figure, {"series": {}, "axes": {}})
    entry["axes"] = {
        "xscale": ax.get_xscale(), "yscale": ax.get_yscale(),
        "xlim": [float(v) for v in ax.get_xlim()], "ylim": [float(v) for v in ax.get_ylim()],
        "xlabel": ax.get_xlabel(), "ylabel": ax.get_ylabel(),
    }


def write_records(path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(_RECORDS, indent=1, sort_keys=True))


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------
def fonts_embedded(pdf_path) -> tuple[bool, str]:
    """Check with poppler's pdffonts that every font is embedded."""
    exe = shutil.which("pdffonts")
    if exe is None:
        return True, "pdffonts not available; embedding not checked"
    out = subprocess.run([exe, str(pdf_path)], capture_output=True, text=True, check=False).stdout
    lines = out.splitlines()[2:]
    bad = []
    for line in lines:
        fields = line.split()
        if not fields:
            continue
        # columns: name type encoding emb sub uni object ID
        emb = fields[-5]
        if emb != "yes":
            bad.append(fields[0])
    return (not bad), out


def save(fig, path, *, title: str | None = None, metadata: dict | None = None,
         close: bool = True, check_fonts: bool = True) -> Path:
    """Write a vector PDF with embedded fonts and PDF metadata."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    meta = {"Creator": "JFNK mixed paper figures (paper_figure_style.py)"}
    if title:
        meta["Title"] = title
    if metadata:
        meta.update(metadata)
    fig.savefig(path, format="pdf", metadata=meta)
    if close:
        plt.close(fig)
    if check_fonts:
        ok, report = fonts_embedded(path)
        if not ok:
            raise RuntimeError(f"non-embedded font in {path}:\n{report}")
    return path


__all__ = [
    "LINEWIDTH_IN", "LINEWIDTH_PT", "BODY_FONT_PT", "CAPTION_FONT_PT", "FONT_SIZES",
    "FONT_FAMILY", "LINE_WIDTH", "MARKER_SIZE", "MARKER_EDGE_WIDTH", "INK", "GRID_COLOUR",
    "SeriesStyle", "METHOD_STYLES", "METHOD_ALIASES", "REFERENCE_STYLES",
    "PRESSURE_SCALE_ORDER", "pressure_scale_colours", "MESH_FAMILY_STYLES",
    "ERROR_MEASURE_STYLES", "MESH_LEVEL_STYLES", "LAND_STAT_STYLES",
    "apply_style", "fig_width", "new_figure", "style_axes", "stix_font_file",
    "SubfigureLayout", "new_subfigure", "outside_legend", "right_legends", "bottom_legends", "keyed_legend", "assert_artists_clear", "check_subfigure", "axes_box_pt",
    "PRESSURE_SCALE_MARKERS", "legend", "legend_handle",
    "legend_overlaps", "assert_legend_clear",
    "panel_label", "annotate", "line_kwargs", "reference_kwargs", "method_style",
    "record_series", "record_axes", "write_records", "save", "fonts_embedded",
]
