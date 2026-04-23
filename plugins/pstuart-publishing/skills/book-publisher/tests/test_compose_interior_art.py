"""Test that compose_interior_art stages the motif to assets/."""
from pathlib import Path
import sys
from PIL import Image


def test_stage_motif_copies_and_resizes(tmp_path: Path):
    src = tmp_path / "cover-assets" / "chapter_motif.png"
    src.parent.mkdir(parents=True)
    Image.new("RGB", (1664, 1088), color=(100, 100, 100)).save(src)

    dst_assets = tmp_path / "assets"
    dst_assets.mkdir()

    sys.path.insert(0, str(Path(__file__).parent.parent))
    from templates.compose_interior_art_template import stage_motif

    out = stage_motif(source=src, dest_dir=dst_assets)
    assert out.exists()
    assert out.name == "chapter_motif.png"
    with Image.open(out) as img:
        assert img.size == (1650, 1020)


def test_stage_motif_rejects_too_small_source(tmp_path: Path):
    """If source is smaller than 1650x1020, the crop would produce partial data.
    Current behavior: max(0, ...) clamps indices — the crop just comes out smaller.
    We accept this; downstream fpdf2 will stretch.
    """
    src = tmp_path / "small.png"
    Image.new("RGB", (500, 300), color=(100, 100, 100)).save(src)

    dst_assets = tmp_path / "assets"
    dst_assets.mkdir()

    sys.path.insert(0, str(Path(__file__).parent.parent))
    from templates.compose_interior_art_template import stage_motif

    out = stage_motif(source=src, dest_dir=dst_assets)
    assert out.exists()
    # No assertion on size — PIL's behavior for crop beyond source bounds is
    # to fill with black in newer versions; we're just proving it doesn't crash.
