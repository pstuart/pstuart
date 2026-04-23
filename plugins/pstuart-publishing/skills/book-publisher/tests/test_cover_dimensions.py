"""Tests for cover dimension calculations."""
import pytest
from templates.lib.cover_dimensions import (
    spine_width_inches,
    wrap_canvas_inches,
    panel_offsets_inches,
    PAPER_THICKNESS,
    BLEED_INCHES,
    TRIM_WIDTH_INCHES,
    TRIM_HEIGHT_INCHES,
)


def test_white_paper_spine_200_pages():
    assert spine_width_inches(200, "white") == pytest.approx(0.4504, rel=1e-4)


def test_cream_paper_spine_300_pages():
    assert spine_width_inches(300, "cream") == pytest.approx(0.7500, rel=1e-4)


def test_unknown_paper_type_raises():
    with pytest.raises(ValueError, match="paper_type"):
        spine_width_inches(200, "glossy")


def test_wrap_canvas_200_pages_white():
    w, h = wrap_canvas_inches(200, "white")
    # 2 * (5.5 + 0.125) + 0.4504 = 11.7004
    assert w == pytest.approx(11.7004, rel=1e-4)
    # 8.5 + 2 * 0.125 = 8.75
    assert h == pytest.approx(8.75, rel=1e-4)


def test_panel_offsets_split_wrap_correctly():
    offsets = panel_offsets_inches(200, "white")
    # Back: starts at 0, ends at BLEED + TRIM_WIDTH = 5.625
    assert offsets["back_start"] == pytest.approx(0.0, rel=1e-4)
    assert offsets["back_end"] == pytest.approx(5.625, rel=1e-4)
    # Spine: 5.625 to 5.625 + 0.4504 = 6.0754
    assert offsets["spine_start"] == pytest.approx(5.625, rel=1e-4)
    assert offsets["spine_end"] == pytest.approx(6.0754, rel=1e-4)
    # Front: 6.0754 to wrap_width
    assert offsets["front_start"] == pytest.approx(6.0754, rel=1e-4)
    assert offsets["front_end"] == pytest.approx(11.7004, rel=1e-4)
