"""bookpub.with_covers — assemble a complete reading PDF: [front | interior | back].

Crops the front and back panels out of the finished paperback WRAP (which is a
single landscape page: back | spine | front, with 0.125" bleed) and wraps them
around the interior. Page 1 becomes the real cover — photo plus crisp vector
text — at trim size, matching the interior pages. Nothing is rasterised: the
crop is a pypdf mediabox transform, so both the bitmap art and the vector text
survive.

This is a PROOF / direct-distribution PDF. For KDP print you still upload the
interior and the wrap separately; this combined file is for review and ebook-PDF
sharing where readers expect the cover on page 1.

    python3 -m bookpub.with_covers book.toml output            # uses output/<slug>_{wrap,interior}.pdf
    python3 -m bookpub.with_covers book.toml output --slug x --wrap a.pdf --interior b.pdf
"""
from __future__ import annotations

import argparse
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from pypdf.generic import RectangleObject

from bookpub.build_book import _slug
from bookpub.config import load_book_config

PT = 72.0
BLEED = 0.125


def _panel(wrap_pdf: Path, x0_in: float, trim_w: float, trim_h: float):
    """Return a single wrap page cropped to a trim-sized panel at x0 (inches)."""
    page = PdfReader(str(wrap_pdf)).pages[0]
    x0, y0 = x0_in * PT, BLEED * PT
    x1, y1 = (x0_in + trim_w) * PT, (BLEED + trim_h) * PT
    box = RectangleObject((x0, y0, x1, y1))
    page.mediabox = box
    page.cropbox = box
    return page


def build_with_covers(book_toml: str | Path, out_dir: str | Path,
                      slug: str | None = None,
                      wrap: str | Path | None = None,
                      interior: str | Path | None = None,
                      out: str | Path | None = None) -> dict:
    cfg = load_book_config(book_toml)
    slug = slug or _slug(cfg)
    out_dir = Path(out_dir)
    wrap = Path(wrap) if wrap else out_dir / f"{slug}_wrap.pdf"
    interior = Path(interior) if interior else out_dir / f"{slug}_interior.pdf"
    out = Path(out) if out else out_dir / f"{slug}_with_covers.pdf"

    # Trim is whatever the interior pages actually are (they carry no bleed), so
    # this works for a 5.5x8.5 novel and an 8.5x11 screenplay alike — no need to
    # trust book.toml, whose trim describes the novel.
    ipage = PdfReader(str(interior)).pages[0].mediabox
    trim_w, trim_h = float(ipage.width) / PT, float(ipage.height) / PT

    wrap_w_in = float(PdfReader(str(wrap)).pages[0].mediabox.width) / PT
    front_x0 = wrap_w_in - trim_w - BLEED   # inner (spine-side) edge of the front trim
    back_x0 = BLEED                         # inner edge of the back trim

    writer = PdfWriter()
    writer.add_page(_panel(wrap, front_x0, trim_w, trim_h))
    for p in PdfReader(str(interior)).pages:
        writer.add_page(p)
    writer.add_page(_panel(wrap, back_x0, trim_w, trim_h))
    with open(out, "wb") as f:
        writer.write(f)
    return {"output": str(out), "pages": len(writer.pages),
            "trim_in": (trim_w, trim_h)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("book_toml")
    ap.add_argument("out_dir")
    ap.add_argument("--slug")
    ap.add_argument("--wrap")
    ap.add_argument("--interior")
    ap.add_argument("--out")
    a = ap.parse_args()
    res = build_with_covers(a.book_toml, a.out_dir, a.slug, a.wrap, a.interior, a.out)
    print(f"{res['output']}  ({res['pages']} pp, trim {res['trim_in']})")


if __name__ == "__main__":
    main()
