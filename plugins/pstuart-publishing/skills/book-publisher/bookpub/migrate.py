"""bookpub.migrate — scaffold a legacy book onto the shared engine.

A book moves off its forked ``publishing/generate_*.py`` by gaining:
  * a ``book.toml`` (single source of truth), and
  * a ~3-line ``publishing/generate.py`` shim that calls
    :func:`bookpub.build_book.build_book`.

The package itself is vendored into the book (a byte-identical copy, the pattern
the cover lib already proved drift-free) so the book builds reproducibly without
depending on a globally-installed bookpub.

This module only *scaffolds* — a human reviews the generated ``book.toml`` (ISBNs,
BISAC, style) before publishing. It does not overwrite an existing ``book.toml``.
"""
from __future__ import annotations

from pathlib import Path

SHIM = '''\
#!/usr/bin/env python3
"""Thin shim — all logic lives in the vendored bookpub package."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))  # vendored bookpub/
from bookpub.build_book import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main([str(Path(__file__).parent.parent / "book.toml"),
                           "-o", str(Path(__file__).parent / "output")]))
'''


def discover_manuscript_files(book_dir: str | Path,
                              manuscript_dir: str = "manuscript") -> list[str]:
    """Sorted markdown chapter files (names only) under ``book_dir/manuscript``."""
    mdir = Path(book_dir) / manuscript_dir
    return sorted(p.name for p in mdir.glob("*.md")) if mdir.is_dir() else []


def _toml_str(value) -> str:
    if isinstance(value, list):
        inner = ",\n  ".join(f'"{v}"' for v in value)
        return f"[\n  {inner},\n]"
    if isinstance(value, (int, float)):
        return str(value)
    return f'"{value}"'


def render_book_toml(meta: dict, files: list[str],
                     manuscript_dir: str = "manuscript") -> str:
    """Render a book.toml from metadata + an ordered chapter-file list."""
    order = ("title", "subtitle", "author", "year", "publisher", "language",
             "style_preset", "paper", "description")
    lines = ["# bookpub single-source-of-truth config (scaffolded — review before publishing)."]
    for key in order:
        if meta.get(key):
            lines.append(f"{key} = {_toml_str(meta[key])}")
    lines.append(f"manuscript_dir = {_toml_str(manuscript_dir)}")
    lines.append(f"file_order = {_toml_str(files)}")
    if meta.get("index_terms"):
        lines.append(f"index_terms = {_toml_str(meta['index_terms'])}")
    isbn = meta.get("isbn") or {}
    if isbn:
        lines.append("\n[isbn]")
        for fmt, val in isbn.items():
            lines.append(f"{fmt} = {_toml_str(val)}")
    else:
        lines.append("\n# [isbn]  # add before a release build")
        lines.append('# paperback = "..."')
        lines.append('# ebook = "..."')
    return "\n".join(lines) + "\n"


def scaffold(book_dir: str | Path, meta: dict, *, manuscript_dir: str = "manuscript",
             write_shim: bool = True) -> dict:
    """Write book.toml (if absent) + the publishing/generate.py shim."""
    book = Path(book_dir)
    files = discover_manuscript_files(book, manuscript_dir)
    toml_path = book / "book.toml"
    created = False
    if not toml_path.exists():
        toml_path.write_text(render_book_toml(meta, files, manuscript_dir))
        created = True
    if write_shim:
        (book / "publishing").mkdir(exist_ok=True)
        (book / "publishing" / "generate.py").write_text(SHIM)
    return {"book_toml": str(toml_path), "created": created,
            "n_chapters": len(files), "shim": write_shim}
