"""Decorative vector primitives for cover ornamentation.

Everything here draws via fpdf2's low-level API so the output stays vector
(confirmed via pypdf content-stream inspection in tests). These helpers
mimic the flourish style of the legacy Pillow cover generator: thin rules
and a flourish rule with a centered diamond glyph.
"""
from fpdf import FPDF

RGB = tuple[int, int, int]


def draw_ink_rule(
    pdf: FPDF,
    x_start: float,
    x_end: float,
    y: float,
    color: RGB,
    width: float = 0.008,
) -> None:
    """Draw a thin horizontal rule from (x_start, y) to (x_end, y)."""
    pdf.set_draw_color(*color)
    pdf.set_line_width(width)
    pdf.line(x_start, y, x_end, y)


def draw_flourish_rule(
    pdf: FPDF,
    x_center: float,
    y: float,
    half_width: float,
    color: RGB,
    rule_width: float = 0.01,
    diamond_size: float = 0.06,
) -> None:
    """Draw a horizontal rule with a centered filled diamond.

    Layout:  ─────◆─────
    - Rule extends from (x_center - half_width, y) to (x_center + half_width, y),
      BUT the diamond area in the middle is skipped so the rule visibly breaks around it.
    - Diamond is centered on (x_center, y), size `diamond_size` controls the half-extent.
    """
    pdf.set_draw_color(*color)
    pdf.set_fill_color(*color)
    pdf.set_line_width(rule_width)

    # Left half of rule, ending just before the diamond
    pdf.line(
        x_center - half_width, y,
        x_center - diamond_size - 0.02, y,
    )
    # Right half of rule, starting just after the diamond
    pdf.line(
        x_center + diamond_size + 0.02, y,
        x_center + half_width, y,
    )

    # Diamond (4-point polygon, filled)
    pdf.polygon(
        [
            (x_center, y - diamond_size),
            (x_center + diamond_size, y),
            (x_center, y + diamond_size),
            (x_center - diamond_size, y),
        ],
        style="F",
    )


def draw_panel_border(
    pdf: FPDF,
    x: float,
    y: float,
    w: float,
    h: float,
    color: RGB,
    outer_width: float = 0.02,
    inner_width: float = 0.01,
    gap: float = 0.015,
) -> None:
    """Draw a double-line border: outer rectangle + inner rectangle inset by `gap`."""
    pdf.set_draw_color(*color)

    # Outer rect
    pdf.set_line_width(outer_width)
    pdf.rect(x, y, w, h, style="D")

    # Inner rect inset by `gap`
    pdf.set_line_width(inner_width)
    pdf.rect(x + gap, y + gap, w - 2 * gap, h - 2 * gap, style="D")
