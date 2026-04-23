"""Integration test — Kindle JPEG has right dimensions + validation guards."""
from pathlib import Path
import sys
import pytest
from PIL import Image


def _make_kindle_placeholder(path: Path) -> None:
    Image.new("RGB", (1600, 2560), color=(30, 58, 95)).save(path)


def _import_compose_kindle():
    root = Path(__file__).parent.parent
    for p in (root, root / "templates"):
        p_str = str(p)
        if p_str not in sys.path:
            sys.path.insert(0, p_str)
    from templates.compose_kindle_cover_template import compose_kindle
    return compose_kindle


def test_compose_kindle_produces_1600x2560_jpeg(tmp_path: Path, sample_book_config: dict):
    pub = tmp_path / "publishing" / "cover-assets"
    pub.mkdir(parents=True)
    _make_kindle_placeholder(pub / "kindle_art.png")

    compose_kindle = _import_compose_kindle()

    out_jpg = compose_kindle(
        book_config=sample_book_config,
        kindle_art=pub / "kindle_art.png",
        output=pub / "kindle_cover.jpg",
    )
    assert out_jpg.exists()
    with Image.open(out_jpg) as img:
        assert img.size == (1600, 2560)
        assert img.mode == "RGB"


def test_compose_kindle_raises_when_title_missing(tmp_path: Path, sample_book_config: dict):
    compose_kindle = _import_compose_kindle()
    sample_book_config.pop("title", None)
    with pytest.raises(ValueError, match="title"):
        compose_kindle(
            book_config=sample_book_config,
            kindle_art=tmp_path / "nonexistent.png",
            output=tmp_path / "out.jpg",
        )


def test_compose_kindle_raises_on_unknown_style_preset(
    tmp_path: Path, sample_book_config: dict
):
    compose_kindle = _import_compose_kindle()
    sample_book_config["style_preset"] = "neon_pink"
    with pytest.raises(ValueError, match="style_preset"):
        compose_kindle(
            book_config=sample_book_config,
            kindle_art=tmp_path / "nonexistent.png",
            output=tmp_path / "out.jpg",
        )
