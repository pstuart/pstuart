#!/usr/bin/env python3
"""
Professional PDF Generation Template
Generate Amazon-ready trade paperback PDFs with full styling.

CUSTOMIZATION REQUIRED:
1. Update BASE_DIR to your book project path
2. Update BOOK_CONFIG with your book details
3. Update COVER_COLORS and DESIGN_COLORS for your theme
4. Update toc_items in main() with your chapter structure
5. Optionally add custom infographic methods

Features:
- Two-pass generation for accurate TOC page numbers
- Full-color front cover with gradient
- Professional interior styling (pull quotes, insight boxes, etc.)
- Running headers/footers with chapter tracking
- Tables, checkboxes, blockquotes with visual styling
- Infographic/flowchart generation methods
- Trade paperback size (5.5 x 8.5")
- Unicode font support via TTF loading
"""

import re
from pathlib import Path
from datetime import datetime
from fpdf import FPDF

# ============================================================================
# CONFIGURATION - CUSTOMIZE THESE FOR YOUR BOOK
# ============================================================================

BASE_DIR = Path("/path/to/your/BookProject")
PUB_DIR = BASE_DIR / "publishing"

# Book metadata and marketing copy
BOOK_CONFIG = {
    "title": "YOUR BOOK TITLE",
    "subtitle": "Your Compelling Subtitle Here",
    "author": "Author Name",
    "tagline": "A one-line hook that captures your book's promise.",
    "website": "yourwebsite.com",
    "price": "$24.99 US",
    "category": "Category / Subcategory",
    "hook": "Opening hook for back cover that draws readers in immediately.",
    "author_bio": "Author Name has spent years mastering this topic. This book shares their proven system for success.",
    "dedication": "For those who believed in this work.",
}

# ============================================================================
# STYLE PRESETS - Choose one or customize your own
# ============================================================================

STYLE_PRESETS = {
    # Professional navy and gold (business, leadership, non-fiction)
    "navy_gold": {
        "name": "Navy & Gold",
        "cover": {
            "gradient_start": (15, 32, 55),
            "gradient_end": (25, 55, 95),
            "accent": (218, 165, 32),
            "accent_light": (255, 215, 100),
            "text_light": (240, 240, 240),
            "text_muted": (200, 200, 200),
        },
        "interior": {
            "primary": (15, 32, 55),
            "primary_light": (35, 65, 115),
            "accent": (178, 134, 11),
            "accent_light": (255, 248, 220),
            "accent_border": (218, 165, 32),
            "text": (40, 40, 40),
            "bg_light": (245, 245, 245),
            "gray": (180, 180, 180),
        },
    },
    # Deep burgundy and cream (literary, memoir, sophisticated)
    "burgundy_cream": {
        "name": "Burgundy & Cream",
        "cover": {
            "gradient_start": (68, 14, 22),
            "gradient_end": (98, 34, 42),
            "accent": (245, 235, 220),
            "accent_light": (255, 248, 240),
            "text_light": (255, 255, 255),
            "text_muted": (220, 200, 190),
        },
        "interior": {
            "primary": (88, 24, 32),
            "primary_light": (120, 50, 60),
            "accent": (160, 140, 120),
            "accent_light": (255, 250, 245),
            "accent_border": (180, 160, 140),
            "text": (50, 40, 40),
            "bg_light": (252, 250, 248),
            "gray": (180, 170, 165),
        },
    },
    # Modern teal and coral (self-help, wellness, contemporary)
    "teal_coral": {
        "name": "Teal & Coral",
        "cover": {
            "gradient_start": (0, 75, 95),
            "gradient_end": (0, 105, 125),
            "accent": (255, 127, 102),
            "accent_light": (255, 180, 160),
            "text_light": (255, 255, 255),
            "text_muted": (200, 230, 235),
        },
        "interior": {
            "primary": (0, 95, 115),
            "primary_light": (0, 130, 150),
            "accent": (230, 100, 80),
            "accent_light": (255, 240, 235),
            "accent_border": (255, 127, 102),
            "text": (40, 45, 50),
            "bg_light": (245, 250, 252),
            "gray": (170, 185, 190),
        },
    },
    # Classic black and silver (thriller, mystery, serious)
    "black_silver": {
        "name": "Black & Silver",
        "cover": {
            "gradient_start": (15, 15, 15),
            "gradient_end": (35, 35, 35),
            "accent": (192, 192, 192),
            "accent_light": (230, 230, 230),
            "text_light": (255, 255, 255),
            "text_muted": (160, 160, 160),
        },
        "interior": {
            "primary": (30, 30, 30),
            "primary_light": (80, 80, 80),
            "accent": (140, 140, 140),
            "accent_light": (248, 248, 248),
            "accent_border": (180, 180, 180),
            "text": (35, 35, 35),
            "bg_light": (250, 250, 250),
            "gray": (160, 160, 160),
        },
    },
    # Warm earth tones (spirituality, nature, grounded)
    "earth_warm": {
        "name": "Earth Warm",
        "cover": {
            "gradient_start": (69, 45, 21),
            "gradient_end": (99, 70, 41),
            "accent": (218, 165, 32),
            "accent_light": (245, 222, 179),
            "text_light": (255, 250, 240),
            "text_muted": (210, 180, 140),
        },
        "interior": {
            "primary": (89, 60, 31),
            "primary_light": (130, 100, 60),
            "accent": (180, 130, 20),
            "accent_light": (255, 250, 235),
            "accent_border": (200, 150, 50),
            "text": (50, 40, 30),
            "bg_light": (252, 248, 240),
            "gray": (180, 165, 150),
        },
    },
    # Royal purple and gold (luxury, transformation, spiritual)
    "purple_gold": {
        "name": "Purple & Gold",
        "cover": {
            "gradient_start": (45, 15, 65),
            "gradient_end": (70, 35, 95),
            "accent": (218, 165, 32),
            "accent_light": (255, 215, 100),
            "text_light": (255, 255, 255),
            "text_muted": (200, 180, 220),
        },
        "interior": {
            "primary": (60, 25, 85),
            "primary_light": (100, 60, 130),
            "accent": (178, 134, 11),
            "accent_light": (255, 250, 235),
            "accent_border": (200, 150, 30),
            "text": (45, 35, 55),
            "bg_light": (252, 250, 255),
            "gray": (175, 165, 185),
        },
    },
    # Forest green and cream (nature, sustainability, wisdom)
    "forest_cream": {
        "name": "Forest & Cream",
        "cover": {
            "gradient_start": (24, 65, 41),
            "gradient_end": (44, 95, 61),
            "accent": (255, 248, 220),
            "accent_light": (255, 255, 240),
            "text_light": (255, 255, 255),
            "text_muted": (200, 230, 200),
        },
        "interior": {
            "primary": (34, 85, 51),
            "primary_light": (60, 120, 80),
            "accent": (160, 140, 100),
            "accent_light": (250, 255, 245),
            "accent_border": (180, 160, 120),
            "text": (40, 50, 40),
            "bg_light": (248, 252, 248),
            "gray": (165, 180, 170),
        },
    },
    # Minimalist white and black (modern, clean, professional)
    "minimal_white": {
        "name": "Minimal White",
        "cover": {
            "gradient_start": (245, 245, 245),
            "gradient_end": (255, 255, 255),
            "accent": (30, 30, 30),
            "accent_light": (80, 80, 80),
            "text_light": (20, 20, 20),
            "text_muted": (100, 100, 100),
        },
        "interior": {
            "primary": (30, 30, 30),
            "primary_light": (80, 80, 80),
            "accent": (100, 100, 100),
            "accent_light": (252, 252, 252),
            "accent_border": (60, 60, 60),
            "text": (30, 30, 30),
            "bg_light": (250, 250, 250),
            "gray": (180, 180, 180),
        },
    },
}

# ============================================================================
# ACTIVE STYLE SELECTION
# ============================================================================

# Choose your style preset here (or set to None and use custom colors below)
STYLE_PRESET = "navy_gold"

# Get colors from preset or use custom
def get_style_colors():
    """Return the active color scheme based on preset or custom."""
    if STYLE_PRESET and STYLE_PRESET in STYLE_PRESETS:
        preset = STYLE_PRESETS[STYLE_PRESET]
        return preset["cover"], preset["interior"]
    return COVER_COLORS, DESIGN_COLORS

# Custom color scheme (used if STYLE_PRESET is None)
COVER_COLORS = {
    "gradient_start": (15, 32, 55),     # Dark navy
    "gradient_end": (25, 55, 95),       # Deep blue
    "accent": (218, 165, 32),           # Gold
    "accent_light": (255, 215, 100),    # Light gold
    "text_light": (240, 240, 240),      # Light text
    "text_muted": (200, 200, 200),      # Muted text
}

# Custom interior design colors (used if STYLE_PRESET is None)
DESIGN_COLORS = {
    "primary": (15, 32, 55),            # Primary color for headings
    "primary_light": (35, 65, 115),     # Lighter primary for accents
    "accent": (178, 134, 11),           # Accent for highlights
    "accent_light": (255, 248, 220),    # Very light accent background
    "accent_border": (218, 165, 32),    # Accent for borders
    "text": (40, 40, 40),               # Dark text
    "bg_light": (245, 245, 245),        # Light gray background
    "gray": (180, 180, 180),            # Medium gray for rules
}

# ============================================================================
# LAYOUT PROFILES (Copy Fitting)
# ============================================================================

# Standard layout - comfortable reading, more pages
LAYOUT_STANDARD = {
    "MARGIN_H": 0.625,              # inches horizontal margins
    "MARGIN_TOP": 0.75,
    "MARGIN_BOTTOM": 0.75,
    "LINE_HEIGHT_BODY": 0.18,       # inches between lines
    "LINE_HEIGHT_CODE": 0.12,
    "PARA_SPACING": 0.06,
    "SECTION_SPACING_BEFORE": 0.16,
    "SECTION_SPACING_AFTER": 0.04,
    "H2_FONT_SIZE": 13,
    "H3_FONT_SIZE": 11,
    "H4_FONT_SIZE": 10,
    # Orphan prevention (generous - fewer orphans, more whitespace)
    "H1_MIN_AFTER": 2.0,            # inches
    "H2_MIN_AFTER": 1.8,
    "H3_MIN_AFTER": 2.8,
    "H4_MIN_AFTER": 2.2,
}

# Copy-fitted layout - 20-25% denser, fewer pages
LAYOUT_COMPACT = {
    "MARGIN_H": 0.5,                # Tighter margins
    "MARGIN_TOP": 0.6,
    "MARGIN_BOTTOM": 0.65,
    "LINE_HEIGHT_BODY": 0.165,      # Tighter line spacing
    "LINE_HEIGHT_CODE": 0.11,
    "PARA_SPACING": 0.05,
    "SECTION_SPACING_BEFORE": 0.12,
    "SECTION_SPACING_AFTER": 0.03,
    "H2_FONT_SIZE": 12,             # Slightly smaller headings
    "H3_FONT_SIZE": 10,
    "H4_FONT_SIZE": 9.5,
    # Orphan prevention (balanced - some orphans ok for space savings)
    "H1_MIN_AFTER": 1.4,
    "H2_MIN_AFTER": 1.2,
    "H3_MIN_AFTER": 1.8,
    "H4_MIN_AFTER": 1.4,
}

# Select active layout profile
LAYOUT = LAYOUT_STANDARD  # Change to LAYOUT_COMPACT for copy-fitted output

# Key quotes to highlight with pull quote styling (optional)
# These phrases will be auto-detected and styled as pull quotes
PULL_QUOTES = [
    "Your memorable quote here.",
    "Another key statement to highlight.",
    # Add more key phrases from your book
]

# Features for back cover bullet list
BACK_COVER_FEATURES = [
    "First key benefit readers will get from your book",
    "Second compelling reason to buy",
    "Third value proposition",
    "Fourth takeaway or promise",
]


# ============================================================================
# TEXT UTILITIES
# ============================================================================

def sanitize_text(text):
    """Normalize text and handle Unicode characters for PDF output."""
    # Convert double hyphens to em dash
    text = text.replace('--', '\u2014')

    # Unicode replacements for latin-1 compatibility
    replacements = {
        '\u2013': '-',        # en dash to hyphen
        '\u2014': '-',        # em dash to hyphen (after conversion)
        '\u2018': "'",        # left single quote
        '\u2019': "'",        # right single quote
        '\u201c': '"',        # left double quote
        '\u201d': '"',        # right double quote
        '\u2026': '...',      # ellipsis
        '\u2022': '-',        # bullet
        '\u00a0': ' ',        # non-breaking space
        '\u00a9': '(c)',      # copyright
        '\u00ae': '(R)',      # registered
        '\u2122': '(TM)',     # trademark
        '\u2212': '-',        # minus sign
        '\u00d7': 'x',        # multiplication
        '\u2032': "'",        # prime
        '\u2033': '"',        # double prime
        '\u00b7': '-',        # middle dot
        '\u2010': '-',        # hyphen
        '\u2011': '-',        # non-breaking hyphen
        '\ufffd': '?',        # replacement character
        '\u2500': '-',        # horizontal line
        '\u2502': '|',        # vertical line
        '\u251c': '|--',      # T-branch right
        '\u2514': '`--',      # L-corner
        '\u2192': '->',       # right arrow
        '\u2190': '<-',       # left arrow
    }
    for char, repl in replacements.items():
        text = text.replace(char, repl)

    return text.encode('cp1252', errors='replace').decode('cp1252')


def strip_markdown(text):
    """Remove markdown formatting and convert to plain text."""
    text = sanitize_text(text)
    # Convert checkboxes to markers for later rendering
    text = re.sub(r'\[\s*[xX]\s*\]', '\x01CHECKED\x01', text)
    text = re.sub(r'\[\s*\]', '\x01UNCHECKED\x01', text)
    # Remove markdown formatting
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)  # Bold
    text = re.sub(r'\*(.+?)\*', r'\1', text)      # Italic
    text = re.sub(r'_(.+?)_', r'\1', text)        # Underscore italic
    text = re.sub(r'`(.+?)`', r'\1', text)        # Code
    text = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', text)  # Links
    return text.strip()


# ============================================================================
# PDF CLASS WITH FULL STYLING
# ============================================================================

class BookPDF(FPDF):
    def __init__(self):
        super().__init__(unit='in', format=(5.5, 8.5))
        # Apply layout profile settings
        self.set_auto_page_break(auto=True, margin=LAYOUT["MARGIN_BOTTOM"])
        self.set_margins(LAYOUT["MARGIN_H"], LAYOUT["MARGIN_TOP"], LAYOUT["MARGIN_H"])
        self.chapter_title = ""
        self.in_front_matter = True
        self.page_numbers = {}
        self.collecting_pages = False
        self.is_chapter_start = False
        self.layout = LAYOUT  # Store for reference

        # Try to load Unicode-compatible TTF fonts
        self._load_fonts()

    def _load_fonts(self):
        """Load system TTF fonts for Unicode support."""
        try:
            base = "/System/Library/Fonts/Supplemental/"
            self.add_font("TimesNR", "", f"{base}Times New Roman.ttf")
            self.add_font("TimesNR", "B", f"{base}Times New Roman Bold.ttf")
            self.add_font("TimesNR", "I", f"{base}Times New Roman Italic.ttf")
            self.add_font("TimesNR", "BI", f"{base}Times New Roman Bold Italic.ttf")
            self.unicode_font = "TimesNR"
        except Exception:
            self.unicode_font = None

    def use_font(self, style='', size=10):
        """Set font using Unicode font if available, otherwise Times."""
        font = self.unicode_font if self.unicode_font else 'Times'
        self.set_font(font, style, size)

    def header(self):
        """Running header with book/chapter title."""
        if self.page_no() > 6 and not self.in_front_matter and not self.is_chapter_start:
            self.set_y(0.3)
            self.set_text_color(150, 150, 150)
            if self.page_no() % 2 == 0:
                self.use_font('I', 8)
                self.cell(0, 0.15, BOOK_CONFIG["title"].upper(), align='L')
            else:
                header_text = self.chapter_title.upper()
                font_size = 7 if len(header_text) > 25 else 8
                self.use_font('I', font_size)
                self.cell(0, 0.15, header_text, align='R')
            self.ln(0.1)
            self.set_draw_color(200, 200, 200)
            self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
            self.set_y(0.75)

    def footer(self):
        """Page number footer."""
        if self.page_no() > 6 and not self.in_front_matter:
            self.set_y(-0.35)
            self.use_font('', 9)
            self.set_text_color(120, 120, 120)
            self.cell(0, 0.2, str(self.page_no()), align='C')

    # ========================================================================
    # COVER METHODS
    # ========================================================================

    def draw_gradient_background(self):
        """Draw gradient background for covers."""
        c = COVER_COLORS
        strips = 50
        for i in range(strips):
            r = int(c["gradient_start"][0] + (c["gradient_end"][0] - c["gradient_start"][0]) * i / strips)
            g = int(c["gradient_start"][1] + (c["gradient_end"][1] - c["gradient_start"][1]) * i / strips)
            b = int(c["gradient_start"][2] + (c["gradient_end"][2] - c["gradient_start"][2]) * i / strips)
            self.set_fill_color(r, g, b)
            y = i * self.h / strips
            self.rect(0, y, self.w, self.h / strips + 0.01, 'F')

    def front_cover(self):
        """Generate front cover page."""
        self.add_page()
        self.in_front_matter = True
        self.draw_gradient_background()

        c = COVER_COLORS

        # Decorative line at top
        self.set_draw_color(*c["accent"])
        self.set_line_width(0.02)
        self.line(1.5, 1.5, 4.0, 1.5)

        # Title (split if needed)
        self.set_y(2.0)
        self.use_font('B', 26)
        self.set_text_color(255, 255, 255)
        title_parts = BOOK_CONFIG["title"].upper().split()
        if len(title_parts) > 2:
            mid = len(title_parts) // 2
            line1 = ' '.join(title_parts[:mid])
            line2 = ' '.join(title_parts[mid:])
            self.cell(0, 0.45, line1, align='C', new_x='LMARGIN', new_y='NEXT')
            self.cell(0, 0.45, line2, align='C', new_x='LMARGIN', new_y='NEXT')
        else:
            self.cell(0, 0.45, BOOK_CONFIG["title"].upper(), align='C', new_x='LMARGIN', new_y='NEXT')

        # Subtitle
        self.ln(0.2)
        self.use_font('', 11)
        self.set_text_color(*c["accent"])
        self.multi_cell(0, 0.22, BOOK_CONFIG["subtitle"], align='C')

        # Tagline
        self.ln(0.4)
        self.use_font('I', 10)
        self.set_text_color(*c["text_muted"])
        self.cell(0, 0.2, BOOK_CONFIG["tagline"], align='C')

        # Decorative line
        self.set_y(5.5)
        self.set_draw_color(*c["accent"])
        self.line(1.5, 5.5, 4.0, 5.5)

        # Author at bottom
        self.set_y(self.h - 1.5)
        self.use_font('', 10)
        self.set_text_color(*c["text_muted"])
        self.cell(0, 0.2, "WRITTEN BY", align='C', new_x='LMARGIN', new_y='NEXT')
        self.use_font('B', 14)
        self.set_text_color(*c["accent"])
        self.cell(0, 0.3, BOOK_CONFIG["author"], align='C')

    def title_page(self):
        """Generate interior title page."""
        self.add_page()
        self.set_y(2.5)
        self.use_font('B', 22)
        self.set_text_color(0, 0, 0)
        self.cell(0, 0.45, BOOK_CONFIG["title"].upper(), align='C', new_x='LMARGIN', new_y='NEXT')
        self.ln(0.2)
        self.use_font('', 12)
        self.multi_cell(0, 0.22, BOOK_CONFIG["subtitle"], align='C')
        self.ln(0.5)
        self.use_font('', 12)
        self.cell(0, 0.3, BOOK_CONFIG["author"], align='C')

    def copyright_page(self):
        """Generate copyright page."""
        self.add_page()
        self.use_font('', 9)
        self.set_text_color(60, 60, 60)

        year = datetime.now().year
        text = f"""{BOOK_CONFIG["title"]}: {BOOK_CONFIG["subtitle"]}

Copyright (c) {year} by {BOOK_CONFIG["author"]}

All rights reserved. No part of this publication may be reproduced, distributed, or transmitted in any form or by any means, including photocopying, recording, or other electronic or mechanical methods, without the prior written permission of the publisher, except in the case of brief quotations embodied in critical reviews.

DISCLAIMER: This book is intended for informational and educational purposes only. The author is not a licensed professional advisor. Before making any decisions, readers should consult with qualified professionals.

ISBN: 978-1-XXXXXX-XX-X (Paperback)
ISBN: 978-1-XXXXXX-XX-X (eBook)

First Edition: {year}

{BOOK_CONFIG["website"]}

Printed in the United States of America

10  9  8  7  6  5  4  3  2  1"""

        for para in text.split('\n\n'):
            self.multi_cell(0, 0.18, para.strip())
            self.ln(0.15)

    def dedication_page(self):
        """Generate dedication page."""
        self.add_page()
        self.set_y(2.5)
        self.use_font('I', 11)
        self.set_text_color(60, 60, 60)
        for line in BOOK_CONFIG["dedication"].split('\n'):
            self.multi_cell(0, 0.22, line, align='C')
            self.ln(0.1)

    def table_of_contents(self, toc_items):
        """Generate table of contents with collected page numbers."""
        self.add_page()
        self.set_y(0.8)
        self.use_font('B', 13)
        self.set_text_color(0, 0, 0)
        self.cell(0, 0.25, 'CONTENTS', align='C', new_x='LMARGIN', new_y='NEXT')
        self.ln(0.12)

        width = self.w - self.l_margin - self.r_margin
        line_height = 0.175

        for item, key, is_part in toc_items:
            page_num = self.page_numbers.get(key, "")
            page_str = str(page_num)

            if is_part:
                self.ln(0.06)
                self.use_font('B', 9)
                indent = 0
            else:
                self.use_font('', 9)
                indent = 0.15

            self.set_x(self.l_margin + indent)
            page_width = self.get_string_width(page_str)
            item_max_width = width - indent - page_width - 0.2
            self.cell(item_max_width, line_height, item, align='L')
            self.set_x(self.l_margin + width - page_width)
            self.cell(page_width, line_height, page_str, align='R', new_x='LMARGIN', new_y='NEXT')

    # ========================================================================
    # INTERIOR STYLING ELEMENTS
    # ========================================================================

    def pull_quote(self, text):
        """Render a styled pull quote with gold accent box."""
        d = DESIGN_COLORS

        if self.get_y() > 6.5:
            self.add_page()

        self.ln(0.15)
        width = self.w - self.l_margin - self.r_margin - 0.4
        x_start = self.l_margin + 0.2
        y_start = self.get_y()

        # Gold left border
        self.set_fill_color(*d["gold_border"])
        self.rect(x_start, y_start, 0.04, 0.8, 'F')

        # Light gold background
        self.set_fill_color(*d["gold_light"])
        self.rect(x_start + 0.08, y_start, width - 0.08, 0.8, 'F')

        # Quote text
        self.set_xy(x_start + 0.2, y_start + 0.15)
        self.use_font('I', 11)
        self.set_text_color(*d["navy"])
        self.multi_cell(width - 0.4, 0.22, sanitize_text(text), align='C')

        self.set_y(y_start + 0.9)
        self.ln(0.1)

    def key_insight_box(self, title, content):
        """Render a key insight box with navy header."""
        d = DESIGN_COLORS

        if self.get_y() > 6.0:
            self.add_page()

        self.ln(0.1)
        width = self.w - self.l_margin - self.r_margin
        x_start = self.l_margin
        y_start = self.get_y()

        # Calculate heights
        title_upper = sanitize_text(title.upper())
        header_height = 0.28
        estimated_lines = max(2, len(content) // 55 + 1)
        content_height = (estimated_lines * 0.17) + 0.15
        box_height = header_height + content_height

        # Navy header bar
        self.set_fill_color(*d["navy"])
        self.rect(x_start, y_start, width, header_height, 'F')

        # Gray content background
        self.set_fill_color(*d["gray_light"])
        self.rect(x_start, y_start + header_height, width, content_height, 'F')

        # Border
        self.set_draw_color(*d["gold_border"])
        self.set_line_width(0.02)
        self.rect(x_start, y_start, width, box_height, 'D')

        # Title
        self.set_xy(x_start + 0.1, y_start + 0.06)
        self.use_font('B', 9)
        self.set_text_color(255, 255, 255)
        self.multi_cell(width - 0.2, 0.16, title_upper, align='L')

        # Content
        self.set_xy(x_start + 0.1, y_start + header_height + 0.07)
        self.use_font('', 9)
        self.set_text_color(*d["charcoal"])
        self.multi_cell(width - 0.2, 0.17, sanitize_text(content))

        self.set_y(y_start + box_height + 0.1)

    def draw_decorative_line(self, style='gold'):
        """Draw a decorative divider line with optional diamond."""
        d = DESIGN_COLORS
        y = self.get_y()
        x_center = self.w / 2

        if style == 'gold':
            self.set_draw_color(*d["gold_border"])
            self.set_line_width(0.015)
            self.line(self.l_margin + 0.5, y, x_center - 0.15, y)
            self.line(x_center + 0.15, y, self.w - self.r_margin - 0.5, y)
            # Diamond
            self.set_fill_color(*d["gold_border"])
            size = 0.06
            self._draw_diamond(x_center, y, size)
        elif style == 'simple':
            self.set_draw_color(*d["gray_medium"])
            self.set_line_width(0.01)
            self.line(self.l_margin + 1, y, self.w - self.r_margin - 1, y)

        self.ln(0.15)

    def _draw_diamond(self, x, y, size):
        """Draw a small diamond shape."""
        self._out(f'{x*72:.2f} {(self.h-(y-size))*72:.2f} m')
        self._out(f'{(x+size)*72:.2f} {(self.h-y)*72:.2f} l')
        self._out(f'{x*72:.2f} {(self.h-(y+size))*72:.2f} l')
        self._out(f'{(x-size)*72:.2f} {(self.h-y)*72:.2f} l')
        self._out('f')

    def chapter_number_badge(self, num):
        """Draw a styled chapter number badge."""
        d = DESIGN_COLORS
        x_center = self.w / 2
        y_center = self.get_y() + 0.25
        radius = 0.25

        # Gold circle
        self.set_fill_color(*d["gold_border"])
        self.set_draw_color(*d["navy"])
        self.set_line_width(0.02)
        self.ellipse(x_center - radius, y_center - radius, radius * 2, radius * 2, 'FD')

        # Number
        self.use_font('B', 14)
        self.set_text_color(*d["navy"])
        num_str = str(num)
        num_width = self.get_string_width(num_str)
        self.set_xy(x_center - num_width/2, y_center - 0.1)
        self.cell(num_width, 0.2, num_str, align='C')

        self.set_y(y_center + radius + 0.1)

    def _render_chapter_motif_if_present(self, num, title) -> bool:
        """If assets/chapter_motif.png exists, render as top banner.

        Returns True if motif was rendered (caller should skip its own top
        margin positioning since this has already set_y below the banner),
        False otherwise.
        """
        from pathlib import Path
        motif_path = Path(__file__).parent.parent / "assets" / "chapter_motif.png"
        if not motif_path.exists():
            return False
        # Banner is top 40% of page height, full page width (no margins).
        banner_h = self.h * 0.40
        self.image(str(motif_path), x=0, y=0, w=self.w, h=banner_h)
        # Move cursor below motif with a 0.15" whitespace gap (no divider rule).
        self.set_y(banner_h + 0.15)
        return True

    # ========================================================================
    # CHAPTER AND SECTION METHODS
    # ========================================================================

    def chapter_heading(self, num, title, toc_key=None):
        """Generate chapter heading with styling."""
        d = DESIGN_COLORS

        if num:
            self.chapter_title = f'Chapter {num}'
        else:
            clean = strip_markdown(title)
            self.chapter_title = clean[:30] if len(clean) > 30 else clean

        self.is_chapter_start = True
        self.add_page()
        self.is_chapter_start = False
        self.in_front_matter = False

        if self.collecting_pages:
            if toc_key:
                self.page_numbers[toc_key] = self.page_no()
            elif num:
                self.page_numbers[f"ch_{num}"] = self.page_no()

        # Optional chapter motif banner. If present, the helper already
        # positioned the cursor below the banner; otherwise use the
        # default top-margin positioning.
        if not self._render_chapter_motif_if_present(num, title):
            self.set_y(1.0)

        if num:
            self.chapter_number_badge(num)
            self.ln(0.15)

        self.use_font('B', 16)
        self.set_text_color(*d["navy"])
        width = self.w - self.l_margin - self.r_margin
        self.multi_cell(width, 0.28, strip_markdown(title), align='C')

        self.ln(0.15)
        self.draw_decorative_line('gold')
        self.ln(0.2)

    def part_page(self, part_num, title, subtitle=""):
        """Generate part divider page."""
        d = DESIGN_COLORS

        self.is_chapter_start = True
        self.add_page()
        self.is_chapter_start = False
        self.in_front_matter = False

        if self.collecting_pages:
            self.page_numbers[f"part_{part_num}"] = self.page_no()

        # Decorative gold bars
        self.set_fill_color(*d["gold_border"])
        self.rect(0, 0, self.w, 0.08, 'F')
        self.rect(0, self.h - 0.08, self.w, 0.08, 'F')

        self.set_y(2.8)
        self.draw_decorative_line('gold')
        self.ln(0.3)

        self.use_font('B', 14)
        self.set_text_color(*d["gold"])
        self.cell(0, 0.3, f'PART {part_num}', align='C', new_x='LMARGIN', new_y='NEXT')
        self.ln(0.15)

        self.use_font('B', 18)
        self.set_text_color(*d["navy"])
        self.cell(0, 0.4, title.upper(), align='C', new_x='LMARGIN', new_y='NEXT')

        if subtitle:
            self.ln(0.2)
            self.use_font('I', 11)
            self.set_text_color(*d["charcoal"])
            self.cell(0, 0.25, subtitle, align='C')

        self.ln(0.4)
        self.draw_decorative_line('gold')

    def section_heading(self, title):
        """Generate section heading (##) with gold accent."""
        d = DESIGN_COLORS
        clean_title = strip_markdown(title)

        # Check for practical tool sections
        if 'PRACTICAL TOOL' in clean_title.upper():
            self.add_page()
            self.ln(0.1)
            y_start = self.get_y()
            width = self.w - self.l_margin - self.r_margin
            box_height = 0.35

            self.set_fill_color(*d["gold_light"])
            self.rect(self.l_margin, y_start, width, box_height, 'F')
            self.set_draw_color(*d["gold_border"])
            self.set_line_width(0.02)
            self.rect(self.l_margin, y_start, width, box_height, 'D')

            self.set_xy(self.l_margin + 0.1, y_start + 0.08)
            self.use_font('B', 11)
            self.set_text_color(*d["navy"])
            self.multi_cell(width - 0.2, 0.18, clean_title, align='C')
            self.set_y(y_start + box_height + 0.1)
            self.ln(0.1)
        else:
            remaining_space = 7.75 - self.get_y()
            if remaining_space < 2.0:
                self.add_page()

            self.ln(0.2)
            y_pos = self.get_y()

            # Gold accent bar
            self.set_fill_color(*d["gold_border"])
            self.rect(self.l_margin, y_pos, 0.04, 0.22, 'F')

            self.set_x(self.l_margin + 0.12)
            self.use_font('B', 11)
            self.set_text_color(*d["navy"])
            width = self.w - self.l_margin - self.r_margin - 0.12
            self.multi_cell(width, 0.22, clean_title)
            self.ln(0.08)

    def subsection_heading(self, title):
        """Generate subsection heading (###)."""
        d = DESIGN_COLORS
        clean_title = strip_markdown(title)

        remaining_space = 7.75 - self.get_y()
        is_step = re.match(r'STEP\s+\d', clean_title, re.IGNORECASE)

        if is_step and remaining_space < 2.5:
            self.add_page()
        elif remaining_space < 1.5:
            self.add_page()

        self.ln(0.12)

        if is_step:
            y_pos = self.get_y()
            step_match = re.match(r'STEP\s+(\d+)', clean_title, re.IGNORECASE)
            if step_match:
                step_num = step_match.group(1)
                self.set_fill_color(*d["gold_border"])
                self.ellipse(self.l_margin, y_pos, 0.25, 0.25, 'F')
                self.use_font('B', 9)
                self.set_text_color(255, 255, 255)
                self.set_xy(self.l_margin + 0.07, y_pos + 0.04)
                self.cell(0.11, 0.17, step_num, align='C')

                self.set_xy(self.l_margin + 0.32, y_pos + 0.02)
                self.use_font('B', 10)
                self.set_text_color(*d["navy"])
                rest_title = re.sub(r'STEP\s+\d+:?\s*', '', clean_title, flags=re.IGNORECASE)
                self.cell(0, 0.2, rest_title)
                self.set_y(y_pos + 0.28)
        else:
            self.use_font('B', 10)
            self.set_text_color(*d["navy_light"])
            width = self.w - self.l_margin - self.r_margin
            self.multi_cell(width, 0.2, clean_title)

        self.ln(0.06)

    # ========================================================================
    # CONTENT RENDERING
    # ========================================================================

    def body_text(self, text):
        """Generate body paragraph with pull quote detection."""
        d = DESIGN_COLORS
        width = self.w - self.l_margin - self.r_margin
        text = strip_markdown(text)

        if not text:
            return

        # Check for pull quote
        is_pull_quote = False
        for quote in PULL_QUOTES:
            if quote.lower() in text.lower():
                is_pull_quote = True
                break

        if is_pull_quote and len(text) < 120:
            self.pull_quote(text)
        else:
            self.use_font('', 10)
            self.set_text_color(0, 0, 0)
            self.multi_cell(width, 0.18, text)
            self.ln(0.06)

    def blockquote(self, text):
        """Generate styled blockquote."""
        d = DESIGN_COLORS
        clean_text = strip_markdown(text)

        self.ln(0.08)
        y_start = self.get_y()
        width = self.w - self.l_margin - self.r_margin - 0.4
        x_start = self.l_margin + 0.2

        # Estimate height
        num_lines = max(1, len(clean_text) // 55 + 1)
        box_height = max(0.5, (num_lines * 0.18) + 0.2)

        if self.get_y() + box_height > 7.5:
            self.add_page()
            y_start = self.get_y()

        # Gray background
        self.set_fill_color(*d["gray_light"])
        self.rect(x_start, y_start, width, box_height, 'F')

        # Navy left border
        self.set_fill_color(*d["navy_light"])
        self.rect(x_start, y_start, 0.04, box_height, 'F')

        # Text
        self.set_xy(x_start + 0.15, y_start + 0.1)
        self.use_font('I', 10)
        self.set_text_color(*d["charcoal"])
        self.multi_cell(width - 0.25, 0.18, sanitize_text(clean_text))

        self.set_x(self.l_margin)
        self.set_y(y_start + box_height + 0.1)

    def bullet_item(self, text, indent=0):
        """Generate bullet point."""
        self.use_font('', 10)
        self.set_text_color(0, 0, 0)
        start_x = self.l_margin + 0.2 + (indent * 0.15)
        processed_text = strip_markdown(text)

        # Handle checkboxes
        if '\x01UNCHECKED\x01' in processed_text or '\x01CHECKED\x01' in processed_text:
            is_checked = '\x01CHECKED\x01' in processed_text
            clean_text = processed_text.replace('\x01CHECKED\x01', '').replace('\x01UNCHECKED\x01', '').strip()

            self.set_x(start_x)
            self._draw_checkbox(self.get_x(), self.get_y() + 0.04, checked=is_checked)
            self.set_x(self.get_x() + 0.18)
            if clean_text:
                width = self.w - self.r_margin - self.get_x()
                self.multi_cell(width, 0.18, clean_text)
            else:
                self.ln(0.18)
        else:
            self.set_x(start_x)
            self.cell(0.15, 0.18, '-')
            width = self.w - self.r_margin - start_x - 0.15
            self.multi_cell(width, 0.18, processed_text)

        self.set_x(self.l_margin)

    def numbered_item(self, num, text):
        """Generate numbered list item."""
        self.use_font('', 10)
        self.set_text_color(0, 0, 0)
        start_x = self.l_margin + 0.2
        self.set_x(start_x)
        self.cell(0.2, 0.18, f'{num}.')
        width = self.w - self.r_margin - start_x - 0.2
        self.multi_cell(width, 0.18, strip_markdown(text))
        self.set_x(self.l_margin)

    def _draw_checkbox(self, x, y, checked=False, size=0.1):
        """Draw a checkbox square."""
        self.set_draw_color(80, 80, 80)
        self.set_line_width(0.01)
        self.rect(x, y, size, size, 'D')
        if checked:
            self.line(x + 0.02, y + 0.02, x + size - 0.02, y + size - 0.02)
            self.line(x + size - 0.02, y + 0.02, x + 0.02, y + size - 0.02)

    def render_table(self, rows):
        """Render a table with grid lines."""
        if not rows or len(rows) < 2:
            return

        d = DESIGN_COLORS
        num_cols = len(rows[0])
        available_width = self.w - self.l_margin - self.r_margin - 0.2
        col_width = available_width / num_cols

        # Check page space
        table_height = len(rows) * 0.3 + 0.1
        if self.get_y() + table_height > 7.75:
            self.add_page()

        self.ln(0.1)
        start_x = self.l_margin + 0.1
        line_height = 0.16
        cell_padding = 0.05

        self.set_draw_color(100, 100, 100)
        self.set_line_width(0.01)

        for row_idx, row in enumerate(rows):
            # Skip separator rows
            if row and all(c.strip().replace('-', '') == '' for c in row):
                continue

            y = self.get_y()
            if y > 7.5:
                self.add_page()
                self.ln(0.1)
                y = self.get_y()

            # Header styling
            if row_idx == 0:
                self.use_font('B', 9)
                self.set_fill_color(*d["navy"])
                self.set_text_color(255, 255, 255)
                fill = True
            else:
                self.use_font('', 9)
                self.set_text_color(0, 0, 0)
                fill = row_idx % 2 == 0
                if fill:
                    self.set_fill_color(*d["gray_light"])

            actual_row_height = line_height + (cell_padding * 2)

            for col_idx, cell in enumerate(row):
                x = start_x + col_idx * col_width
                self.rect(x, y, col_width, actual_row_height, 'FD' if fill else 'D')

            for col_idx, cell in enumerate(row):
                x = start_x + col_idx * col_width
                self.set_xy(x + cell_padding, y + cell_padding)
                cell_text = strip_markdown(cell.strip())
                usable_width = col_width - (cell_padding * 2)
                self.cell(usable_width, line_height, cell_text[:30], align='L')

            self.set_y(y + actual_row_height)

        self.ln(0.1)
        self.set_x(self.l_margin)

    # ========================================================================
    # INFOGRAPHIC METHODS (EXAMPLES - CUSTOMIZE FOR YOUR BOOK)
    # ========================================================================

    def framework_infographic(self, title, items):
        """
        Draw a vertical framework infographic.
        items: list of (letter, title, description, color) tuples
        """
        d = DESIGN_COLORS

        if self.get_y() > 2.5:
            self.add_page()

        self.ln(0.15)
        self.use_font('B', 12)
        self.set_text_color(*d["navy"])
        self.cell(0, 0.25, title, align='C', new_x='LMARGIN', new_y='NEXT')
        self.ln(0.15)

        width = self.w - self.l_margin - self.r_margin
        x_start = self.l_margin
        y_start = self.get_y()
        box_height = 0.55
        spacing = 0.06

        for idx, (letter, item_title, desc, color) in enumerate(items):
            y = y_start + idx * (box_height + spacing)

            # Background
            self.set_fill_color(*d["gray_light"])
            self.rect(x_start + 0.45, y, width - 0.45, box_height, 'F')

            # Colored accent
            self.set_fill_color(*color)
            self.rect(x_start + 0.45, y, 0.05, box_height, 'F')

            # Letter circle
            self.set_fill_color(*color)
            self.ellipse(x_start, y + 0.08, 0.4, 0.38, 'F')
            self.use_font('B', 16)
            self.set_text_color(255, 255, 255)
            self.set_xy(x_start + 0.12, y + 0.16)
            self.cell(0.16, 0.2, letter, align='C')

            # Title
            self.set_xy(x_start + 0.58, y + 0.08)
            self.use_font('B', 9)
            self.set_text_color(*d["navy"])
            self.cell(width - 0.65, 0.16, item_title)

            # Description
            self.set_xy(x_start + 0.58, y + 0.28)
            self.use_font('', 8)
            self.set_text_color(*d["charcoal"])
            self.cell(width - 0.65, 0.14, desc)

        self.set_y(y_start + len(items) * (box_height + spacing) + 0.1)

    def decision_flowchart(self, title, steps):
        """
        Draw a decision flowchart.
        steps: list of (number, title, description) tuples
        """
        d = DESIGN_COLORS

        self.ln(0.15)
        self.use_font('B', 12)
        self.set_text_color(*d["navy"])
        self.cell(0, 0.25, title, align='C', new_x='LMARGIN', new_y='NEXT')
        self.ln(0.2)

        width = self.w - self.l_margin - self.r_margin
        x_start = self.l_margin
        y_start = self.get_y()
        x_center = self.w / 2
        step_height = 0.35

        for idx, (num, step_title, desc) in enumerate(steps):
            y = y_start + idx * (step_height + 0.15)

            # Step box
            self.set_fill_color(*d["gray_light"])
            self.rect(x_start + 0.4, y, width - 0.4, step_height, 'F')

            # Gold left edge
            self.set_fill_color(*d["gold_border"])
            self.rect(x_start + 0.4, y, 0.04, step_height, 'F')

            # Number circle
            self.set_fill_color(*d["navy"])
            self.ellipse(x_start, y + 0.05, 0.28, 0.25, 'F')
            self.use_font('B', 11)
            self.set_text_color(255, 255, 255)
            self.set_xy(x_start + 0.08, y + 0.08)
            self.cell(0.12, 0.18, str(num), align='C')

            # Title and description
            self.set_xy(x_start + 0.55, y + 0.05)
            self.use_font('B', 9)
            self.set_text_color(*d["navy"])
            self.cell(0.6, 0.12, step_title)

            self.set_x(x_start + 1.2)
            self.use_font('', 8)
            self.set_text_color(*d["charcoal"])
            self.cell(width - 1.7, 0.12, desc)

            # Arrow to next
            if idx < len(steps) - 1:
                arrow_y = y + step_height + 0.04
                self.set_draw_color(*d["gold_border"])
                self.set_line_width(0.015)
                self.line(x_center, arrow_y, x_center, arrow_y + 0.08)

        self.set_y(y_start + len(steps) * (step_height + 0.15) + 0.2)


# ============================================================================
# CONTENT PARSING
# ============================================================================

def generate_content(pdf, content, toc_items):
    """Parse markdown and generate PDF content."""
    lines = content.split('\n')

    # Skip front matter
    start_idx = 0
    for idx, line in enumerate(lines):
        s = line.strip()
        if s.startswith('# INTRODUCTION') or s.upper().startswith('# PART '):
            start_idx = idx
            break

    lines = lines[start_idx:]
    i = 0
    current_chapter = 0
    blockquote_text = []

    while i < len(lines):
        line = lines[i].strip()

        # Skip dividers and LaTeX
        if line in ['---', '***', '___'] or line.startswith('\\'):
            i += 1
            continue

        # Blockquotes
        if line.startswith('>'):
            quote_line = line[1:].strip()
            if quote_line.startswith('>'):
                quote_line = quote_line[1:].strip()
            blockquote_text.append(quote_line)
            i += 1
            continue
        elif blockquote_text:
            pdf.blockquote(' '.join(blockquote_text))
            blockquote_text = []

        # Part headers
        if line.upper().startswith('# PART '):
            match = re.match(r'# PART ([IVX]+): (.+)', line, re.IGNORECASE)
            if match:
                part_num = match.group(1).upper()
                part_title = match.group(2)
                subtitle = ""
                if i + 2 < len(lines) and lines[i+2].strip().startswith('*'):
                    subtitle = lines[i+2].strip().strip('*')
                    i += 2
                pdf.part_page(part_num, part_title, subtitle)
            i += 1
            continue

        # Chapter headers
        if line.startswith('# ') and not line.upper().startswith('# PART'):
            title = line[2:].strip()
            ch_match = re.match(r'CHAPTER (\d+)', title, re.IGNORECASE)
            if ch_match:
                current_chapter = int(ch_match.group(1))
                if i + 1 < len(lines) and lines[i+1].strip().startswith('##'):
                    title = lines[i+1].strip()[2:].strip()
                    i += 1
                pdf.chapter_heading(current_chapter, title)
            elif 'INTRODUCTION' in title.upper():
                pdf.chapter_heading(None, "Introduction", toc_key="intro")
            elif 'CONCLUSION' in title.upper():
                pdf.chapter_heading(None, "Conclusion", toc_key="conclusion")
            elif 'APPENDIX' in title.upper() or 'APPENDICES' in title.upper():
                pdf.chapter_heading(None, "Appendices", toc_key="appendices")
            else:
                pdf.chapter_heading(None, title)
            i += 1
            continue

        # Section headers
        if line.startswith('## '):
            pdf.section_heading(line[3:])
            i += 1
            continue

        # Subsection headers
        if line.startswith('### '):
            pdf.subsection_heading(line[4:])
            i += 1
            continue

        # Numbered lists
        num_match = re.match(r'^(\d+)\.\s+(.+)', line)
        if num_match:
            pdf.numbered_item(int(num_match.group(1)), num_match.group(2))
            i += 1
            continue

        # Bullet items
        if line.startswith('- ') or line.startswith('* '):
            pdf.bullet_item(line[2:])
            i += 1
            continue

        # Tables
        if line.startswith('|') and '|' in line[1:]:
            table_rows = []
            while i < len(lines) and lines[i].strip().startswith('|'):
                row_line = lines[i].strip()
                cells = [c.strip() for c in row_line.split('|')]
                if cells and cells[0] == '':
                    cells = cells[1:]
                if cells and cells[-1] == '':
                    cells = cells[:-1]
                if cells:
                    table_rows.append(cells)
                i += 1
            if table_rows:
                pdf.render_table(table_rows)
            continue

        # Regular paragraphs
        if line and not line.startswith('#'):
            pdf.body_text(line)

        i += 1

    if blockquote_text:
        pdf.blockquote(' '.join(blockquote_text))


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def get_next_version():
    """Get next version number from existing PDFs."""
    existing = list(PUB_DIR.glob("*_v*_*.pdf"))
    versions = []
    for pdf in existing:
        match = re.search(r'_v(\d+)_', pdf.name)
        if match:
            versions.append(int(match.group(1)))
    return max(versions) + 1 if versions else 1


def main():
    """Generate PDF using two-pass approach."""

    # TOC items: (display_text, key, is_part_header)
    # CUSTOMIZE THIS FOR YOUR BOOK STRUCTURE
    toc_items = [
        ("Introduction", "intro", False),
        ("PART I: FOUNDATIONS", "part_I", True),
        ("1. Chapter One Title", "ch_1", False),
        ("2. Chapter Two Title", "ch_2", False),
        ("3. Chapter Three Title", "ch_3", False),
        ("PART II: PRACTICES", "part_II", True),
        ("4. Chapter Four Title", "ch_4", False),
        ("5. Chapter Five Title", "ch_5", False),
        ("Conclusion", "conclusion", False),
        ("Appendices", "appendices", False),
    ]

    manuscript = PUB_DIR / "manuscript_compiled.md"
    if not manuscript.exists():
        print("ERROR: Run compile_book.py first!")
        return

    with open(manuscript, 'r', encoding='utf-8') as f:
        content = f.read()

    # Remove YAML front matter
    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            content = parts[2]

    print("Pass 1: Collecting page numbers...")
    pdf1 = BookPDF()
    pdf1.collecting_pages = True
    pdf1.front_cover()
    pdf1.title_page()
    pdf1.copyright_page()
    pdf1.dedication_page()
    pdf1.table_of_contents(toc_items)
    generate_content(pdf1, content, toc_items)
    collected = pdf1.page_numbers.copy()
    print(f"  Collected {len(collected)} page numbers")

    print("Pass 2: Generating final PDF...")
    pdf = BookPDF()
    pdf.page_numbers = collected
    pdf.front_cover()
    pdf.title_page()
    pdf.copyright_page()
    pdf.dedication_page()
    pdf.table_of_contents(toc_items)
    generate_content(pdf, content, toc_items)

    version = get_next_version()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    safe_title = BOOK_CONFIG["title"].replace(' ', '_')
    filename = f"{safe_title}_v{version}_{timestamp}.pdf"
    output_path = PUB_DIR / filename

    pdf.output(output_path)
    print(f"\nPDF generated: {output_path}")
    print(f"  Pages: {pdf.page_no()}")


if __name__ == "__main__":
    main()
