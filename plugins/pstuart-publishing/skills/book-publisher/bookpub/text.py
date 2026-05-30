"""bookpub.text — the ONE canonical text normaliser.

This replaces the two contradictory `sanitize_text` functions that caused the
catalog-wide ``--`` em-dash artifact:

  * the interior path upgraded ``--`` to an em-dash, then flattened em/en-dashes
    back to hyphens and force-encoded cp1252 — discarding the very glyphs it had
    just created;
  * the index / back-cover path turned em-dashes into a literal ``--`` and
    encoded latin-1, with core (non-embedded) fonts.

Because the engine now *always* embeds EB Garamond (see :mod:`bookpub.fonts`),
which contains every typographic glyph we use except box-drawing characters
(verified against the font's cmap, 2026-05-29), normalisation reduces to:

  1. upgrade ASCII ``--`` to a real em-dash (manuscripts use ``--`` for em-dashes);
  2. ASCII-ize ONLY the glyphs the bundled serif cannot render, so prose never
     shows tofu;
  3. preserve everything else as real Unicode — no lossy cp1252/latin-1 encode.
"""
from __future__ import annotations

import re

# Glyphs the bundled serif (EB Garamond) lacks — verified via fontTools cmap on
# 2026-05-29. Mapped to ASCII so prose never renders an empty box. If the bundled
# serif ever changes, re-verify and update this map (and only this map).
_MISSING_GLYPH_FALLBACKS = {
    "─": "-", "│": "|", "├": "|-", "└": "`-",   # light box drawing
    "┌": "+", "┐": "+", "┘": "+", "┤": "+",     # corners / tees (full set)
    "┬": "+", "┴": "+", "┼": "+", "═": "=", "║": "|",
    "●": "•", "◐": "•", "◆": "•", "▪": "•", "►": ">", "▶": ">",  # geometric -> ascii
    "█": "#", "▓": "#", "▒": ":", "░": ".",       # shading blocks (ascii-art bars)
    "�": "?",                                     # replacement character
}

# Pictographic ranges no print font (serif or mono) carries: emoji, dingbats,
# technical & arrow symbols. Stripped rather than tofu'd. These ranges deliberately
# EXCLUDE Geometric Shapes (U+25A0–25FF) so the □/■ checkbox squares survive; real
# punctuation (em/en-dash, quotes, ellipsis) is far below these ranges.
_PICTOGRAPH_RE = re.compile(
    "[\U0001F000-\U0001FAFF"   # emoji & supplemental symbols/pictographs
    "\U00002600-\U000026FF"    # miscellaneous symbols (☀ ☎ …)
    "\U00002700-\U000027FF"    # dingbats + misc (✓ ✗ ⟳ …)
    "\U00002300-\U000023FF"    # technical (⏸ ⎇ …)
    "\U00002B00-\U00002BFF"    # arrows / geometric supplement
    "️‍]"            # variation selector / zero-width joiner
)


def sanitize_text(text: str, *, em_dash: bool = True) -> str:
    """Normalise prose for an embedded-Unicode-font PDF.

    Real punctuation (em/en-dash, curly quotes, ellipsis, bullets, ©/®/™,
    arrows, primes) is preserved verbatim because EB Garamond supports it.
    Set ``em_dash=False`` for content where ``--`` is literal (e.g. CLI flags
    inside code) — though code blocks should bypass normalisation entirely.
    """
    if em_dash:
        text = text.replace("--", "—")
    for ch, repl in _MISSING_GLYPH_FALLBACKS.items():
        if ch in text:
            text = text.replace(ch, repl)
    return _PICTOGRAPH_RE.sub("", text)


# Checkbox glyphs the bundled serif actually contains (verified: U+25A0/U+25A1).
# Earlier revisions used \x01 sentinels that no renderer consumed — they leaked
# into output as control characters (missing-glyph tofu). Use real squares.
CHECKED = "■"    # U+25A0 black square
UNCHECKED = "□"  # U+25A1 white square


def strip_unsupported(text: str) -> str:
    """Drop/degrade glyphs no bundled font can render, for VERBATIM contexts
    (fenced code) that bypass :func:`sanitize_text` to preserve code-significant
    characters like ``--``. Applies the missing-glyph fallbacks + pictograph strip
    only — never the em-dash transform."""
    for ch, repl in _MISSING_GLYPH_FALLBACKS.items():
        if ch in text:
            text = text.replace(ch, repl)
    return _PICTOGRAPH_RE.sub("", text)


def render_checkboxes(text: str) -> str:
    """Replace `[x]` / `[ ]` task markers with squares the serif can render."""
    text = re.sub(r"\[\s*[xX]\s*\]", CHECKED, text)
    return re.sub(r"\[\s*\]", UNCHECKED, text)


def strip_markdown(text: str, *, em_dash: bool = True) -> str:
    """Sanitise then strip inline markdown to plain text (for headings, TOC,
    running headers, and anywhere styled spans must collapse to text)."""
    text = sanitize_text(text, em_dash=em_dash)
    text = render_checkboxes(text)
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)      # bold
    text = re.sub(r"\*(.+?)\*", r"\1", text)          # italic
    text = re.sub(r"_(.+?)_", r"\1", text)            # underscore italic
    text = re.sub(r"`(.+?)`", r"\1", text)            # inline code
    text = re.sub(r"\[(.+?)\]\(.+?\)", r"\1", text)   # links -> link text
    return text.strip()
