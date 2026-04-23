"""Atomic read/write of cover-session.json with schema versioning."""
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
import json
import os
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1


class IncompatibleSchemaError(Exception):
    """Raised when on-disk schema_version exceeds what this code can read."""


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


@dataclass
class CoverSession:
    schema_version: int = SCHEMA_VERSION
    book_title: str = ""
    style_preset: str = ""
    created: str = field(default_factory=_now_iso)
    last_modified: str = field(default_factory=_now_iso)
    surfaces: dict[str, dict[str, Any]] = field(default_factory=dict)

    @classmethod
    def new(cls, book_title: str, style_preset: str) -> "CoverSession":
        return cls(book_title=book_title, style_preset=style_preset)

    def record_iteration(
        self,
        surface: str,
        prompt: str,
        seed: int,
        approved: bool,
        width: int | None = None,
        height: int | None = None,
    ) -> None:
        """Append an iteration to the given surface's history.

        If approved=True, also sets approved_file/seed/prompt canonical fields.
        """
        entry = self.surfaces.setdefault(
            surface,
            {"history": [], "zgen_args": {}},
        )
        entry["history"].append(
            {
                "iteration": len(entry["history"]) + 1,
                "prompt": prompt,
                "seed": seed,
                "approved": approved,
                "timestamp": _now_iso(),
            }
        )
        if width is not None and height is not None:
            entry["zgen_args"] = {"width": width, "height": height}
        if approved:
            entry["approved_prompt"] = prompt
            entry["approved_seed"] = seed
            entry["approved_file"] = f"{surface}_art.png"
        self.last_modified = _now_iso()


def save_session_atomic(session: CoverSession, path: Path) -> None:
    """Write session to path atomically (temp + os.replace).

    If os.replace fails, original file is untouched.
    """
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(asdict(session), indent=2))
    try:
        os.replace(tmp, path)
    except OSError:
        tmp.unlink(missing_ok=True)
        raise


def load_session(path: Path) -> CoverSession:
    """Load session from disk. Raises IncompatibleSchemaError if newer schema."""
    data = json.loads(path.read_text())
    if data.get("schema_version", 0) > SCHEMA_VERSION:
        raise IncompatibleSchemaError(
            f"File schema {data['schema_version']} exceeds supported {SCHEMA_VERSION}"
        )
    return CoverSession(**data)
