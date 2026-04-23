"""Render an EAN-13 barcode PNG from an ISBN.

The paperback back cover has a barcode zone (bottom-right of the back panel)
that must show a scannable ISBN barcode per KDP and trade-paperback conventions.
This module takes the ISBN from BOOK_CONFIG and emits a sharp PNG sized to
fit the zone.
"""
from pathlib import Path
import io
from barcode import EAN13
from barcode.writer import ImageWriter
from PIL import Image


def normalize_isbn(isbn: str) -> str:
    """Strip hyphens/spaces. Require exactly 13 numeric digits."""
    stripped = isbn.replace("-", "").replace(" ", "")
    if not stripped.isdigit():
        raise ValueError(f"ISBN must be numeric after stripping punctuation, got {isbn!r}")
    if len(stripped) != 13:
        raise ValueError(
            f"ISBN must be 13 digits (got {len(stripped)}). "
            "ISBN-10 is not supported; convert to ISBN-13 first."
        )
    return stripped


def render_isbn_barcode(
    isbn: str,
    output: Path,
    width_px: int | None = None,
    height_px: int | None = None,
) -> Path:
    """Render a scannable EAN-13 barcode PNG from an ISBN.

    If both width_px and height_px are provided, the output is resized to
    that exact pixel size (LANCZOS). Otherwise the barcode's native size is used.

    Raises ValueError on bad input (non-numeric, wrong length, bad checksum).
    """
    normalized = normalize_isbn(isbn)

    try:
        barcode_obj = EAN13(normalized, writer=ImageWriter())
    except Exception as e:  # python-barcode raises various exception types
        raise ValueError(f"Invalid EAN-13 ISBN {normalized!r}: {e}") from e

    # python-barcode silently corrects bad check digits — detect mismatch manually
    if barcode_obj.ean != normalized:
        raise ValueError(
            f"Invalid EAN-13 check digit in {normalized!r}. "
            f"Expected check digit {barcode_obj.ean[-1]!r}, got {normalized[-1]!r}."
        )

    buf = io.BytesIO()
    barcode_obj.write(
        buf,
        options={
            "module_height": 15.0,
            "font_size": 10,
            "text_distance": 5.0,
            "quiet_zone": 6.5,
        },
    )
    buf.seek(0)

    output.parent.mkdir(parents=True, exist_ok=True)

    if width_px is not None and height_px is not None:
        with Image.open(buf) as img:
            img = img.convert("RGB").resize((width_px, height_px), Image.Resampling.LANCZOS)
            img.save(output, "PNG")
    else:
        with open(output, "wb") as f:
            f.write(buf.getvalue())

    return output
