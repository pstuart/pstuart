# pstuart-publishing

Book publishing toolkit for [Claude Code](https://claude.ai/code).

Turns Markdown, Word, or plain-text manuscripts into trade-paperback PDFs, Kindle EPUBs, and KDP-ready covers.

## Install

```bash
/plugin marketplace add pstuart/pstuart
/plugin install pstuart-publishing@pstuart
```

Then invoke the skill: `/pstuart-publishing:book-publisher`

## What It Does

| Piece | Description |
|-------|-------------|
| `book-publisher` skill | Style questionnaire, manuscript pipeline, KDP checklist |
| `bookpub/` | Shared Python engine: PDF, EPUB, covers, ONIX, QA |
| `templates/` | Copy-into-project scripts for compile/PDF/EPUB/covers |
| `converters/` | `.docx` and `.txt` → Markdown |

## Local tests

```bash
cd skills/book-publisher
python3 -m pip install -e ".[test]"
python3 -m pytest -q
```

Cover-art generation uses a local `zgen` binary on `PATH` (Draw Things / Z Image Turbo). Image generation is serial — one call at a time.

## Requirements

- Python 3.11+
- `fpdf2`, `pypdf`, `EbookLib`, `Pillow`, `python-barcode` (see `skills/book-publisher/pyproject.toml`)
- Optional: `poppler` (`pdftotext` / `pdftoppm`), `epubcheck`, `zgen` on PATH

## License

MIT
