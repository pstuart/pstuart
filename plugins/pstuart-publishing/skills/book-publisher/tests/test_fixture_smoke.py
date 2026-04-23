"""End-to-end smoke test using the full fixture BOOK_CONFIG.

Runs compose_wrap + compose_kindle against the fixture PNGs and asserts
that every populated zone surfaces in the output. This is the test that
catches silent zone regressions when the cover-layout system evolves.
"""
from pathlib import Path
import sys
from PIL import Image
from pypdf import PdfReader
import pytest


def _add_paths():
    root = Path(__file__).parent.parent
    for p in (root, root / "templates"):
        if str(p) not in sys.path:
            sys.path.insert(0, str(p))


@pytest.fixture
def fixture_dir(tmp_path: Path) -> Path:
    """Clone fixture PNGs into tmp_path/sample_book so the smoke test is reproducible."""
    _add_paths()
    from shutil import copytree
    src = Path(__file__).parent.parent / "templates" / "fixtures" / "sample_book"
    dst = tmp_path / "sample_book"
    copytree(src, dst)
    return dst


def test_fixture_wrap_contains_every_populated_zone(fixture_dir: Path):
    _add_paths()
    from fixtures.sample_book.BOOK_CONFIG import BOOK_CONFIG
    from compose_paperback_wrap_template import compose_wrap

    # Point the author_photo to the copied fixture's path
    config = dict(BOOK_CONFIG)
    config["author_photo"] = str(fixture_dir / "assets" / "author_photo.png")

    wrap_art = fixture_dir / "cover-assets" / "wrap_art.png"
    output = fixture_dir / "cover-assets" / "paperback_wrap.pdf"
    compose_wrap(book_config=config, wrap_art=wrap_art, output=output)

    assert output.exists()
    reader = PdfReader(str(output))
    text = "\n".join(p.extract_text() or "" for p in reader.pages)

    expected = [
        "SAMPLE BOOK",                  # title uppercased
        "A Fixture for Smoke Tests",    # subtitle
        "BY TEST AUTHOR",               # byline default (uppercase)
        "Elizabethan England",          # series_line_front
        "Historical Conspiracy",        # genre_line
        "playwright who never existed", # back_tagline
        "Every great conspiracy",       # quote line 1
        "starts with a single lie",     # quote line 2
        "Fixture Daily",                # quote_attribution
        "printing press",               # blurb para 1
        "typesetter",                   # blurb para 2
        "Test Author lives",            # author_bio
        "About the Author",             # author_bio_label
        "$18.99",                       # price_us
        "Fixture Press",                # publisher
        "Seattle",                      # publisher_city
        "Fixture Imprint",              # imprint
        "Fixture Conspiracy",           # series_line_back
    ]
    missing = [s for s in expected if s not in text]
    assert not missing, f"Fixture zone regression: these strings not found in wrap PDF: {missing}"


def test_fixture_kindle_produces_correct_dimensions(fixture_dir: Path):
    _add_paths()
    from fixtures.sample_book.BOOK_CONFIG import BOOK_CONFIG
    from compose_kindle_cover_template import compose_kindle

    config = dict(BOOK_CONFIG)
    kindle_art = fixture_dir / "cover-assets" / "kindle_art.png"
    output = fixture_dir / "cover-assets" / "kindle_cover.jpg"
    compose_kindle(book_config=config, kindle_art=kindle_art, output=output)

    assert output.exists()
    with Image.open(output) as img:
        assert img.size == (1600, 2560)
        assert img.mode == "RGB"


def test_fixture_legacy_back_body_lines_migrates(tmp_path: Path):
    """A legacy-config user relying on back_body_lines should still work."""
    _add_paths()
    from compose_paperback_wrap_template import compose_wrap

    wrap_art = tmp_path / "wrap.png"
    Image.new("RGB", (100, 100), color=(30, 58, 95)).save(wrap_art)

    output = tmp_path / "paperback.pdf"
    compose_wrap(
        book_config={
            "title": "Legacy",
            "author": "Older User",
            "page_count": 100,
            "back_body_lines": ["migrated line 1", "migrated line 2"],
        },
        wrap_art=wrap_art,
        output=output,
    )
    reader = PdfReader(str(output))
    text = "\n".join(p.extract_text() or "" for p in reader.pages)
    assert "migrated line 1" in text
    assert "migrated line 2" in text
