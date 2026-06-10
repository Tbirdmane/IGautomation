#!/usr/bin/env python3
"""Tile a post's rendered slides into one contact-sheet preview image.

Lets you review a whole carousel at a glance — and stay well under any
per-chat image limit — while the full-res slides still live in
output/<slug>/ and in the --zip bundle for actual posting.

Usage:
    python -m igslides.montage daily-ai-ipo-race          # by slug
    python -m igslides.montage output/daily-ai-ipo-race   # by folder
    python -m igslides.montage content/daily_mythos.json  # by content file
"""

import argparse
import json
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from . import config

THUMB_W = 380          # thumbnail width per slide
GAP = 24
PAD = 28
SHEET_BG = (12, 12, 14)
BADGE_BG = (232, 55, 43)   # brand red
BADGE_FG = (255, 255, 255)


def _slug_dir(target, base):
    base = Path(base or config.OUTPUT)
    p = Path(target)
    if p.suffix == ".json":
        return base / json.loads(p.read_text()).get("slug", p.stem)
    if p.exists() and p.is_dir():
        return p
    return base / p.name


def make_montage(target, out=None, cols=None, base=None):
    d = _slug_dir(target, base)
    slides = sorted(d.glob("slide-*.png"))
    if not slides:
        raise SystemExit(f"No slides found in {d}")

    cols = cols or min(3, len(slides))
    rows = math.ceil(len(slides) / cols)

    s0 = Image.open(slides[0])
    thumb_h = round(THUMB_W * s0.height / s0.width)

    W = PAD * 2 + cols * THUMB_W + (cols - 1) * GAP
    H = PAD * 2 + rows * thumb_h + (rows - 1) * GAP
    sheet = Image.new("RGB", (W, H), SHEET_BG)
    draw = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype(config.FONT_BOLD, 26)
    except Exception:
        font = ImageFont.load_default()

    for i, sp in enumerate(slides):
        r, c = divmod(i, cols)
        x = PAD + c * (THUMB_W + GAP)
        y = PAD + r * (thumb_h + GAP)
        im = Image.open(sp).convert("RGB").resize((THUMB_W, thumb_h), Image.LANCZOS)
        sheet.paste(im, (x, y))
        # order badge so you know which slide goes first
        n = str(i + 1)
        draw.rectangle([x, y, x + 44, y + 44], fill=BADGE_BG)
        tb = draw.textbbox((0, 0), n, font=font)
        draw.text((x + (44 - (tb[2] - tb[0])) / 2 - tb[0],
                   y + (44 - (tb[3] - tb[1])) / 2 - tb[1]), n, fill=BADGE_FG, font=font)

    out = Path(out) if out else Path(base or config.OUTPUT) / f"{d.name}-preview.png"
    sheet.save(out, "PNG")
    return out


def main():
    ap = argparse.ArgumentParser(description="Make a contact-sheet preview of a rendered post.")
    ap.add_argument("target", nargs="+", help="slug, output folder, or content JSON")
    ap.add_argument("-o", "--out", default=None, help="output PNG (single target only)")
    ap.add_argument("--cols", type=int, default=None)
    args = ap.parse_args()
    single = len(args.target) == 1
    for t in args.target:
        print(f"  preview -> {make_montage(t, args.out if single else None, args.cols)}")


if __name__ == "__main__":
    main()
