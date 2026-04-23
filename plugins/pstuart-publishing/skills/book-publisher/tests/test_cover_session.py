"""Tests for cover-session.json read/write."""
import json
from pathlib import Path
import pytest
from templates.lib.cover_session import (
    CoverSession,
    load_session,
    save_session_atomic,
    SCHEMA_VERSION,
    IncompatibleSchemaError,
)


def test_new_session_has_current_schema(tmp_cover_assets: Path):
    s = CoverSession.new(book_title="Test", style_preset="navy_gold")
    assert s.schema_version == SCHEMA_VERSION
    assert s.book_title == "Test"
    assert s.surfaces == {}


def test_round_trip_preserves_state(tmp_cover_assets: Path):
    s1 = CoverSession.new(book_title="Test", style_preset="navy_gold")
    s1.record_iteration(
        surface="wrap",
        prompt="cinematic mountain",
        seed=4201983,
        approved=False,
    )
    save_session_atomic(s1, tmp_cover_assets / "cover-session.json")

    s2 = load_session(tmp_cover_assets / "cover-session.json")
    assert s2.book_title == s1.book_title
    assert s2.surfaces["wrap"]["history"][0]["seed"] == 4201983
    assert s2.surfaces["wrap"]["history"][0]["approved"] is False


def test_atomic_write_survives_crash(tmp_cover_assets: Path, monkeypatch):
    """Simulate a crash between tmp-write and rename — existing file preserved."""
    target = tmp_cover_assets / "cover-session.json"
    target.write_text(json.dumps({"schema_version": 1, "book_title": "old"}))

    from templates.lib import cover_session as cs
    original_replace = cs.os.replace

    def crash_before_rename(*args, **kwargs):
        raise OSError("simulated crash")

    monkeypatch.setattr(cs.os, "replace", crash_before_rename)

    s = CoverSession.new(book_title="new", style_preset="navy_gold")
    with pytest.raises(OSError):
        save_session_atomic(s, target)

    # Original file content preserved
    assert json.loads(target.read_text())["book_title"] == "old"


def test_incompatible_schema_raises(tmp_cover_assets: Path):
    target = tmp_cover_assets / "cover-session.json"
    target.write_text(json.dumps({"schema_version": 999, "book_title": "future"}))
    with pytest.raises(IncompatibleSchemaError):
        load_session(target)


def test_approve_sets_canonical_fields(tmp_cover_assets: Path):
    s = CoverSession.new(book_title="Test", style_preset="navy_gold")
    s.record_iteration(surface="kindle", prompt="p1", seed=111, approved=True)
    assert s.surfaces["kindle"]["approved_seed"] == 111
    assert s.surfaces["kindle"]["approved_prompt"] == "p1"
