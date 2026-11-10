#!/usr/bin/env python3
"""Verify that the regenerated figures plot exactly the numbers stored in this package.

Every plotting script writes the arrays it handed to the drawing library (``--dump-series``) to
``<OUT>/_work/series/*.json``.  This script recomputes the expected arrays INDEPENDENTLY from the input files
(own parsers; the selection rules and unit conversions are written out below, not imported from the
plotting scripts) and compares names, point counts and values (relative tolerance 1e-9).  It also checks
the derived quantities: observed orders and the Land problem 1 statistics.

Usage: tools/verify_numerics.py <OUT> [--cases a,b] [--report file.md]
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
import statistics
import sys
from pathlib import Path

sys.dont_write_bytecode = True
from package_info import BEAM, CON, FAMILIES, INF, LC, MMS, MMS_DS, NC, ROOT, parse_cases  # noqa: E402

TOL = 1e-9
lines: list[str] = []
failures = 0


def log(message: str) -> None:
    lines.append(message)
    print(message)


def fail(message: str) -> None:
    global failures
    failures += 1
    log(f"  FAIL {message}")


def close(a: float, b: float, rel: float = TOL, abs_: float = 1e-12) -> bool:
    return math.isclose(float(a), float(b), rel_tol=rel, abs_tol=abs_)


def table(path: Path) -> list[list[float]]:
    rows = []
    for line in path.read_text().splitlines():
        if line.strip() and not line.lstrip().startswith("#"):
            rows.append([float(v) for v in line.split()])
    return rows


def csv_rows(path: Path, delimiter: str = ",") -> list[dict[str, str]]:
    with path.open(newline="") as handle:
        return list(csv.DictReader((line for line in handle if not line.startswith("#")), delimiter=delimiter))


def series_of(out: Path, name: str) -> dict:
    path = out / "_work" / "series" / name
    if not path.is_file():
        raise SystemExit(f"ERROR: series record not found: {path} (run ./Allrun first)")
    return json.loads(path.read_text())


def compare(figure: str, name: str, exp_x, exp_y, got: dict | None) -> None:
    if got is None:
        fail(f"{figure} :: {name}: curve missing from the figure")
        return
    if len(got["x"]) != len(exp_x) or len(got["y"]) != len(exp_y):
        fail(f"{figure} :: {name}: {len(got['x'])} points, expected {len(exp_x)}")
        return
    for index, (ex, ey, x, y) in enumerate(zip(exp_x, exp_y, got["x"], got["y"])):
        if not (close(ex, x) and close(ey, y)):
            fail(f"{figure} :: {name}: point {index} expected ({ex:.12g}, {ey:.12g}), plotted ({x:.12g}, {y:.12g})")
            return
    log(f"  ok   {figure} :: {name}: {len(exp_x)} points identical")


def no_extra(figure: str, got: dict, names: set[str]) -> None:
    extra = set(got["series"]) - names
    missing = names - set(got["series"])
    if extra:
        fail(f"{figure}: unexpected curves {sorted(extra)}")
    if missing:
        fail(f"{figure}: curves not drawn {sorted(missing)}")


def axes(figure: str, got: dict, xscale: str, yscale: str, ylim: tuple[float, float] | None = None) -> None:
    ax = got["axes"]
    if (ax.get("xscale"), ax.get("yscale")) != (xscale, yscale):
        fail(f"{figure}: axis scales {ax.get('xscale')}/{ax.get('yscale')}, expected {xscale}/{yscale}")
    elif ylim is not None and not (close(ax["ylim"][0], ylim[0]) and close(ax["ylim"][1], ylim[1])):
        fail(f"{figure}: y-range {ax['ylim']}, expected {list(ylim)}")
    else:
        extra = f"; y-range {ax['ylim'][0]:g} to {ax['ylim'][1]:g}" if ylim is not None else ""
        log(f"  ok   {figure}: axes {xscale}/{yscale}; labels '{ax.get('xlabel')}' / '{ax.get('ylabel')}'{extra}")


# ---------------------------------------------------------------------------------------------------------
def verify_fourier(out: Path) -> None:
    log("\n## Fig 1: Fourier verification (normalisedSpectralCuts.pdf)")
    data = ROOT / "01_fourierVerification" / "data" / "stabilisationFourierCheck"
    got = series_of(out, "fourier.json")["normalisedSpectralCuts.pdf"]
    models = ("laplacian", "JST", "gen2", "RhieChow")   # drawn as coupled m = 0, m = 1 / JST-type, m = 2, Rhie-Chow
    tags = ("16x16x1", "32x32x1", "64x64x1")
    symbols = csv_rows(data / "symbols_64x64x1.csv")
    maps = csv_rows(data / "symbolMaps_64x64x1.csv")
    reference = {}
    for model in models:   # analytical response of the full checkerboard (theta_x = theta_y = pi)
        rows = [r for r in maps if r["model"] == model and close(float(r["thetaX_over_pi"]), 1, abs_=1e-8)
                and close(float(r["thetaY_over_pi"]), 1, abs_=1e-8)]
        if len(rows) != 1:
            fail(f"Fig 1: checkerboard entry for {model} not unique")
            return
        reference[model] = abs(float(rows[0]["lambda_exact"]))

    def on_cut(row, cut):
        tx, ty = float(row["thetaX_over_pi"]), float(row["thetaY_over_pi"])
        return (abs(ty) <= 1e-8, abs(tx - ty) <= 1e-8 + 1e-5 * abs(ty), abs(tx - 1) <= 1e-8 + 1e-5)[cut]

    names = set()
    for cut in range(3):   # (theta, 0), (theta, theta), (pi, theta)
        for model in models:
            curve = [r for r in symbols if r["model"] == model and int(r["cut"]) == cut]
            key = f"cut{cut}:{model}:analytical"
            names.add(key)
            compare("Fig 1", key, [float(r["theta_over_pi"]) for r in curve],
                    [abs(float(r["lambda_exact"])) / reference[model] for r in curve], got["series"].get(key))
            for tag in tags:
                rows = [r for r in csv_rows(data / f"results_{tag}.csv")
                        if r["normalise"] == "1" and r["model"] == model and on_cut(r, cut)]
                key = f"cut{cut}:{model}:measured:{tag}"
                names.add(key)
                compare("Fig 1", key, [float(r["thetaY_over_pi"] if cut == 2 else r["thetaX_over_pi"]) for r in rows],
                        [abs(float(r["lambda_num"])) / abs(float(r["lambda_ref"])) for r in rows], got["series"].get(key))
    no_extra("Fig 1", got, names)
    log("  transformations: analytical |lambda_exact| / |lambda_exact(checkerboard)|; measured |lambda_num| / |lambda_ref| "
        "(normalised campaign, r* = 2); x = theta/pi; dimensionless")


# ---------------------------------------------------------------------------------------------------------
def verify_mms(out: Path) -> None:
    log("\n## Figs 3-5: manufactured solution")
    slopes = ROOT / MMS / "plotScripts"
    sources = {
        "mms_disp_stress.json": ROOT / MMS_DS,   # Figs 3, 4
        "mms_pressure.json": ROOT / MMS / "data",  # Fig 5
    }
    dx = 0.04   # nominal spacing of mesh 1 [m]
    error_spec = {   # figure: (record, RMS column, maximum column [1-based], scale, slope file, first-order multiplier)
        "mms_dispErrors.pdf": ("mms_disp_stress.json", 4, 5, 1e6, "orderOfAccuracySlopesDisp.dat", 7.0),
        "mms_stressErrors_v2.pdf": ("mms_disp_stress.json", 6, 7, 1e-6, "orderOfAccuracySlopesStress.dat", 1.0),
        "mms_pressureErrors.pdf": ("mms_pressure.json", 10, 11, 1e-6, "orderOfAccuracySlopesPressure.dat", 1.0),
    }
    order_spec = {
        "mms_disp_orderOfAccuracy.pdf": ("mms_disp_stress.json", 2, 3, 4, 5),
        "mms_stress_orderOfAccuracy_v2.pdf": ("mms_disp_stress.json", 4, 5, 6, 7),
        "mms_pressure_orderOfAccuracy.pdf": ("mms_pressure.json", 6, 7, 10, 11),
    }
    for figure, (record, rms, mx, scale, slope_file, first) in error_spec.items():
        data, got = sources[record], series_of(out, record)[figure]
        names = {"guide:first-order", "guide:second-order"}
        for family in ("poly", "hex", "distHex"):
            rows = table(data / f"{family}.hypre.summary.txt")
            x = [1e3 * dx / 2 ** (r[0] - 1) for r in rows]
            for measure, column in (("rms", rms), ("max", mx)):
                key = f"{family}:{measure}"
                names.add(key)
                compare(figure, key, x, [scale * r[column - 1] for r in rows], got["series"].get(key))
        guide = table(slopes / slope_file)
        compare(figure, "guide:first-order", [r[0] for r in guide], [first * r[1] for r in guide], got["series"].get("guide:first-order"))
        compare(figure, "guide:second-order", [r[0] for r in guide], [r[2] for r in guide], got["series"].get("guide:second-order"))
        no_extra(figure, got, names)
        axes(figure, got, "log", "log")
    worst = 0.0
    for figure, (record, rms, mx, summary_rms, summary_max) in order_spec.items():
        data, got = sources[record], series_of(out, record)[figure]
        names = set()
        for family in ("poly", "hex", "distHex"):
            rows = table(data / f"{family}.hypre.orderOfAccuracy.txt")
            summary = table(data / f"{family}.hypre.summary.txt")
            x = [1e3 * dx / 2 ** r[0] for r in rows]
            for measure, column, source_column in (("rms", rms, summary_rms), ("max", mx, summary_max)):
                key = f"{family}:{measure}"
                names.add(key)
                compare(figure, key, x, [r[column - 1] for r in rows], got["series"].get(key))
                # derived quantity: order = log2(e_coarse / e_fine) of successive meshes of the summary table
                recomputed = [math.log2(summary[i][source_column - 1] / summary[i + 1][source_column - 1])
                              for i in range(len(summary) - 1)]
                difference = max(abs(a - r[column - 1]) for a, r in zip(recomputed, rows))
                worst = max(worst, difference)
                if len(recomputed) != len(rows) or difference > 2e-4:
                    fail(f"{figure} :: {key}: tabulated orders differ from log2 ratios of the summary table by {difference:.2e}")
        no_extra(figure, got, names)
        axes(figure, got, "log", "linear")
    log(f"  ok   observed orders = log2 of successive error ratios of the summary tables (largest difference {worst:.1e}, "
        "the rounding of the 6-significant-figure tables)")
    log("  transformations: x = 1e3 * 0.04 m / 2^(mesh-1) [mm] (orders: 1e3 * 0.04 / 2^pair); displacement m -> um (x 1e6); "
        "stress, pressure Pa -> MPa (x 1e-6); 'RMS' = sqrt(mean(e^2)) over cells with equal weights; 'maximum' = max over cells")
    # the two table sets of the campaign: rows shared by both must agree
    for family in FAMILIES:
        a, b = table(ROOT / MMS_DS / f"{family}.hypre.summary.txt"), table(ROOT / MMS / "data" / f"{family}.hypre.summary.txt")
        worst_rel = max(abs(p[c] - q[c]) / abs(q[c]) for p, q in zip(a, b) for c in range(3, 9))
        log(f"  info {family}: displacement/stress columns of the Figs 3-4 table vs the Fig 5 table differ by at most "
            f"{100 * worst_rel:.4f} %")


# ---------------------------------------------------------------------------------------------------------
def verify_linear_cooks(out: Path) -> None:
    log("\n## Figs 7, 8, 9b, 17, 18: linear Cook's membrane")
    got_all = series_of(out, "linearCooks.json")
    base = ROOT / LC / "data"
    benchmark = [(float(r[1]), float(r[0])) for r in csv.reader((ROOT / LC / "plotScripts" / "Bijelona.csv").open()) if len(r) >= 2]
    bench = "Bijelonja (2006)"
    methods = {"jst": "jst", "laplacian": "laplacian", "rhiechow": "rhiechow",
               "evenlap_m0": "coupled_m0", "evenlap_m1": "coupled_m1", "evenlap_m2": "coupled_m2"}

    def rows_of(study: str, tag: str) -> list[dict]:
        rows = csv_rows(base / "derived_summary" / f"{study}_sm{tag}.tsv", "\t")
        for row in rows:
            if row["normalise"] != "true" or row["referenceNyquistDirections"] != "2" or row["status"] != "OK":
                fail(f"{row['case']}: not a completed normalised r* = 2 result")
        return rows

    def points(rows, method, sp=None):
        return sorted((float(r["cells_per_side"]), float(r["dy_scaled"])) for r in rows
                      if r["method"] == method and (sp is None or r["sp"] == sp))

    checked = 0
    for tag in ("1p0", "0p1"):
        structured, parameter = rows_of("structured", tag), rows_of("parameter", tag)
        checked += len(structured) + len(parameter)
        figure = f"figure5_structured_displacement_sm{tag}.pdf"
        got = got_all[figure]
        compare(figure, "benchmark", [x for x, _ in benchmark], [y for _, y in benchmark], got["series"].get(bench))
        for method, key in methods.items():
            pts = points(structured, method)
            compare(figure, key, [x for x, _ in pts], [y for _, y in pts], got["series"].get(key))
        no_extra(figure, got, {bench, *methods.values()})
        axes(figure, got, "linear", "linear")

        figure = f"figure5_execution_time_vs_error_sm{tag}.pdf"
        got = got_all[figure]
        reference_row = max((r for r in structured if r["method"] == "evenlap_m2"), key=lambda r: int(r["mesh_index"]))
        finest, reference = int(reference_row["mesh_index"]), float(reference_row["dy_scaled"])
        for method, key in methods.items():
            pts = sorted((float(r["execution_time_s"]), abs(float(r["dy_scaled"]) - reference)) for r in structured
                         if r["method"] == method and 2 <= int(r["mesh_index"]) < finest)
            pts = [(t, e) for t, e in pts if t > 0 and e > 0]
            compare(figure, key, [t for t, _ in pts], [e for _, e in pts], got["series"].get(key))
        no_extra(figure, got, set(methods.values()))
        axes(figure, got, "log", "log")
        log(f"  info {figure}: error reference = coupled m = 2 on the finest mesh ({finest}) = {reference!r}; meshes 2 to {finest - 1} plotted")

        for name, method in (("m1", "evenlap_m0"), ("m2", "evenlap_m1"), ("m3", "evenlap_m2"), ("rhiechow", "rhiechow")):
            figure = f"figure6_pressure_scale_{name}_sm{tag}.pdf"
            got = got_all[figure]
            names = {bench}
            compare(figure, "benchmark", [x for x, _ in benchmark], [y for _, y in benchmark], got["series"].get(bench))
            for sp in ("0.01", "0.1", "1", "10", "100", "1000"):
                pts = points(parameter, method, sp)
                names.add(f"sp={sp}")
                compare(figure, f"sp={sp}", [x for x, _ in pts], [y for _, y in pts], got["series"].get(f"sp={sp}"))
            no_extra(figure, got, names)
            axes(figure, got, "linear", "linear")
    unstructured = rows_of("unstructured", "1p0")
    checked += len(unstructured)
    figure = "figure7b_unstructured_displacement.pdf"
    got = got_all[figure]
    compare(figure, "benchmark", [x for x, _ in benchmark], [y for _, y in benchmark], got["series"].get(bench))
    for method, key in methods.items():
        pts = points(unstructured, method)
        compare(figure, key, [x for x, _ in pts], [y for _, y in pts], got["series"].get(key))
    no_extra(figure, got, {bench, *methods.values()})
    axes(figure, got, "linear", "linear")
    log(f"  ok   {checked} summary-table rows read (dy_scaled = 1e-3 x D_y of the case output; execution_time_s = solver time)")
    log("  transformations: plotted displacement = 1e-3 x D_y of the case output, axis label '[mm]' (the accepted rescaling "
        "of the linear response); file tags m1/m2/m3 = coupled m = 0/1/2")


# ---------------------------------------------------------------------------------------------------------
def verify_nonlinear_cooks(out: Path) -> None:
    log("\n## Figs 10b, 11: nonlinear Cook's membrane")
    got_all = series_of(out, "nonlinearCooks.json")
    comp, inc = ROOT / NC / "compressible" / "data", ROOT / NC / "nearIncompressible" / "data"
    dx, dx_reference = 12.649, 18.973666
    figure = "LargeStrainCooksIncomp.pdf"
    got = got_all[figure]
    rows = table(comp / "hex_snes__evenlap_m2.summary.txt")
    compare(figure, "present:coupled_m2", [dx / 2 ** (r[0] - 1) for r in rows], [r[3] * 1000 for r in rows], got["series"].get("present:coupled_m2"))
    deal = table(comp / "deal.II.dat")
    compare(figure, "Pelteret-McBride Q1", [dx_reference / 2 ** i for i in range(len(deal))], [r[1] for r in deal], got["series"].get("Pelteret-McBride Q1"))
    compare(figure, "Pelteret-McBride Q2", [dx_reference / 2 ** i for i in range(len(deal))], [r[2] for r in deal], got["series"].get("Pelteret-McBride Q2"))
    abaqus = table(comp / "abaqus.dat")
    compare(figure, "Abaqus CPE4H", [r[1] for r in abaqus], [r[3] for r in abaqus], got["series"].get("Abaqus CPE4H"))
    no_extra(figure, got, {"present:coupled_m2", "Pelteret-McBride Q1", "Pelteret-McBride Q2", "Abaqus CPE4H"})
    axes(figure, got, "log", "linear", (0.0, 17.0))

    figure = "largeStrainIncompCooksMembrane-neoHookeanTipDispConvergenceStabCompatible.pdf"
    got = got_all[figure]
    rows = [r for r in table(inc / "hex_snes__evenlap_m2.summary.txt") if r[0] >= 2]
    compare(figure, "present:coupled_m2", [dx / 2 ** (r[0] - 1) for r in rows], [r[3] * 1000 for r in rows], got["series"].get("present:coupled_m2"))
    reference = got["series"].get("Abaqus CPE4RH")
    if reference and all(close(v, 13.5843) for v in reference["y"]):
        log("  ok   Fig 11 :: Abaqus CPE4RH reference line 13.5843 mm (constant in plot_nonlinear_cooks.py)")
    else:
        fail(f"Fig 11 :: Abaqus CPE4RH reference: {reference}")
    no_extra(figure, got, {"present:coupled_m2", "Abaqus CPE4RH"})
    axes(figure, got, "log", "linear", (0.0, 16.0))   # Fig 11: the 0-16 mm ordinate is an author decision
    log("  transformations: x = 12.649 mm / 2^(mesh-1) (present work), 18.973666 mm / 2^i (Pelteret & McBride); "
        "y = D [m] x 1000 [mm]; Abaqus CPE4H: columns 2 (spacing, mm) and 4 (displacement, mm) of abaqus.dat")


# ---------------------------------------------------------------------------------------------------------
def verify_beam(out: Path) -> None:
    log("\n## Fig 13: heart-tissue beam (Land et al. 2015, problem 1)")
    data = ROOT / BEAM / "data"
    figure = "land_problem1_m3_verticalDisplacement_vs_cellSize.pdf"
    got = series_of(out, "beam.json")[figure]
    rows = table(data / "beam.summary.txt")[1:]   # mesh 1 is not plotted
    compare("Fig 13", "simulation:coupled_m2", [r[1] for r in rows], [1.0 + 1e3 * r[3] for r in rows], got["series"].get("simulation:coupled_m2"))
    values = [float(r[1]) for r in csv.reader((data / "Landp1Data" / "land1Data.csv").open()) if len(r) >= 2 and r[1].strip()]
    stats = {"min": min(values), "median": statistics.median(values), "max": max(values)}
    gp = (data / "reference_data" / "land_problem1_reference_stats.gp").read_text()
    recorded = {k: float(v) for k, v in re.findall(r"(landN|landMin|landMedian|landMax)\s*=\s*([-+0-9.eE]+)", gp)}
    if len(values) != 23 or recorded.get("landN") != 23:
        fail(f"Fig 13: {len(values)} reference points, expected 23")
    for key, gp_key in (("min", "landMin"), ("median", "landMedian"), ("max", "landMax")):
        plotted = got["series"].get(f"reference:{key}")
        if plotted and all(close(v, stats[key]) for v in plotted["y"]) and close(recorded[gp_key], stats[key]):
            log(f"  ok   Fig 13 :: reference {key} = {stats[key]!r} mm (recomputed from the {len(values)} points; equals the .gp file and the plotted line)")
        else:
            fail(f"Fig 13 :: reference {key}: recomputed {stats[key]!r}, .gp {recorded.get(gp_key)!r}, plotted {plotted and plotted['y']}")
    no_extra("Fig 13", got, {"simulation:coupled_m2", "reference:min", "reference:median", "reference:max"})
    axes("Fig 13", got, "log", "linear")
    log("  transformations: x = cell size [mm] (column 2); y = 1 mm + 1e3 x D_z [m] = deformed z-coordinate of the "
        "monitored point [mm]; meshes 2-6 plotted (mesh 1, z = 1.05 mm, omitted as in the approved figure)")


# ---------------------------------------------------------------------------------------------------------
def midline(path: Path) -> tuple[list[float], list[float]]:
    rows = table(path)
    return [1e3 * r[0] for r in rows], [1e3 * r[2] for r in rows]


def verify_ventricle(out: Path, problem: int) -> None:
    figure = {2: "Fig 15: idealised LV inflation (Land problem 2)", 3: "Fig 16: idealised LV active contraction (Land problem 3)"}[problem]
    log(f"\n## {figure}")
    record = "inflation.json" if problem == 2 else "contraction.json"
    got = series_of(out, record)[f"land_problem{problem}_layer"]
    base = ROOT / (INF if problem == 2 else CON) / "data" / "midWallLines"
    for mesh in ("mesh1", "mesh2", "mesh3"):
        x, z = midline(base / mesh / "midLineDeformed.txt")
        compare(f"Fig {13 + problem}", mesh, x, z, got["series"].get(mesh))
    no_extra(f"Fig {13 + problem}", got, {"mesh1", "mesh2", "mesh3"})
    log("  transformations: x, z of midLineDeformed.txt [m] -> [mm] (x 1e3); every point of the mid-wall line is drawn")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("out", type=Path)
    parser.add_argument("--cases", default=None)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    cases = parse_cases(args.cases)
    log("# Plotted arrays versus the package inputs")
    log("Expected values recomputed independently from the input files; 'identical' = every x and y agrees to a relative tolerance of 1e-9.")
    steps = {
        "fourier": lambda: verify_fourier(args.out),
        "mms": lambda: verify_mms(args.out),
        "linearCooks": lambda: verify_linear_cooks(args.out),
        "nonlinearCooks": lambda: verify_nonlinear_cooks(args.out),
        "beam": lambda: verify_beam(args.out),
        "inflation": lambda: verify_ventricle(args.out, 2),
        "contraction": lambda: verify_ventricle(args.out, 3),
    }
    for case in cases:
        steps[case]()
    log(f"\n## Result: {'ALL CHECKS PASSED' if failures == 0 else f'{failures} FAILURE(S)'} ({', '.join(cases)})")
    if args.report is not None:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text("\n".join(lines) + "\n")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
