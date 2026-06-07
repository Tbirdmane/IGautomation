# IGautomation — Fortune University slide generator

Turn the day's real news into two finished Instagram carousels — one **Twitter-style**
value post and one **flashy "mythos"** hook post — from a single JSON file each.

- **`mythos`** — flashy dark style: big ALL-CAPS lines, white text with key
  phrases in red, a cinematic AI-energy backdrop (or your own hero art), a
  "swipe left" hook, and a follow-CTA outro.
- **`twitter`** — tweet-thread style: a dark branded cover, then clean white
  "tweet card" slides with the verified badge, heading + body.

Everything renders to **1080×1350 PNGs** (Instagram's reach-friendly 4:5 portrait).

---

## The daily loop

```
research the web ──► pick 2 ideas ──► write copy (JSON) ──► [hero art] ──► render ──► post
   ideas.py / chat         you          generate.py        imagegen.py    igslides
```

1. **Get ideas** — researched from live news (see below). Pick one for `twitter`,
   one for `mythos`.
2. **Write the copy** into `content/<slug>.json` — by hand (copy an example),
   in a chat with Claude, or with `generate.py`.
3. **Flashy cover art** (mythos only) — generate the hero image from the cover's
   `image_prompt`, or let the built-in cinematic backdrop stand in. (details below)
4. **Render**: `python -m igslides content/your_post.json`
5. Post the `output/<slug>/` folder as a carousel.

---

## Quickstart

```bash
pip install -r requirements.txt          # just Pillow

# render today's two example posts
python -m igslides content/daily_twitter.json content/daily_mythos.json

# or everything in the folder
python -m igslides content/
```

Output lands in `output/<slug>/slide-01.png`, `slide-02.png`, …

---

## 1. Daily ideas (live research)

Two ways to get fresh, on-brand ideas grounded in real news (AI, crypto, money,
apps, tech):

- **Just ask Claude in chat** — "give me today's two post ideas" — and Claude
  researches the web and proposes a `mythos` hook + a `twitter` post.
- **Run the script** for hands-off automation:
  ```bash
  pip install anthropic && export ANTHROPIC_API_KEY=sk-...
  python ideas.py --count 8 --json ideas.json
  ```
  It web-searches and prints ranked ideas, each tagged `mythos`/`twitter` with a
  source link, ready to hand to `generate.py`.

> Ground every hook in something true. The audience that converts to buyers is
> the one that trusts you.

---

## 2. Generate the copy

```bash
pip install anthropic && export ANTHROPIC_API_KEY=sk-...
python generate.py "A solo founder hit $10k/mo in 47 days with no code" --style twitter --render
python generate.py "ChatGPT just hit 1 billion users" --style mythos --render
```

Writes `content/<slug>.json` (and renders with `--render`). For `mythos` posts it
also fills in an `image_prompt` and `mood` for the cover. Tweak the voice by
editing `SYSTEM_PROMPT` in `generate.py`. No API key? Hand-write the JSON — copy
`content/daily_twitter.json` or `content/daily_mythos.json` and edit.

---

## 3. Flashy cover art (mythos)

Each `mythos` cover carries an **`image_prompt`** (art-direction for a dramatic AI
hero image) and a **`mood`**. Pick how the cover image gets made:

1. **Pollinations — FREE, the default.** Cinematic FLUX-based AI art, no API key,
   no cost. One-time setup so the sandbox can reach it: edit the environment →
   **Network access → Custom** → add `image.pollinations.ai` to **Allowed
   domains** (keep the default package-manager list checked) → save → start a new
   session. Then:
   ```bash
   python -m igslides.imagegen content/daily_mythos.json   # free art, wired in
   python -m igslides content/daily_mythos.json            # re-render
   ```
2. **Nano Banana (Gemini) — paid, top quality.** `export IMAGE_PROVIDER=gemini`
   and set `GEMINI_API_KEY`. Image output is billed (~cents/image). Higher-res
   "Nano Banana Pro": `export GEMINI_IMAGE_MODEL=gemini-3-pro-image`. (OpenAI also
   works: `IMAGE_PROVIDER=openai` + `OPENAI_API_KEY`, runs locally.)
3. **Zero setup.** Leave `"background": "auto"` and pick a `mood`
   (`ember`, `crimson`, `electric`, `gold`, `violet`) for the built-in cinematic
   "AI energy core" backdrop — free, instant, no network.
4. **Paste workflow.** Generate the `image_prompt` in any free tool (the Gemini
   app, Bing/Copilot…), save to `assets/backgrounds/<slug>.png`, and set the
   cover's `"background"` to that path.

---

## 4. Your logo

Drop your real Fortune University seal at **`assets/logo.png`** — it's used
automatically as the avatar on Twitter-style slides (circular-cropped). Until
then, slides fall back to a navy/gold "FU" monogram. See `assets/README.md`.

---

## Content schema (reference)

```jsonc
{
  "style": "mythos" | "twitter",
  "slug": "kebab-case-name",          // output folder name
  "brand": { "name": "...", "handle": "@...", "verified": true, "avatar": "assets/logo.png" },
  "slides": [ ... ]
}
```

A **line** is a string, `{"text", "color"}`, or `{"spans": [...]}` for inline
multi-colour. Colours: `white`, `red`, `muted`, `blue`, or hex (`"#E8372B"`).

- **mythos** `variant`: `cover` (`background`, `mood`, `image_prompt`, `lines`, `hint`)
  · `content` (`lines`, optional `subtext`) · `outro` (`lines`).
- **twitter** `variant`: `cover` (`lines`, optional `accent_right`/`accent_left` emoji)
  · `tweet` (`heading`, `body` array) · `outro` (`lines`).

Full working examples: `content/daily_*.json` and `content/example_*.json`.
