"""Tests for fpdf2 vector text helpers (integration)."""
from pathlib import Path
from fpdf import FPDF
from pypdf import PdfReader
from templates.lib.cover_text import (
    draw_centered_text,
    draw_italic_block,
    draw_bold_text,
    draw_left_aligned_block,
    draw_spine_text,
)


def _extract_text(pdf_path: Path) -> str:
    reader = PdfReader(str(pdf_path))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def test_centered_text_appears_in_extracted_pdf(tmp_path: Path):
    pdf = FPDF(unit="in", format=(5.5, 8.5))
    pdf.add_page()
    draw_centered_text(
        pdf, text="TEST TITLE", x_center=2.75, y=4.0, size_pt=32,
        color=(255, 255, 255),
    )
    out = tmp_path / "out.pdf"
    pdf.output(str(out))
    assert "TEST TITLE" in _extract_text(out)


def test_left_block_wraps_and_survives_to_pdf(tmp_path: Path):
    pdf = FPDF(unit="in", format=(5.5, 8.5))
    pdf.add_page()
    draw_left_aligned_block(
        pdf,
        lines=["First line of back cover copy.", "Second line."],
        x=0.5, y=2.0, size_pt=10,
        color=(20, 20, 20), line_height_in=0.18,
    )
    out = tmp_path / "out.pdf"
    pdf.output(str(out))
    text = _extract_text(out)
    assert "First line" in text
    assert "Second line" in text


def test_spine_text_survives_when_spine_wide_enough(tmp_path: Path):
    pdf = FPDF(unit="in", format=(12, 8.75))
    pdf.add_page()
    draw_spine_text(
        pdf, text="SAMPLE TITLE / Author Name",
        spine_start_x=5.625, spine_width=0.5, wrap_height=8.75,
        size_pt=10, color=(255, 255, 255),
    )
    out = tmp_path / "out.pdf"
    pdf.output(str(out))
    assert "SAMPLE TITLE" in _extract_text(out)


# ---- Font-aware tests (added in T6) ----

from templates.lib.cover_fonts import register_fonts


def test_font_key_defaults_to_regular_and_uses_helvetica_when_unregistered(tmp_path: Path):
    """Without register_fonts, falls back to core Helvetica."""
    pdf = FPDF(unit="in", format=(5.5, 8.5))
    pdf.add_page()
    # no register_fonts call
    draw_centered_text(
        pdf, text="TEST TITLE", x_center=2.75, y=4.0, size_pt=32,
        color=(255, 255, 255),
    )
    # Should work with Helvetica (no UnicodeEncodeError for ASCII-only text)
    out = tmp_path / "helv.pdf"
    pdf.output(str(out))
    assert "TEST TITLE" in _extract_text(out)


def test_registered_ebg_enables_unicode(tmp_path: Path):
    """With fonts registered, en-dash renders without error."""
    pdf = FPDF(unit="in", format=(5.5, 8.5))
    register_fonts(pdf)
    pdf.add_page()
    draw_centered_text(
        pdf, text="Historical – Fiction", x_center=2.75, y=4.0, size_pt=18,
        color=(80, 20, 30),
        font_key="regular",
    )
    out = tmp_path / "unicode.pdf"
    pdf.output(str(out))
    text = _extract_text(out)
    assert "–" in text, f"en-dash not found: {text!r}"


def test_italic_block_uses_italic_variant(tmp_path: Path):
    pdf = FPDF(unit="in", format=(5.5, 8.5))
    register_fonts(pdf)
    pdf.add_page()
    draw_italic_block(
        pdf, lines=["First italic line.", "Second italic line."],
        x=0.5, y=1.0, size_pt=12, color=(60, 40, 30), line_height_in=0.2,
    )
    out = tmp_path / "italic.pdf"
    pdf.output(str(out))
    text = _extract_text(out)
    assert "First italic line." in text
    assert "Second italic line." in text


def test_bold_text_uses_bold_variant(tmp_path: Path):
    pdf = FPDF(unit="in", format=(5.5, 8.5))
    register_fonts(pdf)
    pdf.add_page()
    draw_bold_text(
        pdf, text="BOLD TITLE", x_center=2.75, y=2.0, size_pt=24,
        color=(80, 20, 30),
    )
    out = tmp_path / "bold.pdf"
    pdf.output(str(out))
    text = _extract_text(out)
    assert "BOLD TITLE" in text


def test_unknown_font_key_raises():
    import pytest
    pdf = FPDF()
    pdf.add_page()
    with pytest.raises(ValueError, match="font_key"):
        draw_centered_text(
            pdf, text="hi", x_center=1, y=1, size_pt=10,
            color=(0, 0, 0), font_key="made_up",
        )
