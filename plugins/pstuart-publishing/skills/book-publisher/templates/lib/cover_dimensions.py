"""Pure-function cover dimension calculations.

Trade paperback 5.5 x 8.5 at 300 DPI. All public functions return inches
and are pure — no I/O, no config reads.
"""
from typing import Literal, TypedDict

TRIM_WIDTH_INCHES = 5.5
TRIM_HEIGHT_INCHES = 8.5
BLEED_INCHES = 0.125
SAFE_MARGIN_INCHES = 0.25

# Amazon KDP published paper-thickness constants.
PAPER_THICKNESS = {
    "white": 0.002252,
    "cream": 0.002500,
}

PaperType = Literal["white", "cream"]


class PanelOffsets(TypedDict):
    back_start: float
    back_end: float
    spine_start: float
    spine_end: float
    front_start: float
    front_end: float


def spine_width_inches(page_count: int, paper_type: PaperType) -> float:
    """Compute spine width in inches from page count and paper type."""
    if paper_type not in PAPER_THICKNESS:
        raise ValueError(
            f"Unknown paper_type {paper_type!r}. "
            f"Expected one of: {sorted(PAPER_THICKNESS)}"
        )
    return page_count * PAPER_THICKNESS[paper_type]


def wrap_canvas_inches(
    page_count: int, paper_type: PaperType
) -> tuple[float, float]:
    """Return (width, height) of full wrap canvas in inches, including bleed."""
    spine = spine_width_inches(page_count, paper_type)
    width = 2 * (TRIM_WIDTH_INCHES + BLEED_INCHES) + spine
    height = TRIM_HEIGHT_INCHES + 2 * BLEED_INCHES
    return (width, height)


def panel_offsets_inches(
    page_count: int, paper_type: PaperType
) -> PanelOffsets:
    """Compute x-axis offsets for each wrap panel in inches.

    Panels laid out left-to-right when cover is flat: BACK | SPINE | FRONT.
    """
    spine = spine_width_inches(page_count, paper_type)
    wrap_w, _ = wrap_canvas_inches(page_count, paper_type)

    back_start = 0.0
    back_end = BLEED_INCHES + TRIM_WIDTH_INCHES
    spine_start = back_end
    spine_end = spine_start + spine
    front_start = spine_end
    front_end = wrap_w

    return {
        "back_start": back_start,
        "back_end": back_end,
        "spine_start": spine_start,
        "spine_end": spine_end,
        "front_start": front_start,
        "front_end": front_end,
    }
