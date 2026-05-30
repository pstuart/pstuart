"""Tests for bookpub.screenplay — theatrical renderer."""
from pypdf import PdfReader

from bookpub.qa_report import _count_outline
from bookpub.screenplay import build_screenplay, clean_source, parse_screenplay

SCRIPT = """\
---
title: "The Late Night Miracle"
---
\\newpage
# THE LATE NIGHT MIRACLE
## A Production
**CAST OF CHARACTERS**
JACK STERLING \\- host
# **NIGHT ONE \\- DECEMBER 22**
## **SCENE 1: COLD OPEN**

**\\[LIGHTS: Full house lights down\\]**

*JACK STERLING bounds out from backstage.*

**JACK**
*(working the crowd)*
Hey hey hey\\! Welcome to the show\\!

## **SCENE 2: INTERVIEW**

**MARCUS**
Good to be here.
"""


def test_clean_source_unescapes_and_strips():
    out = clean_source(SCRIPT)
    assert "---\ntitle" not in out          # YAML stripped
    assert "\\newpage" not in out           # LaTeX stripped
    assert "DECEMBER 22" in out and "\\-" not in out  # \- unescaped
    assert "Welcome to the show!" in out    # \! unescaped


def test_parse_classifies_blocks():
    els = parse_screenplay(SCRIPT)
    kinds = [e["kind"] for e in els]
    assert kinds == ["act", "scene", "scene"]
    assert els[0]["title"].startswith("NIGHT ONE")
    s1 = els[1]["blocks"]
    types = [b["t"] for b in s1]
    assert "tech" in types and "stage" in types and "char" in types
    char = next(b for b in s1 if b["t"] == "char")
    assert char["name"] == "JACK"
    assert any("paren" in x for x in char["speech"])
    assert any(x.get("line", "").startswith("Hey hey hey") for x in char["speech"])


def test_technical_cue_text_extracted():
    s1 = parse_screenplay(SCRIPT)[1]["blocks"]
    tech = next(b for b in s1 if b["t"] == "tech")
    assert "LIGHTS" in tech["text"]


def test_build_screenplay(tmp_path):
    out = tmp_path / "script.pdf"
    stats = build_screenplay({"title": "The Late Night Miracle", "author": "Patrick Stuart",
                              "year": "2026", "style_preset": "black_silver"}, SCRIPT, out)
    assert stats["acts"] == 1 and stats["scenes"] == 2
    reader = PdfReader(str(out))
    assert _count_outline(reader.outline) >= 3  # act + 2 scenes
