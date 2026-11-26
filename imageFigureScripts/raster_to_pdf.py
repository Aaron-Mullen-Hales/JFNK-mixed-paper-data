#!/usr/bin/env python3
"""Wrap a static raster figure (ParaView screenshot) in a single-page PDF, losslessly.

The image is placed pixel for pixel (no resampling) with Flate compression;
transparency is composited on white.  The page size is the image size at
``--dpi`` (default 300), so the manuscript keeps its own ``width=`` for the
subfigure.  Content is unchanged: only the container format differs.

Usage: raster_to_pdf.py <image.png> --output <file.pdf> [--dpi 300]
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import numpy as np
from PIL import Image


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
plt = pfs.plt


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("image", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--dpi", type=float, default=300.0)
    args = parser.parse_args()

    rgba = Image.open(args.image).convert("RGBA")
    rgb = Image.alpha_composite(Image.new("RGBA", rgba.size, "white"), rgba).convert("RGB")
    fig = plt.figure(figsize=(rgb.width / args.dpi, rgb.height / args.dpi), dpi=args.dpi)
    fig.figimage(np.asarray(rgb), xo=0, yo=0, origin="upper")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.output, format="pdf", dpi=args.dpi,
                metadata={"Creator": "JFNK mixed paper figures (raster_to_pdf.py)", "Title": args.image.name})
    plt.close(fig)
    print(f"Wrote {args.output} ({rgb.width} x {rgb.height} px at {args.dpi:g} ppi)")


if __name__ == "__main__":
    main()
