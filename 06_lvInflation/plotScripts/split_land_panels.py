#!/usr/bin/env python3
"""Cut the compact ventricle figure (Figs 15, 16) into three subfigure PDFs.

The composite page made by ``composite_land_overlay.py --layout compact`` has
panel (a) on the left and the two zooms on the right ((b) inflection on top,
(c) apex below).  Each panel becomes its own PDF so that LaTeX can place them
as independent subfigures with their own sub-captions.

Crop boxes: horizontally, the visible content of each panel's region (found
by rendering the page with poppler); vertically, the axes frame plus the SAME
margins above and below for all three panels, so that the frames line up
when (a) is set beside the (b)/(c) column.  The page content is not changed:
only the page boxes are set (no re-encoding, no scaling).

Usage: split_land_panels.py --problem 2 --input <composite.pdf> --output-prefix <path/name>
       -> <name>_a.pdf, <name>_b.pdf, <name>_c.pdf
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image
from pypdf import PdfReader, PdfWriter
from pypdf.generic import RectangleObject

sys.path.insert(0, str(Path(__file__).resolve().parent))
import render_land_midline_layers as R  # noqa: E402

DPI = 144.0          # 2 px per pt
MARGIN_PT = 1.0      # white margin kept around the content


def render_grey(pdf: Path) -> np.ndarray:
    exe = shutil.which("pdftoppm")
    if exe is None:
        raise SystemExit("ERROR: pdftoppm (poppler) not found")
    with tempfile.TemporaryDirectory() as tmp:
        stem = Path(tmp) / "page"
        subprocess.run([exe, "-r", str(DPI), "-png", "-singlefile", str(pdf), str(stem)], check=True)
        return np.asarray(Image.open(f"{stem}.png").convert("L"))


def content_bbox(grey, page_h, region, threshold=245):
    """Visible content inside region (x0, y0, x1, y1) [pt, PDF coordinates]."""
    k = DPI / 72.0
    x0, y0, x1, y1 = region
    r0, r1 = int((page_h - y1) * k), int((page_h - y0) * k)
    c0, c1 = int(x0 * k), int(x1 * k)
    sub = grey[max(r0, 0):r1, max(c0, 0):c1] < threshold
    rows, cols = np.where(sub.any(axis=1))[0], np.where(sub.any(axis=0))[0]
    if len(rows) == 0:
        raise SystemExit(f"ERROR: empty region {region}")
    return (x0 + cols[0] / k, y1 - (rows[-1] + 1) / k, x0 + (cols[-1] + 1) / k, y1 - rows[0] / k)


def split(problem: int, composite: Path, prefix: Path) -> None:
    S = R.LAYER_SCALE
    a, apex, inflection = R.compact_layout(problem)["panels"]
    frames = {}
    for name, panel in (("a", a), ("b", inflection), ("c", apex)):
        frames[name] = (S * panel.left, S * panel.bottom, S * (panel.left + panel.width), S * (panel.bottom + panel.height))
    page = PdfReader(str(composite)).pages[0]
    page_w, page_h = float(page.mediabox.width), float(page.mediabox.height)
    grey = render_grey(composite)

    # regions: left column for (a); right column split half-way between (b) and (c)
    split_x = 0.5 * (frames["a"][2] + frames["b"][0])
    split_y = 0.5 * (frames["c"][3] + frames["b"][1])
    regions = {"a": (0.0, 0.0, split_x, page_h), "b": (split_x, split_y, page_w, page_h),
               "c": (split_x, 0.0, page_w, split_y)}
    boxes = {name: content_bbox(grey, page_h, region) for name, region in regions.items()}
    above = max(boxes[n][3] - frames[n][3] for n in boxes) + MARGIN_PT
    below = max(frames[n][1] - boxes[n][1] for n in boxes) + MARGIN_PT
    # (b) and (c) share one horizontal crop, so their frames stay aligned in the right-hand column
    bx0, bx1 = min(boxes["b"][0], boxes["c"][0]), max(boxes["b"][2], boxes["c"][2])
    for n in ("b", "c"):
        boxes[n] = (bx0, boxes[n][1], bx1, boxes[n][3])

    for name in ("a", "b", "c"):
        x0, _, x1, _ = boxes[name]
        crop = RectangleObject([x0 - MARGIN_PT, frames[name][1] - below, x1 + MARGIN_PT, frames[name][3] + above])
        writer = PdfWriter()
        writer.append(PdfReader(str(composite)))
        out_page = writer.pages[0]
        for box in ("mediabox", "cropbox", "trimbox", "bleedbox", "artbox"):
            setattr(out_page, box, crop)
        out = prefix.parent / f"{prefix.name}_{name}.pdf"
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("wb") as handle:
            writer.write(handle)
        print(f"Wrote {out}: {float(crop.width):.1f} x {float(crop.height):.1f} pt")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--problem", type=int, choices=(2, 3), required=True)
    parser.add_argument("--input", type=Path, required=True, help="compact composite PDF")
    parser.add_argument("--output-prefix", type=Path, required=True)
    args = parser.parse_args()
    split(args.problem, args.input, args.output_prefix)


if __name__ == "__main__":
    main()
