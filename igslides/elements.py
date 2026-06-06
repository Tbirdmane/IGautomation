"""Reusable visual elements: backgrounds, gradients, avatars, verified badge."""

import random

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from . import config, textkit

SERIF_BOLD = "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf"

# Accent colours for the procedural "AI energy core" backdrop.
MOODS = {
    "ember":    {"glow": (232, 55, 43),  "ring": (180, 30, 18)},
    "crimson":  {"glow": (205, 20, 45),  "ring": (120, 10, 28)},
    "electric": {"glow": (46, 155, 232), "ring": (24, 90, 180)},
    "gold":     {"glow": (232, 182, 43), "ring": (150, 110, 20)},
    "violet":   {"glow": (150, 70, 230), "ring": (90, 40, 150)},
}


def _cover(im, w, h):
    """Scale + center-crop an image to exactly fill w x h (preserve mode)."""
    scale = max(w / im.width, h / im.height)
    nw, nh = max(1, int(im.width * scale + 0.5)), max(1, int(im.height * scale + 0.5))
    im = im.resize((nw, nh), Image.LANCZOS)
    left, top = (nw - w) // 2, (nh - h) // 2
    return im.crop((left, top, left + w, top + h))


def cover_image(path, w, h):
    return _cover(Image.open(config.resolve_path(path)).convert("RGB"), w, h)


def bottom_gradient(w, h, start_frac=0.30, max_alpha=235):
    """Transparent at the top fading to near-black at the bottom (text legibility)."""
    col = Image.new("L", (1, h), 0)
    px = col.load()
    span = max(1e-6, 1 - start_frac)
    for y in range(h):
        frac = (y / h - start_frac) / span
        px[0, y] = 0 if frac < 0 else int(min(1.0, frac) ** 1.4 * max_alpha)
    alpha = col.resize((w, h))
    black = Image.new("RGBA", (w, h), (0, 0, 0, 255))
    black.putalpha(alpha)
    return black


def _radial_mask(w, h, center, radius, blur):
    m = Image.new("L", (w, h), 0)
    cx, cy = center
    ImageDraw.Draw(m).ellipse((cx - radius, cy - radius, cx + radius, cy + radius), fill=255)
    return m.filter(ImageFilter.GaussianBlur(blur))


def make_backdrop(w, h, mood="ember"):
    """Cinematic abstract 'AI energy core' on near-black — the procedural
    stand-in for AI hero art on mythos covers. Pick a `mood` for the accent."""
    accent = MOODS.get(mood, MOODS["ember"])
    glow_c, ring_c = accent["glow"], accent["ring"]
    cx, cy = w // 2, int(h * 0.40)
    base = Image.new("RGB", (w, h), "#060608")

    # glowing core
    core = _radial_mask(w, h, (cx, cy), int(w * 0.40), int(w * 0.27))
    core = core.point(lambda v: int(v * 0.72))
    base = Image.composite(Image.new("RGB", (w, h), glow_c), base, core)

    # concentric HUD rings
    rings = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    rd = ImageDraw.Draw(rings)
    for i, rad in enumerate(range(int(w * 0.16), int(w * 0.64), int(w * 0.072))):
        rd.ellipse((cx - rad, cy - rad, cx + rad, cy + rad),
                   outline=ring_c + (max(0, 72 - i * 9),), width=3)
    base = Image.alpha_composite(base.convert("RGBA"),
                                 rings.filter(ImageFilter.GaussianBlur(1.4))).convert("RGB")

    # faint particle field
    parts = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    pd = ImageDraw.Draw(parts)
    rnd = random.Random(7)
    for _ in range(150):
        x, y, r = rnd.randint(0, w), rnd.randint(0, int(h * 0.82)), rnd.choice([1, 1, 2, 3])
        pd.ellipse((x, y, x + r, y + r), fill=(255, 255, 255, rnd.randint(18, 90)))
    base = Image.alpha_composite(base.convert("RGBA"), parts).convert("RGB")

    # vignette (darken corners) + bottom gradient for legibility
    edge = _radial_mask(w, h, (w // 2, h // 2), int(w * 0.72), int(w * 0.35)).point(
        lambda v: int((255 - v) * 0.8))
    base = Image.composite(Image.new("RGB", (w, h), "#000000"), base, edge)
    return Image.alpha_composite(base.convert("RGBA"),
                                 bottom_gradient(w, h, 0.32, 215)).convert("RGB")


def circle_avatar(path, size):
    im = _cover(Image.open(config.resolve_path(path)).convert("RGBA"), size, size)
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, size - 1, size - 1), fill=255)
    im.putalpha(mask)
    return im


def monogram(name, size, bg="#0A1C33", ring="#C9A22B", fg="#E8C45A"):
    """Seal-style fallback avatar: navy disk, gold ring, gold serif initials.
    Used until a real logo is dropped at assets/logo.png."""
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse((0, 0, size - 1, size - 1), fill=bg)
    pad = max(2, int(size * 0.07))
    d.ellipse((pad, pad, size - 1 - pad, size - 1 - pad),
              outline=ring, width=max(2, int(size * 0.035)))
    initials = "".join(w[0] for w in name.split()[:2]).upper() or "FU"
    try:
        f = ImageFont.truetype(SERIF_BOLD, int(size * 0.40))
    except Exception:
        f = textkit.font("bold", int(size * 0.40))
    bbox = d.textbbox((0, 0), initials, font=f)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    d.text(((size - tw) / 2 - bbox[0], (size - th) / 2 - bbox[1]), initials, font=f, fill=fg)
    return im


def get_avatar(brand, size):
    path = brand.get("avatar")
    if path and config.resolve_path(path).exists():
        return circle_avatar(path, size)
    return monogram(brand.get("name", "FU"), size, bg=brand.get("monogram_bg", "#11243F"))


def verified_badge(size, color=config.TW_BLUE):
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse((0, 0, size - 1, size - 1), fill=color)
    pts = [(size * 0.27, size * 0.52), (size * 0.43, size * 0.68), (size * 0.74, size * 0.33)]
    d.line(pts, fill="white", width=max(2, int(size * 0.10)), joint="curve")
    return im
