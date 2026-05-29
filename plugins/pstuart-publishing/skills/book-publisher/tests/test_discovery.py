"""Tests for bookpub.discovery — page-count detection + cover consistency guard."""
import pytest
from fpdf import FPDF

from bookpub.discovery import (
    assert_cover_matches_interior,
    detect_page_count,
    expected_wrap_width_in,
    find_latest_pdf,
    kdp_paperback_manifest,
)
from bookpub.pdf_engine import build_pdf, parse_manuscript

MD = "# CHAPTER 1\n## One\n\nBody.\n\n# CHAPTER 2\n## Two\n\nMore body.\n"


def _interior(tmp_path):
    out = tmp_path / "interior.pdf"
    stats = build_pdf({"title": "T", "author": "A", "year": "2026"},
                      parse_manuscript(MD), out)
    return out, stats["pages"]


def test_detect_page_count(tmp_path):
    out, pages = _interior(tmp_path)
    assert detect_page_count(out) == pages


def test_find_latest_pdf(tmp_path):
    (tmp_path / "a.pdf").write_bytes(b"%PDF-1.4")
    import os, time
    time.sleep(0.01)
    (tmp_path / "b.pdf").write_bytes(b"%PDF-1.4")
    latest = find_latest_pdf(tmp_path)
    assert latest.name == "b.pdf"


def _fake_wrap(tmp_path, width_in):
    pdf = FPDF(unit="in", format=(width_in, 8.75))
    pdf.add_page()
    out = tmp_path / f"wrap_{width_in:.3f}.pdf"
    pdf.output(str(out))
    return out


def test_cover_matches_interior_passes_when_consistent(tmp_path):
    interior, pages = _interior(tmp_path)
    wrap = _fake_wrap(tmp_path, expected_wrap_width_in(pages, "white"))
    res = assert_cover_matches_interior(wrap, interior, paper="white")
    assert res["pages"] == pages


def test_cover_matches_interior_raises_on_drift(tmp_path):
    interior, pages = _interior(tmp_path)
    # a wrap sized for 999 pages will not match a tiny interior
    wrap = _fake_wrap(tmp_path, expected_wrap_width_in(999, "white"))
    with pytest.raises(AssertionError):
        assert_cover_matches_interior(wrap, interior, paper="white")


def test_kdp_manifest_lists_separate_files():
    m = kdp_paperback_manifest("interior.pdf", "wrap.pdf", "k.jpg", "b.epub")
    assert m["paperback_interior"] == "interior.pdf"
    assert m["paperback_cover"] == "wrap.pdf"
    assert "_with_covers" not in str(m)  # the merged proof is never a deliverable
