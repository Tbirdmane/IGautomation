"""The two slide styles: mythos (flashy) and twitter (tweet card)."""

from PIL import Image, ImageDraw

from . import config, elements, textkit


def _size(content):
    w, h = content.get("size", [config.WIDTH, config.HEIGHT])
    return int(w), int(h)


def _brand(content):
    return {**config.DEFAULT_BRAND, **content.get("brand", {})}


def _paste_emoji(img, ch, center_xy, px):
    em = textkit.render_emoji(ch, px)
    if em is None:
        return
    x = int(center_xy[0] - em.width / 2)
    y = int(center_xy[1] - em.height / 2)
    img.paste(em, (x, y), em)


# ---------------------------------------------------------------- MYTHOS -----
def render_mythos(content):
    W, H = _size(content)
    brand = _brand(content)
    imgs = []

    for slide in content["slides"]:
        variant = slide.get("variant", "content")
        margin = 84

        if variant == "cover":
            bg = slide.get("background")
            if bg and bg != "auto":
                img = elements.cover_image(bg, W, H)
                img = Image.alpha_composite(
                    img.convert("RGBA"), elements.bottom_gradient(W, H)
                ).convert("RGB")
            else:
                img = elements.make_backdrop(W, H, slide.get("mood", "ember"))
            textkit.draw_lines(
                img, slide["lines"], box=(margin, 0, W - 2 * margin, H - 230),
                align="center", valign="bottom", max_size=104, min_size=46, leading=0.96,
            )
            if slide.get("hint"):
                textkit.draw_centered(img, slide["hint"], y=H - 150,
                                      color=config.MUTED, size=30)

        elif variant == "outro":
            img = Image.new("RGB", (W, H), config.DARK_BG)
            _, y_end, _ = textkit.draw_lines(
                img, slide["lines"], box=(margin, 0, W - 2 * margin, int(H * 0.66)),
                align="center", valign="center", max_size=104, min_size=46, leading=1.0,
            )
            y = y_end + 46
            y = textkit.draw_centered(img, slide.get("handle", brand["handle"]),
                                      y=y, color=config.MUTED, size=40)
            tagline = slide.get("tagline", brand.get("tagline"))
            if tagline:
                textkit.draw_centered(img, tagline, y=y + 12, color=config.MUTED, size=32,
                                      weight="regular")

        else:  # content
            img = Image.new("RGB", (W, H), config.DARK_BG)
            has_sub = bool(slide.get("subtext"))
            box_h = int(H * 0.74) if has_sub else H
            _, y_end, _ = textkit.draw_lines(
                img, slide["lines"], box=(margin, 0, W - 2 * margin, box_h),
                align="center", valign="center", max_size=100, min_size=40, leading=1.0,
            )
            if has_sub:
                textkit.draw_centered(img, slide["subtext"], y=y_end + 40,
                                      color=config.MUTED, size=32, weight="regular")

        imgs.append(img)
    return imgs


# --------------------------------------------------------------- TWITTER -----
def _brand_row_left(img, brand, x, y, av=92):
    draw = ImageDraw.Draw(img)
    avatar = elements.get_avatar(brand, av)
    img.paste(avatar, (x, y), avatar)
    tx = x + av + 22
    nf = textkit.font("bold", 40)
    name = brand["name"]
    draw.text((tx, y + 4), name, font=nf, fill=config.TW_TEXT)
    nw = textkit.text_w(draw, name, nf)
    if brand.get("verified"):
        badge = elements.verified_badge(36)
        img.paste(badge, (int(tx + nw + 12), int(y + 8)), badge)
    hf = textkit.font("regular", 34)
    draw.text((tx, y + 4 + textkit.line_height(nf) - 4), brand["handle"],
              font=hf, fill=config.TW_GREY)
    return y + av


def _brand_row_centered(img, brand, y, av=72, on_dark=True):
    draw = ImageDraw.Draw(img)
    nf = textkit.font("bold", 40)
    name = brand["name"]
    nw = textkit.text_w(draw, name, nf)
    badge_w = 36 if brand.get("verified") else 0
    gap_badge = 12 if badge_w else 0
    group_w = av + 18 + nw + gap_badge + badge_w
    sx = (img.width - group_w) / 2

    avatar = elements.get_avatar(brand, av)
    img.paste(avatar, (int(sx), int(y)), avatar)
    tx = sx + av + 18
    name_color = config.WHITE if on_dark else config.TW_TEXT
    draw.text((tx, y + (av - textkit.line_height(nf)) / 2 + 4), name, font=nf, fill=name_color)
    if badge_w:
        badge = elements.verified_badge(badge_w)
        img.paste(badge, (int(tx + nw + gap_badge), int(y + (av - badge_w) / 2)), badge)
    hf = textkit.font("regular", 32)
    hw = textkit.text_w(draw, brand["handle"], hf)
    draw.text(((img.width - hw) / 2, y + av + 10), brand["handle"],
              font=hf, fill=config.MUTED if on_dark else config.TW_GREY)
    return y + av + 10 + textkit.line_height(hf)


def render_twitter(content):
    W, H = _size(content)
    brand = _brand(content)
    imgs = []

    for slide in content["slides"]:
        variant = slide.get("variant", "tweet")

        if variant in ("cover", "outro"):
            img = Image.new("RGB", (W, H), config.BLACK)
            _brand_row_centered(img, brand, y=int(H * 0.16), on_dark=True)
            if slide.get("accent_left"):
                _paste_emoji(img, slide["accent_left"], (int(W * 0.14), int(H * 0.165)), 96)
            if slide.get("accent_right"):
                _paste_emoji(img, slide["accent_right"], (int(W * 0.86), int(H * 0.165)), 96)
            valign = "top" if variant == "cover" else "center"
            box = (84, int(H * 0.30), W - 168, int(H * 0.50))
            textkit.draw_lines(img, slide["lines"], box=box, align="center",
                               valign=valign, max_size=90, min_size=42, leading=1.02)
            if variant == "outro":
                tagline = slide.get("tagline", brand.get("tagline"))
                if tagline:
                    textkit.draw_centered(img, tagline, y=int(H * 0.82),
                                          color=config.MUTED, size=32, weight="regular")
        else:  # tweet — white card
            img = Image.new("RGB", (W, H), config.TW_BG)
            pad = 72
            row_bottom = _brand_row_left(img, brand, pad, pad)
            y = row_bottom + 44
            if slide.get("heading"):
                y = textkit.draw_wrapped(img, slide["heading"], x=pad, y=y,
                                         max_w=W - 2 * pad, weight="bold", size=52,
                                         color=config.TW_TEXT, leading=1.16) + 20
            body = slide.get("body")
            if isinstance(body, str):
                body = [body]
            for para in body or []:
                y = textkit.draw_wrapped(img, para, x=pad, y=y, max_w=W - 2 * pad,
                                         weight="regular", size=44, color=config.TW_TEXT,
                                         leading=1.30) + 24

        imgs.append(img)
    return imgs


RENDERERS = {"mythos": render_mythos, "twitter": render_twitter}
