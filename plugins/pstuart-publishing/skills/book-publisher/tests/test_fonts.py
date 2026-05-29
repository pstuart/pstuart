"""Tests for bookpub.fonts — portable, fail-loud font registration."""
import pytest
from fpdf import FPDF

from bookpub.fonts import (
    FontError,
    MONO_FAMILY,
    SERIF_FAMILY,
    register_fonts,
    register_mono,
    register_serif,
)


def test_register_serif_registers_all_variants():
    pdf = FPDF()
    fam = register_serif(pdf)
    assert fam == SERIF_FAMILY
    for style in ("", "B", "I", "BI"):
        assert f"{SERIF_FAMILY}{style}" in pdf.fonts


def test_register_serif_is_idempotent():
    pdf = FPDF()
    register_serif(pdf)
    register_serif(pdf)  # must not raise or duplicate
    assert f"{SERIF_FAMILY}B" in pdf.fonts


def test_register_serif_fails_loud_when_font_missing(tmp_path):
    pdf = FPDF()
    with pytest.raises(FontError):
        register_serif(pdf, font_dir_override=tmp_path)  # empty dir


def test_register_mono_fails_loud_until_shipped():
    # The mono TTF ships in Phase 2; until then this must fail loudly rather
    # than silently emit a non-embedded core Courier.
    pdf = FPDF()
    with pytest.raises(FontError):
        register_mono(pdf)


def test_register_fonts_serif_only_by_default():
    pdf = FPDF()
    fams = register_fonts(pdf)
    assert fams == {"serif": SERIF_FAMILY}
    assert MONO_FAMILY not in pdf.fonts
