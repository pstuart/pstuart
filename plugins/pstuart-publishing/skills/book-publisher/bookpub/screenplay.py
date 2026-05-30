"""bookpub.screenplay — theatrical / screenplay renderer.

The base engine flattens a script's semantics (stage directions, character cues,
parentheticals, technical light/sound/video cues) to plain prose. This renderer
preserves them, reusing BookPDF's chrome (embedded fonts, footer, clickable TOC,
bookmark outline) while classifying screenplay blocks:

  * ``# **NIGHT ONE ...**`` / ``# ACT ...``        -> act divider  (outline L0)
  * ``## **SCENE 1: ...**``                          -> scene opener (outline L1)
  * ``**\\[LIGHTS: ...\\]**`` / SOUND / VIDEO         -> technical cue (boxed)
  * ``**JACK**`` (bold, all-caps)                     -> character cue
  * ``*(working the crowd)*``                         -> parenthetical
  * plain lines after a cue                           -> dialogue (indented)
  * ``*JACK bounds out ...*`` (lone italic)           -> stage direction

Handles the manuscript's Pandoc/LaTeX flavour: strips YAML front matter,
``\\newpage`` / ``\\vspace``, and Pandoc backslash escapes (``\\-`` ``\\!`` ``\\(``).
"""
from __future__ import annotations

import re
from pathlib import Path

from bookpub.pdf_engine import SERIF, BookPDF, _count_toc_pages, _TocEntry
from bookpub.text import sanitize_text

_ACT_RE = re.compile(r"^#\s+\*{0,2}\s*(NIGHT|ACT|PART)\b", re.IGNORECASE)
_SCENE_RE = re.compile(r"^##\s+\*{0,2}\s*SCENE\b", re.IGNORECASE)
_CUE_RE = re.compile(r"^\*\*\[(.+?)\]\*\*$")            # **[LIGHTS: ...]**
_CHARACTER_RE = re.compile(r"^\*\*([A-Z0-9][A-Z0-9 .,'’()/&-]{0,40})\*\*$")
_PAREN_RE = re.compile(r"^\*\((.+?)\)\*$")
_ITALIC_LINE_RE = re.compile(r"^\*([^*].*?)\*$")


def clean_source(md: str) -> str:
    """Strip YAML front matter, LaTeX directives, and Pandoc backslash escapes."""
    md = re.sub(r"\A---\n.*?\n---\n", "", md, count=1, flags=re.DOTALL)
    md = re.sub(r"\\newpage", "", md)
    md = re.sub(r"\\vspace\{[^}]*\}", "", md)
    md = re.sub(r"\\([-!+().\[\]#*])", r"\1", md)  # \- \! \( etc -> literal
    return md


def _heading_text(line: str) -> str:
    return re.sub(r"^#+\s*", "", line).replace("**", "").strip()


def split_preamble(md: str) -> tuple[str, str]:
    """Return (preamble, script). Script starts at the first act heading."""
    lines = md.splitlines()
    for i, ln in enumerate(lines):
        if _ACT_RE.match(ln):
            return "\n".join(lines[:i]), "\n".join(lines[i:])
    return md, ""


def parse_screenplay(md: str) -> list[dict]:
    """Parse the script portion into acts -> scenes -> typed body blocks."""
    _, script = split_preamble(clean_source(md))
    elements: list[dict] = []
    cur_scene = None
    body: list[str] = []

    def flush():
        nonlocal body, cur_scene
        if cur_scene is not None:
            cur_scene["blocks"] = _classify_blocks(body)
        body = []

    for raw in script.splitlines():
        if _ACT_RE.match(raw):
            flush()
            elements.append({"kind": "act", "title": _heading_text(raw)})
            cur_scene = None
        elif _SCENE_RE.match(raw):
            flush()
            cur_scene = {"kind": "scene", "title": _heading_text(raw), "blocks": []}
            elements.append(cur_scene)
        else:
            body.append(raw)
    flush()
    return elements


def _classify_blocks(lines: list[str]) -> list[dict]:
    """Group blank-line-separated blocks and tag each by screenplay role."""
    blocks: list[dict] = []
    buf: list[str] = []

    def emit(buf):
        if not buf:
            return
        first = buf[0].strip()
        cue = _CUE_RE.match(first)
        char = _CHARACTER_RE.match(first)
        if cue:
            blocks.append({"t": "tech", "text": cue.group(1).strip()})
        elif char and not first.endswith(":**"):  # cue, not a "**LABEL:**"
            speech = []
            for ln in buf[1:]:
                s = ln.strip()
                p = _PAREN_RE.match(s)
                if p:
                    speech.append({"paren": p.group(1)})
                elif s:
                    speech.append({"line": s})
            blocks.append({"t": "char", "name": char.group(1).strip(), "speech": speech})
        elif len(buf) == 1 and _ITALIC_LINE_RE.match(first):
            blocks.append({"t": "stage", "text": _ITALIC_LINE_RE.match(first).group(1)})
        else:
            blocks.append({"t": "action", "text": " ".join(b.strip() for b in buf)})

    for ln in lines:
        if ln.strip() == "":
            emit(buf); buf = []
        else:
            buf.append(ln)
    emit(buf)
    return blocks


class ScreenplayPDF(BookPDF):
    def act_divider(self, title: str):
        self.add_page()
        self.start_section(title, level=0, strict=False)
        self.toc_entries.append((title, 0, self.page_no()))
        self.ln(2.5)
        self._text(0, 0.45, title, style="B", size=22, color="heading",
                   align="C", strip=True)

    def scene_open(self, title: str):
        self.add_page()
        self.start_section(title, level=1, strict=False)
        self.toc_entries.append((title, 1, self.page_no()))
        self.ln(0.6)
        self._text(0, 0.4, title, style="B", size=16, color="heading",
                   align="C", strip=True)
        self.set_draw_color(*self.palette["accent"])
        self.set_line_width(0.01)
        cx = self.w / 2
        self.line(cx - 0.5, self.get_y() + 0.08, cx + 0.5, self.get_y() + 0.08)
        self.ln(0.4)

    def technical_cue(self, text: str):
        self.ln(0.06)
        self.set_font(SERIF, "B", 9.5)
        self.set_text_color(*self.palette["accent"])
        self.multi_cell(0, 0.2, sanitize_text(f"[ {text} ]"), align="C",
                        new_x="LMARGIN", new_y="NEXT")
        self.ln(0.04)

    def stage_direction(self, text: str):
        self.ln(0.04)
        self.set_font(SERIF, "I", 10.5)
        self.set_text_color(*self.palette["muted"])
        self.multi_cell(0, 0.2, sanitize_text(text), align="L",
                        new_x="LMARGIN", new_y="NEXT")
        self.ln(0.04)

    def character_block(self, name: str, speech: list[dict]):
        if self.get_y() > self.h - self.b_margin - 1.0:
            self.add_page()
        self.ln(0.08)
        # centered character cue
        self.set_font(SERIF, "B", 11)
        self.set_text_color(*self.palette["heading"])
        self.cell(0, 0.22, sanitize_text(name.upper()), align="C",
                  new_x="LMARGIN", new_y="NEXT")
        indent = 0.9
        for item in speech:
            if "paren" in item:
                self.set_font(SERIF, "I", 10)
                self.set_text_color(*self.palette["muted"])
                self.set_x(self.l_margin + indent)
                self.multi_cell(self.epw - 2 * indent, 0.18,
                                sanitize_text(f"({item['paren']})"), align="C",
                                new_x="LMARGIN", new_y="NEXT")
            else:
                self.set_font(SERIF, "", 11)
                self.set_text_color(*self.palette["body"])
                self.set_x(self.l_margin + indent)
                self.multi_cell(self.epw - 2 * indent, 0.205,
                                sanitize_text(item["line"]), align="L",
                                new_x="LMARGIN", new_y="NEXT")
        self.ln(0.04)

    def action(self, text: str):
        self.set_font(SERIF, "", 11)
        self.set_text_color(*self.palette["body"])
        self.multi_cell(0, 0.205, sanitize_text(text), align="J",
                        new_x="LMARGIN", new_y="NEXT")
        self.ln(0.06)

    def render_scene(self, blocks: list[dict]):
        for b in blocks:
            if b["t"] == "tech":
                self.technical_cue(b["text"])
            elif b["t"] == "stage":
                self.stage_direction(b["text"])
            elif b["t"] == "char":
                self.character_block(b["name"], b["speech"])
            else:
                self.action(b["text"])


def _build_screenplay(config: dict, elements: list[dict], output: str | Path, *,
                      toc_final: list[tuple[str, int, int]] | None = None) -> dict:
    from pypdf import PdfReader

    pdf = ScreenplayPDF(config)
    pdf.title_page()
    pdf.copyright_page()
    pdf.dedication_page()

    if toc_final is not None:
        pdf._in_toc = True
        pdf.add_page()
        toc_start = pdf.page_no()
        pdf._render_toc(pdf, [_TocEntry(t, lvl, pg) for t, lvl, pg in toc_final])
        pdf._toc_page_range = (toc_start, pdf.page_no())
        pdf._in_toc = False
    pdf.in_front_matter = False

    n_acts = n_scenes = 0
    for el in elements:
        if el["kind"] == "act":
            pdf.act_divider(el["title"]); n_acts += 1
        else:
            pdf.scene_open(el["title"])
            pdf.render_scene(el.get("blocks", []))
            n_scenes += 1

    out = Path(output)
    out.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(out))
    return {"acts": n_acts, "scenes": n_scenes, "toc_entries": pdf.toc_entries,
            "pages": len(PdfReader(str(out)).pages), "output": str(out)}


def build_screenplay(config: dict, manuscript_md: str, output: str | Path) -> dict:
    """Render a screenplay with a clickable, correctly-paginated TOC (two-pass)."""
    import tempfile

    elements = parse_screenplay(manuscript_md)
    tmp = Path(tempfile.mkdtemp()) / "_pass1.pdf"
    p1 = _build_screenplay(config, elements, tmp)
    toc_span = _count_toc_pages(config, [(t, lvl) for t, lvl, _ in p1["toc_entries"]])
    toc_final = [(t, lvl, pg + toc_span) for t, lvl, pg in p1["toc_entries"]]
    return _build_screenplay(config, elements, output, toc_final=toc_final)
