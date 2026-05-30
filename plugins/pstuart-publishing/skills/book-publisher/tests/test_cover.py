"""Tests for bookpub.cover — Kindle + paperback-wrap composition."""
from PIL import Image
from pypdf import PdfReader

from bookpub.cover import build_kindle_cover, build_paperback_wrap

CFG = {"title": "Test Title", "subtitle": "A Subtitle", "author": "An Author",
       "style_preset": "navy_gold", "description": "A short blurb for the back cover.",
       "trim_inches": [5.5, 8.5]}


def _art(tmp_path):
    p = tmp_path / "front.png"
    Image.new("RGB", (1200, 1800), (20, 40, 70)).save(p)
    return p


def test_kindle_cover_dimensions(tmp_path):
    out = build_kindle_cover(_art(tmp_path), CFG, tmp_path / "k.jpg")
    im = Image.open(out)
    assert im.size == (1600, 2560)
    assert im.format == "JPEG"


def test_paperback_wrap_dimensions_and_spine(tmp_path):
    res = build_paperback_wrap(_art(tmp_path), CFG, 200, tmp_path / "w.pdf", paper="white")
    expected_w = 2 * (5.5 + 0.125) + 200 * 0.002252
    assert abs(res["wrap_in"][0] - expected_w) < 0.001
    assert res["wrap_in"][1] == 8.75
    assert res["spine_text"] is True  # >= 100 pages
    # the PDF mediabox matches the computed wrap size
    page = PdfReader(str(tmp_path / "w.pdf")).pages[0]
    assert abs(float(page.mediabox.width) / 72.0 - expected_w) < 0.01


def test_paperback_wrap_no_spine_text_under_100pp(tmp_path):
    res = build_paperback_wrap(_art(tmp_path), CFG, 60, tmp_path / "w.pdf")
    assert res["spine_text"] is False


def test_wrap_vector_text_present(tmp_path):
    import shutil
    import subprocess
    build_paperback_wrap(_art(tmp_path), CFG, 200, tmp_path / "w.pdf")
    if shutil.which("pdftotext"):
        txt = subprocess.run(["pdftotext", str(tmp_path / "w.pdf"), "-"],
                             capture_output=True, text=True).stdout
        assert "TEST TITLE" in txt.upper()
        assert "An Author" in txt or "AUTHOR" in txt.upper()
