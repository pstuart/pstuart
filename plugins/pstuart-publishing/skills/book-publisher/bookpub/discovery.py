"""bookpub.discovery — page-count detection, artifact discovery, deliverable rules.

Closes two recurring defects:

  * covers whose spine derived from a hard-coded ``page_count`` that drifted from
    the real interior (the audit's recurring spine-mismatch class) — fixed by
    :func:`detect_page_count` + :func:`assert_cover_matches_interior`;
  * shipping the merged ``_with_covers.pdf`` as the upload artifact — KDP and
    IngramSpark require the interior and the cover as *separate* files, which
    :func:`kdp_paperback_manifest` makes explicit.
"""
from __future__ import annotations

import sys
from pathlib import Path

from pypdf import PdfReader


def detect_page_count(pdf_path: str | Path) -> int:
    """Authoritative interior page count — read it, never hard-code it."""
    return len(PdfReader(str(pdf_path)).pages)


def find_latest_pdf(directory: str | Path, pattern: str = "*.pdf") -> Path | None:
    """Most recently modified PDF matching ``pattern`` in ``directory``."""
    files = [p for p in Path(directory).glob(pattern) if p.is_file()]
    return max(files, key=lambda p: p.stat().st_mtime) if files else None


def _cover_dimensions():
    """Import the canonical spine math (moves to bookpub.covers in Phase 3 of the
    cover-lib relocation; resolve both layouts)."""
    pkg = Path(__file__).resolve().parent
    for cand in (pkg / "covers" / "lib", pkg.parent / "templates" / "lib",
                 pkg.parent / "templates"):
        if cand.is_dir() and str(cand) not in sys.path:
            sys.path.insert(0, str(cand))
    try:
        from lib import cover_dimensions as cd  # type: ignore
        return cd
    except Exception:
        try:
            from templates.lib import cover_dimensions as cd  # type: ignore
            return cd
        except Exception:
            return None


def expected_wrap_width_in(page_count: int, paper: str = "white") -> float:
    """Expected full-wrap width (inches) for a page count + paper, via the
    canonical cover_dimensions math."""
    cd = _cover_dimensions()
    if cd is None:
        raise RuntimeError("cover_dimensions unavailable")
    width, _ = cd.wrap_canvas_inches(page_count, paper)
    return width


def assert_cover_matches_interior(wrap_pdf: str | Path, interior_pdf: str | Path,
                                  paper: str = "white", tol_in: float = 0.0625) -> dict:
    """Raise AssertionError if the wrap cover's width disagrees with the spine
    implied by the REAL interior page count. Catches stale-page-count covers."""
    pages = detect_page_count(interior_pdf)
    expected = expected_wrap_width_in(pages, paper)
    actual = float(PdfReader(str(wrap_pdf)).pages[0].mediabox.width) / 72.0
    if abs(actual - expected) > tol_in:
        raise AssertionError(
            f"cover width {actual:.4f}in != expected {expected:.4f}in for "
            f"{pages}pp {paper} (tol {tol_in})"
        )
    return {"pages": pages, "expected_in": expected, "actual_in": actual}


def kdp_paperback_manifest(interior_pdf: str | Path, wrap_cover_pdf: str | Path,
                           kindle_cover_jpg: str | Path | None = None,
                           epub: str | Path | None = None) -> dict:
    """The per-channel deliverable set — SEPARATE files. The merged
    ``_with_covers.pdf`` is a human proof only and is never uploaded."""
    manifest = {
        "paperback_interior": str(interior_pdf),
        "paperback_cover": str(wrap_cover_pdf),
    }
    if kindle_cover_jpg:
        manifest["kindle_cover"] = str(kindle_cover_jpg)
    if epub:
        manifest["ebook_epub"] = str(epub)
    return manifest
