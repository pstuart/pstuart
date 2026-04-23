#!/usr/bin/env python3
"""Compose a print-ready paperback wrap PDF.

Vector text is drawn over a full-bleed bitmap. The bitmap itself should be
a zgen-generated wrap_art.png at 4992 x 2624 (trimmed to exact wrap dims).

Usage (as a script):
    python3 compose_paperback_wrap.py

Usage (as a library, e.g. from tests):
    from compose_paperback_wrap_template import compose_wrap
    compose_wrap(book_config=..., wrap_art=..., output=...)
"""
from pathlib import Path
from fpdf import FPDF

from lib.cover_dimensions import (
    wrap_canvas_inches,
    panel_offsets_inches,
    TRIM_WIDTH_INCHES,
    TRIM_HEIGHT_INCHES,
    BLEED_INCHES,
    SAFE_MARGIN_INCHES,
)
from lib.cover_text import (
    draw_centered_text,
    draw_left_aligned_block,
    draw_spine_text,
)
from lib.cover_style import resolve_colors


def compose_wrap(
    book_config: dict,
    wrap_art: Path,
    output: Path,
) -> Path:
    """Render paperback_wrap.pdf. Returns output path."""
    missing = [k for k in ("title", "author") if not book_config.get(k)]
    if missing:
        raise ValueError(
            f"book_config missing required keys: {missing}. "
            "Set TITLE and AUTHOR in BOOK_CONFIG before composing."
        )
    if book_config.get("page_count", 0) < 24:
        raise ValueError(
            f"book_config['page_count'] must be >= 24 (got {book_config.get('page_count')}). "
            "Set PAGE_COUNT in BOOK_CONFIG before composing — spine depends on it."
        )
    page_count = book_config["page_count"]
    paper = book_config.get("paper_type", "white")
    preset = book_config.get("style_preset", "navy_gold")
    tone = book_config.get("background_tone", "light_bg")
    colors = resolve_colors(preset, tone=tone)

    wrap_w, wrap_h = wrap_canvas_inches(page_count, paper)
    offsets = panel_offsets_inches(page_count, paper)

    pdf = FPDF(unit="in", format=(wrap_w, wrap_h))
    pdf.set_auto_page_break(auto=False)
    pdf.add_page()

    # 1. Full-bleed bitmap background
    if wrap_art.exists():
        pdf.image(str(wrap_art), x=0, y=0, w=wrap_w, h=wrap_h)

    # 2. Front panel text (right side)
    front_cx = (offsets["front_start"] + offsets["front_end"]) / 2
    front_safe_top = BLEED_INCHES + SAFE_MARGIN_INCHES
    draw_centered_text(
        pdf, text=book_config["title"].upper(),
        x_center=front_cx, y=front_safe_top + 0.8,
        size_pt=42, color=colors["title"],
    )
    if book_config.get("subtitle"):
        draw_centered_text(
            pdf, text=book_config["subtitle"],
            x_center=front_cx, y=front_safe_top + 1.6,
            size_pt=16, color=colors["body"],
        )
    draw_centered_text(
        pdf, text=book_config["author"].upper(),
        x_center=front_cx,
        y=wrap_h - BLEED_INCHES - SAFE_MARGIN_INCHES - 0.4,
        size_pt=18, color=colors["title"],
    )

    # 3. Back panel text (left side)
    back_safe_left = offsets["back_start"] + BLEED_INCHES + SAFE_MARGIN_INCHES
    back_safe_top = BLEED_INCHES + SAFE_MARGIN_INCHES + 0.5
    if book_config.get("tagline"):
        draw_centered_text(
            pdf, text=book_config["tagline"],
            x_center=(offsets["back_start"] + offsets["back_end"]) / 2,
            y=back_safe_top,
            size_pt=14, color=colors["accent"],
        )
    back_body_y = back_safe_top + 0.6
    body_lines = book_config.get("back_body_lines", [])
    if body_lines:
        draw_left_aligned_block(
            pdf, lines=body_lines,
            x=back_safe_left, y=back_body_y,
            size_pt=10, color=colors["body"], line_height_in=0.18,
        )

    # 4. Spine text (if spine wide enough)
    spine_w = offsets["spine_end"] - offsets["spine_start"]
    spine_text = f"{book_config['title']}  /  {book_config['author']}"
    draw_spine_text(
        pdf, text=spine_text,
        spine_start_x=offsets["spine_start"],
        spine_width=spine_w,
        wrap_height=wrap_h,
        size_pt=10, color=colors["title"],
    )

    output.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(output))
    return output


if __name__ == "__main__":
    # CUSTOMIZE: set BOOK_CONFIG and paths for your project
    from BOOK_CONFIG import BOOK_CONFIG  # noqa

    project = Path(__file__).parent
    assets = project / "cover-assets"
    compose_wrap(
        book_config=BOOK_CONFIG,
        wrap_art=assets / "wrap_art.png",
        output=assets / "paperback_wrap.pdf",
    )
    print(f"Wrote {assets / 'paperback_wrap.pdf'}")
