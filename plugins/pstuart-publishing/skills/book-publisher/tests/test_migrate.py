"""Tests for bookpub.migrate — book.toml scaffolding round-trips through config."""
import tomllib

from bookpub.config import load_book_config
from bookpub.migrate import discover_manuscript_files, render_book_toml, scaffold


def test_discover_manuscript_files(tmp_path):
    md = tmp_path / "manuscript"
    md.mkdir()
    (md / "02-b.md").write_text("x")
    (md / "01-a.md").write_text("x")
    assert discover_manuscript_files(tmp_path) == ["01-a.md", "02-b.md"]


def test_render_book_toml_is_parseable():
    meta = {"title": "T", "author": "A", "year": "2026", "style_preset": "navy_gold",
            "index_terms": ["x", "y"], "isbn": {"paperback": "978-1-2345-6789-7"}}
    toml = render_book_toml(meta, ["01.md", "02.md"])
    cfg = tomllib.loads(toml)
    assert cfg["title"] == "T"
    assert cfg["file_order"] == ["01.md", "02.md"]
    assert cfg["index_terms"] == ["x", "y"]
    assert cfg["isbn"]["paperback"] == "978-1-2345-6789-7"


def test_scaffold_writes_toml_and_shim(tmp_path):
    (tmp_path / "manuscript").mkdir()
    (tmp_path / "manuscript" / "01-intro.md").write_text("# CHAPTER 1\n## Hi\n\nBody.\n")
    res = scaffold(tmp_path, {"title": "T", "author": "A"})
    assert res["created"] and res["n_chapters"] == 1
    # the written book.toml validates through the real loader
    cfg = load_book_config(tmp_path / "book.toml")
    assert cfg["title"] == "T"
    assert (tmp_path / "publishing" / "generate.py").exists()


def test_scaffold_does_not_overwrite_existing(tmp_path):
    (tmp_path / "book.toml").write_text('title="Keep"\nauthor="Me"\n')
    res = scaffold(tmp_path, {"title": "New", "author": "Other"}, write_shim=False)
    assert res["created"] is False
    assert 'Keep' in (tmp_path / "book.toml").read_text()
