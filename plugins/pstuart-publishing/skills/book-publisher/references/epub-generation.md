# EPUB Generation (`bookpub.epub_engine`)

Produces an EPUB 3.3 that passes epubcheck with zero errors/warnings and is
saleable on every major store, including the EU after the Accessibility Act.

## Structure

- **Package (.opf)**: `dc:identifier` is `urn:isbn:` when a real ebook ISBN exists,
  else a deterministic `urn:uuid5(title|author)` so re-editions supersede cleanly;
  `dc:title`, `dc:language`, `dc:creator`, `dc:date`, `dc:publisher`, `dc:rights`,
  `dc:description`.
- **Navigation**: both `EpubNcx` (EPUB2 back-compat) and `EpubNav` (EPUB3). The
  TOC is **nested** — Part → [chapters].
- **Content**: each chapter is a `<section epub:type="bodymatter chapter"
  role="doc-chapter">`; parts use `epub:type="part"`; the index uses
  `epub:type="index"`. Cover page is in the spine.
- **Landmarks** (`book.guide`): cover, toc, and a bodymatter "Begin Reading" target.

## Accessibility metadata (required)

Emitted via `add_metadata(None, "meta", value, {"property": "..."})`:

| Property | Value(s) |
|----------|----------|
| `schema:accessMode` | `textual`, `visual` |
| `schema:accessModeSufficient` | `textual` |
| `schema:accessibilityFeature` | `tableOfContents`, `readingOrder`, `structuralNavigation`, `displayTransformability`, `unlocked` |
| `schema:accessibilityHazard` | `none` |
| `schema:accessibilitySummary` | human-readable WCAG 2.1 AA statement |
| `dcterms:conformsTo` | `EPUB Accessibility 1.1 - WCAG 2.1 Level AA` |

The QA gate (`bookpub.qa_report`) fails an EPUB missing `schema:accessMode` or
`schema:accessibilitySummary`.

## Styling

- One stylesheet (`style/main.css`). It pairs `break-*` with legacy
  `page-break-*` for reflow engines, scopes code to JetBrains Mono, gives tables
  `break-inside: avoid`, and includes a `prefers-color-scheme: dark` block.
- Prose is normalised by `bookpub.text`, so EPUB and PDF share real em-dashes and
  identical block parsing — the two formats cannot drift.

## Index & page-list

- The EPUB index is **chapter-anchored** (`index.xhtml` links each term to the
  chapters containing it) — page numbers do not apply to reflowable text.
- `epub:type="page-list"` print-page parity is built when the PDF and EPUB are
  produced together so the authoritative PDF page map is available (Phase 5+).

## Validation

```bash
epubcheck book.epub                 # required: 0 errors
# Kindle Previewer 3 (optional, macOS) for KFX/enhanced-typesetting preview
python3 -m bookpub.qa_report --epub book.epub
```
