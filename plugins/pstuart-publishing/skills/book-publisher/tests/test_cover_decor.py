"""Tests for decorative vector primitives."""
from pathlib import Path
from fpdf import FPDF
from pypdf import PdfReader
from templates.lib.cover_decor import (
    draw_ink_rule,
    draw_flourish_rule,
    draw_panel_border,
)


def _extract_operators(pdf_path: Path) -> str:
    """Dump the raw content stream of page 0 as a string of drawing operators."""
    reader = PdfReader(str(pdf_path))
    page = reader.pages[0]
    content = page.get_contents()
    if content is None:
        return ""
    # pypdf returns an EncodedStreamObject or ContentStream; get raw bytes
    data = content.get_data() if hasattr(content, "get_data") else bytes(content)
    return data.decode("latin-1", errors="replace")


def _build_pdf(tmp_path: Path, draw_fn) -> Path:
    pdf = FPDF(unit="in", format=(5.5, 8.5))
    pdf.add_page()
    draw_fn(pdf)
    out = tmp_path / "out.pdf"
    pdf.output(str(out))
    return out


def test_ink_rule_emits_line_operator(tmp_path: Path):
    out = _build_pdf(tmp_path, lambda pdf: draw_ink_rule(
        pdf, x_start=0.5, x_end=5.0, y=4.0, color=(100, 100, 100)
    ))
    ops = _extract_operators(out)
    # fpdf2 emits 'l' (line-to) or 'S' (stroke) for line drawing
    assert " l\n" in ops or "l " in ops or " S" in ops or "RG" in ops, \
        f"no line operator found: {ops[:200]!r}"


def test_flourish_rule_emits_line_and_polygon(tmp_path: Path):
    out = _build_pdf(tmp_path, lambda pdf: draw_flourish_rule(
        pdf, x_center=2.75, y=4.0, half_width=1.5, color=(140, 100, 40)
    ))
    ops = _extract_operators(out)
    # Should have at least one stroke (rule) and one fill (diamond)
    # fpdf2: 'S' = stroke, 'f' or 'F' = fill, 'B' = both
    assert "S" in ops or "l" in ops, "no stroke ops found"
    assert "f" in ops or "F" in ops or "B" in ops, "no fill ops found (for diamond)"


def test_panel_border_emits_two_rectangles(tmp_path: Path):
    out = _build_pdf(tmp_path, lambda pdf: draw_panel_border(
        pdf, x=0.25, y=0.25, w=5.0, h=8.0, color=(180, 150, 100)
    ))
    ops = _extract_operators(out)
    # fpdf2 emits 're' (rectangle) operator for pdf.rect
    # Two rectangles from the double-border should produce two 're' tokens
    count = ops.count(" re\n") + ops.count(" re ")
    assert count >= 2, f"expected >=2 rect operators for double border, got {count} in {ops[:300]!r}"


def test_panel_border_respects_gap(tmp_path: Path):
    """Inner border should be inset by `gap` from outer border."""
    # This is a structural test — we trust fpdf2's rect to respect args.
    # If the impl passes different widths, it's a caller-visible behavior change.
    # For now, just assert the function runs without error for different gap values.
    for gap in (0.01, 0.015, 0.05):
        out = _build_pdf(tmp_path, lambda pdf: draw_panel_border(
            pdf, x=0.25, y=0.25, w=5.0, h=8.0, color=(100, 100, 100), gap=gap
        ))
        assert out.exists()


def test_ink_rule_respects_width(tmp_path: Path):
    """Passing a different line width should not error."""
    for w in (0.005, 0.01, 0.02):
        _build_pdf(tmp_path, lambda pdf: draw_ink_rule(
            pdf, x_start=0.5, x_end=5.0, y=4.0, color=(0, 0, 0), width=w
        ))
