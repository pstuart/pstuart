"""Tests for bookpub.text — the canonical sanitiser that kills the `--` bug."""
import pytest

from bookpub.text import sanitize_text, strip_markdown


def test_double_hyphen_becomes_emdash():
    assert sanitize_text("planning your exit -- this is the guide") == \
        "planning your exit — this is the guide"


def test_real_emdash_is_preserved():
    # THE regression guard: a real em-dash must survive verbatim. This fails the
    # instant anyone re-introduces an em-dash->hyphen or ->'--' flattening.
    assert sanitize_text("exit—now") == "exit—now"
    assert "--" not in sanitize_text("exit—now")


def test_unicode_punctuation_preserved():
    # EB Garamond has all of these; they must pass through untouched.
    s = "“curly” ‘quotes’ – en-dash … ellipsis • bullet © ® ™ → ′ ″"
    assert sanitize_text(s, em_dash=False) == s


def test_no_lossy_encode():
    # Nothing should be downgraded to latin-1/cp1252; non-latin-1 survives.
    assert sanitize_text("café — résumé") == "café — résumé"


def test_box_drawing_falls_back_to_ascii():
    # The only glyphs the bundled serif lacks get ASCII fallbacks (no tofu).
    assert sanitize_text("a─b│c") == "a-b|c"


def test_em_dash_disabled_keeps_double_hyphen():
    assert sanitize_text("run --flag now", em_dash=False) == "run --flag now"


def test_strip_markdown_removes_inline_formatting():
    assert strip_markdown("**bold** and *italic* and `code`") == "bold and italic and code"


def test_strip_markdown_link_text_only():
    assert strip_markdown("see [the docs](https://x.y)") == "see the docs"


def test_strip_markdown_checkboxes_become_real_squares():
    # Must be glyphs the bundled serif contains (no \x01 control-char leak).
    assert "■" in strip_markdown("- [x] done")
    assert "□" in strip_markdown("- [ ] todo")
    assert "\x01" not in strip_markdown("- [ ] todo - [x] done")
