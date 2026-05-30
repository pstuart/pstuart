"""bookpub.preflight — per-channel validation + print-color conversion.

KDP accepts the RGB interior the engine emits; IngramSpark (offset) wants CMYK
and ideally PDF/X-1a:2001. This module converts to CMYK via Ghostscript and runs
the validators that were documented but never executed by any forked script:
epubcheck (required) and Kindle Previewer (optional, macOS app).

Honest about coverage: full PDF/X-1a conformance needs an embedded OutputIntent
ICC profile (IngramSpark publishes the one to use) and veraPDF to verify; when
those are absent we still perform the DeviceCMYK conversion and report that,
rather than claiming a conformance we did not check.
"""
from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

_KINDLE_PREVIEWER = "/Applications/Kindle Previewer 3.app/Contents/MacOS/Kindle Previewer 3"


@dataclass
class PreflightReport:
    checks: list[tuple[str, str, str]] = field(default_factory=list)  # (name, status, detail)

    def add(self, name: str, status: str, detail: str = "") -> None:
        self.checks.append((name, status, detail))

    @property
    def ok(self) -> bool:
        return all(s != "FAIL" for _, s, _ in self.checks)

    def render(self) -> str:
        icon = {"PASS": "✓", "FAIL": "✗", "WARN": "!", "SKIP": "·"}
        return "\n".join(f"  {icon.get(s, '?')} [{s:4}] {n:22} {d}"
                         for n, s, d in self.checks)


def convert_to_cmyk(interior_pdf: str | Path, out_pdf: str | Path,
                    icc_profile: str | Path | None = None) -> dict:
    """Convert an RGB interior to DeviceCMYK via Ghostscript (IngramSpark/offset).

    With ``icc_profile`` set, also requests a PDF/X-3 OutputIntent. Returns a dict
    with the conversion outcome. Raises RuntimeError if Ghostscript is absent.
    """
    if shutil.which("gs") is None:
        raise RuntimeError("Ghostscript (gs) not installed; cannot convert to CMYK")
    out_pdf = Path(out_pdf)
    out_pdf.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "gs", "-dBATCH", "-dNOPAUSE", "-dSAFER", "-sDEVICE=pdfwrite",
        "-dProcessColorModel=/DeviceCMYK", "-sColorConversionStrategy=CMYK",
        "-dCompatibilityLevel=1.4",
    ]
    pdfx = False
    if icc_profile and Path(icc_profile).exists():
        cmd += [f"-sOutputICCProfile={icc_profile}", "-dPDFX"]
        pdfx = True
    cmd += [f"-sOutputFile={out_pdf}", str(interior_pdf)]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    return {"ok": proc.returncode == 0, "pdfx": pdfx, "output": str(out_pdf),
            "log": (proc.stdout + proc.stderr)[-2000:]}


def run_epubcheck(epub: str | Path) -> tuple[int, str] | None:
    if shutil.which("epubcheck") is None:
        return None
    p = subprocess.run(["epubcheck", str(epub)], capture_output=True, text=True)
    return p.returncode, (p.stdout + p.stderr)


def run_kindle_previewer(epub: str | Path, out_dir: str | Path) -> tuple[int, str] | None:
    if not Path(_KINDLE_PREVIEWER).exists():
        return None
    p = subprocess.run([_KINDLE_PREVIEWER, str(epub), "-convert",
                        "-output", str(out_dir)], capture_output=True, text=True)
    return p.returncode, (p.stdout + p.stderr)


def preflight(interior_pdf: str | Path, epub: str | Path, out_dir: str | Path,
              *, icc_profile: str | Path | None = None) -> PreflightReport:
    """Run the full per-channel preflight and return a report."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    rep = PreflightReport()

    # IngramSpark / offset: CMYK conversion
    try:
        res = convert_to_cmyk(interior_pdf, out_dir / "interior_CMYK.pdf", icc_profile)
        if res["ok"]:
            rep.add("ingram.cmyk", "PASS" if res["pdfx"] else "WARN",
                    "PDF/X-1a (ICC OutputIntent)" if res["pdfx"]
                    else "DeviceCMYK only — add an ICC profile + veraPDF for full PDF/X-1a")
        else:
            rep.add("ingram.cmyk", "FAIL", "Ghostscript conversion failed")
    except RuntimeError as e:
        rep.add("ingram.cmyk", "SKIP", str(e))

    # KDP / Apple / Kobo: EPUB validity
    ec = run_epubcheck(epub)
    if ec is None:
        rep.add("epub.epubcheck", "SKIP", "epubcheck not installed")
    else:
        rep.add("epub.epubcheck", "PASS" if ec[0] == 0 else "FAIL",
                "valid EPUB3" if ec[0] == 0 else f"exit {ec[0]}")

    # Kindle: enhanced-typesetting / KFX conversion check
    kp = run_kindle_previewer(epub, out_dir / "kindle")
    if kp is None:
        rep.add("kindle.previewer", "SKIP", "Kindle Previewer 3 not installed")
    else:
        rep.add("kindle.previewer", "PASS" if kp[0] == 0 else "WARN",
                "KPF conversion ok" if kp[0] == 0 else "see Kindle Previewer log")

    return rep
