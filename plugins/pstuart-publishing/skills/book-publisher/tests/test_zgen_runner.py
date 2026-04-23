"""Tests for zgen subprocess wrapper."""
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest
from templates.lib.zgen_runner import (
    run_zgen,
    ZgenNotFoundError,
    ZgenFailureError,
)


def test_zgen_not_on_path_raises(monkeypatch):
    monkeypatch.setattr("shutil.which", lambda _: None)
    with pytest.raises(ZgenNotFoundError):
        run_zgen(prompt="x", output=Path("/tmp/out.png"), width=832, height=1472, seed=1)


def test_successful_run_returns_path(tmp_path: Path, monkeypatch):
    out = tmp_path / "out.png"
    monkeypatch.setattr("shutil.which", lambda _: "/usr/bin/zgen")

    def fake_run(*args, **kwargs):
        out.write_bytes(b"fake png")
        m = MagicMock()
        m.returncode = 0
        m.stderr = ""
        return m

    monkeypatch.setattr("subprocess.run", fake_run)

    result = run_zgen(prompt="x", output=out, width=832, height=1472, seed=1)
    assert result == out
    assert result.exists()


def test_nonzero_returncode_raises_with_stderr(tmp_path: Path, monkeypatch):
    monkeypatch.setattr("shutil.which", lambda _: "/usr/bin/zgen")

    def fake_run(*args, **kwargs):
        m = MagicMock()
        m.returncode = 1
        m.stderr = "model load failed"
        return m

    monkeypatch.setattr("subprocess.run", fake_run)

    with pytest.raises(ZgenFailureError, match="model load failed"):
        run_zgen(
            prompt="x", output=tmp_path / "out.png",
            width=832, height=1472, seed=1,
        )


def test_missing_output_file_raises(tmp_path: Path, monkeypatch):
    """zgen returns 0 but produces no file — should raise."""
    monkeypatch.setattr("shutil.which", lambda _: "/usr/bin/zgen")

    def fake_run(*args, **kwargs):
        m = MagicMock()
        m.returncode = 0
        m.stderr = ""
        return m

    monkeypatch.setattr("subprocess.run", fake_run)

    with pytest.raises(ZgenFailureError, match="did not produce output"):
        run_zgen(
            prompt="x", output=tmp_path / "missing.png",
            width=832, height=1472, seed=1,
        )
