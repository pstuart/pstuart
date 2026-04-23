---
name: book-publisher
description: Professional book publishing from Markdown, Word, or text to PDF/EPUB. Use when creating books, converting manuscripts to PDF, generating covers (Kindle and paperback with spine), building indexes with real page numbers, creating table of contents, or formatting chapters. Handles trade paperback (5.5x8.5), two-pass TOC generation, EPUB conversion, and Amazon KDP requirements.
---

# Book Publisher Skill

Transform manuscripts into professional, Amazon-ready books. Supports multiple input formats (Markdown, Word, text) and outputs print-ready PDFs, Kindle EPUBs, and professional covers.

## Capabilities

- **PDF Generation**: Trade paperback with full-color covers, accurate TOC, running headers, professional typography, infographics
- **EPUB Generation**: Kindle-optimized e-books with responsive styling
- **Cover Design**: Kindle covers (1600x2560) and paperback wraps with automatic spine calculation
- **Index Generation**: Automatic term extraction with real page numbers
- **Input Conversion**: Word documents, plain text, and Markdown

## Interactive Style Workflow

**IMPORTANT**: When helping users create a book, ALWAYS gather their style preferences BEFORE generating any files. Each book should have a unique look that matches its content and audience.

### Style Questionnaire

Ask users these questions before starting:

1. **Book Genre/Type**: What type of book is this?
   - Business/Leadership
   - Self-Help/Personal Development
   - Memoir/Biography
   - Spiritual/Religious
   - Fiction (Literary/Thriller/Romance)
   - Academic/Reference

2. **Color Scheme**: What mood should the design convey?
   - **Navy & Gold** - Professional, authoritative (business, leadership)
   - **Burgundy & Cream** - Sophisticated, literary (memoir, literary fiction)
   - **Teal & Coral** - Modern, fresh (self-help, wellness)
   - **Black & Silver** - Dramatic, serious (thriller, mystery)
   - **Earth Warm** - Grounded, spiritual (spirituality, nature)
   - **Purple & Gold** - Luxurious, transformative (personal growth)
   - **Forest & Cream** - Natural, wise (sustainability, wisdom)
   - **Minimal White** - Clean, modern (contemporary, minimalist)
   - **Custom colors** - Specify your own RGB values

3. **Interior Style**: How should the interior pages look?
   - Classic with serif fonts and traditional layout
   - Modern with clean lines and sans-serif accents
   - Decorative with ornamental dividers and flourishes
   - Minimal with lots of white space

4. **Cover Elements**: What should appear on your cover?
   - Title arrangement (one line, two lines, stacked)
   - Subtitle style (italic, all caps, sentence case)
   - Author name placement (top, bottom, with "by" or "Written by")
   - Decorative elements (lines, borders, icons)

5. **Back Cover Content**: What information for the back?
   - Hook/tagline
   - Description paragraphs
   - Feature bullet points
   - Author bio
   - Price and category
   - Website/URL

### Available Style Presets

```python
STYLE_PRESETS = {
    "navy_gold": {
        "name": "Navy & Gold",
        "background": (30, 58, 95),
        "accent": (201, 162, 39),
        "title_color": (255, 255, 255),
        # Best for: Business, Leadership, Non-fiction
    },
    "burgundy_cream": {
        "name": "Burgundy & Cream",
        "background": (88, 24, 32),
        "accent": (245, 235, 220),
        # Best for: Memoir, Literary Fiction, Biography
    },
    "teal_coral": {
        "name": "Teal & Coral",
        "background": (0, 95, 115),
        "accent": (255, 127, 102),
        # Best for: Self-Help, Wellness, Contemporary
    },
    "black_silver": {
        "name": "Black & Silver",
        "background": (25, 25, 25),
        "accent": (192, 192, 192),
        # Best for: Thriller, Mystery, Drama
    },
    "earth_warm": {
        "name": "Earth Warm",
        "background": (89, 60, 31),
        "accent": (218, 165, 32),
        # Best for: Spirituality, Nature, Grounded Topics
    },
    "purple_gold": {
        "name": "Purple & Gold",
        "background": (60, 25, 85),
        "accent": (218, 165, 32),
        # Best for: Transformation, Luxury, Spiritual Growth
    },
    "forest_cream": {
        "name": "Forest & Cream",
        "background": (34, 85, 51),
        "accent": (255, 248, 220),
        # Best for: Sustainability, Nature, Wisdom
    },
    "minimal_white": {
        "name": "Minimal White",
        "background": (250, 250, 250),
        "accent": (30, 30, 30),
        # Best for: Modern, Clean, Contemporary
    },
}
```

### Custom Color Configuration

For custom colors, collect RGB values for:
- **Background**: Main cover/header background color
- **Accent**: Decorative elements, highlighted text
- **Title**: Main title text color
- **Subtitle**: Subtitle and tagline color
- **Body Text**: Interior text color
- **Headings**: Chapter and section heading color

## Quick Start

```bash
# 1. Convert source files to markdown (if needed)
python3 converters/docx_to_markdown.py manuscript.docx

# 2. Compile chapters into single manuscript
python3 compile_book.py

# 3. Generate PDF (two-pass for accurate TOC)
python3 generate_pdf.py

# 4. Generate index and final PDF
python3 generate_index.py

# 5. Generate EPUB for Kindle
python3 generate_epub.py

# 6. Generate covers
python3 create_kindle_cover.py
python3 create_paperback_cover.py

# 7. Add covers to PDF
python3 add_covers_to_pdf.py

# 8. Protect PDF (optional)
python3 protect_pdf.py "YourOwnerPassword"
```

## Project Structure

```
BookProject/
├── manuscript/                    # Source chapter files
│   ├── 00_INTRODUCTION.md
│   ├── 01_CHAPTER_ONE.md
│   ├── 02_CHAPTER_TWO.md
│   └── BACK_MATTER.md
├── publishing/                    # Generated outputs
│   ├── compile_book.py           # Manuscript compiler
│   ├── generate_pdf.py           # PDF generator
│   ├── generate_epub.py          # EPUB generator
│   ├── generate_index.py         # Index generator
│   ├── create_kindle_cover.py    # Kindle cover
│   ├── create_paperback_cover.py # Paperback wrap cover
│   ├── epub_styles.css           # EPUB stylesheet
│   ├── manuscript_compiled.md    # Compiled output
│   ├── BookTitle_v*.pdf          # Generated PDFs
│   └── BookTitle_*.epub          # Generated EPUBs
└── assets/                        # Optional images, fonts
```

## Configuration System

Each script uses configuration dictionaries for easy customization:

### Book Metadata
```python
BOOK_CONFIG = {
    "title": "Your Book Title",
    "subtitle": "Your Compelling Subtitle",
    "author": "Author Name",
    "tagline": "A one-line hook for readers",
    "website": "authorwebsite.com",
    "price": "$24.99 US",
    "category": "Category / Subcategory",
    "year": "2025",
    "dedication": "For those who believed...",
    "hook": "Opening hook for back cover that draws readers in.",
    "author_bio": "Author bio paragraph for back cover...",
}
```

### Cover Color Schemes
```python
COVER_COLORS = {
    "gradient_start": (15, 32, 55),    # Dark navy
    "gradient_end": (25, 55, 95),      # Deep blue
    "accent": (218, 165, 32),          # Gold
    "accent_light": (255, 215, 100),   # Light gold
    "text_light": (240, 240, 240),
    "text_muted": (200, 200, 200),
}
```

### Interior Design Colors
```python
DESIGN_COLORS = {
    "navy": (15, 32, 55),              # Dark navy for headings
    "navy_light": (35, 65, 115),       # Lighter navy for accents
    "gold": (178, 134, 11),            # Gold for highlights
    "gold_light": (255, 248, 220),     # Light gold background
    "gold_border": (218, 165, 32),     # Gold for borders
    "charcoal": (40, 40, 40),          # Dark text
    "gray_light": (245, 245, 245),     # Light gray background
    "gray_medium": (180, 180, 180),    # Medium gray for rules
}
```

## PDF Features

### Two-Pass Generation
Accurate TOC page numbers via two rendering passes:
1. **Pass 1**: Render entire book, collect actual page numbers
2. **Pass 2**: Re-render with correct TOC page references

### Professional Typography
- Trade paperback: 5.5" x 8.5" (configurable)
- Proper margins: 0.625" sides, 0.75" top/bottom
- Running headers: book title (even) / chapter title (odd)
- Centered page numbers in footer
- Unicode font support via system TTF fonts

### Interior Styling Elements
- **Pull Quotes**: Gold-bordered highlight boxes for key statements
- **Key Insight Boxes**: Navy header bar with gray content area
- **Blockquotes**: Gray background with navy left border
- **Tables**: Grid lines with navy headers, alternating row colors
- **Checklists**: Visual checkbox squares (checked/unchecked)
- **Decorative Dividers**: Gold lines with centered diamond accent
- **Chapter Number Badges**: Gold circles with chapter numbers

### Infographics & Flowcharts
Built-in methods for visual elements:
- `life_framework_infographic()` - 2x2 quadrant diagrams
- `daniel_decision_flowchart()` - Step-by-step vertical flows
- `triage_flowchart()` - Decision trees with yes/no branches
- `power_framework_infographic()` - Vertical list with icons
- `no_decision_tree_flowchart()` - Complex branching logic

### Part Dividers
- Full-page part headers with page break
- Decorative gold bars at top and bottom
- Roman numeral part number
- Centered title with optional subtitle

### Section Styling
- **## Sections**: Gold left accent bar, navy title
- **### Subsections**: STEP badges for numbered steps
- **Practical Tools**: Gold-bordered box with special header

### Terminal-Style Code Blocks
Modern terminal appearance for code examples:
```python
STYLE = {
    "code_bg": (30, 30, 30),           # Dark terminal background
    "code_text": (220, 220, 220),      # Light gray text
}
```
- Monospace font (Courier)
- No decorative sidebars
- Tight line spacing (3.0mm)

### Box Height Calculation (Preventing Overflow)
Conservative character estimation prevents text overflow in blockquotes and tip boxes:
```python
# Use conservative chars_per_line for italic/variable-width text
chars_per_line = int(content_width * 1.5)  # Not 2.0+ which causes overflow
num_lines = max(1, (len(text) // chars_per_line) + 2)  # +2 for word wrap safety
box_height = max(14, text_height + 8)  # Extra padding
```

### Orphan/Widow Prevention
Prevent headings at page bottom with no content following:
```python
# Check remaining space before adding heading
def check_page_space(self, min_content_after: float = 25):
    """Check if enough space remains for heading + content."""
    remaining = PAGE_HEIGHT - MARGIN_BOTTOM - self.get_y()
    if remaining < min_content_after:
        self.add_page()
```

Recommended `min_content_after` values (standard layout):
| Heading Level | Threshold | Notes |
|---------------|-----------|-------|
| H1 (Chapters) | 35-50mm | Chapter starts get new page anyway |
| H2 (Sections) | 30-45mm | Major sections need visible content |
| H3 (Subsections) | 40-70mm | Higher values prevent orphans but increase whitespace |
| H4 (Minor) | 35-55mm | Balance based on content density |

**Trade-off**: Higher thresholds = fewer orphans but more wasted space. Use copy fitting to compensate.

### Running Header Filtering
Filter invalid chapter names from running headers:
```python
INVALID_HEADER_PATTERNS = [
    'my skill', 'invite multiple', 'best practices',
    'troubleshooting', 'common issues', 'summary'
]

def _is_valid_chapter_name(title: str) -> bool:
    title_lower = title.lower()
    for pattern in INVALID_HEADER_PATTERNS:
        if pattern in title_lower:
            return False
    return True
```

### Line Spacing Configuration
Optimized spacing for professional layout:
```python
LINE_HEIGHT_BODY = 4.5      # Body text (tighter than default)
LINE_HEIGHT_CODE = 3.0      # Code blocks (compact terminal)
LINE_HEIGHT_LIST = 4.5      # List items
PARA_SPACING = 1.5          # After paragraphs (minimal)
SECTION_SPACING_BEFORE = 4  # Before headings
SECTION_SPACING_AFTER = 1   # After headings
```

### Copy Fitting

Copy fitting adjusts typography to fit more content per page while maintaining readability. Use this when your PDF has too many pages or excessive whitespace.

#### Copy Fitting Configuration
```python
# === STANDARD LAYOUT (comfortable reading) ===
MARGIN_H = 12              # Horizontal margins (mm)
MARGIN_TOP = 12            # Top margin
MARGIN_BOTTOM = 15         # Bottom margin
LINE_HEIGHT_BODY = 4.5     # Body text line height
LINE_HEIGHT_CODE = 3.0     # Code blocks
PARA_SPACING = 1.5         # After paragraphs
SECTION_SPACING_BEFORE = 4 # Before headings
SECTION_SPACING_AFTER = 1  # After headings

# === COPY-FITTED LAYOUT (20-25% more compact) ===
MARGIN_H = 10              # Tighter margins
MARGIN_TOP = 11
MARGIN_BOTTOM = 13
LINE_HEIGHT_BODY = 4.2     # Tighter line height
LINE_HEIGHT_CODE = 2.9     # Compact code blocks
PARA_SPACING = 1.2         # Minimal paragraph spacing
SECTION_SPACING_BEFORE = 3 # Less space before headings
SECTION_SPACING_AFTER = 0.8
```

#### Copy Fitting Font Adjustments
Reduce font sizes slightly for denser layout:
```python
# Standard → Copy-fitted
H2_FONT_SIZE = 13  → 12     # Section headings
H3_FONT_SIZE = 11  → 10     # Subsection headings
H4_FONT_SIZE = 10  → 9.5    # Minor headings
```

#### Balancing Copy Fitting with Orphan Prevention
When tightening layout, also reduce orphan prevention thresholds proportionally:
```python
# Standard orphan prevention (looser layout)
H1_MIN_CONTENT_AFTER = 50   # mm
H2_MIN_CONTENT_AFTER = 45
H3_MIN_CONTENT_AFTER = 70   # High value prevents orphans but wastes space
H4_MIN_CONTENT_AFTER = 55

# Copy-fitted orphan prevention (balanced)
H1_MIN_CONTENT_AFTER = 35   # Enough to prevent orphans
H2_MIN_CONTENT_AFTER = 30   # but not wasteful
H3_MIN_CONTENT_AFTER = 45
H4_MIN_CONTENT_AFTER = 35
```

#### Copy Fitting Results
Typical results from copy fitting:
- 15-25% page reduction
- 10-15% file size reduction
- Maintains readability with proper testing
- Best applied after content is finalized

#### When to Apply Copy Fitting
1. **After all content edits are complete**
2. **When page count exceeds target**
3. **When excessive whitespace is visible**
4. **Before final review and publication**

**Warning**: Always verify readability after copy fitting by reviewing sample pages across the document.

## PDF Protection

### protect_pdf.py Features
- **2-page book layout view** - Opens like a physical book
- **Password protection** - Owner password required for editing
- **Read-only access** - No password needed to read
- **Disabled features**: Printing, copying text, modifying

```python
from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject, DictionaryObject, BooleanObject

# Set 2-page layout
writer._root_object[NameObject("/PageLayout")] = NameObject("/TwoPageLeft")

# Encrypt with read-only permissions
writer.encrypt(
    user_password="",              # Empty = no password to read
    owner_password=owner_pwd,      # Required to edit
    permissions_flag=0b0000,       # No permissions (read-only)
)
```

## EPUB Features

### Kindle Optimization
- Responsive CSS for all Kindle devices (Paperwhite, Fire, app)
- Proper chapter breaks with page-break-before
- NCX and NAV table of contents
- Color scheme matching PDF design

### Supported Elements
- Title page with centered layout
- Copyright page formatting
- Part dividers with styling
- Chapter headers with number and title
- Blockquotes with gold border
- Tables with navy headers
- Checklists with checkbox symbols
- Decision trees and flowcharts
- Key principle callout boxes

### CSS Classes Available
```css
.title-page, .copyright-page, .part-page
.chapter-header, .chapter-number, .chapter-title
.key-principle, .remember-box, .practical-tool
.decision-tree, .flowchart, .checklist
```

## Cover Generation

### Kindle Cover
- Dimensions: 1600 x 2560 pixels (1:1.6 ratio)
- Format: JPEG at 95% quality
- Elements: Title, subtitle, tagline, decorative lines, author name
- Solid or gradient background

### Paperback Wrap Cover
Full wrap including front, spine, and back:
- Automatic spine width calculation based on page count
- Proper bleed: 0.125" on all edges
- Safe zones: 0.25" from trim for text
- Back cover: hook, features list, author bio, price, barcode area

### Spine Width Calculation
```python
# Standard calculations for Amazon KDP
SPINE_WIDTH = PAGE_COUNT * 0.002252  # White paper (inches per page)
SPINE_WIDTH = PAGE_COUNT * 0.002500  # Cream paper (inches per page)
```

## Index Generation

### Automatic Term Discovery
```python
INDEX_TERMS = {
    "Leadership": [],
    "Daniel Principle": [],
    "Sabbath": [],
    "Calendar": [],
    # Page numbers populated automatically from PDF
}
```

### Features
- PDF text extraction via pypdf
- Variant matching (hyphenated, spaced, case-insensitive)
- Page range formatting: `1-3, 5, 7-9`
- Alphabetical letter sections
- Dot leaders between term and pages
- Long page lists wrap to next line

### PDF Merging
Final output merges:
1. Main content PDF
2. Generated index pages
3. Back cover (optional)

## Adding Covers to PDF

### add_covers_to_pdf.py
Extracts front and back covers from paperback wrap and adds to content PDF:

```python
def extract_front_cover_from_wrap(wrap_image_path: Path) -> Image.Image:
    """Extract front cover (right portion) from full wrap."""
    DPI = 300
    TRIM_WIDTH = int(5.5 * DPI)   # 1650 pixels
    BLEED = int(0.125 * DPI)      # 38 pixels
    SPINE_WIDTH = int(PAGE_COUNT * 0.002252 * DPI)

    # Front cover starts after back + spine
    front_x = (TRIM_WIDTH + BLEED) + SPINE_WIDTH
    return img.crop((front_x, BLEED, front_x + TRIM_WIDTH, BLEED + TRIM_HEIGHT))
```

### Usage
```bash
python3 add_covers_to_pdf.py
# Automatically finds latest PDF and paperback_cover_clean.png
# Output: BookTitle_v*_with_covers.pdf
```

## Front Matter / Preface

### Recommended Preface Sections
Include a `00-preface.md` file with:

```markdown
# Preface

## About This Book
Brief introduction to what the book covers.

## Version Information
**Book Version:** 1.0
**Publication Date:** January 10, 2026
**Software Version:** 2.1.3

## Staying Current
- Check official docs at [product-docs-url]
- Find latest book version at [author-website/books]
- Available as PDF/EPUB or wherever books are sold

## About the Author
Author biography and credentials.

## Acknowledgments
Thanks to contributors and supporters.
```

### Version Tracking
Create `VERSION.md` to track book editions:

```markdown
| Book Version | Date | Software Version | Notes |
|--------------|------|------------------|-------|
| 1.0 | Jan 10, 2026 | 2.1.3 | Initial release |
| 1.1 | TBD | TBD | Updates for new features |
```

## Input Conversion

### Word Documents (.docx)
```bash
python3 converters/docx_to_markdown.py input.docx -o output.md
```
- Preserves headings (H1-H6)
- Converts bold, italic, underline
- Handles bullet and numbered lists
- Converts tables to Markdown format
- Extracts images (optional: `--extract-images`)

### Plain Text Files
```bash
python3 converters/text_to_markdown.py input.txt -o output.md
```
- Auto-detects chapter markers ("Chapter", "CHAPTER", numbers)
- Preserves paragraph structure
- Identifies potential headings by patterns

## Manuscript Formatting

### Chapter Structure
```markdown
# CHAPTER 1
## The Chapter Title

Opening paragraph after chapter heading...

## Section Heading

Content with **bold** and *italic* formatting.

### Subsection Heading

More detailed content here.
```

### Part Dividers
```markdown
# PART I: FOUNDATIONS

*The Principles That Ground Everything Else*
```

### Special Elements
```markdown
> Scripture or important quote here
> -- Attribution

- [ ] Unchecked checkbox item
- [x] Checked checkbox item

| Column 1 | Column 2 | Column 3 |
|----------|----------|----------|
| Data     | Data     | Data     |

**Key Takeaway:** Important point to remember.
```

## Amazon KDP Requirements

### PDF Interior Specifications
- Trim sizes: 5" x 8" to 8.5" x 11" (various options)
- Bleed: 0.125" if images touch edge
- Resolution: 300 DPI minimum for images
- Color space: RGB or CMYK
- Fonts: Must be embedded (automatic with fpdf2)

### Kindle Cover Specifications
- Minimum: 625 x 1000 pixels
- Ideal: 1600 x 2560 pixels
- Maximum: 10,000 pixels on longest side
- Aspect ratio: 1:1.6 (height = width * 1.6)
- Format: JPEG or TIFF
- Color space: RGB

### Paperback Cover Specifications
- Calculate exact dimensions based on page count and paper type
- Include 0.125" bleed on all edges
- Spine text only if spine > 0.0625" (typically 79+ pages)
- Leave barcode area: ~2" x 1.2" on back cover lower right
- Resolution: 300 DPI

## Dependencies

```bash
# Core PDF generation
pip3 install fpdf2 pypdf

# EPUB generation
pip3 install ebooklib

# Cover generation
pip3 install Pillow

# Word document conversion
pip3 install python-docx

# PDF to image conversion (for validation)
brew install poppler
pip3 install pdf2image
```

## Template Files

| File | Purpose |
|------|---------|
| `templates/compile_book_template.py` | Compile chapters into manuscript |
| `templates/generate_pdf_template.py` | Full PDF generation with styling |
| `templates/generate_epub_template.py` | EPUB generation with ebooklib |
| `templates/generate_index_template.py` | Index extraction and PDF merge |
| `templates/create_kindle_cover_template.py` | Kindle front cover |
| `templates/create_paperback_cover_template.py` | Full wrap cover with spine |
| `templates/add_covers_to_pdf_template.py` | Extract covers from wrap, add to PDF |
| `templates/protect_pdf_template.py` | PDF encryption and protection |
| `templates/epub_styles.css` | Kindle-optimized stylesheet |
| `converters/docx_to_markdown.py` | Word document converter |
| `converters/text_to_markdown.py` | Plain text converter |

## Reference Documentation

- `references/pdf-generation.md` - Detailed PDF techniques, styling, infographics
- `references/epub-generation.md` - EPUB structure, CSS, validation
- `references/cover-generation.md` - Cover design, dimensions, typography
- `references/index-generation.md` - Term extraction, page search, formatting
- `references/amazon-kdp-requirements.md` - Full KDP specifications
- `references/manuscript-structure.md` - File organization patterns

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| TOC page numbers wrong | Single-pass generation | Ensure two-pass approach in generate_pdf.py |
| Unicode errors | Non-latin1 characters | Use `sanitize_text()` or load TTF fonts |
| Cover text blurry | Low DPI or small fonts | Use 300 DPI, minimum 24pt for titles |
| EPUB not validating | Invalid HTML structure | Run through epubcheck, fix errors |
| Index terms missing | Variant spellings | Add alternate forms to INDEX_TERMS |
| Spine text cut off | Wrong page count | Recalculate spine width after final page count |
| Headers on chapter starts | Missing flag | Set `is_chapter_start = True` before add_page() |
| Tables overflow page | Wide content | Reduce column count or font size |
| Box text overflow | chars_per_line too high | Use `content_width * 1.5` not `* 2.0+`, add +2 lines buffer |
| Orphaned headings | min_content_after too low | Use 25mm for H1, 20mm for H2, 15mm for H3 |
| Invalid running headers | Subsection titles in header | Add `_is_valid_chapter_name()` filter |
| Nearly blank pages | Short sections forcing breaks | Add `_should_force_page_break()` check |
| DeprecationWarning: ln=True | fpdf2 v2.5.2+ | Use `new_x=XPos.LMARGIN, new_y=YPos.NEXT` |
| Font subsetting warnings | macOS system fonts | Add `suppress_stderr()` context manager |
| Too much white space | Default spacing too loose | Reduce LINE_HEIGHT and PARA_SPACING values |

### Suppressing Font Warnings
```python
import os
from contextlib import contextmanager

@contextmanager
def suppress_stderr():
    """Suppress stderr during PDF output (fonttools noise)."""
    devnull = os.open(os.devnull, os.O_WRONLY)
    old_stderr = os.dup(2)
    os.dup2(devnull, 2)
    try:
        yield
    finally:
        os.dup2(old_stderr, 2)
        os.close(devnull)
        os.close(old_stderr)

# Usage
with suppress_stderr():
    pdf.output(str(output_path))
```

### Using Modern fpdf2 API
```python
from fpdf.enums import XPos, YPos

# Old (deprecated):
self.cell(0, 10, "Text", ln=True)

# New:
self.cell(0, 10, "Text", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
```

## Validation Checklist

Before publishing:

### PDF Content
- [ ] PDF opens correctly in Preview and Adobe Acrobat
- [ ] TOC page numbers match actual pages
- [ ] Running headers show correct book/chapter titles
- [ ] No headers appear on chapter start pages
- [ ] No orphaned headings at page bottom
- [ ] No nearly-blank pages from unnecessary breaks
- [ ] Box content (blockquotes, tips) doesn't overflow
- [ ] Code blocks use monospace font
- [ ] All fonts are embedded in PDF
- [ ] No orphan/widow lines at page breaks

### Cover & Layout
- [ ] Cover meets Amazon dimension requirements
- [ ] Spine width calculated for final page count
- [ ] Bleed extends 0.125" on cover
- [ ] Images are 300 DPI minimum
- [ ] Front/back covers extracted correctly from wrap

### EPUB
- [ ] EPUB validates in Kindle Previewer
- [ ] EPUB displays correctly on multiple devices
- [ ] Index terms have correct page numbers

### Protection (if applicable)
- [ ] PDF opens in 2-page book layout
- [ ] Read access works without password
- [ ] Printing is disabled
- [ ] Copying text is disabled
- [ ] Owner password required to edit

### Front Matter
- [ ] Preface includes version information
- [ ] Publication date is correct
- [ ] Software version is current
- [ ] Author bio is included
- [ ] "Staying Current" links are valid

## Example Workflow: Non-Fiction Book

```bash
# 1. Set up project structure
mkdir -p MyBook/{manuscript,publishing,assets}
cd MyBook

# 2. Copy templates
cp ~/.claude/skills/book-publisher/templates/*.py publishing/
cp ~/.claude/skills/book-publisher/templates/epub_styles.css publishing/

# 3. Write chapters in manuscript/
# 00-preface.md, 01-chapter.md, etc.

# 4. Edit publishing/compile_book.py
# - Update BOOK_METADATA
# - Update FILE_ORDER (include preface)

# 5. Edit publishing/generate_pdf.py
# - Update BOOK_CONFIG
# - Update COVER_COLORS / DESIGN_COLORS
# - Adjust LINE_HEIGHT values if needed

# 6. Run the pipeline
cd publishing
python3 compile_book.py
python3 generate_pdf.py
python3 generate_index.py
python3 generate_epub.py
python3 create_kindle_cover.py
python3 create_paperback_cover.py

# 7. Add covers to PDF
python3 add_covers_to_pdf.py

# 8. Protect PDF (optional)
python3 protect_pdf.py "YourSecurePassword"

# 9. Validate outputs
open MyBook_v*_with_covers.pdf
open MyBook_v*_protected.pdf
open MyBook_*.epub  # In Kindle Previewer
```

## Page Review Workflow

For comprehensive quality assurance, export pages to images and review:

```python
from pdf2image import convert_from_path
from pathlib import Path

pdf_path = "MyBook_v1.0_with_covers.pdf"
output_dir = Path("page_review")
output_dir.mkdir(exist_ok=True)

# Export all pages at 150 DPI for review
images = convert_from_path(pdf_path, dpi=150)
for i, img in enumerate(images, 1):
    img.save(output_dir / f"page_{i:03d}.png", "PNG")
    print(f"Exported page {i}")

# Review specific pages
problem_pages = [16, 86, 139]  # Check these for issues
for page_num in problem_pages:
    images = convert_from_path(pdf_path, first_page=page_num, last_page=page_num, dpi=200)
    images[0].save(f"review_page_{page_num}.png", "PNG")
```

## Layout Validation Workflow

Comprehensive layout validation should check for these common issues:

### Issues to Detect
| Issue | Description | How to Fix |
|-------|-------------|------------|
| **Orphaned headers** | Section heading at bottom of page with no content following | Increase `min_content_after` for that heading level |
| **Large whitespace** | Half-page or more of blank space | Reduce orphan thresholds or apply copy fitting |
| **Unrendered markdown** | Raw `**text**` or `*text*` appearing in output | Fix markdown parsing in content renderer |
| **Text overflow** | Text running outside margins or overlapping | Check box height calculations, reduce chars_per_line estimate |
| **Navigation text** | Web navigation links (`[Previous]`, `[Next]`) in print output | Remove navigation markdown from source files |
| **Bad pagination** | Content split awkwardly across pages | Adjust min_content_after or add manual page breaks |

### Validation Script
```python
#!/usr/bin/env python3
"""Visual PDF layout validation via image export."""
from pdf2image import convert_from_path
from pathlib import Path

def validate_pdf_layout(pdf_path: str, output_dir: str = "validation"):
    """Export PDF to images for visual inspection."""
    output = Path(output_dir)
    output.mkdir(exist_ok=True)

    images = convert_from_path(pdf_path, dpi=150)
    issues = []

    for i, img in enumerate(images, 1):
        img_path = output / f"page_{i:03d}.png"
        img.save(img_path, "PNG")

        # Basic heuristics for common issues
        # (Full validation requires visual inspection)
        width, height = img.size

        # Check for mostly white pages (potential large whitespace)
        pixels = list(img.getdata())
        white_count = sum(1 for p in pixels if sum(p[:3]) > 750)
        white_ratio = white_count / len(pixels)

        if white_ratio > 0.85:
            issues.append(f"Page {i}: High whitespace ({white_ratio:.1%})")

    print(f"Exported {len(images)} pages to {output}/")
    if issues:
        print("Potential issues:")
        for issue in issues:
            print(f"  - {issue}")

    return issues

if __name__ == "__main__":
    import sys
    pdf = sys.argv[1] if len(sys.argv) > 1 else "book.pdf"
    validate_pdf_layout(pdf)
```

### Fixing Issues: Work Back-to-Front
When fixing layout issues, **always work from the last page to the first**. This prevents earlier fixes from shifting page numbers and invalidating your issue list.

```bash
# Example workflow
1. Export all pages to images
2. Review and note issues: [page 220, 170, 160, 110, 70, 27, 24, 22, 13]
3. Fix page 220 first, then 170, then 160, etc.
4. Regenerate PDF after each batch of fixes
5. Verify fixes didn't introduce new issues
```

### Quick Validation Checklist
```bash
# After generating PDF, check:
□ First 5 pages (title, copyright, dedication, TOC)
□ Every 20th page for layout consistency
□ Last 3 pages (appendix, back matter)
□ Any pages with tables or code blocks
□ Part divider pages
□ Chapter start pages
```
