#!/usr/bin/env python3
"""Compose a Kindle cover JPEG (1600x2560).

Internal layout uses the same vector-first approach as paperback —
render a small PDF with vector text over bitmap, then rasterize to JPEG
as the very last step. Keeps one mental model across all cover surfaces.

Front-cover zones (top to bottom):
  1. kindle_quote (optional pull-quote, italic accent)
  2. title (bold uppercased)
  3. subtitle (italic, ACCENT color — reads over any bitmap tone)
  4. author (bold uppercased, near bottom)
  5. series_line_front (very bottom, small italic)
"""
from pathlib import Path
from fpdf import FPDF
from PIL import Image
from pdf2image import convert_from_path

from lib.cover_text import draw_centered_text, draw_bold_text
from lib.cover_style import resolve_colors
from lib.cover_fonts import register_fonts
from lib.cover_config import validate_and_defaults

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
    config = validate_and_defaults(book_config)
    preset = config["style_preset"]
    tone = config["background_tone"]
    colors = resolve_colors(preset, tone=tone)

    # Build PDF at Kindle dimensions
    pdf = FPDF(unit="in", format=(KINDLE_WIDTH_IN, KINDLE_HEIGHT_IN))
    pdf.set_auto_page_break(auto=False)
    pdf.add_page()
    register_fonts(pdf)

    if kindle_art.exists():
        pdf.image(str(kindle_art), x=0, y=0, w=KINDLE_WIDTH_IN, h=KINDLE_HEIGHT_IN)

    center_x = KINDLE_WIDTH_IN / 2

    # Zone 1: optional front pull-quote (italic, above title)
    if config.get("kindle_quote"):
        draw_centered_text(
            pdf, text=config["kindle_quote"],
            x_center=center_x, y=1.1,
            size_pt=16, color=colors["accent"], font_key="italic",
            halo=colors["halo"],
        )

    # Zone 2: title (bold, uppercased)
    draw_bold_text(
        pdf, text=config["title"].upper(),
        x_center=center_x, y=1.9,
        size_pt=56, color=colors["title"],
        halo=colors["halo"],
    )

    # Zone 3: subtitle — uses ACCENT color (fixes #663: reads over any bg tone)
    if config.get("subtitle"):
        draw_centered_text(
            pdf, text=config["subtitle"],
            x_center=center_x, y=2.7,
            size_pt=20, color=colors["accent"], font_key="italic",
            halo=colors["halo"],
        )

    # Zone 4: author (bold, uppercased) — sit near bottom
    draw_bold_text(
        pdf, text=config["author"].upper(),
        x_center=center_x, y=KINDLE_HEIGHT_IN - 1.1,
        size_pt=24, color=colors["title"],
        halo=colors["halo"],
    )

    # Zone 5: optional series line (very bottom)
    if config.get("series_line_front"):
        draw_centered_text(
            pdf, text=config["series_line_front"],
            x_center=center_x, y=KINDLE_HEIGHT_IN - 0.5,
            size_pt=12, color=colors["body"], font_key="italic",
            halo=colors["halo"],
        )

    # Rasterize (Kindle requires JPEG per KDP spec)
    tmp_pdf = output.with_suffix(".tmp.pdf")
    output.parent.mkdir(parents=True, exist_ok=True)
    try:
        pdf.output(str(tmp_pdf))
        images = convert_from_path(str(tmp_pdf), dpi=DPI)
        img = images[0].convert("RGB")
        if img.size != (KINDLE_WIDTH_PX, KINDLE_HEIGHT_PX):
            img = img.resize(
                (KINDLE_WIDTH_PX, KINDLE_HEIGHT_PX),
                Image.Resampling.LANCZOS,
            )
        img.save(output, "JPEG", quality=95)
    finally:
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
