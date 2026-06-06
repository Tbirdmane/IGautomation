#!/usr/bin/env python3
"""Optional: turn a cover's `image_prompt` into a hero background image.

Default provider is OpenAI Images (gpt-image-1). NOTE: image-generation hosts
are firewalled inside the cloud sandbox, so run this on YOUR machine — or skip
it and use the paste workflow (generate the prompt in any image tool, save the
result to assets/backgrounds/, and point the cover's "background" at it).

Usage:
    pip install openai
    export OPENAI_API_KEY=sk-...
    python -m igslides.imagegen content/daily_mythos.json
"""

import argparse
import base64
import json
import sys
from pathlib import Path

from . import config


def generate_image_openai(prompt, out_path, size="1024x1536", model="gpt-image-1"):
    """Generate one image and write it to out_path. Raises on failure."""
    try:
        from openai import OpenAI
    except ImportError:
        sys.exit("The 'openai' package is required.\n  pip install openai   (and set OPENAI_API_KEY)")
    client = OpenAI()
    result = client.images.generate(model=model, prompt=prompt, size=size)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(base64.b64decode(result.data[0].b64_json))
    return out_path


def process(content_path):
    content_path = Path(content_path)
    data = json.loads(content_path.read_text())
    slug = data.get("slug", content_path.stem)

    changed = False
    for slide in data.get("slides", []):
        if slide.get("variant") == "cover" and slide.get("image_prompt"):
            out = config.ASSETS / "backgrounds" / f"{slug}.png"
            print(f"Generating hero image -> {out}")
            generate_image_openai(slide["image_prompt"], out)
            slide["background"] = str(out.relative_to(config.ROOT))
            changed = True

    if changed:
        content_path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
        print(f"Updated {content_path.name} to use the generated background. "
              f"Re-render with:  python -m igslides {content_path}")
    else:
        print("No cover slide with an 'image_prompt' was found — nothing to do.")


def main():
    ap = argparse.ArgumentParser(description="Generate cover hero images from image_prompt fields.")
    ap.add_argument("content", help="content JSON file")
    process(ap.parse_args().content)


if __name__ == "__main__":
    main()
