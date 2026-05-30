"""bookpub.cover — compose finished covers from a generated front-art bitmap.

Turns one portrait front-art image (e.g. from zgen-grok / gpt-image-2) into:
  * a Kindle cover JPEG (1600x2560) — art cover-filled, legibility scrims, vector-
    style title/subtitle/author drawn with the bundled EB Garamond (PIL);
  * a print-ready paperback WRAP PDF (back | spine | front) sized exactly for the
    page count + paper, with crisp vector text (fpdf2), spine text at KDP's
    100-page rule, an EAN-13 barcode when a real ISBN is present, and the blurb +
    author on the back.

No new dependencies: PIL (already used) + fpdf2 + the bundled fonts. Trim is
parameterised so 5.5x8.5, 6x9, and US-Letter workbooks all work.
"""
from __future__ import annotations

import textwrap as _tw
from pathlib import Path

from fpdf import FPDF
from PIL import Image, ImageDraw, ImageFont, ImageOps

from bookpub.fonts import font_dir, register_serif
from bookpub.pdf_engine import STYLE_PRESETS

_SCRIM = (12, 16, 28)  # near-black used for legibility gradients
_PAPER_THICKNESS = {"white": 0.002252, "cream": 0.0025}
_BLEED = 0.125
_SAFE = 0.25


def _palette(config: dict) -> dict:
    return STYLE_PRESETS.get(config.get("style_preset", "navy_gold"),
                             STYLE_PRESETS["navy_gold"])


# --------------------------------------------------------------------------- #
# Kindle cover (PIL raster)
# --------------------------------------------------------------------------- #

def _pil_font(style: str, px: int) -> ImageFont.FreeTypeFont:
    fn = {"": "EBGaramond-Regular.ttf", "B": "EBGaramond-Bold.ttf",
          "I": "EBGaramond-Italic.ttf", "BI": "EBGaramond-BoldItalic.ttf"}[style]
    return ImageFont.truetype(str(font_dir() / fn), px)


def _wrap_px(draw, text, font, max_w):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=font) <= max_w or not cur:
            cur = t
        else:
            lines.append(cur); cur = w
    if cur:
        lines.append(cur)
    return lines


def _draw_centered(draw, lines, font, y, W, fill, gap=1.15):
    for ln in lines:
        bbox = draw.textbbox((0, 0), ln, font=font)
        w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.text(((W - w) / 2, y), ln, font=font, fill=fill)
        y += int(h * gap)
    return y


def build_kindle_cover(front_art: str | Path, config: dict, out: str | Path,
                       size: tuple[int, int] = (1600, 2560)) -> str:
    W, H = size
    art = ImageOps.fit(Image.open(front_art).convert("RGB"), (W, H), Image.LANCZOS)
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    top = int(H * 0.46)
    for y in range(top):  # top scrim for the title
        od.line([(0, y), (W, y)], fill=(*_SCRIM, int(165 * (1 - y / top))))
    bot0 = int(H * 0.74)
    for y in range(bot0, H):  # bottom scrim for the author
        od.line([(0, y), (W, y)], fill=(*_SCRIM, int(170 * (y - bot0) / (H - bot0))))
    art = Image.alpha_composite(art.convert("RGBA"), overlay).convert("RGB")

    draw = ImageDraw.Draw(art)
    accent = _palette(config)["accent"]
    margin = int(W * 0.09)
    maxw = W - 2 * margin
    # Title
    tfont = _pil_font("B", int(W * 0.115))
    tlines = _wrap_px(draw, config["title"].upper(), tfont, maxw)
    y = _draw_centered(draw, tlines, tfont, int(H * 0.10), W, (245, 245, 245))
    # Subtitle
    if config.get("subtitle"):
        sfont = _pil_font("I", int(W * 0.045))
        y = _draw_centered(draw, _wrap_px(draw, config["subtitle"], sfont, maxw),
                           sfont, y + int(H * 0.012), W, accent)
    # Author (bottom)
    if config.get("author"):
        afont = _pil_font("", int(W * 0.05))
        _draw_centered(draw, _wrap_px(draw, config["author"], afont, maxw),
                       afont, int(H * 0.88), W, (240, 240, 240))
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    art.save(out, "JPEG", quality=92)
    return str(out)


# --------------------------------------------------------------------------- #
# Paperback wrap (fpdf2 vector text over the bitmap)
# --------------------------------------------------------------------------- #

def _fit_to_png(front_art: str | Path, w_in: float, h_in: float, dpi: int = 300) -> str:
    import tempfile
    px = (max(1, int(w_in * dpi)), max(1, int(h_in * dpi)))
    img = ImageOps.fit(Image.open(front_art).convert("RGB"), px, Image.LANCZOS)
    p = Path(tempfile.mkdtemp()) / "_front_panel.png"
    img.save(p, "PNG")
    return str(p)


def build_paperback_wrap(front_art: str | Path, config: dict, page_count: int,
                         out: str | Path, *, paper: str = "white") -> dict:
    trim_w, trim_h = config.get("trim_inches", [5.5, 8.5])
    spine = page_count * _PAPER_THICKNESS.get(paper, 0.002252)
    wrap_w = 2 * (trim_w + _BLEED) + spine
    wrap_h = trim_h + 2 * _BLEED
    back_end = _BLEED + trim_w
    spine_end = back_end + spine
    heading = _palette(config)["heading"]
    accent = _palette(config)["accent"]

    pdf = FPDF(unit="in", format=(wrap_w, wrap_h))
    pdf.set_auto_page_break(False)
    pdf.add_page()
    register_serif(pdf)

    # Back + spine: solid heading colour across the whole wrap.
    pdf.set_fill_color(*heading)
    pdf.rect(0, 0, wrap_w, wrap_h, "F")

    # Front panel: the generated art, bleed to the trim edges.
    front_w = wrap_w - spine_end
    panel = _fit_to_png(front_art, front_w, wrap_h)
    pdf.image(panel, x=spine_end, y=0, w=front_w, h=wrap_h)

    # Front vector text (title/subtitle/author), inside the safe area.
    fx = spine_end + _BLEED + _SAFE
    fw = trim_w - 2 * _SAFE
    pdf.set_xy(fx, _BLEED + _SAFE + 0.2)
    pdf.set_text_color(245, 245, 245)
    pdf.set_font("serif", "B", 34)
    pdf.multi_cell(fw, 0.55, config["title"].upper(), align="C", new_x="LMARGIN", new_y="NEXT")
    if config.get("subtitle"):
        pdf.set_x(fx); pdf.set_text_color(*accent); pdf.set_font("serif", "I", 16)
        pdf.multi_cell(fw, 0.3, config["subtitle"], align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_xy(fx, wrap_h - _BLEED - _SAFE - 0.4)
    pdf.set_text_color(240, 240, 240); pdf.set_font("serif", "", 17)
    pdf.multi_cell(fw, 0.3, config.get("author", ""), align="C", new_x="LMARGIN", new_y="NEXT")

    # Spine text (KDP requires >= 100 pages).
    if page_count >= 100 and spine >= 0.0625:
        pdf.set_text_color(245, 245, 245)
        with pdf.rotation(90, spine_end - spine / 2, wrap_h / 2):
            pdf.set_font("serif", "B", 11)
            pdf.set_xy(spine_end - spine / 2 - trim_h / 2 + 0.5, spine_end - spine / 2 - 0.08)
            pdf.cell(trim_h - 1.0, spine, f"{config['title']}    {config.get('author','')}",
                     align="C")

    # Back panel: blurb + author, with a barcode zone if a real ISBN exists.
    bx = _BLEED + _SAFE
    bw = trim_w - 2 * _SAFE
    pdf.set_xy(bx, _BLEED + _SAFE + 0.3)
    blurb = config.get("description") or config.get("hook") or ""
    if blurb:
        pdf.set_text_color(235, 235, 235); pdf.set_font("serif", "", 12)
        pdf.multi_cell(bw, 0.24, blurb, align="L", new_x="LMARGIN", new_y="NEXT")
    if config.get("author_bio"):
        pdf.ln(0.2); pdf.set_x(bx); pdf.set_font("serif", "I", 10.5)
        pdf.set_text_color(*[min(255, c + 90) for c in accent])
        pdf.multi_cell(bw, 0.2, config["author_bio"], align="L", new_x="LMARGIN", new_y="NEXT")

    _maybe_barcode(pdf, config, back_end, wrap_h)

    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(out))
    return {"output": str(out), "wrap_in": (round(wrap_w, 3), round(wrap_h, 3)),
            "spine_in": round(spine, 4), "spine_text": page_count >= 100}


def _maybe_barcode(pdf: FPDF, config: dict, back_end: float, wrap_h: float) -> None:
    isbn = (config.get("isbn") or {}).get("paperback") if isinstance(config.get("isbn"), dict) \
        else config.get("isbn", "")
    if not isbn or "X" in isbn.upper() or len(isbn.replace("-", "").replace(" ", "")) != 13:
        return
    import tempfile

    try:
        from lib.cover_barcode import render_isbn_barcode  # type: ignore
    except Exception:
        import sys
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "templates" / "lib"))
        try:
            from cover_barcode import render_isbn_barcode  # type: ignore
        except Exception:
            return
    bw_in, bh_in = 1.75, 0.95
    bx = back_end - _SAFE - bw_in
    by = wrap_h - _BLEED - _SAFE - bh_in
    png = Path(tempfile.mkdtemp()) / "_barcode.png"
    try:
        render_isbn_barcode(isbn, png, width_px=int(bw_in * 300), height_px=int(bh_in * 300))
    except Exception:
        return
    pdf.set_fill_color(255, 255, 255)
    pdf.rect(bx, by, bw_in, bh_in, "F")
    pdf.image(str(png), x=bx + 0.06, y=by + 0.06, w=bw_in - 0.12, h=bh_in - 0.12)
