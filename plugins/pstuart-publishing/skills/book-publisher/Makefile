# bookpub — shared book-publishing engine
# QA usage:  make qa PDF=path/to/book.pdf EPUB=path/to/book.epub
.PHONY: install test qa clean

install:
	pip install -e ".[test]"

test:
	python3 -m pytest -q

# Fail-loud gate over built artifacts. Pass PDF=, EPUB=, and/or COVER=/INTERIOR=.
qa:
	python3 -m bookpub.qa_report \
		$(if $(PDF),--pdf $(PDF)) \
		$(if $(EPUB),--epub $(EPUB)) \
		$(if $(COVER),--cover $(COVER) --interior $(INTERIOR) --paper $(or $(PAPER),white)) \
		$(if $(RELEASE),--release) \
		$(if $(ALLOW_DASHES),--allow-dashes $(ALLOW_DASHES))

clean:
	python3 -c "import shutil, glob; [shutil.rmtree(p, ignore_errors=True) for p in glob.glob('**/__pycache__', recursive=True) + glob.glob('*.egg-info') + ['build', 'dist', '.pytest_cache']]"
