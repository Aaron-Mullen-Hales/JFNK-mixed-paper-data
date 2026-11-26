#!/usr/bin/env python3
"""Shared definitions for the paperData tools: cases, required inputs and expected outputs.

The required inputs below are the files the plotting commands in ../Allrun read.  They are the single
list used by make_checksums.py (to record sizes and md5 sums in INPUT_CHECKSUMS.tsv) and by
check_package.py (to verify them before anything is plotted).
"""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# short case name -> folder
CASES = {
    "fourier": "01_fourierVerification",
    "mms": "02_manufacturedSolution",
    "linearCooks": "03_linearCooksMembrane",
    "nonlinearCooks": "04_nonlinearCooksMembrane",
    "beam": "05_heartTissueBeam",
    "inflation": "06_lvInflation",
    "contraction": "07_lvContraction",
}

MMS = "02_manufacturedSolution"
MMS_DS = f"{MMS}/data/recoveredOriginalRun_2026-09-02_Apple_M4_Pro_171316"
LC = "03_linearCooksMembrane"
NC = "04_nonlinearCooksMembrane"
BEAM = "05_heartTissueBeam"
INF = "06_lvInflation"
CON = "07_lvContraction"
FAMILIES = ("hex", "distHex", "poly")

# (case, role, path).  Roles: data = plotted numbers; reference = literature/benchmark values;
# asset = image or overlay used as drawn; static = figure file copied unchanged.
REQUIRED_INPUTS: list[tuple[str, str, str]] = []


def _add(case: str, role: str, *paths: str) -> None:
    REQUIRED_INPUTS.extend((case, role, p) for p in paths)


_F = "01_fourierVerification/data/stabilisationFourierCheck"
_add("fourier", "data", *(f"{_F}/results_{n}x{n}x1.csv" for n in (16, 32, 64)),
     f"{_F}/symbols_64x64x1.csv", f"{_F}/symbolMaps_64x64x1.csv")

_add("mms", "data",
     *(f"{MMS_DS}/{f}.hypre.{k}.txt" for f in FAMILIES for k in ("summary", "orderOfAccuracy")),
     *(f"{MMS}/data/{f}.hypre.{k}.txt" for f in FAMILIES for k in ("summary", "orderOfAccuracy")))
_add("mms", "reference", *(f"{MMS}/plotScripts/orderOfAccuracySlopes{q}.dat" for q in ("Disp", "Stress", "Pressure")))
_add("mms", "asset", f"{MMS}/data/fieldRenderLayer/fig2b_layer.png", f"{MMS}/data/fieldRenderLayer/fig2b_layer.json")
_add("mms", "asset", f"{MMS}/data/mesh/mms_polyhedral_mesh3_8000cells.vtk")

_add("linearCooks", "data",
     *(f"{LC}/data/derived_summary/{s}_sm{m}.tsv" for s in ("structured", "parameter") for m in ("1p0", "0p1")),
     f"{LC}/data/derived_summary/unstructured_sm1p0.tsv")
_add("linearCooks", "reference", f"{LC}/plotScripts/Bijelona.csv")
_add("linearCooks", "asset", f"{LC}/data/unstructuredMesh/trapezoid_mesh3.msh",
     f"{LC}/data/unstructuredMesh/trapezoidOpenFOAM_mesh3.geo")
_add("nonlinearCooks", "data", f"{NC}/compressible/data/hex_snes__evenlap_m2.summary.txt",
     f"{NC}/nearIncompressible/data/hex_snes__evenlap_m2.summary.txt")
_add("nonlinearCooks", "reference", f"{NC}/compressible/data/abaqus.dat", f"{NC}/compressible/data/deal.II.dat")
_add("nonlinearCooks", "asset", f"{NC}/compressible/data/fieldRenderLayer/fig10a_layer.png",
     f"{NC}/compressible/data/fieldRenderLayer/fig10a_layer.json")

_add("beam", "data", f"{BEAM}/data/beam.summary.txt")
_add("beam", "reference", f"{BEAM}/data/reference_data/land_problem1_reference_stats.gp",
     f"{BEAM}/data/Landp1Data/land1Data.csv")
_add("beam", "asset", f"{BEAM}/data/landDefomed_original_powerpoint_export.pdf")
_add("beam", "asset", f"{BEAM}/data/mesh/landBeam_level3_40x4x4_mm.vtk")

_add("inflation", "data", *(f"{INF}/data/midWallLines/mesh{i}/midLineDeformed.txt" for i in (1, 2, 3)))
_add("inflation", "asset", f"{INF}/data/land_problem2_m3_combined_overlay_original_keynote.pdf",
     f"{INF}/data/fieldRenderLayer/fig14b_layer.png", f"{INF}/data/fieldRenderLayer/fig14b_layer.json")
_add("inflation", "asset", f"{INF}/data/mesh/landVentricle_mesh1_15x3x36_mm.vtk")

_add("contraction", "data", *(f"{CON}/data/midWallLines/mesh{i}/midLineDeformed.txt" for i in (1, 2, 3)))
_add("contraction", "asset", f"{CON}/data/land_problem3_m3_combined_overlay_original_keynote.pdf")

# series records written by the plotting scripts (--dump-series), relative to <OUT>/_work/series
SERIES_FILES = {
    "fourier": ["fourier.json"],
    "mms": ["mms_disp_stress.json", "mms_pressure.json"],
    "linearCooks": ["linearCooks.json"],
    "nonlinearCooks": ["nonlinearCooks.json"],
    "beam": ["beam.json"],
    "inflation": ["inflation.json"],
    "contraction": ["contraction.json"],
}


def md5(path: Path) -> str:
    digest = hashlib.md5()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def manifest_rows() -> list[dict[str, str]]:
    with (ROOT / "tools" / "figure_manifest.tsv").open(newline="") as handle:
        return list(csv.DictReader((line for line in handle if not line.startswith("#")), delimiter="\t"))


def parse_cases(text: str | None) -> list[str]:
    """Accept short names, folder names or the two-digit prefixes (01 ... 07)."""
    if not text:
        return list(CASES)
    lookup = {}
    for name, folder in CASES.items():
        lookup[name.lower()] = name
        lookup[folder.lower()] = name
        lookup[folder[:2]] = name
    selected = []
    for item in text.replace(",", " ").split():
        key = item.strip().strip("/").lower()
        if key not in lookup:
            raise SystemExit(f"ERROR: unknown case '{item}'. Choose from: {', '.join(CASES)} (or 01 ... 07)")
        if lookup[key] not in selected:
            selected.append(lookup[key])
    return selected
