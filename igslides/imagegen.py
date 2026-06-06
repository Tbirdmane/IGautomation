#!/usr/bin/env python3
"""Turn a cover's `image_prompt` into a hero background image.

Providers (each writes the cover hero to assets/backgrounds/<slug>.png):
  * gemini     — Google Nano Banana (Gemini image model). Default. Plain REST,
                 no SDK, and its host is reachable from the Claude cloud sandbox.
                 Heads-up: image *output* needs a billing-enabled key — the free
                 tier allows 0 images/day (the API returns a 429 with "limit: 0").
  * cloudflare — Cloudflare Workers AI, FLUX.1-schnell. Plain REST, no SDK, and
                 reachable from the sandbox. Free tier is generous (10k Neurons/
                 day, no credit card); FLUX.1-schnell is Apache-2.0 (commercial OK).
  * openai     — OpenAI Images (needs `pip install openai`; OpenAI's host is
                 firewalled in the sandbox, so run this one locally).

Provider is auto-detected from whichever credentials are present, or forced with
IMAGE_PROVIDER=gemini|cloudflare|openai.

Usage:
    # Nano Banana (default):
    export GEMINI_API_KEY=...
    python -m igslides.imagegen content/daily_mythos.json
    python -m igslides content/daily_mythos.json          # re-render with the new art

    # Cloudflare Workers AI (free FLUX.1-schnell):
    export CLOUDFLARE_ACCOUNT_ID=...  CLOUDFLARE_API_TOKEN=...  IMAGE_PROVIDER=cloudflare
    python -m igslides.imagegen content/daily_mythos.json
    python -m igslides content/daily_mythos.json

    # OpenAI (local only):
    export OPENAI_API_KEY=...  IMAGE_PROVIDER=openai && pip install openai
"""

import argparse
import base64
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

from . import config

GEMINI_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
# Nano Banana = gemini-2.5-flash-image. For Nano Banana Pro (4K, better text)
# set GEMINI_IMAGE_MODEL=gemini-3-pro-image.
GEMINI_DEFAULT_MODEL = "gemini-2.5-flash-image"

CLOUDFLARE_ENDPOINT = "https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/{model}"
# FLUX.1 [schnell] — Apache-2.0 (commercial OK), 1-8 diffusion steps. Swap in a
# different Workers AI model with CLOUDFLARE_IMAGE_MODEL (e.g. a newer FLUX).
CLOUDFLARE_DEFAULT_MODEL = "@cf/black-forest-labs/flux-1-schnell"

_SUPPORTED_RATIOS = {
    "1:1": 1.0, "4:5": 0.8, "5:4": 1.25, "3:4": 0.75, "4:3": 1.333,
    "2:3": 0.667, "3:2": 1.5, "9:16": 0.5625, "16:9": 1.778, "21:9": 2.333,
}


def _gemini_key():
    return os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")


def _cloudflare_creds():
    return os.environ.get("CLOUDFLARE_ACCOUNT_ID"), os.environ.get("CLOUDFLARE_API_TOKEN")


def _closest_ratio(w, h):
    target = w / h
    return min(_SUPPORTED_RATIOS, key=lambda r: abs(_SUPPORTED_RATIOS[r] - target))


def generate_image_gemini(prompt, out_path, aspect_ratio="4:5", model=None):
    key = _gemini_key()
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


def generate_image_cloudflare(prompt, out_path, model=None):
    """Cloudflare Workers AI (FLUX.1-schnell by default). The model returns a
    base64 JPEG in result.image; we normalise it to PNG to match the .png path."""
    account_id, token = _cloudflare_creds()
    if not (account_id and token):
        sys.exit("Set CLOUDFLARE_ACCOUNT_ID and CLOUDFLARE_API_TOKEN for Cloudflare Workers AI.")
    model = model or os.environ.get("CLOUDFLARE_IMAGE_MODEL", CLOUDFLARE_DEFAULT_MODEL)
    try:
        steps = max(1, min(8, int(os.environ.get("CF_FLUX_STEPS", "4"))))
    except ValueError:
        steps = 4
    req = urllib.request.Request(
        CLOUDFLARE_ENDPOINT.format(account_id=account_id, model=model),
        data=json.dumps({"prompt": prompt, "steps": steps}).encode(),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            data = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        raise SystemExit(f"Cloudflare Workers AI request failed ({e.code}):\n{e.read().decode(errors='replace')}")

    b64 = (data.get("result") or {}).get("image")
    if not b64:
        raise SystemExit("Cloudflare Workers AI returned no image:\n" + json.dumps(data, indent=2)[:1200])
    raw = base64.b64decode(b64)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        import io
        from PIL import Image
        Image.open(io.BytesIO(raw)).convert("RGB").save(out_path, "PNG")
    except Exception:
        out_path.write_bytes(raw)  # PIL sniffs the real format at render time anyway
    return out_path


def generate_image_openai(prompt, out_path, size="1024x1536", model="gpt-image-1"):
    try:
        from openai import OpenAI
    except ImportError:
        sys.exit("pip install openai   (and set OPENAI_API_KEY)")
    client = OpenAI()
    result = client.images.generate(model=model, prompt=prompt, size=size)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(base64.b64decode(result.data[0].b64_json))
    return out_path


def _provider():
    forced = os.environ.get("IMAGE_PROVIDER", "").lower()
    if forced:
        return forced
    if _gemini_key():
        return "gemini"
    if all(_cloudflare_creds()):
        return "cloudflare"
    if os.environ.get("OPENAI_API_KEY"):
        return "openai"
    return "gemini"


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
            if provider == "openai":
                generate_image_openai(slide["image_prompt"], out)
            elif provider == "cloudflare":
                generate_image_cloudflare(slide["image_prompt"], out)
            else:
                generate_image_gemini(slide["image_prompt"], out, _closest_ratio(w, h))
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
