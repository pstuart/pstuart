"""bookpub.pdf_engine — config-driven interior PDF generation.

Phase 2a skeleton. The headline capabilities the forked engines never had:

  * **Clickable TOC** — entries are real PDF link annotations (``add_link(page=)``
    + ``cell(link=)``) that jump to the chapter.
  * **Bookmark outline** — ``start_section()`` populates the PDF ``/Outlines``
    tree (the reader sidebar). Headings are rendered by this module; sections are
    registered with ``strict=False`` purely for the outline/destinations.
  * **Robust two-pass TOC** — ``insert_toc_placeholder(allow_extra_pages=True)``
    reserves the TOC pages, renders the body, then fills the TOC with FINAL page
    numbers. No hand-rolled page map, no drift.

Text + fonts come from :mod:`bookpub.text` and :mod:`bookpub.fonts`, so the
``--`` artifact and macOS-font problems are fixed here by construction.

Phase 2b adds measured tables, fenced-code (mono), callouts, and reconciles the
legacy ``DESIGN_COLORS`` key set. This module deliberately uses its own small
palette rather than the broken one, so it never raises ``KeyError``.
"""
from __future__ import annotations

import re
from pathlib import Path

from fpdf import FPDF

from bookpub.fonts import register_serif
from bookpub.text import sanitize_text, strip_markdown

SERIF = "serif"

# Minimal, safe palette. Phase 2b wires the full style-preset system; for now a
# config may override any of these via config["palette"][key] = (r, g, b).
_DEFAULT_PALETTE = {
    "heading": (30, 58, 95),    # navy
    "accent": (201, 162, 39),   # gold
    "body": (40, 40, 40),       # near-black
    "muted": (110, 110, 110),   # eyebrow / folio
    "rule": (200, 200, 200),    # light rule
}

_ROMAN = ["", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X",
          "XI", "XII", "XIII", "XIV", "XV", "XVI", "XVII", "XVIII", "XIX", "XX"]


class BookPDF(FPDF):
    """Interior PDF with outline + clickable-TOC plumbing."""

    def __init__(self, config: dict):
        trim = tuple(config.get("trim_inches", (5.5, 8.5)))
        super().__init__(unit="in", format=trim)
        self.config = config
        m = config.get("margins", {})
        self.set_margins(m.get("h", 0.625), m.get("top", 0.6), m.get("h", 0.625))
        self.set_auto_page_break(auto=True, margin=m.get("bottom", 0.6))
        self.palette = {**_DEFAULT_PALETTE, **config.get("palette", {})}
        self.in_front_matter = True
        register_serif(self)
        self.set_font(SERIF, "", 11)

    # -- chrome --------------------------------------------------------------
    def footer(self):
        if self.in_front_matter:
            return  # no folio on title/copyright/dedication/TOC
        self.set_y(-0.5)
        self.set_font(SERIF, "", 9)
        self.set_text_color(*self.palette["muted"])
        self.cell(0, 0.3, str(self.page_no()), align="C")

    def _text(self, w, h, s, *, style="", size=11, color="body", align="J",
              strip=False):
        self.set_font(SERIF, style, size)
        self.set_text_color(*self.palette[color])
        s = strip_markdown(s) if strip else sanitize_text(s)
        self.multi_cell(w, h, s, align=align, new_x="LMARGIN", new_y="NEXT")

    # -- front matter --------------------------------------------------------
    def title_page(self):
        self.add_page()
        self.ln(1.6)
        self._text(0, 0.5, self.config["title"], style="B", size=30,
                   color="heading", align="C", strip=True)
        if self.config.get("subtitle"):
            self.ln(0.15)
            self._text(0, 0.3, self.config["subtitle"], style="I", size=15,
                       color="accent", align="C", strip=True)
        self.ln(2.2)
        self._text(0, 0.3, self.config.get("author", ""), size=15,
                   color="body", align="C", strip=True)

    def copyright_page(self):
        self.add_page()
        self.ln(5.5)
        yr = self.config.get("year", "")
        author = self.config.get("author", "")
        lines = [
            f"Copyright © {yr} {author}".strip(),
            "All rights reserved.",
            "",
            f"ISBN: {self.config.get('isbn', '')}".rstrip(),
            self.config.get("publisher", ""),
        ]
        for ln in lines:
            self._text(0, 0.22, ln, size=9, color="muted", align="C")

    def dedication_page(self):
        if not self.config.get("dedication"):
            return
        self.add_page()
        self.ln(3.5)
        self._text(0, 0.3, self.config["dedication"], style="I", size=13,
                   color="body", align="C", strip=True)

    # -- table of contents (rendered last, with final page numbers) ----------
    def _render_toc(self, pdf: "BookPDF", outline):
        pdf.set_font(SERIF, "B", 20)
        pdf.set_text_color(*pdf.palette["heading"])
        pdf.cell(0, 0.6, "Contents", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(0.2)
        for sec in outline:
            if sec.level > 2:
                continue
            indent = 0.0 if sec.level == 0 else (0.3 if sec.level == 1 else 0.6)
            is_part = sec.level == 0
            style = "B" if is_part else ""
            size = 12 if is_part else 11
            link = pdf.add_link(page=sec.page_number)
            name = sanitize_text(sec.name)
            num = str(sec.page_number)
            pdf.set_font(SERIF, style, size)
            pdf.set_text_color(*pdf.palette["heading" if is_part else "body"])
            page_w = pdf.get_string_width(num) + 0.05
            name_w = pdf.epw - indent - page_w
            x0 = pdf.l_margin + indent
            pdf.set_x(x0)
            # truncate by real width, not character count
            while pdf.get_string_width(name) > name_w - 0.1 and len(name) > 4:
                name = name[:-2]
            pdf.cell(name_w, 0.28, name, link=link, new_x="RIGHT", new_y="TOP")
            pdf.cell(page_w, 0.28, num, align="R", link=link,
                     new_x="LMARGIN", new_y="NEXT")

    # -- structure -----------------------------------------------------------
    def part_divider(self, el: dict):
        self.add_page()
        self.start_section(strip_markdown(el["title"]), level=0, strict=False)
        self.ln(2.5)
        if el.get("number"):
            self._text(0, 0.3, f"PART {_ROMAN[el['number']]}", size=12,
                       color="accent", align="C", strip=True)
            self.ln(0.1)
        self._text(0, 0.45, el["title"], style="B", size=24, color="heading",
                   align="C", strip=True)
        if el.get("subtitle"):
            self.ln(0.1)
            self._text(0, 0.3, el["subtitle"], style="I", size=13,
                       color="muted", align="C", strip=True)

    def chapter_open(self, el: dict, level: int):
        self.add_page()
        title = el.get("title") or f"Chapter {el.get('number', '')}".strip()
        self.start_section(strip_markdown(title), level=level, strict=False)
        self.ln(0.8)
        if el.get("number"):
            self._text(0, 0.3, f"CHAPTER {el['number']}", size=11,
                       color="accent", align="C", strip=True)
            self.ln(0.05)
        self._text(0, 0.5, title, style="B", size=22, color="heading",
                   align="C", strip=True)
        # decorative rule
        self.set_draw_color(*self.palette["accent"])
        self.set_line_width(0.01)
        cx = self.w / 2
        self.line(cx - 0.5, self.get_y() + 0.1, cx + 0.5, self.get_y() + 0.1)
        self.ln(0.45)

    # -- body block rendering ------------------------------------------------
    def render_body(self, body: str, section_level: int):
        for block in _split_blocks(body):
            first = block[0]
            if first.startswith("## "):
                self._heading(first[3:].strip(), level=section_level, size=14)
            elif first.startswith("### "):
                self._heading(first[4:].strip(), level=None, size=12)
            elif first.startswith("```") or first.startswith("~~~"):
                self._code_block(block)
            elif first.lstrip().startswith((">",)):
                self._blockquote(block)
            elif _is_list(first):
                self._list(block)
            else:
                self._paragraph(" ".join(block))

    def _heading(self, text: str, level, size: int):
        if self.get_y() > self.h - self.b_margin - 1.0:
            self.add_page()
        self.ln(0.12)
        if level is not None:  # register H2 sections in the outline
            self.start_section(strip_markdown(text), level=level, strict=False)
        self._text(0, 0.32, text, style="B", size=size, color="heading",
                   align="L", strip=True)
        self.ln(0.04)

    def _paragraph(self, text: str):
        self._text(0, 0.205, text, size=11, color="body", align="J", strip=True)
        self.ln(0.07)

    def _blockquote(self, lines: list[str]):
        text = " ".join(re.sub(r"^\s*>\s?", "", ln) for ln in lines)
        x0 = self.l_margin
        self.set_draw_color(*self.palette["accent"])
        self.set_line_width(0.02)
        y0 = self.get_y()
        self.set_x(x0 + 0.2)
        self.set_font(SERIF, "I", 11)
        self.set_text_color(*self.palette["muted"])
        self.multi_cell(self.epw - 0.3, 0.205, sanitize_text(text),
                        align="L", new_x="LMARGIN", new_y="NEXT")
        self.line(x0 + 0.05, y0, x0 + 0.05, self.get_y())
        self.ln(0.08)

    def _list(self, lines: list[str]):
        for ln in lines:
            m = re.match(r"^\s*(?:[-*+]|\d+\.)\s+(.*)$", ln)
            if not m:
                continue
            self.set_font(SERIF, "", 11)
            self.set_text_color(*self.palette["body"])
            self.set_x(self.l_margin + 0.2)
            self.cell(0.2, 0.205, "•")
            self.set_x(self.l_margin + 0.4)
            self.multi_cell(self.epw - 0.4, 0.205, strip_markdown(m.group(1)),
                            align="L", new_x="LMARGIN", new_y="NEXT")
        self.ln(0.06)

    def _code_block(self, block: list[str]):
        # Phase 2a: render verbatim in serif (no markdown transforms). Phase 2b
        # ships a bundled monospace font and a tinted code background.
        code = [ln for ln in block if not (ln.startswith("```") or ln.startswith("~~~"))]
        self.set_font(SERIF, "", 9.5)
        self.set_text_color(*self.palette["muted"])
        for ln in code:
            self.set_x(self.l_margin + 0.15)
            self.multi_cell(self.epw - 0.15, 0.18, ln, align="L",
                            new_x="LMARGIN", new_y="NEXT")
        self.ln(0.08)


# --------------------------------------------------------------------------- #
# Block splitting + manuscript parsing
# --------------------------------------------------------------------------- #

def _split_blocks(body: str) -> list[list[str]]:
    """Split body markdown into blocks (paragraphs/lists/quotes/code fences)."""
    blocks: list[list[str]] = []
    cur: list[str] = []
    in_code = False
    for raw in body.splitlines():
        line = raw.rstrip()
        fence = line.startswith("```") or line.startswith("~~~")
        if fence:
            if not in_code:
                if cur:
                    blocks.append(cur); cur = []
                in_code = True
                cur = [line]
            else:
                cur.append(line)
                blocks.append(cur); cur = []
                in_code = False
            continue
        if in_code:
            cur.append(line); continue
        if not line.strip():
            if cur:
                blocks.append(cur); cur = []
            continue
        # headings and list-item boundaries start their own block
        if (line.startswith(("## ", "### ")) or _is_list(line)) and cur and not _is_list(cur[0]):
            blocks.append(cur); cur = []
        cur.append(line)
    if cur:
        blocks.append(cur)
    return blocks


def _is_list(line: str) -> bool:
    return bool(re.match(r"^\s*(?:[-*+]|\d+\.)\s+", line))


_PART_RE = re.compile(r"^\s*part\b", re.IGNORECASE)


def parse_manuscript(md: str) -> list[dict]:
    """Minimal parser for the project's `# CHAPTER` / `# PART` convention.

    Splits on H1. A heading matching /^part/i becomes a part divider; otherwise
    a chapter. If the first body line is an H2, it is used as the chapter title
    (the `# CHAPTER 1` / `## Real Title` convention).
    """
    elements: list[dict] = []
    chunks = re.split(r"(?m)^# (.+)$", md)
    # chunks: [pre, h1, body, h1, body, ...]
    ch_num = 0
    part_num = 0
    for i in range(1, len(chunks), 2):
        h1 = chunks[i].strip()
        body = chunks[i + 1] if i + 1 < len(chunks) else ""
        if _PART_RE.match(h1):
            part_num += 1
            sub = None
            m = re.search(r"(?m)^\*(.+?)\*\s*$", body)
            if m:
                sub = m.group(1)
            elements.append({"kind": "part", "number": part_num,
                             "title": re.sub(r"^[Pp]art\s+[^:]*:\s*", "", h1) or h1,
                             "subtitle": sub})
        else:
            ch_num += 1
            title = h1
            body_lines = body.splitlines()
            # consume a leading H2 as the real chapter title
            for j, ln in enumerate(body_lines):
                if ln.strip() == "":
                    continue
                if ln.startswith("## "):
                    title = ln[3:].strip()
                    body = "\n".join(body_lines[j + 1:])
                break
            elements.append({"kind": "chapter", "number": ch_num,
                             "title": title, "body": body})
    return elements


def build_pdf(config: dict, elements: list[dict], output: str | Path) -> dict:
    """Render a book to ``output``. Returns stats (pages, chapters, parts)."""
    pdf = BookPDF(config)
    pdf.title_page()
    pdf.copyright_page()
    pdf.dedication_page()

    # Reserve the TOC right after front matter; filled with final page numbers.
    pdf.insert_toc_placeholder(pdf._render_toc, pages=2, allow_extra_pages=True)
    pdf.in_front_matter = False

    has_parts = any(e["kind"] == "part" for e in elements)
    chapter_level = 1 if has_parts else 0
    n_chapters = n_parts = 0
    for el in elements:
        if el["kind"] == "part":
            pdf.part_divider(el); n_parts += 1
        else:
            pdf.chapter_open(el, level=chapter_level)
            pdf.render_body(el.get("body", ""), section_level=chapter_level + 1)
            n_chapters += 1

    out = Path(output)
    out.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(out))
    return {"pages": pdf.page_no(), "chapters": n_chapters, "parts": n_parts,
            "output": str(out)}
