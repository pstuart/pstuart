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
