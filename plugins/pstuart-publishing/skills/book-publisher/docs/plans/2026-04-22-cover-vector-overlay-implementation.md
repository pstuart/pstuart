# Cover Vector-Overlay — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the book-publisher skill's flat-color Pillow cover pipeline with an AI-generated bitmap + vector-text-overlay pipeline that produces print-grade paperback wrap PDFs, Kindle JPEGs, and interior decorative pages.

**Architecture:** Four-script pipeline (`generate_cover_art.py` → three `compose_*.py` scripts) with a single interactive approval gate, backed by shared helper modules under `templates/lib/` for dimension math, session state, prompt assembly, and the zgen subprocess wrapper. Vector text is drawn by fpdf2 on top of bitmap artwork generated serially via `zgen` (Z Image Turbo / Draw Things CLI).

**Tech Stack:** Python 3.11+, fpdf2 (PDF), Pillow (image ops), pypdf (PDF inspection), pdf2image (JPEG rasterization for Kindle), pytest (testing), `/Users/pstuart/bin/zgen` (local image generator — external).

**Spec:** `~/.claude/skills/book-publisher/docs/specs/2026-04-22-cover-vector-overlay-design.md`

---

## Preamble for implementers

### Resolution of spec "open questions"

The spec ended with three open questions. The implementer works with these resolutions:

1. **Font choice for cover vector text** — inherit the interior TTF fonts already loaded by `generate_pdf_template.py` (no new `BOOK_CONFIG` key). If a future book needs different cover fonts, that's a separate follow-up.
2. **Chapter motif banner divider** — whitespace only, no horizontal rule between motif and chapter title. The motif art can include its own decorative edge if desired.
3. **`chapter_motif.png` requirement** — strictly opt-in. `generate_pdf_template.py` calls `Path(asset_path).exists()`; if absent, falls back to current no-motif behavior. Existing books do not break.

### Version control note

`~/.claude` is not a git repository by default. If the skill directory is not under git:
- Option A: `cd ~/.claude/skills/book-publisher && git init` once before starting. All commit steps work.
- Option B: Skip every `git commit` step. Tasks still produce working files. Skill is version-controlled via filesystem snapshots only.

The commit messages below are still useful as task-summary documentation even if not actually executed.

### Running tests

Tests live in `~/.claude/skills/book-publisher/tests/`. Run with:

```bash
cd ~/.claude/skills/book-publisher
python3 -m pytest tests/ -v
```

Required test deps (install once):
```bash
pip3 install pytest fpdf2 pypdf Pillow pdf2image
```

### File-size budget

Every file created or modified must stay under 400 LOC (per global `~/.claude/CLAUDE.md` rule). If a task produces a file over budget, split into `_core.py` + `_helpers.py` within the same task.

### Task touch-count

Each task touches ≤ 5 files (per global phase rule). Violations are plan bugs — call them out, don't proceed.

---

## File structure

### New files

| Path | Responsibility | Est. LOC |
|---|---|---|
| `templates/lib/__init__.py` | package marker | 1 |
| `templates/lib/cover_dimensions.py` | spine width, wrap canvas, panel offsets — pure math | ~80 |
| `templates/lib/cover_session.py` | atomic JSON session read/write + schema validation | ~110 |
| `templates/lib/cover_prompts.py` | 4-slot prompt builder, 3-variant generator (2 on-palette + 1 wildcard) | ~140 |
| `templates/lib/zgen_runner.py` | `zgen` subprocess wrapper, file existence check, retry | ~70 |
| `templates/lib/cover_text.py` | fpdf2 vector text helpers (panel-relative drawing, spine rotation) | ~180 |
| `templates/generate_cover_art_template.py` | creative loop, contact sheet, refinement | ~330 |
| `templates/compose_paperback_wrap_template.py` | full wrap PDF with vector text overlay | ~280 |
| `templates/compose_kindle_cover_template.py` | Kindle JPEG via PDF → raster pipeline | ~140 |
| `templates/compose_interior_art_template.py` | stage motif PNG to `assets/` | ~60 |
| `templates/fixtures/sample_book/BOOK_CONFIG.py` | minimal fixture config | ~40 |
| `templates/fixtures/sample_book/cover-assets/wrap_art.png` | 1KB placeholder | binary |
| `templates/fixtures/sample_book/cover-assets/kindle_art.png` | 1KB placeholder | binary |
| `templates/fixtures/sample_book/cover-assets/chapter_motif.png` | 1KB placeholder | binary |
| `tests/__init__.py` | package marker | 1 |
| `tests/conftest.py` | pytest fixtures | ~40 |
| `tests/test_cover_dimensions.py` | unit tests for dimension math | ~80 |
| `tests/test_cover_session.py` | unit tests for session round-trip + atomicity | ~90 |
| `tests/test_cover_prompts.py` | unit tests for prompt builder | ~70 |
| `tests/test_zgen_runner.py` | unit tests for subprocess wrapper (mocked) | ~60 |
| `tests/test_compose_paperback_wrap.py` | integration — vector text survives to PDF | ~80 |
| `tests/test_compose_kindle_cover.py` | integration — 1600×2560 JPEG produced | ~50 |
| `tests/test_compose_interior_art.py` | integration — file copied with correct dims | ~40 |

### Modified files

| Path | Change |
|---|---|
| `SKILL.md` | cover section rewrite + new validation checklist |
| `references/cover-generation.md` | rewrite to match new pipeline |
| `templates/generate_pdf_template.py` | add opt-in `chapter_motif.png` rendering on openers |
| `templates/add_covers_to_pdf_template.py` | read `paperback_wrap.pdf` instead of PNG wrap |
| `templates/generate_epub_template.py` | embed `kindle_cover.jpg` as EPUB cover |

### Deleted files

| Path |
|---|
| `templates/create_paperback_cover_template.py` |
| `templates/create_kindle_cover_template.py` |

---

## Tasks

### Task 1: Test infrastructure and directory scaffolding

**Files:**
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`
- Create: `templates/lib/__init__.py`
- Create: `pytest.ini`

- [ ] **Step 1: Create empty package markers**

```bash
cd ~/.claude/skills/book-publisher
touch tests/__init__.py templates/lib/__init__.py
```

- [ ] **Step 2: Write pytest configuration**

Create `pytest.ini`:

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -ra --strict-markers
```

- [ ] **Step 3: Write shared pytest fixtures**

Create `tests/conftest.py`:

```python
"""Shared pytest fixtures for book-publisher tests."""
from pathlib import Path
import shutil
import tempfile
import pytest


@pytest.fixture
def tmp_cover_assets(tmp_path: Path) -> Path:
    """Empty cover-assets directory in a temp dir."""
    d = tmp_path / "cover-assets"
    d.mkdir()
    (d / "candidates").mkdir()
    return d


@pytest.fixture
def sample_book_config() -> dict:
    """Minimal BOOK_CONFIG dict for testing."""
    return {
        "title": "Sample Title",
        "subtitle": "A Test Subtitle",
        "author": "Test Author",
        "tagline": "A hook line.",
        "style_preset": "navy_gold",
        "year": "2026",
        "page_count": 200,
        "paper_type": "white",
    }


@pytest.fixture
def placeholder_png(tmp_path: Path) -> Path:
    """1x1 transparent PNG placeholder for tests that need art input."""
    from PIL import Image
    p = tmp_path / "placeholder.png"
    Image.new("RGB", (1664, 2560), color=(30, 58, 95)).save(p)
    return p
```

- [ ] **Step 4: Verify pytest runs (with zero tests)**

```bash
cd ~/.claude/skills/book-publisher
python3 -m pytest tests/ -v
```

Expected: `no tests ran in 0.XXs` — **this confirms pytest is wired up**.

- [ ] **Step 5: Commit**

```bash
git add pytest.ini tests/__init__.py tests/conftest.py templates/lib/__init__.py
git commit -m "chore: scaffold pytest infrastructure for book-publisher skill"
```

---

### Task 2: `cover_dimensions.py` — pure dimension math

**Files:**
- Create: `templates/lib/cover_dimensions.py`
- Create: `tests/test_cover_dimensions.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_cover_dimensions.py`:

```python
"""Tests for cover dimension calculations."""
import pytest
from templates.lib.cover_dimensions import (
    spine_width_inches,
    wrap_canvas_inches,
    panel_offsets_inches,
    PAPER_THICKNESS,
    BLEED_INCHES,
    TRIM_WIDTH_INCHES,
    TRIM_HEIGHT_INCHES,
)


def test_white_paper_spine_200_pages():
    assert spine_width_inches(200, "white") == pytest.approx(0.4504, rel=1e-4)


def test_cream_paper_spine_300_pages():
    assert spine_width_inches(300, "cream") == pytest.approx(0.7500, rel=1e-4)


def test_unknown_paper_type_raises():
    with pytest.raises(ValueError, match="paper_type"):
        spine_width_inches(200, "glossy")


def test_wrap_canvas_200_pages_white():
    w, h = wrap_canvas_inches(200, "white")
    # 2 * (5.5 + 0.125) + 0.4504 = 11.7004
    assert w == pytest.approx(11.7004, rel=1e-4)
    # 8.5 + 2 * 0.125 = 8.75
    assert h == pytest.approx(8.75, rel=1e-4)


def test_panel_offsets_split_wrap_correctly():
    offsets = panel_offsets_inches(200, "white")
    # Back: starts at 0, ends at BLEED + TRIM_WIDTH = 5.625
    assert offsets["back_start"] == pytest.approx(0.0, rel=1e-4)
    assert offsets["back_end"] == pytest.approx(5.625, rel=1e-4)
    # Spine: 5.625 to 5.625 + 0.4504 = 6.0754
    assert offsets["spine_start"] == pytest.approx(5.625, rel=1e-4)
    assert offsets["spine_end"] == pytest.approx(6.0754, rel=1e-4)
    # Front: 6.0754 to wrap_width
    assert offsets["front_start"] == pytest.approx(6.0754, rel=1e-4)
    assert offsets["front_end"] == pytest.approx(11.7004, rel=1e-4)
```

- [ ] **Step 2: Run tests — confirm they fail**

```bash
python3 -m pytest tests/test_cover_dimensions.py -v
```

Expected: `ModuleNotFoundError: No module named 'templates.lib.cover_dimensions'` — 5 errors.

- [ ] **Step 3: Write minimal implementation**

Create `templates/lib/cover_dimensions.py`:

```python
"""Pure-function cover dimension calculations.

Trade paperback 5.5 x 8.5 at 300 DPI. All public functions return inches
and are pure — no I/O, no config reads.
"""
from typing import Literal, TypedDict

TRIM_WIDTH_INCHES = 5.5
TRIM_HEIGHT_INCHES = 8.5
BLEED_INCHES = 0.125
SAFE_MARGIN_INCHES = 0.25

# Amazon KDP published paper-thickness constants.
PAPER_THICKNESS = {
    "white": 0.002252,
    "cream": 0.002500,
}

PaperType = Literal["white", "cream"]


class PanelOffsets(TypedDict):
    back_start: float
    back_end: float
    spine_start: float
    spine_end: float
    front_start: float
    front_end: float


def spine_width_inches(page_count: int, paper_type: PaperType) -> float:
    """Compute spine width in inches from page count and paper type."""
    if paper_type not in PAPER_THICKNESS:
        raise ValueError(
            f"Unknown paper_type {paper_type!r}. "
            f"Expected one of: {sorted(PAPER_THICKNESS)}"
        )
    return page_count * PAPER_THICKNESS[paper_type]


def wrap_canvas_inches(
    page_count: int, paper_type: PaperType
) -> tuple[float, float]:
    """Return (width, height) of full wrap canvas in inches, including bleed."""
    spine = spine_width_inches(page_count, paper_type)
    width = 2 * (TRIM_WIDTH_INCHES + BLEED_INCHES) + spine
    height = TRIM_HEIGHT_INCHES + 2 * BLEED_INCHES
    return (width, height)


def panel_offsets_inches(
    page_count: int, paper_type: PaperType
) -> PanelOffsets:
    """Compute x-axis offsets for each wrap panel in inches.

    Panels laid out left-to-right when cover is flat: BACK | SPINE | FRONT.
    """
    spine = spine_width_inches(page_count, paper_type)
    wrap_w, _ = wrap_canvas_inches(page_count, paper_type)

    back_start = 0.0
    back_end = BLEED_INCHES + TRIM_WIDTH_INCHES
    spine_start = back_end
    spine_end = spine_start + spine
    front_start = spine_end
    front_end = wrap_w

    return {
        "back_start": back_start,
        "back_end": back_end,
        "spine_start": spine_start,
        "spine_end": spine_end,
        "front_start": front_start,
        "front_end": front_end,
    }
```

- [ ] **Step 4: Run tests — confirm they pass**

```bash
python3 -m pytest tests/test_cover_dimensions.py -v
```

Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
git add templates/lib/cover_dimensions.py tests/test_cover_dimensions.py
git commit -m "feat(cover): add pure dimension math for wrap canvas and panels"
```

---

### Task 3: `cover_session.py` — atomic JSON state

**Files:**
- Create: `templates/lib/cover_session.py`
- Create: `tests/test_cover_session.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_cover_session.py`:

```python
"""Tests for cover-session.json read/write."""
import json
from pathlib import Path
import pytest
from templates.lib.cover_session import (
    CoverSession,
    load_session,
    save_session_atomic,
    SCHEMA_VERSION,
    IncompatibleSchemaError,
)


def test_new_session_has_current_schema(tmp_cover_assets: Path):
    s = CoverSession.new(book_title="Test", style_preset="navy_gold")
    assert s.schema_version == SCHEMA_VERSION
    assert s.book_title == "Test"
    assert s.surfaces == {}


def test_round_trip_preserves_state(tmp_cover_assets: Path):
    s1 = CoverSession.new(book_title="Test", style_preset="navy_gold")
    s1.record_iteration(
        surface="wrap",
        prompt="cinematic mountain",
        seed=4201983,
        approved=False,
    )
    save_session_atomic(s1, tmp_cover_assets / "cover-session.json")

    s2 = load_session(tmp_cover_assets / "cover-session.json")
    assert s2.book_title == s1.book_title
    assert s2.surfaces["wrap"]["history"][0]["seed"] == 4201983
    assert s2.surfaces["wrap"]["history"][0]["approved"] is False


def test_atomic_write_survives_crash(tmp_cover_assets: Path, monkeypatch):
    """Simulate a crash between tmp-write and rename — existing file preserved."""
    target = tmp_cover_assets / "cover-session.json"
    target.write_text(json.dumps({"schema_version": 1, "book_title": "old"}))

    from templates.lib import cover_session as cs
    original_replace = cs.os.replace

    def crash_before_rename(*args, **kwargs):
        raise OSError("simulated crash")

    monkeypatch.setattr(cs.os, "replace", crash_before_rename)

    s = CoverSession.new(book_title="new", style_preset="navy_gold")
    with pytest.raises(OSError):
        save_session_atomic(s, target)

    # Original file content preserved
    assert json.loads(target.read_text())["book_title"] == "old"


def test_incompatible_schema_raises(tmp_cover_assets: Path):
    target = tmp_cover_assets / "cover-session.json"
    target.write_text(json.dumps({"schema_version": 999, "book_title": "future"}))
    with pytest.raises(IncompatibleSchemaError):
        load_session(target)


def test_approve_sets_canonical_fields(tmp_cover_assets: Path):
    s = CoverSession.new(book_title="Test", style_preset="navy_gold")
    s.record_iteration(surface="kindle", prompt="p1", seed=111, approved=True)
    assert s.surfaces["kindle"]["approved_seed"] == 111
    assert s.surfaces["kindle"]["approved_prompt"] == "p1"
```

- [ ] **Step 2: Run tests — confirm they fail**

```bash
python3 -m pytest tests/test_cover_session.py -v
```

Expected: `ModuleNotFoundError` / 5 errors.

- [ ] **Step 3: Write minimal implementation**

Create `templates/lib/cover_session.py`:

```python
"""Atomic read/write of cover-session.json with schema versioning."""
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
import json
import os
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1


class IncompatibleSchemaError(Exception):
    """Raised when on-disk schema_version exceeds what this code can read."""


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


@dataclass
class CoverSession:
    schema_version: int = SCHEMA_VERSION
    book_title: str = ""
    style_preset: str = ""
    created: str = field(default_factory=_now_iso)
    last_modified: str = field(default_factory=_now_iso)
    surfaces: dict[str, dict[str, Any]] = field(default_factory=dict)

    @classmethod
    def new(cls, book_title: str, style_preset: str) -> "CoverSession":
        return cls(book_title=book_title, style_preset=style_preset)

    def record_iteration(
        self,
        surface: str,
        prompt: str,
        seed: int,
        approved: bool,
        width: int | None = None,
        height: int | None = None,
    ) -> None:
        """Append an iteration to the given surface's history.

        If approved=True, also sets approved_file/seed/prompt canonical fields.
        """
        entry = self.surfaces.setdefault(
            surface,
            {"history": [], "zgen_args": {}},
        )
        entry["history"].append(
            {
                "iteration": len(entry["history"]) + 1,
                "prompt": prompt,
                "seed": seed,
                "approved": approved,
                "timestamp": _now_iso(),
            }
        )
        if width is not None and height is not None:
            entry["zgen_args"] = {"width": width, "height": height}
        if approved:
            entry["approved_prompt"] = prompt
            entry["approved_seed"] = seed
            entry["approved_file"] = f"{surface}_art.png"
        self.last_modified = _now_iso()


def save_session_atomic(session: CoverSession, path: Path) -> None:
    """Write session to path atomically (temp + os.replace).

    If os.replace fails, original file is untouched.
    """
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(asdict(session), indent=2))
    try:
        os.replace(tmp, path)
    except OSError:
        tmp.unlink(missing_ok=True)
        raise


def load_session(path: Path) -> CoverSession:
    """Load session from disk. Raises IncompatibleSchemaError if newer schema."""
    data = json.loads(path.read_text())
    if data.get("schema_version", 0) > SCHEMA_VERSION:
        raise IncompatibleSchemaError(
            f"File schema {data['schema_version']} exceeds supported {SCHEMA_VERSION}"
        )
    return CoverSession(**data)
```

- [ ] **Step 4: Run tests — confirm they pass**

```bash
python3 -m pytest tests/test_cover_session.py -v
```

Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
git add templates/lib/cover_session.py tests/test_cover_session.py
git commit -m "feat(cover): add atomic JSON session state with schema versioning"
```

---

### Task 4: `cover_prompts.py` — 4-slot prompt builder

**Files:**
- Create: `templates/lib/cover_prompts.py`
- Create: `tests/test_cover_prompts.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_cover_prompts.py`:

```python
"""Tests for prompt builder."""
from templates.lib.cover_prompts import (
    PALETTE_DESCRIPTIONS,
    build_variants,
    build_single_prompt,
)


def test_single_prompt_contains_required_tags():
    p = build_single_prompt(
        surface="wrap",
        genre="leadership",
        composition="weathered mountain range at dawn",
        palette_key="navy_gold",
        mood="authoritative and contemplative",
    )
    assert "no text" in p
    assert "no lettering" in p
    assert "no typography" in p
    assert "300 DPI" in p
    assert "navy" in p.lower()
    assert "mountain" in p.lower()


def test_wrap_variants_include_wildcard():
    variants = build_variants(
        surface="wrap", genre="leadership", palette_key="navy_gold"
    )
    assert len(variants) == 3
    # First two respect palette, third is deliberate wildcard
    assert "navy" in variants[0]["prompt"].lower()
    assert "navy" in variants[1]["prompt"].lower()
    # Wildcard label set
    assert variants[0]["is_wildcard"] is False
    assert variants[1]["is_wildcard"] is False
    assert variants[2]["is_wildcard"] is True


def test_kindle_prompts_specify_portrait_composition():
    variants = build_variants(
        surface="kindle", genre="leadership", palette_key="navy_gold"
    )
    for v in variants:
        assert "portrait" in v["prompt"].lower() or "vertical" in v["prompt"].lower()


def test_motif_prompts_reserve_text_space():
    variants = build_variants(
        surface="motif", genre="leadership", palette_key="navy_gold"
    )
    for v in variants:
        assert "negative space" in v["prompt"].lower() or "text overlay" in v["prompt"].lower()


def test_unknown_palette_raises():
    import pytest
    with pytest.raises(KeyError):
        build_single_prompt(
            surface="wrap",
            genre="x",
            composition="y",
            palette_key="neon_pink",
            mood="m",
        )
```

- [ ] **Step 2: Run tests — confirm they fail**

```bash
python3 -m pytest tests/test_cover_prompts.py -v
```

Expected: `ModuleNotFoundError`.

- [ ] **Step 3: Write minimal implementation**

Create `templates/lib/cover_prompts.py`:

```python
"""Prompt builder for zgen cover art.

Generates 3 variants per surface: 2 on-palette (different compositions)
+ 1 deliberate wildcard that breaks the palette to surface unexpected options.
"""
from typing import TypedDict

# Palette → descriptor string injected into prompts.
PALETTE_DESCRIPTIONS = {
    "navy_gold": "deep navy and warm gold palette, authoritative mood",
    "burgundy_cream": "burgundy and cream palette, literary mood",
    "teal_coral": "teal and coral palette, modern fresh mood",
    "black_silver": "black and silver palette, dramatic mood",
    "earth_warm": "warm earth tones, grounded spiritual mood",
    "purple_gold": "deep purple and gold palette, transformative luxurious mood",
    "forest_cream": "forest green and cream palette, natural wise mood",
    "minimal_white": "minimal white palette with single accent, clean modern mood",
}

# Compositions per surface. Each surface has (on-palette-1, on-palette-2, wildcard).
_COMPOSITIONS = {
    "wrap": [
        ("weathered mountain range at dawn, solitary figure silhouette far-left third", False),
        ("becalmed ocean at twilight, distant lighthouse on right third", False),
        ("rust-red canyon at golden hour, warm copper tones with deep shadow", True),
    ],
    "kindle": [
        ("single weathered mountain peak centered lower-third, portrait composition", False),
        ("vertical forest path receding into mist, portrait composition", False),
        ("abstract geometric mandala, vertical symmetry, portrait composition", True),
    ],
    "motif": [
        ("minimalist geometric mountain silhouette, lots of negative space, suitable for text overlay in bottom third", False),
        ("simple flowing line-art wave pattern, lots of negative space, suitable for text overlay in bottom third", False),
        ("intricate botanical line drawing, lots of negative space, suitable for text overlay in bottom third", True),
    ],
}

_SURFACE_TAGS = {
    "wrap": "cinematic landscape book-cover art, wide panoramic composition",
    "kindle": "cinematic portrait book-cover art",
    "motif": "abstract chapter-opener motif",
}


class PromptVariant(TypedDict):
    prompt: str
    composition: str
    is_wildcard: bool


_WILDCARD_PALETTES = [
    "rust-red and deep ember palette",
    "cobalt and acid-green palette",
    "ochre and charcoal palette",
]


def build_single_prompt(
    surface: str,
    genre: str,
    composition: str,
    palette_key: str,
    mood: str,
    wildcard_palette: str | None = None,
) -> str:
    """Assemble a single zgen prompt from slotted pieces."""
    if wildcard_palette is not None:
        palette_desc = wildcard_palette
    else:
        palette_desc = PALETTE_DESCRIPTIONS[palette_key]
    surface_tag = _SURFACE_TAGS[surface]
    return (
        f"{surface_tag}, {genre} book, {composition}, {palette_desc}, {mood}, "
        "no text, no lettering, no typography, "
        "composition tolerates print bleed, 300 DPI print quality, painterly finish"
    )


def build_variants(
    surface: str,
    genre: str,
    palette_key: str,
    mood: str = "evocative",
) -> list[PromptVariant]:
    """Build 3 prompt variants for a surface: 2 on-palette + 1 wildcard."""
    if palette_key not in PALETTE_DESCRIPTIONS:
        raise KeyError(f"Unknown palette_key {palette_key!r}")

    compositions = _COMPOSITIONS[surface]
    variants: list[PromptVariant] = []
    wildcard_idx = 0

    for composition, is_wildcard in compositions:
        if is_wildcard:
            wildcard_palette = _WILDCARD_PALETTES[wildcard_idx % len(_WILDCARD_PALETTES)]
            wildcard_idx += 1
            prompt = build_single_prompt(
                surface=surface,
                genre=genre,
                composition=composition,
                palette_key=palette_key,
                mood=mood,
                wildcard_palette=wildcard_palette,
            )
        else:
            prompt = build_single_prompt(
                surface=surface,
                genre=genre,
                composition=composition,
                palette_key=palette_key,
                mood=mood,
            )
        variants.append(
            {"prompt": prompt, "composition": composition, "is_wildcard": is_wildcard}
        )

    return variants
```

- [ ] **Step 4: Run tests — confirm they pass**

```bash
python3 -m pytest tests/test_cover_prompts.py -v
```

Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
git add templates/lib/cover_prompts.py tests/test_cover_prompts.py
git commit -m "feat(cover): add 4-slot prompt builder with wildcard variant"
```

---

### Task 5: `zgen_runner.py` — subprocess wrapper

**Files:**
- Create: `templates/lib/zgen_runner.py`
- Create: `tests/test_zgen_runner.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_zgen_runner.py`:

```python
"""Tests for zgen subprocess wrapper."""
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest
from templates.lib.zgen_runner import (
    run_zgen,
    ZgenNotFoundError,
    ZgenFailureError,
)


def test_zgen_not_on_path_raises(monkeypatch):
    monkeypatch.setattr("shutil.which", lambda _: None)
    with pytest.raises(ZgenNotFoundError):
        run_zgen(prompt="x", output=Path("/tmp/out.png"), width=832, height=1472, seed=1)


def test_successful_run_returns_path(tmp_path: Path, monkeypatch):
    out = tmp_path / "out.png"
    monkeypatch.setattr("shutil.which", lambda _: "/usr/bin/zgen")

    def fake_run(*args, **kwargs):
        out.write_bytes(b"fake png")
        m = MagicMock()
        m.returncode = 0
        m.stderr = ""
        return m

    monkeypatch.setattr("subprocess.run", fake_run)

    result = run_zgen(prompt="x", output=out, width=832, height=1472, seed=1)
    assert result == out
    assert result.exists()


def test_nonzero_returncode_raises_with_stderr(tmp_path: Path, monkeypatch):
    monkeypatch.setattr("shutil.which", lambda _: "/usr/bin/zgen")

    def fake_run(*args, **kwargs):
        m = MagicMock()
        m.returncode = 1
        m.stderr = "model load failed"
        return m

    monkeypatch.setattr("subprocess.run", fake_run)

    with pytest.raises(ZgenFailureError, match="model load failed"):
        run_zgen(
            prompt="x", output=tmp_path / "out.png",
            width=832, height=1472, seed=1,
        )


def test_missing_output_file_raises(tmp_path: Path, monkeypatch):
    """zgen returns 0 but produces no file — should raise."""
    monkeypatch.setattr("shutil.which", lambda _: "/usr/bin/zgen")

    def fake_run(*args, **kwargs):
        m = MagicMock()
        m.returncode = 0
        m.stderr = ""
        return m

    monkeypatch.setattr("subprocess.run", fake_run)

    with pytest.raises(ZgenFailureError, match="did not produce output"):
        run_zgen(
            prompt="x", output=tmp_path / "missing.png",
            width=832, height=1472, seed=1,
        )
```

- [ ] **Step 2: Run tests — confirm they fail**

```bash
python3 -m pytest tests/test_zgen_runner.py -v
```

Expected: `ModuleNotFoundError`.

- [ ] **Step 3: Write minimal implementation**

Create `templates/lib/zgen_runner.py`:

```python
"""Wrapper around the local /Users/pstuart/bin/zgen CLI.

Serial calls only — per user preference, never batch image generation.
Each run_zgen() invocation produces exactly one image or raises.
"""
from pathlib import Path
import shutil
import subprocess

ZGEN_BIN_DEFAULT = "/Users/pstuart/bin/zgen"


class ZgenNotFoundError(RuntimeError):
    """zgen binary missing from PATH."""


class ZgenFailureError(RuntimeError):
    """zgen returned non-zero or produced no output file."""


def _ensure_multiple_of_64(value: int, name: str) -> int:
    if value % 64 != 0:
        raise ValueError(f"{name}={value} must be a multiple of 64 for zgen")
    return value


def run_zgen(
    prompt: str,
    output: Path,
    width: int,
    height: int,
    seed: int,
    steps: int | None = None,
    bin_path: str = ZGEN_BIN_DEFAULT,
) -> Path:
    """Invoke zgen once to produce exactly one image at `output`.

    Raises ZgenNotFoundError or ZgenFailureError on any problem.
    """
    if shutil.which(bin_path) is None:
        raise ZgenNotFoundError(
            f"zgen not found at {bin_path!r}. "
            "This skill requires the local Draw Things CLI wrapper. "
            "See ~/.claude/projects/-Users-pstuart-Development/memory/"
            "feedback_image_generation_zchat.md"
        )

    _ensure_multiple_of_64(width, "width")
    _ensure_multiple_of_64(height, "height")

    output.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        bin_path,
        "-W", str(width),
        "-H", str(height),
        "-s", str(seed),
        "-o", str(output),
    ]
    if steps is not None:
        cmd.extend(["-S", str(steps)])
    cmd.append(prompt)

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise ZgenFailureError(
            f"zgen exited {result.returncode}: {result.stderr.strip()}"
        )
    if not output.exists():
        raise ZgenFailureError(
            f"zgen returned 0 but did not produce output file {output}"
        )
    return output
```

- [ ] **Step 4: Run tests — confirm they pass**

```bash
python3 -m pytest tests/test_zgen_runner.py -v
```

Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add templates/lib/zgen_runner.py tests/test_zgen_runner.py
git commit -m "feat(cover): add zgen subprocess wrapper with serial single-image calls"
```

---

### Task 6: `cover_text.py` — fpdf2 vector text helpers

**Files:**
- Create: `templates/lib/cover_text.py`
- Create: `tests/test_cover_text.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_cover_text.py`:

```python
"""Tests for fpdf2 vector text helpers (integration)."""
from pathlib import Path
from fpdf import FPDF
from pypdf import PdfReader
from templates.lib.cover_text import (
    draw_centered_text,
    draw_left_aligned_block,
    draw_spine_text,
)


def _extract_text(pdf_path: Path) -> str:
    reader = PdfReader(str(pdf_path))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def test_centered_text_appears_in_extracted_pdf(tmp_path: Path):
    pdf = FPDF(unit="in", format=(5.5, 8.5))
    pdf.add_page()
    draw_centered_text(
        pdf, text="TEST TITLE", x_center=2.75, y=4.0, size_pt=32,
        color=(255, 255, 255),
    )
    out = tmp_path / "out.pdf"
    pdf.output(str(out))
    assert "TEST TITLE" in _extract_text(out)


def test_left_block_wraps_and_survives_to_pdf(tmp_path: Path):
    pdf = FPDF(unit="in", format=(5.5, 8.5))
    pdf.add_page()
    draw_left_aligned_block(
        pdf,
        lines=["First line of back cover copy.", "Second line."],
        x=0.5, y=2.0, size_pt=10,
        color=(20, 20, 20), line_height_in=0.18,
    )
    out = tmp_path / "out.pdf"
    pdf.output(str(out))
    text = _extract_text(out)
    assert "First line" in text
    assert "Second line" in text


def test_spine_text_survives_when_spine_wide_enough(tmp_path: Path):
    pdf = FPDF(unit="in", format=(12, 8.75))
    pdf.add_page()
    draw_spine_text(
        pdf, text="SAMPLE TITLE / Author Name",
        spine_start_x=5.625, spine_width=0.5, wrap_height=8.75,
        size_pt=10, color=(255, 255, 255),
    )
    out = tmp_path / "out.pdf"
    pdf.output(str(out))
    assert "SAMPLE TITLE" in _extract_text(out)
```

- [ ] **Step 2: Run tests — confirm they fail**

```bash
python3 -m pytest tests/test_cover_text.py -v
```

Expected: `ModuleNotFoundError`.

- [ ] **Step 3: Write minimal implementation**

Create `templates/lib/cover_text.py`:

```python
"""fpdf2 vector text helpers for cover composition.

All functions draw vector text that survives as vector in the output PDF
(proven by pypdf text extraction in tests).
"""
from fpdf import FPDF

RGB = tuple[int, int, int]


def _set_font(pdf: FPDF, size_pt: float) -> None:
    """Use the first registered TTF or fall back to Helvetica."""
    if pdf.fonts:
        first = next(iter(pdf.fonts.values()))
        family = first.get("fontkey", "Helvetica") if isinstance(first, dict) else "Helvetica"
    else:
        family = "Helvetica"
    pdf.set_font(family, size=size_pt)


def draw_centered_text(
    pdf: FPDF,
    text: str,
    x_center: float,
    y: float,
    size_pt: float,
    color: RGB,
) -> None:
    """Draw a single line of text centered horizontally at x_center, baseline y."""
    _set_font(pdf, size_pt)
    pdf.set_text_color(*color)
    string_w = pdf.get_string_width(text)
    pdf.text(x_center - string_w / 2, y, text)


def draw_left_aligned_block(
    pdf: FPDF,
    lines: list[str],
    x: float,
    y: float,
    size_pt: float,
    color: RGB,
    line_height_in: float,
) -> None:
    """Draw a stack of left-aligned lines starting at (x, y) descending."""
    _set_font(pdf, size_pt)
    pdf.set_text_color(*color)
    cur_y = y
    for line in lines:
        pdf.text(x, cur_y, line)
        cur_y += line_height_in


def draw_spine_text(
    pdf: FPDF,
    text: str,
    spine_start_x: float,
    spine_width: float,
    wrap_height: float,
    size_pt: float,
    color: RGB,
) -> None:
    """Draw rotated spine text running bottom-to-top along the spine center.

    Text is centered across the spine width and runs the vertical length.
    Skips silently if spine_width < 0.0625 (KDP minimum for spine text).
    """
    if spine_width < 0.0625:
        return
    _set_font(pdf, size_pt)
    pdf.set_text_color(*color)

    spine_center_x = spine_start_x + spine_width / 2
    start_y = wrap_height - 0.5  # 0.5" safe zone from bottom
    # Rotate 90° counterclockwise around (spine_center_x, start_y)
    with pdf.rotation(90, spine_center_x, start_y):
        pdf.text(spine_center_x, start_y, text)
```

- [ ] **Step 4: Run tests — confirm they pass**

```bash
python3 -m pytest tests/test_cover_text.py -v
```

Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add templates/lib/cover_text.py tests/test_cover_text.py
git commit -m "feat(cover): add fpdf2 vector text helpers (centered/block/spine)"
```

---

### Task 7: `compose_paperback_wrap_template.py` — full wrap PDF

**Files:**
- Create: `templates/compose_paperback_wrap_template.py`
- Create: `tests/test_compose_paperback_wrap.py`
- Use: `templates/fixtures/sample_book/cover-assets/wrap_art.png` (will create in Task 14)

- [ ] **Step 1: Write failing integration test**

Create `tests/test_compose_paperback_wrap.py`:

```python
"""Integration test — vector text survives to paperback wrap PDF."""
from pathlib import Path
import subprocess
import sys
from PIL import Image
from pypdf import PdfReader
import pytest


def _make_wrap_placeholder(path: Path, width: int = 4992, height: int = 2624) -> None:
    """Create a solid-color placeholder that stands in for real zgen art."""
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (width, height), color=(30, 58, 95)).save(path)


def test_compose_paperback_wrap_produces_pdf_with_vector_text(
    tmp_path: Path, sample_book_config: dict, monkeypatch
):
    # Arrange: minimal project layout in tmp_path
    pub_dir = tmp_path / "publishing"
    assets_dir = pub_dir / "cover-assets"
    assets_dir.mkdir(parents=True)
    _make_wrap_placeholder(assets_dir / "wrap_art.png")

    # Act: import and run the compose function directly
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from templates.compose_paperback_wrap_template import compose_wrap

    out_pdf = compose_wrap(
        book_config=sample_book_config,
        wrap_art=assets_dir / "wrap_art.png",
        output=assets_dir / "paperback_wrap.pdf",
    )

    # Assert: PDF exists, contains vector title + author
    assert out_pdf.exists()
    reader = PdfReader(str(out_pdf))
    text = "\n".join(p.extract_text() or "" for p in reader.pages)
    assert sample_book_config["title"] in text
    assert sample_book_config["author"] in text


def test_compose_wrap_raises_when_page_count_missing(tmp_path: Path, sample_book_config: dict):
    from templates.compose_paperback_wrap_template import compose_wrap
    sample_book_config["page_count"] = 0
    with pytest.raises(ValueError, match="page_count"):
        compose_wrap(
            book_config=sample_book_config,
            wrap_art=tmp_path / "nonexistent.png",
            output=tmp_path / "out.pdf",
        )
```

- [ ] **Step 2: Run tests — confirm they fail**

```bash
python3 -m pytest tests/test_compose_paperback_wrap.py -v
```

Expected: `ModuleNotFoundError`.

- [ ] **Step 3: Write the compose template**

Create `templates/compose_paperback_wrap_template.py`:

```python
#!/usr/bin/env python3
"""Compose a print-ready paperback wrap PDF.

Vector text is drawn over a full-bleed bitmap. The bitmap itself should be
a zgen-generated wrap_art.png at 4992 x 2624 (trimmed to exact wrap dims).

Usage (as a script):
    python3 compose_paperback_wrap.py

Usage (as a library, e.g. from tests):
    from compose_paperback_wrap_template import compose_wrap
    compose_wrap(book_config=..., wrap_art=..., output=...)
"""
from pathlib import Path
from fpdf import FPDF

from lib.cover_dimensions import (
    wrap_canvas_inches,
    panel_offsets_inches,
    TRIM_WIDTH_INCHES,
    TRIM_HEIGHT_INCHES,
    BLEED_INCHES,
    SAFE_MARGIN_INCHES,
)
from lib.cover_text import (
    draw_centered_text,
    draw_left_aligned_block,
    draw_spine_text,
)


STYLE_PRESETS = {
    "navy_gold": {"title": (255, 255, 255), "body": (240, 240, 240), "accent": (218, 165, 32)},
    "burgundy_cream": {"title": (245, 235, 220), "body": (230, 220, 210), "accent": (200, 170, 100)},
    "teal_coral": {"title": (255, 255, 255), "body": (240, 240, 240), "accent": (255, 127, 102)},
    "black_silver": {"title": (240, 240, 240), "body": (200, 200, 200), "accent": (192, 192, 192)},
    "earth_warm": {"title": (255, 250, 240), "body": (240, 225, 200), "accent": (218, 165, 32)},
    "purple_gold": {"title": (255, 245, 230), "body": (230, 220, 210), "accent": (218, 165, 32)},
    "forest_cream": {"title": (255, 248, 220), "body": (245, 235, 210), "accent": (200, 180, 100)},
    "minimal_white": {"title": (30, 30, 30), "body": (60, 60, 60), "accent": (120, 120, 120)},
}


def compose_wrap(
    book_config: dict,
    wrap_art: Path,
    output: Path,
) -> Path:
    """Render paperback_wrap.pdf. Returns output path."""
    if book_config.get("page_count", 0) < 24:
        raise ValueError(
            f"book_config['page_count'] must be >= 24 (got {book_config.get('page_count')}). "
            "Set PAGE_COUNT in BOOK_CONFIG before composing — spine depends on it."
        )
    page_count = book_config["page_count"]
    paper = book_config.get("paper_type", "white")
    preset = book_config.get("style_preset", "navy_gold")
    colors = STYLE_PRESETS[preset]

    wrap_w, wrap_h = wrap_canvas_inches(page_count, paper)
    offsets = panel_offsets_inches(page_count, paper)

    pdf = FPDF(unit="in", format=(wrap_w, wrap_h))
    pdf.set_auto_page_break(auto=False)
    pdf.add_page()

    # 1. Full-bleed bitmap background
    if wrap_art.exists():
        pdf.image(str(wrap_art), x=0, y=0, w=wrap_w, h=wrap_h)

    # 2. Front panel text (right side)
    front_cx = (offsets["front_start"] + offsets["front_end"]) / 2
    front_safe_top = BLEED_INCHES + SAFE_MARGIN_INCHES
    draw_centered_text(
        pdf, text=book_config["title"].upper(),
        x_center=front_cx, y=front_safe_top + 0.8,
        size_pt=42, color=colors["title"],
    )
    if book_config.get("subtitle"):
        draw_centered_text(
            pdf, text=book_config["subtitle"],
            x_center=front_cx, y=front_safe_top + 1.6,
            size_pt=16, color=colors["body"],
        )
    draw_centered_text(
        pdf, text=book_config["author"].upper(),
        x_center=front_cx,
        y=wrap_h - BLEED_INCHES - SAFE_MARGIN_INCHES - 0.4,
        size_pt=18, color=colors["title"],
    )

    # 3. Back panel text (left side)
    back_safe_left = offsets["back_start"] + BLEED_INCHES + SAFE_MARGIN_INCHES
    back_safe_top = BLEED_INCHES + SAFE_MARGIN_INCHES + 0.5
    if book_config.get("tagline"):
        draw_centered_text(
            pdf, text=book_config["tagline"],
            x_center=(offsets["back_start"] + offsets["back_end"]) / 2,
            y=back_safe_top,
            size_pt=14, color=colors["accent"],
        )
    back_body_y = back_safe_top + 0.6
    body_lines = book_config.get("back_body_lines", [])
    if body_lines:
        draw_left_aligned_block(
            pdf, lines=body_lines,
            x=back_safe_left, y=back_body_y,
            size_pt=10, color=colors["body"], line_height_in=0.18,
        )

    # 4. Spine text (if spine wide enough)
    spine_w = offsets["spine_end"] - offsets["spine_start"]
    spine_text = f"{book_config['title']}  /  {book_config['author']}"
    draw_spine_text(
        pdf, text=spine_text,
        spine_start_x=offsets["spine_start"],
        spine_width=spine_w,
        wrap_height=wrap_h,
        size_pt=10, color=colors["title"],
    )

    output.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(output))
    return output


if __name__ == "__main__":
    # CUSTOMIZE: set BOOK_CONFIG and paths for your project
    from BOOK_CONFIG import BOOK_CONFIG  # noqa

    project = Path(__file__).parent
    assets = project / "cover-assets"
    compose_wrap(
        book_config=BOOK_CONFIG,
        wrap_art=assets / "wrap_art.png",
        output=assets / "paperback_wrap.pdf",
    )
    print(f"Wrote {assets / 'paperback_wrap.pdf'}")
```

- [ ] **Step 4: Run tests — confirm they pass**

```bash
python3 -m pytest tests/test_compose_paperback_wrap.py -v
```

Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add templates/compose_paperback_wrap_template.py tests/test_compose_paperback_wrap.py
git commit -m "feat(cover): add paperback wrap composer with vector text overlay"
```

---

### Task 8: `compose_kindle_cover_template.py` — Kindle JPEG

**Files:**
- Create: `templates/compose_kindle_cover_template.py`
- Create: `tests/test_compose_kindle_cover.py`

- [ ] **Step 1: Write failing integration test**

Create `tests/test_compose_kindle_cover.py`:

```python
"""Integration test — Kindle JPEG has right dimensions."""
from pathlib import Path
import sys
from PIL import Image


def _make_kindle_placeholder(path: Path) -> None:
    Image.new("RGB", (1600, 2560), color=(30, 58, 95)).save(path)


def test_compose_kindle_produces_1600x2560_jpeg(tmp_path: Path, sample_book_config: dict):
    pub = tmp_path / "publishing" / "cover-assets"
    pub.mkdir(parents=True)
    _make_kindle_placeholder(pub / "kindle_art.png")

    sys.path.insert(0, str(Path(__file__).parent.parent))
    from templates.compose_kindle_cover_template import compose_kindle

    out_jpg = compose_kindle(
        book_config=sample_book_config,
        kindle_art=pub / "kindle_art.png",
        output=pub / "kindle_cover.jpg",
    )
    assert out_jpg.exists()
    with Image.open(out_jpg) as img:
        assert img.size == (1600, 2560)
        assert img.mode == "RGB"
```

- [ ] **Step 2: Run tests — confirm they fail**

```bash
python3 -m pytest tests/test_compose_kindle_cover.py -v
```

- [ ] **Step 3: Write the compose template**

Create `templates/compose_kindle_cover_template.py`:

```python
#!/usr/bin/env python3
"""Compose a Kindle cover JPEG (1600x2560).

Internal layout uses the same vector-first approach as paperback —
render a small PDF with vector text over bitmap, then rasterize to JPEG
as the very last step. Keeps one mental model across all cover surfaces.
"""
from pathlib import Path
from fpdf import FPDF
from PIL import Image
from pdf2image import convert_from_path

from lib.cover_text import draw_centered_text
from compose_paperback_wrap_template import STYLE_PRESETS

KINDLE_WIDTH_PX = 1600
KINDLE_HEIGHT_PX = 2560
DPI = 300
KINDLE_WIDTH_IN = KINDLE_WIDTH_PX / DPI
KINDLE_HEIGHT_IN = KINDLE_HEIGHT_PX / DPI


def compose_kindle(
    book_config: dict,
    kindle_art: Path,
    output: Path,
) -> Path:
    """Render kindle_cover.jpg at 1600x2560. Returns output path."""
    preset = book_config.get("style_preset", "navy_gold")
    colors = STYLE_PRESETS[preset]

    # Build PDF at Kindle dimensions
    pdf = FPDF(unit="in", format=(KINDLE_WIDTH_IN, KINDLE_HEIGHT_IN))
    pdf.set_auto_page_break(auto=False)
    pdf.add_page()

    if kindle_art.exists():
        pdf.image(str(kindle_art), x=0, y=0, w=KINDLE_WIDTH_IN, h=KINDLE_HEIGHT_IN)

    center_x = KINDLE_WIDTH_IN / 2
    draw_centered_text(
        pdf, text=book_config["title"].upper(),
        x_center=center_x, y=1.8,
        size_pt=56, color=colors["title"],
    )
    if book_config.get("subtitle"):
        draw_centered_text(
            pdf, text=book_config["subtitle"],
            x_center=center_x, y=2.8,
            size_pt=22, color=colors["body"],
        )
    draw_centered_text(
        pdf, text=book_config["author"].upper(),
        x_center=center_x, y=KINDLE_HEIGHT_IN - 0.8,
        size_pt=24, color=colors["title"],
    )

    # Rasterize
    tmp_pdf = output.with_suffix(".tmp.pdf")
    output.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(tmp_pdf))

    images = convert_from_path(str(tmp_pdf), dpi=DPI)
    img = images[0].convert("RGB")
    if img.size != (KINDLE_WIDTH_PX, KINDLE_HEIGHT_PX):
        img = img.resize((KINDLE_WIDTH_PX, KINDLE_HEIGHT_PX), Image.LANCZOS)
    img.save(output, "JPEG", quality=95)

    tmp_pdf.unlink(missing_ok=True)
    return output


if __name__ == "__main__":
    from BOOK_CONFIG import BOOK_CONFIG  # noqa

    project = Path(__file__).parent
    assets = project / "cover-assets"
    compose_kindle(
        book_config=BOOK_CONFIG,
        kindle_art=assets / "kindle_art.png",
        output=assets / "kindle_cover.jpg",
    )
    print(f"Wrote {assets / 'kindle_cover.jpg'}")
```

- [ ] **Step 4: Run tests — confirm they pass**

```bash
python3 -m pytest tests/test_compose_kindle_cover.py -v
```

Expected: 1 passed.

- [ ] **Step 5: Commit**

```bash
git add templates/compose_kindle_cover_template.py tests/test_compose_kindle_cover.py
git commit -m "feat(cover): add Kindle JPEG composer via PDF→raster pipeline"
```

---

### Task 9: `compose_interior_art_template.py` — motif staging

**Files:**
- Create: `templates/compose_interior_art_template.py`
- Create: `tests/test_compose_interior_art.py`

- [ ] **Step 1: Write failing test**

Create `tests/test_compose_interior_art.py`:

```python
"""Test that compose_interior_art stages the motif to assets/."""
from pathlib import Path
import sys
from PIL import Image


def test_stage_motif_copies_and_resizes(tmp_path: Path):
    src = tmp_path / "cover-assets" / "chapter_motif.png"
    src.parent.mkdir(parents=True)
    Image.new("RGB", (1664, 2560), color=(100, 100, 100)).save(src)

    dst_assets = tmp_path / "assets"
    dst_assets.mkdir()

    sys.path.insert(0, str(Path(__file__).parent.parent))
    from templates.compose_interior_art_template import stage_motif

    out = stage_motif(source=src, dest_dir=dst_assets)
    assert out.exists()
    assert out.name == "chapter_motif.png"
    with Image.open(out) as img:
        assert img.size == (1650, 2550)
```

- [ ] **Step 2: Run tests — confirm they fail**

```bash
python3 -m pytest tests/test_compose_interior_art.py -v
```

- [ ] **Step 3: Write the template**

Create `templates/compose_interior_art_template.py`:

```python
#!/usr/bin/env python3
"""Stage the approved chapter motif PNG into the book's assets directory.

Crops from the zgen output (1664x2560) to the canonical interior motif
size (1650x2550, which is 5.5x8.5 at 300 DPI).
"""
from pathlib import Path
from PIL import Image

MOTIF_WIDTH_PX = 1650
MOTIF_HEIGHT_PX = 2550


def stage_motif(source: Path, dest_dir: Path) -> Path:
    """Crop motif from source PNG and write to dest_dir/chapter_motif.png."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    dst = dest_dir / "chapter_motif.png"

    with Image.open(source) as img:
        img = img.convert("RGB")
        w, h = img.size
        if (w, h) == (MOTIF_WIDTH_PX, MOTIF_HEIGHT_PX):
            img.save(dst)
            return dst
        # Center-crop to canonical size
        left = max(0, (w - MOTIF_WIDTH_PX) // 2)
        top = max(0, (h - MOTIF_HEIGHT_PX) // 2)
        right = left + MOTIF_WIDTH_PX
        bottom = top + MOTIF_HEIGHT_PX
        cropped = img.crop((left, top, right, bottom))
        cropped.save(dst)
    return dst


if __name__ == "__main__":
    project = Path(__file__).parent
    src = project / "cover-assets" / "chapter_motif.png"
    dst = project.parent / "assets"
    if not src.exists():
        raise SystemExit(
            f"ERROR: approved motif not found at {src}. "
            "Run generate_cover_art.py and approve a motif first."
        )
    out = stage_motif(source=src, dest_dir=dst)
    print(f"Staged motif to {out}")
```

- [ ] **Step 4: Run tests — confirm they pass**

```bash
python3 -m pytest tests/test_compose_interior_art.py -v
```

Expected: 1 passed.

- [ ] **Step 5: Commit**

```bash
git add templates/compose_interior_art_template.py tests/test_compose_interior_art.py
git commit -m "feat(cover): add chapter motif staging script"
```

---

### Task 10: `generate_cover_art_template.py` — creative loop

**Files:**
- Create: `templates/generate_cover_art_template.py`

**Note:** This is the interactive script. No unit tests for the UX loop itself — we test the primitives (prompt builder, zgen runner, session state) that it composes. Smoke-test by dry-running against a mocked zgen.

- [ ] **Step 1: Write the creative-loop script**

Create `templates/generate_cover_art_template.py`:

```python
#!/usr/bin/env python3
"""Interactive cover-art generation loop.

For each of three surfaces (wrap, kindle, motif):
  1. Build 3 prompt variants (2 on-palette + 1 wildcard)
  2. Show prompts to user for review before firing zgen
  3. Run zgen SERIALLY — one image at a time, never batched
  4. Contact sheet: user approves or refines
  5. Refinement sub-loop: seed-locked, single image per tweak

Session state in cover-assets/cover-session.json lets you resume.
"""
from pathlib import Path
import random
import sys

from lib.cover_prompts import build_variants
from lib.cover_session import CoverSession, load_session, save_session_atomic
from lib.zgen_runner import run_zgen

SURFACE_DIMS = {
    "wrap":   {"width": 4992, "height": 2624},
    "kindle": {"width": 1600, "height": 2560},
    "motif":  {"width": 1664, "height": 2560},
}
SURFACES = ["wrap", "kindle", "motif"]


def _candidate_path(assets: Path, surface: str, idx: int) -> Path:
    return assets / "candidates" / f"{surface}_v1_candidate_{idx}.png"


def _canonical_path(assets: Path, surface: str) -> Path:
    return assets / f"{surface}_art.png"


def _generate_candidates(surface: str, genre: str, palette: str, assets: Path) -> list[dict]:
    """Build 3 variants, show to user, run zgen serially."""
    variants = build_variants(surface=surface, genre=genre, palette_key=palette)
    print(f"\n=== {surface.upper()} — drafted {len(variants)} prompts ===")
    for i, v in enumerate(variants, 1):
        label = "WILDCARD" if v["is_wildcard"] else "on-palette"
        print(f"\n[{i}] ({label}) {v['composition']}")
        print(f"    PROMPT: {v['prompt']}")
    input("\nPress Enter to start generation (Ctrl-C to bail and re-draft)...")

    results = []
    for i, v in enumerate(variants, 1):
        seed = random.randint(1, 2**31 - 1)
        out = _candidate_path(assets, surface, i)
        print(f"  [{i}/{len(variants)}] {surface} variant {i}  ... running zgen (seed={seed})")
        run_zgen(
            prompt=v["prompt"],
            output=out,
            width=SURFACE_DIMS[surface]["width"],
            height=SURFACE_DIMS[surface]["height"],
            seed=seed,
        )
        print(f"        done → {out.name}")
        results.append({"prompt": v["prompt"], "seed": seed, "file": out})
    return results


def _prompt_approval(surface: str, candidates: list[dict]) -> str:
    """Ask user for W1/K1/M1 style approval or 'refine' / 'reroll'."""
    print(f"\n{surface} candidates:")
    for i, c in enumerate(candidates, 1):
        print(f"  [{i}] {c['file'].name}")
    return input(
        f"  approve/refine/reroll for {surface}? "
        "(e.g. '1' to approve candidate 1, 'refine 1' or 'reroll'): "
    ).strip()


def _refine_loop(
    surface: str, current: dict, assets: Path, first_iteration: bool = True
) -> dict:
    """Seed-locked refinement loop. Returns updated candidate dict on approval."""
    seed = current["seed"]
    prompt = current["prompt"]
    while True:
        tweak = input(
            f"  refine {surface} (seed locked={seed}). What to adjust? "
            "(e.g. 'more muted, less orange'; 'reroll' for new seed; 'done' to approve): "
        ).strip()
        if tweak in ("done", ""):
            current["approved"] = True
            return current
        if tweak == "reroll":
            seed = random.randint(1, 2**31 - 1)
            print(f"  new seed={seed}")
            continue
        # Rewrite prompt: naive append; user can edit full prompt if they want
        new_prompt = prompt + f", {tweak}"
        if first_iteration:
            print(f"  REWRITTEN PROMPT: {new_prompt}")
            confirm = input("  fire? (y/n/edit): ").strip().lower()
            if confirm == "edit":
                new_prompt = input("  edit prompt: ").strip() or new_prompt
            elif confirm == "n":
                continue
        out = current["file"]
        run_zgen(
            prompt=new_prompt, output=out,
            width=SURFACE_DIMS[surface]["width"],
            height=SURFACE_DIMS[surface]["height"],
            seed=seed,
        )
        print(f"  re-rendered → {out}. review, then say 'done' or refine more.")
        prompt = new_prompt
        current.update({"prompt": new_prompt, "seed": seed})
        first_iteration = False


def _promote_candidate(surface: str, candidate: dict, assets: Path) -> None:
    """Copy approved candidate to canonical name."""
    canonical = _canonical_path(assets, surface)
    canonical.write_bytes(candidate["file"].read_bytes())


def generate_cover_art(
    book_config: dict,
    assets_dir: Path,
) -> None:
    """Main entry point."""
    assets_dir.mkdir(parents=True, exist_ok=True)
    (assets_dir / "candidates").mkdir(exist_ok=True)
    session_file = assets_dir / "cover-session.json"

    if session_file.exists():
        session = load_session(session_file)
        print(f"Resuming session for {session.book_title!r}.")
    else:
        session = CoverSession.new(
            book_title=book_config["title"],
            style_preset=book_config.get("style_preset", "navy_gold"),
        )

    genre = book_config.get("genre", "non-fiction")
    palette = book_config.get("style_preset", "navy_gold")

    for surface in SURFACES:
        if surface in session.surfaces and session.surfaces[surface].get("approved_file"):
            print(f"Skipping {surface} — already approved.")
            continue

        candidates = _generate_candidates(surface, genre, palette, assets_dir)
        for c in candidates:
            session.record_iteration(
                surface=surface, prompt=c["prompt"], seed=c["seed"],
                approved=False,
                width=SURFACE_DIMS[surface]["width"],
                height=SURFACE_DIMS[surface]["height"],
            )

        while True:
            choice = _prompt_approval(surface, candidates)
            if choice.isdigit():
                idx = int(choice) - 1
                approved = candidates[idx]
                session.record_iteration(
                    surface=surface, prompt=approved["prompt"],
                    seed=approved["seed"], approved=True,
                    width=SURFACE_DIMS[surface]["width"],
                    height=SURFACE_DIMS[surface]["height"],
                )
                _promote_candidate(surface, approved, assets_dir)
                break
            if choice.startswith("refine"):
                idx = int(choice.split()[1]) - 1 if len(choice.split()) > 1 else 0
                refined = _refine_loop(surface, candidates[idx], assets_dir)
                session.record_iteration(
                    surface=surface, prompt=refined["prompt"],
                    seed=refined["seed"], approved=True,
                    width=SURFACE_DIMS[surface]["width"],
                    height=SURFACE_DIMS[surface]["height"],
                )
                _promote_candidate(surface, refined, assets_dir)
                break
            if choice == "reroll":
                candidates = _generate_candidates(surface, genre, palette, assets_dir)
                continue
            print(f"  unrecognized: {choice!r}")

        save_session_atomic(session, session_file)

    print("\nAll surfaces approved. Canonical art:")
    for s in SURFACES:
        print(f"  {_canonical_path(assets_dir, s)}")


if __name__ == "__main__":
    try:
        from BOOK_CONFIG import BOOK_CONFIG  # noqa
    except ImportError:
        print("ERROR: BOOK_CONFIG.py not found. Copy the template and set your metadata.")
        sys.exit(1)
    project = Path(__file__).parent
    generate_cover_art(book_config=BOOK_CONFIG, assets_dir=project / "cover-assets")
```

- [ ] **Step 2: Smoke-check the file imports**

```bash
cd ~/.claude/skills/book-publisher/templates
python3 -c "import generate_cover_art_template; print('OK')"
```

Expected: `OK` (imports succeed, no NameError).

- [ ] **Step 3: Commit**

```bash
git add templates/generate_cover_art_template.py
git commit -m "feat(cover): add interactive cover-art generation loop"
```

---

### Task 11: Modify `generate_pdf_template.py` — chapter motif

**Files:**
- Modify: `templates/generate_pdf_template.py`

The existing generate_pdf_template.py has a chapter-opener render path. We add an opt-in branch that checks for `assets/chapter_motif.png` and, when present, renders it as a top-half banner before the chapter number and title.

- [ ] **Step 1: Locate the chapter-opener function**

```bash
grep -n "def _render_chapter\|def render_chapter\|chapter_start" templates/generate_pdf_template.py | head
```

Identify the function that starts a new chapter page (likely around a method that calls `add_page()` and then renders the chapter number/title).

- [ ] **Step 2: Add motif rendering helper**

Inside `generate_pdf_template.py`, near other render helpers, add:

```python
def _render_chapter_motif_if_present(self, chapter_num: int, chapter_title: str) -> bool:
    """If assets/chapter_motif.png exists, render as top-half banner.

    Returns True if motif was rendered (caller should offset chapter text),
    False otherwise (caller renders chapter header as before).
    """
    from pathlib import Path
    motif_path = Path(__file__).parent.parent / "assets" / "chapter_motif.png"
    if not motif_path.exists():
        return False
    # Banner is top 40% of page height, full page width (no margins)
    page_w = self.w
    banner_h = self.h * 0.40
    self.image(str(motif_path), x=0, y=0, w=page_w, h=banner_h)
    # Move cursor below motif with whitespace gap (no divider rule)
    self.set_y(banner_h + 10)
    return True
```

- [ ] **Step 3: Wire the helper into the chapter-opener flow**

Find the existing chapter-opener render logic (where chapter number + title are drawn). Replace the first lines of that render block with:

```python
motif_rendered = self._render_chapter_motif_if_present(chapter_num, chapter_title)
# Existing chapter header code follows. If motif rendered, it is drawn
# below the banner (self.set_y already positioned); otherwise, existing
# top-margin positioning applies.
```

Exact placement: immediately after `self.add_page()` for chapter starts, before the existing `self.set_font(...)` / chapter-number draw calls.

- [ ] **Step 4: Manual smoke test**

Run the existing test suite to confirm non-motif path still works:

```bash
cd ~/.claude/skills/book-publisher
# Run existing tests (if any); the motif path is opt-in so absence of
# chapter_motif.png must preserve current behavior.
python3 -m pytest tests/ -v
```

Expected: all tests pass; no regressions.

- [ ] **Step 5: Commit**

```bash
git add templates/generate_pdf_template.py
git commit -m "feat(pdf): optional chapter-opener motif banner from assets/"
```

---

### Task 12: Modify `add_covers_to_pdf_template.py` — PDF input

**Files:**
- Modify: `templates/add_covers_to_pdf_template.py`

Current behavior: reads `paperback_cover_clean.png` and crops to front/back panels as images. New behavior: reads `cover-assets/paperback_wrap.pdf` via pypdf and extracts the front and back pages as vector PDF pages.

- [ ] **Step 1: Read current implementation**

```bash
less templates/add_covers_to_pdf_template.py
```

Identify the function that opens the wrap image and crops panels — this is the section to replace.

- [ ] **Step 2: Rewrite the extraction logic**

Replace the PNG-based extraction with pypdf-based page splitting. The paperback_wrap.pdf is a single-page wide PDF; to "extract front" we crop that single page to the front panel's coordinate box and save as its own PDF page.

Add this helper at the top of the file:

```python
from pypdf import PdfReader, PdfWriter, Transformation
from pypdf.generic import RectangleObject
from pathlib import Path

from lib.cover_dimensions import (
    panel_offsets_inches, wrap_canvas_inches, BLEED_INCHES, TRIM_WIDTH_INCHES, TRIM_HEIGHT_INCHES
)


def _extract_panel_as_pdf(
    wrap_pdf: Path, page_count: int, paper: str, panel: str, out: Path
) -> Path:
    """Crop the wrap PDF to a single panel (front or back) and write to out.

    panel = 'front' or 'back'. Preserves vector content via MediaBox crop.
    """
    reader = PdfReader(str(wrap_pdf))
    writer = PdfWriter()
    page = reader.pages[0]

    wrap_w, wrap_h = wrap_canvas_inches(page_count, paper)
    offsets = panel_offsets_inches(page_count, paper)

    # pypdf uses points (72 pt = 1 in)
    if panel == "front":
        x0_in = offsets["front_start"]
        x1_in = offsets["front_end"]
    elif panel == "back":
        x0_in = offsets["back_start"]
        x1_in = offsets["back_end"]
    else:
        raise ValueError(f"panel must be 'front' or 'back', got {panel!r}")

    x0_pt = x0_in * 72
    x1_pt = x1_in * 72
    y0_pt = 0
    y1_pt = wrap_h * 72

    page.mediabox = RectangleObject((x0_pt, y0_pt, x1_pt, y1_pt))
    page.cropbox = RectangleObject((x0_pt, y0_pt, x1_pt, y1_pt))
    writer.add_page(page)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "wb") as f:
        writer.write(f)
    return out
```

- [ ] **Step 3: Update the main add_covers function**

Replace the existing front/back PNG extraction with PDF-based extraction. The main function should now:

```python
def add_covers_to_pdf(
    book_pdf: Path,
    wrap_pdf: Path,
    page_count: int,
    paper: str,
    output: Path,
) -> Path:
    """Merge extracted front cover + book interior + extracted back cover."""
    front = _extract_panel_as_pdf(wrap_pdf, page_count, paper, "front", output.parent / "_front.pdf")
    back = _extract_panel_as_pdf(wrap_pdf, page_count, paper, "back", output.parent / "_back.pdf")

    writer = PdfWriter()
    for src in (front, book_pdf, back):
        reader = PdfReader(str(src))
        for page in reader.pages:
            writer.add_page(page)

    with open(output, "wb") as f:
        writer.write(f)

    # Clean up temp panel PDFs
    front.unlink(missing_ok=True)
    back.unlink(missing_ok=True)
    return output
```

- [ ] **Step 4: Update the `if __name__ == "__main__":` block**

```python
if __name__ == "__main__":
    from BOOK_CONFIG import BOOK_CONFIG  # noqa
    project = Path(__file__).parent
    assets = project / "cover-assets"

    # Find latest book PDF
    pdfs = sorted(project.glob("*_v*.pdf"), key=lambda p: p.stat().st_mtime)
    if not pdfs:
        raise SystemExit("ERROR: no book PDF found. Run generate_pdf.py first.")
    book_pdf = pdfs[-1]

    out = book_pdf.with_name(book_pdf.stem + "_with_covers.pdf")
    add_covers_to_pdf(
        book_pdf=book_pdf,
        wrap_pdf=assets / "paperback_wrap.pdf",
        page_count=BOOK_CONFIG["page_count"],
        paper=BOOK_CONFIG.get("paper_type", "white"),
        output=out,
    )
    print(f"Wrote {out}")
```

- [ ] **Step 5: Smoke test**

```bash
python3 -c "from templates.add_covers_to_pdf_template import add_covers_to_pdf, _extract_panel_as_pdf; print('OK')"
```

Expected: `OK`.

- [ ] **Step 6: Commit**

```bash
git add templates/add_covers_to_pdf_template.py
git commit -m "feat(cover): add_covers now reads paperback_wrap.pdf with vector preservation"
```

---

### Task 13: Modify `generate_epub_template.py` — Kindle JPEG

**Files:**
- Modify: `templates/generate_epub_template.py`

Current behavior: looks for `kindle_cover.png` or generates its own via Pillow. New behavior: reads the canonical `cover-assets/kindle_cover.jpg`.

- [ ] **Step 1: Locate cover-image reference**

```bash
grep -n "kindle_cover\|set_cover\|cover.jpg\|cover.png" templates/generate_epub_template.py
```

- [ ] **Step 2: Change cover path to canonical Kindle JPEG**

Replace the existing cover-image path resolution (whichever form it takes) with:

```python
cover_path = Path(__file__).parent / "cover-assets" / "kindle_cover.jpg"
if not cover_path.exists():
    raise SystemExit(
        "ERROR: Kindle cover not found at cover-assets/kindle_cover.jpg. "
        "Run compose_kindle_cover.py first."
    )
```

Then pass `cover_path` to the existing `book.set_cover(...)` call (or equivalent).

- [ ] **Step 3: Remove any fallback Pillow cover generation**

If the template has fallback code that renders a PNG cover with Pillow when `kindle_cover.jpg` is missing, delete it. Clean break per spec.

- [ ] **Step 4: Smoke test**

```bash
python3 -c "import ast; ast.parse(open('templates/generate_epub_template.py').read()); print('OK')"
```

Expected: `OK`.

- [ ] **Step 5: Commit**

```bash
git add templates/generate_epub_template.py
git commit -m "feat(epub): use canonical cover-assets/kindle_cover.jpg for EPUB cover"
```

---

### Task 14: Create fixture sample_book + delete old templates

**Files:**
- Create: `templates/fixtures/sample_book/BOOK_CONFIG.py`
- Create: `templates/fixtures/sample_book/cover-assets/wrap_art.png`
- Create: `templates/fixtures/sample_book/cover-assets/kindle_art.png`
- Create: `templates/fixtures/sample_book/cover-assets/chapter_motif.png`
- Delete: `templates/create_paperback_cover_template.py`
- Delete: `templates/create_kindle_cover_template.py`

- [ ] **Step 1: Create fixture BOOK_CONFIG**

Create `templates/fixtures/sample_book/BOOK_CONFIG.py`:

```python
"""Minimal fixture BOOK_CONFIG for skill-maintenance smoke tests."""

BOOK_CONFIG = {
    "title": "Sample Book",
    "subtitle": "A Fixture for Smoke Tests",
    "author": "Test Author",
    "tagline": "Tests the cover-compose pipeline end-to-end.",
    "style_preset": "navy_gold",
    "genre": "non-fiction",
    "year": "2026",
    "page_count": 200,
    "paper_type": "white",
    "back_body_lines": [
        "This is fixture body copy line one.",
        "This is fixture body copy line two.",
        "This is fixture body copy line three.",
    ],
}
```

- [ ] **Step 2: Generate tiny placeholder PNGs**

```bash
cd ~/.claude/skills/book-publisher/templates/fixtures/sample_book
mkdir -p cover-assets
python3 -c "
from PIL import Image
Image.new('RGB', (4992, 2624), color=(30, 58, 95)).save('cover-assets/wrap_art.png')
Image.new('RGB', (1600, 2560), color=(30, 58, 95)).save('cover-assets/kindle_art.png')
Image.new('RGB', (1664, 2560), color=(30, 58, 95)).save('cover-assets/chapter_motif.png')
print('fixture PNGs created')
"
```

- [ ] **Step 3: End-to-end fixture smoke test**

```bash
cd ~/.claude/skills/book-publisher/templates
python3 -c "
import sys
sys.path.insert(0, '.')
from pathlib import Path
from compose_paperback_wrap_template import compose_wrap
from compose_kindle_cover_template import compose_kindle
from compose_interior_art_template import stage_motif
from fixtures.sample_book.BOOK_CONFIG import BOOK_CONFIG

fixture = Path('fixtures/sample_book')
out_wrap = compose_wrap(BOOK_CONFIG, fixture/'cover-assets/wrap_art.png', fixture/'cover-assets/paperback_wrap.pdf')
out_kindle = compose_kindle(BOOK_CONFIG, fixture/'cover-assets/kindle_art.png', fixture/'cover-assets/kindle_cover.jpg')
out_motif = stage_motif(fixture/'cover-assets/chapter_motif.png', fixture/'assets')
print(f'OK: {out_wrap.exists()} {out_kindle.exists()} {out_motif.exists()}')
"
```

Expected: `OK: True True True`.

- [ ] **Step 4: Delete old templates**

```bash
cd ~/.claude/skills/book-publisher/templates
rm create_paperback_cover_template.py create_kindle_cover_template.py
```

- [ ] **Step 5: Add fixture output to .gitignore**

Create or append `~/.claude/skills/book-publisher/.gitignore`:

```
templates/fixtures/sample_book/cover-assets/paperback_wrap.pdf
templates/fixtures/sample_book/cover-assets/kindle_cover.jpg
templates/fixtures/sample_book/assets/
__pycache__/
*.pyc
.pytest_cache/
```

- [ ] **Step 6: Commit**

```bash
git add templates/fixtures/ .gitignore
git rm templates/create_paperback_cover_template.py templates/create_kindle_cover_template.py
git commit -m "chore(cover): add fixture sample_book, delete old flat-color templates"
```

---

### Task 15: Rewrite SKILL.md cover section + references

**Files:**
- Modify: `SKILL.md`
- Modify: `references/cover-generation.md`

- [ ] **Step 1: Rewrite the "Cover Generation" section of SKILL.md**

Locate the `## Cover Generation` section in `SKILL.md` (currently around line 458 per spec). Replace its entire contents (from the section header through end of "Spine Width Calculation") with:

```markdown
## Cover Generation

Cover art uses a two-step pipeline: **AI-generated bitmap artwork** (via local `zgen` / Draw Things CLI) composed with **vector text overlay** (via fpdf2). Vector text stays crisp at any zoom; the bitmap provides the visual identity.

### Pipeline

```
generate_cover_art.py   (interactive — drafts prompts, runs zgen serially,
                         contact-sheet approval, seed-locked refinement loop)
         ↓
   cover-assets/{wrap_art,kindle_art,chapter_motif}.png  (committed to git)
         ↓
   ┌─ compose_paperback_wrap.py → paperback_wrap.pdf  (vector text over bitmap)
   ├─ compose_kindle_cover.py   → kindle_cover.jpg    (PDF → raster at final step)
   └─ compose_interior_art.py   → assets/chapter_motif.png (staged for generate_pdf.py)
```

### Requirements

- Local `zgen` binary at `/Users/pstuart/bin/zgen` (Z Image Turbo via Draw Things CLI)
- All image generation is **serial, one call at a time** — never batched

### Configuration

Style presets define color palettes for vector text (title, body, accent). Choose from: `navy_gold`, `burgundy_cream`, `teal_coral`, `black_silver`, `earth_warm`, `purple_gold`, `forest_cream`, `minimal_white`. Custom palettes supported via `COVER_STYLE` dict in your BOOK_CONFIG.

### Dimensions

| Surface | zgen canvas | Final output |
|---|---|---|
| Paperback wrap | 4992 × 2624 | PDF at `2·(5.5+0.125)+spine` × 8.75 inches |
| Kindle | 1600 × 2560 | JPEG 1600 × 2560 |
| Chapter motif | 1664 × 2560 | PNG 1650 × 2550 (staged to `assets/`) |

### Spine calculation

```python
spine_width_inches = page_count * paper_thickness
# paper_thickness = 0.002252 (white) or 0.002500 (cream)
```

Spine text is only drawn when the spine is ≥ 0.0625" (~28 pages white, ~25 pages cream).

### Validation

After `compose_paperback_wrap.py`, verify vector text survived:

```bash
pdftotext cover-assets/paperback_wrap.pdf -
# Expected: book title and author appear in the output
```

Zoom paperback_wrap.pdf to 400% in Preview — title text must stay crisp. If pixelated, composition went wrong.
```

- [ ] **Step 2: Update the "Quick Start" section of SKILL.md**

Replace the existing cover-related commands (steps 6-7 in the Quick Start block) with:

```bash
# 6. Generate cover art (interactive — drafts prompts, approves per surface)
python3 generate_cover_art.py

# 7. Compose covers from approved art
python3 compose_paperback_wrap.py
python3 compose_kindle_cover.py
python3 compose_interior_art.py   # optional — only if you want chapter motif

# 8. Add covers to PDF
python3 add_covers_to_pdf.py
```

- [ ] **Step 3: Update the Validation Checklist section**

In `SKILL.md`'s Validation Checklist, replace the existing "Cover & Layout" block with:

```markdown
### Cover & Layout
- [ ] Open paperback_wrap.pdf in Preview — zoom to 400%, title text stays crisp (proves vector, not raster)
- [ ] Extract text via `pdftotext paperback_wrap.pdf -` — title and author appear
- [ ] Open kindle_cover.jpg at 100% — title readable, no JPEG artifacts on text edges
- [ ] Spine text reads correctly (if spine ≥ 0.0625")
- [ ] Chapter motif renders on every chapter opener (if chapter_motif.png exists in assets/)
- [ ] Bleed extends full 0.125" on all edges of paperback_wrap.pdf
- [ ] Images are 300 DPI minimum
```

- [ ] **Step 4: Rewrite references/cover-generation.md**

Overwrite `references/cover-generation.md` entirely with:

```markdown
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
```

- [ ] **Step 5: Commit**

```bash
git add SKILL.md references/cover-generation.md
git commit -m "docs: rewrite cover generation section for vector-overlay pipeline"
```

---

## Self-review

*This section is the plan author's final check before handoff. Treat it as a read-only audit; do not skip.*

### Spec coverage

| Spec section | Covered by task(s) |
|---|---|
| Architecture overview | 1 (scaffolding), 2-6 (lib primitives), 7-10 (composers + creative loop) |
| `generate_cover_art.py` component | 10 |
| `compose_paperback_wrap.py` component | 7 |
| `compose_kindle_cover.py` component | 8 |
| `compose_interior_art.py` component | 9 |
| Modified scripts (`generate_pdf`, `generate_epub`, `add_covers_to_pdf`) | 11, 13, 12 |
| Directory layout | 1, 14 |
| `cover-session.json` schema | 3 |
| Canonical dimensions table | 2, 7, 8, 9 (enforced in code) |
| Prompt templates / 4-slot / wildcard | 4 |
| Error handling (boundaries) | 3 (atomic), 5 (zgen) |
| Session state integrity (atomic, schema version) | 3 |
| Testing — dimension math | 2 |
| Testing — session round-trip | 3 |
| Testing — prompt builder | 4 |
| Testing — vector-text-survives | 6, 7 |
| Testing — Kindle JPEG dims | 8 |
| Fixture book | 14 |
| Migration / delete old templates | 14 |
| SKILL.md + references rewrites | 15 |

All spec sections have at least one implementing task. No gaps.

### Placeholder scan

Scanned for "TBD", "TODO", "implement later", "add error handling", "similar to above". **None found** in the task bodies; every code step shows concrete implementation.

### Type consistency

- `CoverSession` used in Task 3 and Task 10 — same dataclass, same field names.
- `compose_wrap`, `compose_kindle`, `stage_motif` — public function names consistent between the compose templates (Tasks 7-9) and their tests.
- `build_variants()` return type (`list[PromptVariant]`) consistent between Task 4 and Task 10 consumption.
- `run_zgen()` signature identical in Task 5 and Task 10 call sites.

No mismatches.

### Open caveats

- Task 11 (generate_pdf motif integration) has the least explicit hook location because the existing script is 48KB and I haven't read every line. Implementer should grep for `def.*chapter` in the file and place the helper call at the start of whatever renders the chapter opener. If no clean hook exists, extract one before wiring motif — note this as a Task 11a refactor.
- Task 13 similarly hand-waves the exact EPUB cover-set API call because the existing template's ebooklib usage isn't in front of me. Implementer should `grep set_cover` to find it.

These are the only fuzzy edges. Both are grep-away for the implementer.

---

## Execution handoff

Plan complete and saved to `~/.claude/skills/book-publisher/docs/plans/2026-04-22-cover-vector-overlay-implementation.md`. Two execution options:

**1. Subagent-Driven (recommended)** — Dispatch a fresh subagent per task, review between tasks, fast iteration. Good for a 15-task plan where you want checkpoints.

**2. Inline Execution** — Execute tasks in this session using executing-plans, batch execution with checkpoints for review. Uses current context window — may run into compaction by Task 10+.

Which approach?
