"""BOOK_CONFIG schema validation and defaults.

Why this module exists: the zone-based renderer needs a LOT of optional
fields (quote, bio, photo, isbn, publisher, etc). Callers shouldn't have
to set them all. This module accepts a partial BOOK_CONFIG dict, fills
defaults, validates required fields, migrates legacy names (back_body_lines
-> blurb), and returns a complete normalized dict.

Validation is upfront + all-at-once: if you're missing multiple required
fields, you learn about all of them in a single error rather than one at
a time across multiple compose runs.
"""
from typing import Any

# Required fields. Missing or empty value raises ValueError.
REQUIRED_KEYS = ("title", "author", "page_count")

# Optional fields with their defaults.
OPTIONAL_DEFAULTS: dict[str, Any] = {
    # Display
    "subtitle": "",
    "byline": "",
    "tagline": "",
    "back_tagline": "",
    # Back cover zones
    "genre_line": "",
    "quote": "",
    "quote_attribution": "",
    "blurb": [],
    "author_bio": "",
    "author_bio_label": "About the Author",
    "author_photo": None,
    # Series
    "series_line_front": "",
    "series_line_back": "",
    # Publishing
    "publisher": "",
    "publisher_city": "",
    "imprint": "",
    # Commerce
    "isbn": "",
    "price_us": "",
    # Styling
    "style_preset": "navy_gold",
    "background_tone": "light_bg",
    "paper_type": "white",
    "genre": "non-fiction",
}

# Known keys (used to detect typos)
_KNOWN_KEYS = set(REQUIRED_KEYS) | set(OPTIONAL_DEFAULTS.keys())
_LEGACY_KEYS = {"back_body_lines"}  # migrated, not considered unknown


_STRING_REQUIRED = {"title", "author"}
_STRING_OPTIONAL = {
    "subtitle", "byline", "tagline", "back_tagline", "genre_line",
    "quote", "quote_attribution", "author_bio", "author_bio_label",
    "series_line_front", "series_line_back", "publisher", "publisher_city",
    "imprint", "isbn", "price_us", "style_preset", "background_tone",
    "paper_type", "genre",
}


def validate_and_defaults(raw: dict) -> dict:
    """Validate raw BOOK_CONFIG dict; return normalized dict with all defaults filled.

    Raises:
        ValueError: if any required field is missing/empty, or page_count < 24.
        TypeError: if a string field has a non-string value, or page_count isn't int.

    Returns:
        dict with every key from REQUIRED_KEYS and OPTIONAL_DEFAULTS.
        Includes `_migrations: list[str]` noting any legacy-name translations or unknown keys.
    """
    migrations: list[str] = []

    # 1. Collect ALL missing required fields
    missing = []
    for key in REQUIRED_KEYS:
        if key not in raw or raw.get(key) in (None, "", [], ()):
            missing.append(key)
    if missing:
        raise ValueError(
            f"BOOK_CONFIG missing required keys: {missing}. "
            f"All of {list(REQUIRED_KEYS)} must be present and non-empty."
        )

    # 2. Type-check required string fields
    for key in _STRING_REQUIRED:
        if not isinstance(raw[key], str):
            raise TypeError(
                f"BOOK_CONFIG[{key!r}] must be str, got {type(raw[key]).__name__}"
            )

    # 3. Type-check and bounds-check page_count
    pc = raw["page_count"]
    if not isinstance(pc, int) or isinstance(pc, bool):
        raise TypeError(
            f"BOOK_CONFIG['page_count'] must be int, got {type(pc).__name__}"
        )
    if pc < 24:
        raise ValueError(
            f"BOOK_CONFIG['page_count']={pc} must be >= 24 (KDP paperback minimum)."
        )

    # 4. Build the normalized dict: start with defaults, overlay raw
    result: dict[str, Any] = dict(OPTIONAL_DEFAULTS)
    # Copy required keys
    for key in REQUIRED_KEYS:
        result[key] = raw[key]
    # Overlay optional keys where present
    for key, default in OPTIONAL_DEFAULTS.items():
        if key in raw:
            value = raw[key]
            # Type-check if it's a string field and the value isn't None-like
            if key in _STRING_OPTIONAL and value is not None and not isinstance(value, str):
                raise TypeError(
                    f"BOOK_CONFIG[{key!r}] must be str, got {type(value).__name__}"
                )
            result[key] = value

    # 5. Legacy migration: back_body_lines -> blurb
    if "back_body_lines" in raw:
        if not raw.get("blurb"):  # blurb absent or empty
            result["blurb"] = raw["back_body_lines"]
            migrations.append(
                "back_body_lines -> blurb (legacy name migrated; "
                "rename the key in BOOK_CONFIG to suppress this note)"
            )
        else:
            migrations.append(
                "back_body_lines ignored (both blurb and back_body_lines present; blurb used)"
            )

    # 6. Note unknown keys (typo detection)
    for key in raw:
        if key not in _KNOWN_KEYS and key not in _LEGACY_KEYS:
            migrations.append(f"unknown key {key!r} (typo?); ignored")

    result["_migrations"] = migrations
    return result
