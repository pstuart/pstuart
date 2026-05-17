"""Tests for ISBN EAN-13 barcode renderer."""
from pathlib import Path
import pytest
from PIL import Image
from templates.lib.cover_barcode import render_isbn_barcode, normalize_isbn


def test_normalize_isbn_strips_hyphens():
    assert normalize_isbn("978-0-00-000000-2") == "9780000000002"


def test_normalize_isbn_strips_spaces():
    assert normalize_isbn("978 0 00 000000 2") == "9780000000002"


def test_normalize_isbn_rejects_isbn10():
    with pytest.raises(ValueError, match="13 digits"):
        normalize_isbn("0-00-000000-0")


def test_normalize_isbn_rejects_non_numeric():
    with pytest.raises(ValueError, match="numeric"):
        normalize_isbn("978X000000002")


def test_render_isbn_barcode_produces_png(tmp_path: Path):
    out = tmp_path / "barcode.png"
    result = render_isbn_barcode("9780000000002", out)
    assert result == out
    assert out.exists()
    with Image.open(out) as img:
        assert img.format == "PNG"
        assert img.size[0] > 100 and img.size[1] > 30  # sanity dims


def test_render_isbn_barcode_respects_target_size(tmp_path: Path):
    out = tmp_path / "barcode.png"
    render_isbn_barcode("9780000000002", out, width_px=600, height_px=200)
    with Image.open(out) as img:
        # Final resized output should match the requested box
        assert img.size == (600, 200)


def test_render_isbn_barcode_accepts_hyphenated_input(tmp_path: Path):
    out = tmp_path / "barcode.png"
    render_isbn_barcode("978-0-00-000000-2", out)
    assert out.exists()


def test_render_isbn_barcode_rejects_bad_checksum(tmp_path: Path):
    """EAN-13 with wrong check digit should fail."""
    with pytest.raises(ValueError):
        render_isbn_barcode("9780000000003", tmp_path / "b.png")  # wrong check digit
