#!/usr/bin/env python3
"""Merge vector cover panels with the book interior PDF.

Reads the paperback_wrap.pdf produced by compose_paperback_wrap.py,
crops out the front and back panels via pypdf mediabox transforms
(preserving vector content), then stitches:

    [ front_panel.pdf | book_interior.pdf | back_panel.pdf ]

into one KDP-upload-ready PDF.
"""
from pathlib import Path
from pypdf import PdfReader, PdfWriter
from pypdf.generic import RectangleObject

from lib.cover_dimensions import (
    panel_offsets_inches,
    wrap_canvas_inches,
    BLEED_INCHES,
    TRIM_WIDTH_INCHES,
    TRIM_HEIGHT_INCHES,
)


def _extract_panel_as_pdf(
    wrap_pdf: Path, page_count: int, paper: str, panel: str, out: Path
) -> Path:
    """Crop the wrap PDF to a single panel (front or back) and write to out.

    panel = 'front' or 'back'. Preserves vector content via MediaBox crop.
    """
    reader = PdfReader(str(wrap_pdf))
    writer = PdfWriter()
    page = reader.pages[0]

    wrap_w, wrap_h = wrap_canvas_inches(page_count, paper)
    offsets = panel_offsets_inches(page_count, paper)

    # pypdf uses points (72 pt = 1 in)
    if panel == "front":
        x0_in = offsets["front_start"]
        x1_in = offsets["front_end"]
    elif panel == "back":
        x0_in = offsets["back_start"]
        x1_in = offsets["back_end"]
    else:
        raise ValueError(f"panel must be 'front' or 'back', got {panel!r}")

    x0_pt = x0_in * 72
    x1_pt = x1_in * 72
    y0_pt = 0
    y1_pt = wrap_h * 72

    page.mediabox = RectangleObject((x0_pt, y0_pt, x1_pt, y1_pt))
    page.cropbox = RectangleObject((x0_pt, y0_pt, x1_pt, y1_pt))
    writer.add_page(page)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "wb") as f:
        writer.write(f)
    return out


def add_covers_to_pdf(
    book_pdf: Path,
    wrap_pdf: Path,
    page_count: int,
    paper: str,
    output: Path,
) -> Path:
    """Merge extracted front cover + book interior + extracted back cover."""
    front = _extract_panel_as_pdf(wrap_pdf, page_count, paper, "front", output.parent / "_front.pdf")
    back = _extract_panel_as_pdf(wrap_pdf, page_count, paper, "back", output.parent / "_back.pdf")

    writer = PdfWriter()
    for src in (front, book_pdf, back):
        reader = PdfReader(str(src))
        for page in reader.pages:
            writer.add_page(page)

    with open(output, "wb") as f:
        writer.write(f)

    # Clean up temp panel PDFs
    front.unlink(missing_ok=True)
    back.unlink(missing_ok=True)
    return output


if __name__ == "__main__":
    from BOOK_CONFIG import BOOK_CONFIG  # noqa
    project = Path(__file__).parent
    assets = project / "cover-assets"

    # Find latest book PDF
    pdfs = sorted(project.glob("*_v*.pdf"), key=lambda p: p.stat().st_mtime)
    if not pdfs:
        raise SystemExit("ERROR: no book PDF found. Run generate_pdf.py first.")
    book_pdf = pdfs[-1]

    out = book_pdf.with_name(book_pdf.stem + "_with_covers.pdf")
    add_covers_to_pdf(
        book_pdf=book_pdf,
        wrap_pdf=assets / "paperback_wrap.pdf",
        page_count=BOOK_CONFIG["page_count"],
        paper=BOOK_CONFIG.get("paper_type", "white"),
        output=out,
    )
    print(f"Wrote {out}")
