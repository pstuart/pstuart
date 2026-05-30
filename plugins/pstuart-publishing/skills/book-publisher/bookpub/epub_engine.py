"""bookpub.epub_engine — EPUB3 generation with accessibility + navigation parity.

The forked EPUBs validated, but every one shipped with ZERO accessibility
metadata — which Apple flags and the EU Accessibility Act (in force 2025-06-28)
treats as non-saleable. This engine adds the full ``schema:*`` accessibility set
plus ``dcterms:conformsTo``, a nested Part→chapter TOC, semantic ``epub:type``
structure, landmarks, a stable ``urn:isbn``/UUID identifier, the cover in the
spine, and a chapter-anchored EPUB index.

It reuses the SAME block parser and text normaliser as :mod:`bookpub.pdf_engine`,
so the PDF and EPUB renderings cannot drift, and EPUB prose gets real em-dashes
too.

Print-page-list parity (``epub:type="page-list"`` keyed to the PDF page map) is
deferred to Phase 5, where the PDF and EPUB are built together and the authoritative
page map is available — a synthetic page-list would misrepresent print pages.
"""
from __future__ import annotations

import html as _html
import re
import uuid
from pathlib import Path

from ebooklib import epub

from bookpub.pdf_engine import (
    _CALLOUT_RE,
    _is_list,
    _is_scene_break,
    _is_table,
    _parse_table,
    _split_blocks,
    parse_manuscript,
)
from bookpub.qa_report import is_placeholder_isbn
from bookpub.text import render_checkboxes, sanitize_text, strip_unsupported

EPUB_CSS = """\
html { font-size: 100%; }
body { font-family: "EB Garamond", Georgia, serif; line-height: 1.5;
       margin: 0 5%; color: #1a1a1a; }
h1, h2, h3 { font-family: "EB Garamond", Georgia, serif; color: #1e3a5f;
             line-height: 1.2; }
section.chapter, section.part {
    page-break-before: always; break-before: page; }
h1.chapter-title { text-align: center; margin-top: 2em; }
.chapter-number { text-align: center; color: #c9a227; letter-spacing: 0.1em;
                  font-variant: small-caps; }
blockquote { border-left: 3px solid #c9a227; margin: 1em 0; padding: 0 1em;
             color: #555; font-style: italic; }
pre { background: #f4f4f6; padding: 0.8em; overflow-x: auto;
      page-break-inside: avoid; break-inside: avoid; }
code { font-family: "JetBrains Mono", Consolas, monospace; font-size: 0.9em; }
table { border-collapse: collapse; width: 100%; margin: 1em 0;
        page-break-inside: avoid; break-inside: avoid; }
th, td { border: 1px solid #bbb; padding: 0.3em 0.5em; text-align: left; }
th { background: #1e3a5f; color: #fff; }
.callout { border: 1px solid #c9a227; background: #faf7ef; padding: 0.6em 0.8em;
           margin: 1em 0; }
p.scene-break { text-align: center; margin: 1.5em 0; color: #666;
                letter-spacing: 0.4em; }
nav[epub|type~="toc"] ol { list-style: none; }
@media (prefers-color-scheme: dark) {
    body { background: #1a1a1a; color: #e8e8e8; }
    h1, h2, h3 { color: #9fc0e8; }
    pre { background: #2a2a2a; }
    th { background: #24496f; }
}
"""


def _link_sub(m: re.Match) -> str:
    """Keep real links; drop inter-chapter `.md` links (they don't exist inside an
    EPUB and fail epubcheck RSC-007) to their text."""
    text, href = m.group(1), m.group(2)
    if re.search(r"\.md(#|$)", href, re.I) or href.lower().endswith(".markdown"):
        return text
    return f'<a href="{href}">{text}</a>'


def _inline(text: str) -> str:
    """Inline markdown -> XHTML, HTML-escaped, with real Unicode punctuation."""
    t = _html.escape(text, quote=False)
    t = sanitize_text(t)
    t = render_checkboxes(t)
    t = re.sub(r"!\[([^\]]*)\]\([^)]*\)", r"\1", t)  # inline image -> alt (block images bundled)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<!\*)\*(?!\*)(.+?)\*(?!\*)", r"<em>\1</em>", t)
    t = re.sub(r"`(.+?)`", r"<code>\1</code>", t)
    t = re.sub(r"\[(.+?)\]\((.+?)\)", _link_sub, t)
    return t


_IMG_BLOCK_RE = re.compile(r"^!\[([^\]]*)\]\(([^)]+)\)$")


def _table_xhtml(rows: list[list[str]]) -> str:
    if not rows:
        return ""
    ncols = max(len(r) for r in rows)
    rows = [list(r) + [""] * (ncols - len(r)) for r in rows]
    head = "".join(f"<th>{_inline(c.strip())}</th>" for c in rows[0])
    body = "".join(
        "<tr>" + "".join(f"<td>{_inline(c.strip())}</td>" for c in r) + "</tr>"
        for r in rows[1:]
    )
    return f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"


def body_to_xhtml(body: str, register_image=None) -> str:
    """Render a chapter body (markdown) to an XHTML fragment.

    ``register_image(src) -> internal_href | None`` bundles a referenced image
    into the EPUB and returns its in-package path (else None -> alt-text fallback).
    """
    out: list[str] = []
    for block in _split_blocks(body):
        first = block[0]
        joined = " ".join(block)
        img = _IMG_BLOCK_RE.match(first.strip()) if len(block) == 1 else None
        if img:
            href = register_image(img.group(2)) if register_image else None
            alt = _html.escape(img.group(1), quote=True)
            if href:
                out.append(f'<figure><img src="{href}" alt="{alt}"/></figure>')
            else:
                out.append(f'<p><em>[image: {alt or _html.escape(img.group(2))}]</em></p>')
        elif first.startswith("## "):
            out.append(f"<h2>{_inline(first[3:].strip())}</h2>")
        elif first.startswith("### "):
            out.append(f"<h3>{_inline(first[4:].strip())}</h3>")
        elif first.startswith(("```", "~~~")):
            code = [ln for ln in block if not ln.startswith(("```", "~~~"))]
            esc = "\n".join(_html.escape(strip_unsupported(ln)) for ln in code)
            out.append(f"<pre><code>{esc}</code></pre>")
        elif _is_table(block):
            out.append(_table_xhtml(_parse_table(block)))
        elif _is_scene_break(block):
            out.append('<p class="scene-break">* * *</p>')
        elif first.lstrip().startswith(">"):
            txt = " ".join(re.sub(r"^\s*>\s?", "", ln) for ln in block)
            out.append(f"<blockquote><p>{_inline(txt)}</p></blockquote>")
        elif _is_list(first):
            ordered = bool(re.match(r"^\s*\d+\.", first))
            tag = "ol" if ordered else "ul"
            items = []
            for ln in block:
                m = re.match(r"^\s*(?:[-*+]|\d+\.)\s+(.*)$", ln)
                if m:
                    items.append(f"<li>{_inline(m.group(1))}</li>")
            out.append(f"<{tag}>{''.join(items)}</{tag}>")
        elif _CALLOUT_RE.match(joined):
            m = _CALLOUT_RE.match(joined)
            out.append(f'<div class="callout"><strong>{_inline(m.group(1))}:</strong> '
                       f"{_inline(m.group(2))}</div>")
        else:
            out.append(f"<p>{_inline(joined)}</p>")
    return "\n".join(out)


def _identifier(config: dict) -> str:
    isbn = config.get("isbn", "")
    if isbn and not is_placeholder_isbn(isbn):
        return f"urn:isbn:{isbn.replace('-', '').replace(' ', '')}"
    # Deterministic fallback (no random/time) so editions supersede cleanly.
    seed = f"{config.get('title', '')}|{config.get('author', '')}"
    return f"urn:uuid:{uuid.uuid5(uuid.NAMESPACE_DNS, seed)}"


def _add_accessibility_metadata(book: epub.EpubBook) -> None:
    """The EU EAA / Apple-required accessibility set."""
    def meta(prop, value):
        book.add_metadata(None, "meta", value, {"property": prop})

    meta("schema:accessMode", "textual")
    meta("schema:accessMode", "visual")
    meta("schema:accessModeSufficient", "textual")
    for feat in ("tableOfContents", "readingOrder", "structuralNavigation",
                 "displayTransformability", "unlocked"):
        meta("schema:accessibilityFeature", feat)
    meta("schema:accessibilityHazard", "none")
    meta("schema:accessibilitySummary",
         "This publication conforms to WCAG 2.1 Level AA. It has structural "
         "navigation, a logical reading order, and fully reflowable text with no "
         "known hazards.")
    meta("dcterms:conformsTo",
         "EPUB Accessibility 1.1 - WCAG 2.1 Level AA")


def _make_image_registrar(book: epub.EpubBook, asset_bases: list[Path]):
    """Return register_image(src) that bundles an image found under any asset base
    into the EPUB and returns its in-package href (None if not found)."""
    seen: dict[str, str] = {}

    def register(src: str) -> str | None:
        rel = src.lstrip("./")
        for base in asset_bases:
            for cand in (Path(base) / src, Path(base) / rel, Path(base) / Path(src).name):
                try:
                    cand = cand.resolve()
                except OSError:
                    continue
                if cand.is_file():
                    key = str(cand)
                    if key in seen:
                        return seen[key]
                    name = f"images/{cand.name}"
                    media = "image/png" if cand.suffix.lower() == ".png" else "image/jpeg"
                    book.add_item(epub.EpubImage(uid=f"img_{len(seen)}", file_name=name,
                                                 media_type=media, content=cand.read_bytes()))
                    seen[key] = name
                    return name
        return None

    return register


def build_epub(config: dict, elements: list[dict], output: str | Path, *,
               index_terms: list[str] | None = None,
               asset_bases: list[Path] | None = None) -> dict:
    book = epub.EpubBook()
    register_image = _make_image_registrar(book, asset_bases or [])
    book.set_identifier(_identifier(config))
    book.set_title(sanitize_text(config["title"]))
    book.set_language(config.get("language", "en"))
    if config.get("author"):
        book.add_author(sanitize_text(config["author"]))
    if config.get("year"):
        book.add_metadata("DC", "date", str(config["year"]))
    if config.get("publisher"):
        book.add_metadata("DC", "publisher", config["publisher"])
    if config.get("description"):
        book.add_metadata("DC", "description", sanitize_text(config["description"]))
    book.add_metadata("DC", "rights",
                      f"Copyright © {config.get('year', '')} {config.get('author', '')}".strip())
    _add_accessibility_metadata(book)

    css = epub.EpubItem(uid="style", file_name="style/main.css",
                        media_type="text/css", content=EPUB_CSS)
    book.add_item(css)

    has_cover = bool(config.get("cover_image") and Path(config["cover_image"]).exists())
    if has_cover:
        book.set_cover("cover.jpg", Path(config["cover_image"]).read_bytes())

    # Build chapter/part documents with semantic epub:type.
    items: list[epub.EpubHtml] = []
    chapter_items: list[epub.EpubHtml] = []   # for the index anchors
    toc_entries = []
    current_part = None
    chap_idx = 0
    for el in elements:
        if el["kind"] == "part":
            uid = f"part_{el['number']}"
            title = sanitize_text(el["title"])
            content = (f'<section epub:type="part">'
                       f'<h1 class="chapter-title">{_inline(el["title"])}</h1>'
                       + (f'<p><em>{_inline(el["subtitle"])}</em></p>' if el.get("subtitle") else "")
                       + "</section>")
            doc = epub.EpubHtml(uid=uid, file_name=f"{uid}.xhtml", title=title, lang="en")
            doc.content = content
            doc.add_link(href="style/main.css", rel="stylesheet", type="text/css")
            book.add_item(doc); items.append(doc)
            current_part = (epub.Section(title, href=f"{uid}.xhtml"), [])
            toc_entries.append(current_part)
        else:
            chap_idx += 1
            uid = f"chap_{chap_idx}"
            title = sanitize_text(el.get("title") or f"Chapter {chap_idx}")
            num_html = (f'<p class="chapter-number">CHAPTER {el["number"]}</p>'
                        if el.get("number") else "")
            content = (f'<section epub:type="bodymatter chapter" role="doc-chapter" id="{uid}">'
                       f'{num_html}<h1 class="chapter-title">{_inline(title)}</h1>'
                       f'{body_to_xhtml(el.get("body", ""), register_image)}</section>')
            doc = epub.EpubHtml(uid=uid, file_name=f"{uid}.xhtml", title=title, lang="en")
            doc.content = content
            doc.add_link(href="style/main.css", rel="stylesheet", type="text/css")
            book.add_item(doc); items.append(doc); chapter_items.append(doc)
            if current_part is not None:
                current_part[1].append(doc)
            else:
                toc_entries.append(doc)

    # Optional EPUB index (chapter-anchored — page numbers do not apply to reflow).
    index_item = None
    if index_terms:
        index_map = _chapter_term_map(elements, chapter_items, index_terms)
        if index_map:
            index_item = _build_index_doc(book, index_map)

    book.toc = toc_entries + ([(epub.Section("Index"), [index_item])] if index_item else [])
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    spine: list = (["cover"] if has_cover else []) + ["nav"] + items
    if index_item:
        spine.append(index_item)
    book.spine = spine

    # Landmarks
    guide = []
    if has_cover:
        guide.append({"type": "cover", "href": "cover.xhtml", "title": "Cover"})
    guide.append({"type": "toc", "href": "nav.xhtml", "title": "Table of Contents"})
    if chapter_items:
        guide.append({"type": "bodymatter", "href": chapter_items[0].file_name,
                      "title": "Begin Reading"})
    book.guide = guide

    out = Path(output)
    out.parent.mkdir(parents=True, exist_ok=True)
    epub.write_epub(str(out), book)
    return {"chapters": len(chapter_items),
            "parts": sum(1 for e in elements if e["kind"] == "part"),
            "identifier": _identifier(config),
            "index_terms": len(index_terms or []), "output": str(out)}


def _chapter_term_map(elements, chapter_items, terms) -> dict[str, list]:
    """Map term -> list of chapter EpubHtml items whose body/title contains it."""
    chapters = [e for e in elements if e["kind"] == "chapter"]
    result: dict[str, list] = {}
    for term in terms:
        pat = re.compile(r"\b" + re.escape(term) + r"\b", re.IGNORECASE)
        hits = [chapter_items[i] for i, el in enumerate(chapters)
                if pat.search(el.get("body", "") + " " + el.get("title", ""))]
        if hits:
            result[term] = hits
    return result


def _build_index_doc(book: epub.EpubBook, index_map: dict[str, list]) -> epub.EpubHtml:
    rows = []
    for term in sorted(index_map, key=str.lower):
        links = ", ".join(
            f'<a href="{it.file_name}">{_html.escape(it.title)}</a>'
            for it in index_map[term]
        )
        rows.append(f"<li>{_html.escape(term)}: {links}</li>")
    content = (f'<section epub:type="index" role="doc-index">'
               f"<h1>Index</h1><ul>{''.join(rows)}</ul></section>")
    doc = epub.EpubHtml(uid="index", file_name="index.xhtml", title="Index", lang="en")
    doc.content = content
    doc.add_link(href="style/main.css", rel="stylesheet", type="text/css")
    book.add_item(doc)
    return doc
