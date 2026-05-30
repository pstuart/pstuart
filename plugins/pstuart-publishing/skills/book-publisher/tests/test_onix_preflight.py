"""Tests for bookpub.onix + bookpub.preflight."""
import shutil
import xml.etree.ElementTree as ET

import pytest

from bookpub.onix import generate_onix
from bookpub.preflight import convert_to_cmyk, preflight

CFG = {
    "title": "Sample", "subtitle": "Sub", "author": "Test Author", "slug": "sample",
    "publisher": "Stuart Press", "language": "eng", "year": "2026",
    "description": "A test book.", "bisac": ["BUS000000"], "keywords": ["money"],
    "prices": {"USD": "24.99"},
    "isbn": {"paperback": "978-1-2345-6789-7", "ebook": "978-1-2345-6788-0"},
}


def test_onix_is_well_formed_with_per_format_products():
    xml = generate_onix(CFG)
    root = ET.fromstring(xml)
    assert root.tag == "ONIXMessage"
    products = root.findall("Product")
    assert len(products) == 2  # paperback + ebook
    ids = [p.findtext("ProductIdentifier/IDValue") for p in products]
    assert "9781234567897" in ids and "9781234567880" in ids
    assert "BUS000000" in xml
    assert "24.99" in xml


def test_onix_omits_formats_without_isbn():
    cfg = {**CFG, "isbn": {"paperback": "978-1-2345-6789-7"}}
    root = ET.fromstring(generate_onix(cfg))
    assert len(root.findall("Product")) == 1


@pytest.mark.skipif(shutil.which("gs") is None, reason="Ghostscript not installed")
def test_convert_to_cmyk(tmp_path):
    # build a tiny interior to convert
    from bookpub.build_book import build_book
    (tmp_path / "book.toml").write_text(
        'title="T"\nauthor="A"\nyear="2026"\nmanuscript="m.md"\n')
    (tmp_path / "m.md").write_text("# CHAPTER 1\n## One\n\nBody.\n")
    res = build_book(tmp_path / "book.toml", tmp_path / "out")
    cmyk = convert_to_cmyk(res["interior"], tmp_path / "cmyk.pdf")
    assert cmyk["ok"]
    assert (tmp_path / "cmyk.pdf").exists()


@pytest.mark.skipif(shutil.which("epubcheck") is None, reason="epubcheck not installed")
def test_preflight_reports_epub_valid(tmp_path):
    from bookpub.build_book import build_book
    (tmp_path / "book.toml").write_text(
        'title="T"\nauthor="A"\nyear="2026"\nmanuscript="m.md"\n')
    (tmp_path / "m.md").write_text("# CHAPTER 1\n## One\n\nBody.\n")
    res = build_book(tmp_path / "book.toml", tmp_path / "out")
    rep = preflight(res["interior"], res["epub"], tmp_path / "pf")
    names = {n: s for n, s, _ in rep.checks}
    assert names.get("epub.epubcheck") == "PASS"
