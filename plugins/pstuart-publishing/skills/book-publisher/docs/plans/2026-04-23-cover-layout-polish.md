# Cover Layout Polish Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restructure the paperback wrap + Kindle cover composers with zone-based vector layouts that match or exceed the legacy Pillow output. Front panel: title/subtitle/byline/series. Back panel: genre line, tagline, optional quote, blurb, author bio + optional photo, ISBN barcode + price, publisher/imprint info, series line. Spine: title/author/imprint. All vector, overlaid on AI-generated image-only backgrounds.

**Architecture:**
- Extract hardcoded palettes, primitives, and helpers into dedicated `lib/` modules (absorbs polish items #657, #661, #662, #663).
- Bundle EB Garamond OFL serif fonts in `templates/lib/fonts/` — solves Unicode rendering.
- Split each palette into `light_bg` and `dark_bg` variants (dark text vs light text) so the caller picks based on bitmap tone.
- Zone-based rendering: each panel is a sequence of named sub-zones with fixed y-coordinates, gracefully omitting absent BOOK_CONFIG fields.
- Real ISBN EAN-13 barcode via `python-barcode` library.
- Optional rectangular author photo.

**Tech Stack:** Python 3.10+, fpdf2 2.8+, pypdf 6+, python-barcode 0.16+, PIL, pytest.

---

## Phase 1: Infrastructure

Each task extracts one concern into its own `lib/` module with tests.

### Task 1: Bundle EB Garamond fonts + python-barcode dep

**Files:**
- Create: `templates/lib/fonts/EBGaramond-Regular.ttf`
- Create: `templates/lib/fonts/EBGaramond-Italic.ttf`
- Create: `templates/lib/fonts/EBGaramond-Bold.ttf`
- Create: `templates/lib/fonts/EBGaramond-BoldItalic.ttf`
- Create: `templates/lib/fonts/OFL.txt` (license)
- Create: `templates/lib/fonts/README.md` (attribution + version)
- Modify: `SKILL.md` (add `python-barcode` to dep list)

- [ ] **Step 1: Download EB Garamond from Google Fonts**

```bash
cd templates/lib/fonts
curl -sL -o EBGaramond.zip https://fonts.google.com/download?family=EB+Garamond
# alternate: fetch from github.com/googlefonts/ebgaramond-GF-fonts
unzip -j EBGaramond.zip 'static/EBGaramond-Regular.ttf' \
  'static/EBGaramond-Italic.ttf' \
  'static/EBGaramond-Bold.ttf' \
  'static/EBGaramond-BoldItalic.ttf' \
  'OFL.txt'
rm EBGaramond.zip
ls -la
```

Expected: 4 TTFs (~400KB each), OFL.txt.

- [ ] **Step 2: Add attribution README**

Create `templates/lib/fonts/README.md`:

```markdown
# Bundled fonts

EB Garamond — © 2017 Georg Duffner (https://fonts.google.com/specimen/EB+Garamond)
Licensed under SIL Open Font License v1.1 (see OFL.txt).

Used for vector text rendering in book covers. Chosen for:
- Classical proportions suitable for literary fiction
- Full Unicode support (en-dash, em-dash, smart quotes)
- Italic + bold variants for back-cover hierarchy
```

- [ ] **Step 3: Commit**

```bash
git add templates/lib/fonts/
git commit -m "chore(cover): bundle EB Garamond OFL serif fonts"
```

---

### Task 2: `lib/cover_fonts.py` — font registration helper

**Files:**
- Create: `templates/lib/cover_fonts.py`
- Create: `tests/test_cover_fonts.py`

Provides `register_fonts(pdf)` that adds EB Garamond variants to an FPDF instance. Returns a dict of face-key → registered-name for downstream text draws.

Signature:
```python
def register_fonts(pdf: FPDF) -> dict[str, str]:
    """Register EB Garamond on the pdf. Returns {'regular': family, 'italic': family, 'bold': family, 'bolditalic': family}."""
```

Tests cover: (a) registration succeeds without error, (b) registered family name appears in pdf.fonts, (c) `pdf.set_font(registered['regular'], size=12)` followed by `pdf.get_string_width('–')` (en-dash) works without UnicodeEncodeError.

Commit: `feat(cover): add font registration helper with Unicode-capable TTF`

---

### Task 3: `lib/cover_barcode.py` — ISBN → PNG

**Files:**
- Create: `templates/lib/cover_barcode.py`
- Create: `tests/test_cover_barcode.py`

Renders an EAN-13 barcode from an ISBN string to a PNG file on disk. Validates input (must be numeric, 13 digits or 13 with hyphens that get stripped; treat 10-digit ISBN as input error with clear message).

Signature:
```python
def render_isbn_barcode(isbn: str, output: Path, width_px: int = 600, height_px: int = 200) -> Path:
    """Render an EAN-13 barcode PNG from a 13-digit ISBN (with or without hyphens)."""
```

Tests cover: (a) valid 13-digit ISBN produces PNG, (b) hyphens in ISBN are stripped, (c) 10-digit ISBN raises ValueError, (d) invalid checksum raises ValueError, (e) output PNG dimensions match request.

Commit: `feat(cover): add ISBN EAN-13 barcode renderer`

---

## Phase 2: Style & decor primitives

### Task 4: `lib/cover_style.py` — palette light/dark variants

**Files:**
- Create: `templates/lib/cover_style.py`
- Create: `tests/test_cover_style.py`
- Modify: `templates/compose_paperback_wrap.py` (remove STYLE_PRESETS, import from lib)
- Modify: `templates/compose_kindle_cover.py` (import from lib)

Each palette has `light_bg` (dark text for light bitmap) and `dark_bg` (light text for dark bitmap). BOOK_CONFIG gains `background_tone: "light" | "dark"` with default `"light"` (most AI art we generate is cream-dominant per validation experience).

```python
STYLE_PRESETS = {
    "navy_gold": {
        "dark_bg":  {"title": (255, 255, 255), "body": (240, 240, 240), "accent": (218, 165, 32)},
        "light_bg": {"title": (30, 50, 90),    "body": (50, 60, 80),    "accent": (140, 100, 40)},
    },
    "burgundy_cream": {
        "dark_bg":  {"title": (245, 235, 220), "body": (230, 220, 210), "accent": (200, 170, 100)},
        "light_bg": {"title": (80, 20, 30),    "body": (60, 40, 30),    "accent": (140, 100, 40)},
    },
    # ... other 6 palettes with both variants
}

def resolve_colors(preset: str, tone: str = "light") -> dict:
    """Return the title/body/accent dict for the given palette + tone."""
```

Tests cover: (a) every palette has both dark_bg and light_bg keys, (b) resolve_colors raises ValueError on unknown preset, (c) resolve_colors defaults to light_bg when tone omitted, (d) backward compat: old `STYLE_PRESETS[preset]` access path still works via a compatibility shim if needed during the transition.

Commit: `feat(cover): extract palettes to lib/cover_style with light/dark variants`

---

### Task 5: `lib/cover_decor.py` — decorative vector primitives

**Files:**
- Create: `templates/lib/cover_decor.py`
- Create: `tests/test_cover_decor.py`

Vector helpers for decorative marks:
```python
def draw_flourish_rule(pdf, x_center, y, half_width, color):
    """Horizontal rule with small diamond at center. Legacy style."""

def draw_ink_rule(pdf, x_start, x_end, y, color, width=0.008):
    """Simple thin horizontal rule."""

def draw_panel_border(pdf, x, y, w, h, color, outer_width=0.02, inner_width=0.01, gap=0.015):
    """Double-line rectangle border inset within a panel."""
```

Tests cover each primitive writing to a PDF and surviving to vector content (inspection via pypdf page's `/Contents` stream shows drawing ops).

Commit: `feat(cover): add decorative vector primitives (flourish, ink rule, border)`

---

### Task 6: Refactor `cover_text.py` to use registered fonts

**Files:**
- Modify: `templates/lib/cover_text.py`
- Modify: `tests/test_cover_text.py`

Add `font_key: str = "regular"` parameter to each helper (`draw_centered_text`, `draw_left_aligned_block`, `draw_spine_text`). Use the mapping returned from `register_fonts()`. When caller hasn't registered fonts, fall back to Helvetica as before.

New: `draw_italic_block` and `draw_bold_text` convenience wrappers.

Tests extended: (a) draw_centered_text with en-dash text survives to vector extraction, (b) italic/bold variants apply the correct registered family.

Commit: `feat(cover): cover_text now uses registered TTF fonts for Unicode support`

---

## Phase 3: Paperback zone rendering

### Task 7: `lib/cover_config.py` — BOOK_CONFIG schema + validation

**Files:**
- Create: `templates/lib/cover_config.py`
- Create: `tests/test_cover_config.py`

Defines the full expanded schema as a TypedDict + runtime validator. New optional fields:
- `byline` (e.g., "by PATRICK STUART" — overrides auto-derivation from `author`)
- `genre_line` (e.g., "A Historical Conspiracy Thriller")
- `back_tagline` (distinct from front-cover `tagline` — usually more dramatic)
- `quote`, `quote_attribution`
- `blurb` (list of paragraph strings — replaces `back_body_lines`)
- `author_bio`, `author_bio_label` (default "About the Author")
- `author_photo` (Path | None)
- `isbn`, `price_us`
- `series_line_back`, `series_line_front`
- `publisher`, `publisher_city`, `imprint`
- `background_tone` ("light" | "dark", default "light")

Validator: `validate_and_defaults(raw: dict) -> dict` — fills defaults, coerces types, raises ValueError listing ALL missing required keys at once.

Required: `title`, `author`, `page_count` (>= 24).
All others optional with sensible defaults.

**Backwards compat:** if `back_body_lines` is present but `blurb` is not, convert automatically.

Tests cover: (a) minimal valid config passes, (b) missing title raises, (c) missing author raises, (d) back_body_lines → blurb migration works, (e) optional fields default correctly.

Commit: `feat(cover): expand BOOK_CONFIG schema with structured back-cover zones`

---

### Task 8: Zone helpers in `compose_paperback_wrap.py`

**Files:**
- Modify: `templates/compose_paperback_wrap.py`
- Create: `tests/test_compose_paperback_zones.py`

Add internal helpers (private to the module):

```python
def _render_front_panel(pdf, config, offsets, colors, fonts):
    # Zones top-to-bottom:
    # 1. Optional front quote (small italic, y=BLEED+SAFE+0.3)
    # 2. Title (size 42, bold, upper, y=safe_top+1.2)
    # 3. Subtitle (size 16, italic, y=title_y+0.9)
    # 4. Central visual region (empty — bitmap shows through)
    # 5. Decorative flourish rule (y=wrap_h-3.0)
    # 6. Byline (size 18, y=flourish_y+0.3) — "by AUTHOR" or overrideable
    # 7. Series line front (size 12, italic, y=wrap_h-BLEED-SAFE-0.3)

def _render_back_panel(pdf, config, offsets, colors, fonts):
    # Zones top-to-bottom:
    # 1. Genre line (size 14, italic, y=BLEED+SAFE+0.5)
    # 2. Flourish rule
    # 3. Back tagline (size 18, italic, centered)
    # 4. Ink rule
    # 5. Optional quote block (italic + attribution)
    # 6. Ink rule
    # 7. Blurb paragraphs (size 10, justified left, 0.18in line height)
    # 8. Ink rule
    # 9. Author bio label (bold) + bio paragraph
    # 10. Author photo (optional rect, bottom-left)
    # 11. ISBN barcode + price (bottom-right rectangle)
    # 12. Publisher/imprint line (very bottom, center)
    # 13. Series line back (very bottom, center)

def _render_spine(pdf, config, offsets, colors, fonts):
    # Existing spine_text logic, plus:
    # - Imprint mark at bottom of spine (if spine_width >= 0.5")
```

Each function returns None, mutates pdf in place. All zones gracefully skip when their source BOOK_CONFIG field is empty.

Tests cover each zone function:
- Render to a real PDF, extract text via pypdf, assert all expected strings appear
- Tests with minimal config (no optional fields) assert no crashes and no text from absent zones

Commit: `feat(cover): add zone-based rendering helpers for paperback panels`

---

### Task 9: Rewire `compose_wrap` main to use zone helpers

**Files:**
- Modify: `templates/compose_paperback_wrap.py`
- Modify: `tests/test_compose_paperback_wrap.py`

Replace the inline text placement code in `compose_wrap` with three calls: `_render_front_panel`, `_render_back_panel`, `_render_spine`. `compose_wrap` becomes ~40 LOC (from ~90 LOC).

Resolve fonts + colors once at top, pass into each zone helper.

Update the existing 4 tests to assert that ALL zones rendered (title, author, back_tagline, blurb, isbn, publisher, series lines). Add 2 new tests:
- Full-config test: every optional zone populated, every string extracted via pdftotext.
- Minimal-config test: only title/author/page_count set, compose succeeds, PDF produced with just essentials.

Commit: `refactor(cover): compose_wrap delegates to zone renderers`

---

## Phase 4: Kindle + fixtures

### Task 10: Update `compose_kindle_cover.py` for new font + palette system

**Files:**
- Modify: `templates/compose_kindle_cover.py`
- Modify: `tests/test_compose_kindle_cover.py`

Use `register_fonts(pdf)` + `resolve_colors(preset, tone)`. Add front-cover zones (title, subtitle, byline, series). Accept optional `kindle_quote` field for a front pull-quote.

Also fix the subtitle y-coordinate collision (#663): use the `accent` color (gold) for subtitle since it reads over both light and dark bitmap regions.

Tests: extract title/author from rasterized JPEG not possible (pixels, not vector), but assert JPEG produced + dimensions correct. Add a test that internally renders to PDF before raster and extracts text — proves vector was used before rasterization.

Commit: `feat(kindle): use zone rendering + gold accent subtitle for contrast`

---

### Task 11: Update fixture `BOOK_CONFIG` + end-to-end smoke

**Files:**
- Modify: `templates/fixtures/sample_book/BOOK_CONFIG.py`
- Modify: `templates/fixtures/sample_book/cover-assets/wrap_art.png` (regenerate with better size)

Expand the fixture BOOK_CONFIG to exercise every new field. The smoke test (from Task 14 of the original plan) should produce a wrap PDF with every zone populated.

Commit: `chore(cover): fixture exercises full BOOK_CONFIG schema`

---

## Phase 5: Validation on 1600-novel

### Task 12: Re-run pipeline against The Folio Conspiracy Book 1

**Files (outside the skill repo):**
- Modify: `/Users/pstuart/Documents/Books/1600-novel/publishing/BOOK_CONFIG.py`

Expand the real BOOK_CONFIG with:
- `genre_line: "A Historical Conspiracy Thriller"`
- `blurb: [paragraph1, paragraph2, paragraph3]` (convert existing back_body_lines)
- `author_bio`, `author_bio_label`
- `isbn` (user provides a real ISBN or a placeholder 13-digit)
- `price_us: "$18.99"`
- `publisher`, `publisher_city`, `imprint`
- `series_line_back: "The Folio Conspiracy • Book I"`
- `series_line_front: "A Novel of Elizabethan England"`
- `background_tone: "light"`

Copy new lib/ modules into `1600-novel/publishing/lib/`. Run compose_paperback_wrap.py + compose_kindle_cover.py. Visual review in Preview.

Expected: legacy-quality back cover structure with all zones, vector text, real ISBN barcode, crisp EB Garamond typography.

No commit — validation only, changes are local to 1600-novel.

---

## Self-review

### Spec coverage
Every user-listed requirement mapped to a task:
- Front: title/subtitle/byline → Task 8 (_render_front_panel zones 2/3/6)
- Spine: title/author/imprint → Task 8 (_render_spine)
- Back blurb → Task 8 zone 7
- Quote option → Task 8 zone 5
- Photo area → Task 8 zone 10
- Barcode + pricing → Task 8 zone 11 + Task 3
- Publishing info → Task 8 zone 12
- Vector over image-only background → architecture constraint, honored throughout

### Absorbed polish items
- #657 STYLE_PRESETS to lib → Task 4
- #661 Unicode TTF font → Tasks 1, 2, 6
- #662 Palette light/dark variants → Task 4
- #663 Subtitle y-coord collision → Task 10 (gold accent)

### Deferred
- #658 composition overrides (orthogonal — layout work doesn't need it)
- #659 motif aspect ratio (motif not in active use)
- #660 negative_prompt on zgen_runner (nice-to-have, not blocking)

### Open caveats
- EB Garamond fonts: download from Google Fonts requires network. If the implementation subagent can't fetch, fallback is `brew install font-eb-garamond` on macOS or vendoring the specific TTFs from googlefonts/ebgaramond-GF-fonts GitHub repo.
- Author photo: legacy layout used a rectangular area. If photo isn't exactly that aspect ratio we crop to fit. This may not be ideal for all photos — future enhancement could accept crop hints.
- KDP bulk/series imprint: the "publisher" string is rendered at bottom back cover. This is not the same as KDP's imprint metadata (separate field during upload). Users should set both.

---

## Execution handoff

Execute via superpowers:subagent-driven-development. Fresh subagent per task, spec compliance review on every task, code quality review on substantive tasks (skip for pure config/scaffolding like Task 1). Use model:sonnet for mechanical tasks; opus only if a task needs architectural judgment (none expected in this plan — everything is mechanical given the spec).
