#!/usr/bin/env python3
"""Fig 6: Cook's membrane geometry (a) and structured mesh (b), vector drawings.

Replace the rasters ``cooksDiagram.png`` and ``cooksCoarseMesh2.png``.
Everything is drawn from the benchmark geometry (vertices (0, 0), (48, 44),
(48, 60), (0, 44), lengths in mm).

* (a) clamped left edge, vertical traction tau on the right edge, dimensions
  44 / 16 / 44 / 48 mm and the x-y axes;
* (b) with ``--mesh n``: the uniform n x n structured mesh (blockMesh, no
  grading: vertical lines every 48/n mm, each horizontal line joins equally
  spaced points of the left and right edges).

Both use the same drawing window, so the membranes have the same size and
position in the two subfigures.  Shared style: STIX text, printed sizes.

Usage: draw_cooks_diagram.py --output <pdf> [--mesh n]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "plotStyle"))
import paper_figure_style as pfs  # noqa: E402

WIDTH_FRACTION = 0.45                     # subfigure width / \linewidth
XLIM, YLIM = (-22.0, 62.0), (-14.0, 72.0)  # drawing window [mm]
OUTLINE_WIDTH = 1.0                       # membrane edges [pt]
THIN = 0.5                                # dimension and extension lines [pt]
TEXT = pfs.FONT_SIZES["label"]            # 9 pt printed
VERTICES = [(0.0, 0.0), (48.0, 44.0), (48.0, 60.0), (0.0, 44.0)]
# No unit on the dimensions: the linear case uses metres (as Bijelonja et al. 2006) and the
# nonlinear case millimetres; the manuscript text states the unit of each case.
UNIT = ""                                 # printed after every dimension value ("" = none)
FILL = "#E6E6E6"                          # membrane interior (light grey)
EXTENSION_DASH = (0, (3, 2))              # dash pattern of every extension line


def line(ax, xs, ys, **kw):
    kw.setdefault("color", pfs.INK)
    kw.setdefault("linewidth", THIN)
    kw.setdefault("solid_capstyle", "butt")
    ax.plot(xs, ys, **kw)


def dimension(ax, p0, p1, text):
    """Dimension line with filled arrowheads at both ends and the value at its middle."""
    ax.annotate("", xy=p1, xytext=p0,
                arrowprops=dict(arrowstyle="<|-|>", color=pfs.INK, linewidth=THIN,
                                mutation_scale=7, shrinkA=0, shrinkB=0))
    label = f"{text} {UNIT}" if UNIT else text
    ax.text(0.5 * (p0[0] + p1[0]), 0.5 * (p0[1] + p1[1]), label, ha="center", va="center",
            fontsize=TEXT, color=pfs.INK, bbox=dict(facecolor="white", edgecolor="none", pad=1.2))


def arrow(ax, p0, p1, width):
    ax.annotate("", xy=p1, xytext=p0,
                arrowprops=dict(arrowstyle="-|>", color=pfs.INK, linewidth=width,
                                mutation_scale=8, shrinkA=0, shrinkB=0))


def canvas(xlim=XLIM, ylim=YLIM):
    """Figure at the printed size; every drawing uses the scale [in/mm] of Fig 6."""
    scale = pfs.fig_width(WIDTH_FRACTION) / (XLIM[1] - XLIM[0])
    width = scale * (xlim[1] - xlim[0])
    height = scale * (ylim[1] - ylim[0])
    pfs.apply_style()
    fig = pfs.plt.figure(figsize=(width, height))
    ax = fig.add_axes((0, 0, 1, 1))
    ax.set_xlim(xlim)
    ax.set_ylim(ylim)
    ax.set_aspect("equal")
    ax.axis("off")
    return fig, ax


def membrane(ax):
    """Light grey fill under the outline."""
    xs, ys = zip(*(VERTICES + VERTICES[:1]))
    ax.fill(xs, ys, color=FILL, linewidth=0, zorder=1)
    line(ax, xs, ys, linewidth=OUTLINE_WIDTH, solid_joinstyle="miter", zorder=3)


def draw_mesh(output: Path, n: int) -> None:
    """Uniform n x n structured mesh of the membrane."""
    fig, ax = canvas()
    membrane(ax)
    (x0, y0), (x1, y1), (x2, y2), (x3, y3) = VERTICES   # bottom-left, bottom-right, top-right, top-left
    for k in range(1, n):
        t = k / n
        # line of constant x: from the bottom edge to the top edge
        line(ax, [x0 + t * (x1 - x0), x3 + t * (x2 - x3)], [y0 + t * (y1 - y0), y3 + t * (y2 - y3)], zorder=2)
        # line across the membrane: from the left edge to the right edge
        line(ax, [x0 + t * (x3 - x0), x1 + t * (x2 - x1)], [y0 + t * (y3 - y0), y1 + t * (y2 - y1)], zorder=2)
    pfs.check_subfigure(fig, ax, None, output.name)
    pfs.save(fig, output, title=f"Linear Cook's membrane: structured mesh {n} x {n}")


def read_msh_triangles(path: Path):
    """Triangles of the z = 0 face of a gmsh msh2 file, as lists of (x, y) [mm]."""
    lines = path.read_text().split("\n")
    i = lines.index("$Nodes")
    nodes = {}
    for row in lines[i + 2:i + 2 + int(lines[i + 1])]:
        tag, x, y, z = row.split()[:4]
        nodes[int(tag)] = (float(x), float(y), float(z))
    j = lines.index("$Elements")
    triangles = []
    for row in lines[j + 2:j + 2 + int(lines[j + 1])]:
        fields = row.split()
        if fields[1] != "2":                       # element type 2 = 3-node triangle
            continue
        verts = [nodes[int(v)] for v in fields[3 + int(fields[2]):]]
        if all(abs(v[2]) < 1e-12 for v in verts):
            triangles.append([(v[0], v[1]) for v in verts])
    if not triangles:
        raise ValueError(f"no z = 0 triangles in {path}")
    return triangles


def draw_triangles(output: Path, msh: Path) -> None:
    """Unstructured triangular mesh (gmsh), at the scale of Fig 6, window fitted to the membrane."""
    fig, ax = canvas(xlim=(-1.0, 49.0), ylim=(-1.0, 61.0))
    membrane(ax)
    triangles = read_msh_triangles(msh)
    edges = set()
    for tri in triangles:
        for a, b in ((tri[0], tri[1]), (tri[1], tri[2]), (tri[2], tri[0])):
            edges.add(tuple(sorted((a, b))))
    for a, b in edges:
        line(ax, [a[0], b[0]], [a[1], b[1]], zorder=2)
    pfs.check_subfigure(fig, ax, None, output.name)
    pfs.save(fig, output, title=f"Linear Cook's membrane: unstructured mesh, {len(triangles)} triangles")


def draw(output: Path) -> None:
    fig, ax = canvas()
    membrane(ax)

    # clamped edge: wall line and hatching
    line(ax, [0.0, 0.0], [-1.0, 48.0], linewidth=OUTLINE_WIDTH)
    for y in [2.5 * k for k in range(0, 20)]:
        line(ax, [0.0, -2.6], [y, y - 2.6])

    # extension lines (from the membrane to the dimension lines) are all dashed
    ext = dict(linestyle=EXTENSION_DASH)

    # left height 44
    line(ax, [-17.0, -1.0], [44.0, 44.0], **ext)
    line(ax, [-17.0, -4.0], [0.0, 0.0], **ext)
    dimension(ax, (-14.0, 0.0), (-14.0, 44.0), "44")

    # right heights 16 and 44
    line(ax, [49.0, 58.5], [60.0, 60.0], **ext)
    line(ax, [49.0, 58.5], [44.0, 44.0], **ext)
    line(ax, [41.0, 58.5], [0.0, 0.0], **ext)
    line(ax, [48.0, 48.0], [0.0, 43.0], **ext)
    dimension(ax, (56.0, 44.0), (56.0, 60.0), "16")
    dimension(ax, (56.0, 0.0), (56.0, 44.0), "44")

    # bottom width 48
    line(ax, [0.0, 0.0], [-2.0, -11.0], **ext)
    line(ax, [48.0, 48.0], [-2.0, -11.0], **ext)
    dimension(ax, (0.0, -8.5), (48.0, -8.5), "48")

    # traction on the right edge
    arrow(ax, (48.0, 62.0), (48.0, 70.5), OUTLINE_WIDTH)
    ax.text(50.0, 68.5, r"$\tau$", ha="left", va="center", fontsize=TEXT, color=pfs.INK)

    # axes
    origin = (-20.0, -12.5)
    arrow(ax, origin, (origin[0] + 7.0, origin[1]), THIN)
    arrow(ax, origin, (origin[0], origin[1] + 7.0), THIN)
    ax.text(origin[0] + 7.8, origin[1], r"$x$", ha="left", va="center", fontsize=TEXT, color=pfs.INK)
    ax.text(origin[0], origin[1] + 7.8, r"$y$", ha="center", va="bottom", fontsize=TEXT, color=pfs.INK)

    pfs.check_subfigure(fig, ax, None, output.name)
    pfs.save(fig, output, title="Linear Cook's membrane: geometry and boundary conditions")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--mesh", type=int, default=None, help="draw the uniform n x n mesh instead of the geometry")
    parser.add_argument("--msh", type=Path, default=None, help="draw the triangles of this gmsh msh2 file (z = 0 face)")
    args = parser.parse_args()
    if args.msh is not None:
        draw_triangles(args.output, args.msh)
    elif args.mesh is not None:
        draw_mesh(args.output, args.mesh)
    else:
        draw(args.output)
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
