#!/usr/bin/env python3
"""
Kindle Cover Generation Template
Creates professional Kindle front covers (1600x2560 pixels).

CUSTOMIZATION REQUIRED:
1. Update BOOK_CONFIG with your book details
2. Choose a STYLE_PRESET or customize COVER_STYLE
3. Run the script to generate your cover

Dependencies: pip3 install Pillow
"""

from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import os

# ============================================================================
# CONFIGURATION - CUSTOMIZE THESE
# ============================================================================

# Output directory
OUTPUT_DIR = Path("/path/to/your/BookProject/publishing")

# Book metadata
BOOK_CONFIG = {
    "title_line1": "YOUR BOOK",
    "title_line2": "TITLE HERE",
    "subtitle_line1": "Your Compelling",
    "subtitle_line2": "Subtitle Here",
    "tagline": "A powerful tagline that hooks readers.",
    "author": "Author Name",
    "output_prefix": "YourBookTitle",
}

# ============================================================================
# STYLE PRESETS - Choose one or customize your own
# ============================================================================

STYLE_PRESETS = {
    # Professional navy and gold (business, leadership, non-fiction)
    "navy_gold": {
        "name": "Navy & Gold",
        "background": (30, 58, 95),          # Navy
        "accent": (201, 162, 39),             # Gold
        "accent_light": (220, 190, 100),      # Light gold
        "title_color": (255, 255, 255),       # White
        "subtitle_color": (201, 162, 39),     # Gold
        "tagline_color": (220, 190, 100),     # Light gold
        "author_label_color": (255, 255, 255),
        "author_color": (201, 162, 39),
        "use_gradient": False,
    },

    # Deep burgundy and cream (literary, memoir, sophisticated)
    "burgundy_cream": {
        "name": "Burgundy & Cream",
        "background": (88, 24, 32),           # Deep burgundy
        "accent": (245, 235, 220),            # Cream
        "accent_light": (255, 248, 240),      # Light cream
        "title_color": (255, 255, 255),
        "subtitle_color": (245, 235, 220),
        "tagline_color": (220, 200, 180),
        "author_label_color": (200, 180, 160),
        "author_color": (245, 235, 220),
        "use_gradient": False,
    },

    # Modern teal and coral (self-help, wellness, contemporary)
    "teal_coral": {
        "name": "Teal & Coral",
        "background": (0, 95, 115),           # Deep teal
        "accent": (255, 127, 102),            # Coral
        "accent_light": (255, 180, 160),      # Light coral
        "title_color": (255, 255, 255),
        "subtitle_color": (255, 127, 102),
        "tagline_color": (200, 230, 235),
        "author_label_color": (200, 230, 235),
        "author_color": (255, 127, 102),
        "use_gradient": False,
    },

    # Classic black and silver (thriller, mystery, serious)
    "black_silver": {
        "name": "Black & Silver",
        "background": (25, 25, 25),           # Near black
        "accent": (192, 192, 192),            # Silver
        "accent_light": (230, 230, 230),      # Light silver
        "title_color": (255, 255, 255),
        "subtitle_color": (192, 192, 192),
        "tagline_color": (160, 160, 160),
        "author_label_color": (140, 140, 140),
        "author_color": (220, 220, 220),
        "use_gradient": False,
    },

    # Warm earth tones (spirituality, nature, grounded)
    "earth_warm": {
        "name": "Earth Warm",
        "background": (89, 60, 31),           # Rich brown
        "accent": (218, 165, 32),             # Golden
        "accent_light": (245, 222, 179),      # Wheat
        "title_color": (255, 250, 240),       # Floral white
        "subtitle_color": (218, 165, 32),
        "tagline_color": (210, 180, 140),     # Tan
        "author_label_color": (200, 180, 160),
        "author_color": (245, 222, 179),
        "use_gradient": False,
    },

    # Royal purple and gold (luxury, transformation, spiritual)
    "purple_gold": {
        "name": "Purple & Gold",
        "background": (60, 25, 85),           # Deep purple
        "accent": (218, 165, 32),             # Gold
        "accent_light": (255, 215, 100),      # Bright gold
        "title_color": (255, 255, 255),
        "subtitle_color": (218, 165, 32),
        "tagline_color": (200, 180, 220),     # Light purple
        "author_label_color": (180, 160, 200),
        "author_color": (255, 215, 100),
        "use_gradient": False,
    },

    # Forest green and cream (nature, sustainability, wisdom)
    "forest_cream": {
        "name": "Forest & Cream",
        "background": (34, 85, 51),           # Forest green
        "accent": (255, 248, 220),            # Cream
        "accent_light": (255, 255, 240),      # Ivory
        "title_color": (255, 255, 255),
        "subtitle_color": (255, 248, 220),
        "tagline_color": (200, 230, 200),     # Light green
        "author_label_color": (180, 210, 180),
        "author_color": (255, 248, 220),
        "use_gradient": False,
    },

    # Minimalist white and black (modern, clean, professional)
    "minimal_white": {
        "name": "Minimal White",
        "background": (250, 250, 250),        # Off-white
        "accent": (30, 30, 30),               # Near black
        "accent_light": (80, 80, 80),         # Dark gray
        "title_color": (20, 20, 20),          # Near black
        "subtitle_color": (60, 60, 60),
        "tagline_color": (100, 100, 100),
        "author_label_color": (120, 120, 120),
        "author_color": (40, 40, 40),
        "use_gradient": False,
    },
}

# Choose your style preset (or set to None and customize COVER_STYLE below)
STYLE_PRESET = "navy_gold"

# Custom style (used if STYLE_PRESET is None)
COVER_STYLE = {
    "name": "Custom",
    "background": (30, 58, 95),
    "accent": (201, 162, 39),
    "accent_light": (220, 190, 100),
    "title_color": (255, 255, 255),
    "subtitle_color": (201, 162, 39),
    "tagline_color": (220, 190, 100),
    "author_label_color": (255, 255, 255),
    "author_color": (201, 162, 39),
    "use_gradient": False,
}

# ============================================================================
# KINDLE COVER SPECIFICATIONS
# ============================================================================

# Amazon Kindle requirements:
# - Ideal: 1600 x 2560 pixels (1:1.6 aspect ratio)
# - Minimum: 625 x 1000 pixels
# - Maximum: 10,000 pixels on longest side
WIDTH = 1600
HEIGHT = 2560

# ============================================================================
# COVER GENERATION
# ============================================================================

def get_style():
    """Get the active style configuration."""
    if STYLE_PRESET and STYLE_PRESET in STYLE_PRESETS:
        return STYLE_PRESETS[STYLE_PRESET]
    return COVER_STYLE


def load_fonts():
    """Load fonts with fallbacks."""
    fonts = {}
    try:
        base_path = "/System/Library/Fonts/Supplemental/"
        fonts['title'] = ImageFont.truetype(f"{base_path}Georgia Bold.ttf", 140)
        fonts['subtitle'] = ImageFont.truetype(f"{base_path}Georgia.ttf", 56)
        fonts['tagline'] = ImageFont.truetype(f"{base_path}Georgia Italic.ttf", 44)
        fonts['author_label'] = ImageFont.truetype(f"{base_path}Arial.ttf", 32)
        fonts['author'] = ImageFont.truetype(f"{base_path}Georgia Bold.ttf", 64)
    except:
        try:
            # Try alternative paths
            base_path = "/Library/Fonts/"
            fonts['title'] = ImageFont.truetype(f"{base_path}Georgia Bold.ttf", 140)
            fonts['subtitle'] = ImageFont.truetype(f"{base_path}Georgia.ttf", 56)
            fonts['tagline'] = ImageFont.truetype(f"{base_path}Georgia Italic.ttf", 44)
            fonts['author_label'] = ImageFont.truetype(f"{base_path}Arial.ttf", 32)
            fonts['author'] = ImageFont.truetype(f"{base_path}Georgia Bold.ttf", 64)
        except:
            # Use default font as fallback
            default = ImageFont.load_default()
            for key in ['title', 'subtitle', 'tagline', 'author_label', 'author']:
                fonts[key] = default
    return fonts


def draw_centered_text(draw, text, y, font, fill, width=WIDTH):
    """Draw text centered horizontally."""
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    x = (width - text_width) // 2
    draw.text((x, y), text, font=font, fill=fill)
    return bbox[3] - bbox[1]  # Return text height


def create_cover():
    """Create the Kindle front cover."""
    style = get_style()

    # Create base image
    img = Image.new('RGB', (WIDTH, HEIGHT), style['background'])
    draw = ImageDraw.Draw(img)

    # Load fonts
    fonts = load_fonts()

    # Center x position
    center_x = WIDTH // 2

    # Calculate vertical positions
    top_line_y = 450
    title1_y = 550
    title2_y = 720
    subtitle1_y = 950
    subtitle2_y = 1020
    tagline_y = 1150
    bottom_line_y = 1550
    author_label_y = 1950
    author_y = 2010

    # Top decorative line
    line_width = 500
    line_thickness = 4
    draw.rectangle(
        [center_x - line_width//2, top_line_y,
         center_x + line_width//2, top_line_y + line_thickness],
        fill=style['accent']
    )

    # Title line 1
    draw_centered_text(draw, BOOK_CONFIG['title_line1'], title1_y,
                       fonts['title'], style['title_color'])

    # Title line 2
    draw_centered_text(draw, BOOK_CONFIG['title_line2'], title2_y,
                       fonts['title'], style['title_color'])

    # Subtitle line 1
    draw_centered_text(draw, BOOK_CONFIG['subtitle_line1'], subtitle1_y,
                       fonts['subtitle'], style['subtitle_color'])

    # Subtitle line 2
    draw_centered_text(draw, BOOK_CONFIG['subtitle_line2'], subtitle2_y,
                       fonts['subtitle'], style['subtitle_color'])

    # Tagline
    draw_centered_text(draw, BOOK_CONFIG['tagline'], tagline_y,
                       fonts['tagline'], style['tagline_color'])

    # Bottom decorative line
    draw.rectangle(
        [center_x - line_width//2, bottom_line_y,
         center_x + line_width//2, bottom_line_y + line_thickness],
        fill=style['accent']
    )

    # "WRITTEN BY" label
    draw_centered_text(draw, "WRITTEN BY", author_label_y,
                       fonts['author_label'], style['author_label_color'])

    # Author name
    draw_centered_text(draw, BOOK_CONFIG['author'], author_y,
                       fonts['author'], style['author_color'])

    return img


def main():
    """Generate the Kindle cover."""
    style = get_style()
    print("=" * 60)
    print("Kindle Cover Generation")
    print("=" * 60)
    print(f"\nStyle: {style['name']}")
    print(f"Size: {WIDTH} x {HEIGHT} pixels")

    # Create output directory if needed
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Create the cover
    cover = create_cover()

    # Generate output filenames
    prefix = BOOK_CONFIG['output_prefix']

    # Save as JPEG (Kindle preferred format)
    jpg_path = OUTPUT_DIR / f"{prefix}_Kindle_Cover.jpg"
    cover.save(jpg_path, "JPEG", quality=95)
    print(f"\nJPEG saved: {jpg_path}")

    # Save as PNG for higher quality editing
    png_path = OUTPUT_DIR / f"{prefix}_Kindle_Cover.png"
    cover.save(png_path, "PNG")
    print(f"PNG saved: {png_path}")

    # Print dimensions for verification
    print(f"\nCover dimensions: {cover.width} x {cover.height} pixels")
    print(f"Aspect ratio: 1:{cover.height/cover.width:.2f}")

    print("\n" + "=" * 60)
    print("Available style presets:")
    for key, preset in STYLE_PRESETS.items():
        marker = " <-- ACTIVE" if key == STYLE_PRESET else ""
        print(f"  - {key}: {preset['name']}{marker}")
    print("=" * 60)


if __name__ == "__main__":
    main()
