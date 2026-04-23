"""Tests for BOOK_CONFIG schema validator."""
import pytest
from templates.lib.cover_config import (
    validate_and_defaults,
    REQUIRED_KEYS,
    OPTIONAL_DEFAULTS,
)


def _minimal() -> dict:
    """Smallest valid config."""
    return {"title": "T", "author": "A", "page_count": 100}


def test_minimal_config_passes():
    result = validate_and_defaults(_minimal())
    assert result["title"] == "T"
    assert result["author"] == "A"
    assert result["page_count"] == 100


def test_all_optional_fields_get_defaults():
    result = validate_and_defaults(_minimal())
    # A selection of optional fields
    assert result["subtitle"] == ""
    assert result["blurb"] == []
    assert result["author_bio_label"] == "About the Author"
    assert result["style_preset"] == "navy_gold"
    assert result["background_tone"] == "light_bg"
    assert result["paper_type"] == "white"
    assert result["author_photo"] is None


def test_missing_title_raises():
    with pytest.raises(ValueError, match="title"):
        validate_and_defaults({"author": "A", "page_count": 100})


def test_missing_author_raises():
    with pytest.raises(ValueError, match="author"):
        validate_and_defaults({"title": "T", "page_count": 100})


def test_missing_page_count_raises():
    with pytest.raises(ValueError, match="page_count"):
        validate_and_defaults({"title": "T", "author": "A"})


def test_multiple_missing_reported_together():
    """All missing fields should be listed in one error."""
    with pytest.raises(ValueError) as exc_info:
        validate_and_defaults({})
    msg = str(exc_info.value)
    for required in REQUIRED_KEYS:
        assert required in msg, f"missing {required} not reported: {msg}"


def test_page_count_below_24_raises():
    with pytest.raises(ValueError, match="24"):
        validate_and_defaults({"title": "T", "author": "A", "page_count": 10})


def test_page_count_non_int_raises():
    with pytest.raises((TypeError, ValueError)):
        validate_and_defaults({"title": "T", "author": "A", "page_count": "100"})


def test_empty_title_raises():
    with pytest.raises(ValueError, match="title"):
        validate_and_defaults({"title": "", "author": "A", "page_count": 100})


def test_back_body_lines_migrates_to_blurb():
    """Legacy back_body_lines -> new blurb."""
    config = _minimal()
    config["back_body_lines"] = ["Line 1", "", "Line 2"]
    result = validate_and_defaults(config)
    assert result["blurb"] == ["Line 1", "", "Line 2"]
    assert "_migrations" in result
    assert any("back_body_lines" in m for m in result["_migrations"])


def test_explicit_blurb_wins_over_migration():
    """If both blurb and back_body_lines present, blurb wins; migration noted."""
    config = _minimal()
    config["blurb"] = ["Explicit"]
    config["back_body_lines"] = ["Legacy"]
    result = validate_and_defaults(config)
    assert result["blurb"] == ["Explicit"]


def test_unknown_keys_noted_but_not_fatal():
    config = _minimal()
    config["typo_field"] = "whoops"
    result = validate_and_defaults(config)
    assert "_migrations" in result
    assert any("typo_field" in m for m in result["_migrations"])
    # Original fields still present
    assert result["title"] == "T"


def test_non_string_title_raises():
    with pytest.raises(TypeError):
        validate_and_defaults({"title": 123, "author": "A", "page_count": 100})


def test_author_photo_none_is_valid():
    config = _minimal()
    config["author_photo"] = None
    result = validate_and_defaults(config)
    assert result["author_photo"] is None


def test_author_photo_string_path_passes_through():
    config = _minimal()
    config["author_photo"] = "/tmp/photo.png"
    result = validate_and_defaults(config)
    assert result["author_photo"] == "/tmp/photo.png"


def test_blurb_as_list_of_strings_preserved():
    config = _minimal()
    config["blurb"] = ["Para 1.", "", "Para 2."]
    result = validate_and_defaults(config)
    assert result["blurb"] == ["Para 1.", "", "Para 2."]


def test_returned_dict_has_no_required_missing():
    """Sanity: after validation, all required keys are present."""
    result = validate_and_defaults(_minimal())
    for key in REQUIRED_KEYS:
        assert key in result
