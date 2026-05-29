"""bookpub — the shared book-publishing engine.

One config-driven engine that replaces the per-book forked `publishing/` scripts.
Books vendor this package and supply a ``book.toml`` plus a thin shim, the same
pattern the cover library (now ``bookpub.covers``) already proved drift-free.

Phase 0 ships only the QA gate (:mod:`bookpub.qa_report`); the PDF/EPUB/index
engines land in later phases.
"""

__version__ = "0.1.0"
