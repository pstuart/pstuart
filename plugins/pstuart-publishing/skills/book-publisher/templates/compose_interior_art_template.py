#!/usr/bin/env python3
"""Stage the approved chapter motif PNG into the book's assets directory.

Crops from the zgen output (1664x1088) to the canonical interior motif
size (1650x1020 = 5.5" x 3.4" at 300 DPI). That matches the landscape
banner shape that generate_pdf renders at the top of each chapter page.

Previous versions used portrait (1650x2550); those get stretched 2.5×
vertical by fpdf2.image() into the banner area — distorted art. This
version generates at banner aspect from the start.
"""
from pathlib import Path
from PIL import Image

MOTIF_WIDTH_PX = 1650
MOTIF_HEIGHT_PX = 1020


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
