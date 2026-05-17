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


# ---- Negative prompt tests (added in T17) ----

def test_negative_prompt_appears_in_argv(tmp_path: Path, monkeypatch):
    """run_zgen must pass --negative-prompt to the subprocess when given."""
    captured_cmds = []

    def fake_run(cmd, **kwargs):
        captured_cmds.append(cmd)
        # Simulate success + output file
        (tmp_path / "out.png").write_bytes(b"fake")
        m = MagicMock()
        m.returncode = 0
        m.stderr = ""
        return m

    monkeypatch.setattr("shutil.which", lambda _: "/usr/bin/zgen")
    monkeypatch.setattr("subprocess.run", fake_run)

    run_zgen(
        prompt="test prompt",
        output=tmp_path / "out.png",
        width=832, height=1472, seed=1,
        negative_prompt="bad text, bad content",
    )

    assert len(captured_cmds) == 1
    cmd = captured_cmds[0]
    assert "--negative-prompt" in cmd
    # The value must come directly after --negative-prompt
    neg_idx = cmd.index("--negative-prompt")
    assert cmd[neg_idx + 1] == "bad text, bad content"
    # And --negative-prompt must come BEFORE the positional prompt (which is last)
    assert cmd[-1] == "test prompt"
    assert neg_idx < cmd.index("test prompt")


def test_negative_prompt_omitted_by_default(tmp_path: Path, monkeypatch):
    """When negative_prompt is None, no --negative-prompt appears in argv."""
    captured_cmds = []

    def fake_run(cmd, **kwargs):
        captured_cmds.append(cmd)
        (tmp_path / "out.png").write_bytes(b"fake")
        m = MagicMock()
        m.returncode = 0
        m.stderr = ""
        return m

    monkeypatch.setattr("shutil.which", lambda _: "/usr/bin/zgen")
    monkeypatch.setattr("subprocess.run", fake_run)

    run_zgen(prompt="test", output=tmp_path / "out.png", width=832, height=1472, seed=1)

    assert "--negative-prompt" not in captured_cmds[0]


def test_default_negative_prompt_exports():
    """DEFAULT_NEGATIVE_PROMPT is importable and non-empty."""
    from templates.lib.zgen_runner import DEFAULT_NEGATIVE_PROMPT
    assert isinstance(DEFAULT_NEGATIVE_PROMPT, str)
    assert "text" in DEFAULT_NEGATIVE_PROMPT
    assert "letters" in DEFAULT_NEGATIVE_PROMPT
    assert len(DEFAULT_NEGATIVE_PROMPT) > 20
