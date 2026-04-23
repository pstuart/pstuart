# Cover Generation Reference

## Architecture

Cover generation is a two-phase pipeline with one interactive approval gate:

1. **`generate_cover_art.py`** — interactive. Drafts 3 prompt variants per surface (2 on-palette + 1 wildcard). Calls `zgen` serially. Contact-sheet UX. Seed-locked refinement loop.
2. **`compose_*.py`** — mechanical. Takes approved PNGs and emits print-ready outputs.

Approved art lives in `cover-assets/` and is committed to git. Candidate drafts live in `cover-assets/candidates/` and are ignored.

## The seed-lock rule

Z Image Turbo anchors composition to the seed. During refinement:
- **Prompt changes + same seed** → same composition, different style (what you usually want)
- **`reroll` command** → new seed, completely new composition (use sparingly)

Session state in `cover-session.json` records every seed so art is reproducible.

## Prompt slots

Every prompt is assembled from four slots:

```
{surface_tag} {genre} {composition} {palette}, {mood},
no text, no lettering, no typography,
composition tolerates print bleed, 300 DPI print quality, painterly finish
```

The "no text" tags are critical — vector text is drawn by fpdf2 on top, so any baked-in text on the AI art is redundant and usually wrong.

## Paperback wrap: front + spine + back as one canvas

The wrap art is one wide image (4992 × 2624) that bleeds across front + spine + back. `compose_paperback_wrap.py` places it as a full-bleed image and draws vector text into each panel's safe zone.

Panel coordinates (in inches, measured from left edge of wrap):

| Panel | x range | Usage |
|---|---|---|
| Back | 0 → (BLEED + TRIM_WIDTH) | tagline, body copy, features, bio |
| Spine | back_end → back_end + spine_width | rotated title + author text |
| Front | spine_end → wrap_width | title, subtitle, author |

Safe margins: 0.25" from trim edge for all text.

## Kindle: forced raster, vector-first internally

Kindle covers must be flat JPEG per KDP spec. We still layout in fpdf2 (bitmap + vector text) and rasterize only as the final step. This keeps one mental model across all surfaces — a tweak to paperback title positioning automatically applies to Kindle.

## Chapter motif: opt-in banner

If `assets/chapter_motif.png` exists, `generate_pdf.py` renders it as a 40%-of-page banner at the top of each chapter opener, with the chapter number and title drawn below as vector text. Absent the file, behavior is unchanged (current chapter-opener rendering).

## Validation

The load-bearing test:

```bash
pdftotext cover-assets/paperback_wrap.pdf -
```

Title and author **must** appear in the output. If they don't, text was rasterized somewhere it shouldn't have been.
