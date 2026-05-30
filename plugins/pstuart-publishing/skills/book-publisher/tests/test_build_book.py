"""Tests for bookpub.config + bookpub.build_book (the orchestrator)."""
from pathlib import Path

import pytest

from bookpub.config import (
    for_epub,
    for_pdf,
    gutter_inches_for_pages,
    isbn_for,
    load_book_config,
    validate,
)
from bookpub.build_book import build_book

BOOK_TOML = """\
title = "Sample Book"
subtitle = "A Test"
author = "Test Author"
year = "2026"
publisher = "Stuart Press"
style_preset = "earth_warm"
manuscript = "manuscript.md"
index_terms = ["savings", "Sabbath"]

[isbn]
paperback = "978-1-2345-6789-7"
ebook = "978-1-2345-6788-0"
"""

MANUSCRIPT = """\
# CHAPTER 1
## Saving

Savings build a buffer. Savings matter.

# CHAPTER 2
## Rest

The Sabbath restores; keep the Sabbath.
"""


def _book(tmp_path):
    (tmp_path / "book.toml").write_text(BOOK_TOML)
    (tmp_path / "manuscript.md").write_text(MANUSCRIPT)
    return tmp_path / "book.toml"


def test_gutter_table():
    assert gutter_inches_for_pages(100) == 0.375
    assert gutter_inches_for_pages(400) == 0.625
    assert gutter_inches_for_pages(900) == 0.875


def test_validate_requires_title_author():
    with pytest.raises(ValueError):
        validate({"title": "x"})  # missing author


def test_per_format_isbn(tmp_path):
    cfg = load_book_config(_book(tmp_path))
    assert isbn_for(cfg, "paperback") == "978-1-2345-6789-7"
    assert isbn_for(cfg, "ebook") == "978-1-2345-6788-0"
    # engines get the format-correct ISBN — a paperback never prints an ebook ISBN
    assert for_pdf(cfg)["isbn"] == "978-1-2345-6789-7"
    assert for_epub(cfg)["isbn"] == "978-1-2345-6788-0"


def test_build_book_produces_both_artifacts(tmp_path):
    out = tmp_path / "out"
    res = build_book(_book(tmp_path), out)
    assert Path(res["interior"]).exists()
    assert Path(res["epub"]).exists()
    assert res["pages"] >= 4
    assert res["paperback_isbn"] == "978-1-2345-6789-7"
    assert res["ebook_isbn"] == "978-1-2345-6788-0"
    # the merged proof is never in the deliverable manifest
    assert "_with_covers" not in str(res["manifest"])
    # gutter sized from real page count
    assert res["gutter_in"] >= 0.375


def test_build_book_passes_qa(tmp_path):
    res = build_book(_book(tmp_path), tmp_path / "out")
    # the new engine's own output should clear the gate (links, outline, fonts,
    # no '--', a11y); report any failures explicitly.
    assert res["qa_pass"], res["qa_fails"]
