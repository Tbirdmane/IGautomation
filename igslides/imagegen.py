#!/usr/bin/env python3
"""Turn a cover's `image_prompt` into a hero background image.

Providers (set IMAGE_PROVIDER to force one; otherwise the free default is used):

  * pollinations (DEFAULT) — FREE, no API key. Cinematic FLUX-based AI art.
      Requires allowing image.pollinations.ai in your environment's network
      settings (Network access -> Custom -> Allowed domains). No cost.
  * gemini        — Google "Nano Banana". High quality but PAID (image output
      is billed). Needs GEMINI_API_KEY.
  * openai        — OpenAI Images. PAID. Needs OPENAI_API_KEY + `pip install openai`.
      (OpenAI's host is firewalled in the sandbox; runs locally.)

Usage:
    python -m igslides.imagegen content/daily_mythos.json   # free Pollinations
    IMAGE_PROVIDER=gemini python -m igslides.imagegen content/daily_mythos.json
    python -m igslides content/daily_mythos.json            # re-render
"""

import argparse
import base64
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from . import config

POLLINATIONS_ENDPOINT = "https://image.pollinations.ai/prompt/{prompt}"

GEMINI_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
# Nano Banana = gemini-2.5-flash-image. Nano Banana Pro = gemini-3-pro-image.
GEMINI_DEFAULT_MODEL = "gemini-2.5-flash-image"

_SUPPORTED_RATIOS = {
    "1:1": 1.0, "4:5": 0.8, "5:4": 1.25, "3:4": 0.75, "4:3": 1.333,
    "2:3": 0.667, "3:2": 1.5, "9:16": 0.5625, "16:9": 1.778, "21:9": 2.333,
}


def _closest_ratio(w, h):
    target = w / h
    return min(_SUPPORTED_RATIOS, key=lambda r: abs(_SUPPORTED_RATIOS[r] - target))


# ----------------------------------------------------------- Pollinations ----
def generate_image_pollinations(prompt, out_path, width=1080, height=1350,
                                model=None, seed=None):
    """FREE, key-less image generation via Pollinations (FLUX)."""
    params = {
        "width": int(width), "height": int(height),
        "model": model or os.environ.get("POLLINATIONS_MODEL", "flux"),
        "nologo": "true", "enhance": "true", "private": "true",
    }
    if seed is not None:
        params["seed"] = seed
    if os.environ.get("POLLINATIONS_TOKEN"):       # optional, only for paid tiers
        params["token"] = os.environ["POLLINATIONS_TOKEN"]
    url = POLLINATIONS_ENDPOINT.format(prompt=urllib.parse.quote(prompt))
    url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "igslides/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=240) as resp:
            ctype = resp.headers.get("Content-Type", "")
            data = resp.read()
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")[:200]
        if e.code == 403 and "allowlist" in body.lower():
            raise SystemExit(
                "Pollinations is blocked by your environment's network allowlist.\n"
                "Fix (free): edit the environment -> Network access -> Custom ->\n"
                "add  image.pollinations.ai  to Allowed domains, keep the default\n"
                "package-manager list checked, save, then start a new session.")
        raise SystemExit(f"Pollinations request failed ({e.code}): {body}")
    except urllib.error.URLError as e:
        raise SystemExit(f"Could not reach Pollinations: {e.reason}")
    if not ctype.startswith("image") or len(data) < 1000:
        raise SystemExit(f"Pollinations returned no image (type={ctype}, {len(data)} bytes).")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(data)
    return out_path


# ----------------------------------------------------------------- Gemini ----
def generate_image_gemini(prompt, out_path, aspect_ratio="4:5", model=None):
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not key:
        sys.exit("Set GEMINI_API_KEY (or GOOGLE_API_KEY) for Nano Banana image generation.")
    model = model or os.environ.get("GEMINI_IMAGE_MODEL", GEMINI_DEFAULT_MODEL)
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseModalities": ["IMAGE"],
            "imageConfig": {"aspectRatio": aspect_ratio},
        },
    }
    req = urllib.request.Request(
        GEMINI_ENDPOINT.format(model=model),
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json", "x-goog-api-key": key},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            data = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        raise SystemExit(f"Nano Banana request failed ({e.code}):\n{e.read().decode(errors='replace')}")
    for cand in data.get("candidates", []):
        for part in cand.get("content", {}).get("parts", []):
            inline = part.get("inlineData") or part.get("inline_data")
            if inline and inline.get("data"):
                out_path.parent.mkdir(parents=True, exist_ok=True)
                out_path.write_bytes(base64.b64decode(inline["data"]))
                return out_path
    raise SystemExit("Nano Banana returned no image:\n" + json.dumps(data, indent=2)[:1200])


# ----------------------------------------------------------------- OpenAI ----
def generate_image_openai(prompt, out_path, size="1024x1536", model="gpt-image-1"):
    try:
        from openai import OpenAI
    except ImportError:
        sys.exit("pip install openai   (and set OPENAI_API_KEY)")
    result = OpenAI().images.generate(model=model, prompt=prompt, size=size)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(base64.b64decode(result.data[0].b64_json))
    return out_path


def _provider():
    return os.environ.get("IMAGE_PROVIDER", "pollinations").lower()


def process(content_path):
    content_path = Path(content_path)
    data = json.loads(content_path.read_text())
    slug = data.get("slug", content_path.stem)
    w, h = data.get("size", [config.WIDTH, config.HEIGHT])
    provider = _provider()

    changed = False
    for slide in data.get("slides", []):
        if slide.get("variant") == "cover" and slide.get("image_prompt"):
            out = config.ASSETS / "backgrounds" / f"{slug}.png"
            print(f"[{provider}] generating hero image -> {out}")
            if provider == "gemini":
                generate_image_gemini(slide["image_prompt"], out, _closest_ratio(w, h))
            elif provider == "openai":
                generate_image_openai(slide["image_prompt"], out)
            else:
                generate_image_pollinations(slide["image_prompt"], out, w, h)
            slide["background"] = str(out.relative_to(config.ROOT))
            changed = True

    if changed:
        content_path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
        print(f"Updated {content_path.name}. Re-render with:  python -m igslides {content_path}")
    else:
        print("No cover slide with an 'image_prompt' was found — nothing to do.")


def main():
    ap = argparse.ArgumentParser(description="Generate cover hero images from image_prompt fields.")
    ap.add_argument("content", help="content JSON file")
    process(ap.parse_args().content)


if __name__ == "__main__":
    main()
