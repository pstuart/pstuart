"""Tests for the pure detectors in bookpub.qa_report.

These verify the GATE is trustworthy — that it actually flags the defects the
platform review found, and does not false-flag correct output.
"""
from bookpub.qa_report import (
    epub_accessibility,
    find_dash_artifacts,
    is_placeholder_isbn,
    non_embedded_fonts,
    parse_pdffonts,
)

SAMPLE_PDFFONTS = """\
name                                 type              encoding         emb sub uni object ID
------------------------------------ ----------------- ---------------- --- --- --- ---------
ABCDEF+EBGaramond-Regular            CID TrueType      Identity-H       yes yes yes      5  0
Times-Roman                          Type 1            Custom           no  no  no       7  0
GHIJKL+EBGaramond-Italic             CID TrueType      Identity-H       yes yes yes      9  0
"""


def test_parse_pdffonts_handles_multiword_type():
    rows = parse_pdffonts(SAMPLE_PDFFONTS)
    assert len(rows) == 3
    by_name = {r["name"]: r["embedded"] for r in rows}
    assert by_name["ABCDEF+EBGaramond-Regular"] is True
    assert by_name["Times-Roman"] is False  # "Type 1" has a space — parsed correctly
    assert by_name["GHIJKL+EBGaramond-Italic"] is True


def test_non_embedded_fonts_flags_core_times():
    rows = parse_pdffonts(SAMPLE_PDFFONTS)
    assert non_embedded_fonts(rows) == ["Times-Roman"]


def test_non_embedded_empty_when_all_embedded():
    good = "\n".join(SAMPLE_PDFFONTS.splitlines()[:3])  # header+sep+one embedded row
    assert non_embedded_fonts(parse_pdffonts(good)) == []


def test_find_dash_artifacts_spaced_and_unspaced():
    assert find_dash_artifacts("planning your exit -- this is the guide")
    assert find_dash_artifacts("a long word--another word")


def test_find_dash_artifacts_clean_emdash_passes():
    # A correctly rendered em-dash (U+2014) must NOT be flagged.
    assert find_dash_artifacts("planning your exit—this is the guide") == []


def test_find_dash_artifacts_count_respects_limit():
    text = "a--b " * 20
    assert len(find_dash_artifacts(text, limit=5)) == 5


def test_is_placeholder_isbn_detects_common_placeholders():
    assert is_placeholder_isbn("ISBN 978-1-XXXXXX-XX-X")
    assert is_placeholder_isbn("ISBN 000-0-000000-00-0")


def test_is_placeholder_isbn_passes_real_isbn():
    assert is_placeholder_isbn("ISBN 978-1-2345-6789-7") == []


def test_epub_accessibility_detects_present_props():
    opf = (
        '<meta property="schema:accessMode">textual</meta>'
        '<meta property="schema:accessibilitySummary">Fully navigable.</meta>'
    )
    a = epub_accessibility(opf)
    assert a["schema:accessMode"] is True
    assert a["schema:accessibilitySummary"] is True
    assert a["schema:accessibilityHazard"] is False  # absent


def test_epub_accessibility_all_absent():
    a = epub_accessibility("<package><metadata></metadata></package>")
    assert not any(a.values())
