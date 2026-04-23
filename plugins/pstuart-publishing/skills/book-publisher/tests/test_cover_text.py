"""Tests for fpdf2 vector text helpers (integration)."""
from pathlib import Path
from fpdf import FPDF
from pypdf import PdfReader
from templates.lib.cover_text import (
    draw_centered_text,
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
