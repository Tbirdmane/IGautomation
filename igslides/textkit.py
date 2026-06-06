"""Text utilities: font loading, measuring, wrapping, auto-fit rich lines, emoji."""

from functools import lru_cache

from PIL import Image, ImageDraw, ImageFont

from . import config


@lru_cache(maxsize=256)
def font(weight="bold", size=72):
    path = config.FONT_BOLD if weight == "bold" else config.FONT_REG
    return ImageFont.truetype(path, size)


def line_height(f):
    ascent, descent = f.getmetrics()
    return ascent + descent


def text_w(draw, s, f):
    return draw.textlength(s, font=f)


# --- rich "lines" -----------------------------------------------------------
# A line may be:
#   "plain string"                         -> single span, default colour
#   {"text": "...", "color": "red"}        -> single coloured span
#   {"spans": [{"text": "..", "color":..}]}-> several inline-coloured spans
def to_spans(line, default_color="white"):
    if isinstance(line, str):
        return [{"text": line, "color": default_color}]
    if isinstance(line, dict):
        if "spans" in line:
            return [
                {"text": s.get("text", ""), "color": s.get("color", default_color)}
                for s in line["spans"]
            ]
        return [{"text": line.get("text", ""), "color": line.get("color", default_color)}]
    return [{"text": str(line), "color": default_color}]


def spans_width(draw, spans, f):
    return sum(text_w(draw, s["text"], f) for s in spans)


def wrap(draw, text, f, max_w):
    """Greedy word-wrap to a pixel width."""
    lines, cur = [], ""
    for word in text.split():
        trial = f"{cur} {word}".strip()
        if not cur or text_w(draw, trial, f) <= max_w:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines or [""]


def _fit_size(draw, lines_spans, weight, box_w, box_h, max_size, min_size, leading):
    size = max_size
    while size > min_size:
        f = font(weight, size)
        widest = max((spans_width(draw, sp, f) for sp in lines_spans), default=0)
        total_h = line_height(f) * leading * len(lines_spans)
        if widest <= box_w and total_h <= box_h:
            return size
        size -= 2
    return min_size


def draw_lines(img, lines, *, box, weight="bold", align="center", valign="center",
               max_size=110, min_size=40, leading=0.96, default_color="white",
               fixed_size=None):
    """Draw explicitly-broken headline lines, auto-fitting the font to `box`.

    `box` is (x, y, w, h). Returns (top_y, bottom_y, font_size).
    """
    draw = ImageDraw.Draw(img)
    lines_spans = [to_spans(ln, default_color) for ln in lines]
    bx, by, bw, bh = box
    size = fixed_size or _fit_size(draw, lines_spans, weight, bw, bh,
                                   max_size, min_size, leading)
    f = font(weight, size)
    step = line_height(f) * leading
    block_h = step * len(lines_spans)

    if valign == "top":
        y = by
    elif valign == "bottom":
        y = by + bh - block_h
    else:
        y = by + (bh - block_h) / 2
    top_y = y

    for spans in lines_spans:
        lw = spans_width(draw, spans, f)
        if align == "left":
            x = bx
        elif align == "right":
            x = bx + bw - lw
        else:
            x = bx + (bw - lw) / 2
        for s in spans:
            draw.text((x, y), s["text"], font=f, fill=config.resolve_color(s["color"]))
            x += text_w(draw, s["text"], f)
        y += step
    return top_y, y, size


def draw_centered(img, text, *, y, color, size, weight="bold"):
    draw = ImageDraw.Draw(img)
    f = font(weight, size)
    w = text_w(draw, text, f)
    draw.text(((img.width - w) / 2, y), text, font=f, fill=config.resolve_color(color))
    return y + line_height(f)


def draw_wrapped(img, text, *, x, y, max_w, weight, size, color, leading=1.28):
    draw = ImageDraw.Draw(img)
    f = font(weight, size)
    step = line_height(f) * leading
    for ln in wrap(draw, text, f, max_w):
        draw.text((x, y), ln, font=f, fill=config.resolve_color(color))
        y += step
    return y


# --- emoji (optional polish) ------------------------------------------------
@lru_cache(maxsize=8)
def _emoji_font():
    for sz in (109, 137, 128, 96, 64):
        try:
            return ImageFont.truetype(config.FONT_EMOJI, sz)
        except Exception:
            continue
    return None


def render_emoji(ch, px):
    """Render a colour emoji to an RGBA image ~`px` tall, or None if unavailable."""
    ef = _emoji_font()
    if ef is None:
        return None
    tmp = Image.new("RGBA", (180, 180), (0, 0, 0, 0))
    try:
        ImageDraw.Draw(tmp).text((4, 4), ch, font=ef, embedded_color=True)
    except Exception:
        return None
    bbox = tmp.getbbox()
    if not bbox:
        return None
    crop = tmp.crop(bbox)
    scale = px / max(crop.size)
    return crop.resize(
        (max(1, int(crop.width * scale)), max(1, int(crop.height * scale))),
        Image.LANCZOS,
    )
