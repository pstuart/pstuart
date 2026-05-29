"""Tests for bookpub.epub_engine — accessibility metadata + valid EPUB3."""
import shutil
import subprocess

import pytest

from bookpub.epub_engine import _identifier, body_to_xhtml, build_epub
from bookpub.pdf_engine import parse_manuscript
from bookpub.qa_report import _A11Y_PROPS, _read_epub_opf, epub_accessibility

MD = """# PART I: Foundations

*Begin here*

# CHAPTER 1
## The First Idea

Prose -- with em-dash, *italic*, **bold**.

- alpha
- beta

> wisdom

| A | B |
|---|---|
| 1 | two hundred |

# CHAPTER 2
## The Second Idea

Sabbath rest and savings.
"""

CONFIG = {"title": "Test", "author": "A", "year": "2026",
          "isbn": "978-1-2345-6789-7", "publisher": "P", "description": "d"}


def _build(tmp_path, **over):
    cfg = {**CONFIG, **over}
    out = tmp_path / "book.epub"
    stats = build_epub(cfg, parse_manuscript(MD), out, index_terms=["Sabbath", "savings"])
    return out, stats


def test_build_stats(tmp_path):
    _, stats = _build(tmp_path)
    assert stats["chapters"] == 2
    assert stats["parts"] == 1
    assert stats["identifier"].startswith("urn:isbn:")


def test_accessibility_metadata_present(tmp_path):
    out, _ = _build(tmp_path)
    opf = _read_epub_opf(out)
    a11y = epub_accessibility(opf)
    # All five schema:* properties must be present (EU EAA / Apple gate).
    for prop in _A11Y_PROPS:
        assert a11y[prop], f"missing {prop}"
    assert "dcterms:conformsTo" in opf


def test_identifier_isbn_vs_uuid():
    assert _identifier({"title": "T", "author": "A", "isbn": "978-1-2345-6789-7"}) \
        == "urn:isbn:9781234567897"
    # placeholder ISBN -> deterministic uuid fallback
    uid = _identifier({"title": "T", "author": "A", "isbn": "978-1-XXXXXX-XX-X"})
    assert uid.startswith("urn:uuid:")
    # deterministic: same inputs -> same id
    assert uid == _identifier({"title": "T", "author": "A", "isbn": ""})


def test_body_to_xhtml_blocks():
    md = "Para with *em* and **strong**.\n\n- one\n- two\n\n```\nx--y\n```"
    html = body_to_xhtml(md)
    assert "<em>em</em>" in html
    assert "<strong>strong</strong>" in html
    assert "<ul><li>one</li><li>two</li></ul>" in html
    assert "<pre><code>x--y</code></pre>" in html  # code keeps -- verbatim


def test_body_to_xhtml_emdash_and_escaping():
    html = body_to_xhtml("a -- b and <tag> & ampersand")
    assert "—" in html            # real em-dash in prose
    assert "&lt;tag&gt;" in html  # HTML escaped
    assert "&amp;" in html


def test_table_to_xhtml(tmp_path):
    html = body_to_xhtml("| A | B |\n|---|---|\n| 1 | two hundred |")
    assert "<table>" in html and "<th>A</th>" in html
    assert "<td>two hundred</td>" in html  # not truncated


@pytest.mark.skipif(shutil.which("epubcheck") is None, reason="epubcheck not installed")
def test_passes_epubcheck(tmp_path):
    out, _ = _build(tmp_path)
    r = subprocess.run(["epubcheck", str(out)], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
