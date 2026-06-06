"""Brand configuration: canvas size, fonts, colour palette, defaults."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
OUTPUT = ROOT / "output"

# --- Canvas -----------------------------------------------------------------
# Instagram portrait carousel (4:5) — the most reach-friendly feed format.
WIDTH = 1080
HEIGHT = 1350

# --- Fonts ------------------------------------------------------------------
# Liberation Sans is metric-compatible with Arial/Helvetica — the exact bold
# look used in both reference styles. Ships on the box, so no downloads.
FONT_BOLD = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
FONT_REG = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
FONT_EMOJI = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"

# --- Palette ----------------------------------------------------------------
WHITE = "#FFFFFF"
BLACK = "#000000"
RED = "#E8372B"        # vivid red used for emphasis lines
MUTED = "#7C7C7C"      # grey subtext on dark backgrounds
DARK_BG = "#000000"    # mythos content / outro background

# Tweet-card palette
TW_BG = "#FFFFFF"
TW_TEXT = "#0F1419"
TW_GREY = "#536471"
TW_BLUE = "#1D9BF0"

COLORS = {
    "white": WHITE,
    "black": BLACK,
    "red": RED,
    "muted": MUTED,
    "grey": MUTED,
    "gray": MUTED,
    "blue": TW_BLUE,
    "tw_text": TW_TEXT,
    "tw_grey": TW_GREY,
}

DEFAULT_BRAND = {
    "name": "Fortune University",
    "handle": "@FortuneUniversity",
    "verified": True,
    "avatar": None,          # path to a logo/photo; falls back to a monogram
    "tagline": "New post every week.",
    "monogram_bg": "#11243F",
}


def resolve_color(c, default=WHITE):
    """Map a palette name to hex; pass hex/None through sensibly."""
    if not c:
        return default
    return COLORS.get(c, c)


def resolve_path(p):
    """Resolve an asset path relative to the repo root (absolute passes through)."""
    pp = Path(p)
    return pp if pp.is_absolute() else (ROOT / pp)
