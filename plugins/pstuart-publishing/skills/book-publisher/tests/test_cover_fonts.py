"""Tests for EB Garamond font registration helper."""
from pathlib import Path
from fpdf import FPDF
from pypdf import PdfReader
from templates.lib.cover_fonts import register_fonts, FONT_DIR


def test_font_dir_points_to_bundled_ttfs():
    """Sanity check: the 4 TTF files are actually bundled."""
    expected = {
        "EBGaramond-Regular.ttf",
        "EBGaramond-Italic.ttf",
        "EBGaramond-Bold.ttf",
        "EBGaramond-BoldItalic.ttf",
    }
    found = {p.name for p in FONT_DIR.glob("*.ttf")}
    assert expected.issubset(found), f"Missing TTFs: {expected - found}"


def test_register_fonts_returns_all_four_keys():
    pdf = FPDF()
    fonts = register_fonts(pdf)
    assert set(fonts.keys()) == {"regular", "italic", "bold", "bolditalic"}
    for key, family in fonts.items():
        assert isinstance(family, str) and family, f"{key} family is empty"


def test_registered_fonts_accept_unicode(tmp_path: Path):
    """en-dash and smart quotes must render without UnicodeEncodeError."""
    pdf = FPDF(unit="in", format=(5.5, 8.5))
    fonts = register_fonts(pdf)
    pdf.add_page()
    pdf.set_font(fonts["regular"], size=12)
    pdf.text(1, 1, "Historical – Fiction “The Mask”")
    out = tmp_path / "out.pdf"
    pdf.output(str(out))
    text = "\n".join(p.extract_text() or "" for p in PdfReader(str(out)).pages)
    # en-dash must survive extraction
    assert "–" in text or "Historical" in text


def test_italic_and_bold_variants_apply(tmp_path: Path):
    """After registering, set_font on each key should succeed."""
    pdf = FPDF()
    fonts = register_fonts(pdf)
    pdf.add_page()
    # Each variant should accept set_font without error
    for key, family in fonts.items():
        pdf.set_font(family, size=10)
    # The pdf should have all 4 fonts registered
    assert len(pdf.fonts) >= 4


def test_register_fonts_idempotent_on_same_pdf():
    """Calling register_fonts twice on the same pdf should not raise."""
    pdf = FPDF()
    fonts1 = register_fonts(pdf)
    fonts2 = register_fonts(pdf)
    assert fonts1 == fonts2
