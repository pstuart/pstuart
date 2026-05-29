"""bookpub.fonts — portable, fail-loud font registration for the interior engine.

Replaces the per-book ``_load_fonts()`` that hard-coded
``/System/Library/Fonts/Supplemental/Times New Roman.ttf`` (macOS-only; breaks
on Linux/CI; not the bundled font; and embedding Times New Roman in a sold book
is a licensing exposure) and *silently* fell back to the core latin-1 Times when
the file was absent — the latent source of non-embedded fonts and lost Unicode.

Here the bundled SIL OFL EB Garamond is loaded relative to the package, and a
missing font is a hard error: we never silently ship a degraded book.
"""
from __future__ import annotations

from pathlib import Path

from fpdf import FPDF

SERIF_FAMILY = "serif"
MONO_FAMILY = "mono"

# Style-suffix -> filename. fpdf2 keys fonts as (family, style).
_SERIF_VARIANTS = {
    "": "EBGaramond-Regular.ttf",
    "B": "EBGaramond-Bold.ttf",
    "I": "EBGaramond-Italic.ttf",
    "BI": "EBGaramond-BoldItalic.ttf",
}

# A monospace face for fenced code (shipped in Phase 2 — code blocks).
# Kept as a single regular weight; bold/italic code is rare.
_MONO_FILE = "JetBrainsMono-Regular.ttf"

# Candidate font directories, newest layout first. The cover lib (and its fonts)
# move from templates/lib to bookpub/covers/lib in Phase 3; resolve both so this
# module keeps working across the migration.
_PKG = Path(__file__).resolve().parent
_FONT_DIR_CANDIDATES = (
    _PKG / "covers" / "lib" / "fonts",          # post-Phase-3 home
    _PKG.parent / "templates" / "lib" / "fonts",  # current home
)


class FontError(RuntimeError):
    """Raised when a required bundled font is missing — fail loud, never degrade."""


def font_dir(override: Path | None = None) -> Path:
    """Return the directory holding the bundled TTFs (or ``override`` if given)."""
    if override is not None:
        return Path(override)
    for cand in _FONT_DIR_CANDIDATES:
        if cand.is_dir():
            return cand
    raise FontError(
        f"no bundled font directory found; looked in {[str(c) for c in _FONT_DIR_CANDIDATES]}"
    )


def register_serif(pdf: FPDF, *, font_dir_override: Path | None = None) -> str:
    """Register the 4 EB Garamond variants under family ``serif``.

    Returns the family name. Idempotent. Raises :class:`FontError` if any variant
    file is missing — we do not fall back to a core latin-1 font.
    """
    fdir = font_dir(font_dir_override)
    for style, filename in _SERIF_VARIANTS.items():
        path = fdir / filename
        if not path.exists():
            raise FontError(f"missing serif font: {path}")
        if f"{SERIF_FAMILY}{style}" not in pdf.fonts:
            pdf.add_font(SERIF_FAMILY, style, str(path))
    return SERIF_FAMILY


def register_mono(pdf: FPDF, *, font_dir_override: Path | None = None) -> str:
    """Register the monospace face under family ``mono`` (for code blocks).

    Raises :class:`FontError` if the mono TTF is not bundled. (The file ships in
    Phase 2; until then, callers that need code rendering will fail loudly rather
    than silently emit a non-embedded core Courier.)
    """
    path = font_dir(font_dir_override) / _MONO_FILE
    if not path.exists():
        raise FontError(
            f"missing mono font: {path} — bundle an OFL monospace TTF for code blocks"
        )
    if MONO_FAMILY not in pdf.fonts:
        pdf.add_font(MONO_FAMILY, "", str(path))
    return MONO_FAMILY


def register_fonts(pdf: FPDF, *, mono: bool = False,
                   font_dir_override: Path | None = None) -> dict[str, str]:
    """Register the serif (always) and, if ``mono=True``, the monospace face."""
    families = {"serif": register_serif(pdf, font_dir_override=font_dir_override)}
    if mono:
        families["mono"] = register_mono(pdf, font_dir_override=font_dir_override)
    return families
