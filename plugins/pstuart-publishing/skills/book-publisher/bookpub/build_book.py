"""bookpub.build_book — the one deterministic driver a book's shim calls.

Replaces each book's bespoke ``generate_pdf.py`` / ``generate_epub.py`` fork with
a single config-driven pipeline:

    book.toml + manuscript  ->  interior PDF (gutter-sized, linked, outlined)
                            ->  EPUB3 (accessible)
                            ->  QA gate findings + deliverable manifest

A book's ``publishing/generate.py`` becomes a ~3-line shim::

    from bookpub.build_book import build_book
    build_book("book.toml", "output")
"""
from __future__ import annotations

import re
from collections.abc import Iterable
from pathlib import Path

from bookpub.config import (
    for_epub,
    for_pdf,
    gutter_inches_for_pages,
    isbn_for,
    load_book_config,
)
from bookpub.discovery import kdp_paperback_manifest
from bookpub.epub_engine import build_epub
from bookpub.pdf_engine import build_pdf, parse_manuscript
from bookpub.qa_report import FAIL, check_epub, check_pdf

_VALID_FORMATS = {"pdf", "epub"}


def _slug(cfg: dict) -> str:
    if cfg.get("slug"):
        return cfg["slug"]
    return re.sub(r"[^a-z0-9]+", "_", cfg["title"].lower()).strip("_")


def _assemble_manuscript(cfg: dict, base: Path) -> str:
    """Resolve the manuscript source to one markdown string (single source)."""
    if cfg.get("manuscript"):
        return (base / cfg["manuscript"]).read_text(encoding="utf-8")
    if cfg.get("file_order"):
        mdir = base / cfg.get("manuscript_dir", "manuscript")
        return "\n\n".join((mdir / f).read_text(encoding="utf-8")
                           for f in cfg["file_order"])
    raise ValueError("book.toml needs either `manuscript` (one file) or "
                     "`file_order` (list of chapter files)")


def _normalize_formats(formats: str | Iterable[str] | None) -> set[str]:
    if formats is None:
        return set(_VALID_FORMATS)
    if isinstance(formats, str):
        values = [formats]
    else:
        values = list(formats)
    selected: set[str] = set()
    for value in values:
        fmt = value.lower()
        if fmt == "all":
            selected.update(_VALID_FORMATS)
        elif fmt in _VALID_FORMATS:
            selected.add(fmt)
        else:
            raise ValueError(f"unsupported build format: {value}")
    if not selected:
        raise ValueError("at least one build format is required")
    return selected


def build_book(book_toml: str | Path, out_dir: str | Path,
               formats: str | Iterable[str] | None = None) -> dict:
    cfg = load_book_config(book_toml)
    base = Path(book_toml).parent
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    slug = _slug(cfg)
    selected_formats = _normalize_formats(formats)
    elements = parse_manuscript(_assemble_manuscript(cfg, base))
    index_terms = cfg.get("index_terms")

    interior = out / f"{slug}_interior.pdf"
    epub_path = out / f"{slug}.epub"
    pdf_stats = None
    gutter = None
    epub_stats = None
    manifest = {}

    if "pdf" in selected_formats:
        # Sizing pass learns page count so the binding margin (gutter) meets KDP
        # minimums for the book's thickness.
        pdf_cfg = for_pdf(cfg)
        sizing = build_pdf(pdf_cfg, elements, out / "_sizing.pdf")
        gutter = gutter_inches_for_pages(sizing["pages"])
        margins = dict(pdf_cfg.get("margins") or {})
        margins["h"] = max(margins.get("h", 0.625), gutter)
        pdf_cfg["margins"] = margins
        pdf_stats = build_pdf(pdf_cfg, elements, interior, index_terms=index_terms)
        manifest = kdp_paperback_manifest(
            interior,
            cfg.get("cover_pdf", "(none yet)"),
            kindle_cover_jpg=cfg.get("kindle_cover"),
            epub=epub_path if "epub" in selected_formats else None,
        )

    if "epub" in selected_formats:
        # Image references resolve relative to the book root and its manuscript dir.
        asset_bases = [base, base / cfg.get("manuscript_dir", "manuscript"), base / "publishing"]
        epub_cfg = for_epub(cfg)
        # Embed the front cover if one has been composed. The Kindle JPG is the same
        # front art used for the paperback wrap; it's composed (page-count-independent)
        # alongside the wrap, so on any rebuild after the first it is already present.
        if not epub_cfg.get("cover_image"):
            kindle_jpg = out / f"{slug}_kindle.jpg"
            if kindle_jpg.exists():
                epub_cfg["cover_image"] = str(kindle_jpg)
        epub_stats = build_epub(epub_cfg, elements, epub_path, index_terms=index_terms,
                                asset_bases=asset_bases)
        if "pdf" not in selected_formats:
            manifest = {"ebook_epub": str(epub_path)}

    # Gate only the artifacts requested in this build.
    allow_dashes = int(cfg.get("allow_dashes", 0))
    pdf_findings = []
    epub_findings = []
    if "pdf" in selected_formats:
        pdf_findings = check_pdf(interior, release=bool(cfg.get("release")),
                                 allow_dashes=allow_dashes, min_links=1, min_outline=1)
    if "epub" in selected_formats:
        epub_findings = check_epub(epub_path)
    fails = [f for f in (pdf_findings + epub_findings) if f.level == FAIL]

    return {
        "slug": slug,
        "formats": sorted(selected_formats),
        "pages": pdf_stats["pages"] if pdf_stats else None,
        "gutter_in": gutter,
        "interior": str(interior) if pdf_stats else None,
        "epub": str(epub_path) if epub_stats else None,
        "paperback_isbn": isbn_for(cfg, "paperback"),
        "ebook_isbn": isbn_for(cfg, "ebook"),
        "manifest": manifest,
        "qa_fails": [f"{f.check}: {f.detail}" for f in fails],
        "qa_pass": not fails,
    }


def main(argv: list[str] | None = None) -> int:
    import argparse

    ap = argparse.ArgumentParser(prog="bookpub-build", description="Build a book from book.toml")
    ap.add_argument("book_toml")
    ap.add_argument("-o", "--out", default="output")
    ap.add_argument("--format", choices=["all", "pdf", "epub"], default="all",
                    help="artifact format to build")
    args = ap.parse_args(argv)
    result = build_book(args.book_toml, args.out, formats=args.format)
    if result["pages"] is not None:
        print(f"\n{result['slug']}: {result['pages']}pp, gutter {result['gutter_in']}in")
    else:
        print(f"\n{result['slug']}: EPUB build")
    if result["interior"]:
        print(f"  interior: {result['interior']}")
    if result["epub"]:
        print(f"  epub:     {result['epub']}")
    if result["qa_fails"]:
        print("  QA FAIL:")
        for f in result["qa_fails"]:
            print(f"    - {f}")
        return 1
    print("  QA: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
