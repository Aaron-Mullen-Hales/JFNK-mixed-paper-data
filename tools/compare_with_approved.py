#!/usr/bin/env python3
"""Compare regenerated figures with the approved manuscript figures kept in <case>/figures/.

The approved files are the ones embedded in the compiled manuscript of 10 Nov 2026 (FIGURE_MANIFEST.md).
Byte identity is NOT required (PDF dates and library versions differ).  For every file the script reports

  identical drawing   the PDF page content stream (PNG: every pixel) is the same as the approved file
  pixel match         rendered at 150 dpi, both images agree within the tolerance below
  DIFFERENT           visible difference (listed with its size); look at the two files

Usage: tools/compare_with_approved.py <OUT> [--cases a,b] [--report file.md] [--dpi 150]
Exit status 1 if any file is DIFFERENT or missing.
"""

from __future__ import annotations

import argparse
import hashlib
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True
from package_info import ROOT, manifest_rows, parse_cases  # noqa: E402

MAX_CHANGED_FRACTION = 0.002    # share of pixels differing by more than 32 grey levels
lines: list[str] = []


def log(message: str) -> None:
    lines.append(message)
    print(message)


def content_md5(pdf: Path) -> str:
    from pypdf import PdfReader
    return hashlib.md5(PdfReader(str(pdf)).pages[0].get_contents().get_data()).hexdigest()


def raster(path: Path, dpi: int, work: Path):
    import numpy as np
    from PIL import Image
    if path.suffix.lower() == ".pdf":
        stem = work / hashlib.md5(str(path).encode()).hexdigest()
        subprocess.run([shutil.which("pdftoppm") or "pdftoppm", "-r", str(dpi), "-png", "-singlefile", str(path), str(stem)],
                       check=True, capture_output=True)
        image = Image.open(f"{stem}.png")
    else:
        image = Image.open(path)
    rgba = image.convert("RGBA")
    white = Image.new("RGBA", rgba.size, "white")
    return np.asarray(Image.alpha_composite(white, rgba).convert("L")).astype(int)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("out", type=Path)
    parser.add_argument("--cases", default=None)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--dpi", type=int, default=150)
    args = parser.parse_args()
    cases = parse_cases(args.cases)
    import numpy as np

    bad = 0
    log("# Regenerated figures versus the approved manuscript figures")
    log(f"| Fig | File | Kind | Result | Detail |\n|---|---|---|---|---|")
    with tempfile.TemporaryDirectory() as tmp:
        for row in manifest_rows():
            if row["case"] not in cases:
                continue
            new, approved = args.out / row["output"], ROOT / row["approved"]
            tag = f"| {row['figure']}{'' if row['panel'] == '-' else row['panel']} | `{row['output']}` | {row['kind']} |"
            if not new.is_file():
                bad += 1
                log(f"{tag} MISSING | not in {args.out} |")
                continue
            if new.read_bytes() == approved.read_bytes():
                log(f"{tag} identical file | byte-identical |")
                continue
            if new.suffix.lower() == ".pdf" and content_md5(new) == content_md5(approved):
                log(f"{tag} identical drawing | same page content stream (only PDF metadata differs) |")
                continue
            a, b = raster(new, args.dpi, Path(tmp)), raster(approved, args.dpi, Path(tmp))
            if a.shape != b.shape:
                bad += 1
                log(f"{tag} DIFFERENT | size {a.shape[1]}x{a.shape[0]} vs approved {b.shape[1]}x{b.shape[0]} px |")
                continue
            difference = np.abs(a - b)
            changed = float((difference > 32).mean())
            detail = f"max grey difference {int(difference.max())}, {100 * changed:.4f} % of pixels differ by > 32 levels"
            if int(difference.max()) == 0:
                log(f"{tag} identical drawing | every pixel equal |")
            elif changed <= MAX_CHANGED_FRACTION:
                log(f"{tag} pixel match | {detail} |")
            else:
                bad += 1
                log(f"{tag} DIFFERENT | {detail} |")
    log(f"\nResult: {'no visible difference from the approved figures' if bad == 0 else f'{bad} file(s) differ or are missing'}")
    if args.report is not None:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text("\n".join(lines) + "\n")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
