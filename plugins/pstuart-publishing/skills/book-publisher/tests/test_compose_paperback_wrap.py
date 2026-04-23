"""Integration test — vector text survives to paperback wrap PDF."""
from pathlib import Path
import sys
from PIL import Image
from pypdf import PdfReader
import pytest


def _make_wrap_placeholder(path: Path, width: int = 4992, height: int = 2624) -> None:
    """Create a solid-color placeholder that stands in for real zgen art."""
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (width, height), color=(30, 58, 95)).save(path)


def _import_compose_wrap():
    """Shared helper to register both skill root and templates/ onto sys.path."""
    root = Path(__file__).parent.parent
    for p in (root, root / "templates"):
        p_str = str(p)
        if p_str not in sys.path:
            sys.path.insert(0, p_str)
    from templates.compose_paperback_wrap_template import compose_wrap
    return compose_wrap


def test_compose_paperback_wrap_produces_pdf_with_vector_text(
    tmp_path: Path, sample_book_config: dict, monkeypatch
):
    # Arrange: minimal project layout in tmp_path
    pub_dir = tmp_path / "publishing"
    assets_dir = pub_dir / "cover-assets"
    assets_dir.mkdir(parents=True)
    _make_wrap_placeholder(assets_dir / "wrap_art.png")

    compose_wrap = _import_compose_wrap()

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
    compose_wrap = _import_compose_wrap()
    sample_book_config["page_count"] = 0
    with pytest.raises(ValueError, match="page_count"):
        compose_wrap(
            book_config=sample_book_config,
            wrap_art=tmp_path / "nonexistent.png",
            output=tmp_path / "out.pdf",
        )
