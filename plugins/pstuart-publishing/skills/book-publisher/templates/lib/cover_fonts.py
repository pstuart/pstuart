"""Register bundled EB Garamond fonts on an FPDF instance.

Why: fpdf2's core fonts (Helvetica, Times, Courier) are latin-1 only and
cannot render Unicode punctuation (en-dash, em-dash, smart quotes, etc).
Real book metadata needs those glyphs. EB Garamond is bundled under SIL OFL;
see templates/lib/fonts/OFL.txt.
"""
from pathlib import Path
from fpdf import FPDF

FONT_DIR = Path(__file__).parent / "fonts"

_FAMILY = "ebgaramond"
_VARIANTS = {
    "regular": ("", "EBGaramond-Regular.ttf"),
    "italic": ("I", "EBGaramond-Italic.ttf"),
    "bold": ("B", "EBGaramond-Bold.ttf"),
    "bolditalic": ("BI", "EBGaramond-BoldItalic.ttf"),
}


def register_fonts(pdf: FPDF) -> dict[str, str]:
    """Register all 4 EB Garamond variants on `pdf`.

    Returns a dict mapping face-key -> family name for use with
    pdf.set_font(family, size=...). The family name is the same across
    variants; fpdf2 distinguishes by style param in set_font.

    Idempotent: safe to call multiple times on the same FPDF instance.
    """
    for key, (style, filename) in _VARIANTS.items():
        path = FONT_DIR / filename
        # fpdf2 stores fonts under family+style (exact case: "ebgaramond", "ebgaramondI", etc.)
        font_key = f"{_FAMILY}{style}"
        if font_key not in pdf.fonts:
            pdf.add_font(_FAMILY, style, str(path))
    return {key: _FAMILY for key in _VARIANTS}
