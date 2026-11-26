#!/usr/bin/env python3
"""Checks used by ../Allrun.  Nothing here writes into the package.

  check_package.py --deps    [--cases a,b]            Python modules, external programs, fonts
  check_package.py --inputs  [--cases a,b]            required inputs exist and match INPUT_CHECKSUMS.tsv
  check_package.py --outputs <OUT> [--cases a,b]      every expected figure file exists, is readable, has
                                                      embedded fonts, and every expected curve was drawn
Exit status 0 only if every requested check passes.
"""

from __future__ import annotations

import argparse
import csv
import importlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True
from package_info import CASES, ROOT, SERIES_FILES, manifest_rows, md5, parse_cases  # noqa: E402

MIN_PYTHON = (3, 9)
MODULES = {  # import name -> (pip name, minimum version or None)
    "matplotlib": ("matplotlib", (3, 8)),
    "numpy": ("numpy", None),
    "reportlab": ("reportlab", None),
    "pypdf": ("pypdf", None),
    "PIL": ("pillow", None),
}

errors: list[str] = []
warnings: list[str] = []


def version_tuple(text: str) -> tuple[int, ...]:
    parts = []
    for item in text.split("."):
        digits = "".join(ch for ch in item if ch.isdigit())
        if not digits:
            break
        parts.append(int(digits))
    return tuple(parts)


def check_deps(cases: list[str]) -> None:
    print(f"== dependencies (python {sys.version.split()[0]} at {sys.executable})")
    if sys.version_info < MIN_PYTHON:
        errors.append(f"python >= {MIN_PYTHON[0]}.{MIN_PYTHON[1]} is required, found {sys.version.split()[0]}")
    for name, (pip_name, minimum) in MODULES.items():
        try:
            module = importlib.import_module(name)
        except Exception as error:  # noqa: BLE001
            errors.append(f"python module '{name}' is missing ({error}); install with: pip install -r requirements.txt")
            continue
        version = getattr(module, "__version__", getattr(module, "Version", "?"))
        print(f"   ok   {pip_name} {version}")
        if minimum and version_tuple(str(version)) < minimum:
            errors.append(f"{pip_name} >= {'.'.join(map(str, minimum))} is required, found {version}")
    programs = {"pdffonts": "all cases (font-embedding check)"}
    if "beam" in cases:
        programs["pdfimages"] = "beam (Fig 12b raster extraction)"
    for program, used_by in programs.items():
        path = shutil.which(program)
        if path:
            print(f"   ok   {program} ({path})")
        else:
            errors.append(f"program '{program}' (poppler) not found on PATH; needed for: {used_by}")
    # fonts: STIXGeneral as bundled with matplotlib (same family as the cas-sc text/maths)
    try:
        import matplotlib
        for name in ("STIXGeneral.ttf", "STIXGeneralBol.ttf"):
            path = Path(matplotlib.get_data_path()) / "fonts" / "ttf" / name
            if path.is_file():
                print(f"   ok   font {path}")
            else:
                errors.append(f"matplotlib's bundled font {name} not found at {path}")
    except Exception as error:  # noqa: BLE001
        errors.append(f"cannot locate matplotlib's STIX fonts ({error})")


def check_inputs(cases: list[str]) -> None:
    print("== required inputs (existence, size, md5 against INPUT_CHECKSUMS.tsv)")
    record = ROOT / "INPUT_CHECKSUMS.tsv"
    if not record.is_file():
        errors.append("INPUT_CHECKSUMS.tsv is missing")
        return
    with record.open(newline="") as handle:
        rows = list(csv.DictReader((line for line in handle if not line.startswith("#")), delimiter="\t"))
    counts = {}
    for row in rows:
        if row["case"] not in cases:
            continue
        path = ROOT / row["path"]
        if not path.is_file():
            errors.append(f"missing input [{row['case']}, {row['role']}]: {row['path']}")
            continue
        if path.stat().st_size == 0:
            errors.append(f"empty input [{row['case']}]: {row['path']}")
            continue
        if md5(path) != row["md5"]:
            errors.append(f"input differs from the recorded checksum [{row['case']}]: {row['path']} "
                          "(if the change is intended, run tools/make_checksums.py)")
            continue
        counts[row["case"]] = counts.get(row["case"], 0) + 1
    for case in cases:
        print(f"   ok   {case}: {counts.get(case, 0)} input files verified")
    # scripts the commands call
    for script in ("plotStyle/paper_figure_style.py", "imageFigureScripts/compose_field_figure.py"):
        if not (ROOT / script).is_file():
            errors.append(f"missing script: {script}")


def fonts_embedded(pdf: Path) -> tuple[bool, str]:
    exe = shutil.which("pdffonts")
    if exe is None:
        return False, "pdffonts not available"
    out = subprocess.run([exe, str(pdf)], capture_output=True, text=True, check=False).stdout
    bad = [line for line in out.splitlines()[2:] if line.split()[-5:-4] != ["yes"]]
    return not bad, "\n".join(bad)


def check_outputs(out: Path, cases: list[str]) -> None:
    print(f"== outputs in {out}")
    rows = [row for row in manifest_rows() if row["case"] in cases]
    found = 0
    for row in rows:
        path = out / row["output"]
        tag = f"Fig {row['figure']}{'' if row['panel'] == '-' else row['panel']} {row['output']}"
        if not path.is_file() or path.stat().st_size == 0:
            errors.append(f"expected output missing or empty: {tag}")
            continue
        try:
            if path.suffix.lower() == ".pdf":
                from pypdf import PdfReader
                if len(PdfReader(str(path)).pages) != 1:
                    errors.append(f"unexpected page count: {tag}")
                    continue
                ok, report = fonts_embedded(path)
                if not ok:
                    errors.append(f"non-embedded font in {tag}: {report}")
                    continue
            else:
                from PIL import Image
                with Image.open(path) as image:
                    image.verify()
        except Exception as error:  # noqa: BLE001
            errors.append(f"unreadable output {tag}: {error}")
            continue
        found += 1
    print(f"   {found} of {len(rows)} expected figure files present and readable")

    # every expected curve drawn, with the expected number of points
    expected = json.loads((ROOT / "tools" / "expected_series.json").read_text())
    for case in cases:
        for name in SERIES_FILES[case]:
            path = out / "_work" / "series" / name
            if not path.is_file():
                errors.append(f"series record missing (was the plotting step run?): _work/series/{name}")
                continue
            got = json.loads(path.read_text())
            if name not in expected:
                errors.append(f"tools/expected_series.json has no entry for {name}")
                continue
            for figure, series in expected[name].items():
                drawn = got.get(figure, {}).get("series", {})
                for key, count in series.items():
                    if key not in drawn:
                        errors.append(f"curve not drawn: {figure} :: {key}")
                    elif len(drawn[key]["x"]) != count or len(drawn[key]["y"]) != count:
                        errors.append(f"curve has {len(drawn[key]['x'])} points, expected {count}: {figure} :: {key}")
                extra = set(drawn) - set(series)
                if extra:
                    errors.append(f"unexpected curve(s) in {figure}: {sorted(extra)} "
                                  "(if intended, update tools/expected_series.json)")
        print(f"   ok   {case}: curves and point counts as expected" if not errors else f"   --   {case}: see errors")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--deps", action="store_true")
    parser.add_argument("--inputs", action="store_true")
    parser.add_argument("--outputs", type=Path)
    parser.add_argument("--cases", default=None)
    args = parser.parse_args()
    cases = parse_cases(args.cases)
    if args.deps:
        check_deps(cases)
    if args.inputs:
        check_inputs(cases)
    if args.outputs is not None:
        check_outputs(args.outputs, cases)
    for message in warnings:
        print(f"   WARNING: {message}")
    if errors:
        print(f"\n{len(errors)} problem(s):", file=sys.stderr)
        for message in errors:
            print(f"   ERROR: {message}", file=sys.stderr)
        raise SystemExit(1)
    print("   all requested checks passed")


if __name__ == "__main__":
    main()
