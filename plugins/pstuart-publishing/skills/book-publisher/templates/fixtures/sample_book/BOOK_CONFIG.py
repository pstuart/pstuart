"""Full-fixture BOOK_CONFIG exercising every zone in the cover composer.

This fixture is the smoke-test source of truth: if you add a new field to
the cover layout system, add it here too so the end-to-end test catches it.
"""
from pathlib import Path

_FIXTURE_DIR = Path(__file__).parent

BOOK_CONFIG = {
    # Required
    "title": "Sample Book",
    "author": "Test Author",
    "page_count": 200,

    # Display
    "subtitle": "A Fixture for Smoke Tests",
    "byline": "",  # falls back to "BY TEST AUTHOR"
    "tagline": "",  # front-cover tagline — leave empty; back_tagline is used
    "back_tagline": "A playwright who never existed.",
    "kindle_quote": "A thrilling debut. — Fixture Reviewer",

    # Back cover zones
    "genre_line": "A Historical Conspiracy Thriller",
    "quote": "Every great conspiracy\nstarts with a single lie.",
    "quote_attribution": "Fixture Daily",
    "blurb": [
        "The printing press is alive with whispers.",
        "",
        "In the back rooms of Elizabethan London, a small circle",
        "of scholars, spies, and printers conspire to hide the",
        "truth of who wrote the plays the world will call",
        "Shakespeare.",
        "",
        "One night, a typesetter discovers something",
        "that should not exist.",
    ],
    "author_bio": (
        "Test Author lives in the Pacific Northwest,\n"
        "where the rain encourages long thinking."
    ),
    "author_bio_label": "About the Author",
    "author_photo": str(_FIXTURE_DIR / "assets" / "author_photo.png"),

    # Series
    "series_line_front": "A Novel of Elizabethan England",
    "series_line_back": "The Fixture Conspiracy · Book I",

    # Publishing
    "publisher": "Fixture Press",
    "publisher_city": "Seattle",
    "imprint": "Fixture Imprint",

    # Commerce
    "isbn": "9780000000002",
    "price_us": "$18.99",

    # Styling
    "style_preset": "burgundy_cream",
    "background_tone": "light_bg",
    "paper_type": "white",
    "genre": "historical thriller",
}
