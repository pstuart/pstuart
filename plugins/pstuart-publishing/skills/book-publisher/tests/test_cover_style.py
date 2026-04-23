"""Tests for cover style palette resolution."""
import pytest
from templates.lib.cover_style import STYLE_PRESETS, resolve_colors


def test_every_palette_has_both_tone_variants():
    """Every palette must offer both light_bg and dark_bg versions."""
    for name, preset in STYLE_PRESETS.items():
        assert set(preset.keys()) == {"light_bg", "dark_bg"}, \
            f"Palette {name!r} missing a tone variant: {set(preset.keys())}"


def test_every_variant_has_title_body_accent_rgb():
    """Every tone variant has the three color slots."""
    for name, preset in STYLE_PRESETS.items():
        for tone in ("light_bg", "dark_bg"):
            variant = preset[tone]
            assert set(variant.keys()) == {"title", "body", "accent"}, \
                f"{name}[{tone}] missing slot: {set(variant.keys())}"
            for slot, rgb in variant.items():
                assert isinstance(rgb, tuple) and len(rgb) == 3, \
                    f"{name}[{tone}][{slot}] not an (r, g, b) tuple"
                assert all(isinstance(c, int) and 0 <= c <= 255 for c in rgb), \
                    f"{name}[{tone}][{slot}] channels out of range: {rgb}"


def test_light_bg_has_darker_title_than_dark_bg():
    """Sanity check: on light backgrounds, title text should be darker (smaller average RGB)."""
    for name, preset in STYLE_PRESETS.items():
        light_title = preset["light_bg"]["title"]
        dark_title = preset["dark_bg"]["title"]
        light_avg = sum(light_title) / 3
        dark_avg = sum(dark_title) / 3
        assert light_avg < dark_avg, \
            f"{name}: light_bg title should be darker than dark_bg title " \
            f"(got light={light_avg:.0f}, dark={dark_avg:.0f})"


def test_resolve_colors_default_is_light_bg():
    """Omitting tone defaults to light_bg (most AI art is light-dominant)."""
    colors = resolve_colors("navy_gold")
    assert colors == STYLE_PRESETS["navy_gold"]["light_bg"]


def test_resolve_colors_respects_tone():
    dark = resolve_colors("navy_gold", tone="dark_bg")
    light = resolve_colors("navy_gold", tone="light_bg")
    assert dark == STYLE_PRESETS["navy_gold"]["dark_bg"]
    assert light == STYLE_PRESETS["navy_gold"]["light_bg"]
    assert dark != light


def test_resolve_colors_unknown_preset_raises():
    with pytest.raises(ValueError, match="neon_pink"):
        resolve_colors("neon_pink")


def test_resolve_colors_unknown_tone_raises():
    with pytest.raises(ValueError, match="mystery_tone"):
        resolve_colors("navy_gold", tone="mystery_tone")


def test_all_eight_presets_present():
    """Keep the existing palette vocabulary so downstream BOOK_CONFIGs still work."""
    assert set(STYLE_PRESETS.keys()) == {
        "navy_gold", "burgundy_cream", "teal_coral", "black_silver",
        "earth_warm", "purple_gold", "forest_cream", "minimal_white",
    }
