"""Tests for bookpub.pdf_engine — clickable TOC links + bookmark outline."""
from pypdf import PdfReader

from bookpub.pdf_engine import build_pdf, parse_manuscript
from bookpub.qa_report import _count_outline

MANUSCRIPT = """\
# PART I: Foundations

*Where everything begins*

# CHAPTER 1
## The First Idea

This is the opening paragraph -- it uses a double hyphen that should become a
real em-dash, plus a real em-dash—right here.

## A Section Heading

Some more prose with a list:

- first item
- second item

> A quoted line of wisdom.

# CHAPTER 2
## The Second Idea

Body text for chapter two.

### A subsection

```
code stays verbatim --flag
```
"""

CONFIG = {
    "title": "Test Book",
    "subtitle": "A Fixture",
    "author": "Test Author",
    "year": "2026",
    "isbn": "978-1-2345-6789-7",
    "dedication": "For the test suite.",
}


def _build(tmp_path):
    elements = parse_manuscript(MANUSCRIPT)
    stats = build_pdf(CONFIG, elements, tmp_path / "book.pdf")
    return stats, PdfReader(str(tmp_path / "book.pdf"))


def test_parse_manuscript_structure():
    els = parse_manuscript(MANUSCRIPT)
    kinds = [e["kind"] for e in els]
    assert kinds == ["part", "chapter", "chapter"]
    assert els[1]["title"] == "The First Idea"  # H2 promoted to chapter title
    assert els[0]["subtitle"] == "Where everything begins"


def test_build_returns_stats(tmp_path):
    stats, _ = _build(tmp_path)
    assert stats["chapters"] == 2
    assert stats["parts"] == 1
    assert stats["pages"] >= 5


def test_pdf_has_clickable_toc_links(tmp_path):
    _, reader = _build(tmp_path)
    links = sum(
        1
        for pg in reader.pages
        for ref in (pg.get("/Annots") or [])
        if ref.get_object().get("/Subtype") == "/Link"
    )
    # >= one clickable entry per chapter (TOC links to each chapter/part/section)
    assert links >= 2, f"expected clickable TOC links, found {links}"


def test_pdf_has_bookmark_outline(tmp_path):
    _, reader = _build(tmp_path)
    n = _count_outline(reader.outline)
    # part + 2 chapters + sections all register in the outline
    assert n >= 3, f"expected bookmark outline entries, found {n}"


def test_pdf_links_point_to_real_pages(tmp_path):
    _, reader = _build(tmp_path)
    npages = len(reader.pages)
    seen_dest = False
    for pg in reader.pages:
        for ref in (pg.get("/Annots") or []):
            o = ref.get_object()
            if o.get("/Subtype") == "/Link":
                dest = o.get("/Dest") or (o.get("/A") or {}).get("/D")
                seen_dest = seen_dest or dest is not None
    assert seen_dest, "link annotations must carry a destination"
    assert npages >= 5
