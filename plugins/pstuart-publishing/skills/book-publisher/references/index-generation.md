# Index Generation Reference

## Overview

The index generation system:
1. Extracts index terms from the manuscript
2. Generates the base PDF without index
3. Extracts text from each PDF page
4. Searches for terms across pages
5. Generates formatted index pages
6. Merges index (and back cover) into final PDF

## Term Extraction

### Index Section Format

```markdown
## Index

### A
Account architecture, 000-000
   automation, 000
   setup, 000

### B
Budgeting, 000-000
   conscious spending, 000
   zero-based, 000
```

### Extraction Code

```python
def extract_index_terms(manuscript_path):
    """Extract index terms from manuscript's Index section."""
    with open(manuscript_path, 'r') as f:
        content = f.read()

    # Find Index section
    index_match = re.search(
        r'^## Index\s*\n(.*?)(?=^## |\Z)',
        content, re.MULTILINE | re.DOTALL
    )
    if not index_match:
        return {}

    terms = {}
    current_main_term = None

    for line in index_match.group(1).split('\n'):
        # Letter headers (### A)
        if re.match(r'^### ([A-Z])$', line):
            continue

        # Main terms (no indent): "Term name, 000-000"
        main_match = re.match(r'^([A-Za-z][^,]+),\s*(\d+-\d+|\d+)', line)
        if main_match:
            term = main_match.group(1).strip()
            current_main_term = term
            terms[term] = {
                'search_terms': [term],
                'pages': [],
                'subterms': {}
            }
            continue

        # Subterms (indented): "   subterm, 000"
        sub_match = re.match(r'^   ([^,]+),\s*(\d+-\d+|\d+)', line)
        if sub_match and current_main_term:
            subterm = sub_match.group(1).strip()
            terms[current_main_term]['subterms'][subterm] = []

    return terms
```

## PDF Text Extraction

```python
from pypdf import PdfReader

def extract_text_by_page(pdf_path):
    """Extract text content from each page."""
    reader = PdfReader(pdf_path)
    pages = {}

    for i, page in enumerate(reader.pages):
        page_num = i + 1
        text = page.extract_text() or ""
        # Normalize for searching
        pages[page_num] = text.lower()

    return pages
```

## Term Searching

```python
def find_term_pages(term, pages_text, search_variations=None):
    """Find all pages containing a term."""
    found_pages = set()

    # Default to term itself plus common variations
    search_terms = search_variations or [term]

    # Add lowercase/uppercase variations
    search_terms.extend([
        term.lower(),
        term.title(),
        term.replace('-', ' '),  # Handle hyphenation
        term.replace(' ', '-'),
    ])

    for page_num, text in pages_text.items():
        text_lower = text.lower()
        for search in search_terms:
            if search.lower() in text_lower:
                found_pages.add(page_num)
                break

    return sorted(found_pages)
```

## Index Formatting

### Page Number Formatting

```python
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
            # End current range
            if start == prev:
                ranges.append(str(start))
            else:
                ranges.append(f"{start}-{prev}")
            start = prev = page

    # Add final range
    if start == prev:
        ranges.append(str(start))
    else:
        ranges.append(f"{start}-{prev}")

    return ", ".join(ranges)
```

### Index PDF Generation

```python
class IndexPDF(FPDF):
    def __init__(self):
        super().__init__(unit='in', format=(5.5, 8.5))
        self.set_auto_page_break(auto=True, margin=0.75)
        self.set_margins(0.625, 0.75, 0.625)

    def header(self):
        if self.page_no() > 0:
            self.set_y(0.3)
            self.set_font('Times', 'I', 8)
            self.set_text_color(150, 150, 150)
            self.cell(0, 0.15, 'INDEX', align='C')
            self.ln(0.1)
            self.line(self.l_margin, self.get_y(),
                     self.w - self.r_margin, self.get_y())
            self.set_y(0.75)

def generate_index_pdf(terms_with_pages, output_path):
    """Generate formatted index PDF."""
    pdf = IndexPDF()
    pdf.add_page()

    # Title
    pdf.set_font('Times', 'B', 16)
    pdf.cell(0, 0.4, 'INDEX', align='C', new_x='LMARGIN', new_y='NEXT')
    pdf.ln(0.3)

    effective_width = pdf.w - pdf.l_margin - pdf.r_margin

    # Group by first letter
    current_letter = None

    for term in sorted(terms_with_pages.keys(), key=str.lower):
        first_letter = term[0].upper()

        # Letter section header
        if first_letter != current_letter:
            current_letter = first_letter
            pdf.ln(0.15)
            pdf.set_font('Times', 'B', 12)
            pdf.cell(0, 0.25, first_letter, new_x='LMARGIN', new_y='NEXT')
            pdf.ln(0.08)

        # Main term
        pages = terms_with_pages[term]['pages']
        page_str = format_page_numbers(pages)

        pdf.set_font('Times', '', 10)
        render_index_entry(pdf, term, page_str, effective_width, indent=0)

        # Subterms
        for subterm, sub_pages in terms_with_pages[term].get('subterms', {}).items():
            sub_page_str = format_page_numbers(sub_pages)
            render_index_entry(pdf, subterm, sub_page_str, effective_width, indent=0.2)

    pdf.output(output_path)
```

### Dot Leaders

```python
def render_index_entry(pdf, term, page_str, width, indent=0):
    """Render index entry with dot leaders."""
    pdf.set_x(pdf.l_margin + indent)

    # Calculate widths
    term_width = pdf.get_string_width(term)
    page_width = pdf.get_string_width(page_str)
    dot_space = width - indent - term_width - page_width - 0.3

    # Term
    pdf.cell(term_width + 0.05, 0.2, term)

    # Dot leaders
    if dot_space > 0.2:
        dots = '.' * int(dot_space / pdf.get_string_width('.'))
        pdf.set_text_color(180, 180, 180)
        pdf.cell(dot_space, 0.2, dots)
        pdf.set_text_color(0, 0, 0)

    # Page numbers
    pdf.cell(page_width, 0.2, page_str, align='R', new_x='LMARGIN', new_y='NEXT')
```

## PDF Merging

```python
from pypdf import PdfReader, PdfWriter

def merge_pdfs(main_pdf, index_pdf, back_cover_pdf, output_path):
    """Merge main content + index + back cover."""
    writer = PdfWriter()

    # Main content
    main_reader = PdfReader(main_pdf)
    for page in main_reader.pages:
        writer.add_page(page)

    # Index
    index_reader = PdfReader(index_pdf)
    for page in index_reader.pages:
        writer.add_page(page)

    # Back cover
    back_reader = PdfReader(back_cover_pdf)
    for page in back_reader.pages:
        writer.add_page(page)

    with open(output_path, 'wb') as f:
        writer.write(f)

    return len(writer.pages)
```

## Complete Workflow

```python
def main():
    # 1. Find latest PDF
    pdf_path = find_latest_pdf()
    print(f"Using PDF: {pdf_path}")

    # 2. Extract index terms
    terms = extract_index_terms(manuscript_path)
    print(f"Found {len(terms)} main terms")

    # 3. Extract text from pages
    pages_text = extract_text_by_page(pdf_path)
    print(f"Extracted text from {len(pages_text)} pages")

    # 4. Search for terms
    for term, data in terms.items():
        data['pages'] = find_term_pages(term, pages_text)
        for subterm in data['subterms']:
            data['subterms'][subterm] = find_term_pages(subterm, pages_text)

    # 5. Generate index PDF
    generate_index_pdf(terms, index_path)
    print(f"Generated index")

    # 6. Generate back cover PDF
    generate_back_cover_pdf(back_cover_path)

    # 7. Merge everything
    total_pages = merge_pdfs(pdf_path, index_path, back_cover_path, output_path)
    print(f"Final PDF: {total_pages} pages")
```

## Versioning

Auto-increment version numbers:

```python
def get_next_version(pub_dir):
    """Find next version number from existing PDFs."""
    import re as re_mod

    existing = list(pub_dir.glob("*_v*_*.pdf"))
    versions = []

    for pdf in existing:
        match = re_mod.search(r'_v(\d+)_', pdf.name)
        if match:
            versions.append(int(match.group(1)))

    return max(versions) + 1 if versions else 1
```

## Common Issues

### No Terms Found
- Check Index section header is exactly `## Index`
- Ensure term format: `Term name, 000`
- Verify letter headers: `### A`

### Wrong Page Numbers
- PDF text extraction varies by PDF structure
- Try different search variations
- Check for hyphenated terms

### Index Overlaps Content
- Generate index separately
- Merge as final step
- Don't include index placeholder in main PDF
