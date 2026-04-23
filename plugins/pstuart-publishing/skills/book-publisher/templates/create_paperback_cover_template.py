#!/usr/bin/env python3
"""
Paperback Wrap Cover Generation Template
Creates full wrap covers (front + spine + back) for Amazon KDP print books.

CUSTOMIZATION REQUIRED:
1. Update BOOK_CONFIG with your book details
2. Set PAGE_COUNT to your book's final page count
3. Choose a STYLE_PRESET or customize COVER_STYLE
4. Update BACK_COVER content

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

# Book specifications
TRIM_WIDTH = 5.5   # inches (common trade paperback)
TRIM_HEIGHT = 8.5  # inches
PAGE_COUNT = 200   # UPDATE THIS with your actual page count
PAPER_TYPE = "white"  # "white" or "cream"

# Paper thickness (inches per page)
PAPER_THICKNESS = {
    "white": 0.002252,   # White paper
    "cream": 0.002500,   # Cream/off-white paper
}

# Print specifications
BLEED = 0.125      # inches bleed on all edges
SAFE_MARGIN = 0.25 # inches from trim edge for text
DPI = 300

# Book metadata
BOOK_CONFIG = {
    "title_line1": "YOUR BOOK",
    "title_line2": "TITLE",
    "subtitle_line1": "Your Compelling",
    "subtitle_line2": "Subtitle Here",
    "tagline": "A powerful tagline that hooks readers.",
    "author": "Author Name",
    "output_prefix": "YourBookTitle",
}

# Back cover content
BACK_COVER = {
    "hook_line1": "Your compelling hook line one.",
    "hook_line2": "Your compelling hook line two.",
    "question_line1": "What if everything you believed",
    "question_line2": "about success was backwards?",
    "body_lines": [
        "Author Name brings twenty-five years of",
        "expertise and real-world experience to",
        "this transformative guide.",
    ],
    "features_header": "INSIDE YOU'LL DISCOVER:",
    "features": [
        "+ Feature or benefit one",
        "+ Feature or benefit two",
        "+ Feature or benefit three",
        "+ Feature or benefit four",
    ],
    "author_bio_lines": [
        "has led in multiple industries, mentored",
        "hundreds, and brings decades of wisdom",
        "to this powerful guide.",
    ],
    "website": "yourwebsite.com",
    "price": "$24.99 US",
    "category": "Category / Subcategory",
}

# ============================================================================
# STYLE PRESETS - Same as Kindle cover for consistency
# ============================================================================

STYLE_PRESETS = {
    "navy_gold": {
        "name": "Navy & Gold",
        "background": (30, 58, 95),
        "background_light": (45, 75, 115),
        "accent": (201, 162, 39),
        "accent_light": (220, 190, 100),
        "title_color": (255, 255, 255),
        "subtitle_color": (201, 162, 39),
        "tagline_color": (220, 190, 100),
        "author_label_color": (255, 255, 255),
        "author_color": (201, 162, 39),
        "back_text": (240, 240, 240),
        "back_text_muted": (200, 200, 200),
    },
    "burgundy_cream": {
        "name": "Burgundy & Cream",
        "background": (88, 24, 32),
        "background_light": (110, 40, 50),
        "accent": (245, 235, 220),
        "accent_light": (255, 248, 240),
        "title_color": (255, 255, 255),
        "subtitle_color": (245, 235, 220),
        "tagline_color": (220, 200, 180),
        "author_label_color": (200, 180, 160),
        "author_color": (245, 235, 220),
        "back_text": (245, 235, 220),
        "back_text_muted": (200, 180, 160),
    },
    "teal_coral": {
        "name": "Teal & Coral",
        "background": (0, 95, 115),
        "background_light": (20, 115, 135),
        "accent": (255, 127, 102),
        "accent_light": (255, 180, 160),
        "title_color": (255, 255, 255),
        "subtitle_color": (255, 127, 102),
        "tagline_color": (200, 230, 235),
        "author_label_color": (200, 230, 235),
        "author_color": (255, 127, 102),
        "back_text": (230, 245, 248),
        "back_text_muted": (180, 210, 215),
    },
    "black_silver": {
        "name": "Black & Silver",
        "background": (25, 25, 25),
        "background_light": (45, 45, 45),
        "accent": (192, 192, 192),
        "accent_light": (230, 230, 230),
        "title_color": (255, 255, 255),
        "subtitle_color": (192, 192, 192),
        "tagline_color": (160, 160, 160),
        "author_label_color": (140, 140, 140),
        "author_color": (220, 220, 220),
        "back_text": (220, 220, 220),
        "back_text_muted": (160, 160, 160),
    },
    "earth_warm": {
        "name": "Earth Warm",
        "background": (89, 60, 31),
        "background_light": (110, 80, 50),
        "accent": (218, 165, 32),
        "accent_light": (245, 222, 179),
        "title_color": (255, 250, 240),
        "subtitle_color": (218, 165, 32),
        "tagline_color": (210, 180, 140),
        "author_label_color": (200, 180, 160),
        "author_color": (245, 222, 179),
        "back_text": (245, 235, 220),
        "back_text_muted": (200, 180, 160),
    },
    "purple_gold": {
        "name": "Purple & Gold",
        "background": (60, 25, 85),
        "background_light": (80, 45, 110),
        "accent": (218, 165, 32),
        "accent_light": (255, 215, 100),
        "title_color": (255, 255, 255),
        "subtitle_color": (218, 165, 32),
        "tagline_color": (200, 180, 220),
        "author_label_color": (180, 160, 200),
        "author_color": (255, 215, 100),
        "back_text": (230, 220, 240),
        "back_text_muted": (180, 160, 200),
    },
    "forest_cream": {
        "name": "Forest & Cream",
        "background": (34, 85, 51),
        "background_light": (50, 105, 70),
        "accent": (255, 248, 220),
        "accent_light": (255, 255, 240),
        "title_color": (255, 255, 255),
        "subtitle_color": (255, 248, 220),
        "tagline_color": (200, 230, 200),
        "author_label_color": (180, 210, 180),
        "author_color": (255, 248, 220),
        "back_text": (230, 245, 235),
        "back_text_muted": (180, 210, 180),
    },
}

# Choose your style preset
STYLE_PRESET = "navy_gold"

# ============================================================================
# CALCULATED DIMENSIONS
# ============================================================================

def calculate_dimensions():
    """Calculate all cover dimensions based on configuration."""
    spine_width = PAGE_COUNT * PAPER_THICKNESS[PAPER_TYPE]

    # Full cover dimensions in inches
    full_width = BLEED + TRIM_WIDTH + spine_width + TRIM_WIDTH + BLEED
    full_height = BLEED + TRIM_HEIGHT + BLEED

    # Convert to pixels
    width_px = int(full_width * DPI)
    height_px = int(full_height * DPI)
    bleed_px = int(BLEED * DPI)
    safe_px = int(SAFE_MARGIN * DPI)
    trim_width_px = int(TRIM_WIDTH * DPI)
    spine_width_px = int(spine_width * DPI)

    # Cover section boundaries (from left edge)
    back_start = bleed_px
    back_end = bleed_px + trim_width_px
    spine_start = back_end
    spine_end = spine_start + spine_width_px
    front_start = spine_end
    front_end = front_start + trim_width_px

    # Safe zones
    back_safe_left = bleed_px + safe_px
    back_safe_right = back_end - safe_px
    front_safe_left = front_start + safe_px
    front_safe_right = front_end - safe_px
    top_safe = bleed_px + safe_px
    bottom_safe = height_px - bleed_px - safe_px

    return {
        'spine_width': spine_width,
        'full_width': full_width,
        'full_height': full_height,
        'width_px': width_px,
        'height_px': height_px,
        'bleed_px': bleed_px,
        'safe_px': safe_px,
        'trim_width_px': trim_width_px,
        'spine_width_px': spine_width_px,
        'back_start': back_start,
        'back_end': back_end,
        'spine_start': spine_start,
        'spine_end': spine_end,
        'front_start': front_start,
        'front_end': front_end,
        'back_safe_left': back_safe_left,
        'back_safe_right': back_safe_right,
        'front_safe_left': front_safe_left,
        'front_safe_right': front_safe_right,
        'top_safe': top_safe,
        'bottom_safe': bottom_safe,
    }


def get_style():
    """Get the active style configuration."""
    return STYLE_PRESETS.get(STYLE_PRESET, STYLE_PRESETS["navy_gold"])


def load_fonts():
    """Load fonts with appropriate sizes for print."""
    fonts = {}
    try:
        base_path = "/System/Library/Fonts/Supplemental/"

        # Front cover fonts
        fonts['title_large'] = ImageFont.truetype(f"{base_path}Georgia Bold.ttf", 95)
        fonts['subtitle'] = ImageFont.truetype(f"{base_path}Georgia.ttf", 36)
        fonts['tagline'] = ImageFont.truetype(f"{base_path}Georgia Italic.ttf", 28)
        fonts['author_label'] = ImageFont.truetype(f"{base_path}Arial.ttf", 20)
        fonts['author'] = ImageFont.truetype(f"{base_path}Georgia Bold.ttf", 42)

        # Back cover fonts
        fonts['hook'] = ImageFont.truetype(f"{base_path}Georgia Italic.ttf", 34)
        fonts['body'] = ImageFont.truetype(f"{base_path}Georgia.ttf", 30)
        fonts['body_bold'] = ImageFont.truetype(f"{base_path}Georgia Bold.ttf", 30)
        fonts['bullets'] = ImageFont.truetype(f"{base_path}Georgia.ttf", 28)
        fonts['bio'] = ImageFont.truetype(f"{base_path}Georgia.ttf", 26)
        fonts['price'] = ImageFont.truetype(f"{base_path}Georgia Bold.ttf", 34)
        fonts['category'] = ImageFont.truetype(f"{base_path}Georgia.ttf", 24)
        fonts['url'] = ImageFont.truetype(f"{base_path}Georgia.ttf", 26)

        # Spine fonts
        fonts['spine_title'] = ImageFont.truetype(f"{base_path}Georgia Bold.ttf", 32)
        fonts['spine_author'] = ImageFont.truetype(f"{base_path}Georgia.ttf", 24)

    except:
        default = ImageFont.load_default()
        for key in ['title_large', 'subtitle', 'tagline', 'author_label', 'author',
                    'hook', 'body', 'body_bold', 'bullets', 'bio', 'price',
                    'category', 'url', 'spine_title', 'spine_author']:
            fonts[key] = default

    return fonts


def draw_centered_text(draw, text, y, font, fill, x_start, x_end):
    """Draw text centered between x_start and x_end."""
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    x = x_start + (x_end - x_start - text_width) // 2
    draw.text((x, y), text, font=font, fill=fill)
    return bbox[3] - bbox[1]


def draw_front_cover(draw, fonts, dims, style):
    """Draw the front cover section."""
    center_x = dims['front_start'] + dims['trim_width_px'] // 2

    # Top decorative line
    line_y = dims['top_safe'] + 120
    line_width = 320
    draw.rectangle(
        [center_x - line_width//2, line_y, center_x + line_width//2, line_y + 3],
        fill=style['accent']
    )

    # Title line 1
    draw_centered_text(draw, BOOK_CONFIG['title_line1'], dims['top_safe'] + 180,
                       fonts['title_large'], style['title_color'],
                       dims['front_safe_left'], dims['front_safe_right'])

    # Title line 2
    draw_centered_text(draw, BOOK_CONFIG['title_line2'], dims['top_safe'] + 290,
                       fonts['title_large'], style['title_color'],
                       dims['front_safe_left'], dims['front_safe_right'])

    # Subtitle line 1
    draw_centered_text(draw, BOOK_CONFIG['subtitle_line1'], dims['top_safe'] + 450,
                       fonts['subtitle'], style['subtitle_color'],
                       dims['front_safe_left'], dims['front_safe_right'])

    # Subtitle line 2
    draw_centered_text(draw, BOOK_CONFIG['subtitle_line2'], dims['top_safe'] + 495,
                       fonts['subtitle'], style['subtitle_color'],
                       dims['front_safe_left'], dims['front_safe_right'])

    # Tagline
    draw_centered_text(draw, BOOK_CONFIG['tagline'], dims['top_safe'] + 580,
                       fonts['tagline'], style['tagline_color'],
                       dims['front_safe_left'], dims['front_safe_right'])

    # Bottom decorative line
    line_y_bottom = dims['top_safe'] + 780
    draw.rectangle(
        [center_x - line_width//2, line_y_bottom, center_x + line_width//2, line_y_bottom + 3],
        fill=style['accent']
    )

    # "WRITTEN BY"
    draw_centered_text(draw, "WRITTEN BY", dims['bottom_safe'] - 220,
                       fonts['author_label'], style['author_label_color'],
                       dims['front_safe_left'], dims['front_safe_right'])

    # Author name
    draw_centered_text(draw, BOOK_CONFIG['author'], dims['bottom_safe'] - 180,
                       fonts['author'], style['author_color'],
                       dims['front_safe_left'], dims['front_safe_right'])


def draw_back_cover(draw, fonts, dims, style):
    """Draw the back cover section."""
    bc = BACK_COVER

    # Hook (gold, italic)
    hook_y = dims['top_safe'] + 80
    draw_centered_text(draw, bc['hook_line1'], hook_y,
                       fonts['hook'], style['accent'],
                       dims['back_safe_left'], dims['back_safe_right'])
    draw_centered_text(draw, bc['hook_line2'], hook_y + 45,
                       fonts['hook'], style['accent'],
                       dims['back_safe_left'], dims['back_safe_right'])

    # Opening question
    question_y = hook_y + 130
    draw_centered_text(draw, bc['question_line1'], question_y,
                       fonts['body'], style['back_text'],
                       dims['back_safe_left'], dims['back_safe_right'])
    draw_centered_text(draw, bc['question_line2'], question_y + 38,
                       fonts['body'], style['back_text'],
                       dims['back_safe_left'], dims['back_safe_right'])

    # Body paragraph
    body_y = question_y + 110
    for i, line in enumerate(bc['body_lines']):
        draw_centered_text(draw, line, body_y + i * 32,
                           fonts['bio'], style['back_text'],
                           dims['back_safe_left'], dims['back_safe_right'])

    # Features header
    inside_y = body_y + len(bc['body_lines']) * 32 + 50
    draw_centered_text(draw, bc['features_header'], inside_y,
                       fonts['body_bold'], style['accent'],
                       dims['back_safe_left'], dims['back_safe_right'])

    # Features list
    bullet_y = inside_y + 50
    for i, bullet in enumerate(bc['features']):
        draw_centered_text(draw, bullet, bullet_y + i * 38,
                           fonts['bullets'], style['back_text'],
                           dims['back_safe_left'], dims['back_safe_right'])

    # Divider line
    center_x = dims['back_start'] + (dims['back_end'] - dims['back_start']) // 2
    divider_y = bullet_y + len(bc['features']) * 38 + 30
    draw.rectangle(
        [center_x - 180, divider_y, center_x + 180, divider_y + 2],
        fill=style['accent']
    )

    # Author bio section
    bio_y = divider_y + 25
    draw_centered_text(draw, BOOK_CONFIG['author'], bio_y,
                       fonts['body_bold'], style['accent'],
                       dims['back_safe_left'], dims['back_safe_right'])

    for i, line in enumerate(bc['author_bio_lines']):
        draw_centered_text(draw, line, bio_y + 38 + i * 30,
                           fonts['bio'], style['back_text'],
                           dims['back_safe_left'], dims['back_safe_right'])

    # Bottom section
    bottom_y = dims['bottom_safe'] - 100

    # URL on left
    draw.text((dims['back_safe_left'], bottom_y + 35), bc['website'],
              font=fonts['url'], fill=style['accent'])

    # Price on right
    price_bbox = draw.textbbox((0, 0), bc['price'], font=fonts['price'])
    price_width = price_bbox[2] - price_bbox[0]
    draw.text((dims['back_safe_right'] - price_width, bottom_y), bc['price'],
              font=fonts['price'], fill=style['accent'])

    # Category
    cat_bbox = draw.textbbox((0, 0), bc['category'], font=fonts['category'])
    cat_width = cat_bbox[2] - cat_bbox[0]
    draw.text((dims['back_safe_right'] - cat_width, bottom_y + 42), bc['category'],
              font=fonts['category'], fill=style['back_text'])


def draw_spine(img, draw, fonts, dims, style):
    """Draw the spine with rotated text."""
    spine_center_x = dims['spine_start'] + dims['spine_width_px'] // 2

    # Only draw spine text if spine is wide enough (typically 79+ pages)
    if dims['spine_width_px'] < 19:  # ~0.0625 inches
        return

    # Title text
    title_text = f"{BOOK_CONFIG['title_line1']} {BOOK_CONFIG['title_line2']}"
    author_text = BOOK_CONFIG['author']

    # Create rotated title
    title_bbox = draw.textbbox((0, 0), title_text, font=fonts['spine_title'])
    title_width = title_bbox[2] - title_bbox[0]
    title_height = title_bbox[3] - title_bbox[1]

    title_img = Image.new('RGBA', (title_width + 10, title_height + 10), (0, 0, 0, 0))
    title_draw = ImageDraw.Draw(title_img)
    title_draw.text((5, 5), title_text, font=fonts['spine_title'], fill=style['title_color'])
    title_rotated = title_img.rotate(90, expand=True)

    # Create rotated author
    author_bbox = draw.textbbox((0, 0), author_text, font=fonts['spine_author'])
    author_width = author_bbox[2] - author_bbox[0]
    author_height = author_bbox[3] - author_bbox[1]

    author_img = Image.new('RGBA', (author_width + 10, author_height + 10), (0, 0, 0, 0))
    author_draw = ImageDraw.Draw(author_img)
    author_draw.text((5, 5), author_text, font=fonts['spine_author'], fill=style['accent'])
    author_rotated = author_img.rotate(90, expand=True)

    # Position and paste
    title_paste_x = spine_center_x - title_rotated.width // 2
    title_paste_y = (dims['height_px'] - title_rotated.height) // 2 + 100
    img.paste(title_rotated, (title_paste_x, title_paste_y), title_rotated)

    author_paste_x = spine_center_x - author_rotated.width // 2
    author_paste_y = dims['top_safe'] + 80
    img.paste(author_rotated, (author_paste_x, author_paste_y), author_rotated)


def create_cover():
    """Create the full paperback wrap cover."""
    dims = calculate_dimensions()
    style = get_style()

    # Create base image
    img = Image.new('RGB', (dims['width_px'], dims['height_px']), style['background'])
    draw = ImageDraw.Draw(img)

    # Load fonts
    fonts = load_fonts()

    # Draw each section
    draw_front_cover(draw, fonts, dims, style)
    draw_back_cover(draw, fonts, dims, style)
    draw_spine(img, draw, fonts, dims, style)

    return img, dims


def main():
    """Generate the paperback wrap cover."""
    dims = calculate_dimensions()
    style = get_style()

    print("=" * 60)
    print("Paperback Wrap Cover Generation")
    print("=" * 60)
    print(f"\nStyle: {style['name']}")
    print(f"Trim size: {TRIM_WIDTH}\" x {TRIM_HEIGHT}\"")
    print(f"Page count: {PAGE_COUNT}")
    print(f"Paper type: {PAPER_TYPE}")
    print(f"Spine width: {dims['spine_width']:.3f}\"")
    print(f"Full dimensions: {dims['full_width']:.2f}\" x {dims['full_height']:.2f}\"")
    print(f"Pixels at {DPI} DPI: {dims['width_px']} x {dims['height_px']}")
    print(f"Safe margin: {SAFE_MARGIN}\" from trim")

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Create the cover
    cover, _ = create_cover()

    # Generate filenames
    prefix = BOOK_CONFIG['output_prefix']

    # Save as PDF (preferred for print)
    pdf_path = OUTPUT_DIR / f"{prefix}_Paperback_Cover.pdf"
    cover.save(pdf_path, "PDF", resolution=DPI)
    print(f"\nPDF saved: {pdf_path}")

    # Save as PNG for preview
    png_path = OUTPUT_DIR / f"{prefix}_Paperback_Cover.png"
    cover.save(png_path, "PNG")
    print(f"PNG preview: {png_path}")

    # Save as JPEG
    jpg_path = OUTPUT_DIR / f"{prefix}_Paperback_Cover.jpg"
    cover.save(jpg_path, "JPEG", quality=95)
    print(f"JPEG saved: {jpg_path}")

    print(f"\nCover dimensions: {cover.width} x {cover.height} pixels")

    print("\n" + "=" * 60)
    print("Available style presets:")
    for key, preset in STYLE_PRESETS.items():
        marker = " <-- ACTIVE" if key == STYLE_PRESET else ""
        print(f"  - {key}: {preset['name']}{marker}")
    print("=" * 60)


if __name__ == "__main__":
    main()
