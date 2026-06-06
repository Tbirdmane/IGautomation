"""Load a content JSON and render it to numbered PNG slides."""

import argparse
import json
from pathlib import Path

from . import config
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


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="igslides", description="Render Fortune University carousel slides from JSON."
    )
    ap.add_argument("content", help="content JSON file, or a directory of them")
    ap.add_argument("-o", "--out", default=None, help="output directory (default: ./output)")
    args = ap.parse_args(argv)

    target = Path(args.content)
    files = sorted(target.glob("*.json")) if target.is_dir() else [target]
    if not files:
        raise SystemExit(f"No JSON content found at {target}")

    for f in files:
        saved = render_content(f, args.out)
        print(f"  {f.name}: {len(saved)} slides -> {saved[0].parent}/")


if __name__ == "__main__":
    main()
