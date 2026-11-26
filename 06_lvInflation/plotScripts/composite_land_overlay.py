#!/usr/bin/env python3
"""Put a re-rendered data layer back into the Keynote overlay figures.

``land_problem2_m3_combined_overlay.pdf`` and
``land_problem3_m3_combined_overlay.pdf`` (manuscript Figs 15, 16) are Keynote
exports in which P. Cardiff placed faint JPEG crops of the Land et al. (2015)
result figures (Form XObjects /Fm1-/Fm3 drawn with alpha ~0.2) and pasted the
vector data layer on top, once per panel (Fig 15: three copies with slightly
different transforms, each clipped to its panel region) or once (Fig 16).

This tool rebuilds the page content:
  * keeps every original content group that draws a faint layer (``Do``) or
    the white background, unchanged;
  * removes the pasted vector data groups (identified by their ``cm``
    matrices, which are listed below and were read from the originals);
  * appends the new data layer as a Form XObject, drawn under exactly the
    same clip rectangles and transformation matrices as the removed copies.
Because the new layer keeps the original panel geometry, the alignment with
the faint reference layers is preserved.  The Keynote-added tick labels
"-8.75"/"-8.25" of Fig 16 panel (c) are removed because the new layer draws
those ticks itself.

Usage:
  composite_land_overlay.py --problem 2 --overlay <original overlay pdf>
                            --layer <new layer pdf> --output <pdf>
"""

from __future__ import annotations

import argparse
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from pypdf.generic import (ArrayObject, ContentStream, DictionaryObject, FloatObject,
                           NameObject, StreamObject)

# (clip rectangle x y w h, matrix a b c d e f) of each pasted data copy
PLACEMENTS = {
    2: [
        ((194.915, 256.6357, 378.9659, 268.6548), (0.877236, 0, 0, 0.877236, 194.915, 70.53152)),
        ((199.5775, 79.2078, 182.4218, 178.5669), (0.876243, 0, 0, 0.876243, 194.8726, 70.3641)),
        ((389.438, 77.6899, 181.6047, 179.7183), (0.871905, 0, 0, 0.871905, 196.9999, 70.97111)),
    ],
    3: [
        ((263.2329, 63.0092, 384.4167, 461.3), (0.889853, 0, 0, 0.889853, 263.2329, 63.00916)),
    ],
}
# panel index (0 full line, 1 apex, 2 inflection) of each faint layer, in drawing order
# (checked by drawing each layer alone: in Fig 16 /Fm2 is the inflection and /Fm3 the apex)
FAINT_PANEL = {2: (0, 1, 2), 3: (0, 2, 1)}
# matrices of the data copies to remove (matched on the scale factor)
DATA_SCALES = {2: (0.877236, 0.876243, 0.871905), 3: (0.889853,)}
# Fig 16 only: the group that draws /Fm3 also contains hand-typed tick labels
STRIP_TEXT_IN_GROUPS_WITH_DO = {3: ("/Fm3",)}


def _op_name(op) -> str:
    return op.decode() if isinstance(op, bytes) else str(op)


def top_level_groups(ops):
    """Yield (start, end) index pairs of the top-level q ... Q groups."""
    depth = 0
    start = None
    for i, (_, op) in enumerate(ops):
        name = _op_name(op)
        if name == "q":
            depth += 1
            if depth == 1:
                start = i
        elif name == "Q":
            depth -= 1
            if depth == 0:
                yield start, i
                start = None
    if depth != 0:
        raise ValueError("unbalanced q/Q in overlay content stream")


def group_info(ops, start, end):
    cm = None
    dos = []
    for operands, op in ops[start:end + 1]:
        name = _op_name(op)
        if name == "cm" and cm is None:
            cm = [float(v) for v in operands]
        if name == "Do":
            dos.append(str(operands[0]))
    return cm, dos


def strip_text(ops_slice):
    """Remove BT ... ET blocks from a list of operations."""
    out = []
    in_text = False
    for operands, op in ops_slice:
        name = _op_name(op)
        if name == "BT":
            in_text = True
            continue
        if name == "ET":
            in_text = False
            continue
        if not in_text:
            out.append((operands, op))
    return out


def composite(problem: int, overlay: Path, layer: Path, output: Path) -> None:
    reader = PdfReader(str(overlay))
    writer = PdfWriter()
    writer.append(reader)
    page = writer.pages[0]

    # --- new data layer as a Form XObject -------------------------------
    layer_reader = PdfReader(str(layer))
    layer_page = layer_reader.pages[0]
    writer.add_page(layer_page)                     # imports fonts/resources
    imported = writer.pages[-1]
    form = StreamObject()
    form[NameObject("/Type")] = NameObject("/XObject")
    form[NameObject("/Subtype")] = NameObject("/Form")
    form[NameObject("/FormType")] = FloatObject(1)
    form[NameObject("/BBox")] = ArrayObject([FloatObject(float(v)) for v in layer_page.mediabox])
    form[NameObject("/Resources")] = imported["/Resources"]
    form.set_data(imported.get_contents().get_data())
    form_ref = writer._add_object(form)
    writer.remove_page(len(writer.pages) - 1)

    resources = page["/Resources"]
    xobjects = resources.get("/XObject")
    if xobjects is None:
        xobjects = DictionaryObject()
        resources[NameObject("/XObject")] = xobjects
    xobjects = xobjects.get_object()
    layer_name = "/FmDataLayer2026"
    xobjects[NameObject(layer_name)] = form_ref

    # --- rebuild the content stream ------------------------------------
    content = ContentStream(page.get_contents(), writer)
    ops = content.operations
    kept = []
    removed = 0
    scales = DATA_SCALES[problem]
    for start, end in top_level_groups(ops):
        cm, dos = group_info(ops, start, end)
        is_data_copy = (not dos) and cm is not None and any(abs(cm[0] - s) < 1e-5 for s in scales)
        if is_data_copy:
            removed += 1
            continue
        block = ops[start:end + 1]
        if dos and any(d in STRIP_TEXT_IN_GROUPS_WITH_DO.get(problem, ()) for d in dos):
            block = strip_text(block)
        kept.extend(block)
    if removed != 13 * len(PLACEMENTS[problem]):
        raise RuntimeError(f"expected {13 * len(PLACEMENTS[problem])} data groups, removed {removed}")

    def f(v):
        return FloatObject(round(float(v), 6))

    for (x, y, w, h), (a, b, c, d, e, g) in PLACEMENTS[problem]:
        kept.append(([], b"q"))
        kept.append(([f(x), f(y), f(w), f(h)], b"re"))
        kept.append(([], b"W"))
        kept.append(([], b"n"))
        kept.append(([f(a), f(b), f(c), f(d), f(e), f(g)], b"cm"))
        kept.append(([NameObject(layer_name)], b"Do"))
        kept.append(([], b"Q"))
    content.operations = kept
    page.replace_contents(content)

    # prune font resources that are no longer referenced (old pasted layer
    # fonts on the page; ReportLab's default base-14 entry in the new layer)
    def used_fonts(operations):
        return {str(operands[0]) for operands, op in operations if _op_name(op) == "Tf"}

    def prune(resource_dict, keep):
        fonts = resource_dict.get("/Font")
        if fonts is None:
            return
        fonts = fonts.get_object()
        for key in [k for k in fonts.keys() if str(k) not in keep]:
            del fonts[key]

    prune(resources, used_fonts(kept))
    layer_ops = ContentStream(form, writer).operations
    prune(form["/Resources"].get_object(), used_fonts(layer_ops))

    output.parent.mkdir(parents=True, exist_ok=True)
    writer.add_metadata({"/Title": f"Land problem {problem}: mid-wall deformation with Land et al. (2015) overlay",
                         "/Subject": "Keynote composite by P. Cardiff; data layer re-rendered 2026-10-29 (geometry unchanged)"})
    with output.open("wb") as handle:
        writer.write(handle)
    print(f"Wrote {output} (removed {removed} pasted data groups, added {len(PLACEMENTS[problem])} layer placements)")


def compose_compact(problem: int, overlay: Path, layer: Path, output: Path) -> None:
    """New page in the compact layout: each faint Land et al. layer moved with its panel.

    For panel k the faint layer keeps its alignment with the data because it
    is drawn with T_k = A_new o A_old^-1, where A_old maps data (x, z) to the
    Keynote page (layer panel geometry + Keynote placement) and A_new maps
    data to the new page (compact panel geometry at LAYER_SCALE).  Both are
    axis-aligned affine maps, so T_k is a per-axis scale plus a shift.
    """
    import render_land_midline_layers as R

    old_panels = R.PROBLEMS[problem]["panels"]
    compact = R.compact_layout(problem)
    new_panels = compact["panels"]
    S = R.LAYER_SCALE
    page_w, page_h = (S * v for v in compact["page"])

    reader = PdfReader(str(overlay))
    writer = PdfWriter()
    writer.append(reader)
    page = writer.pages[0]
    ops = ContentStream(page.get_contents(), writer).operations

    # the three faint layers, in drawing order: clip rectangle, alpha states, form name;
    # reordered to the panel index (0 full line, 1 apex, 2 inflection)
    found = []
    for start, end in top_level_groups(ops):
        _, dos = group_info(ops, start, end)
        if not dos:
            continue
        rect = next([float(v) for v in operands] for operands, op in ops[start:end + 1] if _op_name(op) == "re")
        # alpha states set BEFORE the faint layer is drawn (later ones belong to Keynote text, e.g. /Gs3 = opaque)
        states = []
        for operands, op in ops[start:end + 1]:
            if _op_name(op) == "Do":
                break
            if _op_name(op) == "gs":
                states.append(str(operands[0]))
        found.append((rect, states, dos[0]))
    if len(found) != len(new_panels):
        raise RuntimeError(f"expected {len(new_panels)} faint layers, found {len(found)}")
    faint = [None] * len(found)
    for drawn, panel_index in enumerate(FAINT_PANEL[problem]):
        faint[panel_index] = found[drawn]

    # data layer as a Form XObject (same import as composite())
    layer_page = PdfReader(str(layer)).pages[0]
    writer.add_page(layer_page)
    imported = writer.pages[-1]
    form = StreamObject()
    form[NameObject("/Type")] = NameObject("/XObject")
    form[NameObject("/Subtype")] = NameObject("/Form")
    form[NameObject("/FormType")] = FloatObject(1)
    form[NameObject("/BBox")] = ArrayObject([FloatObject(float(v)) for v in layer_page.mediabox])
    form[NameObject("/Resources")] = imported["/Resources"]
    form.set_data(imported.get_contents().get_data())
    form_ref = writer._add_object(form)
    writer.remove_page(len(writer.pages) - 1)
    resources = page["/Resources"]
    xobjects = resources["/XObject"].get_object()
    layer_name = "/FmDataLayer2026"
    xobjects[NameObject(layer_name)] = form_ref

    def f(v):
        return FloatObject(round(float(v), 6))

    placements = PLACEMENTS[problem]
    new_ops = []
    for k, (old, new, (rect, states, fm)) in enumerate(zip(old_panels, new_panels, faint)):
        _, (s, _, _, _, e, g) = placements[k if len(placements) == len(old_panels) else 0]
        ax = S * new.width / (s * old.width)
        bx = S * new.left - ax * (e + s * old.left)
        az = S * new.height / (s * old.height)
        bz = S * new.bottom - az * (g + s * old.bottom)
        # old clip mapped to the new page, intersected with the new panel frame
        x0, y0 = ax * rect[0] + bx, az * rect[1] + bz
        x1, y1 = ax * (rect[0] + rect[2]) + bx, az * (rect[1] + rect[3]) + bz
        fx0, fy0 = S * new.left, S * new.bottom
        fx1, fy1 = fx0 + S * new.width, fy0 + S * new.height
        cx0, cy0, cx1, cy1 = max(x0, fx0), max(y0, fy0), min(x1, fx1), min(y1, fy1)
        new_ops += [([], b"q"), ([f(cx0), f(cy0), f(cx1 - cx0), f(cy1 - cy0)], b"re"), ([], b"W"), ([], b"n"),
                    ([f(ax), f(0), f(0), f(az), f(bx), f(bz)], b"cm")]
        new_ops += [([NameObject(gs)], b"gs") for gs in states]
        new_ops += [([NameObject(fm)], b"Do"), ([], b"Q")]
    new_ops += [([], b"q"), ([f(S), f(0), f(0), f(S), f(0), f(0)], b"cm"), ([NameObject(layer_name)], b"Do"),
                ([], b"Q")]
    content = ContentStream(page.get_contents(), writer)
    content.operations = new_ops
    page.replace_contents(content)
    box = ArrayObject([f(0), f(0), f(page_w), f(page_h)])
    for key in ("/MediaBox", "/CropBox", "/BleedBox", "/TrimBox", "/ArtBox"):
        if key in page or key == "/MediaBox":
            page[NameObject(key)] = box

    # keep only what the new page uses
    fonts = resources.get("/Font")
    if fonts is not None:
        del resources["/Font"]
    used = {fm for _, _, fm in faint} | {layer_name}
    for key in [k for k in xobjects.keys() if str(k) not in used]:
        del xobjects[key]
    layer_ops = ContentStream(form, writer).operations
    used_fonts = {str(operands[0]) for operands, op in layer_ops if _op_name(op) == "Tf"}
    layer_fonts = form["/Resources"].get_object().get("/Font")
    if layer_fonts is not None:
        layer_fonts = layer_fonts.get_object()
        for key in [k for k in layer_fonts.keys() if str(k) not in used_fonts]:
            del layer_fonts[key]

    output.parent.mkdir(parents=True, exist_ok=True)
    writer.add_metadata({"/Title": f"Land problem {problem}: mid-wall deformation with Land et al. (2015) overlay",
                         "/Subject": "compact layout: (a) left, (b)/(c) stacked right; faint layers moved with their panels"})
    with output.open("wb") as handle:
        writer.write(handle)
    print(f"Wrote {output} (compact layout, {page_w:.1f} x {page_h:.1f} pt)")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--problem", type=int, choices=(2, 3), required=True)
    parser.add_argument("--overlay", type=Path, required=True, help="original Keynote overlay PDF")
    parser.add_argument("--layer", type=Path, required=True, help="re-rendered data layer PDF")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--layout", choices=("keynote", "compact"), default="keynote")
    args = parser.parse_args()
    if args.layout == "compact":
        compose_compact(args.problem, args.overlay, args.layer, args.output)
    else:
        composite(args.problem, args.overlay, args.layer, args.output)


if __name__ == "__main__":
    main()
