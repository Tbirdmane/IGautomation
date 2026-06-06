"""Reusable visual elements: backgrounds, gradients, avatars, verified badge."""

from PIL import Image, ImageDraw, ImageFilter

from . import config, textkit


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


def make_backdrop(w, h):
    """A moody ember glow on near-black — stand-in for AI art on mythos covers."""
    base = Image.new("RGB", (w, h), "#070708")
    glow_mask = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(glow_mask)
    cx, cy, r = w // 2, int(h * 0.40), int(w * 0.62)
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=255)
    glow_mask = glow_mask.filter(ImageFilter.GaussianBlur(r * 0.45))
    glow_mask = glow_mask.point(lambda v: int(v * 0.55))
    glow = Image.new("RGB", (w, h), "#7E160C")
    base = Image.composite(glow, base, glow_mask)
    return Image.alpha_composite(base.convert("RGBA"), bottom_gradient(w, h, 0.35, 200)).convert("RGB")


def circle_avatar(path, size):
    im = _cover(Image.open(config.resolve_path(path)).convert("RGBA"), size, size)
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, size - 1, size - 1), fill=255)
    im.putalpha(mask)
    return im


def monogram(name, size, bg="#11243F", fg="#FFFFFF"):
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse((0, 0, size - 1, size - 1), fill=bg)
    initials = "".join(w[0] for w in name.split()[:2]).upper() or "FU"
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
