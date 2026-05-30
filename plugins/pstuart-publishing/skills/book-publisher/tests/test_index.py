"""Tests for bookpub.index + the clickable in-document index."""
from pypdf import PdfReader

from bookpub.index import (
    compress_ranges,
    find_term_pages,
    format_ranges,
    over_broad_terms,
)
from bookpub.pdf_engine import build_pdf, parse_manuscript
from bookpub.qa_report import _count_outline


def test_word_boundary_matching_avoids_substrings():
    pages = ["Bonds are great and bonds rule", "abandon the bondsman", "stocks only here"]
    res = find_term_pages(pages, ["bonds", "stocks", "bond"])
    assert res["bonds"] == [1]      # not page 2 ("bondsman")
    assert res["stocks"] == [3]
    assert "bond" not in res        # \b stops "bond" matching "bonds"


def test_compress_ranges():
    assert compress_ranges([1, 2, 3, 5, 7, 8]) == [(1, 3), (5, 5), (7, 8)]
    assert compress_ranges([4, 2, 2, 3]) == [(2, 4)]


def test_format_ranges():
    assert format_ranges([(1, 3), (5, 5), (7, 8)]) == "1-3, 5, 7-8"


def test_over_broad_terms():
    idx = {"common": [1, 2, 3, 4, 5], "rare": [3]}
    assert over_broad_terms(idx, n_pages=10, threshold=0.15) == ["common"]


def test_build_pdf_with_clickable_index(tmp_path):
    md = "# CHAPTER 1\n## Money\n\nSavings and budgets matter. More about savings here.\n"
    out = tmp_path / "book.pdf"
    stats = build_pdf({"title": "T", "author": "A", "year": "2026"},
                      parse_manuscript(md), out, index_terms=["savings", "budgets"])
    assert stats["index_terms"] >= 1
    reader = PdfReader(str(out))
    # "Index" appears in the outline
    names = []

    def _names(o):
        for it in o:
            if isinstance(it, list):
                _names(it)
            else:
                names.append(str(it.title))
    _names(reader.outline)
    assert any("Index" in n for n in names)
    # index page references are real link annotations
    links = sum(
        1 for pg in reader.pages for ref in (pg.get("/Annots") or [])
        if ref.get_object().get("/Subtype") == "/Link"
    )
    assert links >= 1
    assert _count_outline(reader.outline) >= 2  # chapter + Index
