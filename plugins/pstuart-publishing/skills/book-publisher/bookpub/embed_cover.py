"""bookpub.embed_cover — re-emit a book's EPUB with its front cover embedded.

The EPUB and interior are built together by ``build_book`` *before* the Kindle
cover JPG is composed, so a first-pass EPUB carries no cover image. Rather than
rebuild the interior, this re-runs only the EPUB stage through the same engine
code path (so the result stays epubcheck-clean and accessible), this time with
``cover_image`` pointed at the already-composed Kindle JPG. No new art.

    python3 -m bookpub.embed_cover book.toml output            # auto-find output/<slug>_kindle.jpg
    python3 -m bookpub.embed_cover book.toml output cover.jpg  # explicit cover
"""
from __future__ import annotations

import sys
from pathlib import Path

from bookpub.build_book import _assemble_manuscript, _slug
from bookpub.config import for_epub, load_book_config
from bookpub.epub_engine import build_epub
from bookpub.pdf_engine import parse_manuscript


def embed_cover(book_toml: str | Path, out_dir: str | Path,
                cover_image: str | Path | None = None) -> dict:
    cfg = load_book_config(book_toml)
    base = Path(book_toml).parent
    out = Path(out_dir)
    slug = _slug(cfg)

    cover = Path(cover_image) if cover_image else out / f"{slug}_kindle.jpg"
    if not cover.exists():
        raise FileNotFoundError(f"cover image not found: {cover}")

    elements = parse_manuscript(_assemble_manuscript(cfg, base))
    epub_cfg = for_epub(cfg)
    epub_cfg["cover_image"] = str(cover)
    epub_path = out / f"{slug}.epub"
    asset_bases = [base, base / cfg.get("manuscript_dir", "manuscript"), base / "publishing"]
    build_epub(epub_cfg, elements, epub_path, index_terms=cfg.get("index_terms"),
               asset_bases=asset_bases)
    return {"epub": str(epub_path), "cover": str(cover), "slug": slug}


def main() -> None:
    if len(sys.argv) < 3:
        print(__doc__.strip())
        raise SystemExit(2)
    cover = sys.argv[3] if len(sys.argv) > 3 else None
    res = embed_cover(sys.argv[1], sys.argv[2], cover)
    print(f"embedded cover '{Path(res['cover']).name}' -> {res['epub']}")


if __name__ == "__main__":
    main()
