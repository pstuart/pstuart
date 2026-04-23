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
