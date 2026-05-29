"""bookpub.index — back-of-book index with real, CLICKABLE page numbers.

Two problems the forked index code had:

  * it rendered the index as a *separate* pypdf-merged PDF, so the page numbers
    were dead text (no ``/Link``) and structure was lost;
  * it used core (non-embedded) Times + latin-1, emitting a literal ``--`` for
    em-dashes on the index/back-cover.

This module solves the first with pure page-finding logic that the engine renders
as appended pages in the *same* document (so ``add_link(page=)`` resolves and the
embedded font is inherited), and improves quality with word-boundary matching and
an over-broad-term guard.
"""
from __future__ import annotations

import re


def find_term_pages(pages_text: list[str], terms: list[str],
                    start_page: int = 1) -> dict[str, list[int]]:
    """Map each term to the 1-based page numbers it appears on.

    ``pages_text[i]`` is the extracted text of page ``i+1``. Matching is
    case-insensitive and word-boundary anchored (``\\bterm\\b``) so "Bond" no
    longer matches "bonds", "abandon", etc. — the over-broad-substring defect.
    ``start_page`` skips front matter / TOC so a chapter title echoed in the TOC
    does not produce a spurious index reference to the TOC page.
    """
    result: dict[str, list[int]] = {}
    for term in terms:
        pat = re.compile(r"\b" + re.escape(term) + r"\b", re.IGNORECASE)
        pages = [i + 1 for i, text in enumerate(pages_text)
                 if i + 1 >= start_page and pat.search(text)]
        if pages:
            result[term] = pages
    return result


def compress_ranges(pages: list[int]) -> list[tuple[int, int]]:
    """Collapse a page list into contiguous (start, end) runs: [1,2,3,5] -> [(1,3),(5,5)]."""
    runs: list[list[int]] = []
    for p in sorted(set(pages)):
        if runs and p == runs[-1][1] + 1:
            runs[-1][1] = p
        else:
            runs.append([p, p])
    return [(a, b) for a, b in runs]


def format_ranges(runs: list[tuple[int, int]]) -> str:
    """Render runs as an index page-string: [(1,3),(5,5)] -> '1-3, 5'."""
    return ", ".join(str(a) if a == b else f"{a}-{b}" for a, b in runs)


def over_broad_terms(index_map: dict[str, list[int]], n_pages: int,
                     threshold: float = 0.15) -> list[str]:
    """Terms appearing on > threshold of all pages — likely too generic to index."""
    if n_pages <= 0:
        return []
    return sorted(t for t, pages in index_map.items()
                  if len(set(pages)) > threshold * n_pages)
