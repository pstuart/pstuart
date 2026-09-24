# bookpub — shared book-publishing engine
# QA usage:  make qa PDF=path/to/book.pdf EPUB=path/to/book.epub
.PHONY: install test qa clean

install:
	uv sync --frozen --extra test

test:
	uv run --frozen --extra test pytest -q

# Fail-loud gate over built artifacts. Pass PDF=, EPUB=, and/or COVER=/INTERIOR=.
qa:
	uv run --frozen --extra test python -m bookpub.qa_report \
		$(if $(PDF),--pdf $(PDF)) \
		$(if $(EPUB),--epub $(EPUB)) \
		$(if $(COVER),--cover $(COVER) --interior $(INTERIOR) --paper $(or $(PAPER),white)) \
		$(if $(RELEASE),--release) \
		$(if $(ALLOW_DASHES),--allow-dashes $(ALLOW_DASHES))

clean:
	python3 -c "import shutil, glob; [shutil.rmtree(p, ignore_errors=True) for p in glob.glob('**/__pycache__', recursive=True) + glob.glob('*.egg-info') + ['build', 'dist', '.pytest_cache']]"
