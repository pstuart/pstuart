#!/usr/bin/env python3
"""
Index Generation Template
Generate index with real page numbers and merge into final PDF.

CUSTOMIZATION REQUIRED:
1. Update BASE_DIR to your book project path
2. Update BOOK_PREFIX for output filename
3. Configure INDEX_TERMS with your book's key terms
4. Update BACK_COVER_CONFIG with your content

Process:
1. Extract text from each PDF page
2. Search for index terms and find page numbers
3. Generate formatted index pages with dot leaders
4. Optionally generate back cover
5. Merge everything into final PDF

Dependencies: pip3 install fpdf2 pypdf
"""

import re
from pathlib import Path
from datetime import datetime
from pypdf import PdfReader, PdfWriter
from fpdf import FPDF

# ============================================================================
# CONFIGURATION - CUSTOMIZE THESE
# ============================================================================

BASE_DIR = Path("/path/to/your/BookProject")
PUB_DIR = BASE_DIR / "publishing"

# Book name prefix for output files (e.g., "YourBookTitle_v62_...")
BOOK_PREFIX = "YourBookTitle"

# Set to True to generate and append back cover
INCLUDE_BACK_COVER = True

# Index terms to search for
# Add all key concepts, people, and topics you want indexed
# The script will find which pages contain each term
INDEX_TERMS = {
    # Core Concepts
    "Key Concept One": [],
    "Key Concept Two": [],
    "Important Principle": [],

    # People & Models
    "Person Name": [],
    "Framework Name": [],

    # Topics
    "Topic One": [],
    "Topic Two": [],
    "Topic Three": [],

    # Practices
    "Practice One": [],
    "Practice Two": [],

    # Add more terms as needed...
    # Format: "Term Name": [] (pages will be populated automatically)
}

# Back cover configuration (if INCLUDE_BACK_COVER is True)
BACK_COVER_CONFIG = {
    "title": "YOUR BOOK TITLE",
    "hook": "Your compelling opening hook for the back cover.",
    "description": """A longer description paragraph that expands on the hook.

This can be multiple paragraphs explaining what the reader will gain from the book.""",
    "author": "Author Name",
    "author_bio": "Author bio text goes here. Include credentials and relevant experience.",
    "price": "$24.99 US",
    "category": "Category / Subcategory",
    "website": "www.yoursite.com",
    "features": [
        "First key benefit or discovery",
        "Second key benefit or discovery",
        "Third key benefit or discovery",
        "Fourth key benefit or discovery",
    ],
}

# Colors matching your book design
COLORS = {
    "navy": (15, 32, 55),
    "navy_light": (25, 55, 95),
    "gold": (218, 165, 32),
    "text_light": (230, 230, 230),
    "text_muted": (180, 180, 180),
}

# ============================================================================
# TEXT UTILITIES
# ============================================================================

def sanitize_text(text):
    """Normalize text for core fonts (no Unicode support).

    FPDF's built-in fonts (Times, Helvetica, Courier) only support
    latin-1 characters. This function converts Unicode characters
    to their latin-1 equivalents.
    """
    replacements = {
        '\u2014': '--',       # em dash to double hyphen
        '\u2013': '-',        # en dash to hyphen
        '\u2018': "'",        # left single quote
        '\u2019': "'",        # right single quote
        '\u201c': '"',        # left double quote
        '\u201d': '"',        # right double quote
        '\u2026': '...',      # ellipsis
        '\u00a0': ' ',        # non-breaking space
        '\u2022': '*',        # bullet
        '\u00b7': '*',        # middle dot
    }
    for char, repl in replacements.items():
        text = text.replace(char, repl)

    return text.encode('latin-1', errors='replace').decode('latin-1')


# ============================================================================
# PDF TEXT EXTRACTION
# ============================================================================

def extract_text_by_page(pdf_path):
    """Extract text from each page of the PDF."""
    reader = PdfReader(pdf_path)
    pages = {}
    for i, page in enumerate(reader.pages):
        pages[i + 1] = (page.extract_text() or "").lower()
    return pages


def find_term_pages(term, pages_text):
    """Find all pages containing a term.

    Searches for multiple variants of the term:
    - Original term (case-insensitive)
    - With hyphens replaced by spaces
    - With spaces replaced by hyphens
    """
    found = set()
    search_terms = [
        term.lower(),
        term.replace('-', ' ').lower(),
        term.replace(' ', '-').lower(),
    ]

    for page_num, text in pages_text.items():
        for search in search_terms:
            if search in text:
                found.add(page_num)
                break
    return sorted(found)


# ============================================================================
# INDEX PDF GENERATION
# ============================================================================

def format_page_numbers(pages):
    """Format page list with ranges: [1,2,3,5,7,8,9] -> '1-3, 5, 7-9'"""
    if not pages:
        return ""

    pages = sorted(set(pages))
    ranges = []
    start = prev = pages[0]

    for page in pages[1:]:
        if page == prev + 1:
            prev = page
        else:
            ranges.append(str(start) if start == prev else f"{start}-{prev}")
            start = prev = page

    ranges.append(str(start) if start == prev else f"{start}-{prev}")
    return ", ".join(ranges)


class IndexPDF(FPDF):
    def __init__(self):
        super().__init__(unit='in', format=(5.5, 8.5))
        self.set_auto_page_break(auto=True, margin=0.75)
        self.set_margins(0.625, 0.75, 0.625)

    def header(self):
        self.set_y(0.3)
        self.set_font('Times', 'I', 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 0.15, 'INDEX', align='C')
        self.ln(0.1)
        self.set_draw_color(200, 200, 200)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.set_y(0.75)

    def footer(self):
        pass  # Page numbers handled by main PDF


def generate_index_pdf(terms, output_path):
    """Generate formatted index PDF.

    Args:
        terms: Dictionary of {term: [page_numbers]} where page_numbers
               is a list of integers
        output_path: Path for output PDF file

    Returns:
        Number of pages in generated index
    """
    pdf = IndexPDF()
    pdf.add_page()

    # Title
    pdf.set_font('Times', 'B', 16)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 0.4, 'INDEX', align='C', new_x='LMARGIN', new_y='NEXT')
    pdf.ln(0.3)

    width = pdf.w - pdf.l_margin - pdf.r_margin
    current_letter = None

    # Sort terms alphabetically (case-insensitive), only include those with pages
    sorted_terms = sorted(
        [(t, p) for t, p in terms.items() if p],
        key=lambda x: x[0].lower()
    )

    for term, pages in sorted_terms:
        first = term[0].upper()

        # Letter section header
        if first != current_letter:
            current_letter = first
            pdf.ln(0.15)
            pdf.set_font('Times', 'B', 12)
            pdf.cell(0, 0.25, first, new_x='LMARGIN', new_y='NEXT')
            pdf.ln(0.08)

        # Format page numbers with ranges
        page_str = format_page_numbers(pages)
        pdf.set_font('Times', '', 10)
        pdf.set_text_color(0, 0, 0)

        term_w = pdf.get_string_width(term)
        page_w = pdf.get_string_width(page_str)
        min_dot_space = 0.3
        available_for_pages = width - term_w - min_dot_space - 0.1

        # Check if page numbers fit on same line
        if page_w <= available_for_pages:
            # Single line layout with dot leaders
            dot_space = width - term_w - page_w - 0.1
            pdf.cell(term_w + 0.05, 0.2, term)
            if dot_space > 0.2:
                dots = '.' * int(dot_space / pdf.get_string_width('.'))
                pdf.set_text_color(180, 180, 180)
                pdf.cell(dot_space, 0.2, dots)
                pdf.set_text_color(0, 0, 0)
            pdf.cell(page_w, 0.2, page_str, align='R', new_x='LMARGIN', new_y='NEXT')
        else:
            # Page numbers need wrapping - term on first line, pages on next
            pdf.cell(term_w + 0.05, 0.2, term, new_x='LMARGIN', new_y='NEXT')
            pdf.set_x(pdf.l_margin + 0.3)
            pdf.multi_cell(width - 0.3, 0.18, page_str, align='L')
            pdf.set_x(pdf.l_margin)

    pdf.output(output_path)
    return pdf.page_no()


# ============================================================================
# BACK COVER (OPTIONAL)
# ============================================================================

def generate_back_cover_pdf(output_path):
    """Generate back cover PDF with gradient background.

    Creates a professional back cover with:
    - Navy gradient background
    - Gold accent text for hook and headers
    - Features list
    - Author bio
    - Price and category
    - Website
    """
    pdf = FPDF(unit='in', format=(5.5, 8.5))
    pdf.set_auto_page_break(auto=False)  # Prevent page breaks on cover
    pdf.add_page()

    # Gradient background (navy to lighter navy)
    navy = COLORS["navy"]
    navy_light = COLORS["navy_light"]
    for i in range(50):
        r = int(navy[0] + (navy_light[0] - navy[0]) * i / 50)
        g = int(navy[1] + (navy_light[1] - navy[1]) * i / 50)
        b = int(navy[2] + (navy_light[2] - navy[2]) * i / 50)
        pdf.set_fill_color(r, g, b)
        pdf.rect(0, i * 8.5 / 50, 5.5, 8.5 / 50 + 0.01, 'F')

    cfg = BACK_COVER_CONFIG
    gold = COLORS["gold"]
    text_light = COLORS["text_light"]
    text_muted = COLORS["text_muted"]
    width = 5.5 - 1.0  # Margins

    # Hook (bold, gold)
    pdf.set_xy(0.5, 0.6)
    pdf.set_font('Times', 'B', 14)
    pdf.set_text_color(*gold)
    pdf.multi_cell(width, 0.25, sanitize_text(cfg["hook"]))

    # Description (if present)
    if cfg.get("description"):
        pdf.ln(0.15)
        pdf.set_x(0.5)
        pdf.set_font('Times', '', 10)
        pdf.set_text_color(*text_light)
        pdf.multi_cell(width, 0.19, sanitize_text(cfg["description"]))

    # Features header
    pdf.ln(0.2)
    pdf.set_font('Times', 'B', 10)
    pdf.set_text_color(*gold)
    pdf.set_x(0.5)
    pdf.cell(0, 0.25, "INSIDE YOU'LL DISCOVER:", new_x='LMARGIN', new_y='NEXT')
    pdf.ln(0.08)

    # Features list
    pdf.set_font('Times', '', 9)
    pdf.set_text_color(220, 220, 220)
    for feat in cfg["features"]:
        pdf.set_x(0.5)
        pdf.cell(0.15, 0.18, "+")
        pdf.multi_cell(width - 0.15, 0.18, sanitize_text(feat))
        pdf.ln(0.02)

    # Author section with divider line
    pdf.set_y(5.8)
    pdf.set_x(0.5)
    pdf.set_draw_color(*gold)
    pdf.set_line_width(0.01)
    pdf.line(0.5, pdf.get_y(), 5.0, pdf.get_y())
    pdf.ln(0.15)

    # Author name
    pdf.set_x(0.5)
    pdf.set_font('Times', 'B', 11)
    pdf.set_text_color(*gold)
    pdf.cell(0, 0.25, cfg["author"], new_x='LMARGIN', new_y='NEXT')

    # Author bio
    pdf.set_x(0.5)
    pdf.set_font('Times', '', 9)
    pdf.set_text_color(200, 200, 200)
    pdf.multi_cell(width, 0.17, sanitize_text(cfg["author_bio"]))

    # Price/Category at bottom right
    pdf.set_xy(3.5, 7.7)
    pdf.set_font('Times', 'B', 14)
    pdf.set_text_color(*gold)
    pdf.cell(0, 0.2, cfg["price"])
    pdf.set_xy(3.5, 7.95)
    pdf.set_font('Times', '', 8)
    pdf.set_text_color(*text_muted)
    pdf.cell(0, 0.15, cfg["category"])

    # Website at bottom left
    pdf.set_xy(0.5, 8.1)
    pdf.set_font('Times', '', 9)
    pdf.set_text_color(*gold)
    pdf.cell(0, 0.15, cfg["website"])

    pdf.output(output_path)


# ============================================================================
# PDF MERGING
# ============================================================================

def merge_pdfs(main_pdf, index_pdf, back_cover_pdf, output_path):
    """Merge main PDF + index + optional back cover."""
    writer = PdfWriter()

    # Main content
    main_reader = PdfReader(main_pdf)
    for page in main_reader.pages:
        writer.add_page(page)

    # Index
    index_reader = PdfReader(index_pdf)
    for page in index_reader.pages:
        writer.add_page(page)

    # Back cover (optional)
    if back_cover_pdf and back_cover_pdf.exists():
        back_reader = PdfReader(back_cover_pdf)
        for page in back_reader.pages:
            writer.add_page(page)

    with open(output_path, 'wb') as f:
        writer.write(f)

    return len(writer.pages)


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def find_latest_pdf():
    """Find the most recent non-FINAL PDF in publishing directory."""
    # Look for versioned PDFs, exclude FINAL PDFs (those already have index)
    pdfs = [p for p in PUB_DIR.glob(f"{BOOK_PREFIX}_v*_*.pdf")
            if "FINAL" not in p.name]

    if not pdfs:
        # Try more general pattern
        pdfs = [p for p in PUB_DIR.glob("*_v*_*.pdf")
                if "FINAL" not in p.name]

    if not pdfs:
        raise FileNotFoundError(
            f"No PDF found in {PUB_DIR}. Run generate_pdf.py first!"
        )

    def version_key(p):
        match = re.search(r'_v(\d+)_', p.name)
        return int(match.group(1)) if match else 0

    return max(pdfs, key=version_key)


def get_next_version():
    """Get next version number based on existing PDFs."""
    pdfs = list(PUB_DIR.glob(f"{BOOK_PREFIX}_v*_*.pdf"))
    if not pdfs:
        pdfs = list(PUB_DIR.glob("*_v*_*.pdf"))

    versions = []
    for pdf in pdfs:
        match = re.search(r'_v(\d+)_', pdf.name)
        if match:
            versions.append(int(match.group(1)))

    return max(versions) + 1 if versions else 1


def main():
    print("=" * 60)
    print("Index & Back Cover Generation")
    print("=" * 60)

    # Find source PDF
    pdf_path = find_latest_pdf()
    print(f"\nUsing PDF: {pdf_path.name}")

    # 1. Extract text from PDF pages
    print("\n1. Extracting text from PDF pages...")
    pages_text = extract_text_by_page(pdf_path)
    print(f"   Extracted text from {len(pages_text)} pages")

    # 2. Search for terms
    print("\n2. Searching for index terms...")
    terms = INDEX_TERMS.copy()
    found_count = 0
    for term in terms:
        terms[term] = find_term_pages(term, pages_text)
        if terms[term]:
            found_count += 1
            print(f"   {term}: {len(terms[term])} pages")

    print(f"\n   Found pages for {found_count}/{len(terms)} terms")

    # 3. Generate index PDF
    print("\n3. Generating index PDF...")
    index_path = PUB_DIR / "index.pdf"
    num_pages = generate_index_pdf(terms, index_path)
    print(f"   Generated {num_pages} index pages")

    # 4. Generate back cover (optional)
    back_cover_path = None
    if INCLUDE_BACK_COVER:
        print("\n4. Generating back cover PDF...")
        back_cover_path = PUB_DIR / "back_cover.pdf"
        generate_back_cover_pdf(back_cover_path)
        print("   Generated back cover")

    # 5. Merge everything
    print("\n5. Merging final PDF...")
    version = get_next_version()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    output_name = f"{BOOK_PREFIX}_v{version}_{timestamp}_FINAL.pdf"
    output_path = PUB_DIR / output_name

    total = merge_pdfs(pdf_path, index_path, back_cover_path, output_path)

    print()
    print("=" * 60)
    print(f"FINAL PDF: {output_path.name}")
    print(f"Total pages: {total}")
    print("=" * 60)


if __name__ == "__main__":
    main()
