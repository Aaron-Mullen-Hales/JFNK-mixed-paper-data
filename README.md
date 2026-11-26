# Figure data for the mixed pressure–displacement JFNK paper

Everything needed to redraw and edit the 35 figure files of the manuscript (18 figures): the plotted tables, reference
data, image assets, plotting scripts and the shared style. No simulation data, meshes or solver logs are included; the
complete run archive is kept separately.

```
./Allrun                     # all figures  -> generatedFigures/  (flat, the file names the manuscript uses)
./Allrun --case linearCooks  # one benchmark: fourier mms linearCooks nonlinearCooks beam inflation contraction
./Allrun --check             # dependencies and input files only
```

`./Allrun` only plots (about 10 s). It stops at the first failed step and then checks that every expected file and curve
is present and that the plotted numbers equal the data files.

## Requirements

* Python ≥ 3.9 with the packages in `requirements.txt` (the versions used for the CMAME submission figures; other
  versions give the same figures up to small rendering differences):
  `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt` — `./Allrun` uses `.venv` automatically;
  otherwise `python3` from the `PATH`, or `PYTHON=/path/to/python ./Allrun`.
* poppler (`pdffonts`, `pdfimages`; `pdftoppm` for the comparison tool): `brew install poppler` / `apt install poppler-utils`.
* Font: macOS Helvetica (`/System/Library/Fonts/Helvetica.ttc`). Without it the line figures fall back to another
  sans-serif font (numbers unchanged, text widths differ), and Figs 15–16 need
  `JFNK_PAPER_FONT_FILE=/path/to/font.ttc` (regular face at index 0, bold at index 1).

## Figures

| Fig | Output file(s) | Script | Data |
|---|---|---|---|
| 1 | `normalisedSpectralCuts.pdf` | `01_fourierVerification/plotScripts/plotPaperFigures.py` | `01_…/data/stabilisationFourierCheck/*.csv` |
| 2a | `MMS_Poly_Mesh.pdf` | `imageFigureScripts/render_vtk_mesh.py --view cube` (vector drawing of the mesh, height of 2b) | `02_…/data/mesh/mms_polyhedral_mesh3_8000cells.vtk` (polyhedral mesh 3, gmsh + polyDualMesh, foamToVTK, m) |
| 2b | `MMS_SigmaXX (2).pdf` | `imageFigureScripts/compose_field_figure.py` | `02_…/data/fieldRenderLayer/fig2b_layer.{png,json}` |
| 3, 4 | `mms_dispErrors.pdf`, `mms_disp_orderOfAccuracy.pdf`, `mms_stressErrors_v2.pdf`, `mms_stress_orderOfAccuracy_v2.pdf` | `02_…/plotScripts/mms_paper_figures.py` | `02_…/data/recoveredOriginalRun_2026-09-02_Apple_M4_Pro_171316/*.txt` |
| 5 | `mms_pressureErrors.pdf`, `mms_pressure_orderOfAccuracy.pdf` | same | `02_…/data/*.hypre.*.txt` |
| 6a, 6b | `cooksDiagram.pdf`, `cooksCoarseMesh2.pdf` | `03_linearCooksMembrane/plotScripts/draw_cooks_diagram.py` (6b: `--mesh 6`) | geometry only (vector drawings; replace the former `cooksDiagram.png`, `cooksCoarseMesh2.png`) |
| 9a | `unstructured_cooks3.pdf` | `03_linearCooksMembrane/plotScripts/draw_cooks_diagram.py --msh` | `03_…/data/unstructuredMesh/trapezoid_mesh3.msh` (gmsh 4.11.1 from `trapezoidOpenFOAM_mesh3.geo`, VIn = VOut = 4; replaces the former `unstructured_cooks3.png`) |
| 7, 8, 9b, 17, 18 | `figure5_*`, `figure6_pressure_scale_*`, `figure7b_unstructured_displacement.pdf` (13 files) | `03_…/plotScripts/plot_paper.py` | `03_…/data/derived_summary/*.tsv`, `plotScripts/Bijelona.csv` |
| 10a | `sigmaCompressibleLargeStrainCooks_cropped_kPa.pdf` | `imageFigureScripts/compose_field_figure.py` | `04_…/compressible/data/fieldRenderLayer/fig10a_layer.{png,json}` |
| 10b, 11 | `LargeStrainCooksIncomp.pdf`, `largeStrainIncompCooksMembrane-…StabCompatible.pdf` | `04_nonlinearCooksMembrane/plotScripts/plot_nonlinear_cooks.py` | `04_…/{compressible,nearIncompressible}/data/` |
| 12a | `landbeam.pdf` | `imageFigureScripts/render_vtk_mesh.py --view beam` (vector drawing of the mesh) | `05_…/data/mesh/landBeam_level3_40x4x4_mm.vtk` (foamToVTK of the blockMesh generator, mm) |
| 12b | `landDefomed.pdf` | `imageFigureScripts/compose_field_figure.py` | `05_…/data/landDefomed_original_powerpoint_export.pdf` |
| 13 | `land_problem1_m3_verticalDisplacement_vs_cellSize.pdf` | `05_…/plotScripts/plot_land_problem1.py` | `05_…/data/beam.summary.txt`, `data/reference_data/`, `data/Landp1Data/land1Data.csv` |
| 14a | `Land_Geom.pdf` | `imageFigureScripts/render_vtk_mesh.py --view ventricle` (vector drawing of the mesh) | `06_…/data/mesh/landVentricle_mesh1_15x3x36_mm.vtk` (foamToVTK of the blockMesh + extrudeMesh generator, mm) |
| 14b | `LandDeformed.pdf` | `imageFigureScripts/compose_field_figure.py` | `06_…/data/fieldRenderLayer/fig14b_layer.{png,json}` |
| 15a–c | `land_problem2_m3_combined_overlay_{a,b,c}.pdf` (one subfigure per panel, `split_land_panels.py`) | `06_…/plotScripts/render_land_midline_layers.py`, `composite_land_overlay.py` | `06_…/data/midWallLines/mesh{1,2,3}/midLineDeformed.txt`, Keynote overlay PDF |
| 16a–c | `land_problem3_m3_combined_overlay_{a,b,c}.pdf` (one subfigure per panel, `split_land_panels.py`) | same two scripts | `07_lvContraction/data/midWallLines/mesh{1,2,3}/midLineDeformed.txt`, Keynote overlay PDF |

The exact commands are in `Allrun`. Each case folder also has `figures/` with the approved files (those in the manuscript);
`python3 tools/compare_with_approved.py generatedFigures` lists which regenerated files differ from them.
The shared look (fonts, sizes, colours, markers) is `plotStyle/paper_figure_style.py`.

## Notes

* m = 0 Laplacian, m = 1 bi-Laplacian, m = 2 sixth-order operator. File names with `m1`, `m2`, `m3` carry an older
  one-based tag (file `m1` shows m = 0, and so on).
* Linear Cook's membrane: the plotted displacement is the case output × 1e-3, labelled "[mm]" (intentional).
* Fig 11 keeps the 0–16 mm ordinate.
* Field panels (Figs 2b, 10a, 14b) are composed from stored ParaView rasters; only the colour bar and labels are redrawn.
  Fig 12b keeps the raster of the original export. Re-rendering a field needs the simulation archive and is not possible
  from this package. Six images are static (2a, 6a, 6b, 9a, 12a, 14a).
* After a deliberate change: a replaced data file → `python3 tools/make_checksums.py`; an added or removed curve →
  update `tools/expected_series.json`. Otherwise `./Allrun` reports the change as an error.
