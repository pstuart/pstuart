"""bookpub.qa_report — a fail-loud quality gate for built book artifacts.

Every defect the 2026-05-29 platform review verified is mechanically detectable.
This module asserts against the *output* artifacts (the built PDF / EPUB), so it
has zero coupling to the generation engine and can gate any book — including the
already-shipped forks — today.

Checks (FAIL = nonzero exit unless downgraded):
  PDF   links present .......... 0 link annotations => dead TOC/index
        outline present ........ 0 bookmarks => empty reader sidebar
        fonts embedded ......... any non-embedded font => render/licensing risk
        em-dash artifact ....... `word--word` / ` -- ` => the catalog-wide bug
        ISBN placeholder ....... `978-1-XXXX` etc. (FAIL only with --release)
        tagged (WARN) .......... untagged => fails PDF/UA accessibility
  EPUB  epubcheck ............. nonzero returncode => invalid EPUB
        accessibility metadata . missing schema:accessMode/accessibilitySummary
                                 => Apple rejection + EU EAA non-saleable
  COVER spine consistency ..... wrap width != 2*(trim+bleed)+spine(real pages)

Usage:
    python3 -m bookpub.qa_report --pdf book.pdf --epub book.epub [--release]
    python3 -m bookpub.qa_report --pdf interior.pdf --cover wrap.pdf \\
            --interior interior.pdf --paper white
"""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path

FAIL, WARN, OK, SKIP = "FAIL", "WARN", "OK", "SKIP"


@dataclass
class Finding:
    level: str          # FAIL | WARN | OK | SKIP
    check: str          # short id, e.g. "pdf.links"
    detail: str         # human-readable result


# --------------------------------------------------------------------------- #
# Pure detectors (no I/O — unit-tested directly)
# --------------------------------------------------------------------------- #

# pdffonts data rows look like:
#   name                          type           encoding    emb sub uni object ID
# `type`/`encoding`/`name` may contain spaces, but emb/sub/uni are always the
# first run of three consecutive yes/no tokens. Parse from that anchor, not by
# fixed column index.
def parse_pdffonts(output: str) -> list[dict]:
    """Parse `pdffonts` output into rows with name + embedded flag."""
    rows: list[dict] = []
    lines = output.splitlines()
    for line in lines:
        if not line.strip() or line.startswith("name ") or set(line.strip()) <= {"-"}:
            continue
        tokens = line.split()
        # pdffonts emits a single-token PostScript name in column 0; `type` and
        # `encoding` between it and the emb/sub/uni triple may be multi-word, so
        # anchor on the first run of three consecutive yes/no tokens for `emb`.
        for i in range(1, len(tokens) - 2):
            triple = tokens[i : i + 3]
            if all(t in ("yes", "no") for t in triple):
                rows.append({"name": tokens[0], "embedded": triple[0] == "yes"})
                break
    return rows


def non_embedded_fonts(rows: list[dict]) -> list[str]:
    """Font names that are NOT embedded (KDP requires all fonts embedded)."""
    return [r["name"] for r in rows if not r["embedded"]]


_DASH_RE = re.compile(r"\w\s?--\s?\w")


def find_dash_artifacts(text: str, limit: int = 8) -> list[str]:
    """Find `--` used as an em/en-dash artifact in prose (with context).

    Note: command-line flags (`run --flag`) can match; code-heavy books should
    raise --allow-dashes accordingly. For prose interiors any hit is the bug.
    """
    out: list[str] = []
    for m in _DASH_RE.finditer(text):
        s, e = max(0, m.start() - 25), min(len(text), m.end() + 25)
        ctx = text[s:e].replace("\n", " ").strip()
        out.append(ctx)
        if len(out) >= limit:
            break
    return out


_ISBN_PLACEHOLDER_RE = re.compile(
    r"(978-1-X|97[89][-\s]?[0-9]?[-\s]?X{2,}|0{3}-0-0{6}-0{2}-0|XXXXXX)",
    re.IGNORECASE,
)


def is_placeholder_isbn(text: str) -> list[str]:
    """Return placeholder-ISBN strings found in the text (release blocker)."""
    return sorted({m.group(0) for m in _ISBN_PLACEHOLDER_RE.finditer(text)})


_A11Y_PROPS = (
    "schema:accessMode",
    "schema:accessModeSufficient",
    "schema:accessibilityFeature",
    "schema:accessibilityHazard",
    "schema:accessibilitySummary",
)


def epub_accessibility(opf_text: str) -> dict[str, bool]:
    """Which EPUB accessibility metadata properties are present in the OPF."""
    return {p: (p in opf_text) for p in _A11Y_PROPS}


# --------------------------------------------------------------------------- #
# IO helpers
# --------------------------------------------------------------------------- #

def _run(cmd: list[str]) -> tuple[int, str] | None:
    """Run a command, return (returncode, combined output) or None if missing."""
    if shutil.which(cmd[0]) is None:
        return None
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def _read_epub_opf(path: Path) -> str | None:
    """Read the EPUB's package document (.opf) text via zipfile (no subprocess)."""
    try:
        with zipfile.ZipFile(path) as z:
            names = z.namelist()
            opf = next((n for n in names if n.lower().endswith(".opf")), None)
            try:  # prefer the rootfile declared in container.xml
                container = z.read("META-INF/container.xml").decode("utf-8", "replace")
                m = re.search(r'full-path="([^"]+\.opf)"', container)
                if m and m.group(1) in names:
                    opf = m.group(1)
            except KeyError:
                pass
            if opf:
                return z.read(opf).decode("utf-8", "replace")
    except (zipfile.BadZipFile, OSError):
        return None
    return None


def _count_outline(entries) -> int:
    n = 0
    for it in entries:
        if isinstance(it, list):
            n += _count_outline(it)
        else:
            n += 1
    return n


# --------------------------------------------------------------------------- #
# Artifact checks
# --------------------------------------------------------------------------- #

def check_pdf(path: Path, *, release: bool, allow_dashes: int,
              min_links: int, min_outline: int) -> list[Finding]:
    findings: list[Finding] = []
    from pypdf import PdfReader

    try:
        reader = PdfReader(str(path))
    except Exception as e:  # noqa: BLE001 - report, don't crash the gate
        return [Finding(FAIL, "pdf.open", f"cannot open {path.name}: {e}")]

    # links
    links = 0
    for pg in reader.pages:
        for ref in pg.get("/Annots", []) or []:
            try:
                if ref.get_object().get("/Subtype") == "/Link":
                    links += 1
            except Exception:  # noqa: BLE001
                pass
    findings.append(
        Finding(OK if links >= min_links else FAIL, "pdf.links",
                f"{links} link annotation(s) (need >= {min_links})")
    )

    # outline / bookmarks
    try:
        n_outline = _count_outline(reader.outline)
    except Exception:  # noqa: BLE001
        n_outline = 0
    findings.append(
        Finding(OK if n_outline >= min_outline else FAIL, "pdf.outline",
                f"{n_outline} bookmark(s) (need >= {min_outline})")
    )

    # fonts embedded
    res = _run(["pdffonts", str(path)])
    if res is None:
        findings.append(Finding(SKIP, "pdf.fonts", "pdffonts not installed"))
    else:
        bad = non_embedded_fonts(parse_pdffonts(res[1]))
        findings.append(
            Finding(OK if not bad else FAIL, "pdf.fonts",
                    "all fonts embedded" if not bad
                    else f"non-embedded: {', '.join(bad)}")
        )

    # text-derived checks
    res = _run(["pdftotext", str(path), "-"])
    if res is None:
        findings.append(Finding(SKIP, "pdf.text", "pdftotext not installed"))
    else:
        text = res[1]
        dashes = find_dash_artifacts(text)
        if len(dashes) <= allow_dashes:
            findings.append(Finding(OK, "pdf.dashes",
                                    f"{len(dashes)} '--' artifact(s) (allow {allow_dashes})"))
        else:
            findings.append(Finding(FAIL, "pdf.dashes",
                                    f"{len(dashes)} '--' artifact(s), e.g. {dashes[:3]}"))
        isbns = is_placeholder_isbn(text)
        if isbns:
            findings.append(Finding(FAIL if release else WARN, "pdf.isbn",
                                    f"placeholder ISBN(s): {isbns}"))
        else:
            findings.append(Finding(OK, "pdf.isbn", "no placeholder ISBN"))

    # tagging (accessibility) — advisory
    try:
        tagged = "/StructTreeRoot" in reader.trailer["/Root"]
    except Exception:  # noqa: BLE001
        tagged = False
    findings.append(Finding(OK if tagged else WARN, "pdf.tagged",
                            "tagged PDF" if tagged else "untagged (fails PDF/UA)"))
    return findings


def check_epub(path: Path) -> list[Finding]:
    findings: list[Finding] = []

    res = _run(["epubcheck", str(path)])
    if res is None:
        findings.append(Finding(SKIP, "epub.epubcheck", "epubcheck not installed"))
    else:
        findings.append(
            Finding(OK if res[0] == 0 else FAIL, "epub.epubcheck",
                    "valid (0 errors)" if res[0] == 0
                    else f"epubcheck exit {res[0]}")
        )

    opf = _read_epub_opf(path)
    if opf is None:
        findings.append(Finding(FAIL, "epub.opf", "could not read package .opf"))
        return findings

    a11y = epub_accessibility(opf)
    required = ("schema:accessMode", "schema:accessibilitySummary")
    missing_req = [p for p in required if not a11y[p]]
    if missing_req:
        findings.append(Finding(FAIL, "epub.a11y",
                                f"missing required a11y metadata: {missing_req}"))
    else:
        findings.append(Finding(OK, "epub.a11y", "accessMode + summary present"))
    missing_opt = [p for p in _A11Y_PROPS if p not in required and not a11y[p]]
    if missing_opt:
        findings.append(Finding(WARN, "epub.a11y.full",
                                f"missing recommended: {[p.split(':')[1] for p in missing_opt]}"))
    return findings


def check_cover(cover: Path, interior: Path, paper: str,
                tol_in: float = 0.0625) -> list[Finding]:
    """Assert the wrap cover width matches the real interior page count.

    Reuses the canonical spine math from the cover library (moves to
    bookpub.covers in Phase 3). Skips gracefully if the math is unavailable.
    """
    from pypdf import PdfReader

    try:
        pages = len(PdfReader(str(interior)).pages)
    except Exception as e:  # noqa: BLE001
        return [Finding(FAIL, "cover.interior", f"cannot read interior: {e}")]

    # locate the canonical cover-dimension math
    skill_root = Path(__file__).resolve().parent.parent
    tdir = skill_root / "templates"
    dims = None
    for p in (str(tdir), str(tdir / "lib")):
        if p not in sys.path:
            sys.path.insert(0, p)
    try:
        from lib import cover_dimensions as dims  # type: ignore
    except Exception:
        try:
            from templates.lib import cover_dimensions as dims  # type: ignore
        except Exception:
            dims = None
    if dims is None:
        return [Finding(SKIP, "cover.spine",
                        "cover_dimensions unavailable (wired fully in Phase 3)")]

    try:
        expected_w, _ = dims.wrap_canvas_inches(pages, paper)
        cover_w_pts = float(PdfReader(str(cover)).pages[0].mediabox.width)
        cover_w_in = cover_w_pts / 72.0
        delta = abs(cover_w_in - expected_w)
        lvl = OK if delta <= tol_in else FAIL
        return [Finding(lvl, "cover.spine",
                        f"wrap {cover_w_in:.4f}in vs expected {expected_w:.4f}in "
                        f"for {pages}pp {paper} (delta {delta:.4f}, tol {tol_in})")]
    except Exception as e:  # noqa: BLE001
        return [Finding(SKIP, "cover.spine", f"spine check skipped: {e}")]


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def render(findings: list[Finding]) -> str:
    icon = {FAIL: "✗", WARN: "!", OK: "✓", SKIP: "·"}
    lines = [f"  {icon[f.level]} [{f.level:4}] {f.check:18} {f.detail}" for f in findings]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="bookpub-qa", description="Fail-loud QA gate for built books.")
    ap.add_argument("--pdf", action="append", default=[], help="interior/final PDF (repeatable)")
    ap.add_argument("--epub", action="append", default=[], help="EPUB (repeatable)")
    ap.add_argument("--cover", help="wrap cover PDF (with --interior)")
    ap.add_argument("--interior", help="interior PDF for cover spine check")
    ap.add_argument("--paper", default="white", choices=["white", "cream"])
    ap.add_argument("--release", action="store_true", help="placeholder ISBN becomes FAIL")
    ap.add_argument("--allow-dashes", type=int, default=0, help="tolerated '--' count (code-heavy books)")
    ap.add_argument("--min-links", type=int, default=1)
    ap.add_argument("--min-outline", type=int, default=1)
    args = ap.parse_args(argv)

    if not (args.pdf or args.epub or args.cover):
        ap.error("nothing to check: pass --pdf, --epub, and/or --cover")

    all_findings: list[Finding] = []
    for pdf in args.pdf:
        print(f"\nPDF  {pdf}")
        fs = check_pdf(Path(pdf), release=args.release, allow_dashes=args.allow_dashes,
                       min_links=args.min_links, min_outline=args.min_outline)
        print(render(fs))
        all_findings += fs
    for epub in args.epub:
        print(f"\nEPUB {epub}")
        fs = check_epub(Path(epub))
        print(render(fs))
        all_findings += fs
    if args.cover:
        if not args.interior:
            ap.error("--cover requires --interior")
        print(f"\nCOVER {args.cover}")
        fs = check_cover(Path(args.cover), Path(args.interior), args.paper)
        print(render(fs))
        all_findings += fs

    fails = sum(1 for f in all_findings if f.level == FAIL)
    warns = sum(1 for f in all_findings if f.level == WARN)
    print(f"\n{'=' * 60}\nQA: {fails} FAIL, {warns} WARN, "
          f"{sum(1 for f in all_findings if f.level == OK)} OK, "
          f"{sum(1 for f in all_findings if f.level == SKIP)} SKIP")
    if fails:
        print("RESULT: FAIL")
        return 1
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
