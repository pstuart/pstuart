"""Wrapper around the local /Users/pstuart/bin/zgen CLI.

Serial calls only — per user preference, never batch image generation.
Each run_zgen() invocation produces exactly one image or raises.
"""
from pathlib import Path
import shutil
import subprocess

ZGEN_BIN_DEFAULT = "/Users/pstuart/bin/zgen"


class ZgenNotFoundError(RuntimeError):
    """zgen binary missing from PATH."""


class ZgenFailureError(RuntimeError):
    """zgen returned non-zero or produced no output file."""


def _ensure_multiple_of_64(value: int, name: str) -> int:
    if value % 64 != 0:
        raise ValueError(f"{name}={value} must be a multiple of 64 for zgen")
    return value


def run_zgen(
    prompt: str,
    output: Path,
    width: int,
    height: int,
    seed: int,
    steps: int | None = None,
    bin_path: str = ZGEN_BIN_DEFAULT,
) -> Path:
    """Invoke zgen once to produce exactly one image at `output`.

    Raises ZgenNotFoundError or ZgenFailureError on any problem.
    """
    if shutil.which(bin_path) is None:
        raise ZgenNotFoundError(
            f"zgen not found at {bin_path!r}. "
            "This skill requires the local Draw Things CLI wrapper. "
            "See ~/.claude/projects/-Users-pstuart-Development/memory/"
            "feedback_image_generation_zchat.md"
        )

    _ensure_multiple_of_64(width, "width")
    _ensure_multiple_of_64(height, "height")

    output.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        bin_path,
        "-W", str(width),
        "-H", str(height),
        "-s", str(seed),
        "-o", str(output),
    ]
    if steps is not None:
        cmd.extend(["-S", str(steps)])
    cmd.append(prompt)

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise ZgenFailureError(
            f"zgen exited {result.returncode}: {result.stderr.strip()}"
        )
    if not output.exists():
        raise ZgenFailureError(
            f"zgen returned 0 but did not produce output file {output}"
        )
    return output
