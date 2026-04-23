#!/usr/bin/env python3
"""
EPUB Generation Template
Converts compiled markdown manuscript to Kindle-optimized EPUB format.

CUSTOMIZATION REQUIRED:
1. Update BOOK_METADATA with your book details
2. Update CSS_FILE path if using external stylesheet
3. Adjust parsing patterns for your manuscript structure

Dependencies: pip3 install ebooklib
"""

import re
from pathlib import Path
from datetime import datetime
from ebooklib import epub

# ============================================================================
# CONFIGURATION - CUSTOMIZE THESE
# ============================================================================

# Base directory of your book project
BASE_DIR = Path("/path/to/your/BookProject")
PUB_DIR = BASE_DIR / "publishing"
MANUSCRIPT = PUB_DIR / "manuscript_compiled.md"

# Optional: External CSS file (set to None to use embedded styles)
CSS_FILE = PUB_DIR / "epub_styles.css"

# Book metadata
BOOK_METADATA = {
    "title": "Your Book Title",
    "subtitle": "Your Compelling Subtitle",
    "author": "Author Name",
    "year": "2025",
    "language": "en",
    "identifier": "your-book-unique-id-2025",
    "publisher": "Publisher Name",
    "rights": "All rights reserved.",
    "description": "A compelling description of your book for metadata.",
    "version": "1.0",  # Increment for each major revision
}


def get_build_version():
    """Generate a version string with build timestamp."""
    build_time = datetime.now().strftime('%Y%m%d.%H%M')
    return f"v{BOOK_METADATA['version']}.{build_time}"

# Cover image (optional - set to None if no cover)
COVER_IMAGE = PUB_DIR / "kindle_cover.jpg"

# ============================================================================
# DEFAULT EMBEDDED CSS - Used if CSS_FILE not found
# ============================================================================

EMBEDDED_CSS = """
/* Book EPUB Stylesheet - Kindle Optimized */

/* ==========================================================================
   COLOR PALETTE (matching PDF navy/gold theme)
   ========================================================================== */
:root {
    --primary-navy: #1e3a5f;
    --accent-gold: #c9a227;
    --light-gold: #f5e6b8;
    --text-dark: #2c2c2c;
    --text-light: #666666;
    --border-light: #d0d0d0;
    --bg-light: #f8f8f8;
    --bg-subtle: #fafafa;
}

/* ==========================================================================
   BASE STYLES
   ========================================================================== */

body {
    font-family: Georgia, "Times New Roman", serif;
    line-height: 1.5;
    margin: 0;
    padding: 0;
    text-align: justify;
    -webkit-hyphens: auto;
    hyphens: auto;
    color: #2c2c2c;
}

/* ==========================================================================
   TITLE PAGE
   ========================================================================== */

.title-page {
    text-align: center;
    margin-top: 20%;
    page-break-after: always;
}

.title-page .book-title {
    font-size: 2.2em;
    font-weight: bold;
    margin-bottom: 0.3em;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    line-height: 1.2;
}

.title-page .book-subtitle {
    font-size: 1.1em;
    font-style: italic;
    margin-bottom: 0.5em;
    color: #c9a227;
}

.title-page .tagline {
    font-size: 1em;
    font-style: italic;
    margin: 1.5em 0;
}

.title-page .author-name {
    font-size: 1.2em;
    margin-top: 2em;
    font-weight: bold;
}

hr.decorative {
    background-color: #c9a227;
    height: 2px;
    width: 40%;
    border: none;
    margin: 1.5em auto;
}

/* ==========================================================================
   COPYRIGHT PAGE
   ========================================================================== */

.copyright-page {
    font-size: 0.85em;
    margin-top: 30%;
    page-break-after: always;
}

.copyright-page p {
    text-align: left;
    margin: 0.5em 0;
    text-indent: 0;
}

/* ==========================================================================
   PART PAGES
   ========================================================================== */

.part-page {
    text-align: center;
    margin-top: 35%;
    page-break-before: always;
    page-break-after: always;
}

.part-page .part-number {
    font-size: 1.4em;
    font-weight: bold;
    text-transform: uppercase;
    letter-spacing: 0.15em;
    margin-bottom: 0.5em;
    color: #1e3a5f;
}

.part-page .part-title {
    font-size: 1.3em;
    font-weight: bold;
    margin-top: 0.5em;
    color: #1e3a5f;
}

.part-page .part-subtitle {
    font-size: 1.1em;
    font-style: italic;
    margin-top: 0.5em;
    color: #666666;
}

/* ==========================================================================
   CHAPTER HEADERS
   ========================================================================== */

.chapter-header {
    text-align: center;
    margin-top: 15%;
    margin-bottom: 2em;
    page-break-before: always;
}

.chapter-number {
    font-size: 0.9em;
    font-weight: normal;
    text-transform: uppercase;
    letter-spacing: 0.2em;
    margin-bottom: 0.5em;
    display: block;
    color: #666666;
}

.chapter-title {
    font-size: 1.6em;
    font-weight: bold;
    line-height: 1.3;
    margin: 0;
    color: #1e3a5f;
}

/* ==========================================================================
   HEADINGS
   ========================================================================== */

h1 {
    font-size: 1.8em;
    font-weight: bold;
    text-align: center;
    margin: 1.5em 0 1em 0;
    line-height: 1.3;
    page-break-after: avoid;
}

h2 {
    font-size: 1.3em;
    font-weight: bold;
    margin: 1.5em 0 0.8em 0;
    line-height: 1.3;
    page-break-after: avoid;
    color: #1e3a5f;
    border-bottom: 1px solid #d0d0d0;
    padding-bottom: 0.3em;
}

h3 {
    font-size: 1.1em;
    font-weight: bold;
    margin: 1.2em 0 0.6em 0;
    line-height: 1.3;
    page-break-after: avoid;
    color: #2c2c2c;
}

h4 {
    font-size: 1em;
    font-weight: bold;
    margin: 1em 0 0.5em 0;
    page-break-after: avoid;
}

/* ==========================================================================
   PARAGRAPHS
   ========================================================================== */

p {
    margin: 0;
    text-indent: 1.5em;
    widows: 2;
    orphans: 2;
}

h1 + p, h2 + p, h3 + p, h4 + p,
.chapter-header + p,
blockquote + p,
table + p,
.no-indent {
    text-indent: 0;
}

/* ==========================================================================
   BLOCKQUOTES
   ========================================================================== */

blockquote {
    margin: 1.2em 1.5em;
    padding: 0.8em 1em;
    font-style: italic;
    text-indent: 0;
    background-color: #fafafa;
    border-left: 3px solid #c9a227;
}

blockquote p {
    text-indent: 0;
    margin: 0.5em 0;
}

/* ==========================================================================
   TABLES
   ========================================================================== */

table {
    width: 100%;
    border-collapse: collapse;
    margin: 1.5em 0;
    font-size: 0.95em;
    page-break-inside: avoid;
}

thead {
    background-color: #1e3a5f;
    color: white;
}

th {
    padding: 0.7em 0.8em;
    text-align: left;
    font-weight: bold;
    border: 1px solid #1e3a5f;
}

td {
    padding: 0.6em 0.8em;
    border: 1px solid #d0d0d0;
    vertical-align: top;
}

tbody tr:nth-child(even) {
    background-color: #f8f8f8;
}

/* ==========================================================================
   DECISION TREES / FLOWCHARTS
   ========================================================================== */

.decision-tree,
.flowchart {
    margin: 1.5em 0;
    padding: 1em;
    background-color: #f8f8f8;
    border: 1px solid #d0d0d0;
    border-radius: 4px;
    font-family: "Helvetica Neue", Arial, sans-serif;
    font-size: 0.95em;
    page-break-inside: avoid;
}

.decision-tree .question,
.flowchart .question {
    font-weight: bold;
    color: #1e3a5f;
    margin-bottom: 0.5em;
    padding: 0.5em;
    background-color: white;
    border-left: 3px solid #c9a227;
}

.decision-tree .branch,
.flowchart .branch {
    margin-left: 1.5em;
    padding: 0.3em 0;
}

.decision-tree .branch-yes,
.flowchart .branch-yes {
    color: #2d5a3d;
}

.decision-tree .branch-no,
.flowchart .branch-no {
    color: #8b6914;
}

.decision-tree .outcome,
.flowchart .outcome {
    font-style: italic;
    background-color: #f5e6b8;
    padding: 0.3em 0.6em;
    border-radius: 3px;
    display: inline-block;
    margin-left: 0.5em;
}

/* ==========================================================================
   CHECKLISTS
   ========================================================================== */

ul.checklist {
    list-style: none;
    padding-left: 0;
    margin: 0.5em 0;
}

ul.checklist li {
    padding: 0.4em 0 0.4em 2em;
    position: relative;
    margin: 0;
}

ul.checklist li::before {
    content: "\\2610";
    position: absolute;
    left: 0;
    color: #1e3a5f;
    font-size: 1.1em;
}

ul.checklist li.checked::before {
    content: "\\2611";
}

/* ==========================================================================
   KEY PRINCIPLES / CALLOUTS
   ========================================================================== */

.key-principle {
    margin: 1.5em 0;
    padding: 1em 1.2em;
    background-color: #f5e6b8;
    border-left: 4px solid #c9a227;
    font-weight: bold;
    text-indent: 0;
}

.remember-box {
    margin: 1.5em 0;
    padding: 1em;
    background-color: #f8f8f8;
    border: 1px solid #1e3a5f;
    text-align: center;
}

.remember-box strong {
    color: #1e3a5f;
}

.practical-tool {
    margin: 2em 0;
    padding: 1.5em;
    background-color: #fafafa;
    border: 2px solid #c9a227;
    border-radius: 4px;
    page-break-inside: avoid;
}

.practical-tool h3 {
    margin-top: 0;
    color: #1e3a5f;
    border-bottom: 1px solid #c9a227;
    padding-bottom: 0.5em;
}

/* ==========================================================================
   LISTS
   ========================================================================== */

ul, ol {
    margin: 1em 0;
    padding-left: 2em;
}

li {
    margin: 0.4em 0;
    text-indent: 0;
}

li p {
    text-indent: 0;
    margin: 0;
}

/* ==========================================================================
   SECTION DIVIDERS
   ========================================================================== */

hr {
    border: none;
    height: 1px;
    background-color: #d0d0d0;
    margin: 2em auto;
    width: 30%;
}

hr.chapter-end {
    margin: 3em auto 2em;
    width: 40%;
    height: 3px;
    background: #c9a227;
}

/* ==========================================================================
   TABLE OF CONTENTS
   ========================================================================== */

nav h1, nav h2 {
    text-align: center;
    font-size: 1.5em;
    margin-bottom: 1.5em;
    border-bottom: none;
}

nav ol {
    list-style: none;
    padding: 0;
    margin: 0;
}

nav li {
    margin: 0.6em 0;
}

nav li a {
    text-decoration: none;
    color: inherit;
}

nav li.toc-part {
    font-weight: bold;
    margin-top: 1.2em;
    text-transform: uppercase;
    font-size: 0.95em;
    letter-spacing: 0.05em;
    color: #1e3a5f;
}

nav li.toc-chapter {
    padding-left: 1em;
}

/* ==========================================================================
   KINDLE OPTIMIZATIONS
   ========================================================================== */

img {
    max-width: 100%;
    height: auto;
}

.page-break-before {
    page-break-before: always;
}

.page-break-after {
    page-break-after: always;
}

.no-page-break {
    page-break-inside: avoid;
}
"""

# ============================================================================
# HTML TEMPLATES
# ============================================================================

HTML_TEMPLATE = """<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
<head>
    <title>{title}</title>
    <link rel="stylesheet" href="style/main.css" type="text/css" />
</head>
<body>
{content}
</body>
</html>
"""

TITLE_PAGE_TEMPLATE = """
<div class="title-page">
    <hr class="decorative" />
    <p class="book-title">{title}</p>
    <p class="book-subtitle">{subtitle}</p>
    <hr class="decorative" />
    <p class="author-name">{author}</p>
    <p style="margin-top: 3em; font-size: 0.9em;">
        Copyright &copy; {year} {author}
    </p>
</div>
"""

COPYRIGHT_TEMPLATE = """
<div class="copyright-page">
    <p><strong>{title}: {subtitle}</strong></p>
    <p>Copyright &copy; {year} by {author}</p>
    <p>&nbsp;</p>
    <p>All rights reserved. No part of this publication may be reproduced,
    distributed, or transmitted in any form or by any means, including
    photocopying, recording, or other electronic or mechanical methods,
    without the prior written permission of the publisher, except in the
    case of brief quotations embodied in critical reviews.</p>
    <p>&nbsp;</p>
    <p><strong>Disclaimer:</strong> This book is intended for informational
    and educational purposes only. The author is not providing professional
    advice specific to your situation.</p>
    <p>&nbsp;</p>
    <p>First Edition: {year}</p>
    <p>&nbsp;</p>
    <p>Printed in the United States of America</p>
</div>
"""

PART_PAGE_TEMPLATE = """
<div class="part-page">
    <p class="part-number">Part {number}</p>
    <p class="part-title">{title}</p>
    {subtitle_html}
</div>
"""

CHAPTER_HEADER_TEMPLATE = """
<div class="chapter-header">
    <span class="chapter-number">Chapter {number}</span>
    <h1 class="chapter-title">{title}</h1>
</div>
"""

# ============================================================================
# MARKDOWN TO HTML CONVERSION
# ============================================================================

def sanitize_text(text):
    """Remove or replace problematic characters."""
    # Replace smart quotes
    text = text.replace('\u2018', "'").replace('\u2019', "'")
    text = text.replace('\u201c', '"').replace('\u201d', '"')
    # Replace em/en dashes
    text = text.replace('\u2014', '&mdash;').replace('\u2013', '&ndash;')
    # Replace ellipsis
    text = text.replace('\u2026', '...')
    return text


def markdown_to_html(text):
    """Convert markdown to semantic HTML."""
    html = sanitize_text(text)

    # Remove LaTeX commands
    html = html.replace('\\newpage', '')
    html = re.sub(r'\\[a-zA-Z]+(\{[^}]*\})?', '', html)

    # Em dashes (plain text)
    html = html.replace('--', '&mdash;')

    # Bold: **text** -> <strong>text</strong>
    html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)

    # Italic: *text* -> <em>text</em>
    html = re.sub(r'\*([^*]+?)\*', r'<em>\1</em>', html)

    # Process blockquotes
    html = process_blockquotes(html)

    # Process tables
    html = process_tables(html)

    # Process checklists
    html = process_checklists(html)

    # Process bullet lists
    html = process_bullet_lists(html)

    # Process numbered lists
    html = process_numbered_lists(html)

    # Process key principle callouts
    html = process_key_principles(html)

    # Wrap paragraphs
    html = wrap_paragraphs(html)

    return html


def process_blockquotes(html):
    """Convert > prefixed lines to blockquotes with tip/note detection."""
    lines = html.split('\n')
    result = []
    in_blockquote = False
    blockquote_lines = []

    for line in lines:
        stripped = line.strip()
        if stripped.startswith('>'):
            # Extract quote text (handle nested >)
            quote_text = stripped[1:].strip()
            while quote_text.startswith('>'):
                quote_text = quote_text[1:].strip()
            blockquote_lines.append(quote_text)
            in_blockquote = True
        else:
            if in_blockquote and blockquote_lines:
                # Close blockquote - check for special box types
                quote_content = ' '.join(blockquote_lines)
                lower_content = quote_content.lower()

                if lower_content.startswith('tip:') or lower_content.startswith('note:'):
                    # Tip or Note box
                    box_type = 'Tip' if lower_content.startswith('tip:') else 'Note'
                    content_text = re.sub(r'^(tip|note):\s*', '', quote_content, flags=re.IGNORECASE)
                    result.append(f'<div class="tip"><strong>{box_type}:</strong> {content_text}</div>')
                elif lower_content.startswith('key insight:') or lower_content.startswith('important:'):
                    # Key insight box
                    content_text = re.sub(r'^(key insight|important):\s*', '', quote_content, flags=re.IGNORECASE)
                    result.append(f'<div class="key-principle">{content_text}</div>')
                else:
                    # Regular blockquote
                    quote_html = '<br/>'.join(blockquote_lines)
                    result.append(f'<blockquote><p>{quote_html}</p></blockquote>')

                blockquote_lines = []
                in_blockquote = False
            result.append(line)

    # Handle unclosed blockquote at end
    if blockquote_lines:
        quote_content = ' '.join(blockquote_lines)
        lower_content = quote_content.lower()

        if lower_content.startswith('tip:') or lower_content.startswith('note:'):
            box_type = 'Tip' if lower_content.startswith('tip:') else 'Note'
            content_text = re.sub(r'^(tip|note):\s*', '', quote_content, flags=re.IGNORECASE)
            result.append(f'<div class="tip"><strong>{box_type}:</strong> {content_text}</div>')
        elif lower_content.startswith('key insight:') or lower_content.startswith('important:'):
            content_text = re.sub(r'^(key insight|important):\s*', '', quote_content, flags=re.IGNORECASE)
            result.append(f'<div class="key-principle">{content_text}</div>')
        else:
            quote_html = '<br/>'.join(blockquote_lines)
            result.append(f'<blockquote><p>{quote_html}</p></blockquote>')

    return '\n'.join(result)


def process_tables(html):
    """Convert markdown tables to HTML tables."""
    lines = html.split('\n')
    result = []
    in_table = False
    table_lines = []

    for line in lines:
        stripped = line.strip()
        if '|' in stripped and stripped.startswith('|'):
            table_lines.append(stripped)
            in_table = True
        else:
            if in_table and table_lines:
                # Process accumulated table
                result.append(render_table(table_lines))
                table_lines = []
                in_table = False
            result.append(line)

    # Handle unclosed table
    if table_lines:
        result.append(render_table(table_lines))

    return '\n'.join(result)


def render_table(table_lines):
    """Render markdown table lines as HTML table."""
    if len(table_lines) < 2:
        return '\n'.join(table_lines)

    html_parts = ['<table>']

    for i, line in enumerate(table_lines):
        # Skip separator line (|---|---|)
        if re.match(r'^\|[\s\-:]+\|$', line.replace('|', '|').strip()):
            continue

        cells = [c.strip() for c in line.strip('|').split('|')]

        if i == 0:
            # Header row
            html_parts.append('<thead><tr>')
            for cell in cells:
                html_parts.append(f'<th>{cell}</th>')
            html_parts.append('</tr></thead>')
            html_parts.append('<tbody>')
        else:
            html_parts.append('<tr>')
            for cell in cells:
                html_parts.append(f'<td>{cell}</td>')
            html_parts.append('</tr>')

    html_parts.append('</tbody></table>')
    return '\n'.join(html_parts)


def process_checklists(html):
    """Convert - [ ] and - [x] to checklist items."""
    lines = html.split('\n')
    result = []
    in_checklist = False

    for line in lines:
        stripped = line.strip()

        # Unchecked: - [ ]
        if stripped.startswith('- [ ]'):
            if not in_checklist:
                result.append('<ul class="checklist">')
                in_checklist = True
            item_text = stripped[5:].strip()
            result.append(f'<li>{item_text}</li>')
            continue

        # Checked: - [x] or - [X]
        if stripped.startswith('- [x]') or stripped.startswith('- [X]'):
            if not in_checklist:
                result.append('<ul class="checklist">')
                in_checklist = True
            item_text = stripped[5:].strip()
            result.append(f'<li class="checked">{item_text}</li>')
            continue

        # Close checklist if we hit non-checklist content
        if in_checklist and stripped and not stripped.startswith('-'):
            result.append('</ul>')
            in_checklist = False

        result.append(line)

    # Close unclosed checklist
    if in_checklist:
        result.append('</ul>')

    return '\n'.join(result)


def process_bullet_lists(html):
    """Convert - items to unordered lists."""
    lines = html.split('\n')
    result = []
    in_list = False

    for line in lines:
        stripped = line.strip()

        # Skip if already processed (checklist, HTML)
        if stripped.startswith('<'):
            if in_list:
                result.append('</ul>')
                in_list = False
            result.append(line)
            continue

        # Bullet item (not checklist)
        if stripped.startswith('- ') and not stripped.startswith('- ['):
            if not in_list:
                result.append('<ul>')
                in_list = True
            item_text = stripped[2:].strip()
            result.append(f'<li>{item_text}</li>')
            continue

        # Close list if needed
        if in_list and stripped and not stripped.startswith('-'):
            result.append('</ul>')
            in_list = False

        result.append(line)

    if in_list:
        result.append('</ul>')

    return '\n'.join(result)


def process_numbered_lists(html):
    """Convert numbered items to ordered lists."""
    lines = html.split('\n')
    result = []
    in_list = False

    for line in lines:
        stripped = line.strip()

        # Skip if already processed
        if stripped.startswith('<'):
            if in_list:
                result.append('</ol>')
                in_list = False
            result.append(line)
            continue

        # Numbered item
        match = re.match(r'^(\d+)\.\s+(.+)$', stripped)
        if match:
            if not in_list:
                result.append('<ol>')
                in_list = True
            item_text = match.group(2)
            result.append(f'<li>{item_text}</li>')
            continue

        # Close list if needed
        if in_list and stripped:
            result.append('</ol>')
            in_list = False

        result.append(line)

    if in_list:
        result.append('</ol>')

    return '\n'.join(result)


def process_key_principles(html):
    """Convert **Key Takeaway:** patterns to callout boxes."""
    patterns = [
        (r'\*\*Key Takeaway:\*\*\s*(.+?)(?=\n\n|\Z)',
         r'<div class="key-principle">\1</div>'),
        (r'\*\*Key Principle:\*\*\s*(.+?)(?=\n\n|\Z)',
         r'<div class="key-principle">\1</div>'),
        (r'\*\*Remember:\*\*\s*(.+?)(?=\n\n|\Z)',
         r'<div class="remember-box"><strong>Remember:</strong> \1</div>'),
    ]

    for pattern, replacement in patterns:
        html = re.sub(pattern, replacement, html, flags=re.DOTALL)

    return html


def wrap_paragraphs(html):
    """Wrap plain text lines in paragraph tags."""
    lines = html.split('\n')
    result = []

    for line in lines:
        stripped = line.strip()

        # Skip empty lines
        if not stripped:
            result.append('')
            continue

        # Skip if already HTML, heading marker, or divider
        if (stripped.startswith('<') or
            stripped.startswith('#') or
            stripped in ['---', '***', '___']):
            result.append(line)
            continue

        # Wrap in paragraph
        result.append(f'<p>{stripped}</p>')

    return '\n'.join(result)


# ============================================================================
# CHAPTER PARSING
# ============================================================================

def parse_manuscript(content):
    """Parse markdown manuscript into structured chapters."""
    chapters = []
    current = None
    current_content = []

    lines = content.split('\n')

    for line in lines:
        stripped = line.strip()

        # Part headers: # PART I: TITLE
        part_match = re.match(r'^#\s+PART\s+([IVX]+):\s*(.+)$', stripped, re.IGNORECASE)
        if part_match:
            if current:
                chapters.append({
                    'type': current['type'],
                    'title': current['title'],
                    'content': '\n'.join(current_content)
                })
            current = {
                'type': 'part',
                'number': part_match.group(1),
                'title': part_match.group(2).strip()
            }
            current_content = []
            continue

        # Chapter headers: # CHAPTER 1 or # Chapter 1: Title
        chapter_match = re.match(r'^#\s+CHAPTER\s+(\d+)(?::\s*(.+))?$', stripped, re.IGNORECASE)
        if chapter_match:
            if current:
                chapters.append({
                    'type': current['type'],
                    'title': current['title'],
                    'content': '\n'.join(current_content),
                    'number': current.get('number')
                })
            chapter_num = chapter_match.group(1)
            chapter_title = chapter_match.group(2) or f"Chapter {chapter_num}"
            current = {
                'type': 'chapter',
                'number': chapter_num,
                'title': chapter_title.strip()
            }
            current_content = []
            continue

        # Introduction: # INTRODUCTION
        if re.match(r'^#\s+INTRODUCTION', stripped, re.IGNORECASE):
            if current:
                chapters.append({
                    'type': current['type'],
                    'title': current['title'],
                    'content': '\n'.join(current_content),
                    'number': current.get('number')
                })
            current = {'type': 'special', 'title': 'Introduction'}
            current_content = ['<h1>Introduction</h1>']
            continue

        # Conclusion: # CONCLUSION
        if re.match(r'^#\s+CONCLUSION', stripped, re.IGNORECASE):
            if current:
                chapters.append({
                    'type': current['type'],
                    'title': current['title'],
                    'content': '\n'.join(current_content),
                    'number': current.get('number')
                })
            current = {'type': 'special', 'title': 'Conclusion'}
            current_content = ['<h1>Conclusion</h1>']
            continue

        # Appendices: # APPENDICES
        if re.match(r'^#\s+APPENDICES', stripped, re.IGNORECASE):
            if current:
                chapters.append({
                    'type': current['type'],
                    'title': current['title'],
                    'content': '\n'.join(current_content),
                    'number': current.get('number')
                })
            current = {'type': 'special', 'title': 'Appendices'}
            current_content = ['<h1>Appendices</h1>']
            continue

        # Section headers: ## Title
        if stripped.startswith('## '):
            title = stripped[3:].strip()
            current_content.append(f'<h2>{title}</h2>')
            continue

        # Subsection headers: ### Title
        if stripped.startswith('### '):
            title = stripped[4:].strip()
            current_content.append(f'<h3>{title}</h3>')
            continue

        # Sub-subsection headers: #### Title
        if stripped.startswith('#### '):
            title = stripped[5:].strip()
            current_content.append(f'<h4>{title}</h4>')
            continue

        # Skip front matter markers
        if stripped in ['---', '***', '___', '```']:
            continue

        # Add content
        current_content.append(line)

    # Add final chapter
    if current:
        chapters.append({
            'type': current['type'],
            'title': current['title'],
            'content': '\n'.join(current_content),
            'number': current.get('number')
        })

    return chapters


# ============================================================================
# EPUB GENERATION
# ============================================================================

def create_epub():
    """Generate EPUB file from compiled manuscript."""
    build_version = get_build_version()
    print("=" * 60)
    print(f"Generating EPUB: {BOOK_METADATA['title']}")
    print(f"Build: {build_version}")
    print("=" * 60)

    # Verify manuscript exists
    if not MANUSCRIPT.exists():
        print(f"Error: {MANUSCRIPT} not found.")
        print("Run compile_book.py first to generate the manuscript.")
        return None

    # Read manuscript
    content = MANUSCRIPT.read_text(encoding='utf-8')

    # Create EPUB book
    book = epub.EpubBook()

    # Set metadata
    book.set_identifier(BOOK_METADATA['identifier'])
    book.set_title(f"{BOOK_METADATA['title']}: {BOOK_METADATA['subtitle']}")
    book.set_language(BOOK_METADATA['language'])
    book.add_author(BOOK_METADATA['author'])
    book.add_metadata('DC', 'date', BOOK_METADATA['year'])
    book.add_metadata('DC', 'publisher', BOOK_METADATA.get('publisher', ''))
    book.add_metadata('DC', 'rights',
        f"Copyright {BOOK_METADATA['year']} {BOOK_METADATA['author']}. {BOOK_METADATA.get('rights', '')}")
    book.add_metadata('DC', 'description', BOOK_METADATA.get('description', ''))
    book.add_metadata('DC', 'source', f'Build: {build_version}')

    # Load CSS
    css_content = EMBEDDED_CSS
    if CSS_FILE and CSS_FILE.exists():
        css_content = CSS_FILE.read_text(encoding='utf-8')
        print(f"  Using external CSS: {CSS_FILE.name}")
    else:
        print("  Using embedded CSS")

    css_item = epub.EpubItem(
        uid="main_css",
        file_name="style/main.css",
        media_type="text/css",
        content=css_content
    )
    book.add_item(css_item)

    # Add cover image if exists
    if COVER_IMAGE and COVER_IMAGE.exists():
        with open(COVER_IMAGE, 'rb') as f:
            cover_data = f.read()
        book.set_cover('cover.jpg', cover_data)
        print(f"  Added cover image: {COVER_IMAGE.name}")

    # Parse chapters
    chapters = parse_manuscript(content)
    print(f"  Parsed {len(chapters)} sections")

    # Create title page
    title_html = TITLE_PAGE_TEMPLATE.format(**BOOK_METADATA)
    title_page = epub.EpubHtml(
        title='Title Page',
        file_name='title.xhtml',
        lang=BOOK_METADATA['language']
    )
    title_page.content = HTML_TEMPLATE.format(title='Title Page', content=title_html)
    title_page.add_item(css_item)
    book.add_item(title_page)

    # Create copyright page
    copyright_html = COPYRIGHT_TEMPLATE.format(**BOOK_METADATA)
    copyright_page = epub.EpubHtml(
        title='Copyright',
        file_name='copyright.xhtml',
        lang=BOOK_METADATA['language']
    )
    copyright_page.content = HTML_TEMPLATE.format(title='Copyright', content=copyright_html)
    copyright_page.add_item(css_item)
    book.add_item(copyright_page)

    # Create chapter files
    epub_chapters = [title_page, copyright_page]
    toc_items = []

    for i, chapter_data in enumerate(chapters):
        chapter_type = chapter_data['type']
        chapter_title = chapter_data['title']
        chapter_content = chapter_data['content']
        chapter_number = chapter_data.get('number')

        # Generate safe filename
        safe_title = re.sub(r'[^a-zA-Z0-9]', '_', chapter_title)[:30]
        filename = f'chapter_{i:02d}_{safe_title}.xhtml'

        # Build content based on type
        if chapter_type == 'part':
            subtitle_html = ''
            # Check for subtitle in next lines
            content_html = PART_PAGE_TEMPLATE.format(
                number=chapter_number,
                title=chapter_title,
                subtitle_html=subtitle_html
            )
        elif chapter_type == 'chapter':
            header_html = CHAPTER_HEADER_TEMPLATE.format(
                number=chapter_number,
                title=chapter_title
            )
            body_html = markdown_to_html(chapter_content)
            content_html = header_html + body_html
        else:
            # Special sections (Introduction, Conclusion, etc.)
            body_html = markdown_to_html(chapter_content)
            content_html = body_html

        # Create chapter
        chapter = epub.EpubHtml(
            title=chapter_title,
            file_name=filename,
            lang=BOOK_METADATA['language']
        )
        chapter.content = HTML_TEMPLATE.format(title=chapter_title, content=content_html)
        chapter.add_item(css_item)

        book.add_item(chapter)
        epub_chapters.append(chapter)
        toc_items.append(chapter)

        print(f"  + {chapter_type.capitalize()}: {chapter_title}")

    # Set table of contents
    book.toc = toc_items

    # Add navigation files (NCX for EPUB2, NAV for EPUB3)
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    # Set spine (reading order)
    book.spine = ['nav'] + epub_chapters

    # Generate output filename
    timestamp = datetime.now().strftime("%Y%m%d")
    safe_title = re.sub(r'[^a-zA-Z0-9]', '', BOOK_METADATA['title'])
    output_file = PUB_DIR / f"{safe_title}_KDP_{timestamp}.epub"

    # Write EPUB
    epub.write_epub(str(output_file), book, {})

    print()
    print("=" * 60)
    print(f"EPUB generated: {output_file}")
    print(f"  Chapters: {len(chapters)}")
    print(f"  File size: {output_file.stat().st_size / 1024:.1f} KB")
    print("=" * 60)

    return output_file


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    create_epub()
