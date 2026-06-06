# IGautomation — Fortune University slide generator

Generate Instagram carousel slides in two proven styles, from a single JSON file:

- **`mythos`** — the flashy dark style: big ALL-CAPS lines, white text with key
  phrases in red, ember backdrop, "swipe left" hook, follow-CTA outro.
- **`twitter`** — the tweet-thread style: a dark cover, then clean white "tweet
  card" slides with a verified badge, heading + body.

Everything renders to **1080×1350 PNGs** (Instagram's reach-friendly 4:5 portrait),
ready to drop straight into a post.

---

## Quickstart

```bash
pip install -r requirements.txt          # just Pillow

# render the two bundled examples
python -m igslides content/

# render one file
python -m igslides content/example_twitter.json

# custom output folder
python -m igslides content/example_mythos.json -o /tmp/slides
```

Output lands in `output/<slug>/slide-01.png`, `slide-02.png`, …

---

## How it works

Copy lives in JSON; a Pillow renderer turns it into images. That split means you
can write the copy **by hand**, **in a chat with Claude**, or **fully automated**
via the API script — the render step is identical either way.

```
topic ──► (you / Claude / generate.py) ──► content/*.json ──► python -m igslides ──► PNGs
```

### Content schema

Common fields:

```jsonc
{
  "style": "mythos" | "twitter",
  "slug": "kebab-case-name",          // output folder name
  "size": [1080, 1350],               // optional
  "brand": {
    "name": "Fortune University",
    "handle": "@FortuneUniversity",
    "verified": true,
    "avatar": "assets/logo.png",      // optional; falls back to an "FU" monogram
    "tagline": "New post every week."
  },
  "slides": [ ... ]
}
```

A **line** (used in headlines) can be a string, a `{"text", "color"}` object, or
`{"spans": [...]}` for inline multi-colour. Colours: `white`, `red`, `muted`,
`blue`, or any hex like `"#E8372B"`.

**mythos slides** — `variant` is `cover` | `content` | `outro`:

```jsonc
{ "variant": "cover", "background": "auto",   // or "assets/backgrounds/x.png"
  "lines": [ {"text": "SEARCHES FOR", "color": "white"},
             {"text": "\"VIBE CODING\"", "color": "red"} ],
  "hint": "(SWIPE LEFT FOR MORE)" }

{ "variant": "content",
  "lines": [ {"text": "LOCAL BUSINESSES PAY", "color": "white"},
             {"text": "$750 - $1,200", "color": "red"} ],
  "subtext": "A plumber's booking page." }      // optional
```

**twitter slides** — `variant` is `cover` | `tweet` | `outro`:

```jsonc
{ "variant": "cover", "accent_right": "💰",
  "lines": [ {"text": "HERE ARE 5 PROMPTS", "color": "red"} ] }

{ "variant": "tweet",
  "heading": "1 — The \"Hard Question\" Prompt",
  "body": [ "Paragraph one.", "Paragraph two." ] }
```

See `content/example_mythos.json` and `content/example_twitter.json` for full,
working examples.

---

## Brand assets

Put your logo at `assets/logo.png` and set `"avatar": "assets/logo.png"`.
Drop dramatic cover art in `assets/backgrounds/`. See `assets/README.md`.

---

## Optional: generate copy automatically

`generate.py` turns a topic into a finished JSON via the Claude API.

```bash
pip install anthropic
export ANTHROPIC_API_KEY=sk-...
python generate.py "5 AI prompts that save 10 hours a week" --style twitter --render
python generate.py "Why 'vibe coding' is a real side hustle" --style mythos --render
```

It writes `content/<slug>.json` and (with `--render`) the PNGs. Tweak the voice
by editing `SYSTEM_PROMPT` in `generate.py`. Set `ANTHROPIC_MODEL` to change models.

---

## A realistic 2-a-day workflow

1. Pick two topics (one `mythos` hook, one `twitter` value post).
2. Generate or hand-write the two JSON files in `content/`.
3. `python -m igslides content/` to render everything.
4. Skim the PNGs, fix any copy in the JSON, re-render.
5. Post the folder as a carousel.

Keep claims true — the audience that converts to buyers is the one that trusts you.
