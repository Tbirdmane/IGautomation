#!/usr/bin/env python3
"""Turn a topic into a ready-to-render slideshow JSON using the Claude API.

This closes the automation loop:  topic in  ->  slide copy out  ->  PNGs.

Usage:
    export ANTHROPIC_API_KEY=sk-...
    pip install anthropic
    python generate.py "5 AI tools every freelancer should steal" --style twitter --render
    python generate.py "Why local businesses overpay for websites" --style mythos --render

Without an API key you can skip this entirely: hand-write a JSON in content/
(copy an example) and run `python -m igslides content/your_file.json`.
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

from igslides import config
from igslides.render import render_content

DEFAULT_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6")

SYSTEM_PROMPT = r"""
You write copy for "Fortune University", an Instagram account about using AI to
make money and run a business. You output ONE slideshow as STRICT JSON and
NOTHING else — no markdown, no commentary, no code fences.

VOICE: punchy, specific, confident, useful. Like a sharp friend who's done it.
Never fabricate facts, fake statistics, or invent secret/insider claims. If you
cite a number, it must be real and defensible. Specific > vague every time.

You produce one of two styles (the caller tells you which).

============================ STYLE: "mythos" ============================
Flashy dark slides with big ALL-CAPS lines, white text with key lines in red.
Schema:
{
  "style": "mythos",
  "slug": "kebab-case-topic",
  "slides": [
    { "variant": "cover", "background": "auto", "mood": "ember",
      "image_prompt": "vivid art-direction for a dramatic AI/tech hero image, dark and cinematic, empty darker space in the lower third for text, vertical 4:5, no text in image",
      "lines": [ {"text": "SHORT LINE", "color": "white"}, {"text": "PUNCH", "color": "red"} ],
      "hint": "(SWIPE LEFT FOR MORE)" },
    { "variant": "content",
      "lines": [ {"text": "...", "color": "white"}, {"text": "...", "color": "red"} ],
      "subtext": "one calm supporting sentence (optional)" },
    { "variant": "outro",
      "lines": [ {"text": "FOLLOW US FOR", "color": "white"}, {"text": "MORE AI MONEY", "color": "red"}, {"text": "SKILLS LIKE THIS.", "color": "white"} ] }
  ]
}
RULES:
- Each line is 2-4 words MAX. Break lines for rhythm and impact, like a poster.
- Put the single most important phrase per slide in "red", the rest "white".
- Cover = the hook (a surprising-but-true fact + a promise). Always include "hint".
- Always add an "image_prompt" to the cover: a vivid prompt for a flashy AI/tech
  hero image (dark, cinematic, dramatic; keep the lower third darker for text;
  vertical 4:5; no text in the image). Pick a "mood": ember, crimson, electric,
  gold, or violet.
- 5 to 7 content slides, each making ONE point. Optional one-line "subtext".
- End with an "outro" follow CTA.

============================ STYLE: "twitter" ===========================
A tweet-thread carousel: a dark cover, then white "tweet card" slides.
Schema:
{
  "style": "twitter",
  "slug": "kebab-case-topic",
  "slides": [
    { "variant": "cover", "accent_right": "💰",
      "lines": [ {"text": "BIG HOOK LINE", "color": "white"}, {"text": "EMPHASIS", "color": "red"}, {"text": "HERE ARE 5 ...:", "color": "white"} ] },
    { "variant": "tweet", "heading": "1 — The \"Name\" Prompt",
      "body": [ "First paragraph.", "Second paragraph." ] },
    { "variant": "outro",
      "lines": [ {"text": "SAVE THIS &", "color": "white"}, {"text": "FOLLOW FOR MORE", "color": "red"}, {"text": "AI MONEY SKILLS.", "color": "white"} ] }
  ]
}
RULES:
- Cover lines are short ALL-CAPS (2-5 words each); "accent_right" emoji optional.
- Each "tweet" slide: a short bold "heading" and 1-2 "body" paragraphs. If the
  topic is prompts/tactics, give a REAL, copy-pasteable prompt with [BRACKETS]
  for the user to fill in. Keep each body paragraph under ~40 words.
- If the cover promises "5 X", deliver exactly 5 numbered tweet slides.
- End with an "outro".

OUTPUT: valid JSON for the requested style. No other text.
""".strip()


def extract_json(text):
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(json)?", "", text).strip().rstrip("`").strip()
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError(f"No JSON object found in model output:\n{text[:400]}")
    return json.loads(text[start:end + 1])


def generate(topic, style, model=DEFAULT_MODEL):
    try:
        from anthropic import Anthropic
    except ImportError:
        sys.exit("The 'anthropic' package is required for generate.py.\n"
                 "  pip install anthropic   (and set ANTHROPIC_API_KEY)")
    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("Set ANTHROPIC_API_KEY in your environment first.")

    client = Anthropic()
    msg = client.messages.create(
        model=model,
        max_tokens=2000,
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": f"Style: {style}\nTopic: {topic}\n\nWrite the slideshow JSON now.",
        }],
    )
    text = "".join(b.text for b in msg.content if getattr(b, "type", None) == "text")
    data = extract_json(text)
    data["style"] = style
    return data


def main():
    ap = argparse.ArgumentParser(description="Generate a slideshow JSON from a topic.")
    ap.add_argument("topic", help="what the slideshow is about")
    ap.add_argument("--style", choices=["mythos", "twitter"], default="twitter")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--render", action="store_true", help="also render PNGs")
    args = ap.parse_args()

    data = generate(args.topic, args.style, args.model)
    slug = data.get("slug") or re.sub(r"[^a-z0-9]+", "-", args.topic.lower()).strip("-")[:50]
    data["slug"] = slug

    out_json = config.ROOT / "content" / f"{slug}.json"
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    print(f"Wrote {out_json}  ({len(data['slides'])} slides)")

    if args.render:
        saved = render_content(out_json)
        print(f"Rendered {len(saved)} slides -> {saved[0].parent}/")


if __name__ == "__main__":
    main()
