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
    draw_italic_block,
    draw_bold_text,
)
from lib.cover_style import resolve_colors
from lib.cover_fonts import register_fonts
from lib.cover_decor import draw_ink_rule, draw_flourish_rule


def _render_front_panel(
    pdf: FPDF,
    config: dict,
    offsets: dict,
    wrap_height: float,
    colors: dict,
    fonts: dict,
) -> None:
    """Render vector text zones for the front (right) panel of the wrap.

    Mutates pdf in place. All optional zones skip silently when the field is
    absent or empty.
    """
    front_start = offsets["front_start"]
    front_end = offsets["front_end"]
    cx = (front_start + front_end) / 2
    safe_top = BLEED_INCHES + SAFE_MARGIN_INCHES
    safe_bottom = wrap_height - BLEED_INCHES - SAFE_MARGIN_INCHES

    # Title (required — always present after validate_and_defaults)
    title = config["title"].upper()
    draw_bold_text(pdf, title, cx, safe_top + 1.2, size_pt=40, color=colors["title"])

    # Subtitle (optional)
    if config.get("subtitle"):
        draw_centered_text(
            pdf, text=config["subtitle"],
            x_center=cx, y=safe_top + 1.9,
            size_pt=18, color=colors["accent"], font_key="italic",
        )

    # Flourish rule — always drawn; anchors the byline visually
    flourish_y = safe_bottom - 1.8
    draw_flourish_rule(pdf, x_center=cx, y=flourish_y, half_width=1.5, color=colors["accent"])

    # Byline: config["byline"] override, or "BY {AUTHOR}"
    byline_text = config.get("byline") or f"BY {config['author'].upper()}"
    draw_bold_text(pdf, byline_text, cx, safe_bottom - 1.5, size_pt=18, color=colors["title"])

    # Series line (very bottom, optional)
    if config.get("series_line_front"):
        draw_centered_text(
            pdf, text=config["series_line_front"],
            x_center=cx, y=safe_bottom - 0.3,
            size_pt=12, color=colors["body"], font_key="italic",
        )


def _render_back_panel(
    pdf: FPDF,
    config: dict,
    offsets: dict,
    wrap_height: float,
    colors: dict,
    fonts: dict,
    asset_dir: Path,
) -> None:
    """Render vector text zones for the back (left) panel of the wrap.

    Mutates pdf in place. All optional zones skip silently when the field is
    absent or empty. asset_dir is used for temporary barcode PNG files.
    """
    back_start = offsets["back_start"]
    back_end = offsets["back_end"]
    safe_left = back_start + BLEED_INCHES + SAFE_MARGIN_INCHES
    safe_right = back_end - SAFE_MARGIN_INCHES
    cx = (back_start + back_end) / 2
    safe_top = BLEED_INCHES + SAFE_MARGIN_INCHES
    safe_bottom = wrap_height - BLEED_INCHES - SAFE_MARGIN_INCHES
    text_w = safe_right - safe_left  # noqa: F841 — available for future use

    # --- Bottom-anchored zones (compute y positions first; flowing zones must not overlap) ---

    # Series line back (very bottom)
    series_y = safe_bottom - 0.15
    if config.get("series_line_back"):
        draw_centered_text(
            pdf, text=config["series_line_back"],
            x_center=cx, y=series_y,
            size_pt=10, color=colors["body"], font_key="italic",
        )

    # Publisher line (above series)
    publisher_parts = [
        p for p in (config.get("imprint"), config.get("publisher"), config.get("publisher_city"))
        if p
    ]
    publisher_y = series_y - 0.25
    if publisher_parts:
        publisher_text = "  ·  ".join(publisher_parts)
        draw_centered_text(
            pdf, text=publisher_text,
            x_center=cx, y=publisher_y,
            size_pt=10, color=colors["body"], font_key="italic",
        )

    # Barcode zone (bottom-right, 1.75"w × 0.9"h, above publisher line)
    barcode_w_in = 1.75
    barcode_h_in = 0.9
    barcode_x = safe_right - barcode_w_in
    barcode_y = publisher_y - 0.2 - barcode_h_in
    if config.get("isbn"):
        from lib.cover_barcode import render_isbn_barcode
        barcode_png = asset_dir / "_barcode.png"
        try:
            render_isbn_barcode(
                config["isbn"], barcode_png,
                width_px=int(barcode_w_in * 300), height_px=int(barcode_h_in * 300),
            )
            # White background ensures barcode scannability on any panel color
            pdf.set_fill_color(255, 255, 255)
            pdf.rect(barcode_x, barcode_y, barcode_w_in, barcode_h_in, style="F")
            pdf.image(
                str(barcode_png),
                x=barcode_x + 0.05, y=barcode_y + 0.05,
                w=barcode_w_in - 0.1, h=barcode_h_in - 0.3,
            )
            # Price label (below the barcode image, inside the white rect)
            if config.get("price_us"):
                draw_centered_text(
                    pdf, text=config["price_us"],
                    x_center=barcode_x + barcode_w_in / 2,
                    y=barcode_y + barcode_h_in - 0.15,
                    size_pt=12, color=(20, 20, 20), font_key="bold",
                )
        except ValueError as e:
            # Bad ISBN (rejected by cover_barcode validator) — skip silently, log warning
            print(f"WARNING: ISBN barcode render failed ({e}); skipping barcode zone")
            barcode_x = safe_right  # collapse zone so photo gets full width

    # Author photo (bottom-left, above publisher line)
    photo_w_in = 1.25
    photo_h_in = 1.5
    photo_x = safe_left
    photo_y = publisher_y - 0.2 - photo_h_in
    has_photo = bool(config.get("author_photo")) and Path(str(config["author_photo"])).exists()
    if has_photo:
        pdf.image(str(config["author_photo"]), x=photo_x, y=photo_y, w=photo_w_in, h=photo_h_in)

    # Flowing zones must stop before bumping into the photo / publisher area
    flow_bottom = photo_y - 0.1 if has_photo else (publisher_y - 0.2)

    # --- Flowing zones (top-down) ---
    cur_y = safe_top + 0.2

    # Genre line (optional)
    if config.get("genre_line"):
        draw_centered_text(
            pdf, text=config["genre_line"],
            x_center=cx, y=cur_y,
            size_pt=14, color=colors["body"], font_key="italic",
        )
        cur_y += 0.35
        draw_flourish_rule(pdf, x_center=cx, y=cur_y, half_width=1.6, color=colors["accent"])
        cur_y += 0.35

    # Back tagline (optional; supports \n for multi-line)
    if config.get("back_tagline"):
        tag_lines = config["back_tagline"].split("\n")
        for line in tag_lines:
            draw_centered_text(
                pdf, text=line, x_center=cx, y=cur_y,
                size_pt=18, color=colors["title"], font_key="italic",
            )
            cur_y += 0.27
        cur_y += 0.1
        draw_ink_rule(
            pdf, x_start=safe_left, x_end=safe_right, y=cur_y,
            color=colors["accent"], width=0.008,
        )
        cur_y += 0.2

    # Quote block (optional; supports \n for multi-line quote text)
    if config.get("quote"):
        quote_lines = config["quote"].split("\n")
        for i, line in enumerate(quote_lines):
            display = f"“{line}”" if i == 0 and not line.startswith("“") else line
            draw_centered_text(
                pdf, text=display, x_center=cx, y=cur_y,
                size_pt=12, color=colors["body"], font_key="italic",
            )
            cur_y += 0.22
        if config.get("quote_attribution"):
            cur_y += 0.05
            draw_centered_text(
                pdf, text=f"— {config['quote_attribution']}",
                x_center=cx, y=cur_y,
                size_pt=10, color=colors["body"], font_key="italic",
            )
            cur_y += 0.25
        draw_ink_rule(
            pdf, x_start=safe_left, x_end=safe_right, y=cur_y,
            color=colors["accent"], width=0.008,
        )
        cur_y += 0.2

    # Blurb paragraphs (left-aligned; blank lines become paragraph breaks)
    blurb = config.get("blurb", [])
    if blurb:
        max_cur_y = flow_bottom - 0.3
        for line in blurb:
            if cur_y > max_cur_y:
                break
            if line:
                draw_left_aligned_block(
                    pdf, lines=[line], x=safe_left, y=cur_y,
                    size_pt=11, color=colors["body"], line_height_in=0.18,
                )
            cur_y += 0.18
        cur_y += 0.1
        draw_ink_rule(
            pdf, x_start=safe_left, x_end=safe_right, y=cur_y,
            color=colors["accent"], width=0.008,
        )
        cur_y += 0.2

    # Author bio
    if config.get("author_bio"):
        draw_bold_text(
            pdf, text=config.get("author_bio_label", "About the Author"),
            x_center=safe_left + 1.0, y=cur_y,
            size_pt=11, color=colors["accent"],
        )
        cur_y += 0.2
        bio_lines = config["author_bio"].split("\n")
        bio_x = safe_left + (photo_w_in + 0.15 if has_photo else 0)
        for line in bio_lines:
            if cur_y > flow_bottom:
                break
            draw_italic_block(
                pdf, lines=[line], x=bio_x, y=cur_y,
                size_pt=10, color=colors["body"], line_height_in=0.17,
            )
            cur_y += 0.17


def _render_spine(
    pdf: FPDF,
    config: dict,
    offsets: dict,
    wrap_height: float,
    colors: dict,
    fonts: dict,
) -> None:
    """Render rotated text along the spine panel.

    Mutates pdf in place. Skips silently if spine is too narrow for text.
    Also adds imprint mark at spine top when spine >= 0.5" and imprint is set.

    Precondition: `fonts` dict must include the 'italic' key. This is
    always satisfied when the caller ran `register_fonts(pdf)` first. If
    the imprint path fires without the italic font registered, fpdf2 will
    raise when attempting to use the unregistered core-italic fallback.
    """
    spine_start = offsets["spine_start"]
    spine_end = offsets["spine_end"]
    spine_w = spine_end - spine_start
    spine_text = f"{config['title']}  /  {config['author']}"
    draw_spine_text(
        pdf, text=spine_text,
        spine_start_x=spine_start, spine_width=spine_w,
        wrap_height=wrap_height,
        size_pt=10, color=colors["title"], font_key="regular",
    )
    # Imprint mark at spine top (bookshelf-visible; only if wide enough and present)
    if spine_w >= 0.5 and config.get("imprint"):
        spine_center_x = spine_start + spine_w / 2
        top_y = 0.5  # 0.5" down from canvas top
        with pdf.rotation(90, spine_center_x, top_y):
            family, style = fonts.get("italic", ("Helvetica", "I"))
            pdf.set_font(family, style, size=8)
            pdf.set_text_color(*colors["body"])
            text_w = pdf.get_string_width(config["imprint"])
            pdf.text(spine_center_x - text_w / 2, top_y, config["imprint"])


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
