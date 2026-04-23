# Book-Publisher Skill — Cover Vector-Overlay Redesign

**Date:** 2026-04-22
**Author:** Patrick Stuart (brainstormed with Claude Opus 4.7)
**Status:** Approved, ready for implementation planning
**Affects:** `~/.claude/skills/book-publisher/`

## Problem

The current book-publisher skill renders covers entirely through Pillow: background colors and gradients combine with title/subtitle/author text, and the whole thing rasterizes to a single flat PNG at 300 DPI. The PNG is then embedded in the book's PDF as a full-bleed bitmap page.

Two consequences:

1. **Title and author text are pixels, not vectors.** When Amazon KDP or a reader zooms into the cover PDF, the text shows raster artifacts that vector glyphs would not. Print shops and professional book covers expect vector text over bitmap artwork; the current pipeline cannot provide that.
2. **The "artwork" is a solid color or gradient.** There is no actual cover illustration or photography — just color blocks behind text. This produces an unmistakably amateur look regardless of how good the typography is.

## Goal

Move cover generation (and selected interior decorative pages) to an **AI-generated bitmap artwork + vector text overlay** pipeline. Text is drawn directly by fpdf2 over the bitmap so it remains vector in the print PDF. Artwork is generated locally via `zgen` (Z Image Turbo via Draw Things CLI).

## Scope

Three surfaces receive the new pipeline:

1. **Paperback wrap** — PDF output with full-bleed bitmap + vector text for front, spine, and back panels
2. **Kindle cover** — JPEG output (KDP requires flat image) with vector-style text layout still used internally, rasterized only at the final step
3. **Interior decorative pages** — part-dividers and a single reused chapter-opener motif, composited into the existing interior PDF

Out of scope: the interior body pages themselves (already work well), EPUB cover (already uses the Kindle JPEG).

## Decisions (from brainstorming)

| # | Decision | Choice |
|---|---|---|
| 1 | Surfaces to redesign | Paperback wrap + Kindle + interior decorative pages |
| 2 | Image generation tool | `zgen` for singles; `zchat --batch` rejected in favor of serial `zgen` calls |
| 3 | PDF library | `fpdf2` everywhere (single dependency; vector text over bitmap is straightforward) |
| 4a | Prompt authorship | Claude drafts 3 variants per surface; 2 on-palette, 1 deliberate wildcard |
| 4b | Iteration model | Serial per-image generation + seed-locked refinement loop |
| 5a | Interior scope | Part-dividers + single reused chapter-opener motif with varied vector chapter-number overlay |
| 5b | Spine treatment | Art bleeds across front → spine → back as one wide canvas |
| 6 | Backward compatibility | Clean replacement of existing cover templates; no dual-path fallback |
| 7 | Prompt transparency | Show full prompt before first `zgen` call; auto-fire on subsequent refinements |
| 8 | Image generation serialization | Always one `zgen` call at a time, never batched (durable preference, saved to memory) |

## Architecture

Four scripts form a linear pipeline with one explicit approval gate between creative and mechanical work.

```
BOOK_CONFIG.py  ─┐
                 │
                 ▼
   ┌──────────────────────────┐
   │  generate_cover_art.py   │ ← creative loop (interactive, iterative)
   │  - drafts 3 prompts/surf │
   │  - serial zgen calls     │
   │  - session state         │
   │  - seed-locked refines   │
   └──────────────────────────┘
                 │
                 ▼
     publishing/cover-assets/
     ├─ wrap_art.png         (4992×2624, full wrap canvas)
     ├─ kindle_art.png       (1600×2560, portrait)
     ├─ chapter_motif.png    (1664×2560 → cropped to 1650×2550)
     └─ cover-session.json   (prompts, seeds, approvals, history)
                 │
                 ├─────────────────┬─────────────────┐
                 ▼                 ▼                 ▼
   compose_paperback_wrap.py  compose_kindle    compose_interior_art
   - full wrap PDF            - flat JPEG       - motif PNG →
   - vector text over bitmap  - text baked in     referenced by
   - spine calc from page#    - 1600×2560         generate_pdf.py
                 │                 │                 │
                 ▼                 ▼                 ▼
        paperback_wrap.pdf   kindle_cover.jpg    (used in interior)
```

### Key architectural properties

- **One approval gate** — `generate_cover_art.py` is the only interactive script; everything downstream is mechanical and repeatable.
- **Re-runnable composition** — change book title, subtitle, author, back-cover copy, or page count, re-run only the three `compose_*` scripts; approved art stays untouched.
- **Deterministic via seeds** — `cover-session.json` records every seed, so any approved art can be reproduced or refined without reshuffling noise.
- **Vector text survives to print** — paperback + interior text stays vector because fpdf2 draws via `set_font()`/`text()` on top of `image()`-placed bitmaps. Kindle is the sole forced-raster surface (KDP JPEG requirement).

## Components

### 1. `generate_cover_art.py` — creative loop (interactive)

**Responsibility:** drive all `zgen` calls, curate candidate output, let the user approve or refine. Zero PDF/composition logic.

**Inputs:**
- `BOOK_CONFIG` (title, subtitle, genre, tagline, style preset)
- Existing `cover-session.json` if present (for resume)

**Outputs:**
- 3 canonical art PNGs in `publishing/cover-assets/` (`wrap_art.png`, `kindle_art.png`, `chapter_motif.png`)
- Candidate drafts in `publishing/cover-assets/candidates/`
- `publishing/cover-assets/cover-session.json`

**Flow:**

1. Read book metadata. Derive style hints from chosen preset (e.g., `navy_gold` → "navy palette, gold accents, authoritative mood").
2. **Claude drafts prompts.** For each surface (wrap / kindle / motif), produce 3 variants: 2 on-palette variants differing in composition (e.g., mountain vs ocean), 1 deliberate wildcard that breaks the palette.
3. **Show the drafted prompts to the user** before any `zgen` call. User can edit before firing.
4. **Serial `zgen` calls**, one image at a time. Print status line after each:
   ```
   [1/9] wrap variant 1 (mountain)  ... done → candidates/wrap_v1_candidate_1.png
   ```
   User can `Ctrl-C` mid-sequence if early candidates reveal the prompt direction is wrong.
5. **Contact-sheet UX**: after all 9 complete, print filenames grouped by surface. User responds in one line:
   - `W1 K2 M3` → approve those, exit
   - `refine wrap` → enter refinement sub-loop for wrap only
   - `reroll kindle` → new seed, regenerate kindle variants
   - Combinations allowed: `W1 refine kindle M3`
6. **Refinement sub-loop** (seed-locked): prompt is rewritten via natural-language tweak ("more muted, less orange"), seed is preserved, single `zgen` call, one new image. User approves or continues refining. After the first refinement iteration, auto-fire without re-showing the prompt unless user says "show prompt".
7. On approval, promote candidate to canonical name, update session.json atomically.

### 2. `compose_paperback_wrap.py` — full-wrap PDF (mechanical)

**Responsibility:** produce `paperback_wrap.pdf` — a single-page PDF at exact wrap dimensions with the bitmap background and vector text overlaid.

**Inputs:** `wrap_art.png`, `BOOK_CONFIG`, `PAGE_COUNT`, `PAPER_TYPE`

**Output:** `publishing/cover-assets/paperback_wrap.pdf`

**Flow:**

1. Compute wrap dimensions:
   - `spine_width = PAGE_COUNT * PAPER_THICKNESS[PAPER_TYPE]` (inches)
   - `wrap_width = 2 * (TRIM_WIDTH + BLEED) + spine_width`
   - `wrap_height = TRIM_HEIGHT + 2 * BLEED`
2. Create single-page fpdf2 document at `(wrap_width × wrap_height)` inches.
3. `self.image(wrap_art.png, 0, 0, wrap_width, wrap_height)` — full-bleed bitmap.
4. Compute panel offsets:
   - Back panel: `x ∈ [0, BLEED + TRIM_WIDTH]`
   - Spine: `x ∈ [BLEED + TRIM_WIDTH, BLEED + TRIM_WIDTH + spine_width]`
   - Front panel: `x ∈ [BLEED + TRIM_WIDTH + spine_width, wrap_width]`
5. Draw vector text layers:
   - **Front:** title, subtitle, author at safe-zone coordinates
   - **Back:** hook, body, features list, author bio, website, price, barcode keep-out (empty rect)
   - **Spine:** vertical text (title / author) using `with self.rotation(90, ...)`; skip spine text if `spine_width < 0.0625"`
6. Text colors come from `STYLE_PRESETS[preset]`.
7. Save.

### 3. `compose_kindle_cover.py` — forced-raster JPEG (mechanical)

**Responsibility:** produce `kindle_cover.jpg` at 1600×2560 using the same vector-first approach internally, rasterized only as the final step.

**Inputs:** `kindle_art.png`, `BOOK_CONFIG`

**Output:** `publishing/cover-assets/kindle_cover.jpg` (q95)

**Flow:**

1. Generate a minimal fpdf2 PDF at Kindle dimensions (`1600px × 2560px` → `5.333" × 8.533"` at 300 DPI). Bitmap background + vector title/subtitle/author overlay.
2. Rasterize to PNG via `pdf2image.convert_from_path(dpi=300)`.
3. Flatten to RGB, save as JPEG quality 95.

**Why route through PDF first instead of drawing directly in Pillow?** To keep one mental model for text layout across all cover surfaces. The rasterization step is the very last operation, not the baseline. A change to how titles render on paperback covers picks up automatically on Kindle.

### 4. `compose_interior_art.py` — chapter motif staging (trivial)

**Responsibility:** copy the approved `chapter_motif.png` from `cover-assets/` to the canonical location the existing interior PDF generator expects (`assets/chapter_motif.png`), with any required resize/crop.

**Why a script at all (vs cp command)?** Keeps `generate_pdf.py` decoupled — it reads a file at a known path. Any future art direction changes route through a single known point.

### 5. Modified scripts

- **`generate_pdf.py`** — adds an optional `render_chapter_motif` call on each chapter opener page, rendering `assets/chapter_motif.png` as a half-page banner at the top with the chapter number drawn as vector text below.
- **`generate_epub.py`** — reads `cover-assets/kindle_cover.jpg` as the EPUB cover image (was: Pillow-rendered PNG).
- **`add_covers_to_pdf.py`** — reads `paperback_wrap.pdf` directly, extracts front/back pages as vector PDF pages via pypdf (no rasterization anywhere).

## Data model

### Directory layout

```
BookProject/
├── manuscript/                         # unchanged
├── assets/
│   └── chapter_motif.png               # staged by compose_interior_art.py
└── publishing/
    ├── BOOK_CONFIG.py                  # single source of truth
    ├── generate_cover_art.py           # NEW — creative loop
    ├── compose_paperback_wrap.py       # NEW — replaces create_paperback_cover.py
    ├── compose_kindle_cover.py         # NEW — replaces create_kindle_cover.py
    ├── compose_interior_art.py         # NEW
    ├── generate_pdf.py                 # MODIFIED — renders chapter_motif on openers
    ├── generate_epub.py                # MODIFIED — embeds kindle_cover.jpg
    ├── add_covers_to_pdf.py            # MODIFIED — reads paperback_wrap.pdf
    └── cover-assets/                   # NEW directory
        ├── cover-session.json
        ├── candidates/                 # .gitignored
        │   ├── wrap_v1_candidate_{1..3}.png
        │   ├── kindle_v1_candidate_{1..3}.png
        │   └── motif_v1_candidate_{1..3}.png
        ├── wrap_art.png                # APPROVED, committed to git
        ├── kindle_art.png              # APPROVED, committed to git
        ├── chapter_motif.png           # APPROVED, committed to git
        ├── paperback_wrap.pdf          # OUTPUT
        └── kindle_cover.jpg            # OUTPUT
```

### Canonical dimensions

| Surface | zgen size | Final size | Rationale |
|---|---|---|---|
| Paperback wrap | **4992 × 2624** | trimmed to exact wrap: `2·(5.5+0.125) + spine_in` × `8.75` at 300 DPI | largest multiple-of-64 canvas that exceeds wrap dims |
| Kindle | **1600 × 2560** | 1600 × 2560 JPEG | native multiples of 64; matches KDP spec |
| Chapter motif | **1664 × 2560** | cropped to 1650 × 2550 | 5.5×8.5 at 300 DPI |

### `cover-session.json` schema

```json
{
  "schema_version": 1,
  "book_title": "...",
  "created": "2026-04-22T12:34:56Z",
  "last_modified": "2026-04-22T13:02:11Z",
  "style_preset": "navy_gold",
  "surfaces": {
    "wrap": {
      "approved_file": "wrap_art.png",
      "approved_seed": 4201983,
      "approved_prompt": "cinematic book cover wrap art, moody navy palette...",
      "history": [
        {"iteration": 1, "prompt": "...", "seed": 111, "approved": false, "timestamp": "..."},
        {"iteration": 2, "prompt": "...", "seed": 111, "approved": true, "timestamp": "..."}
      ],
      "zgen_args": {"width": 4992, "height": 2624, "steps": null}
    },
    "kindle": { "...": "same shape" },
    "motif":  { "...": "same shape" }
  }
}
```

**Seed semantics.** The seed is sticky across refinement iterations (composition preserved, style tweaked). A *reroll* is the only operation that picks a new seed. This distinction is the single most important UX rule — it is documented in both the script's help text and the `SKILL.md` troubleshooting section.

### .gitignore additions

```
publishing/cover-assets/candidates/
```

Approved PNGs **are** committed (source-of-truth for the book, repo alone is enough to reproduce). Only noisy drafts are ignored.

## Prompt templates

Claude synthesizes prompts from 4 slots:

```
{genre_modifier} {composition} {palette_from_preset} {mood_tags},
no text, no lettering, no typography,
composition {edge_crop_clause}, 300 DPI print quality, painterly finish
```

**Example — leadership book, `navy_gold` preset, wrap surface:**

- Variant 1 (on-palette, mountain):
  > "cinematic landscape book-cover art, wide panoramic composition of a weathered mountain range at dawn, deep navy midnight sky transitioning to warm gold horizon, solitary figure silhouette far-left third, authoritative and contemplative mood, no text, no lettering, no typography, composition tolerates full-width print bleed, 300 DPI print quality, painterly finish"
- Variant 2 (on-palette, ocean):
  > "cinematic landscape book-cover art, wide panoramic composition of a becalmed ocean at twilight, navy water and sky with gold lighthouse beam on right third, no text, ...
- Variant 3 (wildcard, deliberate palette break):
  > "cinematic landscape book-cover art, wide panoramic composition of a rust-red canyon at golden hour, warm copper tones with deep shadow, no text, ...

Kindle and motif use the same 4-slot structure with portrait composition and (for motif) "lots of negative space, suitable for text overlay in bottom third".

## Error handling

Only boundaries warrant validation; internal calls trust each other.

| Boundary | Check | Failure mode |
|---|---|---|
| `zgen` binary on PATH | `shutil.which()` at script start | Fail fast: `"zgen not found — this skill requires /Users/pstuart/bin/zgen"` |
| `zgen` returns non-zero or no file | Check subprocess return + file existence | Print stderr from zgen, retry that single image (not the whole sequence), don't write session.json on failure |
| `BOOK_CONFIG` required keys | Validate at script top | List all missing keys in one error |
| `style_preset` name | Match against `STYLE_PRESETS` dict | Suggest closest via `difflib.get_close_matches` |
| `PAGE_COUNT` set before composing wrap | Refuse if 0/None | `"Set PAGE_COUNT in BOOK_CONFIG before composing — spine depends on it"` |
| Canonical art file present before compose | `Path.exists()` check | `"Run generate_cover_art.py first"` |
| `chapter_motif.png` optional in interior | Existence check, skip silently if absent | Falls back to current "no motif" behavior |

**Session state integrity:** writes are atomic (`write temp → os.replace()`). Schema version is validated on read. `Ctrl-C` mid-generation leaves session in pre-iteration state because the write only happens on successful approval.

**Deliberately not handled:** disk space, permissions, malformed PNGs from `zgen`, custom RGB tuple type errors. Underlying libraries raise clear exceptions.

**Error format (stderr, to user):**

```
ERROR in compose_paperback_wrap.py:
  Missing canonical art: publishing/cover-assets/wrap_art.png

  Fix: run `python3 generate_cover_art.py` first, approve a wrap candidate.
```

## Testing

### Unit-testable

| Layer | Approach |
|---|---|
| Dimension math (spine, wrap, offsets) | Pure-function tests: `PAGE_COUNT=200, PAPER=white` → spine = 0.4504". Five representative cases. |
| Session state round-trip | Write → reload → assert equality. Catches schema drift. |
| Prompt builder | Given preset + title, prompt contains required substrings (`navy`, `no text`, `300 DPI`). Not exact-match — just contract. |
| Vector text survives to PDF | Generate sample wrap with placeholder art, open with `pypdf`, extract text, assert title/author present. **This is the load-bearing test — proves we actually get vector text, not raster.** |
| Kindle JPEG output | Generate sample, assert 1600×2560 dimensions and RGB color mode. |

### Deliberately not tested

- Visual quality of generated art (can't assert "this PNG looks good")
- `zgen` / Draw Things behavior (external tool)
- fpdf2 rendering fidelity (trust library)
- Vector text visual quality (human review only)

### Human validation (added to `SKILL.md` checklist)

```
Cover validation:
  □ Open paperback_wrap.pdf in Preview — zoom to 400%, verify title
    text stays crisp (proves vector, not raster)
  □ Extract text from paperback_wrap.pdf via `pdftotext` — title and
    author must appear in output
  □ Open kindle_cover.jpg at 100% — title readable, no JPEG artifacts
    on text edges
  □ Spine text reads correctly (if spine ≥ 0.0625")
  □ Chapter motif renders on every chapter opener
  □ Bleed extends full 0.125" on all edges of paperback_wrap.pdf
```

### Fixture

Maintain one minimal fixture book in `templates/fixtures/sample_book/` with a 1KB placeholder art PNG already approved. `compose_*` scripts can smoke-run against the fixture during skill maintenance without needing `zgen` available.

## Migration / backward compatibility

Clean replacement. Specifically:

- `templates/create_paperback_cover_template.py` → **deleted**, replaced by `templates/compose_paperback_wrap_template.py`
- `templates/create_kindle_cover_template.py` → **deleted**, replaced by `templates/compose_kindle_cover_template.py`
- New templates: `templates/generate_cover_art_template.py`, `templates/compose_interior_art_template.py`
- `templates/add_covers_to_pdf_template.py` → **modified** to read PDF instead of PNG
- `SKILL.md` — cover generation section rewritten end-to-end; validation checklist augmented
- `references/cover-generation.md` — rewritten to reflect the new pipeline

Existing books already published: no automatic migration. Users regenerate covers on demand using the new pipeline. The old PNG output path is gone.

## Implementation phases (suggested ordering)

The implementation plan will flesh these out. Suggested phase ordering for the plan:

1. **Phase 1 — Scaffolding.** Create `cover-assets/` directory convention, session.json schema + atomic write helpers, `.gitignore` updates. No behavior yet.
2. **Phase 2 — `generate_cover_art.py`.** Serial zgen loop, prompt drafting, contact sheet, refinement loop. This is the largest single script.
3. **Phase 3 — `compose_paperback_wrap.py`.** The load-bearing vector-over-bitmap surface. Unit tests for dimension math here.
4. **Phase 4 — `compose_kindle_cover.py`.** Thin script, reuses paperback text-layout helpers.
5. **Phase 5 — `compose_interior_art.py` + `generate_pdf.py` chapter-motif integration.**
6. **Phase 6 — `add_covers_to_pdf.py` and `generate_epub.py` updates.**
7. **Phase 7 — SKILL.md + references rewrites, delete old templates, add fixture book.**

Each phase must touch ≤ 5 files (per global CLAUDE.md rule) and pass verification before the next begins.

## Open questions (for implementation)

1. What font(s) should vector text use on covers? The existing skill loads system TTF fonts for the interior. Inherit same fonts, or allow a cover-specific override in `BOOK_CONFIG`?
2. Should the chapter motif overlay include a thin rule/divider line between the motif banner and the chapter title, or just whitespace?
3. Where does `chapter_motif.png` live on first run — does the interior PDF generator require it (breaking existing books without one) or is it strictly opt-in?

These are genuine open items that the implementation plan or a brief follow-up should resolve before coding begins.

---

## Rollback plan

If the new pipeline proves worse in practice:
1. `git revert` the commits that deleted the old templates
2. Old `create_paperback_cover_template.py` and `create_kindle_cover_template.py` are recovered
3. No user data is lost — the old PNGs never interacted with the new `cover-assets/` directory
