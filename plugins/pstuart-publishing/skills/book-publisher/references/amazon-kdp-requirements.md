# Amazon KDP & Multi-Platform Requirements

Reference specs for the `bookpub` pipeline. KDP is the baseline; IngramSpark,
Apple Books, Google Play, and Kobo notes follow.

## Print interior (paperback)

| Spec | Value |
|------|-------|
| Common trim sizes | 5×8, 5.25×8, **5.5×8.5** (default), 6×9, 7×10, 8.5×11 |
| Bleed | 0.125" on outside edges **only if** art touches the edge |
| Image resolution | 300 DPI minimum |
| Fonts | **All embedded** (the engine embeds EB Garamond + JetBrains Mono) |
| Color | RGB accepted by KDP; **CMYK + PDF/X-1a required by IngramSpark** (`bookpub.preflight.convert_to_cmyk`) |
| File | PDF, interior only — **never** the merged cover+interior file |

### Inside (gutter / binding) margin by page count

`bookpub.config.gutter_inches_for_pages` enforces these minimums:

| Page count | Min inside margin |
|------------|-------------------|
| ≤ 150 | 0.375" |
| 151–300 | 0.5" |
| 301–500 | 0.625" |
| 501–700 | 0.75" |
| 701+ | 0.875" |

Outside margins: 0.25" minimum (no bleed) / 0.375" (with bleed).

## Paperback cover (full wrap)

- Width = `2 × (trim_width + bleed) + spine`; height = `trim_height + 2 × bleed`.
- Spine width = `page_count × paper_thickness` (white 0.002252", cream 0.0025").
- **Spine text** only when the spine is wide enough to hold it: KDP requires
  **≥ 100 pages** for spine text; below that, leave the spine blank. (The older
  ~0.0625"/79-page figure is a geometric floor, not KDP's spine-text rule — use
  the 100-page rule for text.)
- Barcode safe area ~2"×1.2" lower-right of the back panel; the engine renders an
  EAN-13 from the paperback ISBN (`lib/cover_barcode`).
- 300 DPI; bleed 0.125" all sides.

## Kindle cover (ebook)

- Ideal 1600×2560 px, aspect ratio 1:1.6; min 625×1000; max 10,000 px long side.
- JPEG or TIFF, RGB. Title legible at thumbnail size.

## Ebook (reflowable EPUB)

- Upload EPUB 3 directly (KDP converts to KFX). `bookpub.epub_engine` emits
  EPUB 3.3 (epubcheck-clean) with NCX + Nav, nested TOC, and accessibility metadata.
- Validate with epubcheck (required) and Kindle Previewer 3 (`bookpub.preflight`).

## ISBN

- KDP provides a free ISBN, or supply your own (Bowker). **Each format needs its
  own ISBN** (paperback ≠ ebook ≠ hardcover) — `book.toml [isbn]` enforces this;
  the QA gate fails on placeholder ISBNs in a release build.

## Other channels (deltas from KDP)

- **IngramSpark**: PDF/X-1a:2001 + CMYK + embedded ICC OutputIntent; separate cover
  template; wider tolerances; hardcover case-wrap / dust-jacket math (future work).
- **Apple Books**: EPUB 3 with accessibility metadata **mandatory**; embedded fonts
  allowed; cover ≥ 1400 px wide.
- **Google Play Books / Kobo / Draft2Digital**: EPUB 3; ONIX or form metadata
  (`bookpub.onix`).
- **EU**: the European Accessibility Act (in force 2025-06-28) makes EPUBs without
  accessibility metadata non-saleable — the engine ships the full `schema:*` set.
