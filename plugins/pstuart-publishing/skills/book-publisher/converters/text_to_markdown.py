#!/usr/bin/env python3
"""
Plain Text to Markdown Converter
Converts plain text files to Markdown format for book publishing.

Usage:
    python3 text_to_markdown.py input.txt [-o output.md]

Features:
- Auto-detects chapter markers (Chapter, CHAPTER, numbers)
- Preserves paragraph structure
- Identifies potential headings by patterns
- Handles common text formatting conventions

Dependencies: None (uses standard library only)
"""

import argparse
import re
from pathlib import Path


def detect_chapter_header(line):
    """Detect if a line is a chapter header."""
    line = line.strip()

    # "Chapter 1" or "CHAPTER 1" patterns
    if re.match(r'^(?:chapter|CHAPTER)\s+\d+', line, re.IGNORECASE):
        return 1

    # "Chapter 1: Title" pattern
    if re.match(r'^(?:chapter|CHAPTER)\s+\d+\s*[:\-]\s*.+', line, re.IGNORECASE):
        return 1

    # "PART I" or "Part One" patterns
    if re.match(r'^(?:part|PART)\s+(?:[IVX]+|one|two|three|four|five|[1-5])', line, re.IGNORECASE):
        return 1

    # All caps line that looks like a title (5+ chars, mostly letters)
    if line.isupper() and len(line) > 5 and re.match(r'^[A-Z\s:]+$', line):
        return 2

    return 0


def detect_section_header(line, prev_line, next_line):
    """Detect if a line might be a section header."""
    line = line.strip()

    # Short line surrounded by blank lines might be a header
    if len(line) < 60 and not prev_line.strip() and not next_line.strip():
        # Check if it looks like a title (not a sentence fragment)
        if not line.endswith((',', ';', ':', '-')):
            if line.endswith('.') and line.count('.') == 1:
                # Might be a title with period
                return 2
            if not line.endswith('.'):
                return 2

    return 0


def convert_text_to_markdown(input_path, output_path=None):
    """Convert a plain text file to Markdown."""
    input_path = Path(input_path)

    if not input_path.exists():
        print(f"Error: File not found: {input_path}")
        return None

    if output_path:
        output_path = Path(output_path)
    else:
        output_path = input_path.with_suffix('.md')

    print(f"Converting: {input_path.name}")
    print(f"Output: {output_path}")

    # Read input
    with open(input_path, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()

    # Normalize line endings
    content = content.replace('\r\n', '\n').replace('\r', '\n')

    # Split into lines
    lines = content.split('\n')

    # Process lines
    markdown_lines = []
    chapter_count = 0
    section_count = 0

    for i, line in enumerate(lines):
        prev_line = lines[i - 1] if i > 0 else ''
        next_line = lines[i + 1] if i < len(lines) - 1 else ''

        # Check for chapter headers
        heading_level = detect_chapter_header(line)
        if heading_level > 0:
            chapter_count += 1
            prefix = '#' * heading_level
            markdown_lines.append('')
            markdown_lines.append(f"{prefix} {line.strip()}")
            markdown_lines.append('')
            continue

        # Check for section headers
        section_level = detect_section_header(line, prev_line, next_line)
        if section_level > 0 and line.strip():
            section_count += 1
            prefix = '#' * (section_level + 1)  # ## for sections
            markdown_lines.append('')
            markdown_lines.append(f"{prefix} {line.strip()}")
            markdown_lines.append('')
            continue

        # Handle indented lines (might be quotes or lists)
        if line.startswith('    ') or line.startswith('\t'):
            stripped = line.strip()
            if stripped.startswith('-') or stripped.startswith('*'):
                # Already a list item
                markdown_lines.append(stripped)
            elif stripped.startswith('"') or stripped.startswith("'"):
                # Might be a quote
                markdown_lines.append(f"> {stripped}")
            else:
                # Regular indented text - preserve as-is
                markdown_lines.append(line)
            continue

        # Handle bullet points (various formats)
        if re.match(r'^[\*\-•]\s+', line.strip()):
            text = re.sub(r'^[\*\-•]\s+', '', line.strip())
            markdown_lines.append(f"- {text}")
            continue

        # Handle numbered lists
        if re.match(r'^\d+[\.\)]\s+', line.strip()):
            text = re.sub(r'^\d+[\.\)]\s+', '', line.strip())
            markdown_lines.append(f"1. {text}")
            continue

        # Regular text
        markdown_lines.append(line)

    # Join and clean up
    content = '\n'.join(markdown_lines)

    # Normalize multiple blank lines
    content = re.sub(r'\n{3,}', '\n\n', content)

    # Clean up
    content = content.strip() + '\n'

    # Write output
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"  Chapters detected: {chapter_count}")
    print(f"  Sections detected: {section_count}")
    print(f"  Output size: {len(content)} characters")

    return output_path


def main():
    parser = argparse.ArgumentParser(
        description='Convert plain text files to Markdown format'
    )
    parser.add_argument(
        'input',
        help='Input text file path'
    )
    parser.add_argument(
        '-o', '--output',
        help='Output .md file path (default: same name as input)'
    )

    args = parser.parse_args()

    result = convert_text_to_markdown(args.input, args.output)

    if result:
        print(f"\nConversion complete: {result}")
    else:
        print("\nConversion failed")
        exit(1)


if __name__ == '__main__':
    main()
