"""Wrapper around the local /Users/pstuart/bin/zgen CLI.

Serial calls only — per user preference, never batch image generation.
Each run_zgen() invocation produces exactly one image or raises.
"""
from pathlib import Path
import shutil
import subprocess

ZGEN_BIN_DEFAULT = "/Users/pstuart/bin/zgen"

# Recommended negative-prompt for book covers — steers the model away from
# the hallucinated text that diffusion models often bake into "painterly" art.
DEFAULT_NEGATIVE_PROMPT = (
    "text, letters, words, writing, calligraphy, script, symbols, runes, "
    "characters, gibberish text, letterforms, alphabet, handwriting, signature, "
    "lorem ipsum"
)


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
    negative_prompt: str | None = None,
) -> Path:
    """Invoke zgen once to produce exactly one image at `output`.

    negative_prompt: optional guidance to steer the model AWAY from specific
    content. Passed to zgen as --negative-prompt, which zgen forwards to
    draw-things-cli. For book-cover art, consider using DEFAULT_NEGATIVE_PROMPT
    to suppress hallucinated text.

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
    if negative_prompt is not None:
        # Must come BEFORE the positional prompt so zgen's arg parser treats
        # it as a flag rather than a second positional arg.
        cmd.extend(["--negative-prompt", negative_prompt])
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
