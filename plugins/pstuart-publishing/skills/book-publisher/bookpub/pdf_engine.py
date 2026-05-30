"""bookpub.pdf_engine — config-driven interior PDF generation.

Phase 2a gave the headline navigation: clickable TOC (real ``/Link`` annotations
via ``add_link(page=)`` + ``cell(link=)``), a bookmark ``/Outlines`` tree (via
``start_section``), and a robust native two-pass TOC
(``insert_toc_placeholder(allow_extra_pages=True)``). Text + fonts come from
:mod:`bookpub.text` / :mod:`bookpub.fonts`, so output is single-embedded-font
with real em-dashes by construction.

Phase 2b adds: style-preset palettes, fenced code in the bundled monospace on a
tinted background, MEASURED tables (wrapped cells, header repeated on page
break, no ``[:30]`` truncation), and key-takeaway callouts. The legacy
``DESIGN_COLORS`` ``KeyError`` is moot here — this engine uses its own palette.
"""
from __future__ import annotations

import re
from pathlib import Path

from fpdf import FPDF
from fpdf.enums import MethodReturnValue

from bookpub.fonts import register_mono, register_serif
from bookpub.index import compress_ranges, find_term_pages
from bookpub.text import sanitize_text, strip_markdown, strip_unsupported

SERIF = "serif"
MONO = "mono"

# Common interior colours; presets override heading + accent.
_BASE_PALETTE = {
    "body": (40, 40, 40),
    "muted": (110, 110, 110),
    "rule": (200, 200, 200),
    "zebra": (244, 244, 246),
    "code_bg": (244, 244, 246),
}

# The 8 SKILL.md schemes, reduced to interior heading/accent pairs.
STYLE_PRESETS = {
    "navy_gold": {"heading": (30, 58, 95), "accent": (201, 162, 39)},
    "burgundy_cream": {"heading": (88, 24, 32), "accent": (160, 120, 60)},
    "teal_coral": {"heading": (0, 95, 115), "accent": (255, 127, 102)},
    "black_silver": {"heading": (25, 25, 25), "accent": (120, 120, 120)},
    "earth_warm": {"heading": (89, 60, 31), "accent": (218, 165, 32)},
    "purple_gold": {"heading": (60, 25, 85), "accent": (218, 165, 32)},
    "forest_cream": {"heading": (34, 85, 51), "accent": (160, 140, 70)},
    "minimal_white": {"heading": (30, 30, 30), "accent": (90, 90, 90)},
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
        preset = STYLE_PRESETS.get(config.get("style_preset", "navy_gold"),
                                   STYLE_PRESETS["navy_gold"])
        self.palette = {**_BASE_PALETTE, **preset, **config.get("palette", {})}
        self.in_front_matter = True
        register_serif(self)
        register_mono(self)
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
            pdf.set_x(pdf.l_margin + indent)
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
            elif first.startswith(("```", "~~~")):
                self._code_block(block)
            elif _is_table(block):
                self.render_table(_parse_table(block))
            elif _is_scene_break(block):
                self._scene_break()
            elif first.lstrip().startswith(">"):
                self._blockquote(block)
            elif _is_list(first):
                self._list(block)
            elif _CALLOUT_RE.match(first):
                m = _CALLOUT_RE.match(" ".join(block))
                self._key_callout(m.group(1), m.group(2))
            else:
                self._paragraph(" ".join(block))

    def _heading(self, text: str, level, size: int):
        if self.get_y() > self.h - self.b_margin - 1.0:
            self.add_page()
        self.ln(0.12)
        if level is not None:
            self.start_section(strip_markdown(text), level=level, strict=False)
        self._text(0, 0.32, text, style="B", size=size, color="heading",
                   align="L", strip=True)
        self.ln(0.04)

    def _paragraph(self, text: str):
        self._text(0, 0.205, text, size=11, color="body", align="J", strip=True)
        self.ln(0.07)

    def _scene_break(self):
        """Centered divider for `---` / `***` / `* * *` (novel scene breaks)."""
        self.ln(0.12)
        self.set_font(SERIF, "", 12)
        self.set_text_color(*self.palette["muted"])
        self.cell(0, 0.25, "* * *", align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(0.12)

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

    def _key_callout(self, label: str, text: str):
        """A gold-bordered key-takeaway box, sized to its measured content."""
        self.set_font(SERIF, "", 10.5)
        pad = 0.1
        lines = self.multi_cell(self.epw - 2 * pad, 0.2, sanitize_text(text),
                                dry_run=True, output=MethodReturnValue.LINES)
        h = (len(lines) + 1) * 0.2 + 2 * pad
        if self.get_y() + h > self.h - self.b_margin:
            self.add_page()
        x0, y0 = self.l_margin, self.get_y()
        self.set_fill_color(*self.palette["zebra"])
        self.set_draw_color(*self.palette["accent"])
        self.set_line_width(0.015)
        self.rect(x0, y0, self.epw, h, "FD")
        self.set_xy(x0 + pad, y0 + pad)
        self.set_font(SERIF, "B", 10.5)
        self.set_text_color(*self.palette["heading"])
        self.cell(0, 0.2, sanitize_text(label), new_x="LMARGIN", new_y="NEXT")
        self.set_x(x0 + pad)
        self.set_font(SERIF, "", 10.5)
        self.set_text_color(*self.palette["body"])
        self.multi_cell(self.epw - 2 * pad, 0.2, sanitize_text(text),
                        align="L", new_x="LMARGIN", new_y="NEXT")
        self.set_y(y0 + h)
        self.ln(0.1)

    def _code_block(self, block: list[str]):
        code = [ln for ln in block if not ln.startswith(("```", "~~~"))]
        if not code:
            return
        self.set_font(MONO, "", 8.5)
        line_h, pad = 0.16, 0.08
        h = len(code) * line_h + 2 * pad
        if self.get_y() + h > self.h - self.b_margin:
            self.add_page()
        x0, y0 = self.l_margin, self.get_y()
        self.set_fill_color(*self.palette["code_bg"])
        self.rect(x0, y0, self.epw, h, "F")
        self.set_text_color(*self.palette["body"])
        self.set_xy(x0 + pad, y0 + pad)
        for ln in code:  # verbatim ('--' survives), but drop unrenderable glyphs
            self.set_x(x0 + pad)
            self.cell(self.epw - 2 * pad, line_h, strip_unsupported(ln),
                      new_x="LMARGIN", new_y="NEXT")
        self.set_y(y0 + h)
        self.ln(0.08)

    # -- measured table ------------------------------------------------------
    def render_table(self, rows: list[list[str]]):
        if not rows:
            return
        ncols = max(len(r) for r in rows)
        rows = [list(r) + [""] * (ncols - len(r)) for r in rows]
        col_w = self.epw / ncols
        pad, line_h = 0.04, 0.17
        header = rows[0]

        def _row_height(row, style):
            self.set_font(SERIF, style, 9)
            n = 1
            for cell in row:
                lines = self.multi_cell(col_w - 2 * pad, line_h,
                                        strip_markdown(cell.strip()),
                                        dry_run=True, output=MethodReturnValue.LINES)
                n = max(n, len(lines))
            return n * line_h + 2 * pad

        def _draw_row(row, idx):
            style = "B" if idx == 0 else ""
            h = _row_height(row, style)
            if self.get_y() + h > self.h - self.b_margin:
                self.add_page()
                if idx != 0:  # repeat the header on continuation pages
                    _draw_row(header, 0)
            y, x0 = self.get_y(), self.l_margin
            if idx == 0:
                self.set_fill_color(*self.palette["heading"])
                self.set_text_color(255, 255, 255)
                fill = True
            else:
                fill = idx % 2 == 0
                if fill:
                    self.set_fill_color(*self.palette["zebra"])
                self.set_text_color(*self.palette["body"])
            self.set_draw_color(*self.palette["rule"])
            self.set_line_width(0.008)
            self.set_font(SERIF, style, 9)
            for c in range(ncols):
                self.rect(x0 + c * col_w, y, col_w, h, "FD" if fill else "D")
            for c in range(ncols):
                self.set_xy(x0 + c * col_w + pad, y + pad)
                self.multi_cell(col_w - 2 * pad, line_h,
                                strip_markdown(row[c].strip()),
                                align="L", new_x="RIGHT", new_y="TOP")
            self.set_xy(x0, y + h)

        self.ln(0.08)
        for i, row in enumerate(rows):
            _draw_row(row, i)
        self.ln(0.1)

    # -- back-of-book index (clickable, same-document) -----------------------
    def index_pages(self, index_map: dict[str, list[int]]):
        """Render alphabetised index pages. Each page reference is a real link
        (``write(link=)`` -> ``/Link`` annotation) into the body, and inherits
        the embedded serif — so no dead text and no '--' artifacts."""
        if not index_map:
            return
        self.add_page()
        self.start_section("Index", level=0, strict=False)
        self.set_font(SERIF, "B", 18)
        self.set_text_color(*self.palette["heading"])
        self.cell(0, 0.5, "Index", new_x="LMARGIN", new_y="NEXT")
        self.ln(0.1)
        last_letter = None
        for term in sorted(index_map, key=str.lower):
            letter = term[0].upper()
            if letter != last_letter:
                last_letter = letter
                self.ln(0.08)
                self.set_font(SERIF, "B", 12)
                self.set_text_color(*self.palette["accent"])
                self.cell(0, 0.28, letter, new_x="LMARGIN", new_y="NEXT")
            self.set_x(self.l_margin + 0.15)
            self.set_font(SERIF, "", 10.5)
            self.set_text_color(*self.palette["body"])
            self.write(0.2, sanitize_text(term) + "  ")
            runs = compress_ranges(index_map[term])
            for k, (a, b) in enumerate(runs):
                lid = self.add_link(page=a)
                self.set_text_color(*self.palette["heading"])
                self.write(0.2, str(a) if a == b else f"{a}-{b}", lid)
                self.set_text_color(*self.palette["body"])
                if k < len(runs) - 1:
                    self.write(0.2, ", ")
            self.ln(0.26)


# --------------------------------------------------------------------------- #
# Block splitting + manuscript parsing
# --------------------------------------------------------------------------- #

_CALLOUT_RE = re.compile(r"^\*\*([^*]+?):\*\*\s*(.+)$", re.DOTALL)


def _split_blocks(body: str) -> list[list[str]]:
    """Split body markdown into blocks. Table rows and code fences stay grouped."""
    blocks: list[list[str]] = []
    cur: list[str] = []
    in_code = False
    for raw in body.splitlines():
        line = raw.rstrip()
        if line.startswith(("```", "~~~")):
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
        if (line.startswith(("## ", "### ")) or _is_list(line)) and cur and not _is_list(cur[0]):
            blocks.append(cur); cur = []
        cur.append(line)
    if cur:
        blocks.append(cur)
    return blocks


def _is_list(line: str) -> bool:
    return bool(re.match(r"^\s*(?:[-*+]|\d+\.)\s+", line))


def _is_scene_break(block: list[str]) -> bool:
    """A lone `---`, `***`, `* * *`, `___`, `- - -` line (a novel scene break).
    Checked before _is_list because `* * *` also matches the list pattern."""
    if len(block) != 1:
        return False
    s = block[0].strip().replace(" ", "")
    return len(s) >= 3 and len(set(s)) == 1 and s[0] in "*-_"


def _is_table(block: list[str]) -> bool:
    if len(block) < 2 or "|" not in block[0]:
        return False
    return any(set(ln.strip()) <= set("|-: ") and "-" in ln for ln in block)


def _parse_table(block: list[str]) -> list[list[str]]:
    rows = []
    for ln in block:
        if set(ln.strip()) <= set("|-: ") and "-" in ln:  # separator row
            continue
        rows.append([c.strip() for c in ln.strip().strip("|").split("|")])
    return rows


_PART_RE = re.compile(r"^\s*part\b", re.IGNORECASE)
# Front/back matter: titled, but NOT numbered "Chapter N".
_FRONTBACK_RE = re.compile(
    r"^\s*(introduction|conclusion|foreword|preface|prologue|epilogue|afterword|"
    r"acknowledg|about the|appendix|glossary|epigraph|colophon)\b", re.IGNORECASE)
_BARE_CHAPTER_RE = re.compile(r"^\s*chapter\s+(\d+)\s*$", re.IGNORECASE)
_NUM_TITLE_RE = re.compile(r"^\s*chapter\s+(\d+)\s*[:.\-]\s*(.+)$", re.IGNORECASE)


def _promote_h2_title(body: str) -> tuple[str | None, str]:
    """For a bare `# CHAPTER N`, the real title is the following `## Title`."""
    lines = body.splitlines()
    for j, ln in enumerate(lines):
        if ln.strip() == "":
            continue
        if ln.startswith("## "):
            return ln[3:].strip(), "\n".join(lines[j + 1:])
        break
    return None, body


def parse_manuscript(md: str) -> list[dict]:
    """Parser for the project's `# PART` / `# CHAPTER N` / front-matter convention.

    - `# PART ...` -> part divider.
    - bare `# CHAPTER 3` -> numbered chapter; the following `## Title` is promoted.
    - `# CHAPTER 3: Title` -> numbered chapter with inline title.
    - `# Introduction` / `# Conclusion` / ... -> UNNUMBERED chapter (no "CHAPTER N"
      eyebrow), body kept intact (its `## ` lines stay as sections).
    - any other `# Title` -> auto-numbered chapter titled by the H1.
    """
    elements: list[dict] = []
    chunks = re.split(r"(?m)^# (.+)$", md)
    part_num = auto_num = 0
    for i in range(1, len(chunks), 2):
        h1 = chunks[i].strip()
        body = chunks[i + 1] if i + 1 < len(chunks) else ""
        if _PART_RE.match(h1):
            part_num += 1
            m = re.search(r"(?m)^\*(.+?)\*\s*$", body)
            elements.append({"kind": "part", "number": part_num,
                             "title": re.sub(r"^[Pp]art\s+[^:]*:\s*", "", h1) or h1,
                             "subtitle": m.group(1) if m else None})
            continue

        bare = _BARE_CHAPTER_RE.match(h1)
        num_title = _NUM_TITLE_RE.match(h1)
        if bare:
            number = int(bare.group(1))
            promoted, body = _promote_h2_title(body)
            title = promoted or h1
        elif num_title:
            number, title = int(num_title.group(1)), num_title.group(2).strip()
        elif _FRONTBACK_RE.match(h1):
            number, title = None, h1
        else:
            auto_num += 1
            number, title = auto_num, h1
        elements.append({"kind": "chapter", "number": number,
                         "title": title, "body": body})
    return elements


def _count_sections(body: str) -> int:
    return sum(1 for ln in body.splitlines() if ln.startswith("## "))


def _render(config: dict, elements: list[dict], output: str | Path,
            index_map: dict[str, list[int]] | None = None) -> dict:
    import math

    from pypdf import PdfReader

    pdf = BookPDF(config)
    pdf.title_page()
    pdf.copyright_page()
    pdf.dedication_page()

    has_parts = any(e["kind"] == "part" for e in elements)
    chapter_level = 1 if has_parts else 0

    # Reserve enough TOC pages up front that it never overflows: an overflow
    # would let allow_extra_pages insert pages that shift the body and invalidate
    # the outline destinations recorded during the body pass.
    n_entries = len(elements) + sum(
        _count_sections(e.get("body", "")) for e in elements if e["kind"] == "chapter"
    )
    toc_pages = max(1, math.ceil((n_entries + 3) / 24))
    pdf.insert_toc_placeholder(pdf._render_toc, pages=toc_pages, allow_extra_pages=True)
    pdf.in_front_matter = False

    n_chapters = n_parts = 0
    first_body_page = None
    for el in elements:
        if el["kind"] == "part":
            pdf.part_divider(el); n_parts += 1
        else:
            pdf.chapter_open(el, level=chapter_level)
            pdf.render_body(el.get("body", ""), section_level=chapter_level + 1)
            n_chapters += 1
        if first_body_page is None:
            first_body_page = pdf.page_no()

    if index_map:
        pdf.index_pages(index_map)

    out = Path(output)
    out.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(out))
    # Authoritative page count: read the finished file (page_no() can disagree
    # after the TOC placeholder is reconciled at output time).
    pages = len(PdfReader(str(out)).pages)
    return {"pages": pages, "chapters": n_chapters, "parts": n_parts,
            "index_terms": len(index_map or {}), "first_body_page": first_body_page or 1,
            "output": str(out)}


def build_pdf(config: dict, elements: list[dict], output: str | Path, *,
              index_terms: list[str] | None = None) -> dict:
    """Render a book to ``output``. Returns stats (pages, chapters, parts).

    If ``index_terms`` is given, render the body once to learn each term's body
    pages (word-boundary matched), then re-render with a clickable index appended
    — body pagination is identical between passes, so the page references resolve.
    """
    if index_terms:
        import tempfile

        from pypdf import PdfReader

        tmp = Path(tempfile.mkdtemp()) / "_bodyonly.pdf"
        body_stats = _render(config, elements, tmp, index_map=None)
        pages_text = [(pg.extract_text() or "") for pg in PdfReader(str(tmp)).pages]
        index_map = find_term_pages(pages_text, index_terms,
                                    start_page=body_stats["first_body_page"])
        return _render(config, elements, output, index_map=index_map)
    return _render(config, elements, output, index_map=None)
