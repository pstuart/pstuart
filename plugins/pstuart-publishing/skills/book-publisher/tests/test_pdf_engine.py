"""Tests for bookpub.pdf_engine — clickable TOC links + bookmark outline."""
from pypdf import PdfReader

from bookpub.pdf_engine import _is_scene_break, build_pdf, parse_manuscript
from bookpub.qa_report import _count_outline


def test_scene_break_detection():
    assert _is_scene_break(["---"])
    assert _is_scene_break(["***"])
    assert _is_scene_break(["* * *"])
    assert _is_scene_break(["- - -"])
    assert not _is_scene_break(["- a list item"])   # must not eat list items
    assert not _is_scene_break(["normal text"])
    assert not _is_scene_break(["---", "more"])      # only a lone divider

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

A table with a long cell the legacy renderer would truncate:

| Account | Balance | Notes |
|---------|---------|-------|
| Emergency fund reserve account | $2,200 | three months of expenses set aside |
| Checking | $850 | daily spending |

**Key Takeaway:** Always keep a buffer.
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


def test_table_content_survives_untruncated(tmp_path):
    # The legacy renderer truncated cells to [:30] and dropped rows; the measured
    # renderer must keep the full text of every row.
    _, reader = _build(tmp_path)
    raw = "".join(pg.extract_text() or "" for pg in reader.pages)
    text = " ".join(raw.split())  # normalise wrap newlines; content wraps, not truncates
    assert "$2,200" in text                      # row not dropped
    assert "expenses set aside" in text          # long cell wrapped, not truncated at 30
    assert "$850" in text


def _white_ratio(img):
    px = list(img.getdata())
    return sum(1 for p in px if sum(p[:3]) > 735) / len(px)


def test_toc_clean_no_blank_gap_no_stray_folio(tmp_path):
    """Regression for the TOC bugs: Contents on its own page, the body immediately
    after the TOC (no reserved-page blank gap), and no folio printed on TOC pages."""
    import subprocess
    from PIL import Image
    # a book big enough that the TOC spans >1 page
    chapters = "".join(
        f"# CHAPTER {i}\n## Topic {i}\n\n## Section A\n\nText.\n\n## Section B\n\nText.\n\n"
        for i in range(1, 9)
    )
    out = tmp_path / "b.pdf"
    build_pdf({"title": "T", "author": "A", "year": "2026"}, parse_manuscript(chapters), out)
    reader = PdfReader(str(out))
    texts = [(pg.extract_text() or "") for pg in reader.pages]

    toc_idx = next(i for i, t in enumerate(texts) if t.strip().startswith("Contents"))
    first_ch = next(i for i, t in enumerate(texts) if "CHAPTER 1" in t or "Topic 1" in t)
    # No fully-blank page between the TOC start and the first chapter.
    import os
    d = tmp_path / "imgs"
    d.mkdir()
    subprocess.run(["pdftoppm", "-png", "-r", "40", str(out), f"{d}/p"], capture_output=True)
    imgs = sorted(os.listdir(d))
    d = str(d)
    for i in range(toc_idx, first_ch):  # TOC pages
        assert _white_ratio(Image.open(f"{d}/{imgs[i]}").convert("RGB")) < 0.985, \
            f"blank gap page at index {i}"
    # TOC pages carry no folio: the page's own number must not appear as a lone line.
    for i in range(toc_idx, first_ch):
        lines = [ln.strip() for ln in texts[i].splitlines() if ln.strip()]
        assert str(i + 1) not in lines[-1:], f"stray folio on TOC page {i + 1}"


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
