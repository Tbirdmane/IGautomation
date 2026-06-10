"""Load a content JSON and render it to numbered PNG slides."""

import argparse
import json
import zipfile
from datetime import date
from pathlib import Path

from . import config
from . import imagegen
from .montage import make_montage
from .styles import RENDERERS


def render_content(path, outdir=None):
    path = Path(path)
    data = json.loads(path.read_text())
    style = data.get("style", "mythos")
    if style not in RENDERERS:
        raise SystemExit(f"Unknown style '{style}'. Use one of: {', '.join(RENDERERS)}")

    imgs = RENDERERS[style](data)
    slug = data.get("slug", path.stem)
    out = Path(outdir or config.OUTPUT) / slug
    out.mkdir(parents=True, exist_ok=True)

    saved = []
    for i, im in enumerate(imgs, 1):
        p = out / f"slide-{i:02d}.png"
        im.save(p, "PNG")
        saved.append(p)
    return saved


def bundle(slugs, outdir=None, name=None):
    """Zip the given rendered slide folders into one dated archive for easy download.

    Lives in the (git-ignored) output dir, so it never bloats the repo."""
    out = Path(outdir or config.OUTPUT)
    name = name or f"Fortune University {date.today().isoformat()}.zip"
    zpath = out / name
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for slug in slugs:
            for png in sorted((out / slug).glob("*.png")):
                z.write(png, arcname=f"{slug}/{png.name}")
    return zpath


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="igslides", description="Render Fortune University carousel slides from JSON."
    )
    ap.add_argument("content", nargs="+", help="content JSON file(s), or directories of them")
    ap.add_argument("-o", "--out", default=None, help="output directory (default: ./output)")
    ap.add_argument("--zip", action="store_true",
                    help="bundle all rendered slides into one dated .zip for easy download")
    ap.add_argument("--preview", action="store_true",
                    help="also write a one-image contact sheet per post for quick review")
    ap.add_argument("--art", action="store_true",
                    help="generate cover hero art from image_prompt first (free Pollinations by default)")
    args = ap.parse_args(argv)

    files = []
    for c in args.content:
        p = Path(c)
        files.extend(sorted(p.glob("*.json")) if p.is_dir() else [p])
    if not files:
        raise SystemExit(f"No JSON content found at {args.content}")

    slugs = []
    for f in files:
        if args.art:
            try:
                imagegen.process(f)
            except SystemExit as e:
                print(f"  [art] skipped for {f.name}: {e}")
        saved = render_content(f, args.out)
        slugs.append(saved[0].parent.name)
        print(f"  {f.name}: {len(saved)} slides -> {saved[0].parent}/")

    if args.zip:
        zpath = bundle(slugs, args.out)
        print(f"  bundled {len(slugs)} post(s) -> {zpath}")

    if args.preview:
        for slug in slugs:
            print(f"  preview -> {make_montage(slug, base=args.out)}")


if __name__ == "__main__":
    main()
