"""fpdf2 vector text helpers for cover composition.

All functions draw vector text that survives as vector in the output PDF
(proven by pypdf text extraction in tests).
"""
from fpdf import FPDF

RGB = tuple[int, int, int]


def _set_font(pdf: FPDF, size_pt: float) -> None:
    """Use the first registered TTF or fall back to Helvetica."""
    if pdf.fonts:
        first = next(iter(pdf.fonts.values()))
        family = first.get("fontkey", "Helvetica") if isinstance(first, dict) else "Helvetica"
    else:
        family = "Helvetica"
    pdf.set_font(family, size=size_pt)


def draw_centered_text(
    pdf: FPDF,
    text: str,
    x_center: float,
    y: float,
    size_pt: float,
    color: RGB,
) -> None:
    """Draw a single line of text centered horizontally at x_center, baseline y."""
    _set_font(pdf, size_pt)
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
) -> None:
    """Draw a stack of left-aligned lines starting at (x, y) descending."""
    _set_font(pdf, size_pt)
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
) -> None:
    """Draw rotated spine text running bottom-to-top along the spine center.

    Text is centered across the spine width and runs the vertical length.
    Skips silently if spine_width < 0.0625 (KDP minimum for spine text).
    """
    if spine_width < 0.0625:
        return
    _set_font(pdf, size_pt)
    pdf.set_text_color(*color)

    spine_center_x = spine_start_x + spine_width / 2
    start_y = wrap_height - 0.5  # 0.5" safe zone from bottom
    # Rotate 90° counterclockwise around (spine_center_x, start_y)
    with pdf.rotation(90, spine_center_x, start_y):
        pdf.text(spine_center_x, start_y, text)
