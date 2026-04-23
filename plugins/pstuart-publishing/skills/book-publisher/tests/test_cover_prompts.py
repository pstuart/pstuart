"""Tests for prompt builder."""
from templates.lib.cover_prompts import (
    PALETTE_DESCRIPTIONS,
    build_variants,
    build_single_prompt,
)


def test_single_prompt_contains_required_tags():
    p = build_single_prompt(
        surface="wrap",
        genre="leadership",
        composition="weathered mountain range at dawn",
        palette_key="navy_gold",
        mood="authoritative and contemplative",
    )
    assert "no text" in p
    assert "no lettering" in p
    assert "no typography" in p
    assert "300 DPI" in p
    assert "navy" in p.lower()
    assert "mountain" in p.lower()


def test_wrap_variants_include_wildcard():
    variants = build_variants(
        surface="wrap", genre="leadership", palette_key="navy_gold"
    )
    assert len(variants) == 3
    # First two respect palette, third is deliberate wildcard
    assert "navy" in variants[0]["prompt"].lower()
    assert "navy" in variants[1]["prompt"].lower()
    # Wildcard label set
    assert variants[0]["is_wildcard"] is False
    assert variants[1]["is_wildcard"] is False
    assert variants[2]["is_wildcard"] is True


def test_kindle_prompts_specify_portrait_composition():
    variants = build_variants(
        surface="kindle", genre="leadership", palette_key="navy_gold"
    )
    for v in variants:
        assert "portrait" in v["prompt"].lower() or "vertical" in v["prompt"].lower()


def test_motif_prompts_are_landscape_banner():
    variants = build_variants(
        surface="motif", genre="leadership", palette_key="navy_gold"
    )
    for v in variants:
        # Compositions must describe landscape-banner imagery (not portrait).
        assert "banner" in v["prompt"].lower() or "horizontal" in v["prompt"].lower()


def test_unknown_palette_raises():
    import pytest
    with pytest.raises(KeyError):
        build_single_prompt(
            surface="wrap",
            genre="x",
            composition="y",
            palette_key="neon_pink",
            mood="m",
        )


def test_build_variants_with_custom_compositions():
    """Custom compositions override the hardcoded defaults."""
    import pytest
    custom = [
        ("Tudor printshop interior, wide panoramic Elizabethan scene", False),
        ("abstract masked figure, dramatic chiaroscuro", True),
    ]
    variants = build_variants(
        surface="wrap",
        genre="historical thriller",
        palette_key="burgundy_cream",
        compositions=custom,
    )
    assert len(variants) == 2
    # First is on-palette, second is wildcard
    assert "Tudor printshop" in variants[0]["prompt"]
    assert "masked figure" in variants[1]["prompt"]
    assert variants[0]["is_wildcard"] is False
    assert variants[1]["is_wildcard"] is True
    # On-palette variant uses the requested palette
    assert "burgundy" in variants[0]["prompt"].lower()
    # Wildcard uses a different palette — one of the _WILDCARD_PALETTES values
    wc_prompt = variants[1]["prompt"].lower()
    assert any(pal in wc_prompt for pal in ("rust-red", "cobalt", "ochre"))


def test_build_variants_without_compositions_uses_defaults():
    """Omitting compositions param falls back to hardcoded _COMPOSITIONS."""
    variants = build_variants(
        surface="wrap", genre="leadership", palette_key="navy_gold",
    )
    assert len(variants) == 3  # hardcoded default has 3 entries per surface
