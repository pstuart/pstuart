"""Prompt builder for zgen cover art.

Generates 3 variants per surface: 2 on-palette (different compositions)
+ 1 deliberate wildcard that breaks the palette to surface unexpected options.
"""
from typing import TypedDict

# Palette → descriptor string injected into prompts.
PALETTE_DESCRIPTIONS = {
    "navy_gold": "deep navy and warm gold palette, authoritative mood",
    "burgundy_cream": "burgundy and cream palette, literary mood",
    "teal_coral": "teal and coral palette, modern fresh mood",
    "black_silver": "black and silver palette, dramatic mood",
    "earth_warm": "warm earth tones, grounded spiritual mood",
    "purple_gold": "deep purple and gold palette, transformative luxurious mood",
    "forest_cream": "forest green and cream palette, natural wise mood",
    "minimal_white": "minimal white palette with single accent, clean modern mood",
}

# Compositions per surface. Each surface has (on-palette-1, on-palette-2, wildcard).
_COMPOSITIONS = {
    "wrap": [
        ("weathered mountain range at dawn, solitary figure silhouette far-left third", False),
        ("becalmed ocean at twilight, distant lighthouse on right third", False),
        ("rust-red canyon at golden hour, warm copper tones with deep shadow", True),
    ],
    "kindle": [
        ("single weathered mountain peak centered lower-third, portrait composition", False),
        ("vertical forest path receding into mist, portrait composition", False),
        ("abstract geometric mandala, vertical symmetry, portrait composition", True),
    ],
    "motif": [
        ("minimalist geometric mountain silhouette, lots of negative space, suitable for text overlay in bottom third", False),
        ("simple flowing line-art wave pattern, lots of negative space, suitable for text overlay in bottom third", False),
        ("intricate botanical line drawing, lots of negative space, suitable for text overlay in bottom third", True),
    ],
}

_SURFACE_TAGS = {
    "wrap": "cinematic landscape book-cover art, wide panoramic composition",
    "kindle": "cinematic portrait book-cover art",
    "motif": "abstract chapter-opener motif",
}


class PromptVariant(TypedDict):
    prompt: str
    composition: str
    is_wildcard: bool


_WILDCARD_PALETTES = [
    "rust-red and deep ember palette",
    "cobalt and acid-green palette",
    "ochre and charcoal palette",
]


def build_single_prompt(
    surface: str,
    genre: str,
    composition: str,
    palette_key: str,
    mood: str,
    wildcard_palette: str | None = None,
) -> str:
    """Assemble a single zgen prompt from slotted pieces."""
    if wildcard_palette is not None:
        palette_desc = wildcard_palette
    else:
        palette_desc = PALETTE_DESCRIPTIONS[palette_key]
    surface_tag = _SURFACE_TAGS[surface]
    return (
        f"{surface_tag}, {genre} book, {composition}, {palette_desc}, {mood}, "
        "no text, no lettering, no typography, "
        "composition tolerates print bleed, 300 DPI print quality, painterly finish"
    )


def build_variants(
    surface: str,
    genre: str,
    palette_key: str,
    mood: str = "evocative",
) -> list[PromptVariant]:
    """Build 3 prompt variants for a surface: 2 on-palette + 1 wildcard."""
    if palette_key not in PALETTE_DESCRIPTIONS:
        raise KeyError(f"Unknown palette_key {palette_key!r}")

    compositions = _COMPOSITIONS[surface]
    variants: list[PromptVariant] = []
    wildcard_idx = 0

    for composition, is_wildcard in compositions:
        if is_wildcard:
            wildcard_palette = _WILDCARD_PALETTES[wildcard_idx % len(_WILDCARD_PALETTES)]
            wildcard_idx += 1
            prompt = build_single_prompt(
                surface=surface,
                genre=genre,
                composition=composition,
                palette_key=palette_key,
                mood=mood,
                wildcard_palette=wildcard_palette,
            )
        else:
            prompt = build_single_prompt(
                surface=surface,
                genre=genre,
                composition=composition,
                palette_key=palette_key,
                mood=mood,
            )
        variants.append(
            {"prompt": prompt, "composition": composition, "is_wildcard": is_wildcard}
        )

    return variants
