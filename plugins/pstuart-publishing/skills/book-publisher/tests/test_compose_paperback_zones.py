"""Tests for paperback zone-rendering helpers (front / back / spine)."""
from pathlib import Path
import sys
from fpdf import FPDF
from pypdf import PdfReader
from PIL import Image


def _import_helpers():
    root = Path(__file__).parent.parent
    for p in (root, root / "templates"):
        if str(p) not in sys.path:
            sys.path.insert(0, str(p))
    from templates.compose_paperback_wrap_template import (
        _render_front_panel,
        _render_back_panel,
        _render_spine,
    )
    from lib.cover_fonts import register_fonts
    from lib.cover_style import resolve_colors
    from lib.cover_dimensions import panel_offsets_inches, wrap_canvas_inches
    from lib.cover_config import validate_and_defaults
    return (
        _render_front_panel, _render_back_panel, _render_spine,
        register_fonts, resolve_colors, panel_offsets_inches, wrap_canvas_inches,
        validate_and_defaults,
    )


def _mkpdf(wrap_w, wrap_h):
    pdf = FPDF(unit="in", format=(wrap_w, wrap_h))
    pdf.set_auto_page_break(auto=False)
    pdf.add_page()
    return pdf


def _extract(pdf_path: Path) -> str:
    reader = PdfReader(str(pdf_path))
    return "\n".join(p.extract_text() or "" for p in reader.pages)


def _base_config(**overrides):
    cfg = {
        "title": "The Mask",
        "author": "Patrick Stuart",
        "page_count": 200,
        "paper_type": "white",
        "style_preset": "burgundy_cream",
        "background_tone": "light_bg",
    }
    cfg.update(overrides)
    return cfg


def test_front_panel_renders_title_and_author(tmp_path: Path):
    (fp, _bp, _sp, reg, rc, po, wc, v) = _import_helpers()
    config = v(_base_config(subtitle="1585 - 1601", series_line_front="A Novel of Elizabethan England"))
    wrap_w, wrap_h = wc(config["page_count"], config["paper_type"])
    offsets = po(config["page_count"], config["paper_type"])
    pdf = _mkpdf(wrap_w, wrap_h)
    reg(pdf)
    colors = rc(config["style_preset"], tone=config["background_tone"])
    fp(pdf, config, offsets, wrap_h, colors, {})
    out = tmp_path / "front.pdf"
    pdf.output(str(out))
    text = _extract(out)
    assert "THE MASK" in text
    assert "PATRICK STUART" in text.upper() or "BY PATRICK STUART" in text.upper()
    assert "1585 - 1601" in text
    assert "Elizabethan England" in text


def test_front_panel_with_custom_byline(tmp_path: Path):
    (fp, _bp, _sp, reg, rc, po, wc, v) = _import_helpers()
    config = v(_base_config(byline="A NOVEL BY P. STUART"))
    wrap_w, wrap_h = wc(config["page_count"], config["paper_type"])
    offsets = po(config["page_count"], config["paper_type"])
    pdf = _mkpdf(wrap_w, wrap_h)
    reg(pdf)
    colors = rc(config["style_preset"], tone=config["background_tone"])
    fp(pdf, config, offsets, wrap_h, colors, {})
    out = tmp_path / "front_byline.pdf"
    pdf.output(str(out))
    assert "A NOVEL BY P. STUART" in _extract(out)


def test_back_panel_renders_all_zones(tmp_path: Path):
    (_fp, bp, _sp, reg, rc, po, wc, v) = _import_helpers()
    config = v(_base_config(
        genre_line="A Historical Conspiracy Thriller",
        back_tagline="A playwright who never existed.",
        quote="A thrilling debut.", quote_attribution="BookReviewer",
        blurb=["Paragraph one of blurb.", "", "Paragraph two of blurb."],
        author_bio="Patrick Stuart lives in the PNW.",
        isbn="9780000000002",
        price_us="$18.99",
        publisher="Stuart Press",
        publisher_city="Seattle",
        series_line_back="The Folio Conspiracy · Book I",
    ))
    wrap_w, wrap_h = wc(config["page_count"], config["paper_type"])
    offsets = po(config["page_count"], config["paper_type"])
    pdf = _mkpdf(wrap_w, wrap_h)
    reg(pdf)
    colors = rc(config["style_preset"], tone=config["background_tone"])
    bp(pdf, config, offsets, wrap_h, colors, {}, tmp_path)
    out = tmp_path / "back.pdf"
    pdf.output(str(out))
    text = _extract(out)
    for expected in [
        "Historical Conspiracy",
        "playwright who never existed",
        "A thrilling debut",
        "BookReviewer",
        "Paragraph one",
        "Paragraph two",
        "Patrick Stuart lives",
        "$18.99",
        "Stuart Press",
        "Folio Conspiracy",
    ]:
        assert expected in text, f"missing zone content: {expected!r} not in extracted text"


def test_back_panel_minimal_config_no_crash(tmp_path: Path):
    """With no optional fields, back panel renders without crashing."""
    (_fp, bp, _sp, reg, rc, po, wc, v) = _import_helpers()
    config = v(_base_config())
    wrap_w, wrap_h = wc(config["page_count"], config["paper_type"])
    offsets = po(config["page_count"], config["paper_type"])
    pdf = _mkpdf(wrap_w, wrap_h)
    reg(pdf)
    colors = rc(config["style_preset"], tone=config["background_tone"])
    bp(pdf, config, offsets, wrap_h, colors, {}, tmp_path)
    out = tmp_path / "back_min.pdf"
    pdf.output(str(out))
    # No assertion on content — just that it didn't crash


def test_back_panel_with_author_photo(tmp_path: Path):
    """If author_photo points at a real file, it should be embedded without crashing."""
    photo = tmp_path / "photo.png"
    Image.new("RGB", (100, 120), color=(128, 128, 128)).save(photo)
    (_fp, bp, _sp, reg, rc, po, wc, v) = _import_helpers()
    config = v(_base_config(
        author_bio="One line bio.", author_photo=str(photo),
    ))
    wrap_w, wrap_h = wc(config["page_count"], config["paper_type"])
    offsets = po(config["page_count"], config["paper_type"])
    pdf = _mkpdf(wrap_w, wrap_h)
    reg(pdf)
    colors = rc(config["style_preset"], tone=config["background_tone"])
    bp(pdf, config, offsets, wrap_h, colors, {}, tmp_path)
    out = tmp_path / "back_photo.pdf"
    pdf.output(str(out))
    # Just ensure it didn't crash on image embedding


def test_spine_renders_title_and_author(tmp_path: Path):
    (_fp, _bp, sp, reg, rc, po, wc, v) = _import_helpers()
    config = v(_base_config())
    wrap_w, wrap_h = wc(config["page_count"], config["paper_type"])
    offsets = po(config["page_count"], config["paper_type"])
    pdf = _mkpdf(wrap_w, wrap_h)
    reg(pdf)
    colors = rc(config["style_preset"], tone=config["background_tone"])
    sp(pdf, config, offsets, wrap_h, colors, {})
    out = tmp_path / "spine.pdf"
    pdf.output(str(out))
    text = _extract(out)
    # Spine fires for 200 white pages = ~0.45" — above the 0.0625" minimum
    assert "The Mask" in text
    assert "Patrick Stuart" in text


def test_spine_with_imprint(tmp_path: Path):
    (_fp, _bp, sp, reg, rc, po, wc, v) = _import_helpers()
    # Need >= 0.5" spine for imprint to render: 0.5 / 0.002252 ≈ 222 pages minimum
    config = v(_base_config(page_count=250, imprint="STUART PRESS"))
    wrap_w, wrap_h = wc(config["page_count"], config["paper_type"])
    offsets = po(config["page_count"], config["paper_type"])
    pdf = _mkpdf(wrap_w, wrap_h)
    reg(pdf)
    colors = rc(config["style_preset"], tone=config["background_tone"])
    sp(pdf, config, offsets, wrap_h, colors, {})
    out = tmp_path / "spine_imp.pdf"
    pdf.output(str(out))
    text = _extract(out)
    assert "The Mask" in text
    assert "STUART PRESS" in text
