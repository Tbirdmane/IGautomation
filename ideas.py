#!/usr/bin/env python3
"""Research the web for fresh, on-brand post ideas using the Claude API's
built-in web search, and print them ranked so you can hand one to generate.py.

Usage:
    pip install anthropic
    export ANTHROPIC_API_KEY=sk-...
    python ideas.py --count 8
    python ideas.py --count 8 --json ideas.json
"""

import argparse
import json
import os
import sys
from pathlib import Path

DEFAULT_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6")

SYSTEM = """You are the daily content researcher for "Fortune University", an
Instagram account about using AI to make money, build apps, and stay ahead in
tech, crypto and business.

Use web search to find the FRESHEST, most scroll-stopping, REAL stories from the
last few days across: AI news, crypto/markets, people making money with apps or
AI, startup / indie-hacker wins, and notable tech news. Prefer specific numbers
and named, verifiable events over generic advice. Never invent facts.

Return ONLY a JSON array of post ideas, each object:
{
  "hook": "one-line scroll-stopper (a surprising true fact + a promise)",
  "style": "mythos" | "twitter",
  "angle": "what the carousel teaches / the payoff for the viewer",
  "why_now": "why this is timely this week",
  "source_url": "a URL backing the core fact"
}
Use "mythos" for dramatic single-stat shock hooks; "twitter" for how-to / list /
story-breakdown posts. Output nothing except the JSON array."""


def research(count, model=DEFAULT_MODEL):
    try:
        from anthropic import Anthropic
    except ImportError:
        sys.exit("The 'anthropic' package is required.\n  pip install anthropic   (and set ANTHROPIC_API_KEY)")
    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("Set ANTHROPIC_API_KEY in your environment first.")

    client = Anthropic()
    msg = client.messages.create(
        model=model,
        max_tokens=2500,
        system=SYSTEM,
        tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": 6}],
        messages=[{
            "role": "user",
            "content": f"Find {count} post ideas for today. Search broadly first, then return the JSON array.",
        }],
    )
    text = "".join(getattr(b, "text", "") for b in msg.content
                    if getattr(b, "type", None) == "text")
    start, end = text.find("["), text.rfind("]")
    if start == -1 or end == -1:
        sys.exit("Could not find a JSON array in the model output:\n" + text[:600])
    return json.loads(text[start:end + 1])


def main():
    ap = argparse.ArgumentParser(description="Generate researched daily post ideas.")
    ap.add_argument("--count", type=int, default=8)
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--json", default=None, help="also write the ideas to this file")
    args = ap.parse_args()

    ideas = research(args.count, args.model)
    for i, idea in enumerate(ideas, 1):
        print(f"\n{i}. [{idea.get('style', '?')}]  {idea.get('hook', '')}")
        if idea.get("angle"):
            print(f"     angle:   {idea['angle']}")
        if idea.get("why_now"):
            print(f"     why now: {idea['why_now']}")
        if idea.get("source_url"):
            print(f"     source:  {idea['source_url']}")
    if args.json:
        Path(args.json).write_text(json.dumps(ideas, indent=2, ensure_ascii=False))
        print(f"\nWrote {args.json}")


if __name__ == "__main__":
    main()
