#!/usr/bin/env python3
"""
Book Compilation Template
Compile multiple markdown chapter files into a single manuscript.

CUSTOMIZATION REQUIRED:
1. Update BASE_DIR to your book project path
2. Update BOOK_METADATA with your book details
3. Update FILE_ORDER with your chapter structure

Features:
- Combines multiple chapter files into single manuscript
- Generates YAML front matter for pandoc compatibility
- Generates title page, copyright, and dedication
- Supports part dividers with Roman numerals
- Strips existing YAML front matter from individual files
- Supports both flat and nested directory structures

Dependencies: None (uses standard library only)
"""

import os
import re
from pathlib import Path
from datetime import datetime

# ============================================================================
# CONFIGURATION - CUSTOMIZE THESE
# ============================================================================

# Base directory of your book project
BASE_DIR = Path("/path/to/your/BookProject")
OUTPUT_DIR = BASE_DIR / "publishing"

# Book metadata
BOOK_METADATA = {
    "title": "Your Book Title",
    "subtitle": "Your Subtitle Here",
    "author": "Author Name",
    "year": "2025",
    "website": "www.yoursite.com",
    "dedication": "For everyone who believed in this book.",
}

# File order for compilation
# Format: (relative_path, prefix_text)
# - prefix_text is inserted BEFORE the file content
# - Use \newpage for page breaks
# - Use # PART X: TITLE for part headers
FILE_ORDER = [
    # Introduction
    ("Introduction.md", ""),

    # Part 1
    ("Part1_Name/Chapter01_Title.md",
     "\n\\newpage\n\n# PART I: PART TITLE\n\n*Part subtitle*\n\n\\newpage\n\n"),
    ("Part1_Name/Chapter02_Title.md", "\n\\newpage\n\n"),
    ("Part1_Name/Chapter03_Title.md", "\n\\newpage\n\n"),

    # Part 2
    ("Part2_Name/Chapter04_Title.md",
     "\n\\newpage\n\n# PART II: PART TITLE\n\n*Part subtitle*\n\n\\newpage\n\n"),
    ("Part2_Name/Chapter05_Title.md", "\n\\newpage\n\n"),

    # Add more parts/chapters as needed...

    # Back Matter
    ("BackMatter.md", "\n\\newpage\n\n"),
]

# ============================================================================
# COMPILATION LOGIC - GENERALLY DON'T MODIFY
# ============================================================================

def generate_yaml_frontmatter():
    """Generate YAML front matter for pandoc."""
    return f"""---
title: "{BOOK_METADATA['title']}"
subtitle: "{BOOK_METADATA['subtitle']}"
author: "{BOOK_METADATA['author']}"
date: "{BOOK_METADATA['year']}"
rights: "Copyright (c) {BOOK_METADATA['year']} {BOOK_METADATA['author']}. All rights reserved."
lang: en-US
documentclass: book
classoption:
  - 11pt
  - oneside
geometry:
  - paperwidth=6in
  - paperheight=9in
  - margin=0.75in
  - top=1in
  - bottom=1in
mainfont: "Georgia"
sansfont: "Helvetica"
monofont: "Courier"
toc: true
toc-depth: 2
numbersections: false
---
"""


def generate_front_matter():
    """Generate front matter pages."""
    return f"""
\\newpage

# {BOOK_METADATA['title'].upper()}

## {BOOK_METADATA['subtitle']}

\\vspace{{2cm}}

### {BOOK_METADATA['author']}

\\newpage

## Copyright

**{BOOK_METADATA['title']}: {BOOK_METADATA['subtitle']}**

Copyright (c) {BOOK_METADATA['year']} by {BOOK_METADATA['author']}

All rights reserved. No part of this publication may be reproduced, distributed, or transmitted in any form or by any means, including photocopying, recording, or other electronic or mechanical methods, without the prior written permission of the publisher, except in the case of brief quotations embodied in critical reviews.

**Disclaimer:** This book is intended for informational and educational purposes only. The author is not providing professional advice specific to your situation. Before making any decisions based on this book, consult with qualified professionals.

**ISBN:** 978-1-XXXXXX-XX-X (Paperback)

**ISBN:** 978-1-XXXXXX-XX-X (eBook)

First Edition: {BOOK_METADATA['year']}

{BOOK_METADATA['website']}

Printed in the United States of America

10 9 8 7 6 5 4 3 2 1

\\newpage

## Dedication

*{BOOK_METADATA['dedication']}*

\\newpage

"""


def compile_manuscript():
    """Compile all chapters into a single manuscript."""
    OUTPUT_DIR.mkdir(exist_ok=True)
    output_file = OUTPUT_DIR / "manuscript_compiled.md"

    with open(output_file, 'w', encoding='utf-8') as out:
        # Write YAML front matter
        out.write(generate_yaml_frontmatter())

        # Write front matter pages
        out.write(generate_front_matter())

        # Process each file
        for filename, prefix in FILE_ORDER:
            filepath = BASE_DIR / filename
            if filepath.exists():
                out.write(prefix)
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Remove existing YAML front matter from individual files
                    if content.startswith('---'):
                        parts = content.split('---', 2)
                        if len(parts) >= 3:
                            content = parts[2].strip()
                    out.write(content)
                    out.write("\n\n")
                print(f"  + Added: {filename}")
            else:
                print(f"  ! Missing: {filename}")

    print(f"\nCompiled manuscript: {output_file}")
    return output_file


if __name__ == "__main__":
    print(f"Compiling: {BOOK_METADATA['title']}")
    print("=" * 50)
    compile_manuscript()
