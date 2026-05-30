"""bookpub.config — the single source of truth for a book's metadata.

One ``book.toml`` per book replaces the divergent ``BOOK_CONFIG`` /
``BOOK_METADATA`` dicts (PDF and EPUB previously carried separate copies, which
let title/ISBN/price drift between formats). The PDF and EPUB engines both read
the same parsed config, and per-format ISBNs live in one place so a paperback
can never print an ebook's ISBN.

Read-only loader using stdlib ``tomllib`` (no new dependency).
"""
from __future__ import annotations

import tomllib
from pathlib import Path

REQUIRED = ("title", "author")

# KDP inside (gutter) margin minimums by page count, inches.
_GUTTER_TABLE = [
    (150, 0.375),
    (300, 0.5),
    (500, 0.625),
    (700, 0.75),
    (10_000, 0.875),
]


def gutter_inches_for_pages(pages: int) -> float:
    """KDP minimum binding-side margin for a given page count."""
    for limit, gutter in _GUTTER_TABLE:
        if pages <= limit:
            return gutter
    return 0.875


def load_book_config(path: str | Path) -> dict:
    """Load and validate a ``book.toml``."""
    with open(path, "rb") as fh:
        cfg = tomllib.load(fh)
    validate(cfg)
    return cfg


def validate(cfg: dict) -> None:
    missing = [k for k in REQUIRED if not cfg.get(k)]
    if missing:
        raise ValueError(f"book.toml missing required keys: {missing}")
    isbn = cfg.get("isbn")
    if isbn is not None and not isinstance(isbn, dict):
        raise ValueError("isbn must be a table of per-format ISBNs, e.g. "
                         "[isbn] paperback = \"...\"")


def isbn_for(cfg: dict, fmt: str) -> str:
    """Per-format ISBN ('paperback' | 'ebook' | 'hardcover'); '' if unset."""
    return (cfg.get("isbn") or {}).get(fmt, "")


def _engine_config(cfg: dict, isbn: str) -> dict:
    """Flatten the shared keys both engines consume."""
    return {
        "title": cfg["title"],
        "subtitle": cfg.get("subtitle", ""),
        "author": cfg["author"],
        "year": str(cfg.get("year", "")),
        "language": cfg.get("language", "en"),
        "publisher": cfg.get("publisher", ""),
        "description": cfg.get("description", ""),
        "dedication": cfg.get("dedication", ""),
        "style_preset": cfg.get("style_preset", "navy_gold"),
        "trim_inches": cfg.get("trim_inches", [5.5, 8.5]),
        "isbn": isbn,
    }


def for_pdf(cfg: dict) -> dict:
    """Engine config for the print interior (paperback ISBN, gutter applied later)."""
    out = _engine_config(cfg, isbn_for(cfg, "paperback"))
    out["paper"] = cfg.get("paper", "white")
    out["margins"] = dict(cfg.get("margins", {}))
    return out


def for_epub(cfg: dict) -> dict:
    """Engine config for the ebook (ebook ISBN)."""
    return _engine_config(cfg, isbn_for(cfg, "ebook"))
