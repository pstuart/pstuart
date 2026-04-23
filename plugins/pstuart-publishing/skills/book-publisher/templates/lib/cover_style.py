"""Cover color palettes with light/dark background variants.

Why split by tone:
- AI-generated cover art is variable: some zgen outputs are cream/parchment
  dominant, others are dark/ink dominant. A single text palette cannot serve
  both: white text on a cream background is invisible.
- Each palette defines two variants:
  - `dark_bg`: light text colors for use over dark-dominant bitmaps
  - `light_bg`: dark text colors for use over light-dominant bitmaps
- BOOK_CONFIG['background_tone'] drives the choice; default is 'light_bg'
  based on real-usage data showing most zgen art is light-dominant.
"""

STYLE_PRESETS = {
    "navy_gold": {
        "dark_bg":  {"title": (255, 255, 255), "body": (240, 240, 240), "accent": (218, 165, 32)},
        "light_bg": {"title": (30, 50, 90),    "body": (50, 60, 80),    "accent": (140, 100, 40)},
    },
    "burgundy_cream": {
        "dark_bg":  {"title": (245, 235, 220), "body": (230, 220, 210), "accent": (200, 170, 100)},
        "light_bg": {"title": (80, 20, 30),    "body": (60, 40, 30),    "accent": (140, 100, 40)},
    },
    "teal_coral": {
        "dark_bg":  {"title": (255, 255, 255), "body": (240, 240, 240), "accent": (255, 127, 102)},
        "light_bg": {"title": (20, 60, 70),    "body": (40, 70, 80),    "accent": (200, 80, 60)},
    },
    "black_silver": {
        "dark_bg":  {"title": (240, 240, 240), "body": (200, 200, 200), "accent": (192, 192, 192)},
        "light_bg": {"title": (20, 20, 20),    "body": (50, 50, 50),    "accent": (100, 100, 100)},
    },
    "earth_warm": {
        "dark_bg":  {"title": (255, 250, 240), "body": (240, 225, 200), "accent": (218, 165, 32)},
        "light_bg": {"title": (60, 40, 20),    "body": (80, 60, 40),    "accent": (150, 100, 40)},
    },
    "purple_gold": {
        "dark_bg":  {"title": (255, 245, 230), "body": (230, 220, 210), "accent": (218, 165, 32)},
        "light_bg": {"title": (60, 30, 80),    "body": (80, 50, 90),    "accent": (150, 100, 40)},
    },
    "forest_cream": {
        "dark_bg":  {"title": (255, 248, 220), "body": (245, 235, 210), "accent": (200, 180, 100)},
        "light_bg": {"title": (30, 60, 40),    "body": (50, 70, 50),    "accent": (120, 100, 50)},
    },
    "minimal_white": {
        # For minimal_white the palette is intrinsically light. On dark backgrounds
        # we use medium-light text to maintain the minimal aesthetic while staying
        # visible; on light backgrounds we use near-black.
        "dark_bg":  {"title": (200, 200, 200), "body": (170, 170, 170), "accent": (140, 140, 140)},
        "light_bg": {"title": (30, 30, 30),    "body": (60, 60, 60),    "accent": (120, 120, 120)},
    },
}

_VALID_TONES = ("light_bg", "dark_bg")


def resolve_colors(preset: str, tone: str = "light_bg") -> dict:
    """Return the {title, body, accent} color dict for the given palette + tone.

    Raises ValueError with a helpful message on unknown preset or tone.
    """
    if preset not in STYLE_PRESETS:
        raise ValueError(
            f"book_config['style_preset']={preset!r} not in STYLE_PRESETS. "
            f"Valid: {sorted(STYLE_PRESETS.keys())}"
        )
    if tone not in _VALID_TONES:
        raise ValueError(
            f"Unknown tone {tone!r}. Valid: {_VALID_TONES}"
        )
    return STYLE_PRESETS[preset][tone]
