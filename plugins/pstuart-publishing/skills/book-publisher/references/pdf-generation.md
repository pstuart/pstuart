# PDF Generation Reference

## BookPDF Class Architecture

The core PDF generator extends `fpdf.FPDF` with book-specific functionality.

```python
class BookPDF(FPDF):
    def __init__(self):
        # Trade paperback: 5.5 x 8.5 inches
        super().__init__(unit='in', format=(5.5, 8.5))
        self.set_auto_page_break(auto=True, margin=0.75)
        self.set_margins(0.625, 0.75, 0.625)
        self.chapter_title = ""
        self.in_front_matter = True
        self.page_numbers = {}       # TOC page tracking
        self.collecting_pages = False # Two-pass flag
```

## Two-Pass Generation

The key innovation for accurate TOC page numbers:

```python
# PASS 1: Collect page numbers
pdf1 = BookPDF()
pdf1.collecting_pages = True
generate_content(pdf1, content)
collected_pages = pdf1.page_numbers.copy()

# PASS 2: Generate with correct numbers
pdf = BookPDF()
pdf.page_numbers = collected_pages  # Pre-populated
generate_content(pdf, content)
```

## Front Cover Design

### Gradient Background
Create gradient using horizontal strips:

```python
def front_cover(self):
    self.add_page()
    page_w, page_h = self.w, self.h

    # Gradient from dark navy to deep blue
    strips = 50
    for i in range(strips):
        r = int(26 + (15 - 26) * i / strips)
        g = int(26 + (52 - 26) * i / strips)
        b = int(46 + (96 - 46) * i / strips)
        self.set_fill_color(r, g, b)
        y_pos = i * page_h / strips
        self.rect(0, y_pos, page_w, page_h / strips + 0.01, 'F')
```

### Shield Icon
Vector drawing with FPDF primitives:

```python
# Shield outline
shield_x, shield_y = page_w / 2, 1.2
shield_w, shield_h = 0.9, 1.1

self.set_draw_color(255, 140, 0)  # Orange
self.set_line_width(0.02)

# Top arc
self.ellipse(shield_x - shield_w/2, shield_y, shield_w, shield_h * 0.6, 'D')
# Bottom point
self.line(shield_x - shield_w/2, shield_y + shield_h * 0.3, shield_x, shield_y + shield_h)
self.line(shield_x + shield_w/2, shield_y + shield_h * 0.3, shield_x, shield_y + shield_h)

# Dollar sign in center
self.set_font('Times', 'B', 36)
self.set_text_color(255, 200, 100)
self.set_xy(shield_x - 0.2, shield_y + 0.25)
self.cell(0.4, 0.5, '$', align='C')
```

### Typography
```python
# Title (large, bold)
self.set_font('Times', 'B', 32)
self.set_text_color(255, 255, 255)
self.cell(0, 0.5, 'BOOK TITLE', align='C')

# Subtitle (smaller, orange)
self.set_font('Times', '', 14)
self.set_text_color(255, 140, 0)
self.cell(0, 0.3, 'Subtitle Here', align='C')

# Author (bottom section)
self.set_font('Times', '', 12)
self.set_text_color(200, 200, 200)
self.cell(0, 0.25, 'WRITTEN BY', align='C')
self.set_font('Times', 'B', 18)
self.set_text_color(255, 140, 0)
self.cell(0, 0.35, 'Author Name', align='C')
```

## Back Cover Design

### Structure
1. Hook/headline (orange text)
2. Body copy (description)
3. Feature list with bullets
4. Endorsement quote
5. Author photo placeholder + bio
6. Barcode + price

```python
def back_cover(self):
    self.add_page()

    # Dark blue background (same gradient as front)
    # ...gradient code...

    # Hook headline
    self.set_font('Times', 'B', 16)
    self.set_text_color(255, 140, 0)
    hook = "Your compelling hook goes here."
    self.multi_cell(effective_width, 0.28, hook, align='L')

    # Features section
    self.set_text_color(255, 140, 0)
    self.cell(0, 0.25, "INSIDE YOU'LL DISCOVER:")

    features = [
        "Feature one description",
        "Feature two description",
        "Feature three description",
    ]
    self.set_text_color(230, 230, 230)
    for feature in features:
        self.cell(0.15, 0.2, "+")
        self.multi_cell(effective_width - 0.15, 0.2, feature)

    # Barcode placeholder
    self.rect(x, y, 1.2, 0.8)  # Outline
    self.set_font('Courier', '', 8)
    self.cell(0, 0.1, "978-1-XXXXXX-XX-X")
```

## Running Headers/Footers

```python
def header(self):
    # Skip on front matter (first 5 pages)
    if self.page_no() > 5 and not self.in_front_matter:
        self.set_y(0.3)
        self.set_font('Times', 'I', 8)
        self.set_text_color(150, 150, 150)

        if self.page_no() % 2 == 0:  # Even: book title
            self.cell(0, 0.15, 'BOOK TITLE', align='L')
        else:  # Odd: chapter title
            header_text = self.chapter_title.upper()
            # Adaptive font size for long titles
            font_size = 7 if len(header_text) > 25 else 8
            self.set_font('Times', 'I', font_size)
            self.cell(0, 0.15, header_text, align='R')

        # Separator line
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())

def footer(self):
    if self.page_no() > 5 and not self.in_front_matter:
        self.set_y(-0.35)
        self.set_font('Times', '', 9)
        self.set_text_color(120, 120, 120)
        self.cell(0, 0.2, str(self.page_no()), align='C')
```

## Table of Contents

```python
def table_of_contents(self):
    self.add_page()
    self.set_font('Times', 'B', 16)
    self.cell(0, 0.4, 'CONTENTS', align='C')

    toc_items = [
        ("Introduction", "intro", False),
        ("PART I: THE FOUNDATION", "part_I", True),
        ("1. Chapter Title", "ch_1", False),
        # ...
    ]

    for item, key, is_part in toc_items:
        page_num = self.page_numbers.get(key, "")

        if is_part:
            self.set_font('Times', 'B', 10)
        else:
            self.set_font('Times', '', 10)
            self.set_x(self.l_margin + 0.2)  # Indent chapters

        # Title on left, page number on right
        self.cell(effective_width - 0.4, 0.22, item)
        self.cell(0.4, 0.22, str(page_num), align='R')
```

## Content Formatting

### Chapter Headings
```python
def chapter_heading(self, num, title, toc_key=None):
    self.add_page()
    self.in_front_matter = False

    # Record page number (Pass 1 only)
    if self.collecting_pages:
        if toc_key:
            self.page_numbers[toc_key] = self.page_no()
        elif num:
            self.page_numbers[f"ch_{num}"] = self.page_no()

    # Set running header
    self.chapter_title = f'Chapter {num}' if num else title[:30]

    # Render chapter number
    if num:
        self.set_font('Times', '', 12)
        self.cell(0, 0.25, f'CHAPTER {num}', align='C')

    # Render title
    self.set_font('Times', 'B', 16)
    self.multi_cell(effective_width, 0.28, title, align='C')
```

### Part Dividers
```python
def part_page(self, part_num, title, subtitle=""):
    self.add_page()
    self.in_front_matter = False

    # Record page number
    if self.collecting_pages:
        self.page_numbers[f"part_{part_num}"] = self.page_no()

    self.set_y(3)  # Center vertically
    self.set_font('Times', 'B', 20)
    self.cell(0, 0.4, f'PART {part_num}', align='C')

    self.set_font('Times', 'B', 16)
    self.cell(0, 0.35, title.upper(), align='C')

    if subtitle:
        self.set_font('Times', 'I', 11)
        self.cell(0, 0.25, subtitle, align='C')
```

### Checkboxes
```python
def checkbox_item(self, text, checked=False, indent_level=0):
    box_size = 0.1
    start_x = self.l_margin + 0.2 + (indent_level * 0.15)
    start_y = self.get_y() + 0.04

    # Draw box
    self.set_draw_color(0, 0, 0)
    self.rect(start_x, start_y, box_size, box_size)

    # Draw X if checked
    if checked:
        self.line(start_x + 0.02, start_y + 0.02,
                  start_x + box_size - 0.02, start_y + box_size - 0.02)
        self.line(start_x + 0.02, start_y + box_size - 0.02,
                  start_x + box_size - 0.02, start_y + 0.02)

    # Text after checkbox
    text_x = start_x + box_size + 0.12
    self.set_x(text_x)
    self.multi_cell(effective_width, 0.18, text)
```

## Unicode Handling

```python
def sanitize_text(text):
    """Replace Unicode with ASCII for latin-1 encoding."""
    replacements = {
        '\u2014': '--',   # em-dash
        '\u2013': '-',    # en-dash
        '\u2018': "'",    # left single quote
        '\u2019': "'",    # right single quote
        '\u201c': '"',    # left double quote
        '\u201d': '"',    # right double quote
        '\u2026': '...',  # ellipsis
        '\u00a9': '(c)',  # copyright
        # ... more replacements
    }
    for char, replacement in replacements.items():
        text = text.replace(char, replacement)
    return text.encode('latin-1', errors='replace').decode('latin-1')
```

## EPUB Generation

Basic EPUB alongside PDF:

```python
def generate_epub(content, output_path, metadata):
    """Generate EPUB from markdown content."""
    import subprocess

    # Write temp markdown
    temp_md = output_path.with_suffix('.temp.md')
    with open(temp_md, 'w') as f:
        f.write(content)

    # Use pandoc for conversion
    subprocess.run([
        'pandoc', str(temp_md),
        '-o', str(output_path),
        '--metadata', f'title={metadata["title"]}',
        '--metadata', f'author={metadata["author"]}',
        '--toc'
    ])

    temp_md.unlink()  # Cleanup
```

## Page Size Reference

| Format | Width | Height | Use Case |
|--------|-------|--------|----------|
| Trade Paperback | 5.5" | 8.5" | Standard fiction/non-fiction |
| Mass Market | 4.25" | 6.875" | Pocket paperbacks |
| 6x9 | 6" | 9" | Larger non-fiction |
| Letter | 8.5" | 11" | Manuals, textbooks |

## Copy Fitting for Page Optimization

Copy fitting adjusts typography parameters to fit more content per page while maintaining readability. Apply after content is finalized.

### Standard vs Copy-Fitted Configuration

```python
# ============== LAYOUT PROFILES ==============

# STANDARD LAYOUT (comfortable reading)
LAYOUT_STANDARD = {
    "MARGIN_H": 12,              # mm horizontal margins
    "MARGIN_TOP": 12,
    "MARGIN_BOTTOM": 15,
    "LINE_HEIGHT_BODY": 4.5,     # mm between lines
    "LINE_HEIGHT_CODE": 3.0,
    "PARA_SPACING": 1.5,
    "SECTION_SPACING_BEFORE": 4,
    "SECTION_SPACING_AFTER": 1,
    "H2_FONT_SIZE": 13,
    "H3_FONT_SIZE": 11,
    "H4_FONT_SIZE": 10,
    # Orphan prevention (generous)
    "H1_MIN_AFTER": 50,
    "H2_MIN_AFTER": 45,
    "H3_MIN_AFTER": 70,
    "H4_MIN_AFTER": 55,
}

# COPY-FITTED LAYOUT (20-25% denser)
LAYOUT_COMPACT = {
    "MARGIN_H": 10,              # Tighter margins
    "MARGIN_TOP": 11,
    "MARGIN_BOTTOM": 13,
    "LINE_HEIGHT_BODY": 4.2,     # Tighter line spacing
    "LINE_HEIGHT_CODE": 2.9,
    "PARA_SPACING": 1.2,
    "SECTION_SPACING_BEFORE": 3,
    "SECTION_SPACING_AFTER": 0.8,
    "H2_FONT_SIZE": 12,          # Slightly smaller headings
    "H3_FONT_SIZE": 10,
    "H4_FONT_SIZE": 9.5,
    # Orphan prevention (balanced)
    "H1_MIN_AFTER": 35,
    "H2_MIN_AFTER": 30,
    "H3_MIN_AFTER": 45,
    "H4_MIN_AFTER": 35,
}
```

### Applying Copy Fitting

```python
# Select layout profile
LAYOUT = LAYOUT_COMPACT  # or LAYOUT_STANDARD

# Apply in PDF class
class BookPDF(FPDF):
    def __init__(self):
        super().__init__(unit='mm', format=(PAGE_WIDTH, PAGE_HEIGHT))
        self.set_margins(LAYOUT["MARGIN_H"], LAYOUT["MARGIN_TOP"], LAYOUT["MARGIN_H"])
        self.set_auto_page_break(True, LAYOUT["MARGIN_BOTTOM"])

    def add_section_heading(self, title):
        # Check space with layout-specific threshold
        self.check_page_space(LAYOUT["H2_MIN_AFTER"])
        self.set_font("TimesNR", "B", LAYOUT["H2_FONT_SIZE"])
        # ...
```

### Expected Results

| Metric | Standard | Copy-Fitted | Change |
|--------|----------|-------------|--------|
| Page count | 290 | 230 | -21% |
| File size | 375KB | 340KB | -9% |
| Readability | Comfortable | Still good | Verify visually |

### When to Use Copy Fitting

1. **Page count too high** for target (e.g., 300→250)
2. **Excessive whitespace** visible on many pages
3. **Production cost concerns** (fewer pages = lower print cost)
4. **After all content edits** are complete

### Validation After Copy Fitting

Always verify readability after copy fitting:
```bash
# Export sample pages for review
python3 -c "
from pdf2image import convert_from_path
for page in [25, 50, 100, 150, 200]:
    imgs = convert_from_path('book.pdf', first_page=page, last_page=page, dpi=200)
    imgs[0].save(f'sample_page_{page}.png', 'PNG')
"
```

Check for:
- Text still readable at printed size
- No overlapping content
- Adequate margin for binding
- Code blocks not truncated
