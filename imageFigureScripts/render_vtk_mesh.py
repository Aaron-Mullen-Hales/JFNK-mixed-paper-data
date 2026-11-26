#!/usr/bin/env python3
"""Figs 2(a), 12(a) and 14(a): vector drawing of a reference mesh from its legacy-binary VTK file.

The VTK files are the undeformed meshes of the paper (foamToVTK of the
mesh generators): MMS polyhedral cube mesh 3 (VTK polyhedra, m), Land beam
40 x 4 x 4 and Land ventricle mesh 1 (mm).  Only boundary faces are drawn: perspective
camera, back faces culled, painter's algorithm (far to near), Lambert
shading, cell edges on every face.  Output: single-page vector PDF.

Usage: render_vtk_mesh.py mesh.vtk --out out.pdf --view beam|ventricle|cube (--width-fraction 0.48 | --height-pt H)
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import numpy as np


def _load_paper_style():
    candidates = [Path(os.environ["JFNK_PAPER_STYLE_DIR"])] if "JFNK_PAPER_STYLE_DIR" in os.environ else []
    candidates += [parent / "plotStyle" for parent in Path(__file__).resolve().parents]
    for directory in candidates:
        if (directory / "paper_figure_style.py").is_file():
            sys.path.insert(0, str(directory))
            import paper_figure_style  # noqa: E402

            return paper_figure_style
    raise SystemExit("ERROR: paper_figure_style.py not found (set JFNK_PAPER_STYLE_DIR)")


pfs = _load_paper_style()
from matplotlib.collections import PolyCollection  # noqa: E402

# VTK cell type -> local faces (vertex indices, any orientation)
FACES = {
    12: [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)],  # hexahedron
    13: [(0, 1, 2), (3, 5, 4), (0, 3, 4, 1), (1, 4, 5, 2), (2, 5, 3, 0)],                      # wedge
}


def read_legacy_binary(path: Path):
    raw = path.read_bytes()

    def section(keyword: bytes):
        start = raw.index(b"\n" + keyword) + 1
        end = raw.index(b"\n", start)
        return raw[start:end].split(), end + 1

    head, off = section(b"POINTS")
    n = int(head[1])
    dtype = ">f4" if head[2] == b"float" else ">f8"
    pts = np.frombuffer(raw, dtype=dtype, count=3 * n, offset=off).reshape(n, 3).astype(float)
    head, off = section(b"CELLS")
    size = int(head[2])
    conn = np.frombuffer(raw, dtype=">i4", count=size, offset=off)
    head, off = section(b"CELL_TYPES")
    types = np.frombuffer(raw, dtype=">i4", count=int(head[1]), offset=off)
    cells, i = [], 0
    while i < len(conn):
        k = conn[i]
        cells.append(conn[i + 1:i + 1 + k].tolist())
        i += 1 + k
    return pts, cells, types.tolist()


def cell_faces(cell, t):
    """Faces of one cell as vertex-id tuples (in polygon order) and the cell's vertex ids."""
    if t == 42:                                   # VTK polyhedron: [nFaces, (nPts, ids...)...]
        faces, i = [], 1
        for _ in range(cell[0]):
            k = cell[i]
            faces.append(tuple(cell[i + 1:i + 1 + k]))
            i += 1 + k
        return faces, sorted({v for f in faces for v in f})
    if t not in FACES:
        raise ValueError(f"cell type {t} not supported")
    return [tuple(cell[j] for j in f) for f in FACES[t]], cell


def newell_normal(poly):
    """Unit normal of a planar polygon of any number of vertices (Newell's method)."""
    nxt = np.roll(poly, -1, axis=0)
    n = np.array([np.sum((poly[:, 1] - nxt[:, 1]) * (poly[:, 2] + nxt[:, 2])),
                  np.sum((poly[:, 2] - nxt[:, 2]) * (poly[:, 0] + nxt[:, 0])),
                  np.sum((poly[:, 0] - nxt[:, 0]) * (poly[:, 1] + nxt[:, 1]))])
    return n / np.linalg.norm(n)


def boundary_faces(pts, cells, types):
    count, owner = {}, {}
    for c, (cell, t) in enumerate(zip(cells, types)):
        faces, verts_of_cell = cell_faces(cell, t)
        for verts in faces:
            key = tuple(sorted(verts))
            count[key] = count.get(key, 0) + 1
            owner[key] = (verts, verts_of_cell)
    faces = []
    for key, n in count.items():
        if n != 1:
            continue
        verts, verts_of_cell = owner[key]
        poly = pts[list(verts)]
        centre = poly.mean(axis=0)
        normal = newell_normal(poly)
        cell_centre = pts[list(verts_of_cell)].mean(axis=0)
        if np.dot(normal, centre - cell_centre) < 0:   # outward
            normal = -normal
        faces.append((poly, centre, normal))
    return faces


def camera_basis(direction, up=(0.0, 0.0, 1.0)):
    d = np.asarray(direction, float)
    d /= np.linalg.norm(d)          # from target towards the camera
    right = np.cross(up, d)
    right /= np.linalg.norm(right)
    true_up = np.cross(d, right)
    return d, right, true_up


VIEWS = {
    # camera direction (target -> camera), distance in units of the model size, base grey
    "beam": dict(direction=(0.32, -1.0, 0.42), distance=3.0, colour=(0.80, 0.80, 0.80),
                 light=(-0.25, -0.40, 1.0)),
    "ventricle": dict(direction=(0.25, -1.0, 0.55), distance=4.0, colour=(0.80, 0.80, 0.80), light=None),
    # MMS cube (Fig 2a): three faces visible, as in the original ParaView view
    "cube": dict(direction=(0.95, -1.0, 0.85), distance=3.5, colour=(0.80, 0.80, 0.80),
                 light=(0.2, -0.6, 1.0)),
}


def render(vtk: Path, out: Path, view: str, width_fraction: float, edge_width: float,
           height_pt: float | None = None) -> None:
    pts, cells, types = read_legacy_binary(vtk)
    faces = boundary_faces(pts, cells, types)
    spec = VIEWS[view]
    d, right, up = camera_basis(spec["direction"])
    centre = 0.5 * (pts.min(axis=0) + pts.max(axis=0))
    size = np.linalg.norm(pts.max(axis=0) - pts.min(axis=0))
    eye = centre + d * spec["distance"] * size
    light = np.asarray(spec["light"], float) if spec["light"] is not None else d + 0.35 * up + 0.2 * right
    light /= np.linalg.norm(light)

    polys, shades, depths = [], [], []
    for poly, fc, n in faces:
        if np.dot(n, eye - fc) <= 0:          # back face
            continue
        rel = poly - eye
        z = -rel @ d                          # distance along the view axis
        xy = np.stack([rel @ right / z, rel @ up / z], axis=1)
        polys.append(xy)
        depths.append(float(np.mean(-((fc - eye) @ d))))
        if spec["light"] is not None:          # ambient + direct diffuse: distinct tones per face direction
            shades.append(0.50 + 0.45 * max(float(np.dot(n, light)), 0.0))
        else:                                 # soft headlight
            shades.append(0.55 + 0.45 * (0.45 + 0.55 * abs(float(np.dot(n, light)))))
    order = np.argsort(depths)[::-1]          # far first
    polys = [polys[i] for i in order]
    base = np.array(spec["colour"]) / 0.8
    colours = [tuple(np.clip(base * shades[i] * 0.88, 0, 1)) for i in order]

    allxy = np.vstack(polys)
    lo, hi = allxy.min(axis=0), allxy.max(axis=0)
    span = hi - lo
    if height_pt is not None:                 # fixed printed height (e.g. that of the companion panel)
        height = height_pt / 72.0
        width = height * span[0] / span[1]
    else:
        width = pfs.fig_width(width_fraction)
        height = width * span[1] / span[0]
    pfs.apply_style()
    fig = pfs.plt.figure(figsize=(width, height))
    ax = fig.add_axes((0, 0, 1, 1))
    pad = 0.01 * span
    ax.set_xlim(lo[0] - pad[0], hi[0] + pad[0])
    ax.set_ylim(lo[1] - pad[1], hi[1] + pad[1])
    ax.set_aspect("equal")
    ax.axis("off")
    ax.add_collection(PolyCollection(polys, facecolors=colours, edgecolors="#3A3A3A",
                                     linewidths=edge_width, joinstyle="round", antialiaseds=True))
    pfs.save(fig, out, title=f"{vtk.stem} ({view} view)")
    print(f"Wrote {out}: {len(polys)} visible faces of {len(faces)} boundary faces; {width:.2f} x {height:.2f} in")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("vtk", type=Path)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--view", choices=sorted(VIEWS), required=True)
    p.add_argument("--width-fraction", type=float, default=0.48)
    p.add_argument("--edge-width", type=float, default=0.3)
    p.add_argument("--height-pt", type=float, default=None, help="printed height [pt]; overrides --width-fraction")
    a = p.parse_args()
    render(a.vtk, a.out, a.view, a.width_fraction, a.edge_width, a.height_pt)


if __name__ == "__main__":
    main()
