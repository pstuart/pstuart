"""fpdf2 vector text helpers for cover composition.

All functions draw vector text that survives as vector in the output PDF
(proven by pypdf text extraction in tests).

Fonts: if the caller has registered EB Garamond via
`lib.cover_fonts.register_fonts(pdf)`, these helpers use it automatically.
Otherwise they fall back to core Helvetica (latin-1 only — no Unicode punctuation).
"""
from fpdf import FPDF

RGB = tuple[int, int, int]


_EBG_FAMILY = "ebgaramond"


def _font_for(pdf: FPDF, font_key: str) -> tuple[str, str]:
    """Resolve (family, style) for a font_key. Falls back to Helvetica if no EBG registered.

    font_key ∈ {'regular', 'italic', 'bold', 'bolditalic'}.
    """
    style_for_key = {"regular": "", "italic": "I", "bold": "B", "bolditalic": "BI"}
    if font_key not in style_for_key:
        raise ValueError(
            f"Unknown font_key {font_key!r}. "
            f"Valid: {sorted(style_for_key.keys())}"
        )
    style = style_for_key[font_key]
    # Check if EBG is registered for this style
    ebg_key = f"{_EBG_FAMILY}{style}"
    if ebg_key in pdf.fonts:
        return (_EBG_FAMILY, style)
    # Fallback: core Helvetica (latin-1 only)
    return ("Helvetica", style)


def draw_centered_text(
    pdf: FPDF,
    text: str,
    x_center: float,
    y: float,
    size_pt: float,
    color: RGB,
    font_key: str = "regular",
) -> None:
    """Draw a single line of text centered horizontally at x_center, baseline y."""
    family, style = _font_for(pdf, font_key)
    pdf.set_font(family, style, size=size_pt)
    pdf.set_text_color(*color)
    string_w = pdf.get_string_width(text)
    pdf.text(x_center - string_w / 2, y, text)


def draw_left_aligned_block(
    pdf: FPDF,
    lines: list[str],
    x: float,
    y: float,
    size_pt: float,
    color: RGB,
    line_height_in: float,
    font_key: str = "regular",
) -> None:
    """Draw a stack of left-aligned lines starting at (x, y) descending."""
    family, style = _font_for(pdf, font_key)
    pdf.set_font(family, style, size=size_pt)
    pdf.set_text_color(*color)
    cur_y = y
    for line in lines:
        pdf.text(x, cur_y, line)
        cur_y += line_height_in


def draw_spine_text(
    pdf: FPDF,
    text: str,
    spine_start_x: float,
    spine_width: float,
    wrap_height: float,
    size_pt: float,
    color: RGB,
    font_key: str = "regular",
) -> None:
    """Draw rotated spine text running bottom-to-top along the spine center.

    Text is centered across the spine width and runs the vertical length.
    Skips silently if spine_width < 0.0625 (KDP minimum for spine text).
    """
    if spine_width < 0.0625:
        return
    family, style = _font_for(pdf, font_key)
    pdf.set_font(family, style, size=size_pt)
    pdf.set_text_color(*color)

    spine_center_x = spine_start_x + spine_width / 2
    start_y = wrap_height - 0.5  # 0.5" safe zone from bottom
    # Rotate 90° counterclockwise around (spine_center_x, start_y)
    with pdf.rotation(90, spine_center_x, start_y):
        pdf.text(spine_center_x, start_y, text)


# Convenience wrappers for the common hierarchy slots

def draw_italic_block(
    pdf: FPDF,
    lines: list[str],
    x: float,
    y: float,
    size_pt: float,
    color: RGB,
    line_height_in: float,
) -> None:
    """Left-aligned block in italic (for quotes, taglines, bios)."""
    draw_left_aligned_block(pdf, lines, x, y, size_pt, color, line_height_in, font_key="italic")


def draw_bold_text(
    pdf: FPDF,
    text: str,
    x_center: float,
    y: float,
    size_pt: float,
    color: RGB,
) -> None:
    """Centered bold text (for titles, section labels)."""
    draw_centered_text(pdf, text, x_center, y, size_pt, color, font_key="bold")
