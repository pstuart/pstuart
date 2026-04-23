#!/usr/bin/env python3
"""Compose a Kindle cover JPEG (1600x2560).

Internal layout uses the same vector-first approach as paperback —
render a small PDF with vector text over bitmap, then rasterize to JPEG
as the very last step. Keeps one mental model across all cover surfaces.
"""
from pathlib import Path
from fpdf import FPDF
from PIL import Image
from pdf2image import convert_from_path

from lib.cover_text import draw_centered_text
from lib.cover_style import resolve_colors

KINDLE_WIDTH_PX = 1600
KINDLE_HEIGHT_PX = 2560
DPI = 300
KINDLE_WIDTH_IN = KINDLE_WIDTH_PX / DPI
KINDLE_HEIGHT_IN = KINDLE_HEIGHT_PX / DPI


def compose_kindle(
    book_config: dict,
    kindle_art: Path,
    output: Path,
) -> Path:
    """Render kindle_cover.jpg at 1600x2560. Returns output path."""
    missing = [k for k in ("title", "author") if not book_config.get(k)]
    if missing:
        raise ValueError(
            f"book_config missing required keys: {missing}. "
            "Set TITLE and AUTHOR in BOOK_CONFIG before composing."
        )
    preset = book_config.get("style_preset", "navy_gold")
    tone = book_config.get("background_tone", "light_bg")
    colors = resolve_colors(preset, tone=tone)

    # Build PDF at Kindle dimensions
    pdf = FPDF(unit="in", format=(KINDLE_WIDTH_IN, KINDLE_HEIGHT_IN))
    pdf.set_auto_page_break(auto=False)
    pdf.add_page()

    if kindle_art.exists():
        pdf.image(str(kindle_art), x=0, y=0, w=KINDLE_WIDTH_IN, h=KINDLE_HEIGHT_IN)

    center_x = KINDLE_WIDTH_IN / 2
    draw_centered_text(
        pdf, text=book_config["title"].upper(),
        x_center=center_x, y=1.8,
        size_pt=56, color=colors["title"],
    )
    if book_config.get("subtitle"):
        draw_centered_text(
            pdf, text=book_config["subtitle"],
            x_center=center_x, y=2.8,
            size_pt=22, color=colors["body"],
        )
    draw_centered_text(
        pdf, text=book_config["author"].upper(),
        x_center=center_x, y=KINDLE_HEIGHT_IN - 0.8,
        size_pt=24, color=colors["title"],
    )

    # Rasterize
    tmp_pdf = output.with_suffix(".tmp.pdf")
    output.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(tmp_pdf))

    images = convert_from_path(str(tmp_pdf), dpi=DPI)
    img = images[0].convert("RGB")
    if img.size != (KINDLE_WIDTH_PX, KINDLE_HEIGHT_PX):
        img = img.resize((KINDLE_WIDTH_PX, KINDLE_HEIGHT_PX), Image.Resampling.LANCZOS)
    img.save(output, "JPEG", quality=95)

    tmp_pdf.unlink(missing_ok=True)
    return output


if __name__ == "__main__":
    from BOOK_CONFIG import BOOK_CONFIG  # noqa

    project = Path(__file__).parent
    assets = project / "cover-assets"
    compose_kindle(
        book_config=BOOK_CONFIG,
        kindle_art=assets / "kindle_art.png",
        output=assets / "kindle_cover.jpg",
    )
    print(f"Wrote {assets / 'kindle_cover.jpg'}")
